# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_templates_distribuicao_isolados.py
TITULO: O gerador só lê fontes de distribuição de scripts/ e scaffold/
DATA: 26/11/2026 11:34
MODIFICADO: 26/11/2026 11:36
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

ADR-003 fatia 5: as configs do próprio repositório (``.claude/``,
``.github/copilot-instructions.md``, ``.copilot-rules.md``, ``.specify/templates``,
``.github/ISSUE_TEMPLATE/*.md`` e ``docs/guides/BRANCH_PROTECTION_SETUP.md``) deixam
de ser fonte de template. As versões de distribuição ficam em ``scaffold/templates/``.

Critério: uma árvore com **apenas** os arquivos versionados de ``scripts/`` e
``scaffold/`` gera o mesmo projeto que o repositório completo, com os mesmos
arquivos e os mesmos bytes nas fontes migradas. Se o gerador ainda ler algo
das configs do repo, o arquivo some (ou muda) no projeto da árvore isolada.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_NOME = "demo-iso"
_NEW_ARGS = [
    "new",
    "--ci",
    "--name",
    _NOME,
    "--domain",
    "programming",
    "--language",
    "python",
]
# Variam a cada execução (timestamps), não indicam fonte faltando.
_VOLATEIS = ("logs/", ".git/")

# Arquivos do projeto gerado cujas fontes eram configs do repositório.
_MIGRADOS = [
    ".claude/commands/session-start..md",
    ".github/copilot-instructions.md",
    ".copilot-rules.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/improvement.md",
    "docs/BRANCH_PROTECTION_SETUP.md",
]


def _arvore_isolada(destino: Path) -> Path:
    """Copia só os arquivos versionados de scripts/ e scaffold/, preservando symlinks."""
    listados = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-z", "scripts", "scaffold"],  # noqa: S607
        cwd=_PROJECT_ROOT,
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    for bruto in filter(None, listados):
        rel = Path(bruto.decode())
        origem, alvo = _PROJECT_ROOT / rel, destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        if origem.is_symlink():
            alvo.symlink_to(os.readlink(origem))
        elif origem.is_file():
            shutil.copy2(origem, alvo)
    return destino


def _scaffold(root: Path, alvo: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "SCAFFOLD_LOGS_DIR": str(cwd / "_logs"),
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(  # noqa: S603
        [
            sys.executable,
            str(root / "scripts" / "scaffold.py"),
            *_NEW_ARGS,
            "--target-dir",
            str(alvo),
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=300,
    )


_ISO_TS = re.compile(rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}")


def _sem_timestamp(conteudo: bytes) -> bytes:
    """Neutraliza o horário de geração (ex.: rodapé do copilot-instructions.md)."""
    return _ISO_TS.sub(b"<TS>", conteudo)


def _arquivos(projeto: Path) -> set[str]:
    return {
        str(p.relative_to(projeto))
        for p in projeto.rglob("*")
        if (p.is_file() or p.is_symlink())
        and not str(p.relative_to(projeto)).startswith(_VOLATEIS)
    }


@pytest.fixture(scope="module")
def projetos(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """Gera o mesmo projeto pelo repo completo e pela árvore isolada."""
    base = tmp_path_factory.mktemp("iso")
    arvore = _arvore_isolada(base / "arvore")
    alvo_repo, alvo_iso = base / "repo", base / "iso"
    alvo_repo.mkdir()
    alvo_iso.mkdir()
    via_repo = _scaffold(_PROJECT_ROOT, alvo_repo, base)
    via_iso = _scaffold(arvore, alvo_iso, base)
    assert via_repo.returncode == 0, via_repo.stderr[-1500:]
    assert via_iso.returncode == 0, via_iso.stderr[-1500:]
    return alvo_repo / _NOME, alvo_iso / _NOME


def test_arvore_isolada_gera_os_mesmos_arquivos(projetos: tuple[Path, Path]) -> None:
    repo, iso = projetos
    assert len(_arquivos(repo)) > 100
    faltando = _arquivos(repo) - _arquivos(iso)
    sobrando = _arquivos(iso) - _arquivos(repo)
    assert not faltando, f"fontes ainda lidas fora de scaffold/: {sorted(faltando)}"
    assert not sobrando, f"extras na árvore isolada: {sorted(sobrando)}"


@pytest.mark.parametrize("rel", _MIGRADOS)
def test_fonte_migrada_tem_os_mesmos_bytes(
    projetos: tuple[Path, Path], rel: str
) -> None:
    repo, iso = projetos
    assert (repo / rel).is_file(), f"{rel} não foi gerado pelo repositório"
    assert (iso / rel).is_file(), f"{rel} ausente: fonte ainda está fora de scaffold/"
    assert _sem_timestamp((iso / rel).read_bytes()) == _sem_timestamp(
        (repo / rel).read_bytes()
    )


def test_constitution_gerada_na_arvore_isolada(projetos: tuple[Path, Path]) -> None:
    _repo, iso = projetos
    constitution = iso / ".specify" / "memory" / "constitution.md"
    assert constitution.is_file(), "constitution-template ainda lido de .specify/"
