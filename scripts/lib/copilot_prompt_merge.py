"""
Copilot Prompt Merger - Intelligent merge for .prompt.md files

Merger especializado para arquivos .github/prompts/*.prompt.md com suporte a:
- YAML frontmatter (mode, description, agent, etc.)
- Merge de seções markdown
- Preservação de exemplos customizados
- Atualização de instruções padrão

Sprint 2 (P0 HIGH): Resolve gap de 26 prompts sem merge
Bug fix: Prompt engineering improvements não propagados
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
class PromptFrontmatter:
    """Representa o frontmatter YAML de um prompt."""

    raw_yaml: str
    parsed: dict[str, Any]
    mode: str | None = None
    description: str | None = None
    agent: str | None = None

    def __post_init__(self) -> None:
        """Extrai campos comuns do frontmatter."""
        if self.parsed:
            self.mode = self.parsed.get("mode")
            self.description = self.parsed.get("description")
            self.agent = self.parsed.get("agent")


@dataclass
class PromptContent:
    """Representa conteúdo markdown de um prompt (após frontmatter)."""

    sections: dict[str, str]  # heading -> content
    raw_content: str


@dataclass
class PromptMergeDecision:
    """Decisão de merge para um prompt."""

    should_merge: bool
    reason: str
    changes: list[str]


# =============================================================================
# CopilotPromptMerger
# =============================================================================


class CopilotPromptMerger:
    """
    Merger inteligente para arquivos .github/prompts/*.prompt.md

    Estratégia de merge:
    1. **YAML Frontmatter**:
       - mode: Atualizar se mudou
       - description: Atualizar se significativamente diferente
       - agent: Preservar (geralmente é referência)

    2. **Markdown Content**:
       - Extrair seções por heading (##, ###)
       - Atualizar seções de instruções
       - Preservar seções de exemplos customizados
       - Adicionar novas seções ausentes

    3. **Preservação**:
       - Exemplos customizados sempre preservados
       - Merge é sempre aditivo (nunca remove)
       - Em caso de dúvida, preserva local
    """

    # Seções consideradas "instruções padrão" que podem ser atualizadas
    INSTRUCTION_SECTIONS = {
        "Execução do Ritual",
        "Passo",  # Qualquer passo numerado
        "Pre-Execution Checks",
        "Outline",
        "User Input",
        "Instructions",
        "Workflow",
        "Expected Output",
        "Guidelines",
    }

    # Seções consideradas "exemplos/custom" que devem ser preservadas
    CUSTOM_SECTIONS = {
        "Examples",
        "Custom",
        "Project-Specific",
        "Notes",
    }

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é um arquivo .prompt.md na pasta prompts."""
        return (
            file_path.suffix == ".md"
            and ".prompt" in file_path.name
            and file_path.parent.name == "prompts"
            and len(file_path.parts) >= 3
            and ".github" in file_path.parts
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do arquivo .prompt.md

        Algoritmo:
        1. Parse frontmatter e conteúdo (existente e template)
        2. Decidir se deve fazer merge (compara conteúdo)
        3. Merge frontmatter (fields, arrays, etc.)
        4. Merge conteúdo markdown (atualizar instruções, preservar exemplos)
        5. Gerar arquivo mesclado
        6. Salvar com backup do original
        """
        try:
            # 1. Parse existente
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_fm, existing_md = self._parse_prompt_file(existing_content)

            # 2. Parse template
            template_fm, template_md = self._parse_prompt_file(template_content)

            # 3. Decisão de merge
            decision = self._should_merge(
                existing_fm, template_fm, existing_md, template_md, existing_path.name
            )

            if not decision.should_merge:
                log.info("⏭️  Skip: %s (%s)", existing_path.name, decision.reason)
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
            merged_content = self._reconstruct_prompt_file(merged_fm, merged_md)

            # 7. Backup e save
            backup_path = existing_path.with_suffix(".md.backup")
            backup_path.write_text(existing_content, encoding="utf-8")
            existing_path.write_text(merged_content, encoding="utf-8")

            changes_msg = "\n".join(f"  - {change}" for change in decision.changes)
            log.info(
                "✅ Merged: %s\n%s\n  Backup: %s",
                existing_path.name,
                changes_msg,
                backup_path.name,
            )

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="merged",
                message=f"Merged with {len(decision.changes)} changes (backup created)",
            )

        except Exception as e:
            log.error("❌ Merge failed for %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"Merge error: {str(e)}",
            )

    # =========================================================================
    # Parsing Methods
    # =========================================================================

    def _parse_prompt_file(
        self, content: str
    ) -> tuple[PromptFrontmatter, PromptContent]:
        """
        Parse arquivo .prompt.md em frontmatter YAML e conteúdo markdown.

        Formato esperado:
        ```
        ---
        mode: agent
        description: example
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
                PromptFrontmatter(raw_yaml="", parsed={}),
                self._parse_markdown_sections(content),
            )

        raw_yaml = match.group(1)
        markdown_content = content[match.end() :]

        try:
            parsed_yaml = yaml.safe_load(raw_yaml)
            if not isinstance(parsed_yaml, dict):
                parsed_yaml = {}
        except yaml.YAMLError as e:
            log.warning("YAML parse error: %s, using empty frontmatter", e)
            parsed_yaml = {}

        frontmatter = PromptFrontmatter(raw_yaml=raw_yaml, parsed=parsed_yaml)
        markdown = self._parse_markdown_sections(markdown_content)

        return frontmatter, markdown

    def _parse_markdown_sections(self, content: str) -> PromptContent:
        """
        Parse conteúdo markdown em seções por heading.

        Extrai seções definidas por ## ou ### headings.

        Returns:
            PromptContent com dict {heading: content}
        """
        sections = {}
        lines = content.splitlines()
        current_heading = None
        current_content: list[str] = []

        for line in lines:
            # Detecta heading (## ou ###)
            heading_match = re.match(r"^(#{1,3})\s+(.+)$", line)

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

        return PromptContent(sections=sections, raw_content=content)

    # =========================================================================
    # Decision Logic
    # =========================================================================

    def _should_merge(
        self,
        existing_fm: PromptFrontmatter,
        template_fm: PromptFrontmatter,
        existing_md: PromptContent,
        template_md: PromptContent,
        filename: str,
    ) -> PromptMergeDecision:
        """
        Decide se deve fazer merge baseado em mudanças de conteúdo.

        Critérios:
        1. Se template tem description diferente → merge
        2. Se template tem novas seções → merge
        3. Se template tem seções de instruções atualizadas → merge
        4. Caso contrário → skip (já atualizado)
        """
        changes = []

        # 1. Comparar description
        if template_fm.description and existing_fm.description:
            if template_fm.description != existing_fm.description:
                if len(template_fm.description) > len(existing_fm.description) * 0.8:
                    changes.append("Update description (enhanced)")

        # 2. Detectar novas seções
        existing_sections = set(existing_md.sections.keys())
        template_sections = set(template_md.sections.keys())
        new_sections = template_sections - existing_sections

        if new_sections:
            changes.append(f"Add {len(new_sections)} new sections")

        # 3. Detectar mudanças em seções de instruções
        instruction_updates = 0
        for section in template_md.sections:
            if section in existing_md.sections:
                # Verificar se é seção de instrução
                is_instruction = any(
                    pattern in section for pattern in self.INSTRUCTION_SECTIONS
                )
                if is_instruction:
                    template_text = template_md.sections[section]
                    existing_text = existing_md.sections[section]
                    # Se diferente em mais de 10%, considerar atualização
                    if len(template_text) != len(existing_text):
                        diff_pct = abs(len(template_text) - len(existing_text)) / max(
                            len(template_text), 1
                        )
                        if diff_pct > 0.1:
                            instruction_updates += 1

        if instruction_updates > 0:
            changes.append(f"Update {instruction_updates} instruction sections")

        # Decisão final
        if not changes:
            return PromptMergeDecision(
                should_merge=False, reason="Prompt already up-to-date", changes=[]
            )

        return PromptMergeDecision(
            should_merge=True,
            reason=f"Template has updates ({len(changes)} changes)",
            changes=changes,
        )

    # =========================================================================
    # Merge Methods
    # =========================================================================

    def _merge_frontmatter(
        self, existing: PromptFrontmatter, template: PromptFrontmatter
    ) -> dict[str, Any]:
        """
        Merge frontmatter YAML com estratégia de atualização.

        Regras:
        - mode: preferir template se diferente
        - description: preferir template se significativamente diferente
        - agent: preservar existing (geralmente referência específica)
        - outros campos: adicionar ausentes do template
        """
        merged = dict(existing.parsed)  # Start with existing

        # Update mode if template has different value
        if template.mode and template.mode != existing.mode:
            merged["mode"] = template.mode

        # Update description if significantly different
        if template.description and existing.description:
            if len(template.description) > len(existing.description) * 0.8:
                merged["description"] = template.description
        elif template.description and not existing.description:
            merged["description"] = template.description

        # Preserve agent (usually specific reference)
        # But add if missing
        if template.agent and not existing.agent:
            merged["agent"] = template.agent

        # Add any other new fields from template
        for key, value in template.parsed.items():
            if key not in merged and key not in ["mode", "description", "agent"]:
                merged[key] = value

        return merged

    def _merge_markdown_content(
        self, existing: PromptContent, template: PromptContent
    ) -> PromptContent:
        """
        Merge conteúdo markdown preservando exemplos customizados.

        Regras:
        - Seções de instrução: atualizar do template
        - Seções de exemplos/custom: preservar sempre
        - Novas seções: adicionar ao final
        """
        merged_sections = dict(existing.sections)  # Start with existing

        # Atualizar/adicionar seções do template
        for heading, content in template.sections.items():
            # Verificar se é seção de instrução
            is_instruction = any(
                pattern in heading for pattern in self.INSTRUCTION_SECTIONS
            )
            # Verificar se é seção custom
            is_custom = any(pattern in heading for pattern in self.CUSTOM_SECTIONS)

            if is_instruction and not is_custom:
                # Seção de instrução - atualizar
                merged_sections[heading] = content
            elif heading not in merged_sections:
                # Nova seção - adicionar
                merged_sections[heading] = content
            # Seção custom existente - preservar (não faz nada)

        return PromptContent(sections=merged_sections, raw_content="")

    def _reconstruct_prompt_file(
        self, frontmatter: dict[str, Any], content: PromptContent
    ) -> str:
        """
        Reconstrói arquivo .prompt.md a partir de frontmatter e conteúdo.

        Formato de saída:
        ```
        ---
        mode: agent
        description: example
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
            # Determinar nível de heading baseado no conteúdo
            if "Passo" in heading or "▶️" in heading:
                level = "###"
            else:
                level = "##"

            sections_str += f"{level} {heading}\n\n{section_content}\n\n"

        # Combinar
        return f"---\n{yaml_str}---\n\n{sections_str.rstrip()}\n"
