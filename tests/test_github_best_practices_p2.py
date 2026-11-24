"""
tests/test_github_best_practices_p2.py — Testes para GitHub Best Practices P2

Cobertura:
  - copy_github_templates() copia todos arquivos P1 + P2
  - Issue templates YAML são válidos e têm campos esperados
  - Workflow git-validation.yml é válido e tem 5 jobs
  - Pre-commit hook commit-msg é executável e valida commits
  - Script setup-branch-protection.py é executável e tem 3 níveis
  - BADGES.md contém badges esperados
  - Template README tem badges de conformidade
  - Variáveis template são substituídas corretamente
  - Permissões executáveis são aplicadas (chmod 755)
"""

from __future__ import annotations

import stat
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import project  # noqa: E402

_PROJECT_ROOT = Path(__file__).parent.parent
_TEMPLATES_DIR = _PROJECT_ROOT / ".github" / "templates" / "common"


# ---------------------------------------------------------------------------
# Testes de existência dos templates P2
# ---------------------------------------------------------------------------


def test_issue_templates_directory_exists() -> None:
    """Diretório de issue templates existe."""
    issue_template_dir = _TEMPLATES_DIR / "ISSUE_TEMPLATE"
    assert (
        issue_template_dir.is_dir()
    ), f"Issue template dir não encontrado: {issue_template_dir}"


def test_issue_templates_yml_files_exist() -> None:
    """Todos os 5 issue templates YAML existem."""
    issue_template_dir = _TEMPLATES_DIR / "ISSUE_TEMPLATE"
    expected = {
        "bug_report.yml",
        "feature_request.yml",
        "documentation.yml",
        "question.yml",
        "config.yml",
    }
    present = {f.name for f in issue_template_dir.iterdir() if f.is_file()}
    assert expected.issubset(
        present
    ), f"Issue templates faltando. Esperados: {expected}, Presentes: {present}"


def test_workflow_git_validation_exists() -> None:
    """Workflow git-validation.yml existe."""
    workflow = _TEMPLATES_DIR / "workflows" / "git-validation.yml"
    assert workflow.exists(), f"Workflow não encontrado: {workflow}"


def test_git_hook_commit_msg_exists() -> None:
    """Pre-commit hook commit-msg existe."""
    hook = _PROJECT_ROOT / "scripts" / "git-hooks" / "commit-msg"
    assert hook.exists(), f"Hook não encontrado: {hook}"


def test_script_branch_protection_exists() -> None:
    """Script setup-branch-protection.py existe."""
    script = _PROJECT_ROOT / "scripts" / "setup-branch-protection.py"
    assert script.exists(), f"Script não encontrado: {script}"


def test_badges_guide_exists() -> None:
    """Badge guide BADGES.md existe."""
    badges = _TEMPLATES_DIR / "BADGES.md"
    assert badges.exists(), f"Badge guide não encontrado: {badges}"


# ---------------------------------------------------------------------------
# Validação YAML dos issue templates
# ---------------------------------------------------------------------------


def test_bug_report_yml_valid_yaml() -> None:
    """bug_report.yml é YAML válido."""
    path = _TEMPLATES_DIR / "ISSUE_TEMPLATE" / "bug_report.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "bug_report.yml deve ser dict YAML"
    assert "name" in data, "bug_report.yml deve ter campo 'name'"
    assert "description" in data, "bug_report.yml deve ter campo 'description'"
    assert "body" in data, "bug_report.yml deve ter campo 'body'"
    assert isinstance(data["body"], list), "body deve ser lista"


def test_feature_request_yml_valid_yaml() -> None:
    """feature_request.yml é YAML válido."""
    path = _TEMPLATES_DIR / "ISSUE_TEMPLATE" / "feature_request.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "feature_request.yml deve ser dict YAML"
    assert "name" in data
    assert "description" in data
    assert "body" in data


def test_documentation_yml_valid_yaml() -> None:
    """documentation.yml é YAML válido."""
    path = _TEMPLATES_DIR / "ISSUE_TEMPLATE" / "documentation.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert isinstance(data, dict)
    assert "name" in data
    assert "body" in data


def test_question_yml_valid_yaml() -> None:
    """question.yml é YAML válido."""
    path = _TEMPLATES_DIR / "ISSUE_TEMPLATE" / "question.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert isinstance(data, dict)
    assert "name" in data


def test_config_yml_disables_blank_issues() -> None:
    """config.yml desabilita issues em branco."""
    path = _TEMPLATES_DIR / "ISSUE_TEMPLATE" / "config.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert (
        data.get("blank_issues_enabled") is False
    ), "config.yml deve ter blank_issues_enabled: false"


# ---------------------------------------------------------------------------
# Validação do workflow git-validation.yml
# ---------------------------------------------------------------------------


