#!/usr/bin/env python3
"""
test_session_time_tracker.py — Testes para o Session Time Tracker

Valida o fluxo completo de tracking de tempo integrado ao session-manager:
- start → pause → resume → stop
- Múltiplas pausas com diferentes razões
- Geração de CSV
- Visualização de estatísticas
"""

import json
import csv
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep
import pytest

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
TRACKER_SCRIPT = PROJECT_ROOT / "scripts" / "session-time-tracker.py"


def _state_dir() -> Path:
    """Diretório isolado pelo conftest (SCAFFOLD_SESSION_TIME_DIR em tmp_path)."""
    return Path(os.environ["SCAFFOLD_SESSION_TIME_DIR"])


class TestSessionTimeTracker:
    """Suite de testes para session-time-tracker.py"""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Limpar estado antes e depois de cada teste."""
        # Setup: remover arquivos de estado anteriores
        if (_state_dir() / "current.json").exists():
            (_state_dir() / "current.json").unlink()

        yield

        # Teardown: limpar após teste
        if (_state_dir() / "current.json").exists():
            (_state_dir() / "current.json").unlink()

    def _run_tracker(self, *args) -> subprocess.CompletedProcess:
        """Helper para executar o tracker script."""
        cmd = [sys.executable, str(TRACKER_SCRIPT)] + list(args)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            # Fora de repo git: o resultado não depende da branch real do projeto.
            cwd=_state_dir().parent,
        )

    def _load_state(self) -> dict:
        """Carregar estado atual da sessão."""
        if not (_state_dir() / "current.json").exists():
            return {}
        with open((_state_dir() / "current.json"), "r", encoding="utf-8") as f:
            return json.load(f)

    def test_01_start_session(self):
        """Teste: Iniciar nova sessão."""
        result = self._run_tracker("start")

        assert result.returncode == 0, f"Start falhou: {result.stderr}"
        assert "✅ Sessão iniciada:" in result.stdout
        assert (_state_dir() / "current.json").exists(), "Arquivo de estado não foi criado"

        state = self._load_state()
        assert state["status"] == "active"
        assert "start_time" in state
        assert state["pauses"] == []
        assert state["current_pause"] is None

        print(f"✅ test_01: Sessão iniciada com sucesso")

    def test_02_prevent_double_start(self):
        """Teste: Prevenir iniciar sessão quando já existe uma ativa."""
        self._run_tracker("start")
        result = self._run_tracker("start")

        assert result.returncode == 1
        assert "já em andamento" in result.stdout or "já em andamento" in result.stderr

        print(f"✅ test_02: Duplo start corretamente prevenido")

    def test_03_pause_resume_single(self):
        """Teste: Pausar e retomar sessão."""
        # Start
        self._run_tracker("start")

        # Pause
        sleep(0.5)  # Simular trabalho
        result_pause = self._run_tracker("pause", "café")
        assert result_pause.returncode == 0
        assert "⏸️" in result_pause.stdout
        assert "café" in result_pause.stdout

        state = self._load_state()
        assert state["status"] == "paused"
        assert state["current_pause"] is not None
        assert state["current_pause"]["reason"] == "café"

        # Resume
        sleep(0.5)  # Simular pausa
        result_resume = self._run_tracker("resume")
        assert result_resume.returncode == 0
        assert "▶️" in result_resume.stdout

        state = self._load_state()
        assert state["status"] == "active"
        assert state["current_pause"] is None
        assert len(state["pauses"]) == 1
        assert state["pauses"][0]["reason"] == "café"
        assert "duration_seconds" in state["pauses"][0]

        print(f"✅ test_03: Pause/resume funcionando")

    def test_04_multiple_pauses(self):
        """Teste: Múltiplas pausas durante a sessão."""
        # Start
        self._run_tracker("start")

        # Primeira pausa: café
        sleep(0.5)
        self._run_tracker("pause", "café")
        sleep(0.5)
        self._run_tracker("resume")

        # Segunda pausa: reunião
        sleep(0.5)
        self._run_tracker("pause", "reunião")
        sleep(0.5)
        self._run_tracker("resume")

        # Terceira pausa: almoço
        sleep(0.5)
        self._run_tracker("pause", "almoço")
        sleep(0.5)
        self._run_tracker("resume")

        state = self._load_state()
        assert len(state["pauses"]) == 3
        assert state["pauses"][0]["reason"] == "café"
        assert state["pauses"][1]["reason"] == "reunião"
        assert state["pauses"][2]["reason"] == "almoço"

        for pause in state["pauses"]:
            assert "duration_seconds" in pause
            # Accept 0 for very short pauses
            assert pause["duration_seconds"] >= 0

        print(f"✅ test_04: Múltiplas pausas registradas corretamente")

    def test_05_stop_session(self):
        """Teste: Finalizar sessão e gerar CSV."""
        # Start e adicionar pausas
        self._run_tracker("start")
        sleep(0.5)

        self._run_tracker("pause", "café")
        sleep(0.3)
        self._run_tracker("resume")

        sleep(0.5)

        # Stop
        result = self._run_tracker("stop")
        assert result.returncode == 0
        assert "🏁 Sessão finalizada:" in result.stdout or "Sessao finalizada:" in result.stdout
        assert "Duração total:" in result.stdout or "Duracao total:" in result.stdout
        assert "Pausas:" in result.stdout
        assert "líquido:" in result.stdout or "liquido:" in result.stdout

        # Verificar que estado foi removido
        assert not (_state_dir() / "current.json").exists(), "State file deveria ter sido removido"

        # Verificar CSV foi criado
        assert (_state_dir() / "history.csv").exists(), "CSV history não foi criado"

        # Ler última linha do CSV
        with open((_state_dir() / "history.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            last_row = rows[-1]

            assert "session_date" in last_row
            assert "total_duration" in last_row
            assert "pause_duration" in last_row
            assert "net_duration" in last_row
            assert "num_pauses" in last_row
            assert last_row["num_pauses"] == "1"

        print(f"✅ test_05: Session stop e CSV gerado com sucesso")

    def test_06_stop_while_paused(self):
        """Teste: Finalizar sessão enquanto pausada (auto-resume)."""
        self._run_tracker("start")
        sleep(0.5)

        self._run_tracker("pause", "café")
        # NÃO fazer resume, fazer stop diretamente

        result = self._run_tracker("stop")
        assert result.returncode == 0
        assert "Retomando automaticamente" in result.stdout or "🏁" in result.stdout

        assert not (_state_dir() / "current.json").exists()

        print(f"✅ test_06: Auto-resume antes do stop funcionando")

    def test_07_prevent_pause_without_session(self):
        """Teste: Prevenir pause sem sessão ativa."""
        result = self._run_tracker("pause", "café")
        assert result.returncode == 1
        assert "Nenhuma sessão ativa" in result.stdout or "Nenhuma sessão ativa" in result.stderr

        print(f"✅ test_07: Pause sem sessão corretamente bloqueado")

    def test_08_prevent_resume_without_pause(self):
        """Teste: Prevenir resume sem estar pausado."""
        self._run_tracker("start")

        result = self._run_tracker("resume")
        assert result.returncode == 1
        assert "não está pausada" in result.stdout or "não está pausada" in result.stderr

        print(f"✅ test_08: Resume sem pause corretamente bloqueado")

    def test_09_prevent_double_pause(self):
        """Teste: Prevenir pausar quando já pausado."""
        self._run_tracker("start")
        self._run_tracker("pause", "café")

        result = self._run_tracker("pause", "almoço")
        assert result.returncode == 1
        assert "já pausada" in result.stdout or "já pausada" in result.stderr

        print(f"✅ test_09: Duplo pause corretamente bloqueado")

    def test_10_stats_command(self):
        """Teste: Comando stats (requer sessões no CSV)."""
        # Criar pelo menos uma sessão completa
        self._run_tracker("start")
        sleep(0.5)
        self._run_tracker("pause", "café")
        sleep(0.3)
        self._run_tracker("resume")
        sleep(0.5)
        self._run_tracker("stop")

        # Executar stats
        result = self._run_tracker("stats")

        # Pode não ter Rich instalado, mas deve retornar sucesso
        assert result.returncode == 0
        # O output pode variar dependendo se Rich está instalado
        # Mas deve mostrar dados de alguma forma

        print(f"✅ test_10: Stats command executado")

    def test_11_complete_workflow_integration(self):
        """Teste de integração: Workflow completo session-manager."""
        print("\n" + "="*60)
        print("🧪 TESTE DE INTEGRAÇÃO COMPLETO - SESSION MANAGER WORKFLOW")
        print("="*60)

        # Simular workflow de um dia de trabalho
        print("\n📅 Simulando dia de trabalho 09:00-17:00")

        # 09:00 - Start session
        print("\n[09:00] Starting session...")
        result = self._run_tracker("start")
        assert result.returncode == 0
        print(result.stdout.strip())

        # 10:30 - Coffee break
        print("\n[10:30] Coffee break...")
        sleep(0.5)
        result = self._run_tracker("pause", "café")
        assert result.returncode == 0
        print(result.stdout.strip())

        # 10:45 - Resume work
        print("\n[10:45] Back to work...")
        sleep(0.3)
        result = self._run_tracker("resume")
        assert result.returncode == 0
        print(result.stdout.strip())

        # 12:00 - Lunch break
        print("\n[12:00] Lunch break...")
        sleep(0.5)
        result = self._run_tracker("pause", "almoço")
        assert result.returncode == 0
        print(result.stdout.strip())

        # 13:30 - Resume after lunch
        print("\n[13:30] Resume after lunch...")
        sleep(0.5)
        result = self._run_tracker("resume")
        assert result.returncode == 0
        print(result.stdout.strip())

        # 15:00 - Quick break
        print("\n[15:00] Quick break...")
        sleep(0.5)
        result = self._run_tracker("pause", "break")
        assert result.returncode == 0
        print(result.stdout.strip())

        # 15:15 - Resume
        print("\n[15:15] Back to work...")
        sleep(0.3)
        result = self._run_tracker("resume")
        assert result.returncode == 0
        print(result.stdout.strip())

        # 17:00 - End session
        print("\n[17:00] Ending session...")
        sleep(0.5)
        result = self._run_tracker("stop")
        assert result.returncode == 0
        print(result.stdout.strip())

        # Verificações finais
        print("\n📊 Verificações finais:")

        # CSV deve existir com a entrada
        assert (_state_dir() / "history.csv").exists()
        with open((_state_dir() / "history.csv"), "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            last_row = rows[-1]

            print(f"   ✅ CSV gerado: {(_state_dir() / "history.csv")}")
            print(f"   ✅ Date: {last_row['session_date']}")
            print(f"   ✅ Total: {last_row['total_duration']}")
            print(f"   ✅ Breaks: {last_row['pause_duration']}")
            print(f"   ✅ Net work: {last_row['net_duration']}")
            print(f"   ✅ Number of pauses: {last_row['num_pauses']}")

            assert last_row["num_pauses"] == "3", "Deveria ter 3 pausas"

        # State file deve ter sido removido
        assert not (_state_dir() / "current.json").exists()
        print(f"   ✅ State file removido após stop")

        print("\n" + "="*60)
        print("✅ TESTE DE INTEGRAÇÃO COMPLETO - SUCESSO")
        print("="*60)


def run_manual_test():
    """Execução manual de teste de demonstração."""
    print("🧪 TESTE MANUAL - SESSION TIME TRACKER")
    print("="*60)

    tracker = TestSessionTimeTracker()

    # Setup
    if (_state_dir() / "current.json").exists():
        (_state_dir() / "current.json").unlink()

    try:
        tracker.test_11_complete_workflow_integration()
        print("\n✅ Todos os testes passaram!")
        return 0
    except AssertionError as e:
        print(f"\n❌ Teste falhou: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_manual_test())
