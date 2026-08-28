#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "rich>=13.7",
#   "pyyaml>=6.0",
# ]
# ///
"""
scaffold.py — Enterprise Project Scaffold — Entry Point

Subcomandos (v1.1+ — preferido):
  scaffold.py new                           # Novo Projeto (interativo)
  scaffold.py check                         # verifica symlinks e sai
  scaffold.py list-profiles [--json]        # lista perfis disponíveis
  scaffold.py validate [--json]             # valida profile-descriptors
  scaffold.py dry-run --name X --domain Y --language Z [--json]
  scaffold.py compose PROFILES [--json]     # aplica perfis (CSV)
  scaffold.py upgrade [--force]             # re-aplica template
  scaffold.py adopt [--target-dir PATH]     # adota projeto legado (sem state)
  scaffold.py publish [--output-dir PATH]   # gera tarball de release
  scaffold.py new-profile NAME [--profile-layer LAYER]
  scaffold.py infra                         # gera ci.yml, Dockerfile, RUNBOOK

Flags legadas (v1.0 — mantidas por compatibilidade, deprecadas):
  scaffold.py --new | --check | --list-profiles | --validate | --dry-run
  scaffold.py --compose PROFILES | --upgrade | --publish | --new-profile NAME

Modo não-interativo (qualquer forma):
  scaffold.py new --ci --name X --domain Y --language Z
  scaffold.py --ci --name X --domain Y --language Z   # legado

Separação de domínios:
  scaffold.py → scaffolding de projetos (estrutura, links, regras, git)
  Makefile    → build, test, lint, CI/CD (NÃO tem lógica de scaffolding)
"""

from __future__ import annotations
from lib.ui import console, show_banner, show_menu
from lib.flows import (
    _load_descriptor,
    flow_check_links,
    flow_check_templates,
    flow_compose_profiles,
    flow_diff_template,
    flow_dry_run,
    flow_generate_infra,
    flow_generate_rules,
    flow_list_profiles,
    flow_merge_template,
    flow_new_profile,
    flow_new_project,
    flow_objetivo_generate,
    flow_objetivo_init,
    flow_objetivo_migrate,
    flow_objetivo_validate,
    flow_publish,
    flow_release,
    flow_adopt,
    flow_upgrade,
    flow_validate,
)
from lib.config import SCAFFOLD_VERSION

import argparse
import sys
import warnings
from pathlib import Path

# ---------------------------------------------------------------------------
# Subcommand → flat-flag translation (IMP-44)
# ---------------------------------------------------------------------------

# Maps subcommand names to the flat flags they expand to.
# The value is a list of strings that replace the subcommand word in sys.argv.
_SUBCOMMAND_MAP: dict[str, list[str]] = {
    "new":           ["--new"],
    "check":         ["--check"],
    "check-templates": ["--check-templates"],
    "diff-template": ["--diff-template"],
    "merge-template": ["--merge-template"],
    "list-profiles": ["--list-profiles"],
    "validate":      ["--validate"],
    "dry-run":       ["--dry-run"],
    # next positional arg becomes the value
    "compose":       ["--compose"],
    "upgrade":       ["--upgrade"],
    "adopt":         ["--adopt"],
    "publish":       ["--publish"],
    # next positional arg becomes the value
    "new-profile":   ["--new-profile"],
    "infra":         ["--infra"],
    # next positional arg becomes the value
    "release":       ["--release"],
    "objetivo-init":     ["--objetivo-init"],
    "objetivo-validate": ["--objetivo-validate"],
    "objetivo-generate": ["--objetivo-generate"],
    "objetivo-migrate":  ["--objetivo-migrate"],
}

# Subcommands that take a required value as the next positional argument
_SUBCOMMAND_VALUE: frozenset[str] = frozenset(
    {"compose", "new-profile", "release", "diff-template", "merge-template"})


