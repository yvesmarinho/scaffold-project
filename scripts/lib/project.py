"""
lib/project.py — Criação de estrutura de pastas e arquivos base.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import UTC
from pathlib import Path

from . import file_merge, vscode
from .base_templates import load_base_template, render
from .config import (
    DOMAIN_DEFAULT_PROFILES,
    SPECKIT_SYNC_DATE,
    SPECKIT_TRANSVERSAL_PROFILES,
    CreatedItem,
    ProjectConfig,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Raiz do template (scaffold-project/) deduzida a partir da localização deste módulo
_TEMPLATE_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Placeholders e substituição
# ---------------------------------------------------------------------------

PLACEHOLDERS = {
    "{{PROJECT_NAME}}",
    "{{PROJECT_TITLE}}",
    "{{PROJECT_DESCRIPTION}}",
    "{{CREATED_AT}}",
    "{{DOMAIN}}",
    "{{LANGUAGE}}",
    "{{GITHUB_REPO}}",
}


def _apply_placeholders(text: str, config: ProjectConfig) -> str:
    """Substitui todos os placeholders pelo valor real da config."""
    # Valor para GitHub repo: mostrar link se configurado, senão "(não configurado)"
    github_repo_display = (
        config.github_repo if config.github_repo else "(não configurado)"
    )

    return render(
        text,
        {
            "PROJECT_NAME": config.project_name,
            "PROJECT_TITLE": config.project_title,
            "PROJECT_DESCRIPTION": config.description,
            "CREATED_AT": config.created_at,
            "DOMAIN": config.domain,
            "LANGUAGE": config.language,
            "GITHUB_REPO": github_repo_display,
        },
    )


# ---------------------------------------------------------------------------
# Templates internos
# ---------------------------------------------------------------------------

_README_MD = load_base_template("README.md.tmpl")

_DOCS_INDEX_MD = load_base_template("docs/INDEX.md.tmpl")

_DOCS_TODO_MD = load_base_template("docs/TODO.md.tmpl")

_DOCS_TODAY_ACTIVITIES_MD = load_base_template("docs/TODAY_ACTIVITIES.md.tmpl")

_GITIGNORE = load_base_template("gitignore.tmpl")

_SECRETS_README = load_base_template("secrets/README.md.tmpl")

_SECRETS_SECURITY_MD = load_base_template("secrets/SECURITY.md.tmpl")

_PRE_COMMIT_SECRETS_HOOK = load_base_template("git-hooks/pre-commit.secrets.tmpl")

# ---------------------------------------------------------------------------
# READMEs para sub-pastas de docs/ (IMP-61)
# ---------------------------------------------------------------------------

_DOCS_DEBATES_README = load_base_template("docs/debates/README.md.tmpl")

_DOCS_DECISIONS_README = load_base_template("docs/decisions/README.md.tmpl")

_DOCS_GUIDES_README = load_base_template("docs/guides/README.md.tmpl")

_DOCS_BUGS_README = load_base_template("docs/bugs/README.md.tmpl")

_DOCS_IMPLEMENTATIONS_README = load_base_template("docs/implementations/README.md.tmpl")

_DOCS_RETROSPECTIVES_README = load_base_template("docs/retrospectives/README.md.tmpl")

_DOCS_ARCHITECTURE_README = load_base_template("docs/architecture/README.md.tmpl")

_DOCS_TEMPLATES_README = load_base_template("docs/templates/README.md.tmpl")

_PROJECT_CREATION_SUMMARY = load_base_template("docs/PROJECT_CREATION_SUMMARY.md.tmpl")

# IMP-64: Templates _VSCODE_MCP_JSON e _VSCODE_SETTINGS_JSON removidos.
# Esses arquivos são agora gerados dinamicamente por vscode.py com
# customização por domínio e linguagem.

_MAKEFILE = load_base_template("Makefile.tmpl")

# ---------------------------------------------------------------------------
# Templates de segurança GitHub (BUG-06)
# ---------------------------------------------------------------------------

_SECURITY_MD_WITH_GITHUB = load_base_template("SECURITY.with-github.md.tmpl")

_SECURITY_MD_WITHOUT_GITHUB = load_base_template("SECURITY.without-github.md.tmpl")

_CODEOWNERS = load_base_template("github/CODEOWNERS.tmpl")

_DEPENDABOT_YML = load_base_template("github/dependabot.yml.tmpl")

_SECURITY_SCAN_YML = load_base_template("github/workflows/security-scan.yml.tmpl")

_DEPENDENCY_REVIEW_YML = load_base_template(
    "github/workflows/dependency-review.yml.tmpl"
)

_CLAUDE_MD = load_base_template("claude/CLAUDE.md.tmpl")

_CLAUDE_SETTINGS_JSON = load_base_template("claude/settings.json.tmpl")

_LOGS_README = load_base_template("logs/README.md.tmpl")

_TMP_README = load_base_template("tmp/README.md.tmpl")

_MEMORY_README = load_base_template("memory/README.md.tmpl")

_SESSION_TIME_README = load_base_template("session-time/README.md.tmpl")

# ---------------------------------------------------------------------------
# Pastas a criar
# ---------------------------------------------------------------------------

# Diretórios base (presentes em todos os projetos, independente de AI)
DIRS_BASE = [
    "docs",
    "docs/architecture",
    "docs/bugs",
    "docs/debates",
    "docs/decisions",
    "docs/guides",
    "docs/implementations",
    "docs/retrospectives",
    "docs/templates",
    ".github",
    ".github/agents",
    ".github/skills",
    ".git-hooks",
    ".secrets",
    ".vscode",
    "scripts/lib",
    "scripts/logs",
    "src",
    "logs",
    "tmp",
    ".memory",
    ".session-time",
    ".claude",
    ".claude/commands",
    ".claude/skills",
]

# Diretórios exclusivos do GitHub Copilot (gerenciados pelo CopilotPlugin)
DIRS_COPILOT = [
    "docs/copilot",
]

# Mantido para retrocompatibilidade (usado em testes e imports externos)
DIRS_TO_CREATE = DIRS_BASE + DIRS_COPILOT


# ---------------------------------------------------------------------------
# Arquivos a criar: (caminho relativo, conteúdo_template)
# ---------------------------------------------------------------------------


def get_claude_files() -> list[tuple[str, str]]:
    """
    Retorna os templates de arquivos exclusivos do Claude Code.

    Utilizado pelo ClaudePlugin para obter os templates centralizados
    sem duplicar as strings de conteúdo.

    :return: Lista de (caminho_relativo, conteúdo_template).
    :rtype: list[tuple[str, str]]
    """
    return [
        ("CLAUDE.md", _CLAUDE_MD),
        (".claude/settings.json", _CLAUDE_SETTINGS_JSON),
    ]


# Arquivos base (presentes em todos os projetos, independente de AI)
FILES_BASE: list[tuple[str, str]] = [
    ("README.md", _README_MD),
    ("docs/INDEX.md", _DOCS_INDEX_MD),
    ("docs/TODO.md", _DOCS_TODO_MD),
    ("docs/TODAY_ACTIVITIES.md", _DOCS_TODAY_ACTIVITIES_MD),
    ("docs/architecture/README.md", _DOCS_ARCHITECTURE_README),
    ("docs/debates/README.md", _DOCS_DEBATES_README),
    ("docs/decisions/README.md", _DOCS_DECISIONS_README),
    ("docs/guides/README.md", _DOCS_GUIDES_README),
    ("docs/retrospectives/README.md", _DOCS_RETROSPECTIVES_README),
    ("docs/bugs/README.md", _DOCS_BUGS_README),
    ("docs/implementations/README.md", _DOCS_IMPLEMENTATIONS_README),
    ("docs/templates/README.md", _DOCS_TEMPLATES_README),
    (".gitignore", _GITIGNORE),
    (".secrets/README.md", _SECRETS_README),
    (".secrets/SECURITY.md", _SECRETS_SECURITY_MD),
    (".git-hooks/pre-commit.secrets", _PRE_COMMIT_SECRETS_HOOK),
    # .vscode/mcp.json e settings.json são gerados dinamicamente por vscode.py (IMP-64)
    ("Makefile", _MAKEFILE),
    ("scripts/logs/.gitkeep", ""),
    ("logs/README.md", _LOGS_README),
    ("tmp/README.md", _TMP_README),
    (".memory/README.md", _MEMORY_README),
    (".session-time/README.md", _SESSION_TIME_README),
]

# Mantido para retrocompatibilidade (inclui arquivos Claude)
FILES_TO_CREATE: list[tuple[str, str]] = FILES_BASE + get_claude_files()


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------


def create_structure(config: ProjectConfig) -> list[CreatedItem]:
    """
    Cria a estrutura de pastas e arquivos base do projeto em config.project_path.

    - Pastas já existentes → skipped (sem erro)
    - Arquivos já existentes → skipped (não sobrescreve)
    - Retorna lista de CreatedItem com status de cada operação

    A lista de diretórios e arquivos é montada dinamicamente:
    - DIRS_BASE e FILES_BASE para todos os projetos
    - Plugins ativos (via resolve_plugins) contribuem com seus próprios dirs/files
    """
    from .ai import resolve_plugins

    results: list[CreatedItem] = []
    base = config.project_path
    base.mkdir(parents=True, exist_ok=True)

    # Monta lista de diretórios e arquivos com contribuições dos plugins
    dirs = list(DIRS_BASE)
    all_files = list(FILES_BASE)

    for plugin in resolve_plugins(config.ai_assistant):
        dirs.extend(plugin.get_dirs())
        all_files.extend(plugin.get_files())

    # 1. Pastas
    for dir_rel in dirs:
        dir_path = base / dir_rel
        if dir_path.exists():
            results.append(
                CreatedItem(
                    path=dir_path,
                    kind="dir",
                    status="skipped",
                )
            )
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                results.append(
                    CreatedItem(
                        path=dir_path,
                        kind="dir",
                        status="created",
                    )
                )
            except OSError as e:
                results.append(
                    CreatedItem(
                        path=dir_path,
                        kind="dir",
                        status="error",
                        message=str(e),
                    )
                )

    # 2. Arquivos
    for file_rel, template in all_files:
        file_path = base / file_rel
        if file_path.exists():
            # EXCEÇÃO: Sempre sobrescrever hooks de segurança (garantir versão atualizada)
            # Ref: Fix BUG de hook pre-commit bloqueando .git-hooks/ (2026-04-29)
            if file_rel == ".git-hooks/pre-commit.secrets":
                content = _prepare_content(template, file_rel, config)
                file_path.write_text(content, encoding="utf-8")
                file_path.chmod(0o755)  # rwxr-xr-x
                results.append(
                    CreatedItem(
                        path=file_path,
                        kind="file",
                        status="updated",
                        message="hook de segurança atualizado com versão mais recente",
                    )
                )
                continue

            # NOVO: Tentar merge inteligente ao invés de skip incondicional
            # Fix: BUG-#1.1 (P0 sistêmico - arquivos críticos não mesclados)
            content = _prepare_content(template, file_rel, config)
            merge_result = file_merge.merge_or_skip(
                file_path=file_path,
                template_content=content,
                interactive=False,  # Modo CI (não interativo por padrão)
            )
            results.append(merge_result)
            continue
        try:
            # Substitui {{PROJECT_*}} antes de escrever
            content = _prepare_content(template, file_rel, config)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            results.append(
                CreatedItem(
                    path=file_path,
                    kind="file",
                    status="created",
                )
            )
        except OSError as e:
            results.append(
                CreatedItem(
                    path=file_path,
                    kind="file",
                    status="error",
                    message=str(e),
                )
            )

    # 3. [nome].code-workspace (nome dinâmico) - agora com MCP integrado
    ws_result = vscode.generate_workspace(config)
    results.append(ws_result)

    return results


def _prepare_content(template: str, file_rel: str, config: ProjectConfig) -> str:
    """Aplica placeholders e ajustes especiais (ex: README github section)."""
    if file_rel == "README.md":
        github_section = (
            f"**Repositório**: [{config.github_repo}]({config.github_repo})"
            if config.github_repo
            else ""
        )
        template = template.replace("{github_section}", github_section)
    return _apply_placeholders(template, config)


# ---------------------------------------------------------------------------
# SpecKit — inicialização via specify CLI e cópia de assets customizados
# ---------------------------------------------------------------------------

# Diretório de templates customizados do SpecKit (separado do projeto DEV)
_SPECKIT_TEMPLATES = _TEMPLATE_ROOT / "scaffold" / "templates" / "speckit"
_SKILLS_TEMPLATES = _TEMPLATE_ROOT / "scaffold" / "templates" / "skills"

# Scripts de uso duplo (ADR-003 fatia 4): fonte única em runtime/scripts/,
# copiados para scripts/ do projeto gerado; o repositório usa symlinks
# relativos em scripts/ apontando para cá.
RUNTIME_SCRIPTS_DIR = _TEMPLATE_ROOT / "scaffold" / "templates" / "runtime" / "scripts"
_RUNTIME_LIBS: tuple[str, ...] = (
    "lib/__init__.py",
    "lib/memory.py",
    "lib/git_validators.py",
    "lib/sanitize.py",
    "lib/session_context.py",
    "lib/session_security.py",
    "lib/git_session.py",
    "lib/session_workflow.py",
)
_RUNTIME_SESSION_SCRIPTS: tuple[str, ...] = (
    "session-manager.py",
    "session-time-tracker.py",
)
_RUNTIME_MEMORY_SCRIPTS: tuple[str, ...] = (
    "create_memory_structure.py",
    "mem_context.py",
    "mem_search.py",
    "mem_save.py",
    "test_memory_smoke.py",
)
_RUNTIME_UTILITY_SCRIPTS: tuple[str, ...] = (
    "activate-mcp.sh",
    "git-commit-with-file.sh",
    "cleanup-tmp.sh",
    "validate-docs-links.sh",
)
RUNTIME_FILES: tuple[str, ...] = (
    _RUNTIME_LIBS
    + _RUNTIME_SESSION_SCRIPTS
    + _RUNTIME_MEMORY_SCRIPTS
    + _RUNTIME_UTILITY_SCRIPTS
    + ("git-hooks/commit-msg", "setup-branch-protection.py")
)
# Rituais de sessão viram skills no Copilot (Claude usa .claude/commands/)
_SESSION_SKILLS: tuple[str, ...] = (
    "session-start",
    "session-end",
    "session-start-first",
)

# Mapeamento ai_assistant → integração(ões) do specify CLI
_AI_TO_SPECIFY: dict[str, list[str]] = {
    "claude": ["claude"],
    "copilot": ["copilot"],
    "both": ["claude", "copilot"],
    "none": [],
}

# Integração do specify → binário do agente que o `specify init` exige no PATH.
# Ausente o binário, o scaffold passa `--ignore-agent-tools` (gera os arquivos
# mesmo sem o agente instalado, ex.: CI) e registra um warning.
_SPECIFY_AGENT_BINARY: dict[str, str] = {
    "claude": "claude",
}


def run_speckit_init(config: ProjectConfig) -> list[CreatedItem]:
    """
    Executa `specify init --here --force --integration <name>` no diretório do
    projeto para instalar os assets oficiais e versionados do SpecKit.

    Substitui a cópia manual de agents/prompts/specify do projeto DEV. Para
    cada integração mapeada ao ai_assistant do projeto, roda specify uma vez.

    Args:
        config: Configuração do projeto (usa project_path e ai_assistant)
    """
    results: list[CreatedItem] = []
    integrations = _AI_TO_SPECIFY.get(config.ai_assistant, [])

    if not integrations:
        log.info("ai_assistant=%s → specify init ignorado", config.ai_assistant)
        return results

    for integration in integrations:
        cmd = ["specify", "init", "--here", "--force", "--integration", integration]
        agent_binary = _SPECIFY_AGENT_BINARY.get(integration)
        if agent_binary and shutil.which(agent_binary) is None:
            cmd.append("--ignore-agent-tools")
            log.warning(
                "⚠️  '%s' não encontrado no PATH → specify init com --ignore-agent-tools "
                "(arquivos gerados; instale o agente para usá-los)",
                agent_binary,
            )
        log.info("Executando: %s em %s", " ".join(cmd), config.project_path)
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(config.project_path),
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL,  # evita hanging quando stdin é um TTY interativo
            )
            if proc.returncode == 0:
                results.append(
                    CreatedItem(
                        path=config.project_path / ".specify",
                        kind="dir",
                        status="created",
                        message=f"specify init --integration {integration}",
                    )
                )
            else:
                output_diag = (proc.stderr or proc.stdout or "")[:400]
                log.error("specify init falhou (%s):\n%s", integration, output_diag)
                results.append(
                    CreatedItem(
                        path=config.project_path / ".specify",
                        kind="dir",
                        status="error",
                        message=f"specify init --integration {integration}: {output_diag[:200]}",
                    )
                )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            log.error("Erro ao executar specify init: %s", exc)
            results.append(
                CreatedItem(
                    path=config.project_path / ".specify",
                    kind="dir",
                    status="error",
                    message=f"specify não encontrado ou timeout: {exc}",
                )
            )

    return results


def copy_speckit(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Compõe perfis de domínio do scaffold para o projeto gerado.

    Agents, prompts e .specify/ são gerados exclusivamente por run_speckit_init()
    via `specify init --here --force --integration <IA>`. Esta função NÃO copia
    nenhum asset do SpecKit — apenas os perfis de domínio do scaffold próprio.

    Perfis de domínio vão para .github/skills/<perfil>/SKILL.md e são usados por TODAS as IAs:
      - Claude: session-start referencia .github/skills/<perfil>/SKILL.md diretamente
      - Copilot: carregados como agent skills

    Compõe perfis (de scaffold/profiles/):
      - Perfil de domínio principal (DOMAIN_DEFAULT_PROFILES[cfg.domain])
      - Perfis extras selecionados (cfg.extra_profiles)
      - Sempre: SPECKIT_TRANSVERSAL_PROFILES (ex: devops-security)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes (com backup)
    """
    results: list[CreatedItem] = []
    errors: list[str] = []
    base = config.project_path

    # --- Perfis de domínio — usados por todas as IAs ---
    # 1) principal (pelo domínio)
    domain_profile = DOMAIN_DEFAULT_PROFILES.get(config.domain)
    if domain_profile:
        result = _copy_domain_profile(
            _TEMPLATE_ROOT, base, domain_profile, errors, force=force
        )
        results.append(result)

    # 2) extras selecionados pelo utilizador (D-21)
    for profile_name in config.extra_profiles:
        if profile_name != domain_profile:  # evita duplicata
            result = _copy_domain_profile(
                _TEMPLATE_ROOT, base, profile_name, errors, force=force
            )
            results.append(result)

    # 3) transversais — sempre copiados (D-20)
    for profile_name in SPECKIT_TRANSVERSAL_PROFILES:
        result = _copy_domain_profile(
            _TEMPLATE_ROOT, base, profile_name, errors, force=force
        )
        results.append(result)

    if errors:
        log.warning("⚠️  %d erro(s) ao copiar SpecKit: %s", len(errors), errors)

    return results


