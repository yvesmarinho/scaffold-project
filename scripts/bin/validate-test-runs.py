# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------
NOME..: validate-test-runs.py
LANG..: Python3
TITULO: Valida a estrutura dos projetos gerados pelo rotation script
DATA..: 24/06/2026 14:30
MODIFICADO: 24/11/2026 15:00
VERSÃO: 0.1.0
HOST..: local
LOCAL.: scripts/bin/
OBS...: Lê .scaffold-state.yaml de cada projeto em tmp/test-runs/,
        verifica invariantes estruturais e arquivos declarados nos
        descritores de perfil. Gera relatório por projeto + resumo final.

DEPEND: pyyaml (via uv), rich

-------------------------------------------------------------------------
Modifications.....:
 Date          Rev    Author           Description
 24/06/2026    1      scaffold         Elaboração

-------------------------------------------------------------------------
STATUS: DEV
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from rich import box
from rich.console import Console
from rich.table import Table

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_TEST_RUNS_DIR = _PROJECT_ROOT / "tmp" / "test-runs"
_PROFILES_DIR = _PROJECT_ROOT / "scaffold" / "profiles"

console = Console()


def config_logging() -> bool:
    logger = logging.getLogger()
    if logger.hasHandlers():
        return True
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    return True


# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Resultado de uma verificação individual."""

    label: str
    passed: bool
    message: str = ""


@dataclass
class ProjectReport:
    """Relatório completo de um projeto."""

    name: str
    path: Path
    domain: str = ""
    language: str = ""
    ai_assistant: str = ""
    profiles: list[str] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if not c.passed)

    @property
    def ok(self) -> bool:
        return self.failed == 0


# ---------------------------------------------------------------------------
# Leitura de estado e descritores
# ---------------------------------------------------------------------------


def _load_scaffold_state(project_path: Path) -> dict:
    """
    Lê .scaffold-state.yaml do projeto.

    :param project_path: Caminho raiz do projeto.
    :type project_path: Path
    :return: Dicionário com o estado, ou dict vazio em erro.
    :rtype: dict
    """
    logging.info("=== Função: %s ===", sys._getframe().f_code.co_name)
    state_file = project_path / ".scaffold-state.yaml"
    if not state_file.exists():
        return {}
    try:
        return yaml.safe_load(state_file.read_text(encoding="utf-8")) or {}
    except Exception as e:
        logging.error("Erro ao ler scaffold-state: %s", e)
        return {}


def _load_profile_descriptor(profile_name: str) -> dict:
    """
    Lê descriptor YAML de um perfil.

    :param profile_name: Nome do perfil (sem .yaml).
    :type profile_name: str
    :return: Dicionário com o descriptor, ou dict vazio se não encontrado.
    :rtype: dict
    """
    logging.info("=== Função: %s ===", sys._getframe().f_code.co_name)
    yaml_path = _PROFILES_DIR / f"{profile_name}.yaml"
    if not yaml_path.exists():
        return {}
    try:
        return yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        logging.error("Erro ao ler descriptor %s: %s", profile_name, e)
        return {}


# ---------------------------------------------------------------------------
# Verificações
# ---------------------------------------------------------------------------

# Sempre obrigatórios em qualquer projeto
_BASE_REQUIRED = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "Makefile",
    "objetivo.yaml",
    "mcp-questions.yaml",
    ".scaffold-state.yaml",
    ".gitignore",
    ".git",
    "docs",
    "src",
    "scripts",
    "logs",
    "tmp",
    ".vscode",
    ".specify",
    ".memory",
    ".secrets",
]

# Obrigatórios por AI assistant
_AI_REQUIRED: dict[str, list[str]] = {
    "claude": ["CLAUDE.md", ".claude"],
    "both": ["CLAUDE.md", ".claude", ".copilot-rules.md"],
    "copilot": [".copilot-rules.md"],
    "none": [],
}


def _check_base_structure(project_path: Path) -> list[CheckResult]:
    """
    Verifica arquivos e pastas sempre obrigatórios.

    :param project_path: Raiz do projeto.
    :type project_path: Path
    :return: Lista de resultados de verificação.
    :rtype: list[CheckResult]
    """
    logging.info("=== Função: %s ===", sys._getframe().f_code.co_name)
    results = []
    for item in _BASE_REQUIRED:
        p = project_path / item
        results.append(
            CheckResult(
                label=f"base/{item}",
                passed=p.exists(),
                message="" if p.exists() else "ausente",
            )
        )
    return results


