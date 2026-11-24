"""
Test suite for IMP-65 Fase 1: Template Versioning and Drift Detection.

Tests cover:
- YAML frontmatter parsing
- Semantic version comparison
- Template scanning
- Drift detection
- Report generation
"""

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.lib import template_version

# ---------------------------------------------------------------------------
# Unit Tests - Template Version Parsing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTemplateVersionParsing:
    """Test parse_template_version() functionality."""

    def test_parse_valid_frontmatter(self, tmp_path: Path):
        """Parse template with valid YAML frontmatter."""
        template = tmp_path / "spec-template.md"
        template.write_text(dedent("""
            ---
            template_version: "1.2.3"
            last_updated: "2026-04-14"
            breaking_changes: true
            ---
            # Specification Template
            Content here...
        """).strip())

        result = template_version.parse_template_version(template)

        assert result is not None
        assert result.name == "spec-template.md"
        assert result.version == "1.2.3"
        assert result.last_updated == "2026-04-14"
        assert result.breaking_changes is True
        assert result.path == template

    def test_parse_minimal_frontmatter(self, tmp_path: Path):
        """Parse template with minimal required fields."""
        template = tmp_path / "plan-template.md"
        template.write_text(dedent("""
            ---
            template_version: "2.0.0"
            ---
            # Plan Template
        """).strip())

        result = template_version.parse_template_version(template)

        assert result is not None
        assert result.name == "plan-template.md"
        assert result.version == "2.0.0"
        assert result.last_updated == "unknown"  # Default when not provided
        assert result.breaking_changes is False  # Default

    def test_parse_missing_frontmatter(self, tmp_path: Path):
        """Return None when frontmatter is missing."""
        template = tmp_path / "old-template.md"
        template.write_text("# Ancient Template\nNo frontmatter here.")

        result = template_version.parse_template_version(template)
        assert result is None

    def test_parse_invalid_yaml(self, tmp_path: Path):
        """Return None when YAML is malformed."""
        template = tmp_path / "broken-template.md"
        template.write_text(dedent("""
            ---
            template_version: "1.0.0
            invalid :: yaml : here
            ---
        """))

        result = template_version.parse_template_version(template)
        assert result is None

    def test_parse_missing_version_field(self, tmp_path: Path):
        """Return None when template_version field is missing."""
        template = tmp_path / "no-version.md"
        template.write_text(dedent("""
            ---
            last_updated: "2026-01-01"
            ---
            Content
        """))

        result = template_version.parse_template_version(template)
        assert result is None


# ---------------------------------------------------------------------------
# Unit Tests - Version Comparison
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestVersionComparison:
    """Test parse_version_tuple() and compare_versions()."""

    @pytest.mark.parametrize(
        "version,expected",
        [
            ("1.0.0", (1, 0, 0)),
            ("2.15.3", (2, 15, 3)),
            ("0.0.1", (0, 0, 1)),
            ("10.20.30", (10, 20, 30)),
        ],
    )
    def test_parse_valid_versions(self, version: str, expected: tuple[int, int, int]):
        """Parse valid semantic versions."""
        result = template_version.parse_version_tuple(version)
        assert result == expected

    @pytest.mark.parametrize(
        "invalid_version",
        [
            "1.0",  # Missing patch
            "1.0.0.0",  # Too many segments
            "v1.0.0",  # Prefix
            "1.x.0",  # Non-numeric
            "",  # Empty
            "latest",  # Non-semver
        ],
    )
    def test_parse_invalid_versions(self, invalid_version: str):
        """Return None for invalid version strings."""
        result = template_version.parse_version_tuple(invalid_version)
        assert result is None

    @pytest.mark.parametrize(
        "v1,v2,expected",
        [
            ("1.0.0", "1.0.0", 0),  # Equal
            ("1.0.0", "1.0.1", -1),  # Patch bump
            ("1.0.1", "1.0.0", 1),  # v1 newer
            ("1.0.0", "1.1.0", -1),  # Minor bump
            ("1.1.0", "1.0.0", 1),  # v1 newer
            ("1.0.0", "2.0.0", -1),  # Major bump
            ("2.0.0", "1.0.0", 1),  # v1 newer
            ("0.0.1", "0.0.2", -1),  # Pre-1.0 versions
            ("1.9.9", "2.0.0", -1),  # Edge case: major version bump
        ],
    )
    def test_compare_versions(self, v1: str, v2: str, expected: int):
        """Compare semantic versions correctly."""
        result = template_version.compare_versions(v1, v2)
        assert result == expected


