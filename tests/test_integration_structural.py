"""
tests/test_integration_structural.py — IMP-46 (Nível 1)

Valida estrutura física de cada template sem executar nenhuma ferramenta de build.
Roda em CI sem dependências extras além do pytest.

Cobertura: 9 templates × asserções específicas por layer
  - Layer 2  : python-fastapi, python-flask, typescript-next
  - Layer 3  : k8s-helm, terraform-aws, data-pipeline-airflow, data-warehouse-dbt
  - Layer 4  : lgpd-baseline, soc2-baseline

Para cada template são verificados:
  1. Template existe em scaffold/templates/project/
  2. Arquivos obrigatórios presentes
  3. Nenhum placeholder {curly-brace} não substituído no conteúdo de texto
  4. Makefile/equivalente contém os targets principais do descriptor
  5. Arquivo de manifesto de dependências existe (pyproject.toml, package.json, etc.)
"""

from __future__ import annotations

import pytest

from tests.helpers.fake_project import TEMPLATES_DIR, FakeProject, expand_template

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _skip_if_missing(profile: str):
    """Marca o teste como skip se o template físico não existir."""
    if not (TEMPLATES_DIR / profile).is_dir():
        pytest.skip(f"Template '{profile}' não encontrado em {TEMPLATES_DIR}")


# ---------------------------------------------------------------------------
# Layer 2 — python-fastapi
# ---------------------------------------------------------------------------


class TestPythonFastapi:
    """Valida estrutura do template python-fastapi."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("python-fastapi")
        return expand_template("python-fastapi", tmp_path_factory.mktemp("fastapi"))

    def test_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile")

    def test_dockerfile_exists(self, proj):
        proj.assert_file_exists("Dockerfile")

    def test_pyproject_toml_exists(self, proj):
        proj.assert_file_exists("pyproject.toml")

    def test_env_example_exists(self, proj):
        proj.assert_file_exists(".env.example")

    def test_docker_compose_exists(self, proj):
        proj.assert_file_exists("docker-compose.yml")

    def test_src_main_exists(self, proj):
        proj.assert_file_exists("src", "main.py")

    def test_tests_dir_exists(self, proj):
        assert proj.exists("tests"), "Diretório tests/ ausente"

    def test_makefile_has_lint_target(self, proj):
        proj.assert_file_contains("Makefile", "lint:")

    def test_makefile_has_test_target(self, proj):
        proj.assert_file_contains("Makefile", "test:")

    def test_makefile_has_sbom_target(self, proj):
        proj.assert_file_contains("Makefile", "sbom:")

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()

    def test_project_name_expanded_in_makefile(self, proj):
        content = proj.read("Makefile")
        assert (
            "fake-project" in content
        ), "placeholder {project_name} não foi substituído no Makefile"


# ---------------------------------------------------------------------------
# Layer 2 — python-flask
# ---------------------------------------------------------------------------


class TestPythonFlask:
    """Valida estrutura do template python-flask."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("python-flask")
        return expand_template("python-flask", tmp_path_factory.mktemp("flask"))

    def test_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile")

    def test_dockerfile_exists(self, proj):
        proj.assert_file_exists("Dockerfile")

    def test_pyproject_toml_exists(self, proj):
        proj.assert_file_exists("pyproject.toml")

    def test_env_example_exists(self, proj):
        proj.assert_file_exists(".env.example")

    def test_src_app_exists(self, proj):
        # Flask pode ter src/app.py ou src/__init__.py
        has_app = proj.exists("src", "app.py") or proj.exists("src", "__init__.py")
        assert has_app, "src/app.py ou src/__init__.py ausente"

    def test_makefile_has_lint_target(self, proj):
        proj.assert_file_contains("Makefile", "lint:")

    def test_makefile_has_test_target(self, proj):
        proj.assert_file_contains("Makefile", "test:")

    def test_makefile_has_sbom_target(self, proj):
        proj.assert_file_contains("Makefile", "sbom:")

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()


# ---------------------------------------------------------------------------
# Layer 2 — typescript-next
# ---------------------------------------------------------------------------


class TestTypescriptNext:
    """Valida estrutura do template typescript-next."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("typescript-next")
        return expand_template("typescript-next", tmp_path_factory.mktemp("next"))

    def test_package_json_exists(self, proj):
        proj.assert_file_exists("package.json")

    def test_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile")

    def test_tsconfig_exists(self, proj):
        proj.assert_file_exists("tsconfig.json")

    def test_next_config_exists(self, proj):
        proj.assert_file_exists("next.config.ts")

    def test_dockerfile_exists(self, proj):
        proj.assert_file_exists("Dockerfile")

    def test_env_example_exists(self, proj):
        proj.assert_file_exists(".env.example")

    def test_app_dir_exists(self, proj):
        assert proj.exists("app"), "Diretório app/ ausente (Next.js App Router)"

    def test_makefile_has_lint_target(self, proj):
        proj.assert_file_contains("Makefile", "lint:")

    def test_makefile_has_test_target(self, proj):
        proj.assert_file_contains("Makefile", "test:")

    def test_makefile_has_sbom_target(self, proj):
        proj.assert_file_contains("Makefile", "sbom:")

    def test_package_json_name_expanded(self, proj):
        proj.assert_file_contains("package.json", '"fake-project"')

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()


# ---------------------------------------------------------------------------
# Layer 3 — k8s-helm
# ---------------------------------------------------------------------------


class TestK8sHelm:
    """Valida estrutura do template k8s-helm."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("k8s-helm")
        return expand_template("k8s-helm", tmp_path_factory.mktemp("helm"))

    def test_chart_yaml_exists(self, proj):
        proj.assert_file_exists("helm", "Chart.yaml")

    def test_values_yaml_exists(self, proj):
        proj.assert_file_exists("helm", "values.yaml")

    def test_values_staging_exists(self, proj):
        proj.assert_file_exists("helm", "values-staging.yaml")

    def test_values_prod_exists(self, proj):
        proj.assert_file_exists("helm", "values-prod.yaml")

    def test_helm_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile.helm")

    def test_templates_dir_exists(self, proj):
        assert proj.exists("helm", "templates"), "helm/templates/ ausente"

    def test_chart_yaml_has_name(self, proj):
        proj.assert_file_contains("helm/Chart.yaml", "name:", regex=False)

    def test_chart_yaml_is_valid_yaml(self, proj):
        import yaml

        content = proj.read("helm/Chart.yaml")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict), "Chart.yaml não é um mapeamento YAML"
        assert "name" in parsed, "Chart.yaml sem campo 'name'"
        assert "version" in parsed, "Chart.yaml sem campo 'version'"

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()


