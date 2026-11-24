"""
Testes para sistema de consolidação de .copilot-rules

Valida detecção, merge, consolidação e backup de múltiplos
arquivos de regras Copilot.
"""

import pytest

from scripts.lib.copilot_rules_consolidate import (
    consolidate_copilot_rules,
    detect_copilot_rules_files,
    merge_markdown_sections,
    parse_markdown_sections,
    validate_consolidation_needed,
)


@pytest.fixture
def temp_project(tmp_path):
    """Cria estrutura de projeto temporária."""
    project = tmp_path / "test_project"
    project.mkdir()
    return project


@pytest.fixture
def sample_md_content():
    """Conteúdo Markdown de exemplo."""
    return {
        "simple": """# Título Principal

Algum conteúdo introdutório.

## Seção 1

Conteúdo da seção 1.

## Seção 2

Conteúdo da seção 2.
""",
        "with_subsections": """## Regras P0

NUNCA usar heredoc.

### Subsecção A

Detalhes A.

## Regras P1

Sempre usar file_tools.

### Subsecção B

Detalhes B.
""",
    }


# =============================================================================
# Testes de parse_markdown_sections
# =============================================================================


def test_parse_markdown_sections_simple(sample_md_content):
    """Testa parse de Markdown simples com 2 seções."""
    sections = parse_markdown_sections(sample_md_content["simple"])

    assert "Seção 1" in sections
    assert "Seção 2" in sections
    assert "Conteúdo da seção 1" in sections["Seção 1"]
    assert "Conteúdo da seção 2" in sections["Seção 2"]


def test_parse_markdown_sections_with_subsections(sample_md_content):
    """Testa parse preservando subsections dentro de seções."""
    sections = parse_markdown_sections(sample_md_content["with_subsections"])

    assert "Regras P0" in sections
    assert "Regras P1" in sections
    assert "### Subsecção A" in sections["Regras P0"]
    assert "### Subsecção B" in sections["Regras P1"]


def test_parse_markdown_sections_empty():
    """Testa parse de string vazia."""
    sections = parse_markdown_sections("")
    assert sections == {}


# =============================================================================
# Testes de merge_markdown_sections
# =============================================================================


def test_merge_markdown_sections_two_files(temp_project):
    """Testa merge de 2 arquivos com seções únicas."""
    file1 = temp_project / "file1.md"
    file2 = temp_project / "file2.md"

    file1.write_text(
        """## Seção A
Conteúdo A do arquivo 1.

## Seção B
Conteúdo B do arquivo 1.
""",
        encoding="utf-8",
    )

    file2.write_text(
        """## Seção C
Conteúdo C do arquivo 2.

## Seção D
Conteúdo D do arquivo 2.
""",
        encoding="utf-8",
    )

    result = merge_markdown_sections([file1, file2])

    assert "## Seção A" in result
    assert "## Seção B" in result
    assert "## Seção C" in result
    assert "## Seção D" in result
    assert "Consolidado de 2 arquivos" in result


def test_merge_markdown_sections_duplicate_sections(temp_project):
    """Testa que seções duplicadas priorizam primeiro arquivo (user-wins)."""
    file1 = temp_project / "file1.md"
    file2 = temp_project / "file2.md"

    file1.write_text(
        """## Seção Comum
Conteúdo do arquivo 1 (deve ser preservado).
""",
        encoding="utf-8",
    )

    file2.write_text(
        """## Seção Comum
Conteúdo do arquivo 2 (deve ser descartado).
""",
        encoding="utf-8",
    )

    result = merge_markdown_sections([file1, file2])

    assert "Conteúdo do arquivo 1 (deve ser preservado)" in result
    assert "Conteúdo do arquivo 2 (deve ser descartado)" not in result


def test_merge_markdown_sections_preserves_headers(temp_project):
    """Testa que cabeçalho (antes do primeiro ##) é preservado."""
    file1 = temp_project / "file1.md"

    file1.write_text(
        """# Título Principal
Descrição do documento.

## Seção 1
Conteúdo.
""",
        encoding="utf-8",
    )

    result = merge_markdown_sections([file1])

    assert "# Título Principal" in result
    assert "Descrição do documento" in result


def test_merge_markdown_sections_sorts_alphabetically(temp_project):
    """Testa que seções são ordenadas alfabeticamente."""
    file1 = temp_project / "file1.md"

    file1.write_text(
        """## Zebra
Último alfabeticamente.

## Alpha
Primeiro alfabeticamente.

## Beta
Segundo alfabeticamente.
""",
        encoding="utf-8",
    )

    result = merge_markdown_sections([file1])
    lines = result.split("\n")

    # Encontrar posições dos headers
    alpha_pos = next(i for i, line in enumerate(lines) if "## Alpha" in line)
    beta_pos = next(i for i, line in enumerate(lines) if "## Beta" in line)
    zebra_pos = next(i for i, line in enumerate(lines) if "## Zebra" in line)

    assert alpha_pos < beta_pos < zebra_pos


