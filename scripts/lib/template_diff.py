"""
Template diff and comparison for SpecKit templates.

This module provides functionality to:
- Compare local vs upstream template versions
- Generate side-by-side diffs with syntax highlighting
- Detect customizations vs upstream changes
- Export diffs in terminal (colored) and markdown formats

Part of IMP-65 (Template Synchronization System) Phase 2.
"""

import difflib
import logging
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class TemplateDiffResult:
    """Result of comparing local and upstream template."""

    template_name: str
    local_path: Path
    upstream_path: Path
    local_version: str | None
    upstream_version: str | None
    has_differences: bool
    unified_diff: str
    html_diff: str
    stats: dict[str, int]  # lines_added, lines_removed, lines_changed
    customizations_detected: bool
    impact_report: str


# ---------------------------------------------------------------------------
# Diff Generation
# ---------------------------------------------------------------------------


def generate_unified_diff(
    local_content: str,
    upstream_content: str,
    local_path: Path,
    upstream_path: Path,
) -> str:
    """
    Generate unified diff between local and upstream templates.

    Args:
        local_content: Content of local template
        upstream_content: Content of upstream template
        local_path: Path to local template (for header)
        upstream_path: Path to upstream template (for header)

    Returns:
        Unified diff string (git-style format)
    """
    local_lines = local_content.splitlines(keepends=True)
    upstream_lines = upstream_content.splitlines(keepends=True)

    diff = difflib.unified_diff(
        local_lines,
        upstream_lines,
        fromfile=f"local/{local_path.name}",
        tofile=f"upstream/{upstream_path.name}",
        lineterm="",
    )

    return "".join(diff)


def generate_side_by_side_diff(
    local_content: str,
    upstream_content: str,
) -> str:
    """
    Generate side-by-side HTML diff with syntax highlighting.

    Args:
        local_content: Content of local template
        upstream_content: Content of upstream template

    Returns:
        HTML string with side-by-side comparison
    """
    local_lines = local_content.splitlines()
    upstream_lines = upstream_content.splitlines()

    differ = difflib.HtmlDiff(wrapcolumn=80)
    html_diff = differ.make_table(
        local_lines,
        upstream_lines,
        fromdesc="Local (Your Customizations)",
        todesc="Upstream (Latest Version)",
        context=True,
        numlines=3,
    )

    return html_diff


def calculate_diff_stats(unified_diff: str) -> dict[str, int]:
    """
    Calculate statistics from unified diff.

    Args:
        unified_diff: Unified diff string

    Returns:
        Dictionary with lines_added, lines_removed, lines_changed
    """
    lines_added = 0
    lines_removed = 0

    for line in unified_diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            lines_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            lines_removed += 1

    lines_changed = min(lines_added, lines_removed)
    lines_only_added = lines_added - lines_changed
    lines_only_removed = lines_removed - lines_changed

    return {
        "lines_added": lines_only_added,
        "lines_removed": lines_only_removed,
        "lines_changed": lines_changed,
        "total_changes": lines_added + lines_removed,
    }


# ---------------------------------------------------------------------------
# Customization Detection
# ---------------------------------------------------------------------------


def detect_customizations(
    local_content: str,
    upstream_content: str,
    base_version: str | None = None,
) -> bool:
    """
    Detect if local template has customizations beyond upstream changes.

    This is a heuristic detection. For true three-way merge detection,
    we need the base version (Phase 3).

    Args:
        local_content: Content of local template
        upstream_content: Content of upstream template
        base_version: Optional base version for three-way comparison (Phase 3)

    Returns:
        True if customizations detected, False if only upstream changes
    """
    # Phase 2: Heuristic detection
    # If local has sections not in upstream, likely customizations
    local_lines = set(local_content.splitlines())
    upstream_lines = set(upstream_content.splitlines())

    local_only = local_lines - upstream_lines
    upstream_lines - local_lines

    # Filter out frontmatter differences (version metadata)
    local_only_filtered = {
        line
        for line in local_only
        if not line.strip().startswith(
            ("template_version:", "last_updated:", "breaking_changes:")
        )
    }

    # If local has unique content beyond version metadata, it's customized
    return len(local_only_filtered) > 0


