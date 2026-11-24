#!/usr/bin/env python3
"""
Tests for template_migration.py - Template migration to modular system.

Part of IMP-65 Phase 4.4: Migration & Compatibility
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "lib"))

from template_migration import (
    CustomSection,
    MigrationReport,
    TemplateMigrator,
    list_templates,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    project = tmp_path / "project"
    project.mkdir()

    # Create directories
    (project / "templates").mkdir()
    (project / ".specify" / "blocks").mkdir(parents=True)
    (project / ".specify" / "patches").mkdir(parents=True)

    return project


@pytest.fixture
def migrator(temp_project):
    """Create a TemplateMigrator instance."""
    return TemplateMigrator(temp_project)


@pytest.fixture
def sample_monolithic_template():
    """Sample monolithic template with standard and custom sections."""
    return """---
template_type: spec
version: 1.0.0
---

# Objetivo

Business objective goes here.

## User Scenarios

Standard user scenarios section.

## My Custom Section

This is a custom section added by the user.
It should be detected and converted to a patch.

## Success Criteria

Standard success criteria.

## Another Custom Part

More custom content here.
Multiple lines of custom text.

## Out of Scope

Standard out of scope section.
"""


@pytest.fixture
def sample_standard_template():
    """Sample template with only standard sections."""
    return """---
template_type: spec
version: 1.0.0
---

# Objetivo

Business objective.

## User Scenarios

User scenarios content.

## Success Criteria

Success criteria content.

## Out of Scope

Out of scope content.
"""


# ============================================================================
# TemplateMigrator Tests
# ============================================================================


def test_migrator_initialization(temp_project):
    """Test migrator initializes with correct paths."""
    migrator = TemplateMigrator(temp_project)

    assert migrator.project_root == temp_project
    assert migrator.templates_dir == temp_project / "templates"
    assert migrator.blocks_dir == temp_project / ".specify" / "blocks"
    assert migrator.patches_dir == temp_project / ".specify" / "patches"
    assert migrator.backups_dir == temp_project / ".specify" / "migration-backups"


def test_backup_template(migrator, temp_project):
    """Test template backup creation."""
    # Create a template
    template_path = temp_project / "templates" / "test.md"
    template_path.write_text("# Test Content")

    # Backup it
    backup_path = migrator.backup_template(template_path)

    # Verify backup exists
    assert backup_path.exists()
    assert backup_path.parent == migrator.backups_dir
    assert "test_" in backup_path.name
    assert backup_path.read_text() == "# Test Content"


def test_detect_standard_sections(migrator, sample_standard_template):
    """Test detection of standard template sections."""
    sections = migrator.detect_standard_sections(sample_standard_template)

    assert "# Objetivo" in sections
    assert "## User Scenarios" in sections
    assert "## Success Criteria" in sections
    assert "## Out of Scope" in sections


def test_extract_custom_sections(migrator, sample_monolithic_template):
    """Test extraction of custom sections from template."""
    standard = migrator.detect_standard_sections(sample_monolithic_template)
    custom = migrator.extract_custom_sections(sample_monolithic_template, standard)

    assert len(custom) == 2

    # Check first custom section
    assert custom[0].header == "## My Custom Section"
    assert "custom section added by the user" in custom[0].content

    # Check second custom section
    assert custom[1].header == "## Another Custom Part"
    assert "Multiple lines" in custom[1].content


def test_extract_custom_sections_empty(migrator, sample_standard_template):
    """Test extraction with no custom sections."""
    standard = migrator.detect_standard_sections(sample_standard_template)
    custom = migrator.extract_custom_sections(sample_standard_template, standard)

    assert len(custom) == 0


def test_custom_section_line_numbers(migrator):
    """Test custom sections have correct line numbers."""
    content = """# Objetivo

Content

## Standard Section

Standard content

## Custom Section

Custom content

## Another Standard

