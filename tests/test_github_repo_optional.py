"""
Testes para verificar que o sistema funciona corretamente quando github_repo é None.

Ref: Feature solicitada 2026-04-29 — tornar repositório GitHub opcional
     - Quando --repo não for fornecido, github_repo deve ser None
     - Templates devem lidar com None graciosamente
     - Arquivos GitHub-specific não devem ser criados sem repo
     - Placeholders devem mostrar "(não configurado)" em vez de string vazia
"""

from pathlib import Path

from scripts.lib.config import ProjectConfig
from scripts.lib.project import (
    _apply_placeholders,
    generate_github_security_files,
)


def test_apply_placeholders_with_github_repo():
    """Verifica que placeholders são substituídos corretamente quando há repo."""
    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo="https://github.com/org/test-project",
        shared_dir=Path("/tmp/shared"),
        target_dir=Path("/tmp/target"),
        created_at="2026-04-29T10:00:00",
    )

    text = "Repo: {{GITHUB_REPO}}"
    result = _apply_placeholders(text, config)

    assert result == "Repo: https://github.com/org/test-project"
    assert "(não configurado)" not in result


def test_apply_placeholders_without_github_repo():
    """Verifica que placeholders mostram '(não configurado)' quando repo é None."""
    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo=None,  # Repositório não configurado
        shared_dir=Path("/tmp/shared"),
        target_dir=Path("/tmp/target"),
        created_at="2026-04-29T10:00:00",
    )

    text = "Repo: {{GITHUB_REPO}}"
    result = _apply_placeholders(text, config)

    assert result == "Repo: (não configurado)"
    assert "https://" not in result


def test_github_security_files_with_repo(tmp_path):
    """Verifica que todos os arquivos GitHub são criados quando há repo."""
    # ProjectConfig calcula project_path como target_dir/project_name
    # Então passamos target_dir como o pai e configuramos o nome do projeto
    project_dir = tmp_path / "test-project"

    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo="https://github.com/org/test-project",
        shared_dir=Path("/tmp/shared"),
        target_dir=tmp_path,  # Pai do diretório do projeto
        created_at="2026-04-29T10:00:00",
    )

    # Criar diretório do projeto manualmente (generate_github_security_files espera que exista)
    project_dir.mkdir(parents=True, exist_ok=True)

    results = generate_github_security_files(config)

    # Deve criar 5 arquivos quando há repositório GitHub
    assert len(results) == 5

    # Verificar que SECURITY.md foi criado com template GitHub
    security_md = project_dir / "SECURITY.md"
    assert security_md.exists()
    content = security_md.read_text()
    assert "Security tab" in content
    assert "https://github.com/org/test-project" in content

    # Verificar que arquivos .github foram criados
    assert (project_dir / ".github" / "CODEOWNERS").exists()
    assert (project_dir / ".github" / "dependabot.yml").exists()
    assert (project_dir / ".github" / "workflows" / "security-scan.yml").exists()
    assert (project_dir / ".github" / "workflows" / "dependency-review.yml").exists()


def test_github_security_files_without_repo(tmp_path):
    """Verifica que apenas SECURITY.md genérico é criado quando não há repo."""
    # ProjectConfig calcula project_path como target_dir/project_name
    project_dir = tmp_path / "test-project"

    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo=None,  # Repositório não configurado
        shared_dir=Path("/tmp/shared"),
        target_dir=tmp_path,  # Pai do diretório do projeto
        created_at="2026-04-29T10:00:00",
    )

    # Criar diretório do projeto manualmente (generate_github_security_files espera que exista)
    project_dir.mkdir(parents=True, exist_ok=True)

    results = generate_github_security_files(config)

    # Deve criar apenas 1 arquivo quando não há repositório GitHub
    assert len(results) == 1

    # Verificar que SECURITY.md foi criado com template genérico
    security_md = project_dir / "SECURITY.md"
    assert security_md.exists()
    content = security_md.read_text()
    assert "Email" in content  # Template genérico menciona email
    assert "Internal ticketing" in content  # Template genérico menciona ticketing
    assert "Security tab" not in content  # Não deve ter link GitHub
    assert "{{GITHUB_REPO}}" not in content  # Placeholder deve estar substituído

    # Verificar que arquivos .github NÃO foram criados
    assert not (project_dir / ".github" / "CODEOWNERS").exists()
    assert not (project_dir / ".github" / "dependabot.yml").exists()
    assert not (project_dir / ".github" / "workflows" / "security-scan.yml").exists()
    assert not (
        project_dir / ".github" / "workflows" / "dependency-review.yml"
    ).exists()


