"""
JSON and Workspace Merge System

Sistema de merge inteligente para arquivos JSON e .code-workspace.
Implementa estratégia user-wins com deep merge de estruturas aninhadas.

Bug fix: BUG-16 (P1 - JSON/workspace não mergeados, customizações perdidas)
Implementação: Sprint 2026-W21 (Fase 1 e 2)
"""

import json
import logging
import os
from collections import Counter
from pathlib import Path
from typing import Any

from .config import CreatedItem

log = logging.getLogger(__name__)

# DEBUG: Ativar logs de debug para troubleshooting BUG-20
if os.environ.get("DEBUG_MCP_MERGE"):
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.debug("🐛 DEBUG mode enabled for MCP merge troubleshooting")


# =============================================================================
# JSON Deep Merge Utilities
# =============================================================================


def deep_merge_json(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge com estratégia user-wins SEM union de arrays.

    Mudança arquitetural (v2.0): JSON é padrão de configuração no projeto.
    Todos os JSONs devem usar user-wins sem duplicação de arrays.

    Estratégia:
    - Overlay (usuário) sobrescreve base (template)
    - Arrays substituídos completamente (NÃO faz union)
    - Objetos aninhados mergeados recursivamente
    - Chaves novas do template são adicionadas
    - EXCEÇÃO: Mudanças de schema (type em MCP servers) usam template-wins

    Histórico:
    - v1.0: Usava always_merger.merge() (union de arrays) ❌ BUG
    - v2.0: Implementa user-wins sem union ✅ FIX ARQUITETURAL
    - v2.1: Template-wins para mudanças de schema MCP ✅ FIX BUG-20

    Args:
        base: Template (upstream)
        overlay: Usuário (customizações)

    Returns:
        Dicionário mergeado com estratégia user-wins

    Exemplos:
        >>> base = {"a": 1, "b": {"c": 2}}
        >>> overlay = {"b": {"d": 3}, "e": 4}
        >>> deep_merge_json(base, overlay)
        {'a': 1, 'b': {'c': 2, 'd': 3}, 'e': 4}

        >>> base = {"list": [1, 2]}
        >>> overlay = {"list": [3, 4]}
        >>> deep_merge_json(base, overlay)
        {'list': [3, 4]}  # User array wins, NÃO faz union

        >>> # BUG-20 fix: Schema change em MCP server
        >>> base = {"servers": {"github": {"type": "http", "url": "..."}}}
        >>> overlay = {"servers": {"github": {"type": "stdio", "command": "npx"}}}
        >>> result = deep_merge_json(base, overlay)
        >>> result["servers"]["github"]
        {'type': 'http', 'url': '...'}  # Template wins quando type muda
    """
    return _merge_user_wins_recursive(base, overlay, path=[])


def _is_mcp_schema_change(base: dict, overlay: dict, path: list[str]) -> bool:
    """
    Detecta mudança de schema em servidor MCP.

    Mudança de schema ocorre quando:
    1. Estamos em path servers.<server_name>
    2. Campo 'type' mudou entre base e overlay (incluindo adição/remoção)
    3. Caso especial: overlay tem type="stdio" e base não tem type (remoção de campo obsoleto)

    Args:
        base: Config do template
        overlay: Config do usuário
        path: Caminho atual (ex: ['servers', 'github'])

    Returns:
        True se há mudança de schema que requer template-wins

    Exemplos:
        >>> # Caso 1: Mudança stdio → http
        >>> base = {"type": "http", "url": "..."}
        >>> overlay = {"type": "stdio", "command": "npx"}
        >>> _is_mcp_schema_change(base, overlay, ["servers", "github"])
        True

        >>> # Caso 2: Remoção de type obsoleto (npx moderno)
        >>> base = {"command": "npx", "args": [...]}  # sem type
        >>> overlay = {"type": "stdio", "command": "npx"}
        >>> _is_mcp_schema_change(base, overlay, ["servers", "memory"])
        True

        >>> # Caso 3: Mesmo type, só customizações
        >>> base = {"type": "stdio", "command": "npx"}
        >>> overlay = {"type": "stdio", "command": "npx", "timeout": 1000}
        >>> _is_mcp_schema_change(base, overlay, ["servers", "github"])
        False
    """
    # DEBUG: Log entrada da função
    log.debug("🔍 [DEBUG] _is_mcp_schema_change called:")
    log.debug(f"  path: {path}")
    log.debug(f"  len(path): {len(path)}")
    log.debug(f"  path[0] if len>=1: {path[0] if len(path) >= 1 else 'N/A'}")

    # Verificar se estamos em path servers.<server_name>
    if len(path) >= 2 and path[0] == "servers":
        base_type = base.get("type")
        overlay_type = overlay.get("type")

        log.debug("  ✓ In servers path!")
        log.debug(f"  base_type: {base_type}")
        log.debug(f"  overlay_type: {overlay_type}")

        # Caso 1: Ambos têm type mas são diferentes
        if base_type and overlay_type and base_type != overlay_type:
            log.warning(
                f"🔄 Schema change detected in {'.'.join(path)}: "
                f"{overlay_type} → {base_type} (using template)"
            )
            return True

        # Caso 2: overlay tem type="stdio" (obsoleto) mas base não tem type (npx moderno)
        # Isso indica remoção de campo obsoleto = schema change
        if overlay_type == "stdio" and not base_type:
            log.warning(
                f"🔄 Schema change detected in {'.'.join(path)}: "
                f"stdio (obsolete) → npx wrapper (using template)"
            )
            return True

        # Caso 3: base tem type mas overlay não (adição de type no template)
        if base_type and not overlay_type:
            log.warning(
                f"🔄 Schema change detected in {'.'.join(path)}: "
                f"no type → {base_type} (using template)"
            )
            return True
    else:
        log.debug(f"  ✗ Not in servers path (path={path})")

    log.debug("  → No schema change detected")
    return False


def _merge_user_wins_recursive(
    base: dict, overlay: dict, path: list[str] | None = None
) -> dict:
    """
    Implementação do merge user-wins recursivo com detecção de schema change.

    Algoritmo:
    1. Detectar mudança de schema MCP → usar template-wins
    2. Copiar todos valores do overlay (user wins)
    3. Para objetos aninhados: merge recursivo
    4. Adicionar chaves novas do base que não existem no overlay

    Comportamento por tipo:
    - Primitivos: overlay wins
    - Arrays: overlay wins (NÃO faz union)
    - Objects: merge recursivo (exceto schema change)

    Args:
        base: Template
        overlay: Usuário
        path: Caminho atual para contexto (tracking de servers.*)

    Returns:
        Dicionário mergeado
    """
    if path is None:
        path = []

    # DEBUG: Log entrada da função
    if len(path) >= 2 and path[0] == "servers":
        log.debug("🔍 [DEBUG] _merge_user_wins_recursive called:")
        log.debug(f"  path: {path}")
        log.debug(f"  base keys: {list(base.keys())}")
        log.debug(f"  overlay keys: {list(overlay.keys())}")
        log.debug(f"  base.get('type'): {base.get('type')}")
        log.debug(f"  overlay.get('type'): {overlay.get('type')}")

    # BUG-20 FIX: Detectar mudança de schema em servidor MCP
    if _is_mcp_schema_change(base, overlay, path):
        # Template-wins: Usar configuração do template completamente
        log.info(f"✅ Applied template config for {'.'.join(path)} (schema changed)")
        return base.copy()

    merged = {}

    # Passo 1: User wins - copiar tudo do overlay
    for key, overlay_value in overlay.items():
        base_value = base.get(key)

        # Se ambos são dicts, merge recursivo
        if isinstance(overlay_value, dict) and isinstance(base_value, dict):
            merged[key] = _merge_user_wins_recursive(
                base_value, overlay_value, path + [key]
            )
        else:
            # Primitivos e arrays: user wins completamente
            merged[key] = overlay_value

    # Passo 2: Adicionar chaves novas do template
    for key, base_value in base.items():
        if key not in merged:
            merged[key] = base_value

    return merged


def load_json_safe(file_path: Path) -> dict[str, Any]:
    """
    Carrega arquivo JSON com tratamento de erros.

    Args:
        file_path: Caminho do arquivo JSON

    Returns:
        Dict parsed ou {} se erro

    Raises:
        ValueError: Se JSON inválido
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        data: dict[str, Any] = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        log.error(f"❌ JSON inválido em {file_path.name}: {e}")
        raise ValueError(f"JSON inválido: {e}") from e
    except Exception as e:
        log.error(f"❌ Erro ao ler {file_path.name}: {e}")
        raise


def _detect_duplications(data: Any, path: str = "root") -> list[dict[str, Any]]:
    """
    Detecta duplicações em estrutura JSON (versão simplificada).

    Args:
        data: Estrutura JSON a validar
        path: Caminho atual para contexto

    Returns:
        Lista de issues com duplicações
    """
    issues: list[dict[str, Any]] = []

    if isinstance(data, dict):
        for key, value in data.items():
            issues.extend(_detect_duplications(value, f"{path}.{key}"))
    elif isinstance(data, list):
        # Contar itens (objetos comparados por JSON)
        items = [
            json.dumps(i, sort_keys=True) if isinstance(i, (dict, list)) else i
            for i in data
        ]
        counts = Counter(items)
        duplicates = {k: v for k, v in counts.items() if v > 1}

        if duplicates:
            issues.append(
                {
                    "path": path,
                    "duplication_rate": (len(data) - len(counts)) / len(data) * 100,
                }
            )

    return issues


def save_json_formatted(file_path: Path, data: dict[str, Any]) -> None:
    """
    Salva JSON com formatação consistente e validação anti-duplicação.

    Validações:
    - Sintaxe JSON válida
    - Detecção de arrays duplicados (warning)

    Args:
        file_path: Caminho do arquivo JSON
        data: Dados a serem salvos
    """
    # Validar duplicações antes de salvar
    issues = _detect_duplications(data)
    if issues:
        log.warning(f"⚠️  Duplicações detectadas em {file_path.name}:")
        for issue in issues:
            log.warning(
                f"   {issue['path']}: {issue['duplication_rate']:.1f}% duplicado"
            )
        log.warning("   Execute: python scripts/fix-json-duplications.py")

    # Salvar com formatação consistente
    content = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=False)
    file_path.write_text(content + "\n", encoding="utf-8")


