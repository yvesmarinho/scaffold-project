"""
tests/test_smoke_imp26.py — IMP-26: Smoke tests para os perfis Layer 3
data-pipeline-airflow e data-warehouse-dbt.

Cobertura:
  - Descriptors carregados com campos obrigatórios
  - Layer 3 corretamente declarada
  - combines_with contém perfis Layer 2 esperados
  - Todos os templates declarados existem no disco
  - Segurança Airflow: sem credentials hardcoded nos templates
  - Segurança dbt: profiles.yml usa env_var() — sem senha hardcoded
  - DAG template contém padrões obrigatórios (decorator, catchup, retries)
  - dbt_project.yml contém estrutura multi-camada (staging, marts)
  - Makefile targets existem (af-up, dbt-run, etc.)
  - Sem conflitos com perfis Layer 2 compatíveis
  - Composição cria arquivos no projeto alvo
  - Idempotência
  - Ordem de aplicação: layer2 antes de layer3
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.composer import (  # noqa: E402
    ProfileComposer,
    check_conflicts,
    get_template_entries,
    load_all_descriptors,
    resolve_order,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_DESCRIPTORS_DIR = _PROJECT_ROOT / "scaffold" / "profiles"
_AIRFLOW_TPLDIR = (
    _PROJECT_ROOT / "scaffold" / "templates" / "project" / "data-pipeline-airflow"
)
_DBT_TPLDIR = (
    _PROJECT_ROOT / "scaffold" / "templates" / "project" / "data-warehouse-dbt"
)


# ===========================================================================
# data-pipeline-airflow
# ===========================================================================


class TestDataPipelineAirflowDescriptor:

    def test_descriptor_loads(self) -> None:
        """data-pipeline-airflow é carregado por load_all_descriptors."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        assert (
            "data-pipeline-airflow" in descriptors
        ), f"data-pipeline-airflow não encontrado. Carregados: {list(descriptors.keys())}"

    def test_required_fields(self) -> None:
        """Descriptor contém name, layer, version, status, description."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        desc = descriptors["data-pipeline-airflow"]
        for field in ("name", "layer", "version", "status", "description"):
            assert (
                field in desc
            ), f"Campo '{field}' ausente no descriptor data-pipeline-airflow"

    def test_layer_is_3(self) -> None:
        """data-pipeline-airflow deve declarar layer 3."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        layer = descriptors["data-pipeline-airflow"].get("layer")
        assert str(layer) == "3", f"Layer esperada: 3, obtida: {layer!r}"

    def test_combines_with_python_fastapi(self) -> None:
        """combines_with inclui python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["data-pipeline-airflow"].get("combines_with", [])
        assert "python-fastapi" in combines

    def test_combines_with_python_flask(self) -> None:
        """combines_with inclui python-flask."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["data-pipeline-airflow"].get("combines_with", [])
        assert "python-flask" in combines


