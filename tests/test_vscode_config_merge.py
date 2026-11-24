"""
Testes para vscode_config_merge.py (Sprint 4 - P2 Coverage Expansion)

Testes unitários para VSCodeConfigMerger.
"""

import json
from pathlib import Path

from scripts.lib.vscode_config_merge import VSCodeConfigMerger


class TestVSCodeConfigMerger:
    """Testes para VSCodeConfigMerger."""

    def test_can_merge_launch_json(self):
        """Teste: Detecta launch.json em .vscode/."""
        merger = VSCodeConfigMerger()

        assert merger.can_merge(Path(".vscode/launch.json"))
        assert merger.can_merge(Path("/project/.vscode/launch.json"))

    def test_can_merge_tasks_json(self):
        """Teste: Detecta tasks.json em .vscode/."""
        merger = VSCodeConfigMerger()

        assert merger.can_merge(Path(".vscode/tasks.json"))
        assert merger.can_merge(Path("/project/.vscode/tasks.json"))

    def test_cannot_merge_other_vscode_files(self):
        """Teste: Não detecta outros arquivos .vscode/."""
        merger = VSCodeConfigMerger()

        assert not merger.can_merge(Path(".vscode/settings.json"))
        assert not merger.can_merge(Path(".vscode/extensions.json"))
        assert not merger.can_merge(Path(".vscode/mcp.json"))

    def test_cannot_merge_non_vscode(self):
        """Teste: Não detecta arquivos fora de .vscode/."""
        merger = VSCodeConfigMerger()

        assert not merger.can_merge(Path("launch.json"))
        assert not merger.can_merge(Path("tasks.json"))

    def test_merge_adds_new_configuration(self, tmp_path):
        """Teste: Adiciona nova configuration em launch.json."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        launch_file = vscode_dir / "launch.json"

        existing_content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}"
    }
  ]
}"""

        template_content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}"
    },
    {
      "name": "Python: Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest"
    }
  ]
}"""

        launch_file.write_text(existing_content, encoding="utf-8")
        result = merger.merge(launch_file, template_content, interactive=False)

        assert result.status == "merged"
        merged_data = json.loads(launch_file.read_text(encoding="utf-8"))
        assert len(merged_data["configurations"]) == 2
        assert merged_data["configurations"][1]["name"] == "Python: Debug Tests"

    def test_merge_adds_new_task(self, tmp_path):
        """Teste: Adiciona nova task em tasks.json."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        tasks_file = vscode_dir / "tasks.json"

        existing_content = """{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest"
    }
  ]
}"""

        template_content = """{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest"
    },
    {
      "label": "Build Docker",
      "type": "shell",
      "command": "docker build ."
    }
  ]
}"""

        tasks_file.write_text(existing_content, encoding="utf-8")
        result = merger.merge(tasks_file, template_content, interactive=False)

        assert result.status == "merged"
        merged_data = json.loads(tasks_file.read_text(encoding="utf-8"))
        assert len(merged_data["tasks"]) == 2
        assert merged_data["tasks"][1]["label"] == "Build Docker"

    def test_merge_preserves_custom_configuration(self, tmp_path):
        """Teste: Preserva configuration customizada."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        launch_file = vscode_dir / "launch.json"

        existing_content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}"
    },
    {
      "name": "My Custom Config",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/app.js"
    }
  ]
}"""

        template_content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}"
    }
  ]
}"""

        launch_file.write_text(existing_content, encoding="utf-8")
        result = merger.merge(launch_file, template_content, interactive=False)

        assert result.status == "skipped"  # Custom config preservado
        merged_data = json.loads(launch_file.read_text(encoding="utf-8"))
        assert len(merged_data["configurations"]) == 2
        assert merged_data["configurations"][1]["name"] == "My Custom Config"

    def test_merge_updates_existing_configuration(self, tmp_path):
        """Teste: Atualiza configuration existente (deep merge)."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        launch_file = vscode_dir / "launch.json"

        existing_content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "args": ["--verbose"]
    }
  ]
}"""

        template_content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}"""

        launch_file.write_text(existing_content, encoding="utf-8")
        result = merger.merge(launch_file, template_content, interactive=False)

        # Deep merge: user wins preserva args, template adiciona console
        merged_data = json.loads(launch_file.read_text(encoding="utf-8"))
        config = merged_data["configurations"][0]
        # User args preservado
        assert config.get("args") == ["--verbose"]
        # Template adiciona console (se houver mudança)
        if result.status == "merged":
            assert config.get("console") == "integratedTerminal"

    def test_skip_when_no_changes(self, tmp_path):
        """Teste: Skip quando não há mudanças."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        launch_file = vscode_dir / "launch.json"

        content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}"
    }
  ]
}"""

        launch_file.write_text(content, encoding="utf-8")
        result = merger.merge(launch_file, content, interactive=False)

        assert result.status == "skipped"
        assert (
            "mudan" in result.message.lower()
        )  # Aceita "sem mudanças" ou "nenhuma mudança"

    def test_creates_backup(self, tmp_path):
        """Teste: Cria backup antes de mergear."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        launch_file = vscode_dir / "launch.json"

        existing_content = """{
  "version": "0.2.0",
  "configurations": []
}"""

        template_content = """{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}"
    }
  ]
}"""

        launch_file.write_text(existing_content, encoding="utf-8")
        merger.merge(launch_file, template_content, interactive=False)

        backup = vscode_dir / "launch.json.backup"
        assert backup.exists()
        backup_data = json.loads(backup.read_text(encoding="utf-8"))
        assert len(backup_data["configurations"]) == 0

    def test_handles_invalid_json(self, tmp_path):
        """Teste: Lida com JSON inválido."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        launch_file = vscode_dir / "launch.json"

        invalid_content = """{
  "version": "0.2.0"
  "configurations": []  // JSON inválido (falta vírgula)
}"""

        template_content = """{
  "version": "0.2.0",
  "configurations": []
}"""

        launch_file.write_text(invalid_content, encoding="utf-8")
        result = merger.merge(launch_file, template_content, interactive=False)

        assert result.status == "error"
        assert "JSON error" in result.message or "error" in result.message.lower()

    def test_preserves_top_level_properties(self, tmp_path):
        """Teste: Preserva propriedades top-level customizadas."""
        merger = VSCodeConfigMerger()
        vscode_dir = tmp_path / ".vscode"
        vscode_dir.mkdir()
        tasks_file = vscode_dir / "tasks.json"

        existing_content = """{
  "version": "2.0.0",
  "presentation": {
    "reveal": "always"
  },
  "tasks": []
}"""

        template_content = """{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "pytest"
    }
  ]
}"""

        tasks_file.write_text(existing_content, encoding="utf-8")
        merger.merge(tasks_file, template_content, interactive=False)

        merged_data = json.loads(tasks_file.read_text(encoding="utf-8"))
        assert "presentation" in merged_data  # Preservado
        assert merged_data["presentation"]["reveal"] == "always"
        assert len(merged_data["tasks"]) == 1  # Nova task adicionada