More standard
"""

    standard = {"# Objetivo", "## Standard Section", "## Another Standard"}
    custom = migrator.extract_custom_sections(content, standard)

    assert len(custom) == 1
    assert custom[0].header == "## Custom Section"
    assert custom[0].line_start > 0
    assert custom[0].line_end > custom[0].line_start


def test_generate_patch_from_section(migrator):
    """Test patch generation from custom section."""
    section = CustomSection(
        header="## My Custom Section",
        content="## My Custom Section\n\nCustom content here.\n",
        line_start=10,
        line_end=13,
        context_before="## User Scenarios\n\nUser scenarios content.",
        context_after="## Success Criteria\n\nSuccess criteria.",
    )

    filename, content = migrator.generate_patch_from_section(
        section, "spec-template", 1
    )

    # Check filename
    assert filename == "001-custom-my-custom-section.patch"

    # Check content structure
    assert content.startswith("---\n")
    assert "@@ AFTER: ## User Scenarios" in content or "@@ PREPEND: START" in content
    assert "@@ END" in content
    assert "Custom content here" in content

    # Parse and validate frontmatter
    parts = content.split("---\n")
    assert len(parts) >= 3
    metadata = yaml.safe_load(parts[1])

    assert metadata["patch_name"] == "custom-my-custom-section"
    assert metadata["version"] == "1.0.0"
    assert metadata["target_template"] == "spec-template"
    assert "migrated" in metadata["tags"]


def test_generate_patch_with_no_context(migrator):
    """Test patch generation when section has no context."""
    section = CustomSection(
        header="## Custom Header",
        content="## Custom Header\n\nContent.\n",
        line_start=1,
        line_end=3,
        context_before="",
        context_after="## Next Section",
    )

    filename, content = migrator.generate_patch_from_section(section, "template", 1)

    # Should use PREPEND since no context before
    assert "@@ PREPEND: START" in content or "@@ AFTER:" in content


def test_migrate_template_dry_run(migrator, temp_project, sample_monolithic_template):
    """Test dry run migration doesn't create files."""
    template_path = temp_project / "templates" / "test.md"
    template_path.write_text(sample_monolithic_template)

    report = migrator.migrate_template(template_path, dry_run=True)

    # Check report
    assert report.template_name == "test"
    assert report.custom_sections_found == 2
    assert len(report.patches_created) == 2
    assert report.backup_path is None  # No backup in dry run

    # Verify no files created
    patches_dir = migrator.patches_dir / "test"
    assert not patches_dir.exists()
    assert not migrator.backups_dir.exists()


def test_migrate_template_creates_patches(
    migrator, temp_project, sample_monolithic_template
):
    """Test actual migration creates patch files."""
    template_path = temp_project / "templates" / "test.md"
    template_path.write_text(sample_monolithic_template)

    report = migrator.migrate_template(template_path, dry_run=False)

    # Check report
    assert report.template_name == "test"
    assert report.custom_sections_found == 2
    assert len(report.patches_created) == 2
    assert report.backup_path is not None

    # Verify backup created
    assert report.backup_path.exists()
    assert "test_" in report.backup_path.name

    # Verify patches created
    patches_dir = migrator.patches_dir / "test"
    assert patches_dir.exists()

    for patch_name in report.patches_created:
        patch_path = patches_dir / patch_name
        assert patch_path.exists()

        # Verify patch is valid
        content = patch_path.read_text()
        assert content.startswith("---\n")
        assert "@@ " in content
        assert "@@ END" in content


def test_migrate_template_no_customizations(
    migrator, temp_project, sample_standard_template
):
    """Test migration of template with no customizations."""
    template_path = temp_project / "templates" / "standard.md"
    template_path.write_text(sample_standard_template)

    report = migrator.migrate_template(template_path, dry_run=False)

    assert report.custom_sections_found == 0
    assert len(report.patches_created) == 0
    assert report.backup_path is not None  # Backup still created


def test_migrate_template_custom_name(
    migrator, temp_project, sample_monolithic_template
):
    """Test migration with custom template name."""
    template_path = temp_project / "templates" / "file.md"
    template_path.write_text(sample_monolithic_template)

    report = migrator.migrate_template(
        template_path, template_name="my-custom-name", dry_run=False
    )

    assert report.template_name == "my-custom-name"

    # Verify patches directory uses custom name
    patches_dir = migrator.patches_dir / "my-custom-name"
    assert patches_dir.exists()


def test_migrate_template_nonexistent_file(migrator, temp_project):
    """Test migration fails gracefully for nonexistent file."""
    template_path = temp_project / "templates" / "nonexistent.md"

    with pytest.raises(FileNotFoundError):
        migrator.migrate_template(template_path)


def test_migrate_template_with_includes(migrator, temp_project):
    """Test migration warns about templates with @include directives."""
    content = """# Template

@include blocks/section1.md

## Custom Section

Custom content.
"""

    template_path = temp_project / "templates" / "modular.md"
    template_path.write_text(content)

    report = migrator.migrate_template(template_path, dry_run=False)

    # Should have warning about existing @include
    assert any("@include" in w for w in report.warnings)


def test_migrate_template_many_sections(migrator, temp_project):
    """Test migration warns about templates with many standard sections."""
    content = """# Template

## Section 1

Content 1

## Section 2

Content 2

## Section 3

Content 3

## Section 4

Content 4

## Section 5

Content 5

## Section 6

Content 6
"""

    template_path = temp_project / "templates" / "large.md"
    template_path.write_text(content)

    # Override standard sections for test

    def mock_standard(content):
        return {f"## Section {i}" for i in range(1, 7)}

    migrator.detect_standard_sections = mock_standard

    report = migrator.migrate_template(template_path, dry_run=False)

    # Should have warning about many sections
    assert any("standard sections" in w for w in report.warnings)


def test_generate_migration_guide(migrator):
    """Test migration guide generation."""
    report = MigrationReport(
        template_name="test-template",
        backup_path=Path("/path/to/backup.md"),
        blocks_created=["block1.md", "block2.md"],
        patches_created=["001-custom.patch", "002-another.patch"],
        custom_sections_found=2,
        warnings=["Warning 1", "Warning 2"],
        timestamp=datetime.now().isoformat(),
    )

    guide = migrator.generate_migration_guide(report)

    assert "test-template" in guide
    assert "Custom sections found: 2" in guide
    assert "001-custom.patch" in guide
    assert "002-another.patch" in guide
    assert "Warning 1" in guide
    assert "Warning 2" in guide
    assert "Next Steps" in guide