def _check_ai_assets(project_path: Path, ai_assistant: str) -> list[CheckResult]:
    """
    Verifica arquivos obrigatórios conforme o AI assistant configurado.

    :param project_path: Raiz do projeto.
    :type project_path: Path
    :param ai_assistant: Valor do campo ai_assistant (claude, both, copilot, none).
    :type ai_assistant: str
    :return: Lista de resultados de verificação.
    :rtype: list[CheckResult]
    """
    logging.info("=== Função: %s ===", sys._getframe().f_code.co_name)
    required = _AI_REQUIRED.get(ai_assistant, [])
    results = []
    for item in required:
        p = project_path / item
        results.append(
            CheckResult(
                label=f"ai({ai_assistant})/{item}",
                passed=p.exists(),
                message="" if p.exists() else "ausente",
            )
        )
    return results


def _check_profile_files(
    project_path: Path, project_name: str, profiles: list[str]
) -> list[CheckResult]:
    """
    Para cada perfil aplicado, verifica se os arquivos required=true existem.
    Ignora entradas com source inline ou geradas por código.

    :param project_path: Raiz do projeto.
    :type project_path: Path
    :param project_name: Nome do projeto (para substituição de placeholders).
    :type project_name: str
    :param profiles: Lista de nomes de perfis aplicados.
    :type profiles: list[str]
    :return: Lista de resultados de verificação.
    :rtype: list[CheckResult]
    """
    logging.info("=== Função: %s ===", sys._getframe().f_code.co_name)
    results = []
    # Marcadores de entradas não-físicas (geradas por código ou shared)
    _INLINE_MARKERS = ("inline", "()", "templates.py:", "generate_")
    # Fontes gerenciadas externamente pelo --check (symlinks do .copilot-shared/)
    _EXTERNAL_SOURCES = (".copilot-shared/",)

    for profile_name in profiles:
        descriptor = _load_profile_descriptor(profile_name)
        if not descriptor:
            results.append(
                CheckResult(
                    label=f"profile/{profile_name}",
                    passed=False,
                    message="descriptor não encontrado",
                )
            )
            continue

        generates = descriptor.get("generates") or {}
        files = generates.get("files") or []

        for entry in files:
            if not isinstance(entry, dict):
                continue

            path_rel: str = entry.get("path", "")
            source: str = entry.get("source", "")
            required: bool = entry.get("required", True)

            if not path_rel or not required:
                continue

            # Pula diretórios (caminhos terminando em /)
            if path_rel.endswith("/"):
                continue

            # Pula entradas geradas por código (não são arquivos físicos em templates/)
            if any(marker in source for marker in _INLINE_MARKERS):
                continue

            # Pula symlinks gerenciados externamente pelo --check
            if any(source.startswith(ext) for ext in _EXTERNAL_SOURCES):
                continue

            # Substitui placeholder {project_name}
            resolved_path = path_rel.replace("{project_name}", project_name)

            p = project_path / resolved_path
            results.append(
                CheckResult(
                    label=f"profile/{profile_name}/{resolved_path}",
                    passed=p.exists(),
                    message="" if p.exists() else "ausente",
                )
            )

    return results


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------


def validate_project(project_path: Path) -> ProjectReport:
    """
    Executa todas as verificações em um projeto.

    :param project_path: Raiz do projeto a validar.
    :type project_path: Path
    :return: Relatório completo do projeto.
    :rtype: ProjectReport
    """
    logging.info("=== Função: %s ===", sys._getframe().f_code.co_name)
    report = ProjectReport(name=project_path.name, path=project_path)

    state = _load_scaffold_state(project_path)
    if not state:
        report.checks.append(
            CheckResult(
                label=".scaffold-state.yaml",
                passed=False,
                message="arquivo ausente ou inválido",
            )
        )
        return report

    project_info = state.get("project", {})
    report.domain = project_info.get("domain", "")
    report.language = project_info.get("language", "")
    report.ai_assistant = project_info.get("ai_assistant", "")
    report.profiles = state.get("profiles_applied", [])
    project_name = project_info.get("name", project_path.name)

    report.checks.extend(_check_base_structure(project_path))
    report.checks.extend(_check_ai_assets(project_path, report.ai_assistant))
    report.checks.extend(
        _check_profile_files(project_path, project_name, report.profiles)
    )

    return report


