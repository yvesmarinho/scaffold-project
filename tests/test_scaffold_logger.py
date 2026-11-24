#!/usr/bin/env python3
"""
Tests for scaffold_logger.py

Tests:
- Logging scaffold operations
- Querying scaffolds
- Statistics generation
- CSV export
"""

import sys
import tempfile
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scaffold_logger import ScaffoldLogger


def test_log_scaffold():
    """Test logging a scaffold operation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.yaml"
        logger = ScaffoldLogger(log_file)

        entry = logger.log_scaffold(
            project_name="test-project",
            template_version="2.1.0",
            profile="python-fastapi",
            created_by="test_user",
            path="/tmp/test",
        )

        assert entry.id == 1
        assert entry.project_name == "test-project"
        assert entry.success is True

        # Verify it was saved
        entries = logger.query()
        assert len(entries) == 1
        assert entries[0].project_name == "test-project"


def test_query_filters():
    """Test querying with various filters"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.yaml"
        logger = ScaffoldLogger(log_file)

        # Log multiple scaffolds
        logger.log_scaffold("proj-1", "2.0.0", "python-fastapi", "user1", "/tmp/1")
        logger.log_scaffold("proj-2", "2.0.0", "typescript-next", "user2", "/tmp/2")
        logger.log_scaffold("proj-3", "2.1.0", "python-fastapi", "user1", "/tmp/3")

        # Filter by profile
        results = logger.query(profile="python-fastapi")
        assert len(results) == 2
        assert all(r.profile == "python-fastapi" for r in results)

        # Filter by user
        results = logger.query(created_by="user1")
        assert len(results) == 2

        # Filter by project name
        results = logger.query(project_name="proj-2")
        assert len(results) == 1
        assert results[0].project_name == "proj-2"


def test_wildcard_query():
    """Test wildcard matching in queries"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.yaml"
        logger = ScaffoldLogger(log_file)

        logger.log_scaffold(
            "vya-api-users", "2.0.0", "python-fastapi", "user1", "/tmp/1"
        )
        logger.log_scaffold(
            "vya-api-orders", "2.0.0", "python-fastapi", "user1", "/tmp/2"
        )
        logger.log_scaffold(
            "other-project", "2.0.0", "python-fastapi", "user1", "/tmp/3"
        )

        # Wildcard query
        results = logger.query(project_name="vya-*")
        assert len(results) == 2
        assert all(r.project_name.startswith("vya-") for r in results)


def test_query_limit():
    """Test query limit"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.yaml"
        logger = ScaffoldLogger(log_file)

        # Log 10 scaffolds
        for i in range(10):
            logger.log_scaffold(f"proj-{i}", "2.0.0", "python", "user1", f"/tmp/{i}")

        # Query with limit
        results = logger.query(limit=5)
        assert len(results) == 5


def test_statistics():
    """Test statistics generation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.yaml"
        logger = ScaffoldLogger(log_file)

        # Log scaffolds
        logger.log_scaffold(
            "proj-1", "2.0.0", "python-fastapi", "user1", "/tmp/1", success=True
        )
        logger.log_scaffold(
            "proj-2", "2.0.0", "typescript-next", "user2", "/tmp/2", success=True
        )
        logger.log_scaffold(
            "proj-3", "2.0.0", "python-fastapi", "user1", "/tmp/3", success=False
        )

        stats = logger.get_stats()

        assert stats["total_scaffolds"] == 3
        assert stats["success_rate"] == 66.7  # 2/3
        assert stats["by_profile"]["python-fastapi"] == 2
        assert stats["by_profile"]["typescript-next"] == 1
        assert stats["by_user"]["user1"] == 2
        assert stats["by_user"]["user2"] == 1


def test_failed_scaffold_logging():
    """Test logging failed scaffold"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.yaml"
        logger = ScaffoldLogger(log_file)

        entry = logger.log_scaffold(
            project_name="failed-proj",
            template_version="2.0.0",
            profile="python",
            created_by="user1",
            path="/tmp/failed",
            success=False,
            error_message="Template parse error",
        )

        assert entry.success is False
        assert entry.error_message == "Template parse error"

        # Query only failed
        results = logger.query(success=False)
        assert len(results) == 1
        assert results[0].success is False


def test_csv_export():
    """Test CSV export"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.yaml"
        logger = ScaffoldLogger(log_file)

        logger.log_scaffold("proj-1", "2.0.0", "python", "user1", "/tmp/1")
        logger.log_scaffold("proj-2", "2.0.0", "typescript", "user2", "/tmp/2")

        csv_file = Path(tmpdir) / "export.csv"
        logger.export_csv(csv_file)

        # Verify CSV exists and has content
        assert csv_file.exists()
        content = csv_file.read_text()
        assert "project_name" in content
        assert "proj-1" in content
        assert "proj-2" in content


if __name__ == "__main__":
    print("Running scaffold_logger.py tests...")

    tests = [
        test_log_scaffold,
        test_query_filters,
        test_wildcard_query,
        test_query_limit,
        test_statistics,
        test_failed_scaffold_logging,
        test_csv_export,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{'='*70}")
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"{'='*70}")

    sys.exit(0 if failed == 0 else 1)
