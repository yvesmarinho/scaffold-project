# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_scaffold_logs_dir.py
TITULO: Testes do diretório de logs da ferramenta (lib/ui._scaffold_logs_dir)
DATA: 17/11/2026 16:30
MODIFICADO: 17/11/2026 16:21
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bug coberto: a suíte gravava logs de operação no ``logs/`` real do
scaffold-project (centenas de arquivos, inclusive via subprocesso), o que
dispara o ``security-scan`` do session-manager. O diretório passa a ser
configurável por ``SCAFFOLD_LOGS_DIR`` e o conftest o isola em ``tmp_path``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import ui  # noqa: E402
from lib.config import CreatedItem  # noqa: E402

_ENV = "SCAFFOLD_LOGS_DIR"


def test_variavel_de_ambiente_define_o_diretorio(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(_ENV, str(tmp_path / "custom"))
    assert ui._scaffold_logs_dir() == tmp_path / "custom"


def test_sem_variavel_usa_logs_da_ferramenta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_ENV, raising=False)
    assert ui._scaffold_logs_dir() == ui._SCAFFOLD_LOGS_DIR


@pytest.mark.parametrize("valor", ["", "   "])
def test_variavel_vazia_usa_logs_da_ferramenta(
    valor: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(_ENV, valor)
    assert ui._scaffold_logs_dir() == ui._SCAFFOLD_LOGS_DIR


def test_save_operation_log_grava_no_diretorio_da_variavel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    default_dir = tmp_path / "default-nao-usar"
    env_dir = tmp_path / "env-logs"
    monkeypatch.setattr(ui, "_SCAFFOLD_LOGS_DIR", default_dir)
    monkeypatch.setenv(_ENV, str(env_dir))
    project = tmp_path / "demo"
    project.mkdir()

    ui.save_operation_log(
        [CreatedItem(path=project / "README.md", kind="file", status="created")],
        project,
        now=datetime(2026, 11, 17, 19, 0, 0, tzinfo=UTC),
    )

    assert len(list(env_dir.glob("scaffold_*.log"))) == 1
    assert not default_dir.exists()


def test_conftest_isola_logs_da_suite_em_tmp(tmp_path: Path) -> None:
    valor = os.environ.get(_ENV, "")
    assert valor, f"{_ENV} não definido pela fixture autouse do conftest"
    assert Path(valor).is_relative_to(tmp_path)


def test_subprocesso_herda_o_isolamento(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-c", "from lib import ui; print(ui._scaffold_logs_dir())"],
        cwd=_SCRIPTS_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    assert Path(result.stdout.strip()).is_relative_to(tmp_path)


# ---------------------------------------------------------------------------
# scaffold_logger.ScaffoldLogger — histórico logs/scaffolds.yaml
# ---------------------------------------------------------------------------


def test_scaffold_logger_default_respeita_variavel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scaffold_logger

    monkeypatch.setenv(_ENV, str(tmp_path / "env-logs"))
    logger = scaffold_logger.ScaffoldLogger()

    assert logger.log_file == tmp_path / "env-logs" / "scaffolds.yaml"
    assert logger.log_file.exists()


def test_scaffold_logger_sem_variavel_mantem_caminho_padrao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scaffold_logger

    monkeypatch.delenv(_ENV, raising=False)
    monkeypatch.chdir(tmp_path)  # caminho padrão é relativo ao cwd
    logger = scaffold_logger.ScaffoldLogger()

    assert logger.log_file == scaffold_logger.DEFAULT_LOG_FILE


def test_scaffold_logger_caminho_explicito_tem_prioridade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scaffold_logger

    monkeypatch.setenv(_ENV, str(tmp_path / "env-logs"))
    explicit = tmp_path / "explicito.yaml"

    assert scaffold_logger.ScaffoldLogger(explicit).log_file == explicit


def test_objetivo_init_grava_historico_no_diretorio_da_variavel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lib.flows.objetivo_init import _log_objetivo_init
    from lib.objetivo_wizard import WizardAnswers

    monkeypatch.setenv(_ENV, str(tmp_path / "env-logs"))
    monkeypatch.chdir(tmp_path)  # se usar o caminho relativo, cai em tmp_path/logs

    _log_objetivo_init(tmp_path / "objetivo.yaml", WizardAnswers(project_name="x"), True)

    assert (tmp_path / "env-logs" / "scaffolds.yaml").exists()
    assert not (tmp_path / "logs").exists()
