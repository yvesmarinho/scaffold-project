"""
Three-way template merge for SpecKit templates.

This module performs automatic merging of upstream template improvements
while preserving local customizations using git's three-way merge algorithm.

Part of IMP-65 (Template Synchronization System) Phase 3.
"""

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Caminho absoluto do git (S607/B607); "git" como fallback fora do PATH.
_GIT = shutil.which("git") or "git"

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class ConflictRegion:
    """Represents a merge conflict region."""

    start_line: int
    end_line: int
    local_content: str
    upstream_content: str
    region_type: str  # "both_modified" | "local_added" | "upstream_added"


@dataclass
class MergeResult:
    """Result of a three-way merge operation."""

    success: bool
    has_conflicts: bool
    merged_content: str
    conflicts: list[ConflictRegion]
    local_path: Path
    upstream_path: Path
    base_version: str
    local_version: str
    upstream_version: str
    backup_path: Path | None = None
    error_message: str | None = None


# ---------------------------------------------------------------------------
# Three-Way Merge
# ---------------------------------------------------------------------------


def three_way_merge(
    base_content: str,
    local_content: str,
    upstream_content: str,
    template_name: str,
) -> tuple[bool, str, bool]:
    """
    Perform three-way merge using git merge-file.

    Args:
        base_content: Original template content (common ancestor)
        local_content: Current local template with customizations
        upstream_content: Latest upstream template with improvements
        template_name: Name of template for error messages

    Returns:
        Tuple of (success, merged_content, has_conflicts)
        - success: True if merge completed (may have conflicts)
        - merged_content: Result of merge (with conflict markers if conflicts exist)
        - has_conflicts: True if there are unresolved conflicts
    """
    try:
        # Create temporary files for merge
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            base_file = tmp_path / "base.md"
            local_file = tmp_path / "local.md"
            upstream_file = tmp_path / "upstream.md"

            base_file.write_text(base_content, encoding="utf-8")
            local_file.write_text(local_content, encoding="utf-8")
            upstream_file.write_text(upstream_content, encoding="utf-8")

            # Run git merge-file
            # Exit code: 0 = clean merge, 1 = conflicts, >1 = error
            result = subprocess.run(
                [
                    _GIT,
                    "merge-file",
                    "-p",  # Output to stdout
                    "--diff3",  # Show base in conflicts
                    "-L",
                    "LOCAL",
                    "-L",
                    "BASE",
                    "-L",
                    "UPSTREAM",
                    str(local_file),
                    str(base_file),
                    str(upstream_file),
                ],
                capture_output=True,
                text=True,
            )

            merged_content = result.stdout
            has_conflicts = result.returncode == 1

            if result.returncode > 1:
                log.error(
                    "git merge-file failed for %s: %s", template_name, result.stderr
                )
                return False, "", False

            log.debug(
                "Merge %s for %s (conflicts: %s)",
                "completed" if not has_conflicts else "with conflicts",
                template_name,
                has_conflicts,
            )

            return True, merged_content, has_conflicts

    except FileNotFoundError:
        log.error("git merge-file not found - ensure git is installed")
        return False, "", False
    except Exception as exc:
        log.error("Merge failed for %s: %s", template_name, exc)
        return False, "", False


# ---------------------------------------------------------------------------
# Conflict Detection and Parsing
# ---------------------------------------------------------------------------


def detect_conflicts(merged_content: str) -> list[ConflictRegion]:
    """
    Parse conflict markers from merge result.

    Git merge-file uses diff3 format:
    <<<<<<< LOCAL
    local changes
    ||||||| BASE
    original content
    =======
    upstream changes
    >>>>>>> UPSTREAM

    Args:
        merged_content: Merged content with potential conflict markers

    Returns:
        List of ConflictRegion objects
    """
    conflicts = []
    lines = merged_content.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("<<<<<<< LOCAL"):
            # Found conflict start
            start_line = i
            local_lines = []
            base_lines = []
            upstream_lines = []

            # Collect local changes
            i += 1
            while i < len(lines) and not lines[i].startswith("|||||||"):
                local_lines.append(lines[i])
                i += 1

            # Collect base content
            if i < len(lines) and lines[i].startswith("|||||||"):
                i += 1
                while i < len(lines) and not lines[i].startswith("======="):
                    base_lines.append(lines[i])
                    i += 1

            # Collect upstream changes
            if i < len(lines) and lines[i].startswith("======="):
                i += 1
                while i < len(lines) and not lines[i].startswith(">>>>>>>"):
                    upstream_lines.append(lines[i])
                    i += 1

            # Found conflict end
            if i < len(lines) and lines[i].startswith(">>>>>>> UPSTREAM"):
                end_line = i

                # Determine conflict type
                local_str = "\n".join(local_lines)
                upstream_str = "\n".join(upstream_lines)
                base_str = "\n".join(base_lines)

                if not base_str:
                    region_type = "both_added"
                elif not local_str:
                    region_type = "upstream_added"
                elif not upstream_str:
                    region_type = "local_added"
                else:
                    region_type = "both_modified"

                conflicts.append(
                    ConflictRegion(
                        start_line=start_line,
                        end_line=end_line,
                        local_content=local_str,
                        upstream_content=upstream_str,
                        region_type=region_type,
                    )
                )

        i += 1

    return conflicts


