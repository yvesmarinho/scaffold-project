"""
VS Code Config Merger - Intelligent merge for .vscode/launch.json and tasks.json

Merger especializado para arquivos de configuração do VS Code com suporte a:
- Parse JSON (configurations/tasks)
- Merge aditivo de configurações
- Preservação de configs customizadas
- Identificação por label/name

Sprint 4 (P2 MEDIUM): Expansão do merge system para 90% coverage
Feature: VS Code debug/task configs não propagados em upgrades
"""

import json
import logging
from pathlib import Path
from typing import Any

from .config import CreatedItem

log = logging.getLogger(__name__)


# =============================================================================
# VSCodeConfigMerger
# =============================================================================


class VSCodeConfigMerger:
    """
    Merger inteligente para .vscode/launch.json e .vscode/tasks.json

    Estratégia de merge:
    1. **launch.json (configurations)**:
       - Adicionar novas configurations ausentes
       - Identificar por "name" field
       - Preservar configs customizadas
       - Atualizar se mesma name mas diferentes settings

    2. **tasks.json (tasks)**:
       - Adicionar novas tasks ausentes
       - Identificar por "label" field
       - Preservar tasks customizadas
       - Merge de dependsOn arrays

    3. **Preservação**:
       - Configs/tasks customizadas sempre preservadas
       - Merge é sempre aditivo (nunca remove)
       - User-wins strategy em conflitos
    """

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é launch.json ou tasks.json em .vscode/."""
        return (
            file_path.name in ["launch.json", "tasks.json"]
            and ".vscode" in file_path.parts
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do config JSON.

        Algoritmo:
        1. Parse JSON (existente e template)
        2. Identificar tipo (launch vs tasks)
        3. Merge items (configurations ou tasks)
        4. Preservar outras propriedades
        5. Gerar JSON mesclado
        6. Salvar com backup do original
        """
        try:
            # 1. Parse existente
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_data = json.loads(existing_content)

            # 2. Parse template
            template_data = json.loads(template_content)

            # 3. Identificar tipo e key
            if existing_path.name == "launch.json":
                items_key = "configurations"
                id_field = "name"
            elif existing_path.name == "tasks.json":
                items_key = "tasks"
                id_field = "label"
            else:
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message="Tipo de arquivo não suportado",
                )

            # Validar estrutura
            if items_key not in existing_data:
                existing_data[items_key] = []
            if items_key not in template_data:
                template_data[items_key] = []

            # 4. Merge items
            merged_items, changes = self._merge_items(
                existing_data[items_key], template_data[items_key], id_field
            )

            if not changes:
                log.info("⏭️  Skip: %s (sem mudanças)", existing_path.name)
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message="Nenhuma mudança necessária",
                )

            # 5. Backup do original
            backup_path = existing_path.with_suffix(existing_path.suffix + ".backup")
            existing_path.rename(backup_path)
            log.info("📦 Backup: %s", backup_path.name)

            # 6. Construir objeto mesclado
            merged_data = {**template_data, **existing_data}  # User wins top-level
            merged_data[items_key] = merged_items

            # 7. Escrever arquivo
            merged_json = json.dumps(merged_data, indent=2, ensure_ascii=False)
            existing_path.write_text(merged_json + "\n", encoding="utf-8")

            log.info("🔀 Merged %s: %s", existing_path.name, ", ".join(changes))

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="merged",
                message=f"Merged: {', '.join(changes)}",
            )

        except json.JSONDecodeError as e:
            log.error("❌ JSON error em %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"JSON error: {e}",
            )
        except Exception as e:
            log.error("❌ Erro ao mergear %s: %s", existing_path.name, e)
            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"Merge error: {e}",
            )

    def _merge_items(
        self,
        existing: list[dict[str, Any]],
        template: list[dict[str, Any]],
        id_field: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Merge items (configurations ou tasks).

        Retorna: (merged_items, changes_list)
        """
        changes = []
        {item.get(id_field): item for item in existing if id_field in item}
        merged = []
        seen = set()

        # Preservar items existentes (ordem preservada)
        for item in existing:
            item_id = item.get(id_field)
            if not item_id or item_id in seen:
                # Item sem ID ou duplicado, preservar mesmo assim
                merged.append(item)
                continue

            seen.add(item_id)

            # Verificar se há versão no template
            template_item = next(
                (t for t in template if t.get(id_field) == item_id), None
            )

            if template_item:
                # Merge deep (user wins)
                merged_item = self._deep_merge(template_item, item)
                merged.append(merged_item)
            else:
                # Item customizado, preservar
                merged.append(item)

        # Adicionar items novos do template
        for template_item in template:
            item_id = template_item.get(id_field)
            if item_id and item_id not in seen:
                seen.add(item_id)
                merged.append(template_item)
                changes.append(f"+{item_id}")

        return merged, changes

    def _deep_merge(
        self, base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Deep merge de dicts (user wins strategy).

        Template wins para novos campos, user wins para conflitos.
        """
        import copy

        result = copy.deepcopy(override)  # Start with template

        for key, value in base.items():
            if key not in result:
                # User has field that template doesn't → preserve
                result[key] = copy.deepcopy(value)
            elif isinstance(value, dict) and isinstance(result[key], dict):
                # Both have dict → recurse (template wins inside)
                result[key] = self._deep_merge(value, result[key])
            elif isinstance(value, list) and isinstance(result[key], list):
                # Both have list → union (preserve order)
                merged_list = list(result[key])  # Template first
                for item in value:
                    if item not in merged_list:
                        merged_list.append(copy.deepcopy(item))
                result[key] = merged_list
            # Else: template wins (use result[key] from template)

        return result
