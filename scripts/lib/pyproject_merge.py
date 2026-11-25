"""
Pyproject TOML Merger - Intelligent merge for pyproject.toml files

Merger especializado para pyproject.toml com suporte a:
- Parse TOML ([project], [build-system], [tool.*])
- Merge aditivo de dependencies
- Merge de optional-dependencies (dev, security, test)
- Preservação de tool configs customizados
- Atualização de tool best practices

Sprint 3 (P1 HIGH): Resolve gap de pyproject.toml sem merge
Bug fix: Dependencies e tool configs não propagados
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found, no-redef]  # fallback Python<3.11 (requires-python>=3.12)

from .config import CreatedItem

log = logging.getLogger(__name__)


# =============================================================================
# Types and Data Classes
# =============================================================================


@dataclass
class PyprojectContent:
    """Representa conteúdo de pyproject.toml."""

    project: dict[str, Any]  # [project] section
    build_system: dict[str, Any]  # [build-system] section
    tool_configs: dict[str, dict[str, Any]]  # [tool.*] sections
    raw_toml: dict[str, Any]  # TOML completo


@dataclass
class PyprojectMergeDecision:
    """Decisão de merge para pyproject.toml."""

    should_merge: bool
    reason: str
    changes: list[str]


# =============================================================================
# PyprojectMerger
# =============================================================================


class PyprojectMerger:
    """
    Merger inteligente para pyproject.toml

    Estratégia de merge:
    1. **[project] section**:
       - Preservar name, version, description (projeto específico)
       - Atualizar requires-python se mais recente
       - Merge aditivo de dependencies
       - Merge aditivo de optional-dependencies

    2. **[build-system] section**:
       - Preservar se customizado
       - Atualizar se template mais recente

    3. **[tool.*] sections**:
       - Adicionar novas tool configs ausentes (black, ruff, bandit, mypy)
       - Preservar configs customizados
       - Atualizar best practices (select, ignore, target-version)
       - Merge aditivo nunca remove

    4. **Preservação**:
       - Project metadata sempre preservado
       - Tool configs customizados preservados
       - Merge é sempre aditivo (nunca remove)
       - Em caso de dúvida, preserva local
    """

    # Tool sections consideradas "best practices" que podem ser atualizadas
    BEST_PRACTICE_TOOLS = {
        "black",
        "ruff",
        "bandit",
        "mypy",
        "pytest",
        "coverage",
    }

    # Optional dependencies groups recomendados
    RECOMMENDED_GROUPS = {
        "dev",
        "test",
        "security",
        "docs",
    }

    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é arquivo pyproject.toml."""
        return file_path.name == "pyproject.toml"

    def merge(
        self, existing_path: Path, template_content: str, interactive: bool = True
    ) -> CreatedItem:
        """
        Faz merge inteligente do pyproject.toml

        Algoritmo:
        1. Parse TOML (existente e template)
        2. Decidir se deve fazer merge
        3. Merge [project] (dependencies)
        4. Merge [build-system]
        5. Merge [tool.*] sections
        6. Gerar TOML mesclado
        7. Salvar com backup do original
        """
        try:
            # 1. Parse existente
            existing_content = existing_path.read_text(encoding="utf-8")
            existing_proj = self._parse_pyproject(existing_content)

            # 2. Parse template
            template_proj = self._parse_pyproject(template_content)

            # 3. Decisão de merge
            decision = self._should_merge(
                existing_proj, template_proj, existing_path.name
            )

            if not decision.should_merge:
                log.info("⏭️  Skip: %s (%s)", existing_path.name, decision.reason)
                return CreatedItem(
                    path=existing_path,
                    kind="file",
                    status="skipped",
                    message=decision.reason,
                )

            # 4. Merge [project]
            merged_project = self._merge_project_section(
                existing_proj.project, template_proj.project
            )

            # 5. Merge [build-system]
            merged_build = existing_proj.build_system or template_proj.build_system

            # 6. Merge [tool.*]
            merged_tools = self._merge_tool_configs(
                existing_proj.tool_configs, template_proj.tool_configs
            )

            # 7. Gerar TOML final
            merged_toml = {}

            if merged_project:
                merged_toml["project"] = merged_project

            if merged_build:
                merged_toml["build-system"] = merged_build

            # Adicionar tool configs
            for tool_name, tool_config in merged_tools.items():
                merged_toml[f"tool.{tool_name}"] = tool_config

            merged_content = self._format_toml(merged_toml)

            # 8. Backup e save
            backup_path = existing_path.with_suffix(".toml.backup")
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

    def _parse_pyproject(self, content: str) -> PyprojectContent:
        """
        Parse pyproject.toml em estrutura PyprojectContent.

        Extrai: [project], [build-system], [tool.*]

        Bug fix: TOML cria dict aninhado tool->black, não tool.black
        """
        try:
            toml_data = tomllib.loads(content)
        except Exception as e:
            log.warning("TOML parse error: %s, using empty pyproject", e)
            toml_data = {}

        # Bug fix: TOML cria estrutura aninhada {"tool": {"black": {...}}}
        # não {"tool.black": {...}}
        tool_configs = toml_data.get("tool", {})

        return PyprojectContent(
            project=toml_data.get("project", {}),
            build_system=toml_data.get("build-system", {}),
            tool_configs=tool_configs,
            raw_toml=toml_data,
        )

    # =========================================================================
    # Decision Logic
    # =========================================================================

    def _should_merge(
        self,
        existing_proj: PyprojectContent,
        template_proj: PyprojectContent,
        filename: str,
    ) -> PyprojectMergeDecision:
        """
        Decide se deve fazer merge baseado em novas dependencies/tools.

        Critérios:
        1. Se template tem novas dependencies → merge
        2. Se template tem novos optional-dependencies groups → merge
        3. Se template tem novas tool configs → merge
        4. Caso contrário → skip
        """
        changes = []

        # 1. Detectar novas dependencies
        existing_deps = set(existing_proj.project.get("dependencies", []))
        template_deps = set(template_proj.project.get("dependencies", []))

        # Comparar por nome de pacote (antes do >=, ==, etc.)
        existing_pkg_names = {
            dep.split(">")[0].split("=")[0].split("<")[0].strip()
            for dep in existing_deps
        }
        template_pkg_names = {
            dep.split(">")[0].split("=")[0].split("<")[0].strip()
            for dep in template_deps
        }

        new_deps = template_pkg_names - existing_pkg_names
        if new_deps:
            changes.append(f"Add {len(new_deps)} dependencies")

        # 2. Detectar novos optional-dependencies groups
        existing_optional = set(
            existing_proj.project.get("optional-dependencies", {}).keys()
        )
        template_optional = set(
            template_proj.project.get("optional-dependencies", {}).keys()
        )
        new_optional_groups = template_optional - existing_optional

        if new_optional_groups:
            changes.append(
                f"Add {len(new_optional_groups)} optional-dependencies groups"
            )

        # 3. Detectar novas tool configs
        existing_tools = set(existing_proj.tool_configs.keys())
        template_tools = set(template_proj.tool_configs.keys())
        new_tools = template_tools - existing_tools

        new_best_practice_tools = [
            t for t in new_tools if t in self.BEST_PRACTICE_TOOLS
        ]

        if new_best_practice_tools:
            changes.append(f"Add {len(new_best_practice_tools)} tool configs")

        # Decisão final
        if not changes:
            return PyprojectMergeDecision(
                should_merge=False, reason="Pyproject already up-to-date", changes=[]
            )

        return PyprojectMergeDecision(
            should_merge=True,
            reason=f"Template has updates ({len(changes)} changes)",
            changes=changes,
        )

    # =========================================================================
    # Merge Methods
    # =========================================================================

    def _merge_project_section(
        self, existing: dict[str, Any], template: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge [project] section com estratégia de preservar metadata.

        Regras:
        - name, version, description: preservar existing
        - requires-python: atualizar se template mais recente
        - dependencies: merge aditivo
        - optional-dependencies: merge por grupo
        """
        merged = dict(existing)

        # Preservar metadata do projeto
        # (name, version, description, readme já vêm do existing)

        # Atualizar requires-python se template mais recente
        if "requires-python" in template:
            merged["requires-python"] = template["requires-python"]

        # Merge dependencies (aditivo)
        existing_deps = set(existing.get("dependencies", []))
        template_deps = set(template.get("dependencies", []))

        # Criar map por nome de pacote
        existing_dep_map = {}
        for dep in existing_deps:
            pkg_name = dep.split(">")[0].split("=")[0].split("<")[0].strip()
            existing_dep_map[pkg_name] = dep

        # Adicionar dependencies do template que não existem
        for template_dep in template_deps:
            pkg_name = template_dep.split(">")[0].split("=")[0].split("<")[0].strip()
            if pkg_name not in existing_dep_map:
                existing_dep_map[pkg_name] = template_dep

        merged["dependencies"] = sorted(existing_dep_map.values())

        # Merge optional-dependencies por grupo
        existing_optional = existing.get("optional-dependencies", {})
        template_optional = template.get("optional-dependencies", {})

        merged_optional = dict(existing_optional)

        for group, deps in template_optional.items():
            if group not in merged_optional:
                # Novo grupo - adicionar
                merged_optional[group] = deps
            else:
                # Grupo existe - merge dependencies
                merged_optional[group] = self._merge_dependency_list(
                    merged_optional[group], deps
                )

        if merged_optional:
            merged["optional-dependencies"] = merged_optional

        return merged

    def _merge_dependency_list(
        self, existing: list[str], template: list[str]
    ) -> list[str]:
        """Merge lista de dependencies (aditivo por nome de pacote)."""
        existing_set = set(existing)
        template_set = set(template)

        # Map por nome de pacote
        existing_map = {}
        for dep in existing_set:
            pkg_name = dep.split(">")[0].split("=")[0].split("<")[0].strip()
            existing_map[pkg_name] = dep

        # Adicionar ausentes do template
        for template_dep in template_set:
            pkg_name = template_dep.split(">")[0].split("=")[0].split("<")[0].strip()
            if pkg_name not in existing_map:
                existing_map[pkg_name] = template_dep

        return sorted(existing_map.values())

    def _merge_tool_configs(
        self, existing: dict[str, dict[str, Any]], template: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """
        Merge [tool.*] sections com preservação de customizações.

        Regras:
        - Adicionar novas tool configs ausentes (best practices)
        - Preservar configs customizados
        - Atualizar select/ignore/target-version em best practice tools
        - Nunca remover configs existentes
        """
        merged = dict(existing)

        for tool_name, tool_config in template.items():
            if tool_name not in merged:
                # Nova tool config - adicionar
                merged[tool_name] = tool_config
            elif tool_name in self.BEST_PRACTICE_TOOLS:
                # Tool de best practice - merge configs
                merged[tool_name] = self._merge_tool_config(
                    merged[tool_name], tool_config, tool_name
                )
            # Else: preserve existing custom tool config

        return merged

    def _merge_tool_config(
        self, existing: dict[str, Any], template: dict[str, Any], tool_name: str
    ) -> dict[str, Any]:
        """
        Merge configuração de uma tool específica.

        Atualiza campos de best practices, preserva customizações.
        """
        merged = dict(existing)

        # Campos que geralmente devem ser atualizados (best practices)
        update_fields = {
            "target-version",
            "python-version",
            "line-length",
        }

        # Campos que devem ser merged (arrays)
        merge_array_fields = {
            "select",  # ruff
            "ignore",  # ruff
            "exclude_dirs",  # bandit
            "skips",  # bandit
        }

        for key, value in template.items():
            if key in update_fields:
                # Atualizar best practice
                merged[key] = value
            elif key in merge_array_fields and isinstance(value, list):
                # Merge arrays (aditivo)
                if key in merged and isinstance(merged[key], list):
                    merged[key] = list(set(merged[key] + value))
                else:
                    merged[key] = value
            elif key not in merged:
                # Novo campo - adicionar
                merged[key] = value
            # Else: preserve existing custom config

        return merged

    def _format_toml(self, data: dict[str, Any]) -> str:
        """
        Formata dict em TOML string.

        Usa formatação manual para manter ordem e comentários.
        """
        lines = []

        # [project] section
        if "project" in data:
            lines.append("[project]")
            project = data["project"]

            for key in ["name", "version", "description", "readme", "requires-python"]:
                if key in project:
                    value = project[key]
                    if isinstance(value, str):
                        lines.append(f'{key} = "{value}"')
                    else:
                        lines.append(f"{key} = {value}")

            if "dependencies" in project:
                lines.append("dependencies = [")
                for dep in project["dependencies"]:
                    lines.append(f'    "{dep}",')
                lines.append("]")

            if "optional-dependencies" in project:
                lines.append("")
                lines.append("[project.optional-dependencies]")
                for group, deps in project["optional-dependencies"].items():
                    lines.append(f"{group} = [")
                    for dep in deps:
                        lines.append(f'    "{dep}",')
                    lines.append("]")

        # [build-system] section
        if "build-system" in data:
            lines.append("")
            lines.append("[build-system]")
            build = data["build-system"]

            if "requires" in build:
                lines.append("requires = [")
                for req in build["requires"]:
                    lines.append(f'    "{req}",')
                lines.append("]")

            if "build-backend" in build:
                lines.append(f'build-backend = "{build["build-backend"]}"')

        # [tool.*] sections
        for key, value in data.items():
            if key.startswith("tool."):
                lines.append("")
                lines.append(f"[{key}]")
                lines.extend(self._format_tool_section(value))

        return "\n".join(lines) + "\n"

    def _format_tool_section(
        self, config: dict[str, Any], indent: int = 0
    ) -> list[str]:
        """Formata seção de tool recursivamente."""
        lines = []
        indent_str = "    " * indent

        for key, value in config.items():
            if isinstance(value, dict):
                # Sub-section
                lines.append(f"{indent_str}{key} = {{")
                lines.extend(self._format_tool_section(value, indent + 1))
                lines.append(f"{indent_str}}}")
            elif isinstance(value, list):
                # Array
                if all(isinstance(item, str) for item in value):
                    lines.append(f"{indent_str}{key} = [")
                    for item in value:
                        lines.append(f'{indent_str}    "{item}",')
                    lines.append(f"{indent_str}]")
                else:
                    lines.append(f"{indent_str}{key} = {value}")
            elif isinstance(value, str):
                lines.append(f'{indent_str}{key} = "{value}"')
            elif isinstance(value, bool):
                lines.append(f"{indent_str}{key} = {'true' if value else 'false'}")
            else:
                lines.append(f"{indent_str}{key} = {value}")

        return lines
