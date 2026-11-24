"""
Test for BUG-09: Symlink creation with rules/ subdirectory

Bug: scaffold --upgrade failed to create .copilot-rules.md symlink
because code was looking for file at wrong path.

Expected: .copilot-shared/rules/.copilot-rules.md
Was looking at: .copilot-shared/.copilot-rules.md

Fix: Updated scripts/lib/links.py to look in rules/ subdirectory
"""

import os
import tempfile
from pathlib import Path

from scripts.lib.config import ProjectConfig
from scripts.lib.links import setup_symlinks


def test_symlink_points_to_rules_subdirectory():
    """
    BUG-09: Symlink should point to .copilot-shared/rules/.copilot-rules.md,
    not .copilot-shared/.copilot-rules.md
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        project_dir = Path(tmpdir) / "test-project"
        project_dir.mkdir()

        shared_dir = Path(tmpdir) / ".copilot-shared"
        shared_dir.mkdir()

        # Create rules subdirectory and file
        rules_dir = shared_dir / "rules"
        rules_dir.mkdir()
        copilot_rules = rules_dir / ".copilot-rules.md"
        copilot_rules.write_text("# Test Copilot Rules\n")

        # Create config
        config = ProjectConfig(
            project_name="test-project",
            project_title="Test Project",
            description="Test",
            domain="programming",
            language="python",
            github_repo=None,
            shared_dir=shared_dir,
            target_dir=project_dir.parent,
            created_at="2026-05-12T12:00:00Z",
            extra_profiles=[],
        )

        # Execute
        results = setup_symlinks(config)

        # Assert
        assert len(results) == 1, "Should create 1 symlink"

        result = results[0]
        assert result.kind == "symlink"
        assert (
            result.status == "created"
        ), f"Expected created, got {result.status}: {result.message}"

        symlink = project_dir / ".copilot-rules.md"
        assert symlink.is_symlink(), "Symlink should be created"

        # Verify symlink points to correct location (in rules/ subdirectory)
        target = symlink.resolve()
        assert (
            target == copilot_rules
        ), f"Symlink should point to {copilot_rules}, not {target}"

        # Verify symlink is relative (portability)
        raw_target = os.readlink(symlink)
        assert not Path(
            raw_target
        ).is_absolute(), f"Symlink should be relative, got: {raw_target}"
        assert (
            "rules/.copilot-rules.md" in raw_target
        ), f"Symlink should include rules/ subdirectory: {raw_target}"


def test_symlink_skipped_when_file_missing_in_shared():
    """
    BUG-09 regression: If file is missing in shared/rules/, should skip with proper message
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup - create shared dir but NO rules subdirectory
        project_dir = Path(tmpdir) / "test-project"
        project_dir.mkdir()

        shared_dir = Path(tmpdir) / ".copilot-shared"
        shared_dir.mkdir()
        # NO rules/ subdirectory created

        config = ProjectConfig(
            project_name="test-project",
            project_title="Test Project",
            description="Test",
            domain="programming",
            language="python",
            github_repo=None,
            shared_dir=shared_dir,
            target_dir=project_dir.parent,
            created_at="2026-05-12T12:00:00Z",
            extra_profiles=[],
        )

        # Execute
        results = setup_symlinks(config)

        # Assert
        assert len(results) == 1
        result = results[0]
        assert (
            result.status == "skipped"
        ), f"Should skip when file missing, got {result.status}"
        assert (
            "ausente em shared" in result.message
        ), f"Message should mention missing file: {result.message}"

        # Symlink should NOT be created
        symlink = project_dir / ".copilot-rules.md"
        assert (
            not symlink.exists()
        ), "Symlink should not be created when source file is missing"


if __name__ == "__main__":
    print("Running BUG-09 tests...")
    test_symlink_points_to_rules_subdirectory()
    print("✅ test_symlink_points_to_rules_subdirectory PASSED")

    test_symlink_skipped_when_file_missing_in_shared()
    print("✅ test_symlink_skipped_when_file_missing_in_shared PASSED")

    print("\n🟢 All BUG-09 tests passed!")
