"""
Testes para estratégia universal de merge JSON (user-wins sem union).

Testa implementação v2.0 do deep_merge_json() e JSONMerger.
"""

from pathlib import Path

from scripts.lib.json_merge import JSONMerger, deep_merge_json


class TestDeepMergeJsonUserWins:
    """Testa estratégia user-wins universal para merge JSON."""

    def test_arrays_are_replaced_not_merged(self):
        """Arrays do usuário substituem template completamente."""
        base = {"items": [1, 2, 3]}
        overlay = {"items": [4, 5]}

        result = deep_merge_json(base, overlay)

        assert result["items"] == [4, 5], "Array deve ser substituído, NÃO concatenado"
        assert result["items"] != [1, 2, 3, 4, 5], "NÃO deve fazer union de arrays"

    def test_nested_objects_are_merged(self):
        """Objetos aninhados fazem merge recursivo."""
        base = {"config": {"a": 1, "b": 2}}
        overlay = {"config": {"b": 3, "c": 4}}

        result = deep_merge_json(base, overlay)

        assert result == {"config": {"a": 1, "b": 3, "c": 4}}

    def test_new_template_keys_are_added(self):
        """Chaves novas do template são adicionadas."""
        base = {"new_key": "new_value", "nested": {"new": "data"}}
        overlay = {"existing": "value"}

        result = deep_merge_json(base, overlay)

        assert "new_key" in result
        assert "existing" in result
        assert result["nested"] == {"new": "data"}

    def test_user_values_override_template(self):
        """Valores primitivos do usuário sobrescrevem template."""
        base = {"version": "1.0.0", "enabled": True}
        overlay = {"version": "2.0.0"}

        result = deep_merge_json(base, overlay)

        assert result["version"] == "2.0.0"
        assert result["enabled"] is True

    def test_empty_arrays_replace(self):
        """Arrays vazios do usuário substituem arrays do template."""
        base = {"items": [1, 2, 3]}
        overlay = {"items": []}

        result = deep_merge_json(base, overlay)

        assert result["items"] == []

    def test_deeply_nested_merge(self):
        """Merge funciona em estruturas profundamente aninhadas."""
        base = {"level1": {"level2": {"level3": {"a": 1, "b": [1, 2]}}}}
        overlay = {"level1": {"level2": {"level3": {"b": [3, 4], "c": 3}}}}

        result = deep_merge_json(base, overlay)

        assert result["level1"]["level2"]["level3"]["a"] == 1  # template key
        assert result["level1"]["level2"]["level3"]["b"] == [3, 4]  # user array wins
        assert result["level1"]["level2"]["level3"]["c"] == 3  # user key


class TestJSONMergerUniversal:
    """Testa JSONMerger aplicando user-wins para TODOS os JSONs."""

    def test_accepts_vscode_extensions_json(self):
        """JSONMerger aceita extensions.json."""
        merger = JSONMerger()
        path = Path(".vscode/extensions.json")

        assert merger.can_merge(path) is True

    def test_accepts_vscode_mcp_json(self):
        """JSONMerger aceita mcp.json."""
        merger = JSONMerger()
        path = Path(".vscode/mcp.json")

        assert merger.can_merge(path) is True

    def test_accepts_vscode_settings_json(self):
        """JSONMerger aceita settings.json."""
        merger = JSONMerger()
        path = Path(".vscode/settings.json")

        assert merger.can_merge(path) is True

    def test_accepts_package_json(self):
        """JSONMerger aceita package.json."""
        merger = JSONMerger()
        path = Path("package.json")

        assert merger.can_merge(path) is True

    def test_accepts_tsconfig_json(self):
        """JSONMerger aceita tsconfig.json."""
        merger = JSONMerger()
        path = Path("tsconfig.json")

        assert merger.can_merge(path) is True

    def test_accepts_eslintrc_json(self):
        """JSONMerger aceita .eslintrc.json."""
        merger = JSONMerger()
        path = Path(".eslintrc.json")

        assert merger.can_merge(path) is True

    def test_rejects_code_workspace(self):
        """JSONMerger rejeita .code-workspace (tem merger específico)."""
        merger = JSONMerger()
        path = Path("project.code-workspace")

        assert merger.can_merge(path) is False


