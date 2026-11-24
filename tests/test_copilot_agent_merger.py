"""
Test Suite for CopilotAgentMerger

Valida merge inteligente de arquivos .github/agents/*.agent.md com:
- Parse de YAML frontmatter
- Comparação de versões
- Merge aditivo de arrays (handoffs, tools)
- Merge de seções markdown
- Preservação de customizações

Sprint 1 (P0 CRITICAL): 32 agents sem merge
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.lib.copilot_agent_merge import (
    CopilotAgentMerger,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def merger():
    """Instância do CopilotAgentMerger."""
    return CopilotAgentMerger()


@pytest.fixture
def temp_dir():
    """Diretório temporário para testes."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def sample_agent_v1():
    """Agent file v1.0.0 (simula arquivo existente no projeto)."""
    return """---
agentName: test-agent
description: Test agent for validation
version: 1.0.0
handoffs:
  - label: Test Handoff 1
    agent: agent1
    prompt: Do something
tools:
  - read_file
  - grep_search
---

## Role & Purpose

Test agent for validation purposes.

## Core Responsibilities

1. Responsibility 1
2. Responsibility 2

## Custom Section

This is a custom section added by the user.
"""


@pytest.fixture
def sample_agent_v1_2():
    """Agent file v1.2.0 (simula template atualizado)."""
    return """---
agentName: test-agent
description: Enhanced test agent with new features
version: 1.2.0
handoffs:
  - label: Test Handoff 1
    agent: agent1
    prompt: Do something
  - label: New Handoff
    agent: agent2
    prompt: Do something else
tools:
  - read_file
  - grep_search
  - semantic_search
  - file_search
---

## Role & Purpose

Enhanced test agent with improved capabilities.

## Core Responsibilities

1. Responsibility 1
2. Responsibility 2
3. New Responsibility 3

## Workflow

This is a new section added in v1.2.0

## Custom Section

This should be preserved from the existing file.
"""


@pytest.fixture
def sample_agent_no_version():
    """Agent file without version (simula alguns agents existentes)."""
    return """---
description: Agent without version field
name: NoVersion Agent
tools:
  - read_file
---

## Description

This agent does not have a version field.
"""


# =============================================================================
# Test: File Detection
# =============================================================================


def test_01_can_merge_detection(merger):
    """Test 01: Verifica detecção correta de arquivos .agent.md."""
    # Should detect
    assert merger.can_merge(Path(".github/agents/test.agent.md"))
    assert merger.can_merge(Path(".github/agents/session-manager.agent.md"))

    # Should NOT detect
    assert not merger.can_merge(Path(".github/prompts/test.prompt.md"))
    assert not merger.can_merge(Path("README.md"))
    assert not merger.can_merge(Path(".github/agents/test.txt"))
    assert not merger.can_merge(Path("agents/test.agent.md"))  # wrong parent


# =============================================================================
# Test: YAML Frontmatter Parsing
# =============================================================================


def test_02_parse_yaml_frontmatter(merger, sample_agent_v1):
    """Test 02: Parse YAML frontmatter corretamente."""
    fm, md = merger._parse_agent_file(sample_agent_v1)

    assert fm.agent_name == "test-agent"
    assert fm.version == "1.0.0"
    assert fm.description == "Test agent for validation"
    assert len(fm.handoffs) == 1
    assert fm.handoffs[0]["agent"] == "agent1"
    assert len(fm.tools) == 2
    assert "read_file" in fm.tools


def test_03_parse_markdown_sections(merger, sample_agent_v1):
    """Test 03: Parse seções markdown corretamente."""
    fm, md = merger._parse_agent_file(sample_agent_v1)

    assert "Role & Purpose" in md.sections
    assert "Core Responsibilities" in md.sections
    assert "Custom Section" in md.sections
    assert len(md.sections) == 3


# =============================================================================
# Test: Version Comparison
# =============================================================================


def test_04_version_comparison(merger):
    """Test 04: Comparação de versões semânticas."""
    assert merger._compare_versions("1.2.0", "1.0.0") > 0
    assert merger._compare_versions("1.0.0", "1.2.0") < 0
    assert merger._compare_versions("1.2.0", "1.2.0") == 0
    assert merger._compare_versions("2.0.0", "1.9.9") > 0
    assert merger._compare_versions("1.0.1", "1.0.0") > 0


# =============================================================================
# Test: Merge Decision Logic
# =============================================================================


