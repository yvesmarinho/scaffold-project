"""flow_list_profiles + _load_descriptor — lista perfis disponíveis."""

from __future__ import annotations

import argparse
import json as _json
from pathlib import Path

from ..ui import console

_PROFILE_DESCRIPTORS_DIR = (
    Path(__file__).parent.parent.parent.parent / "scaffold" / "profiles"
)


def _load_descriptor(yaml_path: Path) -> dict:
    """Carrega um profile descriptor YAML retornando um dict com os campos."""
    try:
        import yaml  # pyyaml

        with yaml_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback mínimo: parse de campos escalares simples (sem pyyaml)
        data: dict = {}
        with yaml_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.rstrip()
                if not line or line.startswith("#") or line.startswith(" "):
                    continue
                if ": " in line:
                    key, _, val = line.partition(": ")
                    val = val.strip().strip('"').strip("'")
                    if val and val not in ("|", ">", ""):
                        data[key.strip()] = val
        return data


def flow_list_profiles(args: argparse.Namespace) -> int:
    """Lista perfis disponíveis lendo os descriptors YAML em scaffold/profiles/."""
    use_json: bool = getattr(args, "json_output", False)
    profiles: list[dict] = []

    if _PROFILE_DESCRIPTORS_DIR.exists():
        for yaml_file in sorted(_PROFILE_DESCRIPTORS_DIR.glob("*.yaml")):
            try:
                data = _load_descriptor(yaml_file)
                desc = (data.get("description") or "").strip().replace("\n", " ")
                profiles.append(
                    {
                        "name": str(data.get("name", yaml_file.stem)),
                        "description": desc,
                        "layer": str(data.get("layer", "—")),
                        "version": str(
                            data.get("VERSION") or data.get("version") or "—"
                        ),
                        "last_tested": str(
                            data.get("LAST_TESTED_DATE")
                            or data.get("last_tested")
                            or "—"
                        ),
                        "tags": data.get("tags") or [],
                    }
                )
            except Exception as exc:
                console.print(f"  [red]⚠ Erro ao ler {yaml_file.name}: {exc}[/red]")
    else:
        msg = f"Diretório não encontrado: {_PROFILE_DESCRIPTORS_DIR}"
        if use_json:
            print(_json.dumps({"error": msg}, ensure_ascii=False))
        else:
            console.print(f"  [yellow]⚠ {msg}[/yellow]\n")
        return 1

    if use_json:
        print(_json.dumps(profiles, indent=2, ensure_ascii=False))
        return 0

    from rich.table import Table

    table = Table(
        title="[bold]Perfis disponíveis[/bold]", show_lines=True, expand=False
    )
    table.add_column("Nome", style="cyan", no_wrap=True)
    table.add_column("Layer", style="yellow", no_wrap=True)
    table.add_column("Versão", no_wrap=True)
    table.add_column("Última validação", no_wrap=True)
    table.add_column("Descrição")

    for p in profiles:
        desc = p["description"]
        if len(desc) > 72:
            desc = desc[:69] + "..."
        table.add_row(p["name"], p["layer"], p["version"], p["last_tested"], desc)

    console.print()
    console.print(table)
    console.print(
        f"\n  [dim]{len(profiles)} perfil(s) em {_PROFILE_DESCRIPTORS_DIR}[/dim]\n"
    )
    return 0
