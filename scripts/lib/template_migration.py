#!/usr/bin/env python3
"""
Template Migration Module - Convert monolithic templates to modular system.

This module provides tools to migrate existing monolithic templates to the new
block-based modular template system, including:
- Detection of customizations vs standard content
- Auto-generation of patches from customizations
- Backup and versioning of original templates
- State management for migration tracking

Part of IMP-65 Phase 4.4: Migration & Compatibility
"""

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml


@dataclass
class CustomSection:
    """Represents a customized section in a template."""

    header: str
    content: str
    line_start: int
    line_end: int
    context_before: str  # For anchor identification
    context_after: str


@dataclass
class MigrationReport:
    """Results of a template migration operation."""

    template_name: str
    backup_path: Path | None
    blocks_created: list[str]
    patches_created: list[str]
    custom_sections_found: int
    warnings: list[str]
    timestamp: str


class TemplateMigrator:
    """Handles migration of monolithic templates to modular block system."""

    def __init__(self, project_root: Path):
        """
        Initialize migrator.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.templates_dir = self.project_root / "templates"
        self.blocks_dir = self.project_root / ".specify" / "blocks"
        self.patches_dir = self.project_root / ".specify" / "patches"
        self.backups_dir = self.project_root / ".specify" / "migration-backups"

    def backup_template(self, template_path: Path) -> Path:
        """
        Create timestamped backup of template before migration.

        Args:
            template_path: Path to template file

        Returns:
            Path to backup file
        """
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{template_path.stem}_{timestamp}{template_path.suffix}"
        backup_path = self.backups_dir / backup_name
        shutil.copy2(template_path, backup_path)
        return backup_path

    def detect_standard_sections(self, content: str) -> set[str]:
        """
        Identify standard template sections (headers).

        Args:
            content: Template content

        Returns:
            Set of standard section headers found
        """
        # Common standard sections across templates
        standard_headers = {
            "# Objetivo",
            "## Context",
            "## Problem",
            "## Goals",
            "## User Scenarios",
            "## User Stories",
            "## Success Criteria",
            "## Out of Scope",
            "## Assumptions",
            "## Constraints",
            "## Dependencies",
            "## Risks",
            "## Questions",
            "## Notes",
            "# Implementation Plan",
            "## Architecture",
            "## Components",
            "## Data Model",
            "## API Design",
            "## Security",
            "## Testing Strategy",
            "## Deployment",
            "## Rollback Plan",
            "## Monitoring",
            "# Tasks",
            "## Layer 1",
            "## Layer 2",
            "## Layer 3",
            "## Layer 4",
        }

        found_headers = set()
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                # Extract header up to any trailing markers
                header = line.split("{")[0].strip()
                if header in standard_headers:
                    found_headers.add(header)

        return found_headers

    def extract_custom_sections(
        self, content: str, standard_sections: set[str]
    ) -> list[CustomSection]:
        """
        Extract sections that appear to be customizations.

        Args:
            content: Template content
            standard_sections: Set of known standard section headers

        Returns:
            List of custom sections found
        """
        custom_sections = []
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this is a header
            if line.startswith("#"):
                header = line.split("{")[0].strip()

                # If not a standard header, it's likely custom
                if header not in standard_sections:
                    # Extract content until next header or end
                    section_start = i
                    content_lines = [lines[i]]
                    i += 1

                    while i < len(lines):
                        if lines[i].strip().startswith("#"):
                            break
                        content_lines.append(lines[i])
                        i += 1

                    # Get context
                    context_before = "\n".join(
                        lines[max(0, section_start - 3) : section_start]
                    )
                    context_after = "\n".join(lines[i : min(len(lines), i + 3)])

                    custom_sections.append(
                        CustomSection(
                            header=header,
                            content="\n".join(content_lines),
                            line_start=section_start + 1,  # 1-indexed
                            line_end=i,  # 1-indexed
                            context_before=context_before,
                            context_after=context_after,
                        )
                    )
                    continue

            i += 1

        return custom_sections

    def generate_patch_from_section(
        self, section: CustomSection, template_name: str, patch_number: int
    ) -> tuple[str, str]:
        """
        Generate a patch file from a custom section.

        Args:
            section: Custom section to convert
            template_name: Name of target template
            patch_number: Sequential patch number

        Returns:
            Tuple of (patch_filename, patch_content)
        """
        # Generate patch metadata
        today = datetime.now().strftime("%Y-%m-%d")
        patch_name = section.header.strip("#").strip().lower().replace(" ", "-")

        # Create patch frontmatter
        frontmatter = {
            "patch_name": f"custom-{patch_name}",
            "version": "1.0.0",
            "target_template": template_name,
            "target_block": None,  # To be determined during application
            "created": today,
            "description": f"Custom section: {section.header}",
            "author": "migration-tool",
            "tags": ["migrated", "custom"],
        }

        # Determine operation type and anchor
        # If we have context_before, use AFTER operation
        # Otherwise use PREPEND or APPEND based on position
        if section.context_before.strip():
            # Find last header in context_before as anchor
            anchor_lines = [
                linha
                for linha in section.context_before.split("\n")
                if linha.strip().startswith("#")
            ]
            if anchor_lines:
                anchor = anchor_lines[-1].strip()
                operation_type = "AFTER"
            else:
                anchor = "START"
                operation_type = "PREPEND"
        else:
            anchor = "START"
            operation_type = "PREPEND"

        # Build patch content
        patch_content = "---\n"
        patch_content += yaml.dump(
            frontmatter, default_flow_style=False, sort_keys=False
        )
        patch_content += "---\n\n"
        patch_content += f"@@ {operation_type}: {anchor}\n"
        patch_content += section.content.rstrip()
        if not section.content.endswith("\n"):
            patch_content += "\n"
        patch_content += "@@ END\n"

        # Generate filename
        patch_filename = f"{patch_number:03d}-custom-{patch_name}.patch"

        return patch_filename, patch_content

    def migrate_template(
        self,
        template_path: Path,
        template_name: str | None = None,
        dry_run: bool = False,
    ) -> MigrationReport:
        """
        Migrate a monolithic template to modular system.

        Args:
            template_path: Path to template file to migrate
            template_name: Name for the template (default: filename without extension)
            dry_run: If True, don't write files, just report what would happen

        Returns:
            MigrationReport with results
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        if template_name is None:
            template_name = template_path.stem

        # Read template
        content = template_path.read_text(encoding="utf-8")

        # Initialize report
        report = MigrationReport(
            template_name=template_name,
            backup_path=None,
            blocks_created=[],
            patches_created=[],
            custom_sections_found=0,
            warnings=[],
            timestamp=datetime.now().isoformat(),
        )

        # Create backup
        if not dry_run:
            backup_path = self.backup_template(template_path)
            report.backup_path = backup_path

        # Detect standard sections
        standard_sections = self.detect_standard_sections(content)

        # Extract custom sections
        custom_sections = self.extract_custom_sections(content, standard_sections)
        report.custom_sections_found = len(custom_sections)

        if custom_sections:
            # Create patches directory for this template
            template_patches_dir = self.patches_dir / template_name
            if not dry_run:
                template_patches_dir.mkdir(parents=True, exist_ok=True)

            # Generate patch for each custom section
            for idx, section in enumerate(custom_sections, start=1):
                patch_filename, patch_content = self.generate_patch_from_section(
                    section, template_name, idx
                )

                if not dry_run:
                    patch_path = template_patches_dir / patch_filename
                    patch_path.write_text(patch_content, encoding="utf-8")

                report.patches_created.append(patch_filename)

        # Check if template has @include directives (already modular)
        if "@include" in content:
            report.warnings.append(
                "Template already contains @include directives. "
                "It may already be using the modular system."
            )

        # Suggest blocks to extract (standard sections)
        if len(standard_sections) > 5:
            report.warnings.append(
                f"Template has {len(standard_sections)} standard sections. "
                "Consider extracting common sections into reusable blocks."
            )

        return report

    def generate_migration_guide(
        self, report: MigrationReport, output_path: Path | None = None
    ) -> str:
        """
        Generate human-readable migration guide for a template.

        Args:
            report: Migration report to document
            output_path: Optional path to write guide to

        Returns:
            Migration guide content
        """
        guide = f"""# Migration Guide: {report.template_name}

**Generated**: {report.timestamp}

## Summary
- Custom sections found: {report.custom_sections_found}
- Patches created: {len(report.patches_created)}
- Blocks created: {len(report.blocks_created)}
- Backup location: {report.backup_path}

## Patches Generated

"""

        if report.patches_created:
            for patch in report.patches_created:
                guide += f"- `{patch}`\n"
        else:
            guide += "No patches needed - template has no customizations.\n"

        guide += "\n## Warnings\n\n"
        if report.warnings:
            for warning in report.warnings:
                guide += f"- ⚠️  {warning}\n"
        else:
            guide += "No warnings.\n"

        guide += """
## Next Steps

1. **Review patches**: Check generated patches in `.specify/patches/{template}/`
2. **Test composition**: Run `compose-template` to verify template assembles correctly
3. **Adjust patches**: Edit patch files if anchors or content need refinement
4. **Update template**: Replace monolithic template with modular version using @include
5. **Test workflow**: Verify your scaffold/spec/plan workflow still works
6. **Clean up**: Once verified, old backup can be removed

## Manual Steps Required

This migration tool handles detection and patch generation, but you'll need to:

1. **Create template composition file**: Define which blocks to include
2. **Extract reusable blocks**: Move common sections to `.specify/blocks/`
3. **Update @include directives**: Reference blocks in your template
4. **Test thoroughly**: Ensure all customizations are preserved

See `docs/MODULAR_TEMPLATES.md` for detailed migration instructions.
"""

        if output_path:
            output_path.write_text(guide, encoding="utf-8")

        return guide


def list_templates(templates_dir: Path) -> list[Path]:
    """
    Find all markdown templates in directory.

    Args:
        templates_dir: Directory to search

    Returns:
        List of template paths
    """
    if not templates_dir.exists():
        return []

    return sorted(templates_dir.glob("*.md"))


def main() -> None:
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: template_migration.py <template-path> [--dry-run]")
        sys.exit(1)

    template_path = Path(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    project_root = Path.cwd()
    migrator = TemplateMigrator(project_root)

    print(f"🔄 Migrating: {template_path}")
    if dry_run:
        print("   (DRY RUN - no files will be created)")

    try:
        report = migrator.migrate_template(template_path, dry_run=dry_run)

        print("\n✅ Migration complete!")
        print(f"   Custom sections: {report.custom_sections_found}")
        print(f"   Patches created: {len(report.patches_created)}")

        if report.backup_path:
            print(f"   Backup: {report.backup_path}")

        if report.warnings:
            print("\n⚠️  Warnings:")
            for warning in report.warnings:
                print(f"   - {warning}")

        # Generate guide
        guide = migrator.generate_migration_guide(report)
        print(f"\n{guide}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
