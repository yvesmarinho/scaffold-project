"""
test_objetivo_migrator.py — Unit tests for objetivo_migrator.py

Tests the ObjetivoMigrator for various scenarios:
- Valid v1.0 → v2.0 migration (all fields mapped)
- Complex v1.0 with nested rules, multiple personas
- Edge case: missing fields → warnings
- Error case: v2.0 file → error "already v2.0"

Spec: specs/066-objetivo-yaml-v2/spec.md
Task: T020
"""

import pytest
import yaml

from scripts.lib.objetivo_migrator import ObjetivoMigrator


class TestObjetivoMigrator:
    """Test suite for ObjetivoMigrator."""

    @pytest.fixture
    def migrator(self):
        """Create a migrator instance."""
        return ObjetivoMigrator()

    @pytest.fixture
    def valid_v1_simple(self, tmp_path):
        """Create a simple valid v1.0 objetivo.yaml file."""
        content = """---
feature:
  id: "test-feature"
  name: "Test Feature"
  branch: "001-test-feature"
  created: "2026-04-28"

negocio:
  problema:
    descricao: |
      Users need to deploy applications faster without manual configuration.

      Currently, deployment takes 2-3 hours and has 15% error rate.

    impacto_atual: |
      Without automation, deployment time increases by 50% and operational
      costs rise by $30k/month.

    stakeholders:
      - "DevOps Engineers"
      - "SRE Team"

  valor:
    objetivos_estrategicos:
      - "Increase deployment efficiency by 80%"
      - "Reduce deployment time from 2h to 15min"

    metricas_sucesso:
      - metric: "Adoption rate"
        target: "80% of team in 3 months"
      - metric: "Deployment time"
        target: "<= 15 minutes"

  contexto:
    restricoes_negocio:
      - "Budget limit: $50,000"
      - "Regulatory deadline: 2026-12-31"

    premissas:
      - "Users have stable internet (>=10 Mbps)"
      - "Legacy system X API is available"

produto:
  visao_alto_nivel: |
    Automated deployment system that allows DevOps teams to configure
    and execute deployments via web/CLI interface, with automatic rollback
    on failure, reducing time from 2h to 15min and error rate from 15% to <1%.

  personas:
    - name: "DevOps Engineer"
      needs: "Automate repetitive deployments without manual configuration"
      pain_points: "Manual configuration is error-prone and takes 2-3h per deploy"

    - name: "SRE/Platform Admin"
      needs: "Visibility of production deployments and fast rollback on failures"
      pain_points: "30min average downtime when deployment fails due to manual rollback"

  jornadas_criticas:
    - journey: "Deploy new feature to production"
      priority: "P1"
      value: "Reduces time from 2h to 15min and error rate from 15% to <1%"

    - journey: "Automatic rollback on deployment failure"
      priority: "P1"
      value: "Reduces downtime from 30min to 2min with automatic rollback"

decisoes_iniciais:
  - id: "D-01"
    question: "Build custom solution or buy SaaS?"
    decision: "Build custom (justification: specific integration requirements with legacy system not met by existing SaaS)"

  - id: "D-02"
    question: "Use Kubernetes or traditional VMs?"
    decision: "Kubernetes (better scalability and resource utilization)"
"""
        file_path = tmp_path / "objetivo.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def valid_v1_minimal(self, tmp_path):
        """Create a minimal v1.0 file with only required fields."""
        content = """---
feature:
  name: "Minimal Project"

produto:
  visao_alto_nivel: "A minimal project for testing migration."

negocio:
  problema:
    descricao: "Some problem that needs solving."
"""
        file_path = tmp_path / "minimal.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def valid_v2_file(self, tmp_path):
        """Create a v2.0 file (should not be migrated)."""
        content = """---
version: "2.0"
project:
  name: test-project
---

## 1️⃣ What this does

Content here.

## 2️⃣ Problem solved

Content here.

## 3️⃣ Scope

**Incluído ✅**:
- Feature 1
"""
        file_path = tmp_path / "v2.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def invalid_yaml(self, tmp_path):
        """Create an invalid YAML file."""
        content = """---
feature:
  name: "Test"
  invalid: [unclosed bracket
---
"""
        file_path = tmp_path / "invalid.yaml"
        file_path.write_text(content, encoding="utf-8")
        return file_path

    # Test 1: Migrate valid v1.0 → v2.0 (all fields mapped)
    def test_migrate_valid_v1_simple(self, migrator, valid_v1_simple, tmp_path):
        """Test migrating a valid v1.0 file to v2.0 with all fields."""
        result = migrator.migrate(valid_v1_simple)

        # Check success
        assert result.success is True
        assert result.source_version == "1.0"
        assert result.target_version == "2.0"

        # Check preview file created
        assert result.preview_file is not None
        assert result.preview_file.exists()

        # Check mappings
        assert len(result.mappings) > 0
        assert "feature.name" in result.mappings
        assert "produto.visao_alto_nivel" in result.mappings

        # Check warnings (should have manual review warning)
        assert len(result.warnings) > 0

        # Verify v2.0 content structure
        v2_content = result.preview_file.read_text(encoding="utf-8")

        # Should have YAML frontmatter
        assert "---" in v2_content
        assert 'version: "2.0"' in v2_content or "version: '2.0'" in v2_content

        # Should have project name
        assert "test-feature" in v2_content or "Test Feature" in v2_content

        # Should have sections
        assert "## 1️⃣" in v2_content
        assert "## 2️⃣" in v2_content
        assert "## 3️⃣" in v2_content

        # Should have mapped content
        assert "Automated deployment system" in v2_content  # From visao_alto_nivel
        assert "deploy applications faster" in v2_content  # From problema.descricao

    # Test 2: Migrate minimal v1.0 (missing optional fields)
    def test_migrate_minimal_v1(self, migrator, valid_v1_minimal):
        """Test migrating a minimal v1.0 file with warnings for missing fields."""
        result = migrator.migrate(valid_v1_minimal)

        assert result.success is True
        assert result.source_version == "1.0"

        # Should have warnings about missing fields
        assert len(result.warnings) > 0

        # Preview file should exist
        assert result.preview_file.exists()

        # Should still have basic structure
        v2_content = result.preview_file.read_text(encoding="utf-8")
        assert "## 1️⃣" in v2_content
        assert "## 2️⃣" in v2_content
        assert "## 3️⃣" in v2_content

    # Test 3: Try to migrate v2.0 file → error
    def test_migrate_v2_file_error(self, migrator, valid_v2_file):
        """Test that migrating a v2.0 file returns error."""
        result = migrator.migrate(valid_v2_file)

        assert result.success is False
        assert result.source_version == "2.0"

        # Should have error about already v2.0
        assert len(result.errors) > 0
        assert any("already" in e.lower() for e in result.errors)

    # Test 4: Migrate missing file → error
    def test_migrate_missing_file(self, migrator):
        """Test that migrating non-existent file returns error."""
        result = migrator.migrate("/nonexistent/objetivo.yaml")

        assert result.success is False
        assert len(result.errors) > 0
        assert any("not found" in e.lower() for e in result.errors)

    # Test 5: Migrate invalid YAML → error
    def test_migrate_invalid_yaml(self, migrator, invalid_yaml):
        """Test that migrating invalid YAML returns error."""
        result = migrator.migrate(invalid_yaml)

        assert result.success is False

        # Should have error about YAML parsing
        # Note: might be detected as unknown version first
        assert len(result.errors) > 0

    # Test 6: Version detection
    def test_version_detection_v1(self, migrator, valid_v1_simple):
        """Test that version detection correctly identifies v1.0."""
        content = valid_v1_simple.read_text(encoding="utf-8")
        version = migrator._detect_version(content)

        assert version == "1.0"

    def test_version_detection_v2(self, migrator, valid_v2_file):
        """Test that version detection correctly identifies v2.0."""
        content = valid_v2_file.read_text(encoding="utf-8")
        version = migrator._detect_version(content)

        assert version == "2.0"

    def test_version_detection_unknown(self, migrator):
        """Test that version detection returns unknown for unrecognized format."""
        content = "This is not a valid objetivo.yaml file at all."
        version = migrator._detect_version(content)

        assert version == "unknown"

    # Test 7: Custom output path
    def test_migrate_custom_output_path(self, migrator, valid_v1_simple, tmp_path):
        """Test migrating with custom output path."""
        custom_output = tmp_path / "custom-output.yaml"

        result = migrator.migrate(valid_v1_simple, output_path=custom_output)

        assert result.success is True
        assert result.preview_file == custom_output
        assert custom_output.exists()

    # Test 8: Verify frontmatter structure
    def test_migrate_frontmatter_structure(self, migrator, valid_v1_simple):
        """Test that migrated file has correct frontmatter structure."""
        result = migrator.migrate(valid_v1_simple)

        assert result.success is True

        # Parse the v2 file and check frontmatter
        v2_content = result.preview_file.read_text(encoding="utf-8")

        # Extract frontmatter
        import re

        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", v2_content, re.DOTALL)
        assert match is not None

        frontmatter_yaml = match.group(1)
        frontmatter = yaml.safe_load(frontmatter_yaml)

        # Check required frontmatter fields
        assert frontmatter["version"] == "2.0"
        assert "project" in frontmatter
        assert "name" in frontmatter["project"]
        assert "title" in frontmatter["project"]
        assert "type" in frontmatter["project"]
        assert "domain" in frontmatter["project"]

    # Test 9: Verify section content mapping
    def test_migrate_section_content(self, migrator, valid_v1_simple):
        """Test that specific v1.0 fields are correctly mapped to v2.0 sections."""
        result = migrator.migrate(valid_v1_simple)

        assert result.success is True

        v2_content = result.preview_file.read_text(encoding="utf-8")

        # Section 1 should have visao_alto_nivel content
        assert "Automated deployment system" in v2_content

        # Section 2 should have problema content
        assert "deploy applications faster" in v2_content

        # Section 3 should have jornadas mapped to Incluído
        assert "Incluído ✅" in v2_content
        assert (
            "Deploy new feature to production" in v2_content
            or "production" in v2_content.lower()
        )

        # Section 4 should have restricoes if present
        assert "Budget limit" in v2_content or "Restrições" in v2_content

        # Section 5 should have personas mapped
        assert "DevOps Engineer" in v2_content

    # Test 10: Result string representation
    def test_migration_result_str(self, migrator, valid_v1_simple):
        """Test that MigrationResult has useful string representation."""
        result = migrator.migrate(valid_v1_simple)

        result_str = str(result)

        assert "✅" in result_str  # Success indicator
        assert "v1.0" in result_str or "1.0" in result_str
        assert "v2.0" in result_str or "2.0" in result_str
        assert "Preview" in result_str
