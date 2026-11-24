"""
Issue Template Merger - Intelligent merge for .github/ISSUE_TEMPLATE/*

Merger especializado para templates de issues do GitHub com suporte a:
- Parse frontmatter YAML
- Merge de metadata (name, about, labels)
- Preservação de templates customizados
- Atualização de estrutura padrão

Sprint 4 (P2 MEDIUM): Expansão do merge system para 90% coverage
Feature: Issue templates não propagados em upgrades
"""

import logging
import re
from pathlib import Path
from typing import Any

import yaml

from .config import CreatedItem

log = logging.getLogger(__name__)


# =============================================================================
# IssueTemplateMerger
# =============================================================================


class IssueTemplateMerger:
    """
    Merger inteligente para .github/ISSUE_TEMPLATE/*.md e config.yml

    Estratégia de merge:
    1. **Templates Markdown (.md)**:
       - Parse frontmatter YAML
       - Merge metadata (preservar customizações)
       - Corpo: se customizado >50%, preservar; senão atualizar

    2. **Config YAML (config.yml)**:
       - Merge como YAML simples
       - Adicionar novos campos
       - Preservar customizações

    3. **Preservação**:
       - Templates customizados sempre preservados
       - Merge de frontmatter (user wins)
       - Corpo markdown comparado por similaridade
    """

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é arquivo em .github/ISSUE_TEMPLATE/."""
        return (
            ".github" in file_path.parts
            and "ISSUE_TEMPLATE" in file_path.parts
            and file_path.suffix in [".md", ".yml", ".yaml"]
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do template.

        Algoritmo:
        1. Detectar tipo (markdown com frontmatter ou YAML puro)
        2. Parse conteúdo
        3. Merge metadata/frontmatter
        4. Merge corpo (se aplicável)
        5. Gerar conteúdo mesclado
        6. Salvar com backup
        """
        try:
            existing_content = existing_path.read_text(encoding="utf-8")

            if existing_path.suffix in [".yml", ".yaml"]:
                # Config YAML puro
                return self._merge_yaml(
                    existing_path, existing_content, template_content
                )
            else:
                # Markdown com frontmatter
                return self._merge_markdown(
                    existing_path, existing_content, template_content
                )

        except Exception as e:
            log.error("❌ Erro ao mergear %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"Merge error: {e}",
            )

    def _merge_yaml(
        self, existing_path: Path, existing_content: str, template_content: str
    ) -> CreatedItem:
        """Merge de arquivo YAML puro (config.yml)."""
        try:
            existing_data = yaml.safe_load(existing_content)
            template_data = yaml.safe_load(template_content)

            # Deep merge (user wins)
            merged_data = self._deep_merge(template_data, existing_data)

            # Detectar mudanças
            if existing_data == merged_data:
                log.info("⏭️  Skip: %s (sem mudanças)", existing_path.name)
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message="Nenhuma mudança necessária",
                )

            # Backup
            backup_path = existing_path.with_suffix(existing_path.suffix + ".backup")
            existing_path.rename(backup_path)
            log.info("📦 Backup: %s", backup_path.name)

            # Escrever
            merged_yaml = yaml.dump(
                merged_data,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
            existing_path.write_text(merged_yaml, encoding="utf-8")

            log.info("🔀 Merged %s (YAML)", existing_path.name)

            return CreatedItem(
                path=existing_path, kind="file", status="merged", message="YAML merged"
            )

        except yaml.YAMLError as e:
            log.error("❌ YAML error em %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"YAML error: {e}",
            )

    def _merge_markdown(
        self, existing_path: Path, existing_content: str, template_content: str
    ) -> CreatedItem:
        """Merge de markdown com frontmatter."""
        # Parse frontmatter e corpo
        existing_fm, existing_body = self._parse_frontmatter(existing_content)
        template_fm, template_body = self._parse_frontmatter(template_content)

        # Merge frontmatter (user wins)
        merged_fm = (
            self._deep_merge(template_fm, existing_fm) if existing_fm else template_fm
        )

        # Decidir sobre corpo: se customizado significativamente, preservar
        similarity = self._calculate_similarity(existing_body, template_body)

        if similarity > 0.7:
            # Muito similar ao template, usar versão atualizada
            merged_body = template_body
            body_action = "updated"
        else:
            # Customizado, preservar
            merged_body = existing_body
            body_action = "preserved"

        # Detectar mudanças
        if existing_fm == merged_fm and body_action == "preserved":
            log.info("⏭️  Skip: %s (sem mudanças)", existing_path.name)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="skipped",
                message="Nenhuma mudança necessária",
            )

        # Backup
        backup_path = existing_path.with_suffix(existing_path.suffix + ".backup")
        existing_path.rename(backup_path)
        log.info("📦 Backup: %s", backup_path.name)

        # Gerar conteúdo mesclado
        merged_content = self._format_markdown(merged_fm, merged_body)
        existing_path.write_text(merged_content, encoding="utf-8")

        log.info(
            "🔀 Merged %s (frontmatter merged, body %s)",
            existing_path.name,
            body_action,
        )

        return CreatedItem(
            path=existing_path,
            kind="file",
            status="merged",
            message=f"Merged (body {body_action})",
        )

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, Any] | None, str]:
        """
        Parse frontmatter YAML e corpo markdown.

        Retorna: (frontmatter_dict, body_content)
        """
        # Regex para frontmatter: ---\n...\n---
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)

        if match:
            frontmatter_str = match.group(1)
            body = match.group(2)
            try:
                frontmatter = yaml.safe_load(frontmatter_str)
                return frontmatter, body
            except yaml.YAMLError:
                # Frontmatter inválido, tratar como corpo
                return None, content
        else:
            # Sem frontmatter
            return None, content

    def _format_markdown(self, frontmatter: dict[str, Any] | None, body: str) -> str:
        """Formata markdown com frontmatter."""
        if not frontmatter:
            return body

        fm_yaml = yaml.dump(
            frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False
        ).strip()

        return f"---\n{fm_yaml}\n---\n{body}"

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similaridade simples entre dois textos.

        Retorna: valor entre 0.0 (totalmente diferente) e 1.0 (idêntico)
        """
        # Normalizar: lowercase, remover espaços extras
        t1 = " ".join(text1.lower().split())
        t2 = " ".join(text2.lower().split())

        if t1 == t2:
            return 1.0

        # Similaridade por palavras em comum
        words1 = set(t1.split())
        words2 = set(t2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Deep merge de dicts (user wins strategy).
        """
        import copy

        result = copy.deepcopy(base)

        for key, value in override.items():
            if key not in result:
                result[key] = copy.deepcopy(value)
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._deep_merge(result[key], value)
            elif isinstance(value, list) and isinstance(result[key], list):
                # União de listas, tratando dicts internos
                merged_list = result[key][:]
                for item in value:
                    if item not in merged_list:
                        merged_list.append(copy.deepcopy(item))
                result[key] = merged_list
            else:
                # User wins
                result[key] = copy.deepcopy(value)

        return result
