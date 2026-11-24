"""
tests/test_smoke_imp31.py — IMP-31: Smoke tests para CI/CD do template.

Cobertura:
  Existência e estrutura do workflow ci-template.yml:
    - arquivo existe em .github/workflows/ci-template.yml
    - é YAML válido
    - tem chave 'on' (trigger)
    - dispara em pull_request
    - dispara em push e pull_request para main (24/11/2026: master removido)
    - SEM filtro de paths (fonte de required status checks — check obrigatório
      com filtro de paths trava PRs que não o disparam)
    - job 'test' existe
    - usa uv (setup-uv com cache, uv sync --locked) e Python 3.12
    - job 'test' roda 'pytest tests/'
    - job 'cli-smoke' existe
    - job 'cli-smoke' executa --list-profiles --json
    - job 'cli-smoke' executa --dry-run
    - job 'cli-smoke' executa --publish --json
    - job 'lint' existe
    - job 'lint' compila scaffold.py
    - job 'lint' valida YAMLs dos profile descriptors
    - job 'lint' roda ruff no repositório inteiro
    - concurrency com cancel-in-progress
    - job 'cli-smoke' depende de 'test' (needs: test)
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

_PROJECT_ROOT = Path(__file__).parent.parent
_WORKFLOW_PATH = _PROJECT_ROOT / ".github" / "workflows" / "ci-template.yml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_workflow() -> dict:
    """Carrega o workflow YAML — pula o teste se pyyaml não estiver instalado."""
    if not _HAS_YAML:
        pytest.skip("pyyaml não instalado — pulando testes de estrutura YAML")
    return yaml.safe_load(_WORKFLOW_PATH.read_text(encoding="utf-8")) or {}


def _workflow_text() -> str:
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


# ===========================================================================
# Existência e validade
# ===========================================================================


class TestWorkflowExists:

    def test_file_exists(self) -> None:
        assert _WORKFLOW_PATH.exists(), f"Workflow não encontrado: {_WORKFLOW_PATH}"

    def test_file_is_valid_yaml(self) -> None:
        data = _load_workflow()
        assert isinstance(data, dict), "Workflow YAML não é um dict"

    def test_has_on_trigger(self) -> None:
        data = _load_workflow()
        assert "on" in data or True in data, "Chave 'on' ausente no workflow"

    def test_has_jobs(self) -> None:
        data = _load_workflow()
        assert "jobs" in data, "Chave 'jobs' ausente no workflow"


# ===========================================================================
# Triggers
# ===========================================================================


class TestWorkflowTriggers:

    def test_triggers_on_pull_request(self) -> None:
        text = _workflow_text()
        assert "pull_request" in text

    def test_triggers_on_push(self) -> None:
        text = _workflow_text()
        assert "push" in text

    def _triggers(self) -> dict:
        data = _load_workflow()
        return data.get("on", data.get(True, {}))

    def test_push_and_pr_target_main(self) -> None:
        triggers = self._triggers()
        assert triggers["push"]["branches"] == ["main"]
        assert triggers["pull_request"]["branches"] == ["main"]

    def test_no_paths_filter(self) -> None:
        for event in ("push", "pull_request"):
            config = self._triggers()[event] or {}
            assert "paths" not in config, f"{event} com filtro de paths"
            assert "paths-ignore" not in config, f"{event} com paths-ignore"

    def test_has_concurrency_cancel(self) -> None:
        text = _workflow_text()
        assert "cancel-in-progress" in text


# ===========================================================================
# Job: test (matrix)
# ===========================================================================


class TestJobTest:

    def test_job_test_exists(self) -> None:
        data = _load_workflow()
        assert "test" in data["jobs"], "Job 'test' ausente"

    def test_uses_python_312(self) -> None:
        data = _load_workflow()
        assert data["env"]["PYTHON_VERSION"] == "3.12"

    def test_job_test_uses_uv_locked(self) -> None:
        text = _workflow_text()
        assert "astral-sh/setup-uv" in text
        assert "uv sync --locked" in text

    def test_job_test_runs_full_suite(self) -> None:
        text = _workflow_text()
        assert "pytest tests/" in text, "'pytest tests/' ausente nos steps"

    def test_job_test_installs_pinned_specify_cli(self) -> None:
        """`scaffold new` roda `specify init`; sem o CLI a criação retorna erro."""
        steps = _load_workflow()["jobs"]["test"]["steps"]
        runs = " ".join(str(s.get("run", "")) for s in steps)
        assert "uv tool install specify-cli" in runs
        assert "github/spec-kit.git@v" in runs, "specify-cli sem versão fixada"

    def test_job_test_uses_uv_cache(self) -> None:
        text = _workflow_text()
        assert "enable-cache: true" in text, "Cache do uv ausente"


# ===========================================================================
# Job: cli-smoke
# ===========================================================================


class TestJobCliSmoke:

    def test_job_cli_smoke_exists(self) -> None:
        data = _load_workflow()
        assert "cli-smoke" in data["jobs"], "Job 'cli-smoke' ausente"

    def test_cli_smoke_needs_test(self) -> None:
        data = _load_workflow()
        needs = data["jobs"]["cli-smoke"].get("needs", [])
        if isinstance(needs, str):
            needs = [needs]
        assert "test" in needs, "cli-smoke não declara needs: test"

    def test_cli_smoke_runs_list_profiles(self) -> None:
        text = _workflow_text()
        assert "--list-profiles --json" in text

    def test_cli_smoke_runs_dry_run(self) -> None:
        text = _workflow_text()
        assert "--dry-run" in text

    def test_cli_smoke_runs_publish(self) -> None:
        text = _workflow_text()
        assert "--publish --json" in text


# ===========================================================================
# Job: lint
# ===========================================================================


class TestJobLint:

    def test_job_lint_exists(self) -> None:
        data = _load_workflow()
        assert "lint" in data["jobs"], "Job 'lint' ausente"

    def test_lint_compiles_scaffold_py(self) -> None:
        text = _workflow_text()
        assert "py_compile" in text and "scaffold.py" in text

    def test_lint_validates_profile_descriptors_yaml(self) -> None:
        text = _workflow_text()
        assert "profile-descriptors" in text and "yaml" in text.lower()

    def test_lint_runs_ruff_on_whole_repo(self) -> None:
        text = _workflow_text()
        assert "ruff check ." in text, "ruff no repositório inteiro ausente"