class TestDataPipelineAirflowTemplates:

    def test_all_declared_templates_exist_on_disk(self) -> None:
        """Todos os templates declarados existem em scaffold/templates/project/data-pipeline-airflow/."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        entries = get_template_entries(descriptors["data-pipeline-airflow"])

        assert len(entries) > 0, "data-pipeline-airflow não tem entradas de template"

        missing = [
            str(_PROJECT_ROOT / e["src_rel"])
            for e in entries
            if not (_PROJECT_ROOT / e["src_rel"]).exists()
        ]
        assert not missing, "Templates ausentes no disco:\n" + "\n".join(missing)

    def test_dag_template_has_dag_decorator(self) -> None:
        """DAG template usa @dag decorator (TaskFlow API)."""
        dag_file = _AIRFLOW_TPLDIR / "airflow" / "dags" / "example_pipeline.py"
        assert dag_file.exists(), "example_pipeline.py não encontrado"
        content = dag_file.read_text()
        assert "@dag" in content, "DAG template deve usar @dag decorator"

    def test_dag_template_has_catchup_false(self) -> None:
        """DAG template deve ter catchup=False para evitar backfill acidental."""
        dag_file = _AIRFLOW_TPLDIR / "airflow" / "dags" / "example_pipeline.py"
        content = dag_file.read_text()
        assert "catchup=False" in content, "DAG template deve declarar catchup=False"

    def test_dag_template_has_retries(self) -> None:
        """DAG template deve declarar retries nos default_args."""
        dag_file = _AIRFLOW_TPLDIR / "airflow" / "dags" / "example_pipeline.py"
        content = dag_file.read_text()
        assert "retries" in content, "DAG template deve declarar retries"

    def test_dag_no_hardcoded_credentials(self) -> None:
        """DAG template não deve conter credenciais hardcoded."""
        dag_file = _AIRFLOW_TPLDIR / "airflow" / "dags" / "example_pipeline.py"
        content = dag_file.read_text().lower()
        forbidden = ["password=", "secret=", "api_key=", "token="]
        found = [kw for kw in forbidden if kw in content and "env_var" not in content]
        assert (
            not found
        ), f"DAG template contém credencial potencialmente hardcoded: {found}"

    def test_docker_compose_no_plaintext_password(self) -> None:
        """docker-compose.airflow.yml não deve expor senhas em plaintext."""
        dc_file = _AIRFLOW_TPLDIR / "airflow" / "docker-compose.airflow.yml"
        assert dc_file.exists(), "docker-compose.airflow.yml não encontrado"
        content = dc_file.read_text()
        # Password must come from secrets or env, not hardcoded
        assert (
            "POSTGRES_PASSWORD_FILE" in content or "secrets:" in content
        ), "docker-compose.airflow.yml deve usar Docker Secrets ou arquivo para credenciais"
        # Must NOT have plain POSTGRES_PASSWORD: somevalue (without _FILE or env_var)
        assert (
            "POSTGRES_PASSWORD: airflow" not in content
        ), "docker-compose.airflow.yml não deve ter senha Postgres em plaintext"

    def test_makefile_has_standard_targets(self) -> None:
        """Makefile.airflow deve conter targets essenciais."""
        makefile = _AIRFLOW_TPLDIR / "Makefile.airflow"
        assert makefile.exists(), "Makefile.airflow não encontrado"
        content = makefile.read_text()
        for target in ("af-up", "af-down", "af-logs", "af-test", "af-trigger"):
            assert target in content, f"Makefile.airflow deve conter target '{target}'"

    def test_env_example_has_no_real_secrets(self) -> None:
        """.env.airflow.example não deve conter tokens ou chaves reais."""
        env_file = _AIRFLOW_TPLDIR / "airflow" / ".env.airflow.example"
        assert env_file.exists(), ".env.airflow.example não encontrado"
        content = env_file.read_text()
        # Must contain placeholder hints, not real-looking keys
        assert (
            "your-" in content or "change-me" in content
        ), ".env.airflow.example deve conter placeholders claros"


class TestDataPipelineAirflowComposer:

    def test_no_conflicts_with_python_fastapi(self) -> None:
        """data-pipeline-airflow não conflita com python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(
            ["python-fastapi", "data-pipeline-airflow"], descriptors
        )
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_no_conflicts_with_python_flask(self) -> None:
        """data-pipeline-airflow não conflita com python-flask."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(
            ["python-flask", "data-pipeline-airflow"], descriptors
        )
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_compose_creates_files(self, make_project_config, tmp_path) -> None:
        """Composição cria arquivos do template no projeto alvo."""
        cfg = make_project_config("analysis", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        result = composer.compose(["data-pipeline-airflow"], cfg)
        assert result.success, f"Composição falhou: {result.errors}"
        assert result.created_count > 0, "Composição não criou nenhum arquivo"

    def test_compose_is_idempotent(self, make_project_config) -> None:
        """Segunda composição retorna created_count == 0 (idempotente)."""
        cfg = make_project_config("analysis", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        composer.compose(["data-pipeline-airflow"], cfg)
        result2 = composer.compose(["data-pipeline-airflow"], cfg)
        assert result2.success
        assert (
            result2.created_count == 0
        ), f"Segunda composição não é idempotente: created={result2.created_count}"

    def test_resolve_order_layer2_before_layer3(self) -> None:
        """python-fastapi (layer2) deve vir antes de data-pipeline-airflow (layer3)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        ordered = resolve_order(
            ["data-pipeline-airflow", "python-fastapi"], descriptors
        )
        assert ordered.index("python-fastapi") < ordered.index(
            "data-pipeline-airflow"
        ), f"layer2 deve preceder layer3. Ordem: {ordered}"


