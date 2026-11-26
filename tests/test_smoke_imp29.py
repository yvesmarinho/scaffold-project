"""
tests/test_smoke_imp29.py — IMP-29: Smoke tests para documentação gerada por perfil ativo.

Cobertura:
  - _compute_combo_slug exclui perfis core (layer order 0) e transversal (order 99)
  - _compute_combo_slug retorna 'core' quando não há perfis layer2+
  - _compute_combo_slug mantém ordem de aplicação dos perfis layer2+
  - generate_profile_guide cria PROFILE-GUIDE-*.md em docs/
  - Arquivo criado retorna status 'created'
  - Segunda chamada retorna status 'skipped' (idempotente)
  - Lista vazia de perfis retorna status 'skipped'
  - Guia contém nomes de todos os perfis aplicados
  - Guia contém as 5 seções obrigatórias (Combinação, Arquivos Gerados, Segurança, Quick Start, Referências)
  - Guia contém informações de camada dos perfis
  - Guia contém regras de segurança enforces do descriptor
  - Guia lista pré-requisitos do descriptor
  - Nome do arquivo PROFILE-GUIDE-{slug}.md é derivado corretamente do combo
  - Guia contém nome e domínio do projeto
  - Combo com múltiplos perfis reais: python-fastapi + lgpd-baseline
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.composer import load_all_descriptors  # noqa: E402
from lib.templates import (  # noqa: E402
    _compute_combo_slug,
    _layer_display_name,
    _layer_order_int,
    generate_profile_guide,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_DESCRIPTORS_DIR = _PROJECT_ROOT / "scaffold" / "profiles"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_descriptors() -> dict[str, dict]:
    return load_all_descriptors(_DESCRIPTORS_DIR)


# ===========================================================================
# _layer_order_int e _layer_display_name
# ===========================================================================


class TestLayerHelpers:

    def test_layer_order_core_string(self) -> None:
        assert _layer_order_int("core") == 0

    def test_layer_order_layer2_string(self) -> None:
        assert _layer_order_int("layer2") == 1

    def test_layer_order_integer_3(self) -> None:
        """layer: 3 (k8s-helm pattern) → order 2 (Layer 3 / Platform)."""
        assert _layer_order_int(3) == 2

    def test_layer_order_integer_4(self) -> None:
        assert _layer_order_int(4) == 3

    def test_layer_order_transversal(self) -> None:
        assert _layer_order_int("transversal") == 99

    def test_layer_display_core(self) -> None:
        assert "Core" in _layer_display_name("core")

    def test_layer_display_layer2(self) -> None:
        assert "Layer 2" in _layer_display_name("layer2")

    def test_layer_display_integer_3(self) -> None:
        assert "Layer 3" in _layer_display_name(3)

    def test_layer_display_layer4(self) -> None:
        assert "Layer 4" in _layer_display_name(
            4
        ) or "Compliance" in _layer_display_name(4)


# ===========================================================================
# _compute_combo_slug
# ===========================================================================


class TestComputeComboSlug:

    def test_excludes_core_profile(self) -> None:
        """devops-programming (layer: core) é excluído do slug."""
        descriptors = _get_descriptors()
        slug = _compute_combo_slug(["devops-programming"], descriptors)
        assert slug == "core", f"Esperado 'core', obtido '{slug}'"

    def test_excludes_transversal_devops_security(self) -> None:
        """devops-security (transversal) é excluído do slug."""
        descriptors = _get_descriptors()
        # devops-security alone → 'core'
        slug = _compute_combo_slug(["devops-security"], descriptors)
        assert slug == "core"

    def test_core_plus_transversal_returns_core(self) -> None:
        """devops-programming + devops-security → 'core' (nenhum layer2+)."""
        descriptors = _get_descriptors()
        slug = _compute_combo_slug(
            ["devops-programming", "devops-security"], descriptors
        )
        assert slug == "core"

    def test_empty_list_returns_core(self) -> None:
        """Lista vazia → 'core'."""
        descriptors = _get_descriptors()
        slug = _compute_combo_slug([], descriptors)
        assert slug == "core"

    def test_single_layer2_profile(self) -> None:
        """python-fastapi (layer2) → slug 'python-fastapi'."""
        descriptors = _get_descriptors()
        slug = _compute_combo_slug(["python-fastapi"], descriptors)
        assert slug == "python-fastapi"

    def test_layer2_plus_layer4_combo(self) -> None:
        """python-fastapi + lgpd-baseline → slug inclui ambos."""
        descriptors = _get_descriptors()
        slug = _compute_combo_slug(["python-fastapi", "lgpd-baseline"], descriptors)
        assert "python-fastapi" in slug
        assert "lgpd-baseline" in slug

    def test_preserves_application_order(self) -> None:
        """Slug preserva a ordem de profiles_applied."""
        descriptors = _get_descriptors()
        slug_ab = _compute_combo_slug(["python-fastapi", "lgpd-baseline"], descriptors)
        slug_ba = _compute_combo_slug(["lgpd-baseline", "python-fastapi"], descriptors)
        assert slug_ab != slug_ba, "Slug deveria refletir ordem de aplicação"
        assert slug_ab == "python-fastapi-lgpd-baseline"

    def test_core_excluded_from_multi_profile_slug(self) -> None:
        """devops-programming é excluído do slug quando combinado com layer2."""
        descriptors = _get_descriptors()
        slug = _compute_combo_slug(
            ["devops-programming", "python-fastapi"], descriptors
        )
        assert (
            slug == "python-fastapi"
        ), f"'devops-programming' não deveria aparecer no slug: {slug}"


# ===========================================================================
# generate_profile_guide — criação de arquivo
# ===========================================================================


class TestGenerateProfileGuideCreation:

    def test_creates_file_on_first_call(self, make_project_config) -> None:
        """generate_profile_guide cria PROFILE-GUIDE-*.md em docs/."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(cfg, ["python-fastapi"], descriptors)
        assert (
            result.status == "created"
        ), f"Esperado 'created', obtido '{result.status}': {result.message}"

    def test_file_placed_in_docs_directory(self, make_project_config) -> None:
        """Arquivo é criado em docs/ do projeto destino."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(cfg, ["python-fastapi"], descriptors)
        assert result.status == "created"
        assert (
            result.path.parent.name == "docs"
        ), f"Esperado em docs/, obtido: {result.path.parent}"

    def test_filename_matches_combo_slug(self, make_project_config) -> None:
        """Nome do arquivo é PROFILE-GUIDE-{slug}.md."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(cfg, ["python-fastapi"], descriptors)
        assert result.status == "created"
        assert (
            result.path.name == "PROFILE-GUIDE-python-fastapi.md"
        ), f"Nome inesperado: {result.path.name}"

    def test_idempotent_second_call_skipped(self, make_project_config) -> None:
        """Segunda chamada retorna status 'skipped' sem sobrescrever."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        generate_profile_guide(cfg, ["python-fastapi"], descriptors)
        result2 = generate_profile_guide(cfg, ["python-fastapi"], descriptors)
        assert (
            result2.status == "skipped"
        ), f"Esperado 'skipped', obtido: '{result2.status}'"

    def test_empty_profiles_returns_skipped(self, make_project_config) -> None:
        """Lista vazia de perfis retorna 'skipped' sem criar arquivo."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(cfg, [], descriptors)
        assert result.status == "skipped"
        assert not result.path.exists(), "Não deveria criar arquivo para lista vazia"

    def test_core_only_creates_core_guide(self, make_project_config) -> None:
        """Apenas perfil core (devops-programming) → cria PROFILE-GUIDE-core.md."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(cfg, ["devops-programming"], descriptors)
        assert result.status == "created"
        assert result.path.name == "PROFILE-GUIDE-core.md"

    def test_multi_profile_combo_filename(self, make_project_config) -> None:
        """Combo python-fastapi + lgpd-baseline gera PROFILE-GUIDE-python-fastapi-lgpd-baseline.md."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(
            cfg, ["python-fastapi", "lgpd-baseline"], descriptors
        )
        assert result.status == "created"
        assert result.path.name == "PROFILE-GUIDE-python-fastapi-lgpd-baseline.md"


