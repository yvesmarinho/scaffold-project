"""
test_objetivo_parser.py — Unit tests for objetivo_parser.py

Tests the ObjetivoV2Parser for various scenarios:
- Valid objetivo.yaml v2.0 (happy path)
- Frontmatter only (no sections)
- Sections only (no frontmatter)
- Edge cases: code blocks, tables, nested lists
- Error cases: missing file, invalid YAML, missing required fields

Spec: specs/066-objetivo-yaml-v2/spec.md
Task: T010
"""

import pytest

from scripts.lib.objetivo_parser import ObjetivoV2Parser, ParsedObjetivo


class TestObjetivoV2Parser:
    """Test suite for ObjetivoV2Parser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return ObjetivoV2Parser()

    @pytest.fixture
    def valid_objetivo_v2(self, tmp_path):
        """Create a valid objetivo.yaml v2.0 file for testing."""
        content = """---
version: "2.0"
project:
  name: test-project
  title: Test Project
  type: backend-api
  domain: programming
  language: python

created_at: "2026-04-28"
created_by: test-user

generation:
  profiles_auto_detect: true
  validate_on_save: true
---

# 🎯 Objetivo: Test Project

## 1️⃣ O que este projeto faz?

**Em uma frase**: API REST para gerenciamento de usuários

**Componentes principais**:
- **API REST**: Endpoints CRUD
- **Autenticação**: JWT tokens
- **Database**: PostgreSQL

---

## 2️⃣ Qual problema resolve?

Resolver problema de gerenciamento manual de usuários.

Antes: Processos manuais demorados
Depois: Automação completa

---

## 3️⃣ Escopo do Projeto

**Incluído ✅**:
- CRUD de usuários
- Autenticação JWT
- Validação de dados

**Excluído ❌**:
- Interface web
- Relatórios complexos

---

## 4️⃣ Restrições Técnicas

- Performance: <200ms por request
- Segurança: OWASP Top 10
"""
        file_path = tmp_path / "objetivo.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def frontmatter_only(self, tmp_path):
        """Create a file with frontmatter only (no sections)."""
        content = """---
version: "2.0"
project:
  name: minimal-project
  title: Minimal Project
---

# Content without numbered sections
Just some text here.
"""
        file_path = tmp_path / "frontmatter-only.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def with_code_blocks(self, tmp_path):
        """Create a file with code blocks to test edge case."""
        content = """---
version: "2.0"
project:
  name: code-test
---

## 1️⃣ What this does

This section has code:

```python
def hello():
    # This ## is not a section header
    return "Hello"
```

And more text after.

---

## 2️⃣ Problem

Another section here.
"""
        file_path = tmp_path / "with-code.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def with_tables(self, tmp_path):
        """Create a file with tables to test edge case."""
        content = """---
version: "2.0"
project:
  name: table-test
---

## 1️⃣ Features

| Feature | Status |
|---------|--------|
| Auth    | ✅     |
| CRUD    | ✅     |

More content here.

---

## 2️⃣ Tech Stack

- Python
- FastAPI
"""
        file_path = tmp_path / "with-tables.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def invalid_yaml(self, tmp_path):
        """Create a file with invalid YAML."""
        content = """---
