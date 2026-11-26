# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_summary_sem_prompts.py
TITULO: PROJECT_CREATION_SUMMARY não cita prompt files (ADR-005)
DATA: 26/11/2026 14:40
MODIFICADO: 26/11/2026 16:36
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Desde o ADR-005 os projetos gerados não têm ``.github/prompts/``: os rituais
de sessão e perfis de domínio são skills em ``.github/skills/``. O resumo de
criação ainda linkava ``.github/prompts/`` (link quebrado) e listava
"9 prompts" na árvore e nas características.
"""

from __future__ import annotations

import re

from scripts.lib import project


def _summary(make_project_config) -> str:
    cfg = make_project_config("programming", "python")
    (cfg.project_path / "docs").mkdir(parents=True, exist_ok=True)
    item = project.generate_project_creation_summary(cfg)
    assert item.status == "created", item.message
    return (cfg.project_path / "docs" / "PROJECT_CREATION_SUMMARY.md").read_text(
        encoding="utf-8"
    )


def test_resumo_nao_cita_prompts(make_project_config) -> None:
    texto = _summary(make_project_config)

    assert not re.search(r"prompts?\b", texto, re.IGNORECASE), [
        linha for linha in texto.splitlines() if re.search(r"prompt", linha, re.I)
    ]


def test_resumo_linka_skills(make_project_config) -> None:
    texto = _summary(make_project_config)

    assert "[.github/skills/](../.github/skills/)" in texto