# ===========================================================================
# data-warehouse-dbt
# ===========================================================================


class TestDataWarehouseDbtDescriptor:

    def test_descriptor_loads(self) -> None:
        """data-warehouse-dbt é carregado por load_all_descriptors."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        assert (
            "data-warehouse-dbt" in descriptors
        ), f"data-warehouse-dbt não encontrado. Carregados: {list(descriptors.keys())}"

    def test_required_fields(self) -> None:
        """Descriptor contém name, layer, version, status, description."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        desc = descriptors["data-warehouse-dbt"]
        for field in ("name", "layer", "version", "status", "description"):
            assert (
                field in desc
            ), f"Campo '{field}' ausente no descriptor data-warehouse-dbt"

    def test_layer_is_3(self) -> None:
        """data-warehouse-dbt deve declarar layer 3."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        layer = descriptors["data-warehouse-dbt"].get("layer")
        assert str(layer) == "3", f"Layer esperada: 3, obtida: {layer!r}"

    def test_combines_with_python_fastapi(self) -> None:
        """combines_with inclui python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["data-warehouse-dbt"].get("combines_with", [])
        assert "python-fastapi" in combines

    def test_combines_with_python_flask(self) -> None:
        """combines_with inclui python-flask."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["data-warehouse-dbt"].get("combines_with", [])
        assert "python-flask" in combines


class TestDataWarehouseDbtTemplates:

    def test_all_declared_templates_exist_on_disk(self) -> None:
        """Todos os templates declarados existem em scaffold/templates/project/data-warehouse-dbt/."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        entries = get_template_entries(descriptors["data-warehouse-dbt"])

        assert len(entries) > 0, "data-warehouse-dbt não tem entradas de template"

        missing = [
            str(_PROJECT_ROOT / e["src_rel"])
            for e in entries
            if not (_PROJECT_ROOT / e["src_rel"]).exists()
        ]
        assert not missing, "Templates ausentes no disco:\n" + "\n".join(missing)

    def test_dbt_project_yml_has_multi_layer_structure(self) -> None:
        """dbt_project.yml deve declarar staging e marts."""
        dbt_project = _DBT_TPLDIR / "dbt" / "dbt_project.yml"
        assert dbt_project.exists(), "dbt_project.yml não encontrado"
        content = dbt_project.read_text()
        assert "staging" in content, "dbt_project.yml deve declarar camada staging"
        assert "marts" in content, "dbt_project.yml deve declarar camada marts"

    def test_dbt_project_has_materialization_config(self) -> None:
        """dbt_project.yml deve declarar materialização por camada."""
        content = (_DBT_TPLDIR / "dbt" / "dbt_project.yml").read_text()
        assert "materialized" in content, "dbt_project.yml deve declarar +materialized"

    def test_profiles_no_hardcoded_password(self) -> None:
        """profiles.yml.example usa env_var() — sem senha hardcoded."""
        profiles = _DBT_TPLDIR / "dbt" / "profiles.yml.example"
        assert profiles.exists(), "profiles.yml.example não encontrado"
        content = profiles.read_text()
        assert (
            "env_var(" in content
        ), "profiles.yml.example deve usar env_var() para credentials"
        # Must NOT have a real-looking password value
        assert (
            "password: secret" not in content
        ), "profiles.yml.example contém senha hardcoded"

    def test_staging_model_uses_source_macro(self) -> None:
        """Staging model deve referenciar a fonte com {{ source() }}."""
        stg_sql = _DBT_TPLDIR / "dbt" / "models" / "staging" / "stg_example.sql"
        assert stg_sql.exists(), "stg_example.sql não encontrado"
        content = stg_sql.read_text()
        assert "source(" in content, "Staging model deve usar {{ source() }} ref"

    def test_mart_model_uses_ref_macro(self) -> None:
        """Mart model deve referenciar modelo upstream com {{ ref() }}."""
        mart_sql = _DBT_TPLDIR / "dbt" / "models" / "marts" / "mart_example.sql"
        assert mart_sql.exists(), "mart_example.sql não encontrado"
        content = mart_sql.read_text()
        assert (
            "ref(" in content
        ), "Mart model deve usar {{ ref() }} para referenciar staging"

    def test_staging_yml_has_schema_tests(self) -> None:
        """stg_example.yml deve declarar testes: unique, not_null."""
        stg_yml = _DBT_TPLDIR / "dbt" / "models" / "staging" / "stg_example.yml"
        assert stg_yml.exists(), "stg_example.yml não encontrado"
        content = stg_yml.read_text()
        assert "unique" in content, "stg_example.yml deve ter teste 'unique'"
        assert "not_null" in content, "stg_example.yml deve ter teste 'not_null'"

    def test_macro_generate_schema_name_exists(self) -> None:
        """generate_schema_name.sql deve existir em macros/."""
        macro = _DBT_TPLDIR / "dbt" / "macros" / "generate_schema_name.sql"
        assert macro.exists(), "macros/generate_schema_name.sql não encontrado"
        content = macro.read_text()
        assert (
            "macro generate_schema_name" in content
        ), "Macro deve declarar 'macro generate_schema_name'"

    def test_singular_test_returns_rows_on_failure(self) -> None:
        """Singular test deve retornar rows à falhar (padrão dbt)."""
        test_sql = _DBT_TPLDIR / "dbt" / "tests" / "assert_no_negative_amounts.sql"
        assert test_sql.exists(), "tests/assert_no_negative_amounts.sql não encontrado"
        content = test_sql.read_text()
        assert (
            "select" in content.lower()
        ), "Singular test deve ser uma query SELECT (rows = falha no dbt)"

    def test_makefile_has_standard_targets(self) -> None:
        """Makefile.dbt deve conter targets essenciais."""
        makefile = _DBT_TPLDIR / "Makefile.dbt"
        assert makefile.exists(), "Makefile.dbt não encontrado"
        content = makefile.read_text()
        for target in ("dbt-run", "dbt-test", "dbt-docs", "dbt-deps", "dbt-debug"):
            assert target in content, f"Makefile.dbt deve conter target '{target}'"

    def test_packages_yml_declares_dbt_utils(self) -> None:
        """packages.yml deve declarar dbt_utils."""
        packages = _DBT_TPLDIR / "dbt" / "packages.yml"
        assert packages.exists(), "packages.yml não encontrado"
        content = packages.read_text()
        assert "dbt_utils" in content, "packages.yml deve incluir dbt-labs/dbt_utils"


