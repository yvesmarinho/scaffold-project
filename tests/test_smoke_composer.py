"""
tests/test_smoke_composer.py — IMP-24: Motor de Composição de Perfis.

Cobertura:
  - load_all_descriptors: carrega todos os YAMLs da pasta real
  - resolve_order: core antes de layer2
  - check_conflicts: detecta excludes_with
  - ProfileComposer.compose: perfil válido, conflito, perfil inexistente, rollback
  - Idempotência: second compose retorna only 'skipped'
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

# ---------------------------------------------------------------------------
# Paths relativos ao projeto real (usados apenas em testes de carregamento)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).parent.parent
_DESCRIPTORS_DIR = _PROJECT_ROOT / "scaffold" / "profiles"
_TEMPLATES_DIR = _PROJECT_ROOT / ".github" / "templates"


# ---------------------------------------------------------------------------
# load_all_descriptors
# ---------------------------------------------------------------------------


def test_load_all_descriptors_returns_known_profiles() -> None:
    """Carrega os descritores reais e encontra os perfis conhecidos."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    expected = {
        "devops-programming",
        "python-fastapi",
        "python-flask",
        "typescript-next",
        "k8s-helm",
        "terraform-aws",
        "data-pipeline-airflow",
        "data-warehouse-dbt",
        "lgpd-baseline",
        "soc2-baseline",
    }
    assert expected.issubset(
        set(descriptors.keys())
    ), f"Perfis esperados não encontrados. Carregados: {list(descriptors.keys())}"


def test_load_all_descriptors_have_name_field() -> None:
    """Todos os descritores carregados têm o campo 'name'."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    for name, data in descriptors.items():
        assert data.get("name"), f"Descriptor '{name}' não tem campo 'name'"


# ---------------------------------------------------------------------------
# resolve_order
# ---------------------------------------------------------------------------


def test_resolve_order_core_before_layer2() -> None:
    """devops-programming (core) deve vir antes de typescript-next (layer2)."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    profiles = ["typescript-next", "devops-programming"]
    ordered = resolve_order(profiles, descriptors)

    assert ordered.index("devops-programming") < ordered.index(
        "typescript-next"
    ), f"Esperado core antes de layer2, got: {ordered}"


def test_resolve_order_stable_with_single_profile() -> None:
    """Ordenar uma lista de 1 elemento não lança erro."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    ordered = resolve_order(["typescript-next"], descriptors)
    assert ordered == ["typescript-next"]


def test_resolve_order_unknown_profile_defaults_to_layer2() -> None:
    """Perfil desconhecido recebe prioridade de layer2 (não lança erro)."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    ordered = resolve_order(["devops-programming", "unknown-profile"], descriptors)
    # devops-programming (core=0) deve vir antes de unknown (fallback=1)
    assert ordered.index("devops-programming") < ordered.index("unknown-profile")


# ---------------------------------------------------------------------------
# check_conflicts
# ---------------------------------------------------------------------------


def test_check_conflicts_fastapi_vs_flask() -> None:
    """python-fastapi e python-flask são mutuamente exclusivos."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    conflicts = check_conflicts(["python-fastapi", "python-flask"], descriptors)
    assert len(conflicts) == 1, f"Esperado 1 conflito, got: {conflicts}"
    assert set(conflicts[0]) == {"python-fastapi", "python-flask"}


def test_check_conflicts_no_conflict_for_compatible_profiles() -> None:
    """devops-programming + typescript-next não têm conflito."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    conflicts = check_conflicts(["devops-programming", "typescript-next"], descriptors)
    assert not conflicts, f"Conflito inesperado: {conflicts}"


def test_check_conflicts_empty_list() -> None:
    """Lista vazia não gera conflitos."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    assert check_conflicts([], descriptors) == []


def test_check_conflicts_single_profile() -> None:
    """Um único perfil não gera autoconflito."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    assert check_conflicts(["python-fastapi"], descriptors) == []


# ---------------------------------------------------------------------------
# get_template_entries
# ---------------------------------------------------------------------------


def test_get_template_entries_schema_a_typescript_next() -> None:
    """Schema A (templates_path + templates[]): retorna entradas com src_rel."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    entries = get_template_entries(descriptors["typescript-next"])
    assert len(entries) > 0, "typescript-next deve ter entradas de template"
    for e in entries:
        assert "dest" in e
        assert "src_rel" in e
        assert e["src_rel"].startswith("scaffold/templates/project/typescript-next/")


def test_get_template_entries_schema_b_python_fastapi() -> None:
    """Schema B (generates.files[]): retorna entradas com src_rel."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    entries = get_template_entries(descriptors["python-fastapi"])
    assert len(entries) > 0, "python-fastapi deve ter entradas de template"


# ---------------------------------------------------------------------------
# ProfileComposer.compose — casos de sucesso
# ---------------------------------------------------------------------------


def test_compose_typescript_next_creates_files(make_project_config) -> None:
    """Composição de typescript-next cria arquivos a partir dos templates."""
    cfg = make_project_config("programming", "typescript")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    result = composer.compose(["typescript-next"], cfg)

    assert result.success, f"Composição falhou: {result.errors}"
    assert "typescript-next" in result.applied
    # Algum arquivo deve ter sido criado (templates existem em .github/templates/)
    assert result.created_count > 0, "Nenhum arquivo foi criado"


def test_compose_skips_existing_files(make_project_config) -> None:
    """Segunda composição retorna apenas 'skipped' (idempotente)."""
    cfg = make_project_config("programming", "typescript")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    composer.compose(["typescript-next"], cfg)  # 1ª vez
    result2 = composer.compose(["typescript-next"], cfg)  # 2ª vez

    assert result2.success
    assert (
        result2.created_count == 0
    ), "Segunda composição não deve criar novos arquivos"


# ---------------------------------------------------------------------------
# ProfileComposer.compose — casos de erro
# ---------------------------------------------------------------------------


def test_compose_nonexistent_profile_returns_error(make_project_config) -> None:
    """Perfil inexistente resulta em erro sem modificar o sistema de arquivos."""
    cfg = make_project_config("programming", "typescript")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    result = composer.compose(["profile-que-nao-existe"], cfg)

    assert not result.success
    assert result.applied == []
    assert result.created_count == 0


def test_compose_conflict_returns_error_without_creating_files(
    make_project_config,
) -> None:
    """Conflito detectado antes de qualquer operação — nenhum arquivo deve ser criado."""
    cfg = make_project_config("programming", "python")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    result = composer.compose(["python-fastapi", "python-flask"], cfg)

    assert not result.success
    assert (
        "onflito" in result.errors[0]
    ), f"Mensagem de conflito inesperada: {result.errors}"
    assert (
        result.created_count == 0
    ), "Conflito deve abortar antes de criar qualquer arquivo"
    assert (
        result.rolled_back == []
    ), "Rollback não deve ser acionado para conflito preventivo"


# ---------------------------------------------------------------------------
# ProfileComposer.available_profiles / get_layer
# ---------------------------------------------------------------------------


def test_available_profiles_non_empty() -> None:
    """Composer carrega ao menos os 4 perfis conhecidos."""
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    profiles = composer.available_profiles()
    assert len(profiles) >= 4


def test_get_layer_devops_programming_is_core() -> None:
    """devops-programming deve ter ordem 0 (core)."""
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    assert composer.get_layer("devops-programming") == 0


def test_get_layer_typescript_next_is_layer2() -> None:
    """typescript-next deve ter ordem 1 (layer2)."""
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    assert composer.get_layer("typescript-next") == 1
