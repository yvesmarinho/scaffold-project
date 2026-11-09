# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_quality_agents.py
TITULO: Agentes de verificação (scaffold-verifier, security-auditor, docs-structure-validator, adr-reviewer)
DATA: 09/11/2026 17:40
MODIFICADO: 09/11/2026 17:14
VERSÃO: 1.0.0
DEPEND: pytest, pyyaml
STATUS: DEV

Itens abertos de docs/planning/remenber.md ("Novos Agentes SpecKit identificados").
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_AGENTS_DIR = Path(__file__).resolve().parent.parent / "scaffold" / "templates" / "speckit" / "agents"

AGENTS = {
    "scaffold-verifier": ["docs/", ".secrets/", ".scaffold-state.yaml", "scaffold.py --upgrade"],
    "security-auditor": [".gitleaks.toml", "secrets_scan", "branch protection", ".secrets/"],
    "docs-structure-validator": ["docs/INDEX.md", "docs/bugs/", "docs/implementations/", "Criado em:"],
    "adr-reviewer": ["docs/decisions/", "Status", "Consequências", "Alternativas"],
}


def _split(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path.name}: frontmatter ausente"
    _, front, body = text.split("---\n", 2)
    data = yaml.safe_load(front)
    assert isinstance(data, dict), f"{path.name}: frontmatter inválido"
    return data, body


@pytest.mark.parametrize("name", AGENTS)
def test_agente_existe(name: str):
    assert (_AGENTS_DIR / f"{name}.agent.md").is_file()


@pytest.mark.parametrize("name", AGENTS)
def test_frontmatter_valido(name: str):
    data, _ = _split(_AGENTS_DIR / f"{name}.agent.md")
    assert str(data.get("name", "")).strip()
    assert len(str(data.get("description", ""))) >= 30
    tools = data.get("tools")
    assert isinstance(tools, list) and tools


@pytest.mark.parametrize("name", AGENTS)
def test_agente_e_somente_leitura(name: str):
    """Agentes de verificação reportam; não editam arquivos."""
    data, _ = _split(_AGENTS_DIR / f"{name}.agent.md")
    assert not any("edit" in str(t).lower() for t in data["tools"])


@pytest.mark.parametrize("name,terms", AGENTS.items())
def test_cobre_checagens_essenciais(name: str, terms: list[str]):
    _, body = _split(_AGENTS_DIR / f"{name}.agent.md")
    missing = [t for t in terms if t not in body]
    assert not missing, f"{name}: faltam {missing}"


@pytest.mark.parametrize("name", AGENTS)
def test_define_formato_de_relatorio(name: str):
    _, body = _split(_AGENTS_DIR / f"{name}.agent.md")
    assert "## Formato do relatório" in body
    assert "❌" in body and "✅" in body
