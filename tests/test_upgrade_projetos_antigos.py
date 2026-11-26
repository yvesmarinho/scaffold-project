# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_upgrade_projetos_antigos.py
TITULO: O --upgrade migra projetos antigos (branch dev e .github/prompts/)
DATA: 26/11/2026 13:55
MODIFICADO: 26/11/2026 16:15
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

Lacunas registradas no ADR-004 (projetos antigos não recebem ``dev``) e no
ADR-005 (projetos antigos mantêm ``.github/prompts/``). Decisões do dono do
projeto em 26/11/2026:

- ``dev`` só local, **sem checkout** (o usuário continua na branch em que
  estava) e sem mexer no GitHub; o resumo mostra como publicar;
- ``.github/prompts/`` inteiro vai para ``.github/prompts.bak-<AAAAMMDD-HHMMSS>``
  (horário de America/Sao_Paulo), sem comparar conteúdo.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from scripts.lib import git as git_mod
from scripts.lib import legacy_migrations

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GIT = shutil.which("git") or "git"
_SP = ZoneInfo("America/Sao_Paulo")
_AGORA = datetime(2026, 11, 26, 13, 55, 7, tzinfo=_SP)


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        [_GIT, *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo_antigo(make_project_config):
    """Projeto gerado antes do ADR-004: só ``main``, sem ``dev``."""
    cfg = make_project_config("programming", "python")
    cfg.project_path.mkdir(parents=True, exist_ok=True)
    assert git_mod.init_repository(cfg).status == "created"
    (cfg.project_path / "README.md").write_text("x\n", encoding="utf-8")
    assert git_mod.create_initial_commit(cfg).status == "created"
    return cfg


# ---------------------------------------------------------------------------
# Branch dev (sem checkout)
# ---------------------------------------------------------------------------


def test_cria_dev_a_partir_da_main_sem_trocar_de_branch(repo_antigo):
    path = repo_antigo.project_path
    _git(path, "checkout", "-q", "-b", "feat/em-andamento")

    item = git_mod.ensure_dev_branch(repo_antigo)

    assert item.status == "created"
    assert _git(path, "rev-parse", "dev") == _git(path, "rev-parse", "main")
    assert _git(path, "branch", "--show-current") == "feat/em-andamento"


def test_mensagem_explica_como_publicar(repo_antigo):
    item = git_mod.ensure_dev_branch(repo_antigo)

    assert "git push -u origin dev" in item.message
    assert "--default-branch dev" in item.message


def test_usa_master_quando_nao_ha_main(repo_antigo):
    path = repo_antigo.project_path
    _git(path, "branch", "-m", "main", "master")

    item = git_mod.ensure_dev_branch(repo_antigo)

    assert item.status == "created"
    assert _git(path, "rev-parse", "dev") == _git(path, "rev-parse", "master")
    assert "master" in item.message


def test_dev_existente_nao_e_tocada(repo_antigo):
    path = repo_antigo.project_path
    _git(path, "branch", "dev")
    (path / "b.txt").write_text("y\n", encoding="utf-8")
    _git(path, "add", "b.txt")
    _git(path, "commit", "-q", "-m", "avanca main")
    dev_antes = _git(path, "rev-parse", "dev")

    item = git_mod.ensure_dev_branch(repo_antigo)

    assert item.status == "skipped"
    assert _git(path, "rev-parse", "dev") == dev_antes


def test_sem_repositorio_e_skipped(make_project_config):
    cfg = make_project_config("programming", "python")
    cfg.project_path.mkdir(parents=True, exist_ok=True)

    assert git_mod.ensure_dev_branch(cfg).status == "skipped"


def test_sem_main_nem_master_e_skipped(make_project_config):
    cfg = make_project_config("programming", "python")
    cfg.project_path.mkdir(parents=True, exist_ok=True)
    assert git_mod.init_repository(cfg).status == "created"  # sem commit

    item = git_mod.ensure_dev_branch(cfg)

    assert item.status == "skipped"
    assert "main" in item.message


@pytest.mark.parametrize(
    "falha",
    [subprocess.TimeoutExpired(cmd="git", timeout=10), OSError("git sumiu")],
    ids=["timeout", "oserror"],
)
def test_falha_do_git_vira_error_sem_excecao(repo_antigo, monkeypatch, falha):
    def _explode(*_a, **_k):
        raise falha

    monkeypatch.setattr(git_mod.subprocess, "run", _explode)

    item = git_mod.ensure_dev_branch(repo_antigo)

    assert item.status == "error"
    assert item.message


def test_git_branch_com_erro_vira_error(repo_antigo):
    # nome inválido de ref força "git branch" a falhar: dev/ bloqueia dev
    path = repo_antigo.project_path
    _git(path, "branch", "dev/x")

    item = git_mod.ensure_dev_branch(repo_antigo)

    assert item.status == "error"


# ---------------------------------------------------------------------------
# .github/prompts/ → backup
# ---------------------------------------------------------------------------


def _prompts(cfg) -> Path:
    d = cfg.project_path / ".github" / "prompts"
    (d / "domain").mkdir(parents=True)
    (d / "session-start.prompt.md").write_text("antigo\n", encoding="utf-8")
    (d / "domain" / "devops-programming.prompt.md").write_text("d\n", "utf-8")
    (d / "meu-prompt.prompt.md").write_text("do usuário\n", encoding="utf-8")
    return d


def test_move_prompts_inteiro_para_backup(make_project_config):
    cfg = make_project_config("programming", "python")
    origem = _prompts(cfg)

    item = legacy_migrations.archive_legacy_prompts(cfg, now=_AGORA)

    destino = cfg.project_path / ".github" / "prompts.bak-20261126-135507"
    assert item.status == "updated"
    assert not origem.exists()
    assert (destino / "session-start.prompt.md").read_text("utf-8") == "antigo\n"
    assert (destino / "meu-prompt.prompt.md").read_text("utf-8") == "do usuário\n"
    assert (destino / "domain" / "devops-programming.prompt.md").is_file()
    assert "prompts.bak-20261126-135507" in item.message


def test_sem_prompts_e_skipped(make_project_config):
    cfg = make_project_config("programming", "python")
    cfg.project_path.mkdir(parents=True, exist_ok=True)

    item = legacy_migrations.archive_legacy_prompts(cfg, now=_AGORA)

    assert item.status == "skipped"


def test_backup_existente_ganha_sufixo(make_project_config):
    cfg = make_project_config("programming", "python")
    _prompts(cfg)
    ocupado = cfg.project_path / ".github" / "prompts.bak-20261126-135507"
    ocupado.mkdir()
    (ocupado / "x.md").write_text("não apagar\n", encoding="utf-8")

    item = legacy_migrations.archive_legacy_prompts(cfg, now=_AGORA)

    assert item.status == "updated"
    assert (ocupado / "x.md").read_text("utf-8") == "não apagar\n"
    assert (ocupado.parent / "prompts.bak-20261126-135507-1").is_dir()


def test_horario_padrao_e_de_sao_paulo(make_project_config, monkeypatch):
    cfg = make_project_config("programming", "python")
    _prompts(cfg)
    vistos: list[object] = []

    class _Relogio(datetime):
        @classmethod
        def now(cls, tz=None):  # type: ignore[override]
            vistos.append(tz)
            return _AGORA

    monkeypatch.setattr(legacy_migrations, "datetime", _Relogio)

    legacy_migrations.archive_legacy_prompts(cfg)

    assert vistos and str(vistos[0]) == "America/Sao_Paulo"


def test_falha_ao_mover_vira_error_e_preserva_prompts(make_project_config, monkeypatch):
    cfg = make_project_config("programming", "python")
    origem = _prompts(cfg)

    def _falha(*_a, **_k):
        raise PermissionError("sem permissão")

    monkeypatch.setattr(legacy_migrations.shutil, "move", _falha)

    item = legacy_migrations.archive_legacy_prompts(cfg, now=_AGORA)

    assert item.status == "error"
    assert "sem permissão" in item.message
    assert (origem / "session-start.prompt.md").is_file()


# ---------------------------------------------------------------------------
# Integração: scaffold.py --upgrade num projeto "antigo"
# ---------------------------------------------------------------------------


def _scaffold(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "SCAFFOLD_LOGS_DIR": str(cwd / "_logs"),
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_PROJECT_ROOT / "scripts" / "scaffold.py"), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=300,
    )


