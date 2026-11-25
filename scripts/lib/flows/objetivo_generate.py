"""flow_objetivo_generate — gera YAML técnico a partir de objetivo.yaml v2.0."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from ..objetivo_parser import ObjetivoV2Parser, ParsedObjetivo
from ..objetivo_validator import ObjetivoValidator
from ..ui import console


def flow_objetivo_generate(args: argparse.Namespace) -> int:
    """Gera YAML técnico (profiles, features, personas) a partir de objetivo.yaml.

    Args:
        args: Namespace with:
            - input: Path to objetivo.yaml (default: objetivo.yaml)
            - output: Path to output file (default: objetivo-spec.yaml)

    Returns:
        Exit code: 0 se sucesso, 1 se erro
    """
    # Get paths from args
    input_path = Path(getattr(args, "input", "objetivo.yaml"))
    output_path = Path(getattr(args, "output", None) or "objetivo-spec.yaml")

    # Check input exists
    if not input_path.exists():
        console.print(
            f"\n  [bold red]❌ Erro:[/bold red] Arquivo não encontrado: {input_path}\n"
        )
        return 1

    try:
        # Parse and validate
        parser = ObjetivoV2Parser()
        parsed = parser.parse(input_path)

        validator = ObjetivoValidator(strict=False)
        errors, warnings = validator.validate(parsed)

        if errors:
            console.print("\n  [bold red]❌ Erro:[/bold red] objetivo.yaml inválido:\n")
            for err in errors:
                console.print(f"  {err}")
            console.print(
                "\n  Execute 'scaffold.py objetivo-validate' para detalhes.\n"
            )
            return 1

        # Generate technical YAML
        spec_yaml = _generate_spec_yaml(parsed, input_path, warnings)

        # Write to output
        output_path.write_text(spec_yaml, encoding="utf-8")

        # Success message
        console.print(f"\n  [green]✅ Gerado:[/green] {output_path}")
        if warnings:
            console.print(
                f"  [yellow]⚠️  {len(warnings)} aviso(s)[/yellow] — revisar seções P1"
            )
        console.print()

        return 0

    except Exception as e:
        console.print(f"\n  [bold red]❌ Erro:[/bold red] {e}\n")
        return 1


def _generate_spec_yaml(
    parsed: ParsedObjetivo, source_file: Path, warnings: list
) -> str:
    """Gera conteúdo YAML técnico a partir de objetivo.yaml parseado."""

    # Extract frontmatter
    fm = parsed.frontmatter
    project = fm.get("project", {})

    # Build spec YAML
    lines = [
        "# ⚠️  GERADO AUTOMATICAMENTE — NÃO EDITAR!",
        f"# Fonte: {source_file}",
        f"# Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "specification:",
        f"  version: {fm.get('version', '2.0')}",
        f"  generated_from: {source_file}",
        f"  generated_at: {datetime.now().isoformat()}",
        "",
        "project:",
        f"  name: {project.get('name', 'unknown')}",
        f"  title: {project.get('title', project.get('name', 'Unknown Project'))}",
        f"  type: {project.get('type', 'backend-api')}",
        f"  domain: {project.get('domain', 'programming')}",
        f"  language: {project.get('language', 'python')}",
        "",
    ]

    # Add profiles if auto-detect enabled
    generation = fm.get("generation", {})
    if generation.get("profiles_auto_detect", True):
        lines.extend(
            [
                "profiles:",
                f"  - {project.get('domain', 'programming')}",
            ]
        )

        # Add language-specific profile
        lang = project.get("language", "python")
        proj_type = project.get("type", "backend-api")

        # Map common combinations
        profile_map = {
            ("python", "backend-api"): "python-fastapi",
            ("typescript", "frontend-spa"): "typescript-next",
            ("terraform", "infrastructure-code"): "terraform-aws",
            ("helm", "deployment-chart"): "k8s-helm",
        }

        profile_key = (lang, proj_type)
        if profile_key in profile_map:
            lines.append(f"  - {profile_map[profile_key]}")

        lines.append("")

    # Add features from Section 3
    sections = parsed.sections
    if 3 in sections:
        lines.extend(
            [
                "features:",
            ]
        )

        # Extract "Incluído ✅" items from Section 3
        section_3 = sections[3]
        import re

        included_pattern = r"\*\*Incluído ✅\*\*:?\s*\n((?:[-*]\s+.+\n?)+)"
        match = re.search(included_pattern, section_3, re.MULTILINE)

        if match:
            items_text = match.group(1)
            items = re.findall(r"[-*]\s+(.+)", items_text)

            for item in items:
                # Extract priority if present (P0|P1|P2)
                priority_match = re.search(r"\(([P0-2]+)\)", item)
                priority = priority_match.group(1) if priority_match else "P1"

                # Clean item text
                item_clean = re.sub(r"\s*\([P0-2]+\)\s*", "", item).strip()

                lines.append(f"  - name: {item_clean}")
                lines.append(f"    priority: {priority}")

        lines.append("")

    # Add personas from Section 5
    if 5 in sections:
        lines.extend(
            [
                "personas:",
            ]
        )

        # Extract personas from Section 5
        section_5 = sections[5]
        import re

        persona_pattern = r"\*\*([^*]+)\*\*\s*(?:\(([^)]+)\))?"
        personas = re.findall(persona_pattern, section_5)

        for persona_name, persona_role in personas[:3]:  # Limit to 3 personas
            lines.append(f"  - name: {persona_name.strip()}")
            if persona_role:
                lines.append(f"    role: {persona_role.strip()}")

        lines.append("")

    # Add validation summary
    lines.extend(
        [
            "validation:",
            f"  level: {'strict' if not warnings else 'standard'}",
            f"  warnings: {len(warnings)}",
            "  require_p0: true",
            "",
        ]
    )

    return "\n".join(lines)
