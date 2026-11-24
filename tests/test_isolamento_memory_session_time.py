# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_isolamento_memory_session_time.py
TITULO: Isolamento de .memory/ e .session-time/ (SCAFFOLD_MEMORY_ROOT / SCAFFOLD_SESSION_TIME_DIR)
DATA: 17/11/2026 17:01
MODIFICADO: 24/11/2026 10:24
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bug coberto: a suíte gravava memórias fictícias em ``.memory/`` e sessões de
1 segundo em ``.session-time/history.csv`` do repo, e o teste do tracker
apagava o ``.session-time/current.json`` real (sessão em andamento). Os
caminhos passam a ser configuráveis por variável de ambiente e o conftest os
isola em ``tmp_path``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.lib import memory

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TRACKER = _PROJECT_ROOT / "scripts" / "session-time-tracker.py"
_MEM_ENV = "SCAFFOLD_MEMORY_ROOT"
_TIME_ENV = "SCAFFOLD_SESSION_TIME_DIR"


# --- .memory/ -----------------------------------------------------------------


def test_memory_root_respeita_variavel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_MEM_ENV, str(tmp_path / "mem"))

    assert memory._memory_root() == tmp_path / "mem"
    assert memory._memory_dir() == tmp_path / "mem" / "memories"
    assert memory._db_path() == tmp_path / "mem" / "index" / "memory.db"


@pytest.mark.parametrize("valor", [None, "", "   "])
def test_memory_root_sem_variavel_usa_padrao(
    valor: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    if valor is None:
        monkeypatch.delenv(_MEM_ENV, raising=False)
    else:
        monkeypatch.setenv(_MEM_ENV, valor)

    assert memory._memory_root() == memory.MEMORY_ROOT
    assert memory._db_path() == memory.DB_PATH


def test_memory_file_path_padrao_usa_variavel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(_MEM_ENV, str(tmp_path / "mem"))

    item = memory.Memory(title="Decisão X", content="corpo")

    assert item.file_path is not None
    assert item.file_path.is_relative_to(tmp_path / "mem" / "memories" / "project")


def test_memory_store_padrao_cria_estrutura_e_indice_na_variavel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(_MEM_ENV, str(tmp_path / "mem"))

    store = memory.MemoryStore()
    try:
        assert store.db_path == tmp_path / "mem" / "index" / "memory.db"
        assert (tmp_path / "mem" / "memories" / "project").is_dir()
        assert store.db_path.exists()
    finally:
        store.conn.close()


def test_memory_rebuild_index_le_da_variavel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(_MEM_ENV, str(tmp_path / "mem"))
    store = memory.MemoryStore()
    try:
        store.save(memory.Memory(title="Isolada", content="só no tmp"))
        assert store.rebuild_index() == 1
    finally:
        store.conn.close()


# --- .session-time/ -----------------------------------------------------------


def _tracker(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_TRACKER), *args],
        capture_output=True,
        text=True,
        # Fora de repo git: o resultado não depende da branch real do projeto.
        cwd=Path(env[_TIME_ENV]).parent,
        env=env,
        timeout=60,
    )


def test_tracker_grava_estado_e_historico_na_variavel(tmp_path: Path) -> None:
    state_dir = tmp_path / "st"
    env = {**os.environ, _TIME_ENV: str(state_dir)}

    assert _tracker("start", env=env).returncode == 0
    assert (state_dir / "current.json").exists()
    assert _tracker("stop", env=env).returncode == 0
    assert (state_dir / "history.csv").exists()


# --- conftest -------------------------------------------------------------------


@pytest.mark.parametrize("var", [_MEM_ENV, _TIME_ENV])
def test_conftest_isola_em_tmp(var: str, tmp_path: Path) -> None:
    valor = os.environ.get(var, "")
    assert valor, f"{var} não definido pela fixture autouse do conftest"
    assert Path(valor).is_relative_to(tmp_path)
