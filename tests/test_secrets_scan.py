# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_secrets_scan.py
TITULO: Testes do scanner local de segredos (gitleaks) — substitui o GitGuardian
DATA: 09/11/2026 15:45
MODIFICADO: 09/11/2026 15:41
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV
"""

import json
import subprocess
from pathlib import Path

import pytest

from scripts.secrets_scan import (
    GitleaksExecutionError,
    GitleaksNotFoundError,
    GitleaksTimeoutError,
    InvalidScanModeError,
    ScanResult,
    build_command,
    main,
    run_scan,
)


def _which_ok(_name: str) -> str:
    return "/usr/bin/gitleaks"


def _which_missing(_name: str) -> None:
    return None


def _fake_runner(returncode: int, findings: list[dict] | None = None, stderr: str = ""):
    """Simula o gitleaks: grava o relatório JSON no caminho passado em -r."""

    def runner(cmd: list[str], **_kwargs) -> subprocess.CompletedProcess:
        if findings is not None:
            report = Path(cmd[cmd.index("-r") + 1])
            report.write_text(json.dumps(findings), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, returncode, "", stderr)

    return runner


FINDING = {
    "RuleID": "github-pat",
    "File": "src/app.py",
    "StartLine": 12,
    "Commit": "abc1234def",
    "Secret": "REDACTED",
    "Match": "token = REDACTED",
}


# --- Contrato de entrada -----------------------------------------------------


def test_modo_invalido_levanta_erro_semantico(tmp_path: Path):
    with pytest.raises(InvalidScanModeError):
        run_scan(tmp_path, "tudo", which=_which_ok, runner=_fake_runner(0, []))


def test_repo_inexistente_levanta_erro(tmp_path: Path):
    with pytest.raises(NotADirectoryError):
        run_scan(tmp_path / "nao-existe", "history", which=_which_ok, runner=_fake_runner(0, []))


# --- Dependência externa indisponível ----------------------------------------


def test_gitleaks_ausente_levanta_not_found(tmp_path: Path):
    with pytest.raises(GitleaksNotFoundError):
        run_scan(tmp_path, "history", which=_which_missing, runner=_fake_runner(0, []))


def test_timeout_do_gitleaks_levanta_timeout(tmp_path: Path):
    def runner(cmd, **_kwargs):
        raise subprocess.TimeoutExpired(cmd, 1)

    with pytest.raises(GitleaksTimeoutError):
        run_scan(tmp_path, "history", which=_which_ok, runner=runner)


def test_erro_de_execucao_levanta_execution_error(tmp_path: Path):
    with pytest.raises(GitleaksExecutionError):
        run_scan(tmp_path, "history", which=_which_ok, runner=_fake_runner(2, None, "config inválida"))


def test_relatorio_corrompido_levanta_execution_error(tmp_path: Path):
    def runner(cmd, **_kwargs):
        Path(cmd[cmd.index("-r") + 1]).write_text("{não é json", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 1, "", "")

    with pytest.raises(GitleaksExecutionError):
        run_scan(tmp_path, "history", which=_which_ok, runner=runner)


# --- Comportamento -------------------------------------------------------------


def test_comando_sempre_usa_redact_e_config(tmp_path: Path):
    for mode in ("history", "tree", "staged"):
        cmd = build_command(mode, tmp_path, tmp_path / "r.json")
        assert "--redact" in cmd
        assert "-c" in cmd


def test_achados_sao_retornados_sem_o_segredo(tmp_path: Path):
    result = run_scan(tmp_path, "history", which=_which_ok, runner=_fake_runner(1, [FINDING]))
    assert isinstance(result, ScanResult)
    assert result.leaks == 1
    assert result.findings[0].rule == "github-pat"
    assert result.findings[0].location == "src/app.py:12"
    assert not hasattr(result.findings[0], "secret")


def test_sem_achados_resultado_limpo(tmp_path: Path):
    result = run_scan(tmp_path, "tree", which=_which_ok, runner=_fake_runner(0, []))
    assert result.leaks == 0
    assert result.clean


# --- CLI: códigos de saída ------------------------------------------------------


def test_cli_exit_1_com_vazamento(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("scripts.secrets_scan.shutil.which", _which_ok)
    monkeypatch.setattr("scripts.secrets_scan.subprocess.run", _fake_runner(1, [FINDING]))
    assert main(["--mode", "history", "--repo", str(tmp_path)]) == 1


def test_cli_exit_2_sem_gitleaks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("scripts.secrets_scan.shutil.which", _which_missing)
    assert main(["--mode", "history", "--repo", str(tmp_path)]) == 2


def test_cli_exit_0_limpo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("scripts.secrets_scan.shutil.which", _which_ok)
    monkeypatch.setattr("scripts.secrets_scan.subprocess.run", _fake_runner(0, []))
    assert main(["--mode", "tree", "--repo", str(tmp_path)]) == 0
