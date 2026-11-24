"""
Test suite for IMP-65 Fase 3: Template Merge and Three-Way Merge.

Tests cover:
- Three-way merge execution
- Conflict detection and parsing
- Conflict resolution suggestions
- Backup creation
- Merge application
- Template base storage/retrieval
"""

from pathlib import Path
from textwrap import dedent

import pytest

from scripts.lib import template_merge, template_version

# ---------------------------------------------------------------------------
# Unit Tests - Three-Way Merge
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestThreeWayMerge:
    """Test three-way merge functionality."""

    def test_clean_merge_no_conflicts(self):
        """Merge with independent changes should succeed without conflicts."""
        base = dedent("""
            Line 1
            Line 2
            Line 3
        """).strip()

        local = dedent("""
            Line 1 MODIFIED
            Line 2
            Line 3
        """).strip()

        upstream = dedent("""
            Line 1
            Line 2
            Line 3 IMPROVED
        """).strip()

        success, merged, has_conflicts = template_merge.three_way_merge(
            base, local, upstream, "test.md"
        )

        assert success is True
        assert has_conflicts is False
        assert "Line 1 MODIFIED" in merged
        assert "Line 3 IMPROVED" in merged

    def test_merge_with_conflicts(self):
        """Merge with conflicting changes should  detect conflicts."""
        base = "Line 1\nLine 2\nLine 3\n"
        local = "Line 1\nLINE 2 LOCAL\nLine 3\n"
        upstream = "Line 1\nLINE 2 UPSTREAM\nLine 3\n"

        success, merged, has_conflicts = template_merge.three_way_merge(
            base, local, upstream, "test.md"
        )

        assert success is True
        assert has_conflicts is True
        assert "<<<<<<< LOCAL" in merged
        assert ">>>>>>> UPSTREAM" in merged

    def test_merge_identical_content(self):
        """Merge of identical content should succeed without changes."""
        content = "Line 1\nLine 2\nLine 3\n"

        success, merged, has_conflicts = template_merge.three_way_merge(
            content, content, content, "test.md"
        )

        assert success is True
        assert has_conflicts is False
        assert merged == content


# ---------------------------------------------------------------------------
# Unit Tests - Conflict Detection
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConflictDetection:
    """Test conflict parsing and detection."""

    def test_detect_conflicts_none(self):
        """Content without conflict markers should have no conflicts."""
        content = "Line 1\nLine 2\nLine 3\n"

        conflicts = template_merge.detect_conflicts(content)

        assert len(conflicts) == 0

    def test_detect_conflicts_single(self):
        """Single conflict region should be detected."""
        content = dedent("""
            Line 1
            <<<<<<< LOCAL
            local change
            ||||||| BASE
            original
            =======
            upstream change
            >>>>>>> UPSTREAM
            Line 2
        """).strip()

        conflicts = template_merge.detect_conflicts(content)

        assert len(conflicts) == 1
        assert conflicts[0].local_content == "local change"
        assert conflicts[0].upstream_content == "upstream change"

    def test_detect_conflicts_multiple(self):
        """Multiple conflict regions should all be detected."""
        content = dedent("""
            <<<<<<< LOCAL
            conflict 1 local
            ||||||| BASE
            base 1
            =======
            conflict 1 upstream
            >>>>>>> UPSTREAM
            middle content
            <<<<<<< LOCAL
            conflict 2 local
            ||||||| BASE
            base 2
            =======
            conflict 2 upstream
            >>>>>>> UPSTREAM
        """).strip()

        conflicts = template_merge.detect_conflicts(content)

        assert len(conflicts) == 2

    def test_conflict_type_both_modified(self):
        """Conflict with base content should be 'both_modified'."""
        content = dedent("""
            <<<<<<< LOCAL
            local
            ||||||| BASE
            base
            =======
            upstream
            >>>>>>> UPSTREAM
        """).strip()

        conflicts = template_merge.detect_conflicts(content)

        assert len(conflicts) == 1
        assert conflicts[0].region_type == "both_modified"


# ---------------------------------------------------------------------------
# Unit Tests - Conflict Analysis
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConflictAnalysis:
    """Test conflict resolution suggestions."""

    def test_analyze_both_modified(self):
        """Both-modified conflicts should suggest careful review."""
        conflict = template_merge.ConflictRegion(
            start_line=1,
            end_line=5,
            local_content="local",
            upstream_content="upstream",
            region_type="both_modified",
        )

        suggestion = template_merge.analyze_conflict(conflict)

        assert "Both local and upstream modified" in suggestion
        assert "Review carefully" in suggestion

    def test_analyze_local_added(self):
        """Local-only additions should suggest keeping local."""
        conflict = template_merge.ConflictRegion(
            start_line=1,
            end_line=3,
            local_content="custom section",
            upstream_content="",
            region_type="local_added",
        )

        suggestion = template_merge.analyze_conflict(conflict)

        assert "Local customization" in suggestion
        assert "Keep local" in suggestion


# ---------------------------------------------------------------------------
# Unit Tests - Backup Creation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBackupCreation:
    """Test backup file creation."""

    def test_create_backup(self, tmp_path: Path):
        """Backup should create timestamped copy."""
        original = tmp_path / "template.md"
        original.write_text("original content\n", encoding="utf-8")

        backup_path = template_merge.create_backup(original)

        assert backup_path.exists()
        assert backup_path != original
        assert "backup" in backup_path.name
        assert backup_path.read_text() == "original content\n"


