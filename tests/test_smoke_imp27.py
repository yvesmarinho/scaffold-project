"""
tests/test_smoke_imp27.py — IMP-27: Smoke tests para os perfis Layer 4
lgpd-baseline e soc2-baseline.

Cobertura:
  - Descriptors carregados com campos obrigatórios
  - Layer 4 corretamente declarada
  - combines_with contém perfis de compliance esperados
  - Campo compliance com standard/authority declarado
  - Todos os templates declarados existem no disco
  - lgpd-baseline: DATA-MAPPING.md contém campos LGPD obrigatórios (bases legais, retenção)
  - lgpd-baseline: INCIDENT-RESPONSE.md referencia ANPD e Art. 48
  - lgpd-baseline: secret-scan.yml usa Gitleaks e TruffleHog
  - lgpd-baseline: data-subject-request.py expõe ações (export, delete, anonymize)
  - soc2-baseline: SECURITY-POLICY.md cobre critérios TSC (CC6, CC7, CC8)
  - soc2-baseline: RISK-ASSESSMENT.md segue metodologia de risco
  - soc2-baseline: static-analysis.yml usa CodeQL + Bandit + Trivy
  - soc2-baseline: Makefile.soc2 tem targets obrigatórios
  - Sem conflitos entre lgpd-baseline e soc2-baseline
  - Composição cria arquivos no projeto alvo
  - Idempotência
  - Ordem de aplicação: layer2 antes de layer4, layer3 antes de layer4
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
_DESCRIPTORS_DIR = _PROJECT_ROOT / "profile-descriptors"
_LGPD_TPLDIR = _PROJECT_ROOT / ".github" / "templates" / "lgpd-baseline"
_SOC2_TPLDIR = _PROJECT_ROOT / ".github" / "templates" / "soc2-baseline"


# ===========================================================================
# lgpd-baseline
# ===========================================================================


class TestLgpdBaselineDescriptor:

    def test_descriptor_loads(self) -> None:
        """lgpd-baseline é carregado por load_all_descriptors."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        assert (
            "lgpd-baseline" in descriptors
        ), f"lgpd-baseline não encontrado. Carregados: {list(descriptors.keys())}"

    def test_required_fields(self) -> None:
        """Descriptor contém name, layer, version, status, description."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        desc = descriptors["lgpd-baseline"]
        for field in ("name", "layer", "version", "status", "description"):
            assert field in desc, f"Campo '{field}' ausente no descriptor lgpd-baseline"

    def test_layer_is_4(self) -> None:
        """lgpd-baseline deve declarar layer 4."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        layer = descriptors["lgpd-baseline"].get("layer")
        assert str(layer) == "4", f"Layer esperada: 4, obtida: {layer!r}"

    def test_compliance_field_declared(self) -> None:
        """lgpd-baseline deve declarar campo compliance com standard e authority."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        compliance = descriptors["lgpd-baseline"].get("compliance", {})
        assert "standard" in compliance, "Campo compliance.standard ausente"
        assert "authority" in compliance, "Campo compliance.authority ausente"

    def test_combines_with_python_fastapi(self) -> None:
        """combines_with inclui python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["lgpd-baseline"].get("combines_with", [])
        assert "python-fastapi" in combines

    def test_combines_with_soc2_baseline(self) -> None:
        """combines_with inclui soc2-baseline (perfis Layer 4 podem coexistir)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["lgpd-baseline"].get("combines_with", [])
        assert "soc2-baseline" in combines

    def test_combines_with_terraform_aws(self) -> None:
        """combines_with inclui terraform-aws (compliance sobre infra)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["lgpd-baseline"].get("combines_with", [])
        assert "terraform-aws" in combines


