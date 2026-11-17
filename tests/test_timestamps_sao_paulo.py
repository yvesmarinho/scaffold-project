# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_timestamps_sao_paulo.py
TITULO: Timestamps do session-time-tracker e do release-manifest em America/Sao_Paulo
DATA: 17/11/2026 17:20
MODIFICADO: 17/11/2026 17:30
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bugs cobertos:
- ``session-time-tracker.py``: timestamps em UTC (``Z``) e ``session_date``/detecção
  de sessão órfã pela data UTC — sessão iniciada após 21h (SP) caía no dia seguinte.
- ``lib/publish.publish_template``: ``created_at`` do manifesto em UTC e data do nome
  dos arquivos (``YYYYMMDD``) em UTC. Decisão do usuário (17/11/2026): SP com offset.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TRACKER = _PROJECT_ROOT / "scripts" / "session-time-tracker.py"
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib.publish import publish_template  # noqa: E402

# 01:30 UTC do dia 18 == 22:30 do dia 17 em São Paulo (UTC-3)
_VIRADA_UTC = datetime(2026, 11, 18, 1, 30, 0, tzinfo=UTC)


@pytest.fixture(scope="module")
def tracker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("session_time_tracker", _TRACKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --- session-time-tracker -----------------------------------------------------


def test_tracker_iso_now_em_sao_paulo_com_offset(tracker: ModuleType) -> None:
    assert tracker._iso_now(_VIRADA_UTC) == "2026-11-17T22:30:00-03:00"


def test_tracker_data_da_sessao_e_a_local(tracker: ModuleType) -> None:
    assert tracker._today(_VIRADA_UTC) == "2026-11-17"


def test_tracker_rejeita_datetime_sem_timezone(tracker: ModuleType) -> None:
    with pytest.raises(ValueError, match="timezone"):
        tracker._iso_now(datetime(2026, 11, 17, 22, 30))


def test_tracker_default_sem_z(tracker: ModuleType) -> None:
    value = tracker._iso_now()
    assert not value.endswith("Z")
    assert datetime.fromisoformat(value).utcoffset() == timedelta(hours=-3)


@pytest.mark.parametrize(
    ("iso", "esperado"),
    [("2026-11-17T22:30:05-03:00", "22:30:05"), ("2026-08-28T14:11:23Z", "14:11:23")],
)
def test_tracker_hora_exibida_sem_offset(tracker: ModuleType, iso: str, esperado: str) -> None:
    # histórico antigo (Z) e novo (-03:00) convivem no mesmo CSV
    assert tracker._hhmmss(iso) == esperado


def test_tracker_sessao_iniciada_no_formato_antigo_calcula_duracao_correta(
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "st"
    state_dir.mkdir()
    inicio_utc = datetime.now(UTC) - timedelta(seconds=10)
    (state_dir / "current.json").write_text(
        json.dumps(
            {
                "session_date": inicio_utc.strftime("%Y-%m-%d"),
                "start_time": inicio_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "active",
                "pauses": [],
                "current_pause": None,
            }
        ),
        encoding="utf-8",
    )
    env = {**os.environ, "SCAFFOLD_SESSION_TIME_DIR": str(state_dir)}

    result = subprocess.run(
        [sys.executable, str(_TRACKER), "stop"],
        capture_output=True, text=True, env=env, timeout=60,
    )

    assert result.returncode == 0, result.stderr
    with (state_dir / "history.csv").open(encoding="utf-8") as fh:
        row = list(csv.DictReader(fh))[-1]
    # 10s, e não 3h10s (mistura de UTC com local)
    assert row["total_duration"].startswith("00:00:")
    assert row["end_time"].endswith("-03:00")


# --- release-manifest (publish) -----------------------------------------------


def _publish(tmp_path: Path, now: datetime | None = None):
    project = tmp_path / "proj"
    (project / "scripts").mkdir(parents=True)
    (project / "scripts" / "x.py").write_text("x = 1\n", encoding="utf-8")
    return publish_template(output_dir=tmp_path / "out", project_root=project, version="9.9.9", now=now)


def test_manifesto_created_at_em_sao_paulo(tmp_path: Path) -> None:
    result = _publish(tmp_path, _VIRADA_UTC)

    assert result.created_at == "2026-11-17T22:30:00-03:00"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["created_at"] == "2026-11-17T22:30:00-03:00"


def test_manifesto_nome_dos_arquivos_usa_data_local(tmp_path: Path) -> None:
    result = _publish(tmp_path, _VIRADA_UTC)

    assert result.tarball_path.name == "enterprise-template-v9.9.9-20261117.tar.gz"
    assert result.manifest_path.name == "release-manifest-v9.9.9-20261117.json"


def test_manifesto_rejeita_datetime_sem_timezone(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timezone"):
        _publish(tmp_path, datetime(2026, 11, 17, 22, 30))


def test_manifesto_default_com_offset(tmp_path: Path) -> None:
    result = _publish(tmp_path)

    assert datetime.fromisoformat(result.created_at).utcoffset() == timedelta(hours=-3)
