"""
flow_adopt — adota um projeto legado (sem .scaffold-state.yaml) no scaffold.

NOME: adopt.py
TITULO: Flow de adoção de projetos legados
DATA: 15/07/2026 10:20
MODIFICADO: 15/07/2026 16:10
VERSÃO: 1.0.0
DEPEND: lib.project, lib.config, lib.flows.upgrade
STATUS: DEV

Fluxo:
  1. Valida que o diretório alvo existe e ainda não tem .scaffold-state.yaml
     (se tiver, o comando correto é `scaffold.py upgrade`).
  2. Detecta linguagem e domínio pelos marcadores do repositório
     (pyproject.toml, package.json, go.mod, *.tf, ...), permitindo override
     via --language/--domain e confirmação interativa fora de --ci/--json.
  3. Escreve .scaffold-state.yaml com a configuração adotada.
  4. Delega ao flow_upgrade, que re-aplica todos os passos idempotentes do
     template (nunca sobrescreve arquivos existentes sem --force).
"""

from __future__ import annotations

import argparse
import json as _json
import re
from datetime import datetime
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfo

from ..config import (
    AiAssistantType,
    DomainType,
    LanguageType,
    ProjectConfig,
    get_default_shared_dir,
)
from ..project import read_scaffold_state, write_scaffold_state
from ..ui import console
from .upgrade import flow_upgrade

# Marcadores de linguagem, em ordem de precedência
_LANGUAGE_MARKERS: list[tuple[str, list[str]]] = [
    ("python",     ["pyproject.toml", "uv.lock", "setup.py", "requirements.txt", "Pipfile"]),
    ("typescript", ["tsconfig.json", "package.json"]),
    ("go",         ["go.mod"]),
]

# Marcadores de infraestrutura (globs relativos ao alvo)
_INFRA_MARKER_GLOBS: list[str] = [
    "*.tf", "terraform/**/*.tf", "infra/**/*.tf",
    "Chart.yaml", "charts/*/Chart.yaml", "helm/**/Chart.yaml",
    "ansible.cfg", "playbooks/*.yml",
    "k8s/**/*.yaml", "kubernetes/**/*.yaml",
]


def detect_language(target: Path) -> str:
    """
    Detecta a linguagem principal do projeto pelos arquivos marcadores.

    :param target: Diretório raiz do projeto legado.
    :type target: Path
    :return: ``python`` | ``typescript`` | ``go`` | ``other``.
    :rtype: str
    """
    for language, markers in _LANGUAGE_MARKERS:
        if any((target / marker).exists() for marker in markers):
            return language
    return "other"


def detect_domain(target: Path) -> str:
    """
    Detecta o domínio do projeto: infraestrutura se houver marcadores IaC,
    caso contrário programming.

    :param target: Diretório raiz do projeto legado.
    :type target: Path
    :return: ``infrastructure`` | ``programming``.
    :rtype: str
    """
    for pattern in _INFRA_MARKER_GLOBS:
        try:
            if next(target.glob(pattern), None) is not None:
                return "infrastructure"
        except (OSError, ValueError):
            continue
    return "programming"


