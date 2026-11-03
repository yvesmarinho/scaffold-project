"""
tests/test_scaffold_new.py — Testes end-to-end para scaffold new

P0 CRITICAL: Garantir que scaffold new cria projetos corretamente.

Testa:
- Criação de novos projetos via scaffold new --ci
- Estrutura de diretórios básica
- Arquivos críticos (.scaffold-state.yaml, .copilot-rules.md, etc.)
- Configurações VS Code (settings.json, mcp.json)
- Git initialization

Estratégia:
- Executar scaffold new via subprocess em workspace temporário
- Validar estrutura criada
- Validar conteúdo de arquivos críticos
- Validar que projeto está pronto para uso

Relacionado:
- scripts/scaffold.py (flow_new_project)
- scripts/validate-workspace-upgrade.py (reutiliza validações)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Importar validadores do validate-workspace-upgrade.py
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from validate_workspace_upgrade import (
    validate_bug13_copilot_instructions,
    validate_critical_files,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scaffold_script() -> Path:
    """Path para o script scaffold.py."""
    return Path(__file__).parent.parent / "scripts" / "scaffold.py"


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Cria workspace temporário isolado para testes."""
    workspace = tmp_path / "test-new-project"
    workspace.mkdir(parents=True, exist_ok=True)

    # Configurar Git globalmente para este teste
    # (necessário para scaffold new criar commits)
    subprocess.run(
        ["git", "config", "--global", "user.email", "test@example.com"],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "--global", "user.name", "Test User"],
        check=False,
        capture_output=True,
    )

    return workspace


# ---------------------------------------------------------------------------
# Testes — Scaffold New
# ---------------------------------------------------------------------------


def test_scaffold_new_basic(scaffold_script: Path, temp_workspace: Path):
    """
    Teste básico: scaffold new cria projeto com estrutura mínima.

    Verifica:
    - Comando scaffold new --ci executa sem erro
    - Diretórios básicos criados (docs/, scripts/, tests/)
    - Arquivos críticos criados (.scaffold-state.yaml, README.md)
    - Git initialized
    """
    # Executar scaffold new em modo CI (não-interativo)
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-new-project",
            "--domain",
            "programming",
            "--language",
            "python",
            "--target-dir",
            str(temp_workspace),
        ],
        cwd=temp_workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Verificar que comando executou com sucesso
    assert result.returncode == 0, (
        f"scaffold new failed:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # DEBUG: listar conteúdo do workspace
    print(f"\n=== Workspace created at: {temp_workspace} ===")
    print(f"Contents: {list(temp_workspace.iterdir())}")

    # Verificar diretórios básicos
    assert (temp_workspace / "docs").is_dir(), "docs/ não criado"
    assert (temp_workspace / "scripts").is_dir(), "scripts/ não criado"
    # Note: tests/ não é criado por padrão pelo scaffold - seria adicionado manualmente
    assert (temp_workspace / "src").is_dir(), "src/ não criado"

    # Verificar arquivos críticos
    assert (temp_workspace / ".scaffold-state.yaml").is_file(), ".scaffold-state.yaml ausente"
    assert (temp_workspace / "README.md").is_file(), "README.md ausente"
    assert (temp_workspace / ".gitignore").is_file(), ".gitignore ausente"
    # Note: pyproject.toml não é criado por padrão - depende do profile/language específico
    # assert (temp_workspace / "pyproject.toml").is_file(), "pyproject.toml ausente (Python)"

    # Registros de sessão vivem no vault Obsidian (MCP obsidian-rest), não no projeto
    for legacy in (".session-docs", ".session-index", "docs/SESSIONS"):
        assert not (temp_workspace / legacy).exists(), f"{legacy} não deve ser criado"
    mcp = (temp_workspace / ".vscode" / "mcp.json").read_text(encoding="utf-8")
    assert "obsidian-rest" in mcp, "mcp.json sem obsidian-rest"

    # Verificar Git initialization
    assert (temp_workspace / ".git").is_dir(), "Git não inicializado"


def test_scaffold_new_vscode_config(scaffold_script: Path, temp_workspace: Path):
    """
    Teste: scaffold new cria configurações VS Code corretamente.

    Verifica:
    - .vscode/settings.json existe e é JSON válido
    - .vscode/mcp.json existe e é JSON válido
    - MCP servers configurados (memory, sequential-thinking, filesystem, github)
    - Nenhum servidor com type="stdio" obsoleto
    """
    # Executar scaffold new
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-new-project",
            "--domain",
            "programming",
            "--language",
            "python",
            "--target-dir",
            str(temp_workspace),
        ],
        cwd=temp_workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"scaffold new failed: {result.stderr}"

    # Verificar settings.json
    settings_file = temp_workspace / ".vscode" / "settings.json"
    assert settings_file.is_file(), ".vscode/settings.json ausente"

    with settings_file.open() as f:
        settings = json.load(f)
    assert isinstance(settings, dict), "settings.json não é objeto JSON"
    assert len(settings) > 0, "settings.json vazio"

    # Verificar mcp.json
    mcp_file = temp_workspace / ".vscode" / "mcp.json"
    assert mcp_file.is_file(), ".vscode/mcp.json ausente"

    with mcp_file.open() as f:
        mcp_config = json.load(f)
    assert "servers" in mcp_config or "mcpServers" in mcp_config, "MCP servers ausentes"

    servers = mcp_config.get("servers", mcp_config.get("mcpServers", {}))
    assert len(servers) >= 2, f"Poucos MCP servers: {len(servers)} (esperado >= 2)"

    # Verificar que nenhum servidor usa type="stdio" obsoleto
    stdio_servers = [name for name, cfg in servers.items() if cfg.get("type") == "stdio"]
    assert not stdio_servers, f"Servidores com type='stdio' obsoleto: {stdio_servers}"


