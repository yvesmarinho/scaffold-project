"""
Tests for migrate-daily-activities.py script

Part of: IMP-50 — Sistema de documentação incremental — Docs + Migração
Created: 2026-04-05

Tests:
- Format detection (canonical vs. legacy)
- Metadata extraction
- Legacy format parsing (very old, old, semi-canonical)
- Block conversion to canonical
- File migration workflow
- Backup and restore
"""

import importlib.util
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import migration script
import sys
import importlib.util

# Load module from file path (handles hyphens in filename)
script_path = Path(__file__).parent.parent / "scripts" / "migrate-daily-activities.py"
spec = importlib.util.spec_from_file_location("migrate_module", script_path)
migrate_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migrate_module)

SessionDocumentMigrator = migrate_module.SessionDocumentMigrator
ActivityBlock = migrate_module.ActivityBlock


# ==================== Fixtures ====================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def migrator():
    """Create migrator instance."""
    return SessionDocumentMigrator(dry_run=False, force=False)


@pytest.fixture
def sample_canonical_content():
    """Sample canonical format content."""
    return """# 📝 Daily Activities — 2026-04-03

**Project**: Enterprise Scaffold Project Template
**Branch**: master
**Session**: 2026-04-03 (Thursday)
**Initial HEAD**: abc1234

---

> **ℹ️ About This Document**
>
> This is an **incremental activity log** following the [Session Docs Style Guide](../../SESSION_DOCS_STYLE_GUIDE.md).
> Each significant activity is added as a new block with timestamp, context, steps, and outcome.
> Activities are append-only — previous entries are never modified or removed.

---

### Session Initialization

**09:00 — ✅ Completo**

**Objetivo**: Initialize work session

**Contexto**: New session startup

**Passos executados**:
1. Validated MCP configuration
2. Loaded project rules
3. Created session docs

**Resultado**: Session successfully initialized

**Status**: ✅ Completo

---

### Second Activity

**10:30 — ✅ Completo**

**Objetivo**: Complete some work

**Contexto**: Continuing session work

**Passos executados**:
1. Analyzed requirements
2. Implemented solution

**Resultado**: Work completed successfully

**Status**: ✅ Completo

---
"""


@pytest.fixture
def sample_very_old_content():
    """Sample very old format (TODAY_ACTIVITIES)."""
    return """# 📅 Today's Activities - January 28, 2026

**Date**: 2026-01-28
**Project**: Enterprise Scaffold Project Template
**Status**: 🔄 In Progress

---

## 🌅 Morning Session

### Session Start
- **Time**: 09:00
- **Objective**: MCP session initialization
- **Status**: ✅ Completed

### Activities Completed

#### 1. MCP Session Initialization
- **Status**: ✅ Completed
- **Duration**: ~15 minutes
- **Actions**:
  - Initialized Model Context Protocol session
  - Established workspace context
  - Loaded project configuration

#### 2. Previous Session Recovery
- **Status**: ✅ Completed
- **Duration**: ~20 minutes
- **Files Recovered**:
  - `/docs/INDEX.md` - Project index
  - `/docs/TODO.md` - Task tracking
"""


@pytest.fixture
def sample_old_structured_content():
    """Sample old structured format (2026-02-27 style)."""
    return """# 📅 Daily Activities — 27 de Fevereiro de 2026

**Date**: 2026-02-27
**Status**: ✅ Encerrada

---

## 🕐 Linha do Tempo

### Atividade: Session Initialization

**Objetivo**: MCP startup and context recovery

| Atividade | Resultado |
|-----------|-----------|
| MCP inicializado | ✅ |
| Regras Copilot carregadas | ✅ |

### Atividade: Debate Arquitetural

**Objetivo**: Definir domain profiles

**Contexto**: Need adaptable templates for DevOps work

**Passos executados**:
- Análise da estrutura existente
- Proposta de arquitetura 3 camadas
- Identificação de 3 gaps

**Resultado**: Architecture defined, documentation created
"""


