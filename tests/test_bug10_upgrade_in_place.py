"""
tests/test_bug10_upgrade_in_place.py — Teste para BUG-10: Upgrade in-place

Testa o cenário onde:
  - Projeto tem `.scaffold-state.yaml` na raiz (ex: /teste_projetos/.scaffold-state.yaml)
  - Nome do diretório (teste_projetos) ≠ project_name (sistema-deploy-automatizado)
  - Executar `scaffold upgrade` SEM --target-dir deve atualizar a RAIZ, não criar subpasta

Comportamento esperado:
  - `project_path` = path atual (não concatena project_name)
  - Arquivos criados/atualizados na raiz do projeto
  - NÃO cria subpasta com nome do projeto

Implementação:
  - scripts/lib/config.py::ProjectConfig.project_path (detecção de .scaffold-state.yaml)
  - scripts/lib/project.py::config_from_state (target = override_target quando tem state)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.config import ProjectConfig  # noqa: E402
from lib.project import config_from_state  # noqa: E402


def test_upgrade_in_place_dir_name_differs_from_project_name(tmp_path: Path):
    """
    BUG-10: Upgrade in-place quando nome do diretório ≠ project_name.

    Cenário:
      - Diretório: /tmp/pytest-123/teste_projetos/
      - .scaffold-state.yaml: project.name = sistema-deploy-automatizado
      - Executar upgrade de /teste_projetos/ (cwd)

    Comportamento esperado:
      - target_dir = /teste_projetos/
      - project_path = /teste_projetos/ (NÃO concatena nome do projeto)
      - Arquivos criados em /teste_projetos/, não em /teste_projetos/sistema-deploy-automatizado/
    """
    # Setup: criar estrutura com nome diferente do project_name
    project_dir = tmp_path / "teste_projetos"
    project_dir.mkdir()

    # State com project_name diferente do nome do diretório
    state = {
        "scaffold_version": "1.0.0",
        "created_at": "2026-05-12T00:00:00Z",
        "updated_at": "2026-05-12T17:00:00Z",
        "project": {
            "name": "sistema-deploy-automatizado",  # ≠ teste_projetos
            "title": "Sistema Deploy Automatizado",
            "description": "Test project",
            "domain": "programming",
            "language": "python",
        },
        "paths": {
            "target_dir": str(tmp_path),  # parent directory
            "shared_dir": "/home/user/.copilot-shared",
        },
        "profiles_applied": [],
        "template_versions": {},
    }

    # Escrever .scaffold-state.yaml no projeto
    state_file = project_dir / ".scaffold-state.yaml"
    with state_file.open("w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True)

    # Simular: scaffold upgrade executado de /teste_projetos/ (sem --target-dir)
    # override_target = cwd = /teste_projetos/
    cfg = config_from_state(state, override_target=project_dir)

    # Verificar: target_dir = project_dir (upgrade in-place)
    assert cfg.target_dir == project_dir

    # Verificar: project_path = project_dir (NÃO concatena nome)
    assert cfg.project_path == project_dir.resolve()

    # Verificar: project_name preservado do state
    assert cfg.project_name == "sistema-deploy-automatizado"


def test_project_path_detects_in_place_upgrade(tmp_path: Path):
    """
    ProjectConfig.project_path detecta upgrade in-place pela presença de .scaffold-state.yaml.

    Cenário:
      - target_dir tem .scaffold-state.yaml
      - target_dir.name ≠ project_name

    Comportamento esperado:
      - project_path = target_dir (sem concatenação)
    """
    # Setup
    project_dir = tmp_path / "my-project-folder"
    project_dir.mkdir()

    # Criar .scaffold-state.yaml vazio (só precisa existir)
    state_file = project_dir / ".scaffold-state.yaml"
    state_file.write_text("scaffold_version: 1.0.0\n")

    # Criar ProjectConfig com target_dir = project_dir
    cfg = ProjectConfig(
        project_name="different-name",  # nome diferente do diretório
        project_title="Test",
        description="Test",
        domain="programming",
        language="python",
        github_repo=None,
        shared_dir=tmp_path / ".copilot-shared",
        target_dir=project_dir,  # TEM .scaffold-state.yaml
        created_at="2026-05-12T00:00:00Z",
    )

    # Verificar: project_path = target_dir (não concatena)
    assert cfg.project_path == project_dir.resolve()


def test_project_path_normal_mode_concatenates(tmp_path: Path):
    """
    ProjectConfig.project_path em modo normal (sem .scaffold-state.yaml) concatena nome.

    Cenário:
      - target_dir NÃO tem .scaffold-state.yaml
      - target_dir.name ≠ project_name

    Comportamento esperado:
      - project_path = target_dir / project_name (concatenação normal)
    """
    # Setup
    parent = tmp_path / "projects"
    parent.mkdir()

    # NÃO criar .scaffold-state.yaml

    # Criar ProjectConfig
    cfg = ProjectConfig(
        project_name="my-api",
        project_title="My API",
        description="Test",
        domain="programming",
        language="python",
        github_repo=None,
        shared_dir=tmp_path / ".copilot-shared",
        target_dir=parent,  # NÃO tem .scaffold-state.yaml
        created_at="2026-05-12T00:00:00Z",
    )

    # Verificar: project_path = parent / project_name (concatenação)
    assert cfg.project_path == parent / "my-api"


def test_upgrade_in_place_preserves_all_state_fields(tmp_path: Path):
    """
    Upgrade in-place preserva todos os campos do state (título, descrição, profiles, etc).

    Cenário:
      - State tem múltiplos profiles aplicados
      - Upgrade in-place

    Comportamento esperado:
      - Todos os campos do state preservados no ProjectConfig
      - project_path aponta para diretório correto
    """
    # Setup
    project_dir = tmp_path / "complex-project"
    project_dir.mkdir()

    state = {
        "scaffold_version": "1.0.0",
        "created_at": "2026-04-01T10:00:00Z",
        "updated_at": "2026-05-12T18:00:00Z",
        "project": {
            "name": "sistema-complexo",
            "title": "Sistema Complexo de Produção",
            "description": "Sistema de alta complexidade com múltiplos componentes",
            "domain": "infrastructure",
            "language": "typescript",
            "github_repo": "https://github.com/user/sistema-complexo",
        },
        "paths": {
            "target_dir": str(tmp_path),
            "shared_dir": "/home/user/.copilot-shared",
        },
        "profiles_applied": [
            "devops-infrastructure",
            "devops-programming",
            "devops-analysis",
            "devops-security",
        ],
        "template_versions": {
            "agent-file-template.md": "1.0.0",
        },
    }

    # Escrever state
    state_file = project_dir / ".scaffold-state.yaml"
    with state_file.open("w") as f:
        yaml.dump(state, f)

    # Config from state (upgrade in-place)
    cfg = config_from_state(state, override_target=project_dir)

    # Verificar campos preservados
    assert cfg.project_name == "sistema-complexo"
    assert cfg.project_title == "Sistema Complexo de Produção"
    assert cfg.description == "Sistema de alta complexidade com múltiplos componentes"
    assert cfg.domain == "infrastructure"
    assert cfg.language == "typescript"
    assert cfg.github_repo == "https://github.com/user/sistema-complexo"
    assert cfg.created_at == "2026-04-01T10:00:00Z"
    assert cfg.extra_profiles == [
        "devops-infrastructure",
        "devops-programming",
        "devops-analysis",
        "devops-security",
    ]

    # Verificar paths corretos
    assert cfg.target_dir == project_dir
    assert cfg.project_path == project_dir.resolve()