def _translate_subcommand(argv: list[str]) -> tuple[list[str], bool]:
    """If argv[0] is a known subcommand, translate it to legacy flat flags.

    Returns (translated_argv, was_subcommand).
    """
    if not argv:
        return argv, False

    cmd = argv[0]
    if cmd not in _SUBCOMMAND_MAP:
        return argv, False

    replacement = _SUBCOMMAND_MAP[cmd]
    rest = argv[1:]

    if cmd in _SUBCOMMAND_VALUE:
        # The next positional (non-flag) argument is the value for this flag
        new_rest: list[str] = []
        value_consumed = False
        for i, token in enumerate(rest):
            if not token.startswith("-") and not value_consumed:
                new_argv = replacement + [token] + rest[i + 1:]
                return new_argv, True
            new_rest.append(token)
        # No positional value found — pass as-is so argparse can error properly
        return replacement + new_rest, True

    return replacement + rest, True


# Garante que scripts/ está no sys.path para encontrar lib/
sys.path.insert(0, str(Path(__file__).parent))


# ---------------------------------------------------------------------------
# CLI — argparse
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scaffold.py",
        description="Enterprise Project Scaffold — cria projetos a partir do template padrão.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--version", action="version", version=f"scaffold.py {SCAFFOLD_VERSION}"
    )

    # Ações
    action_group = parser.add_argument_group("ações")
    action_group.add_argument(
        "--new",
        action="store_true",
        help="pula menu — inicia fluxo de Novo Projeto diretamente",
    )
    action_group.add_argument(
        "--check",
        action="store_true",
        help="verifica symlinks .copilot-* e sai",
    )
    action_group.add_argument(
        "--check-templates",
        action="store_true",
        dest="check_templates",
        help=(
            "detecta drift de templates SpecKit (IMP-65 Fase 1)\n"
            "  compara versões entre projeto local e upstream\n"
            "  reporta templates desatualizados ou ausentes"
        ),
    )
    action_group.add_argument(
        "--diff-template",
        metavar="TEMPLATE",
        dest="template_name",
        help=(
            "mostra diff entre template local e upstream (IMP-65 Fase 2)\n"
            "  ex: scaffold.py diff-template spec-template\n"
            "  --format: colored (default), markdown, html\n"
            "  --output: arquivo de saída (default: stdout)"
        ),
    )
    action_group.add_argument(
        "--merge-template",
        metavar="TEMPLATE",
        dest="merge_template_name",
        help=(
            "merge de template upstream preservando customizações (IMP-65 Fase 3)\n"
            "  ex: scaffold.py merge-template spec-template\n"
            "  --auto: aplicar se não houver conflitos\n"
            "  --force: aplicar mesmo com conflitos\n"
            "  --dry-run: preview sem aplicar"
        ),
    )
    action_group.add_argument(
        "--list-profiles",
        action="store_true",
        dest="list_profiles",
        help="lista perfis disponíveis com descrição e sai",
    )
    action_group.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="mostra o que seria gerado sem criar arquivos",
    )
    action_group.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="output em JSON (usar com --list-profiles ou --dry-run)",
    )
    action_group.add_argument(
        "--compose",
        metavar="PROFILES",
        help=(
            "aplica perfis ao projeto (lista separada por vírgulas)\n"
            "  ex: --compose typescript-next\n"
            "  ex: --compose devops-programming,python-fastapi"
        ),
    )
    action_group.add_argument(
        "--infra",
        action="store_true",
        help="gera .github/workflows/ci.yml, Dockerfile, docker-compose.yml e docs/RUNBOOK.md",
    )
    action_group.add_argument(
        "--upgrade",
        action="store_true",
        help=(
            "re-aplica o template a um projeto já existente\n"
            "  lê .scaffold-state.yaml no diretório alvo (--target-dir ou cwd)\n"
            "  arquivos ausentes são criados; existentes são mantidos"
        ),
    )
    action_group.add_argument(
        "--adopt",
        action="store_true",
        help=(
            "adota um projeto legado (sem .scaffold-state.yaml) no scaffold\n"
            "  detecta linguagem/domínio (override: --language/--domain/--name/--ai)\n"
            "  cria o state e re-aplica o template sem sobrescrever arquivos existentes"
        ),
    )
    action_group.add_argument(
        "--force",
        action="store_true",
        help=(
            "forçar operação:\n"
            "  --upgrade: sobrescrever arquivos existentes com divergência\n"
            "  --merge-template: aplicar merge mesmo com conflitos"
        ),
    )
    action_group.add_argument(
        "--publish",
        action="store_true",
        help="gera tarball de release do template (dist/enterprise-template-v*.tar.gz)",
    )
    action_group.add_argument(
        "--release",
        metavar="VERSION",
        dest="release_version",
        help=(
            "processo completo de release: CHANGELOG → bump SCAFFOLD_VERSION"
            " → tarball → git tag vX.Y.Z\n"
            "  Ex: --release 1.1.0 | --release 1.1.0 --dry-run"
        ),
    )
    action_group.add_argument(
        "--output-dir",
        metavar="PATH",
        dest="output_dir",
        help="diretório de saída para --publish (default: dist/)",
    )
    action_group.add_argument(
        "--validate",
        action="store_true",
        help="valida todos os profile-descriptors (campos, semver, refs cruzadas)",
    )
    action_group.add_argument(
        "--new-profile",
        metavar="NAME",
        dest="new_profile",
        help=(
            "cria um novo profile-descriptor com campos default e abre --validate\n"
            "  ex: --new-profile meu-framework\n"
            "  ex: --new-profile meu-framework --profile-layer layer2 --ci"
        ),
    )
    action_group.add_argument(
        "--profile-layer",
        metavar="LAYER",
        dest="profile_layer",
        choices=["1", "2", "3", "4", "layer2",
                 "layer3", "layer4", "transversal", "core"],
        default=None,
        help="camada do novo perfil (usar com --new-profile): 1|2|3|4|layer2|layer3|layer4|transversal|core",
    )
    action_group.add_argument(
        "--objetivo-init",
        action="store_true",
        dest="objetivo_init",
        help="inicializa arquivo objetivo.yaml via wizard interativo ou template (ex: scaffold.py objetivo-init)",
    )
    action_group.add_argument(
        "--objetivo-validate",
        action="store_true",
        dest="objetivo_validate",
        help="valida arquivo objetivo.yaml v2.0 (ex: scaffold.py objetivo-validate --file objetivo.yaml)",
    )
    action_group.add_argument(
        "--objetivo-generate",
        action="store_true",
        dest="objetivo_generate",
        help="gera YAML técnico a partir de objetivo.yaml (ex: scaffold.py objetivo-generate)",
    )
    action_group.add_argument(
        "--objetivo-migrate",
        action="store_true",
        dest="objetivo_migrate",
        help="migra objetivo.yaml v1.0 → v2.0 (ex: scaffold.py objetivo-migrate --file objetivo.yaml)",
    )
    action_group.add_argument(
        "--config",
        metavar="FILE",
        help="arquivo YAML com configuração do projeto (força modo não-interativo)",
    )

    # Modo
    mode_group = parser.add_argument_group("modo")
    mode_group.add_argument(
        "--ci",
        action="store_true",
        help="modo não-interativo — usa flags, sem prompts",
    )
    mode_group.add_argument(
        "--no-log",
        action="store_true",
        dest="no_log",
        help="desabilita o salvamento automático de logs de operações",
    )
    mode_group.add_argument(
        "--log-dir",
        "--logdir",
        metavar="PATH",
        dest="log_dir",
        help="diretório para salvar logs (default: <projeto>/logs/)",
    )

    # Campos do projeto
    fields_group = parser.add_argument_group("campos do projeto")
    fields_group.add_argument(
        "--name",        metavar="NAME",  help="nome kebab-case (obrigatório em --ci)")
    fields_group.add_argument(
        "--title",       metavar="TITLE", help="título legível")
    fields_group.add_argument(
        "--description", metavar="DESC",  help="descrição breve")
    fields_group.add_argument(
        "--file",
        metavar="FILE",
        default="objetivo.yaml",
        help="arquivo objetivo.yaml (default: objetivo.yaml)",
    )
    fields_group.add_argument(
        "--input",
        metavar="FILE",
        default="objetivo.yaml",
        help="arquivo de entrada para objetivo-generate (default: objetivo.yaml)",
    )
    fields_group.add_argument(
        "--from-file",
        metavar="FILE",
        dest="from_file",
        help="arquivo JSON com respostas para objetivo-init (modo não-interativo)",
    )
    fields_group.add_argument(
        "--template-only",
        action="store_true",
        dest="template_only",
        help="copiar apenas o template sem wizard (objetivo-init)",
    )
    fields_group.add_argument(
        "--strict",
        action="store_true",
        help="modo strict para objetivo-validate (P1 warnings → errors)",
    )
    fields_group.add_argument(
        "--domain",
        choices=["programming", "infrastructure", "analysis"],
        metavar="DOMAIN",
        help="domínio: programming | infrastructure | analysis",
    )
    fields_group.add_argument(
        "--language",
        choices=["python", "typescript", "go", "other"],
        metavar="LANG",
        help="linguagem: python | typescript | go | other",
    )
    fields_group.add_argument(
        "--repo",       metavar="URL",  help="URL do repositório GitHub")
    fields_group.add_argument(
        "--with-code-profile",
        metavar="PROFILE",
        dest="with_code_profile",
        help=(
            "aplica perfil de código após criar estrutura base (BUG-05 fix)\n"
            "  ex: scaffold.py new --ci --name my-api --domain programming --language python --with-code-profile python-fastapi\n"
            "  equivalente a: scaffold.py new ... && cd my-api && scaffold.py compose python-fastapi"
        ),
    )
    fields_group.add_argument("--shared-dir", metavar="PATH",
                              dest="shared_dir", help="caminho para .copilot-shared")
    fields_group.add_argument("--target-dir", metavar="PATH",
                              dest="target_dir", help="onde criar o projeto (default: cwd)")
    fields_group.add_argument(
        "--format",
        choices=["colored", "markdown", "html"],
        default="colored",
        help="formato de saída para diff-template (default: colored)",
    )
    fields_group.add_argument(
        "--output",
        metavar="FILE",
        dest="output",
        help="arquivo de saída para diff-template (default: stdout)",
    )
    fields_group.add_argument(
        "--auto",
        action="store_true",
        help="auto-aplicar merge se não houver conflitos (merge-template)",
    )
    fields_group.add_argument(
        "--interactive",
        action="store_true",
        help="resolução interativa de conflitos (merge-template)",
    )
    fields_group.add_argument(
        "--extra-profiles",
        metavar="PROFILES",
        dest="extra_profiles",
        default="domain-only",
        help=(
            "perfis SpecKit extras além do domínio principal\n"
            "  domain-only  apenas perfil do domínio (default)\n"
            "  all          todos os perfis disponíveis\n"
            "  none         equivalente a domain-only\n"
            "  p1,p2        lista separada por vírgulas"
        ),
    )
    fields_group.add_argument(
        "--ai-assistant",
        choices=["claude", "copilot", "both", "none"],
        metavar="AI",
        dest="ai_assistant",
        default="both",
        help="assistente de IA: claude | copilot | both | none (default: both)",
    )

    return parser


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

