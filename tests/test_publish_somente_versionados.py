# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_publish_somente_versionados.py
TITULO: --publish empacota só arquivos versionados quando a raiz é um repo git
DATA: 24/11/2026 12:42
MODIFICADO: 26/11/2026 11:38
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

Problema (apontado em revisão): ``_collect_files`` selecionava por glob sobre o
disco, então arquivos locais não versionados (ex.: ``.claude/skills/rascunho``)
entravam no release. Em repo git, a seleção passa a ser limitada a
``git ls-files``; fora de repo (ex.: tarball extraído) ou sem git disponível,
mantém o glob.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib import publish  # noqa: E402

_GIT = shutil.which("git") or "git"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git indisponível")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(  # noqa: S603
        [_GIT, "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _arvore(root: Path) -> Path:
    for rel in (
        "scripts/scaffold.py",
        "scripts/lib/flows/x.py",
        "scaffold/templates/claude/skills/oficial/SKILL.md",
        "scaffold/templates/claude/skills/rascunho/SKILL.md",
        "scripts/lib/segredo_local.py",
    ):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text("x\n", encoding="utf-8")
    return root


def _rel(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in publish._collect_files(root)}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = _arvore(tmp_path / "repo")
    _git(root, "init", "-q")
    _git(
        root,
        "add",
        "scripts/scaffold.py",
        "scripts/lib/flows/x.py",
        "scaffold/templates/claude/skills/oficial/SKILL.md",
    )
    _git(root, "commit", "-q", "-m", "init")
    return root


def test_repo_git_inclui_versionados(repo: Path) -> None:
    rel = _rel(repo)
    assert {
        "scripts/scaffold.py",
        "scripts/lib/flows/x.py",
        "scaffold/templates/claude/skills/oficial/SKILL.md",
    } <= rel


def test_repo_git_exclui_nao_versionados(repo: Path) -> None:
    rel = _rel(repo)
    assert "scaffold/templates/claude/skills/rascunho/SKILL.md" not in rel
    assert "scripts/lib/segredo_local.py" not in rel


def test_staged_mas_nao_commitado_entra(repo: Path) -> None:
    """Arquivo adicionado ao índice é versionado (git ls-files o lista)."""
    _git(repo, "add", "scripts/lib/segredo_local.py")
    assert "scripts/lib/segredo_local.py" in _rel(repo)


def test_fora_de_repo_git_mantem_glob(tmp_path: Path) -> None:
    root = _arvore(tmp_path / "extraido")
    assert "scaffold/templates/claude/skills/rascunho/SKILL.md" in _rel(root)


def test_git_indisponivel_mantem_glob(repo: Path) -> None:
    with patch.object(publish.subprocess, "run", side_effect=FileNotFoundError("git")):
        assert "scaffold/templates/claude/skills/rascunho/SKILL.md" in _rel(repo)
