"""flow_objetivo_init — inicializa arquivo objetivo-init.yaml via wizard ou template."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from ..objetivo_wizard import ObjetivoWizard, WizardAnswers
from ..ui import console


def _log_objetivo_init(
    output_path: Path,
    answers: WizardAnswers,
    success: bool,
    error_msg: str | None = None,
) -> None:
    """
    Log objetivo-init operation to logs/scaffolds.yaml (BUG-001 Fix #3).

    Args:
        output_path: Path where objetivo-init.yaml was created
        answers: Wizard answers (for project metadata)
        success: Whether operation succeeded
        error_msg: Error message if failed
    """
    try:
        # SCAFFOLD_LOGS_DIR (definido pela suíte de testes) evita poluir o histórico real
        logs_dir = os.environ.get("SCAFFOLD_LOGS_DIR", "").strip() or "logs"
        log_file = Path(logs_dir) / "scaffolds.yaml"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        import yaml

        # Load existing log
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        # Ensure "scaffolds" key exists
        if "scaffolds" not in data:
            data["scaffolds"] = []

        # Create entry
        entry = {
            "id": len(data["scaffolds"]) + 1,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": "objetivo-init",
            "project_name": answers.project_name or "unnamed",
            "project_type": answers.project_type or "unknown",
            "project_domain": answers.project_domain or "unknown",
            "project_language": answers.project_language or "unknown",
            "created_by": answers.created_by or os.getenv("USER", "unknown"),
            "output_file": str(output_path.resolve()),
            "success": success,
        }

        if error_msg:
            entry["error_message"] = error_msg

        # Append entry
        data["scaffolds"].append(entry)

        # Save
        with log_file.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    except Exception as e:
        # Non-critical: logging failure shouldn't stop execution
        console.print(f"[dim yellow]⚠️  Falha ao registrar log: {e}[/dim yellow]")


def flow_objetivo_init(args: argparse.Namespace) -> int:
    """Inicializa arquivo objetivo-init.yaml.

    Modos:
    - Interactive (default): Run wizard interativo
    - Non-interactive (--from-file): Read answers from JSON
    - Template copy (--template-only): Copy template sem perguntas

    Args:
        args: Namespace with:
            - interactive: Interactive wizard mode (default True)
            - from_file: Path to JSON with answers (non-interactive mode)
            - template_only: Just copy template without wizard
            - output: Output path (default: objetivo-init.yaml)

    Returns:
        Exit code: 0 se sucesso, 1 se erro
    """
    # Use CWD-relative path (fix for ~/.local/bin/scaffold wrapper issue)
    output_filename = getattr(args, "output", None) or "objetivo-init.yaml"
    output_path = Path.cwd() / output_filename

    # Check if file already exists
    if output_path.exists():
        response = (
            input(f"\n⚠️  {output_path} já existe. Sobrescrever? [y/N]: ")
            .strip()
            .lower()
        )
        if response not in ["y", "yes", "s", "sim"]:
            console.print("\n  [yellow]Cancelado.[/yellow]\n")
            return 1

    # Mode 1: Non-interactive from JSON file
    from_file = getattr(args, "from_file", None)
    if from_file:
        try:
            with open(from_file, encoding="utf-8") as f:
                data = json.load(f)

            answers = WizardAnswers.from_dict(data)
            wizard = ObjetivoWizard()
            result = wizard.run_non_interactive(answers, output_path)

            # BUG-001 Fix #3: Log operation
            _log_objetivo_init(output_path, answers, success=(result == 0))

            return result

        except FileNotFoundError:
            console.print(
                f"\n  [bold red]❌ Erro:[/bold red] Arquivo não encontrado: {from_file}\n"
            )
            _log_objetivo_init(
                output_path,
                WizardAnswers(),
                success=False,
                error_msg=f"File not found: {from_file}",
            )
            return 1
        except json.JSONDecodeError as e:
            console.print(f"\n  [bold red]❌ Erro JSON:[/bold red] {e}\n")
            _log_objetivo_init(
                output_path,
                WizardAnswers(),
                success=False,
                error_msg=f"JSON decode error: {e}",
            )
            return 1
        except Exception as e:
            console.print(f"\n  [bold red]❌ Erro:[/bold red] {e}\n")
            _log_objetivo_init(
                output_path, WizardAnswers(), success=False, error_msg=str(e)
            )
            return 1

    # Mode 2: Template-only (copy without wizard)
    template_only = getattr(args, "template_only", False)
    if template_only:
        try:
            wizard = ObjetivoWizard()
            if not wizard.template_path.exists():
                console.print(
                    f"\n  [bold red]❌ Erro:[/bold red] Template não encontrado: {wizard.template_path}\n"
                )
                return 1

            import shutil

            shutil.copy2(wizard.template_path, output_path)

            console.print(f"\n  [green]✅ Template copiado:[/green] {output_path}")
            console.print(
                "  [dim]Edite o arquivo e preencha os campos manualmente.[/dim]\n"
            )

            # BUG-001 Fix #3: Log operation (template mode)
            template_answers = WizardAnswers(created_by=os.getenv("USER", "unknown"))
            _log_objetivo_init(output_path, template_answers, success=True)

            return 0

        except Exception as e:
            console.print(f"\n  [bold red]❌ Erro:[/bold red] {e}\n")
            template_answers = WizardAnswers()
            _log_objetivo_init(
                output_path, template_answers, success=False, error_msg=str(e)
            )
            return 1

    # Mode 3: Interactive wizard (default)
    wizard = ObjetivoWizard()
    result = wizard.run(output_path)

    # BUG-001 Fix #3: Log operation (interactive mode)
    _log_objetivo_init(output_path, wizard.answers, success=(result == 0))

    return result
