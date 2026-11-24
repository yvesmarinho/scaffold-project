"""
Testes para Sprint 3 - Pre-Commit Hook Activation

Bug fix:
- BUG-#4: Pre-commit hook criado mas nunca ativado → agora ativado automaticamente

Tests:
1. test_pre_commit_hook_content_in_constant - Verifica constante _PRE_COMMIT_SECRETS_HOOK
2. test_setup_secrets_security_activates_hook - Verifica ativação automática do hook
3. test_hook_activation_without_git_hooks_dir - Verifica comportamento sem .git/hooks/
4. test_hook_activation_handles_copy_error - Verifica tratamento de erros
"""

import tempfile
from pathlib import Path


def test_pre_commit_hook_content_in_constant():
    """
    Cenário: Verificar que constante _PRE_COMMIT_SECRETS_HOOK existe e tem conteúdo correto.
    Expectativa: Constante deve ser um script bash que valida secrets.
    """
    from scripts.lib import project

    # Verificar que constante existe
    assert hasattr(
        project, "_PRE_COMMIT_SECRETS_HOOK"
    ), "Constante _PRE_COMMIT_SECRETS_HOOK deve existir em project.py"

    content = project._PRE_COMMIT_SECRETS_HOOK

    # Verificar conteúdo básico
    assert (
        "#!/usr/bin/env bash" in content or "#!/bin/bash" in content
    ), "Hook deve ser um script bash"
    assert ".secrets/" in content, "Hook deve mencionar .secrets/ directory"

    # Verificar padrões críticos
    critical_patterns = [".secrets/", ".env"]
    found_patterns = sum(1 for pattern in critical_patterns if pattern in content)
    assert (
        found_patterns >= 1
    ), f"Hook deve validar pelo menos 1 padrão crítico, encontrou {found_patterns}"


def test_setup_secrets_security_activates_hook():
    """
    Cenário: Testar função setup_secrets_security() ativa hook.
    Expectativa: Hook é copiado para .git/hooks/pre-commit com permissões corretas.

    Bug fix: BUG-#4 (P2 - hook nunca ativado)
    """
    from datetime import datetime

    from scripts.lib.config import ProjectConfig
    from scripts.lib.project import setup_secrets_security

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir)
        project_name = "test-project"

        # Criar config (project_path é calculado automaticamente)
        cfg = ProjectConfig(
            project_name=project_name,
            project_title="Test Project",
            description="Test",
            domain="programming",
            language="python",
            github_repo=None,
            shared_dir=Path("/tmp/shared"),
            target_dir=target_dir,
            created_at=datetime.now().isoformat(),
        )

        project_path = cfg.project_path
        project_path.mkdir(parents=True, exist_ok=True)

        # Criar estrutura mínima
        secrets_dir = project_path / ".secrets"
        secrets_dir.mkdir(mode=0o700)

        git_dir = project_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()

        git_hooks_dir = project_path / ".git-hooks"
        git_hooks_dir.mkdir()

        # Criar hook template
        hook_template = git_hooks_dir / "pre-commit.secrets"
        hook_template.write_text("#!/bin/bash\necho 'Validating secrets...'\n")

        # Criar .gitignore
        gitignore = project_path / ".gitignore"
        gitignore.write_text(".secrets/\n")

        # Executar função
        results = setup_secrets_security(cfg)

        # Verificações
        hook_target = project_path / ".git" / "hooks" / "pre-commit"

        assert (
            hook_target.exists()
        ), "Hook deveria estar instalado em .git/hooks/pre-commit"

        # Verificar permissões (deve ser executável)
        perms = hook_target.stat().st_mode & 0o777
        assert perms == 0o755, f"Hook deve ter permissão 755, tem {oct(perms)}"

        # Verificar que results contém ativação
        hook_results = [
            r for r in results if hasattr(r, "status") and r.status == "activated"
        ]
        assert len(hook_results) == 1, "Deve haver 1 resultado de hook ativado"
        assert "instalado" in hook_results[0].message.lower()


