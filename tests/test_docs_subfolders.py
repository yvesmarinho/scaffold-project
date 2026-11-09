# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_docs_subfolders.py
TITULO: Sub-pastas padrão de docs/ no projeto gerado
DATA: 09/11/2026 17:10
MODIFICADO: 09/11/2026 17:07
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Melhoria de docs/planning/lembrete.md: "na pasta ./docs falta as sub-pastas
implementations e bugs".
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCAFFOLD = _PROJECT_ROOT / "scripts" / "scaffold.py"

EXPECTED = [
    "architecture",
    "bugs",
    "debates",
    "decisions",
    "guides",
    "implementations",
    "retrospectives",
    "templates",
]


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory) -> Path:
    target = tmp_path_factory.mktemp("docs-sub")
    result = subprocess.run(
        [sys.executable, str(_SCAFFOLD), "new", "--ci", "--name", "demo-docs",
         "--domain", "programming", "--language", "python", "--target-dir", str(target)],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr[-500:]
    projects = [p for p in target.rglob(".scaffold-state.yaml")]
    assert projects, "projeto não gerado"
    return projects[0].parent


@pytest.mark.parametrize("sub", EXPECTED)
def test_subpasta_existe_com_readme(generated: Path, sub: str):
    readme = generated / "docs" / sub / "README.md"
    assert readme.is_file(), f"docs/{sub}/README.md ausente"
    assert readme.read_text(encoding="utf-8").strip(), f"docs/{sub}/README.md vazio"


@pytest.mark.parametrize("sub", ["bugs", "implementations"])
def test_indice_de_docs_referencia_subpasta(generated: Path, sub: str):
    index = (generated / "docs" / "INDEX.md").read_text(encoding="utf-8")
    assert f"docs/{sub}/" in index