# ---------------------------------------------------------------------------
# Integration Tests - Template Scanning
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTemplateScanning:
    """Test scan_templates() with real directory structures."""

    def test_scan_empty_directory(self, tmp_path: Path):
        """Scan empty directory returns empty dict."""
        result = template_version.scan_templates(tmp_path)
        assert result == {}

    def test_scan_directory_with_versioned_templates(self, tmp_path: Path):
        """Scan directory with multiple versioned templates."""
        # Create test templates
        (tmp_path / "spec-template.md").write_text(dedent("""
            ---
            template_version: "1.0.0"
            ---
            # Spec
        """).strip())

        (tmp_path / "plan-template.md").write_text(dedent("""
            ---
            template_version: "2.1.3"
            last_updated: "2026-04-14"
            ---
            # Plan
        """).strip())

        result = template_version.scan_templates(tmp_path)

        assert len(result) == 2
        assert "spec-template.md" in result
        assert "plan-template.md" in result
        assert result["spec-template.md"].version == "1.0.0"
        assert result["plan-template.md"].version == "2.1.3"

    def test_scan_directory_ignores_unversioned_files(self, tmp_path: Path):
        """Scan ignores files without version metadata."""
        (tmp_path / "versioned.md").write_text(dedent("""
            ---
            template_version: "1.0.0"
            ---
            Content
        """).strip())

        (tmp_path / "unversioned.md").write_text("# No frontmatter")
        (tmp_path / "README.md").write_text("# Docs")
        (tmp_path / "data.json").write_text("{}")

        result = template_version.scan_templates(tmp_path)

        assert len(result) == 1
        assert "versioned.md" in result


# ---------------------------------------------------------------------------
# Integration Tests - Drift Detection
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestDriftDetection:
    """Test detect_drift() with various local/upstream scenarios."""

    def test_no_drift_identical_versions(self):
        """No drift when local and upstream match."""
        local = {
            "spec-template": template_version.TemplateVersion(
                name="spec-template",
                version="1.0.0",
                last_updated="2026-04-14",
                breaking_changes=False,
                path=Path("/local/spec-template.md"),
            )
        }
        upstream = {
            "spec-template": template_version.TemplateVersion(
                name="spec-template",
                version="1.0.0",
                last_updated="2026-04-14",
                breaking_changes=False,
                path=Path("/upstream/spec-template.md"),
            )
        }

        drifts = template_version.detect_drift(local, upstream)
        assert len(drifts) == 0

    def test_drift_outdated_template(self):
        """Detect drift when local is outdated."""
        local = {
            "spec-template": template_version.TemplateVersion(
                name="spec-template",
                version="1.0.0",
                last_updated="2026-01-01",
                breaking_changes=False,
                path=Path("/local/spec-template.md"),
            )
        }
        upstream = {
            "spec-template": template_version.TemplateVersion(
                name="spec-template",
                version="1.2.0",
                last_updated="2026-04-14",
                breaking_changes=False,
                path=Path("/upstream/spec-template.md"),
            )
        }

        drifts = template_version.detect_drift(local, upstream)

        assert len(drifts) == 1
        assert drifts[0].name == "spec-template"
        assert drifts[0].local_version == "1.0.0"
        assert drifts[0].upstream_version == "1.2.0"
        assert drifts[0].is_outdated is True
        assert drifts[0].is_missing is False
        assert drifts[0].breaking_changes is False

    def test_drift_breaking_change(self):
        """Detect breaking change flag in drift."""
        local = {
            "plan-template": template_version.TemplateVersion(
                name="plan-template",
                version="1.5.0",
                last_updated="2025-12-01",
                breaking_changes=False,
                path=Path("/local/plan-template.md"),
            )
        }
        upstream = {
            "plan-template": template_version.TemplateVersion(
                name="plan-template",
                version="2.0.0",
                last_updated="2026-04-01",
                breaking_changes=True,
                path=Path("/upstream/plan-template.md"),
            )
        }

        drifts = template_version.detect_drift(local, upstream)

        assert len(drifts) == 1
        assert drifts[0].is_outdated is True
        assert drifts[0].breaking_changes is True

    def test_drift_missing_template(self):
        """Detect missing template (exists upstream but not local)."""
        local = {}
        upstream = {
            "new-template": template_version.TemplateVersion(
                name="new-template",
                version="1.0.0",
                last_updated="2026-04-14",
                breaking_changes=False,
                path=Path("/upstream/new-template.md"),
            )
        }

        drifts = template_version.detect_drift(local, upstream)

        assert len(drifts) == 1
        assert drifts[0].is_missing is True
        assert drifts[0].is_outdated is False
        assert drifts[0].local_version is None
        assert drifts[0].upstream_version == "1.0.0"

    def test_drift_multiple_issues(self):
        """Detect multiple drift issues simultaneously."""
        local = {
            "old-template": template_version.TemplateVersion(
                name="old-template",
                version="0.9.0",
                last_updated="2025-01-01",
                breaking_changes=False,
                path=Path("/local/old-template.md"),
            ),
        }
        upstream = {
            "old-template": template_version.TemplateVersion(
                name="old-template",
                version="1.5.0",
                last_updated="2026-04-14",
                breaking_changes=False,
                path=Path("/upstream/old-template.md"),
            ),
            "new-template": template_version.TemplateVersion(
                name="new-template",
                version="1.0.0",
                last_updated="2026-04-14",
                breaking_changes=False,
                path=Path("/upstream/new-template.md"),
            ),
        }

        drifts = template_version.detect_drift(local, upstream)

        assert len(drifts) == 2
        # Check that we have both outdated and missing drifts
        has_outdated = any(d.is_outdated for d in drifts)
        has_missing = any(d.is_missing for d in drifts)
        assert has_outdated is True
        assert has_missing is True


