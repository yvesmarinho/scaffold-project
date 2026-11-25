"""flow_dry_run + _build_manifest — simula criação sem escrever arquivos."""

from __future__ import annotations

import argparse
import json as _json

from ..config import DOMAIN_DEFAULT_PROFILES, ProjectConfig
from ..ui import collect_project_info, console


def _build_manifest(cfg: ProjectConfig) -> list[dict]:
    """Retorna a sequência de operações que flow_new_project executaria."""
    domain_profile = DOMAIN_DEFAULT_PROFILES.get(cfg.domain, cfg.domain)

    lang_files: list[dict] = []
    if cfg.language == "python":
        lang_files = [
            {
                "step": "create_structure",
                "op": "create",
                "path": "pyproject.toml",
                "desc": "Configuração Python PEP 621 + uv",
            }
        ]
    elif cfg.language == "typescript":
        lang_files = [
            {
                "step": "create_structure",
                "op": "create",
                "path": "package.json",
                "desc": "Configuração Node.js",
            }
        ]
    elif cfg.language == "go":
        lang_files = [
            {
                "step": "create_structure",
                "op": "create",
                "path": "go.mod",
                "desc": "Módulo Go",
            }
        ]

    ops: list[dict] = [
        {
            "step": "create_structure",
            "op": "mkdir",
            "path": ".session-docs/",
            "desc": "Estrutura de pastas padrão",
        },
        {
            "step": "create_structure",
            "op": "create",
            "path": "docs/INDEX.md",
            "desc": "Índice do projeto",
        },
        {
            "step": "create_structure",
            "op": "create",
            "path": "docs/TODO.md",
            "desc": "Lista de tarefas",
        },
        {
            "step": "create_structure",
            "op": "create",
            "path": ".gitignore",
            "desc": "Gitignore padrão",
        },
        *lang_files,
        {
            "step": "setup_symlinks",
            "op": "symlink",
            "path": ".copilot-rules.md",
            "desc": "→ .copilot-shared/.copilot-rules.md",
        },
        {
            "step": "generate_rules",
            "op": "create",
            "path": f".copilot-rules-{cfg.project_name}.md",
            "desc": "Regras Copilot específicas do projeto",
        },
        {
            "step": "generate_rules",
            "op": "create",
            "path": ".github/copilot-instructions.md",
            "desc": "Instruções auto-injetadas em toda sessão",
        },
        {
            "step": "vscode",
            "op": "create",
            "path": ".vscode/settings.json",
            "desc": "Configurações VS Code",
        },
        {
            "step": "vscode",
            "op": "create",
            "path": ".vscode/mcp.json",
            "desc": "Servidores MCP",
        },
        {
            "step": "vscode",
            "op": "create",
            "path": ".vscode/extensions.json",
            "desc": "Extensões recomendadas",
        },
        {
            "step": "copy_speckit",
            "op": "copy",
            "path": f".github/skills/{domain_profile}/SKILL.md",
            "desc": "Domain profile (skill)",
        },
        {
            "step": "copy_speckit",
            "op": "copy",
            "path": ".github/skills/devops-security/SKILL.md",
            "desc": "Security profile (transversal)",
        },
        {
            "step": "copy_speckit",
            "op": "copy",
            "path": ".github/skills/session-start/SKILL.md",
            "desc": "Ritual de início de sessão",
        },
        {
            "step": "copy_speckit",
            "op": "copy",
            "path": ".github/skills/session-end/SKILL.md",
            "desc": "Ritual de encerramento",
        },
        {
            "step": "constitution",
            "op": "create",
            "path": ".specify/memory/constitution.md",
            "desc": "Constitution SpecKit",
        },
        {
            "step": "git",
            "op": "git",
            "path": ".git/",
            "desc": "git init + commit inicial",
        },
    ]
    return ops


def flow_dry_run(args: argparse.Namespace) -> int:
    """Mostra o que seria gerado sem criar nenhum arquivo."""
    use_json: bool = getattr(args, "json_output", False)
    ci_mode = args.ci
    overrides = {
        "name": args.name,
        "title": args.title,
        "description": args.description,
        "domain": args.domain,
        "language": args.language,
        "repo": args.repo,
        "shared_dir": args.shared_dir,
        "target_dir": args.target_dir,
    }
    overrides = {k: v for k, v in overrides.items() if v is not None}

    try:
        cfg = collect_project_info(ci_mode=ci_mode, **overrides)
    except ValueError as e:
        console.print(f"\n  [bold red]❌ Erro:[/bold red] {e}\n")
        return 1

    manifest = _build_manifest(cfg)

    if use_json:
        output = {
            "dry_run": True,
            "project_name": cfg.project_name,
            "domain": cfg.domain,
            "language": cfg.language,
            "target_dir": str(cfg.target_dir),
            "manifest": manifest,
        }
        print(_json.dumps(output, indent=2, ensure_ascii=False))
        return 0

    from rich.table import Table

    console.print(
        f"\n  [bold yellow]📋 DRY RUN[/bold yellow] — "
        f"Projeto: [cyan]{cfg.project_name}[/cyan] | "
        f"Domínio: [cyan]{cfg.domain}[/cyan] | "
        f"Linguagem: [cyan]{cfg.language}[/cyan]"
    )
    console.print(f"  [dim]Destino: {cfg.target_dir}[/dim]\n")

    table = Table(show_lines=True, expand=False)
    table.add_column("#", style="dim", width=3, no_wrap=True)
    table.add_column("Etapa", style="yellow", no_wrap=True)
    table.add_column("Op", style="cyan", no_wrap=True)
    table.add_column("Arquivo / Destino")
    table.add_column("Descrição")

    for i, entry in enumerate(manifest, 1):
        table.add_row(str(i), entry["step"], entry["op"], entry["path"], entry["desc"])

    console.print(table)
    console.print(
        "\n  [bold yellow]⚠  Modo dry-run: nenhum arquivo foi criado.[/bold yellow]\n"
    )
    return 0
