"""
Tests for CopilotRulesMerger

Sprint 2 (P0 HIGH): Validar merge inteligente de arquivos .copilot-rules*.md

Test strategy:
- Test file detection (.copilot-rules*.md)
- Test markdown sections parsing
- Test priority detection (P0, P1, P2)
- Test merge decision logic
- Test P0 rules merge (always add/update)
- Test P1/P2 rules merge (additive)
- Test full integration with temp files
- Test edge cases (no priority markers, custom sections)
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.lib.copilot_rules_merge import (
    CopilotRulesMerger,
    RulesContent,
    RuleSection,
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
def sample_rules_v1():
    """Rules básico versão 1 (existente)."""
    return """# GitHub Copilot — Regras Comportamentais

**Status:** ATIVO — Aplicar em todas as sessões
**Última atualização:** 2026-03-01

---

## 1. Ferramentas de Arquivo (P0 — CRÍTICO)

### ❌ PROIBIDO — Nunca criar arquivos via terminal:

```bash
cat > arquivo.txt << 'EOF'   # ❌ heredoc
EOF
```

### ✅ OBRIGATÓRIO — Use ferramentas nativas:

- `create_file` para criar
- `replace_string_in_file` para editar

---

## 2. Git (P1)

Use `git-commit-with-file.sh` para commits com mensagens longas.

---

## 3. Custom Project Rules

This is a custom rule specific to this project.
Should be preserved during merge.
"""


@pytest.fixture
def sample_rules_v2():
    """Rules versão 2 com novas regras P0 (template)."""
    return """# GitHub Copilot — Regras Comportamentais

**Status:** ATIVO — Aplicar em todas as sessões
**Última atualização:** 2026-05-01

---

## 1. Ferramentas de Arquivo (P0 — CRÍTICO)

### ❌ PROIBIDO — Nunca criar arquivos via terminal:

```bash
cat > arquivo.txt << 'EOF'   # ❌ heredoc
echo "texto" > arquivo.txt    # ❌ echo redirect
EOF
```

### ✅ OBRIGATÓRIO — Use ferramentas nativas:

- `create_file` para criar
- `replace_string_in_file` para editar
- `multi_replace_string_in_file` para múltiplas edições

---

## 2. Ferramentas Nativas VS Code (P0 — CRÍTICO)

### ❌ PROIBIDO — Nunca usar CLI para ler arquivos:

- `cat arquivo` → use `read_file`
- `grep -r "texto"` → use `grep_search`

---

## 3. Git (P1)

Use `git-commit-with-file.sh` para commits com mensagens longas.

Formato da mensagem:
- Linha 1: título (50 chars)
- Linha 3+: corpo detalhado

---

## 4. Documentação (P2)