# ---------------------------------------------------------------------------
# Integration Tests - Report Generation
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestReportGeneration:
    """Test report generation functions."""

    def test_generate_text_report_no_drift(self):
        """Text report when no drift exists."""
        report = template_version.generate_drift_report([])
        assert "✅ All templates are up-to-date!" in report

    def test_generate_text_report_with_drift(self):
        """Text report includes drift details."""
        drifts = [
            template_version.TemplateDrift(
                name="spec-template",
                local_version="1.0.0",
                upstream_version="1.2.0",
                is_outdated=True,
                is_missing=False,
                breaking_changes=False,
                local_path=Path("/local/spec-template.md"),
                upstream_path=Path("/upstream/spec-template.md"),
            ),
            template_version.TemplateDrift(
                name="new-template",
                local_version=None,
                upstream_version="1.0.0",
                is_outdated=False,
                is_missing=True,
                breaking_changes=False,
                local_path=None,
                upstream_path=Path("/upstream/new-template.md"),
            ),
        ]

        report = template_version.generate_drift_report(drifts)

        assert "Template Drift Detected" in report
        assert "spec-template" in report
        assert "1.0.0" in report
        assert "1.2.0" in report
        assert "new-template" in report

    def test_generate_json_report_structure(self):
        """JSON report has correct structure."""
        drifts = [
            template_version.TemplateDrift(
                name="spec-template",
                local_version="1.0.0",
                upstream_version="1.5.0",
                is_outdated=True,
                is_missing=False,
                breaking_changes=True,
                local_path=Path("/local/spec-template.md"),
                upstream_path=Path("/upstream/spec-template.md"),
            )
        ]

        result = template_version.generate_drift_json(drifts)

        assert "drift_detected" in result
        assert result["drift_detected"] is True
        assert "total_drifts" in result
        assert result["total_drifts"] == 1
        assert "templates" in result
        assert len(result["templates"]) == 1

        drift = result["templates"][0]
        assert drift["name"] == "spec-template"
        assert drift["local_version"] == "1.0.0"
        assert drift["upstream_version"] == "1.5.0"
        assert drift["is_outdated"] is True
        assert drift["is_missing"] is False
        assert drift["breaking_changes"] is True

    def test_generate_json_report_no_drift(self):
        """JSON report shows no drift when clean."""
        result = template_version.generate_drift_json([])

        assert result["drift_detected"] is False
        assert result["total_drifts"] == 0
        assert result["templates"] == []