# =============================================================================
# Testes de detect_copilot_rules_files
# =============================================================================


def test_detect_copilot_rules_files_finds_multiple(temp_project):
    """Testa detecção de múltiplos arquivos .copilot-rules*."""
    (temp_project / ".copilot-rules.md").touch()
    (temp_project / ".copilot-strict-rules.md").touch()
    (temp_project / "copilot-instructions.md").touch()

    found = detect_copilot_rules_files(temp_project)

    assert len(found) == 3
    names = [f.name for f in found]
    assert ".copilot-rules.md" in names
    assert ".copilot-strict-rules.md" in names
    assert "copilot-instructions.md" in names


def test_detect_copilot_rules_files_empty_directory(temp_project):
    """Testa detecção em diretório sem arquivos."""
    found = detect_copilot_rules_files(temp_project)
    assert found == []


def test_detect_copilot_rules_files_ignores_subdirectories(temp_project):
    """Testa que não detecta arquivos em subdiretórios."""
    subdir = temp_project / "subdir"
    subdir.mkdir()
    (subdir / ".copilot-rules.md").touch()

    found = detect_copilot_rules_files(temp_project)
    assert found == []


# =============================================================================
# Testes de consolidate_copilot_rules
# =============================================================================


def test_consolidate_copilot_rules_no_files(temp_project):
    """Testa consolidação quando não há arquivos."""
    result = consolidate_copilot_rules(temp_project)
    assert result is None


def test_consolidate_copilot_rules_single_file(temp_project):
    """Testa consolidação quando há apenas 1 arquivo."""
    file1 = temp_project / ".copilot-rules.md"
    file1.write_text("## Regra 1\nConteúdo.", encoding="utf-8")

    result = consolidate_copilot_rules(temp_project)

    assert result == file1
    assert file1.exists()


def test_consolidate_copilot_rules_multiple_files(temp_project):
    """Testa consolidação completa de múltiplos arquivos."""
    file1 = temp_project / ".copilot-rules.md"
    file2 = temp_project / ".copilot-strict-rules.md"

    file1.write_text(
        """## Regra A
Conteúdo A.

## Regra B
Conteúdo B.
""",
        encoding="utf-8",
    )

    file2.write_text(
        """## Regra C
Conteúdo C.
""",
        encoding="utf-8",
    )

    backup_dir = temp_project / ".backups" / "copilot-rules"
    result = consolidate_copilot_rules(temp_project, backup_dir)

    # Validar resultado
    assert result == temp_project / ".copilot-rules.md"
    assert result.exists()

    # Validar conteúdo consolidado
    content = result.read_text(encoding="utf-8")
    assert "## Regra A" in content
    assert "## Regra B" in content
    assert "## Regra C" in content

    # Validar backups criados
    assert backup_dir.exists()
    assert (backup_dir / ".copilot-rules.md").exists()
    assert (backup_dir / ".copilot-strict-rules.md").exists()

    # Validar que duplicatas foram removidas
    assert not file2.exists()


def test_consolidate_copilot_rules_preserves_priority(temp_project):
    """Testa que .copilot-rules.md tem prioridade no merge."""
    primary = temp_project / ".copilot-rules.md"
    secondary = temp_project / ".copilot-strict-rules.md"

    primary.write_text(
        """## Regra Compartilhada
Conteúdo do arquivo primary (deve prevalecer).
""",
        encoding="utf-8",
    )

    secondary.write_text(
        """## Regra Compartilhada
Conteúdo do arquivo secondary (deve ser descartado).
""",
        encoding="utf-8",
    )

    result = consolidate_copilot_rules(temp_project)
    content = result.read_text(encoding="utf-8")

    assert "Conteúdo do arquivo primary (deve prevalecer)" in content
    assert "Conteúdo do arquivo secondary (deve ser descartado)" not in content


# =============================================================================
# Testes de validate_consolidation_needed
# =============================================================================


def test_validate_consolidation_needed_true(temp_project):
    """Testa que retorna True quando há múltiplos arquivos."""
    (temp_project / ".copilot-rules.md").touch()
    (temp_project / ".copilot-strict-rules.md").touch()

    needed, files = validate_consolidation_needed(temp_project)

    assert needed is True
    assert len(files) == 2


def test_validate_consolidation_needed_false_single(temp_project):
    """Testa que retorna False quando há apenas 1 arquivo."""
    (temp_project / ".copilot-rules.md").touch()

    needed, files = validate_consolidation_needed(temp_project)

    assert needed is False
    assert len(files) == 1


def test_validate_consolidation_needed_false_none(temp_project):
    """Testa que retorna False quando não há arquivos."""
    needed, files = validate_consolidation_needed(temp_project)

    assert needed is False
    assert len(files) == 0
