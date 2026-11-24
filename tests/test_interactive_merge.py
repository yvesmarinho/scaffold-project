"""
Tests for interactive merge conflict resolution.

Part of IMP-65 (Template Synchronization System) Phase 3.1.
"""

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.lib.interactive_merge import (
    ResolutionChoice,
    apply_resolution,
    count_remaining_conflicts,
    validate_resolution,
)
from scripts.lib.template_merge import ConflictRegion, MergeResult

# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_conflict():
    """Sample conflict region for testing."""
    return ConflictRegion(
        start_line=10,
        end_line=18,
        local_content="Local customization:\n- Security review section\n- Compliance notes",
        upstream_content="Upstream improvements:\n- Performance criteria\n- Cost estimation",
        region_type="both_modified",
    )


@pytest.fixture
def merge_result_with_conflicts():
    """Sample MergeResult with conflicts."""
    merged_content = textwrap.dedent("""
        # Template Header

        ## Section 1
        Normal content here.

        ## Section 2
        <<<<<<< LOCAL
        Local customization:
        - Security review section
        - Compliance notes
        ||||||| BASE
        Original content:
        - Basic requirements
        =======
        Upstream improvements:
        - Performance criteria
        - Cost estimation
        >>>>>>> UPSTREAM

        ## Section 3
        More normal content.
    """).strip()

    conflicts = [
        ConflictRegion(
            start_line=6,
            end_line=14,
            local_content="Local customization:\n- Security review section\n- Compliance notes",
            upstream_content="Upstream improvements:\n- Performance criteria\n- Cost estimation",
            region_type="both_modified",
        )
    ]

    return MergeResult(
        success=True,
        has_conflicts=True,
        merged_content=merged_content,
        conflicts=conflicts,
        local_path=Path("local.md"),
        upstream_path=Path("upstream.md"),
        base_version="1.0.0",
        local_version="1.0.0",
        upstream_version="1.5.0",
    )


# ---------------------------------------------------------------------------
# Test Resolution Application
# ---------------------------------------------------------------------------


class TestApplyResolution:
    """Test applying resolution choices to merged content."""

    def test_apply_local_resolution(self):
        """Test keeping local content."""
        merged_content = textwrap.dedent("""
            Before
            <<<<<<< LOCAL
            Local content
            ||||||| BASE
            Base content
            =======
            Upstream content
            >>>>>>> UPSTREAM
            After
        """).strip()

        conflict = ConflictRegion(
            start_line=1,
            end_line=7,
            local_content="Local content",
            upstream_content="Upstream content",
            region_type="both_modified",
        )

        resolution = ResolutionChoice(action="local")
        result = apply_resolution(merged_content, conflict, resolution)

        assert "Local content" in result
        assert "Upstream content" not in result
        assert "<<<<<<< LOCAL" not in result

    def test_apply_upstream_resolution(self):
        """Test accepting upstream content."""
        merged_content = textwrap.dedent("""
            Before
            <<<<<<< LOCAL
            Local content
            ||||||| BASE
            Base content
            =======
            Upstream content
            >>>>>>> UPSTREAM
            After
        """).strip()

        conflict = ConflictRegion(
            start_line=1,
            end_line=7,
            local_content="Local content",
            upstream_content="Upstream content",
            region_type="both_modified",
        )

        resolution = ResolutionChoice(action="upstream")
        result = apply_resolution(merged_content, conflict, resolution)

        assert "Upstream content" in result
        assert "Local content" not in result
        assert ">>>>>>> UPSTREAM" not in result

    def test_apply_both_resolution(self):
        """Test keeping both local and upstream."""
        merged_content = textwrap.dedent("""
            Before
            <<<<<<< LOCAL
            Local content
            ||||||| BASE
            Base content
            =======
            Upstream content
            >>>>>>> UPSTREAM
            After
        """).strip()

        conflict = ConflictRegion(
            start_line=1,
            end_line=7,
            local_content="Local content",
            upstream_content="Upstream content",
            region_type="both_modified",
        )

        resolution = ResolutionChoice(action="both")
        result = apply_resolution(merged_content, conflict, resolution)

        assert "Local content" in result
        assert "Upstream content" in result
        # Local should come before upstream
        assert result.index("Local") < result.index("Upstream")

    def test_apply_edit_resolution(self):
        """Test custom edited content."""
        merged_content = textwrap.dedent("""
            Before
            <<<<<<< LOCAL
            Local content
            ||||||| BASE
            Base content
            =======
            Upstream content
            >>>>>>> UPSTREAM
            After
        """).strip()

        conflict = ConflictRegion(
            start_line=1,
            end_line=7,
            local_content="Local content",
            upstream_content="Upstream content",
            region_type="both_modified",
        )

        custom = "Custom merged content combining both"
        resolution = ResolutionChoice(action="edit", custom_content=custom)
        result = apply_resolution(merged_content, conflict, resolution)

        assert custom in result
        assert "<<<<<<< LOCAL" not in result

    def test_apply_skip_resolution(self):
        """Test skipping conflict (leave markers)."""
        merged_content = textwrap.dedent("""
            Before
            <<<<<<< LOCAL
            Local content
            ||||||| BASE
            Base content
            =======
            Upstream content
            >>>>>>> UPSTREAM
            After
        """).strip()

        conflict = ConflictRegion(
            start_line=1,
            end_line=7,
            local_content="Local content",
            upstream_content="Upstream content",
            region_type="both_modified",
        )

        resolution = ResolutionChoice(action="skip")
        result = apply_resolution(merged_content, conflict, resolution)

        # Markers should still be present
        assert "<<<<<<< LOCAL" in result
        assert ">>>>>>> UPSTREAM" in result


