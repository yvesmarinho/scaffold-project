# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_conftest_nao_altera_gitconfig.py
TITULO: A suíte de testes não pode alterar o ~/.gitconfig real do usuário
DATA: 24/11/2026 14:34
MODIFICADO: 24/11/2026 15:00
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

Bug (desde 39a3e66, 20/05/2026): a fixture de sessão ``configure_git_for_tests``
rodava ``git config --global user.name "Test User"`` / ``user.email
test@example.com`` ANTES do isolamento de HOME (que é por teste). Cada execução da
suíte sobrescrevia a identidade git global da máquina — 76 commits do projeto
saíram como "Test User <test@example.com>". A fixture também carregava, por engano
de merge, o corpo da fixture ``mock_subprocess`` (com ``monkeypatch`` indefinido).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_IDENTIDADE = "[user]\n\tname = Pessoa Real\n\temail = real@exemplo.com\n"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git indisponível")


def test_suite_nao_altera_gitconfig_global(tmp_path: Path) -> None:
    home = tmp_path / "home-real"
    home.mkdir()
    gitconfig = home / ".gitconfig"
    gitconfig.write_text(_IDENTIDADE, encoding="utf-8")

    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("GIT_", "PYTEST_", "SCAFFOLD_"))
    }
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / ".config"))
    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--no-cov",
            "tests/test_example.py",
        ],
        cwd=_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert proc.returncode == 0, proc.stdout[-2000:]
    assert gitconfig.read_text(encoding="utf-8") == _IDENTIDADE


def test_identidade_de_teste_disponivel_na_sessao() -> None:
    """Commits feitos pelos testes continuam funcionando, sem tocar no global real."""
    nome = subprocess.run(  # noqa: S603
        [shutil.which("git") or "git", "config", "--global", "user.name"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert nome == "Test User"
    assert os.environ.get("GIT_CONFIG_GLOBAL"), "GIT_CONFIG_GLOBAL não configurado"
    assert (
        Path(os.environ["GIT_CONFIG_GLOBAL"]).resolve()
        != (Path.home() / ".gitconfig").resolve()
    )


def test_mock_subprocess_funciona(mock_subprocess) -> None:
    mock = mock_subprocess(stdout="saida", returncode=0)
    resultado = subprocess.run(["qualquer"])  # noqa: S603, S607
    assert resultado.stdout == "saida"
    assert mock.called


def test_nenhum_teste_grava_identidade_global() -> None:
    """Nenhum teste pode rodar `git config --global user.<x> <valor>` (escrita)."""
    import re

    escrita = re.compile(r'"--global",\s*"user\.(?:name|email)",\s*"')
    achados = [
        f"{arq.relative_to(_ROOT)}"
        for arq in sorted((_ROOT / "tests").rglob("*.py"))
        if escrita.search(arq.read_text(encoding="utf-8"))
    ]
    assert not achados, f"escrita na identidade git global: {achados}"
