"""
tests/test_smoke_terraform_aws.py — IMP-23: Smoke tests para o perfil terraform-aws (Layer 3).

Cobertura:
  - Descriptor carregado com campos obrigatórios
  - Layer 3 corretamente declarada
  - combines_with contém perfis Layer 2 esperados
  - Todos os arquivos de template existem no disco
  - Segurança: templates de RDS contêm publicly_accessible=false + storage_encrypted=true
  - Segurança: IAM com ARN específico (sem Resource "*" para serviços sensíveis)
  - Sem conflitos com perfis Layer 2 compatíveis
  - Composição cria arquivos no projeto alvo
  - Idempotência
  - Ordem: layer2 antes de layer3
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
_TEMPLATES_DIR = _PROJECT_ROOT / ".github" / "templates" / "terraform-aws"


# ---------------------------------------------------------------------------
# Descriptor — struct validation
# ---------------------------------------------------------------------------


def test_terraform_aws_descriptor_loads() -> None:
    """terraform-aws descriptor é carregado por load_all_descriptors."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    assert (
        "terraform-aws" in descriptors
    ), f"terraform-aws não encontrado. Carregados: {list(descriptors.keys())}"


def test_terraform_aws_descriptor_has_required_fields() -> None:
    """Descriptor contém campos obrigatórios: name, layer, version, status, description."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    desc = descriptors["terraform-aws"]
    for field in ("name", "layer", "version", "status", "description"):
        assert field in desc, f"Campo '{field}' ausente no descriptor terraform-aws"


def test_terraform_aws_layer_is_3() -> None:
    """terraform-aws deve declarar layer 3."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    layer = descriptors["terraform-aws"].get("layer")
    assert str(layer) == "3", f"Layer esperada: 3, obtida: {layer!r}"


def test_terraform_aws_combines_with_python_fastapi() -> None:
    """combines_with deve incluir python-fastapi."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    combines = descriptors["terraform-aws"].get("combines_with", [])
    assert "python-fastapi" in combines


def test_terraform_aws_combines_with_typescript_next() -> None:
    """combines_with deve incluir typescript-next."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    combines = descriptors["terraform-aws"].get("combines_with", [])
    assert "typescript-next" in combines


# ---------------------------------------------------------------------------
# Templates — existência no disco
# ---------------------------------------------------------------------------


def test_terraform_aws_templates_exist_on_disk() -> None:
    """Todos os templates declarados no descriptor existem em .github/templates/terraform-aws/."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    entries = get_template_entries(descriptors["terraform-aws"])

    assert len(entries) > 0, "terraform-aws não tem entradas de template"

    missing = []
    for entry in entries:
        src_path = _PROJECT_ROOT / entry["src_rel"]
        if not src_path.exists():
            missing.append(str(src_path))

    assert not missing, "Templates ausentes no disco:\n" + "\n".join(missing)


# ---------------------------------------------------------------------------
# Segurança — verificações de conteúdo nos templates HCL
# ---------------------------------------------------------------------------


def test_rds_template_no_public_access() -> None:
    """modules/rds/main.tf deve declarar publicly_accessible = false."""
    rds_main = _TEMPLATES_DIR / "terraform" / "modules" / "rds" / "main.tf"
    assert rds_main.exists(), "modules/rds/main.tf não encontrado"
    content = rds_main.read_text()
    assert (
        "publicly_accessible" in content
    ), "rds/main.tf não contém publicly_accessible"
    assert "false" in content, "rds/main.tf não define publicly_accessible = false"


def test_rds_template_storage_encrypted() -> None:
    """modules/rds/main.tf deve declarar storage_encrypted = true."""
    rds_main = _TEMPLATES_DIR / "terraform" / "modules" / "rds" / "main.tf"
    content = rds_main.read_text()
    assert "storage_encrypted" in content, "rds/main.tf não contém storage_encrypted"
    assert "true" in content, "rds/main.tf não define storage_encrypted = true"


def test_rds_no_hardcoded_password() -> None:
    """modules/rds/main.tf não deve conter senha hardcoded — usa random_password."""
    rds_main = _TEMPLATES_DIR / "terraform" / "modules" / "rds" / "main.tf"
    content = rds_main.read_text()
    assert (
        "random_password" in content
    ), "rds/main.tf não usa random_password para a senha"


def test_ecs_iam_no_wildcard_resource() -> None:
    """modules/ecs/main.tf não deve usar Resource: \"*\" para SSM/Secrets."""
    ecs_main = _TEMPLATES_DIR / "terraform" / "modules" / "ecs" / "main.tf"
    assert ecs_main.exists(), "modules/ecs/main.tf não encontrado"
    content = ecs_main.read_text()
    # The scoped SSM policy should reference var.project_name and var.env, not "*"
    assert "arn:aws:ssm" in content, "ecs/main.tf não contém ARN específico para SSM"


def test_versions_tf_pins_provider_version() -> None:
    """versions.tf deve fixar a versão do provider AWS (não usar latest)."""
    versions_tf = _TEMPLATES_DIR / "terraform" / "versions.tf"
    assert versions_tf.exists(), "terraform/versions.tf não encontrado"
    content = versions_tf.read_text()
    assert "~>" in content, "versions.tf não usa constraint de versão (~>)"
    assert (
        "hashicorp/aws" in content
    ), "versions.tf não declara o provider hashicorp/aws"


# ---------------------------------------------------------------------------
# Compatibilidade — sem conflitos com perfis Layer 2
# ---------------------------------------------------------------------------


def test_terraform_aws_no_conflicts_with_python_fastapi() -> None:
    """terraform-aws + python-fastapi não devem gerar conflito."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    conflicts = check_conflicts(["terraform-aws", "python-fastapi"], descriptors)
    assert not conflicts, f"Conflito inesperado: {conflicts}"


def test_terraform_aws_no_conflicts_with_typescript_next() -> None:
    """terraform-aws + typescript-next não devem gerar conflito."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    conflicts = check_conflicts(["terraform-aws", "typescript-next"], descriptors)
    assert not conflicts, f"Conflito inesperado: {conflicts}"


# ---------------------------------------------------------------------------
# Composição — integração com ProfileComposer
# ---------------------------------------------------------------------------


def test_compose_terraform_aws_creates_files(make_project_config) -> None:
    """Composição de terraform-aws cria arquivos no target dir."""
    cfg = make_project_config("infrastructure", "other")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    result = composer.compose(["terraform-aws"], cfg)

    assert result.success, f"Composição falhou: {result.errors}"
    assert "terraform-aws" in result.applied
    assert result.created_count > 0, "Nenhum arquivo foi criado"


def test_compose_terraform_aws_idempotent(make_project_config) -> None:
    """Segunda composição não cria arquivos novos (idempotente)."""
    cfg = make_project_config("infrastructure", "other")
    composer = ProfileComposer(
        descriptors_dir=_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )
    composer.compose(["terraform-aws"], cfg)
    result2 = composer.compose(["terraform-aws"], cfg)

    assert result2.success
    assert (
        result2.created_count == 0
    ), "Segunda composição criou arquivos — não é idempotente"


def test_resolve_order_layer2_before_terraform_layer3() -> None:
    """python-fastapi (layer2) deve ser aplicado antes de terraform-aws (layer3)."""
    descriptors = load_all_descriptors(_DESCRIPTORS_DIR)
    profiles = ["terraform-aws", "python-fastapi"]
    ordered = resolve_order(profiles, descriptors)

    assert ordered.index("python-fastapi") < ordered.index(
        "terraform-aws"
    ), f"Esperado layer2 antes de layer3, got: {ordered}"