Mantenha README.md atualizado.
"""


@pytest.fixture
def merger():
    """Instância do merger para testes."""
    return CopilotRulesMerger()


# =============================================================================
# Test 01: File Detection
# =============================================================================


def test_01_can_merge_detects_rules_files(merger, temp_dir):
    """Test 01: can_merge() detecta corretamente arquivos .copilot-rules*.md."""
    # Casos positivos
    valid_generic = temp_dir / ".copilot-rules.md"
    valid_generic.touch()
    assert merger.can_merge(valid_generic), "Should detect .copilot-rules.md"

    valid_project = temp_dir / ".copilot-rules-myproject.md"
    valid_project.touch()
    assert merger.can_merge(valid_project), "Should detect .copilot-rules-*.md"

    # Casos negativos
    wrong_name = temp_dir / "copilot-rules.md"
    wrong_name.touch()
    assert not merger.can_merge(wrong_name), "Should reject without leading dot"

    wrong_ext = temp_dir / ".copilot-rules.txt"
    wrong_ext.touch()
    assert not merger.can_merge(wrong_ext), "Should reject non-.md"


# =============================================================================
# Test 02-04: Parsing and Priority Detection
# =============================================================================


def test_02_parse_rules_file_extracts_header(merger, sample_rules_v1):
    """Test 02: Parse extrai header corretamente."""
    rules = merger._parse_rules_file(sample_rules_v1)

    assert isinstance(rules, RulesContent)
    assert "GitHub Copilot" in rules.header
    assert "ATIVO" in rules.header


def test_03_parse_rules_file_extracts_sections(merger, sample_rules_v1):
    """Test 03: Parse extrai seções corretamente."""
    rules = merger._parse_rules_file(sample_rules_v1)

    assert len(rules.sections) == 3
    assert "1. Ferramentas de Arquivo (P0 — CRÍTICO)" in rules.sections
    assert "2. Git (P1)" in rules.sections
    assert "3. Custom Project Rules" in rules.sections


def test_04_detect_priority_in_sections(merger, sample_rules_v1):
    """Test 04: Detecta prioridade (P0, P1, P2) corretamente."""
    rules = merger._parse_rules_file(sample_rules_v1)

    # Verificar prioridades detectadas
    for _heading, section in rules.sections.items():
        assert isinstance(section, RuleSection)
        assert section.priority in ["P0", "P1", "P2"]

    # Ferramentas de Arquivo deve ser P0
    file_tools = rules.sections["1. Ferramentas de Arquivo (P0 — CRÍTICO)"]
    assert file_tools.priority == "P0"

    # Git deve ser P1
    git_section = rules.sections["2. Git (P1)"]
    assert git_section.priority == "P1"

    # Custom sem marcador explícito deve ser P2 (default)
    custom = rules.sections["3. Custom Project Rules"]
    assert custom.priority == "P2"


# =============================================================================
# Test 05-07: Merge Decision Logic
# =============================================================================


def test_05_should_merge_detects_new_p0_rules(merger, sample_rules_v1, sample_rules_v2):
    """Test 05: Detecta novas regras P0 (CRITICAL)."""
    existing_rules = merger._parse_rules_file(sample_rules_v1)
    template_rules = merger._parse_rules_file(sample_rules_v2)

    decision = merger._should_merge(existing_rules, template_rules, ".copilot-rules.md")

    assert decision.should_merge
    # Template tem nova seção P0: "Ferramentas Nativas VS Code"
    assert any("P0" in change or "CRITICAL" in change for change in decision.changes)


def test_06_should_merge_detects_critical_updates(
    merger, sample_rules_v1, sample_rules_v2
):
    """Test 06: Detecta atualizações em seções críticas."""
    existing_rules = merger._parse_rules_file(sample_rules_v1)
    template_rules = merger._parse_rules_file(sample_rules_v2)

    decision = merger._should_merge(existing_rules, template_rules, ".copilot-rules.md")

    assert decision.should_merge
    # "Ferramentas de Arquivo" foi atualizada (echo redirect adicionado)
    assert len(decision.changes) > 0


def test_07_should_skip_if_already_updated(merger, sample_rules_v2):
    """Test 07: Skip se já está atualizado."""
    template_rules = merger._parse_rules_file(sample_rules_v2)

    decision = merger._should_merge(
        template_rules, template_rules, ".copilot-rules.md"  # Existing == Template
    )

    assert not decision.should_merge
    assert "up-to-date" in decision.reason.lower()


# =============================================================================
# Test 08-10: Rules Content Merge
# =============================================================================


def test_08_merge_always_adds_p0_rules(merger, sample_rules_v1, sample_rules_v2):
    """Test 08: Merge sempre adiciona/atualiza regras P0."""
    existing_rules = merger._parse_rules_file(sample_rules_v1)
    template_rules = merger._parse_rules_file(sample_rules_v2)

    merged = merger._merge_rules_content(existing_rules, template_rules)

    # Nova seção P0 "Ferramentas Nativas VS Code" deve ser adicionada
    assert any(
        "Ferramentas Nativas VS Code" in heading for heading in merged.sections.keys()
    )

    # Seção P0 existente "Ferramentas de Arquivo" deve ser atualizada
    file_tools_heading = "1. Ferramentas de Arquivo (P0 — CRÍTICO)"
    assert file_tools_heading in merged.sections
    # Conteúdo deve ser do template (atualizado)
    assert "echo redirect" in merged.sections[file_tools_heading].content.lower()


def test_09_merge_adds_p1_rules_if_absent(merger, sample_rules_v1, sample_rules_v2):
    """Test 09: Merge adiciona regras P1 se ausentes."""
    existing_rules = merger._parse_rules_file(sample_rules_v1)
    template_rules = merger._parse_rules_file(sample_rules_v2)

    merged = merger._merge_rules_content(existing_rules, template_rules)

    # Git (P1) existe em ambos - pode ser atualizada ou preservada
    assert any("Git" in heading for heading in merged.sections.keys())


def test_10_merge_preserves_custom_sections(merger, sample_rules_v1, sample_rules_v2):
    """Test 10: Merge preserva seções customizadas do projeto."""
    existing_rules = merger._parse_rules_file(sample_rules_v1)
    template_rules = merger._parse_rules_file(sample_rules_v2)

    merged = merger._merge_rules_content(existing_rules, template_rules)

    # Seção "Custom Project Rules" deve ser preservada
    assert any("Custom Project Rules" in heading for heading in merged.sections.keys())

    # Conteúdo deve ser do existing (preservado)
    custom_heading = "3. Custom Project Rules"
    if custom_heading in merged.sections:
        assert "specific to this project" in merged.sections[custom_heading].content


# =============================================================================
# Test 11-13: Full Integration
# =============================================================================


def test_11_full_merge_creates_backup(
    merger, temp_dir, sample_rules_v1, sample_rules_v2
):
    """Test 11: Merge completo cria backup do arquivo original."""
    existing_path = temp_dir / ".copilot-rules.md"
    existing_path.write_text(sample_rules_v1, encoding="utf-8")

    result = merger.merge(existing_path, sample_rules_v2, interactive=False)

    assert result.status == "merged"
    backup_path = existing_path.with_suffix(".md.backup")
    assert backup_path.exists(), "Should create backup"
    assert backup_path.read_text(encoding="utf-8") == sample_rules_v1


def test_12_full_merge_generates_valid_rules(
    merger, temp_dir, sample_rules_v1, sample_rules_v2
):
    """Test 12: Merge gera rules válido com header + seções."""
    existing_path = temp_dir / ".copilot-rules.md"
    existing_path.write_text(sample_rules_v1, encoding="utf-8")

    merger.merge(existing_path, sample_rules_v2, interactive=False)

    # Validar arquivo mesclado
    merged_content = existing_path.read_text(encoding="utf-8")
    assert merged_content.startswith("# GitHub Copilot"), "Should have header"
    assert (
        "## 1." in merged_content or "## 2." in merged_content
    ), "Should have sections"
    assert "Custom Project Rules" in merged_content, "Should preserve custom"


def test_13_merge_preserves_header_metadata(
    merger, temp_dir, sample_rules_v1, sample_rules_v2
):
    """Test 13: Merge preserva metadata do header do projeto."""
    existing_path = temp_dir / ".copilot-rules.md"
    existing_path.write_text(sample_rules_v1, encoding="utf-8")

    merger.merge(existing_path, sample_rules_v2, interactive=False)

    merged_content = existing_path.read_text(encoding="utf-8")

    # Header deve vir do existing (preservar metadata do projeto)
    # Mas pode ter atualização de data se regras mudaram
    assert "GitHub Copilot" in merged_content


# =============================================================================
# Test 14-16: Edge Cases
# =============================================================================


def test_14_handles_rules_without_priority_markers(merger, temp_dir):
    """Test 14: Handle rules sem marcadores de prioridade."""
    rules_no_priority = """# Rules

