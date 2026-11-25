"""
Interactive conflict resolution for template merging.

Provides UI for resolving merge conflicts one at a time with
side-by-side diff visualization and multiple resolution options.

Part of IMP-65 (Template Synchronization System) Phase 3.1.
"""

import logging
import re
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .template_merge import ConflictRegion, MergeResult

log = logging.getLogger(__name__)
console = Console()


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class ResolutionChoice:
    """User's choice for resolving a conflict."""

    action: str  # "local" | "upstream" | "both" | "edit" | "skip"
    custom_content: str | None = None  # For "edit" action


# ---------------------------------------------------------------------------
# Side-by-Side Diff Viewer
# ---------------------------------------------------------------------------


def show_side_by_side_diff(
    conflict: ConflictRegion,
    conflict_num: int,
    total_conflicts: int,
) -> None:
    """
    Display conflict with side-by-side comparison.

    Args:
        conflict: ConflictRegion to display
        conflict_num: Current conflict number (1-indexed)
        total_conflicts: Total number of conflicts
    """
    # Header
    console.print()
    console.print(f"[bold cyan]Conflict {conflict_num}/{total_conflicts}[/bold cyan]")
    console.print(
        f"[dim]Lines {conflict.start_line}-{conflict.end_line} • Type: {conflict.region_type}[/dim]"
    )
    console.print()

    # Create side-by-side table
    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column(
        "[bold yellow]LOCAL[/bold yellow] (your changes)", style="yellow", width=50
    )
    table.add_column(
        "[bold green]UPSTREAM[/bold green] (template updates)", style="green", width=50
    )

    # Split content into lines for side-by-side display
    local_lines = conflict.local_content.split("\n")
    upstream_lines = conflict.upstream_content.split("\n")

    max_lines = max(len(local_lines), len(upstream_lines))

    for i in range(max_lines):
        local_line = local_lines[i] if i < len(local_lines) else ""
        upstream_line = upstream_lines[i] if i < len(upstream_lines) else ""
        table.add_row(local_line, upstream_line)

    console.print(table)
    console.print()


def show_conflict_analysis(conflict: ConflictRegion) -> None:
    """
    Show analysis and recommendation for conflict.

    Args:
        conflict: ConflictRegion to analyze
    """
    suggestions = {
        "both_modified": (
            "💡 Both versions modified this section.",
            "Review carefully and choose the best content or combine both.",
        ),
        "local_added": (
            "💡 This is your local customization.",
            "Recommended: Keep LOCAL to preserve your customization.",
        ),
        "upstream_added": (
            "💡 This is new content from upstream.",
            "Recommended: Accept UPSTREAM to get new features.",
        ),
        "both_added": (
            "💡 Both versions added content here.",
            "Consider keeping BOTH to preserve all improvements.",
        ),
    }

    title, recommendation = suggestions.get(
        conflict.region_type,
        ("💡 Conflict detected", "Review both versions carefully."),
    )

    panel = Panel(
        f"{title}\n{recommendation}",
        title="[bold]Analysis[/bold]",
        border_style="cyan",
    )
    console.print(panel)
    console.print()


# ---------------------------------------------------------------------------
# Interactive Resolution
# ---------------------------------------------------------------------------


def prompt_resolution(conflict: ConflictRegion) -> ResolutionChoice:
    """
    Prompt user for conflict resolution choice.

    Args:
        conflict: ConflictRegion to resolve

    Returns:
        ResolutionChoice with user's decision
    """
    console.print("[bold]Resolution options:[/bold]")
    console.print("  [cyan]l[/cyan]  Keep LOCAL (your changes)")
    console.print("  [cyan]u[/cyan]  Accept UPSTREAM (template updates)")
    console.print("  [cyan]b[/cyan]  Keep BOTH (local first, then upstream)")
    console.print("  [cyan]e[/cyan]  Edit manually (open editor)")
    console.print("  [cyan]s[/cyan]  Skip (leave conflict marker for later)")
    console.print("  [cyan]?[/cyan]  Show diff again")
    console.print()

    while True:
        choice = Prompt.ask(
            "Choose resolution",
            choices=["l", "u", "b", "e", "s", "?"],
            default="l" if conflict.region_type == "local_added" else "u",
        ).lower()

        if choice == "?":
            # Show diff again
            console.print()
            return prompt_resolution(conflict)  # Recursive call to show options again

        if choice == "l":
            return ResolutionChoice(action="local")
        elif choice == "u":
            return ResolutionChoice(action="upstream")
        elif choice == "b":
            return ResolutionChoice(action="both")
        elif choice == "e":
            return ResolutionChoice(action="edit")
        elif choice == "s":
            return ResolutionChoice(action="skip")


def edit_conflict_manually(conflict: ConflictRegion) -> str | None:
    """
    Allow user to manually edit conflict content.

    Args:
        conflict: ConflictRegion to edit

    Returns:
        Edited content or None if cancelled
    """
    console.print("\n[yellow]Manual edit mode[/yellow]")
    console.print("Enter your resolved content (end with empty line + 'DONE'):")
    console.print("[dim]Tip: You can combine parts from both LOCAL and UPSTREAM[/dim]")
    console.print()

    lines: list[str] = []
    while True:
        line = input()
        if not line and lines and lines[-1] == "DONE":
            lines.pop()  # Remove "DONE" marker
            break
        lines.append(line)

    if not lines:
        console.print("[yellow]Cancelled - no content entered[/yellow]")
        return None

    content = "\n".join(lines)

    # Preview
    console.print("\n[bold]Preview of your edit:[/bold]")
    console.print(Panel(content, border_style="green"))

    if Confirm.ask("Accept this resolution?", default=True):
        return content

    return None


