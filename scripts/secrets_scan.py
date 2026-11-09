# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: secrets_scan.py
TITULO: Varredura local de segredos com gitleaks (substitui o GitGuardian)
DATA: 09/11/2026 15:45
MODIFICADO: 09/11/2026 15:42
VERSÃO: 1.0.0
DEPEND: gitleaks >= 8.19 (binário no PATH)
STATUS: DEV

Histórico:
    1.0.0 (09/11/2026) — versão inicial; modos history, tree e staged.

Uso:
    uv run python -m scripts.secrets_scan --mode history   # todo o histórico git
    uv run python -m scripts.secrets_scan --mode tree      # arquivos atuais
    uv run python -m scripts.secrets_scan --mode staged    # pré-commit
    make secrets-scan

Códigos de saída:
    0 — nenhum vazamento
    1 — vazamento encontrado
    2 — erro de execução (gitleaks ausente, timeout, configuração)

O gitleaks roda sempre com --redact; o valor do segredo nunca é logado.
"""

import argparse
import logging
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from json import JSONDecodeError, loads
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / ".gitleaks.toml"
VALID_MODES = ("history", "tree", "staged")
TIMEOUT_SECONDS = 300

log = logging.getLogger(__name__)


class SecretsScanError(Exception):
    """Erro base da varredura de segredos."""


class InvalidScanModeError(SecretsScanError):
    """Modo de varredura não suportado."""


class GitleaksNotFoundError(SecretsScanError):
    """Binário gitleaks não encontrado no PATH."""


class GitleaksTimeoutError(SecretsScanError):
    """gitleaks excedeu o tempo limite."""


class GitleaksExecutionError(SecretsScanError):
    """gitleaks falhou ou gerou relatório inválido."""


@dataclass(frozen=True)
class Finding:
    """Achado sem o valor do segredo."""

    rule: str
    location: str
    commit: str = ""


@dataclass
class ScanResult:
    """Resultado agregado de uma varredura."""

    mode: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def leaks(self) -> int:
        return len(self.findings)

    @property
    def clean(self) -> bool:
        return not self.findings


def config_logging() -> bool:
    if logging.getLogger().hasHandlers():
        return True
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    )
    return True


def build_command(mode: str, repo: Path, report: Path) -> list[str]:
    """
    Monta a linha de comando do gitleaks para o modo pedido.

    :param mode: history | tree | staged.
    :type mode: str
    :param repo: Raiz do repositório.
    :type repo: Path
    :param report: Caminho do relatório JSON.
    :type report: Path
    :return: Lista de argumentos para subprocess.
    :rtype: list[str]

    :Example:

    >>> build_command("tree", Path("."), Path("r.json"))[:2]
    ['gitleaks', 'dir']
    """
    if mode not in VALID_MODES:
        raise InvalidScanModeError(f"modo inválido: {mode!r} (use {', '.join(VALID_MODES)})")
    if mode == "tree":
        base = ["gitleaks", "dir", "."]
    elif mode == "staged":
        base = ["gitleaks", "git", "--pre-commit", "--staged", str(repo)]
    else:
        base = ["gitleaks", "git", str(repo)]
    return [
        *base,
        "--redact",
        "--no-banner",
        "-c",
        str(CONFIG_FILE),
        "-f",
        "json",
        "-r",
        str(report),
        "--exit-code",
        "1",
    ]


def _parse_report(report: Path, mode: str) -> ScanResult:
    try:
        raw = loads(report.read_text(encoding="utf-8") or "[]")
    except (OSError, JSONDecodeError) as error:
        raise GitleaksExecutionError(f"relatório do gitleaks ilegível: {error}") from error
    findings = [
        Finding(
            rule=item.get("RuleID", "?"),
            location=f"{item.get('File', '?')}:{item.get('StartLine', '?')}",
            commit=(item.get("Commit") or "")[:7],
        )
        for item in raw
    ]
    return ScanResult(mode=mode, findings=findings)


def run_scan(
    repo: Path,
    mode: str,
    *,
    which: Callable[[str], str | None] | None = None,
    runner: Callable[..., subprocess.CompletedProcess] | None = None,
) -> ScanResult:
    """
    Executa o gitleaks e devolve os achados (sem o segredo).

    :param repo: Raiz do repositório a varrer.
    :type repo: Path
    :param mode: history | tree | staged.
    :type mode: str
    :return: Resultado da varredura.
    :rtype: ScanResult
    :raises InvalidScanModeError: modo não suportado.
    :raises NotADirectoryError: repo não existe.
    :raises GitleaksNotFoundError: gitleaks fora do PATH.
    :raises GitleaksTimeoutError: tempo limite excedido.
    :raises GitleaksExecutionError: falha do gitleaks ou relatório inválido.
    """
    which = which or shutil.which
    runner = runner or subprocess.run
    if mode not in VALID_MODES:
        raise InvalidScanModeError(f"modo inválido: {mode!r} (use {', '.join(VALID_MODES)})")
    if not repo.is_dir():
        raise NotADirectoryError(f"repositório não encontrado: {repo}")
    if not which("gitleaks"):
        raise GitleaksNotFoundError("gitleaks não encontrado no PATH — instale em ~/.local/bin")

    with TemporaryDirectory() as tmp:
        report = Path(tmp) / "gitleaks-report.json"
        cmd = build_command(mode, repo, report)
        log.info("==> VAR: cmd TYPE: %s, CONTENT: %s", type(cmd).__name__, " ".join(cmd[:3]))
        try:
            proc = runner(
                cmd, cwd=repo, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False
            )
        except subprocess.TimeoutExpired as error:
            raise GitleaksTimeoutError(f"gitleaks excedeu {TIMEOUT_SECONDS}s") from error
        if proc.returncode not in (0, 1):
            raise GitleaksExecutionError(
                f"gitleaks saiu com código {proc.returncode}: {proc.stderr.strip()[:300]}"
            )
        if not report.exists():
            return ScanResult(mode=mode)
        return _parse_report(report, mode)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI; devolve o código de saída."""
    config_logging()
    parser = argparse.ArgumentParser(description="Varredura local de segredos (gitleaks)")
    parser.add_argument("--mode", choices=VALID_MODES, default="history")
    parser.add_argument("--repo", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args(argv)

    try:
        result = run_scan(args.repo, args.mode)
    except (SecretsScanError, NotADirectoryError) as error:
        log.error("Varredura não executada: %s", error)
        return 2

    if result.clean:
        log.info("Nenhum segredo encontrado (modo %s)", result.mode)
        return 0
    for item in result.findings:
        suffix = f" commit={item.commit}" if item.commit else ""
        log.warning("Possível segredo: %s em %s%s", item.rule, item.location, suffix)
    log.error("%d possível(is) segredo(s) encontrado(s) — remova e rotacione se for real", result.leaks)
    return 1


if __name__ == "__main__":
    sys.exit(main())
