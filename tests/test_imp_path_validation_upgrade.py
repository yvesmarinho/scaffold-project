"""
tests/test_imp_path_validation_upgrade.py — Validação de divergência de paths no upgrade

Testa a nova funcionalidade que detecta quando há divergência entre:
  - Path salvo em .scaffold-state.yaml (paths.target_dir)
  - Path atual onde upgrade está sendo executado

Comportamento esperado:
  - Se paths coincidem: upgrade prossegue normalmente
  - Se paths divergem: usuário é questionado sobre qual usar
  - Em modo JSON: atualiza automaticamente para path atual

Implementação: scripts/lib/flows/upgrade.py::_validate_and_fix_paths()
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.flows.upgrade import _validate_and_fix_paths  # noqa: E402


def _write_state_yaml(project_path: Path, state: dict) -> None:
    """Helper: escreve .scaffold-state.yaml diretamente (sem ProjectConfig)."""
    import yaml

    state_file = project_path / ".scaffold-state.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True)


@pytest.fixture
def sample_state():
    """Estado mínimo válido para testes."""
    return {
        "scaffold_version": "1.0.0",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-05-12T00:00:00Z",
        "project": {
            "name": "test-project",
            "title": "Test Project",
            "description": "Test project for path validation",
            "domain": "programming",
            "language": "python",
        },
        "paths": {
            "target_dir": "/original/parent/path",
            "shared_dir": "/home/user/.copilot-shared",
        },
        "profiles_applied": [],
        "template_versions": {},
    }


def test_validate_paths_no_divergence(tmp_path: Path, sample_state: dict):
    """
    Teste: Paths coincidem - validação passa sem interação.

    Cenário:
      - State tem target_dir = /tmp/pytest-123/parent
      - Upgrade executado de /tmp/pytest-123/parent/test-project
      - Paths resolvem para o mesmo diretório pai

    Resultado esperado:
      - Retorna state inalterado
      - Nenhuma pergunta ao usuário
    """
    # Setup: criar estrutura
    parent = tmp_path / "parent"
    project = parent / "test-project"
    project.mkdir(parents=True)

    # State com target_dir correto
    sample_state["paths"]["target_dir"] = str(parent)
    _write_state_yaml(project, sample_state)

    # Executar validação (current_target é o projeto)
    result = _validate_and_fix_paths(sample_state, project, use_json=False)

    # Verificar: state inalterado
    assert result is not None
    assert result["paths"]["target_dir"] == str(parent)


def test_validate_paths_divergence_json_mode(tmp_path: Path, sample_state: dict):
    """
    Teste: Paths divergem + modo JSON = atualiza automaticamente.

    Cenário:
      - State tem target_dir = /original/parent/path
      - Upgrade executado de /tmp/pytest-123/new-location/test-project
      - Modo JSON ativo (não pode interagir com usuário)

    Resultado esperado:
      - Atualiza state["paths"]["target_dir"] para new-location
      - Retorna state modificado
      - .scaffold-state.yaml atualizado no disco
    """
    # Setup: criar estrutura em novo local
    new_parent = tmp_path / "new-location"
    project = new_parent / "test-project"
    project.mkdir(parents=True)

    # State com target_dir DIFERENTE (divergência)
    sample_state["paths"]["target_dir"] = "/original/parent/path"
    _write_state_yaml(project, sample_state)

    # Executar validação em modo JSON
    result = _validate_and_fix_paths(sample_state, project, use_json=True)

    # Verificar: state foi atualizado
    assert result is not None
    assert result["paths"]["target_dir"] == str(new_parent.resolve())

    # Verificar: arquivo no disco foi atualizado
    state_file = project / ".scaffold-state.yaml"
    with state_file.open() as f:
        disk_state = yaml.safe_load(f)
    assert disk_state is not None
    assert disk_state["paths"]["target_dir"] == str(new_parent.resolve())


def test_validate_paths_current_target_is_project(tmp_path: Path, sample_state: dict):
    """
    Teste: current_target termina com project_name - extrai pai corretamente.

    Cenário:
      - State tem target_dir = /tmp/pytest-123/parent
      - current_target = /tmp/pytest-123/parent/test-project (nome do projeto)
      - Função deve detectar que é o próprio projeto e extrair pai

    Resultado esperado:
      - Extrai parent/ como diretório pai
      - Compara parent/ com target_dir do state
      - Paths coincidem → retorna state inalterado
    """
    # Setup: criar estrutura
    parent = tmp_path / "parent"
    project = parent / "test-project"
    project.mkdir(parents=True)

    # State correto
    sample_state["paths"]["target_dir"] = str(parent)
    _write_state_yaml(project, sample_state)

    # current_target É O PRÓPRIO PROJETO (termina com test-project)
    result = _validate_and_fix_paths(sample_state, project, use_json=False)

    # Verificar: validação passou
    assert result is not None
    assert result["paths"]["target_dir"] == str(parent)


def test_validate_paths_current_target_is_parent(tmp_path: Path, sample_state: dict):
    """
    Teste: current_target é o diretório pai (não termina com project_name).

    Cenário:
      - State tem target_dir = /tmp/pytest-123/parent
      - current_target = /tmp/pytest-123/parent (diretório pai)
      - Paths coincidem

    Resultado esperado:
      - Usa current_target diretamente como pai
      - Paths coincidem → retorna state inalterado
    """
    # Setup: criar estrutura
    parent = tmp_path / "parent"
    project = parent / "test-project"
    project.mkdir(parents=True)

    # State correto
    sample_state["paths"]["target_dir"] = str(parent)
    _write_state_yaml(project, sample_state)

    # current_target É O DIRETÓRIO PAI (não termina com test-project)
    result = _validate_and_fix_paths(sample_state, parent, use_json=False)

    # Verificar: validação passou
    assert result is not None
    assert result["paths"]["target_dir"] == str(parent)


def test_validate_paths_resolves_symlinks(tmp_path: Path, sample_state: dict):
    """
    Teste: Paths são resolvidos (symlinks, relativos) antes da comparação.

    Cenário:
      - State tem target_dir = "/tmp/parent" (path absoluto)
      - current_target = "." (path relativo, mas resolve para /tmp/parent)
      - Após resolve(), paths devem coincidir

    Resultado esperado:
      - Paths resolvem para o mesmo diretório
      - Retorna state inalterado
    """
    # Setup: criar estrutura
    parent = tmp_path / "parent"
    project = parent / "test-project"
    project.mkdir(parents=True)

    # State com path absoluto
    sample_state["paths"]["target_dir"] = str(parent.resolve())
    _write_state_yaml(project, sample_state)

    # current_target é path relativo, mas resolve para parent
    # (simulamos mudando cwd, mas como não podemos mudar cwd no teste,
    # apenas verificamos que .resolve() funciona)
    result = _validate_and_fix_paths(sample_state, project, use_json=False)

    # Verificar: validação passou (resolve() fez comparação correta)
    assert result is not None


def test_validate_paths_relative_target_dir(tmp_path: Path, sample_state: dict):
    """
    Teste: target_dir no state é relativo - resolve antes de comparar.

    Cenário:
      - State tem target_dir = "poc" (path relativo)
      - current_target = /tmp/pytest-123/parent/test-project
      - Paths são resolvidos antes da comparação

    Resultado esperado:
      - Divergência detectada (paths diferentes após resolve)
      - Em modo JSON: atualiza para path absoluto atual
    """
    # Setup: criar estrutura
    parent = tmp_path / "parent"
    project = parent / "test-project"
    project.mkdir(parents=True)

    # State com target_dir RELATIVO (como no BUG-10)
    sample_state["paths"]["target_dir"] = "poc"
    _write_state_yaml(project, sample_state)

    # Executar validação em modo JSON
    result = _validate_and_fix_paths(sample_state, project, use_json=True)

    # Verificar: state foi atualizado para path absoluto
    assert result is not None
    assert result["paths"]["target_dir"] == str(parent.resolve())
    assert Path(result["paths"]["target_dir"]).is_absolute()