# ---------------------------------------------------------------------------
# Custom Agents — etapa independente do SpecKit, por assistente de IA
# ---------------------------------------------------------------------------


def copy_custom_agents(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia agents customizados (e, no Copilot, as skills de sessão) para o projeto gerado.

    Esta etapa é independente do SpecKit:
      - Agents `speckit.*` são gerenciados pelo `specify init` e NÃO são copiados aqui.
      - Agents customizados (ex: session-manager, debug, devops-expert) foram criados
        pelo usuário e devem estar presentes em TODAS as IAs configuradas.

    Destinos por ai_assistant:
      - "claude" / "both"  → .github/agents/ (formato agent.md, acessível ao Claude)
                              Obs: .claude/commands/session-manager..md já existe via
                              copy_claude_config(); esta etapa adiciona a versão agent.
      - "copilot" / "both" → .github/agents/ (idem)
      - "none"             → ignorado.

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes (com backup)
    """
    results: list[CreatedItem] = []
    errors: list[str] = []
    base = config.project_path

    if config.ai_assistant == "none":
        log.info("⏭️  agents customizados ignorados (ai_assistant=none)")
        return results

    src_agents = _SPECKIT_TEMPLATES / "agents"
    if not src_agents.is_dir():
        log.warning("⚠️  scaffold/templates/speckit/agents/ não encontrado")
        return results

    for src_file in sorted(src_agents.glob("*.agent.md")):
        if src_file.name.startswith("speckit."):
            continue  # gerido pelo specify init
        dst_file = base / ".github" / "agents" / src_file.name
        result = _copy_file(src_file, dst_file, force=force)
        if result.status == "error":
            errors.append(str(src_file))
        results.append(result)

    # Rituais de sessão como agent skills (Copilot P0, harness só Copilot).
    # Claude já os recebe em .claude/commands/ via copy_claude_config().
    if config.ai_assistant in ("copilot", "both"):
        for skill_name in _SESSION_SKILLS:
            src_file = _SKILLS_TEMPLATES / skill_name / "SKILL.md"
            dst_file = base / ".github" / "skills" / skill_name / "SKILL.md"
            result = _copy_file(src_file, dst_file, force=force)
            if result.status == "error":
                errors.append(str(src_file))
            results.append(result)

    if errors:
        log.warning(
            "⚠️  %d erro(s) ao copiar agents customizados: %s", len(errors), errors
        )

    return results


# ---------------------------------------------------------------------------
# Objetivo.yaml Patching — adicionar campos ausentes durante upgrade
# ---------------------------------------------------------------------------


def _patch_objetivo_yaml(dst_objetivo: Path, src_template: Path) -> CreatedItem:
    """
    Patch objetivo.yaml existente com campos ausentes do template.

    Operação non-destructive:
    - Lê objetivo.yaml existente
    - Verifica se project.docstyle existe
    - Se não existir, adiciona após project.success_statement
    - Preserva formatação, comentários e todo conteúdo existente

    Args:
        dst_objetivo: Path para objetivo.yaml existente
        src_template: Path para template com campos padrão

    Returns:
        CreatedItem com status "updated" se modificou, "skipped" se já tinha

    Ref: BUG-001 Fix #1 — docstyle ausente em repositórios legados
    """
    try:
        # Ler arquivo existente
        existing_content = dst_objetivo.read_text(encoding="utf-8")

        # Verificar se project.docstyle já existe
        if "docstyle:" in existing_content:
            log.info("⏭️  objetivo.yaml já tem docstyle")
            return CreatedItem(
                path=dst_objetivo,
                kind="file",
                status="skipped",
                message="Campo docstyle já presente",
            )

        # Ler template para extrair valor default de docstyle
        template_content = src_template.read_text(encoding="utf-8")

        # Extrair linha do docstyle do template
        docstyle_line = None
        for line in template_content.split("\n"):
            if "docstyle:" in line:
                # Preservar indentação correta (2 espaços para campo project)
                docstyle_line = line
                break

        if not docstyle_line:
            log.warning("⚠️  Template não contém docstyle, pulando patch")
            return CreatedItem(
                path=dst_objetivo,
                kind="file",
                status="skipped",
                message="Template sem docstyle",
            )

        # Encontrar onde inserir: após success_statement ou problema/statement
        lines = existing_content.split("\n")
        insert_index = -1

        for i, line in enumerate(lines):
            # Procurar success_statement (campo que vem antes de docstyle)
            if "success_statement:" in line:
                # Encontrar próxima linha não-vazia após success_statement
                j = i + 1
                while j < len(lines) and (
                    not lines[j].strip() or lines[j].strip().startswith("#")
                ):
                    j += 1
                # Se próxima linha é stakeholders:, inserir antes
                if j < len(lines) and "stakeholders:" in lines[j]:
                    insert_index = j
                    break
                # Caso contrário, inserir após success_statement
                insert_index = i + 1
                break

        if insert_index == -1:
            log.warning("⚠️  Não encontrei onde inserir docstyle, pulando patch")
            return CreatedItem(
                path=dst_objetivo,
                kind="file",
                status="skipped",
                message="Ponto de inserção não encontrado",
            )

        # Inserir docstyle
        lines.insert(insert_index, docstyle_line)
        patched_content = "\n".join(lines)

        # Criar backup antes de modificar
        backup_path = dst_objetivo.with_suffix(".yaml.backup")
        dst_objetivo.rename(backup_path)

        # Escrever conteúdo modificado
        dst_objetivo.write_text(patched_content, encoding="utf-8")

        log.info("✅ objetivo.yaml: adicionado campo docstyle")
        return CreatedItem(
            path=dst_objetivo,
            kind="file",
            status="updated",
            message=f"Campo docstyle adicionado (backup: {backup_path.name})",
        )

    except Exception as exc:
        log.warning("⚠️  Erro ao fazer patch de objetivo.yaml: %s", exc)
        return CreatedItem(
            path=dst_objetivo, kind="file", status="error", message=str(exc)
        )


# ---------------------------------------------------------------------------
# Templates de documentação — setup inicial do projeto
# ---------------------------------------------------------------------------


def setup_project_docs(
    config: ProjectConfig, is_upgrade: bool = False
) -> list[CreatedItem]:
    """
    Configura templates de documentação do projeto.

    Operações:
      1. objetivo-manifest-template.yaml → objetivo.yaml (raiz, com placeholders)
      2. mcp-questions-template.yaml → mcp-questions.yaml (raiz)

    Substituições em objetivo.yaml:
      - CHANGE_ME (project.name) → config.project_name
      - CHANGE_ME (summary) → config.description
      - CHANGE_ME (problem_statement) → config.description
      - Pasta do projeto atualizada

    Arquivos já existentes são saltados (idempotente).

    UPGRADE: Se objetivo.yaml existe, verifica e adiciona campos ausentes (ex: docstyle).

    Args:
        config: Configuração do projeto
        is_upgrade: True se executando durante scaffold upgrade

    Ref: BUG-09 (corrigido) — documentado em docs/lembrete.md
    Ref: BUG-001 Fix #1 — patch de docstyle durante upgrade
    Ref: BUG-22 — evitar criação automática de pastas de sessão datadas
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_templates = _TEMPLATE_ROOT / "scaffold" / "templates" / "docs"

    if not src_templates.is_dir():
        log.warning("⚠️  Diretório de origem não encontrado: %s", src_templates)
        return results

    # 1. objetivo.yaml (raiz, com substituições)
    src_objetivo = src_templates / "objetivo-manifest-template.yaml"
    dst_objetivo = base / "objetivo.yaml"
    try:
        if dst_objetivo.exists():
            # BUG-001 Fix #1: Patch campos ausentes durante upgrade
            patch_result = _patch_objetivo_yaml(dst_objetivo, src_objetivo)
            results.append(patch_result)
        else:
            content = src_objetivo.read_text(encoding="utf-8")
            # Substituir placeholders
            content = content.replace(
                'name: "CHANGE_ME"', f'name: "{config.project_name}"'
            )
            content = content.replace(
                'summary: "CHANGE_ME (1-2 linhas)"', f'summary: "{config.description}"'
            )
            content = content.replace(
                'problem_statement: "CHANGE_ME (qual dor real será resolvida?)"',
                f'problem_statement: "{config.description}"',
            )
            content = content.replace(
                'team_or_person: "CHANGE_ME"',
                f'team_or_person: "{config.project_name} team"',
            )
            content = content.replace(
                '- "CHANGE_ME"', f'- "{config.project_name} owner"'
            )

            dst_objetivo.write_text(content, encoding="utf-8")
            log.info("✅ criado: objetivo.yaml")
            results.append(
                CreatedItem(path=dst_objetivo, kind="file", status="created")
            )
    except OSError as exc:
        log.warning("⚠️  erro ao criar objetivo.yaml: %s", exc)
        results.append(
            CreatedItem(
                path=dst_objetivo, kind="file", status="error", message=str(exc)
            )
        )

    # 2. mcp-questions.yaml (raiz, cópia direta)
    src_mcp = src_templates / "mcp-questions-template.yaml"
    dst_mcp = base / "mcp-questions.yaml"
    result = _copy_file(src_mcp, dst_mcp)
    results.append(result)

    return results


# ---------------------------------------------------------------------------
# Session Support Libraries — módulos compartilhados necessários para scripts
# ---------------------------------------------------------------------------


def copy_session_libs(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia módulos compartilhados necessários para scripts de sessão e memory.

    Módulos copiados:
      1. scripts/lib/__init__.py
      2. scripts/lib/memory.py (usado por memory scripts)
      3. scripts/lib/git_validators.py (usado por session-time-tracker, pre-commit hooks)
      4. scripts/lib/sanitize.py (usado por mem_save para detectar/sanitizar secrets)
      5. scripts/lib/session_context.py (usado por session-manager)
      6. scripts/lib/session_security.py (usado por session-manager)
      7. scripts/lib/git_session.py (usado por session-manager)
      8. scripts/lib/session_workflow.py (usado por session-manager)

    Esses módulos são dependências dos scripts de sessão e memory system.
    Sem eles, os scripts falham com ModuleNotFoundError.

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-14 — session scripts missing lib dependencies
    Ref: BUG-19 — git_validators.py deployment
    Ref: BUG-001 Fix #4 — sanitize.py missing for mem_save
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_lib = RUNTIME_SCRIPTS_DIR / "lib"
    dst_lib = base / "scripts" / "lib"

    # Criar diretório scripts/lib/ se não existir
    dst_lib.mkdir(parents=True, exist_ok=True)

    libs_to_copy = [rel.removeprefix("lib/") for rel in _RUNTIME_LIBS]

    for lib_name in libs_to_copy:
        src_file = src_lib / lib_name
        dst_file = dst_lib / lib_name
        result = _copy_file(src_file, dst_file, force=force)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Session Scripts — cópia de scripts de rastreamento para novo projeto
# ---------------------------------------------------------------------------


def copy_session_scripts(
    config: ProjectConfig, force: bool = False
) -> list[CreatedItem]:
    """
    Copia scripts de rastreamento de sessão para o novo projeto.

    Scripts copiados:
      1. session-manager.py → scripts/session-manager.py
      2. session-time-tracker.py → scripts/session-time-tracker.py

    Esses scripts são necessários para:
      - Orquestrar rituais de sessão (session-manager.py); o registro da
        sessão é feito pelo agente no vault Obsidian via MCP obsidian-rest
      - Rastrear tempo de trabalho (session-time-tracker.py)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-11 — session-start-first incomplete initialization
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = RUNTIME_SCRIPTS_DIR

    scripts_to_copy = list(_RUNTIME_SESSION_SCRIPTS)

    for script_name in scripts_to_copy:
        src_script = src_root / script_name
        dst_script = base / "scripts" / script_name
        result = _copy_file(src_script, dst_script, force=force)
        results.append(result)

    return results


def copy_memory_scripts(
    config: ProjectConfig, force: bool = False
) -> list[CreatedItem]:
    """
    Copia scripts do memory system para o novo projeto.

    Scripts copiados:
      1. create_memory_structure.py → scripts/create_memory_structure.py
      2. mem_context.py → scripts/mem_context.py
      3. mem_search.py → scripts/mem_search.py
      4. mem_save.py → scripts/mem_save.py
      5. test_memory_smoke.py → scripts/test_memory_smoke.py

    Esses scripts são necessários para:
      - Criar estrutura .memory/ (create_memory_structure.py)
      - Buscar memories por contexto (mem_context.py)
      - Buscar memories por query (mem_search.py)
      - Salvar novo memory (mem_save.py)
      - Testar funcionalidade do memory system (test_memory_smoke.py)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-12 — memory system not initialized
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = RUNTIME_SCRIPTS_DIR

    scripts_to_copy = list(_RUNTIME_MEMORY_SCRIPTS)

    for script_name in scripts_to_copy:
        src_script = src_root / script_name
        dst_script = base / "scripts" / script_name
        result = _copy_file(src_script, dst_script, force=force)
        results.append(result)

    return results


def copy_utility_scripts(
    config: ProjectConfig, force: bool = False
) -> list[CreatedItem]:
    """
    Copia scripts shell utilitários para o novo projeto.

    Scripts copiados:
      1. activate-mcp.sh → scripts/activate-mcp.sh
      2. git-commit-with-file.sh → scripts/git-commit-with-file.sh
      3. cleanup-tmp.sh → scripts/cleanup-tmp.sh
      4. validate-docs-links.sh → scripts/validate-docs-links.sh

    Esses scripts são necessários para:
      - Validar e ativar servidores MCP (activate-mcp.sh)
      - Git commits com arquivo de mensagem (git-commit-with-file.sh)
      - Limpar arquivos temporários (cleanup-tmp.sh)
      - Validar links em documentação (validate-docs-links.sh)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: Validação pós-scaffold - scripts shell essenciais
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = RUNTIME_SCRIPTS_DIR

    scripts_to_copy = list(_RUNTIME_UTILITY_SCRIPTS)

    for script_name in scripts_to_copy:
        src_script = src_root / script_name
        dst_script = base / "scripts" / script_name
        result = _copy_file(src_script, dst_script, force=force)
        # Garantir permissões executáveis (755)
        if result.status in ("created", "updated") and dst_script.exists():
            try:
                dst_script.chmod(0o755)
                log.debug("✅ Permissões executáveis aplicadas: %s", dst_script.name)
            except OSError as exc:
                log.warning(
                    "⚠️  Não foi possível aplicar chmod 755 em %s: %s", dst_script, exc
                )
        results.append(result)

    return results


def copy_copilot_instructions(
    config: ProjectConfig, force: bool = False
) -> list[CreatedItem]:
    """
    Copia arquivos de instruções customizadas do Copilot para o novo projeto.

    Arquivos copiados:
      1. copilot-instructions.md → .github/copilot-instructions.md
      2. .copilot-rules.md → .copilot-rules.md (raiz)

    Esses arquivos são necessários para:
      - Persistir instruções customizadas do Copilot (copilot-instructions.md)
      - Definir regras críticas P0/P1 do projeto (.copilot-rules.md)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-13 — copilot instructions not persisted
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT

    # Copiar copilot-instructions.md para .github/
    src_instructions = src_root / ".github" / "copilot-instructions.md"
    dst_instructions = base / ".github" / "copilot-instructions.md"
    result = _copy_file(src_instructions, dst_instructions, force=force)
    results.append(result)

    # Copiar .copilot-rules.md para raiz do projeto
    src_rules = src_root / ".copilot-rules.md"
    dst_rules = base / ".copilot-rules.md"
    result = _copy_file(src_rules, dst_rules, force=force)
    results.append(result)

    return results


def copy_claude_config(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia configuração do Claude Code para o novo projeto.

    Arquivos copiados:
      1. .claude/commands/*.md → .claude/commands/ (todos os slash commands)
      2. .claude/skills/*/SKILL.md → .claude/skills/*/ (todos os skills)

    Nota: .claude/settings.json e CLAUDE.md são gerados via FILES_TO_CREATE
    em create_structure() com placeholders substituídos automaticamente.
    settings.local.json (machine-specific) NÃO é copiado — fica em .gitignore.

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: IMP-XX — Claude Code integration
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_claude = _TEMPLATE_ROOT / ".claude"

    if not src_claude.is_dir():
        log.warning("⚠️  Diretório .claude/ não encontrado em %s", _TEMPLATE_ROOT)
        return results

    # 1. commands/ — copiar todos os .md (slash commands)
    src_commands = src_claude / "commands"
    if src_commands.is_dir():
        for src_file in sorted(src_commands.glob("*.md")):
            dst_file = base / ".claude" / "commands" / src_file.name
            result = _copy_file(src_file, dst_file, force=force)
            results.append(result)
    else:
        log.warning("⚠️  .claude/commands/ não encontrado em %s", _TEMPLATE_ROOT)

    # 2. skills/ — copiar cada subdiretório (skill_name/SKILL.md e arquivos extras)
    src_skills = src_claude / "skills"
    if src_skills.is_dir():
        for skill_dir in sorted(src_skills.iterdir()):
            if skill_dir.is_dir():
                for src_file in sorted(skill_dir.rglob("*")):
                    if src_file.is_file():
                        rel = src_file.relative_to(src_claude)
                        dst_file = base / ".claude" / rel
                        result = _copy_file(src_file, dst_file, force=force)
                        results.append(result)
    else:
        log.warning("⚠️  .claude/skills/ não encontrado em %s", _TEMPLATE_ROOT)

    return results


def copy_github_templates(
    config: ProjectConfig, force: bool = False
) -> list[CreatedItem]:
    """
    Copia templates de GitHub Best Practices para o novo projeto.

    Templates copiados (P1):
      1. CONTRIBUTING.md → raiz do projeto (com substituição de variáveis)
      2. PULL_REQUEST_TEMPLATE.md → .github/
      3. CODEOWNERS → .github/
      4. BRANCH_PROTECTION_SETUP.md → docs/

    Templates adicionais (P2):
      5. Issue templates → .github/ISSUE_TEMPLATE/ (bug, feature, docs, question)
      6. GitHub Actions workflows → .github/workflows/
      7. Git hooks → scripts/git-hooks/
      8. Badge guide → .github/BADGES.md
      9. Branch protection script → scripts/

    Variáveis substituídas:
      - {{ project_name }} → config.project_name
      - {{ current_date }} → config.created_at
      - {{ github_repo }} → config.github_repo (se configurado)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: P1/P2 - GitHub Best Practices Integration
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT / "scaffold" / "templates" / "base-configs" / "common"

    # Mapeamento de variáveis customizadas para templates GitHub
    github_owner_repo = config.github_repo if config.github_repo else "owner/repo"
    github_parts = (
        github_owner_repo.split("/") if "/" in github_owner_repo else ["owner", "repo"]
    )

    template_vars = {
        "{{ project_name }}": config.project_name,
        "{{ current_date }}": config.created_at.split("T")[0],  # YYYY-MM-DD apenas
        "{{ github_repo }}": github_parts[1] if len(github_parts) > 1 else "repo",
        "{{ github_owner }}": github_parts[0] if len(github_parts) > 0 else "owner",
    }

    # === P1 Templates ===

    # 1. CONTRIBUTING.md → raiz (com substituição de variáveis)
    src_contributing = src_root / "CONTRIBUTING.md"
    dst_contributing = base / "CONTRIBUTING.md"
    result = _copy_file_with_vars(
        src_contributing, dst_contributing, template_vars, force=force
    )
    results.append(result)

    # 2. PULL_REQUEST_TEMPLATE.md → .github/
    src_pr_template = src_root / "PULL_REQUEST_TEMPLATE.md"
    dst_pr_template = base / ".github" / "PULL_REQUEST_TEMPLATE.md"
    result = _copy_file(src_pr_template, dst_pr_template, force=force)
    results.append(result)

    # 3. CODEOWNERS → .github/
    src_codeowners = src_root / "CODEOWNERS"
    dst_codeowners = base / ".github" / "CODEOWNERS"
    result = _copy_file_with_vars(
        src_codeowners, dst_codeowners, template_vars, force=force
    )
    results.append(result)

    # 4. BRANCH_PROTECTION_SETUP.md → docs/
    src_guide = _TEMPLATE_ROOT / "docs" / "guides" / "BRANCH_PROTECTION_SETUP.md"
    dst_guide = base / "docs" / "BRANCH_PROTECTION_SETUP.md"
    result = _copy_file_with_vars(src_guide, dst_guide, template_vars, force=force)
    results.append(result)

    # === P2 Templates ===

    # 5. Issue templates → .github/ISSUE_TEMPLATE/ (.yml da base-configs + .md do template root)
    issue_templates_yml = [
        "bug_report.yml",
        "feature_request.yml",
        "documentation.yml",
        "question.yml",
        "config.yml",
    ]
    for template_name in issue_templates_yml:
        src_issue = src_root / "ISSUE_TEMPLATE" / template_name
        dst_issue = base / ".github" / "ISSUE_TEMPLATE" / template_name
        result = _copy_file_with_vars(src_issue, dst_issue, template_vars, force=force)
        results.append(result)
    src_issue_md = _TEMPLATE_ROOT / ".github" / "ISSUE_TEMPLATE"
    if src_issue_md.is_dir():
        for src_file in sorted(src_issue_md.glob("*.md")):
            dst_file = base / ".github" / "ISSUE_TEMPLATE" / src_file.name
            result = _copy_file(src_file, dst_file, force=force)
            results.append(result)

    # 6. GitHub Actions workflows → .github/workflows/
    src_workflow = src_root / "workflows" / "git-validation.yml"
    dst_workflow = base / ".github" / "workflows" / "git-validation.yml"
    result = _copy_file_with_vars(
        src_workflow, dst_workflow, template_vars, force=force
    )
    results.append(result)

    # 7. Git hooks → scripts/git-hooks/
    src_hook = RUNTIME_SCRIPTS_DIR / "git-hooks" / "commit-msg"
    dst_hook = base / "scripts" / "git-hooks" / "commit-msg"
    result = _copy_file(src_hook, dst_hook, force=force)
    # Garantir permissões executáveis
    if result.status in ("created", "updated") and dst_hook.exists():
        try:
            dst_hook.chmod(0o755)
            log.debug("✅ Permissões executáveis aplicadas: %s", dst_hook.name)
        except OSError as exc:
            log.warning(
                "⚠️  Não foi possível aplicar chmod 755 em %s: %s", dst_hook, exc
            )
    results.append(result)

    # 8. Badge guide → .github/BADGES.md
    src_badges = src_root / "BADGES.md"
    dst_badges = base / ".github" / "BADGES.md"
    result = _copy_file_with_vars(src_badges, dst_badges, template_vars, force=force)
    results.append(result)

    # 9. Branch protection script → scripts/
    src_script = RUNTIME_SCRIPTS_DIR / "setup-branch-protection.py"
    dst_script = base / "scripts" / "setup-branch-protection.py"
    result = _copy_file(src_script, dst_script, force=force)
    # Garantir permissões executáveis
    if result.status in ("created", "updated") and dst_script.exists():
        try:
            dst_script.chmod(0o755)
            log.debug("✅ Permissões executáveis aplicadas: %s", dst_script.name)
        except OSError as exc:
            log.warning(
                "⚠️  Não foi possível aplicar chmod 755 em %s: %s", dst_script, exc
            )
    results.append(result)

    return results


def _copy_file_with_vars(
    src: Path, dst: Path, template_vars: dict[str, str], force: bool = False
) -> CreatedItem:
    """
    Copia arquivo aplicando substituição de variáveis.

    Args:
        src: Arquivo de origem
        dst: Arquivo de destino
        template_vars: Dicionário de variáveis a substituir
        force: Se True, sobrescreve arquivo existente

    Returns:
        CreatedItem com status da operação
    """
    if not src.exists():
        msg = f"origem não encontrada: {src}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    # Verificar se destino existe
    if dst.exists() and not force:
        msg = "já existe (use --force para sobrescrever)"
        log.info("⏭️  %s: %s", dst.name, msg)
        return CreatedItem(path=dst, kind="file", status="skipped", message=msg)

    try:
        # Criar diretório pai se necessário
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Ler conteúdo do template
        content = src.read_text(encoding="utf-8")

        # Aplicar substituições
        for var, value in template_vars.items():
            content = content.replace(var, value)

        # Escrever arquivo processado
        dst.write_text(content, encoding="utf-8")

        log.info("✅ %s (com substituição de variáveis)", dst.name)
        return CreatedItem(path=dst, kind="file", status="created")

    except (OSError, UnicodeDecodeError) as exc:
        msg = f"erro ao copiar: {exc}"
        log.error("❌ %s: %s", dst.name, msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)


def _copy_domain_profile(
    src_root: Path,
    base: Path,
    profile_name: str,
    errors: list[str],
    force: bool = False,
) -> CreatedItem:
    """Copia um perfil de domínio (skill) de scaffold/templates/skills/<perfil>/."""
    src_file = _SKILLS_TEMPLATES / profile_name / "SKILL.md"
    dst_file = base / ".github" / "skills" / profile_name / "SKILL.md"
    result = _copy_file(src_file, dst_file, force=force)
    if result.status == "error":
        errors.append(str(src_file))
    return result


def _copy_file(src: Path, dst: Path, force: bool = False) -> CreatedItem:
    """Copia src → dst com logging. Detecta drift e permite force com backup.

    Integração BUG-16: Usa sistema de merge inteligente quando disponível.

    Args:
        src: Arquivo de origem (upstream template)
        dst: Arquivo de destino (projeto local)
        force: Se True, sobrescreve arquivo existente após backup

    Returns:
        CreatedItem com status:
        - created: arquivo criado ou atualizado
        - merged: arquivo mergeado com sistema de merge inteligente (BUG-16)
        - skipped: arquivo existe e sem drift ou force=False
        - drift: arquivo existe com drift detectado (apenas se force=False)
        - error: erro ao copiar

    Nota: Se dst for um symlink, NUNCA sobrescreve (preserva symlink).
    """
    import hashlib

    if not src.exists():
        msg = f"origem não encontrada: {src}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    # PROTEÇÃO: Nunca sobrescrever symlinks (preservar configuração de shared files)
    if dst.is_symlink():
        log.info("🔗 skipped (symlink): %s → %s", dst.name, dst.resolve())
        return CreatedItem(
            path=dst,
            kind="symlink",
            status="skipped",
            message=f"Preservado symlink → {dst.resolve()}",
        )

    # Ler conteúdo do template
    try:
        template_content = src.read_text(encoding="utf-8")
    except Exception as exc:
        msg = f"Erro ao ler template {src}: {exc}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    # Calcular hash do arquivo upstream
    src_hash = hashlib.sha256(src.read_bytes()).hexdigest()[:8]

    if dst.exists():
        # BUG-16: Tentar merge inteligente primeiro (antes de force)
        # Verificar se há merger disponível para este tipo de arquivo
        merge_result = file_merge.merge_or_skip(
            dst, template_content, interactive=False
        )

        if merge_result.status == "merged" or merge_result.status == "created":
            # Merge bem-sucedido via sistema de merge inteligente
            log.info(
                "🔀 merged via %s", merge_result.message or "intelligent merge system"
            )
            return merge_result

        # Se chegou aqui, não há merger disponível ou merge foi skipped
        # Continuar com lógica antiga de drift detection

        # Calcular hash do arquivo local
        dst_hash = hashlib.sha256(dst.read_bytes()).hexdigest()[:8]

        # Detectar drift (Opção 3)
        if src_hash != dst_hash:
            if not force:
                log.warning(
                    "📊 drift detectado: %s (upstream: %s, local: %s)",
                    dst.name,
                    src_hash,
                    dst_hash,
                )
                return CreatedItem(
                    path=dst,
                    kind="file",
                    status="drift",
                    message=f"Arquivo difere do upstream (upstream: {src_hash}, local: {dst_hash})",
                )
            else:
                # Opção 1: backup antes de sobrescrever
                backup_path = dst.with_suffix(dst.suffix + ".backup")
                shutil.copy2(dst, backup_path)
                log.info("📦 backup: %s → %s", dst.name, backup_path.name)
        else:
            # Arquivo idêntico ao upstream
            log.info("⏭️  skipped (idêntico ao upstream): %s", dst)
            return CreatedItem(path=dst, kind="file", status="skipped")

    # Criar ou sobrescrever arquivo
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(template_content, encoding="utf-8")
        action = "atualizado" if dst.exists() and force else "criado"
        log.info("✅ %s: %s → %s", action, src.name, dst)
        return CreatedItem(path=dst, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao copiar %s: %s", src, exc)
        return CreatedItem(path=dst, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# Constitution — geração do arquivo .specify/memory/constitution.md
# ---------------------------------------------------------------------------


def generate_constitution(config: ProjectConfig) -> CreatedItem:
    """
    Gera .specify/memory/constitution.md no projeto destino.

    Copia o constitution-template.md do template, resolve os placeholders
    padrão e adiciona metadados do projeto no cabeçalho.
    Se o arquivo já existir no destino, salta (idempotente).
    """
    src = _TEMPLATE_ROOT / ".specify" / "templates" / "constitution-template.md"
    dst = config.project_path / ".specify" / "memory" / "constitution.md"

    if dst.exists():
        log.info("⏭️  skipped (já existe): %s", dst)
        return CreatedItem(path=dst, kind="file", status="skipped")

    if not src.exists():
        msg = f"constitution-template.md não encontrado em {src}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    try:
        template_content = src.read_text(encoding="utf-8")

        # Substitui os marcadores de template do SpecKit
        content = template_content.replace("[PROJECT_NAME]", config.project_title)
        content = content.replace("[RATIFICATION_DATE]", config.created_at[:10])
        content = content.replace("[LAST_AMENDED_DATE]", config.created_at[:10])
        content = content.replace("[CONSTITUTION_VERSION]", "1.0.0")

        # Cabeçalho com metadados do scaffold
        header = (
            f"<!-- Gerado por scaffold.py {SPECKIT_SYNC_DATE} | "
            f"Domínio: {config.domain} | Linguagem: {config.language} -->\n"
        )
        content = header + content

        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
        log.info("✅ constitution.md gerado: %s", dst)
        return CreatedItem(path=dst, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao gerar constitution.md: %s", exc)
        return CreatedItem(path=dst, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# MCP env vars required per domain (mirrors vscode._MCP_BY_DOMAIN "env" fields)
# ---------------------------------------------------------------------------

_MCP_ENV_VARS_BY_DOMAIN: dict[str, list[str]] = {
    "programming": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "infrastructure": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "analysis": ["BRAVE_API_KEY"],
}


# ---------------------------------------------------------------------------
# load-mcp.sh — geração dinâmica por domínio
# ---------------------------------------------------------------------------


def generate_load_mcp(config: ProjectConfig) -> CreatedItem:
    """
    Gera scripts/load-mcp.sh com as variáveis de ambiente obrigatórias para o domínio.

    - Verifica .secrets/.env; orienta o usuário se ausente
    - Carrega as variáveis (set -a; source; set +a)
    - Valida variáveis obrigatórias pelo domínio
    - Verifica presença de npx e node
    - Imprime instrução para abrir o VS Code
    - Idempotente — skip se scripts/load-mcp.sh já existe
    """
    dest = config.project_path / "scripts" / "load-mcp.sh"
    if dest.exists():
        return CreatedItem(
            path=dest, kind="file", status="skipped", message="já existe"
        )

    required_vars = _MCP_ENV_VARS_BY_DOMAIN.get(config.domain, [])

    # Bloco de exemplo para .secrets/.env
    example_lines = (
        "\n".join(f"   {var}=your-value-here" for var in required_vars)
        or "   (nenhuma variável requerida para este domínio)"
    )

    # Bloco de validação de variáveis
    validation_lines = (
        "\n".join(
            f'  [[ -z "${{{var}:-}}" ]] && MISSING+=("{var}")' for var in required_vars
        )
        or "  # nenhuma variável requerida para este domínio"
    )

    script = (
        "#!/usr/bin/env bash\n"
        "# load-mcp.sh — Carrega variáveis de ambiente para MCP Servers\n"
        f"# Domínio: {config.domain}\n"
        "# Gerado por scaffold.py — NÃO commitar este script com tokens reais\n"
        "#\n"
        "# Uso:\n"
        "#   bash scripts/load-mcp.sh\n"
        "#   make mcp\n"
        "set -euo pipefail\n"
        "\n"
        'SECRETS_ENV=".secrets/.env"\n'
        "\n"
        'if [[ ! -f "$SECRETS_ENV" ]]; then\n'
        '  echo "⚠️  .secrets/.env não encontrado."\n'
        '  echo "   Crie o arquivo com os tokens necessários:"\n'
        '  echo ""\n'
        '  echo "   # .secrets/.env"\n'
        f'  echo "{example_lines}"\n'
        '  echo ""\n'
        "  exit 1\n"
        "fi\n"
        "\n"
        "# Carrega sem poluir o histórico do shell\n"
        'set -a; source "$SECRETS_ENV"; set +a\n'
        "\n"
        "# Valida variáveis obrigatórias\n"
        "MISSING=()\n" + validation_lines + "\n"
        "\n"
        "if [[ ${#MISSING[@]} -gt 0 ]]; then\n"
        '  echo "❌ Variáveis obrigatórias ausentes em $SECRETS_ENV:"\n'
        "  printf '   %s\\n' \"${MISSING[@]}\"\n"
        "  exit 1\n"
        "fi\n"
        "\n"
        "# Verifica dependências de runtime\n"
        "for cmd in npx node; do\n"
        '  if ! command -v "$cmd" &>/dev/null; then\n'
        '    echo "❌ Dependência ausente: $cmd"\n'
        '    echo "   Instale o Node.js: https://nodejs.org/"\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "\n"
        'echo "✅ Ambiente MCP carregado com sucesso."\n'
        'echo ""\n'
        'echo "   Abra o VS Code com:"\n'
        'echo "   code ."\n'
    )

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(script, encoding="utf-8")
        # Torna executável: rwxr-xr-x (0o755) — script de shell precisa de +x
        os.chmod(dest, 0o755)  # noqa: S103  # nosec B103
        log.info("✅ load-mcp.sh gerado: %s", dest)
        return CreatedItem(path=dest, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao gerar load-mcp.sh: %s", exc)
        return CreatedItem(path=dest, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# Secrets Security Setup (IMP-60)
# ---------------------------------------------------------------------------


def setup_secrets_security(config: ProjectConfig) -> list[CreatedItem]:
    """
    Configura proteção avançada para .secrets/ directory.

    Implementa:
      - chmod 700 em .secrets/ (somente proprietário tem acesso)
      - .secrets/SECURITY.md já foi criado em FILES_TO_CREATE
      - .git-hooks/pre-commit.secrets template já foi criado
      - Valida que .secrets/ está no .gitignore

    Esta função é chamada APÓS create_structure(), garantindo que:
      1. .secrets/ já existe
      2. Arquivos de documentação já foram criados
      3. Aplicamos permissões restritivas

    Retorna lista de ações realizadas (permissões modificadas, validações).

    Ref: IMP-60 — documentado em docs/lembrete.md
    """
    results: list[CreatedItem] = []
    base = config.project_path
    secrets_dir = base / ".secrets"

    # 1. Verificar que .secrets/ existe
    if not secrets_dir.exists():
        msg = ".secrets/ não existe ainda — pulando setup de segurança"
        log.warning("⚠️  %s", msg)
        return results

    # 2. Aplicar chmod 700 (rwx------)
    try:
        current_perms = secrets_dir.stat().st_mode & 0o777
        if current_perms != 0o700:
            secrets_dir.chmod(0o700)
            log.info("🔒 .secrets/ protegido: chmod 700 aplicado")
            results.append(
                CreatedItem(
                    path=secrets_dir,
                    kind="dir",
                    status="secured",
                    message="chmod 700 aplicado",
                )
            )
        else:
            log.info("✅ .secrets/ já tem permissão 700")
            results.append(
                CreatedItem(
                    path=secrets_dir,
                    kind="dir",
                    status="skipped",
                    message="permissões já corretas (700)",
                )
            )
    except OSError as exc:
        log.warning("⚠️  erro ao aplicar chmod 700: %s", exc)
        results.append(
            CreatedItem(
                path=secrets_dir,
                kind="dir",
                status="error",
                message=f"chmod falhou: {exc}",
            )
        )

    # 3. Validar .gitignore contém .secrets/
    gitignore = base / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".secrets/" in content:
            log.info("✅ .gitignore contém .secrets/")
            results.append(
                CreatedItem(
                    path=gitignore,
                    kind="validation",
                    status="ok",
                    message=".secrets/ está ignorado no git",
                )
            )
        else:
            log.warning("⚠️  .secrets/ NÃO está em .gitignore!")
            results.append(
                CreatedItem(
                    path=gitignore,
                    kind="validation",
                    status="warning",
                    message=".secrets/ ausente no .gitignore",
                )
            )

    # 4. Ativar pre-commit hook automaticamente (BUG-#4 fix)
    hook_template = base / ".git-hooks" / "pre-commit.secrets"
    hook_target = base / ".git" / "hooks" / "pre-commit"

    if hook_template.exists():
        try:
            # Verificar se .git/hooks/ existe
            hooks_dir = base / ".git" / "hooks"
            if not hooks_dir.exists():
                log.warning("⚠️  .git/hooks/ não existe — pulando ativação de hook")
                results.append(
                    CreatedItem(
                        path=hook_template,
                        kind="file",
                        status="available",
                        message="hook disponível (sem .git/hooks/ para instalar)",
                    )
                )
            else:
                # Copiar hook template para .git/hooks/pre-commit
                shutil.copy2(hook_template, hook_target)
                hook_target.chmod(0o755)  # rwxr-xr-x

                log.info("✅ Pre-commit hook ativado automaticamente")
                results.append(
                    CreatedItem(
                        path=hook_target,
                        kind="file",
                        status="activated",
                        message="pre-commit hook instalado em .git/hooks/",
                    )
                )
        except Exception as e:
            log.warning("⚠️  Falha ao ativar pre-commit hook: %s", e)
            results.append(
                CreatedItem(
                    path=hook_template,
                    kind="file",
                    status="available",
                    message=f"hook disponível (ativação manual necessária): {e}",
                )
            )

    return results


# ---------------------------------------------------------------------------
# GitHub Security Files (BUG-06)
# ---------------------------------------------------------------------------


def generate_github_security_files(
    config: ProjectConfig, force: bool = False
) -> list[CreatedItem]:
    """
    Gera arquivos de segurança GitHub no projeto.

    Cria:
      - SECURITY.md (política de reporte de vulnerabilidades)
      - .github/CODEOWNERS (ownership de código) — apenas se github_repo configurado
      - .github/dependabot.yml (atualizações automáticas) — apenas se github_repo configurado
      - .github/workflows/security-scan.yml (CodeQL + secret scan) — apenas se github_repo configurado
      - .github/workflows/dependency-review.yml (análise de dependências em PRs) — apenas se github_repo configurado

    Se github_repo não estiver configurado, gerencia apenas SECURITY.md com versão genérica.

    OWNER placeholder é substituído pelo dono do repo GitHub (se disponível).

    Ref: BUG-06 — documentado em docs/lembrete.md
    """
    results: list[CreatedItem] = []
    base = config.project_path

    # Extrair owner do github_repo (ex: https://github.com/user/repo → user)
    owner = "OWNER"
    if config.github_repo:
        parts = config.github_repo.rstrip("/").split("/")
        if len(parts) >= 2:
            owner = f"@{parts[-2]}"

    # Arquivo 1: SECURITY.md (raiz do projeto)
    # Usa template com GitHub se repositório configurado, senão usa versão genérica
    security_md = base / "SECURITY.md"
    if config.github_repo:
        content = _apply_placeholders(_SECURITY_MD_WITH_GITHUB, config)
    else:
        content = _SECURITY_MD_WITHOUT_GITHUB
    results.append(_write_managed_file(security_md, content, force=force))

    # Arquivos 2-5: Apenas criar se houver repositório GitHub configurado
    if not config.github_repo:
        return results

    # Arquivo 2: .github/CODEOWNERS
    codeowners = base / ".github" / "CODEOWNERS"
    content = render(_CODEOWNERS, {"OWNER": owner})
    results.append(_write_managed_file(codeowners, content, force=force))

    # Arquivo 3: .github/dependabot.yml
    dependabot = base / ".github" / "dependabot.yml"
    content = render(_DEPENDABOT_YML, {"OWNER_LOGIN": owner.lstrip("@")})
    results.append(_write_managed_file(dependabot, content, force=force))

    # Arquivo 4: .github/workflows/security-scan.yml
    security_scan = base / ".github" / "workflows" / "security-scan.yml"
    results.append(_write_managed_file(security_scan, _SECURITY_SCAN_YML, force=force))

    # Arquivo 5: .github/workflows/dependency-review.yml
    dependency_review = base / ".github" / "workflows" / "dependency-review.yml"
    results.append(
        _write_managed_file(dependency_review, _DEPENDENCY_REVIEW_YML, force=force)
    )

    return results


def generate_project_creation_summary(config: ProjectConfig) -> CreatedItem:
    """
    Gera docs/PROJECT_CREATION_SUMMARY.md com resumo completo da criação.

    Contém:
      - Informações do projeto (nome, descrição, domínio, linguagem)
      - Estrutura de diretórios criada
      - Profiles aplicados
      - Status do Git (commit, tag, remote)
      - Próximos passos recomendados
      - Comandos úteis (Makefile, Git, Docs)
      - Links para documentação interna
      - Recursos de segurança
      - Agentes e prompts SpecKit disponíveis
      - Convenções do projeto

    Ref: IMP-63 — Feature documentada em docs/lembrete.md
    """
    summary_path = config.project_path / "docs" / "PROJECT_CREATION_SUMMARY.md"

    if summary_path.exists():
        log.info("⏭️  já existe: %s", summary_path.name)
        return CreatedItem(path=summary_path, kind="file", status="skipped")

    # Construir seção de profiles aplicados
    profiles = []
    # Adicionar profile padrão do domínio
    if config.domain in DOMAIN_DEFAULT_PROFILES:
        # DOMAIN_DEFAULT_PROFILES é dict[str, str], não list!
        profiles.append(DOMAIN_DEFAULT_PROFILES[config.domain])
    # Adicionar profiles transversais (aplicados sempre)
    profiles.extend(SPECKIT_TRANSVERSAL_PROFILES)
    # Adicionar profiles extras (se fornecidos)
    # Estado JSON legado pode trazer string em vez de lista
    extra_profiles: list[str] | str = config.extra_profiles
    if extra_profiles:
        if isinstance(extra_profiles, str):
            # Se for string, fazer split por vírgula
            extra = [p.strip() for p in extra_profiles.split(",") if p.strip()]
            profiles.extend(extra)
        elif isinstance(extra_profiles, list):
            profiles.extend(extra_profiles)

    # Remover duplicatas mantendo ordem
    seen = set()
    unique_profiles = []
    for p in profiles:
        if p not in seen:
            seen.add(p)
            unique_profiles.append(p)

    if unique_profiles:
        profiles_section = "**Profiles aplicados:**\n"
        for profile in unique_profiles:
            profiles_section += f"- ✅ `{profile}`\n"
    else:
        profiles_section = "*Nenhum profile específico aplicado.*\n"

    # Seção de remote Git (se configurado)
    git_remote_section = ""
    if config.github_repo:
        git_remote_section = f"\n- Remote: `origin` → {config.github_repo}"

    # Aplicar placeholders
    content = render(
        _apply_placeholders(_PROJECT_CREATION_SUMMARY, config),
        {
            "PROFILES_SECTION": profiles_section,
            "GIT_REMOTE_SECTION": git_remote_section,
        },
    )

    return _write_file(summary_path, content)


def _write_file(path: Path, content: str) -> CreatedItem:
    """Escreve arquivo com conteúdo, criando diretórios necessários."""
    try:
        if path.exists():
            log.info("⏭️  já existe: %s", path.name)
            return CreatedItem(path=path, kind="file", status="skipped")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log.info("✅ criado: %s", path.name)
        return CreatedItem(path=path, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao criar %s: %s", path.name, exc)
        return CreatedItem(path=path, kind="file", status="error", message=str(exc))


def _write_managed_file(path: Path, content: str, force: bool = False) -> CreatedItem:
    """Escreve arquivo gerenciado com detecção de drift e backup opcional."""
    import hashlib

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]

    if path.is_symlink():
        log.info("🔗 skipped (symlink): %s → %s", path.name, path.resolve())
        return CreatedItem(
            path=path,
            kind="symlink",
            status="skipped",
            message=f"Preservado symlink → {path.resolve()}",
        )

    file_exists = path.exists()
    if file_exists:
        try:
            current_content = path.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning("⚠️  erro ao ler %s: %s", path.name, exc)
            return CreatedItem(path=path, kind="file", status="error", message=str(exc))

        current_hash = hashlib.sha256(current_content.encode("utf-8")).hexdigest()[:8]
        if current_hash == content_hash:
            log.info("⏭️  skipped (idêntico ao upstream): %s", path)
            return CreatedItem(path=path, kind="file", status="skipped")

        if not force:
            log.warning(
                "📊 drift detectado: %s (upstream: %s, local: %s)",
                path.name,
                content_hash,
                current_hash,
            )
            return CreatedItem(
                path=path,
                kind="file",
                status="drift",
                message=f"Arquivo difere do upstream (upstream: {content_hash}, local: {current_hash})",
            )

        backup_path = path.with_suffix(path.suffix + ".backup")
        try:
            shutil.copy2(path, backup_path)
            log.info("📦 backup: %s → %s", path.name, backup_path.name)
        except OSError as exc:
            log.warning("⚠️  erro ao criar backup de %s: %s", path.name, exc)
            return CreatedItem(path=path, kind="file", status="error", message=str(exc))

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        action = "atualizado" if file_exists else "criado"
        log.info("✅ %s: %s", action, path)
        return CreatedItem(path=path, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao escrever %s: %s", path.name, exc)
        return CreatedItem(path=path, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# Scaffold state — persiste e recupera configuração do projeto gerado
# ---------------------------------------------------------------------------

_STATE_FILENAME = ".scaffold-state.yaml"


def write_scaffold_state(
    config: ProjectConfig,
    profiles_applied: list[str] | None = None,
) -> CreatedItem:
    """
    Persiste o estado do projeto em <target_dir>/.scaffold-state.yaml.

    Chamado ao final de flow_new_project e de flow_compose_profiles para que
    o fluxo de upgrade saiba quais perfis foram aplicados e com qual config
    o projeto foi criado.

    O arquivo é SEMPRE sobrescrito (não é idempotente como os demais).

    IMP-65 Fase 1: Agora também armazena template_versions para tracking de drift.
    """
    from datetime import datetime

    state_path = config.project_path / _STATE_FILENAME

    # Carrega estado anterior (se existir) para preservar created_at e profiles
    existing_profiles: list[str] = []
    original_created_at: str = config.created_at
    if state_path.exists():
        try:
            import yaml

            with state_path.open(encoding="utf-8") as f:
                old = yaml.safe_load(f) or {}
            existing_profiles = old.get("profiles_applied", [])
            original_created_at = old.get("created_at", config.created_at)
        except Exception as exc:
            # State ilegível: recomeça do zero (comportamento anterior), mas registra
            log.debug("scaffold state anterior ignorado (%s): %s", state_path, exc)

    # Merge: adiciona novos perfis sem duplicar
    merged_profiles = list(existing_profiles)
    for p in profiles_applied or []:
        if p not in merged_profiles:
            merged_profiles.append(p)

    # IMP-65 Fase 1: Scan current template versions
    # BUG-03 FIX: Also collect template bases for merge tracking (IMP-65 Phase 3)
    template_versions = {}
    template_bases = {}
    template_dir = config.project_path / ".specify" / "templates"
    if template_dir.exists():
        try:
            from . import template_version

            templates = template_version.scan_templates(template_dir)
            template_versions = {name: info.version for name, info in templates.items()}

            # Collect base content for three-way merge support
            for name, info in templates.items():
                content = info.path.read_text(encoding="utf-8")
                template_bases[name] = {
                    "version": info.version,
                    "content": content,
                }
        except Exception as exc:
            log.warning("⚠️  Failed to scan template versions: %s", exc)

    state: dict = {
        "scaffold_version": "1.0.0",
        "created_at": original_created_at,
        "updated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": {
            "name": config.project_name,
            "title": config.project_title,
            "description": config.description,
            "domain": config.domain,
            "language": config.language,
            "github_repo": config.github_repo or "",
            "ai_assistant": config.ai_assistant,
        },
        "paths": {
            "target_dir": str(config.target_dir),
            "shared_dir": str(config.shared_dir),
        },
        "profiles_applied": merged_profiles,
        "template_versions": template_versions,  # IMP-65 Fase 1
        "template_bases": template_bases,  # BUG-03 FIX: IMP-65 Phase 3
    }

    try:
        import yaml

        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            yaml.dump(
                state, allow_unicode=True, default_flow_style=False, sort_keys=False
            ),
            encoding="utf-8",
        )
        log.info("✅ scaffold state gravado: %s", state_path)
        return CreatedItem(path=state_path, kind="file", status="created")
    except Exception as exc:
        log.warning("⚠️  erro ao gravar scaffold state: %s", exc)
        return CreatedItem(
            path=state_path, kind="file", status="error", message=str(exc)
        )


def read_scaffold_state(target_dir: Path) -> dict | None:
    """
    Lê <target_dir>/.scaffold-state.yaml e retorna o dict com o estado.
    Retorna None se o arquivo não existe ou está corrompido.
    """
    state_path = target_dir / _STATE_FILENAME
    if not state_path.exists():
        return None
    try:
        import yaml

        with state_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except Exception as exc:
        log.warning("⚠️  erro ao ler scaffold state: %s", exc)
        return None


def config_from_state(
    state: dict, override_target: Path | None = None
) -> ProjectConfig:
    """
    Reconstrói um ProjectConfig a partir do estado salvo.

    Args:
        state:           dict retornado por read_scaffold_state()
        override_target: se fornecido, sobrescreve paths.target_dir do state
                        No modo upgrade, override_target é o próprio projeto.
    """
    from datetime import datetime

    proj = state.get("project", {})
    paths = state.get("paths", {})
    project_name = proj.get("name", "unknown")

    # Correção IMP-47 + BUG-10: detectar se override_target é o próprio projeto
    if override_target:
        # Verificar se .scaffold-state.yaml existe em override_target
        # Se sim, override_target É O PROJETO (upgrade in-place)
        state_file = override_target / ".scaffold-state.yaml"

        if state_file.exists():
            # Upgrade in-place: override_target tem .scaffold-state.yaml
            # target_dir deve ser override_target (sem parent)
            # project_path será = target_dir (sem concatenação)
            target = override_target
        elif override_target.name == project_name:
            # override_target termina com project_name → é o projeto
            target = override_target.parent
        else:
            # Fallback: assume que override_target é o diretório pai
            target = override_target
    else:
        # Modo normal: usa target_dir do state
        target = Path(paths.get("target_dir", "."))

    shared = Path(
        paths.get(
            "shared_dir", str(Path.home() / "Documentos" / "DevOps" / ".copilot-shared")
        )
    )

    return ProjectConfig(
        project_name=project_name,
        project_title=proj.get("title", proj.get("name", "Unknown")),
        description=proj.get("description", ""),
        domain=proj.get("domain", "programming"),
        language=proj.get("language", "python"),
        github_repo=proj.get("github_repo") or None,
        shared_dir=shared,
        target_dir=target,
        created_at=state.get(
            "created_at", datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        ),
        extra_profiles=state.get("profiles_applied", []),
        ai_assistant=proj.get("ai_assistant", "both"),
    )
