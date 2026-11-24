# -*- coding: utf-8 -*-
"""
Testes para normalize_github_mcp() e _apply_github_normalization() em vscode.py.

Cobre:
- Servidor github já oficial → sem mudanças
- Servidor github com URL errada (mesmo type) → substituído
- Servidor github via npx (type: stdio ou sem type) → substituído
- Entrada não-github com args de servidor GitHub unofficial → removida
- Entrada não-github com URL github não-oficial → removida
- Múltiplos servidores normais preservados → intactos
- Arquivo mcp.json em disco → normalizado corretamente
"""

import json

from scripts.lib.vscode import (
    _ALL_MCP_SERVERS,
    _apply_github_normalization,
    normalize_github_mcp,
)

OFFICIAL = _ALL_MCP_SERVERS["github"]
OFFICIAL_URL = OFFICIAL["url"]  # https://api.githubcopilot.com/mcp/


# ---------------------------------------------------------------------------
# normalize_github_mcp() — testes unitários
# ---------------------------------------------------------------------------


class TestNormalizeGithubMcp:

    def test_oficial_sem_mudancas(self):
        """Servidor github já oficial não gera mudanças."""
        servers = {
            "github": OFFICIAL,
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
            },
        }
        result, changes = normalize_github_mcp(servers)
        assert result["github"] == OFFICIAL
        assert "memory" in result
        assert changes == []

    def test_github_url_errada_substituido(self):
        """Servidor github com URL diferente é substituído."""
        servers = {
            "github": {"type": "http", "url": "https://unofficial.example.com/mcp/"}
        }
        result, changes = normalize_github_mcp(servers)
        assert result["github"] == OFFICIAL
        assert len(changes) == 1
        assert "substituído" in changes[0]

    def test_github_via_npx_substituido(self):
        """Servidor github configurado via npx (tipo antigo) é substituído."""
        servers = {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
            }
        }
        result, changes = normalize_github_mcp(servers)
        assert result["github"] == OFFICIAL
        assert len(changes) == 1

    def test_github_sem_type_substituido(self):
        """Servidor github sem type (npx moderno) é substituído."""
        servers = {
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github", "--token", "xxx"],
            }
        }
        result, changes = normalize_github_mcp(servers)
        assert result["github"] == OFFICIAL
        assert len(changes) == 1

    def test_entrada_nao_github_com_args_unofficial_removida(self):
        """Entrada com nome diferente mas args de servidor GitHub unofficial é removida."""
        servers = {
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
            },
            "github-old": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
            },
        }
        result, changes = normalize_github_mcp(servers)
        assert "github-old" not in result
        assert "memory" in result
        assert len(changes) == 1
        assert "removido" in changes[0]

    def test_entrada_com_url_github_nao_oficial_removida(self):
        """Entrada com URL apontando para github (não-oficial) é removida."""
        servers = {
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
            },
            "gh-unofficial": {
                "type": "http",
                "url": "https://github.example.com/mcp/",
            },
        }
        result, changes = normalize_github_mcp(servers)
        assert "gh-unofficial" not in result
        assert "memory" in result
        assert len(changes) == 1

    def test_servidores_normais_preservados(self):
        """Servidores não-relacionados ao github são preservados."""
        servers = {
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
            },
            "sequential-thinking": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
            },
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
            },
            "github": OFFICIAL,
        }
        result, changes = normalize_github_mcp(servers)
        assert result == servers
        assert changes == []

    def test_sem_entrada_github_preserva_resto(self):
        """Ausência do servidor github não causa erro e outros servidores são preservados."""
        servers = {
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
            },
        }
        result, changes = normalize_github_mcp(servers)
        assert result == servers
        assert changes == []

    def test_multiplas_entradas_problematicas(self):
        """Múltiplas entradas inválidas (github oficial errado + entrada unofficial) são todas corrigidas."""
        servers = {
            "github": {"type": "http", "url": "https://wrong.url/mcp/"},
            "github-unofficial": {
                "command": "npx",
                "args": ["-y", "mcp-server-github"],
            },
            "memory": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-memory"],
            },
        }
        result, changes = normalize_github_mcp(servers)
        assert result["github"] == OFFICIAL
        assert "github-unofficial" not in result
        assert "memory" in result
        assert len(changes) == 2


# ---------------------------------------------------------------------------
# _apply_github_normalization() — testes com arquivo em disco
# ---------------------------------------------------------------------------


class TestApplyGithubNormalization:

    def test_arquivo_ja_oficial_nao_alterado(self, tmp_path):
        """Arquivo com servidor oficial não é reescrito."""
        mcp_file = tmp_path / "mcp.json"
        original = {
            "servers": {
                "github": OFFICIAL,
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                },
            }
        }
        mcp_file.write_text(json.dumps(original, indent=2) + "\n")
        mtime_before = mcp_file.stat().st_mtime

        _apply_github_normalization(mcp_file)

        mtime_after = mcp_file.stat().st_mtime
        assert mtime_before == mtime_after  # arquivo não foi tocado

    def test_arquivo_com_github_errado_e_normalizado(self, tmp_path):
        """Arquivo com servidor github não-oficial é normalizado em disco."""
        mcp_file = tmp_path / "mcp.json"
        data = {
            "servers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                },
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                },
            }
        }
        mcp_file.write_text(json.dumps(data, indent=2) + "\n")

        _apply_github_normalization(mcp_file)

        result = json.loads(mcp_file.read_text())
        assert result["servers"]["github"] == OFFICIAL
        assert "memory" in result["servers"]

    def test_arquivo_inexistente_nao_levanta_excecao(self, tmp_path):
        """Arquivo inexistente não levanta exceção (warning silencioso)."""
        mcp_file = tmp_path / "nonexistent.json"
        _apply_github_normalization(mcp_file)  # não deve levantar

    def test_json_invalido_nao_levanta_excecao(self, tmp_path):
        """JSON inválido não levanta exceção (warning silencioso)."""
        mcp_file = tmp_path / "mcp.json"
        mcp_file.write_text("{ invalid json }")
        _apply_github_normalization(mcp_file)  # não deve levantar