def test_generate_migration_guide_no_patches(migrator):
    """Test guide generation for template with no customizations."""
    report = MigrationReport(
        template_name="clean-template",
        backup_path=Path("/path/to/backup.md"),
        blocks_created=[],
        patches_created=[],
        custom_sections_found=0,
        warnings=[],
        timestamp=datetime.now().isoformat(),
    )

    guide = migrator.generate_migration_guide(report)

    assert "No patches needed" in guide
    assert "No warnings" in guide


def test_generate_migration_guide_to_file(migrator, temp_project):
    """Test guide written to file."""
    report = MigrationReport(
        template_name="test",
        backup_path=None,
        blocks_created=[],
        patches_created=["001-test.patch"],
        custom_sections_found=1,
        warnings=[],
        timestamp=datetime.now().isoformat(),
    )

    output_path = temp_project / "guide.md"
    guide = migrator.generate_migration_guide(report, output_path=output_path)

    assert output_path.exists()
    assert output_path.read_text() == guide


# ============================================================================
# Helper Functions Tests
# ============================================================================


def test_list_templates_empty(temp_project):
    """Test listing templates in empty directory."""
    templates_dir = temp_project / "templates"
    templates = list_templates(templates_dir)

    assert templates == []


def test_list_templates_multiple(temp_project):
    """Test listing multiple templates."""
    templates_dir = temp_project / "templates"

    # Create some templates
    (templates_dir / "spec.md").write_text("# Spec")
    (templates_dir / "plan.md").write_text("# Plan")
    (templates_dir / "tasks.md").write_text("# Tasks")
    (templates_dir / "readme.txt").write_text("Not a markdown")

    templates = list_templates(templates_dir)

    # Should only find .md files
    assert len(templates) == 3
    assert any(t.name == "spec.md" for t in templates)
    assert any(t.name == "plan.md" for t in templates)
    assert any(t.name == "tasks.md" for t in templates)
    assert not any(t.name == "readme.txt" for t in templates)


def test_list_templates_sorted(temp_project):
    """Test templates are returned sorted."""
    templates_dir = temp_project / "templates"

    (templates_dir / "zebra.md").write_text("# Z")
    (templates_dir / "alpha.md").write_text("# A")
    (templates_dir / "middle.md").write_text("# M")

    templates = list_templates(templates_dir)

    names = [t.name for t in templates]
    assert names == ["alpha.md", "middle.md", "zebra.md"]


def test_list_templates_nonexistent_dir(temp_project):
    """Test listing templates in nonexistent directory."""
    nonexistent = temp_project / "nonexistent"
    templates = list_templates(nonexistent)

    assert templates == []


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_migration_workflow(migrator, temp_project):
    """Test complete migration workflow."""
    # Create a template with customizations
    template_content = """---
template_type: spec
---

# Objetivo

Business objective.

## User Scenarios

Standard scenarios.

## My Custom Analysis

This is my custom analysis section.
It has multiple lines.

## Success Criteria

Standard criteria.
"""

    template_path = temp_project / "templates" / "my-spec.md"
    template_path.write_text(template_content)

    # Migrate
    report = migrator.migrate_template(template_path, dry_run=False)

    # Verify report
    assert report.custom_sections_found == 1
    assert len(report.patches_created) == 1

    # Verify backup
    assert report.backup_path.exists()
    assert report.backup_path.read_text() == template_content

    # Verify patch created
    patches_dir = migrator.patches_dir / "my-spec"
    assert patches_dir.exists()

    patch_files = list(patches_dir.glob("*.patch"))
    assert len(patch_files) == 1

    patch_content = patch_files[0].read_text()
    assert "My Custom Analysis" in patch_content
    assert "multiple lines" in patch_content

    # Generate guide
    guide = migrator.generate_migration_guide(report)
    assert "my-spec" in guide
    assert "Custom sections found: 1" in guide


def test_migration_preserves_content(migrator, temp_project):
    """Test migration preserves all custom content accurately."""
    custom_content = """## My Special Section

This content has:
- Bullet points
- **Bold text**
- `code snippets`

```python
def example():
    return "code block"
```

And normal text after.
"""

    template_content = f"""# Objetivo

Standard content.

{custom_content}

## Out of Scope

More standard content.
"""

    template_path = temp_project / "templates" / "test.md"
    template_path.write_text(template_content)

    migrator.migrate_template(template_path, dry_run=False)

    # Find the generated patch
    patches_dir = migrator.patches_dir / "test"
    patch_files = list(patches_dir.glob("*.patch"))
    assert len(patch_files) == 1

    patch_content = patch_files[0].read_text()

    # Verify all custom content preserved
    assert "Bullet points" in patch_content
    assert "**Bold text**" in patch_content
    assert "`code snippets`" in patch_content
    assert "def example():" in patch_content
    assert 'return "code block"' in patch_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