# ---------------------------------------------------------------------------
# Impact Report Generation
# ---------------------------------------------------------------------------


def generate_impact_report(
    template_name: str,
    local_version: str | None,
    upstream_version: str | None,
    stats: dict[str, int],
    customizations_detected: bool,
) -> str:
    """
    Generate human-readable impact report for template diff.

    Args:
        template_name: Name of template
        local_version: Local template version
        upstream_version: Upstream template version
        stats: Diff statistics
        customizations_detected: Whether customizations were detected

    Returns:
        Formatted impact report string
    """
    lines = []
    lines.append(f"📊 Impact Report: {template_name}")
    lines.append("=" * 60)
    lines.append("")

    # Version info
    lines.append(f"Local Version:    {local_version or 'unknown'}")
    lines.append(f"Upstream Version: {upstream_version or 'unknown'}")
    lines.append("")

    # Change statistics
    lines.append("Changes:")
    lines.append(f"  + {stats['lines_added']} lines added")
    lines.append(f"  - {stats['lines_removed']} lines removed")
    lines.append(f"  ~ {stats['lines_changed']} lines modified")
    lines.append(f"  Total: {stats['total_changes']} changes")
    lines.append("")

    # Customization status
    if customizations_detected:
        lines.append("⚠️  Customizations Detected")
        lines.append("   Your local template has custom modifications.")
        lines.append("   Manual merge recommended to preserve your changes.")
    else:
        lines.append("✅ No Customizations Detected")
        lines.append("   Local template appears to match an older upstream version.")
        lines.append("   Safe to update automatically (future Phase 3 feature).")
    lines.append("")

    # Recommendations
    lines.append("Recommendations:")
    if customizations_detected:
        lines.append("  1. Review diff carefully to identify your customizations")
        lines.append(
            "  2. Create backup: cp template.md template.md.backup-$(date +%Y%m%d)"
        )
        lines.append(
            "  3. Manually merge upstream changes while preserving customizations"
        )
        lines.append("  4. Test workflow with new template version")
    else:
        lines.append("  1. Review changes to understand improvements")
        lines.append("  2. Consider updating to latest version")
        lines.append("  3. Wait for Phase 3 auto-merge feature (coming soon)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main Diff Function
# ---------------------------------------------------------------------------


def diff_templates(
    local_path: Path,
    upstream_path: Path,
    local_version: str | None = None,
    upstream_version: str | None = None,
) -> TemplateDiffResult:
    """
    Compare local and upstream templates and generate comprehensive diff.

    Args:
        local_path: Path to local template
        upstream_path: Path to upstream template
        local_version: Local template version (from frontmatter)
        upstream_version: Upstream template version (from frontmatter)

    Returns:
        TemplateDiffResult with complete comparison data
    """
    # Read template contents
    local_content = local_path.read_text(encoding="utf-8")
    upstream_content = upstream_path.read_text(encoding="utf-8")

    # Generate diffs
    unified_diff = generate_unified_diff(
        local_content, upstream_content, local_path, upstream_path
    )
    html_diff = generate_side_by_side_diff(local_content, upstream_content)

    # Calculate statistics
    stats = calculate_diff_stats(unified_diff)
    has_differences = stats["total_changes"] > 0

    # Detect customizations
    customizations_detected = detect_customizations(local_content, upstream_content)

    # Generate impact report
    impact_report = generate_impact_report(
        local_path.name,
        local_version,
        upstream_version,
        stats,
        customizations_detected,
    )

    return TemplateDiffResult(
        template_name=local_path.name,
        local_path=local_path,
        upstream_path=upstream_path,
        local_version=local_version,
        upstream_version=upstream_version,
        has_differences=has_differences,
        unified_diff=unified_diff,
        html_diff=html_diff,
        stats=stats,
        customizations_detected=customizations_detected,
        impact_report=impact_report,
    )


# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------


def format_diff_colored(diff_result: TemplateDiffResult) -> str:
    """
    Format diff with ANSI color codes for terminal output.

    Args:
        diff_result: Diff result to format

    Returns:
        Colored terminal output string
    """
    # ANSI color codes
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    lines = []

    # Header
    lines.append(f"\n{BOLD}{CYAN}{'=' * 80}{RESET}")
    lines.append(f"{BOLD}Template Diff: {diff_result.template_name}{RESET}")
    lines.append(f"{CYAN}{'=' * 80}{RESET}\n")

    # Version info
    lines.append(f"{BOLD}Versions:{RESET}")
    lines.append(f"  Local:    {YELLOW}{diff_result.local_version or 'unknown'}{RESET}")
    lines.append(
        f"  Upstream: {GREEN}{diff_result.upstream_version or 'unknown'}{RESET}"
    )
    lines.append("")

    # Statistics
    stats = diff_result.stats
    lines.append(f"{BOLD}Changes:{RESET}")
    lines.append(f"  {GREEN}+{stats['lines_added']} lines added{RESET}")
    lines.append(f"  {RED}-{stats['lines_removed']} lines removed{RESET}")
    lines.append(f"  {YELLOW}~{stats['lines_changed']} lines modified{RESET}")
    lines.append("")

    # Customization warning
    if diff_result.customizations_detected:
        lines.append(f"{BOLD}{MAGENTA}⚠️  Customizations detected{RESET}")
        lines.append(f"{MAGENTA}   Manual merge recommended{RESET}\n")
    else:
        lines.append(f"{BOLD}{GREEN}✅ No customizations detected{RESET}")
        lines.append(f"{GREEN}   Safe to auto-update (Phase 3){RESET}\n")

    # Unified diff with colors
    lines.append(f"{BOLD}{BLUE}Diff:{RESET}")
    lines.append(f"{BLUE}{'-' * 80}{RESET}")

    for line in diff_result.unified_diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            lines.append(f"{BOLD}{line}{RESET}")
        elif line.startswith("+"):
            lines.append(f"{GREEN}{line}{RESET}")
        elif line.startswith("-"):
            lines.append(f"{RED}{line}{RESET}")
        elif line.startswith("@@"):
            lines.append(f"{CYAN}{line}{RESET}")
        else:
            lines.append(line)

    lines.append(f"{BLUE}{'-' * 80}{RESET}\n")

    # Impact report
    lines.append(diff_result.impact_report)

    return "\n".join(lines)


def format_diff_markdown(diff_result: TemplateDiffResult) -> str:
    """
    Format diff as markdown for export/documentation.

    Args:
        diff_result: Diff result to format

    Returns:
        Markdown formatted diff
    """
    lines = []

    # Header
    lines.append(f"# Template Diff: {diff_result.template_name}\n")

    # Metadata
    lines.append("## Metadata\n")
    lines.append(f"- **Local Version**: {diff_result.local_version or 'unknown'}")
    lines.append(f"- **Upstream Version**: {diff_result.upstream_version or 'unknown'}")
    lines.append(f"- **Has Differences**: {diff_result.has_differences}")
    lines.append(
        f"- **Customizations Detected**: {diff_result.customizations_detected}\n"
    )

    # Statistics
    stats = diff_result.stats
    lines.append("## Statistics\n")
    lines.append(f"- **Lines Added**: {stats['lines_added']}")
    lines.append(f"- **Lines Removed**: {stats['lines_removed']}")
    lines.append(f"- **Lines Modified**: {stats['lines_changed']}")
    lines.append(f"- **Total Changes**: {stats['total_changes']}\n")

    # Diff
    lines.append("## Diff\n")
    lines.append("```diff")
    lines.append(diff_result.unified_diff)
    lines.append("```\n")

    # Impact Report
    lines.append("## Impact Report\n")
    lines.append("```")
    lines.append(diff_result.impact_report)
    lines.append("```\n")

    return "\n".join(lines)
