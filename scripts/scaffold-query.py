#!/usr/bin/env python3
"""
scaffold-query.py — Query Scaffold History

Query and analyze scaffold operations logged in logs/scaffolds.yaml.

Usage:
    # List recent scaffolds
    python scripts/scaffold-query.py --last 30d
    python scripts/scaffold-query.py --limit 10

    # Filter by criteria
    python scripts/scaffold-query.py --profile python-fastapi
    python scripts/scaffold-query.py --user yves_marinho
    python scripts/scaffold-query.py --project "vya-*"

    # Statistics
    python scripts/scaffold-query.py --stats

    # Export
    python scripts/scaffold-query.py --export scaffolds.csv

    # JSON output
    python scripts/scaffold-query.py --json --limit 5
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import scaffold logger
sys.path.insert(0, str(Path(__file__).parent))
from scaffold_logger import ScaffoldEntry, ScaffoldLogger

# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


def format_table(entries: list[ScaffoldEntry]) -> None:
    """Format entries as a table"""
    if not entries:
        print("No scaffolds found.")
        return

    # Header
    print("=" * 100)
    print(f"{'ID':<5} {'Date':<12} {'Project':<25} {'Profile':<20} {'User':<15}")
    print("=" * 100)

    # Rows
    for entry in entries:
        timestamp = datetime.fromisoformat(entry.timestamp.replace("Z", ""))
        date_str = timestamp.strftime("%Y-%m-%d")

        status = "✅" if entry.success else "❌"

        print(
            f"{entry.id:<5} {date_str:<12} {entry.project_name:<25} "
            f"{entry.profile:<20} {entry.created_by:<15} {status}"
        )

    print("=" * 100)
    print(f"Total: {len(entries)} scaffold(s)")


def format_stats(stats: dict) -> None:
    """Format statistics"""
    print("=" * 70)
    print("SCAFFOLD STATISTICS")
    print("=" * 70)
    print(f"Total scaffolds: {stats['total_scaffolds']}")
    print(f"Success rate: {stats['success_rate']}%")
    print(f"Recent activity (30 days): {stats['recent_activity']}")
    print()

    print("By Profile:")
    for profile, count in sorted(
        stats["by_profile"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {profile:<30} {count:>5}")
    print()

    print("By User:")
    for user, count in sorted(
        stats["by_user"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {user:<30} {count:>5}")
    print("=" * 70)


def format_json_output(entries: list[ScaffoldEntry]) -> None:
    """Format entries as JSON"""
    data = [
        {
            "id": e.id,
            "timestamp": e.timestamp,
            "project_name": e.project_name,
            "template_version": e.template_version,
            "profile": e.profile,
            "created_by": e.created_by,
            "path": e.path,
            "success": e.success,
            "error_message": e.error_message,
        }
        for e in entries
    ]
    print(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_time_period(period: str) -> datetime:
    """Parse time period like '30d', '7d', '1w'"""
    if period.endswith("d"):
        days = int(period[:-1])
        return datetime.utcnow() - timedelta(days=days)
    elif period.endswith("w"):
        weeks = int(period[:-1])
        return datetime.utcnow() - timedelta(weeks=weeks)
    elif period.endswith("m"):
        months = int(period[:-1])
        return datetime.utcnow() - timedelta(days=months * 30)
    else:
        raise ValueError(f"Invalid time period: {period}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query scaffold history",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Filters
    parser.add_argument(
        "--project", help="Filter by project name (supports wildcard *)"
    )
    parser.add_argument("--profile", help="Filter by profile")
    parser.add_argument("--user", help="Filter by user")
    parser.add_argument(
        "--success", action="store_true", help="Show only successful scaffolds"
    )
    parser.add_argument(
        "--failed", action="store_true", help="Show only failed scaffolds"
    )

    # Time filters
    parser.add_argument("--last", help="Last N days/weeks (e.g., 30d, 2w, 3m)")
    parser.add_argument("--limit", type=int, help="Limit number of results")

    # Output
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--export", help="Export to CSV file")

    # Config
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path("logs/scaffolds.yaml"),
        help="Path to scaffold log file",
    )

    args = parser.parse_args()

    # Initialize logger
    logger = ScaffoldLogger(args.log_file)

    # Handle export
    if args.export:
        logger.export_csv(Path(args.export))
        return

    # Handle statistics
    if args.stats:
        stats = logger.get_stats()
        format_stats(stats)
        return

    # Query scaffolds
    success_filter = None
    if args.success:
        success_filter = True
    elif args.failed:
        success_filter = False

    entries = logger.query(
        project_name=args.project,
        profile=args.profile,
        created_by=args.user,
        success=success_filter,
        limit=args.limit,
    )

    # Filter by time period
    if args.last:
        cutoff = parse_time_period(args.last)
        entries = [
            e
            for e in entries
            if datetime.fromisoformat(e.timestamp.replace("Z", "")) >= cutoff
        ]

    # Output
    if args.json:
        format_json_output(entries)
    else:
        format_table(entries)


if __name__ == "__main__":
    main()