def test_workflow_git_validation_valid_yaml() -> None:
    """git-validation.yml é YAML válido."""
    path = _TEMPLATES_DIR / "workflows" / "git-validation.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    assert isinstance(data, dict), "Workflow deve ser dict YAML"
    assert "name" in data, "Workflow deve ter 'name'"
    assert "jobs" in data, "Workflow deve ter 'jobs'"


def test_workflow_has_five_jobs() -> None:
    """git-validation.yml tem 5 jobs esperados."""
    path = _TEMPLATES_DIR / "workflows" / "git-validation.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    jobs = data.get("jobs", {})
    expected_jobs = {
        "validate-branch",
        "validate-commits",
        "validate-pr-title",
        "pr-size-check",
        "summary",
    }
    assert (
        set(jobs.keys()) == expected_jobs
    ), f"Jobs esperados: {expected_jobs}, encontrados: {set(jobs.keys())}"


def test_workflow_triggers_on_pull_request() -> None:
    """git-validation.yml triggera em pull_request."""
    path = _TEMPLATES_DIR / "workflows" / "git-validation.yml"
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    # YAML interpreta 'on' como True, então verificamos o conteúdo bruto
    # ou a chave True que contém os triggers
    triggers = data.get("on", data.get(True, {}))
    assert (
        "pull_request" in triggers
    ), f"Workflow deve ter trigger 'pull_request'. Triggers: {triggers}"


# ---------------------------------------------------------------------------
# Validação do pre-commit hook
# ---------------------------------------------------------------------------


def test_commit_msg_hook_is_executable() -> None:
    """commit-msg hook tem permissões executáveis."""
    hook = _PROJECT_ROOT / "scripts" / "git-hooks" / "commit-msg"
    mode = hook.stat().st_mode
    is_executable = bool(mode & stat.S_IXUSR)
    assert is_executable, f"Hook deve ser executável: {hook}"


def test_commit_msg_hook_has_shebang() -> None:
    """commit-msg hook começa com shebang."""
    hook = _PROJECT_ROOT / "scripts" / "git-hooks" / "commit-msg"
    content = hook.read_text(encoding="utf-8")
    assert content.startswith("#!/"), "Hook deve começar com shebang"


def test_commit_msg_hook_validates_conventional_commits() -> None:
    """commit-msg hook contém validação de Conventional Commits."""
    hook = _PROJECT_ROOT / "scripts" / "git-hooks" / "commit-msg"
    content = hook.read_text(encoding="utf-8")
    # Verificar padrão regex esperado
    assert (
        "feat|fix|docs|style|refactor|perf|test|chore|ci|build" in content
    ), "Hook deve validar tipos de Conventional Commits"


def test_commit_msg_hook_allows_merge_commits() -> None:
    """commit-msg hook permite mensagens de merge."""
    hook = _PROJECT_ROOT / "scripts" / "git-hooks" / "commit-msg"
    content = hook.read_text(encoding="utf-8")
    assert (
        "Merge" in content or "merge" in content
    ), "Hook deve permitir mensagens de merge"


# ---------------------------------------------------------------------------
# Validação do script setup-branch-protection.py
# ---------------------------------------------------------------------------


def test_setup_branch_protection_is_executable() -> None:
    """setup-branch-protection.py tem permissões executáveis."""
    script = _PROJECT_ROOT / "scripts" / "setup-branch-protection.py"
    mode = script.stat().st_mode
    is_executable = bool(mode & stat.S_IXUSR)
    assert is_executable, f"Script deve ser executável: {script}"


def test_setup_branch_protection_has_shebang() -> None:
    """setup-branch-protection.py começa com shebang."""
    script = _PROJECT_ROOT / "scripts" / "setup-branch-protection.py"
    content = script.read_text(encoding="utf-8")
    assert content.startswith("#!/"), "Script deve começar com shebang"


def test_setup_branch_protection_has_three_levels() -> None:
    """setup-branch-protection.py define 3 níveis de proteção."""
    script = _PROJECT_ROOT / "scripts" / "setup-branch-protection.py"
    content = script.read_text(encoding="utf-8")
    assert "minimum" in content.lower(), "Script deve ter nível 'minimum'"
    assert "recommended" in content.lower(), "Script deve ter nível 'recommended'"
    assert "maximum" in content.lower(), "Script deve ter nível 'maximum'"


def test_setup_branch_protection_uses_github_api() -> None:
    """setup-branch-protection.py usa GitHub API."""
    script = _PROJECT_ROOT / "scripts" / "setup-branch-protection.py"
    content = script.read_text(encoding="utf-8")
    assert "api.github.com" in content, "Script deve usar GitHub API"


