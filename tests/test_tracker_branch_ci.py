# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_tracker_branch_ci.py
TITULO: session-time-tracker em detached HEAD / sem TTY (ambiente de CI)
DATA: 24/11/2026 10:24
MODIFICADO: 24/11/2026 15:00
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

Bugs cobertos:
- ``_get_current_branch`` devolvia ``"HEAD"`` em detached HEAD (checkout de PR no
  GitHub Actions); o tracker tratava isso como branch fora do padrão.
- Com branch fora do padrão e sem TTY, o ``input()`` de confirmação estourava
  ``EOFError`` com traceback em vez de recusar de forma limpa.
- A suíte do tracker dependia da branch real do repositório (falhava em
  detached HEAD ou em branch fora da convenção).
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TRACKER = _PROJECT_ROOT / "scripts" / "session-time-tracker.py"

_GIT = shutil.which("git") or "git"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git indisponível")


@pytest.fixture(scope="module")
def tracker() -> ModuleType:
    spec = importlib.util.spec_from_file_location("session_time_tracker_ci", _TRACKER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> None:
    subprocess.run(  # noqa: S603
        [_GIT, "-c", "user.name=t", "-c", "user.email=t@t", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def _repo(tmp_path: Path, branch: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", branch)
    _git(repo, "commit", "-q", "--allow-empty", "-m", "init")
    return repo


def test_detached_head_nao_e_branch(
    tracker: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _repo(tmp_path, "main")
    _git(repo, "checkout", "-q", "--detach")
    monkeypatch.chdir(repo)
    assert tracker._get_current_branch() is None


def test_branch_normal_continua_detectada(
    tracker: ModuleType, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(_repo(tmp_path, "fix/algo"))
    assert tracker._get_current_branch() == "fix/algo"


def _start(cwd: Path, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "SCAFFOLD_SESSION_TIME_DIR": str(tmp_path / "st")}
    return subprocess.run(  # noqa: S603
        [sys.executable, str(_TRACKER), "start"],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )


def test_start_em_detached_head_inicia_sessao(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "main")
    _git(repo, "checkout", "-q", "--detach")
    result = _start(repo, tmp_path)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "st" / "current.json").exists()


def test_branch_fora_do_padrao_sem_tty_recusa_sem_traceback(tmp_path: Path) -> None:
    result = _start(_repo(tmp_path, "Nome_Ruim"), tmp_path)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "EOFError" not in result.stderr
    assert "Sessão não iniciada" in result.stderr
    assert not (tmp_path / "st" / "current.json").exists()


@pytest.mark.parametrize(
    "arquivo",
    [
        "tests/test_session_time_tracker.py",
        "tests/test_isolamento_memory_session_time.py",
    ],
)
def test_suite_do_tracker_independe_da_branch_real(
    tmp_path: Path, arquivo: str
) -> None:
    """Roda a suíte do tracker numa cópia do repo em branch fora da convenção."""
    copia = tmp_path / "copia"
    shutil.copytree(
        _PROJECT_ROOT,
        copia,
        ignore=shutil.ignore_patterns(
            ".git",
            ".venv",
            "graphify-out",
            "htmlcov",
            "logs",
            "tmp",
            "*cache*",
            "node_modules",
        ),
    )
    _git(copia, "init", "-q", "-b", "Nome_Ruim")
    _git(copia, "commit", "-q", "--allow-empty", "-m", "init")
    result = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--no-cov",
            arquivo,
        ],
        capture_output=True,
        text=True,
        cwd=copia,
        stdin=subprocess.DEVNULL,
        timeout=300,
    )
    assert result.returncode == 0, result.stdout[-3000:]
