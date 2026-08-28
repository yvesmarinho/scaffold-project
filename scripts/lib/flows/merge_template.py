"""
CLI flow for template merging.

Implements the `scaffold.py merge-template` subcommand for IMP-65 Phase 3.
"""

import argparse
import logging
from pathlib import Path

from .. import interactive_merge, template_diff, template_merge, template_version
from ..ui import console

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Merge Template Flow
# ---------------------------------------------------------------------------

def flow_merge_template(args: argparse.Namespace) -> int:
    """
    Flow: merge upstream template improvements while preserving customizations.

    Args:
        args: Parsed command-line arguments with:
            - template_name: Name of template to merge (required)
            - target_dir: Project directory (default: cwd)
            - interactive: Interactive conflict resolution mode
            - auto: Auto-apply if no conflicts
            - dry_run: Show merge result without applying
            - force: Apply merge even with conflicts

    Returns:
        Exit code (0=success, 1=conflicts, 2=error)
    """
    template_name = args.template_name
    target_dir = Path(args.target_dir if hasattr(
        args, "target_dir") and args.target_dir else ".").resolve()

    interactive = getattr(args, "interactive", False)
    auto = getattr(args, "auto", False)
    dry_run = getattr(args, "dry_run", False)
    force = getattr(args, "force", False)

    # Normalize template name
    if not template_name.endswith(".md"):
        template_name = f"{template_name}.md"

    console.print(f"Merging template: {template_name}...")

    # ---------------------------------------------------------------------------
    # 1. Validate paths
    # ---------------------------------------------------------------------------

    # Find upstream template directory (scaffold-project)
    # scripts/lib/flows -> scripts
    script_dir = Path(__file__).parent.parent.parent
    project_root = script_dir.parent

    # Support both template names and relative paths (e.g., .github/agents/session-manager.agent.md)
    if "/" in template_name or template_name.startswith("."):
        # Relative path provided
        upstream_path = project_root / template_name
        local_path = target_dir / template_name
    else:
        # Just a template name - assume .specify/templates/
        upstream_template_dir = project_root / ".specify" / "templates"

        if not upstream_template_dir.exists():
            console.print(
                f"❌ Upstream templates not found: {upstream_template_dir}", style="red")
            return 2

        upstream_path = upstream_template_dir / template_name

        # Find local template
        local_template_dir = target_dir / ".specify" / "templates"
        if not local_template_dir.exists():
            console.print(
                f"❌ Local templates not found: {local_template_dir}", style="red")
            console.print(
                "  This doesn't appear to be a SpecKit project", style="yellow")
            return 2

        local_path = local_template_dir / template_name

    # Validate files exist
    if not upstream_path.exists():
        console.print(
            f"❌ Upstream template not found: {template_name}", style="red")
        return 2

    if not local_path.exists():
        console.print(
            f"❌ Local template not found: {template_name}", style="red")
        console.print(
            f"  Run 'scaffold.py upgrade' to add missing templates", style="yellow")
        return 2

    # ---------------------------------------------------------------------------
    # 2. Load versions and base
    # ---------------------------------------------------------------------------

    console.print("Parsing template versions...")

    local_version_info = template_version.parse_template_version(local_path)
    upstream_version_info = template_version.parse_template_version(
        upstream_path)

    if not local_version_info:
        console.print(
            f"⚠️  Local template has no version metadata", style="yellow")
        local_ver = "0.0.0"
    else:
        local_ver = local_version_info.version

    if not upstream_version_info:
        console.print(
            f"❌ Upstream template has no version metadata", style="red")
        return 2

    upstream_ver = upstream_version_info.version

    # Check if already up-to-date
    if template_version.compare_versions(local_ver, upstream_ver) >= 0:
        console.print(
            f"✅ Template already up-to-date (v{local_ver})", style="green")
        return 0

    # Load base template
    base_data = template_version.load_template_base(target_dir, template_name)

    if not base_data:
        console.print(f"⚠️  No base template stored", style="yellow")
        console.print(
            f"  Cannot perform three-way merge without base", style="yellow")
        console.print(f"  Showing diff instead...\n", style="yellow")

        # Fallback to diff-template
        diff_result = template_diff.diff_templates(
            local_path=local_path,
            upstream_path=upstream_path,
            local_version=local_ver,
            upstream_version=upstream_ver,
        )

        console.print(template_diff.format_diff_colored(diff_result))
        console.print(f"\n💡 To enable merge:", style="cyan")
        console.print(f"  1. Save current template as base:", style="cyan")
        console.print(f"     Manual: edit .scaffold-state.yaml", style="cyan")
        console.print(f"  2. Re-run merge command", style="cyan")
        return 1

    base_ver, base_content = base_data
    console.print(f"  Local version:    {local_ver}")
    console.print(f"  Upstream version: {upstream_ver}")
    console.print(f"  Base version:     {base_ver}")

    # ---------------------------------------------------------------------------
    # 3. Perform merge
    # ---------------------------------------------------------------------------

    console.print("\nPerforming three-way merge...")

    merge_result = template_merge.merge_templates(
        local_path=local_path,
        upstream_path=upstream_path,
        base_content=base_content,
        base_version=base_ver,
        local_version=local_ver,
        upstream_version=upstream_ver,
        apply=False,  # Don't apply yet
        backup=True,
    )

    if not merge_result.success:
        console.print(
            f"❌ Merge failed: {merge_result.error_message}", style="red")
        return 2

    # ---------------------------------------------------------------------------
    # 4. Handle merge result
    # ---------------------------------------------------------------------------

    if not merge_result.has_conflicts:
        console.print(
            "✅ Merge completed cleanly (no conflicts)", style="green")

        # -------------------------------------------------------------------
        # BUG-04 FIX: Block breaking changes in --auto mode
        # -------------------------------------------------------------------
        if upstream_version_info.breaking_changes and auto and not force:
            console.print(
                f"\n🔴 BREAKING CHANGES detected in v{upstream_ver}",
                style="red bold"
            )

            console.print(
                "\n❌ Cannot auto-apply breaking changes",
                style="red"
            )
            console.print(
                "  --auto mode is blocked for safety",
                style="yellow"
            )
            console.print("\n💡 To proceed:", style="cyan")

            tpl_name = template_name.replace('.md', '')
            console.print(
                f"  1. Review changes: "
                f"scaffold.py diff-template {tpl_name}",
                style="cyan"
            )
            console.print(
                f"  2. Apply with force: "
                f"scaffold.py merge-template {tpl_name} --force",
                style="cyan"
            )
            console.print(
                f"  3. Apply interactively: "
                f"scaffold.py merge-template {tpl_name} --interactive",
                style="cyan"
            )
            return 1

        if dry_run:
            console.print("\n📋 Merged content preview:")
            console.print("─" * 80)
            console.print(merge_result.merged_content[:500] + "..." if len(
                merge_result.merged_content) > 500 else merge_result.merged_content)
            console.print("─" * 80)
            console.print("\n💡 Run without --dry-run to apply", style="cyan")
            return 0

        if auto or force:
            # Apply merge
            backup_path = template_merge.apply_merge_result(
                merged_content=merge_result.merged_content,
                target_path=local_path,
                create_backup_file=True,
            )

            # Update base to new upstream version
            template_version.save_template_base(
                project_dir=target_dir,
                template_name=template_name,
                version=upstream_ver,
                content=merge_result.merged_content,
            )

            console.print(f"✅ Merge applied successfully", style="green")
            if backup_path:
                console.print(f"  Backup: {backup_path}", style="cyan")
            console.print(f"  Updated: {local_path}", style="cyan")
            console.print(
                f"  Version: {local_ver} → {upstream_ver}", style="cyan")
            return 0
        else:
            console.print("\n💡 To apply this merge:", style="cyan")
            console.print(
                "  scaffold.py merge-template {template_name} --auto", style="cyan")
            return 0

    # Has conflicts
    console.print(template_merge.format_conflict_report(
        merge_result), style="yellow")

    if dry_run:
        console.print("\n📋 Merged content with conflict markers:")
        console.print("─" * 80)
        console.print(merge_result.merged_content)
        console.print("─" * 80)
        return 1

    if force:
        console.print(
            "\n⚠️  Force-applying merge with conflicts...", style="yellow")
        backup_path = template_merge.apply_merge_result(
            merged_content=merge_result.merged_content,
            target_path=local_path,
            create_backup_file=True,
        )
        console.print(f"✅ Merge applied (with conflicts)", style="yellow")
        console.print(f"  Backup: {backup_path}", style="cyan")
        console.print(
            f"  Open {local_path} to resolve conflicts", style="cyan")
        return 1

    if interactive:
        # Interactive mode: prompt user for each conflict
        console.print("\n🔧 Interactive conflict resolution", style="cyan")

        resolved_content, all_resolved = interactive_merge.resolve_conflicts_interactively(
            merge_result
        )

        if not resolved_content:
            console.print("[yellow]Resolution cancelled[/yellow]")
            return 1

        # Validate resolution
        is_valid, errors = interactive_merge.validate_resolution(
            resolved_content)
        if not is_valid:
            console.print("\n[red]❌ Resolution validation failed:[/red]")
            for error in errors:
                console.print(f"  • {error}", style="red")
            console.print(
                "\n[yellow]💡 Some conflicts remain - use --force to apply anyway[/yellow]")
            return 1

        # Apply resolved content
        backup_path = template_merge.apply_merge_result(
            merged_content=resolved_content,
            target_path=local_path,
            create_backup_file=True,
        )

        # Update base to new upstream version
        template_version.save_template_base(
            project_dir=target_dir,
            template_name=template_name,
            version=upstream_ver,
            content=resolved_content,
        )

        console.print(f"\n✅ Merge applied successfully", style="green")
        if backup_path:
            console.print(f"  Backup: {backup_path}", style="cyan")
        console.print(f"  Updated: {local_path}", style="cyan")
        console.print(f"  Version: {local_ver} → {upstream_ver}", style="cyan")

        return 0 if all_resolved else 1

    console.print("\n💡 Resolution options:", style="cyan")
    console.print(
        "  --force        Apply merge with conflict markers (manual resolution)", style="cyan")
    console.print(
        "  --interactive  Interactive conflict resolution", style="cyan")
    console.print(
        "  --dry-run      Preview merge without applying", style="cyan")

    return 1
