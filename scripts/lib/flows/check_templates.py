"""
Flow: check-templates

Detecta drift de templates SpecKit entre projeto local e upstream template.
Parte de IMP-65 (Template Synchronization System) Fase 1.

Compara versões de templates em .specify/templates/ e reporta:
- Templates desatualizados (local < upstream)
- Templates ausentes (existe no upstream mas não no projeto)
- Breaking changes detectadas
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from ..template_version import (
    detect_drift,
    generate_drift_json,
    generate_drift_report,
    scan_templates,
)
from ..ui import console

log = logging.getLogger(__name__)


def flow_check_templates(args: argparse.Namespace) -> int:
    """
    Flow: detecta drift de templates SpecKit.

    Args:
        args: Namespace com:
            - target_dir: diretório do projeto a verificar (default: cwd)
            - json_output: output JSON ao invés de texto

    Returns:
        0 se templates estão atualizados
        1 se drift detectado
        2 em caso de erro
    """
    # Determinar diretórios
    target_dir_arg = getattr(args, "target_dir", None)
    if target_dir_arg:
        target_dir = Path(target_dir_arg).resolve()
    else:
        target_dir = Path.cwd().resolve()

    # Diretório upstream (scaffold-project)
    # scaffold.py está em scaffold-project/scripts/
    scaffold_root = Path(__file__).parent.parent.parent.parent
    upstream_dir = scaffold_root / ".specify" / "templates"

    # Diretório local (projeto)
    local_dir = target_dir / ".specify" / "templates"

    json_output = getattr(args, "json_output", False)

    # Validações
    if not upstream_dir.exists():
        msg = f"Upstream templates not found: {upstream_dir}"
        if json_output:
            result = {
                "error": msg,
                "upstream_dir": str(upstream_dir),
            }
            console.print(json.dumps(result, indent=2))
        else:
            console.print(f"\n[bold red]❌ Error:[/bold red] {msg}\n")
        return 2

    if not local_dir.exists():
        msg = f"Local templates not found: {local_dir}"
        if json_output:
            result = {
                "error": msg,
                "local_dir": str(local_dir),
                "hint": "This project may not have been created with SpecKit templates",
            }
            console.print(json.dumps(result, indent=2))
        else:
            console.print(f"\n[bold red]❌ Error:[/bold red] {msg}")
            console.print(f"   Hint: This project may not have been created with SpecKit templates\n")
        return 2

    # Scan templates
    log.info("Scanning upstream templates: %s", upstream_dir)
    log.info("Scanning local templates: %s", local_dir)

    upstream_templates = scan_templates(upstream_dir)
    local_templates = scan_templates(local_dir)

    if not upstream_templates:
        msg = "No upstream templates found (missing frontmatter?)"
        if json_output:
            console.print(json.dumps({"error": msg}, indent=2))
        else:
            console.print(f"\n[bold yellow]⚠️  Warning:[/bold yellow] {msg}\n")
        return 2

    # Detect drift
    drifts = detect_drift(local_templates, upstream_templates)

    # Output
    if json_output:
        result = generate_drift_json(drifts)
        result["upstream_dir"] = str(upstream_dir)
        result["local_dir"] = str(local_dir)
        result["upstream_count"] = len(upstream_templates)
        result["local_count"] = len(local_templates)
        console.print(json.dumps(result, indent=2))
    else:
        console.print(f"\n[bold]Template Drift Detection[/bold]")
        console.print(f"  Upstream: {upstream_dir}")
        console.print(f"  Local:    {local_dir}")
        console.print(f"  Templates scanned: {len(upstream_templates)} upstream, {len(local_templates)} local\n")

        report = generate_drift_report(drifts)
        console.print(report)
        console.print()

    # Exit status
    if drifts:
        return 1  # Drift detected
    else:
        return 0  # All up-to-date
