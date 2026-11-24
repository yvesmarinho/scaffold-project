"""flow_new_profile — scaffolding de um novo profile-descriptor a partir de defaults."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from ..ui import console

_PROFILE_DESCRIPTORS_DIR = (
    Path(__file__).parent.parent.parent.parent / "scaffold" / "profiles"
)
_KEBAB_RE = re.compile(r"^[a-z][a-z0-9-]*$")

# ---------------------------------------------------------------------------
# Template YAML
# ---------------------------------------------------------------------------

_DESCRIPTOR_YAML_TEMPLATE = """\
# ============================================================
# Profile Descriptor — {name}
# Layer: {layer} | Schema v1.1.0
# Gerado por: scaffold.py --new-profile {name}
# ============================================================
# INSTRUÇÃO: Preencha todos os campos marcados com TODO.
#             Remova comentários de instrução antes do commit.
#             Execute: python scripts/scaffold.py --validate
# ============================================================

schema_version: "1.1.0"

# ------------------------------------------------------------------
# Identificação (obrigatórios)
# ------------------------------------------------------------------
name: {name}
description: >
  TODO: descreva o propósito deste perfil em 2-3 linhas.
  Mencione: stack, framework, artefatos gerados, pré-requisitos.

version: "0.1.0"
last_tested: "{today}"
status: draft  # draft | stable | deprecated

# ------------------------------------------------------------------
# Metadados
# ------------------------------------------------------------------
meta:
  maintained_by: "@TODO"
  language: "TODO"  # python | typescript | terraform | any | ...
  framework: "TODO" # fastapi | flask | next | helm | terraform | none
  tags:
    - TODO

# ------------------------------------------------------------------
# Camada (obrigatório)
# ------------------------------------------------------------------
# Valores aceitos: core | 1 | 2 | 3 | 4 | layer2 | layer3 | layer4 | transversal
layer: {layer}

# ------------------------------------------------------------------
# Dependências
# ------------------------------------------------------------------
requires:
  - "TODO: listar pré-requisitos do sistema (tools, runtimes, outros perfis)"

# ------------------------------------------------------------------
# Artefatos gerados (opcional — documente o que este perfil gera)
# ------------------------------------------------------------------
generates:
  files:
    - path: "TODO/path/to/generated/file"
      source: "scaffold/templates/project/{name}/TODO"
      description: "TODO: descreva o arquivo gerado"
      required: true
      when: null   # null = sempre | "flag" = condicionalmente

  patches: []  # lista de arquivos modificados (não criados) por este perfil

# ------------------------------------------------------------------
# Compatibilidade entre perfis
# ------------------------------------------------------------------
excludes_with:
  - "TODO: liste perfis incompatíveis (ou remova este bloco)"

combines_with:
  - name: devops-programming
    notes: "TODO: descreva como estes perfis se complementam"
  - name: devops-security
    notes: "Sempre combinado — transversal"

# ------------------------------------------------------------------
# Segurança (opcional — documente controles automatizados)
# ------------------------------------------------------------------
security:
  enforces:
    - control: "TODO"       # ex: OWASP-A06, CC8, CWE-312
      description: "TODO: descreva o controle de segurança implementado"
      tool: "TODO"          # ex: bandit, pip-audit, cyclonedx-bom
      severity: "medium"    # critical | high | medium | low
      automated: true       # true se executado automaticamente no CI

# ------------------------------------------------------------------
# Targets de CI (opcional — targets Makefile executados no CI)
# ------------------------------------------------------------------
ci_targets:
  - lint
  - test
  - audit
  - TODO

# ------------------------------------------------------------------
# Notas
# ------------------------------------------------------------------
notes: >
  TODO: adicione notas de uso, referências, decisões de design.
  Exemplos de combinação: scaffold.py --compose {name},devops-security
"""

# ---------------------------------------------------------------------------
# Template MD
# ---------------------------------------------------------------------------

_DESCRIPTOR_MD_TEMPLATE = """\
# Profile Descriptor: `{name}`

