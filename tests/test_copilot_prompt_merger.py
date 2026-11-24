"""
Tests for CopilotPromptMerger

Sprint 2 (P0 HIGH): Validar merge inteligente de 26 arquivos .prompt.md

Test strategy:
- Test file detection (.github/prompts/*.prompt.md)
- Test YAML frontmatter parsing
- Test markdown sections parsing
- Test merge decision logic
- Test frontmatter merge (mode, description, agent)
- Test markdown content merge (instructions vs custom)
- Test full integration with temp files
- Test edge cases (no frontmatter, malformed YAML)
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.lib.copilot_prompt_merge import (
    CopilotPromptMerger,
    PromptContent,
    PromptFrontmatter,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_prompt_v1():
    """Prompt básico versão 1 (existente)."""
    return """---
mode: agent
description: Basic session start workflow
---

## Pre-Execution Checks

Verify MCP servers are configured:
- memory
- sequential-thinking

## Workflow

1. Check configuration
2. Load context
3. Start session

## Custom Examples

This is a custom example added by the project.
It should be preserved during merge.
"""


@pytest.fixture
def sample_prompt_v2():
    """Prompt versão 2 com melhorias (template)."""
    return """---
mode: agent
description: Enhanced session start workflow with security checks
---

## Pre-Execution Checks

Verify MCP servers are configured:
- memory
- sequential-thinking
- security-scanner

## Workflow

1. Check configuration
2. Load context
3. Security scan
4. Start session

## Guidelines

Always follow these guidelines:
- Check for sensitive files
- Validate project structure
"""


@pytest.fixture
def merger():
    """Instância do merger para testes."""
    return CopilotPromptMerger()


# =============================================================================
# Test 01: File Detection
# =============================================================================


def test_01_can_merge_detects_prompt_files(merger, temp_dir):
    """Test 01: can_merge() detecta corretamente arquivos .prompt.md."""
    # Criar estrutura .github/prompts/
    prompts_dir = temp_dir / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)

    # Casos positivos
    valid_prompt = prompts_dir / "session-start.prompt.md"
    valid_prompt.touch()
    assert merger.can_merge(valid_prompt), "Should detect .prompt.md in prompts/"

    # Casos negativos
    wrong_ext = prompts_dir / "session-start.md"
    wrong_ext.touch()
    assert not merger.can_merge(wrong_ext), "Should reject non-.prompt.md"

    wrong_dir = temp_dir / "docs" / "session-start.prompt.md"
    wrong_dir.parent.mkdir(parents=True)
    wrong_dir.touch()
    assert not merger.can_merge(wrong_dir), "Should reject prompts outside .github/"


# =============================================================================
# Test 02-03: Parsing
# =============================================================================


def test_02_parse_yaml_frontmatter(merger, sample_prompt_v1):
    """Test 02: Parse YAML frontmatter corretamente."""
    fm, _ = merger._parse_prompt_file(sample_prompt_v1)

    assert isinstance(fm, PromptFrontmatter)
    assert fm.mode == "agent"
    assert fm.description == "Basic session start workflow"
    assert "mode: agent" in fm.raw_yaml


def test_03_parse_markdown_sections(merger, sample_prompt_v1):
    """Test 03: Parse seções markdown corretamente."""
    _, md = merger._parse_prompt_file(sample_prompt_v1)

    assert isinstance(md, PromptContent)
    assert "Pre-Execution Checks" in md.sections
    assert "Workflow" in md.sections
    assert "Custom Examples" in md.sections
    assert "memory" in md.sections["Pre-Execution Checks"]


# =============================================================================
# Test 04-06: Merge Decision Logic
# =============================================================================


def test_04_should_merge_detects_description_update(
    merger, sample_prompt_v1, sample_prompt_v2
):
    """Test 04: Detecta atualização de description."""
    existing_fm, existing_md = merger._parse_prompt_file(sample_prompt_v1)
    template_fm, template_md = merger._parse_prompt_file(sample_prompt_v2)

    decision = merger._should_merge(
        existing_fm, template_fm, existing_md, template_md, "session-start.prompt.md"
    )

    assert decision.should_merge, "Should merge when description enhanced"
    assert len(decision.changes) > 0
    # Pode ter "Update description" ou "Add new sections"
    change_text = " ".join(decision.changes)
    assert "description" in change_text.lower() or "section" in change_text.lower()


def test_05_should_merge_detects_new_sections(
    merger, sample_prompt_v1, sample_prompt_v2
):
    """Test 05: Detecta novas seções no template."""
    existing_fm, existing_md = merger._parse_prompt_file(sample_prompt_v1)
    template_fm, template_md = merger._parse_prompt_file(sample_prompt_v2)

    decision = merger._should_merge(
        existing_fm, template_fm, existing_md, template_md, "session-start.prompt.md"
    )

    assert decision.should_merge
    # Template tem seção "Guidelines" que não existe no existing
    assert any("section" in change.lower() for change in decision.changes)


def test_06_should_skip_if_already_updated(merger, sample_prompt_v2):
    """Test 06: Skip se já está atualizado."""
    template_fm, template_md = merger._parse_prompt_file(sample_prompt_v2)

    decision = merger._should_merge(
        template_fm,
        template_fm,  # Existing == Template
        template_md,
        template_md,
        "session-start.prompt.md",
    )

    assert not decision.should_merge
    assert "up-to-date" in decision.reason.lower()


# =============================================================================
# Test 07-08: Frontmatter Merge
# =============================================================================


def test_07_merge_frontmatter_updates_mode(merger, sample_prompt_v1):
    """Test 07: Merge frontmatter atualiza mode."""
    existing_fm, _ = merger._parse_prompt_file(sample_prompt_v1)

    template_yaml = """---
