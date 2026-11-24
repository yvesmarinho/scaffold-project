"""flow_compose_profiles — aplica perfis ao projeto."""

from __future__ import annotations

import argparse
import json as _json
from pathlib import Path

from .. import composer as _composer_module
from .. import templates
from ..project import write_scaffold_state
from ..ui import collect_project_info, console

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_PROFILE_DESCRIPTORS_DIR = _PROJECT_ROOT / "scaffold" / "profiles"


def flow_compose_profiles(args: argparse.Namespace) -> int:
    """Aplica um ou mais perfis copiando templates para o diretório de destino."""
    use_json: bool = getattr(args, "json_output", False)
    ci_mode = args.ci

    profiles_raw: str = getattr(args, "compose", "") or ""
    profile_names = [p.strip() for p in profiles_raw.split(",") if p.strip()]
    if not profile_names:
        console.print(
            "\n  [bold red]\u274c --compose requer ao menos um perfil (ex: --compose typescript-next)[/bold red]\n"
        )
        return 1

    overrides = {
        "name": args.name,
        "title": args.title,
        "description": args.description,
        "domain": args.domain,
        "language": args.language,
        "ai_assistant": getattr(args, "ai_assistant", None),
        "repo": args.repo,
        "shared_dir": args.shared_dir,
        "target_dir": args.target_dir,
    }
    overrides = {k: v for k, v in overrides.items() if v is not None}

    try:
        cfg = collect_project_info(ci_mode=ci_mode, **overrides)
    except ValueError as e:
        console.print(f"\n  [bold red]\u274c Erro:[/bold red] {e}\n")
        return 1

    composer = _composer_module.ProfileComposer(
        descriptors_dir=_PROFILE_DESCRIPTORS_DIR,
        project_root=_PROJECT_ROOT,
    )

    result = composer.compose(
        profile_names, cfg, force=getattr(args, "update_profile_files", False)
    )

    if use_json:
        output = {
            "success": result.success,
            "applied": result.applied,
            "created": result.created_count,
            "skipped": result.skipped_count,
            "errors": result.errors,
            "rolled_back": [str(p) for p in result.rolled_back],
        }
        print(_json.dumps(output, indent=2, ensure_ascii=False))
        return 0 if result.success else 1

    if result.errors:
        for err in result.errors:
            console.print(f"  [bold red]\u274c {err}[/bold red]")
        if result.rolled_back:
            console.print(
                f"  [yellow]\u21a9 Rollback: {len(result.rolled_back)} arquivo(s) removido(s)[/yellow]"
            )
        return 1

    # Persiste perfis aplicados no state file
    write_scaffold_state(cfg, profiles_applied=result.applied)

    # IMP-29: Gera guia de documentação para a combinação de perfis
    guide_item = templates.generate_profile_guide(
        cfg, result.applied, composer.descriptors
    )
    if guide_item.status == "created":
        console.print(
            f"  [dim]📖 Guia de perfis gerado: docs/{guide_item.path.name}[/dim]"
        )

    from rich.table import Table

    table = Table(show_lines=False, expand=False, show_header=False)
    table.add_column(style="dim", no_wrap=True)
    table.add_column()

    for item in result.items:
        icon = (
            "\u2705"
            if item.status == "created"
            else ("\u23ed" if item.status == "skipped" else "\u274c")
        )
        table.add_row(
            icon,
            (
                str(item.path.relative_to(cfg.target_dir))
                if cfg.target_dir in item.path.parents
                else str(item.path)
            ),
        )

    console.print(f"\n  [bold]Composição:[/bold] {', '.join(result.applied)}")
    console.print(f"  [dim]Destino: {cfg.target_dir}[/dim]\n")
    console.print(table)
    console.print(
        f"\n  [bold green]\u2705 {result.created_count} arquivo(s) criado(s), {result.skipped_count} pulado(s).[/bold green]\n"
    )
    return 0
