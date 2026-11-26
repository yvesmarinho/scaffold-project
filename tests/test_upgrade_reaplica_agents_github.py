# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_upgrade_reaplica_agents_github.py
TITULO: O upgrade reaplica agents e templates GitHub como a criação
DATA: 26/11/2026 12:40
MODIFICADO: 26/11/2026 12:13
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

ADR-003 fatia 6. Antes, o ``--upgrade`` não chamava ``copy_custom_agents`` nem
``copy_github_templates``. Projetos antigos nunca recebiam agents novos nem
templates GitHub (CONTRIBUTING, ISSUE_TEMPLATE, PR template...).

Contrato:
- arquivo ausente é recriado;
- arquivo alterado pelo usuário não é tocado sem ``--force`` (``drift``); nos
  agents vale o merge do BUG-16 (seções customizadas preservadas);
- ``--upgrade --force`` mantém o ``.github/copilot-instructions.md`` **gerado
  para o projeto**. Antes, a cópia estática (as instruções do próprio scaffold)
  o sobrescrevia.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_AGENT = ".github/agents/adr-reviewer.agent.md"
_ISSUE = ".github/ISSUE_TEMPLATE/bug_report.md"
_CONTRIB = "CONTRIBUTING.md"


def _scaffold(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "SCAFFOLD_LOGS_DIR": str(cwd / "_logs"),
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_PROJECT_ROOT / "scripts" / "scaffold.py"), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=300,
    )


@pytest.fixture
def projeto(tmp_path: Path) -> Path:
    proc = _scaffold(
        "new",
        "--ci",
        "--name",
        "p-up6",
        "--domain",
        "programming",
        "--language",
        "python",
        "--ai-assistant",
        "copilot",
        "--shared-dir",
        str(tmp_path / "_shared"),
        "--target-dir",
        str(tmp_path),
        cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr[-1500:]
    return tmp_path / "p-up6"


def _upgrade(proj: Path, *extra: str) -> None:
    proc = _scaffold(
        "--upgrade", "--ci", "--target-dir", str(proj), *extra, cwd=proj.parent
    )
    assert proc.returncode == 0, proc.stderr[-1500:]


def test_upgrade_recria_agent_e_templates_github_ausentes(projeto: Path) -> None:
    for rel in (_AGENT, _ISSUE, _CONTRIB):
        assert (projeto / rel).is_file(), f"{rel} não foi gerado"
        (projeto / rel).unlink()

    _upgrade(projeto)

    for rel in (_AGENT, _ISSUE, _CONTRIB):
        assert (projeto / rel).is_file(), f"upgrade não recriou {rel}"


def test_upgrade_sem_force_nao_toca_arquivo_editado(projeto: Path) -> None:
    (projeto / _CONTRIB).write_text("editado pelo usuário\n", encoding="utf-8")

    _upgrade(projeto)

    assert (projeto / _CONTRIB).read_text(encoding="utf-8") == "editado pelo usuário\n"


def test_upgrade_preserva_secao_customizada_do_agent(projeto: Path) -> None:
    """Agents passam pelo CopilotAgentMerger (BUG-16): seção do usuário fica."""
    agent = projeto / _AGENT
    original = agent.read_text(encoding="utf-8")
    agent.write_text(
        original + "\n## Regras da equipe\n\nNão apagar.\n", encoding="utf-8"
    )

    _upgrade(projeto)

    texto = agent.read_text(encoding="utf-8")
    assert "## Regras da equipe" in texto
    assert "Não apagar." in texto


def test_upgrade_force_mantem_copilot_instructions_do_projeto(projeto: Path) -> None:
    instr = projeto / ".github" / "copilot-instructions.md"
    assert "Projeto: p-up6" in instr.read_text(encoding="utf-8")

    _upgrade(projeto, "--force")

    texto = instr.read_text(encoding="utf-8")
    assert "Projeto: p-up6" in texto, "sobrescrito pela cópia estática do scaffold"
    assert "SPECKIT START" not in texto
