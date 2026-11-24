# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_vscode_shell_integration.py
TITULO: Shell integration do terminal VS Code no settings.json gerado
DATA: 24/11/2026 11:12
MODIFICADO: 24/11/2026 15:00
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Item do backlog (docs/planning/lembrete.md — "shell integration"): todo projeto
gerado passa a declarar explicitamente a shell integration do terminal
(`terminal.integrated.shellIntegration.*`), em qualquer domínio/linguagem, sem
apagar configurações do usuário num settings.json já existente.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib import vscode  # noqa: E402

_ENABLED = "terminal.integrated.shellIntegration.enabled"
_DECORATIONS = "terminal.integrated.shellIntegration.decorationsEnabled"


def _settings(cfg) -> dict:
    return json.loads(
        (cfg.project_path / ".vscode" / "settings.json").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize(
    ("domain", "language"),
    [
        ("programming", "python"),
        ("programming", "typescript"),
        ("infrastructure", "other"),
        ("analysis", "python"),
    ],
)
def test_settings_gerado_habilita_shell_integration(
    make_project_config, domain, language
) -> None:
    cfg = make_project_config(domain, language)
    item = vscode.generate_settings(cfg)

    assert item.status == "created"
    settings = _settings(cfg)
    assert settings[_ENABLED] is True
    assert settings[_DECORATIONS] == "both"


def test_settings_existente_recebe_shell_integration_sem_perder_chaves(
    make_project_config,
) -> None:
    cfg = make_project_config("programming", "python")
    dest = cfg.project_path / ".vscode" / "settings.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps({"workbench.colorTheme": "Minha Tema"}) + "\n", encoding="utf-8"
    )

    vscode.generate_settings(cfg)

    settings = _settings(cfg)
    assert settings["workbench.colorTheme"] == "Minha Tema"
    assert settings[_ENABLED] is True


def test_settings_existente_preserva_escolha_do_usuario(make_project_config) -> None:
    """Quem desligou a shell integration de propósito não é sobrescrito."""
    cfg = make_project_config("programming", "python")
    dest = cfg.project_path / ".vscode" / "settings.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({_ENABLED: False}) + "\n", encoding="utf-8")

    vscode.generate_settings(cfg)

    assert _settings(cfg)[_ENABLED] is False
