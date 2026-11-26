# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_speckit_via_instalador.py
TITULO: Tudo do SpecKit vem do instalador oficial (`specify init`)
DATA: 26/11/2026 12:20
MODIFICADO: 26/11/2026 11:52
VERSÃO: 1.0.0
DEPEND: pytest, specify (só nos testes e2e)
STATUS: DEV

Decisão do usuário (26/11/2026, após a fatia 5 do ADR-003): os arquivos do
SpecKit nos projetos gerados vêm só de
``specify init --here --force --integration <IA>``, e não de cópias estáticas
em ``scaffold/templates/``. Assim, atualizar o SpecKit chega aos projetos novos e,
pelo upgrade, aos antigos.

Contrato coberto:
- ``ai_assistant=none`` usa a integração ``generic`` (comandos em ``.specify/commands/``);
- nenhuma cópia estática de ``speckit*`` em ``scaffold/templates/``;
- ``copy_claude_config`` só copia os comandos próprios do scaffold (``session-*``);
- ``generate_constitution`` lê o template **instalado no projeto** e preenche a
  constitution enquanto ela for idêntica ao template (o ``specify`` a cria sem
  preencher); constitution editada pelo usuário nunca é tocada;
- o upgrade roda o instalador: repõe o SpecKit e preserva constitution e specs.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib import project  # noqa: E402

_TEMPLATES = _PROJECT_ROOT / "scaffold" / "templates"
_CONSTITUTION_TPL = (
    "# [PROJECT_NAME] Constitution\n"
    "**Version**: [CONSTITUTION_VERSION] | **Ratified**: [RATIFICATION_DATE] | "
    "**Last Amended**: [LAST_AMENDED_DATE]\n"
)


def _ok_proc() -> MagicMock:
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "ok"
    proc.stderr = ""
    return proc


def _cfg(make_project_config, ai_assistant: str = "claude"):
    cfg = make_project_config("programming", "python")
    cfg.ai_assistant = ai_assistant
    cfg.project_path.mkdir(parents=True, exist_ok=True)
    return cfg


# --- run_speckit_init -------------------------------------------------------


def test_none_usa_integracao_generic(make_project_config) -> None:
    cfg = _cfg(make_project_config, "none")
    with patch.object(project.subprocess, "run", return_value=_ok_proc()) as run:
        results = project.run_speckit_init(cfg)

    run.assert_called_once()
    assert run.call_args[0][0] == [
        "specify",
        "init",
        "--here",
        "--force",
        "--integration",
        "generic",
        "--integration-options=--commands-dir .specify/commands/",
    ]
    assert [r.status for r in results] == ["created"]


# --- sem cópias estáticas do SpecKit -----------------------------------------


def test_templates_sem_copia_estatica_do_speckit() -> None:
    estaticos = [
        str(p.relative_to(_TEMPLATES))
        for p in (_TEMPLATES / "claude").rglob("*")
        if "speckit" in p.name
    ]
    assert not estaticos, f"cópias estáticas do SpecKit: {estaticos}"
    assert not (_TEMPLATES / "speckit" / "templates").exists()


def test_copy_claude_config_so_copia_comandos_do_scaffold(make_project_config) -> None:
    cfg = _cfg(make_project_config)
    results = project.copy_claude_config(cfg)

    copiados = {r.path.name for r in results if r.status == "created"}
    assert "session-start..md" in copiados
    assert not [n for n in copiados if "speckit" in n]
    assert not (cfg.project_path / ".claude" / "skills").exists()


# --- generate_constitution ----------------------------------------------------


def _instala_template(cfg) -> Path:
    tpl = cfg.project_path / ".specify" / "templates" / "constitution-template.md"
    tpl.parent.mkdir(parents=True, exist_ok=True)
    tpl.write_text(_CONSTITUTION_TPL, encoding="utf-8")
    return tpl


def test_constitution_igual_ao_template_e_preenchida(make_project_config) -> None:
    """O specify cria a constitution sem preencher; o scaffold a preenche."""
    cfg = _cfg(make_project_config)
    _instala_template(cfg)
    dst = cfg.project_path / ".specify" / "memory" / "constitution.md"
    dst.parent.mkdir(parents=True)
    dst.write_text(_CONSTITUTION_TPL, encoding="utf-8")

    item = project.generate_constitution(cfg)

    texto = dst.read_text(encoding="utf-8")
    assert item.status == "updated"
    assert "[PROJECT_NAME]" not in texto
    assert "# Test Project Constitution" in texto
    assert "[CONSTITUTION_VERSION]" not in texto


