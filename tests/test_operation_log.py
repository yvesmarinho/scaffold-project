# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_operation_log.py
TITULO: Testes do log de operação (lib/ui.save_operation_log)
DATA: 09/11/2026 16:10
MODIFICADO: 09/11/2026 16:10
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bugs cobertos (docs/planning/lembrete.md):
- nome/cabeçalho do log em UTC → deve usar America/Sao_Paulo
- log sem a seção de drift exibida no stdout
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib import ui  # noqa: E402
from lib.config import CreatedItem  # noqa: E402

# 18:52:50 UTC == 15:52:50 em São Paulo (UTC-3, sem horário de verão)
_FIXED_UTC = datetime(2026, 11, 9, 18, 52, 50, tzinfo=timezone.utc)


@pytest.fixture
def isolated_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Evita gravar no logs/ real da ferramenta durante os testes."""
    tool_logs = tmp_path / "tool-logs"
    monkeypatch.setattr(ui, "_SCAFFOLD_LOGS_DIR", tool_logs)
    return tool_logs


@pytest.fixture
def project(tmp_path: Path) -> Path:
    path = tmp_path / "demo"
    path.mkdir()
    return path


def _items(project: Path) -> list[CreatedItem]:
    return [
        CreatedItem(path=project / "docs", kind="dir", status="created"),
        CreatedItem(path=project / ".github" / "agents" / "a.agent.md", kind="file", status="drift",
                    message="difere do upstream"),
        CreatedItem(path=project / "README.md", kind="file", status="error", message="sem permissão"),
    ]


# --- Timezone -----------------------------------------------------------------


def test_timestamp_usa_sao_paulo():
    assert ui.log_timestamp(_FIXED_UTC) == "2026-11-09_15-52-50"


def test_timestamp_rejeita_datetime_ingenuo():
    with pytest.raises(ValueError):
        ui.log_timestamp(datetime(2026, 11, 9, 18, 52, 50))


def test_nome_do_arquivo_em_horario_local(project: Path, isolated_logs: Path):
    log = ui.save_operation_log(_items(project), project, now=_FIXED_UTC)
    assert log is not None
    assert log.name == "scaffold_2026-11-09_15-52-50.log"


def test_cabecalho_com_iso_e_offset(project: Path, isolated_logs: Path):
    log = ui.save_operation_log(_items(project), project, now=_FIXED_UTC)
    text = log.read_text(encoding="utf-8")
    assert "# Timestamp: 2026-11-09T15:52:50-03:00" in text


# --- Detalhes / drift -------------------------------------------------------------


def test_log_tem_secao_de_drift_com_path_relativo(project: Path, isolated_logs: Path):
    text = ui.save_operation_log(_items(project), project, now=_FIXED_UTC).read_text(encoding="utf-8")
    assert "## Drift (1)" in text
    assert "- .github/agents/a.agent.md | difere do upstream" in text


def test_log_tem_secao_de_erros(project: Path, isolated_logs: Path):
    text = ui.save_operation_log(_items(project), project, now=_FIXED_UTC).read_text(encoding="utf-8")
    assert "## Errors (1)" in text
    assert "- README.md | sem permissão" in text


def test_sem_drift_nao_cria_secao(project: Path, isolated_logs: Path):
    items = [CreatedItem(path=project / "docs", kind="dir", status="created")]
    text = ui.save_operation_log(items, project, now=_FIXED_UTC).read_text(encoding="utf-8")
    assert "## Drift" not in text


def test_lista_vazia_ainda_gera_log(project: Path, isolated_logs: Path):
    log = ui.save_operation_log([], project, now=_FIXED_UTC)
    assert log is not None and "# Total items: 0" in log.read_text(encoding="utf-8")


def test_diretorio_sem_permissao_nao_derruba(project: Path, isolated_logs: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_args, **_kwargs):
        raise PermissionError("negado")

    monkeypatch.setattr(Path, "mkdir", boom)
    assert ui.save_operation_log(_items(project), project, now=_FIXED_UTC) is None