mode: workflow
description: Basic session start workflow
---
"""
    template_fm, _ = merger._parse_prompt_file(template_yaml)

    merged = merger._merge_frontmatter(existing_fm, template_fm)

    assert merged["mode"] == "workflow", "Should update mode from template"


def test_08_merge_frontmatter_preserves_agent(merger):
    """Test 08: Merge frontmatter preserva agent específico."""
    existing_yaml = """---
mode: agent
agent: session-manager
---
"""
    template_yaml = """---
mode: agent
agent: generic-agent
---
"""

    existing_fm, _ = merger._parse_prompt_file(existing_yaml)
    template_fm, _ = merger._parse_prompt_file(template_yaml)

    merged = merger._merge_frontmatter(existing_fm, template_fm)

    # Agent should be preserved (project-specific reference)
    assert merged["agent"] == "session-manager", "Should preserve existing agent"


# =============================================================================
# Test 09-11: Markdown Content Merge
# =============================================================================


def test_09_merge_markdown_preserves_custom_sections(
    merger, sample_prompt_v1, sample_prompt_v2
):
    """Test 09: Merge preserva seções customizadas."""
    existing_fm, existing_md = merger._parse_prompt_file(sample_prompt_v1)
    template_fm, template_md = merger._parse_prompt_file(sample_prompt_v2)

    merged_md = merger._merge_markdown_content(existing_md, template_md)

    # Seção "Custom Examples" deve ser preservada
    assert "Custom Examples" in merged_md.sections
    assert "custom example" in merged_md.sections["Custom Examples"].lower()


def test_10_merge_markdown_adds_new_sections(
    merger, sample_prompt_v1, sample_prompt_v2
):
    """Test 10: Merge adiciona novas seções ausentes."""
    existing_fm, existing_md = merger._parse_prompt_file(sample_prompt_v1)
    template_fm, template_md = merger._parse_prompt_file(sample_prompt_v2)

    merged_md = merger._merge_markdown_content(existing_md, template_md)

    # Seção "Guidelines" não existe em v1, deve ser adicionada
    assert "Guidelines" in merged_md.sections
    assert "guidelines" in merged_md.sections["Guidelines"].lower()


def test_11_merge_markdown_updates_instructions(
    merger, sample_prompt_v1, sample_prompt_v2
):
    """Test 11: Merge atualiza seções de instruções."""
    existing_fm, existing_md = merger._parse_prompt_file(sample_prompt_v1)
    template_fm, template_md = merger._parse_prompt_file(sample_prompt_v2)

    merged_md = merger._merge_markdown_content(existing_md, template_md)

    # Workflow é instrução padrão - deve ser atualizada com conteúdo do template
    assert "Workflow" in merged_md.sections
    # Template tem 4 passos, existing tem 3
    workflow_content = merged_md.sections["Workflow"]
    assert "4." in workflow_content, "Should update workflow from template"


# =============================================================================
# Test 12-14: Full Integration
# =============================================================================


def test_12_full_merge_creates_backup(
    merger, temp_dir, sample_prompt_v1, sample_prompt_v2
):
    """Test 12: Merge completo cria backup do arquivo original."""
    # Setup
    prompts_dir = temp_dir / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)

    existing_path = prompts_dir / "session-start.prompt.md"
    existing_path.write_text(sample_prompt_v1, encoding="utf-8")

    # Execute merge
    result = merger.merge(existing_path, sample_prompt_v2, interactive=False)

    # Validar
    assert result.status == "merged"
    backup_path = existing_path.with_suffix(".md.backup")
    assert backup_path.exists(), "Should create backup"
    assert backup_path.read_text(encoding="utf-8") == sample_prompt_v1


def test_13_full_merge_generates_valid_prompt(
    merger, temp_dir, sample_prompt_v1, sample_prompt_v2
):
    """Test 13: Merge gera prompt válido com frontmatter + conteúdo."""
    # Setup
    prompts_dir = temp_dir / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)

    existing_path = prompts_dir / "session-start.prompt.md"
    existing_path.write_text(sample_prompt_v1, encoding="utf-8")

    # Execute merge
    merger.merge(existing_path, sample_prompt_v2, interactive=False)

    # Validar arquivo mesclado
    merged_content = existing_path.read_text(encoding="utf-8")
    assert merged_content.startswith("---\n"), "Should have YAML frontmatter"
    assert "mode:" in merged_content
    assert "## Workflow" in merged_content or "### Workflow" in merged_content
    assert "Custom Examples" in merged_content, "Should preserve custom sections"


def test_14_handles_prompt_without_frontmatter(merger, temp_dir):
    """Test 14: Handle prompts sem frontmatter YAML."""
    prompt_no_fm = """## Instructions

