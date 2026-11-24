"""
Test suite for BUG-20: MCP GitHub HTTP merge failure

Reproduz problema onde merge user-wins preserva estrutura antiga ao invés
de aplicar mudança de schema do template (CLI → HTTP).
"""

import pytest

from scripts.lib.json_merge import deep_merge_json


class TestBug20MCPMerge:
    """Testes para BUG-20 - Merge failure de mcp.json"""

    def test_current_behavior_preserves_old_structure(self):
        """
        APÓS CORREÇÃO: Merge aplica template quando há mudança de schema.

        Este teste PASSOU inicialmente (documentava o bug).
        Após correção BUG-20, deve FALHAR nos asserts do bug antigo.
        """
        # Template novo (HTTP)
        base = {
            "servers": {
                "github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/"}
            }
        }

        # Arquivo do usuário (CLI antigo)
        overlay = {
            "servers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "type": "stdio",
                    "env": {
                        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
                    },
                }
            }
        }

        # Merge com correção BUG-20
        merged = deep_merge_json(base, overlay)
        github_config = merged["servers"]["github"]

        # APÓS CORREÇÃO: Template-wins quando type muda
        assert github_config == {
            "type": "http",
            "url": "https://api.githubcopilot.com/mcp/",
        }
        assert "command" not in github_config  # ✅ Removido (schema change)
        assert "args" not in github_config  # ✅ Removido (schema change)
        assert "env" not in github_config  # ✅ Removido (schema change)
        assert github_config["type"] == "http"  # ✅ Template aplicado

    def test_expected_behavior_after_fix(self):
        """
        COMPORTAMENTO ESPERADO após correção:

        Quando há mudança de schema (type mudou), deve:
        1. Detectar breaking change
        2. Substituir completamente ao invés de merge recursivo
        3. Preservar user-wins para servers sem mudança de schema
        """
        base = {
            "servers": {
                "github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/"},
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                },
            }
        }

        overlay = {
            "servers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                    "type": "stdio",
                    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${env:TOKEN}"},
                },
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                },
            }
        }

        # Merge com detecção de schema
        merged = deep_merge_json(base, overlay)

        # GITHUB: Schema mudou (stdio → http) → template-wins
        github_config = merged["servers"]["github"]
        assert github_config == {
            "type": "http",
            "url": "https://api.githubcopilot.com/mcp/",
        }
        assert "command" not in github_config
        assert "args" not in github_config
        assert "env" not in github_config

        # MEMORY: Sem mudança de schema → user-wins preserva customizações
        memory_config = merged["servers"]["memory"]
        assert memory_config == overlay["servers"]["memory"]

    def test_deep_merge_preserves_user_when_no_schema_change(self):
        """
        CASO OK: Quando não há mudança de schema, merge user-wins funciona corretamente.
        """
        base = {
            "servers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "type": "stdio",
                }
            }
        }

        overlay = {
            "servers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "type": "stdio",
                    "timeout": 10000,  # Customização do usuário
                }
            }
        }

        merged = deep_merge_json(base, overlay)

        # OK: Preserva customização do usuário
        memory_config = merged["servers"]["memory"]
        assert memory_config["timeout"] == 10000  # ✅ User customization
        assert memory_config["type"] == "stdio"  # ✅ Sem mudança


@pytest.mark.parametrize(
    "old_type,new_type,is_breaking",
    [
        ("stdio", "http", True),
        ("http", "stdio", True),
        ("stdio", "stdio", False),
        ("http", "http", False),
    ],
)
def test_detect_schema_change(old_type, new_type, is_breaking):
    """
    Teste para função auxiliar que detecta mudança de schema.

    Mudança de 'type' em server MCP é breaking change.
    """
    from scripts.lib.json_merge import _is_mcp_schema_change

    old_config = {"type": old_type, "command": "npx"}
    new_config = {"type": new_type, "url": "https://..."}

    # Detectar mudança em path servers.github
    result = _is_mcp_schema_change(new_config, old_config, ["servers", "github"])
    assert result == is_breaking


