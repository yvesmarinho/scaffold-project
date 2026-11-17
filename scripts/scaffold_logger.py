#!/usr/bin/env python3
"""
scaffold_logger.py — Scaffold History Logger for IMP-65-LITE

Logs all scaffold operations to logs/scaffolds.yaml for historical tracking.

Usage:
    from scaffold_logger import ScaffoldLogger

    logger = ScaffoldLogger()
    logger.log_scaffold(
        project_name="vya-api-users",
        template_version="2.1.0",
        profile="python-fastapi",
        created_by="yves_marinho",
        path="/home/yves/projects/vya-api-users"
    )

Query usage:
    python scripts/scaffold-query.py --last 30d
    python scripts/scaffold-query.py --stats
    python scripts/scaffold-query.py --project "vya-*"
"""

import os
import yaml
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_LOG_FILE = Path("logs/scaffolds.yaml")


def _default_log_file() -> Path:
    """``$SCAFFOLD_LOGS_DIR/scaffolds.yaml`` se definido; senão ``DEFAULT_LOG_FILE``.

    A suíte de testes define a variável para não poluir o histórico real.
    """
    override = os.environ.get("SCAFFOLD_LOGS_DIR", "").strip()
    return Path(override) / "scaffolds.yaml" if override else DEFAULT_LOG_FILE

# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ScaffoldEntry:
    """Single scaffold operation entry"""
    id: int
    timestamp: str
    project_name: str
    template_version: str
    profile: str
    created_by: str
    path: str
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# ---------------------------------------------------------------------------
# Scaffold Logger
# ---------------------------------------------------------------------------