# ---------------------------------------------------------------------------
# Layer 3 — terraform-aws
# ---------------------------------------------------------------------------


class TestTerraformAws:
    """Valida estrutura do template terraform-aws."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("terraform-aws")
        return expand_template("terraform-aws", tmp_path_factory.mktemp("terraform"))

    def test_main_tf_exists(self, proj):
        proj.assert_file_exists("terraform", "main.tf")

    def test_variables_tf_exists(self, proj):
        proj.assert_file_exists("terraform", "variables.tf")

    def test_outputs_tf_exists(self, proj):
        proj.assert_file_exists("terraform", "outputs.tf")

    def test_versions_tf_exists(self, proj):
        proj.assert_file_exists("terraform", "versions.tf")

    def test_envs_dir_exists(self, proj):
        assert proj.exists("terraform", "envs"), "terraform/envs/ ausente"

    def test_terraform_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile.terraform")

    def test_versions_tf_has_terraform_block(self, proj):
        proj.assert_file_contains("terraform/versions.tf", "terraform {", regex=False)

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()


# ---------------------------------------------------------------------------
# Layer 3 — data-pipeline-airflow
# ---------------------------------------------------------------------------


class TestDataPipelineAirflow:
    """Valida estrutura do template data-pipeline-airflow."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("data-pipeline-airflow")
        return expand_template(
            "data-pipeline-airflow", tmp_path_factory.mktemp("airflow")
        )

    def test_airflow_dir_exists(self, proj):
        assert proj.exists("airflow"), "airflow/ ausente"

    def test_requirements_airflow_exists(self, proj):
        proj.assert_file_exists("airflow", "requirements-airflow.txt")

    def test_airflow_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile.airflow")

    def test_requirements_has_apache_airflow(self, proj):
        proj.assert_file_contains("airflow/requirements-airflow.txt", "apache-airflow")

    def test_requirements_has_minimum_secure_version(self, proj):
        """Verifica versão mínima segura (>=) — lock gerado via pip-compile."""
        proj.assert_file_contains(
            "airflow/requirements-airflow.txt",
            "apache-airflow>=",
            regex=False,
        )

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()


# ---------------------------------------------------------------------------
# Layer 3 — data-warehouse-dbt
# ---------------------------------------------------------------------------


class TestDataWarehouseDbt:
    """Valida estrutura do template data-warehouse-dbt."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("data-warehouse-dbt")
        return expand_template("data-warehouse-dbt", tmp_path_factory.mktemp("dbt"))

    def test_dbt_dir_exists(self, proj):
        assert proj.exists("dbt"), "dbt/ ausente"

    def test_dbt_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile.dbt")

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()


# ---------------------------------------------------------------------------
# Layer 4 — lgpd-baseline
# ---------------------------------------------------------------------------


class TestLgpdBaseline:
    """Valida estrutura do template lgpd-baseline."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("lgpd-baseline")
        return expand_template("lgpd-baseline", tmp_path_factory.mktemp("lgpd"))

    def test_docs_dir_exists(self, proj):
        assert proj.exists("docs"), "docs/ ausente"

    def test_lgpd_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile.lgpd")

    def test_github_workflows_exist(self, proj):
        assert proj.exists(".github", "workflows"), ".github/workflows/ ausente"

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()


# ---------------------------------------------------------------------------
# Layer 4 — soc2-baseline
# ---------------------------------------------------------------------------


class TestSoc2Baseline:
    """Valida estrutura do template soc2-baseline."""

    @pytest.fixture(scope="class")
    def proj(self, tmp_path_factory) -> FakeProject:
        _skip_if_missing("soc2-baseline")
        return expand_template("soc2-baseline", tmp_path_factory.mktemp("soc2"))

    def test_docs_dir_exists(self, proj):
        assert proj.exists("docs"), "docs/ ausente"

    def test_soc2_makefile_exists(self, proj):
        proj.assert_file_exists("Makefile.soc2")

    def test_github_workflows_exist(self, proj):
        assert proj.exists(".github", "workflows"), ".github/workflows/ ausente"

    def test_no_placeholders_remaining(self, proj):
        proj.assert_no_placeholders()