def test_05_should_merge_version_update(merger, sample_agent_v1, sample_agent_v1_2):
    """Test 05: Decide merge quando há atualização de versão."""
    existing_fm, _ = merger._parse_agent_file(sample_agent_v1)
    template_fm, _ = merger._parse_agent_file(sample_agent_v1_2)

    decision = merger._should_merge(existing_fm, template_fm, "test.agent.md")

    assert decision.should_merge is True
    assert any("version" in change.lower() for change in decision.changes)
    assert any("1.0.0" in change and "1.2.0" in change for change in decision.changes)


def test_06_should_merge_new_handoffs(merger, sample_agent_v1, sample_agent_v1_2):
    """Test 06: Decide merge quando há novos handoffs."""
    existing_fm, _ = merger._parse_agent_file(sample_agent_v1)
    template_fm, _ = merger._parse_agent_file(sample_agent_v1_2)

    decision = merger._should_merge(existing_fm, template_fm, "test.agent.md")

    assert decision.should_merge is True
    assert any("handoff" in change.lower() for change in decision.changes)


def test_07_should_merge_new_tools(merger, sample_agent_v1, sample_agent_v1_2):
    """Test 07: Decide merge quando há novos tools."""
    existing_fm, _ = merger._parse_agent_file(sample_agent_v1)
    template_fm, _ = merger._parse_agent_file(sample_agent_v1_2)

    decision = merger._should_merge(existing_fm, template_fm, "test.agent.md")

    assert decision.should_merge is True
    assert any("tool" in change.lower() for change in decision.changes)


def test_08_should_skip_if_uptodate(merger, sample_agent_v1):
    """Test 08: Skip se arquivo já está atualizado."""
    fm, _ = merger._parse_agent_file(sample_agent_v1)

    # Mesmo arquivo como template
    decision = merger._should_merge(fm, fm, "test.agent.md")

    assert decision.should_merge is False
    assert "up-to-date" in decision.reason.lower()


# =============================================================================
# Test: Frontmatter Merge
# =============================================================================


def test_09_merge_frontmatter_version(merger, sample_agent_v1, sample_agent_v1_2):
    """Test 09: Merge frontmatter atualiza versão."""
    existing_fm, _ = merger._parse_agent_file(sample_agent_v1)
    template_fm, _ = merger._parse_agent_file(sample_agent_v1_2)

    merged = merger._merge_frontmatter(existing_fm, template_fm)

    assert merged["version"] == "1.2.0"  # Versão do template


def test_10_merge_frontmatter_handoffs_additive(
    merger, sample_agent_v1, sample_agent_v1_2
):
    """Test 10: Merge frontmatter adiciona novos handoffs (aditivo)."""
    existing_fm, _ = merger._parse_agent_file(sample_agent_v1)
    template_fm, _ = merger._parse_agent_file(sample_agent_v1_2)

    merged = merger._merge_frontmatter(existing_fm, template_fm)

    assert len(merged["handoffs"]) == 2  # 1 existing + 1 new
    agents = [h["agent"] for h in merged["handoffs"]]
    assert "agent1" in agents  # Existing
    assert "agent2" in agents  # New from template


def test_11_merge_frontmatter_tools_additive(
    merger, sample_agent_v1, sample_agent_v1_2
):
    """Test 11: Merge frontmatter adiciona novos tools (aditivo)."""
    existing_fm, _ = merger._parse_agent_file(sample_agent_v1)
    template_fm, _ = merger._parse_agent_file(sample_agent_v1_2)

    merged = merger._merge_frontmatter(existing_fm, template_fm)

    assert len(merged["tools"]) == 4  # 2 existing + 2 new
    assert "read_file" in merged["tools"]  # Existing
    assert "grep_search" in merged["tools"]  # Existing
    assert "semantic_search" in merged["tools"]  # New
    assert "file_search" in merged["tools"]  # New


# =============================================================================
# Test: Markdown Content Merge
# =============================================================================


def test_12_merge_markdown_preserves_custom_sections(
    merger, sample_agent_v1, sample_agent_v1_2
):
    """Test 12: Merge markdown preserva seções customizadas."""
    _, existing_md = merger._parse_agent_file(sample_agent_v1)
    _, template_md = merger._parse_agent_file(sample_agent_v1_2)

    merged_md = merger._merge_markdown_content(existing_md, template_md)

    assert "Custom Section" in merged_md.sections
    assert "user" in merged_md.sections["Custom Section"].lower()


