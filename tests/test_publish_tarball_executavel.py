# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_publish_tarball_executavel.py
TITULO: O tarball do --publish precisa ser um gerador completo e executável
DATA: 24/11/2026 12:10
MODIFICADO: 24/11/2026 11:56
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bug coberto (fatia 1 do ADR-003): ``lib/publish._INCLUDE_PATTERNS`` usava
``scripts/lib/*.py`` (não recursivo). O tarball saía sem ``scripts/lib/flows/`` e
``scripts/lib/ai/`` — ``scaffold.py`` extraído falhava no import — e sem várias
fontes que o gerador copia (scripts de sessão/memory, ``.claude/``,
``.specify/templates/`` ...). Também entravam caches locais (``.ruff_cache``).

Critério: o projeto gerado **a partir do tarball extraído** tem exatamente os
mesmos arquivos que o gerado **a partir do repositório**, com os mesmos argumentos.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib.publish import publish_template  # noqa: E402

_NEW_ARGS = ["new", "--ci", "--name", "demo-pub", "--domain", "programming", "--language", "python"]
# Variam a cada execução (timestamps), não indicam arquivo faltando no tarball.
_VOLATEIS = ("logs/", ".git/")
_CACHES = {".ruff_cache", ".mypy_cache", ".pytest_cache", "htmlcov", ".coverage"}


@pytest.fixture(scope="module")
def extraido(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("pub")
    result = publish_template(output_dir=out, project_root=_PROJECT_ROOT)
    root = tmp_path_factory.mktemp("extraido")
    with tarfile.open(result.tarball_path, "r:gz") as tar:
        tar.extractall(root, filter="data")
    return root


def _scaffold(root: Path, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "SCAFFOLD_LOGS_DIR": str(cwd / "_logs"),
        # Hermético: o commit inicial do projeto gerado não depende do git config da máquina.
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    return subprocess.run(  # noqa: S603
        [sys.executable, str(root / "scripts" / "scaffold.py"), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        timeout=300,
    )


def _arquivos(projeto: Path) -> set[str]:
    return {
        str(p.relative_to(projeto))
        for p in projeto.rglob("*")
        if (p.is_file() or p.is_symlink())
        and not str(p.relative_to(projeto)).startswith(_VOLATEIS)
    }


def test_tarball_extraido_lista_perfis(extraido: Path, tmp_path: Path) -> None:
    proc = _scaffold(extraido, "--list-profiles", "--json", cwd=tmp_path)
    assert proc.returncode == 0, proc.stderr[-1500:]


def test_tarball_gera_o_mesmo_projeto_que_o_repositorio(extraido: Path, tmp_path: Path) -> None:
    alvo_repo, alvo_pub = tmp_path / "repo", tmp_path / "pub"
    alvo_repo.mkdir()
    alvo_pub.mkdir()
    via_repo = _scaffold(_PROJECT_ROOT, *_NEW_ARGS, "--target-dir", str(alvo_repo), cwd=tmp_path)
    via_pub = _scaffold(extraido, *_NEW_ARGS, "--target-dir", str(alvo_pub), cwd=tmp_path)

    # Sem isto o teste passaria vazio se as duas gerações falhassem igual.
    erros = [ln for ln in via_repo.stdout.splitlines() if "error" in ln]
    assert via_repo.returncode == 0, erros + [via_repo.stderr[-800:]]
    assert via_pub.returncode == 0, via_pub.stderr[-1500:]
    assert len(_arquivos(alvo_repo / "demo-pub")) > 100
    faltando = _arquivos(alvo_repo / "demo-pub") - _arquivos(alvo_pub / "demo-pub")
    sobrando = _arquivos(alvo_pub / "demo-pub") - _arquivos(alvo_repo / "demo-pub")
    assert not faltando, f"ausentes no projeto gerado pelo tarball: {sorted(faltando)[:40]}"
    assert not sobrando, f"extras no projeto gerado pelo tarball: {sorted(sobrando)[:40]}"


def test_tarball_sem_caches_locais(extraido: Path) -> None:
    caches = [p for p in extraido.rglob("*") if p.name in _CACHES]
    assert not caches, [str(p.relative_to(extraido)) for p in caches[:20]]