# =============================================================================
# JSONMerger - Merge genérico para arquivos .json
# =============================================================================


class JSONMerger:
    """
    Merger genérico para arquivos JSON.

    Aplica-se a:
    - .vscode/settings.json
    - .vscode/mcp.json
    - .vscode/extensions.json
    - package.json
    - tsconfig.json
    - Qualquer outro .json

    Estratégia:
    - Deep merge com user-wins
    - Backup automático antes de merge
    - Validação de sintaxe JSON
    """

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é arquivo .json (exceto os que têm merger próprio)."""
        # launch.json e tasks.json em .vscode/ são tratados por VSCodeConfigMerger
        is_vscode_config = ".vscode" in file_path.parts and file_path.name in (
            "launch.json",
            "tasks.json",
        )
        return (
            file_path.suffix == ".json"
            and not file_path.name.endswith(".code-workspace")
            and not is_vscode_config
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz deep merge de arquivo JSON existente com template.

        Args:
            existing_path: Arquivo JSON existente
            template_content: Conteúdo do template (string JSON)
            interactive: Não usado (merge sempre automático)

        Returns:
            CreatedItem com status="created" se merge bem-sucedido
        """
        try:
            # Backup do arquivo original
            backup_path = existing_path.with_suffix(existing_path.suffix + ".backup")
            existing_path.rename(backup_path)
            log.info(f"📦 Backup: {existing_path.name} → {backup_path.name}")

            # Carregar dados
            base_data = json.loads(template_content)
            overlay_data = load_json_safe(backup_path)

            # Deep merge (overlay sobrescreve base = user-wins)
            merged_data = deep_merge_json(base_data, overlay_data)

            # Salvar resultado
            save_json_formatted(existing_path, merged_data)

            log.info(f"🔄 Merged: {existing_path.name} (template + customizações)")

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="created",
                message=f"Merged with user customizations (backup: {backup_path.name})",
            )

        except ValueError as e:
            # JSON inválido - restaurar backup
            log.error(f"❌ Merge falhou: {e}")
            if backup_path.exists():
                backup_path.rename(existing_path)
                log.info(f"♻️  Restaurado backup: {backup_path.name}")

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="error",
                message=f"Invalid JSON, restored backup: {e}",
            )

        except Exception as e:
            log.error(f"❌ Erro inesperado no merge de {existing_path.name}: {e}")
            return CreatedItem(
                path=existing_path, kind="file", status="error", message=str(e)
            )


