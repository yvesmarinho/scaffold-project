"""
Tests for BUG-03: template_bases initialization during compose.

Validates that write_scaffold_state() properly saves template bases
to .scaffold-state.yaml, enabling three-way merge functionality.
"""

import tempfile

import pytest
import yaml

from scripts.lib.project import ProjectConfig, write_scaffold_state


def test_write_scaffold_state_saves_template_bases(tmp_path):
    """
    Test that write_scaffold_state saves template_bases to .scaffold-state.yaml.

    This is the fix for BUG-03: template bases must be saved during project
    creation to enable three-way merge functionality (IMP-65 Phase 3).
    """
    # Create test project structure
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create .specify/templates directory with a template
    templates_dir = project_dir / ".specify" / "templates"
    templates_dir.mkdir(parents=True)

    # Create a minimal template with version metadata
    spec_template = templates_dir / "spec-template.md"
    spec_template.write_text(
        "---\n"
        "template_version: \"1.0.0\"\n"
        "last_updated: \"2026-04-23\"\n"
        "breaking_changes: false\n"
        "---\n\n"
        "# Test Template\n\n"
        "This is a test template.\n",
        encoding="utf-8"
    )

    # Create ProjectConfig
    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="Test",
        domain="programming",
        language="python",
        target_dir=tmp_path,
        shared_dir=tmp_path / "shared",
        github_repo="",
        created_at="2026-04-23T10:00:00Z",
    )

    # Call write_scaffold_state (which should save template_bases)
    result = write_scaffold_state(config, profiles_applied=["python-fastapi"])

    assert result.status == "created"

    # Verify .scaffold-state.yaml was created
    state_path = project_dir / ".scaffold-state.yaml"
    assert state_path.exists()

    # Load and verify state content
    with state_path.open(encoding="utf-8") as f:
        state = yaml.safe_load(f)

    # Verify template_versions exists (IMP-65 Phase 1)
    assert "template_versions" in state
    assert "spec-template.md" in state["template_versions"]
    assert state["template_versions"]["spec-template.md"] == "1.0.0"

    # BUG-03 FIX: Verify template_bases exists (IMP-65 Phase 3)
    assert "template_bases" in state, "template_bases missing from .scaffold-state.yaml (BUG-03)"
    assert "spec-template.md" in state["template_bases"]

    # Verify base content structure
    base_data = state["template_bases"]["spec-template.md"]
    assert "version" in base_data
    assert "content" in base_data
    assert base_data["version"] == "1.0.0"
    assert "# Test Template" in base_data["content"]
    assert "template_version:" in base_data["content"]


def test_write_scaffold_state_handles_missing_templates_gracefully(tmp_path):
    """
    Test that write_scaffold_state doesn't fail if .specify/templates doesn't exist.
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="Test",
        domain="programming",
        language="python",
        target_dir=tmp_path,
        shared_dir=tmp_path / "shared",
        github_repo="",
        created_at="2026-04-23T10:00:00Z",
    )

    # Call without templates directory
    result = write_scaffold_state(config)

    assert result.status == "created"

    # Verify state file created
    state_path = project_dir / ".scaffold-state.yaml"
    assert state_path.exists()

    with state_path.open(encoding="utf-8") as f:
        state = yaml.safe_load(f)

    # Should have empty template_versions and template_bases
    assert state["template_versions"] == {}
    # template_bases might not exist if no templates were found
    # (this is acceptable - saves aren't called if no templates)


def test_write_scaffold_state_saves_multiple_template_bases(tmp_path):
    """
    Test that all templates in .specify/templates get their bases saved.
    """
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    templates_dir = project_dir / ".specify" / "templates"
    templates_dir.mkdir(parents=True)

    # Create multiple templates
    templates = {
        "spec-template.md": "1.0.0",
        "plan-template.md": "1.0.0",
        "tasks-template.md": "1.0.0",
    }

    for name, version in templates.items():
        template_path = templates_dir / name
        template_path.write_text(
            f"---\n"
            f"template_version: \"{version}\"\n"
            f"last_updated: \"2026-04-23\"\n"
            f"breaking_changes: false\n"
            f"---\n\n"
            f"# {name}\n",
            encoding="utf-8"
        )

    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="Test",
        domain="programming",
        language="python",
        target_dir=tmp_path,
        shared_dir=tmp_path / "shared",
        github_repo="",
        created_at="2026-04-23T10:00:00Z",
    )

    result = write_scaffold_state(config)
    assert result.status == "created"

    # Verify all templates have bases saved
    state_path = project_dir / ".scaffold-state.yaml"
    with state_path.open(encoding="utf-8") as f:
        state = yaml.safe_load(f)

    assert "template_bases" in state

    for name, version in templates.items():
        assert name in state["template_bases"], f"{name} missing from template_bases"
        assert state["template_bases"][name]["version"] == version
        assert name in state["template_bases"][name]["content"]


def test_bug03_regression_compose_creates_template_bases(tmp_path):
    """
    Regression test for BUG-03: Verify compose flow creates template_bases.

    This test simulates the exact scenario where BUG-03 was discovered:
    1. Create a new project with compose
    2. Try to merge a template
    3. Should work without "No base template stored" error

    This is an integration-style test that validates the complete fix.
    """
    # This test validates that the fix in write_scaffold_state() works
    # in the actual compose flow. We test the underlying function here.
    # Full end-to-end test would require running scaffold.py compose.

    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    templates_dir = project_dir / ".specify" / "templates"
    templates_dir.mkdir(parents=True)

    spec_template = templates_dir / "spec-template.md"
    spec_template.write_text(
        "---\n"
        "template_version: \"1.0.0\"\n"
        "last_updated: \"2026-04-14\"\n"
        "breaking_changes: false\n"
        "---\n\n"
        "# Feature Specification\n",
        encoding="utf-8"
    )

    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="Test",
        domain="programming",
        language="python",
        target_dir=tmp_path,
        shared_dir=tmp_path / "shared",
        github_repo="",
        created_at="2026-04-23T10:00:00Z",
    )

    # Simulate compose flow: write_scaffold_state is called
    write_scaffold_state(config, profiles_applied=["python-fastapi"])

    # Verify we can load the base (this is what merge-template does)
    from scripts.lib.template_version import load_template_base

    base_data = load_template_base(project_dir, "spec-template.md")

    # This should NOT be None (BUG-03 would cause None here)
    assert base_data is not None, "BUG-03 regression: template base not saved"

    version, content = base_data
    assert version == "1.0.0"
    assert "# Feature Specification" in content