@pytest.fixture
def sample_semi_canonical_content():
    """Sample semi-canonical format (has fields but no separators)."""
    return """# 📝 Daily Activities — 2026-03-23

**Session**: 2026-03-23
**Branch**: master

### Session Initialization

**09:00 — ✅ Completo**

**Objetivo**: Executar workflow completo de inicialização

**Contexto**: New session startup following session-manager protocol

**Passos executados**:
1. ✅ Leitura de session-start.prompt.md
2. ✅ Carregamento de project rules
3. ✅ Recuperação de contexto da sessão anterior

**Resultado**: Sessão inicializada com sucesso

**Arquivos criados**:
- docs/SESSIONS/2026-03-23/SESSION_RECOVERY_2026-03-23.md
- docs/SESSIONS/2026-03-23/DAILY_ACTIVITIES_2026-03-23.md

**Status**: ✅ Completo

### Bug Analysis & Fix

**16:00 — ✅ Completo**

**Objetivo**: Fix BUG-47 nested folder issue

**Contexto**: Upgrade command creating nested directories

**Passos executados**:
1. Identified root cause in scaffold.py
2. Implemented fix with property logic
3. Added comprehensive tests

**Resultado**: Bug fixed, tests passing

**Arquivos modificados/criados**:
- scripts/lib/project.py (+12/-3)
- tests/test_bug47.py (+150/-0)

**Commits**:
- `abc1234` — fix(scaffold): correct nested folder issue

**Status**: ✅ Completo
"""


# ==================== Tests: Format Detection ====================

def test_is_canonical_format_detects_canonical(migrator, sample_canonical_content):
    """Test detection of canonical format."""
    assert migrator.is_canonical_format(sample_canonical_content) is True


def test_is_canonical_format_detects_legacy(migrator, sample_very_old_content):
    """Test detection of legacy format."""
    assert migrator.is_canonical_format(sample_very_old_content) is False


def test_is_canonical_format_detects_semi_canonical(migrator, sample_semi_canonical_content):
    """Test semi-canonical (has fields but missing markers) detected as non-canonical."""
    assert migrator.is_canonical_format(sample_semi_canonical_content) is False


# ==================== Tests: Metadata Extraction ====================

def test_extract_metadata_from_filename(migrator, temp_dir):
    """Test metadata extraction from file path."""
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-04-05.md"
    file_path.touch()

    metadata = migrator.extract_metadata(file_path)

    assert metadata["date"] == "2026-04-05"
    assert metadata["day_of_week"] == "Sunday"  # 2026-04-05 is Sunday
    assert metadata["original_filename"] == "DAILY_ACTIVITIES_2026-04-05.md"
    assert "migration_date" in metadata


def test_extract_metadata_handles_invalid_date(migrator, temp_dir):
    """Test metadata extraction with invalid date."""
    file_path = temp_dir / "ACTIVITIES_invalid.md"
    file_path.touch()

    metadata = migrator.extract_metadata(file_path)

    assert metadata["date"] == "unknown"
    assert metadata["day_of_week"] == "unknown"


# ==================== Tests: Legacy Parsing ====================

def test_parse_very_old_format(migrator, sample_very_old_content, temp_dir):
    """Test parsing very old TODAY_ACTIVITIES format."""
    file_path = temp_dir / "TODAY_ACTIVITIES_2026-01-28.md"
    blocks = migrator.parse_legacy_content(sample_very_old_content, file_path)

    assert len(blocks) >= 1
    # Should have extracted some activity blocks
    assert any("MCP" in block.title or "Session" in block.title for block in blocks)


def test_parse_old_structured_format(migrator, sample_old_structured_content, temp_dir):
    """Test parsing old structured format with tables."""
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-02-27.md"
    blocks = migrator.parse_legacy_content(sample_old_structured_content, file_path)

    assert len(blocks) >= 1
    # Should have activity blocks with objectives
    assert any(block.objective for block in blocks)


