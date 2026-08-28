"""
lib/ui.py — Interface com usuário: prompts Rich, menus e validação.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

import re
import yaml
from datetime import datetime, timezone
from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .config import (
    ALL_SELECTABLE_PROFILES,
    DOMAIN_DEFAULT_PROFILES,
    SCAFFOLD_VERSION,
    SPECKIT_TRANSVERSAL_PROFILES,
    VALID_AI_ASSISTANTS,
    VALID_DOMAINS,
    VALID_LANGUAGES,
    AiAssistantType,
    CreatedItem,
    LinkStatus,
    ProjectConfig,
    get_default_shared_dir,
    get_default_target_dir,
    load_user_config,
)

console = Console()

# Regex de validação do nome (kebab-case)
_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _to_title(name: str) -> str:
    """Converte kebab-case para Title Case. Ex: my-api-v2 → My Api V2."""
    return " ".join(word.capitalize() for word in name.split("-"))


def _validate_name(name: str) -> bool:
    return bool(_NAME_RE.match(name))


def _validate_directory_conflict(project_name: str, target_dir: Path) -> tuple[bool, str]:
    """
    Valida se há potencial conflito entre nome do projeto e diretório alvo.
    Com a nova lógica de project_path (config.py), se target_dir.name == project_name,o scaffold usa target_dir diretamente (sem criar subdiretório duplicado).

    Esta validação agora apenas AVISA o usuário quando isso acontece,
    sem bloquear a operação.

    Returns:
        (is_valid, warning_message)
    """
    target_dir_resolved = target_dir.resolve()

    # Se nomes coincidem, scaffold criará arquivos diretamente em target_dir
    if target_dir_resolved.name == project_name:
        # Se diretório tem conteúdo, avisar usuário
        if target_dir_resolved.exists() and target_dir_resolved.is_dir():
            try:
                # Verifica se tem algum conteúdo
                has_content = any(target_dir_resolved.iterdir())
                if has_content:
                    # Retorna warning mas permite continuar (valid=True)
                    return True, (
                        f"⚠️  Aviso: o diretório '{target_dir}' já existe e tem conteúdo.\n"
                        f"   Como o nome coincide com o projeto '{project_name}', "
                        f"os arquivos serão criados diretamente neste diretório.\n"
                        f"   Arquivos existentes NÃO serão sobrescritos (serão pulados)."
                    )
            except OSError:
                pass  # Ignorar erros de permissão

    return True, ""


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def show_banner() -> None:
    """Exibe banner Rich com nome do projeto e versão."""
    panel = Panel(
        Text(
            f"🚀  Enterprise Project Scaffold  v{SCAFFOLD_VERSION}", justify="center"),
        style="bold blue",
        border_style="blue",
    )
    console.print()
    console.print(panel)
    console.print()


def show_menu() -> str:
    """
    Exibe menu principal e retorna a opção escolhida ('1'–'4').
    Fica em loop até opção válida.
    """
    while True:
        console.print("  [bold cyan][1][/bold cyan]  Novo Projeto")
        console.print(
            "  [bold cyan][2][/bold cyan]  Verificar Links (.copilot-*)")
        console.print(
            "  [bold cyan][3][/bold cyan]  Gerar .copilot-rules-[projeto].md")
        console.print(
            "  [bold cyan][5][/bold cyan]  Upgrade (re-aplicar template)")
        console.print("  [bold cyan][4][/bold cyan]  Sair")
        console.print()
        choice = Prompt.ask("  Escolha", choices=[
                            "1", "2", "3", "4", "5"], show_choices=False)
        return choice


def collect_project_info(ci_mode: bool = False, **overrides) -> ProjectConfig:
    """
    Coleta informações do projeto via prompts interativos ou via overrides (CI).

    Em modo interativo:
    - Valida formato do project_name (kebab-case)
    - Exibe padrão sugerido para cada campo opcional
    - Permite corrigir antes de confirmar

    Em modo CI (ci_mode=True):
    - Campos obrigatórios ausentes levantam ValueError
    - Campos opcionais usam defaults se ausentes
    """
    # Carregar defaults do JSON e mesclar com overrides
    user_config = load_user_config()
    json_defaults = user_config.get("defaults", {})

    # Mesclar: overrides (CLI) têm prioridade sobre JSON
    merged_defaults = {**json_defaults, **overrides}

    if ci_mode:
        return _collect_ci(merged_defaults)
    return _collect_interactive(merged_defaults)


def _collect_ci(overrides: dict) -> ProjectConfig:
    """Coleta dados no modo CI — sem prompts."""
    required = ("name", "domain", "language")
    missing = [f for f in required if not overrides.get(f)]
    if missing:
        raise ValueError(
            f"Campos obrigatórios ausentes no modo --ci: {', '.join(missing)}"
        )

    domain = overrides["domain"]
    language = overrides["language"]
    if domain not in VALID_DOMAINS:
        raise ValueError(
            f"--domain inválido: '{domain}'. Válidos: {VALID_DOMAINS}")
    if language not in VALID_LANGUAGES:
        raise ValueError(
            f"--language inválido: '{language}'. Válidos: {VALID_LANGUAGES}")

    name = overrides["name"]
    if not _validate_name(name):
        raise ValueError(
            f"--name inválido: '{name}'. Use apenas letras minúsculas, números e hífens."
        )

    # BUG-02 fix: resolve() garante caminho absoluto independente do CWD
    target_dir = Path(overrides["target_dir"]).expanduser().resolve(
    ) if overrides.get("target_dir") else get_default_target_dir().resolve()

    # Validar conflito de diretório (BUG-01)
    is_valid, error_msg = _validate_directory_conflict(name, target_dir)
    if not is_valid:
        raise ValueError(
            f"Conflito de diretório: {name} == {target_dir.name}. {error_msg}")

    # Validar ai_assistant via registry de plugins
    from .ai import resolve_plugins, get_valid_values
    ai_assistant_raw = overrides.get("ai_assistant") or "both"
    valid = get_valid_values()
    if ai_assistant_raw not in valid:
        raise ValueError(
            f"--ai-assistant inválido: '{ai_assistant_raw}'. Válidos: {valid}")

    # Coleta defaults de configuração de cada plugin ativo (ex: shared_dir do Copilot)
    plugin_config: dict = {}
    for plugin in resolve_plugins(ai_assistant_raw):
        plugin_config.update(plugin.get_config_defaults(overrides))

    # shared_dir: plugin_config tem prioridade, depois overrides, depois default
    shared_dir_raw = overrides.get("shared_dir") or plugin_config.get("shared_dir")
    shared_dir = (
        Path(shared_dir_raw).expanduser().resolve()
        if shared_dir_raw
        else get_default_shared_dir().resolve()
    )

    return ProjectConfig(
        project_name=name,
        project_title=overrides.get("title") or _to_title(name),
        description=overrides.get("description") or "",
        domain=domain,
        language=language,
        github_repo=overrides.get("repo") or None,
        shared_dir=shared_dir,
        target_dir=target_dir,
        created_at=_iso_now(),
        extra_profiles=_parse_extra_profiles(overrides.get(
            "extra_profiles") or "domain-only", domain),
        ai_assistant=ai_assistant_raw,
    )


def _select_domain(default: str) -> str:
    """
    Seleção de domínio via menu numerado.

    Args:
        default: Valor padrão (programming, infrastructure, analysis)

    Returns:
        Domínio selecionado
    """
    console.print("\n  [cyan]Domínio do projeto:[/cyan]")

    domain_descriptions = {
        "programming": "Desenvolvimento de software (APIs, apps, CLIs)",
        "infrastructure": "Infraestrutura e DevOps (IaC, K8s, cloud)",
        "analysis": "Análise de dados e BI (ETL, data warehouse)",
    }

    for idx, domain in enumerate(VALID_DOMAINS, start=1):
        desc = domain_descriptions.get(domain, "")
        default_marker = " [dim](default)[/dim]" if domain == default else ""
        console.print(
            f"      [bold cyan][{idx}][/bold cyan]  {domain}  [dim]({desc})[/dim]{default_marker}"
        )

    console.print()

    # Mapear escolha para domínio
    choices = [str(i) for i in range(1, len(VALID_DOMAINS) + 1)]
    default_idx = str(VALID_DOMAINS.index(default) +
                      1) if default in VALID_DOMAINS else "1"

    choice = Prompt.ask(
        "      Escolha",
        choices=choices,
        default=default_idx,
        show_choices=False
    )

    return VALID_DOMAINS[int(choice) - 1]


def _select_language(default: str) -> str:
    """
    Seleção de linguagem via menu numerado.

    Args:
        default: Valor padrão (python, typescript, go, other)

    Returns:
        Linguagem selecionada
    """
    console.print("\n  [cyan]Linguagem principal:[/cyan]")

    language_descriptions = {
        "python": "Python 3.10+",
        "typescript": "TypeScript / JavaScript / Node.js",
        "go": "Go / Golang",
        "other": "Outra linguagem ou multi-linguagem",
    }

    for idx, lang in enumerate(VALID_LANGUAGES, start=1):
        desc = language_descriptions.get(lang, "")
        default_marker = " [dim](default)[/dim]" if lang == default else ""
        console.print(
            f"      [bold cyan][{idx}][/bold cyan]  {lang}  [dim]({desc})[/dim]{default_marker}"
        )

    console.print()

    # Mapear escolha para linguagem
    choices = [str(i) for i in range(1, len(VALID_LANGUAGES) + 1)]
    default_idx = str(VALID_LANGUAGES.index(default) +
                      1) if default in VALID_LANGUAGES else "1"

    choice = Prompt.ask(
        "      Escolha",
        choices=choices,
        default=default_idx,
        show_choices=False
    )

    return VALID_LANGUAGES[int(choice) - 1]


def _select_ai_assistant(default: AiAssistantType) -> AiAssistantType:
    """
    Seleção de assistente de IA via menu numerado, dinâmico a partir do registry de plugins.

    A ordem das opções é determinada pela ordem de registro dos plugins:
    1 = both, 2 = claude, 3 = copilot, 4 = none

    :param default: Valor padrão (ex: "both").
    :type default: AiAssistantType
    :return: Assistente selecionado.
    :rtype: AiAssistantType
    """
    from .ai import get_plugin_menu_options

    console.print("\n  [cyan]Assistente de IA:[/cyan]")
    options = get_plugin_menu_options()

    for idx, (key, desc) in enumerate(options, start=1):
        default_marker = " [dim](default)[/dim]" if key == default else ""
        console.print(
            f"      [bold cyan][{idx}][/bold cyan]  {key}  [dim]({desc})[/dim]{default_marker}"
        )

    console.print()

    choices = [str(i) for i in range(1, len(options) + 1)]
    default_idx = str(next((i for i, (k, _) in enumerate(options, 1) if k == default), 1))

    choice = Prompt.ask(
        "      Escolha",
        choices=choices,
        default=default_idx,
        show_choices=False,
    )
    return options[int(choice) - 1][0]


def _collect_interactive(defaults: dict) -> ProjectConfig:
    """Coleta dados interativamente com Rich prompts."""
    console.print("[bold]Informações do Projeto[/bold]\n", style="blue")

    # project_name — obrigatório, validado
    while True:
        name = Prompt.ask(
            "  [cyan]Nome do projeto[/cyan] [dim](kebab-case, ex: my-api-v2)[/dim]",
            default=defaults.get("name") or "",
        ).strip()
        if not name:
            console.print("  [red]❌ Nome obrigatório.[/red]")
            continue
        if not _validate_name(name):
            console.print(
                "  [red]❌ Formato inválido. Use apenas letras minúsculas, números e hífens.[/red]"
            )
            continue
        break

    title = Prompt.ask(
        "  [cyan]Título legível[/cyan]",
        default=defaults.get("title") or _to_title(name),
    ).strip() or _to_title(name)

    description = Prompt.ask(
        "  [cyan]Descrição[/cyan] [dim](1 frase, opcional)[/dim]",
        default=defaults.get("description") or "",
    ).strip()

    # domain - usando menu numerado
    domain = _select_domain(defaults.get("domain") or "programming")

    # language - usando menu numerado
    language = _select_language(defaults.get("language") or "python")

    # ai_assistant - menu dinâmico via registry de plugins
    ai_assistant = _select_ai_assistant(defaults.get("ai_assistant") or "both")

    github_repo = Prompt.ask(
        "  [cyan]Repositório GitHub[/cyan] [dim](URL ou Enter para pular)[/dim]",
        default=defaults.get("repo") or "",
    ).strip() or None

    # Coleta configuração específica de cada plugin ativo (ex: shared_dir do Copilot)
    from .ai import resolve_plugins
    plugin_config: dict = {}
    for plugin in resolve_plugins(ai_assistant):
        plugin_config.update(plugin.collect_config(defaults))

    shared_dir_str = plugin_config.get("shared_dir") or str(
        defaults.get("shared_dir") or get_default_shared_dir()
    )

    target_dir_str = Prompt.ask(
        "  [cyan]Diretório alvo[/cyan] [dim](onde criar o projeto)[/dim]",
        default=str(defaults.get("target_dir") or get_default_target_dir()),
    ).strip()

    # BUG-02 fix: resolve() garante caminho absoluto independente do CWD
    target_dir = Path(target_dir_str).expanduser().resolve()

    # Validar conflito de diretório (BUG-01)
    is_valid, error_msg = _validate_directory_conflict(name, target_dir)
    if not is_valid:
        console.print(f"\n[bold red]{error_msg}[/bold red]\n")
        raise ValueError(f"Conflito de diretório: {name} == {target_dir.name}")

    return ProjectConfig(
        project_name=name,
        project_title=title,
        description=description,
        domain=domain,
        language=language,
        github_repo=github_repo,
        shared_dir=Path(shared_dir_str).expanduser().resolve(),
        target_dir=target_dir,
        created_at=_iso_now(),
        extra_profiles=_collect_extra_profiles(domain, language),
        ai_assistant=ai_assistant,
    )


def _get_profile_description(profile_name: str) -> str:
    """
    Retorna descrição curta do perfil para exibição no modo interativo.

    Args:
        profile_name: Nome do perfil (ex: "python-fastapi")

    Returns:
        Descrição curta (ex: "REST API com FastAPI")
    """
    descriptions = {
        # Python
        "python-fastapi": "REST API com FastAPI",
        "python-flask": "Web app com Flask",
        # TypeScript/JavaScript
        "typescript-next": "Frontend com Next.js",
        # Infrastructure
        "terraform-aws": "Infraestrutura AWS com Terraform",
        "k8s-helm": "Deploy Kubernetes com Helm",
        # Database
        "database-expert": "Modelagem e otimização de BD",
        # Data
        "data-warehouse-dbt": "Data warehouse com dbt",
        # Security
        "lgpd-baseline": "Compliance LGPD",
        "soc2-baseline": "Compliance SOC2",
        # Architecture
        "backend-architect": "Arquitetura backend",
        "frontend-architect": "Arquitetura frontend",
        # Quality
        "qa-automation-engineer": "Automação de QA",
        # Design
        "ux-design-expert": "Design de experiência",
        "ui-design-expert": "Design de interface",
    }
    return descriptions.get(profile_name, "")


def _get_compatible_layer2_profiles(domain: str, language: str) -> list[str]:
    """
    Retorna perfis de tecnologia compatíveis (Layer 2/3) com domain + language.

    Lê profile-descriptors/*.yaml e filtra por compatibilidade.
    Exclui perfis Layer 1 (já em ALL_SELECTABLE_PROFILES) e transversais.

    Suporta dois formatos de descriptor:
    - Format 1: requires: ["domain == programming", "language == python"]
    - Format 2: meta: { language: typescript, tags: [web, ...] }

    Args:
        domain: Domínio do projeto (programming, infrastructure, analysis)
        language: Linguagem principal (python, typescript, go, other)

    Returns:
        Lista de nomes de perfis compatíveis
        (ex: ["python-fastapi", "terraform-aws", "k8s-helm"])
    """
    profiles = []
    descriptors_dir = (
        Path(__file__).parent.parent.parent / "scaffold" / "profiles"
    )

    if not descriptors_dir.exists():
        return []

    for yaml_file in sorted(descriptors_dir.glob("*.yaml")):
        # Pular perfis Layer 1 (domain base profiles)
        if yaml_file.stem in ALL_SELECTABLE_PROFILES:
            continue

        # Pular perfis transversais (sempre incluídos automaticamente)
        if yaml_file.stem in SPECKIT_TRANSVERSAL_PROFILES:
            continue

        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            domain_ok = False
            language_ok = False

            # Format 1: requires ("domain ==...", "language ==...")
            if "requires" in data:
                requires = data.get("requires", [])
                # Verificar se tem o formato antigo
                has_domain_check = any(
                    "domain ==" in req for req in requires
                )
                has_language_check = any(
                    "language ==" in req for req in requires
                )

                if has_domain_check or has_language_check:
                    # Formato antigo detectado
                    domain_ok = any(
                        f"domain == {domain}" in req for req in requires
                    )
                    language_ok = any(
                        f"language == {language}" in req for req in requires
                    )

            # Format 2: meta (dict estruturado) - sempre processar se presente
            if "meta" in data and not (domain_ok and language_ok):
                meta = data.get("meta", {})
                # Verificar language no meta
                meta_lang = meta.get("language")
                # language: any significa compatível com qualquer linguagem
                if meta_lang == "any":
                    language_ok = True
                elif meta_lang == language:
                    language_ok = True
                # Mapear aliases comuns
                elif meta_lang == "hcl" and language in ["terraform", "other"]:
                    language_ok = True
                elif meta_lang == "yaml" and language in [
                    "kubernetes", "other"
                ]:
                    language_ok = True

                # Inferir domain a partir de tags ou context
                # programming: web, api, cli
                # infrastructure: iac, cloud, k8s
                # analysis: data, etl, analytics
                tags = meta.get("tags", [])
                if domain == "programming":
                    if any(t in tags for t in ["web", "api", "cli", "app"]):
                        domain_ok = True
                elif domain == "infrastructure":
                    infra_tags = [
                        "iac", "cloud", "k8s", "terraform",
                        "kubernetes", "infrastructure"
                    ]
                    if any(t in tags for t in infra_tags):
                        domain_ok = True
                elif domain == "analysis":
                    analysis_tags = ["data", "etl", "analytics", "dbt"]
                    if any(t in tags for t in analysis_tags):
                        domain_ok = True

            if domain_ok and language_ok:
                profiles.append(yaml_file.stem)

        except (yaml.YAMLError, OSError, KeyError):
            # Ignorar arquivos inválidos silenciosamente
            continue

    return profiles


def _select_layer2_profile(domain: str, language: str) -> str | None:
    """
    Selecionar perfil de código específico (Layer 2) no modo interativo.

    Mostra apenas perfis compatíveis com domain + language.
    Pergunta [9] do fluxo interativo.

    Args:
        domain: Domínio do projeto
        language: Linguagem principal

    Returns:
        Nome do perfil selecionado ou None se usuário escolheu "nenhum"
    """
    available = _get_compatible_layer2_profiles(domain, language)

    if not available:
        # Sem perfis Layer 2 disponíveis para esta combinação
        return None

    console.print(
        "\n  [cyan][9] Adicionar perfil de código específico?[/cyan]"
    )
    console.print(
        "      [bold cyan][1][/bold cyan]  Não, apenas estrutura base  "
        "[dim](default)[/dim]"
    )

    for idx, profile in enumerate(available, start=2):
        desc = _get_profile_description(profile)
        desc_str = f" [dim]({desc})[/dim]" if desc else ""
        console.print(
            f"      [bold cyan][{idx}][/bold cyan]  {profile}{desc_str}"
        )

    console.print()

    choices = ["1"] + [str(i) for i in range(2, len(available) + 2)]
    choice = Prompt.ask(
        "      Escolha",
        choices=choices,
        default="1",
        show_choices=False
    )

    if choice == "1":
        return None

    # Converter escolha para índice do array
    idx = int(choice) - 2
    return available[idx]


def _collect_extra_profiles(domain: str, language: str) -> list[str]:
    """
    Pergunta [8]: quais perfis Layer 1 adicionais além do domínio principal.
    Pergunta [9]: perfil Layer 2 código específico
                  (python-fastapi, typescript-next, etc.)

    Opções [8]:
      [1] Apenas meu domínio — só o perfil principal (default)
      [2] Todos disponíveis  — todos os perfis selecionáveis
      [3] Selecionar         — escolha individual por número

    devops-security é sempre incluído (D-20) e não aparece nesta escolha.

    Args:
        domain: Domínio do projeto (programming, infrastructure, analysis)
        language: Linguagem principal (python, typescript, etc.)

    Returns:
        Lista combinada de perfis Layer 1 + Layer 2
    """
    domain_profile = DOMAIN_DEFAULT_PROFILES.get(domain, f"devops-{domain}")
    # Perfis extras (excluindo o do domínio atual)
    available_extras = [
        p for p in ALL_SELECTABLE_PROFILES if p != domain_profile
    ]

    console.print(
        f"\n  [cyan][8] Perfis adicionais além de "
        f"[bold]{domain_profile}[/bold]?[/cyan]"
    )
    console.print(
        "      [dim]devops-security incluído sempre — "
        "não aparece aqui[/dim]"
    )
    console.print(
        f"      [bold cyan][1][/bold cyan]  "
        f"Apenas meu domínio ({domain_profile})  [dim](default)[/dim]"
    )
    console.print("      [bold cyan][2][/bold cyan]  Todos disponíveis")
    console.print(
        "      [bold cyan][3][/bold cyan]  Selecionar individualmente"
    )
    console.print()

    mode = Prompt.ask(
        "      Escolha",
        choices=["1", "2", "3"],
        default="1",
        show_choices=False
    )

    layer1_profiles: list[str] = []

    if mode == "1":
        layer1_profiles = []
    elif mode == "2":
        layer1_profiles = list(available_extras)
    else:
        # mode == "3": seleção individual
        console.print("\n      Perfis disponíveis:")
        for idx, profile in enumerate(available_extras, start=1):
            console.print(f"        [bold cyan][{idx}][/bold cyan]  {profile}")
        console.print()

        raw = Prompt.ask(
            "      Números separados por vírgula [dim](ex: 1,2)[/dim] ou "
            "Enter para nenhum",
            default="",
        ).strip()
        if raw:
            for part in raw.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(available_extras):
                        layer1_profiles.append(available_extras[idx])

    # Pergunta [9]: Selecionar perfil Layer 2 (código específico)
    layer2_profile = _select_layer2_profile(domain, language)

    # Combinar Layer 1 + Layer 2
    result = list(layer1_profiles)
    if layer2_profile:
        result.append(layer2_profile)

    return result


def _parse_extra_profiles(value: str, domain: str) -> list[str]:
    """
    Interpreta o valor de --extra-profiles no modo CI.

    Aceita:
      "domain-only"  → [] (apenas domínio, default)
      "all"          → todos os perfis exceto o domínio
      "none"         → [] (equivalente a domain-only)
      "profile1,profile2" → lista explícita
    """
    domain_profile = DOMAIN_DEFAULT_PROFILES.get(domain, f"devops-{domain}")
    available_extras = [
        p for p in ALL_SELECTABLE_PROFILES if p != domain_profile]

    if value in ("domain-only", "none", ""):
        return []
    if value == "all":
        return list(available_extras)
    # lista explícita
    selected = []
    for name in value.split(","):
        name = name.strip()
        if name in available_extras:
            selected.append(name)
    return selected


def confirm_summary(config: ProjectConfig) -> bool:
    """Exibe tabela resumo da configuração e pede confirmação (s/n)."""
    console.print()
    table = Table(
        title="📋 Resumo do Projeto",
        box=box.ROUNDED,
        border_style="blue",
        show_header=False,
    )
    table.add_column("Campo", style="cyan", no_wrap=True)
    table.add_column("Valor", style="white")

    table.add_row("Nome", config.project_name)
    table.add_row("Título", config.project_title)
    table.add_row("Descrição", config.description or "[dim](vazia)[/dim]")
    table.add_row("Domínio", config.domain)
    table.add_row("Linguagem", config.language)
    table.add_row(
        "Repositório", config.github_repo or "[dim](não informado)[/dim]")
    table.add_row("Shared dir", str(config.shared_dir))
    table.add_row("Target dir", str(config.target_dir))
    table.add_row("Project path", str(config.project_path))

    domain_profile = DOMAIN_DEFAULT_PROFILES.get(
        config.domain, f"devops-{config.domain}")
    extras = config.extra_profiles or []
    all_profiles = [domain_profile] + extras + SPECKIT_TRANSVERSAL_PROFILES
    table.add_row("Perfis SpecKit", ", ".join(all_profiles))

    console.print(table)
    console.print()
    return Confirm.ask("  Confirmar e criar projeto?", default=True)



# Diretório de logs da ferramenta scaffold (scaffold-project/logs/).
# Os logs da operação são gravados aqui além do projeto criado.
_SCAFFOLD_LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def _write_log_to_dir(
    logs_dir: Path,
    items: list[CreatedItem | LinkStatus],
    project_path: Path,
    operation: str,
    timestamp: str,
) -> Path | None:
    """Grava o arquivo de log em um diretório específico. Retorna o Path ou None."""
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / f"{operation}_{timestamp}.log"
        with log_file.open("w", encoding="utf-8") as f:
            f.write(f"# {operation.upper()} Operation Log\n")
            f.write(f"# Timestamp: {timestamp}\n")
            f.write(f"# Project: {project_path.name}\n")
            f.write(f"# Total items: {len(items)}\n\n")

            stats: dict[str, int] = {}
            for item in items:
                s = item.status if isinstance(item, CreatedItem) else item.status
                stats[s] = stats.get(s, 0) + 1

            f.write("## Statistics\n")
            for s, count in stats.items():
                if count > 0:
                    f.write(f"- {s}: {count}\n")
            f.write("\n## Detailed Items\n\n")

            for item in items:
                if isinstance(item, CreatedItem):
                    f.write(f"[{item.status.upper()}] {item.kind} | {item.path}")
                    if item.message:
                        f.write(f" | {item.message}")
                    f.write("\n")
                else:
                    target_str = str(item.target) if item.target else "(no target)"
                    f.write(f"[{item.status.upper()}] symlink | {item.name} -> {target_str}\n")
        return log_file
    except Exception as e:
        console.print(f"[yellow]⚠️  Não foi possível salvar log em {logs_dir}: {e}[/yellow]")
        return None


def save_operation_log(items: list[CreatedItem | LinkStatus], project_path: Path, operation: str = "scaffold", log_dir: Path | None = None) -> Path | None:
    """
    Salva log detalhado da operação em até três locais:
    1. Sempre em <projeto-criado>/logs/ (primary — retornado).
    2. Sempre em <scaffold-project>/logs/ (rastreio da ferramenta).
    3. Em --log-dir customizado, se diferente dos anteriores.

    Args:
        items: Lista de itens criados/operados
        project_path: Caminho do projeto criado
        operation: Nome da operação (scaffold, upgrade, etc.)
        log_dir: Diretório adicional via --log-dir (opcional)

    Returns:
        Path do arquivo de log em <projeto-criado>/logs/, ou None se falhar
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    # 1. Log sempre no projeto criado (project_path/logs/)
    project_logs_dir = project_path / "logs"
    primary_log = _write_log_to_dir(project_logs_dir, items, project_path, operation, timestamp)

    # 2. Log na ferramenta scaffold (_SCAFFOLD_LOGS_DIR), se diferente do projeto
    if project_logs_dir.resolve() != _SCAFFOLD_LOGS_DIR.resolve():
        _write_log_to_dir(_SCAFFOLD_LOGS_DIR, items, project_path, operation, timestamp)

    # 3. Log em --log-dir customizado, se diferente dos anteriores
    if log_dir:
        custom_dir = Path(log_dir)
        if (custom_dir.resolve() != project_logs_dir.resolve()
                and custom_dir.resolve() != _SCAFFOLD_LOGS_DIR.resolve()):
            _write_log_to_dir(custom_dir, items, project_path, operation, timestamp)

    return primary_log


def print_final_summary(items: list[CreatedItem | LinkStatus], project_path: Path | None = None, save_log: bool = True, log_dir: Path | None = None) -> None:
    """
    Exibe tabela Rich agrupada por pasta com status de cada item.

    Args:
        items: Lista de itens criados/operados
        project_path: Caminho do projeto (para salvar log)
        save_log: Se True, salva log detalhado em arquivo
        log_dir: Diretório customizado para logs (default: <projeto>/logs/)
    """
    console.print()

    # Agrupar itens por pasta
    from collections import defaultdict
    folders: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)

    status_styles = {
        "created": "[green]created[/green]",
        "skipped": "[yellow]skipped[/yellow]",
        "error":   "[red]error[/red]",
        "ok":      "[green]ok[/green]",
        "broken":  "[red]broken[/red]",
        "missing": "[yellow]missing[/yellow]",
    }

    for item in items:
        if isinstance(item, CreatedItem):
            path = Path(item.path)

            # Converter para path relativo se project_path fornecido
            if project_path and path.is_absolute():
                try:
                    path = path.relative_to(project_path)
                except ValueError:
                    pass  # Se não for relativo, manter absoluto

            # Agrupar por primeira pasta (ex: .vscode, docs, scripts) ou (root)
            parts = path.parts
            if len(parts) > 1:
                folder = parts[0]  # Primeira pasta (.vscode, docs, etc.)
            else:
                folder = "(root)"  # Arquivo na raiz

            # Adicionar à lista da pasta
            folders[folder].append((
                item.kind,        # Tipo: "file", "dir", etc.
                str(path),        # Path relativo completo ou nome do arquivo
                status_styles.get(item.status, item.status),
                item.message or ""
            ))
        else:  # LinkStatus
            target_str = str(item.target) if item.target else ""
            folders["(symlinks)"].append((
                "symlink",
                item.name,
                status_styles.get(item.status, item.status),
                target_str
            ))

    # Criar tabela agrupada
    table = Table(
        title="✅ Resultado da Operação (Agrupado por Pasta)",
        box=box.ROUNDED,
        border_style="green",
    )
    table.add_column("Pasta / Tipo", style="cyan", width=25)
    table.add_column("Arquivo", style="white")
    table.add_column("Status", width=10)
    table.add_column("Mensagem", style="dim", overflow="fold")

    # Ordenar pastas (root primeiro, symlinks por último, depois alfabeticamente)
    def sort_key(folder: str) -> tuple:
        if folder == "(root)":
            return (0, "")
        elif folder == "(symlinks)":
            return (2, "")
        else:
            return (1, folder)

    sorted_folders = sorted(folders.keys(), key=sort_key)

    for folder in sorted_folders:
        files = folders[folder]
        # Adicionar header da pasta
        table.add_row(f"[bold blue]📁 {folder}[/bold blue]", "", "", f"[dim]{len(files)} arquivo(s)[/dim]")

        # Adicionar arquivos
        for kind, filename, status, message in files:
            table.add_row(
                f"  {kind}",
                filename,
                status,
                message
            )

    console.print(table)

    # Estatísticas resumidas
    stats = {"created": 0, "skipped": 0, "error": 0, "ok": 0}
    for item in items:
        status = item.status if isinstance(item, CreatedItem) else item.status
        stats[status] = stats.get(status, 0) + 1

    summary_parts = []
    if stats.get("created", 0) > 0:
        summary_parts.append(f"[green]{stats['created']} criado(s)[/green]")
    if stats.get("skipped", 0) > 0:
        summary_parts.append(f"[yellow]{stats['skipped']} pulado(s)[/yellow]")
    if stats.get("error", 0) > 0:
        summary_parts.append(f"[red]{stats['error']} erro(s)[/red]")
    if stats.get("ok", 0) > 0:
        summary_parts.append(f"[green]{stats['ok']} ok[/green]")

    if summary_parts:
        console.print(f"\n  {' | '.join(summary_parts)}")

    # Salvar log se solicitado
    if save_log and project_path:
        log_file = save_operation_log(items, project_path, log_dir=log_dir)
        if log_file:
            console.print(f"  [dim]Log salvo em:\n{log_file}[/dim]")

    console.print()
