"""
Test suite for IMP-65 Fase 2: Template Diff and Visualization.

Tests cover:
- Unified diff generation
- HTML diff generation
- Diff statistics calculation
- Customization detection
- Impact report generation
- Output formatting (colored and markdown)
"""

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.lib import template_diff

# ---------------------------------------------------------------------------
# Unit Tests - Diff Generation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDiffGeneration:
    """Test diff generation functions."""

    def test_unified_diff_identical_content(self, tmp_path: Path):
        """Unified diff of identical content should be empty."""
        content = "Line 1\nLine 2\nLine 3\n"
        local = tmp_path / "local.md"
        upstream = tmp_path / "upstream.md"
        local.write_text(content)
        upstream.write_text(content)

        diff = template_diff.generate_unified_diff(content, content, local, upstream)

        assert diff == ""

    def test_unified_diff_added_lines(self, tmp_path: Path):
        """Unified diff should show added lines with + prefix."""
        local_content = "Line 1\nLine 2\n"
        upstream_content = "Line 1\nLine 2\nLine 3\n"
        local = tmp_path / "local.md"
        upstream = tmp_path / "upstream.md"

        diff = template_diff.generate_unified_diff(
            local_content, upstream_content, local, upstream
        )

        assert "+Line 3" in diff
        assert "@@" in diff  # Chunk header

    def test_unified_diff_removed_lines(self, tmp_path: Path):
        """Unified diff should show removed lines with - prefix."""
        local_content = "Line 1\nLine 2\nLine 3\n"
        upstream_content = "Line 1\nLine 3\n"
        local = tmp_path / "local.md"
        upstream = tmp_path / "upstream.md"

        diff = template_diff.generate_unified_diff(
            local_content, upstream_content, local, upstream
        )

        assert "-Line 2" in diff

    def test_calculate_diff_stats_no_changes(self):
        """Stats for empty diff should all be zero."""
        stats = template_diff.calculate_diff_stats("")

        assert stats["lines_added"] == 0
        assert stats["lines_removed"] == 0
        assert stats["lines_changed"] == 0
        assert stats["total_changes"] == 0

    def test_calculate_diff_stats_only_additions(self):
        """Stats should correctly count pure additions."""
        diff = dedent("""
            --- local
            +++ upstream
            @@ -1,2 +1,4 @@
             Line 1
             Line 2
            +Line 3
            +Line 4
        """).strip()

        stats = template_diff.calculate_diff_stats(diff)

        assert stats["lines_added"] == 2
        assert stats["lines_removed"] == 0
        assert stats["lines_changed"] == 0
        assert stats["total_changes"] == 2

    def test_calculate_diff_stats_mixed_changes(self):
        """Stats should correctly identify changes vs additions/removals."""
        diff = dedent("""
            --- local
            +++ upstream
            @@ -1,4 +1,4 @@
             Line 1
            -Line 2
            +Line 2 modified
             Line 3
            +Line 4
        """).strip()

        stats = template_diff.calculate_diff_stats(diff)

        # 1 change (Line 2), 1 pure addition (Line 4)
        assert stats["lines_changed"] == 1
        assert stats["lines_added"] == 1
        assert stats["lines_removed"] == 0
        assert stats["total_changes"] == 3  # 1 + 1 + 1


# ---------------------------------------------------------------------------
# Unit Tests - Customization Detection
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCustomizationDetection:
    """Test customization detection heuristics."""

    def test_no_customizations_identical_content(self):
        """Identical content should have no customizations."""
        content = "Line 1\nLine 2\nLine 3\n"

        result = template_diff.detect_customizations(content, content)

        assert result is False

    def test_no_customizations_version_metadata_only(self):
        """Version metadata differences don't count as customizations."""
        local = dedent("""
            ---
            template_version: "1.0.0"
            last_updated: "2026-01-01"
            ---
            # Template
            Content here
        """).strip()

        upstream = dedent("""
            ---
            template_version: "1.5.0"
            last_updated: "2026-04-14"
            ---
            # Template
            Content here
        """).strip()

        result = template_diff.detect_customizations(local, upstream)

        # Should be False because only frontmatter differs
        # (heuristic: filters out version metadata lines)
        assert result is False

    def test_customizations_detected_extra_content(self):
        """Local content with extra lines should be detected as customized."""
        local = dedent("""
            # Template
            Standard content

            ## Custom Section
            My custom notes here
        """).strip()

        upstream = dedent("""
            # Template
            Standard content
        """).strip()

        result = template_diff.detect_customizations(local, upstream)

        assert result is True

    def test_customizations_detected_modified_content(self):
        """Modified lines should be detected as customizations."""
        local = "Line 1\nLine 2 CUSTOM\nLine 3\n"
        upstream = "Line 1\nLine 2\nLine 3\n"

        result = template_diff.detect_customizations(local, upstream)

        assert result is True


