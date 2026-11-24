"""flow_objetivo_validate — valida arquivo objetivo.yaml v2.0."""

from __future__ import annotations

import argparse
from pathlib import Path

from ..objetivo_parser import ObjetivoV2Parser
from ..objetivo_validator import ObjetivoValidator
from ..ui import console


def flow_objetivo_validate(args: argparse.Namespace) -> int:
    """Valida arquivo objetivo.yaml v2.0 e reporta erros/avisos.

    Args:
        args: Namespace with:
            - file: Path to objetivo.yaml file (default: objetivo.yaml)
            - strict: Strict mode (P1 warnings become errors)

    Returns:
        Exit code: 0 se válido, 1 se erros
    """
    # Get file path from args
    file_path = Path(getattr(args, "file", "objetivo.yaml"))
    strict_mode = getattr(args, "strict", False)

    # Check file exists
    if not file_path.exists():
        console.print(
            f"\n  [bold red]❌ Erro:[/bold red] Arquivo não encontrado: {file_path}\n"
        )
        return 1

    try:
        # Parse file
        parser = ObjetivoV2Parser()
        parsed = parser.parse(file_path)

        # Validate
        validator = ObjetivoValidator(strict=strict_mode)
        errors, warnings = validator.validate(parsed)

        # Print results
        console.print(f"\n[bold]Validação de {file_path}[/bold]\n")

        if not errors and not warnings:
            console.print("  [green]✅ Válido — sem erros ou avisos[/green]\n")
            return 0

        # Print errors
        if errors:
            console.print("[bold red]❌ Erros:[/bold red]")
            for err in errors:
                console.print(f"  {err}")
            console.print()

        # Print warnings
        if warnings:
            console.print("[bold yellow]⚠️  Avisos:[/bold yellow]")
            for warn in warnings:
                console.print(f"  {warn}")
            console.print()

        # Summary
        console.print(
            f"  [dim]Total: [red]{len(errors)} erro(s)[/red] | "
            f"[yellow]{len(warnings)} aviso(s)[/yellow][/dim]\n"
        )

        return 1 if errors else 0

    except ValueError as e:
        console.print(f"\n  [bold red]❌ Erro de validação:[/bold red] {e}\n")
        return 1
    except Exception as e:
        console.print(f"\n  [bold red]❌ Erro inesperado:[/bold red] {e}\n")
        return 1