def test_13_merge_markdown_adds_new_sections(
    merger, sample_agent_v1, sample_agent_v1_2
):
    """Test 13: Merge markdown adiciona novas seções do template."""
    _, existing_md = merger._parse_agent_file(sample_agent_v1)
    _, template_md = merger._parse_agent_file(sample_agent_v1_2)

    merged_md = merger._merge_markdown_content(existing_md, template_md)

    assert "Workflow" in merged_md.sections  # New section from template


def test_14_merge_markdown_updates_standard_sections(
    merger, sample_agent_v1, sample_agent_v1_2
):
    """Test 14: Merge markdown atualiza seções padrão."""
    _, existing_md = merger._parse_agent_file(sample_agent_v1)
    _, template_md = merger._parse_agent_file(sample_agent_v1_2)

    merged_md = merger._merge_markdown_content(existing_md, template_md)

    # Role & Purpose é seção padrão - deve ser atualizada do template
    assert "Enhanced" in merged_md.sections["Role & Purpose"]


# =============================================================================
# Test: Full Integration (End-to-End)
# =============================================================================


def test_15_full_merge_integration(
    merger, temp_dir, sample_agent_v1, sample_agent_v1_2
):
    """Test 15: Teste de integração completo do merge."""
    # Setup
    agents_dir = temp_dir / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    existing_file = agents_dir / "test.agent.md"
    existing_file.write_text(sample_agent_v1, encoding="utf-8")

    # Execute merge
    result = merger.merge(existing_file, sample_agent_v1_2, interactive=False)

    # Validate
    assert result.status == "merged"
    assert "backup" in result.message.lower()

    # Verify backup exists
    backup_file = existing_file.with_suffix(".md.backup")
    assert backup_file.exists()
    assert backup_file.read_text(encoding="utf-8") == sample_agent_v1

    # Verify merged content
    merged_content = existing_file.read_text(encoding="utf-8")
    assert "version: 1.2.0" in merged_content  # Updated version
    assert "agent2" in merged_content  # New handoff
    assert "semantic_search" in merged_content  # New tool
    assert "Custom Section" in merged_content  # Preserved custom


def test_16_add_version_to_versionless_agent(merger, temp_dir, sample_agent_no_version):
    """Test 16: Adiciona version a agent que não tinha."""
    # Setup
    agents_dir = temp_dir / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    existing_file = agents_dir / "noversion.agent.md"
    existing_file.write_text(sample_agent_no_version, encoding="utf-8")

    # Template com version
    template_with_version = """---
description: Agent now with version
name: NoVersion Agent
version: 1.0.0
tools:
  - read_file
  - grep_search
---

## Description

This agent now has a version field.
"""

    # Execute merge
    result = merger.merge(existing_file, template_with_version, interactive=False)

    # Validate
    assert result.status == "merged"
    merged_content = existing_file.read_text(encoding="utf-8")
    assert "version: 1.0.0" in merged_content  # Version added


# =============================================================================
# Test: Edge Cases
# =============================================================================


def test_17_merge_handles_malformed_yaml(merger, temp_dir):
    """Test 17: Merge lida com YAML malformado graciosamente."""
    # Setup
    agents_dir = temp_dir / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    existing_file = agents_dir / "malformed.agent.md"

    malformed = """---
agentName: broken
version: [this is: not: valid: yaml
---

## Content

Some content here.
"""

    existing_file.write_text(malformed, encoding="utf-8")

    # Template válido
    template = """---
agentName: fixed
version: 1.0.0
---

## Content

Fixed content.
"""

    # Execute merge (não deve crashear)
    result = merger.merge(existing_file, template, interactive=False)

    # Validate - pode dar erro ou skip, mas não deve crashear
    assert result.status in ["merged", "skipped", "error"]


def test_18_skip_if_no_changes_needed(merger, temp_dir, sample_agent_v1):
    """Test 18: Skip se não há mudanças necessárias."""
    # Setup
    agents_dir = temp_dir / ".github" / "agents"
    agents_dir.mkdir(parents=True)
    existing_file = agents_dir / "unchanged.agent.md"
    existing_file.write_text(sample_agent_v1, encoding="utf-8")

    # Template idêntico ao existente
    result = merger.merge(existing_file, sample_agent_v1, interactive=False)

    # Validate
    assert result.status == "skipped"
    assert "up-to-date" in result.message.lower()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
