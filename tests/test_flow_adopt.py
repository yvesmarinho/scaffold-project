"""
tests/test_flow_adopt.py — Testes do comando `scaffold adopt` (projetos legados).

Criado em: 15/07/2026 14:30
Modificado em: 15/07/2026 14:30

Cobertura:
  detect_language: python, typescript, go, other (e precedência python > ts)
  detect_domain:   infrastructure (*.tf, Chart.yaml), programming (default)
  _kebab:          normalização de nomes
  flow_adopt:
    - erro se diretório alvo não existe
    - erro se .scaffold-state.yaml já existe (deve usar upgrade)
    - cria state com detecção correta e delega ao upgrade (mockado)
    - overrides via --name/--domain/--language/--ai
    - não sobrescreve arquivos existentes (integração real, --ci)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib.flows import adopt as adopt_mod  # noqa: E402
from lib.flows.adopt import (  # noqa: E402
    _kebab,
    detect_domain,
    detect_language,
    flow_adopt,
)


def _args(target: Path, **overrides) -> argparse.Namespace:
    base = {
        "target_dir": str(target),
        "ci": True,
        "json_output": False,
        "force": False,
        "no_log": True,
        "name": None,
        "title": None,
        "description": None,
        "domain": None,
        "language": None,
        "ai_assistant": None,
        "repo": None,
        "shared_dir": None,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


# ---------------------------------------------------------------------------
# Detecção
# ---------------------------------------------------------------------------

def test_detect_language_python(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    assert detect_language(tmp_path) == "python"


def test_detect_language_typescript(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert detect_language(tmp_path) == "typescript"


def test_detect_language_go(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module x\n", encoding="utf-8")
    assert detect_language(tmp_path) == "go"


def test_detect_language_other(tmp_path: Path) -> None:
    assert detect_language(tmp_path) == "other"


def test_detect_language_python_precedes_typescript(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert detect_language(tmp_path) == "python"


def test_detect_domain_terraform(tmp_path: Path) -> None:
    (tmp_path / "main.tf").write_text("", encoding="utf-8")
    assert detect_domain(tmp_path) == "infrastructure"


def test_detect_domain_helm(tmp_path: Path) -> None:
    (tmp_path / "Chart.yaml").write_text("name: x\n", encoding="utf-8")
    assert detect_domain(tmp_path) == "infrastructure"


def test_detect_domain_default_programming(tmp_path: Path) -> None:
    assert detect_domain(tmp_path) == "programming"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("My Legacy_App", "my-legacy-app"),
        ("já.existente", "j-existente"),
        ("---", "adopted-project"),
    ],
)
def test_kebab(raw: str, expected: str) -> None:
    assert _kebab(raw) == expected


# ---------------------------------------------------------------------------
# flow_adopt — validações e delegação
# ---------------------------------------------------------------------------

def test_adopt_missing_dir_returns_error(tmp_path: Path) -> None:
    args = _args(tmp_path / "nao-existe")
    assert flow_adopt(args) == 1


def test_adopt_refuses_existing_state(tmp_path: Path) -> None:
    (tmp_path / ".scaffold-state.yaml").write_text("project: {}\n", encoding="utf-8")
    args = _args(tmp_path)
    assert flow_adopt(args) == 1


def test_adopt_writes_state_and_delegates(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    args = _args(tmp_path)

    with patch.object(adopt_mod, "flow_upgrade", return_value=0) as mock_up:
        rc = flow_adopt(args)

    assert rc == 0
    mock_up.assert_called_once()
    state = yaml.safe_load((tmp_path / ".scaffold-state.yaml").read_text(encoding="utf-8"))
    assert state["project"]["name"] == _kebab(tmp_path.name)
    assert state["project"]["language"] == "python"
    assert state["project"]["domain"] == "programming"


def test_adopt_honors_overrides(tmp_path: Path) -> None:
    args = _args(
        tmp_path,
        name="Meu App",
        domain="infrastructure",
        language="go",
        ai_assistant="claude",
    )

    with patch.object(adopt_mod, "flow_upgrade", return_value=0):
        rc = flow_adopt(args)

    assert rc == 0
    state = yaml.safe_load((tmp_path / ".scaffold-state.yaml").read_text(encoding="utf-8"))
    assert state["project"]["name"] == "meu-app"
    assert state["project"]["domain"] == "infrastructure"
    assert state["project"]["language"] == "go"
    assert state["project"]["ai_assistant"] == "claude"


def test_adopt_dry_run_writes_nothing(tmp_path: Path) -> None:
    """--dry-run simula e NÃO cria state nem delega ao upgrade (BUG relatado 15/07)."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    args = _args(tmp_path, dry_run=True)

    with patch.object(adopt_mod, "flow_upgrade", return_value=0) as mock_up:
        rc = flow_adopt(args)

    assert rc == 0
    mock_up.assert_not_called()
    assert not (tmp_path / ".scaffold-state.yaml").exists()
    # Nada do template foi criado (ignora dirs criados pela fixture isolate_tests)
    contents = {p.name for p in tmp_path.iterdir()} - {"tmp", "home"}
    assert contents == {"pyproject.toml"}


def test_adopt_dry_run_json_plan(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    (tmp_path / "go.mod").write_text("module x\n", encoding="utf-8")
    args = _args(tmp_path, dry_run=True, json_output=True)

    assert flow_adopt(args) == 0
    import json

    plan = json.loads(capsys.readouterr().out)
    assert plan["dry_run"] is True
    assert plan["project"]["language"] == "go"
    assert not (tmp_path / ".scaffold-state.yaml").exists()


# ---------------------------------------------------------------------------
# Integração real (pipeline completo, --ci)
# ---------------------------------------------------------------------------

def test_adopt_integration_preserves_existing_files(tmp_path: Path) -> None:
    original = "[project]\nname = 'legacy'\n"
    (tmp_path / "pyproject.toml").write_text(original, encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")

    args = _args(tmp_path, ai_assistant="claude")
    rc = flow_adopt(args)

    assert rc == 0
    # Arquivos do legado intocados
    assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original
    assert (tmp_path / "src" / "main.py").exists()
    # Estrutura do template criada
    assert (tmp_path / ".scaffold-state.yaml").exists()
    assert (tmp_path / "docs").is_dir()
    # Re-adopt é bloqueado (state já existe)
    assert flow_adopt(_args(tmp_path)) == 1
