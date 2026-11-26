# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_publish_conteudo.py
TITULO: O tarball do --publish leva só o gerador e as dependências
DATA: 26/11/2026 12:40
MODIFICADO: 26/11/2026 12:13
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

ADR-003 fatia 6 (escopo decidido pelo dono do projeto em 26/11/2026): o release
contém os arquivos versionados de ``scripts/`` e ``scaffold/``, mais
``pyproject.toml``, ``uv.lock`` e ``README.md`` (para instalar ``rich``/``pyyaml``
com ``uv``). O que é só do desenvolvimento do scaffold (tests, Makefile,
pytest.ini, CHANGELOG, workflows, prompts) e ``scripts/tmp/`` ficam de fora.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib.publish import _collect_files  # noqa: E402

_PERMITIDOS_DIR = ("scripts/", "scaffold/")
_PERMITIDOS_ARQ = {"pyproject.toml", "uv.lock", "README.md"}


def _rel() -> set[str]:
    return {
        p.relative_to(_PROJECT_ROOT).as_posix() for p in _collect_files(_PROJECT_ROOT)
    }


def test_so_entra_gerador_e_dependencias() -> None:
    fora = sorted(
        r
        for r in _rel()
        if not r.startswith(_PERMITIDOS_DIR) and r not in _PERMITIDOS_ARQ
    )
    assert not fora, f"fora do escopo do release: {fora[:20]}"


def test_inclui_declaracao_de_dependencias() -> None:
    assert _PERMITIDOS_ARQ <= _rel()


def test_nao_inclui_scripts_tmp() -> None:
    assert not [r for r in _rel() if r.startswith("scripts/tmp/")]


def test_inclui_scaffold_recursivo() -> None:
    """scaffold/ inteiro (versionado), não só profiles/*.yaml e templates/."""
    rel = _rel()
    assert "scaffold/setup/README.md" in rel
    assert "scaffold/templates/runtime/scripts/session-manager.py" in rel
