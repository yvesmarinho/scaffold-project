"""
Copilot Agent Merger - Intelligent merge for .agent.md files

Merger especializado para arquivos .github/agents/*.agent.md com suporte a:
- YAML frontmatter (version, description, handoffs, tools, etc.)
- Merge aditivo de arrays (handoffs, tools)
- Preservação de customizações (seções não-padrão)
- Atualização de versões (se template > local)
- Merge de seções markdown por heading

Sprint 1 (P0 CRITICAL): Resolve gap de 32 agentes sem merge
Bug fix: 60+ arquivos de automação não recebiam atualizações
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .config import CreatedItem

log = logging.getLogger(__name__)


# =============================================================================
# Types and Data Classes
# =============================================================================


@dataclass
class AgentFrontmatter:
    """Representa o frontmatter YAML de um agent."""

    raw_yaml: str
    parsed: dict[str, Any]
    version: str | None = None
    description: str | None = None
    name: str | None = None
    agent_name: str | None = None
    handoffs: list[dict[str, Any]] = None
    tools: list[str] = None

    def __post_init__(self):
        """Extrai campos comuns do frontmatter."""
        if self.parsed:
            self.version = self.parsed.get("version")
            self.description = self.parsed.get("description")
            self.name = self.parsed.get("name")
            self.agent_name = self.parsed.get("agentName")
            self.handoffs = self.parsed.get("handoffs", [])
            self.tools = self.parsed.get("tools", [])


@dataclass
class AgentContent:
    """Representa conteúdo markdown de um agent (após frontmatter)."""

    sections: dict[str, str]  # heading -> content
    raw_content: str


@dataclass
class MergeDecision:
    """Decisão de merge para um agent."""

    should_merge: bool
    reason: str
    changes: list[str]


# =============================================================================
# CopilotAgentMerger
# =============================================================================


class CopilotAgentMerger:
    """
    Merger inteligente para arquivos .github/agents/*.agent.md

    Estratégia de merge:
    1. **YAML Frontmatter**:
       - version: Se template > local → atualizar
       - description: Atualizar se mudou significativamente
       - handoffs: Merge aditivo (adicionar ausentes)
       - tools: Merge aditivo (adicionar ausentes)

    2. **Markdown Content**:
       - Extrair seções por heading (##, ###)
       - Adicionar novas seções ausentes
       - Atualizar seções padrão se versão mais recente
       - Preservar seções customizadas (não presentes no template)

    3. **Preservação**:
       - Customizações do usuário sempre preservadas
       - Merge é sempre aditivo (nunca remove)
       - Em caso de dúvida, preserva local
    """

    # Seções consideradas "padrão" que podem ser atualizadas do template
    STANDARD_SECTIONS = {
        "Role & Purpose",
        "When to Use This Agent",
        "Core Responsibilities",
        "Tool Preferences",
        "Workflow",
        "Session Start Workflow",
        "Session End Workflow",
        "Output Format",
        "Examples",
    }

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é um arquivo .agent.md na pasta agents."""
        return (
            file_path.suffix == ".md"
            and ".agent" in file_path.name
            and file_path.parent.name == "agents"
            and
            # Deve ter pelo menos .github/agents/file.md
            len(file_path.parts) >= 3
            and ".github" in file_path.parts  # Deve estar dentro de .github/
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do arquivo .agent.md

        Algoritmo:
        1. Parse frontmatter e conteúdo (existente e template)
        2. Decidir se deve fazer merge (compara versões)
        3. Merge frontmatter (version, arrays, etc.)
        4. Merge conteúdo markdown (adicionar seções ausentes)
        5. Gerar arquivo mesclado
        6. Salvar com backup do original
        """
        try:
            # 1. Parse existente
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_fm, existing_md = self._parse_agent_file(existing_content)

            # 2. Parse template
            template_fm, template_md = self._parse_agent_file(template_content)

            # 3. Decisão de merge
            decision = self._should_merge(existing_fm, template_fm, existing_path.name)

            if not decision.should_merge:
                log.info(f"⏭️  Skip: {existing_path.name} ({decision.reason})")
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message=decision.reason,
                )

            # 4. Merge frontmatter
            merged_fm = self._merge_frontmatter(existing_fm, template_fm)

            # 5. Merge conteúdo markdown
            merged_md = self._merge_markdown_content(existing_md, template_md)

            # 6. Gerar arquivo final
            merged_content = self._reconstruct_agent_file(merged_fm, merged_md)

            # 7. Backup e save
            backup_path = existing_path.with_suffix(".md.backup")
            backup_path.write_text(existing_content, encoding="utf-8")
            existing_path.write_text(merged_content, encoding="utf-8")

            changes_msg = "\n".join(f"  - {change}" for change in decision.changes)
            log.info(
                f"✅ Merged: {existing_path.name}\n{changes_msg}\n"
                f"  Backup: {backup_path.name}"
            )

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="merged",
                message=f"Merged with {len(decision.changes)} changes (backup created)",
            )

        except Exception as e:
            log.error(f"❌ Merge failed for {existing_path.name}: {e}")
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"Merge error: {str(e)}",
            )

    # =========================================================================
    # Parsing Methods
    # =========================================================================

    def _parse_agent_file(self, content: str) -> tuple[AgentFrontmatter, AgentContent]:
        """
        Parse arquivo .agent.md em frontmatter YAML e conteúdo markdown.

        Formato esperado:
        ```
        ---
        agentName: example
        version: 1.0.0
        ---

        # Content here
        ```

        Returns:
            Tupla (frontmatter, markdown_content)
        """
        # Regex para extrair frontmatter (entre --- e ---)
        fm_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(fm_pattern, content, re.DOTALL)

        if not match:
            # Sem frontmatter válido - tratar como markdown puro
            return (
                AgentFrontmatter(raw_yaml="", parsed={}),
                self._parse_markdown_sections(content),
            )

        raw_yaml = match.group(1)
        markdown_content = content[match.end() :]

        try:
            parsed_yaml = yaml.safe_load(raw_yaml)
            if not isinstance(parsed_yaml, dict):
                parsed_yaml = {}
        except yaml.YAMLError as e:
            log.warning(f"YAML parse error: {e}, using empty frontmatter")
            parsed_yaml = {}

        frontmatter = AgentFrontmatter(raw_yaml=raw_yaml, parsed=parsed_yaml)
        markdown = self._parse_markdown_sections(markdown_content)

        return frontmatter, markdown

    def _parse_markdown_sections(self, content: str) -> AgentContent:
        """
        Parse conteúdo markdown em seções por heading.

        Extrai seções definidas por ## ou ### headings.

        Returns:
            AgentContent com dict {heading: content}
        """
        sections = {}
        lines = content.splitlines()
        current_heading = None
        current_content = []

        for line in lines:
            # Detecta heading (## ou ###)
            heading_match = re.match(r"^(#{2,3})\s+(.+)$", line)

            if heading_match:
                # Salvar seção anterior
                if current_heading:
                    sections[current_heading] = "\n".join(current_content).strip()

                # Iniciar nova seção
                current_heading = heading_match.group(2).strip()
                current_content = []
            else:
                # Adicionar linha à seção atual
                if current_heading:
                    current_content.append(line)

        # Salvar última seção
        if current_heading:
            sections[current_heading] = "\n".join(current_content).strip()

        return AgentContent(sections=sections, raw_content=content)

    # =========================================================================
    # Decision Logic
    # =========================================================================

    def _should_merge(
        self,
        existing_fm: AgentFrontmatter,
        template_fm: AgentFrontmatter,
        filename: str,
    ) -> MergeDecision:
        """
        Decide se deve fazer merge baseado em versões e mudanças.

        Critérios:
        1. Se template tem version e local não tem → merge (adicionar version)
        2. Se ambos têm version e template > local → merge (update)
        3. Se template tem novas seções → merge (adicionar)
        4. Se template tem novos handoffs/tools → merge (adicionar)
        5. Caso contrário → skip (já atualizado)
        """
        changes = []

        # 1. Comparar versões
        if template_fm.version:
            if not existing_fm.version:
                changes.append(f"Add version field: {template_fm.version}")
            elif self._compare_versions(template_fm.version, existing_fm.version) > 0:
                changes.append(
                    f"Update version: {existing_fm.version} → {template_fm.version}"
                )

        # 2. Detectar novos handoffs
        if template_fm.handoffs:
            existing_handoff_agents = {
                h.get("agent") for h in (existing_fm.handoffs or []) if h.get("agent")
            }
            new_handoffs = [
                h
                for h in template_fm.handoffs
                if h.get("agent") and h.get("agent") not in existing_handoff_agents
            ]
            if new_handoffs:
                changes.append(f"Add {len(new_handoffs)} new handoffs")

        # 3. Detectar novos tools
        if template_fm.tools:
            existing_tools = set(existing_fm.tools or [])
            new_tools = [t for t in template_fm.tools if t not in existing_tools]
            if new_tools:
                changes.append(f"Add {len(new_tools)} new tools")

        # 4. Detectar description change (significativo)
        if template_fm.description and existing_fm.description:
            if (
                template_fm.description != existing_fm.description
                and len(template_fm.description) > len(existing_fm.description) * 1.2
            ):
                changes.append("Update description (significantly enhanced)")

        # Decisão final
        if not changes:
            return MergeDecision(
                should_merge=False, reason="Agent already up-to-date", changes=[]
            )

        return MergeDecision(
            should_merge=True,
            reason=f"Template has updates ({len(changes)} changes)",
            changes=changes,
        )

    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        Compara versões semânticas.

        Returns:
            1 se v1 > v2, -1 se v1 < v2, 0 se iguais
        """
        try:
            parts1 = [int(p) for p in v1.split(".")]
            parts2 = [int(p) for p in v2.split(".")]

            # Pad com zeros
            max_len = max(len(parts1), len(parts2))
            parts1 += [0] * (max_len - len(parts1))
            parts2 += [0] * (max_len - len(parts2))

            for p1, p2 in zip(parts1, parts2, strict=True):
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1

            return 0
        except (ValueError, AttributeError):
            # Se não for semver válido, comparar como strings
            return 1 if v1 > v2 else (-1 if v1 < v2 else 0)

    # =========================================================================
    # Merge Methods
    # =========================================================================

    def _merge_frontmatter(
        self, existing: AgentFrontmatter, template: AgentFrontmatter
    ) -> dict[str, Any]:
        """
        Merge frontmatter YAML com estratégia aditiva.

        Regras:
        - version: preferir template se > existing
        - description: preferir template se significativamente diferente
        - handoffs: merge aditivo (adicionar ausentes)
        - tools: merge aditivo (adicionar ausentes)
        - outros campos: preservar existing, adicionar ausentes do template
        """
        merged = dict(existing.parsed)  # Start with existing

        # Update version if template is newer
        if template.version:
            if (
                not existing.version
                or self._compare_versions(template.version, existing.version) > 0
            ):
                merged["version"] = template.version

        # Update description if significantly different
        if template.description and existing.description:
            if len(template.description) > len(existing.description) * 1.2:
                merged["description"] = template.description
        elif template.description and not existing.description:
            merged["description"] = template.description

        # Merge handoffs (additive)
        if template.handoffs:
            existing_handoffs = existing.handoffs or []
            existing_agents = {
                h.get("agent") for h in existing_handoffs if h.get("agent")
            }

            for handoff in template.handoffs:
                agent = handoff.get("agent")
                if agent and agent not in existing_agents:
                    existing_handoffs.append(handoff)

            if existing_handoffs:
                merged["handoffs"] = existing_handoffs

        # Merge tools (additive)
        if template.tools:
            existing_tools = set(existing.tools or [])
            merged_tools = list(existing_tools)

            for tool in template.tools:
                if tool not in existing_tools:
                    merged_tools.append(tool)

            if merged_tools:
                merged["tools"] = sorted(merged_tools)

        # Add any other new fields from template (non-destructive)
        for key, value in template.parsed.items():
            if key not in merged and key not in [
                "version",
                "description",
                "handoffs",
                "tools",
            ]:
                merged[key] = value

        return merged

    def _merge_markdown_content(
        self, existing: AgentContent, template: AgentContent
    ) -> AgentContent:
        """
        Merge conteúdo markdown preservando customizações.

        Regras:
        - Seções padrão (STANDARD_SECTIONS): atualizar do template se mudou
        - Seções customizadas: preservar sempre
        - Novas seções do template: adicionar ao final
        """
        merged_sections = dict(existing.sections)  # Start with existing

        # Atualizar/adicionar seções do template
        for heading, content in template.sections.items():
            if heading in self.STANDARD_SECTIONS:
                # Seção padrão - atualizar se diferente
                if (
                    heading not in merged_sections
                    or merged_sections[heading] != content
                ):
                    merged_sections[heading] = content
            elif heading not in merged_sections:
                # Nova seção - adicionar
                merged_sections[heading] = content
            # Seção customizada existente - preservar

        return AgentContent(sections=merged_sections, raw_content="")

    def _reconstruct_agent_file(
        self, frontmatter: dict[str, Any], content: AgentContent
    ) -> str:
        """
        Reconstrói arquivo .agent.md a partir de frontmatter e conteúdo.

        Formato de saída:
        ```
        ---
        agentName: example
        version: 1.0.0
        ---

        ## Section 1
        Content here

        ## Section 2
        More content
        ```
        """
        # Gerar YAML frontmatter
        yaml_str = yaml.dump(
            frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False
        )

        # Gerar conteúdo markdown
        sections_str = ""
        for heading, section_content in content.sections.items():
            # Determinar nível de heading (## ou ###)
            level = "###" if heading in ["Tool Preferences", "Examples"] else "##"
            sections_str += f"{level} {heading}\n\n{section_content}\n\n"

        # Combinar
        return f"---\n{yaml_str}---\n\n{sections_str.rstrip()}\n"
