# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_gitignore_ai_files.py
TITULO: .gitignore gerado — arquivos locais de IA ignorados, dados do projeto versionados
DATA: 09/11/2026 16:25
MODIFICADO: 09/11/2026 16:21
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

Bug de docs/planning/lembrete.md: "gitignore ignorar os arquivos gerados pelo copilot,
claude e speckit. exceção para os arquivos que contem dados do projeto."
Decisão (09/11/2026): .github/agents/ e .github/prompts/ continuam versionados.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib.project import _GITIGNORE  # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git não disponível")

IGNORED = [
    ".claude/settings.local.json",
    "CLAUDE.local.md",
    ".claude/todos/t.json",
    ".claude/projects/p.jsonl",
    "graphify-out/graph.json",
    ".specify/.cache/x",
]

VERSIONED = [
    "CLAUDE.md",
    ".claude/settings.json",
    ".claude/commands/session-start.md",
    ".claude/agents/a.md",
    ".claude/skills/s/SKILL.md",
    ".specify/memory/constitution.md",
    ".specify/templates/spec-template.md",
    ".specify/scripts/bash/common.sh",
    "specs/001-x/spec.md",
    ".github/copilot-instructions.md",
    ".github/instructions/python.instructions.md",
    ".github/agents/devops-expert.agent.md",
    ".github/prompts/speckit.plan.prompt.md",
    ".github/workflows/ci.yml",
    "objetivo.yaml",
    "CONTEXT.md",
]


@pytest.fixture(scope="module")
def repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("gi")
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    (path / ".gitignore").write_text(_GITIGNORE, encoding="utf-8")
    return path


def _ignored(repo: Path, rel: str) -> bool:
    result = subprocess.run(["git", "check-ignore", "-q", "--no-index", rel], cwd=repo)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"git check-ignore falhou para {rel}")
    return result.returncode == 0


@pytest.mark.parametrize("rel", IGNORED)
def test_arquivo_local_de_ia_e_ignorado(repo: Path, rel: str):
    assert _ignored(repo, rel), f"{rel} deveria ser ignorado"


@pytest.mark.parametrize("rel", VERSIONED)
def test_dado_do_projeto_e_versionado(repo: Path, rel: str):
    assert not _ignored(repo, rel), f"{rel} deveria ser versionado"