def test_setup_branch_protection_supports_dry_run() -> None:
    """setup-branch-protection.py suporta modo dry-run."""
    script = _PROJECT_ROOT / "scripts" / "setup-branch-protection.py"
    content = script.read_text(encoding="utf-8")
    assert (
        "dry" in content.lower() or "dry-run" in content.lower()
    ), "Script deve suportar dry-run"


# ---------------------------------------------------------------------------
# Validação do badge guide
# ---------------------------------------------------------------------------


def test_badges_md_has_conventional_commits_badge() -> None:
    """BADGES.md contém badge de Conventional Commits."""
    badges = _TEMPLATES_DIR / "BADGES.md"
    content = badges.read_text(encoding="utf-8")
    assert (
        "Conventional Commits" in content
    ), "BADGES.md deve conter badge de Conventional Commits"


def test_badges_md_has_github_flow_badge() -> None:
    """BADGES.md contém badge de GitHub Flow."""
    badges = _TEMPLATES_DIR / "BADGES.md"
    content = badges.read_text(encoding="utf-8")
    assert "GitHub Flow" in content, "BADGES.md deve conter badge de GitHub Flow"


def test_badges_md_has_branch_protection_badge() -> None:
    """BADGES.md contém badge de Branch Protection."""
    badges = _TEMPLATES_DIR / "BADGES.md"
    content = badges.read_text(encoding="utf-8")
    assert (
        "Branch Protection" in content
    ), "BADGES.md deve conter badge de Branch Protection"


def test_badges_md_has_shields_io_reference() -> None:
    """BADGES.md referencia shields.io."""
    badges = _TEMPLATES_DIR / "BADGES.md"
    content = badges.read_text(encoding="utf-8")
    assert "shields.io" in content, "BADGES.md deve referenciar shields.io"


# ---------------------------------------------------------------------------
# Testes de integração - copy_github_templates()
# ---------------------------------------------------------------------------


def test_copy_github_templates_copies_all_p1_files(make_project_config) -> None:
    """copy_github_templates() copia todos arquivos P1."""
    cfg = make_project_config("programming", "python")
    project.copy_github_templates(cfg)

    # Verificar P1 files
    assert (cfg.target_dir / "CONTRIBUTING.md").exists(), "CONTRIBUTING.md não copiado"
    assert (
        cfg.target_dir / ".github" / "PULL_REQUEST_TEMPLATE.md"
    ).exists(), "PULL_REQUEST_TEMPLATE.md não copiado"
    assert (
        cfg.target_dir / ".github" / "CODEOWNERS"
    ).exists(), "CODEOWNERS não copiado"
    assert (
        cfg.target_dir / "docs" / "BRANCH_PROTECTION_SETUP.md"
    ).exists(), "BRANCH_PROTECTION_SETUP.md não copiado"


def test_copy_github_templates_copies_all_p2_files(make_project_config) -> None:
    """copy_github_templates() copia todos arquivos P2."""
    cfg = make_project_config("programming", "python")
    project.copy_github_templates(cfg)

    # Verificar P2 issue templates
    issue_dir = cfg.target_dir / ".github" / "ISSUE_TEMPLATE"
    assert (issue_dir / "bug_report.yml").exists(), "bug_report.yml não copiado"
    assert (
        issue_dir / "feature_request.yml"
    ).exists(), "feature_request.yml não copiado"
    assert (issue_dir / "documentation.yml").exists(), "documentation.yml não copiado"
    assert (issue_dir / "question.yml").exists(), "question.yml não copiado"
    assert (issue_dir / "config.yml").exists(), "config.yml não copiado"

    # Verificar workflow
    assert (
        cfg.target_dir / ".github" / "workflows" / "git-validation.yml"
    ).exists(), "git-validation.yml não copiado"

    # Verificar git hook
    assert (
        cfg.target_dir / "scripts" / "git-hooks" / "commit-msg"
    ).exists(), "commit-msg não copiado"

    # Verificar script
    assert (
        cfg.target_dir / "scripts" / "setup-branch-protection.py"
    ).exists(), "setup-branch-protection.py não copiado"

    # Verificar badge guide
    assert (cfg.target_dir / ".github" / "BADGES.md").exists(), "BADGES.md não copiado"


def test_copy_github_templates_substitutes_variables(make_project_config) -> None:
    """copy_github_templates() substitui variáveis template."""
    cfg = make_project_config("programming", "python", project_name="my-test-project")
    project.copy_github_templates(cfg)

    # Verificar substituição em CONTRIBUTING.md
    contributing = cfg.target_dir / "CONTRIBUTING.md"
    content = contributing.read_text(encoding="utf-8")
    assert (
        "my-test-project" in content
    ), "{{ project_name }} não foi substituído em CONTRIBUTING.md"
    assert (
        "{{ project_name }}" not in content
    ), "Variável {{ project_name }} não processada em CONTRIBUTING.md"