def test_upgrade_cria_dev_e_arquiva_prompts(tmp_path: Path) -> None:
    proc = _scaffold(
        "new", "--ci", "--name", "p-antigo", "--domain", "programming",
        "--language", "python", "--ai-assistant", "copilot",
        "--shared-dir", str(tmp_path / "_shared"), "--target-dir", str(tmp_path),
        cwd=tmp_path,
    )  # fmt: skip
    assert proc.returncode == 0, proc.stderr[-1500:]
    proj = tmp_path / "p-antigo"
    # simula projeto anterior aos ADR-004/005
    _git(proj, "checkout", "-q", "main")
    _git(proj, "branch", "-D", "dev")
    _git(proj, "checkout", "-q", "-b", "feat/x")
    legado = proj / ".github" / "prompts"
    legado.mkdir(parents=True)
    (legado / "session-start.prompt.md").write_text("antigo\n", encoding="utf-8")

    proc = _scaffold("--upgrade", "--ci", "--target-dir", str(proj), cwd=tmp_path)

    assert proc.returncode == 0, proc.stderr[-1500:]
    assert _git(proj, "rev-parse", "dev") == _git(proj, "rev-parse", "main")
    assert _git(proj, "branch", "--show-current") == "feat/x"
    assert not legado.exists()
    backups = list((proj / ".github").glob("prompts.bak-*"))
    assert len(backups) == 1
    assert (backups[0] / "session-start.prompt.md").is_file()
