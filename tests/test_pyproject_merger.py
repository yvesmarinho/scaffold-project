"""
Tests for PyprojectMerger

Sprint 3 (P1 HIGH): Validar merge inteligente de pyproject.toml

Test strategy:
- Test file detection (pyproject.toml)
- Test TOML parsing ([project], [build-system], [tool.*])
- Test merge decision logic
- Test dependencies merge (aditivo)
- Test optional-dependencies merge por grupo
- Test tool configs merge (black, ruff, bandit, mypy)
- Test full integration with temp files
- Test edge cases (malformed TOML, no changes)
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.lib.pyproject_merge import (
    PyprojectContent,
    PyprojectMerger,
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
def sample_pyproject_v1():
    """pyproject.toml básico versão 1 (existente)."""
    return """[project]
name = "my-project"
version = "1.0.0"
description = "My awesome project"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "fastapi>=0.100",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
]

[build-system]
requires = ["setuptools>=65.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ["py310"]
"""


@pytest.fixture
def sample_pyproject_v2():
    """pyproject.toml versão 2 com security tools (template)."""
    return """[project]
name = "template-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "fastapi>=0.100",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "black>=23.0",
    "ruff>=0.1.0",
]
security = [
    "bandit>=1.7",
    "safety>=2.0",
]

[build-system]
requires = ["setuptools>=65.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 100
target-version = ["py312"]

[tool.ruff]
select = ["E", "F", "I"]
ignore = ["E501"]
line-length = 100

[tool.bandit]
exclude_dirs = ["tests/", "build/"]
skips = ["B101"]

[tool.mypy]
python_version = "3.12"
strict = true
"""


@pytest.fixture
def merger():
    """Instância do merger para testes."""
    return PyprojectMerger()


# =============================================================================
# Test 01: File Detection
# =============================================================================


def test_01_can_merge_detects_pyproject_toml(merger, temp_dir):
    """Test 01: can_merge() detecta pyproject.toml corretamente."""
    # Caso positivo
    valid_file = temp_dir / "pyproject.toml"
    valid_file.touch()
    assert merger.can_merge(valid_file), "Should detect pyproject.toml"

    # Casos negativos
    wrong_name = temp_dir / "pyproject.txt"
    wrong_name.touch()
    assert not merger.can_merge(wrong_name), "Should reject non-pyproject.toml"

    other_toml = temp_dir / "config.toml"
    other_toml.touch()
    assert not merger.can_merge(other_toml), "Should reject other .toml files"


# =============================================================================
# Test 02-03: Parsing
# =============================================================================


def test_02_parse_pyproject_toml(merger, sample_pyproject_v1):
    """Test 02: Parse TOML pyproject corretamente."""
    proj = merger._parse_pyproject(sample_pyproject_v1)

    assert isinstance(proj, PyprojectContent)
    assert proj.project["name"] == "my-project"
    assert proj.project["version"] == "1.0.0"
    assert "pydantic>=2.0" in proj.project["dependencies"]
    assert "dev" in proj.project["optional-dependencies"]
    assert "black" in proj.tool_configs
    assert proj.tool_configs["black"]["line-length"] == 88


def test_03_parse_pyproject_with_security_tools(merger, sample_pyproject_v2):
    """Test 03: Parse pyproject com security tools."""
    proj = merger._parse_pyproject(sample_pyproject_v2)

    assert "security" in proj.project["optional-dependencies"]
    assert "ruff" in proj.tool_configs
    assert "bandit" in proj.tool_configs
    assert "mypy" in proj.tool_configs


# =============================================================================
# Test 04-06: Merge Decision Logic
# =============================================================================


def test_04_should_merge_detects_new_dependencies(
    merger, sample_pyproject_v1, sample_pyproject_v2
):
    """Test 04: Detecta novas dependencies."""
    existing_proj = merger._parse_pyproject(sample_pyproject_v1)
    template_proj = merger._parse_pyproject(sample_pyproject_v2)

    decision = merger._should_merge(existing_proj, template_proj, "pyproject.toml")

    assert decision.should_merge
    # Deve detectar pyyaml como nova dependency
    assert any("dependencies" in change.lower() for change in decision.changes)


def test_05_should_merge_detects_new_optional_groups(
    merger, sample_pyproject_v1, sample_pyproject_v2
):
    """Test 05: Detecta novos optional-dependencies groups."""
    existing_proj = merger._parse_pyproject(sample_pyproject_v1)
    template_proj = merger._parse_pyproject(sample_pyproject_v2)

    decision = merger._should_merge(existing_proj, template_proj, "pyproject.toml")

    assert decision.should_merge
    # Deve detectar grupo "security"
    assert any("optional-dependencies" in change.lower() for change in decision.changes)


def test_06_should_skip_if_already_updated(merger, sample_pyproject_v2):
    """Test 06: Skip se já está atualizado."""
    template_proj = merger._parse_pyproject(sample_pyproject_v2)

    decision = merger._should_merge(
        template_proj, template_proj, "pyproject.toml"  # Existing == Template
    )

    assert not decision.should_merge
    assert "up-to-date" in decision.reason.lower()


# =============================================================================
# Test 07-09: Dependencies Merge
# =============================================================================


def test_07_merge_dependencies_adds_new_packages(merger):
    """Test 07: Merge adiciona novos pacotes."""
    existing_project = {
        "dependencies": [
            "pydantic>=2.0",
            "fastapi>=0.100",
        ]
    }
    template_project = {
        "dependencies": [
            "pydantic>=2.0",
            "fastapi>=0.100",
            "pyyaml>=6.0",
        ]
    }

    merged = merger._merge_project_section(existing_project, template_project)

    assert "pyyaml>=6.0" in merged["dependencies"]


def test_08_merge_dependencies_preserves_existing(merger):
    """Test 08: Merge preserva dependencies customizados."""
    existing_project = {
        "dependencies": [
            "pydantic>=2.0",
            "custom-lib==1.2.3",
        ]
    }
    template_project = {
        "dependencies": [
            "pydantic>=2.0",
        ]
    }

    merged = merger._merge_project_section(existing_project, template_project)

    # Deve preservar custom-lib
    assert "custom-lib==1.2.3" in merged["dependencies"]


def test_09_merge_optional_dependencies_by_group(merger):
    """Test 09: Merge optional-dependencies por grupo."""
    existing_project = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=23.0"],
        }
    }
    template_project = {
        "optional-dependencies": {
            "dev": ["pytest>=7.0", "black>=23.0", "ruff>=0.1.0"],
            "security": ["bandit>=1.7", "safety>=2.0"],
        }
    }

    merged = merger._merge_project_section(existing_project, template_project)

    # Grupo dev deve ter ruff adicionado
    assert "ruff>=0.1.0" in merged["optional-dependencies"]["dev"]
    # Novo grupo security deve existir
    assert "security" in merged["optional-dependencies"]


# =============================================================================
# Test 10-12: Tool Configs Merge
# =============================================================================


def test_10_merge_tool_configs_adds_new_tools(merger):
    """Test 10: Merge adiciona novas tool configs."""
    existing_tools = {"black": {"line-length": 88}}
    template_tools = {
        "black": {"line-length": 100},
        "ruff": {"select": ["E", "F"], "ignore": ["E501"]},
        "bandit": {"exclude_dirs": ["tests/"]},
    }

    merged = merger._merge_tool_configs(existing_tools, template_tools)

    assert "ruff" in merged
    assert "bandit" in merged


def test_11_merge_tool_config_updates_best_practices(merger):
    """Test 11: Merge tool config atualiza best practices."""
    existing = {
        "line-length": 88,
        "target-version": ["py310"],
    }
    template = {
        "line-length": 100,
        "target-version": ["py312"],
    }

    merged = merger._merge_tool_config(existing, template, "black")

    # Best practices devem ser atualizadas
    assert merged["line-length"] == 100
    assert merged["target-version"] == ["py312"]


def test_12_merge_tool_config_preserves_custom_settings(merger):
    """Test 12: Merge preserva configurações customizadas."""
    existing = {
        "line-length": 88,
        "extend-exclude": ["*.pyi"],  # Custom setting
    }
    template = {
        "line-length": 100,
        "target-version": ["py312"],
    }

    merged = merger._merge_tool_config(existing, template, "black")

    # Custom setting deve ser preservado
    assert "extend-exclude" in merged
    # Best practice deve ser atualizado
    assert merged["line-length"] == 100


# =============================================================================
# Test 13-14: Project Metadata Preservation
# =============================================================================


def test_13_merge_preserves_project_metadata(merger):
    """Test 13: Merge preserva name, version, description do projeto."""
    existing_project = {
        "name": "my-project",
        "version": "1.0.0",
        "description": "My awesome project",
        "dependencies": ["pydantic>=2.0"],
    }
    template_project = {
        "name": "template-project",
        "version": "0.1.0",
        "description": "Template description",
        "dependencies": ["pydantic>=2.0", "pyyaml>=6.0"],
    }

    merged = merger._merge_project_section(existing_project, template_project)

    # Metadata do projeto deve ser preservado
    assert merged["name"] == "my-project"
    assert merged["version"] == "1.0.0"
    assert merged["description"] == "My awesome project"
    # Dependencies devem ser mesclados
    assert "pyyaml>=6.0" in merged["dependencies"]


def test_14_merge_updates_requires_python(merger):
    """Test 14: Merge atualiza requires-python se template mais recente."""
    existing_project = {
        "name": "my-project",
        "requires-python": ">=3.10",
        "dependencies": [],
    }
    template_project = {
        "name": "template",
        "requires-python": ">=3.12",
        "dependencies": [],
    }

    merged = merger._merge_project_section(existing_project, template_project)

    # requires-python deve ser atualizado
    assert merged["requires-python"] == ">=3.12"


# =============================================================================
# Test 15-16: Full Integration
# =============================================================================


def test_15_full_merge_creates_backup(
    merger, temp_dir, sample_pyproject_v1, sample_pyproject_v2
):
    """Test 15: Merge completo cria backup do arquivo original."""
    existing_path = temp_dir / "pyproject.toml"
    existing_path.write_text(sample_pyproject_v1, encoding="utf-8")

    result = merger.merge(existing_path, sample_pyproject_v2, interactive=False)

    assert result.status == "merged"
    backup_path = existing_path.with_suffix(".toml.backup")
    assert backup_path.exists(), "Should create backup"
    assert backup_path.read_text(encoding="utf-8") == sample_pyproject_v1


def test_16_handles_malformed_toml(merger, temp_dir):
    """Test 16: Handle TOML malformado gracefully."""
    malformed = """[project]
name = "test"
dependencies = [
    "package>=1.0"
    "missing-comma"
]
"""

    existing_path = temp_dir / "pyproject.toml"
    existing_path.write_text(malformed, encoding="utf-8")

    template = """[project]
name = "template"
dependencies = []
"""

    # Não deve crashar (pode dar error ou skip)
    result = merger.merge(existing_path, template, interactive=False)

    assert result.status in ["merged", "skipped", "error"]
