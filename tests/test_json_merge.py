"""
Testes para json_merge.py (BUG-16 Fase 1 e 2)

Testes unitários para JSONMerger e WorkspaceMerger.
"""

import json
from pathlib import Path

from scripts.lib.json_merge import (
    JSONMerger,
    WorkspaceMerger,
    deep_merge_json,
)


class TestDeepMergeJSON:
    """Testes para deep_merge_json."""

    def test_merge_flat_dicts(self):
        """Teste: Merge de dicionários simples."""
        base = {"a": 1, "b": 2}
        overlay = {"b": 3, "c": 4}

        result = deep_merge_json(base, overlay)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dicts(self):
        """Teste: Merge de dicionários aninhados."""
        base = {"a": {"b": 1, "c": 2}}
        overlay = {"a": {"c": 3, "d": 4}}

        result = deep_merge_json(base, overlay)

        assert result == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_merge_lists_union(self):
        """Teste: Merge de listas com estratégia user-wins v2.0 (overlay substitui base)."""
        base = {"list": [1, 2]}
        overlay = {"list": [2, 3]}

        result = deep_merge_json(base, overlay)

        # v2.0: user-wins sem union - overlay substitui base completamente
        assert result == {"list": [2, 3]}

    def test_user_wins_strategy(self):
        """Teste: Valores do overlay sobrescrevem base (user-wins v2.0)."""
        base = {"python.analysis.extraPaths": ["./src"]}
        overlay = {"python.analysis.extraPaths": ["./custom/lib"]}

        result = deep_merge_json(base, overlay)

        # v2.0: user-wins sem union - overlay substitui base completamente
        assert result["python.analysis.extraPaths"] == ["./custom/lib"]
        assert "./custom/lib" in result["python.analysis.extraPaths"]
        assert "./src" not in result["python.analysis.extraPaths"]


class TestJSONMerger:
    """Testes para JSONMerger."""

    def test_can_merge_json_files(self):
        """Teste: Detecta arquivos .json."""
        merger = JSONMerger()

        assert merger.can_merge(Path(".vscode/settings.json"))
        assert merger.can_merge(Path(".vscode/mcp.json"))
        assert merger.can_merge(Path("package.json"))

    def test_cannot_merge_workspace(self):
        """Teste: Não detecta .code-workspace (merger próprio)."""
        merger = JSONMerger()

        assert not merger.can_merge(Path("project.code-workspace"))

    def test_cannot_merge_non_json(self):
        """Teste: Não detecta arquivos não-.json."""
        merger = JSONMerger()

        assert not merger.can_merge(Path("README.md"))
        assert not merger.can_merge(Path("Makefile"))

    def test_merge_settings_json(self, tmp_path):
        """Teste: Merge de settings.json real."""
        merger = JSONMerger()

        # Criar arquivo existente com customizações
        existing_file = tmp_path / "settings.json"
        existing_data = {
            "chat.mcp.autostart": True,
            "python.analysis.extraPaths": ["./custom/lib"],
            "editor.rulers": [120],
        }
        existing_file.write_text(json.dumps(existing_data, indent=2))

        # Template com novos campos
        template_data = {
            "chat.mcp.autostart": True,
            "github.copilot.chat.enableMcp": True,
            "python.analysis.extraPaths": ["./src"],
            "editor.formatOnSave": True,
        }
        template_content = json.dumps(template_data, indent=2)

        # Executar merge
        result = merger.merge(existing_file, template_content, interactive=False)

        # Verificar resultado
        assert result.status == "created"
        assert existing_file.exists()

        # Verificar conteúdo mergeado
        merged_data = json.loads(existing_file.read_text())

        # Campos do template presentes
        assert merged_data["github.copilot.chat.enableMcp"] is True
        assert merged_data["editor.formatOnSave"] is True

        # Customizações do usuário preservadas
        assert merged_data["editor.rulers"] == [120]
        assert "./custom/lib" in merged_data["python.analysis.extraPaths"]

        # Backup criado
        backup_file = tmp_path / "settings.json.backup"
        assert backup_file.exists()


class TestWorkspaceMerger:
    """Testes para WorkspaceMerger."""

    def test_can_merge_workspace_files(self):
        """Teste: Detecta arquivos .code-workspace."""
        merger = WorkspaceMerger()

        assert merger.can_merge(Path("project.code-workspace"))
        assert merger.can_merge(Path("my-app.code-workspace"))

    def test_cannot_merge_regular_json(self):
        """Teste: Não detecta JSON regular."""
        merger = WorkspaceMerger()

        assert not merger.can_merge(Path("settings.json"))
        assert not merger.can_merge(Path("package.json"))

    def test_merge_folders_union(self, tmp_path):
        """Teste: Merge de folders (união sem duplicatas)."""
        merger = WorkspaceMerger()

        # Arquivo existente
        existing_file = tmp_path / "project.code-workspace"
        existing_data = {"folders": [{"path": "."}, {"path": "../shared-libs"}]}
        existing_file.write_text(json.dumps(existing_data, indent=2))

        # Template
        template_data = {"folders": [{"path": "."}]}
        template_content = json.dumps(template_data, indent=2)

        # Executar merge
        result = merger.merge(existing_file, template_content, interactive=False)

        # Verificar resultado
        assert result.status == "created"

        merged_data = json.loads(existing_file.read_text())

        # Deve ter 2 folders (união, sem duplicata de ".")
        assert len(merged_data["folders"]) == 2
        paths = [f["path"] for f in merged_data["folders"]]
        assert "." in paths
        assert "../shared-libs" in paths

    def test_merge_complete_workspace(self, tmp_path):
        """Teste: Merge completo de workspace (folders + settings + extensions)."""
        merger = WorkspaceMerger()

        # Arquivo existente com customizações
        existing_file = tmp_path / "app.code-workspace"
        existing_data = {
            "folders": [{"path": "."}, {"path": "../libs"}],
            "settings": {"editor.rulers": [120], "python.linting.enabled": True},
            "extensions": {
                "recommendations": [
                    "dbaeumer.vscode-eslint",
                    "ms-vscode.vscode-typescript-next",
                ]
            },
        }
        existing_file.write_text(json.dumps(existing_data, indent=2))

        # Template
        template_data = {
            "folders": [{"path": "."}],
            "settings": {"editor.rulers": [80], "editor.formatOnSave": True},
            "extensions": {"recommendations": ["ms-python.python", "github.copilot"]},
        }
        template_content = json.dumps(template_data, indent=2)

        # Executar merge
        result = merger.merge(existing_file, template_content, interactive=False)

        assert result.status == "created"

        merged_data = json.loads(existing_file.read_text())

        # Verificar folders (união)
        assert len(merged_data["folders"]) == 2

        # Verificar settings (deep merge, lista unida)
        # Nota: deepmerge concatena listas, então teremos [80, 120]
        assert 120 in merged_data["settings"]["editor.rulers"]  # usuário
        assert merged_data["settings"]["editor.formatOnSave"] is True  # template
        assert merged_data["settings"]["python.linting.enabled"] is True  # usuário

        # Verificar extensions (união)
        ext_ids = merged_data["extensions"]["recommendations"]
        assert len(ext_ids) == 4  # 2 do usuário + 2 do template
        assert "dbaeumer.vscode-eslint" in ext_ids
        assert "ms-python.python" in ext_ids
        assert "github.copilot" in ext_ids
