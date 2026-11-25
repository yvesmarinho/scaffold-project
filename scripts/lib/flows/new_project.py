"""flow_new_project — criação completa de novo projeto."""

from __future__ import annotations

import argparse
from pathlib import Path

from .. import git, github_setup, project, vscode
from ..ai import resolve_plugins
from ..config import DOMAIN_DEFAULT_PROFILES, SPECKIT_TRANSVERSAL_PROFILES
from ..project import write_scaffold_state
from ..ui import collect_project_info, confirm_summary, console, print_final_summary


def flow_new_project(args: argparse.Namespace) -> int:
    """Fluxo completo de criação de novo projeto."""
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
        "extra_profiles": getattr(args, "extra_profiles", None),
        "ai_assistant": getattr(args, "ai_assistant", None),
    }
    # Remove chaves None para não substituir defaults
    overrides = {k: v for k, v in overrides.items() if v is not None}

    try:
        cfg = collect_project_info(ci_mode=ci_mode, **overrides)
    except ValueError as e:
        console.print(f"\n  [bold red]❌ Erro:[/bold red] {e}\n")
        return 1

    if not ci_mode:
        if not confirm_summary(cfg):
            console.print("\n  [yellow]Operação cancelada.[/yellow]\n")
            return 0

    results = []

    # 1. Estrutura de pastas e arquivos base
    console.print("\n  [blue]📁 Criando estrutura...[/blue]")
    results.extend(project.create_structure(cfg))

    # 2. Setup de cada AI ativo via plugins (symlinks, regras, instruções, config)
    for plugin in resolve_plugins(cfg.ai_assistant):
        console.print(f"  [blue]⚡ Configurando {plugin.label}...[/blue]")
        results.extend(plugin.setup(cfg))

    # 4. VS Code: settings, mcp, extensions, tasks, launch
    console.print("  [blue]🔧 Gerando configuração VS Code...[/blue]")
    results.append(vscode.generate_settings(cfg))
    results.append(vscode.generate_mcp(cfg))
    results.append(vscode.generate_extensions(cfg))
    results.append(vscode.generate_tasks(cfg))
    results.append(vscode.generate_launch(cfg))

    # 5. SpecKit: inicialização via specify CLI (agents, prompts, .specify oficiais)
    console.print("  [blue]🤖 Inicializando SpecKit via specify CLI...[/blue]")
    results.extend(project.run_speckit_init(cfg))

    # 5a. Perfis de domínio (scaffold) para Copilot — .github/prompts/domain/
    console.print("  [blue]🤖 Compondo perfis de domínio...[/blue]")
    results.extend(project.copy_speckit(cfg))

    # 5aa. Agents customizados do scaffold — etapa independente do SpecKit
    console.print(
        "  [blue]🤖 Configurando agents customizados para IA selecionada...[/blue]"
    )
    results.extend(project.copy_custom_agents(cfg))

    # 5b. Session Support Libraries: scripts/lib/*.py (dependências)
    console.print("  [blue]📚 Copiando bibliotecas de suporte...[/blue]")
    results.extend(project.copy_session_libs(cfg))

    # 5c. Session Scripts: session-index, session-time-tracker, session-search
    console.print("  [blue]📊 Copiando scripts de sessão...[/blue]")
    results.extend(project.copy_session_scripts(cfg))

    # 5d. Memory Scripts: create_memory_structure, mem_context, mem_search, mem_save
    console.print("  [blue]🧠 Copiando scripts de memory...[/blue]")
    results.extend(project.copy_memory_scripts(cfg))

    # 5e. Utility Scripts: activate-mcp.sh, git-commit-with-file.sh, cleanup-tmp.sh, validate-docs-links.sh
    console.print("  [blue]🔧 Copiando scripts utilitários...[/blue]")
    results.extend(project.copy_utility_scripts(cfg))

    # 5f. GitHub Templates: CONTRIBUTING.md, PR template, CODEOWNERS, Branch Protection guide
    console.print("  [blue]🐙 Copiando templates GitHub (best practices)...[/blue]")
    results.extend(project.copy_github_templates(cfg))

    # 5d. Templates de documentação (BUG-09 fix - corrigido conceito)
    console.print("  [blue]📋 Configurando templates de documentação...[/blue]")
    results.extend(project.setup_project_docs(cfg))

    # 6. Constitution: .specify/memory/constitution.md
    console.print("  [blue]📜 Gerando constitution.md...[/blue]")
    results.append(project.generate_constitution(cfg))

    # 7. MCP script: scripts/load-mcp.sh
    console.print("  [blue]🔑 Gerando load-mcp.sh...[/blue]")
    results.append(project.generate_load_mcp(cfg))

    # 7b. Project Creation Summary (IMP-63) - resumo de criação
    console.print("  [blue]📋 Gerando resumo de criação do projeto...[/blue]")
    results.append(project.generate_project_creation_summary(cfg))

    # 8. Git
    console.print("  [blue]🗃️  Inicializando repositório Git...[/blue]")
    results.append(git.init_repository(cfg))

    # 8b. Proteção avançada de .secrets/ (IMP-60) + ativar pre-commit hook (BUG-#4 fix)
    # IMPORTANTE: Chamado APÓS git.init_repository() para que .git/hooks/ exista
    console.print("  [blue]🔒 Configurando segurança de .secrets/...[/blue]")
    results.extend(project.setup_secrets_security(cfg))

    # 9. GitHub Security Files (BUG-06 fix)
    console.print("  [blue]🔒 Gerando arquivos de segurança GitHub...[/blue]")
    results.extend(project.generate_github_security_files(cfg))

    # 9b. Persiste estado do projeto ANTES do commit (BUG-#3 fix)
    # Calcula profiles aplicados (BUG-#2 fix)
    domain_profile = DOMAIN_DEFAULT_PROFILES.get(cfg.domain, f"devops-{cfg.domain}")
    extras = cfg.extra_profiles or []
    all_profiles = [domain_profile] + extras + SPECKIT_TRANSVERSAL_PROFILES
    write_scaffold_state(cfg, profiles_applied=all_profiles)

    # 10. Commit inicial (IMP-62) - após TODOS os arquivos estarem prontos
    # IMPORTANTE: .scaffold-state.yaml já foi criado acima, será incluído no commit
    console.print("  [blue]💾 Criando commit inicial...[/blue]")
    results.append(git.create_initial_commit(cfg))

    # 11. Tag scaffold-v* (IMP-62)
    console.print("  [blue]🏷️  Criando tag de versão scaffold...[/blue]")
    results.append(git.tag_scaffold(cfg, version="1.0.0"))

    # 12. Branches main/dev/release (spec 067, ADR-004): dev local + GitHub opcional
    console.print("  [blue]🌿 Criando branch dev...[/blue]")
    results.append(git.create_dev_branch(cfg))
    if cfg.github_repo and not getattr(args, "no_github_setup", False):
        console.print("  [blue]🛡️  Configurando branches no GitHub (gh)...[/blue]")
        results.append(github_setup.configure_github_branches(cfg))

    # Resumo final (com logging automático se não for --no-log)
    save_log = not getattr(args, "no_log", False)
    log_dir_arg = getattr(args, "log_dir", None)
    log_dir = Path(log_dir_arg) if log_dir_arg else None
    print_final_summary(
        results, project_path=cfg.project_path, save_log=save_log, log_dir=log_dir
    )

    errors = [r for r in results if hasattr(r, "status") and r.status == "error"]
    if errors:
        console.print(
            f"  [bold red]❌ {len(errors)} erro(s) durante a criação.[/bold red]\n"
        )
        return 1

    # 10. Log scaffold operation (IMP-65-LITE)
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from scaffold_logger import (
            ScaffoldLogger,
            get_current_user,
            get_template_version,
        )

        logger = ScaffoldLogger()
        logger.log_scaffold(
            project_name=cfg.project_name,
            template_version=get_template_version(),
            profile=cfg.language or "base",  # type: ignore[unreachable]  # defensivo: valor de runtime pode não respeitar o Literal
            created_by=get_current_user(),
            path=str(cfg.project_path),
            success=True,
        )
    except Exception as e:
        # Don't fail scaffold if logging fails
        console.print(
            f"  [dim yellow]⚠️  Aviso: Falha ao registrar log: {e}[/dim yellow]"
        )

    console.print(
        f"  [bold green]✅ Projeto '{cfg.project_name}' criado com sucesso![/bold green]\n"
    )
    console.print(f"  [dim]Diretório: {cfg.project_path}[/dim]\n")

    # BUG-05 Phase 2: Se --with-code-profile fornecido, aplicar perfil de código
    if hasattr(args, "with_code_profile") and args.with_code_profile:
        console.print(
            f"\n  [blue]🚀 Aplicando perfil de código '{args.with_code_profile}'...[/blue]\n"
        )
        from .compose import flow_compose_profiles

        # Criar namespace com argumentos para compose
        compose_args = argparse.Namespace(
            compose=args.with_code_profile,
            ci=True,  # Sempre não-interativo quando chamado via --with-code-profile
            json_output=False,
            name=cfg.project_name,
            title=cfg.project_title,
            description=cfg.description,
            domain=cfg.domain,
            language=cfg.language,
            ai_assistant=cfg.ai_assistant,
            repo=cfg.github_repo,
            shared_dir=getattr(args, "shared_dir", None),
            target_dir=str(cfg.project_path),
        )

        # Executar flow_compose_profiles
        result = flow_compose_profiles(compose_args)
        if result != 0:
            console.print(
                f"  [bold red]❌ Erro ao aplicar perfil '{args.with_code_profile}'[/bold red]\n"
            )
            return result

        console.print(
            f"  [bold green]✅ Perfil '{args.with_code_profile}' aplicado com sucesso![/bold green]\n"
        )

    return 0