def analyze_conflict(conflict: ConflictRegion) -> str:
    """
    Analyze a conflict and provide resolution suggestions.

    Args:
        conflict: ConflictRegion to analyze

    Returns:
        Human-readable suggestion string
    """
    if conflict.region_type == "both_modified":
        return (
            "Both local and upstream modified this section.\n"
            "Review carefully and choose the best combination."
        )
    elif conflict.region_type == "local_added":
        return (
            "Local customization not present in upstream.\n"
            "Recommendation: Keep local content (your customization)."
        )
    elif conflict.region_type == "upstream_added":
        return (
            "New content from upstream not in local.\n"
            "Recommendation: Accept upstream content (new feature)."
        )
    elif conflict.region_type == "both_added":
        return (
            "Both added content in same location.\n"
            "Review to determine if both should be kept."
        )
    else:
        return "Unknown conflict type."


# ---------------------------------------------------------------------------
# Merge Operations
# ---------------------------------------------------------------------------


def create_backup(file_path: Path) -> Path:
    """
    Create timestamped backup of a file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = file_path.with_suffix(f".backup-{timestamp}{file_path.suffix}")

    content = file_path.read_text(encoding="utf-8")
    backup_path.write_text(content, encoding="utf-8")

    log.info("✅ Created backup: %s", backup_path)
    return backup_path


def apply_merge_result(
    merged_content: str,
    target_path: Path,
    create_backup_file: bool = True,
) -> Path | None:
    """
    Apply merged content to target file with optional backup.

    Args:
        merged_content: Content to write
        target_path: Destination file path
        create_backup_file: Whether to create backup before overwriting

    Returns:
        Path to backup file if created, None otherwise
    """
    backup_path = None

    if create_backup_file and target_path.exists():
        backup_path = create_backup(target_path)

    target_path.write_text(merged_content, encoding="utf-8")
    log.info("✅ Applied merge to %s", target_path)

    return backup_path


def merge_templates(
    local_path: Path,
    upstream_path: Path,
    base_content: str,
    base_version: str,
    local_version: str,
    upstream_version: str,
    apply: bool = False,
    backup: bool = True,
) -> MergeResult:
    """
    Perform three-way merge of templates.

    Args:
        local_path: Path to local template
        upstream_path: Path to upstream template
        base_content: Original template content (common ancestor)
        base_version: Version of base template
        local_version: Version of local template
        upstream_version: Version of upstream template
        apply: If True, write merged result to local_path
        backup: If True and apply=True, create backup before writing

    Returns:
        MergeResult object with merge outcome
    """
    try:
        local_content = local_path.read_text(encoding="utf-8")
        upstream_content = upstream_path.read_text(encoding="utf-8")

        success, merged_content, has_conflicts = three_way_merge(
            base_content=base_content,
            local_content=local_content,
            upstream_content=upstream_content,
            template_name=local_path.name,
        )

        if not success:
            return MergeResult(
                success=False,
                has_conflicts=False,
                merged_content="",
                conflicts=[],
                local_path=local_path,
                upstream_path=upstream_path,
                base_version=base_version,
                local_version=local_version,
                upstream_version=upstream_version,
                error_message="Merge operation failed",
            )

        conflicts = detect_conflicts(merged_content) if has_conflicts else []
        backup_path = None

        if apply and not has_conflicts:
            backup_path = apply_merge_result(
                merged_content=merged_content,
                target_path=local_path,
                create_backup_file=backup,
            )

        return MergeResult(
            success=True,
            has_conflicts=has_conflicts,
            merged_content=merged_content,
            conflicts=conflicts,
            local_path=local_path,
            upstream_path=upstream_path,
            base_version=base_version,
            local_version=local_version,
            upstream_version=upstream_version,
            backup_path=backup_path,
        )

    except Exception as exc:
        log.error("Merge failed: %s", exc)
        return MergeResult(
            success=False,
            has_conflicts=False,
            merged_content="",
            conflicts=[],
            local_path=local_path,
            upstream_path=upstream_path,
            base_version=base_version,
            local_version=local_version,
            upstream_version=upstream_version,
            error_message=str(exc),
        )


# ---------------------------------------------------------------------------
# Conflict Resolution Helpers
# ---------------------------------------------------------------------------


def format_conflict_report(merge_result: MergeResult) -> str:
    """
    Generate human-readable conflict report.

    Args:
        merge_result: MergeResult with conflicts

    Returns:
        Formatted conflict report string
    """
    if not merge_result.has_conflicts:
        return "✅ No conflicts - merge completed successfully!"

    lines = []
    lines.append(f"⚠️  {len(merge_result.conflicts)} conflict(s) detected\n")

    for i, conflict in enumerate(merge_result.conflicts, 1):
        lines.append(
            f"Conflict #{i} (lines {conflict.start_line}-{conflict.end_line}):"
        )
        lines.append(f"  Type: {conflict.region_type}")
        lines.append(f"  Suggestion: {analyze_conflict(conflict)}")
        lines.append("")

    lines.append("To resolve conflicts:")
    lines.append("  1. Open the merged file in your editor")
    lines.append("  2. Search for conflict markers (<<<<<<, =======, >>>>>>>)")
    lines.append("  3. Choose or combine the best content")
    lines.append("  4. Remove all conflict markers")
    lines.append("  5. Save the file")

    return "\n".join(lines)