def _kebab(name: str) -> str:
    """Normaliza um nome para kebab-case (slug de projeto)."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return slug.strip("-") or "adopted-project"


def flow_adopt(args: argparse.Namespace) -> int:
    """
    Modo adopt: gera .scaffold-state.yaml para um projeto legado e re-aplica
    o template via pipeline idempotente do upgrade.

    - Arquivos ausentes → criados
    - Arquivos existentes → preservados (skipped/drift; --force sobrescreve com backup)
    """
    use_json: bool = getattr(args, "json_output", False)
    ci_mode: bool = getattr(args, "ci", False)

    target = (Path(args.target_dir) if getattr(args, "target_dir", None) else Path.cwd()).resolve()

    if not target.is_dir():
        msg = f"Diretório alvo não existe: {target}"
        if use_json:
            print(_json.dumps({"error": msg}, ensure_ascii=False))
        else:
            console.print(f"  [bold red]❌ {msg}[/bold red]\n")
        return 1

    if read_scaffold_state(target) is not None:
        msg = (
            f"{target} já possui .scaffold-state.yaml — projeto já é gerido pelo scaffold.\n"
            "  Use: scaffold.py upgrade"
        )
        if use_json:
            print(_json.dumps({"error": msg}, ensure_ascii=False))
        else:
            console.print(f"  [bold red]❌ {msg}[/bold red]\n")
        return 1

    # Detecção com override via CLI
    language = getattr(args, "language", None) or detect_language(target)
    domain = getattr(args, "domain", None) or detect_domain(target)
    name = _kebab(getattr(args, "name", None) or target.name)
    title = getattr(args, "title", None) or name.replace("-", " ").title()
    description = getattr(args, "description", None) or f"Projeto {name} adotado pelo scaffold"
    ai_assistant = getattr(args, "ai_assistant", None) or "both"

    if not use_json:
        console.print(
            f"\n  [bold cyan]🧬 Adopt:[/bold cyan] [cyan]{name}[/cyan] | "
            f"domínio: [cyan]{domain}[/cyan] | linguagem: [cyan]{language}[/cyan] | "
            f"ai: [cyan]{ai_assistant}[/cyan]"
        )
        console.print(f"  [dim]Alvo: {target}[/dim]\n")

    # --dry-run: apenas simula — NUNCA escreve state nem aplica o template
    if getattr(args, "dry_run", False):
        plan = {
            "adopt": True,
            "dry_run": True,
            "target": str(target),
            "project": {
                "name": name,
                "title": title,
                "domain": domain,
                "language": language,
                "ai_assistant": ai_assistant,
            },
            "would_create": [
                ".scaffold-state.yaml",
                "estrutura do template via pipeline do upgrade "
                "(arquivos existentes seriam preservados)",
            ],
        }
        if use_json:
            print(_json.dumps(plan, indent=2, ensure_ascii=False))
        else:
            console.print("  [yellow]🔍 Dry-run: nenhum arquivo foi escrito.[/yellow]")
            console.print(
                "  [dim]Seria criado .scaffold-state.yaml e aplicado o template "
                "(idempotente; existentes preservados).[/dim]"
            )
            console.print(
                "  [dim]Para executar de fato: remova --dry-run do comando.[/dim]\n"
            )
        return 0

    # Confirmação interativa (fora de --ci/--json)
    if not use_json and not ci_mode:
        from rich.prompt import Confirm

        if not Confirm.ask(
            "  Confirmar adoção com os valores detectados acima?", default=True
        ):
            console.print(
                "\n  [yellow]❌ Adoção cancelada. Ajuste com --name/--domain/"
                "--language/--ai e execute novamente.[/yellow]\n"
            )
            return 1

    shared_dir = (
        Path(args.shared_dir) if getattr(args, "shared_dir", None) else get_default_shared_dir()
    )

    cfg = ProjectConfig(
        project_name=name,
        project_title=title,
        description=description,
        domain=cast(DomainType, domain),
        language=cast(LanguageType, language),
        github_repo=getattr(args, "repo", None),
        shared_dir=shared_dir,
        target_dir=target,
        created_at=datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        ai_assistant=cast(AiAssistantType, ai_assistant),
    )

    # Persiste o estado ANTES do upgrade: project_path passa a resolver para
    # o próprio target (upgrade in-place) e o flow_upgrade encontra o state.
    # O touch prévio garante o modo in-place mesmo quando o nome do diretório
    # difere do slug kebab-case (cfg.project_path só retorna target_dir se o
    # state existir nele ou se os nomes coincidirem).
    (target / ".scaffold-state.yaml").touch()
    write_scaffold_state(cfg, profiles_applied=[])

    if not use_json:
        console.print("  [green]✅ .scaffold-state.yaml criado — aplicando template...[/green]\n")

    # Delegar ao pipeline idempotente do upgrade
    args.target_dir = str(target)
    return flow_upgrade(args)