class TestRealWorldScenarios:
    """Testa cenários reais de merge."""

    def test_extensions_json_merge(self):
        """Simula merge de extensions.json sem duplicação."""
        base = {"recommendations": ["ms-python.python", "github.copilot"]}
        overlay = {
            "recommendations": ["github.copilot", "ms-python.python", "astral-sh.uv"]
        }

        result = deep_merge_json(base, overlay)

        # User list wins completamente
        assert result["recommendations"] == [
            "github.copilot",
            "ms-python.python",
            "astral-sh.uv",
        ]
        # NÃO deve ter duplicações ou concatenação
        assert len(result["recommendations"]) == 3

    def test_mcp_json_merge_args_not_duplicated(self):
        """Simula merge de mcp.json sem duplicar args."""
        base = {
            "mcpServers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                }
            }
        }
        overlay = {
            "mcpServers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "env": {"CUSTOM": "value"},
                },
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                },
            }
        }

        result = deep_merge_json(base, overlay)

        # Args do usuário não duplicam
        assert result["mcpServers"]["memory"]["args"] == [
            "-y",
            "@modelcontextprotocol/server-memory",
        ]
        # Custom env preservado
        assert result["mcpServers"]["memory"]["env"] == {"CUSTOM": "value"}
        # Custom server preservado
        assert "filesystem" in result["mcpServers"]

    def test_package_json_scripts_merge(self):
        """Simula merge de package.json scripts."""
        base = {"scripts": {"build": "tsc", "test": "jest"}}
        overlay = {"scripts": {"dev": "tsx watch src/index.ts", "build": "vite build"}}

        result = deep_merge_json(base, overlay)

        # User script sobrescreve template
        assert result["scripts"]["build"] == "vite build"
        # Template script adicionado
        assert result["scripts"]["test"] == "jest"
        # User script preservado
        assert result["scripts"]["dev"] == "tsx watch src/index.ts"

    def test_tsconfig_paths_merge(self):
        """Simula merge de tsconfig.json."""
        base = {
            "compilerOptions": {"target": "ES2020", "module": "commonjs"},
            "include": ["src/**/*"],
        }
        overlay = {
            "compilerOptions": {"target": "ES2022", "paths": {"@/*": ["src/*"]}},
            "include": ["src/**/*", "types/**/*"],
        }

        result = deep_merge_json(base, overlay)

        # User target wins
        assert result["compilerOptions"]["target"] == "ES2022"
        # Template module adicionado
        assert result["compilerOptions"]["module"] == "commonjs"
        # User paths preservado
        assert result["compilerOptions"]["paths"] == {"@/*": ["src/*"]}
        # User include wins (NÃO concatena)
        assert result["include"] == ["src/**/*", "types/**/*"]

    def test_settings_json_merge(self):
        """Simula merge de settings.json."""
        base = {"editor.rulers": [80], "editor.formatOnSave": True}
        overlay = {"editor.rulers": [120], "python.linting.enabled": True}

        result = deep_merge_json(base, overlay)

        # User rulers win (não concatena)
        assert result["editor.rulers"] == [120]
        # Template setting adicionado
        assert result["editor.formatOnSave"] is True
        # User setting preservado
        assert result["python.linting.enabled"] is True

    def test_complex_object_with_multiple_array_levels(self):
        """Testa merge complexo com arrays em múltiplos níveis."""
        base = {
            "settings": {
                "editor": {"rulers": [80, 100], "codeActionsOnSave": ["source.fixAll"]}
            }
        }
        overlay = {
            "settings": {
                "editor": {"rulers": [120], "fontSize": 14},
                "python": {"analysis": {"typeCheckingMode": "strict"}},
            }
        }

        result = deep_merge_json(base, overlay)

        # User rulers win
        assert result["settings"]["editor"]["rulers"] == [120]
        # Template codeActionsOnSave adicionado
        assert result["settings"]["editor"]["codeActionsOnSave"] == ["source.fixAll"]
        # User fontSize preservado
        assert result["settings"]["editor"]["fontSize"] == 14
        # User python config preservado
        assert result["settings"]["python"]["analysis"]["typeCheckingMode"] == "strict"


class TestEdgeCases:
    """Testa casos extremos e edge cases."""

    def test_null_values(self):
        """Testa merge com valores null."""
        base = {"key": "value"}
        overlay = {"key": None}

        result = deep_merge_json(base, overlay)

        assert result["key"] is None  # User null wins

    def test_boolean_values(self):
        """Testa merge com valores booleanos."""
        base = {"enabled": True, "debug": False}
        overlay = {"enabled": False}

        result = deep_merge_json(base, overlay)

        assert result["enabled"] is False  # User value wins
        assert result["debug"] is False  # Template value preserved

    def test_number_values(self):
        """Testa merge com valores numéricos."""
        base = {"port": 3000, "timeout": 5000}
        overlay = {"port": 8080}

        result = deep_merge_json(base, overlay)

        assert result["port"] == 8080
        assert result["timeout"] == 5000

    def test_mixed_types_in_arrays(self):
        """Testa arrays com tipos mistos."""
        base = {"items": [1, "two", {"three": 3}]}
        overlay = {"items": ["a", 2, {"b": "B"}]}

        result = deep_merge_json(base, overlay)

        # User array wins completamente
        assert result["items"] == ["a", 2, {"b": "B"}]

    def test_empty_base(self):
        """Testa merge com base vazio."""
        base = {}
        overlay = {"key": "value"}

        result = deep_merge_json(base, overlay)

        assert result == {"key": "value"}

    def test_empty_overlay(self):
        """Testa merge com overlay vazio."""
        base = {"key": "value"}
        overlay = {}

        result = deep_merge_json(base, overlay)

        assert result == {"key": "value"}

    def test_both_empty(self):
        """Testa merge com ambos vazios."""
        base = {}
        overlay = {}

        result = deep_merge_json(base, overlay)

        assert result == {}
