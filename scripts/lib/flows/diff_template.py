"""
Flow: Template diff to compare local vs upstream templates.

Part of IMP-65 (Template Synchronization System) Phase 2.
"""

import argparse
import logging
from pathlib import Path

from .. import template_diff, template_version
from ..ui import console

log = logging.getLogger(__name__)


def flow_diff_template(args: argparse.Namespace) -> int:
    """
    Flow: show diff between local and upstream template.

    Args:
        args: Namespace with:
            - template_name: name of template to diff
            - target_dir: project directory (default: cwd)
            - format: output format (colored, markdown, html)
            - output: output file path (optional, default: stdout)

    Returns:
        0 on success
        1 if template not found
        2 on error
    """
    # Get template name
    template_name = getattr(args, "template_name", None)
    if not template_name:
        console.print("[red]❌ Template name required[/red]")
        console.print("Usage: scaffold.py diff-template <template-name>")
        console.print("\nAvailable templates:")
        console.print("  - spec-template.md")
        console.print("  - plan-template.md")
        console.print("  - tasks-template.md")
        console.print("  - agent-file-template.md")
        console.print("  - checklist-template.md")
        console.print("  - constitution-template.md")
        return 1

    # Ensure .md extension
    if not template_name.endswith(".md"):
        template_name = f"{template_name}.md"

    # Determine directories
    target_dir_arg = getattr(args, "target_dir", None)
    if target_dir_arg:
        target_dir = Path(target_dir_arg).resolve()
    else:
        target_dir = Path.cwd().resolve()

    scaffold_root = Path(__file__).parent.parent.parent.parent

    # Support both template names and relative paths (e.g., .github/agents/session-manager.agent.md)
    if "/" in template_name or template_name.startswith("."):
        # Relative path provided
        local_path = target_dir / template_name
        upstream_path = scaffold_root / template_name
    else:
        # Just a template name - assume .specify/templates/
        upstream_dir = scaffold_root / ".specify" / "templates"
        local_dir = target_dir / ".specify" / "templates"

        if not upstream_dir.exists():
            console.print(f"[red]❌ Upstream templates not found: {upstream_dir}[/red]")
            return 2

        if not local_dir.exists():
            console.print(f"[red]❌ Local templates not found: {local_dir}[/red]")
            console.print("Are you in a project directory created with scaffold.py?")
            return 1

        local_path = local_dir / template_name
        upstream_path = upstream_dir / template_name

    # Validate template exists

    if not local_path.exists():
        console.print(f"[red]❌ Local template not found: {local_path}[/red]")
        console.print("\nAvailable local templates:")
        for tmpl in sorted(local_dir.glob("*.md")):
            console.print(f"  - {tmpl.name}")
        return 1

    if not upstream_path.exists():
        console.print(f"[red]❌ Upstream template not found: {upstream_path}[/red]")
        console.print("This template may have been removed from upstream.")
        return 1

    # Parse versions
    console.print("Parsing template versions...")
    local_info = template_version.parse_template_version(local_path)
    upstream_info = template_version.parse_template_version(upstream_path)

    local_ver = local_info.version if local_info else None
    upstream_ver = upstream_info.version if upstream_info else None

    # Generate diff
    console.print(f"Generating diff for {template_name}...")
    diff_result = template_diff.diff_templates(
        local_path=local_path,
        upstream_path=upstream_path,
        local_version=local_ver,
        upstream_version=upstream_ver,
    )

    # Check if there are any differences
    if not diff_result.has_differences:
        console.print("\n[green]✅ No differences found![/green]")
        console.print("Local and upstream templates are identical.")
        return 0

    # Determine output format
    output_format = getattr(args, "format", "colored")
    output_file = getattr(args, "output", None)

    # Format output
    if output_format == "markdown":
        output_text = template_diff.format_diff_markdown(diff_result)
    elif output_format == "html":
        output_text = diff_result.html_diff
    else:  # colored (default)
        output_text = template_diff.format_diff_colored(diff_result)

    # Output to file or stdout
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(output_text, encoding="utf-8")
        console.print(f"\n[green]✅ Diff written to: {output_path}[/green]")
    else:
        # Print to stdout (console.print strips ANSI codes when piped)
        print(output_text)

    return 0
