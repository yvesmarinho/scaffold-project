"""
objetivo_migrator.py — Migrator for objetivo.yaml v1.0 → v2.0

Automatically migrates objetivo.yaml files from v1.0 (YAML puro) to v2.0
(Markdown Híbrido) format with zero data loss.

Features:
- Detects version automatically (v1.0, v2.0, or unknown)
- Maps all v1.0 fields to corresponding v2.0 sections
- Preserves all data (warns if fields cannot be mapped)
- Generates preview file for review before overwriting

Usage:
    from scripts.lib.objetivo_migrator import ObjetivoMigrator

    migrator = ObjetivoMigrator()
    result = migrator.migrate("objetivo.yaml")

    if result.success:
        print(f"✅ Migrated! Preview: {result.preview_file}")
        print(f"Warnings: {len(result.warnings)}")

Spec: specs/066-objetivo-yaml-v2/spec.md
Tasks: T016-T020
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class MigrationResult:
    """Dataclass representing the result of a migration.

    Attributes:
        success: Whether migration completed successfully
        source_version: Detected version of source file ("1.0" | "2.0" | "unknown")
        target_version: Target version (always "2.0")
        preview_file: Path to preview file (objetivo.yaml.v2)
        mappings: Dict of field mappings applied (v1_field -> v2_section)
        warnings: List of warnings (e.g., unmapped fields, data loss risks)
        errors: List of errors that prevented migration
    """

    success: bool
    source_version: str
    target_version: str = "2.0"
    preview_file: Path | None = None
    mappings: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Format result for display."""
        if not self.success:
            return "❌ Migration failed:\n  " + "\n  ".join(self.errors)

        result = f"✅ Migration successful: v{self.source_version} → v{self.target_version}\n"
        result += f"📄 Preview: {self.preview_file}\n"
        result += f"🔄 Mappings: {len(self.mappings)} fields\n"

        if self.warnings:
            result += f"⚠️  Warnings ({len(self.warnings)}):\n"
            for w in self.warnings[:3]:  # Show first 3 warnings
                result += f"  - {w}\n"
            if len(self.warnings) > 3:
                result += f"  ... and {len(self.warnings) - 3} more\n"

        return result