def apply_resolution(
    merged_content: str,
    conflict: ConflictRegion,
    resolution: ResolutionChoice,
) -> str:
    """
    Apply resolution choice to merged content.

    Args:
        merged_content: Current merged content with conflict markers
        conflict: ConflictRegion being resolved
        resolution: User's resolution choice

    Returns:
        Updated merged content with conflict resolved
    """
    if resolution.action == "skip":
        # Leave conflict markers in place
        return merged_content

    # Extract content based on resolution
    if resolution.action == "local":
        resolved_content = conflict.local_content
    elif resolution.action == "upstream":
        resolved_content = conflict.upstream_content
    elif resolution.action == "both":
        # Combine both (local first, then upstream)
        resolved_content = f"{conflict.local_content}\n\n{conflict.upstream_content}"
    elif resolution.action == "edit":
        if resolution.custom_content:
            resolved_content = resolution.custom_content
        else:
            # Edit was cancelled, skip
            return merged_content
    else:
        log.warning("Unknown resolution action: %s", resolution.action)
        return merged_content

    # Find and replace the conflict region
    # We need to find the first occurrence of the conflict pattern
    lines = merged_content.split("\n")

    # Search for conflict markers
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if line.startswith("<<<<<<< LOCAL") and start_idx is None:
            start_idx = i
        elif (
            line.startswith(">>>>>>> UPSTREAM")
            and start_idx is not None
            and end_idx is None
        ):
            end_idx = i
            break

    if start_idx is None or end_idx is None:
        log.warning("Could not find conflict markers in content")
        return merged_content

    # Replace conflict region (from start marker to end marker inclusive) with resolved content
    new_lines = lines[:start_idx] + resolved_content.split("\n") + lines[end_idx + 1 :]

    return "\n".join(new_lines)


# ---------------------------------------------------------------------------
# Main Interactive Loop
# ---------------------------------------------------------------------------


def resolve_conflicts_interactively(merge_result: MergeResult) -> tuple[str, bool]:
    """
    Interactively resolve all conflicts in merge result.

    Args:
        merge_result: MergeResult with conflicts to resolve

    Returns:
        Tuple of (resolved_content, all_resolved)
        - resolved_content: Merged content with resolutions applied
        - all_resolved: True if all conflicts were resolved (no skips)
    """
    if not merge_result.conflicts:
        log.info("No conflicts to resolve")
        return merge_result.merged_content, True

    total_conflicts = len(merge_result.conflicts)
    console.print(
        f"\n[bold yellow]⚠️  {total_conflicts} conflict(s) detected[/bold yellow]\n"
    )

    # Confirm to proceed
    if not Confirm.ask("Start interactive resolution?", default=True):
        console.print("[yellow]Cancelled - merge not applied[/yellow]")
        return merge_result.merged_content, False

    resolved_content = merge_result.merged_content
    skipped_count = 0

    for i, conflict in enumerate(merge_result.conflicts, start=1):
        show_side_by_side_diff(conflict, i, total_conflicts)
        show_conflict_analysis(conflict)

        resolution = prompt_resolution(conflict)

        # Handle edit action
        if resolution.action == "edit":
            custom_content = edit_conflict_manually(conflict)
            if custom_content is not None:
                resolution.custom_content = custom_content
            else:
                # Edit cancelled, skip this conflict
                resolution.action = "skip"

        # Apply resolution
        if resolution.action == "skip":
            skipped_count += 1
            console.print(
                "[yellow]⏭️  Skipped - conflict marker left in place[/yellow]\n"
            )
        else:
            resolved_content = apply_resolution(resolved_content, conflict, resolution)
            console.print(
                f"[green]✅ Resolved as: {resolution.action.upper()}[/green]\n"
            )

        # Show progress
        if i < total_conflicts:
            console.print(
                f"[dim]Progress: {i}/{total_conflicts} conflicts processed[/dim]"
            )
            console.print("[dim]" + "─" * 60 + "[/dim]\n")

    # Summary
    console.print("\n[bold]Resolution Summary:[/bold]")
    resolved_count = total_conflicts - skipped_count
    console.print(f"  ✅ Resolved: {resolved_count}/{total_conflicts}")
    if skipped_count > 0:
        console.print(f"  ⏭️  Skipped: {skipped_count}/{total_conflicts}")

    all_resolved = skipped_count == 0

    if all_resolved:
        console.print("\n[bold green]🎉 All conflicts resolved![/bold green]")
    else:
        console.print(
            f"\n[yellow]⚠️  {skipped_count} conflict(s) still need manual resolution[/yellow]"
        )

    return resolved_content, all_resolved


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------


def count_remaining_conflicts(content: str) -> int:
    """
    Count remaining conflict markers in content.

    Args:
        content: Text content to check

    Returns:
        Number of remaining conflict regions
    """
    return len(re.findall(r"<<<<<<< LOCAL", content))


def validate_resolution(content: str) -> tuple[bool, list[str]]:
    """
    Validate that all conflicts are resolved.

    Args:
        content: Resolved content to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check for remaining conflict markers
    markers = ["<<<<<<< LOCAL", "||||||| BASE", "=======", ">>>>>>> UPSTREAM"]
    for marker in markers:
        if marker in content:
            errors.append(f"Conflict marker '{marker}' still present")

    is_valid = len(errors) == 0
    return is_valid, errors
