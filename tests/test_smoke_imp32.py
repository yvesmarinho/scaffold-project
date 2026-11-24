"""
tests/test_smoke_imp32.py — IMP-32: Smoke tests para scaffold.py --validate.

Cobertura:
  validate.py — ValidationIssue / ProfileResult / ValidationReport:
    - ValidationIssue tem campos field, severity, message
    - ProfileResult.status == "ok" quando sem issues
    - ProfileResult.status == "warning" quando só warnings
    - ProfileResult.status == "error" quando tem erros
    - ProfileResult.errors filtra só erros
    - ProfileResult.warnings filtra só warnings
    - ValidationReport.valid é False quando há erros
    - ValidationReport.valid é True quando só avisos
    - ValidationReport.profiles_checked conta resultados
    - ValidationReport.total_errors soma erros
    - ValidationReport.total_warnings soma warnings

  validate_descriptors (validação real):
    - retorna ValidationReport para diretório existente
    - retorna report vazio para diretório inexistente
    - todos os 13 descritores reais são encontrados
    - nenhum descriptor real tem erros (valid == True)
    - fallback de parse em YAML inválido → issue "error" no resultado
    - descriptor sem 'name' gera issue de erro
    - descriptor sem 'description' gera issue de erro
    - descriptor com versão inválida gera issue de erro
    - descriptor sem 'last_tested' gera issue de warning
    - descriptor sem 'layer' gera issue de warning
    - combines_with com perfil inexistente gera warning (não erro)
    - nomes duplicados geram erro no segundo descriptor

  Regra 6 — security.enforces estruturado (IMP-41):
    - enforces ausente não gera issue
    - enforces vazio não gera issue
    - enforces com string (legado) gera error
    - enforces com objeto parcial (campos faltando) gera error
    - enforces com severity inválida gera error
    - enforces com objeto completo válido não gera issue
    - todas as severidades aceitas: critical, high, medium, low

  CLI --validate:
    - --help menciona --validate
    - --validate retorna exit code 0 (todos os descritores reais são válidos)
    - --validate --json retorna JSON válido
    - --validate --json tem chave 'valid' == True
    - --validate --json tem chave 'profiles_checked' == 13
    - --validate --json tem chave 'errors' == 0
    - --validate --json tem chave 'results' com 13 itens
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.validate import (  # noqa: E402
    ProfileResult,
    ValidationIssue,
    ValidationReport,
    _cross_validate,
    _validate_descriptor,
    validate_descriptors,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_DESCRIPTORS_DIR = _PROJECT_ROOT / "profile-descriptors"
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
_PYTHON = sys.executable


# ===========================================================================
# Dataclass helpers
# ===========================================================================


class TestValidationIssue:
    def test_has_field(self):
        iss = ValidationIssue(field="name", severity="error", message="ausente")
        assert iss.field == "name"

    def test_has_severity(self):
        iss = ValidationIssue(field="name", severity="error", message="ausente")
        assert iss.severity == "error"

    def test_has_message(self):
        iss = ValidationIssue(field="name", severity="error", message="ausente")
        assert iss.message == "ausente"


class TestProfileResult:
    def _make(self, issues: list[ValidationIssue]) -> ProfileResult:
        r = ProfileResult(name="test-profile", file="test.yaml")
        r.issues = issues
        return r

    def test_status_ok_when_no_issues(self):
        assert self._make([]).status == "ok"

    def test_status_warning_when_only_warnings(self):
        r = self._make([ValidationIssue("layer", "warning", "ausente")])
        assert r.status == "warning"

    def test_status_error_when_has_errors(self):
        r = self._make(
            [
                ValidationIssue("name", "error", "vazio"),
                ValidationIssue("layer", "warning", "ausente"),
            ]
        )
        assert r.status == "error"

    def test_errors_filters_errors_only(self):
        r = self._make(
            [
                ValidationIssue("name", "error", "vazio"),
                ValidationIssue("layer", "warning", "ausente"),
            ]
        )
        assert len(r.errors) == 1
        assert r.errors[0].severity == "error"

    def test_warnings_filters_warnings_only(self):
        r = self._make(
            [
                ValidationIssue("name", "error", "vazio"),
                ValidationIssue("layer", "warning", "ausente"),
            ]
        )
        assert len(r.warnings) == 1
        assert r.warnings[0].severity == "warning"


class TestValidationReport:
    def _make_report(self, results: list[ProfileResult]) -> ValidationReport:
        report = ValidationReport(descriptor_dir=Path("/tmp"))
        report.results = results
        return report

    def test_valid_false_when_errors(self):
        r = ProfileResult(name="p", file="p.yaml")
        r.issues = [ValidationIssue("name", "error", "vazio")]
        assert not self._make_report([r]).valid

    def test_valid_true_when_only_warnings(self):
        r = ProfileResult(name="p", file="p.yaml")
        r.issues = [ValidationIssue("layer", "warning", "ausente")]
        assert self._make_report([r]).valid

    def test_profiles_checked_counts_results(self):
        r1 = ProfileResult(name="a", file="a.yaml")
        r2 = ProfileResult(name="b", file="b.yaml")
        assert self._make_report([r1, r2]).profiles_checked == 2

    def test_total_errors_sums_across_results(self):
        r1 = ProfileResult(name="a", file="a.yaml")
        r1.issues = [ValidationIssue("name", "error", "x")]
        r2 = ProfileResult(name="b", file="b.yaml")
        r2.issues = [ValidationIssue("desc", "error", "y")]
        assert self._make_report([r1, r2]).total_errors == 2

    def test_total_warnings_sums_across_results(self):
        r1 = ProfileResult(name="a", file="a.yaml")
        r1.issues = [ValidationIssue("layer", "warning", "x")]
        r2 = ProfileResult(name="b", file="b.yaml")
        r2.issues = [ValidationIssue("layer", "warning", "y")]
        assert self._make_report([r1, r2]).total_warnings == 2


# ===========================================================================
# _validate_descriptor — validações individuais
# ===========================================================================


class TestValidateDescriptor:
    def _min_valid(self) -> dict:
        """Descriptor mínimo válido com todos os campos obrigatórios."""
        return {
            "name": "my-profile",
            "description": "Test description",
            "version": "1.0.0",
            "last_tested": "2026-03-08",
            "layer": "2",
        }

    def test_empty_name_gives_error(self):
        data = self._min_valid()
        data["name"] = ""
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "name" in fields

    def test_missing_name_gives_error(self):
        data = self._min_valid()
        del data["name"]
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "name" in fields

    def test_missing_description_gives_error(self):
        data = self._min_valid()
        del data["description"]
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "description" in fields

    def test_invalid_version_gives_error(self):
        data = self._min_valid()
        data["version"] = "1.0"  # falta patch
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "version" in fields

    def test_old_schema_VERSION_field_accepted(self):
        data = self._min_valid()
        del data["version"]
        data["VERSION"] = "1.0.0"
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "version" not in fields

    def test_missing_last_tested_gives_warning(self):
        data = self._min_valid()
        del data["last_tested"]
        r = _validate_descriptor(data, Path("test.yaml"))
        sev = [i.severity for i in r.issues if i.field == "last_tested"]
        assert sev == ["warning"]

    def test_missing_layer_gives_warning(self):
        data = self._min_valid()
        del data["layer"]
        r = _validate_descriptor(data, Path("test.yaml"))
        sev = [i.severity for i in r.issues if i.field == "layer"]
        assert sev == ["warning"]

    def test_invalid_layer_gives_error(self):
        data = self._min_valid()
        data["layer"] = "layer5-invalid"
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "layer" in fields

    def test_valid_descriptor_has_no_issues(self):
        r = _validate_descriptor(self._min_valid(), Path("test.yaml"))
        assert r.issues == []

    # -- Regra 6: security.enforces estruturado (IMP-41) --

    def _min_valid_with_enforces(self, enforces_val) -> dict:
        data = self._min_valid()
        data["security"] = {"enforces": enforces_val}
        return data

    def test_enforces_absent_no_issues(self):
        """security.enforces ausente não gera nenhum issue."""
        data = self._min_valid()
        r = _validate_descriptor(data, Path("test.yaml"))
        assert r.issues == []

    def test_enforces_empty_list_no_issues(self):
        """security.enforces vazio ([]) não gera issue."""
        r = _validate_descriptor(self._min_valid_with_enforces([]), Path("test.yaml"))
        assert r.issues == []

    def test_enforces_string_item_gives_error(self):
        """enforces com string (formato legado) gera error."""
        data = self._min_valid_with_enforces(["controle legado como string"])
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "security.enforces" in fields

    def test_enforces_missing_required_fields_gives_error(self):
        """enforces com objeto parcial (sem 'automated') gera error."""
        data = self._min_valid_with_enforces(
            [
                {
                    "control": "CWE-312",
                    "description": "Desc",
                    "tool": "manual",
                    "severity": "high",
                },
            ]
        )
        r = _validate_descriptor(data, Path("test.yaml"))
        fields = [i.field for i in r.errors]
        assert "security.enforces" in fields

    def test_enforces_invalid_severity_gives_error(self):
        """enforces com severity inválida gera error."""
        data = self._min_valid_with_enforces(
            [
                {
                    "control": "CWE-312",
                    "description": "Desc",
                    "tool": "manual",
                    "severity": "ultra-critical",
                    "automated": False,
                },
            ]
        )
        r = _validate_descriptor(data, Path("test.yaml"))
        msgs = [i.message for i in r.errors if i.field == "security.enforces"]
        assert any("severity" in m for m in msgs)

    def test_enforces_valid_item_no_issues(self):
        """enforces com objeto completo e válido não gera issue."""
        data = self._min_valid_with_enforces(
            [
                {
                    "control": "OWASP-A06",
                    "description": "bandit scan",
                    "tool": "bandit",
                    "severity": "high",
                    "automated": True,
                },
            ]
        )
        r = _validate_descriptor(data, Path("test.yaml"))
        sec_issues = [i for i in r.issues if i.field == "security.enforces"]
        assert sec_issues == []

    def test_enforces_all_severities_accepted(self):
        """Todas as severidades válidas são aceitas."""
        for sev in ("critical", "high", "medium", "low"):
            data = self._min_valid_with_enforces(
                [
                    {
                        "control": "CC6.1",
                        "description": "desc",
                        "tool": "trivy",
                        "severity": sev,
                        "automated": True,
                    },
                ]
            )
            r = _validate_descriptor(data, Path(f"test-{sev}.yaml"))
            sec_errors = [i for i in r.errors if i.field == "security.enforces"]
            assert sec_errors == [], f"severity '{sev}' gerou erro inesperado"


# ===========================================================================
# _cross_validate
# ===========================================================================


class TestCrossValidate:
    def _two_results(self) -> tuple[list[ProfileResult], dict[str, dict]]:
        r1 = ProfileResult(name="profile-a", file="profile-a.yaml")
        r2 = ProfileResult(name="profile-b", file="profile-b.yaml")
        all_data = {
            "profile-a.yaml": {"combines_with": ["profile-b"]},
            "profile-b.yaml": {"combines_with": ["profile-a"]},
        }
        return [r1, r2], all_data

    def test_known_combines_with_no_warning(self):
        results, all_data = self._two_results()
        _cross_validate(results, all_data)
        assert all(not r.issues for r in results)

    def test_unknown_combines_with_gives_warning(self):
        r1 = ProfileResult(name="profile-a", file="profile-a.yaml")
        all_data = {"profile-a.yaml": {"combines_with": ["ghost-profile"]}}
        _cross_validate([r1], all_data)
        assert any(
            i.field == "combines_with" and i.severity == "warning" for i in r1.issues
        )

    def test_duplicate_name_gives_error(self):
        r1 = ProfileResult(name="dup", file="dup-1.yaml")
        r2 = ProfileResult(name="dup", file="dup-2.yaml")
        all_data = {"dup-1.yaml": {}, "dup-2.yaml": {}}
        _cross_validate([r1, r2], all_data)
        assert any(i.field == "name" and i.severity == "error" for i in r2.issues)


# ===========================================================================
# validate_descriptors — integração com disco real
# ===========================================================================


class TestValidateDescriptorsIntegration:
    def test_returns_validation_report(self):
        report = validate_descriptors(_DESCRIPTORS_DIR)
        assert isinstance(report, ValidationReport)

    def test_empty_dir_returns_empty_report(self, tmp_path):
        report = validate_descriptors(tmp_path)
        assert report.profiles_checked == 0

    def test_nonexistent_dir_returns_empty_report(self, tmp_path):
        report = validate_descriptors(tmp_path / "no-such-dir")
        assert report.profiles_checked == 0

    def test_finds_all_13_real_descriptors(self):
        report = validate_descriptors(_DESCRIPTORS_DIR)
        assert report.profiles_checked == 22

    def test_real_descriptors_have_no_errors(self):
        report = validate_descriptors(_DESCRIPTORS_DIR)
        assert report.total_errors == 0

    def test_valid_is_true_for_real_descriptors(self):
        report = validate_descriptors(_DESCRIPTORS_DIR)
        assert report.valid is True

    def test_parse_error_captured_as_issue(self, tmp_path):
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("name: ok\nbroken: [\nno_close", encoding="utf-8")
        report = validate_descriptors(tmp_path)
        assert report.total_errors >= 1
        assert any(i.field == "yaml" for r in report.results for i in r.issues)


# ===========================================================================
# CLI integration
# ===========================================================================


class TestValidateCLI:
    def _run(self, *extra_args: str, **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(
            [_PYTHON, str(_SCRIPTS_DIR / "scaffold.py"), "--validate", *extra_args],
            capture_output=True,
            text=True,
            cwd=str(_PROJECT_ROOT),
            **kwargs,
        )

    def test_help_mentions_validate(self):
        proc = subprocess.run(
            [_PYTHON, str(_SCRIPTS_DIR / "scaffold.py"), "--help"],
            capture_output=True,
            text=True,
        )
        assert (
            "--validate" in proc.stdout
        ), f"--validate ausente no --help; stdout: {proc.stdout}"

    def test_validate_exits_zero(self):
        proc = self._run()
        assert proc.returncode == 0, f"rc={proc.returncode}; stderr={proc.stderr}"

    def test_validate_json_exits_zero(self):
        proc = self._run("--json")
        assert proc.returncode == 0, f"rc={proc.returncode}; stderr={proc.stderr}"

    def test_validate_json_is_valid_json(self):
        proc = self._run("--json")
        data = json.loads(proc.stdout)
        assert isinstance(data, dict)

    def test_validate_json_has_valid_true(self):
        proc = self._run("--json")
        data = json.loads(proc.stdout)
        assert data["valid"] is True

    def test_validate_json_profiles_checked_is_13(self):
        proc = self._run("--json")
        data = json.loads(proc.stdout)
        assert data["profiles_checked"] == 22

    def test_validate_json_errors_is_zero(self):
        proc = self._run("--json")
        data = json.loads(proc.stdout)
        assert data["errors"] == 0

    def test_validate_json_has_results_list(self):
        proc = self._run("--json")
        data = json.loads(proc.stdout)
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 22

    def test_validate_json_each_result_has_name(self):
        proc = self._run("--json")
        data = json.loads(proc.stdout)
        for r in data["results"]:
            assert "name" in r and r["name"]

    def test_validate_json_each_result_has_status(self):
        proc = self._run("--json")
        data = json.loads(proc.stdout)
        valid_statuses = {"ok", "warning", "error"}
        for r in data["results"]:
            assert r["status"] in valid_statuses