_LEGACY_FLAG_DEPRECATIONS: dict[str, str] = {
    "--new":           "scaffold.py new",
    "--check":         "scaffold.py check",
    "--list-profiles": "scaffold.py list-profiles",
    "--validate":      "scaffold.py validate",
    "--dry-run":       "scaffold.py dry-run",
    "--compose":       "scaffold.py compose PROFILES",
    "--upgrade":       "scaffold.py upgrade",
    "--adopt":         "scaffold.py adopt",
    "--publish":       "scaffold.py publish",
    "--new-profile":   "scaffold.py new-profile NAME",
    "--infra":         "scaffold.py infra",
    "--release":       "scaffold.py release VERSION",
}


def _warn_legacy_flags(argv: list[str]) -> None:
    """Emits a DeprecationWarning for each legacy flat flag found in argv."""
    for flag, suggestion in _LEGACY_FLAG_DEPRECATIONS.items():
        if flag in argv:
            warnings.warn(
                f"{flag} is deprecated. Use subcommand instead: '{suggestion}'",
                DeprecationWarning,
                stacklevel=3,
            )


def main() -> int:
    raw_argv = sys.argv[1:]

    # Attempt subcommand translation BEFORE parsing
    translated, was_subcommand = _translate_subcommand(raw_argv)
    if was_subcommand:
        # Replace argv so build_parser() sees the flat flags
        sys.argv[1:] = translated
    else:
        # Legacy flat-flag invocation — emit deprecation hints
        _warn_legacy_flags(raw_argv)

    parser = build_parser()
    args = parser.parse_args()

    # --config: carrega configuração de arquivo YAML e injeta em args
    if getattr(args, "config", None):
        try:
            cfg_data = _load_descriptor(Path(args.config))
            for key in ("name", "title", "description", "domain", "language", "repo"):
                yaml_val = cfg_data.get(key)
                if yaml_val is not None and getattr(args, key, None) is None:
                    setattr(args, key, str(yaml_val))
            if "shared_dir" in cfg_data and args.shared_dir is None:
                args.shared_dir = cfg_data["shared_dir"]
            if "target_dir" in cfg_data and args.target_dir is None:
                args.target_dir = cfg_data["target_dir"]
            args.ci = True  # força modo não-interativo
        except Exception as exc:
            console.print(
                f"\n  [bold red]❌ Erro ao carregar --config:[/bold red] {exc}\n")
            return 1

    # --validate: valida profile-descriptors e sai
    if getattr(args, "validate", False):
        return flow_validate(args)

    # --new-profile: scaffolda descriptor de novo perfil e sai
    if getattr(args, "new_profile", None):
        return flow_new_profile(args)

    # --publish: gera tarball de release e sai
    if getattr(args, "publish", False):
        return flow_publish(args)

    # --release: processo completo de release (CHANGELOG → bump → tarball → tag)
    if getattr(args, "release_version", None):
        return flow_release(args)

    # --list-profiles: lista perfis e sai
    if getattr(args, "list_profiles", False):
        return flow_list_profiles(args)

    # --upgrade: re-aplica template a projeto existente
    if getattr(args, "upgrade", False):
        if not getattr(args, "json_output", False):
            show_banner()
        return flow_upgrade(args)

    # --adopt: adota projeto legado sem .scaffold-state.yaml
    if getattr(args, "adopt", False):
        if not getattr(args, "json_output", False):
            show_banner()
        return flow_adopt(args)

    # --dry-run: simula criação sem escrever arquivos
    if getattr(args, "dry_run", False):
        if not getattr(args, "json_output", False):
            show_banner()
        return flow_dry_run(args)

    # --compose: aplica perfis e sai
    if getattr(args, "compose", None):
        if not getattr(args, "json_output", False):
            show_banner()
        return flow_compose_profiles(args)

    # --infra: gera arquivos de infra e sai
    if getattr(args, "infra", False):
        if not getattr(args, "json_output", False):
            show_banner()
        return flow_generate_infra(args)

    # --objetivo-init: initialize objetivo.yaml via wizard or template
    if getattr(args, "objetivo_init", False):
        return flow_objetivo_init(args)

    # --objetivo-validate: valida objetivo.yaml v2.0 e sai
    if getattr(args, "objetivo_validate", False):
        return flow_objetivo_validate(args)

    # --objetivo-generate: gera spec YAML a partir de objetivo.yaml e sai
    if getattr(args, "objetivo_generate", False):
        return flow_objetivo_generate(args)

    # --objetivo-migrate: migra v1.0 → v2.0 e sai
    if getattr(args, "objetivo_migrate", False):
        return flow_objetivo_migrate(args)

    # --check: verifica links e sai
    if args.check:
        return flow_check_links(args)

    # --check-templates: detecta drift de templates e sai (IMP-65 Fase 1)
    if getattr(args, "check_templates", False):
        return flow_check_templates(args)

    # --merge-template: merge de template upstream e sai (IMP-65 Fase 3)
    # IMPORTANTE: verificar ANTES de diff-template pois ambos usam template_name
    if getattr(args, "merge_template_name", None):
        # Rename merge_template_name to template_name for flow compatibility
        args.template_name = args.merge_template_name
        return flow_merge_template(args)

    # --diff-template: mostra diff entre templates e sai (IMP-65 Fase 2)
    if getattr(args, "template_name", None):
        return flow_diff_template(args)

    # --new: pula menu
    if args.new or args.ci:
        show_banner()
        return flow_new_project(args)

    # Modo interativo: exibe banner + menu
    show_banner()
    while True:
        choice = show_menu()
        if choice == "1":
            rc = flow_new_project(args)
            return rc
        elif choice == "2":
            rc = flow_check_links(args)
            # não sai — volta ao menu após check
            continue
        elif choice == "3":
            rc = flow_generate_rules(args)
            continue
        elif choice == "5":
            rc = flow_upgrade(args)
            continue
        elif choice == "4":
            console.print("\n  [dim]Até mais.[/dim]\n")
            return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n  Cancelado.\n")
        sys.exit(130)
