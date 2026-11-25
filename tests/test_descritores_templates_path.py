"""
Testes — ADR-003 fatia 2: descritores com ``templates_path`` inexistente.

9 descritores (appsec-engineer, backend-architect, …) declaravam templates que
nunca foram escritos; o composer só registrava ``skipped`` arquivo a arquivo.
Decisão: marcar com ``templates_status: pendente`` — o composer não tenta
copiar, o guia de perfil sinaliza, e o validador barra caminho quebrado sem a
marca (ou marca obsoleta / valor inválido).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from scripts.lib.composer import get_template_entries
from scripts.lib.validate import validate_descriptors

_ROOT = Path(__file__).resolve().parent.parent
_PROFILES = _ROOT / "scaffold" / "profiles"


def _descriptors() -> list[tuple[str, dict]]:
    return [
        (p.name, yaml.safe_load(p.read_text(encoding="utf-8")) or {})
        for p in sorted(_PROFILES.glob("*.yaml"))
    ]


@pytest.mark.parametrize(
    ("name", "data"), _descriptors(), ids=[n for n, _ in _descriptors()]
)
def test_templates_path_existe_ou_esta_marcado_pendente(name, data):
    path = data.get("templates_path")
    if not path:
        return
    exists = (_ROOT / path).is_dir()
    assert (
        exists or data.get("templates_status") == "pendente"
    ), f"{name}: templates_path inexistente sem templates_status: pendente"


@pytest.mark.parametrize(
    ("name", "data"), _descriptors(), ids=[n for n, _ in _descriptors()]
)
def test_templates_declarados_existem(name, data):
    """Schema A sem marca pendente: todo arquivo em templates[] existe na pasta."""
    if "templates_path" not in data or data.get("templates_status") == "pendente":
        return
    missing = [
        e["src_rel"]
        for e in get_template_entries(data)
        if not (_ROOT / e["src_rel"]).exists()
    ]
    assert missing == [], f"{name}: templates declarados inexistentes"


def test_composer_nao_lista_templates_pendentes():
    descriptor = {
        "templates_path": "scaffold/templates/project/nao-existe",
        "templates_status": "pendente",
        "templates": [{"path": "a.md", "description": "x"}],
    }
    assert get_template_entries(descriptor) == []


def test_composer_ignora_entradas_generated():
    descriptor = {
        "templates_path": "scaffold/templates/project/x",
        "templates": [
            {"path": "a.md", "description": "x"},
            {"path": "sbom.json", "generated": True, "description": "make sbom"},
        ],
    }
    assert [e["dest"] for e in get_template_entries(descriptor)] == ["a.md"]


def test_composer_lista_templates_sem_marca():
    descriptor = {
        "templates_path": "scaffold/templates/project/x",
        "templates": [{"path": "a.md", "description": "x"}],
    }
    assert [e["dest"] for e in get_template_entries(descriptor)] == ["a.md"]


# ---------------------------------------------------------------------------
# Validador (--validate)
# ---------------------------------------------------------------------------


@pytest.fixture
def repo_falso(tmp_path: Path) -> Path:
    """Repo mínimo: scaffold/profiles/ com um descritor válido copiado."""
    profiles = tmp_path / "scaffold" / "profiles"
    profiles.mkdir(parents=True)
    shutil.copy(_PROFILES / "appsec-engineer.yaml", profiles / "appsec-engineer.yaml")
    return tmp_path


def _rewrite(repo: Path, **changes) -> None:
    path = repo / "scaffold" / "profiles" / "appsec-engineer.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key, value in changes.items():
        if value is None:
            data.pop(key, None)
        else:
            data[key] = value
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def _issues(repo: Path, severity: str) -> list[str]:
    report = validate_descriptors(repo / "scaffold" / "profiles")
    return [
        i.message
        for r in report.results
        for i in r.issues
        if i.field == "templates_path" and i.severity == severity
    ]


def test_validador_acusa_path_inexistente_sem_marca(repo_falso):
    _rewrite(repo_falso, templates_status=None)

    assert _issues(repo_falso, "error")


def test_validador_aceita_path_inexistente_marcado(repo_falso):
    _rewrite(repo_falso, templates_status="pendente")

    assert _issues(repo_falso, "error") == []


def test_validador_acusa_valor_invalido_de_status(repo_falso):
    _rewrite(repo_falso, templates_status="talvez")

    assert _issues(repo_falso, "error")


def test_validador_avisa_marca_obsoleta(repo_falso):
    tp = yaml.safe_load(
        (repo_falso / "scaffold/profiles/appsec-engineer.yaml").read_text(
            encoding="utf-8"
        )
    )["templates_path"]
    (repo_falso / tp).mkdir(parents=True)
    _rewrite(repo_falso, templates_status="pendente")

    assert _issues(repo_falso, "warning")


def test_repositorio_real_sem_erros_de_templates_path():
    report = validate_descriptors(_PROFILES)
    errors = [
        f"{r.file}: {i.message}"
        for r in report.results
        for i in r.issues
        if i.field == "templates_path" and i.severity == "error"
    ]
    assert errors == []
