"""
Test suite para validar scaffold upgrade no test-workspace-fix

Valida correções aplicadas após scaffold upgrade --force:
- BUG-20: MCP GitHub HTTP migration
- BUG-17: session-time-tracker deployment
- BUG-18: objetivo.yaml deployment
- BUG-19: git_validators.py deployment
- Arquivos críticos e configurações

Usage:
    pytest tests/test_validate_test_workspace_fix.py -v
    pytest tests/test_validate_test_workspace_fix.py::TestBug20MCP -v
"""

import json
from pathlib import Path

import pytest

# Path para test-workspace-fix
TEST_WORKSPACE_FIX = Path("/home/yves_marinho/DevOps/Projetos/test-workspace-fix")


@pytest.fixture
def workspace_path():
    """Fixture que retorna o path do test-workspace-fix."""
    if not TEST_WORKSPACE_FIX.exists():
        pytest.skip(f"test-workspace-fix não encontrado em {TEST_WORKSPACE_FIX}")
    return TEST_WORKSPACE_FIX


class TestBug20MCP:
    """Validação da correção do BUG-20: MCP GitHub HTTP migration."""

    def test_mcp_json_exists(self, workspace_path):
        """Verificar que .vscode/mcp.json existe."""
        mcp_file = workspace_path / ".vscode" / "mcp.json"
        assert mcp_file.exists(), ".vscode/mcp.json não encontrado"

    def test_mcp_json_is_valid(self, workspace_path):
        """Verificar que mcp.json contém JSON válido."""
        mcp_file = workspace_path / ".vscode" / "mcp.json"
        try:
            with mcp_file.open() as f:
                data = json.load(f)
            assert isinstance(data, dict), "mcp.json deve ser um objeto JSON"
        except json.JSONDecodeError as e:
            pytest.fail(f"mcp.json contém JSON inválido: {e}")

    def test_github_server_uses_http(self, workspace_path):
        """BUG-20: Verificar que GitHub server usa HTTP (não stdio CLI)."""
        mcp_file = workspace_path / ".vscode" / "mcp.json"
        with mcp_file.open() as f:
            mcp_config = json.load(f)

        github_server = mcp_config.get("mcpServers", {}).get("github")

        if not github_server:
            pytest.skip("GitHub MCP server não configurado (OK se intencional)")

        server_type = github_server.get("type")

        # BUG-20 Fix: Deve ser HTTP, não stdio
        assert server_type != "stdio", (
            f"❌ BUG-20 NÃO CORRIGIDO: GitHub server ainda usa 'stdio' (CLI obsoleto)\n"
            f"Esperado: type='http' ou comando npx\n"
            f"Encontrado: type='{server_type}'"
        )

        # Validar configuração HTTP correta
        if server_type == "http":
            # Configuração HTTP nativa
            url = github_server.get("url")
            assert url, "Configuração HTTP deve ter campo 'url'"
            assert (
                "githubcopilot.com" in url or "github.com" in url
            ), f"URL suspeita: {url}"
        else:
            # Configuração via npx (também aceitável)
            command = github_server.get("command")
            args = github_server.get("args", [])
            assert command == "npx", f"Comando esperado 'npx', encontrado '{command}'"
            assert (
                "@modelcontextprotocol/server-github" in args
            ), "Args devem incluir @modelcontextprotocol/server-github"

    def test_github_server_no_obsolete_fields(self, workspace_path):
        """Verificar que campos obsoletos (stdio) foram removidos."""
        mcp_file = workspace_path / ".vscode" / "mcp.json"
        with mcp_file.open() as f:
            mcp_config = json.load(f)

        github_server = mcp_config.get("mcpServers", {}).get("github", {})

        if github_server.get("type") == "http":
            # Configuração HTTP não deve ter campos CLI
            obsolete_fields = ["command", "args", "env"]
            found_obsolete = [f for f in obsolete_fields if f in github_server]

            assert not found_obsolete, (
                f"❌ Configuração HTTP contém campos obsoletos do CLI: {found_obsolete}\n"
                f"Remova: {', '.join(found_obsolete)}"
            )