> **Status**: draft — gerado em {today} via `scaffold.py --new-profile {name}`

## Visão Geral

TODO: descreva o propósito e escopo deste perfil.

## Pré-requisitos

TODO: liste ferramentas, runtimes e outros perfis necessários.

## Artefatos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `TODO/path/to/file` | TODO |

## Como Usar

```bash
# Aplicar este perfil a um projeto existente
python scripts/scaffold.py --compose {name}

# Validar o descriptor
python scripts/scaffold.py --validate
```

## Compatibilidade

- **Combina com**: `devops-programming`, `devops-security`
- **Incompatível com**: TODO (ou nenhum)

## Controles de Segurança

| Controle | Descrição | Ferramenta | Automatizado |
|----------|-----------|------------|:---:|
| TODO | TODO | TODO | ✅ |

## Notas de Implementação

TODO: decisões de design, referências, links úteis.

## Checklist de Preenchimento

- [ ] `name` único e em kebab-case
- [ ] `description` com propósito claro (2-3 linhas)
- [ ] `meta.maintained_by` preenchido
- [ ] `meta.language` e `meta.framework` corretos
- [ ] `layer` com valor válido
- [ ] `requires` lista ferramentas obrigatórias
- [ ] `generates.files` documenta cada arquivo gerado
- [ ] `combines_with` / `excludes_with` corretos
- [ ] `security.enforces` preenche controles reais
- [ ] `ci_targets` lista targets do Makefile
- [ ] `status` mudado de `draft` para `stable` antes do merge
- [ ] `last_tested` atualizado para a data de validação
- [ ] `python scripts/scaffold.py --validate` passa sem erros
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prompt_layer() -> str:
    """Interativamente pede a camada do perfil."""
    console.print()
    console.print("  [bold]Camada do perfil[/bold]")
    console.print(
        "  [dim]1 — core       (fundação: devops-programming, devops-security)[/dim]"
    )
    console.print(
        "  [dim]2 — layer2     (framework-specific: python-fastapi, typescript-next)[/dim]"
    )
    console.print(
        "  [dim]3 — layer3     (integração: data-pipeline-airflow, k8s-helm)[/dim]"
    )
    console.print(
        "  [dim]4 — layer4     (compliance: soc2-baseline, lgpd-baseline)[/dim]"
    )
    console.print("  [dim]t — transversal (aplica a todos: devops-security)[/dim]")
    console.print()
    valid = {"1": "1", "2": "layer2", "3": "layer3", "4": "layer4", "t": "transversal"}
    while True:
        choice = input("  Camada [1/2/3/4/t]: ").strip().lower()
        if choice in valid:
            return valid[choice]
        console.print("  [red]Opção inválida. Digite 1, 2, 3, 4 ou t.[/red]")


def _prompt_name() -> str:
    """Interativamente pede o nome do perfil."""
    console.print()
    while True:
        name = (
            input("  Nome do perfil (kebab-case, ex: my-framework): ").strip().lower()
        )
        if _KEBAB_RE.match(name):
            return name
        console.print(
            "  [red]Nome inválido. Use apenas letras minúsculas, números e hífens.[/red]"
        )


# ---------------------------------------------------------------------------
# Flow principal
# ---------------------------------------------------------------------------