class TestDataWarehouseDbtComposer:

    def test_no_conflicts_with_python_fastapi(self) -> None:
        """data-warehouse-dbt não conflita com python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(
            ["python-fastapi", "data-warehouse-dbt"], descriptors
        )
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_compose_creates_files(self, make_project_config) -> None:
        """Composição cria arquivos do template no projeto alvo."""
        cfg = make_project_config("analysis", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        result = composer.compose(["data-warehouse-dbt"], cfg)
        assert result.success, f"Composição falhou: {result.errors}"
        assert result.created_count > 0, "Composição não criou nenhum arquivo"

    def test_compose_is_idempotent(self, make_project_config) -> None:
        """Segunda composição retorna created_count == 0 (idempotente)."""
        cfg = make_project_config("analysis", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        composer.compose(["data-warehouse-dbt"], cfg)
        result2 = composer.compose(["data-warehouse-dbt"], cfg)
        assert result2.success
        assert (
            result2.created_count == 0
        ), f"Segunda composição não é idempotente: created={result2.created_count}"

    def test_resolve_order_layer2_before_layer3(self) -> None:
        """python-fastapi (layer2) deve vir antes de data-warehouse-dbt (layer3)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        ordered = resolve_order(["data-warehouse-dbt", "python-fastapi"], descriptors)
        assert ordered.index("python-fastapi") < ordered.index(
            "data-warehouse-dbt"
        ), f"layer2 deve preceder layer3. Ordem: {ordered}"

    def test_no_conflicts_between_both_data_profiles(self) -> None:
        """data-pipeline-airflow e data-warehouse-dbt podem coexistir."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(
            ["python-fastapi", "data-pipeline-airflow", "data-warehouse-dbt"],
            descriptors,
        )
        assert not conflicts, f"Os dois perfis de dados conflitam: {conflicts}"
