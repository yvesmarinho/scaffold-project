"""
tests/test_smoke_imp33.py — IMP-33: Smoke tests para perfis novos (devops-security,
devops-infrastructure, devops-analysis) e validação de warnings=0.

Cobertura:
  Descritores novos — existência e campos obrigatórios:
    - devops-security.yaml existe no diretório profile-descriptors
    - devops-security tem layer == 'transversal'
    - devops-security tem excludes_with vazio (nenhum conflito)
    - devops-security combina com devops-programming
    - devops-security combina com python-fastapi
    - devops-infrastructure.yaml existe no diretório profile-descriptors
    - devops-infrastructure tem layer == 'core'
    - devops-infrastructure exclui devops-programming
    - devops-infrastructure exclui devops-analysis
    - devops-infrastructure combina com devops-security
    - devops-analysis.yaml existe no diretório profile-descriptors
    - devops-analysis tem layer == 'core'
    - devops-analysis exclui devops-programming
    - devops-analysis exclui devops-infrastructure
    - devops-analysis combina com devops-security

  Validação cruzada — meta principal de IMP-33:
    - --validate retorna 0 warnings (9 warnings → 0)
    - --validate --json tem 'warnings' == 0
    - --validate --json tem 'profiles_checked' == 13
    - devops-security não gera warnings no validator
    - devops-infrastructure não gera warnings no validator
    - devops-analysis não gera warnings no validator
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.validate import validate_descriptors  # noqa: E402

_PROJECT_ROOT = Path(__file__).parent.parent
_DESCRIPTORS_DIR = _PROJECT_ROOT / "profile-descriptors"
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
_PYTHON = sys.executable


# ===========================================================================
# Helpers
# ===========================================================================


def _load_yaml(name: str) -> dict:
    """Carrega e parseia um descriptor YAML pelo nome do perfil."""
    path = _DESCRIPTORS_DIR / f"{name}.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _combines_names(data: dict) -> list[str]:
    """Extrai os nomes de combines_with de um descriptor."""
    return [entry["name"] for entry in data.get("combines_with", [])]


# ===========================================================================
# devops-security descriptor
# ===========================================================================


class TestDevopsSecurityDescriptor:
    def test_descriptor_file_exists(self):
        assert (_DESCRIPTORS_DIR / "devops-security.yaml").is_file()

    def test_name_is_correct(self):
        data = _load_yaml("devops-security")
        assert data["name"] == "devops-security"

    def test_has_description(self):
        data = _load_yaml("devops-security")
        assert data.get("description")

    def test_layer_is_transversal(self):
        data = _load_yaml("devops-security")
        assert data["layer"] == "transversal"

    def test_has_version(self):
        data = _load_yaml("devops-security")
        assert data.get("VERSION")

    def test_excludes_with_is_empty(self):
        """Perfil transversal não conflita com nenhum outro perfil."""
        data = _load_yaml("devops-security")
        assert data.get("excludes_with", []) == []

    def test_combines_with_devops_programming(self):
        data = _load_yaml("devops-security")
        assert "devops-programming" in _combines_names(data)

    def test_combines_with_python_fastapi(self):
        data = _load_yaml("devops-security")
        assert "python-fastapi" in _combines_names(data)

    def test_combines_with_python_flask(self):
        data = _load_yaml("devops-security")
        assert "python-flask" in _combines_names(data)

    def test_combines_with_typescript_next(self):
        data = _load_yaml("devops-security")
        assert "typescript-next" in _combines_names(data)

    def test_combines_with_k8s_helm(self):
        data = _load_yaml("devops-security")
        assert "k8s-helm" in _combines_names(data)

    def test_combines_with_terraform_aws(self):
        data = _load_yaml("devops-security")
        assert "terraform-aws" in _combines_names(data)

    def test_validator_reports_no_warnings_for_devops_security(self):
        report = validate_descriptors(_DESCRIPTORS_DIR)
        security_result = next(
            (r for r in report.results if r.name == "devops-security"), None
        )
        assert security_result is not None, "devops-security não encontrado no report"
        assert security_result.status in ("ok",), (
            f"devops-security status inesperado: {security_result.status}; "
            f"issues: {[i.message for i in security_result.issues]}"
        )


# ===========================================================================
# devops-infrastructure descriptor (stub)
# ===========================================================================


class TestDevopsInfrastructureDescriptor:
    def test_descriptor_file_exists(self):
        assert (_DESCRIPTORS_DIR / "devops-infrastructure.yaml").is_file()

    def test_name_is_correct(self):
        data = _load_yaml("devops-infrastructure")
        assert data["name"] == "devops-infrastructure"

    def test_has_description(self):
        data = _load_yaml("devops-infrastructure")
        assert data.get("description")

    def test_layer_is_core(self):
        data = _load_yaml("devops-infrastructure")
        assert data["layer"] == "core"

    def test_has_version(self):
        data = _load_yaml("devops-infrastructure")
        assert data.get("VERSION")

    def test_excludes_devops_programming(self):
        data = _load_yaml("devops-infrastructure")
        assert "devops-programming" in data.get("excludes_with", [])

    def test_excludes_devops_analysis(self):
        data = _load_yaml("devops-infrastructure")
        assert "devops-analysis" in data.get("excludes_with", [])

    def test_combines_with_devops_security(self):
        data = _load_yaml("devops-infrastructure")
        assert "devops-security" in _combines_names(data)

    def test_combines_with_k8s_helm(self):
        data = _load_yaml("devops-infrastructure")
        assert "k8s-helm" in _combines_names(data)

    def test_combines_with_terraform_aws(self):
        data = _load_yaml("devops-infrastructure")
        assert "terraform-aws" in _combines_names(data)

    def test_validator_reports_no_warnings(self):
        report = validate_descriptors(_DESCRIPTORS_DIR)
        infra_result = next(
            (r for r in report.results if r.name == "devops-infrastructure"), None
        )
        assert (
            infra_result is not None
        ), "devops-infrastructure não encontrado no report"
        assert infra_result.status in ("ok",), (
            f"devops-infrastructure status inesperado: {infra_result.status}; "
            f"issues: {[i.message for i in infra_result.issues]}"
        )


# ===========================================================================
# devops-analysis descriptor (stub)
# ===========================================================================


class TestDevopsAnalysisDescriptor:
    def test_descriptor_file_exists(self):
        assert (_DESCRIPTORS_DIR / "devops-analysis.yaml").is_file()

    def test_name_is_correct(self):
        data = _load_yaml("devops-analysis")
        assert data["name"] == "devops-analysis"

    def test_has_description(self):
        data = _load_yaml("devops-analysis")
        assert data.get("description")

    def test_layer_is_core(self):
        data = _load_yaml("devops-analysis")
        assert data["layer"] == "core"

    def test_has_version(self):
        data = _load_yaml("devops-analysis")
        assert data.get("VERSION")

    def test_excludes_devops_programming(self):
        data = _load_yaml("devops-analysis")
        assert "devops-programming" in data.get("excludes_with", [])

    def test_excludes_devops_infrastructure(self):
        data = _load_yaml("devops-analysis")
        assert "devops-infrastructure" in data.get("excludes_with", [])

    def test_combines_with_devops_security(self):
        data = _load_yaml("devops-analysis")
        assert "devops-security" in _combines_names(data)

    def test_combines_with_data_pipeline_airflow(self):
        data = _load_yaml("devops-analysis")
        assert "data-pipeline-airflow" in _combines_names(data)

    def test_combines_with_data_warehouse_dbt(self):
        data = _load_yaml("devops-analysis")
        assert "data-warehouse-dbt" in _combines_names(data)

    def test_validator_reports_no_warnings(self):
        report = validate_descriptors(_DESCRIPTORS_DIR)
        analysis_result = next(
            (r for r in report.results if r.name == "devops-analysis"), None
        )
        assert analysis_result is not None, "devops-analysis não encontrado no report"
        assert analysis_result.status in ("ok",), (
            f"devops-analysis status inesperado: {analysis_result.status}; "
            f"issues: {[i.message for i in analysis_result.issues]}"
        )


# ===========================================================================
# Meta-validação: IMP-33 goal — 9 warnings → 0 warnings
# ===========================================================================


class TestValidateZeroWarnings:
    """Objetivo central do IMP-33: eliminar os 9 warnings de --validate."""

    def _run_json(self) -> dict:
        proc = subprocess.run(
            [_PYTHON, str(_SCRIPTS_DIR / "scaffold.py"), "--validate", "--json"],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
        )
        return json.loads(proc.stdout)

    def test_validate_zero_warnings_programmatic(self):
        """validate_descriptors() deve retornar 0 warnings para os descritores reais."""
        report = validate_descriptors(_DESCRIPTORS_DIR)
        assert report.total_warnings == 0, (
            f"Esperado 0 warnings, obtido {report.total_warnings}. "
            f"Mensagens: {[i.message for r in report.results for i in r.warnings]}"
        )

    def test_validate_zero_warnings_cli_json(self):
        """--validate --json deve reportar warnings == 0."""
        data = self._run_json()
        assert (
            data.get("warnings", data.get("total_warnings", -1)) == 0
        ), f"--validate --json retornou warnings != 0: {data}"

    def test_validate_thirteen_profiles_cli(self):
        """Todos os perfis registrados devem ser encontrados."""
        data = self._run_json()
        assert (
            data["profiles_checked"] == 22
        ), f"Esperado 22 perfis, obtido {data['profiles_checked']}"

    def test_validate_no_errors(self):
        """Nenhum descriptor deve ter erros após IMP-33."""
        report = validate_descriptors(_DESCRIPTORS_DIR)
        assert report.total_errors == 0

    def test_validate_valid_is_true(self):
        """report.valid deve ser True após IMP-33."""
        report = validate_descriptors(_DESCRIPTORS_DIR)
        assert report.valid is True

    def test_all_profiles_have_ok_or_warning_status(self):
        """Nenhum perfil deve ter status 'error'."""
        report = validate_descriptors(_DESCRIPTORS_DIR)
        errors = [r for r in report.results if r.status == "error"]
        assert errors == [], f"Perfis com erro: {[r.name for r in errors]}"
