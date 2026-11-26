"""flow_upgrade — re-aplica o template a um projeto já existente."""

from __future__ import annotations

import argparse
import json as _json
from pathlib import Path

from .. import composer as _composer_module
from .. import links, project, templates, vscode
from ..ai import resolve_plugins
from ..copilot_rules_consolidate import consolidate_copilot_rules
from ..project import config_from_state, read_scaffold_state, write_scaffold_state
from ..ui import console, print_final_summary

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_PROFILE_DESCRIPTORS_DIR = _PROJECT_ROOT / "scaffold" / "profiles"


def _validate_and_fix_paths(
    state: dict,
    current_target: Path,
    use_json: bool,
    ci_mode: bool = False,
) -> dict | None:
    """
    Valida se os paths no state divergem do local atual de execução.

    Se houver divergência, questiona o usuário sobre qual usar:
    - Atualizar paths no state para refletir local atual
    - Cancelar e executar do local correto

    Args:
        state: Estado lido de .scaffold-state.yaml
        current_target: Path onde upgrade está sendo executado
        use_json: Se True, não interage com usuário (assume paths atuais)
        ci_mode: Se True, não interage com usuário (assume paths atuais)

    Returns:
        state atualizado ou None se usuário cancelar
    """
    import yaml
    from rich.prompt import Prompt

    paths = state.get("paths", {})
    project_name = state.get("project", {}).get("name", "unknown")
    saved_target_dir = Path(paths.get("target_dir", "."))

    # Normalizar saved_target_dir: se termina com project_name, extrai o pai.
    # O state pode ter sido escrito com o diretório do projeto (upgrade in-place)
    # ou com o diretório pai (criação inicial); ambos devem comparar igual.
    if saved_target_dir.name == project_name:
        saved_parent = saved_target_dir.parent
    else:
        saved_parent = saved_target_dir

    # Resolve current_target para comparação
    # Se current_target termina com project_name, extrai o pai
    if current_target.name == project_name:
        current_parent = current_target.parent
    else:
        current_parent = current_target

    # Normalizar paths para comparação (resolve symlinks, relativos, etc)
    saved_target_resolved = saved_parent.resolve()
    current_parent_resolved = current_parent.resolve()

    # Verificar divergência
    if saved_target_resolved == current_parent_resolved:
        # Paths coincidem, tudo ok
        return state

    # DIVERGÊNCIA DETECTADA!
    console.print("\n  [yellow]⚠️  DIVERGÊNCIA DE PATHS DETECTADA[/yellow]\n")
    console.print("  Path salvo em [cyan].scaffold-state.yaml[/cyan]:")
    console.print(f"    [dim]{saved_target_resolved}[/dim]\n")
    console.print("  Path onde upgrade está sendo executado:")
    console.print(f"    [dim]{current_parent_resolved}[/dim]\n")

    if use_json or ci_mode:
        # Modo JSON ou CI: assume usar path atual (não pode interagir)
        mode_label = "Modo JSON" if use_json else "Modo CI"
        console.print(
            f"  [yellow]{mode_label}: atualizando automaticamente para path atual[/yellow]\n"
        )
        state["paths"]["target_dir"] = str(current_parent_resolved)
        # Escreve YAML diretamente (sem ProjectConfig)
        state_file = current_target / ".scaffold-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
        return state

    # Perguntar ao usuário o que fazer
    console.print("  [bold]Escolha uma opção:[/bold]\n")
    console.print(
        "    [green]1[/green] - Usar path atual e atualizar .scaffold-state.yaml"
    )
    console.print(f"        [dim]{current_parent_resolved}[/dim]\n")
    console.print(
        "    [yellow]2[/yellow] - Cancelar upgrade (execute do diretório salvo)"
    )
    console.print(f"        [dim]{saved_target_resolved / project_name}[/dim]\n")

    choice = Prompt.ask(
        "  Sua escolha",
        choices=["1", "2"],
        default="1",
    )

    if choice == "1":
        # Atualizar state com path atual
        console.print(
            "\n  [green]✅ Atualizando .scaffold-state.yaml com path atual[/green]\n"
        )
        state["paths"]["target_dir"] = str(current_parent_resolved)
        # Escreve YAML diretamente (sem ProjectConfig)
        state_file = current_target / ".scaffold-state.yaml"
        with state_file.open("w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
        return state
    else:
        # Usuário escolheu cancelar
        console.print(
            f"\n  [yellow]❌ Upgrade cancelado[/yellow]\n"
            f"  Execute upgrade do diretório correto:\n"
            f"    [cyan]cd {saved_target_resolved / project_name}[/cyan]\n"
            f"    [cyan]scaffold.py upgrade[/cyan]\n"
        )
        return None


def flow_upgrade(args: argparse.Namespace) -> int:
    """
    Modo upgrade: relê .scaffold-state.yaml do projeto alvo e re-aplica
    todos os passos de geração.

    - Arquivos já existentes com conteúdo idêntico → skipped
    - Arquivos já existentes com conteúdo diferente → skipped (use --force para sobrescrever)
    - Arquivos ausentes → criados
    Útil quando o template é atualizado e você quer trazer novidades para
    um projeto existente sem apagar personalizações.
    """
    force: bool = getattr(args, "force", False)
    use_json: bool = getattr(args, "json_output", False)
    ci_mode: bool = getattr(args, "ci", False)

    # Diretório alvo (default: cwd)
    target = Path(args.target_dir) if args.target_dir else Path.cwd()

    state = read_scaffold_state(target)
    if state is None:
        msg = (
            f".scaffold-state.yaml não encontrado em {target}\n"
            "  Este projeto não foi criado com scaffold.py, ou o arquivo foi removido.\n"
            "  Crie um novo projeto com: scaffold.py --new"
        )
        if use_json:
            print(_json.dumps({"error": msg}, ensure_ascii=False))
        else:
            console.print(f"  [bold red]❌ {msg}[/bold red]\n")
        return 1

    # Verificar divergência de paths
    state = _validate_and_fix_paths(state, target, use_json, ci_mode)
    if state is None:
        # Usuário cancelou ou erro fatal
        return 1

    cfg = config_from_state(state, override_target=target)
    profiles_applied: list[str] = state.get("profiles_applied", [])

    if not use_json:
        console.print(
            f"\n  [bold cyan]🔄 Upgrade:[/bold cyan] "
            f"[cyan]{cfg.project_name}[/cyan] | "
            f"domínio: [cyan]{cfg.domain}[/cyan] | "
            f"linguagem: [cyan]{cfg.language}[/cyan]"
        )
        if profiles_applied:
            console.print(
                f"  [dim]Perfis aplicados anteriormente: {', '.join(profiles_applied)}[/dim]"
            )
        if force:
            console.print(
                "  [yellow]⚠  --force: arquivos existentes serão sobrescritos.[/yellow]"
            )
        console.print()

    results = []

    # Em JSON mode, redireciona consoles dos módulos lib para stderr para evitar
    # que warnings de setup (ex: symlink ausente) poluam o output JSON.
    if use_json:
        from rich.console import Console as _RichConsole

        _stderr_console = _RichConsole(stderr=True, highlight=False)
        links.console = _stderr_console

    # Re-aplica todos os passos de geração (idempotentes por design)
    if not use_json:
        console.print("  [blue]📁 Verificando estrutura...[/blue]")
    results.extend(project.create_structure(cfg))

    # Upgrade de cada AI ativo via plugins (symlinks, regras, instruções, config)
    for plugin in resolve_plugins(cfg.ai_assistant):
        if not use_json:
            console.print(f"  [blue]⚡ Verificando {plugin.label}...[/blue]")
        results.extend(plugin.upgrade(cfg, force=force))

    if not use_json:
        console.print("  [blue]🔧 Verificando configuração VS Code...[/blue]")
    results.append(vscode.generate_settings(cfg))
    results.append(vscode.generate_mcp(cfg))
    results.append(vscode.generate_extensions(cfg))
    results.append(vscode.generate_tasks(cfg))
    results.append(vscode.generate_launch(cfg))

    if not use_json:
        console.print("  [blue]🤖 Verificando assets SpecKit...[/blue]")

    # SpecKit oficial: reaplica o instalador para a IA do projeto. O --force do
    # specify repõe templates/scripts/comandos e preserva .specify/memory e specs/.
    results.extend(project.run_speckit_init(cfg))

    # Opção 3: Detectar drift antes de aplicar force
    if force:
        # Primeiro, detectar drift sem force
        drift_results = project.copy_speckit(cfg, force=False)
        drift_files = [
            r for r in drift_results if hasattr(r, "status") and r.status == "drift"
        ]

        if drift_files and not use_json:
            console.print()
            console.print(
                "  [yellow]⚠️  DRIFT DETECTADO EM ARQUIVOS DO TEMPLATE[/yellow]"
            )
            console.print(
                f"  [yellow]{len(drift_files)} arquivo(s) diferem do upstream:[/yellow]"
            )
            console.print()
            for item in drift_files[:10]:  # Mostrar no máximo 10
                console.print(f"    • [dim]{item.path.name}[/dim]")
            if len(drift_files) > 10:
                console.print(f"    ... e mais {len(drift_files) - 10} arquivo(s)")
            console.print()
            console.print("  [yellow]💡 Opções disponíveis:[/yellow]")
            console.print(
                "    1. [cyan]--force ativado[/cyan]: arquivos serão backupados (.backup) e sobrescritos"
            )
            console.print(
                "    2. [cyan]Verificar manualmente[/cyan]: uv run scripts/scaffold.py --check-templates"
            )
            console.print(
                "    3. [cyan]Diff assistido[/cyan]: uv run scripts/scaffold.py --diff-template <arquivo>"
            )
            console.print(
                "    4. [cyan]Merge 3-way[/cyan]: uv run scripts/scaffold.py --merge-template <arquivo>"
            )
            console.print()
            console.print(
                "  [yellow]⚠️  Prosseguindo com --force em 3 segundos...[/yellow]"
            )
            import time

            time.sleep(3)
            console.print()

    # Aplicar copy_speckit com force (se especificado)
    results.extend(project.copy_speckit(cfg, force=force))

    # Agents customizados do scaffold (ADR-003 fatia 6: antes só na criação)
    if not use_json:
        console.print("  [blue]🤖 Verificando agents customizados...[/blue]")
    results.extend(project.copy_custom_agents(cfg, force=force))

    # BUG-16: Consolidação automática de .copilot-rules antes de copiar template
    if not use_json:
        console.print("  [blue]🔀 Consolidando arquivos .copilot-rules...[/blue]")

    # Consolidar múltiplos .copilot-rules*.md em um único arquivo
    consolidated_path = consolidate_copilot_rules(cfg.project_path)
    if consolidated_path:
        if not use_json:
            console.print(f"  [green]✅ Consolidado: {consolidated_path.name}[/green]")
        results.append(
            project.CreatedItem(
                path=consolidated_path,
                kind="file",
                status="merged",
                message="Consolidação automática de múltiplos .copilot-rules*.md",
            )
        )

    # BUG-14: Session Support Libraries (scripts/lib/*.py dependencies)
    if not use_json:
        console.print("  [blue]📚 Verificando bibliotecas de suporte...[/blue]")
    results.extend(project.copy_session_libs(cfg, force=force))

    # BUG-11: Session Scripts (session-index, session-time-tracker, etc)
    if not use_json:
        console.print("  [blue]📊 Verificando scripts de sessão...[/blue]")
    results.extend(project.copy_session_scripts(cfg, force=force))

    # BUG-12: Memory Scripts (create_memory_structure, mem_*, etc)
    if not use_json:
        console.print("  [blue]🧠 Verificando scripts de memory...[/blue]")
    results.extend(project.copy_memory_scripts(cfg, force=force))

    # Utility Scripts (activate-mcp.sh, git-commit-with-file.sh, cleanup-tmp.sh, validate-docs-links.sh)
    if not use_json:
        console.print("  [blue]🔧 Verificando scripts utilitários...[/blue]")
    results.extend(project.copy_utility_scripts(cfg, force=force))

    # Templates GitHub: CONTRIBUTING, PR/issue templates, CODEOWNERS, workflows
    # (ADR-003 fatia 6: antes só na criação)
    if not use_json:
        console.print("  [blue]🐙 Verificando templates GitHub...[/blue]")
    results.extend(project.copy_github_templates(cfg, force=force))

    # BUG-09: Templates de documentação
    if not use_json:
        console.print("  [blue]📋 Verificando templates de documentação...[/blue]")
    results.extend(project.setup_project_docs(cfg, is_upgrade=True))

    if not use_json:
        console.print("  [blue]📜 Verificando constitution.md...[/blue]")
    results.append(project.generate_constitution(cfg))

    if not use_json:
        console.print("  [blue]🔑 Verificando load-mcp.sh...[/blue]")
    results.append(project.generate_load_mcp(cfg))

    if not use_json:
        console.print("  [blue]🔒 Verificando arquivos de segurança GitHub...[/blue]")
    results.extend(project.generate_github_security_files(cfg, force=force))

    # Re-aplica perfis previamente aplicados (idempotentes)
    if profiles_applied:
        composer = _composer_module.ProfileComposer(
            descriptors_dir=_PROFILE_DESCRIPTORS_DIR,
            project_root=_PROJECT_ROOT,
        )
        if not use_json:
            console.print(
                f"  [blue]🧩 Re-aplicando {len(profiles_applied)} perfil(is)...[/blue]"
            )
        # Arquivos de perfil (src/main.py, Dockerfile...) costumam ser editados:
        # só são atualizados com --update-profile-files (nunca pelo --force).
        update_profile_files: bool = getattr(args, "update_profile_files", False)
        divergentes = composer.divergent_files(profiles_applied, cfg)
        if divergentes and not use_json:
            nomes = "\n".join(
                f"      - {p.relative_to(cfg.target_dir)}" for p in divergentes
            )
            if update_profile_files:
                console.print(
                    f"  [yellow]⚠  {len(divergentes)} arquivo(s) de perfil serão"
                    f" atualizados (backup <arquivo>.backup):[/yellow]\n{nomes}"
                )
            else:
                console.print(
                    f"  [yellow]ℹ  {len(divergentes)} arquivo(s) de perfil diferem do"
                    f" template e foram preservados:[/yellow]\n{nomes}\n"
                    "     Para atualizá-los (com backup): --update-profile-files"
                )
        compose_result = composer.compose(
            profiles_applied, cfg, force=update_profile_files
        )
        # Converte CompositionItem → CreatedItem para o resumo
        for item in getattr(compose_result, "items", []):
            results.append(item)
        # IMP-29: Gera/verifica guia de combinação de perfis
        guide_item = templates.generate_profile_guide(
            cfg, profiles_applied, composer.descriptors
        )
        results.append(guide_item)

    # Atualiza state file com updated_at
    write_scaffold_state(cfg, profiles_applied=profiles_applied)

    if use_json:
        created = [r for r in results if hasattr(r, "status") and r.status == "created"]
        skipped = [r for r in results if hasattr(r, "status") and r.status == "skipped"]
        drift = [r for r in results if hasattr(r, "status") and r.status == "drift"]
        errors = [r for r in results if hasattr(r, "status") and r.status == "error"]
        output = {
            "project": cfg.project_name,
            "upgrade": True,
            "created": len(created),
            "skipped": len(skipped),
            "drift": len(drift),
            "errors": len(errors),
            "profiles_applied": profiles_applied,
        }
        if drift:
            output["drift_files"] = [str(r.path) for r in drift[:20]]
        print(_json.dumps(output, indent=2, ensure_ascii=False))
        return 0 if not errors else 1

    # Resumo final (com logging automático se não for --no-log)
    save_log = not getattr(args, "no_log", False)
    log_dir_arg = getattr(args, "log_dir", None)
    log_dir = Path(log_dir_arg) if log_dir_arg else None
    print_final_summary(
        results, project_path=cfg.project_path, save_log=save_log, log_dir=log_dir
    )

    created = [r for r in results if hasattr(r, "status") and r.status == "created"]
    drift = [r for r in results if hasattr(r, "status") and r.status == "drift"]
    errs = [r for r in results if hasattr(r, "status") and r.status == "error"]

    if errs:
        console.print(
            f"  [bold red]❌ {len(errs)} erro(s) durante o upgrade.[/bold red]\n"
        )
        return 1

    if drift:
        console.print()
        console.print(
            f"  [bold yellow]📊 DRIFT DETECTADO: {len(drift)} arquivo(s) diferem do template upstream[/bold yellow]"
        )
        console.print()
        console.print("  [yellow]Arquivos com drift:[/yellow]")
        for item in drift[:15]:
            console.print(f"    • {item.path.relative_to(cfg.project_path)}")
        if len(drift) > 15:
            console.print(f"    ... e mais {len(drift) - 15} arquivo(s)")
        console.print()
        console.print("  [cyan]💡 Para atualizar os arquivos:[/cyan]")
        console.print()
        console.print(
            "    [bold cyan]Opção 1 — Sobrescrever tudo (com backup):[/bold cyan]"
        )
        console.print("      uv run scripts/scaffold.py --upgrade --force")
        console.print()
        console.print("    [bold cyan]Opção 2 — Verificar manualmente:[/bold cyan]")
        console.print("      uv run scripts/scaffold.py --check-templates")
        console.print()
        console.print("    [bold cyan]Opção 3 — Diff individual:[/bold cyan]")
        console.print(
            "      uv run scripts/scaffold.py --diff-template .github/agents/session-manager.agent.md"
        )
        console.print()
        console.print(
            "    [bold cyan]Opção 4 — Merge 3-way (preserva customizações):[/bold cyan]"
        )
        console.print(
            "      uv run scripts/scaffold.py --merge-template .github/agents/session-manager.agent.md"
        )
        console.print()
        console.print(
            "  [dim]Nota: Arquivos com drift NÃO foram modificados (use --force ou merge manual)[/dim]"
        )
        console.print()
        return 0

    if created:
        console.print(
            f"  [bold green]✅ Upgrade concluído: {len(created)} arquivo(s) novo(s) ou atualizado(s).[/bold green]\n"
        )
    else:
        console.print(
            "  [bold green]✅ Projeto já está atualizado — nenhuma mudança necessária.[/bold green]\n"
        )
    return 0