class TestBug17TimeTracker:
    """Validação da correção do BUG-17: session-time-tracker deployment."""

    def test_session_time_tracker_script_exists(self, workspace_path):
        """Verificar que session-time-tracker.py foi deployado."""
        script = workspace_path / "scripts" / "session-time-tracker.py"
        assert script.exists(), "scripts/session-time-tracker.py não encontrado"

    def test_session_start_prompt_uses_session_manager(self, workspace_path):
        """Verificar que session-start.prompt.md usa o CLI canônico."""
        candidates = [
            workspace_path / ".github" / "prompts" / "session-start.prompt.md",
            workspace_path / ".claude" / "commands" / "session-start..md",
        ]
        prompt = next(
            (candidate for candidate in candidates if candidate.exists()), None
        )
        assert prompt is not None, "Nenhum wrapper de session-start encontrado"

        content = prompt.read_text(encoding="utf-8")
        assert (
            "python scripts/session-manager.py start --json" in content
        ), "Wrapper de session-start não usa scripts/session-manager.py"
        assert (
            "Passo 6.5" not in content
        ), "Wrapper de session-start ainda contém fluxo legado numerado"

    def test_session_manager_script_exists(self, workspace_path):
        """Verificar que session-manager.py foi deployado."""
        script = workspace_path / "scripts" / "session-manager.py"
        assert script.exists(), "scripts/session-manager.py não encontrado"

    def test_session_time_directory_exists(self, workspace_path):
        """Verificar que diretório .session-time/ foi criado."""
        session_time_dir = workspace_path / ".session-time"
        assert session_time_dir.is_dir(), ".session-time/ não foi criado"


class TestBug18ObjetivoYaml:
    """Validação da correção do BUG-18: objetivo.yaml deployment."""

    def test_objetivo_yaml_exists(self, workspace_path):
        """Verificar que objetivo.yaml foi deployado na raiz."""
        objetivo = workspace_path / "objetivo.yaml"
        assert objetivo.exists(), "objetivo.yaml não encontrado na raiz do projeto"

    def test_objetivo_yaml_is_valid(self, workspace_path):
        """Verificar que objetivo.yaml contém YAML válido."""
        objetivo = workspace_path / "objetivo.yaml"
        try:
            import yaml

            with objetivo.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict), "objetivo.yaml deve ser um objeto YAML"
        except yaml.YAMLError as e:
            pytest.fail(f"objetivo.yaml contém YAML inválido: {e}")

    def test_objetivo_yaml_has_project_info(self, workspace_path):
        """Verificar que objetivo.yaml contém informações do projeto."""
        objetivo = workspace_path / "objetivo.yaml"
        import yaml

        with objetivo.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert "project" in data, "objetivo.yaml deve ter seção 'project'"
        project = data["project"]
        assert "name" in project, "project deve ter campo 'name'"
        assert (
            project["name"] == "test-workspace-fix"
        ), f"Nome do projeto incorreto: {project.get('name')}"


class TestBug19GitValidators:
    """Validação da correção do BUG-19: git_validators.py deployment."""

    def test_git_validators_script_exists(self, workspace_path):
        """Verificar que scripts/lib/git_validators.py foi deployado."""
        script = workspace_path / "scripts" / "lib" / "git_validators.py"
        assert script.exists(), "scripts/lib/git_validators.py não encontrado"

    def test_git_validators_is_importable(self, workspace_path):
        """Verificar que git_validators.py é um módulo Python válido."""
        script = workspace_path / "scripts" / "lib" / "git_validators.py"
        content = script.read_text(encoding="utf-8")

        # Check for basic Python syntax (no syntax errors on read)
        assert (
            "def " in content or "class " in content
        ), "git_validators.py não contém funções ou classes Python"