# ---------------------------------------------------------------------------
# Test Validation
# ---------------------------------------------------------------------------


class TestValidation:
    """Test conflict validation functions."""

    def test_count_remaining_conflicts(self):
        """Test counting conflict markers."""
        content_no_conflicts = "Normal content without conflicts"
        assert count_remaining_conflicts(content_no_conflicts) == 0

        content_one_conflict = textwrap.dedent("""
            <<<<<<< LOCAL
            Local
            =======
            Upstream
            >>>>>>> UPSTREAM
        """)
        assert count_remaining_conflicts(content_one_conflict) == 1

        content_multiple = textwrap.dedent("""
            <<<<<<< LOCAL
            Local 1
            >>>>>>> UPSTREAM
            Some content
            <<<<<<< LOCAL
            Local 2
            >>>>>>> UPSTREAM
        """)
        assert count_remaining_conflicts(content_multiple) == 2

    def test_validate_resolution_clean(self):
        """Test validation with no remaining conflicts."""
        clean_content = textwrap.dedent("""
            # Template

            ## Section 1
            All conflicts resolved.

            ## Section 2
            No markers present.
        """)

        is_valid, errors = validate_resolution(clean_content)
        assert is_valid
        assert len(errors) == 0

    def test_validate_resolution_with_markers(self):
        """Test validation with remaining conflict markers."""
        content_with_markers = textwrap.dedent("""
            # Template

            <<<<<<< LOCAL
            Unresolved conflict
            =======
            Still here
            >>>>>>> UPSTREAM
        """)

        is_valid, errors = validate_resolution(content_with_markers)
        assert not is_valid
        assert len(errors) > 0
        assert any("<<<<<<< LOCAL" in error for error in errors)

    def test_validate_resolution_partial_markers(self):
        """Test validation with partial conflict markers."""
        # Test each marker type
        markers = ["<<<<<<< LOCAL", "||||||| BASE", "=======", ">>>>>>> UPSTREAM"]

        for marker in markers:
            content = f"Normal content\n{marker}\nMore content"
            is_valid, errors = validate_resolution(content)
            assert not is_valid
            assert any(marker in error for error in errors)


# ---------------------------------------------------------------------------
# Test Resolution Choice
# ---------------------------------------------------------------------------