## Section 1

Some rules here.

## Section 2

More rules.
"""

    existing_path = temp_dir / ".copilot-rules.md"
    existing_path.write_text(rules_no_priority, encoding="utf-8")

    template = """# Rules

## Section 1 (P0 — CRÍTICO)

Updated rules.
"""

    # Não deve crashar
    result = merger.merge(existing_path, template, interactive=False)

    # Pode ser merged ou skipped, mas não deve dar error
    assert result.status in ["merged", "skipped"]


def test_15_reconstructs_file_in_priority_order(merger, sample_rules_v2):
    """Test 15: Reconstrói arquivo com seções ordenadas por prioridade."""
    rules = merger._parse_rules_file(sample_rules_v2)

    reconstructed = merger._reconstruct_rules_file(rules)

    # P0 sections devem aparecer primeiro
    p0_index = reconstructed.find("P0 — CRÍTICO")
    p1_index = reconstructed.find("## 3. Git (P1)")
    p2_index = reconstructed.find("## 4. Documentação (P2)")

    # P0 antes de P1 antes de P2
    if p0_index >= 0 and p1_index >= 0:
        assert p0_index < p1_index, "P0 should come before P1"
    if p1_index >= 0 and p2_index >= 0:
        assert p1_index < p2_index, "P1 should come before P2"


def test_16_skip_when_no_changes_needed(merger, temp_dir, sample_rules_v2):
    """Test 16: Skip quando não há mudanças necessárias."""
    existing_path = temp_dir / ".copilot-rules.md"
    existing_path.write_text(sample_rules_v2, encoding="utf-8")

    result = merger.merge(existing_path, sample_rules_v2, interactive=False)

    assert result.status == "skipped"
    assert "up-to-date" in result.message.lower()