def test_copy_github_templates_applies_executable_permissions(
    make_project_config,
) -> None:
    """copy_github_templates() aplica permissões executáveis."""
    cfg = make_project_config("programming", "python")
    project.copy_github_templates(cfg)

    # Verificar hook executável
    hook = cfg.target_dir / "scripts" / "git-hooks" / "commit-msg"
    mode = hook.stat().st_mode
    is_executable = bool(mode & stat.S_IXUSR)
    assert is_executable, "commit-msg deve ser executável após cópia"

    # Verificar script executável
    script = cfg.target_dir / "scripts" / "setup-branch-protection.py"
    mode = script.stat().st_mode
    is_executable = bool(mode & stat.S_IXUSR)
    assert is_executable, "setup-branch-protection.py deve ser executável após cópia"


def test_copy_github_templates_creates_16_files(make_project_config) -> None:
    """copy_github_templates() cria exatamente 16 arquivos (4 P1 + 12 P2)."""
    cfg = make_project_config("programming", "python")
    results = project.copy_github_templates(cfg)

    # Contar resultados
    created_count = sum(1 for r in results if r.status == "created")
    assert created_count == 16, (
        f"Esperado 16 arquivos criados, obteve {created_count}. "
        f"Resultados: {[r.path for r in results]}"
    )


def test_copy_github_templates_substitutes_github_owner(make_project_config) -> None:
    """copy_github_templates() substitui {{ github_owner }}."""
    cfg = make_project_config("programming", "python")
    cfg.github_repo = "testowner/testrepo"
    project.copy_github_templates(cfg)

    # Verificar substituição em BADGES.md se tiver variável
    badges_template = _TEMPLATES_DIR / "BADGES.md"
    badges_template_content = badges_template.read_text(encoding="utf-8")

    badges = cfg.target_dir / ".github" / "BADGES.md"
    content = badges.read_text(encoding="utf-8")

    # Verificar se o template tem variáveis e se foram substituídas
    if "{{ github_owner }}" in badges_template_content:
        assert (
            "testowner" in content
        ), "{{ github_owner }} não foi substituído corretamente"
        assert (
            "{{ github_owner }}" not in content
        ), "{{ github_owner }} permanece no arquivo processado"
    # Se não tem variável no template, apenas verificar que o arquivo foi copiado
    else:
        assert badges.exists(), "BADGES.md não foi copiado"


# ---------------------------------------------------------------------------
# Testes de validação de conteúdo dos templates
# ---------------------------------------------------------------------------


def test_contributing_md_has_workflow_section() -> None:
    """CONTRIBUTING.md tem seção de workflow."""
    contributing = _TEMPLATES_DIR / "CONTRIBUTING.md"
    content = contributing.read_text(encoding="utf-8")
    assert (
        "Workflow" in content or "workflow" in content
    ), "CONTRIBUTING.md deve ter seção de workflow"


def test_contributing_md_has_conventional_commits() -> None:
    """CONTRIBUTING.md menciona Conventional Commits."""
    contributing = _TEMPLATES_DIR / "CONTRIBUTING.md"
    content = contributing.read_text(encoding="utf-8")
    assert (
        "Conventional Commits" in content
    ), "CONTRIBUTING.md deve mencionar Conventional Commits"


def test_pr_template_has_checklist() -> None:
    """PULL_REQUEST_TEMPLATE.md tem checklist."""
    pr_template = _TEMPLATES_DIR / "PULL_REQUEST_TEMPLATE.md"
    content = pr_template.read_text(encoding="utf-8")
    assert (
        "[ ]" in content or "- [ ]" in content
    ), "PULL_REQUEST_TEMPLATE.md deve ter checklist"


def test_codeowners_has_placeholders() -> None:
    """CODEOWNERS tem placeholders para customização."""
    codeowners = _TEMPLATES_DIR / "CODEOWNERS"
    content = codeowners.read_text(encoding="utf-8")
    assert "@" in content, "CODEOWNERS deve ter menções de usuários/times"


# ---------------------------------------------------------------------------
# Teste de regressão - README template
# ---------------------------------------------------------------------------


def test_readme_template_has_badges() -> None:
    """Template README (_README_MD) contém badges de conformidade."""
    # Ler o template diretamente do project.py
    from lib.project import _README_MD

    assert (
        "Conventional Commits" in _README_MD
    ), "README template deve conter badge de Conventional Commits"
    assert (
        "GitHub Flow" in _README_MD
    ), "README template deve conter badge de GitHub Flow"
    assert (
        "Branch Protection" in _README_MD
    ), "README template deve conter badge de Branch Protection"
    assert (
        "shields.io" in _README_MD or "img.shields.io" in _README_MD
    ), "README template deve usar shields.io para badges"
