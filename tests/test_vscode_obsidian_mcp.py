"""
tests/test_vscode_obsidian_mcp.py — mcp.json gerado pelo scaffold inclui obsidian-rest.

O registro de sessão é feito no vault Obsidian via MCP ``obsidian-rest``; todo
projeto gerado precisa do servidor, com credenciais apenas via ``${env:...}``.
"""

from __future__ import annotations

import pytest

from scripts.lib.vscode import _ALL_MCP_SERVERS, _MCP_BY_DOMAIN


@pytest.mark.parametrize("domain", sorted(_MCP_BY_DOMAIN))
def test_every_domain_includes_obsidian_rest(domain: str) -> None:
    assert "obsidian-rest" in _MCP_BY_DOMAIN[domain]


def test_obsidian_rest_reads_credentials_only_from_env() -> None:
    server = _ALL_MCP_SERVERS["obsidian-rest"]

    assert server["command"] == "uvx"
    assert "mcp-obsidian" in server["args"]
    for key in ("OBSIDIAN_API_KEY", "OBSIDIAN_HOST"):
        assert server["env"][key] == f"${{env:{key}}}"


def test_obsidian_rest_has_no_hardcoded_secret_or_ip() -> None:
    for value in _ALL_MCP_SERVERS["obsidian-rest"]["env"].values():
        assert value.startswith("${env:") or value in {"https", "27124"}
