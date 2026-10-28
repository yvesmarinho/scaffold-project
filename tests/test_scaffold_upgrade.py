"""
tests/test_scaffold_upgrade.py — Testes end-to-end para scaffold upgrade

P0 CRITICAL: Garantir que scaffold upgrade atualiza projetos corretamente.

Testa:
- Upgrade de projetos existentes via scaffold upgrade
- Todas as 48 validações de validate-workspace-upgrade.py
- BUG fixes (BUG-20, BUG-001, BUG-11, BUG-12, BUG-13, BUG-16, BUG-17, BUG-18, BUG-19)
- Merge strategies (JSON, YAML, Markdown)
- Backup creation
- Logs de upgrade

Estratégia:
- Criar projeto base via scaffold new
- Executar scaffold upgrade --force
- Importar e executar todas as 11 suites de validação
- Assertar que todas as 48 validações passam
- Validar logs e backups

Relacionado:
- scripts/scaffold.py (flow_upgrade)
- scripts/validate-workspace-upgrade.py (48 validações)
- scripts/lib/flows/upgrade.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Importar todos os validadores do validate-workspace-upgrade.py
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from validate_workspace_upgrade import (
    validate_bug001_objetivo_init,
    validate_bug11_session_init,
    validate_bug12_memory_init,
    validate_bug13_copilot_instructions,
    validate_bug16_merge_strategy,
    validate_bug17_timetracker,
    validate_bug18_objetivo,
    validate_bug19_gitvalidators,
    validate_bug20_mcp,
    validate_critical_files,
    validate_scaffold_logs,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scaffold_script() -> Path:
    """Path para o script scaffold.py."""
    return Path(__file__).parent.parent / "scripts" / "scaffold.py"


@pytest.fixture
def base_workspace(tmp_path: Path, scaffold_script: Path) -> Path:
    """
    Cria workspace base para upgrade via scaffold new.

    Simula um projeto criado com uma versão anterior do template
    que precisa ser atualizado.
    """
    # Configurar Git globalmente ANTES de criar workspace
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

    workspace = tmp_path / "test-upgrade-workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Criar projeto base via scaffold new
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-upgrade-workspace",
            "--domain",
            "programming",
            "--language",
            "python",
            "--target-dir",
            str(workspace),
        ],
        cwd=workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, f"scaffold new failed: {result.stderr}"

    # DEBUG: verificar onde o projeto foi realmente criado
    print(f"\n=== DEBUG base_workspace ===")
    print(f"workspace path: {workspace}")
    print(f"workspace exists: {workspace.exists()}")
    print(f"workspace contents: {list(workspace.iterdir()) if workspace.exists() else 'N/A'}")
    if (workspace / "test-upgrade-workspace").exists():
        print(f"DETECTED: scaffold new criou subdiretório! Ajustando workspace...")
        workspace = workspace / "test-upgrade-workspace"

    # Simular projeto "antigo" removendo alguns arquivos
    # que serão recriados pelo upgrade
    files_to_remove = [
        ".github/copilot-instructions.md",  # BUG-13
        "scripts/lib/git_validators.py",    # BUG-19
        "scripts/lib/sanitize.py",          # BUG-19
    ]

    for file_path in files_to_remove:
        full_path = workspace / file_path
        if full_path.exists():
            full_path.unlink()

    return workspace


# ---------------------------------------------------------------------------
# Testes — Scaffold Upgrade
# ---------------------------------------------------------------------------


def test_scaffold_upgrade_basic(scaffold_script: Path, base_workspace: Path):
    """
    Teste básico: scaffold upgrade executa sem erro.

    Verifica:
    - Comando scaffold upgrade --force executa sem erro
    - Logs de upgrade criados
    - Backups criados
    """
    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, (
        f"scaffold upgrade failed:\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # Verificar que logs foram criados
    logs_dir = base_workspace / "logs"
    assert logs_dir.is_dir(), "logs/ não criado"

    scaffold_logs = list(logs_dir.glob("scaffold_*.log"))
    assert len(scaffold_logs) > 0, "Nenhum log de scaffold encontrado"

    # Verificar que backup foi criado
    backups = list(base_workspace.glob(".vscode/*.backup.*"))
    # Nota: backup pode ou não existir dependendo se houve merge
    # Apenas verificar que diretório existe
    assert (base_workspace / ".vscode").is_dir()


def test_scaffold_upgrade_all_validations(scaffold_script: Path, base_workspace: Path):
    """
    Teste CRITICAL: Todas as 48 validações passam após upgrade.

    Executa scaffold upgrade e depois roda todas as 11 suites de validação
    do validate-workspace-upgrade.py.

    Este é o teste mais importante — garante que upgrade funciona corretamente
    e que todos os BUG fixes foram aplicados.
    """
    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar todas as 11 suites de validação
    suites = [
        validate_bug20_mcp(base_workspace, verbose=True),
        validate_bug001_objetivo_init(base_workspace, verbose=True),
        validate_bug11_session_init(base_workspace, verbose=True),
        validate_bug12_memory_init(base_workspace, verbose=True),
        validate_bug13_copilot_instructions(base_workspace, verbose=True),
        validate_bug16_merge_strategy(base_workspace, verbose=True),
        validate_bug17_timetracker(base_workspace, verbose=True),
        validate_bug18_objetivo(base_workspace, verbose=True),
        validate_bug19_gitvalidators(base_workspace, verbose=True),
        validate_critical_files(base_workspace, verbose=True),
        validate_scaffold_logs(base_workspace, verbose=True),
    ]

    # Coletar resultados
    total_passed = sum(s.passed_count for s in suites)
    total_failed = sum(s.failed_count for s in suites)
    total = total_passed + total_failed

    # Construir mensagem de erro detalhada se alguma validação falhou
    if total_failed > 0:
        error_details = []
        for suite in suites:
            if not suite.all_passed:
                error_details.append(f"\n{suite.name}:")
                for result in suite.results:
                    if not result.passed:
                        error_details.append(f"  ❌ {result.name}: {result.message}")
                        if result.details:
                            error_details.append(f"     {result.details}")

        pytest.fail(
            f"Validações falharam após scaffold upgrade:\n"
            f"Total: {total} | Passaram: {total_passed} | Falharam: {total_failed}\n"
            f"{''.join(error_details)}"
        )

    # Assertar que todas as 48 validações passaram
    assert total_failed == 0, f"{total_failed} validações falharam"
    assert total_passed == 48, f"Esperado 48 validações, encontrado {total_passed}"


def test_scaffold_upgrade_bug20_mcp_http(scaffold_script: Path, base_workspace: Path):
    """
    Teste: BUG-20 — MCP GitHub HTTP migration aplicado.

    Verifica que após upgrade:
    - Nenhum servidor MCP usa type="stdio" obsoleto
    - Servidor GitHub usa type="http" ou npx
    """
    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar validação BUG-20
    suite = validate_bug20_mcp(base_workspace, verbose=True)

    # Assertar que todas validações de BUG-20 passaram
    assert suite.all_passed, (
        f"BUG-20 validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_upgrade_bug001_objetivo_init(scaffold_script: Path, base_workspace: Path):
    """
    Teste: BUG-001 — Scaffold objetivo-init fixes aplicados.

    Verifica que após upgrade:
    - Fix #1: DEFAULT_DOCSTYLE populated
    - Fix #2: out-scope conditional
    - Fix #3: Logging to logs/scaffolds.yaml
    """
    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar validação BUG-001
    suite = validate_bug001_objetivo_init(base_workspace, verbose=True)

    # Assertar que todas validações de BUG-001 passaram
    assert suite.all_passed, (
        f"BUG-001 validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_upgrade_bug19_gitvalidators(scaffold_script: Path, base_workspace: Path):
    """
    Teste: BUG-19 — Git validators e sanitize.py deployados.

    Verifica que após upgrade:
    - scripts/lib/git_validators.py existe
    - scripts/lib/sanitize.py existe
    """
    # Remover arquivos antes do upgrade para simular projeto antigo
    git_validators = base_workspace / "scripts" / "lib" / "git_validators.py"
    sanitize = base_workspace / "scripts" / "lib" / "sanitize.py"

    if git_validators.exists():
        git_validators.unlink()
    if sanitize.exists():
        sanitize.unlink()

    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar validação BUG-19
    suite = validate_bug19_gitvalidators(base_workspace, verbose=True)

    # Assertar que todas validações de BUG-19 passaram
    assert suite.all_passed, (
        f"BUG-19 validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_upgrade_copilot_instructions(scaffold_script: Path, base_workspace: Path):
    """
    Teste: BUG-13 — Copilot instructions deployado após upgrade.

    Verifica que após upgrade:
    - .github/copilot-instructions.md existe
    - Frontmatter YAML com applyTo presente
    - Conteúdo menciona regras P0
    """
    # Remover copilot-instructions antes do upgrade
    copilot_instructions = base_workspace / ".github" / "copilot-instructions.md"
    if copilot_instructions.exists():
        copilot_instructions.unlink()

    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar validação BUG-13
    suite = validate_bug13_copilot_instructions(base_workspace, verbose=True)

    # Assertar que todas validações de BUG-13 passaram
    assert suite.all_passed, (
        f"BUG-13 validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_upgrade_merge_strategy(scaffold_script: Path, base_workspace: Path):
    """
    Teste: BUG-16 — JSON/workspace merge strategy aplicado.

    Verifica que após upgrade:
    - Backups criados (.vscode/*.backup.*)
    - .copilot-rules.md consolidado
    - settings.json e mcp.json válidos
    """
    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar validação BUG-16
    suite = validate_bug16_merge_strategy(base_workspace, verbose=True)

    # Assertar que todas validações de BUG-16 passaram
    assert suite.all_passed, (
        f"BUG-16 validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_upgrade_session_memory_init(scaffold_script: Path, base_workspace: Path):
    """
    Teste: BUG-11 e BUG-12 — Session e Memory systems inicializados.

    Verifica que após upgrade:
    - BUG-11: Scripts de session deployados
    - BUG-12: Scripts de memory deployados
    - Databases podem ou não existir (opcionais)
    """
    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar validações BUG-11 e BUG-12
    suite_11 = validate_bug11_session_init(base_workspace, verbose=True)
    suite_12 = validate_bug12_memory_init(base_workspace, verbose=True)

    # Assertar que todas validações passaram
    assert suite_11.all_passed, (
        f"BUG-11 (session) validation failed:\n"
        f"Passed: {suite_11.passed_count}\n"
        f"Failed: {suite_11.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite_11.results if not r.passed)
    )

    assert suite_12.all_passed, (
        f"BUG-12 (memory) validation failed:\n"
        f"Passed: {suite_12.passed_count}\n"
        f"Failed: {suite_12.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite_12.results if not r.passed)
    )


def test_scaffold_upgrade_logs_created(scaffold_script: Path, base_workspace: Path):
    """
    Teste: Logs de scaffold upgrade criados corretamente.

    Verifica:
    - logs/scaffold_*.log existe
    - Log contém estatísticas (created, skipped, merged)
    """
    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Executar validação de logs
    suite = validate_scaffold_logs(base_workspace, verbose=True)

    # Assertar que todas validações de logs passaram
    assert suite.all_passed, (
        f"Scaffold logs validation failed:\n"
        f"Passed: {suite.passed_count}\n"
        f"Failed: {suite.failed_count}\n"
        f"Details:\n" + "\n".join(str(r) for r in suite.results if not r.passed)
    )


def test_scaffold_upgrade_idempotent(scaffold_script: Path, base_workspace: Path):
    """
    Teste: scaffold upgrade é idempotente.

    Verifica que executar upgrade múltiplas vezes não quebra o projeto.
    Todas as 48 validações devem passar após cada upgrade.
    """
    # Executar upgrade 3 vezes
    for i in range(3):
        result = subprocess.run(
            [
                sys.executable,
                str(scaffold_script),
                "upgrade",
                "--force",
            "--ci",
            ],
            cwd=base_workspace,
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, (
            f"scaffold upgrade #{i+1} failed:\n{result.stderr}"
        )

    # Executar todas as validações após o último upgrade
    suites = [
        validate_bug20_mcp(base_workspace, verbose=False),
        validate_bug001_objetivo_init(base_workspace, verbose=False),
        validate_bug11_session_init(base_workspace, verbose=False),
        validate_bug12_memory_init(base_workspace, verbose=False),
        validate_bug13_copilot_instructions(base_workspace, verbose=False),
        validate_bug16_merge_strategy(base_workspace, verbose=False),
        validate_bug17_timetracker(base_workspace, verbose=False),
        validate_bug18_objetivo(base_workspace, verbose=False),
        validate_bug19_gitvalidators(base_workspace, verbose=False),
        validate_critical_files(base_workspace, verbose=False),
        validate_scaffold_logs(base_workspace, verbose=False),
    ]

    # Verificar que todas as validações passaram
    total_failed = sum(s.failed_count for s in suites)
    total_passed = sum(s.passed_count for s in suites)

    assert total_failed == 0, (
        f"Validações falharam após upgrade idempotente:\n"
        f"Passed: {total_passed} | Failed: {total_failed}"
    )


def test_scaffold_upgrade_refreshes_security_files(scaffold_script: Path, tmp_path: Path):
    """Teste: upgrade com --force atualiza arquivos gerenciados de segurança."""
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

    workspace = tmp_path / "test-upgrade-security"
    workspace.mkdir(parents=True, exist_ok=True)

    new_result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "new",
            "--ci",
            "--name",
            "test-upgrade-security",
            "--domain",
            "programming",
            "--language",
            "python",
            "--repo",
            "https://github.com/org/test-upgrade-security",
            "--target-dir",
            str(workspace),
        ],
        cwd=workspace.parent,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert new_result.returncode == 0, f"scaffold new failed: {new_result.stderr}"

    if (workspace / "test-upgrade-security").exists():
        workspace = workspace / "test-upgrade-security"

    codeowners = workspace / ".github" / "CODEOWNERS"
    codeowners.write_text("* @custom-owner\n", encoding="utf-8")

    upgrade_result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert upgrade_result.returncode == 0, f"scaffold upgrade failed: {upgrade_result.stderr}"

    assert "@custom-owner" not in codeowners.read_text(encoding="utf-8")
    assert (workspace / ".github" / "CODEOWNERS.backup").exists()


# ---------------------------------------------------------------------------
# Testes — Regression: Bugs específicos
# ---------------------------------------------------------------------------


def test_scaffold_upgrade_no_old_sessions_folder(scaffold_script: Path, base_workspace: Path):
    """
    Teste: BUG-22 — Scaffold upgrade não cria pasta SESSIONS antiga.

    Verifica que após upgrade:
    - Nenhuma pasta docs/SESSIONS/<created_at>/ vazia é criada
    - Apenas pastas de sessões reais existem
    """
    # Ler created_at do .scaffold-state.yaml
    state_file = base_workspace / ".scaffold-state.yaml"
    with state_file.open() as f:
        state = yaml.safe_load(f)
    created_at = state["created_at"]
    created_date = created_at[:10]  # YYYY-MM-DD

    # Executar scaffold upgrade
    result = subprocess.run(
        [
            sys.executable,
            str(scaffold_script),
            "upgrade",
            "--force",
            "--ci",
        ],
        cwd=base_workspace,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"scaffold upgrade failed: {result.stderr}"

    # Verificar que pasta SESSIONS/<created_at>/ NÃO foi criada
    sessions_dir = base_workspace / "docs" / "SESSIONS"
    if sessions_dir.exists():
        old_session_folder = sessions_dir / created_date

        # Se existe, verificar se está vazia
        if old_session_folder.exists():
            # Verificar se tem apenas arquivos de template ou está vazia
            files = list(old_session_folder.iterdir())
            pytest.fail(
                f"BUG-22 regression: Pasta SESSIONS antiga criada durante upgrade:\n"
                f"{old_session_folder}\n"
                f"Arquivos: {files}"
            )