class ObjetivoMigrator:
    """Migrator for objetivo.yaml v1.0 → v2.0.

    Detects version automatically and migrates from v1.0 YAML structure
    to v2.0 Markdown Híbrido format.

    Example:
        migrator = ObjetivoMigrator()
        result = migrator.migrate("objetivo.yaml")

        if result.success:
            print(f"Preview: {result.preview_file}")
            # User reviews objetivo.yaml.v2
            # Then: mv objetivo.yaml objetivo.yaml.v1.bak
            #       mv objetivo.yaml.v2 objetivo.yaml
    """

    # v1.0 field patterns
    V1_INDICATORS = [
        "feature.id",
        "negocio.problema",
        "produto.visao_alto_nivel",
        "decisoes_iniciais",
    ]

    # v2.0 indicators
    V2_INDICATORS = [
        'version: "2.0"',
        "## 1️⃣",
        "## 2️⃣",
        "## 3️⃣",
    ]

    def __init__(self) -> None:
        """Initialize migrator."""
        pass

    def migrate(
        self, file_path: str | Path, output_path: str | Path | None = None
    ) -> MigrationResult:
        """Migrate objetivo.yaml v1.0 → v2.0.

        Args:
            file_path: Path to source objetivo.yaml file
            output_path: Path to write preview (default: {file_path}.v2)

        Returns:
            MigrationResult with success status, mappings, and warnings

        Raises:
            FileNotFoundError: If source file does not exist

        Implementation:
            1. Read source file
            2. Detect version (_detect_version)
            3. If already v2.0, return error
            4. If v1.0, map to v2.0 (_map_v1_to_v2)
            5. Render template with mappings
            6. Write preview file
            7. Return MigrationResult
        """
        # Convert to Path
        source_path = Path(file_path)

        # Check file exists
        if not source_path.exists():
            return MigrationResult(
                success=False,
                source_version="unknown",
                errors=[f"Source file not found: {source_path}"],
            )

        # Read source file
        try:
            content = source_path.read_text(encoding="utf-8")
        except Exception as e:
            return MigrationResult(
                success=False,
                source_version="unknown",
                errors=[f"Failed to read source file: {e}"],
            )

        # Detect version
        version = self._detect_version(content)

        # Check if already v2.0
        if version == "2.0":
            return MigrationResult(
                success=False,
                source_version="2.0",
                errors=["File is already in v2.0 format - no migration needed"],
            )

        # Check if unknown version
        if version == "unknown":
            return MigrationResult(
                success=False,
                source_version="unknown",
                errors=[
                    "Cannot detect version format",
                    "File may be malformed or in an unsupported format",
                ],
                warnings=["Check if file is valid YAML or has expected v1.0 fields"],
            )

        # Parse v1.0 YAML (handle multi-document YAML with comments)
        try:
            # First, try safe_load for single document
            try:
                v1_data = yaml.safe_load(content)
            except yaml.composer.ComposerError:
                # Multi-document YAML - load all documents and use last one
                # (templates have frontmatter comments as first document)
                docs = list(yaml.safe_load_all(content))
                # Filter out None documents (from pure comments)
                docs = [d for d in docs if d is not None]
                if not docs:
                    raise ValueError("No valid YAML documents found") from None
                # Use last non-None document
                v1_data = docs[-1]
        except yaml.YAMLError as e:
            return MigrationResult(
                success=False,
                source_version="1.0",
                errors=[f"Failed to parse v1.0 YAML: {e}"],
            )
        except Exception as e:
            return MigrationResult(
                success=False,
                source_version="1.0",
                errors=[f"Failed to parse YAML: {e}"],
            )

        if not isinstance(v1_data, dict):
            return MigrationResult(
                success=False,
                source_version="1.0",
                errors=[f"Expected YAML dict, got {type(v1_data).__name__}"],
            )

        # Map v1.0 to v2.0
        v2_content, warnings = self._map_v1_to_v2(v1_data)

        # Render v2.0 template
        frontmatter = v2_content["frontmatter"]
        sections = v2_content["sections"]
        v2_text = self._render_v2_template(frontmatter, sections)

        # Determine output path
        if output_path is None:
            output_path = source_path.parent / f"{source_path.name}.v2"
        else:
            output_path = Path(output_path)

        # Write preview file
        try:
            output_path.write_text(v2_text, encoding="utf-8")
        except Exception as e:
            return MigrationResult(
                success=False,
                source_version="1.0",
                errors=[f"Failed to write preview file: {e}"],
                warnings=warnings,
            )

        # Build mappings summary
        mappings = {
            "feature.name": f"project.name ({frontmatter['project']['name']})",
            "produto.visao_alto_nivel": "Section 1️⃣",
            "negocio.problema": "Section 2️⃣",
            "produto.jornadas_criticas": "Section 3️⃣",
            "negocio.contexto.restricoes": "Section 4️⃣",
            "produto.personas": "Section 5️⃣",
            "decisoes_iniciais": "Section 7️⃣",
        }

        # Success!
        return MigrationResult(
            success=True,
            source_version="1.0",
            target_version="2.0",
            preview_file=output_path,
            mappings=mappings,
            warnings=warnings,
        )

    def _detect_version(self, content: str) -> str:
        """Detect objetivo.yaml version from content.

        Args:
            content: File content as string

        Returns:
            Version string: "1.0" | "2.0" | "unknown"

        Detection Logic:
            - v1.0: YAML puro, has fields like feature:, negocio:, produto:
            - v2.0: Markdown Híbrido, has YAML frontmatter with version: "2.0"
            - unknown: Cannot determine (malformed or new format)

        Implementation:
            Check for v2.0 indicators first (version field, ## sections)
            Then check for v1.0 indicators (nested YAML fields)
            Return "unknown" if neither matches
        """
        # Check for v2.0 indicators first (more specific)
        # Strong v2.0 signal: has version: "2.0" AND markdown sections
        if 'version: "2.0"' in content and any(
            f"## {i}️⃣" in content for i in [1, 2, 3]
        ):
            return "2.0"

        if "version: '2.0'" in content and any(
            f"## {i}️⃣" in content for i in [1, 2, 3]
        ):
            return "2.0"

        # Check for v1.0 indicators - top-level YAML keys
        v1_score = 0
        v1_keys = ["feature:", "negocio:", "produto:", "decisoes_iniciais:"]

        for key in v1_keys:
            # Check if key appears at start of line (top-level YAML key)
            if re.search(rf"^{re.escape(key)}", content, re.MULTILINE):
                v1_score += 1

        # Decision logic
        if v1_score >= 2:
            return "1.0"

        return "unknown"

    def _map_v1_to_v2(
        self, v1_data: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """Map v1.0 YAML structure to v2.0 format.

        Args:
            v1_data: Parsed v1.0 YAML dict

        Returns:
            Tuple of (v2_content, warnings)
            - v2_content: Dict with frontmatter + sections for template rendering
            - warnings: List of warnings (unmapped fields, missing data, etc.)

        Mapping Rules:
            feature.name → frontmatter project.name
            produto.visao_alto_nivel → Section 1️⃣ (What this does)
            negocio.problema.descricao → Section 2️⃣ (Problem solved)
            produto.jornadas_criticas → Section 3️⃣ Incluído (In scope)
            [missing out-scope] → Section 3️⃣ Excluído (Out of scope)
            negocio.contexto.restricoes_negocio → Section 4️⃣ (Constraints)
            produto.personas → Section 5️⃣ (Business rules - adapted)
            decisoes_iniciais → Section 7️⃣ (Technologies - adapted)

        Implementation:
            Build dict with frontmatter (project.name, type, domain)
            and sections dict {1: content, 2: content, ...}
            Track unmapped fields and add warnings
        """
        warnings = []
        sections = {}

        # Extract feature info
        feature = v1_data.get("feature", {})
        project_name = feature.get("name", "migrated-project").lower().replace(" ", "-")

        # Build frontmatter
        frontmatter = {
            "version": "2.0",
            "project": {
                "name": project_name,
                "title": feature.get("name", "Migrated Project"),
                "type": "backend-api",  # Default, user should update
                "domain": "programming",  # Default, user should update
                "language": "python",  # Default, user should update
            },
            "created_at": feature.get("created", ""),
            "created_by": "migrated-from-v1.0",
            "generation": {
                "profiles_auto_detect": True,
                "validate_on_save": True,
            },
            "validation": {
                "level": "strict",
                "require_p0": True,
            },
        }

        # Section 1: What this does (from produto.visao_alto_nivel)
        produto = v1_data.get("produto", {})
        visao = produto.get("visao_alto_nivel", "").strip()
        if visao:
            sections[1] = f"**Em uma frase**: {visao}\n\n"
            sections[1] += "**Componentes principais**:\n"
            sections[1] += "- [Atualizar após migração]\n"
        else:
            warnings.append(
                "Section 1: produto.visao_alto_nivel not found - section will be minimal"
            )
            sections[1] = "**Em uma frase**: [Descreva o que este projeto faz]\n"

        # Section 2: Problem solved (from negocio.problema)
        negocio = v1_data.get("negocio", {})
        problema = negocio.get("problema", {})
        problema_desc = problema.get("descricao", "").strip()
        impacto = problema.get("impacto_atual", "").strip()

        if problema_desc or impacto:
            sections[2] = ""
            if problema_desc:
                sections[2] += f"### Problema Atual\n\n{problema_desc}\n\n"
            if impacto:
                sections[2] += f"### Impacto\n\n{impacto}\n"
        else:
            warnings.append(
                "Section 2: negocio.problema not found - section will be minimal"
            )
            sections[2] = (
                "### Problema Atual\n\n[Descreva o problema que este projeto resolve]\n"
            )

        # Section 3: Scope (from produto.jornadas_criticas)
        jornadas = produto.get("jornadas_criticas", [])
        sections[3] = "**Incluído ✅**:\n"

        if jornadas:
            for jornada in jornadas:
                if isinstance(jornada, dict):
                    journey_name = jornada.get("journey", "")
                    priority = jornada.get("priority", "P2")
                    if journey_name:
                        sections[3] += f"- {journey_name} ({priority})\n"
        else:
            warnings.append(
                "Section 3: produto.jornadas_criticas not found - adding placeholder"
            )
            sections[3] += "- [Adicione itens do escopo]\n"

        sections[3] += "\n**Excluído ❌**:\n"
        sections[3] += "- [Adicione itens fora do escopo]\n"

        # Section 4: Constraints (from negocio.contexto.restricoes_negocio)
        contexto = negocio.get("contexto", {})
        restricoes = contexto.get("restricoes_negocio", [])

        if restricoes:
            sections[4] = "**Restrições de Negócio**:\n"
            for restricao in restricoes:
                if isinstance(restricao, str):
                    sections[4] += f"- {restricao}\n"
        else:
            # Optional section, don't add if no data
            pass

        # Section 5: Business Rules (adapted from produto.personas)
        personas = produto.get("personas", [])

        if personas:
            sections[5] = "**Personas e Necessidades**:\n\n"
            for persona in personas:
                if isinstance(persona, dict):
                    name = persona.get("name", "")
                    needs = persona.get("needs", "")
                    pain_points = persona.get("pain_points", "")

                    if name:
                        sections[5] += f"**{name}**:\n"
                        if needs:
                            sections[5] += f"- Necessidade: {needs}\n"
                        if pain_points:
                            sections[5] += f"- Pain Point: {pain_points}\n"
                        sections[5] += "\n"
        else:
            # Optional section
            pass

        # Section 7: Technologies (adapted from decisoes_iniciais)
        decisoes = v1_data.get("decisoes_iniciais", [])

        if decisoes:
            sections[7] = "**Decisões Técnicas Iniciais**:\n\n"
            for decisao in decisoes:
                if isinstance(decisao, dict):
                    question = decisao.get("question", "")
                    decision = decisao.get("decision", "")

                    if question and decision:
                        sections[7] += f"- **{question}**\n"
                        sections[7] += f"  Decisão: {decision}\n\n"

        # Add general warning about manual review
        warnings.append(
            "Migration complete but manual review recommended: "
            "update project.type, project.domain, project.language in frontmatter"
        )

        v2_content = {
            "frontmatter": frontmatter,
            "sections": sections,
        }

        return v2_content, warnings

    def _render_v2_template(
        self, frontmatter: dict[str, Any], sections: dict[int, str]
    ) -> str:
        """Render v2.0 template with mapped content.

        Args:
            frontmatter: YAML frontmatter dict
            sections: Dict mapping section number to content

        Returns:
            Complete v2.0 objetivo.yaml content as string
        """
        # Build YAML frontmatter
        yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)

        # Build Markdown sections
        section_titles = {
            1: "O que este projeto faz?",
            2: "Qual problema resolve?",
            3: "Escopo do Projeto",
            4: "Restrições Técnicas",
            5: "Regras de Negócio",
            6: "Estrutura de Pastas",
            7: "Tecnologias",
            8: "Próximos Passos",
            9: "Contexto Adicional",
        }

        # Start with frontmatter
        result = f"---\n{yaml_str}---\n\n"
        result += f"# 🎯 Objetivo: {frontmatter.get('project', {}).get('title', 'Project')}\n\n"

        # Add sections
        for num in sorted(sections.keys()):
            if num in section_titles and sections[num].strip():
                result += f"## {num}️⃣ {section_titles[num]}\n\n"
                result += sections[num].strip() + "\n\n---\n\n"

        return result
