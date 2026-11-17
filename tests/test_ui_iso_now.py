# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_ui_iso_now.py
TITULO: Testes do timestamp created_at (lib/ui._iso_now)
DATA: 17/11/2026 16:05
MODIFICADO: 17/11/2026 16:11
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bug coberto: ``ui._iso_now()`` gerava ``created_at`` em UTC (sufixo ``Z``);
deve usar America/Sao_Paulo em ISO 8601 com offset (ex.: ``-03:00``).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib import ui  # noqa: E402

# 18:52:50 UTC == 15:52:50 em São Paulo (UTC-3, sem horário de verão)
_UTC_INSTANT = datetime(2026, 11, 9, 18, 52, 50, tzinfo=UTC)


def test_converte_instante_utc_para_sao_paulo() -> None:
    assert ui._iso_now(_UTC_INSTANT) == "2026-11-09T15:52:50-03:00"


def test_virada_de_dia_em_utc_permanece_no_dia_anterior_local() -> None:
    # 01:30 UTC do dia 10 ainda é 22:30 do dia 09 em São Paulo
    instant = datetime(2026, 11, 10, 1, 30, 0, tzinfo=UTC)
    assert ui._iso_now(instant) == "2026-11-09T22:30:00-03:00"


def test_datetime_sem_timezone_e_rejeitado() -> None:
    with pytest.raises(ValueError, match="timezone"):
        ui._iso_now(datetime(2026, 11, 9, 18, 52, 50))


def test_default_usa_agora_com_offset_de_sao_paulo() -> None:
    value = ui._iso_now()

    assert not value.endswith("Z"), f"created_at ainda em UTC: {value}"
    parsed = datetime.fromisoformat(value)
    assert parsed.utcoffset() == timedelta(hours=-3)
    assert abs(datetime.now(UTC) - parsed) < timedelta(minutes=1)