def test_github_security_files_detect_drift_without_force(tmp_path):
    """Verifica que arquivos gerenciados reportam drift sem sobrescrever."""
    project_dir = tmp_path / "test-project"
    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo="https://github.com/org/test-project",
        shared_dir=Path("/tmp/shared"),
        target_dir=tmp_path,
        created_at="2026-04-29T10:00:00",
    )
    project_dir.mkdir(parents=True, exist_ok=True)

    generate_github_security_files(config)
    (project_dir / ".github" / "CODEOWNERS").write_text(
        "* @custom-owner\n", encoding="utf-8"
    )

    results = generate_github_security_files(config, force=False)

    drift_paths = {result.path.name for result in results if result.status == "drift"}
    assert "CODEOWNERS" in drift_paths
    assert (project_dir / ".github" / "CODEOWNERS").read_text(
        encoding="utf-8"
    ) == "* @custom-owner\n"


def test_github_security_files_refresh_with_force(tmp_path):
    """Verifica que --force atualiza arquivo gerenciado e cria backup."""
    project_dir = tmp_path / "test-project"
    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo="https://github.com/org/test-project",
        shared_dir=Path("/tmp/shared"),
        target_dir=tmp_path,
        created_at="2026-04-29T10:00:00",
    )
    project_dir.mkdir(parents=True, exist_ok=True)

    generate_github_security_files(config)
    codeowners = project_dir / ".github" / "CODEOWNERS"
    codeowners.write_text("* @custom-owner\n", encoding="utf-8")

    results = generate_github_security_files(config, force=True)

    assert any(
        result.path.name == "CODEOWNERS" and result.status == "created"
        for result in results
    )
    assert codeowners.read_text(encoding="utf-8") != "* @custom-owner\n"
    assert (project_dir / ".github" / "CODEOWNERS.backup").exists()


def test_project_config_github_repo_none():
    """Verifica que ProjectConfig aceita github_repo=None."""
    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo=None,
        shared_dir=Path("/tmp/shared"),
        target_dir=Path("/tmp/target"),
        created_at="2026-04-29T10:00:00",
    )

    assert config.github_repo is None
    assert config.project_name == "test-project"


def test_project_config_github_repo_empty_string():
    """Verifica que string vazia é tratada como None (conforme ui.py linha 241)."""
    # Nota: ui.py faz `.strip() or None` para converter string vazia em None
    # Este teste documenta o comportamento esperado
    config = ProjectConfig(
        project_name="test-project",
        project_title="Test Project",
        description="A test project",
        domain="programming",
        language="python",
        github_repo="",  # String vazia
        shared_dir=Path("/tmp/shared"),
        target_dir=Path("/tmp/target"),
        created_at="2026-04-29T10:00:00",
    )

    # String vazia é aceita, mas ui.py deve converter para None antes de criar config
    assert config.github_repo == ""

    # Quando usado em templates, string vazia deve ser tratada como "(não configurado)"
    # porque _apply_placeholders verifica `if config.github_repo` (falsy para "")
    text = "Repo: {{GITHUB_REPO}}"
    result = _apply_placeholders(text, config)
    assert result == "Repo: (não configurado)"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
