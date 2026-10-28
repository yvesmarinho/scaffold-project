"""
lib/session_context.py — Descoberta e resumo de contexto de sessão.

Centraliza leitura de arquivos-base do workflow de sessão para reduzir lógica
duplicada em prompts e CLIs.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

VAULT_MCP_SERVER = "obsidian-rest"
REQUIRED_MCP_SERVERS = ("memory", "sequential-thinking", VAULT_MCP_SERVER)
PENDING_TODO_RE = re.compile(r"^\s*-\s*\[ \]\s+(.*)$")


def _today_iso() -> str:
    return date.today().isoformat()


def _safe_read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _load_json_loose(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None

    raw_content = path.read_text(encoding="utf-8")
    cleaned_lines = [
        line
        for line in raw_content.splitlines()
        if not line.lstrip().startswith("//")
    ]
    cleaned = "\n".join(cleaned_lines)
    return json.loads(cleaned)


@dataclass(frozen=True)
class SessionPaths:
    """Caminhos relevantes do workflow de sessão."""

    root: Path
    docs_dir: Path
    todo_file: Path
    index_file: Path
    rules_file: Path
    vscode_mcp_file: Path
    gitignore_file: Path
    readme_file: Path

    @classmethod
    def from_root(cls, root: Path | str) -> "SessionPaths":
        root_path = Path(root).resolve()
        docs_dir = root_path / "docs"
        return cls(
            root=root_path,
            docs_dir=docs_dir,
            todo_file=docs_dir / "TODO.md",
            index_file=docs_dir / "INDEX.md",
            rules_file=root_path / ".copilot-rules.md",
            vscode_mcp_file=root_path / ".vscode" / "mcp.json",
            gitignore_file=root_path / ".gitignore",
            readme_file=root_path / "README.md",
        )


@dataclass(frozen=True)
class McpConfigStatus:
    """Estado da configuração MCP em .vscode/mcp.json."""

    exists: bool
    configured_servers: tuple[str, ...]
    missing_servers: tuple[str, ...]
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.exists and not self.missing_servers and self.error is None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ok"] = self.ok
        return data


def validate_mcp_config(paths: SessionPaths) -> McpConfigStatus:
    """Valida se memory e sequential-thinking estão configurados."""

    if not paths.vscode_mcp_file.exists():
        return McpConfigStatus(
            exists=False,
            configured_servers=(),
            missing_servers=REQUIRED_MCP_SERVERS,
            error=None,
        )

    try:
        data = _load_json_loose(paths.vscode_mcp_file) or {}
    except json.JSONDecodeError as exc:
        return McpConfigStatus(
            exists=True,
            configured_servers=(),
            missing_servers=REQUIRED_MCP_SERVERS,
            error=f"JSON inválido: {exc}",
        )

    servers = data.get("servers", {})
    if not isinstance(servers, dict):
        return McpConfigStatus(
            exists=True,
            configured_servers=(),
            missing_servers=REQUIRED_MCP_SERVERS,
            error="Campo 'servers' ausente ou inválido",
        )

    configured = tuple(
        server_name
        for server_name in REQUIRED_MCP_SERVERS
        if server_name in servers and isinstance(servers[server_name], dict)
    )
    missing = tuple(
        server_name
        for server_name in REQUIRED_MCP_SERVERS
        if server_name not in configured
    )
    return McpConfigStatus(
        exists=True,
        configured_servers=configured,
        missing_servers=missing,
    )


def build_vault_targets(paths: SessionPaths, session_date: str) -> dict[str, str]:
    """Caminhos (relativos ao vault claude_memory) que o agente usa via MCP."""

    project = paths.root.name
    sessions_dir = f"projects/{project}/sessions/"
    return {
        "mcp_server": VAULT_MCP_SERVER,
        "project": project,
        "project_note": f"projects/{project}.md",
        "sessions_dir": sessions_dir,
        "session_note": f"{sessions_dir}{session_date}.md",
    }


def read_pending_todos(todo_file: Path, *, limit: int = 5) -> list[str]:
    """Extrai itens pendentes de docs/TODO.md."""

    if not todo_file.exists():
        return []

    pending_items: list[str] = []
    for line in todo_file.read_text(encoding="utf-8").splitlines():
        match = PENDING_TODO_RE.match(line)
        if not match:
            continue
        pending_items.append(match.group(1).strip())
        if len(pending_items) >= limit:
            break
    return pending_items


def recover_context(
    paths: SessionPaths,
    *,
    today: str | None = None,
) -> dict[str, Any]:
    """Recupera contexto útil para início e encerramento de sessão."""

    today_iso = today or _today_iso()
    return {
        "today": today_iso,
        "todo_exists": paths.todo_file.exists(),
        "index_exists": paths.index_file.exists(),
        "rules_exists": paths.rules_file.exists(),
        "readme_exists": paths.readme_file.exists(),
        "pending_todos": read_pending_todos(paths.todo_file),
        "todo_excerpt": _safe_read_text(paths.todo_file)[:400],
    }