# =============================================================================
# WorkspaceMerger - Merge especializado para .code-workspace
# =============================================================================


class WorkspaceMerger:
    """
    Merger especializado para arquivos .code-workspace.

    Lógica específica:
    - folders: União de paths (sem duplicatas, preservar ordem overlay → base)
    - settings: Deep merge (user-wins)
    - extensions.recommendations: União de IDs (sem duplicatas)

    Exemplo:
        Base:
        {
          "folders": [{"path": "."}],
          "settings": {"editor.rulers": [80]},
          "extensions": {"recommendations": ["ms-python.python"]}
        }

        Overlay:
        {
          "folders": [{"path": "."}, {"path": "../libs"}],
          "settings": {"editor.rulers": [120], "python.linting.enabled": true},
          "extensions": {"recommendations": ["dbaeumer.vscode-eslint"]}
        }

        Resultado:
        {
          "folders": [{"path": "."}, {"path": "../libs"}],
          "settings": {
            "editor.rulers": [120],
            "python.linting.enabled": true
          },
          "extensions": {
            "recommendations": [
              "ms-python.python",
              "dbaeumer.vscode-eslint"
            ]
          }
        }
    """

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é arquivo .code-workspace."""
        return file_path.suffix == ".code-workspace" or file_path.name.endswith(
            ".code-workspace"
        )

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Merge especializado de .code-workspace.

        Args:
            existing_path: Arquivo .code-workspace existente
            template_content: Conteúdo do template
            interactive: Não usado

        Returns:
            CreatedItem com resultado do merge
        """
        try:
            # Backup
            backup_path = existing_path.with_suffix(".code-workspace.backup")
            existing_path.rename(backup_path)
            log.info(f"📦 Backup: {existing_path.name} → {backup_path.name}")

            # Carregar dados
            base_data = json.loads(template_content)
            overlay_data = load_json_safe(backup_path)

            # Merge especializado
            merged_data = self._merge_workspace_data(base_data, overlay_data)

            # Salvar
            save_json_formatted(existing_path, merged_data)

            log.info(f"🔄 Merged workspace: {existing_path.name}")

            return CreatedItem(
                path=existing_path,
                kind="file",
                status="created",
                message=f"Merged workspace (backup: {backup_path.name})",
            )

        except Exception as e:
            log.error(f"❌ Erro no merge de workspace: {e}")
            if backup_path.exists():
                backup_path.rename(existing_path)
                log.info("♻️  Restaurado backup")

            return CreatedItem(
                path=existing_path, kind="file", status="error", message=str(e)
            )

    def _merge_workspace_data(
        self, base: dict[str, Any], overlay: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge de dados de workspace com lógica específica.

        Args:
            base: Dados do template
            overlay: Dados do usuário

        Returns:
            Dados mergeados
        """
        merged: dict[str, Any] = {}

        # 1. Merge folders (união, sem duplicatas)
        base_folders = base.get("folders", [])
        overlay_folders = overlay.get("folders", [])

        # Usar set de paths para detectar duplicatas
        folders_set = set()
        merged_folders = []

        # Priorizar overlay (customizações do usuário primeiro)
        for folder in overlay_folders + base_folders:
            path = folder.get("path")
            if path and path not in folders_set:
                folders_set.add(path)
                merged_folders.append(folder)

        if merged_folders:
            merged["folders"] = merged_folders

        # 2. Merge settings (deep merge, user-wins)
        base_settings = base.get("settings", {})
        overlay_settings = overlay.get("settings", {})

        if base_settings or overlay_settings:
            merged["settings"] = deep_merge_json(base_settings, overlay_settings)

        # 3. Merge extensions.recommendations (união)
        base_ext = base.get("extensions", {}).get("recommendations", [])
        overlay_ext = overlay.get("extensions", {}).get("recommendations", [])

        if base_ext or overlay_ext:
            # União sem duplicatas, preservando ordem
            all_extensions = overlay_ext + base_ext
            unique_extensions = []
            seen = set()

            for ext_id in all_extensions:
                if ext_id not in seen:
                    seen.add(ext_id)
                    unique_extensions.append(ext_id)

            merged["extensions"] = {"recommendations": unique_extensions}

        # 4. Preservar outros campos do overlay (se houver)
        for key in overlay:
            if key not in ["folders", "settings", "extensions"]:
                merged[key] = overlay[key]

        return merged
