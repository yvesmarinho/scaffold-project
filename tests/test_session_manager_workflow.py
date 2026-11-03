"""
tests/test_session_manager_workflow.py — Testes do CLI unificado de sessão.

Os docs de sessão vivem no vault Obsidian (claude_memory) e são lidos/gravados
pelo agente via MCP ``obsidian-rest``; o CLI apenas informa os caminhos no vault
e nunca cria ``docs/SESSIONS/`` no projeto.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.lib.session_context import (
    SessionPaths,
    build_vault_targets,
    recover_context,
    validate_mcp_config,
)
from scripts.lib.session_security import scan_workspace
from scripts.lib.session_workflow import run_end, run_recover, run_start, run_status

PROJECT_ROOT = Path(__file__).parent.parent
SESSION_MANAGER = PROJECT_ROOT / "scripts" / "session-manager.py"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _mcp_servers(*names: str) -> str:
    return json.dumps({"servers": {name: {"command": "npx"} for name in names}})


def _create_workspace(tmp_path: Path, name: str = "workspace") -> Path:
    root = tmp_path / name
    _write(
        root / ".vscode" / "mcp.json",
        _mcp_servers("memory", "sequential-thinking", "obsidian-rest"),
    )
    _write(root / ".gitignore", ".secrets/\n")
    _write(root / ".copilot-rules.md", "# rules\n")
    _write(root / "README.md", "# Teste\n")
    _write(
        root / "docs" / "TODO.md",
        "# TODO\n\n- [ ] Primeira pendência\n- [ ] Segunda pendência\n",
    )
    _write(root / "docs" / "INDEX.md", "# INDEX\n")
    return root


def test_validate_mcp_config_detects_required_servers(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)
    status = validate_mcp_config(SessionPaths.from_root(root))

    assert status.ok is True
    assert status.missing_servers == ()


def test_validate_mcp_config_requires_obsidian_rest(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)
    _write(root / ".vscode" / "mcp.json", _mcp_servers("memory", "sequential-thinking"))

    status = validate_mcp_config(SessionPaths.from_root(root))

    assert status.ok is False
    assert status.missing_servers == ("obsidian-rest",)


def test_build_vault_targets_uses_project_folder_name(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path, name="meu-projeto")

    targets = build_vault_targets(SessionPaths.from_root(root), "2026-07-07")

    assert targets == {
        "mcp_server": "obsidian-rest",
        "project": "meu-projeto",
        "project_note": "projects/meu-projeto.md",
        "sessions_dir": "projects/meu-projeto/sessions/",
        "session_note": "projects/meu-projeto/sessions/2026-07-07.md",
    }


def test_recover_context_reads_todos_without_local_sessions(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)
    context = recover_context(SessionPaths.from_root(root), today="2026-07-07")

    assert context["pending_todos"] == ["Primeira pendência", "Segunda pendência"]
    assert "latest_session_date" not in context


def test_run_start_returns_vault_targets_and_creates_no_local_docs(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)

    result = run_start(root, today="2026-07-07")

    assert result["ready"] is True
    assert result["vault"]["session_note"] == "projects/workspace/sessions/2026-07-07.md"
    assert "docs" not in result
    assert not (root / "docs" / "SESSIONS").exists()


def test_run_start_not_ready_without_obsidian_mcp(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)
    _write(root / ".vscode" / "mcp.json", _mcp_servers("memory", "sequential-thinking"))

    result = run_start(root, today="2026-07-07")

    assert result["ready"] is False


def test_run_start_not_ready_with_invalid_mcp_json(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)
    _write(root / ".vscode" / "mcp.json", "{ invalido")

    result = run_start(root, today="2026-07-07")

    assert result["ready"] is False
    assert result["mcp"]["error"]


def test_scan_workspace_flags_sensitive_files_outside_secrets(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)
    _write(root / "config" / "prod.key", "secret")

    result = scan_workspace(SessionPaths.from_root(root))

    assert result["clean"] is False
    assert any(item["path"] == "config/prod.key" for item in result["findings"])


def test_run_end_writes_nothing_locally(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)

    result = run_end(root, today="2026-07-07")

    assert result["ready_for_next_session"] is True
    assert result["vault"]["session_note"].endswith("2026-07-07.md")
    assert "doc_updates" not in result
    assert not (root / "docs" / "SESSIONS").exists()


def test_run_end_not_ready_with_sensitive_file(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)
    _write(root / "config" / "prod.key", "secret")

    result = run_end(root, today="2026-07-07")

    assert result["ready_for_next_session"] is False


def test_run_status_and_recover_expose_vault(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)

    status = run_status(root, today="2026-07-07")
    recover = run_recover(root, today="2026-07-07")

    assert "daily_validation" not in status
    assert status["vault"] == recover["vault"]


def test_session_manager_cli_outputs_json(tmp_path: Path) -> None:
    root = _create_workspace(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(SESSION_MANAGER),
            "--root",
            str(root),
            "--today",
            "2026-07-07",
            "--json",
            "start",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["command"] == "start"
    assert payload["ready"] is True
    assert payload["vault"]["mcp_server"] == "obsidian-rest"