version: "2.0"
project:
  name: test
  invalid: [unclosed bracket
---
"""
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def missing_version(self, tmp_path):
        """Create a file missing required version field."""
        content = """---
project:
  name: test
---
"""
        file_path = tmp_path / "missing-version.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def missing_project_name(self, tmp_path):
        """Create a file missing required project.name field."""
        content = """---
version: "2.0"
project:
  title: Test
---
"""
        file_path = tmp_path / "missing-name.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    # Test 1: Parse valid objetivo.yaml v2.0 (happy path)
    def test_parse_valid_objetivo_v2(self, parser, valid_objetivo_v2):
        """Test parsing a valid objetivo.yaml v2.0 file."""
        parsed = parser.parse(valid_objetivo_v2)

        # Check type
        assert isinstance(parsed, ParsedObjetivo)

        # Check frontmatter
        assert parsed.frontmatter["version"] == "2.0"
        assert parsed.frontmatter["project"]["name"] == "test-project"
        assert parsed.frontmatter["project"]["type"] == "backend-api"
        assert parsed.version == "2.0"
        assert parsed.is_valid_v2 is True

        # Check sections
        assert len(parsed.sections) == 4
        assert 1 in parsed.sections
        assert 2 in parsed.sections
        assert 3 in parsed.sections
        assert 4 in parsed.sections

        # Check section content
        assert "API REST para gerenciamento de usuários" in parsed.sections[1]
        assert "gerenciamento manual de usuários" in parsed.sections[2]
        assert "CRUD de usuários" in parsed.sections[3]
        assert "Performance: <200ms" in parsed.sections[4]

        # Check convenience properties
        assert parsed.project_name == "test-project"
        assert parsed.project_type == "backend-api"

        # Check P0/P1/P2 sections
        assert len(parsed.p0_sections) == 3
        assert len(parsed.p1_sections) == 1
        assert len(parsed.p2_sections) == 0

        # Check file path
        assert parsed.file_path == valid_objetivo_v2

        # Check raw content preserved
        assert "---" in parsed.raw_content
        assert "## 1️⃣" in parsed.raw_content

    # Test 2: Parse frontmatter only (no sections)
    def test_parse_frontmatter_only(self, parser, frontmatter_only):
        """Test parsing file with frontmatter but no numbered sections."""
        parsed = parser.parse(frontmatter_only)

        assert parsed.frontmatter["version"] == "2.0"
        assert parsed.frontmatter["project"]["name"] == "minimal-project"
        assert len(parsed.sections) == 0

    # Test 3: Parse with code blocks
    def test_parse_with_code_blocks(self, parser, with_code_blocks):
        """Test that ## inside code blocks are not parsed as sections."""
        parsed = parser.parse(with_code_blocks)

        assert len(parsed.sections) == 2
        assert 1 in parsed.sections
        assert 2 in parsed.sections

        # Check that code block is included in section 1
        assert "```python" in parsed.sections[1]
        assert "def hello():" in parsed.sections[1]
        assert "This ## is not a section header" in parsed.sections[1]

    # Test 4: Parse with tables
    def test_parse_with_tables(self, parser, with_tables):
        """Test parsing sections with markdown tables."""
        parsed = parser.parse(with_tables)

        assert len(parsed.sections) == 2
        assert "| Feature | Status |" in parsed.sections[1]
        assert "| Auth    | ✅     |" in parsed.sections[1]

    # Test 5: Parse nested lists
    def test_parse_nested_lists(self, parser, tmp_path):
        """Test parsing sections with nested lists."""
        content = """---
version: "2.0"
project:
  name: nested-test
---

## 1️⃣ Features

- Level 1 item
  - Level 2 nested
    - Level 3 deep nested
  - Another level 2
- Back to level 1
"""
        file_path = tmp_path / "nested.yaml"
        file_path.write_text(content, encoding="utf-8")

        parsed = parser.parse(file_path)

        assert "Level 1 item" in parsed.sections[1]
        assert "Level 2 nested" in parsed.sections[1]
        assert "Level 3 deep nested" in parsed.sections[1]

    # Test 6: Missing file error
    def test_parse_missing_file(self, parser):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse("/nonexistent/path/objetivo.yaml")

        assert "File not found" in str(exc_info.value)

    # Test 7: Invalid YAML error
    def test_parse_invalid_yaml(self, parser, invalid_yaml):
        """Test that YAMLError is raised for invalid YAML."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(invalid_yaml)

        assert "Failed to parse frontmatter" in str(exc_info.value)

    # Test 8: Missing version field
    def test_parse_missing_version(self, parser, missing_version):
        """Test that ValueError is raised when version field is missing."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(missing_version)

        assert "Missing required field 'version'" in str(exc_info.value)

    # Test 9: Missing project.name field
    def test_parse_missing_project_name(self, parser, missing_project_name):
        """Test that ValueError is raised when project.name is missing."""
        with pytest.raises(ValueError) as exc_info:
            parser.parse(missing_project_name)

        assert "Missing required field 'project.name'" in str(exc_info.value)

    # Test 10: Empty sections
    def test_parse_empty_sections(self, parser, tmp_path):
        """Test parsing file with empty sections."""
        content = """---
version: "2.0"
project:
  name: empty-test
---

## 1️⃣ First Section

Content here.

---

## 2️⃣ Empty Section

---

## 3️⃣ Another Section

More content.
"""
        file_path = tmp_path / "empty-sections.yaml"
        file_path.write_text(content, encoding="utf-8")

        parsed = parser.parse(file_path)

        assert 1 in parsed.sections
        assert 2 in parsed.sections
        assert 3 in parsed.sections

        assert "Content here" in parsed.sections[1]
        # Section 2 should be empty or just "---"
        assert len(parsed.sections[2].strip()) <= 3  # Allow for "---"
        assert "More content" in parsed.sections[3]
