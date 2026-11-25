"""
Testes — ADR-003 fatia 4: scripts de uso duplo em ``scaffold/templates/runtime/``.

Fonte única: o arquivo real fica em ``scaffold/templates/runtime/scripts/<rel>``;
o repositório usa ``scripts/<rel>`` como **symlink relativo** para ele (sem
duplicar conteúdo). O projeto gerado recebe **cópia real** (não symlink), com
os mesmos bytes e, nos executáveis, permissão de execução.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lib import project
from scripts.lib.project import RUNTIME_FILES, RUNTIME_SCRIPTS_DIR

_ROOT = Path(__file__).resolve().parent.parent
_SCAFFOLD_PY = _ROOT / "scripts" / "scaffold.py"


def test_conjunto_runtime_esperado():
    expected = {
        "lib/__init__.py",
        "lib/memory.py",
        "lib/git_validators.py",
        "lib/sanitize.py",
        "lib/session_context.py",
        "lib/session_security.py",
        "lib/git_session.py",
        "lib/session_workflow.py",
        "session-manager.py",
        "session-time-tracker.py",
        "create_memory_structure.py",
        "mem_context.py",
        "mem_search.py",
        "mem_save.py",
        "test_memory_smoke.py",
        "activate-mcp.sh",
        "git-commit-with-file.sh",
        "cleanup-tmp.sh",
        "validate-docs-links.sh",
        "git-hooks/commit-msg",
        "setup-branch-protection.py",
    }
    assert set(RUNTIME_FILES) == expected
    assert len(RUNTIME_FILES) == len(set(RUNTIME_FILES)), "duplicados"


def test_runtime_dir_dentro_de_scaffold_templates():
    assert (
        RUNTIME_SCRIPTS_DIR == _ROOT / "scaffold" / "templates" / "runtime" / "scripts"
    )


@pytest.mark.parametrize("rel", sorted(RUNTIME_FILES))
def test_fonte_real_existe_no_runtime(rel):
    src = RUNTIME_SCRIPTS_DIR / rel
    assert src.is_file() and not src.is_symlink(), rel


@pytest.mark.parametrize("rel", sorted(RUNTIME_FILES))
def test_repositorio_usa_symlink_relativo_para_o_runtime(rel):
    link = _ROOT / "scripts" / rel
    assert link.is_symlink(), f"scripts/{rel} deveria ser symlink"
    target = os.readlink(link)
    assert not os.path.isabs(target), f"scripts/{rel}: symlink absoluto quebra no clone"
    assert link.resolve() == (RUNTIME_SCRIPTS_DIR / rel).resolve()


def test_sem_orfaos_no_runtime():
    on_disk = {
        p.relative_to(RUNTIME_SCRIPTS_DIR).as_posix()
        for p in RUNTIME_SCRIPTS_DIR.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    assert on_disk == set(RUNTIME_FILES)


@pytest.mark.parametrize("rel", sorted(RUNTIME_FILES))
def test_executaveis_preservam_bit_x(rel):
    src = RUNTIME_SCRIPTS_DIR / rel
    if rel.endswith(".sh") or rel == "git-hooks/commit-msg":
        assert src.stat().st_mode & stat.S_IXUSR, rel


def test_runtime_dir_ausente_gera_erro_nomeado(monkeypatch, make_project_config):
    """Fonte indisponível: a cópia vira item 'error' com o caminho — não exceção crua."""
    monkeypatch.setattr(project, "RUNTIME_SCRIPTS_DIR", Path("/nao/existe/runtime"))
    cfg = make_project_config("programming", "python")
    items = project.copy_session_scripts(cfg)
    assert items and all(i.status == "error" for i in items)
    assert all("/nao/existe/runtime" in i.message for i in items)


# ---------------------------------------------------------------------------
# Projeto gerado
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def projeto(tmp_path_factory) -> Path:
    tmp = tmp_path_factory.mktemp("rt")
    shared = tmp / "shared"
    shared.mkdir()
    target = tmp / "proj"
    result = subprocess.run(
        [
            sys.executable,
            str(_SCAFFOLD_PY),
            "--new",
            "--ci",
            "--no-log",
            "--name",
            "proj",
            "--domain",
            "programming",
            "--language",
            "python",
            "--ai-assistant",
            "both",
            "--repo",
            "https://github.com/org/proj",
            "--no-github-setup",
            "--shared-dir",
            str(shared),
            "--target-dir",
            str(target),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    return target


@pytest.mark.integration
@pytest.mark.parametrize("rel", sorted(RUNTIME_FILES))
def test_projeto_recebe_copia_real_identica(projeto, rel):
    dst = projeto / "scripts" / rel
    assert dst.is_file() and not dst.is_symlink(), rel
    assert dst.read_bytes() == (RUNTIME_SCRIPTS_DIR / rel).read_bytes(), rel


@pytest.mark.integration
def test_scripts_de_sessao_rodam_no_projeto_gerado(projeto):
    result = subprocess.run(
        [sys.executable, "scripts/session-manager.py", "--help"],
        cwd=projeto,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-1500:]


def test_scripts_de_sessao_rodam_no_repositorio_via_symlink():
    result = subprocess.run(
        [sys.executable, "scripts/session-manager.py", "--help"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr[-1500:]


# ---------------------------------------------------------------------------
# publish: symlink do repo + alvo real no runtime (bug encontrado na fatia 4)
# ---------------------------------------------------------------------------


def test_publish_inclui_symlink_e_alvo_real(tmp_path):
    """_collect_files deduplicava pelo caminho resolvido: o symlink em scripts/
    entrava e o arquivo real em scaffold/templates/runtime/ era descartado."""
    from scripts.lib import publish

    rt = tmp_path / "scaffold" / "templates" / "runtime" / "scripts"
    rt.mkdir(parents=True)
    (rt / "session-manager.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "session-manager.py").symlink_to(
        "../scaffold/templates/runtime/scripts/session-manager.py"
    )

    rels = {
        p.relative_to(tmp_path).as_posix() for p in publish._collect_files(tmp_path)
    }

    assert "scripts/session-manager.py" in rels
    assert "scaffold/templates/runtime/scripts/session-manager.py" in rels
