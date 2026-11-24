# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_precommit_versoes_alinhadas.py
TITULO: Versões dos hooks de lint do pre-commit == versões travadas no uv.lock
DATA: 24/11/2026 13:40
MODIFICADO: 24/11/2026 13:24
VERSÃO: 1.0.0
DEPEND: pytest, pyyaml
STATUS: DEV

Problema: o hook do ruff estava fixado em v0.1.11 enquanto o projeto/CI usam o
ruff do uv.lock (0.16.5). As duas versões apontam achados diferentes (até a linha
do S603 mudava), então o pre-commit e o CI discordavam. Este teste trava o
alinhamento: quando o Dependabot atualizar o uv.lock, o teste acusa o hook velho.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent

# repo do hook → pacote no uv.lock
_HOOKS = {
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
    "https://github.com/psf/black": "black",
    "https://github.com/pycqa/bandit": "bandit",
}


def _versao_lock(pacote: str) -> str:
    lock = tomllib.loads((_ROOT / "uv.lock").read_text(encoding="utf-8"))
    versoes = {p["version"] for p in lock["package"] if p["name"] == pacote}
    assert len(versoes) == 1, f"{pacote}: versões no uv.lock = {versoes}"
    return versoes.pop()


def _rev_hook(repo: str) -> str:
    config = yaml.safe_load(
        (_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )
    revs = [r["rev"] for r in config["repos"] if r.get("repo") == repo]
    assert len(revs) == 1, f"hook {repo} ausente ou duplicado"
    return revs[0].removeprefix("v")


@pytest.mark.parametrize(("repo", "pacote"), sorted(_HOOKS.items()))
def test_hook_usa_a_versao_do_uv_lock(repo: str, pacote: str) -> None:
    assert _rev_hook(repo) == _versao_lock(pacote), (
        f"{pacote}: pre-commit em {_rev_hook(repo)}, uv.lock em {_versao_lock(pacote)} — "
        "alinhe o `rev` do hook em .pre-commit-config.yaml"
    )