This is a simple prompt without frontmatter.

## Examples

Some examples here.
"""

    prompts_dir = temp_dir / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)

    existing_path = prompts_dir / "simple.prompt.md"
    existing_path.write_text(prompt_no_fm, encoding="utf-8")

    template = """---
mode: agent
---

## Instructions

Updated instructions.
"""

    # Não deve crashar
    result = merger.merge(existing_path, template, interactive=False)

    # Pode ser merged ou skipped, mas não deve dar error
    assert result.status in ["merged", "skipped"]


# =============================================================================
# Test 15-16: Edge Cases
# =============================================================================


def test_15_handles_malformed_yaml(merger):
    """Test 15: Handle YAML malformado gracefully."""
    malformed = """---
mode: agent
description: "unclosed quote
---

## Content

Some content.
"""

    # Não deve crashar
    fm, md = merger._parse_prompt_file(malformed)

    # Deve retornar frontmatter vazio
    assert fm.parsed == {}


def test_16_skip_when_no_changes_needed(merger, temp_dir, sample_prompt_v2):
    """Test 16: Skip quando não há mudanças necessárias."""
    prompts_dir = temp_dir / ".github" / "prompts"
    prompts_dir.mkdir(parents=True)

    # Existing já é igual ao template
    existing_path = prompts_dir / "session-start.prompt.md"
    existing_path.write_text(sample_prompt_v2, encoding="utf-8")

    result = merger.merge(existing_path, sample_prompt_v2, interactive=False)

    assert result.status == "skipped"
    assert "up-to-date" in result.message.lower()
