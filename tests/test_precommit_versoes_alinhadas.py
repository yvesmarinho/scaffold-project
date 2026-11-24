# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_precommit_versoes_alinhadas.py
TITULO: Hooks de lint do pre-commit rodam a versão do uv.lock (via `uv run`)
DATA: 24/11/2026 13:24
MODIFICADO: 24/11/2026 15:00
VERSÃO: 2.0.0
DEPEND: pytest, pyyaml
STATUS: DEV

Histórico:
- 1.0.0 (24/11/2026 13:40): exigia `rev` do hook == versão do uv.lock (PR #59).
  Efeito colateral: todo PR do Dependabot que subisse ruff/black/bandit no
  uv.lock ficava bloqueado até alguém editar o .pre-commit-config.yaml à mão.
- 2.0.0 (24/11/2026 14:10): elimina a duplicação em vez de vigiá-la — ruff,
  black e bandit viram hooks `repo: local` executados por `uv run`, então a
  única fonte da versão é o uv.lock (mesma do CI).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_FERRAMENTAS = ("ruff", "black", "bandit")
_REPOS_REMOTOS = (
    "https://github.com/astral-sh/ruff-pre-commit",
    "https://github.com/psf/black",
    "https://github.com/pycqa/bandit",
)


def _config() -> dict:
    return yaml.safe_load(
        (_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    )


def _hooks_locais() -> dict[str, dict]:
    return {
        hook["id"]: hook
        for repo in _config()["repos"]
        if repo.get("repo") == "local"
        for hook in repo["hooks"]
    }


def test_sem_repos_remotos_com_versao_propria() -> None:
    repos = {r.get("repo") for r in _config()["repos"]}
    assert not repos & set(_REPOS_REMOTOS), (
        "ruff/black/bandit não devem fixar versão própria no pre-commit — use hook local "
        "com `uv run` (versão vem do uv.lock)"
    )


@pytest.mark.parametrize("ferramenta", _FERRAMENTAS)
def test_hook_local_roda_via_uv(ferramenta: str) -> None:
    hook = _hooks_locais().get(ferramenta)
    assert hook is not None, f"hook local '{ferramenta}' ausente"
    assert hook["language"] == "system"
    partes = hook["entry"].split()
    # "uv run [--extra X] <ferramenta> ..." — versão vem do uv.lock
    assert partes[:2] == ["uv", "run"] and ferramenta in partes, hook["entry"]
    assert "python" in hook.get("types", []), "hook deve rodar só em arquivos Python"


def test_ferramentas_declaradas_no_pyproject() -> None:
    """`uv run <ferramenta>` precisa que ela esteja nas dependências do projeto."""
    import tomllib

    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    extras = pyproject["project"].get("optional-dependencies", {})
    declaradas = " ".join(dep for grupo in extras.values() for dep in grupo)
    for ferramenta in _FERRAMENTAS:
        assert (
            ferramenta in declaradas
        ), f"{ferramenta} fora de [project.optional-dependencies]"
