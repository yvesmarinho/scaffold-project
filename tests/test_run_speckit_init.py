"""
tests/test_run_speckit_init.py — Validação de run_speckit_init() para todos os
valores de ai_assistant (claude, copilot, both, none).

Criado em: 15/07/2026 10:00
Modificado em: 24/11/2026 11:00

Cobertura (subprocess mockado — sem rede):
  - claude  → 1 chamada `specify init --here --force --integration claude`
  - copilot → 1 chamada com integração copilot
  - both    → 2 chamadas (claude + copilot), na ordem
  - none    → nenhuma chamada, lista vazia
  - returncode != 0 → CreatedItem com status "error"
  - specify ausente (FileNotFoundError) → CreatedItem com status "error"
  - binário do agente ausente (ex.: `claude` fora do PATH) → `--ignore-agent-tools`
    + warning; com o binário presente, comando inalterado (24/11/2026)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib import project  # noqa: E402


def _make_cfg(make_project_config, ai_assistant: str):
    cfg = make_project_config("programming", "python")
    cfg.ai_assistant = ai_assistant
    return cfg


def _ok_proc() -> MagicMock:
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "ok"
    proc.stderr = ""
    return proc


@pytest.mark.parametrize("assistant", ["claude", "copilot"])
def test_single_integration_calls_specify_once(make_project_config, assistant) -> None:
    cfg = _make_cfg(make_project_config, assistant)
    with patch.object(project.subprocess, "run", return_value=_ok_proc()) as mock_run, \
            patch.object(project.shutil, "which", return_value="/usr/bin/agent"):
        results = project.run_speckit_init(cfg)

    assert mock_run.call_count == 1
    cmd = mock_run.call_args[0][0]
    assert cmd == ["specify", "init", "--here", "--force", "--integration", assistant]
    assert mock_run.call_args.kwargs["cwd"] == str(cfg.project_path)
    assert len(results) == 1
    assert results[0].status == "created"


def test_both_runs_claude_then_copilot(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "both")
    with patch.object(project.subprocess, "run", return_value=_ok_proc()) as mock_run, \
            patch.object(project.shutil, "which", return_value="/usr/bin/agent"):
        results = project.run_speckit_init(cfg)

    assert mock_run.call_count == 2
    integrations = [call.args[0][-1] for call in mock_run.call_args_list]
    assert integrations == ["claude", "copilot"]
    assert [r.status for r in results] == ["created", "created"]


def test_none_skips_specify(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "none")
    with patch.object(project.subprocess, "run") as mock_run:
        results = project.run_speckit_init(cfg)

    mock_run.assert_not_called()
    assert results == []


def test_nonzero_returncode_reports_error(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "claude")
    proc = MagicMock()
    proc.returncode = 1
    proc.stdout = ""
    proc.stderr = "boom"
    with patch.object(project.subprocess, "run", return_value=proc):
        results = project.run_speckit_init(cfg)

    assert len(results) == 1
    assert results[0].status == "error"
    assert "boom" in results[0].message


def test_specify_missing_reports_error(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "claude")
    with patch.object(project.subprocess, "run", side_effect=FileNotFoundError("specify")):
        results = project.run_speckit_init(cfg)

    assert len(results) == 1
    assert results[0].status == "error"


def test_timeout_reports_error(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "both")
    with patch.object(
        project.subprocess,
        "run",
        side_effect=subprocess.TimeoutExpired(cmd="specify", timeout=120),
    ):
        results = project.run_speckit_init(cfg)

    # Uma tentativa por integração; ambas reportam erro sem abortar o lote
    assert [r.status for r in results] == ["error", "error"]


# --- binário do agente ausente (CI / máquina sem Claude Code) -------------------


def test_claude_ausente_usa_ignore_agent_tools_e_avisa(
    make_project_config, caplog: pytest.LogCaptureFixture
) -> None:
    cfg = _make_cfg(make_project_config, "claude")
    with patch.object(project.subprocess, "run", return_value=_ok_proc()) as mock_run, \
            patch.object(project.shutil, "which", return_value=None), \
            caplog.at_level("WARNING"):
        results = project.run_speckit_init(cfg)

    cmd = mock_run.call_args[0][0]
    assert cmd == [
        "specify", "init", "--here", "--force", "--integration", "claude",
        "--ignore-agent-tools",
    ]
    assert results[0].status == "created"
    assert any("claude" in r.message and "--ignore-agent-tools" in r.message
               for r in caplog.records if r.levelname == "WARNING")


def test_claude_presente_nao_usa_ignore_agent_tools(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "claude")
    with patch.object(project.subprocess, "run", return_value=_ok_proc()) as mock_run, \
            patch.object(project.shutil, "which", return_value="/usr/bin/claude"):
        project.run_speckit_init(cfg)

    assert "--ignore-agent-tools" not in mock_run.call_args[0][0]


def test_copilot_nunca_usa_ignore_agent_tools(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "copilot")
    with patch.object(project.subprocess, "run", return_value=_ok_proc()) as mock_run, \
            patch.object(project.shutil, "which", return_value=None):
        project.run_speckit_init(cfg)

    assert "--ignore-agent-tools" not in mock_run.call_args[0][0]


def test_both_sem_claude_so_marca_a_integracao_claude(make_project_config) -> None:
    cfg = _make_cfg(make_project_config, "both")
    with patch.object(project.subprocess, "run", return_value=_ok_proc()) as mock_run, \
            patch.object(project.shutil, "which", return_value=None):
        project.run_speckit_init(cfg)

    cmds = [call.args[0] for call in mock_run.call_args_list]
    assert "--ignore-agent-tools" in cmds[0]
    assert "--ignore-agent-tools" not in cmds[1]