class TestSolutionApproach:
    """
    Testes para validar abordagem de correção.

    Opção A: Template-wins para mudanças de schema
    Opção B: Detectar conflito e avisar usuário
    Opção C: Metadata de versão nos servers
    """

    def test_solution_a_template_wins_on_schema_change(self):
        """
        Solução A: Quando 'type' muda, usar template completamente.

        Pros:
        - Simples de implementar
        - Garante que updates críticos sejam aplicados
        - Comportamento previsível

        Cons:
        - Perde customizações do usuário (ex: timeout, retries)
        - Pode ser muito agressivo
        """
        pytest.skip("Solução A - a ser implementada")

    def test_solution_b_detect_and_warn(self):
        """
        Solução B: Detectar conflito e avisar usuário (interativo).

        Pros:
        - Usuário tem controle
        - Não perde dados

        Cons:
        - Requer interação (não funciona em CI/CD)
        - Mais complexo
        """
        pytest.skip("Solução B - a ser implementada")

    def test_solution_c_metadata_versioning(self):
        """
        Solução C: Adicionar metadata de versão aos servers.

        Exemplo:
        {
          "servers": {
            "github": {
              "_schema_version": "2.0",
              "type": "http",
              "url": "..."
            }
          }
        }

        Pros:
        - Tracking explícito de mudanças
        - Pode aplicar migrations

        Cons:
        - Mais invasivo
        - Requer mudança no template
        """
        pytest.skip("Solução C - a ser implementada")

    def test_schema_change_removal_of_obsolete_type_field(self):
        """
        BUG-20 EXTENDED: Detectar remoção de campo 'type' obsoleto.

        Caso real encontrado no test-workspace-fix:
        - Template (base): npx sem campo 'type' (padrão moderno)
        - User (overlay): type='stdio' com npx (padrão antigo)

        Isso também é mudança de schema! Deve aplicar template-wins.
        """
        # Template moderno: npx SEM campo type
        base = {
            "servers": {
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
            }
        }

        # Usuário: config antiga com type='stdio' (OBSOLETO)
        overlay = {
            "servers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "type": "stdio",  # ❌ OBSOLETO - deve ser removido
                },
                "sequential-thinking": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
                    "type": "stdio",  # ❌ OBSOLETO
                },
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
                    "type": "stdio",  # ❌ OBSOLETO
                },
            }
        }

        # Merge com detecção de schema change
        merged = deep_merge_json(base, overlay)

        # EXPECTATIVA: Template-wins porque overlay tem type="stdio" obsoleto
        for server_name in ["memory", "sequential-thinking", "filesystem"]:
            server_config = merged["servers"][server_name]

            # ✅ Deve usar config do template (sem type)
            assert (
                "type" not in server_config
            ), f"{server_name}: Campo 'type' obsoleto deveria ser removido"

            # ✅ Deve manter command e args do template
            assert server_config["command"] == "npx"
            assert "-y" in server_config["args"]

    def test_schema_change_addition_of_type_field(self):
        """
        BUG-20 EXTENDED: Detectar adição de campo 'type' no template.

        Caso hipotético: template adiciona type='http' onde antes não tinha.
        """
        # Template: adiciona type='http'
        base = {
            "servers": {
                "github": {"type": "http", "url": "https://api.githubcopilot.com/mcp/"}
            }
        }

        # Usuário: config antiga sem type
        overlay = {
            "servers": {
                "github": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-github"],
                }
            }
        }

        # Merge com detecção de schema change
        merged = deep_merge_json(base, overlay)

        # EXPECTATIVA: Template-wins porque type foi adicionado
        github_config = merged["servers"]["github"]

        # ✅ Deve usar config do template (com type)
        assert github_config["type"] == "http"
        assert github_config["url"] == "https://api.githubcopilot.com/mcp/"
        assert "command" not in github_config
        assert "args" not in github_config
