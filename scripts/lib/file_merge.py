"""
File Merge System for Template Scaffold

Sistema unificado de merge inteligente para arquivos críticos do template.
Resolve problema sistêmico onde arquivos pré-existentes eram sempre pulados,
causando perda de proteções de segurança e features do template.

Arquitetura:
- FileMerger Protocol: Interface comum para todos os mergers
- Mergers específicos: GitignoreMerger, MakefileMerger, ReadmeMerger
- Registry: Mapeamento automático arquivo → merger apropriado
- Fallback: Se não há merger disponível, faz skip (comportamento seguro)

Bug fix: BUG-#1.1 (P0 CRITICAL - Sistema de merge ausente)
Implementação: Sprint 1 (Security Critical)
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import CreatedItem
from .copilot_agent_merge import CopilotAgentMerger
from .copilot_prompt_merge import CopilotPromptMerger
from .copilot_rules_merge import CopilotRulesMerger
from .github_workflow_merge import GitHubWorkflowMerger
from .issue_template_merge import IssueTemplateMerger
from .json_merge import JSONMerger, WorkspaceMerger
from .precommit_merge import PreCommitMerger
from .pyproject_merge import PyprojectMerger
from .vscode_config_merge import VSCodeConfigMerger

log = logging.getLogger(__name__)


# =============================================================================
# Protocol e Tipos
# =============================================================================


class FileMerger(Protocol):
    """
    Protocol para mergers de arquivos específicos.

    Cada merger implementa lógica especializada para um tipo de arquivo
    (ex: .gitignore usa append de linhas, Makefile preserva targets customizados).
    """

    def can_merge(self, file_path: Path) -> bool:
        """
        Verifica se este merger pode processar o arquivo dado.

        Args:
            file_path: Caminho do arquivo a ser verificado

        Returns:
            True se o merger pode processar este arquivo
        """
        ...

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge do conteúdo do template com arquivo existente.

        Args:
            existing_path: Caminho do arquivo existente
            template_content: Conteúdo do template a ser mesclado
            interactive: Se True, pode solicitar confirmação do usuário

        Returns:
            CreatedItem com resultado do merge
        """
        ...


@dataclass
class MergeResult:
    """Resultado de uma operação de merge."""

    success: bool
    merged_content: str
    changes_made: list[str]
    conflicts: list[str]


# =============================================================================
# GitignoreMerger - P0 CRITICAL (Segurança)
# =============================================================================


class GitignoreMerger:
    """
    Merger para .gitignore com foco em segurança.

    Estratégia:
    1. Detecta padrões críticos ausentes (.secrets/, *.key, etc.)
    2. Adiciona seção "Enterprise Template Security" no topo
    3. Não duplica linhas já existentes
    4. Preserva comentários e organização do usuário

    Bug fix: BUG-#1 (P0 - .gitignore não atualizado, risco de vazamento)
    """

    # Padrões críticos de segurança que DEVEM estar presentes
    CRITICAL_PATTERNS = [
        ".secrets/",
        "*.key",
        "*.pem",
        ".env",
        ".vault_pass",
        "*.crt",
        "*secret*",
        "*password*",
        "*token*",
    ]

    SECURITY_HEADER = """# === Enterprise Template Security (Auto-Added by Scaffold) ===
# CRITICAL: Never commit credentials, tokens, or keys
# Added: {timestamp}
"""

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é um arquivo .gitignore."""
        return file_path.name == ".gitignore"

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do .gitignore.

        Algoritmo:
        1. Lê conteúdo existente
        2. Detecta padrões críticos ausentes
        3. Adiciona header de segurança + padrões ausentes no topo
        4. Preserva conteúdo original abaixo
        """
        existing_content = existing_path.read_text()
        existing_lines = {
            line.strip()
            for line in existing_content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        }

        # Detectar padrões críticos ausentes
        missing_patterns = [
            pattern
            for pattern in self.CRITICAL_PATTERNS
            if pattern not in existing_lines
        ]

        if not missing_patterns:
            log.info(f"✅ {existing_path.name}: Todos padrões críticos presentes")
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="skipped",
                message="All critical patterns present",
            )

        # Construir seção de segurança
        from datetime import datetime

        security_section = self.SECURITY_HEADER.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        security_section += "\n".join(missing_patterns)
        security_section += "\n\n# === Original Content Below ===\n"

        # Merge: segurança no topo + conteúdo original
        merged_content = security_section + existing_content

        # Escrever resultado
        existing_path.write_text(merged_content)

        log.warning(
            f"🔒 {existing_path.name}: Added {len(missing_patterns)} "
            f"critical security patterns: {', '.join(missing_patterns)}"
        )

        return CreatedItem(
            path=existing_path,
            kind="file",
            status="created",
            message=f"Added {len(missing_patterns)} security patterns",
        )


# =============================================================================
# MakefileMerger - P1 IMPORTANT (Workflow)
# =============================================================================