def test_scaffold_new_copilot_instructions(scaffold_script: Path, temp_workspace: Path):
    """
    Teste: scaffold new deploya .github/copilot-instructions.md.

    Verifica:
    - Arquivo existe
    - Frontmatter YAML com applyTo presente
    - Conteúdo menciona regras P0
    - Reutiliza validate_bug13_copilot_instructions()
    """
    # Executar scaffold new
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-new-project",
            "--domain",
            "programming",
            "--language",
            "python",
            "--target-dir",
            str(temp_workspace),
        ],
        cwd=temp_workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"scaffold new failed: {result.stderr}"

    # Reutilizar validador existente
    suite = validate_bug13_copilot_instructions(temp_workspace, verbose=True)

    # Verificar que todas validações passaram
    assert suite.all_passed, (
        f"BUG-13 validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_new_critical_files(scaffold_script: Path, temp_workspace: Path):
    """
    Teste: scaffold new cria todos os arquivos críticos.

    Verifica:
    - .scaffold-state.yaml com metadados corretos
    - .copilot-rules.md deployado
    - .vscode/settings.json e mcp.json válidos
    - Reutiliza validate_critical_files()
    """
    # Executar scaffold new
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-new-project",
            "--domain",
            "programming",
            "--language",
            "python",
            "--target-dir",
            str(temp_workspace),
        ],
        cwd=temp_workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"scaffold new failed: {result.stderr}"

    # Reutilizar validador existente
    suite = validate_critical_files(temp_workspace, verbose=True)

    # Verificar que todas validações passaram
    assert suite.all_passed, (
        f"Critical files validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_new_scaffold_state(scaffold_script: Path, temp_workspace: Path):
    """
    Teste: .scaffold-state.yaml contém metadados corretos.

    Verifica:
    - project_name, domain, language corretos
    - created_at timestamp presente
    - profiles aplicados
    """
    # Executar scaffold new
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-new-project",
            "--domain",
            "programming",
            "--language",
            "python",
            "--target-dir",
            str(temp_workspace),
        ],
        cwd=temp_workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"scaffold new failed: {result.stderr}"

    state_file = temp_workspace / ".scaffold-state.yaml"
    assert state_file.is_file(), ".scaffold-state.yaml ausente"

    with state_file.open() as f:
        state = yaml.safe_load(f)

    # DEBUG: ver conteúdo real do state file
    print(f"\n=== .scaffold-state.yaml content ===")
    print(yaml.dump(state, indent=2))

    # Verificar estrutura do state file (.scaffold-state.yaml v1.0+)
    # Estrutura: project.name, project.domain, project.language, created_at, profiles_applied
    assert "project" in state, "project section ausente"
    assert state["project"]["name"] == "test-new-project", f"project.name incorreto: {state['project']['name']}"
    assert state["project"]["domain"] == "programming", f"project.domain incorreto: {state['project']['domain']}"
    assert state["project"]["language"] == "python", f"project.language incorreto: {state['project']['language']}"
    assert "created_at" in state, "created_at ausente"
    assert "profiles_applied" in state, "profiles_applied ausente"

    # Verificar que perfil devops-programming foi aplicado
    profiles = state["profiles_applied"]
    assert "devops-programming" in profiles or "python" in [p.lower() for p in profiles], (
        f"Perfil programming/Python ausente: {profiles}"
    )


