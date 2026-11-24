"""
Tests for GitHubWorkflowMerger

Sprint 3 (P1 HIGH): Validar merge inteligente de workflows YAML

Test strategy:
- Test file detection (.github/workflows/*.yml)
- Test YAML parsing (name, on, permissions, jobs)
- Test merge decision logic
- Test triggers merge (on: push, schedule)
- Test permissions merge
- Test jobs merge (security jobs vs custom)
- Test action version updates
- Test full integration with temp files
- Test edge cases (malformed YAML, no changes)
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from scripts.lib.github_workflow_merge import (
    GitHubWorkflowMerger,
    WorkflowContent,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_dir():
    """Cria diretório temporário para testes."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_workflow_v1():
    """Workflow básico versão 1 (existente)."""
    return """name: CI Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Run pytest
        run: pytest tests/
"""


@pytest.fixture
def sample_workflow_v2():
    """Workflow versão 2 com security scans (template)."""
    return """name: CI Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:

permissions:
  contents: read
  security-events: write

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Run pytest
        run: pytest tests/

  secret-scan:
    name: Secret Scanning
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2.3.9
"""


@pytest.fixture
def merger():
    """Instância do merger para testes."""
    return GitHubWorkflowMerger()


# =============================================================================
# Test 01: File Detection
# =============================================================================


def test_01_can_merge_detects_workflow_files(merger, temp_dir):
    """Test 01: can_merge() detecta workflows corretamente."""
    # Criar estrutura .github/workflows/
    workflows_dir = temp_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    # Casos positivos
    valid_yml = workflows_dir / "test.yml"
    valid_yml.touch()
    assert merger.can_merge(valid_yml), "Should detect .yml in workflows/"

    valid_yaml = workflows_dir / "test.yaml"
    valid_yaml.touch()
    assert merger.can_merge(valid_yaml), "Should detect .yaml in workflows/"

    # Casos negativos
    wrong_dir = temp_dir / "workflows" / "test.yml"
    wrong_dir.parent.mkdir(parents=True)
    wrong_dir.touch()
    assert not merger.can_merge(wrong_dir), "Should reject workflows/ outside .github/"

    wrong_ext = workflows_dir / "test.txt"
    wrong_ext.touch()
    assert not merger.can_merge(wrong_ext), "Should reject non-.yml files"


# =============================================================================
# Test 02-03: Parsing
# =============================================================================


def test_02_parse_workflow_yaml(merger, sample_workflow_v1):
    """Test 02: Parse YAML workflow corretamente."""
    wf = merger._parse_workflow(sample_workflow_v1)

    assert isinstance(wf, WorkflowContent)
    assert wf.name == "CI Tests"
    assert "push" in wf.on_triggers
    assert "pull_request" in wf.on_triggers
    assert wf.permissions["contents"] == "read"
    assert "test" in wf.jobs


def test_03_parse_workflow_with_schedule(merger, sample_workflow_v2):
    """Test 03: Parse workflow com schedule trigger."""
    wf = merger._parse_workflow(sample_workflow_v2)

    assert "schedule" in wf.on_triggers
    assert "workflow_dispatch" in wf.on_triggers
    assert wf.permissions["security-events"] == "write"
    assert "secret-scan" in wf.jobs


# =============================================================================
# Test 04-06: Merge Decision Logic
# =============================================================================


def test_04_should_merge_detects_new_security_jobs(
    merger, sample_workflow_v1, sample_workflow_v2
):
    """Test 04: Detecta novos security jobs."""
    existing_wf = merger._parse_workflow(sample_workflow_v1)
    template_wf = merger._parse_workflow(sample_workflow_v2)

    decision = merger._should_merge(existing_wf, template_wf, "test.yml")

    assert decision.should_merge
    assert any("security" in change.lower() for change in decision.changes)


def test_05_should_merge_detects_new_triggers(
    merger, sample_workflow_v1, sample_workflow_v2
):
    """Test 05: Detecta novos triggers (schedule, workflow_dispatch)."""
    existing_wf = merger._parse_workflow(sample_workflow_v1)
    template_wf = merger._parse_workflow(sample_workflow_v2)

    decision = merger._should_merge(existing_wf, template_wf, "test.yml")

    assert decision.should_merge
    # Deve detectar schedule e workflow_dispatch
    assert any("trigger" in change.lower() for change in decision.changes)


def test_06_should_skip_if_already_updated(merger, sample_workflow_v2):
    """Test 06: Skip se já está atualizado."""
    template_wf = merger._parse_workflow(sample_workflow_v2)

    decision = merger._should_merge(
        template_wf, template_wf, "test.yml"  # Existing == Template
    )

    assert not decision.should_merge
    assert "up-to-date" in decision.reason.lower()


# =============================================================================
# Test 07-09: Triggers Merge
# =============================================================================


def test_07_merge_triggers_adds_new_triggers(merger):
    """Test 07: Merge adiciona novos triggers."""
    existing = {
        "push": {"branches": ["main"]},
        "pull_request": {"branches": ["main"]},
    }
    template = {
        "push": {"branches": ["main", "develop"]},
        "pull_request": {"branches": ["main"]},
        "schedule": [{"cron": "0 6 * * *"}],
        "workflow_dispatch": None,
    }

    merged = merger._merge_triggers(existing, template)

    assert "schedule" in merged
    assert "workflow_dispatch" in merged
    assert "push" in merged


