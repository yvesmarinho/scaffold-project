#!/usr/bin/env python3
"""
Session Documentation Migration Script

Migrates legacy DAILY_ACTIVITIES/TODAY_ACTIVITIES files to the canonical format
defined in SESSION_DOCS_STYLE_GUIDE.md.

Part of: IMP-50 — Sistema de documentação incremental — Docs + Migração
Created: 2026-04-05

Supports migration from:
- TODAY_ACTIVITIES_*.md (very old format, pre-2026-02)
- DAILY_ACTIVITIES_*.md (old formats, 2026-02 to 2026-03-29)
- DAILY_ACTIVITIES_*.md (partial canonical, 2026-03-30+)

Usage:
    # Migrate single file
    python scripts/migrate-daily-activities.py docs/SESSIONS/2026-01-28/TODAY_ACTIVITIES_2026-01-28.md

    # Migrate directory (all files in session)
    python scripts/migrate-daily-activities.py docs/SESSIONS/2026-01-28/

    # Migrate all sessions
    python scripts/migrate-daily-activities.py --all

    # Dry-run (preview only, no changes)
    python scripts/migrate-daily-activities.py --all --dry-run

    # Force overwrite existing (normally skips already canonical files)
    python scripts/migrate-daily-activities.py --all --force
"""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"


