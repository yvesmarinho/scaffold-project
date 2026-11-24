"""
tests/test_smoke_imp17.py — IMP-17: Smoke tests para Issue Templates, load-mcp.sh,
generate_tasks() e generate_launch().

Cobertura:
  - .github/ISSUE_TEMPLATE/ contém os 4 arquivos esperados
  - bug_report.md, feature_request.md, improvement.md têm frontmatter YAML válido
  - config.yml desabilita blank_issues
  - copy_speckit() copia ISSUE_TEMPLATE/* para o projeto filho
  - generate_load_mcp() cria scripts/load-mcp.sh com status 'created'
  - load-mcp.sh contém as variáveis corretas por domínio
  - load-mcp.sh é idempotente (skip se já existe)
  - load-mcp.sh nunca exibe o valor do token (SPEC-11)
  - generate_tasks() cria .vscode/tasks.json com todos os targets padrão
  - tasks.json tem versão 2.0.0 e grupos corretos
  - generate_tasks() é idempotente
  - generate_launch() cria .vscode/launch.json por linguagem
  - launch.json tem configurações corretas por linguagem
  - generate_launch() é idempotente
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import project, vscode  # noqa: E402

_PROJECT_ROOT = Path(__file__).parent.parent
_ISSUE_TEMPLATE_DIR = _PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE"


# ---------------------------------------------------------------------------
# Issue Templates — arquivos estáticos no template-base
# ---------------------------------------------------------------------------


def test_issue_template_dir_exists() -> None:
    """Diretório .github/ISSUE_TEMPLATE/ existe no template-base."""
    assert (
        _ISSUE_TEMPLATE_DIR.is_dir()
    ), f".github/ISSUE_TEMPLATE/ não encontrado em {_ISSUE_TEMPLATE_DIR}"


def test_issue_template_has_required_files() -> None:
    """Todos os 4 arquivos esperados existem em .github/ISSUE_TEMPLATE/."""
    expected = {"bug_report.md", "feature_request.md", "improvement.md", "config.yml"}
    present = {f.name for f in _ISSUE_TEMPLATE_DIR.iterdir() if f.is_file()}
    assert expected.issubset(
        present
    ), f"Arquivos esperados ausentes. Presentes: {present}"


def test_bug_report_has_yaml_frontmatter() -> None:
    """bug_report.md começa com frontmatter YAML (---) e tem campo 'name'."""
    content = (_ISSUE_TEMPLATE_DIR / "bug_report.md").read_text(encoding="utf-8")
    assert content.startswith(
        "---"
    ), "bug_report.md deve iniciar com frontmatter YAML '---'"
    assert "name:" in content, "bug_report.md deve ter campo 'name:'"
    assert "labels:" in content, "bug_report.md deve ter campo 'labels:'"


def test_feature_request_has_yaml_frontmatter() -> None:
    """feature_request.md começa com frontmatter YAML e tem campo 'name'."""
    content = (_ISSUE_TEMPLATE_DIR / "feature_request.md").read_text(encoding="utf-8")
    assert content.startswith(
        "---"
    ), "feature_request.md deve iniciar com frontmatter YAML '---'"
    assert "name:" in content, "feature_request.md deve ter campo 'name:'"


def test_improvement_has_yaml_frontmatter() -> None:
    """improvement.md começa com frontmatter YAML e tem campo 'name'."""
    content = (_ISSUE_TEMPLATE_DIR / "improvement.md").read_text(encoding="utf-8")
    assert content.startswith(
        "---"
    ), "improvement.md deve iniciar com frontmatter YAML '---'"
    assert "name:" in content, "improvement.md deve ter campo 'name:'"


def test_config_yml_disables_blank_issues() -> None:
    """config.yml desabilita issues em branco (blank_issues_enabled: false)."""
    content = (_ISSUE_TEMPLATE_DIR / "config.yml").read_text(encoding="utf-8")
    assert (
        "blank_issues_enabled: false" in content
    ), "config.yml deve conter 'blank_issues_enabled: false'"


# ---------------------------------------------------------------------------
# copy_github_templates() — copia ISSUE_TEMPLATE/* para o projeto filho
# ---------------------------------------------------------------------------


def test_copy_speckit_includes_issue_templates(make_project_config) -> None:
    """copy_github_templates() copia os arquivos de ISSUE_TEMPLATE para o projeto filho."""
    cfg = make_project_config("programming", "python")
    project.copy_github_templates(cfg)

    dst_template_dir = cfg.target_dir / ".github" / "ISSUE_TEMPLATE"
    assert (
        dst_template_dir.is_dir()
    ), f".github/ISSUE_TEMPLATE não copiado para {cfg.target_dir}"
    for expected in (
        "bug_report.md",
        "feature_request.md",
        "improvement.md",
        "config.yml",
    ):
        assert (
            dst_template_dir / expected
        ).exists(), f"{expected} não copiado pelo copy_github_templates()"


# ---------------------------------------------------------------------------
# generate_load_mcp() — scripts/load-mcp.sh
# ---------------------------------------------------------------------------


def test_generate_load_mcp_creates_file(make_project_config) -> None:
    """generate_load_mcp() cria scripts/load-mcp.sh com status 'created'."""
    cfg = make_project_config("programming", "python")
    result = project.generate_load_mcp(cfg)
    assert result.status == "created", f"status={result.status!r}: {result.message}"
    assert result.path.exists()


def test_generate_load_mcp_programming_domain(make_project_config) -> None:
    """Domínio programming: load-mcp.sh deve conter GITHUB_PERSONAL_ACCESS_TOKEN."""
    cfg = make_project_config("programming", "python")
    project.generate_load_mcp(cfg)
    content = (cfg.target_dir / "scripts" / "load-mcp.sh").read_text()
    assert (
        "GITHUB_PERSONAL_ACCESS_TOKEN" in content
    ), "programming domain deve validar GITHUB_PERSONAL_ACCESS_TOKEN"


def test_generate_load_mcp_analysis_domain(make_project_config) -> None:
    """Domínio analysis: load-mcp.sh deve conter BRAVE_API_KEY."""
    cfg = make_project_config("analysis", "python")
    project.generate_load_mcp(cfg)
    content = (cfg.target_dir / "scripts" / "load-mcp.sh").read_text()
    assert "BRAVE_API_KEY" in content, "analysis domain deve validar BRAVE_API_KEY"


def test_generate_load_mcp_infrastructure_domain(make_project_config) -> None:
    """Domínio infrastructure: load-mcp.sh deve conter GITHUB_PERSONAL_ACCESS_TOKEN."""
    cfg = make_project_config("infrastructure", "go")
    project.generate_load_mcp(cfg)
    content = (cfg.target_dir / "scripts" / "load-mcp.sh").read_text()
    assert (
        "GITHUB_PERSONAL_ACCESS_TOKEN" in content
    ), "infrastructure domain deve validar GITHUB_PERSONAL_ACCESS_TOKEN"


def test_generate_load_mcp_no_token_value_leak(make_project_config) -> None:
    """SPEC-11: load-mcp.sh não exibe o valor do token — apenas o nome da variável."""
    cfg = make_project_config("programming", "python")
    project.generate_load_mcp(cfg)
    content = (cfg.target_dir / "scripts" / "load-mcp.sh").read_text()
    # O script NÃO deve ter `echo "... $GITHUB_PERSONAL_ACCESS_TOKEN"` (exibindo o valor)
    assert (
        'echo "$GITHUB_PERSONAL_ACCESS_TOKEN"' not in content
    ), "SPEC-11: o valor do token não deve ser exibido via echo"
    assert (
        "echo $GITHUB_PERSONAL_ACCESS_TOKEN" not in content
    ), "SPEC-11: o valor do token não deve ser exibido via echo"


def test_generate_load_mcp_has_shebang_and_strict(make_project_config) -> None:
    """load-mcp.sh deve ter shebang bash e set -euo pipefail."""
    cfg = make_project_config("programming", "python")
    project.generate_load_mcp(cfg)
    content = (cfg.target_dir / "scripts" / "load-mcp.sh").read_text()
    assert content.startswith(
        "#!/usr/bin/env bash"
    ), "Deve ter shebang #!/usr/bin/env bash"
    assert "set -euo pipefail" in content, "Deve ter set -euo pipefail"


def test_generate_load_mcp_is_idempotent(make_project_config) -> None:
    """Segunda chamada retorna status 'skipped' (não sobrescreve customizações)."""
    cfg = make_project_config("programming", "python")
    project.generate_load_mcp(cfg)
    result = project.generate_load_mcp(cfg)
    assert (
        result.status == "skipped"
    ), f"Segunda chamada deve ser idempotente, got status={result.status!r}"


def test_generate_load_mcp_is_executable(make_project_config) -> None:
    """load-mcp.sh deve ter permissão de execução."""
    import os
    import stat

    cfg = make_project_config("programming", "python")
    project.generate_load_mcp(cfg)
    mcp_path = cfg.target_dir / "scripts" / "load-mcp.sh"
    mode = os.stat(mcp_path).st_mode
    assert bool(mode & stat.S_IXUSR), "load-mcp.sh deve ser executável (chmod +x)"


# ---------------------------------------------------------------------------
# generate_tasks() — .vscode/tasks.json
# ---------------------------------------------------------------------------


def test_generate_tasks_creates_file(make_project_config) -> None:
    """generate_tasks() cria .vscode/tasks.json com status 'created'."""
    cfg = make_project_config("programming", "python")
    result = vscode.generate_tasks(cfg)
    assert result.status == "created", f"status={result.status!r}: {result.message}"
    assert result.path.exists()


def test_generate_tasks_valid_json(make_project_config) -> None:
    """tasks.json gerado é JSON válido com chave 'tasks'."""
    cfg = make_project_config("programming", "python")
    vscode.generate_tasks(cfg)
    content = (cfg.target_dir / ".vscode" / "tasks.json").read_text(encoding="utf-8")
    data = json.loads(content)
    assert "tasks" in data, "tasks.json deve ter chave 'tasks'"
    assert data["version"] == "2.0.0", "tasks.json deve ter version '2.0.0'"


def test_generate_tasks_has_standard_labels(make_project_config) -> None:
    """tasks.json contém os labels padrão esperados (SPEC-12)."""
    cfg = make_project_config("programming", "python")
    vscode.generate_tasks(cfg)
    data = json.loads((cfg.target_dir / ".vscode" / "tasks.json").read_text())
    labels = {t["label"] for t in data["tasks"]}
    expected_labels = {
        "make: install-deps",
        "make: dev",
        "make: build",
        "make: test",
        "make: lint",
        "make: format",
        "make: clean",
    }
    assert expected_labels.issubset(
        labels
    ), f"Labels padrão ausentes. Presentes: {labels}"


def test_generate_tasks_test_is_default(make_project_config) -> None:
    """'make: test' deve ser o default do grupo test."""
    cfg = make_project_config("infrastructure", "python")
    vscode.generate_tasks(cfg)
    data = json.loads((cfg.target_dir / ".vscode" / "tasks.json").read_text())
    test_task = next(t for t in data["tasks"] if t["label"] == "make: test")
    assert test_task["group"] == {
        "kind": "test",
        "isDefault": True,
    }, "'make: test' deve ser isDefault no grupo test"


def test_generate_tasks_is_idempotent(make_project_config) -> None:
    """Segunda chamada retorna status 'skipped'."""
    cfg = make_project_config("programming", "typescript")
    vscode.generate_tasks(cfg)
    result = vscode.generate_tasks(cfg)
    assert (
        result.status == "skipped"
    ), f"Segunda chamada deve ser idempotente, got status={result.status!r}"


# ---------------------------------------------------------------------------
# generate_launch() — .vscode/launch.json
# ---------------------------------------------------------------------------


def test_generate_launch_creates_file(make_project_config) -> None:
    """generate_launch() cria .vscode/launch.json com status 'created'."""
    cfg = make_project_config("programming", "python")
    result = vscode.generate_launch(cfg)
    assert result.status == "created", f"status={result.status!r}: {result.message}"
    assert result.path.exists()


def test_generate_launch_python_uses_debugpy(make_project_config) -> None:
    """launch.json para Python deve usar type 'debugpy'."""
    cfg = make_project_config("programming", "python")
    vscode.generate_launch(cfg)
    data = json.loads((cfg.target_dir / ".vscode" / "launch.json").read_text())
    types = {cfg_item["type"] for cfg_item in data["configurations"]}
    assert (
        "debugpy" in types
    ), f"Python: launch.json deve conter type 'debugpy'. Types encontrados: {types}"


def test_generate_launch_python_includes_pytest(make_project_config) -> None:
    """launch.json para Python deve incluir configuração de pytest."""
    cfg = make_project_config("analysis", "python")
    vscode.generate_launch(cfg)
    data = json.loads((cfg.target_dir / ".vscode" / "launch.json").read_text())
    names = {cfg_item["name"] for cfg_item in data["configurations"]}
    assert any(
        "pytest" in name.lower() for name in names
    ), f"Python: deve incluir configuração de pytest. Nomes encontrados: {names}"


def test_generate_launch_typescript_configs(make_project_config) -> None:
    """launch.json para TypeScript deve ter pelo menos 2 configurações."""
    cfg = make_project_config("programming", "typescript")
    vscode.generate_launch(cfg)
    data = json.loads((cfg.target_dir / ".vscode" / "launch.json").read_text())
    assert (
        len(data["configurations"]) >= 2
    ), "TypeScript: launch.json deve ter ao menos 2 configurações"


def test_generate_launch_go_configs(make_project_config) -> None:
    """launch.json para Go deve ter configuração com type 'go'."""
    cfg = make_project_config("infrastructure", "go")
    vscode.generate_launch(cfg)
    data = json.loads((cfg.target_dir / ".vscode" / "launch.json").read_text())
    types = {cfg_item["type"] for cfg_item in data["configurations"]}
    assert (
        "go" in types
    ), f"Go: launch.json deve conter type 'go'. Types encontrados: {types}"


def test_generate_launch_is_idempotent(make_project_config) -> None:
    """Segunda chamada retorna status 'skipped'."""
    cfg = make_project_config("programming", "python")
    vscode.generate_launch(cfg)
    result = vscode.generate_launch(cfg)
    assert (
        result.status == "skipped"
    ), f"Segunda chamada deve ser idempotente, got status={result.status!r}"


# ---------------------------------------------------------------------------
# B.2 — _CODE_WORKSPACE enriquecido com tasks e launch sections
# ---------------------------------------------------------------------------


def test_code_workspace_has_tasks_section(make_project_config) -> None:
    """[nome].code-workspace gerado por create_structure() contém seção 'tasks'."""
    cfg = make_project_config("programming", "python")
    project.create_structure(cfg)
    ws_path = cfg.target_dir / f"{cfg.project_name}.code-workspace"
    assert ws_path.exists(), f"{ws_path.name} não foi gerado por create_structure()"
    data = json.loads(ws_path.read_text(encoding="utf-8"))
    assert "tasks" in data, "code-workspace deve ter seção 'tasks'"
    assert data["tasks"]["version"] == "2.0.0", "tasks.version deve ser '2.0.0'"
    assert (
        len(data["tasks"]["tasks"]) == 7
    ), f"Esperados 7 tasks padrão, encontrados: {len(data['tasks']['tasks'])}"


def test_code_workspace_tasks_has_standard_labels(make_project_config) -> None:
    """code-workspace.tasks contém os mesmos labels padrão do tasks.json."""
    cfg = make_project_config("analysis", "python")
    project.create_structure(cfg)
    ws_path = cfg.target_dir / f"{cfg.project_name}.code-workspace"
    data = json.loads(ws_path.read_text(encoding="utf-8"))
    labels = {t["label"] for t in data["tasks"]["tasks"]}
    expected = {
        "make: install-deps",
        "make: dev",
        "make: build",
        "make: test",
        "make: lint",
        "make: format",
        "make: clean",
    }
    assert (
        expected == labels
    ), f"Labels no workspace diferem do esperado. Encontrados: {labels}"


def test_code_workspace_has_launch_section(make_project_config) -> None:
    """[nome].code-workspace gerado contém seção 'launch' com version 0.2.0."""
    cfg = make_project_config("infrastructure", "go")
    project.create_structure(cfg)
    ws_path = cfg.target_dir / f"{cfg.project_name}.code-workspace"
    data = json.loads(ws_path.read_text(encoding="utf-8"))
    assert "launch" in data, "code-workspace deve ter seção 'launch'"
    assert data["launch"]["version"] == "0.2.0", "launch.version deve ser '0.2.0'"
    assert "configurations" in data["launch"], "launch deve ter chave 'configurations'"


def test_code_workspace_has_enriched_settings(make_project_config) -> None:
    """code-workspace.settings contém rulers, trimTrailingWhitespace, insertFinalNewline."""
    cfg = make_project_config("programming", "typescript")
    project.create_structure(cfg)
    ws_path = cfg.target_dir / f"{cfg.project_name}.code-workspace"
    data = json.loads(ws_path.read_text(encoding="utf-8"))
    settings = data.get("settings", {})
    assert "editor.rulers" in settings, "settings deve ter 'editor.rulers'"
    assert (
        "files.trimTrailingWhitespace" in settings
    ), "settings deve ter 'files.trimTrailingWhitespace'"
    assert (
        "files.insertFinalNewline" in settings
    ), "settings deve ter 'files.insertFinalNewline'"


def test_generate_launch_version_is_correct(make_project_config) -> None:
    """launch.json deve ter versão '0.2.0'."""
    cfg = make_project_config("programming", "python")
    vscode.generate_launch(cfg)
    data = json.loads((cfg.target_dir / ".vscode" / "launch.json").read_text())
    assert (
        data["version"] == "0.2.0"
    ), f"launch.json deve ter version '0.2.0', got: {data.get('version')!r}"
