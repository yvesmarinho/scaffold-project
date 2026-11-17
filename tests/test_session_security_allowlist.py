# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: test_session_security_allowlist.py
TITULO: Falsos positivos do security-scan de sessão (lib/session_security)
DATA: 17/11/2026 16:39
MODIFICADO: 17/11/2026 16:39
VERSÃO: 1.0.0
DEPEND: pytest
STATUS: DEV

Bug coberto: o scan casa nomes de arquivo (``*token*``, ``*secret*``...) e
acusava caches de ferramentas (``.mypy_cache``, ``.ruff_cache``), o ``tmp/``
local, o próprio scanner de secrets e os exemplos de ``scaffold/templates/``,
deixando ``clean: false`` sem nenhum segredo real. Os testes de "ainda acusa"
garantem que a allowlist não abre brecha para arquivos sensíveis de verdade.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.session_context import SessionPaths
from scripts.lib.session_security import scan_workspace


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "ws"
    root.mkdir()
    (root / ".gitignore").write_text(".secrets/\n", encoding="utf-8")
    return root


def _write(root: Path, relative: str, content: str = "x") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _flagged(root: Path) -> set[str]:
    result = scan_workspace(SessionPaths.from_root(root))
    return {item["path"] for item in result["findings"]}


# --- Deve ignorar -----------------------------------------------------------


@pytest.mark.parametrize(
    "relative",
    [
        ".mypy_cache/3.12/token.data.json",
        ".ruff_cache/0.6/secret.bin",
        "tmp/commit-secrets-scan.txt",
        "scripts/secrets_scan.py",
        "tests/test_secrets_scan.py",
        "scaffold/templates/project/lgpd/.github/workflows/secret-scan.yml",
        "scaffold/templates/project/airflow/.env.airflow.example",
    ],
)
def test_falso_positivo_conhecido_nao_e_acusado(tmp_path: Path, relative: str) -> None:
    root = _workspace(tmp_path)
    _write(root, relative)

    assert _flagged(root) == set()


def test_env_example_de_template_nao_e_acusado(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    _write(root, "scaffold/templates/project/flask/.env.example", "SECRET_KEY=abc123\n")

    result = scan_workspace(SessionPaths.from_root(root))

    assert result["clean"] is True


# --- Deve continuar acusando ------------------------------------------------


@pytest.mark.parametrize(
    "relative",
    [
        "config/prod.key",
        "deploy/db_password.txt",
        "src/api_token.json",
        "app.log",
        # o nome isento é só o do scanner, não qualquer arquivo em scripts/ ou tests/
        "scripts/secrets.json",
        "tests/fixtures/token.txt",
        # só a raiz scaffold/templates/ é isenta, não um "templates" qualquer
        "src/templates/secret.yml",
    ],
)
def test_arquivo_sensivel_real_continua_acusado(tmp_path: Path, relative: str) -> None:
    root = _workspace(tmp_path)
    _write(root, relative)

    assert relative in _flagged(root)


def test_env_example_fora_de_template_com_valor_real_continua_acusado(
    tmp_path: Path,
) -> None:
    root = _workspace(tmp_path)
    _write(root, ".env.example", "SECRET_KEY=abc123\n")

    result = scan_workspace(SessionPaths.from_root(root))

    assert result["findings_by_kind"].get("env-example-value") == 1