def test_08_merge_triggers_preserves_existing(merger):
    """Test 08: Merge preserva triggers customizados."""
    existing = {
        "push": {"branches": ["main", "feature/*"]},
        "release": {"types": ["published"]},
    }
    template = {
        "push": {"branches": ["main"]},
        "schedule": [{"cron": "0 6 * * *"}],
    }

    merged = merger._merge_triggers(existing, template)

    # Deve preservar "release" trigger customizado
    assert "release" in merged
    assert merged["release"]["types"] == ["published"]


def test_09_merge_triggers_merges_branches(merger):
    """Test 09: Merge combina branches arrays."""
    existing = {
        "push": {"branches": ["main"]},
    }
    template = {
        "push": {"branches": ["main", "develop"]},
    }

    merged = merger._merge_triggers(existing, template)

    # Deve ter ambos branches
    assert set(merged["push"]["branches"]) >= {"main", "develop"}


# =============================================================================
# Test 10-11: Permissions and Jobs Merge
# =============================================================================


def test_10_merge_permissions_adds_new(merger):
    """Test 10: Merge permissions adiciona novas."""
    existing = {"contents": "read"}
    template = {"contents": "read", "security-events": "write"}

    merged = merger._merge_permissions(existing, template)

    assert merged["security-events"] == "write"


def test_11_merge_jobs_adds_security_jobs(
    merger, sample_workflow_v1, sample_workflow_v2
):
    """Test 11: Merge jobs adiciona security jobs."""
    existing_wf = merger._parse_workflow(sample_workflow_v1)
    template_wf = merger._parse_workflow(sample_workflow_v2)

    merged_jobs = merger._merge_jobs(existing_wf.jobs, template_wf.jobs)

    # Deve ter job original + security job
    assert "test" in merged_jobs
    assert "secret-scan" in merged_jobs


# =============================================================================
# Test 12-14: Action Version Updates
# =============================================================================


def test_12_merge_job_steps_updates_action_versions(merger):
    """Test 12: Merge steps atualiza action versions."""
    existing_job = {
        "runs-on": "ubuntu-latest",
        "steps": [
            {"name": "Checkout", "uses": "actions/checkout@v3"},
            {"name": "Run tests", "run": "pytest"},
        ],
    }
    template_job = {
        "runs-on": "ubuntu-latest",
        "steps": [
            {"name": "Checkout", "uses": "actions/checkout@v4"},
        ],
    }

    merged = merger._merge_job_steps(existing_job, template_job)

    # Action version deve ser atualizada para v4
    checkout_step = next(s for s in merged["steps"] if s.get("name") == "Checkout")
    assert "@v4" in checkout_step["uses"]


def test_13_merge_job_steps_preserves_custom_steps(merger):
    """Test 13: Merge steps preserva steps customizados."""
    existing_job = {
        "runs-on": "ubuntu-latest",
        "steps": [
            {"name": "Checkout", "uses": "actions/checkout@v3"},
            {"name": "Custom Build", "run": "make build"},
        ],
    }
    template_job = {
        "runs-on": "ubuntu-latest",
        "steps": [
            {"name": "Checkout", "uses": "actions/checkout@v4"},
        ],
    }

    merged = merger._merge_job_steps(existing_job, template_job)

    # Step customizado deve ser preservado
    assert any(s.get("name") == "Custom Build" for s in merged["steps"])


def test_14_merge_jobs_preserves_custom_jobs(merger):
    """Test 14: Merge preserva jobs customizados."""
    existing_jobs = {
        "test": {"runs-on": "ubuntu-latest", "steps": []},
        "custom-deploy": {"runs-on": "ubuntu-latest", "steps": []},
    }
    template_jobs = {
        "test": {"runs-on": "ubuntu-latest", "steps": []},
        "secret-scan": {"runs-on": "ubuntu-latest", "steps": []},
    }

    merged = merger._merge_jobs(existing_jobs, template_jobs)

    # Job customizado deve ser preservado
    assert "custom-deploy" in merged
    # Novo security job deve ser adicionado
    assert "secret-scan" in merged


# =============================================================================
# Test 15-16: Full Integration
# =============================================================================


def test_15_full_merge_creates_backup(
    merger, temp_dir, sample_workflow_v1, sample_workflow_v2
):
    """Test 15: Merge completo cria backup do arquivo original."""
    workflows_dir = temp_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    existing_path = workflows_dir / "test.yml"
    existing_path.write_text(sample_workflow_v1, encoding="utf-8")

    result = merger.merge(existing_path, sample_workflow_v2, interactive=False)

    assert result.status == "merged"
    backup_path = existing_path.with_suffix(".yml.backup")
    assert backup_path.exists(), "Should create backup"
    assert backup_path.read_text(encoding="utf-8") == sample_workflow_v1


def test_16_handles_malformed_yaml(merger, temp_dir):
    """Test 16: Handle YAML malformado gracefully."""
    workflows_dir = temp_dir / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)

    malformed = """name: Test
on:
  push:
    branches: [main
jobs:
  test:
"""

    existing_path = workflows_dir / "test.yml"
    existing_path.write_text(malformed, encoding="utf-8")

    template = """name: Test
on:
  push:
    branches: [main]
"""

    # Não deve crashar (pode dar error ou skip)
    result = merger.merge(existing_path, template, interactive=False)

    assert result.status in ["merged", "skipped", "error"]