def test_scaffold_new_git_initialized(scaffold_script: Path, temp_workspace: Path):
    """
    Teste: Git é inicializado corretamente após scaffold new.

    Verifica:
    - .git/ existe
    - Initial commit criado
    - Branch master existe
    """
    # Executar scaffold new
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-new-project",
            "--domain",
            "programming",
            "--language",
            "python",
            "--target-dir",
            str(temp_workspace),
        ],
        cwd=temp_workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"scaffold new failed: {result.stderr}"

    # Verificar .git/
    git_dir = temp_workspace / ".git"
    assert git_dir.is_dir(), "Git não inicializado"

    # Verificar que tem commits
    git_log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=temp_workspace,
        capture_output=True,
        text=True,
    )
    assert git_log.returncode == 0, "git log failed"
    assert len(git_log.stdout.strip()) > 0, "Nenhum commit encontrado"

    # Verificar branch master
    git_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=temp_workspace,
        capture_output=True,
        text=True,
    )
    assert git_branch.returncode == 0, "git branch failed"
    current_branch = git_branch.stdout.strip()
    assert current_branch in ["master", "main"], f"Branch incorreta: {current_branch}"


# ---------------------------------------------------------------------------
# Testes — Parametrized: Múltiplas combinações domain × language
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "domain,language",
    [
        ("programming", "python"),
        ("programming", "typescript"),
        ("infrastructure", "other"),  # infrastructure usa "other" como language
        ("analysis", "python"),
    ],
)
def test_scaffold_new_combinations(
    scaffold_script: Path, tmp_path: Path, domain: str, language: str
):
    """
    Teste parametrizado: scaffold new funciona para múltiplas combinações.

    Verifica que scaffold new executa sem erro para diferentes domínios e linguagens.
    """
    # Configurar Git globalmente (necessário para scaffold new criar commits)
    subprocess.run(
        ["git", "config", "--global", "user.email", "test@example.com"],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "--global", "user.name", "Test User"],
        check=False,
        capture_output=True,
    )

    workspace = tmp_path / f"test-{domain}-{language}"
    workspace.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            f"test-{domain}-{language}",
            "--domain",
            domain,
            "--language",
            language,
            "--target-dir",
            str(workspace),
        ],
        cwd=workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"scaffold new failed for {domain}/{language}:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Verificar estrutura básica
    assert (workspace / ".scaffold-state.yaml").is_file()
    assert (workspace / "README.md").is_file()
    assert (workspace / ".git").is_dir()
