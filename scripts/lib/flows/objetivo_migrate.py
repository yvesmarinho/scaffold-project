"""flow_objetivo_migrate — migra objetivo.yaml v1.0 → v2.0."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ..objetivo_migrator import ObjetivoMigrator
from ..ui import console


def flow_objetivo_migrate(args: argparse.Namespace) -> int:
    """Migra objetivo.yaml v1.0 → v2.0 com preview e confirmação.

    Args:
        args: Namespace with:
            - file: Path to objetivo.yaml (default: objetivo.yaml)
            - auto: Auto-accept without confirmation (default: False)

    Returns:
        Exit code: 0 se sucesso, 1 se erro
    """
    # Get file path from args
    file_path = Path(getattr(args, "file", "objetivo.yaml"))
    auto_accept = getattr(args, "auto", False) or False

    # Check file exists
    if not file_path.exists():
        console.print(
            f"\n  [bold red]❌ Erro:[/bold red] Arquivo não encontrado: {file_path}\n"
        )
        return 1

    try:
        # Run migration
        migrator = ObjetivoMigrator()
        result = migrator.migrate(file_path)

        # Check if migration succeeded (success=True sempre traz preview_file)
        if not result.success or result.preview_file is None:
            console.print("\n  [bold red]❌ Erro na migração:[/bold red]\n")
            for err in result.errors:
                console.print(f"  • {err}")
            console.print()
            return 1

        # Show migration result
        console.print(
            f"\n[bold green]✅ Migração concluída:[/bold green] {result.source_version} → {result.target_version}\n"
        )

        # Show mappings
        if result.mappings:
            console.print("[bold]Mapeamentos:[/bold]")
            for old_field, new_field in result.mappings.items():
                console.print(f"  • {old_field} → {new_field}")
            console.print()

        # Show warnings
        if result.warnings:
            console.print("[bold yellow]⚠️  Avisos:[/bold yellow]")
            for warn in result.warnings:
                console.print(f"  • {warn}")
            console.print()

        # Show preview file location
        console.print(f"[dim]Preview gerado:[/dim] {result.preview_file}\n")

        # Show side-by-side preview (first 30 lines of each)
        _show_preview_comparison(file_path, result.preview_file)

        # Ask for confirmation (unless --auto)
        if not auto_accept:
            console.print()
            response = (
                input("Aceitar migração? (substituir arquivo original) [y/N]: ")
                .strip()
                .lower()
            )

            if response != "y":
                console.print(
                    f"\n  [yellow]Cancelado.[/yellow] Preview mantido em: {result.preview_file}\n"
                )
                return 0

        # Backup original to .v1
        backup_path = file_path.parent / f"{file_path.name}.v1"
        shutil.copy2(file_path, backup_path)

        # Replace original with v2
        shutil.copy2(result.preview_file, file_path)

        # Remove preview file
        result.preview_file.unlink()

        # Success
        console.print("\n  [green]✅ Migração aplicada:[/green]")
        console.print(f"    • Original (v1.0): {backup_path}")
        console.print(f"    • Migrado (v2.0): {file_path}")
        console.print()

        return 0

    except Exception as e:
        console.print(f"\n  [bold red]❌ Erro inesperado:[/bold red] {e}\n")
        return 1


def _show_preview_comparison(v1_file: Path, v2_file: Path, max_lines: int = 30) -> None:
    """Mostra comparação lado a lado dos primeiros N linhas de cada versão."""
    from rich.columns import Columns
    from rich.panel import Panel

    # Read files
    v1_content = v1_file.read_text(encoding="utf-8").split("\n")[:max_lines]
    v2_content = v2_file.read_text(encoding="utf-8").split("\n")[:max_lines]

    # Limit content
    v1_preview = "\n".join(v1_content)
    v2_preview = "\n".join(v2_content)

    if len(v1_file.read_text(encoding="utf-8").split("\n")) > max_lines:
        v1_preview += f"\n\n[dim]... (+{len(v1_file.read_text(encoding='utf-8').split('\n')) - max_lines} linhas)[/dim]"

    if len(v2_file.read_text(encoding="utf-8").split("\n")) > max_lines:
        v2_preview += f"\n\n[dim]... (+{len(v2_file.read_text(encoding='utf-8').split('\n')) - max_lines} linhas)[/dim]"

    # Create panels
    v1_panel = Panel(
        v1_preview,
        title=f"[red]v1.0[/red] ({v1_file.name})",
        border_style="red",
        padding=(1, 2),
    )

    v2_panel = Panel(
        v2_preview,
        title="[green]v2.0[/green] (preview)",
        border_style="green",
        padding=(1, 2),
    )

    # Show side by side
    console.print(Columns([v1_panel, v2_panel], equal=True, expand=True))