def test_parse_semi_canonical_format(migrator, sample_semi_canonical_content, temp_dir):
    """Test parsing semi-canonical format."""
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-03-23.md"
    blocks = migrator.parse_legacy_content(sample_semi_canonical_content, file_path)

    assert len(blocks) >= 2  # Should have at least 2 activities

    # First block should have session initialization
    assert "Session Initialization" in blocks[0].title or "Initialization" in blocks[0].title
    assert blocks[0].objective is not None
    assert blocks[0].timestamp is not None

    # Should have extracted files and commits from second block
    if len(blocks) > 1:
        bug_block = blocks[1]
        assert bug_block.files or bug_block.commits


# ==================== Tests: Block Conversion ====================

def test_activity_block_to_canonical():
    """Test converting ActivityBlock to canonical format."""
    block = ActivityBlock(
        title="Test Activity",
        timestamp="14:30",
        status="✅ Completo",
        objective="Test objective",
        context="Test context",
        steps=["Step 1", "Step 2", "Step 3"],
        result="Test result",
        decisions="Test decision",
        files=["file1.py", "file2.md"],
        commits=["`abc1234` — fix: test"],
    )

    canonical = block.to_canonical()

    # Check structure
    assert canonical.startswith("---\n\n###")
    assert "**14:30 — ✅ Completo**" in canonical
    assert "**Objetivo**: Test objective" in canonical
    assert "**Contexto**: Test context" in canonical
    assert "**Passos executados**:" in canonical
    assert "1. Step 1" in canonical
    assert "**Resultado**: Test result" in canonical
    assert "**Decisões técnicas**: Test decision" in canonical
    assert "**Arquivos modificados/criados**:" in canonical
    assert "- file1.py" in canonical
    assert "**Commits**:" in canonical
    assert "**Status**: ✅ Completo" in canonical


def test_activity_block_minimal_fields():
    """Test block with minimal required fields."""
    block = ActivityBlock(
        title="Minimal Activity",
        timestamp="10:00",
        status="✅ Completo",
    )

    canonical = block.to_canonical()

    assert "### Minimal Activity" in canonical
    assert "**10:00 — ✅ Completo**" in canonical
    assert "**Status**: ✅ Completo" in canonical


# ==================== Tests: File Migration ====================

def test_migrate_file_skips_canonical(migrator, temp_dir, sample_canonical_content):
    """Test that canonical files are skipped without --force."""
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-04-03.md"
    file_path.write_text(sample_canonical_content)

    result = migrator.migrate_file(file_path)

    assert result is True  # Success (skipped)
    assert migrator.files_skipped == 1
    assert migrator.files_migrated == 0


def test_migrate_file_forces_canonical_with_flag(temp_dir, sample_canonical_content):
    """Test that --force migrates even canonical files."""
    migrator = SessionDocumentMigrator(dry_run=False, force=True)
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-04-03.md"
    file_path.write_text(sample_canonical_content)

    result = migrator.migrate_file(file_path)

    assert result is True
    assert migrator.files_migrated == 1


def test_migrate_file_creates_backup(migrator, temp_dir, sample_semi_canonical_content):
    """Test that migration creates backup file."""
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-03-23.md"
    file_path.write_text(sample_semi_canonical_content)

    migrator.migrate_file(file_path)

    backup_path = temp_dir / "DAILY_ACTIVITIES_2026-03-23.md.backup"
    assert backup_path.exists()

    # Backup should have original content
    backup_content = backup_path.read_text()
    assert backup_content == sample_semi_canonical_content


def test_migrate_file_produces_canonical_output(migrator, temp_dir, sample_semi_canonical_content):
    """Test that migration produces canonical format."""
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-03-23.md"
    file_path.write_text(sample_semi_canonical_content)

    migrator.migrate_file(file_path)

    new_content = file_path.read_text()

    # Check canonical markers
    assert "SESSION_DOCS_STYLE_GUIDE.md" in new_content
    assert "📝 Migration Note" in new_content
    assert "migrated from legacy format" in new_content
    assert new_content.count("---\n\n###") >= 2  # At least 2 activity blocks


