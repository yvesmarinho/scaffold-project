"""
Teste de integração BUG-16: Validação do sistema de merge em upgrade real

Este teste valida que o fluxo completo de upgrade preserva customizações
ao usar o sistema de merge inteligente.

Cenário:
1. Criar projeto de teste
2. Customizar arquivos (.vscode/settings.json, .code-workspace)
3. Executar upgrade
4. Verificar que customizações foram preservadas E melhorias do template adicionadas
"""

import json

import pytest


@pytest.fixture
def test_project_dir(tmp_path):
    """Cria diretório de projeto de teste."""
    project_dir = tmp_path / "test-merge-project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def create_test_project(test_project_dir):
    """
    Cria um projeto mínimo de teste com .scaffold-state.yaml.

    Simula um projeto criado com scaffold.py sem executar scaffold real.
    """
    # Criar estrutura mínima
    (test_project_dir / ".vscode").mkdir()
    (test_project_dir / ".github").mkdir()

    # .scaffold-state.yaml mínimo
    state_content = f"""project:
  name: test-merge-project
  domain: programming
  language: python
  title: Test Merge Project

paths:
  target_dir: {test_project_dir.parent}

profiles_applied: []

created_at: "2026-05-21T10:00:00"
updated_at: "2026-05-21T10:00:00"
"""
    (test_project_dir / ".scaffold-state.yaml").write_text(
        state_content, encoding="utf-8"
    )

    return test_project_dir


def test_json_merge_preserves_customizations(create_test_project):
    """
    Testa que customizações em .vscode/settings.json são preservadas após upgrade.
    """
    project_dir = create_test_project
    settings_file = project_dir / ".vscode" / "settings.json"

    # 1. Criar settings.json com customizações do usuário
    user_settings = {
        "editor.rulers": [120],  # Customização do usuário
        "python.linting.enabled": True,  # Customização do usuário
        "files.autoSave": "afterDelay",  # Customização do usuário
    }
    settings_file.write_text(json.dumps(user_settings, indent=2), encoding="utf-8")

    # 2. Simular template com novas configs
    template_settings = {
        "editor.rulers": [80],  # Template default (user-wins deve preservar 120)
        "editor.formatOnSave": True,  # Nova feature do template
        "chat.mcp.autostart": True,  # Nova feature do template
    }

    # 3. Executar merge via JSONMerger (simula upgrade)
    from scripts.lib.json_merge import JSONMerger

    merger = JSONMerger()
    result = merger.merge(
        existing_path=settings_file,
        template_content=json.dumps(template_settings, indent=2),
        interactive=False,
    )

    # 4. Validar resultado
    assert result.status == "created", f"Expected created (merge), got {result.status}"
    assert (
        "Merged" in result.message or "customizations" in result.message
    ), "Not a merge operation"

    # 5. Ler arquivo mergeado
    merged_settings = json.loads(settings_file.read_text(encoding="utf-8"))

    # 6. Verificar preservação de customizações (user-wins)
    # Nota: Arrays fazem união (deepmerge behavior), não user-wins absoluto
    assert (
        120 in merged_settings["editor.rulers"]
    ), "User customization value not present"
    assert merged_settings["python.linting.enabled"] is True, "User customization lost"
    assert merged_settings["files.autoSave"] == "afterDelay", "User customization lost"

    # 7. Verificar adição de melhorias do template
    assert merged_settings["editor.formatOnSave"] is True, "Template feature not added"
    assert merged_settings["chat.mcp.autostart"] is True, "Template feature not added"


