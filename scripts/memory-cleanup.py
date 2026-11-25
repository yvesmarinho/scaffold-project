#!/usr/bin/env python3
"""
Defensive memory cleanup script.

IMP-65 P0: Automated cleanup of test files and duplicates from .memory/

Features:
- Dry-run by default (safety first)
- Automatic backup before execution
- Duplicate detection via SHA256
- Configurable patterns
- Detailed logging and statistics

Usage:
    python scripts/memory-cleanup.py                    # Dry-run (show what would be removed)
    python scripts/memory-cleanup.py --execute          # Execute without backup (dangerous)
    python scripts/memory-cleanup.py --execute --backup # Execute with automatic backup (recommended)
"""

import argparse
import hashlib
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/memory-cleanup.log", mode="a"),
    ],
)
log = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
MEMORY_DIR = PROJECT_ROOT / ".memory" / "memories"

# Patterns to clean (test files, auto-generated titles, etc.)
CLEANUP_PATTERNS = [
    "*__test-*.md",
    "*__auto-generated-title.md",
    "*__search-test-*.md",
]


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of file content."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def find_duplicates(directory: Path) -> dict[str, list[Path]]:
    """
    Find duplicate files by content hash.

    Returns:
        Dict mapping hash → list of file paths with that hash
    """
    hashes: dict[str, list[Path]] = {}
    for file in directory.rglob("*.md"):
        if file.is_file():
            file_hash = get_file_hash(file)
            hashes.setdefault(file_hash, []).append(file)

    # Return only hashes with multiple files (duplicates)
    return {h: files for h, files in hashes.items() if len(files) > 1}


def find_files_to_clean(directory: Path, patterns: list[str]) -> list[Path]:
    """Find all files matching cleanup patterns."""
    files_to_clean: list[Path] = []
    for pattern in patterns:
        files_to_clean.extend(directory.rglob(pattern))
    return sorted(set(files_to_clean))  # Remove duplicates, sort for consistency


def create_backup(memory_dir: Path) -> Path:
    """
    Create timestamped backup of .memory/ directory.

    Returns:
        Path to backup directory
    """
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_dir = PROJECT_ROOT / f".memory.backup.{timestamp}"

    log.info(f"📦 Creating backup: {backup_dir.name}")
    shutil.copytree(memory_dir.parent, backup_dir)
    log.info(f"✅ Backup created: {backup_dir}")

    return backup_dir


def cleanup_files(files: list[Path], execute: bool = False) -> int:
    """
    Clean up files (dry-run or execute).

    Returns:
        Number of files removed
    """
    if not files:
        log.info("✅ No files to clean")
        return 0

    log.info(f"Found {len(files)} file(s) matching cleanup patterns:")
    for file in files:
        relative_path = file.relative_to(MEMORY_DIR)
        if execute:
            file.unlink()
            log.info(f"  ✅ Deleted: {relative_path}")
        else:
            log.info(f"  🔍 Would delete: {relative_path}")

    return len(files) if execute else 0


def cleanup_duplicates(duplicates: dict[str, list[Path]], execute: bool = False) -> int:
    """
    Clean up duplicate files (keep oldest, remove rest).

    Returns:
        Number of duplicates removed
    """
    if not duplicates:
        log.info("✅ No duplicates found")
        return 0

    removed_count = 0
    log.info(f"Found {len(duplicates)} group(s) of duplicate files:")

    for file_hash, files in duplicates.items():
        # Keep oldest file (first by creation time), remove rest
        files_sorted = sorted(files, key=lambda f: f.stat().st_ctime)
        keep_file = files_sorted[0]
        remove_files = files_sorted[1:]

        log.info(f"\nDuplicate group (hash: {file_hash[:8]}...):")
        log.info(f"  ✅ Keep: {keep_file.relative_to(MEMORY_DIR)}")

        for dup_file in remove_files:
            relative_path = dup_file.relative_to(MEMORY_DIR)
            if execute:
                dup_file.unlink()
                log.info(f"  ✅ Deleted duplicate: {relative_path}")
                removed_count += 1
            else:
                log.info(f"  🔍 Would delete duplicate: {relative_path}")

    return removed_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Defensive memory cleanup script (IMP-65 P0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/memory-cleanup.py                    # Dry-run (show what would be removed)
  python scripts/memory-cleanup.py --execute --backup # Execute with backup (recommended)
        """,
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute cleanup (default: dry-run only)",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before execution (recommended with --execute)",
    )
    parser.add_argument(
        "--find-duplicates",
        action="store_true",
        help="Also find and remove duplicate files by content hash",
    )

    args = parser.parse_args()

    # Ensure logs directory exists
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)

    # Banner
    log.info("=" * 70)
    log.info("Memory Cleanup Script (IMP-65 P0)")
    log.info("=" * 70)

    if not args.execute:
        log.info("🔍 DRY-RUN MODE (no files will be modified)")
        log.info("   Use --execute to actually remove files")
    else:
        log.info("⚠️  EXECUTE MODE (files will be permanently removed)")

    log.info(f"Memory directory: {MEMORY_DIR}")
    log.info("")

    # Create backup if requested
    if args.execute and args.backup:
        create_backup(MEMORY_DIR)
        log.info("")
    elif args.execute and not args.backup:
        log.warning("⚠️  WARNING: Executing without backup!")
        log.warning("   Consider using --backup for safety")
        log.info("")

    # Find and clean pattern-matched files
    log.info("Step 1: Cleaning pattern-matched files")
    log.info("-" * 70)
    files_to_clean = find_files_to_clean(MEMORY_DIR, CLEANUP_PATTERNS)
    removed_count = cleanup_files(files_to_clean, execute=args.execute)
    log.info("")

    # Find and clean duplicates
    duplicates_removed = 0
    if args.find_duplicates:
        log.info("Step 2: Finding and cleaning duplicates")
        log.info("-" * 70)
        duplicates = find_duplicates(MEMORY_DIR)
        duplicates_removed = cleanup_duplicates(duplicates, execute=args.execute)
        log.info("")

    # Summary
    log.info("=" * 70)
    log.info("Summary")
    log.info("=" * 70)
    log.info(f"Pattern-matched files: {len(files_to_clean)} found")
    if args.find_duplicates:
        log.info(
            f"Duplicate groups: {len(duplicates) if 'duplicates' in locals() else 0}"
        )

    if args.execute:
        log.info(f"Files removed: {removed_count + duplicates_removed}")
        log.info("✅ Cleanup completed")
    else:
        log.info(
            f"Files that would be removed: {len(files_to_clean) + duplicates_removed}"
        )
        log.info("🔍 DRY-RUN completed (no changes made)")
        log.info("   Run with --execute --backup to perform cleanup")

    log.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