# ---------------------------------------------------------------------------
# Unit Tests - Impact Report
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestImpactReport:
    """Test impact report generation."""

    def test_impact_report_structure(self):
        """Impact report should have all required sections."""
        stats = {
            "lines_added": 5,
            "lines_removed": 2,
            "lines_changed": 3,
            "total_changes": 10,
        }

        report = template_diff.generate_impact_report(
            template_name="spec-template.md",
            local_version="1.0.0",
            upstream_version="1.5.0",
            stats=stats,
            customizations_detected=True,
        )

        assert "Impact Report" in report
        assert "spec-template.md" in report
        assert "1.0.0" in report
        assert "1.5.0" in report
        assert "+ 5 lines added" in report
        assert "- 2 lines removed" in report
        assert "~ 3 lines modified" in report
        assert "Customizations Detected" in report
        assert "Recommendations" in report

    def test_impact_report_no_customizations(self):
        """Report should suggest safe update when no customizations."""
        stats = {
            "lines_added": 3,
            "lines_removed": 0,
            "lines_changed": 1,
            "total_changes": 4,
        }

        report = template_diff.generate_impact_report(
            template_name="plan-template.md",
            local_version="2.0.0",
            upstream_version="2.1.0",
            stats=stats,
            customizations_detected=False,
        )

        assert "No Customizations Detected" in report
        assert "Safe to update automatically" in report


# ---------------------------------------------------------------------------
# Integration Tests - Full Diff
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFullDiff:
    """Test complete diff workflow."""

    def test_diff_templates_identical(self, tmp_path: Path):
        """Diff of identical templates should show no differences."""
        content = dedent("""
            ---
            template_version: "1.0.0"
            ---
            # Template
            Content
        """).strip()

        local = tmp_path / "spec-template.md"
        upstream = tmp_path / "spec-template.md"
        local.write_text(content)

        result = template_diff.diff_templates(
            local_path=local,
            upstream_path=upstream,
            local_version="1.0.0",
            upstream_version="1.0.0",
        )

        assert result.template_name == "spec-template.md"
        assert result.has_differences is False
        assert result.stats["total_changes"] == 0
        assert result.customizations_detected is False

    def test_diff_templates_upstream_changes(self, tmp_path: Path):
        """Diff should detect upstream improvements."""
        local_content = dedent("""
            ---
            template_version: "1.0.0"
            ---
            # Specification
            ## Overview
            Basic content
        """).strip()

        upstream_content = dedent("""
            ---
            template_version: "1.5.0"
            ---
            # Specification
            ## Overview
            Basic content

            ## Performance Criteria
            New section added in v1.5
        """).strip()

        local = tmp_path / "spec-template.md"
        upstream = tmp_path / "upstream-spec-template.md"
        local.write_text(local_content)
        upstream.write_text(upstream_content)

        result = template_diff.diff_templates(
            local_path=local,
            upstream_path=upstream,
            local_version="1.0.0",
            upstream_version="1.5.0",
        )

        assert result.has_differences is True
        assert result.stats["lines_added"] > 0
        assert "Performance Criteria" in result.unified_diff

    def test_diff_templates_with_customizations(self, tmp_path: Path):
        """Diff should detect custom local modifications."""
        local_content = dedent("""
            ---
            template_version: "1.0.0"
            ---
            # Specification

            ## Custom Security Review
            My custom section
        """).strip()

        upstream_content = dedent("""
            ---
            template_version: "1.0.0"
            ---
            # Specification
        """).strip()

        local = tmp_path / "spec-template.md"
        upstream = tmp_path / "upstream-spec-template.md"
        local.write_text(local_content)
        upstream.write_text(upstream_content)

        result = template_diff.diff_templates(
            local_path=local,
            upstream_path=upstream,
            local_version="1.0.0",
            upstream_version="1.0.0",
        )

        assert result.customizations_detected is True
        # Impact report should mention customizations
        assert (
            "Customizations Detected" in result.impact_report
            or "customizations" in result.impact_report.lower()
        )
        # The actual custom content should be in the unified diff
        assert "Custom Security Review" in result.unified_diff
        upstream = tmp_path / "upstream.md"
        local.write_text("Line 1\nLine 2\n")
        upstream.write_text("Line 1\nLine 2\nLine 3\n")

        diff_result = template_diff.diff_templates(local, upstream, "1.0.0", "1.2.0")
        markdown = template_diff.format_diff_markdown(diff_result)

        # Should have markdown headers
        assert "# Template Diff" in markdown
        assert "## Metadata" in markdown
        assert "## Statistics" in markdown
        assert "## Diff" in markdown
        assert "## Impact Report" in markdown
        # Should have code fence for diff
        assert "```diff" in markdown

    def test_format_diff_markdown_no_ansi(self, tmp_path: Path):
        """Markdown output should not contain ANSI codes."""
        local = tmp_path / "local.md"
        upstream = tmp_path / "upstream.md"
        local.write_text("Content\n")
        upstream.write_text("Content\n")

        diff_result = template_diff.diff_templates(local, upstream, "1.0.0", "1.0.0")
        markdown = template_diff.format_diff_markdown(diff_result)

        # Should NOT have ANSI codes
        assert "\033[" not in markdown