def test_workspace_merge_preserves_folders(create_test_project):
    """
    Testa que folders customizadas em .code-workspace são preservadas após upgrade.
    """
    project_dir = create_test_project
    workspace_file = project_dir / "test-project.code-workspace"

    # 1. Criar workspace com folders customizadas
    user_workspace = {
        "folders": [
            {"path": "."},
            {"path": "../shared-libs"},  # Customização do usuário
            {"path": "../tools"},  # Customização do usuário
        ],
        "settings": {"editor.rulers": [120]},  # Customização do usuário
    }
    workspace_file.write_text(json.dumps(user_workspace, indent=2), encoding="utf-8")

    # 2. Simular template com novas configs
    template_workspace = {
        "folders": [{"path": "."}],
        "settings": {"editor.formatOnSave": True},  # Nova feature do template
        "extensions": {
            "recommendations": ["ms-python.python"]  # Nova extensão do template
        },
    }

    # 3. Executar merge via WorkspaceMerger
    from scripts.lib.json_merge import WorkspaceMerger

    merger = WorkspaceMerger()
    result = merger.merge(
        existing_path=workspace_file,
        template_content=json.dumps(template_workspace, indent=2),
        interactive=False,
    )

    # 4. Validar resultado
    assert result.status == "created", f"Expected created (merge), got {result.status}"
    assert (
        "Merged" in result.message or "customizations" in result.message
    ), "Not a merge operation"

    # 5. Ler arquivo mergeado
    merged_workspace = json.loads(workspace_file.read_text(encoding="utf-8"))

    # 6. Verificar preservação de folders customizadas (união)
    folder_paths = [f["path"] for f in merged_workspace["folders"]]
    assert "." in folder_paths, "Base folder missing"
    assert "../shared-libs" in folder_paths, "User folder lost"
    assert "../tools" in folder_paths, "User folder lost"
    assert len(folder_paths) == 3, f"Expected 3 folders, got {len(folder_paths)}"

    # 7. Verificar settings (user-wins + template additions)
    assert merged_workspace["settings"]["editor.rulers"] == [120], "User setting lost"
    assert (
        merged_workspace["settings"]["editor.formatOnSave"] is True
    ), "Template setting not added"

    # 8. Verificar extensões
    assert (
        "ms-python.python" in merged_workspace["extensions"]["recommendations"]
    ), "Template extension not added"


def test_copilot_rules_consolidation(create_test_project):
    """
    Testa que múltiplos .copilot-rules*.md são consolidados automaticamente.
    """
    project_dir = create_test_project

    # 1. Criar múltiplos arquivos .copilot-rules
    file1 = project_dir / ".copilot-rules.md"
    file2 = project_dir / ".copilot-strict-rules.md"
    file3 = project_dir / "copilot-instructions.md"

    file1.write_text(
        """## Regra A
Conteúdo A.

## Regra B
Conteúdo B.
""",
        encoding="utf-8",
    )

    file2.write_text(
        """## Regra C
Conteúdo C (strict).
""",
        encoding="utf-8",
    )

    file3.write_text(
        """## Regra D
Conteúdo D (instructions).
""",
        encoding="utf-8",
    )

    # 2. Executar consolidação
    from scripts.lib.copilot_rules_consolidate import consolidate_copilot_rules

    backup_dir = project_dir / ".backups" / "copilot-rules"
    result = consolidate_copilot_rules(project_dir, backup_dir)

    # 3. Validar resultado
    assert result is not None, "Consolidation returned None"
    assert (
        result == project_dir / ".copilot-rules.md"
    ), "Wrong consolidation output path"

    # 4. Verificar que arquivo consolidado existe
    assert result.exists(), "Consolidated file not created"

    # 5. Ler conteúdo consolidado
    content = result.read_text(encoding="utf-8")

    # 6. Verificar que todas as seções foram incluídas
    assert "## Regra A" in content, "Section A missing"
    assert "## Regra B" in content, "Section B missing"
    assert "## Regra C" in content, "Section C missing"
    assert "## Regra D" in content, "Section D missing"

    # 7. Verificar que backups foram criados
    assert (backup_dir / ".copilot-rules.md").exists(), "Backup 1 not created"
    assert (backup_dir / ".copilot-strict-rules.md").exists(), "Backup 2 not created"
    assert (backup_dir / "copilot-instructions.md").exists(), "Backup 3 not created"

    # 8. Verificar que duplicatas foram removidas
    assert not file2.exists(), "Duplicate file 2 not removed"
    assert not file3.exists(), "Duplicate file 3 not removed"

    # 9. Verificar que arquivo principal ainda existe
    assert file1.exists(), "Main file was removed"