def test_hook_activation_without_git_hooks_dir():
    """
    Cenário: Tentar ativar hook sem .git/hooks/ directory.
    Expectativa: Função deve avisar mas não falhar.

    Edge case: projeto sem repositório git inicializado.
    """
    from datetime import datetime

    from scripts.lib.config import ProjectConfig
    from scripts.lib.project import setup_secrets_security

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir)
        project_name = "test-project"

        cfg = ProjectConfig(
            project_name=project_name,
            project_title="Test Project",
            description="Test",
            domain="programming",
            language="python",
            github_repo=None,
            shared_dir=Path("/tmp/shared"),
            target_dir=target_dir,
            created_at=datetime.now().isoformat(),
        )

        project_path = cfg.project_path
        project_path.mkdir(parents=True, exist_ok=True)

        # Criar estrutura mínima SEM .git/
        secrets_dir = project_path / ".secrets"
        secrets_dir.mkdir(mode=0o700)

        git_hooks_dir = project_path / ".git-hooks"
        git_hooks_dir.mkdir()

        hook_template = git_hooks_dir / "pre-commit.secrets"
        hook_template.write_text("#!/bin/bash\necho test\n")

        gitignore = project_path / ".gitignore"
        gitignore.write_text(".secrets/\n")

        # Executar função (não deve falhar)
        results = setup_secrets_security(cfg)

        # Verificar que aviso foi gerado
        hook_results = [
            r for r in results if r.path == hook_template and r.status == "available"
        ]
        assert (
            len(hook_results) == 1
        ), "Deve haver 1 resultado de hook disponível (mas não ativado)"
        assert (
            ".git/hooks/" in hook_results[0].message
            or "sem .git/hooks/" in hook_results[0].message
        )


def test_hook_activation_handles_copy_error():
    """
    Cenário: Simular erro durante cópia do hook.
    Expectativa: Função deve capturar exceção e marcar hook como 'available'.

    Robustez: scaffold não deve falhar se hook não puder ser ativado.
    """
    from datetime import datetime

    from scripts.lib.config import ProjectConfig
    from scripts.lib.project import setup_secrets_security

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir)
        project_name = "test-project"

        cfg = ProjectConfig(
            project_name=project_name,
            project_title="Test Project",
            description="Test",
            domain="programming",
            language="python",
            github_repo=None,
            shared_dir=Path("/tmp/shared"),
            target_dir=target_dir,
            created_at=datetime.now().isoformat(),
        )

        project_path = cfg.project_path
        project_path.mkdir(parents=True, exist_ok=True)

        secrets_dir = project_path / ".secrets"
        secrets_dir.mkdir(mode=0o700)

        # Criar .git/hooks/ mas torná-lo read-only para forçar erro
        git_dir = project_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(mode=0o444)  # read-only

        git_hooks_dir = project_path / ".git-hooks"
        git_hooks_dir.mkdir()

        hook_template = git_hooks_dir / "pre-commit.secrets"
        hook_template.write_text("#!/bin/bash\necho test\n")

        gitignore = project_path / ".gitignore"
        gitignore.write_text(".secrets/\n")

        # Executar função (não deve falhar)
        results = setup_secrets_security(cfg)

        # Deve retornar resultado mas não falhar
        assert len(results) > 0, "Deve retornar resultados mesmo com erro"

        # Verificar que hook foi marcado como 'available' (não 'activated')
        hook_results = [r for r in results if r.path == hook_template]
        assert len(hook_results) == 1, "Deve haver 1 resultado relacionado ao hook"
        assert (
            hook_results[0].status == "available"
        ), f"Hook deveria estar marcado como 'available', está como '{hook_results[0].status}'"
        assert (
            "ativação manual necessária" in hook_results[0].message
            or "Permission denied" in hook_results[0].message
        )