@dataclass
class ActivityBlock:
    """Represents an activity block extracted from legacy format."""

    title: str
    timestamp: Optional[str] = None
    status: Optional[str] = "✅ Completo"  # Default to completed for legacy
    objective: Optional[str] = None
    context: Optional[str] = None
    steps: List[str] = None
    result: Optional[str] = None
    decisions: Optional[str] = None
    files: List[str] = None
    commits: List[str] = None
    observations: Optional[str] = None

    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.files is None:
            self.files = []
        if self.commits is None:
            self.commits = []

    def to_canonical(self) -> str:
        """Convert to canonical format with separator."""
        lines = ["---", ""]

        # Title (required)
        lines.append(f"### {self.title}")
        lines.append("")

        # Timestamp + Status (required)
        timestamp = self.timestamp or "[timestamp not available]"
        lines.append(f"**{timestamp} — {self.status}**")
        lines.append("")

        # Objective (required)
        if self.objective:
            lines.append(f"**Objetivo**: {self.objective}")
            lines.append("")

        # Context (required)
        if self.context:
            lines.append(f"**Contexto**: {self.context}")
            lines.append("")

        # Steps (required)
        if self.steps:
            lines.append("**Passos executados**:")
            for i, step in enumerate(self.steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        # Result (required)
        if self.result:
            lines.append(f"**Resultado**: {self.result}")
            lines.append("")

        # Decisions (optional)
        if self.decisions:
            lines.append(f"**Decisões técnicas**: {self.decisions}")
            lines.append("")

        # Files (optional)
        if self.files:
            lines.append("**Arquivos modificados/criados**:")
            for file_entry in self.files:
                lines.append(f"- {file_entry}")
            lines.append("")

        # Commits (optional)
        if self.commits:
            lines.append("**Commits**:")
            for commit in self.commits:
                lines.append(f"- {commit}")
            lines.append("")

        # Observations (optional)
        if self.observations:
            lines.append(f"**Observações**: {self.observations}")
            lines.append("")

        # Status (required, end of block)
        lines.append(f"**Status**: {self.status}")
        lines.append("")

        return "\n".join(lines)


class SessionDocumentMigrator:
    """Migrates session documentation to canonical format."""

    CANONICAL_HEADER = """# 📝 Daily Activities — {date}

**Project**: Enterprise Scaffold Project Template
**Branch**: {branch}
**Session**: {date} ({day_of_week})
**Initial HEAD**: {head}

---

> **ℹ️ About This Document**
>
> This is an **incremental activity log** following the [Session Docs Style Guide](../../SESSION_DOCS_STYLE_GUIDE.md).
> Each significant activity is added as a new block with timestamp, context, steps, and outcome.
> Activities are append-only — previous entries are never modified or removed.

> **📝 Migration Note**
>
> This document was **migrated from legacy format** on {migration_date}.
> Original format: `{original_filename}`
> Some fields may be incomplete or inferred from context.

---
"""

    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.files_migrated = 0
        self.files_skipped = 0
        self.files_failed = 0

    def is_canonical_format(self, content: str) -> bool:
        """Check if file is already in canonical format."""
        # Check for canonical markers
        has_style_guide_ref = "SESSION_DOCS_STYLE_GUIDE.md" in content
        has_separator_blocks = content.count("---\n\n###") >= 2
        has_required_fields = all(
            field in content for field in ["**Objetivo**:", "**Contexto**:", "**Status**:"]
        )

        return has_style_guide_ref and has_separator_blocks and has_required_fields

    def extract_metadata(self, file_path: Path) -> dict:
        """Extract metadata from file path and content."""
        # Extract date from filename
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", file_path.name)
        date_str = date_match.group(1) if date_match else "unknown"

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            day_of_week = date_obj.strftime("%A")
        except ValueError:
            day_of_week = "unknown"

        return {
            "date": date_str,
            "day_of_week": day_of_week,
            "branch": "master",  # Default, can be overridden
            "head": "[not available]",  # Default
            "original_filename": file_path.name,
            "migration_date": datetime.now().strftime("%Y-%m-%d"),
        }

    def parse_legacy_content(self, content: str, file_path: Path) -> List[ActivityBlock]:
        """Parse legacy format and extract activity blocks."""
        blocks = []

        # Detect format type
        if "TODAY_ACTIVITIES" in file_path.name:
            blocks = self._parse_very_old_format(content)
        elif "## " in content and "### Atividade:" in content:
            blocks = self._parse_old_structured_format(content)
        elif "### " in content and "**Objetivo**:" in content:
            blocks = self._parse_semi_canonical_format(content)
        else:
            # Fallback: treat as freeform, create single block
            blocks = [self._parse_freeform(content)]

        return blocks

    def _parse_very_old_format(self, content: str) -> List[ActivityBlock]:
        """Parse very old format (TODAY_ACTIVITIES with Morning Session, etc.)."""
        blocks = []

        # Split by major sections (## headers)
        sections = re.split(r'\n## ', content)

        for section in sections[1:]:  # Skip preamble
            lines = section.split('\n')
            title = lines[0].strip()

            if title.startswith('🌅') or title.startswith('📊'):
                # Skip metadata sections
                continue

            # Extract activities from bullets
            block = ActivityBlock(
                title=title,
                timestamp="[migrated]",
                objective=self._extract_field(section, "Objective"),
                context=self._extract_field(section, "Actions") or self._extract_field(section, "Findings"),
                steps=self._extract_bullets(section),
                result=self._extract_field(section, "Status") or "Completed",
            )

            blocks.append(block)

        return blocks if blocks else [self._parse_freeform(content)]

    def _parse_old_structured_format(self, content: str) -> List[ActivityBlock]:
        """Parse old structured format (2026-02-27 style with tables and phases)."""
        blocks = []

        # Split by ### Atividade: or ## Fase
        activity_pattern = r'\n### Atividade: ([^\n]+)'
        phase_pattern = r'\n## ([^\n]+Fase [^\n]+)'

        activities = re.split(activity_pattern, content)

        for i in range(1, len(activities), 2):
            if i + 1 >= len(activities):
                break

            title = activities[i].strip()
            body = activities[i + 1]

            block = ActivityBlock(
                title=title,
                timestamp=self._extract_time(body),
                objective=self._extract_field(body, "Objetivo"),
                context=self._extract_field(body, "Contexto") or self._extract_field(body, "Actions"),
                steps=self._extract_list_items(body, "Passos executados") or self._extract_bullets(body),
                result=self._extract_field(body, "Resultado") or self._extract_field(body, "Status"),
                decisions=self._extract_field(body, "Decisões"),
                files=self._extract_list_items(body, "Arquivos") or self._extract_files(body),
            )

            blocks.append(block)

        return blocks if blocks else [self._parse_freeform(content)]

    def _parse_semi_canonical_format(self, content: str) -> List[ActivityBlock]:
        """Parse semi-canonical format (has fields but missing separators)."""
        blocks = []

        # Split by ### headers
        sections = re.split(r'\n### ', content)

        for section in sections[1:]:
            lines = section.split('\n', 1)
            title = lines[0].strip()
            body = lines[1] if len(lines) > 1 else ""

            # Extract timestamp from first line after title
            timestamp = self._extract_time(body)

            block = ActivityBlock(
                title=title,
                timestamp=timestamp,
                objective=self._extract_field(body, "Objetivo"),
                context=self._extract_field(body, "Contexto"),
                steps=self._extract_list_items(body, "Passos executados"),
                result=self._extract_field(body, "Resultado"),
                decisions=self._extract_field(body, "Decisões técnicas"),
                files=self._extract_list_items(body, "Arquivos modificados/criados") or self._extract_files(body),
                commits=self._extract_commits(body),
                observations=self._extract_field(body, "Observações"),
            )

            blocks.append(block)

        return blocks

    def _parse_freeform(self, content: str) -> ActivityBlock:
        """Parse completely freeform content as single block."""
        return ActivityBlock(
            title="Legacy Session Activities (Migrated)",
            timestamp="[see original content]",
            objective="Legacy session content migrated from freeform format",
            context="Original content preserved below",
            steps=["Content was in freeform format and could not be automatically parsed"],
            result="Migrated to canonical format for consistency",
            observations=f"Original freeform content:\n\n{content}",
        )

    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract single-line field value."""
        patterns = [
            rf'\*\*{field_name}\*\*:\s*([^\n]+)',
            rf'- \*\*{field_name}\*\*:\s*([^\n]+)',
            rf'{field_name}:\s*([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_time(self, text: str) -> str:
        """Extract timestamp."""
        # Look for HH:MM pattern
        time_match = re.search(r'\b(\d{1,2}:\d{2})\b', text)
        if time_match:
            return time_match.group(1)

        # Look for "Time: ..." pattern
        time_field = self._extract_field(text, "Time")
        if time_field:
            return time_field

        return "[migrated]"

    def _extract_bullets(self, text: str) -> List[str]:
        """Extract bullet points (- or *)."""
        bullets = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                bullets.append(line[2:].strip())
            elif re.match(r'^\d+\.', line):
                bullets.append(re.sub(r'^\d+\.\s*', '', line))

        return bullets

    def _extract_list_items(self, text: str, header: str) -> List[str]:
        """Extract items from a list under a specific header."""
        # Find section starting with header
        pattern = rf'\*\*{header}\*\*:\s*\n((?:(?:\d+\.|-|\*)\s*[^\n]+\n?)+)'
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)

        if not match:
            return []

        list_text = match.group(1)
        items = []

        for line in list_text.split('\n'):
            line = line.strip()
            if re.match(r'^[\d\-\*\.]+\s+', line):
                item = re.sub(r'^[\d\-\*\.]+\s+', '', line).strip()
                if item:
                    items.append(item)

        return items

    def _extract_files(self, text: str) -> List[str]:
        """Extract file paths from text."""
        files = []
        patterns = [
            r'`([^`]+\.[a-z]{2,4})`',
            r'(?:Created|Modified|Updated):\s*([^\n]+)',
            r'- ([a-zA-Z0-9_/\-\.]+\.[a-z]{2,4})',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            files.extend(matches)

        return files

    def _extract_commits(self, text: str) -> List[str]:
        """Extract commit references."""
        commits = []

        # Look for commit hashes
        hash_pattern = r'`([0-9a-f]{7,40})`'
        matches = re.findall(hash_pattern, text)
        commits.extend([f"`{m}`" for m in matches])

        return commits

    def migrate_file(self, file_path: Path) -> bool:
        """Migrate a single file to canonical format."""
        print(f"\n{BLUE}Processing:{RESET} {file_path}")

        # Read original content
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"{RED}✗ Failed to read:{RESET} {e}")
            self.files_failed += 1
            return False

        # Check if already canonical
        if self.is_canonical_format(content) and not self.force:
            print(f"{YELLOW}⊘ Skipped:{RESET} Already in canonical format (use --force to override)")
            self.files_skipped += 1
            return True

        # Extract metadata
        metadata = self.extract_metadata(file_path)

        # Parse legacy content
        blocks = self.parse_legacy_content(content, file_path)

        if not blocks:
            print(f"{RED}✗ Failed:{RESET} Could not parse content")
            self.files_failed += 1
            return False

        # Build canonical document
        canonical_content = self.CANONICAL_HEADER.format(**metadata)

        for block in blocks:
            canonical_content += block.to_canonical()

        # Write output
        if self.dry_run:
            print(f"{CYAN}[DRY RUN]{RESET} Would migrate {len(blocks)} block(s)")
            print(f"{CYAN}[DRY RUN]{RESET} Preview (first 500 chars):")
            print(canonical_content[:500])
            print("...\n")
            self.files_migrated += 1
            return True

        # Backup original
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
        try:
            file_path.rename(backup_path)
            print(f"{GREEN}✓ Backup created:{RESET} {backup_path.name}")
        except Exception as e:
            print(f"{YELLOW}⚠ Warning:{RESET} Could not create backup: {e}")

        # Write canonical version
        try:
            file_path.write_text(canonical_content, encoding="utf-8")
            print(f"{GREEN}✓ Migrated:{RESET} {len(blocks)} block(s) → canonical format")
            self.files_migrated += 1
            return True
        except Exception as e:
            print(f"{RED}✗ Failed to write:{RESET} {e}")
            # Restore backup
            if backup_path.exists():
                backup_path.rename(file_path)
                print(f"{YELLOW}⚠ Restored from backup{RESET}")
            self.files_failed += 1
            return False

    def migrate_directory(self, dir_path: Path) -> None:
        """Migrate all DAILY_ACTIVITIES/TODAY_ACTIVITIES in a directory."""
        patterns = ["DAILY_ACTIVITIES_*.md", "TODAY_ACTIVITIES_*.md"]

        files = []
        for pattern in patterns:
            files.extend(dir_path.glob(pattern))

        if not files:
            print(f"{YELLOW}No activity files found in {dir_path}{RESET}")
            return

        for file_path in sorted(files):
            self.migrate_file(file_path)

    def migrate_all_sessions(self, sessions_root: Path) -> None:
        """Migrate all sessions in docs/SESSIONS/."""
        session_dirs = sorted([d for d in sessions_root.iterdir() if d.is_dir() and re.match(r'\d{4}-\d{2}-\d{2}', d.name)])

        print(f"\n{BLUE}Found {len(session_dirs)} session directories{RESET}")

        for session_dir in session_dirs:
            print(f"\n{CYAN}{'='*60}{RESET}")
            print(f"{CYAN}Session: {session_dir.name}{RESET}")
            print(f"{CYAN}{'='*60}{RESET}")
            self.migrate_directory(session_dir)

    def print_summary(self) -> None:
        """Print migration summary."""
        print(f"\n{CYAN}{'='*60}{RESET}")
        print(f"{CYAN}Migration Summary{RESET}")
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{GREEN}✓ Migrated:{RESET} {self.files_migrated}")
        print(f"{YELLOW}⊘ Skipped:{RESET}  {self.files_skipped}")
        print(f"{RED}✗ Failed:{RESET}   {self.files_failed}")
        print(f"{CYAN}Total:{RESET}     {self.files_migrated + self.files_skipped + self.files_failed}")

        if self.dry_run:
            print(f"\n{CYAN}[DRY RUN] No files were modified{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate session documentation to canonical format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        help="File or directory to migrate",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Migrate all sessions in docs/SESSIONS/",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if file appears canonical",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.path and not args.all:
        parser.error("Must specify path or --all")

    migrator = SessionDocumentMigrator(dry_run=args.dry_run, force=args.force)

    try:
        if args.all:
            # Migrate all sessions
            project_root = Path(__file__).parent.parent
            sessions_root = project_root / "docs" / "SESSIONS"

            if not sessions_root.exists():
                print(f"{RED}Error: docs/SESSIONS/ not found{RESET}")
                sys.exit(1)

            migrator.migrate_all_sessions(sessions_root)

        elif args.path:
            if args.path.is_file():
                migrator.migrate_file(args.path)
            elif args.path.is_dir():
                migrator.migrate_directory(args.path)
            else:
                print(f"{RED}Error: {args.path} not found{RESET}")
                sys.exit(1)

        migrator.print_summary()

        # Exit code
        sys.exit(0 if migrator.files_failed == 0 else 1)

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Migration interrupted by user{RESET}")
        migrator.print_summary()
        sys.exit(130)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