class ScaffoldLogger:
    """Log and query scaffold operations"""

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or _default_log_file()
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Create log file if it doesn't exist"""
        if not self.log_file.exists():
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({"scaffolds": []})

    def _load_data(self) -> Dict[str, Any]:
        """Load scaffold log data"""
        try:
            with self.log_file.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data else {"scaffolds": []}
        except Exception as e:
            print(f"Warning: Failed to load {self.log_file}: {e}")
            return {"scaffolds": []}

    def _save_data(self, data: Dict[str, Any]):
        """Save scaffold log data"""
        with self.log_file.open('w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def _get_next_id(self, data: Dict[str, Any]) -> int:
        """Get next sequential ID"""
        scaffolds = data.get("scaffolds", [])
        if not scaffolds:
            return 1
        return max(s["id"] for s in scaffolds) + 1

    def log_scaffold(
        self,
        project_name: str,
        template_version: str,
        profile: str,
        created_by: str,
        path: str,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScaffoldEntry:
        """
        Log a scaffold operation

        Args:
            project_name: Name of the created project
            template_version: Version of template used
            profile: Profile applied (e.g., "python-fastapi")
            created_by: User who created the scaffold
            path: Path where project was created
            success: Whether scaffold succeeded
            error_message: Error message if failed
            metadata: Additional metadata (optional)

        Returns:
            ScaffoldEntry with logged data
        """
        data = self._load_data()

        entry = ScaffoldEntry(
            id=self._get_next_id(data),
            timestamp=datetime.utcnow().isoformat() + "Z",
            project_name=project_name,
            template_version=template_version,
            profile=profile,
            created_by=created_by,
            path=path,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )

        data["scaffolds"].append(asdict(entry))
        self._save_data(data)

        return entry

    def query(
        self,
        project_name: Optional[str] = None,
        profile: Optional[str] = None,
        created_by: Optional[str] = None,
        success: Optional[bool] = None,
        limit: Optional[int] = None
    ) -> List[ScaffoldEntry]:
        """
        Query scaffold history

        Args:
            project_name: Filter by project name (supports wildcard *)
            profile: Filter by profile
            created_by: Filter by user
            success: Filter by success status
            limit: Limit number of results

        Returns:
            List of matching ScaffoldEntry objects
        """
        data = self._load_data()
        scaffolds = data.get("scaffolds", [])

        # Convert to ScaffoldEntry objects
        results = []
        for s in scaffolds:
            # Apply filters
            if project_name and not self._match_pattern(s["project_name"], project_name):
                continue
            if profile and s["profile"] != profile:
                continue
            if created_by and s["created_by"] != created_by:
                continue
            if success is not None and s["success"] != success:
                continue

            results.append(ScaffoldEntry(**s))

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply limit
        if limit:
            results = results[:limit]

        return results

    def _match_pattern(self, text: str, pattern: str) -> bool:
        """Simple wildcard matching (* only)"""
        if '*' not in pattern:
            return text == pattern

        # Convert wildcard to regex
        import re
        regex_pattern = pattern.replace('*', '.*')
        return bool(re.match(f'^{regex_pattern}$', text))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get scaffold statistics

        Returns:
            Dictionary with statistics:
            - total_scaffolds
            - success_rate
            - by_profile: count per profile
            - by_user: count per user
            - recent_activity: scaffolds in last 30 days
        """
        data = self._load_data()
        scaffolds = data.get("scaffolds", [])

        if not scaffolds:
            return {
                "total_scaffolds": 0,
                "success_rate": 0.0,
                "by_profile": {},
                "by_user": {},
                "recent_activity": 0
            }

        # Count by profile
        by_profile = {}
        for s in scaffolds:
            profile = s["profile"]
            by_profile[profile] = by_profile.get(profile, 0) + 1

        # Count by user
        by_user = {}
        for s in scaffolds:
            user = s["created_by"]
            by_user[user] = by_user.get(user, 0) + 1

        # Success rate
        successful = sum(1 for s in scaffolds if s["success"])
        success_rate = (successful / len(scaffolds)) * 100

        # Recent activity (last 30 days)
        from datetime import timedelta
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        recent = sum(
            1 for s in scaffolds
            if datetime.fromisoformat(s["timestamp"].replace('Z', ''))
            >= thirty_days_ago
        )

        return {
            "total_scaffolds": len(scaffolds),
            "success_rate": round(success_rate, 1),
            "by_profile": by_profile,
            "by_user": by_user,
            "recent_activity": recent
        }

    def export_csv(self, output_file: Path):
        """Export scaffold history to CSV"""
        import csv

        data = self._load_data()
        scaffolds = data.get("scaffolds", [])

        if not scaffolds:
            print("No scaffolds to export")
            return

        with output_file.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                "id", "timestamp", "project_name", "template_version",
                "profile", "created_by", "path", "success", "error_message"
            ])
            writer.writeheader()

            for s in scaffolds:
                # Remove metadata field for CSV (too complex)
                row = {k: v for k, v in s.items() if k != "metadata"}
                writer.writerow(row)

        print(f"✅ Exported {len(scaffolds)} scaffolds to {output_file}")

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def get_current_user() -> str:
    """Get current system user"""
    import getpass
    return getpass.getuser()

def get_template_version() -> str:
    """Get current template version from spec-template.md"""
    template_file = Path(".specify/templates/spec-template.md")

    if not template_file.exists():
        return "unknown"

    try:
        content = template_file.read_text(encoding="utf-8")
        # Extract frontmatter
        if content.startswith("---"):
            lines = content.split('\n')
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if line.startswith("template_version:"):
                    version = line.split(":", 1)[1].strip().strip('"\'')
                    return version
    except Exception:
        pass

    return "unknown"

# ---------------------------------------------------------------------------
# CLI (simple test)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scaffold logger utility")
    parser.add_argument("--test", action="store_true", help="Run test")
    args = parser.parse_args()

    if args.test:
        print("Running scaffold logger test...")

        logger = ScaffoldLogger(Path("logs/scaffolds-test.yaml"))

        # Log test scaffold
        entry = logger.log_scaffold(
            project_name="test-project",
            template_version="2.1.0",
            profile="python-fastapi",
            created_by=get_current_user(),
            path="/tmp/test-project"
        )

        print(f"✅ Logged scaffold #{entry.id}: {entry.project_name}")

        # Query
        results = logger.query(limit=5)
        print(f"✅ Query returned {len(results)} results")

        # Stats
        stats = logger.get_stats()
        print(f"✅ Stats: {stats['total_scaffolds']} total scaffolds")

        # Cleanup
        Path("logs/scaffolds-test.yaml").unlink()
        print("✅ Test completed successfully")