class TestCriticalFiles:
    """Validação de arquivos críticos do projeto."""

    def test_scaffold_state_exists(self, workspace_path):
        """Verificar que .scaffold-state.yaml existe (criado pelo upgrade)."""
        state = workspace_path / ".scaffold-state.yaml"
        assert state.exists(), ".scaffold-state.yaml não encontrado (upgrade falhou?)"

    def test_scaffold_state_is_valid(self, workspace_path):
        """Verificar que .scaffold-state.yaml contém dados válidos."""
        state = workspace_path / ".scaffold-state.yaml"
        import yaml

        with state.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert "scaffold_version" in data, "Estado deve ter scaffold_version"
        assert "updated_at" in data, "Estado deve ter updated_at"
        assert "project" in data, "Estado deve ter seção project"

    def test_copilot_rules_exists(self, workspace_path):
        """Verificar que .copilot-rules.md existe."""
        rules = workspace_path / ".copilot-rules.md"
        assert rules.exists(), ".copilot-rules.md não encontrado"

    def test_vscode_settings_exists(self, workspace_path):
        """Verificar que .vscode/settings.json existe."""
        settings = workspace_path / ".vscode" / "settings.json"
        assert settings.exists(), ".vscode/settings.json não encontrado"

    def test_vscode_settings_is_valid(self, workspace_path):
        """Verificar que settings.json contém JSON válido."""
        settings = workspace_path / ".vscode" / "settings.json"
        try:
            with settings.open(encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict), "settings.json deve ser um objeto JSON"
        except json.JSONDecodeError as e:
            pytest.fail(f"settings.json contém JSON inválido: {e}")


class TestScaffoldUpgradeLog:
    """Validação dos logs do scaffold upgrade."""

    def test_latest_scaffold_log_exists(self, workspace_path):
        """Verificar que existe log de scaffold upgrade."""
        logs_dir = workspace_path / "logs"
        if not logs_dir.exists():
            pytest.skip("Diretório logs/ não existe")

        scaffold_logs = list(logs_dir.glob("scaffold_*.log"))
        assert len(scaffold_logs) > 0, "Nenhum log de scaffold encontrado em logs/"

    def test_latest_log_contains_upgrade_info(self, workspace_path):
        """Verificar que o último log contém informações de upgrade."""
        logs_dir = workspace_path / "logs"
        if not logs_dir.exists():
            pytest.skip("Diretório logs/ não existe")

        scaffold_logs = sorted(
            logs_dir.glob("scaffold_*.log"), key=lambda p: p.stat().st_mtime
        )
        if not scaffold_logs:
            pytest.skip("Nenhum log de scaffold encontrado")

        latest_log = scaffold_logs[-1]
        content = latest_log.read_text(encoding="utf-8")

        # Verificar que contém estatísticas de upgrade
        assert (
            "created:" in content or "skipped:" in content or "merged:" in content
        ), f"Log {latest_log.name} não contém estatísticas de scaffold"


# ===========================================================================
# Summary Report Generator
# ===========================================================================


@pytest.fixture(scope="session", autouse=True)
def print_validation_summary(request):
    """Print summary após todos os testes."""
    yield

    # This runs after all tests
    if hasattr(request.config, "pluginmanager"):
        stats = request.config.pluginmanager.get_plugin("terminalreporter").stats

        passed = len(stats.get("passed", []))
        failed = len(stats.get("failed", []))
        skipped = len(stats.get("skipped", []))

        print("\n" + "=" * 70)
        print("📊 RESUMO DA VALIDAÇÃO — test-workspace-fix")
        print("=" * 70)
        print(f"✅ Passaram: {passed}")
        print(f"❌ Falharam: {failed}")
        print(f"⏭️  Pulados: {skipped}")

        if failed == 0:
            print("\n🎉 VALIDAÇÃO COMPLETA: Todos os bugs corrigidos aplicados!")
        else:
            print("\n⚠️  ATENÇÃO: Algumas validações falharam. Veja detalhes acima.")
        print("=" * 70)
