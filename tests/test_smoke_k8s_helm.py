"""
tests/test_smoke_k8s_helm.py — IMP-22: Smoke tests para o perfil k8s-helm (Layer 3).

Cobertura:
  - Descriptor carregado com campos obrigatórios
  - Layer 3 corretamente declarada
  - combines_with contém perfis Layer 2 esperados
  - Todos os arquivos de template existem em scaffold/templates/project/k8s-helm/
  - Sem conflitos com perfis Layer 2 compatíveis
  - Composição cria arquivos no projeto alvo
  - Chart.yaml contém apiVersion v2
  - values.yaml contém seções obrigatórias
  - Idempotência da composição
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
_TEMPLATES_DIR = _PROJECT_ROOT / "scaffold" / "templates" / "project" / "k8s-helm"


# ---------------------------------------------------------------------------
# Descriptor — struct validation
# ---------------------------------------------------------------------------


def test_k8s_helm_descriptor_loads() -> None:
    """k8s-helm descriptor carregado pela função load_all_descriptors."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    assert (
        "k8s-helm" in descriptors
    ), f"k8s-helm não encontrado. Carregados: {list(descriptors.keys())}"


def test_k8s_helm_descriptor_has_required_fields() -> None:
    """Descriptor k8s-helm contém campos obrigatórios: name, layer, version, status."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    desc = descriptors["k8s-helm"]
    for field in ("name", "layer", "version", "status", "description"):
        assert field in desc, f"Campo '{field}' ausente no descriptor k8s-helm"


def test_k8s_helm_layer_is_3() -> None:
    """k8s-helm deve declarar layer 3 (não 2 nem core)."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    layer = descriptors["k8s-helm"].get("layer")
    assert str(layer) == "3", f"Layer esperada: 3, obtida: {layer!r}"


def test_k8s_helm_combines_with_python_fastapi() -> None:
    """combines_with deve incluir python-fastapi."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    combines = descriptors["k8s-helm"].get("combines_with", [])
    assert (
        "python-fastapi" in combines
    ), f"python-fastapi não está em combines_with: {combines}"


def test_k8s_helm_combines_with_typescript_next() -> None:
    """combines_with deve incluir typescript-next."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    combines = descriptors["k8s-helm"].get("combines_with", [])
    assert (
        "typescript-next" in combines
    ), f"typescript-next não está em combines_with: {combines}"


# ---------------------------------------------------------------------------
# Templates — existência no disco
# ---------------------------------------------------------------------------


def test_k8s_helm_templates_exist_on_disk() -> None:
    """Todos os arquivos de template declarados no descriptor existem em scaffold/templates/project/k8s-helm/."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    entries = get_template_entries(descriptors["k8s-helm"])

    assert len(entries) > 0, "k8s-helm não tem entradas de template"

    missing = []
    for entry in entries:
        src_path = _PROJECT_ROOT / entry["src_rel"]
        if not src_path.exists():
            missing.append(str(src_path))

    assert not missing, "Templates ausentes no disco:\n" + "\n".join(missing)


def test_k8s_helm_chart_yaml_has_apiv2() -> None:
    """helm/Chart.yaml deve declarar apiVersion: v2."""
    chart_yaml = _TEMPLATES_DIR / "helm" / "Chart.yaml"
    assert chart_yaml.exists(), "helm/Chart.yaml não encontrado"
    content = chart_yaml.read_text()
    assert "apiVersion: v2" in content, "Chart.yaml não declara apiVersion: v2"


def test_k8s_helm_values_yaml_has_security_defaults() -> None:
    """values.yaml deve conter runAsNonRoot e allowPrivilegeEscalation."""
    values_yaml = _TEMPLATES_DIR / "helm" / "values.yaml"
    assert values_yaml.exists(), "helm/values.yaml não encontrado"
    content = values_yaml.read_text()
    assert "runAsNonRoot" in content, "values.yaml sem runAsNonRoot"
    assert (
        "allowPrivilegeEscalation" in content
    ), "values.yaml sem allowPrivilegeEscalation"


# ---------------------------------------------------------------------------
# Compatibilidade — sem conflitos com perfis Layer 2
# ---------------------------------------------------------------------------


def test_k8s_helm_no_conflicts_with_python_fastapi() -> None:
    """k8s-helm + python-fastapi não devem gerar conflito."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    conflicts = check_conflicts(["k8s-helm", "python-fastapi"], descriptors)
    assert not conflicts, f"Conflito inesperado: {conflicts}"


def test_k8s_helm_no_conflicts_with_typescript_next() -> None:
    """k8s-helm + typescript-next não devem gerar conflito."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    conflicts = check_conflicts(["k8s-helm", "typescript-next"], descriptors)
    assert not conflicts, f"Conflito inesperado: {conflicts}"


# ---------------------------------------------------------------------------
# Composição — integração com ProfileComposer
# ---------------------------------------------------------------------------


def test_compose_k8s_helm_creates_files(make_project_config) -> None:
    """Composição de k8s-helm cria arquivos no target dir."""
    cfg = make_project_config("infrastructure", "other")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    result = composer.compose(["k8s-helm"], cfg)

    assert result.success, f"Composição falhou: {result.errors}"
    assert "k8s-helm" in result.applied
    assert result.created_count > 0, "Nenhum arquivo foi criado"


def test_compose_k8s_helm_idempotent(make_project_config) -> None:
    """Segunda composição de k8s-helm não cria arquivos novos (idempotente)."""
    cfg = make_project_config("infrastructure", "other")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    composer.compose(["k8s-helm"], cfg)
    result2 = composer.compose(["k8s-helm"], cfg)

    assert result2.success
    assert (
        result2.created_count == 0
    ), "Segunda composição criou arquivos — não é idempotente"


def test_resolve_order_layer2_before_layer3() -> None:
    """python-fastapi (layer2) deve ser aplicado antes de k8s-helm (layer3)."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    profiles = ["k8s-helm", "python-fastapi"]
    ordered = resolve_order(profiles, descriptors)

    assert ordered.index("python-fastapi") < ordered.index(
        "k8s-helm"
    ), f"Esperado layer2 antes de layer3, got: {ordered}"
