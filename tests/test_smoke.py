"""
tests/test_smoke.py — IMP-16: Smoke tests para todos os combos domínio × linguagem.

Cobertura: 9 combos × 2 funções = 18 smoke tests.
Cada teste verifica que a função produz:
  - status "created" (arquivo criado com sucesso)
  - conteúdo com > 200 chars (não vazio/truncado)
  - project_name substituído no conteúdo
  - nenhum placeholder não-resolvido ("{{" restante após .format())
  - presença do domínio e linguagem no conteúdo
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.templates import (  # noqa: E402
    generate_copilot_instructions,
    generate_copilot_rules,
)

# ---------------------------------------------------------------------------
# Combos domínio × linguagem (cobrem os 9 casos do backlog)
# ---------------------------------------------------------------------------
COMBOS: list[tuple[str, str]] = [
    ("programming", "python"),
    ("programming", "typescript"),
    ("programming", "go"),
    ("programming", "other"),
    ("infrastructure", "python"),
    ("infrastructure", "typescript"),
    ("infrastructure", "go"),
    ("analysis", "python"),
    ("analysis", "typescript"),
]

COMBO_IDS = [f"{d}__{lang}" for d, lang in COMBOS]


# ---------------------------------------------------------------------------
# Smoke: generate_copilot_rules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain,language", COMBOS, ids=COMBO_IDS)
def test_copilot_rules_smoke_created(
    make_project_config, domain: str, language: str
) -> None:
    """Arquivo .copilot-rules-*.md é criado com status 'created'."""
    cfg = make_project_config(domain, language)
    result = generate_copilot_rules(cfg)

    assert (
        result.status == "created"
    ), f"[{domain}×{language}] status={result.status!r}: {result.message}"


@pytest.mark.parametrize("domain,language", COMBOS, ids=COMBO_IDS)
def test_copilot_rules_smoke_content(
    make_project_config, domain: str, language: str
) -> None:
    """Conteúdo gerado tem placeholders resolvidos e informações corretas."""
    cfg = make_project_config(domain, language)
    result = generate_copilot_rules(cfg)
    content = result.path.read_text(encoding="utf-8")

    assert len(content) > 200, f"[{domain}×{language}] conteúdo suspeitosamente curto"
    assert (
        cfg.project_name in content
    ), f"[{domain}×{language}] project_name não substituído"
    assert (
        "{{" not in content
    ), f"[{domain}×{language}] placeholder não-resolvido encontrado no output"
    assert domain in content, f"[{domain}×{language}] domínio ausente no output"
    assert language in content, f"[{domain}×{language}] linguagem ausente no output"


@pytest.mark.parametrize("domain,language", COMBOS, ids=COMBO_IDS)
def test_copilot_rules_smoke_idempotent(
    make_project_config, domain: str, language: str
) -> None:
    """Segunda chamada retorna status 'skipped' (não sobrescreve)."""
    cfg = make_project_config(domain, language)
    generate_copilot_rules(cfg)  # primeira vez: cria
    result2 = generate_copilot_rules(cfg)  # segunda vez: skip

    assert (
        result2.status == "skipped"
    ), f"[{domain}×{language}] arquivo existente deveria ser pulado, got={result2.status!r}"


# ---------------------------------------------------------------------------
# Smoke: generate_copilot_instructions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("domain,language", COMBOS, ids=COMBO_IDS)
def test_copilot_instructions_smoke_created(
    make_project_config, domain: str, language: str
) -> None:
    """Arquivo copilot-instructions.md é criado com status 'created'."""
    cfg = make_project_config(domain, language)
    result = generate_copilot_instructions(cfg)

    assert (
        result.status == "created"
    ), f"[{domain}×{language}] status={result.status!r}: {result.message}"


@pytest.mark.parametrize("domain,language", COMBOS, ids=COMBO_IDS)
def test_copilot_instructions_smoke_content(
    make_project_config, domain: str, language: str
) -> None:
    """Conteúdo do copilot-instructions.md tem frontmatter e placeholders resolvidos."""
    cfg = make_project_config(domain, language)
    result = generate_copilot_instructions(cfg)
    content = result.path.read_text(encoding="utf-8")

    assert len(content) > 200, f"[{domain}×{language}] conteúdo suspeitosamente curto"
    assert cfg.project_name in content, f"[{domain}×{language}] project_name ausente"
    assert (
        "applyTo" in content
    ), f"[{domain}×{language}] YAML frontmatter 'applyTo' ausente"
    assert (
        "{{" not in content
    ), f"[{domain}×{language}] placeholder não-resolvido encontrado"


@pytest.mark.parametrize("domain,language", COMBOS, ids=COMBO_IDS)
def test_copilot_instructions_smoke_idempotent(
    make_project_config, domain: str, language: str
) -> None:
    """Segunda chamada retorna 'skipped'."""
    cfg = make_project_config(domain, language)
    generate_copilot_instructions(cfg)
    result2 = generate_copilot_instructions(cfg)

    assert (
        result2.status == "skipped"
    ), f"[{domain}×{language}] esperado 'skipped', got={result2.status!r}"