def discover_projects(test_runs_dir: Path) -> list[Path]:
    """
    Retorna subpastas de test_runs_dir que contenham .scaffold-state.yaml,
    ordenadas por nome.

    :param test_runs_dir: Diretório raiz dos projetos de teste.
    :type test_runs_dir: Path
    :return: Lista de caminhos de projeto.
    :rtype: list[Path]
    """
    logging.info("=== Função: %s ===", sys._getframe().f_code.co_name)
    if not test_runs_dir.exists():
        return []
    return sorted(
        p
        for p in test_runs_dir.iterdir()
        if p.is_dir() and (p / ".scaffold-state.yaml").exists()
    )


# ---------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------


def _print_project_report(report: ProjectReport, verbose: bool) -> None:
    """Exibe o resultado de um projeto na console."""
    status = (
        "[bold green]✅ OK[/bold green]"
        if report.ok
        else f"[bold red]❌ {report.failed} falha(s)[/bold red]"
    )
    meta = f"[dim]{report.domain}/{report.language}/{report.ai_assistant}[/dim]"
    console.print(f"\n  {status}  [bold]{report.name}[/bold]  {meta}")

    if not report.ok or verbose:
        table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
        table.add_column(width=4, no_wrap=True)
        table.add_column(style="dim", no_wrap=True)
        table.add_column()

        for check in report.checks:
            if check.passed and not verbose:
                continue
            icon = "✅" if check.passed else "❌"
            msg = f"[red]{check.message}[/red]" if check.message else ""
            table.add_row(icon, check.label, msg)

        console.print(table)


def _print_summary(reports: list[ProjectReport]) -> None:
    """Exibe tabela-resumo final."""
    table = Table(
        title="\n[bold]Resumo da Validação — test-runs[/bold]",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Projeto", style="cyan", no_wrap=True)
    table.add_column("Domain", style="dim", no_wrap=True)
    table.add_column("Lang", style="dim", no_wrap=True)
    table.add_column("AI", style="dim", no_wrap=True)
    table.add_column("Perfis", style="dim")
    table.add_column("✅ OK", justify="right")
    table.add_column("❌ Falhas", justify="right")
    table.add_column("Status", no_wrap=True)

    for r in reports:
        status = (
            "[bold green]✅ PASS[/bold green]"
            if r.ok
            else "[bold red]❌ FAIL[/bold red]"
        )
        table.add_row(
            r.name,
            r.domain,
            r.language,
            r.ai_assistant,
            ", ".join(r.profiles),
            str(r.passed),
            str(r.failed) if r.failed else "[dim]0[/dim]",
            status,
        )

    console.print(table)

    total = len(reports)
    ok_count = sum(1 for r in reports if r.ok)
    fail_count = total - ok_count
    total_checks = sum(len(r.checks) for r in reports)
    total_fail = sum(r.failed for r in reports)

    console.print(
        f"\n  [bold]{total}[/bold] projeto(s) | "
        f"[green]{ok_count} OK[/green] | "
        f"[red]{fail_count} com falhas[/red] | "
        f"[dim]{total_checks} verificações, {total_fail} falha(s)[/dim]\n"
    )


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------


def main() -> int:
    """
    Ponto de entrada principal.

    :return: 0 se todos os projetos passaram, 1 caso contrário.
    :rtype: int
    """
    logging.info("=== Programa: %s ===", Path(sys.argv[0]).name)

    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    only_failed = "--only-failed" in sys.argv or "-f" in sys.argv

    projects = discover_projects(_TEST_RUNS_DIR)

    if not projects:
        console.print(
            f"\n  [yellow]Nenhum projeto encontrado em {_TEST_RUNS_DIR}[/yellow]\n"
        )
        return 0

    console.print(
        f"\n  [bold]Validando {len(projects)} projeto(s) em[/bold] [dim]{_TEST_RUNS_DIR}[/dim]"
    )
    console.print(f"  [dim]Perfis verificados via: {_PROFILES_DIR}[/dim]\n")

    reports = []
    for project_path in projects:
        report = validate_project(project_path)
        reports.append(report)
        if only_failed and report.ok:
            continue
        _print_project_report(report, verbose=verbose)

    _print_summary(reports)

    logging.info("=== Termino programa: %s ===", Path(sys.argv[0]).name)
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    config_logging()
    sys.exit(main())
