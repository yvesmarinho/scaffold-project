"""
tests/test_smoke_imp36.py — IMP-36: Staleness check nos profile-descriptors.

Cobertura:
  _check_staleness():
    - Perfil com data atual não gera warning
    - Perfil com data de exatamente threshold_days atrás NÃO gera warning (limite exclusivo)
    - Perfil com data de threshold_days+1 atrás gera warning
    - Perfil com data muito antiga gera warning com delta correto na mensagem
    - Perfil sem last_tested não recebe warning de staleness (apenas ausência)
    - Perfil com formato de data inválido não gera warning de staleness
    - Limiar customizado é respeitado

  ValidationReport.stale_profiles:
    - Retorna lista de nomes com staleness warning
    - Retorna lista vazia quando não há stale
    - stale_days_threshold preservado no report

  validate_descriptors() integração:
    - Aceita argumento stale_days_threshold
    - Com threshold=1 e date atual, todos os perfis (testados em 2026-03-07) ficam stale
    - Com threshold=9999, nenhum perfil fica stale
    - stale_profiles está vazio com threshold=9999

  CLI --validate --json:
    - Campo 'warnings' conta inclui staleness warnings com threshold baixo
    - campo 'stale_days_threshold' não quebra a chamada existente
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.validate import (  # noqa: E402
    ProfileResult,
    ValidationIssue,
    ValidationReport,
    _check_staleness,
    validate_descriptors,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_DESCRIPTORS_DIR = _PROJECT_ROOT / "profile-descriptors"
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
_PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(name: str, filename: str | None = None) -> ProfileResult:
    return ProfileResult(name=name, file=filename or f"{name}.yaml")


def _all_data_with_date(result: ProfileResult, d: date) -> dict[str, dict]:
    return {result.file: {"last_tested": d.isoformat()}}


def _all_data_no_date(result: ProfileResult) -> dict[str, dict]:
    return {result.file: {}}


def _all_data_invalid_date(result: ProfileResult) -> dict[str, dict]:
    return {result.file: {"last_tested": "not-a-date"}}


# ---------------------------------------------------------------------------
# _check_staleness() — comportamento unitário
# ---------------------------------------------------------------------------


class TestCheckStaleness:
    TODAY = date(2026, 3, 14)

    def _run(self, tested: date, threshold: int = 90) -> list[ValidationIssue]:
        r = _make_result("perfil-teste")
        all_data = _all_data_with_date(r, tested)
        _check_staleness([r], all_data, threshold_days=threshold, reference_date=self.TODAY)
        return r.warnings

    def test_data_atual_nao_gera_warning(self):
        warnings = self._run(self.TODAY)
        assert not warnings

    def test_exatamente_no_limite_nao_gera_warning(self):
        # dia = threshold_days → não é MAIOR QUE, então não avisa
        tested = self.TODAY - timedelta(days=90)
        warnings = self._run(tested, threshold=90)
        assert not warnings

    def test_um_dia_alem_do_limite_gera_warning(self):
        tested = self.TODAY - timedelta(days=91)
        warnings = self._run(tested, threshold=90)
        assert len(warnings) == 1

    def test_data_muito_antiga_gera_warning_com_delta(self):
        tested = date(2020, 1, 1)
        delta = (self.TODAY - tested).days
        warnings = self._run(tested, threshold=90)
        assert len(warnings) == 1
        assert str(delta) in warnings[0].message

    def test_sem_last_tested_nao_gera_staleness(self):
        r = _make_result("perfil-sem-data")
        all_data = _all_data_no_date(r)
        _check_staleness([r], all_data, threshold_days=90, reference_date=self.TODAY)
        stale_warnings = [w for w in r.warnings if "desatualizado" in w.message]
        assert not stale_warnings

    def test_formato_invalido_nao_gera_staleness(self):
        r = _make_result("perfil-data-ruim")
        all_data = _all_data_invalid_date(r)
        _check_staleness([r], all_data, threshold_days=90, reference_date=self.TODAY)
        stale_warnings = [w for w in r.warnings if "desatualizado" in w.message]
        assert not stale_warnings

    def test_limiar_customizado_respeitado(self):
        # 10 dias atrás com threshold=5 deve gerar warning
        tested = self.TODAY - timedelta(days=10)
        warnings = self._run(tested, threshold=5)
        assert len(warnings) == 1

    def test_limiar_customizado_ok_abaixo(self):
        # 10 dias atrás com threshold=30 não deve gerar warning
        tested = self.TODAY - timedelta(days=10)
        warnings = self._run(tested, threshold=30)
        assert not warnings

    def test_warning_tem_field_last_tested(self):
        tested = self.TODAY - timedelta(days=200)
        warnings = self._run(tested)
        assert warnings[0].field == "last_tested"

    def test_warning_tem_severity_warning(self):
        tested = self.TODAY - timedelta(days=200)
        warnings = self._run(tested)
        assert warnings[0].severity == "warning"

    def test_aceita_last_tested_uppercase(self):
        """Campo LAST_TESTED_DATE (uppercase) também deve ser verificado."""
        r = _make_result("perfil-uppercase")
        tested = self.TODAY - timedelta(days=200)
        all_data = {r.file: {"LAST_TESTED_DATE": tested.isoformat()}}
        _check_staleness([r], all_data, threshold_days=90, reference_date=self.TODAY)
        stale_warnings = [w for w in r.warnings if "desatualizado" in w.message]
        assert len(stale_warnings) == 1


# ---------------------------------------------------------------------------
# ValidationReport.stale_profiles
# ---------------------------------------------------------------------------


class TestValidationReportStaleProfiles:
    TODAY = date(2026, 3, 14)

    def _build_report(self, *profiles: tuple[str, date | None], threshold: int = 90) -> ValidationReport:
        report = ValidationReport(descriptor_dir=Path("."), stale_days_threshold=threshold)
        all_data: dict[str, dict] = {}
        for name, d in profiles:
            r = _make_result(name)
            report.results.append(r)
            all_data[r.file] = {"last_tested": d.isoformat()} if d else {}
        parsed = [r for r in report.results if r.file in all_data]
        _check_staleness(parsed, all_data, threshold_days=threshold, reference_date=self.TODAY)
        return report

    def test_retorna_lista_nomes_stale(self):
        old_date = self.TODAY - timedelta(days=200)
        report = self._build_report(("perfil-velho", old_date))
        assert "perfil-velho" in report.stale_profiles

    def test_retorna_vazio_sem_stale(self):
        recent = self.TODAY - timedelta(days=5)
        report = self._build_report(("perfil-recente", recent))
        assert report.stale_profiles == []

    def test_threshold_preservado(self):
        report = ValidationReport(descriptor_dir=Path("."), stale_days_threshold=30)
        assert report.stale_days_threshold == 30

    def test_apenas_stale_retornados(self):
        old_date = self.TODAY - timedelta(days=200)
        recent = self.TODAY - timedelta(days=5)
        report = self._build_report(
            ("perfil-velho", old_date),
            ("perfil-recente", recent),
        )
        assert report.stale_profiles == ["perfil-velho"]
        assert "perfil-recente" not in report.stale_profiles


# ---------------------------------------------------------------------------
# validate_descriptors() — integração real com profile-descriptors/
# ---------------------------------------------------------------------------


class TestValidateDescriptorsIntegration:
    def test_aceita_stale_days_threshold(self):
        """validate_descriptors aceita argumento stale_days_threshold."""
        report = validate_descriptors(_DESCRIPTORS_DIR, stale_days_threshold=9999)
        assert report.stale_days_threshold == 9999

    def test_threshold_9999_nenhum_stale(self):
        """Com threshold=9999, nenhum perfil é marcado como stale."""
        report = validate_descriptors(_DESCRIPTORS_DIR, stale_days_threshold=9999)
        assert report.stale_profiles == []

    @staticmethod
    def _aged_descriptors(tmp_path: Path, days_ago: int = 30) -> Path:
        """Cópia dos descriptors reais com last_tested fixado em `days_ago` dias atrás.

        Evita depender da data real de revalidação dos perfis.
        """
        old = (date.today() - timedelta(days=days_ago)).isoformat()
        dest = tmp_path / "descriptors"
        dest.mkdir()
        for src in _DESCRIPTORS_DIR.glob("*.yaml"):
            lines = [
                f'{line.split(":", 1)[0]}: "{old}"'
                if line.startswith(("last_tested:", "LAST_TESTED_DATE:"))
                else line
                for line in src.read_text(encoding="utf-8").splitlines()
            ]
            (dest / src.name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        return dest

    def test_threshold_1_perfis_antigos_stale(self, tmp_path: Path):
        """Com threshold=1, perfis testados há 30 dias ficam stale."""
        aged = self._aged_descriptors(tmp_path)
        report = validate_descriptors(aged, stale_days_threshold=1)
        assert len(report.stale_profiles) >= 10

    def test_stale_warnings_contados_em_total_warnings(self, tmp_path: Path):
        """Com threshold=1, total_warnings deve incluir os staleness warnings."""
        aged = self._aged_descriptors(tmp_path)
        report_stale = validate_descriptors(aged, stale_days_threshold=1)
        report_ok = validate_descriptors(aged, stale_days_threshold=9999)
        assert report_stale.total_warnings > report_ok.total_warnings

    def test_sem_novos_erros_com_threshold_normal(self):
        """Staleness check não introduz errors, apenas warnings."""
        report = validate_descriptors(_DESCRIPTORS_DIR, stale_days_threshold=90)
        assert report.total_errors == 0


# ---------------------------------------------------------------------------
# CLI --validate --json com staleness
# ---------------------------------------------------------------------------


class TestCLIValidateStaleness:
    def _run(self, *extra_args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [_PYTHON, str(_SCRIPTS_DIR / "scaffold.py"), "--validate", "--json", *extra_args],
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

    def test_validate_json_exit_zero(self):
        """--validate --json deve retornar exit 0 (0 errors)."""
        proc = self._run()
        assert proc.returncode == 0, f"stderr: {proc.stderr}"

    def test_validate_json_tem_profiles_checked(self):
        proc = self._run()
        data = json.loads(proc.stdout)
        assert data["profiles_checked"] == 22

    def test_validate_json_zero_errors(self):
        """Nenhum erro novo introduzido por IMP-36."""
        proc = self._run()
        data = json.loads(proc.stdout)
        assert data["errors"] == 0
