"""flow_generate_infra — gera CI, Dockerfile, docker-compose e RUNBOOK."""

from __future__ import annotations

import argparse
from pathlib import Path

from .. import infra
from ..ui import collect_project_info, console, print_final_summary


def flow_generate_infra(args: argparse.Namespace) -> int:
    """Gera .github/workflows/ci.yml, Dockerfile, docker-compose.yml e docs/RUNBOOK.md."""
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
        console.print(f"\n  [bold red]\u274c Erro:[/bold red] {e}\n")
        return 1

    results = [
        infra.generate_ci_workflow(cfg),
        infra.generate_dockerfile(cfg),
        infra.generate_docker_compose(cfg),
        infra.generate_runbook(cfg),
    ]
    # Logging automático se não for --no-log
    save_log = not getattr(args, "no_log", False)
    log_dir_arg = getattr(args, "log_dir", None)
    log_dir = Path(log_dir_arg) if log_dir_arg else None
    print_final_summary(
        results, project_path=cfg.project_path, save_log=save_log, log_dir=log_dir
    )

    errors = [r for r in results if hasattr(r, "status") and r.status == "error"]
    if errors:
        console.print(
            f"  [bold red]\u274c {len(errors)} erro(s) durante a geração.[/bold red]\n"
        )
        return 1

    console.print(
        "  [bold green]\u2705 Arquivos de infra gerados com sucesso![/bold green]\n"
    )
    return 0