class TestResolutionChoice:
    """Test ResolutionChoice dataclass."""

    def test_create_local_choice(self):
        """Test creating local resolution choice."""
        choice = ResolutionChoice(action="local")
        assert choice.action == "local"
        assert choice.custom_content is None

    def test_create_edit_choice(self):
        """Test creating edit resolution with custom content."""
        custom = "My custom resolution"
        choice = ResolutionChoice(action="edit", custom_content=custom)
        assert choice.action == "edit"
        assert choice.custom_content == custom


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestInteractiveResolution:
    """Test interactive resolution workflow (mocked input)."""

    @patch("scripts.lib.interactive_merge.Prompt.ask")
    @patch("scripts.lib.interactive_merge.Confirm.ask")
    def test_resolve_single_conflict_local(
        self, mock_confirm, mock_prompt, merge_result_with_conflicts
    ):
        """Test resolving single conflict choosing local."""
        # Mock user choosing to proceed and selecting local
        mock_confirm.return_value = True
        mock_prompt.return_value = "l"

        from scripts.lib.interactive_merge import resolve_conflicts_interactively

        resolved_content, all_resolved = resolve_conflicts_interactively(
            merge_result_with_conflicts
        )

        assert all_resolved
        assert "Security review section" in resolved_content
        assert "Performance criteria" not in resolved_content
        assert "<<<<<<< LOCAL" not in resolved_content

    @patch("scripts.lib.interactive_merge.Prompt.ask")
    @patch("scripts.lib.interactive_merge.Confirm.ask")
    def test_resolve_single_conflict_upstream(
        self, mock_confirm, mock_prompt, merge_result_with_conflicts
    ):
        """Test resolving single conflict choosing upstream."""
        mock_confirm.return_value = True
        mock_prompt.return_value = "u"

        from scripts.lib.interactive_merge import resolve_conflicts_interactively

        resolved_content, all_resolved = resolve_conflicts_interactively(
            merge_result_with_conflicts
        )

        assert all_resolved
        assert "Performance criteria" in resolved_content
        assert "Security review section" not in resolved_content
        assert ">>>>>>> UPSTREAM" not in resolved_content

    @patch("scripts.lib.interactive_merge.Prompt.ask")
    @patch("scripts.lib.interactive_merge.Confirm.ask")
    def test_resolve_conflict_skip(
        self, mock_confirm, mock_prompt, merge_result_with_conflicts
    ):
        """Test skipping conflict resolution."""
        mock_confirm.return_value = True
        mock_prompt.return_value = "s"

        from scripts.lib.interactive_merge import resolve_conflicts_interactively

        resolved_content, all_resolved = resolve_conflicts_interactively(
            merge_result_with_conflicts
        )

        assert not all_resolved  # Skipped, so not all resolved
        assert "<<<<<<< LOCAL" in resolved_content  # Markers still present

    @patch("scripts.lib.interactive_merge.Confirm.ask")
    def test_cancel_interactive_resolution(
        self, mock_confirm, merge_result_with_conflicts
    ):
        """Test cancelling interactive resolution."""
        mock_confirm.return_value = False

        from scripts.lib.interactive_merge import resolve_conflicts_interactively

        resolved_content, all_resolved = resolve_conflicts_interactively(
            merge_result_with_conflicts
        )

        assert not all_resolved
        assert resolved_content == merge_result_with_conflicts.merged_content


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_apply_resolution_out_of_bounds(self):
        """Test applying resolution with invalid line numbers."""
        merged_content = "Line 1\nLine 2\nLine 3"

        conflict = ConflictRegion(
            start_line=100,  # Out of bounds
            end_line=200,
            local_content="Local",
            upstream_content="Upstream",
            region_type="both_modified",
        )

        resolution = ResolutionChoice(action="local")
        result = apply_resolution(merged_content, conflict, resolution)

        # Should return original content unchanged
        assert result == merged_content

    def test_count_conflicts_empty_content(self):
        """Test counting conflicts in empty content."""
        assert count_remaining_conflicts("") == 0

    def test_validate_empty_content(self):
        """Test validating empty content."""
        is_valid, errors = validate_resolution("")
        assert is_valid
        assert len(errors) == 0
