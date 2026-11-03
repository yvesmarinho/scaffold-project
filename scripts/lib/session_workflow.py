"""
lib/session_workflow.py — Orquestração unificada do workflow de sessão.

Os docs de sessão vivem no vault Obsidian ``claude_memory`` e são lidos/gravados
pelo agente via MCP ``obsidian-rest``. Este módulo só executa passos
determinísticos (MCP, contexto, git, segurança) e devolve em ``vault`` os
caminhos da nota do projeto e da nota da sessão no vault.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .git_session import collect_git_state, commit_all, push_current_branch
from .session_context import (
    SessionPaths,
    build_vault_targets,
    recover_context,
    validate_mcp_config,
)
from .session_security import scan_workspace


def _today_iso() -> str:
    return date.today().isoformat()


def _prepare_common_state(root: Path | str, *, today: str | None = None) -> dict[str, Any]:
    session_date = today or _today_iso()
    paths = SessionPaths.from_root(root)
    mcp = validate_mcp_config(paths).to_dict()
    context = recover_context(paths, today=session_date)
    git_state = collect_git_state(paths.root).to_dict()
    return {
        "paths": paths,
        "session_date": session_date,
        "mcp": mcp,
        "context": context,
        "git": git_state,
        "vault": build_vault_targets(paths, session_date),
    }


def run_start(
    root: Path | str,
    *,
    first_time: bool = False,
    today: str | None = None,
) -> dict[str, Any]:
    """Executa o ritual enxuto de início de sessão."""

    state = _prepare_common_state(root, today=today)
    paths: SessionPaths = state["paths"]
    security = scan_workspace(paths)
    ready = bool(state["mcp"]["ok"] and security["clean"])
    return {
        "command": "start-first" if first_time else "start",
        "root": str(paths.root),
        "date": state["session_date"],
        "mcp": state["mcp"],
        "context": state["context"],
        "git": state["git"],
        "vault": state["vault"],
        "security": security,
        "ready": ready,
    }


def run_recover(root: Path | str, *, today: str | None = None) -> dict[str, Any]:
    """Recupera contexto sem executar o fluxo completo."""

    state = _prepare_common_state(root, today=today)
    return {
        "command": "recover",
        "root": str(state["paths"].root),
        "date": state["session_date"],
        "mcp": state["mcp"],
        "context": state["context"],
        "git": state["git"],
        "vault": state["vault"],
    }


def run_security_scan(root: Path | str) -> dict[str, Any]:
    """Executa o scan de segurança do workspace."""

    paths = SessionPaths.from_root(root)
    workspace = scan_workspace(paths)
    return {
        "command": "security-scan",
        "root": str(paths.root),
        "workspace": workspace,
        "clean": workspace["clean"],
    }


def run_status(root: Path | str, *, today: str | None = None) -> dict[str, Any]:
    """Resume o estado atual da sessão."""

    state = _prepare_common_state(root, today=today)
    return {
        "command": "status",
        "root": str(state["paths"].root),
        "date": state["session_date"],
        "mcp": state["mcp"],
        "context": state["context"],
        "git": state["git"],
        "vault": state["vault"],
    }


def run_end(
    root: Path | str,
    *,
    today: str | None = None,
    commit: bool = False,
    push: bool = False,
) -> dict[str, Any]:
    """Executa encerramento de sessão (o registro no vault é feito pelo agente)."""

    state = _prepare_common_state(root, today=today)
    paths: SessionPaths = state["paths"]
    workspace_security = scan_workspace(paths)

    commit_result: dict[str, Any] | None = None
    push_result: dict[str, Any] | None = None
    if commit:
        commit_result = commit_all(
            paths.root,
            title=f"chore(sessao): encerramento {state['session_date']}",
            body_lines=[
                f"Sessão {state['session_date']} encerrada.",
                f"Registro da sessão no vault: {state['vault']['session_note']}",
                (
                    "Segurança do workspace: LIMPO"
                    if workspace_security["clean"]
                    else "Segurança do workspace: ATENÇÃO"
                ),
            ],
        )
    if push:
        push_result = push_current_branch(paths.root)

    return {
        "command": "end",
        "root": str(paths.root),
        "date": state["session_date"],
        "mcp": state["mcp"],
        "context": state["context"],
        "git": collect_git_state(paths.root).to_dict(),
        "vault": state["vault"],
        "workspace_security": workspace_security,
        "commit": commit_result,
        "push": push_result,
        "ready_for_next_session": bool(workspace_security["clean"]),
    }