def test_migrate_file_preserves_content(migrator, temp_dir, sample_semi_canonical_content):
    """Test that migration preserves original content."""
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-03-23.md"
    file_path.write_text(sample_semi_canonical_content)

    migrator.migrate_file(file_path)

    new_content = file_path.read_text()

    # Key content should be preserved
    assert "Session Initialization" in new_content
    assert "Bug Analysis & Fix" in new_content
    assert "Executar workflow completo" in new_content
    assert "BUG-47" in new_content or "nested folder" in new_content


def test_migrate_file_dry_run(temp_dir, sample_semi_canonical_content):
    """Test dry-run mode doesn't modify files."""
    migrator = SessionDocumentMigrator(dry_run=True, force=False)
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-03-23.md"
    original_content = sample_semi_canonical_content
    file_path.write_text(original_content)

    migrator.migrate_file(file_path)

    # File should be unchanged
    assert file_path.read_text() == original_content

    # No backup should be created
    backup_path = file_path.with_suffix(".md.backup")
    assert not backup_path.exists()

    # Counter should still increment
    assert migrator.files_migrated == 1


# ==================== Tests: Directory Migration ====================

def test_migrate_directory(migrator, temp_dir, sample_semi_canonical_content, sample_very_old_content):
    """Test migrating all files in a directory."""
    # Create multiple files
    (temp_dir / "DAILY_ACTIVITIES_2026-03-23.md").write_text(sample_semi_canonical_content)
    (temp_dir / "TODAY_ACTIVITIES_2026-01-28.md").write_text(sample_very_old_content)

    migrator.migrate_directory(temp_dir)

    assert migrator.files_migrated == 2


def test_migrate_directory_no_files(migrator, temp_dir, capsys):
    """Test migrating directory with no activity files."""
    migrator.migrate_directory(temp_dir)

    captured = capsys.readouterr()
    assert "No activity files found" in captured.out


# ==================== Tests: Edge Cases ====================

def test_migrate_file_handles_read_error(migrator, temp_dir):
    """Test handling of file read errors."""
    file_path = temp_dir / "nonexistent.md"

    result = migrator.migrate_file(file_path)

    assert result is False
    assert migrator.files_failed == 1


def test_extract_commits(migrator):
    """Test commit extraction from text."""
    text = """
    **Commits**:
    - `abc1234` — fix: something
    - `def5678` — feat: another thing

    Also mentioned `987fedc` in passing.
    """

    commits = migrator._extract_commits(text)

    assert len(commits) == 3
    assert "`abc1234`" in commits
    assert "`def5678`" in commits


def test_extract_files(migrator):
    """Test file path extraction from text."""
    text = """
    Created: scripts/lib/project.py
    Modified: `tests/test_example.py`
    - docs/README.md
    """

    files = migrator._extract_files(text)

    assert "scripts/lib/project.py" in files or "tests/test_example.py" in files


# ==================== Integration Tests ====================

def test_full_migration_workflow(temp_dir, sample_semi_canonical_content):
    """Test complete migration workflow."""
    # Setup
    migrator = SessionDocumentMigrator(dry_run=False, force=False)
    file_path = temp_dir / "DAILY_ACTIVITIES_2026-03-23.md"
    file_path.write_text(sample_semi_canonical_content)

    # Migrate
    result = migrator.migrate_file(file_path)

    # Verify
    assert result is True
    assert migrator.files_migrated == 1
    assert migrator.files_failed == 0

    # Check backup exists
    assert (temp_dir / "DAILY_ACTIVITIES_2026-03-23.md.backup").exists()

    # Check new content is canonical
    new_content = file_path.read_text()
    assert migrator.is_canonical_format(new_content) is True

    # Check metadata is present
    assert "2026-03-23" in new_content
    assert "📝 Migration Note" in new_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
