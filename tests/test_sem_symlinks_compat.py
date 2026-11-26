# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_sem_symlinks_compat.py
TITULO: Os caminhos de compatibilidade do ADR-003 não existem mais
DATA: 26/11/2026 13:24
MODIFICADO: 26/11/2026 13:26
VERSÃO: 1.0.0
DEPEND: pytest, git
STATUS: DEV

ADR-003 fatia 7. ``.github/templates/*`` e ``profile-descriptors`` eram
symlinks para ``scaffold/templates/{project,base-configs/common}`` e
``scaffold/profiles``, mantidos só enquanto testes e configs usavam os
caminhos antigos. Com a migração:

- os symlinks não existem;
- nenhum arquivo ativo (código, testes, configs, CI, README/QUICKSTART) cita
  os caminhos antigos. Documentos históricos (CHANGELOG, TODO, bugs, debates,
  ADRs) ficam de fora, porque registram o passado.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

_CAMINHOS_ANTIGOS = (".github/templates", "profile-descriptors")

_ARQUIVOS_ATIVOS = (
    "scripts",
    "tests",
    "scaffold",
    "Makefile",
    ".github/workflows",
    ".github/dependabot.yml",
    # .gitleaks.toml fica de fora: a allowlist de .github/templates/ ainda
    # cobre commits antigos na varredura do histórico (make secrets-scan).
    ".scaffold-config.json",
    ".scaffold-config.example.json",
    "README.md",
    "QUICKSTART.md",
    "docs/copilot/PROFILE-DESCRIPTOR-SCHEMA.md",
)

# Uso como caminho (não o termo "profile-descriptors" como conceito).
_REFERENCIA_ANTIGA = re.compile(
    r"profile-descriptors/"
    r"|[\"']profile-descriptors[\"']"
    r"|\.github/templates"
    r"|\\\.github/templates"
    r"|\"\.github\"\s*/\s*\"templates\""
)


@pytest.mark.parametrize("rel", _CAMINHOS_ANTIGOS)
def test_caminho_de_compatibilidade_removido(rel: str) -> None:
    alvo = _PROJECT_ROOT / rel
    assert not alvo.is_symlink() and not alvo.exists(), f"{rel} ainda existe"


def test_nenhum_arquivo_ativo_cita_caminho_antigo() -> None:
    proc = subprocess.run(  # noqa: S603
        ["git", "ls-files", "-z", "--", *_ARQUIVOS_ATIVOS],  # noqa: S607
        cwd=_PROJECT_ROOT,
        capture_output=True,
        check=True,
    )
    proprio = Path(__file__).resolve().relative_to(_PROJECT_ROOT).as_posix()
    achados: list[str] = []
    for rel in proc.stdout.decode().split("\0"):
        if not rel or rel == proprio:
            continue
        caminho = _PROJECT_ROOT / rel
        if caminho.is_symlink() or not caminho.is_file():
            continue
        try:
            texto = caminho.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, linha in enumerate(texto.splitlines(), 1):
            if _REFERENCIA_ANTIGA.search(linha):
                achados.append(f"{rel}:{n}: {linha.strip()[:100]}")
    assert not achados, "referências aos caminhos antigos:\n" + "\n".join(achados)