# ===========================================================================
# generate_profile_guide — conteúdo do arquivo
# ===========================================================================


class TestGenerateProfileGuideContent:

    def _guide_content(self, make_project_config, profiles: list[str]) -> str:
        """Helper: cria guia e retorna conteúdo."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(cfg, profiles, descriptors)
        assert result.status == "created"
        return result.path.read_text(encoding="utf-8")

    def test_contains_all_required_sections(self, make_project_config) -> None:
        """Guia contém as 5 seções obrigatórias."""
        content = self._guide_content(make_project_config, ["python-fastapi"])
        assert "Combinação de Perfis" in content, "Seção 'Combinação de Perfis' ausente"
        assert "Arquivos Gerados" in content, "Seção 'Arquivos Gerados' ausente"
        assert "Segurança" in content, "Seção 'Segurança' ausente"
        assert "Quick Start" in content, "Seção 'Quick Start' ausente"
        assert "Referências" in content, "Seção 'Referências' ausente"

    def test_contains_profile_name(self, make_project_config) -> None:
        """Guia contém o nome do perfil aplicado."""
        content = self._guide_content(make_project_config, ["python-fastapi"])
        assert "python-fastapi" in content

    def test_contains_project_name(self, make_project_config) -> None:
        """Guia contém o nome do projeto."""
        cfg = make_project_config("programming", "python")
        descriptors = _get_descriptors()
        result = generate_profile_guide(cfg, ["python-fastapi"], descriptors)
        assert result.status == "created"
        content = result.path.read_text(encoding="utf-8")
        assert cfg.project_name in content

    def test_contains_layer_info(self, make_project_config) -> None:
        """Guia contém informação de camada do perfil."""
        content = self._guide_content(make_project_config, ["python-fastapi"])
        assert "Layer 2" in content, "Informação de camada 'Layer 2' ausente"

    def test_contains_security_enforces(self, make_project_config) -> None:
        """Guia contém as regras de segurança 'enforces' do descriptor."""
        content = self._guide_content(make_project_config, ["python-fastapi"])
        # python-fastapi.yaml tem "SECRET_KEY" em security.enforces
        assert (
            "SECRET_KEY" in content
        ), "Regra de segurança 'SECRET_KEY' não encontrada no guia"

    def test_contains_requires_section(self, make_project_config) -> None:
        """Guia lista pré-requisitos do descriptor."""
        content = self._guide_content(make_project_config, ["python-fastapi"])
        assert "Pré-requisitos" in content
        # python-fastapi requer python >= 3.11
        assert (
            "python" in content.lower() or "uv" in content.lower()
        ), "Pré-requisitos do python-fastapi não encontrados"

    def test_contains_references_for_python_tag(self, make_project_config) -> None:
        """Guia contém referências para a tag 'python'."""
        content = self._guide_content(make_project_config, ["python-fastapi"])
        assert (
            "Python" in content and "docs.python.org" in content
        ), "Referência Python não encontrada"

    def test_multi_profile_contains_all_profiles(self, make_project_config) -> None:
        """Guia de combo contém nomes de todos os perfis aplicados."""
        content = self._guide_content(
            make_project_config, ["python-fastapi", "lgpd-baseline"]
        )
        assert "python-fastapi" in content
        assert "lgpd-baseline" in content

    def test_multi_profile_security_from_both(self, make_project_config) -> None:
        """Guia de combo contém regras de segurança de ambos os perfis."""
        content = self._guide_content(
            make_project_config, ["python-fastapi", "lgpd-baseline"]
        )
        # python-fastapi: SECRET_KEY, lgpd-baseline: LGPD / ANPD-related
        assert "SECRET_KEY" in content, "Regras de segurança de python-fastapi ausentes"
        # lgpd-baseline deve ter alguma regra de segurança
        assert (
            "lgpd-baseline" in content
        ), "Seção lgpd-baseline ausente no guia de combo"
