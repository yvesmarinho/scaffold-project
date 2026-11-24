"""
Copilot Rules Merger - Intelligent merge for .copilot-rules*.md files

Merger especializado para arquivos .copilot-rules*.md com suporte a:
- Parse de seções de regras (P0, P1, P2)
- Merge aditivo de regras críticas
- Preservação de regras customizadas do projeto
- Detecção de novas melhores práticas

Sprint 2 (P0 HIGH): Resolve gap de 2 arquivos copilot-rules sem merge
Bug fix: Melhores práticas não disseminadas entre projetos
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .config import CreatedItem

log = logging.getLogger(__name__)


# =============================================================================
# Types and Data Classes
# =============================================================================


@dataclass
class RuleSection:
    """Representa uma seção de regras."""

    heading: str
    content: str
    priority: str  # P0, P1, P2, etc.


@dataclass
class RulesContent:
    """Representa conteúdo de arquivo .copilot-rules.md."""

    header: str  # Cabeçalho do arquivo
    sections: dict[str, RuleSection]  # heading -> RuleSection
    raw_content: str


@dataclass
class RulesMergeDecision:
    """Decisão de merge para copilot-rules."""

    should_merge: bool
    reason: str
    changes: list[str]


# =============================================================================
# CopilotRulesMerger
# =============================================================================


class CopilotRulesMerger:
    """
    Merger inteligente para arquivos .copilot-rules*.md

    Estratégia de merge:
    1. **Header/Metadata**:
       - Preservar título e metadata do arquivo existente
       - Atualizar "Última atualização" se regras mudaram

    2. **Regras P0 (CRÍTICO)**:
       - Sempre adicionar novas regras P0 do template
       - Nunca remover regras P0 existentes
       - Atualizar se texto mudou significativamente

    3. **Regras P1/P2**:
       - Adicionar novas regras ausentes
       - Preservar regras customizadas
       - Atualizar se versão mais recente

    4. **Preservação**:
       - Regras específicas do projeto sempre preservadas
       - Merge é sempre aditivo (nunca remove)
       - Em caso de dúvida, preserva local
    """

    # Padrões de prioridade reconhecidos
    PRIORITY_PATTERNS = {
        "P0": r"P0\s*[—-]\s*CRÍTICO",
        "P1": r"P1\s*(?:[—-]|[\)\]])",  # P1 seguido de travessão ou ) ou ]
        "P2": r"P2\s*(?:[—-]|[\)\]])",  # P2 seguido de travessão ou ) ou ]
    }

    # Seções críticas que devem ser sempre verificadas
    CRITICAL_SECTIONS = {
        "Ferramentas de Arquivo",
        "Ferramentas Nativas VS Code",
        "Operações de Arquivo",
        "Git",
        "Segurança",
    }

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é um arquivo .copilot-rules*.md."""
        return (
            file_path.suffix == ".md"
            and ".copilot-rules" in file_path.name
            and (
                file_path.name == ".copilot-rules.md"
                or file_path.name.startswith(".copilot-rules-")
            )
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do arquivo .copilot-rules*.md

        Algoritmo:
        1. Parse conteúdo (existente e template)
        2. Identificar seções por prioridade (P0, P1, P2)
        3. Decidir se deve fazer merge
        4. Merge aditivo de regras (P0 primeiro)
        5. Gerar arquivo mesclado
        6. Salvar com backup do original
        """
        try:
            # 1. Parse existente
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_rules = self._parse_rules_file(existing_content)

            # 2. Parse template
            template_rules = self._parse_rules_file(template_content)

            # 3. Decisão de merge
            decision = self._should_merge(
                existing_rules, template_rules, existing_path.name
            )

            if not decision.should_merge:
                log.info("⏭️  Skip: %s (%s)", existing_path.name, decision.reason)
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message=decision.reason,
                )

            # 4. Merge conteúdo
            merged_rules = self._merge_rules_content(existing_rules, template_rules)

            # 5. Gerar arquivo final
            merged_content = self._reconstruct_rules_file(merged_rules)

            # 6. Backup e save
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

    def _parse_rules_file(self, content: str) -> RulesContent:
        """
        Parse arquivo .copilot-rules.md em seções organizadas.

        Formato esperado:
        ```
        # GitHub Copilot — Regras Comportamentais

        **Status:** ATIVO

        ## 1. Seção P0 — CRÍTICO

        Content...

        ## 2. Seção P1

        More content...
        ```

        Returns:
            RulesContent com header e seções organizadas
        """
        lines = content.splitlines()
        header = []
        sections = {}
        current_heading = None
        current_content = []
        current_priority = None

        # Extrair header (até primeira seção ##)
        in_header = True

        for line in lines:
            # Detecta seção principal (## apenas, ignorar ###)
            heading_match = re.match(r"^(#{2})\s+(.+)$", line)

            if heading_match:
                in_header = False

                # Salvar seção anterior
                if current_heading:
                    section = RuleSection(
                        heading=current_heading,
                        content="\n".join(current_content).strip(),
                        priority=current_priority or "P2",
                    )
                    sections[current_heading] = section

                # Iniciar nova seção
                current_heading = heading_match.group(2).strip()
                current_content = []

                # Detectar prioridade no heading
                current_priority = self._detect_priority(current_heading)
            else:
                if in_header:
                    header.append(line)
                elif current_heading:
                    current_content.append(line)

        # Salvar última seção
        if current_heading:
            section = RuleSection(
                heading=current_heading,
                content="\n".join(current_content).strip(),
                priority=current_priority or "P2",
            )
            sections[current_heading] = section

        return RulesContent(
            header="\n".join(header).strip(), sections=sections, raw_content=content
        )

    def _detect_priority(self, heading: str) -> str:
        """
        Detecta prioridade (P0, P1, P2) no heading.

        Exemplos:
        - "1. Ferramentas de Arquivo (P0 — CRÍTICO)" -> P0
        - "2. Git (P1)" -> P1
        - "3. Documentação" -> P2 (default)
        """
        for priority, pattern in self.PRIORITY_PATTERNS.items():
            if re.search(pattern, heading, re.IGNORECASE):
                return priority

        # Default: P2 (baixa prioridade)
        return "P2"

    # =========================================================================
    # Decision Logic
    # =========================================================================

    def _should_merge(
        self, existing_rules: RulesContent, template_rules: RulesContent, filename: str
    ) -> RulesMergeDecision:
        """
        Decide se deve fazer merge baseado em novas regras.

        Critérios:
        1. Se template tem novas seções P0 → merge (CRITICAL)
        2. Se template tem novas seções P1 → merge (importante)
        3. Se seções críticas foram atualizadas → merge
        4. Caso contrário → skip
        """
        changes = []

        # 1. Detectar novas seções P0 (CRITICAL)
        existing_p0 = {
            h for h, s in existing_rules.sections.items() if s.priority == "P0"
        }
        template_p0 = {
            h for h, s in template_rules.sections.items() if s.priority == "P0"
        }
        new_p0 = template_p0 - existing_p0

        if new_p0:
            changes.append(f"Add {len(new_p0)} new P0 CRITICAL rules")

        # 2. Detectar novas seções P1
        existing_p1 = {
            h for h, s in existing_rules.sections.items() if s.priority == "P1"
        }
        template_p1 = {
            h for h, s in template_rules.sections.items() if s.priority == "P1"
        }
        new_p1 = template_p1 - existing_p1

        if new_p1:
            changes.append(f"Add {len(new_p1)} new P1 rules")

        # 3. Detectar atualizações em seções críticas
        critical_updates = 0
        for section_name in self.CRITICAL_SECTIONS:
            # Buscar seção que contenha o nome crítico
            existing_section = None
            template_section = None

            for h, s in existing_rules.sections.items():
                if section_name in h:
                    existing_section = s
                    break

            for h, s in template_rules.sections.items():
                if section_name in h:
                    template_section = s
                    break

            if existing_section and template_section:
                # Comparar conteúdo
                if len(template_section.content) != len(existing_section.content):
                    diff_pct = abs(
                        len(template_section.content) - len(existing_section.content)
                    ) / max(len(template_section.content), 1)
                    if diff_pct > 0.1:  # Mudança > 10%
                        critical_updates += 1

        if critical_updates > 0:
            changes.append(f"Update {critical_updates} critical sections")

        # Decisão final
        if not changes:
            return RulesMergeDecision(
                should_merge=False, reason="Rules already up-to-date", changes=[]
            )

        return RulesMergeDecision(
            should_merge=True,
            reason=f"Template has updates ({len(changes)} changes)",
            changes=changes,
        )

    # =========================================================================
    # Merge Methods
    # =========================================================================

    def _merge_rules_content(
        self, existing: RulesContent, template: RulesContent
    ) -> RulesContent:
        """
        Merge conteúdo de regras com estratégia aditiva por prioridade.

        Regras:
        1. Header: preservar existing (metadata do projeto)
        2. P0 sections: adicionar todas ausentes, atualizar existentes
        3. P1 sections: adicionar ausentes
        4. P2 sections: preservar existing (customizações)
        """
        merged_sections = dict(existing.sections)  # Start with existing

        # Processar seções do template por prioridade
        priorities_order = ["P0", "P1", "P2"]

        for priority in priorities_order:
            template_sections_p = {
                h: s for h, s in template.sections.items() if s.priority == priority
            }

            for heading, section in template_sections_p.items():
                if priority == "P0":
                    # P0: sempre adicionar/atualizar (CRITICAL)
                    merged_sections[heading] = section
                elif priority == "P1":
                    # P1: adicionar se ausente
                    if heading not in merged_sections:
                        merged_sections[heading] = section
                else:
                    # P2: preservar existing (customizações)
                    if heading not in merged_sections:
                        merged_sections[heading] = section

        return RulesContent(
            header=existing.header,  # Preservar header do projeto
            sections=merged_sections,
            raw_content="",
        )

    def _reconstruct_rules_file(self, rules: RulesContent) -> str:
        """
        Reconstrói arquivo .copilot-rules.md a partir das seções.

        Formato de saída:
        ```
        # GitHub Copilot — Regras Comportamentais

        **Status:** ATIVO

        ## 1. Seção P0 — CRÍTICO

        Content...

        ## 2. Seção P1

        More content...
        ```
        """
        # Header
        result = rules.header + "\n\n---\n\n"

        # Ordenar seções por prioridade: P0 primeiro, depois P1, depois P2
        sorted_sections = sorted(
            rules.sections.items(),
            key=lambda x: (
                0 if x[1].priority == "P0" else 1 if x[1].priority == "P1" else 2,
                x[0],  # Alfabético dentro da mesma prioridade
            ),
        )

        # Gerar seções
        for heading, section in sorted_sections:
            result += f"## {heading}\n\n{section.content}\n\n---\n\n"

        return result.rstrip() + "\n"