def flow_new_profile(args: argparse.Namespace) -> int:
    """Gera profile-descriptor YAML + MD a partir de defaults e executa --validate."""
    ci_mode: bool = getattr(args, "ci", False)
    use_json: bool = getattr(args, "json_output", False)
    force: bool = getattr(args, "force", False)
    profile_name: str | None = getattr(args, "new_profile", None)
    layer: str | None = getattr(args, "profile_layer", None)

    # --- Nome ------------------------------------------------------------------
    if not profile_name:
        if ci_mode:
            _emit_error(
                "--new-profile requer um nome (ex: --new-profile my-profile)", use_json
            )
            return 1
        profile_name = _prompt_name()

    # Validar nome
    if not _KEBAB_RE.match(profile_name):
        _emit_error(
            f"Nome inválido: '{profile_name}'. Use apenas letras minúsculas, números e hífens.",
            use_json,
        )
        return 1

    # --- Layer -----------------------------------------------------------------
    if not layer:
        if ci_mode:
            layer = "layer2"  # default sensato em --ci
        else:
            layer = _prompt_layer()

    # --- Caminhos --------------------------------------------------------------
    yaml_path = _PROFILE_DESCRIPTORS_DIR / f"{profile_name}.yaml"
    md_path = _PROFILE_DESCRIPTORS_DIR / f"{profile_name}.md"

    # --- Verificar existência --------------------------------------------------
    if yaml_path.exists() and not force:
        _emit_error(
            f"Perfil '{profile_name}' já existe: {yaml_path}\n"
            "  Use --force para sobrescrever.",
            use_json,
        )
        return 1

    # --- Gerar arquivos -------------------------------------------------------
    today = date.today().isoformat()
    yaml_content = _DESCRIPTOR_YAML_TEMPLATE.format(
        name=profile_name,
        layer=layer,
        today=today,
    )
    md_content = _DESCRIPTOR_MD_TEMPLATE.format(
        name=profile_name,
        today=today,
    )

    try:
        yaml_path.write_text(yaml_content, encoding="utf-8")
        md_path.write_text(md_content, encoding="utf-8")
    except OSError as exc:
        _emit_error(f"Erro ao escrever arquivos: {exc}", use_json)
        return 1

    if not use_json:
        console.print()
        console.print(
            f"  [green]✅ Criado:[/green] {yaml_path.relative_to(Path.cwd())}"
        )
        console.print(f"  [green]✅ Criado:[/green] {md_path.relative_to(Path.cwd())}")
        console.print()
        console.print("  [bold]Próximos passos:[/bold]")
        console.print(
            f"  1. Edite [cyan]scaffold/profiles/{profile_name}.yaml[/cyan] — preencha os TODOs"
        )
        console.print("  2. Execute [cyan]python scripts/scaffold.py --validate[/cyan]")
        console.print()

    # --- Validação automática -------------------------------------------------
    if use_json:
        # Em modo JSON: executamos a validação silenciosamente e embutimos o resultado
        import json as _json

        from .. import validate as _validate_module

        report = _validate_module.validate_descriptors(_PROFILE_DESCRIPTORS_DIR)
        # Re-emite JSON enriquecido com informação de validação
        print(
            _json.dumps(
                {
                    "success": True,
                    "name": profile_name,
                    "layer": layer,
                    "yaml": str(yaml_path),
                    "md": str(md_path),
                    "validate": {
                        "valid": report.valid,
                        "profiles_checked": report.profiles_checked,
                        "errors": report.total_errors,
                        "warnings": report.total_warnings,
                    },
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0

    console.print("  [dim]Executando --validate...[/dim]")
    from .validate import flow_validate

    validate_args = argparse.Namespace(json_output=False)
    rc = flow_validate(validate_args)

    # O descriptor gerado tem TODOs, então validate vai retornar warnings.
    # Isso é esperado — reportamos mas não falhamos.
    if rc != 0 and not use_json:
        console.print(
            "\n  [yellow]⚠  O validator encontrou avisos no novo descriptor.[/yellow]"
            "\n  [dim]Isso é esperado — preencha os campos TODO antes do merge.[/dim]\n"
        )
    elif not use_json:
        console.print("  [green]✅ Validação OK[/green]\n")

    return 0


def _emit_error(msg: str, use_json: bool) -> None:
    if use_json:
        import json as _json

        print(_json.dumps({"success": False, "error": msg}, ensure_ascii=False))
    else:
        console.print(f"\n  [bold red]❌ Erro:[/bold red] {msg}\n")