# ---------------------------------------------------------------------------
# Unit Tests - Template Base Storage
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTemplateBaseStorage:
    """Test template base save/load functionality."""

    def test_save_and_load_base(self, tmp_path: Path):
        """Saved base should be retrievable."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        # Create minimal state file
        state_file = project_dir / ".scaffold-state.yaml"
        state_file.write_text("scaffold_version: '1.0.0'\n", encoding="utf-8")

        # Save base
        template_version.save_template_base(
            project_dir=project_dir,
            template_name="spec-template.md",
            version="1.0.0",
            content="# Spec Template\nContent",
        )

        # Load base
        result = template_version.load_template_base(project_dir, "spec-template.md")

        assert result is not None
        version, content = result
        assert version == "1.0.0"
        assert content == "# Spec Template\nContent"

    def test_load_nonexistent_base(self, tmp_path: Path):
        """Loading nonexistent base should return None."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        result = template_version.load_template_base(project_dir, "missing.md")

        assert result is None

    def test_save_all_template_bases(self, tmp_path: Path):
        """Save all templates in a directory."""
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create state file
        state_file = project_dir / ".scaffold-state.yaml"
        state_file.write_text("scaffold_version: '1.0.0'\n", encoding="utf-8")

        # Create test templates
        (template_dir / "spec-template.md").write_text(
            dedent("""
                ---
                template_version: "1.0.0"
                last_updated: "2026-04-14"
                breaking_changes: false
                ---
                # Spec
            """).strip(),
            encoding="utf-8",
        )

        (template_dir / "plan-template.md").write_text(
            dedent("""
                ---
                template_version: "1.0.0"
                last_updated: "2026-04-14"
                breaking_changes: false
                ---
                # Plan
            """).strip(),
            encoding="utf-8",
        )

        count = template_version.save_all_template_bases(project_dir, template_dir)

        assert count == 2

        # Verify both were saved
        spec_base = template_version.load_template_base(project_dir, "spec-template.md")
        plan_base = template_version.load_template_base(project_dir, "plan-template.md")

        assert spec_base is not None
        assert plan_base is not None


# ---------------------------------------------------------------------------
# Integration Tests - Full Merge
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFullMerge:
    """Test complete merge workflow."""

    def test_merge_templates_clean(self, tmp_path: Path):
        """Clean merge should succeed and update file."""
        base_content = "Line 1\nLine 2\nLine 3\n"
        local_content = "Line 1 LOCAL\nLine 2\nLine 3\n"
        upstream_content = "Line 1\nLine 2\nLine 3 UPSTREAM\n"

        local = tmp_path / "local.md"
        upstream = tmp_path / "upstream.md"
        local.write_text(local_content, encoding="utf-8")
        upstream.write_text(upstream_content, encoding="utf-8")

        result = template_merge.merge_templates(
            local_path=local,
            upstream_path=upstream,
            base_content=base_content,
            base_version="1.0.0",
            local_version="1.0.0",
            upstream_version="1.5.0",
            apply=True,
            backup=True,
        )

        assert result.success is True
        assert result.has_conflicts is False
        assert result.backup_path is not None
        assert result.backup_path.exists()

        # Verify merged content
        merged = local.read_text()
        assert "Line 1 LOCAL" in merged
        assert "Line 3 UPSTREAM" in merged

    def test_merge_templates_with_conflicts(self, tmp_path: Path):
        """Merge with conflicts should not auto-apply."""
        base_content = "Line 1\n"
        local_content = "Line 1 LOCAL\n"
        upstream_content = "Line 1 UPSTREAM\n"

        local = tmp_path / "local.md"
        upstream = tmp_path / "upstream.md"
        local.write_text(local_content, encoding="utf-8")
        upstream.write_text(upstream_content, encoding="utf-8")

        result = template_merge.merge_templates(
            local_path=local,
            upstream_path=upstream,
            base_content=base_content,
            base_version="1.0.0",
            local_version="1.0.0",
            upstream_version="1.5.0",
            apply=False,
            backup=True,
        )

        assert result.success is True
        assert result.has_conflicts is True
        assert len(result.conflicts) > 0
        # File should not be modified when apply=False
        assert local.read_text() == local_content

    def test_conflict_report_generation(self, tmp_path: Path):
        """Conflict report should be informative."""
        base_content = "Line 1\n"
        local_content = "Line 1 LOCAL\n"
        upstream_content = "Line 1 UPSTREAM\n"

        local = tmp_path / "local.md"
        upstream = tmp_path / "upstream.md"
        local.write_text(local_content, encoding="utf-8")
        upstream.write_text(upstream_content, encoding="utf-8")

        result = template_merge.merge_templates(
            local_path=local,
            upstream_path=upstream,
            base_content=base_content,
            base_version="1.0.0",
            local_version="1.0.0",
            upstream_version="1.5.0",
            apply=False,
        )

        report = template_merge.format_conflict_report(result)

        assert "conflict(s) detected" in report
        assert "To resolve conflicts" in report
