"""
tests/test_templates_snapshot.py — IMP-16: Snapshot test para combo programming × python.

Garante que mudanças acidentais em templates.py produzam diff visível no CI.

Fluxo:
  1ª execução (snapshot não existe):
    pytest tests/test_templates_snapshot.py --update-snapshots
    → cria tests/snapshots/copilot_rules__programming__python.md
    → cria tests/snapshots/copilot_instructions__programming__python.md
    → commitar esses snapshots como baseline

  Execuções subsequentes (CI/PR):
    pytest tests/test_templates_snapshot.py
    → compara output gerado contra os snapshots commitados
    → falha com diff se algo mudou
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.templates import (  # noqa: E402
    generate_copilot_instructions,
    generate_copilot_rules,
)

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

# Timestamp fixo usado nos configs de teste — substituído antes de comparar
_FIXED_TS = "2026-03-07T00:00:00"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _normalize(content: str) -> str:
    """Remove o timestamp para que snapshots sejam estáveis entre execuções."""
    return content.replace(_FIXED_TS, "{{CREATED_AT}}")


def _assert_or_update(actual: str, snapshot_name: str, *, update: bool) -> None:
    """
    Compara 'actual' contra o snapshot em disco.
    Se update=True (ou snapshot não existe): cria/sobrescreve o arquivo.
    """
    snap_file = SNAPSHOT_DIR / snapshot_name
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    if update or not snap_file.exists():
        snap_file.write_text(actual, encoding="utf-8")
        pytest.skip(
            f"Snapshot {'atualizado' if snap_file.exists() else 'criado'}: {snap_file.name}"
        )

    expected = snap_file.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Regressão detectada em {snapshot_name!r}\n"
        "Execute com --update-snapshots para regenerar o baseline."
    )


# ---------------------------------------------------------------------------
# Snapshot: copilot-rules — programming × python
# ---------------------------------------------------------------------------


def test_copilot_rules_snapshot_programming_python(
    make_project_config, update_snapshots: bool
) -> None:
    """
    Snapshot baseline para o combo mais comum: programming × python.
    Qualquer alteração em _COPILOT_RULES_TEMPLATE, _DOMAIN_P0_RULES['programming']
    ou _LANGUAGE_CONVENTIONS['python'] será detectada aqui.
    """
    cfg = make_project_config("programming", "python")
    result = generate_copilot_rules(cfg)

    assert result.status == "created"
    content = _normalize(result.path.read_text(encoding="utf-8"))

    _assert_or_update(
        content,
        "copilot_rules__programming__python.md",
        update=update_snapshots,
    )


# ---------------------------------------------------------------------------
# Snapshot: copilot-instructions — programming × python
# ---------------------------------------------------------------------------


def test_copilot_instructions_snapshot_programming_python(
    make_project_config, update_snapshots: bool
) -> None:
    """
    Snapshot baseline do copilot-instructions.md para programming × python.
    Detecta mudanças em _COPILOT_INSTRUCTIONS_TEMPLATE.
    """
    cfg = make_project_config("programming", "python")
    result = generate_copilot_instructions(cfg)

    assert result.status == "created"
    content = _normalize(result.path.read_text(encoding="utf-8"))

    _assert_or_update(
        content,
        "copilot_instructions__programming__python.md",
        update=update_snapshots,
    )


# ---------------------------------------------------------------------------
# Snapshot: copilot-rules — infrastructure × python  (infra usa _default)
# ---------------------------------------------------------------------------


def test_copilot_rules_snapshot_infrastructure_python(
    make_project_config, update_snapshots: bool
) -> None:
    """
    Snapshot para infrastructure × python — cobre o caminho _default de folder structure.
    """
    cfg = make_project_config("infrastructure", "python")
    result = generate_copilot_rules(cfg)

    assert result.status == "created"
    content = _normalize(result.path.read_text(encoding="utf-8"))

    _assert_or_update(
        content,
        "copilot_rules__infrastructure__python.md",
        update=update_snapshots,
    )


# ---------------------------------------------------------------------------
# Snapshot: copilot-rules com extra_profiles
# ---------------------------------------------------------------------------


def test_copilot_rules_snapshot_with_extra_profiles(
    make_project_config, update_snapshots: bool
) -> None:
    """
    Snapshot para programming × python com perfis extras — verifica a tabela
    de perfis ativos no output.
    """
    cfg = make_project_config(
        "programming",
        "python",
        extra_profiles=["devops-infrastructure", "devops-analysis"],
    )
    result = generate_copilot_rules(cfg)

    assert result.status == "created"
    content = _normalize(result.path.read_text(encoding="utf-8"))

    # Sem snapshot em disco para este — apenas valida conteúdo inline
    assert "devops-infrastructure" in content, "extra profile 'infrastructure' ausente"
    assert "devops-analysis" in content, "extra profile 'analysis' ausente"


# ---------------------------------------------------------------------------
# IMP-39: Snapshots de arquivos representativos por perfil
# ---------------------------------------------------------------------------

_TEMPLATES_BASE = Path(__file__).parent.parent / "scaffold" / "templates" / "project"

# (profile_name, rel_path_dentro_do_template) — 1 arquivo por perfil Layer 2/3
_PROFILE_FILE_SNAPSHOTS: list[tuple[str, str]] = [
    ("python-fastapi", "src/main.py"),
    ("python-flask", "src/app.py"),
    ("typescript-next", "app/layout.tsx"),
    ("k8s-helm", "helm/Chart.yaml"),
    ("terraform-aws", "terraform/main.tf"),
    ("lgpd-baseline", "docs/lgpd/DATA-MAPPING.md"),
    ("soc2-baseline", "docs/soc2/SECURITY-POLICY.md"),
    ("data-pipeline-airflow", "airflow/dags/example_pipeline.py"),
    ("data-warehouse-dbt", "dbt/dbt_project.yml"),
]


@pytest.mark.parametrize("profile_name,rel_path", _PROFILE_FILE_SNAPSHOTS)
def test_profile_template_file_snapshot(
    profile_name: str, rel_path: str, update_snapshots: bool
) -> None:
    """
    Snapshot de arquivo representativo por perfil.

    Detecta regressões acidentais em arquivos de template:
    se o conteúdo de qualquer arquivo mudar, este teste falha e
    exige decisão explícita (--update-snapshots) para aceitar a mudança.

    Cobertura: 9 perfis Layer 2/3 × 1 arquivo cada.
    """
    src_file = _TEMPLATES_BASE / profile_name / rel_path
    assert src_file.exists(), f"Template não encontrado: {src_file}"

    content = src_file.read_text(encoding="utf-8")

    safe_profile = profile_name.replace("-", "_")
    safe_relpath = rel_path.replace("/", "__").replace(".", "_")
    snap_name = f"template__{safe_profile}__{safe_relpath}"

    _assert_or_update(content, snap_name, update=update_snapshots)