class MakefileMerger:
    """
    Merger para Makefile preservando targets customizados.

    Estratégia:
    1. Extrai targets do template (help, test, lint, etc.)
    2. Extrai targets do Makefile existente
    3. Adiciona apenas targets ausentes
    4. Preserva targets customizados do usuário
    5. Mantém ordem lógica (help primeiro, depois build/test, depois custom)

    Bug fix: BUG-#1.1 (P0 sistêmico - Makefile não atualizado)
    """

    # Targets essenciais do template
    ESSENTIAL_TARGETS = [
        "help",
        "test",
        "lint",
        "format",
        "clean",
        "install-deps",
    ]

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é um Makefile."""
        return file_path.name == "Makefile"

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do Makefile.

        Algoritmo:
        1. Extrai targets do template usando regex
        2. Extrai targets do Makefile existente
        3. Identifica targets ausentes
        4. Adiciona targets ausentes preservando customizações
        """
        import re

        existing_content = existing_path.read_text()

        # Regex para extrair targets: linhas que começam com palavra: (não tab)
        target_pattern = re.compile(r"^([a-zA-Z0-9_-]+):", re.MULTILINE)

        existing_targets = set(target_pattern.findall(existing_content))
        set(target_pattern.findall(template_content))

        # Targets essenciais ausentes
        missing_essential = [
            target
            for target in self.ESSENTIAL_TARGETS
            if target not in existing_targets
        ]

        if not missing_essential:
            log.info(f"✅ {existing_path.name}: Todos targets essenciais presentes")
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="skipped",
                message="All essential targets present",
            )

        # Extrair definições completas dos targets ausentes do template
        missing_definitions = []
        for target in missing_essential:
            # Encontrar bloco completo do target no template
            pattern = re.compile(
                rf"^({target}:.*?)(?=^\S|\Z)", re.MULTILINE | re.DOTALL
            )
            match = pattern.search(template_content)
            if match:
                missing_definitions.append(match.group(1).rstrip())

        # Construir seção de targets do template
        template_section = "\n# === Enterprise Template Targets (Auto-Added) ===\n"
        template_section += "\n\n".join(missing_definitions)
        template_section += "\n\n# === Original Targets Below ===\n"

        # Merge: targets template + conteúdo original
        merged_content = template_section + existing_content

        # Escrever resultado
        existing_path.write_text(merged_content)

        log.warning(
            f"🔧 {existing_path.name}: Added {len(missing_essential)} "
            f"essential targets: {', '.join(missing_essential)}"
        )

        return CreatedItem(
            path=existing_path,
            kind="file",
            status="created",
            message=f"Added {len(missing_essential)} targets",
        )


# =============================================================================
# ReadmeMerger - P1 IMPORTANT (Documentação)
# =============================================================================


class ReadmeMerger:
    """
    Merger para README.md preservando introdução do usuário.

    Estratégia:
    1. Detecta seções markdown (## ...) no template
    2. Identifica seções ausentes no README existente
    3. Preserva título e introdução do usuário (até primeiro ##)
    4. Adiciona seções template ausentes após introdução
    5. Mantém ordem lógica (intro → status → stack → features)

    Bug fix: BUG-#1.1 (P0 sistêmico - README não atualizado)
    """

    # Seções essenciais do template
    ESSENTIAL_SECTIONS = [
        "Project Status",
        "Stack",
        "Features",
        "Installation",
        "Usage",
    ]

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é um README.md."""
        return file_path.name == "README.md"

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do README.md.

        Algoritmo:
        1. Extrai introdução do README existente (até primeiro ##)
        2. Extrai seções do template
        3. Identifica seções ausentes
        4. Merge: intro preservada + seções template ausentes
        """
        import re

        existing_content = existing_path.read_text()

        # Regex para extrair seções: linhas que começam com ##
        section_pattern = re.compile(r"^## (.+?)$", re.MULTILINE)

        existing_sections = set(section_pattern.findall(existing_content))
        set(section_pattern.findall(template_content))

        # Seções essenciais ausentes
        missing_sections = [
            section
            for section in self.ESSENTIAL_SECTIONS
            if section not in existing_sections
        ]

        if not missing_sections:
            log.info(f"✅ {existing_path.name}: Todas seções essenciais presentes")
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="skipped",
                message="All essential sections present",
            )

        # Extrair introdução do README existente (até primeiro ##)
        intro_match = re.match(
            r"^(.*?)(?=^##|\Z)", existing_content, re.DOTALL | re.MULTILINE
        )
        intro = intro_match.group(1).rstrip() if intro_match else ""

        # Extrair definições completas das seções ausentes do template
        missing_definitions = []
        for section in missing_sections:
            # Encontrar bloco completo da seção no template
            pattern = re.compile(
                rf"^(## {re.escape(section)}.*?)(?=^##|\Z)", re.MULTILINE | re.DOTALL
            )
            match = pattern.search(template_content)
            if match:
                missing_definitions.append(match.group(1).rstrip())

        # Construir README mesclado
        merged_content = intro
        if intro and not intro.endswith("\n\n"):
            merged_content += "\n\n"

        merged_content += "---\n\n"
        merged_content += "<!-- Enterprise Template Sections (Auto-Added) -->\n\n"
        merged_content += "\n\n".join(missing_definitions)
        merged_content += "\n\n---\n\n"
        merged_content += "<!-- Original Sections Below -->\n\n"

        # Adicionar seções originais (se houver)
        original_sections_match = re.search(
            r"^##.*", existing_content, re.MULTILINE | re.DOTALL
        )
        if original_sections_match:
            merged_content += original_sections_match.group(0)

        # Escrever resultado
        existing_path.write_text(merged_content)

        log.warning(
            f"📝 {existing_path.name}: Added {len(missing_sections)} "
            f"essential sections: {', '.join(missing_sections)}"
        )

        return CreatedItem(
            path=existing_path,
            kind="file",
            status="created",
            message=f"Added {len(missing_sections)} sections",
        )