def test_constitution_ausente_e_criada_do_template_instalado(
    make_project_config,
) -> None:
    cfg = _cfg(make_project_config)
    _instala_template(cfg)

    item = project.generate_constitution(cfg)

    dst = cfg.project_path / ".specify" / "memory" / "constitution.md"
    assert item.status == "created"
    assert "# Test Project Constitution" in dst.read_text(encoding="utf-8")


def test_constitution_editada_pelo_usuario_nao_e_tocada(make_project_config) -> None:
    cfg = _cfg(make_project_config)
    _instala_template(cfg)
    dst = cfg.project_path / ".specify" / "memory" / "constitution.md"
    dst.parent.mkdir(parents=True)
    dst.write_text("# Minha constitution\n", encoding="utf-8")

    item = project.generate_constitution(cfg)

    assert item.status == "skipped"
    assert dst.read_text(encoding="utf-8") == "# Minha constitution\n"


def test_constitution_sem_template_instalado_e_erro(make_project_config) -> None:
    """Sem o specify (ou se ele falhou), não há fallback estático."""
    cfg = _cfg(make_project_config)

    item = project.generate_constitution(cfg)

    assert item.status == "error"
    assert "specify" in (item.message or "")


# --- e2e: criação e upgrade com o specify real --------------------------------

_SEM_SPECIFY = shutil.which("specify") is None


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


def _novo(tmp_path: Path, nome: str, ai: str) -> Path:
    proc = _scaffold(
        "new",
        "--ci",
        "--name",
        nome,
        "--domain",
        "programming",
        "--language",
        "python",
        "--ai-assistant",
        ai,
        "--shared-dir",
        str(tmp_path / "_shared"),
        "--target-dir",
        str(tmp_path),
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr[-1500:]
    return tmp_path / nome


@pytest.mark.skipif(_SEM_SPECIFY, reason="specify CLI não instalado")
def test_e2e_none_recebe_speckit_generic(tmp_path: Path) -> None:
    proj = _novo(tmp_path, "p-none", "none")

    assert (proj / ".specify" / "templates" / "spec-template.md").is_file()
    assert (proj / ".specify" / "commands" / "speckit.plan.md").is_file()
    constitution = (proj / ".specify" / "memory" / "constitution.md").read_text()
    assert "[PROJECT_NAME]" not in constitution


@pytest.mark.skipif(_SEM_SPECIFY, reason="specify CLI não instalado")
def test_e2e_claude_so_tem_speckit_do_instalador(tmp_path: Path) -> None:
    proj = _novo(tmp_path, "p-claude", "claude")

    comandos = sorted(p.name for p in (proj / ".claude" / "commands").glob("*"))
    assert not [c for c in comandos if c.startswith("speckit")], comandos
    assert (proj / ".claude" / "skills" / "speckit-plan" / "SKILL.md").is_file()
    constitution = (proj / ".specify" / "memory" / "constitution.md").read_text()
    assert "[PROJECT_NAME]" not in constitution


@pytest.mark.skipif(_SEM_SPECIFY, reason="specify CLI não instalado")
def test_e2e_upgrade_reaplica_instalador_e_preserva_dados(tmp_path: Path) -> None:
    proj = _novo(tmp_path, "p-up", "claude")
    (proj / ".specify" / "templates" / "spec-template.md").unlink()
    shutil.rmtree(proj / ".claude" / "skills" / "speckit-plan")
    constitution = proj / ".specify" / "memory" / "constitution.md"
    constitution.write_text("# Minha constitution\n", encoding="utf-8")
    spec = proj / "specs" / "001-x" / "spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("minha spec\n", encoding="utf-8")

    proc = _scaffold("--upgrade", "--ci", "--target-dir", str(proj), cwd=tmp_path)

    assert proc.returncode == 0, proc.stderr[-1500:]
    assert (proj / ".specify" / "templates" / "spec-template.md").is_file()
    assert (proj / ".claude" / "skills" / "speckit-plan" / "SKILL.md").is_file()
    assert constitution.read_text(encoding="utf-8") == "# Minha constitution\n"
    assert spec.read_text(encoding="utf-8") == "minha spec\n"