class TestLgpdBaselineTemplates:

    def test_all_declared_templates_exist_on_disk(self) -> None:
        """Todos os templates declarados existem em .github/templates/lgpd-baseline/."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        entries = get_template_entries(descriptors["lgpd-baseline"])

        assert len(entries) > 0, "lgpd-baseline não tem entradas de template"

        missing = [
            str(_PROJECT_ROOT / e["src_rel"])
            for e in entries
            if not (_PROJECT_ROOT / e["src_rel"]).exists()
        ]
        assert not missing, "Templates ausentes no disco:\n" + "\n".join(missing)

    def test_data_mapping_has_base_legal_section(self) -> None:
        """DATA-MAPPING.md contém seção de bases legais (Art. 7º)."""
        content = (_LGPD_TPLDIR / "docs" / "lgpd" / "DATA-MAPPING.md").read_text()
        assert (
            "Base Legal" in content or "base legal" in content.lower()
        ), "DATA-MAPPING.md não tem seção de bases legais"

    def test_data_mapping_references_article_37(self) -> None:
        """DATA-MAPPING.md referencia o Art. 37 (obrigatoriedade do registro)."""
        content = (_LGPD_TPLDIR / "docs" / "lgpd" / "DATA-MAPPING.md").read_text()
        assert (
            "Art. 37" in content or "37" in content
        ), "DATA-MAPPING.md não referencia o Art. 37 da LGPD"

    def test_incident_response_references_anpd(self) -> None:
        """INCIDENT-RESPONSE.md menciona a ANPD."""
        content = (_LGPD_TPLDIR / "docs" / "lgpd" / "INCIDENT-RESPONSE.md").read_text()
        assert "ANPD" in content, "INCIDENT-RESPONSE.md não menciona a ANPD"

    def test_incident_response_has_72h_deadline(self) -> None:
        """INCIDENT-RESPONSE.md menciona prazo de 72 horas para notificação."""
        content = (_LGPD_TPLDIR / "docs" / "lgpd" / "INCIDENT-RESPONSE.md").read_text()
        assert (
            "72" in content
        ), "INCIDENT-RESPONSE.md não menciona o prazo de 72h para notificação"

    def test_secret_scan_uses_gitleaks(self) -> None:
        """secret-scan.yml usa Gitleaks para detecção de segredos."""
        content = (
            _LGPD_TPLDIR / ".github" / "workflows" / "secret-scan.yml"
        ).read_text()
        assert "gitleaks" in content.lower(), "secret-scan.yml não usa Gitleaks"

    def test_secret_scan_uses_trufflehog(self) -> None:
        """secret-scan.yml usa TruffleHog como scanner complementar."""
        content = (
            _LGPD_TPLDIR / ".github" / "workflows" / "secret-scan.yml"
        ).read_text()
        assert "trufflehog" in content.lower(), "secret-scan.yml não usa TruffleHog"

    def test_dsar_script_has_export_action(self) -> None:
        """data-subject-request.py expõe action 'export' (Art. 18, I/II)."""
        content = (
            _LGPD_TPLDIR / "scripts" / "lgpd" / "data-subject-request.py"
        ).read_text()
        assert "export" in content, "DSAR script não tem ação 'export'"

    def test_dsar_script_has_delete_action(self) -> None:
        """data-subject-request.py expõe action 'delete' (Art. 18, VI)."""
        content = (
            _LGPD_TPLDIR / "scripts" / "lgpd" / "data-subject-request.py"
        ).read_text()
        assert "delete" in content, "DSAR script não tem ação 'delete'"

    def test_dsar_script_has_anonymize_action(self) -> None:
        """data-subject-request.py expõe action 'anonymize' (Art. 12)."""
        content = (
            _LGPD_TPLDIR / "scripts" / "lgpd" / "data-subject-request.py"
        ).read_text()
        assert "anonymize" in content, "DSAR script não tem ação 'anonymize'"

    def test_dsar_script_no_hardcoded_credentials(self) -> None:
        """data-subject-request.py não contém credenciais hardcoded."""
        content = (
            _LGPD_TPLDIR / "scripts" / "lgpd" / "data-subject-request.py"
        ).read_text()
        # Não deve ter senhas/tokens hardcoded — acesso é via variável de ambiente
        import re

        hardcoded_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
        ]
        for pattern in hardcoded_patterns:
            assert not re.search(
                pattern, content, re.IGNORECASE
            ), f"Possível credencial hardcoded (padrão: {pattern!r})"

    def test_makefile_lgpd_has_standard_targets(self) -> None:
        """Makefile.lgpd contém targets obrigatórios."""
        content = (_LGPD_TPLDIR / "Makefile.lgpd").read_text()
        required = [
            "lgpd-check",
            "lgpd-scan-secrets",
            "lgpd-scan-deps",
            "lgpd-docs-check",
            "lgpd-report",
        ]
        missing = [t for t in required if t not in content]
        assert not missing, f"Makefile.lgpd não tem targets: {missing}"

    def test_privacy_notice_has_titular_rights(self) -> None:
        """PRIVACY-NOTICE.md cobre os direitos dos titulares (Art. 18)."""
        content = (_LGPD_TPLDIR / "docs" / "lgpd" / "PRIVACY-NOTICE.md").read_text()
        assert (
            "Art. 18" in content or "direitos" in content.lower()
        ), "PRIVACY-NOTICE.md não menciona os direitos dos titulares"


class TestLgpdBaselineComposer:

    def test_no_conflicts_with_python_fastapi(self) -> None:
        """lgpd-baseline não conflita com python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(["python-fastapi", "lgpd-baseline"], descriptors)
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_no_conflicts_with_terraform_aws(self) -> None:
        """lgpd-baseline não conflita com terraform-aws."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(["terraform-aws", "lgpd-baseline"], descriptors)
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_no_conflicts_with_soc2_baseline(self) -> None:
        """lgpd-baseline não conflita com soc2-baseline."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(["lgpd-baseline", "soc2-baseline"], descriptors)
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_compose_creates_files(self, make_project_config) -> None:
        """Composição cria arquivos do template no projeto alvo."""
        cfg = make_project_config("programming", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        result = composer.compose(["lgpd-baseline"], cfg)
        assert result.success, f"Composição falhou: {result.errors}"
        assert result.created_count > 0, "Composição não criou nenhum arquivo"

    def test_compose_is_idempotent(self, make_project_config) -> None:
        """Segunda composição retorna created_count == 0 (idempotente)."""
        cfg = make_project_config("programming", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        composer.compose(["lgpd-baseline"], cfg)
        result2 = composer.compose(["lgpd-baseline"], cfg)
        assert result2.success
        assert (
            result2.created_count == 0
        ), f"Segunda composição não é idempotente: created={result2.created_count}"

    def test_resolve_order_layer2_before_layer4(self) -> None:
        """python-fastapi (layer2) deve vir antes de lgpd-baseline (layer4)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        ordered = resolve_order(["lgpd-baseline", "python-fastapi"], descriptors)
        assert ordered.index("python-fastapi") < ordered.index(
            "lgpd-baseline"
        ), f"layer2 deve preceder layer4. Ordem: {ordered}"

    def test_resolve_order_layer3_before_layer4(self) -> None:
        """k8s-helm (layer3) deve vir antes de lgpd-baseline (layer4)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        ordered = resolve_order(["lgpd-baseline", "k8s-helm"], descriptors)
        assert ordered.index("k8s-helm") < ordered.index(
            "lgpd-baseline"
        ), f"layer3 deve preceder layer4. Ordem: {ordered}"


# ===========================================================================
# soc2-baseline
# ===========================================================================


class TestSoc2BaselineDescriptor:

    def test_descriptor_loads(self) -> None:
        """soc2-baseline é carregado por load_all_descriptors."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        assert (
            "soc2-baseline" in descriptors
        ), f"soc2-baseline não encontrado. Carregados: {list(descriptors.keys())}"

    def test_required_fields(self) -> None:
        """Descriptor contém name, layer, version, status, description."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        desc = descriptors["soc2-baseline"]
        for field in ("name", "layer", "version", "status", "description"):
            assert field in desc, f"Campo '{field}' ausente no descriptor soc2-baseline"

    def test_layer_is_4(self) -> None:
        """soc2-baseline deve declarar layer 4."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        layer = descriptors["soc2-baseline"].get("layer")
        assert str(layer) == "4", f"Layer esperada: 4, obtida: {layer!r}"

    def test_compliance_field_declared(self) -> None:
        """soc2-baseline deve declarar campo compliance com standard e authority."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        compliance = descriptors["soc2-baseline"].get("compliance", {})
        assert "standard" in compliance, "Campo compliance.standard ausente"
        assert "authority" in compliance, "Campo compliance.authority ausente"

    def test_combines_with_python_fastapi(self) -> None:
        """combines_with inclui python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["soc2-baseline"].get("combines_with", [])
        assert "python-fastapi" in combines

    def test_combines_with_lgpd_baseline(self) -> None:
        """combines_with inclui lgpd-baseline (dois perfis Layer 4 coexistem)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["soc2-baseline"].get("combines_with", [])
        assert "lgpd-baseline" in combines

    def test_combines_with_k8s_helm(self) -> None:
        """combines_with inclui k8s-helm."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        combines = descriptors["soc2-baseline"].get("combines_with", [])
        assert "k8s-helm" in combines


class TestSoc2BaselineTemplates:

    def test_all_declared_templates_exist_on_disk(self) -> None:
        """Todos os templates declarados existem em .github/templates/soc2-baseline/."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        entries = get_template_entries(descriptors["soc2-baseline"])

        assert len(entries) > 0, "soc2-baseline não tem entradas de template"

        missing = [
            str(_PROJECT_ROOT / e["src_rel"])
            for e in entries
            if not (_PROJECT_ROOT / e["src_rel"]).exists()
        ]
        assert not missing, "Templates ausentes no disco:\n" + "\n".join(missing)

    def test_security_policy_covers_cc6_access_control(self) -> None:
        """SECURITY-POLICY.md cobre CC6 (controles de acesso lógico)."""
        content = (_SOC2_TPLDIR / "docs" / "soc2" / "SECURITY-POLICY.md").read_text()
        assert "CC6" in content, "SECURITY-POLICY.md não cobre critério CC6"

    def test_security_policy_covers_cc7_monitoring(self) -> None:
        """SECURITY-POLICY.md cobre CC7 (monitoramento)."""
        content = (_SOC2_TPLDIR / "docs" / "soc2" / "SECURITY-POLICY.md").read_text()
        assert "CC7" in content, "SECURITY-POLICY.md não cobre critério CC7"

    def test_security_policy_covers_cc8_change_management(self) -> None:
        """SECURITY-POLICY.md cobre CC8 (gestão de mudanças)."""
        content = (_SOC2_TPLDIR / "docs" / "soc2" / "SECURITY-POLICY.md").read_text()
        assert "CC8" in content, "SECURITY-POLICY.md não cobre critério CC8"

    def test_security_policy_requires_mfa(self) -> None:
        """SECURITY-POLICY.md exige MFA para acesso a sistemas."""
        content = (_SOC2_TPLDIR / "docs" / "soc2" / "SECURITY-POLICY.md").read_text()
        assert (
            "MFA" in content or "multifator" in content.lower()
        ), "SECURITY-POLICY.md não menciona MFA"

    def test_risk_assessment_has_risk_register(self) -> None:
        """RISK-ASSESSMENT.md contém registro de riscos com probabilidade e impacto."""
        content = (_SOC2_TPLDIR / "docs" / "soc2" / "RISK-ASSESSMENT.md").read_text()
        assert (
            "Probabilidade" in content or "Prob." in content
        ), "RISK-ASSESSMENT.md não tem coluna de Probabilidade"
        assert "Impacto" in content, "RISK-ASSESSMENT.md não tem coluna de Impacto"

    def test_risk_assessment_references_cc3(self) -> None:
        """RISK-ASSESSMENT.md referencia critério CC3."""
        content = (_SOC2_TPLDIR / "docs" / "soc2" / "RISK-ASSESSMENT.md").read_text()
        assert "CC3" in content, "RISK-ASSESSMENT.md não referencia critério CC3"

    def test_static_analysis_uses_codeql(self) -> None:
        """static-analysis.yml usa CodeQL (SAST)."""
        content = (
            _SOC2_TPLDIR / ".github" / "workflows" / "static-analysis.yml"
        ).read_text()
        assert "codeql" in content.lower(), "static-analysis.yml não usa CodeQL"

    def test_static_analysis_uses_bandit(self) -> None:
        """static-analysis.yml usa Bandit para Python SAST."""
        content = (
            _SOC2_TPLDIR / ".github" / "workflows" / "static-analysis.yml"
        ).read_text()
        assert "bandit" in content.lower(), "static-analysis.yml não usa Bandit"

    def test_static_analysis_uses_trivy(self) -> None:
        """static-analysis.yml usa Trivy para container/filesystem scan."""
        content = (
            _SOC2_TPLDIR / ".github" / "workflows" / "static-analysis.yml"
        ).read_text()
        assert "trivy" in content.lower(), "static-analysis.yml não usa Trivy"

    def test_makefile_soc2_has_standard_targets(self) -> None:
        """Makefile.soc2 contém targets obrigatórios."""
        content = (_SOC2_TPLDIR / "Makefile.soc2").read_text()
        required = [
            "soc2-check",
            "soc2-scan-sast",
            "soc2-scan-deps",
            "soc2-docs-check",
            "soc2-report",
            "soc2-evidence",
            "soc2-access-review",
        ]
        missing = [t for t in required if t not in content]
        assert not missing, f"Makefile.soc2 não tem targets: {missing}"


class TestSoc2BaselineComposer:

    def test_no_conflicts_with_python_fastapi(self) -> None:
        """soc2-baseline não conflita com python-fastapi."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(["python-fastapi", "soc2-baseline"], descriptors)
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_no_conflicts_with_k8s_helm(self) -> None:
        """soc2-baseline não conflita com k8s-helm."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(["k8s-helm", "soc2-baseline"], descriptors)
        assert not conflicts, f"Conflitos inesperados: {conflicts}"

    def test_compose_creates_files(self, make_project_config) -> None:
        """Composição cria arquivos do template no projeto alvo."""
        cfg = make_project_config("programming", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        result = composer.compose(["soc2-baseline"], cfg)
        assert result.success, f"Composição falhou: {result.errors}"
        assert result.created_count > 0, "Composição não criou nenhum arquivo"

    def test_compose_is_idempotent(self, make_project_config) -> None:
        """Segunda composição retorna created_count == 0 (idempotente)."""
        cfg = make_project_config("programming", "python")
        composer = ProfileComposer(
            descriptors_dir=_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        composer.compose(["soc2-baseline"], cfg)
        result2 = composer.compose(["soc2-baseline"], cfg)
        assert result2.success
        assert (
            result2.created_count == 0
        ), f"Segunda composição não é idempotente: created={result2.created_count}"

    def test_resolve_order_layer2_before_layer4(self) -> None:
        """python-fastapi (layer2) deve vir antes de soc2-baseline (layer4)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        ordered = resolve_order(["soc2-baseline", "python-fastapi"], descriptors)
        assert ordered.index("python-fastapi") < ordered.index(
            "soc2-baseline"
        ), f"layer2 deve preceder layer4. Ordem: {ordered}"

    def test_resolve_order_layer3_before_layer4(self) -> None:
        """terraform-aws (layer3) deve vir antes de soc2-baseline (layer4)."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        ordered = resolve_order(["soc2-baseline", "terraform-aws"], descriptors)
        assert ordered.index("terraform-aws") < ordered.index(
            "soc2-baseline"
        ), f"layer3 deve preceder layer4. Ordem: {ordered}"

    def test_no_conflicts_between_both_compliance_profiles(self) -> None:
        """lgpd-baseline e soc2-baseline podem coexistir sem conflitos."""
        descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
        conflicts = check_conflicts(["lgpd-baseline", "soc2-baseline"], descriptors)
        assert not conflicts, f"Dois perfis Layer 4 não devem conflitar: {conflicts}"