# =============================================================================
# Registry e Função Principal
# =============================================================================

# Registry global de mergers (ordem importa: mais específico primeiro)
_MERGERS: list[FileMerger] = [
    WorkspaceMerger(),  # Sprint W21: BUG-16 (.code-workspace merge)
    JSONMerger(),  # v2.0: User-wins universal para TODOS os JSONs (fix duplicação)
    CopilotAgentMerger(),  # Sprint 1: P0 CRITICAL (32 agents)
    CopilotPromptMerger(),  # Sprint 2: P0 HIGH (26 prompts)
    CopilotRulesMerger(),  # Sprint 2: P0 HIGH (2 rules files)
    GitHubWorkflowMerger(),  # Sprint 3: P1 HIGH (3+ workflows)
    PyprojectMerger(),  # Sprint 3: P1 HIGH (pyproject.toml)
    PreCommitMerger(),  # Sprint 4: P2 MEDIUM (.pre-commit-config.yaml)
    VSCodeConfigMerger(),  # Sprint 4: P2 MEDIUM (launch.json, tasks.json)
    IssueTemplateMerger(),  # Sprint 4: P2 MEDIUM (.github/ISSUE_TEMPLATE/*)
    GitignoreMerger(),
    MakefileMerger(),
    ReadmeMerger(),
]


def merge_or_skip(
    file_path: Path, template_content: str, interactive: bool = True
) -> CreatedItem:
    """
    Tenta fazer merge inteligente; se não há merger disponível, faz skip.

    Esta é a função principal usada por create_structure() para substituir
    a lógica antiga de skip incondicional (linhas 1590-1596 em project.py).

    Args:
        file_path: Caminho do arquivo existente
        template_content: Conteúdo do template
        interactive: Se True, pode solicitar confirmação do usuário

    Returns:
        CreatedItem com resultado (status="created" para merge, "skipped" se não aplicável)

    Exemplos:
        >>> # .gitignore existente → merge automático
        >>> result = merge_or_skip(Path(".gitignore"), template_gitignore)
        >>> assert result.status == "created"

        >>> # Arquivo sem merger → skip seguro
        >>> result = merge_or_skip(Path("custom.txt"), template_content)
        >>> assert result.status == "skipped"
    """
    # Tentar encontrar merger apropriado
    for merger in _MERGERS:
        if merger.can_merge(file_path):
            log.debug(f"🔀 Merge: {file_path.name} via {merger.__class__.__name__}")
            return merger.merge(file_path, template_content, interactive)

    # Sem merger disponível → skip (comportamento seguro)
    log.info(f"⏭️  Skip: {file_path.name} (no merger available)")
    return CreatedItem(
        path=file_path,
        kind="file",
        status="skipped",
        message="File exists, no merger available",
    )


def register_merger(merger: FileMerger) -> None:
    """
    Registra um merger customizado.

    Útil para extensões do template que precisam de merge especializado
    (ex: docker-compose.yml, package.json, etc.)

    Args:
        merger: Instância do merger a ser registrado

    Exemplo:
        >>> class DockerComposeMerger:
        ...     def can_merge(self, file_path: Path) -> bool:
        ...         return file_path.name == "docker-compose.yml"
        ...     def merge(self, existing_path, template_content, interactive=True):
        ...         # ... lógica de merge YAML ...
        ...         pass
        >>>
        >>> register_merger(DockerComposeMerger())
    """
    _MERGERS.insert(0, merger)  # Adiciona no início (prioridade)
    log.info(f"✅ Merger registrado: {merger.__class__.__name__}")


def get_registered_mergers() -> list[str]:
    """
    Retorna lista de mergers registrados (útil para debug/testes).

    Returns:
        Lista de nomes de classes dos mergers registrados
    """
    return [merger.__class__.__name__ for merger in _MERGERS]
