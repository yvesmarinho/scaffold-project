#!/usr/bin/env python3
"""
SpecKit Quality Gates Validation Engine

Validates transitions between 4-layer Spec Driven Development:
- Layer 1 (Business) → Layer 2 (Product): objetivo.yaml → spec.md
- Layer 2 (Product) → Layer 3 (Architecture): spec.md → plan.md
- Layer 3 (Architecture) → Layer 4 (Implementation): plan.md → tasks.md

Validation includes:
- JSON Schema validation for objetivo.yaml
- Quality gates enforcement per layer
- Automated checks for completeness and compliance

Usage:
    from scripts.lib.spec_validate import SpecValidator

    validator = SpecValidator(feature_dir=".specify/specs/IMP-53")
    result = validator.validate_layer_transition("business", "product")

    if result.passed:
        print("✅ Quality gates passed!")
    else:
        print(f"❌ {len(result.errors)} errors, {len(result.warnings)} warnings")
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import cast

try:
    import yaml
except ImportError:
    logging.warning("PyYAML not installed. Install with: uv pip install pyyaml")
    yaml = None  # type: ignore[assignment]  # dependência opcional

try:
    from jsonschema import Draft7Validator, ValidationError, validate
except ImportError:
    logging.warning("jsonschema not installed. Install with: uv pip install jsonschema")
    # fallbacks de dependência opcional (jsonschema ausente)
    ValidationError = Exception  # type: ignore[misc, assignment]  # fallback opcional
    Draft7Validator = None  # type: ignore[misc, assignment]  # fallback opcional
    validate = None  # type: ignore[assignment]  # fallback opcional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


class Layer(Enum):
    """4-layer Spec Driven Development layers"""

    BUSINESS = "business"  # Layer 1: objetivo.yaml
    PRODUCT = "product"  # Layer 2: spec.md
    ARCHITECTURE = "architecture"  # Layer 3: plan.md
    IMPLEMENTATION = "implementation"  # Layer 4: tasks.md


class Severity(Enum):
    """Validation issue severity levels"""

    ERROR = "error"  # Blocks progression to next layer
    WARNING = "warning"  # Should be addressed but not blocking
    INFO = "info"  # Informational, best practice recommendation


@dataclass
class ValidationIssue:
    """Represents a single validation issue"""

    severity: Severity
    layer: Layer
    rule: str
    message: str
    file: str | None = None
    line: int | None = None
    suggestion: str | None = None

    def __str__(self) -> str:
        prefix = {Severity.ERROR: "❌", Severity.WARNING: "⚠️", Severity.INFO: "ℹ️"}[
            self.severity
        ]

        location = (
            f" ({self.file}" + (f":{self.line}" if self.line else "") + ")"
            if self.file
            else ""
        )
        suggestion = f"\n   💡 {self.suggestion}" if self.suggestion else ""

        return f"{prefix} [{self.rule}] {self.message}{location}{suggestion}"


@dataclass
class ValidationResult:
    """Aggregated validation result"""

    layer_from: Layer
    layer_to: Layer
    passed: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    infos: list[ValidationIssue] = field(default_factory=list)

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add validation issue to appropriate list"""
        if issue.severity == Severity.ERROR:
            self.errors.append(issue)
            self.passed = False
        elif issue.severity == Severity.WARNING:
            self.warnings.append(issue)
        else:
            self.infos.append(issue)

    def summary(self) -> str:
        """Generate human-readable summary"""
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        counts = f"{len(self.errors)} errors, {len(self.warnings)} warnings, {len(self.infos)} infos"
        return f"{status}: {self.layer_from.value} → {self.layer_to.value} ({counts})"

    def detailed_report(self) -> str:
        """Generate detailed validation report"""
        lines = [
            f"\n{'='*80}",
            f"Validation Report: {self.layer_from.value.upper()} → {self.layer_to.value.upper()}",
            f"{'='*80}",
            f"Status: {'✅ PASSED' if self.passed else '❌ FAILED'}",
            f"Errors: {len(self.errors)} | Warnings: {len(self.warnings)} | Info: {len(self.infos)}",
            f"{'='*80}\n",
        ]

        if self.errors:
            lines.append("ERRORS (blocking):")
            for issue in self.errors:
                lines.append(f"  {issue}")
            lines.append("")

        if self.warnings:
            lines.append("WARNINGS (should fix):")
            for issue in self.warnings:
                lines.append(f"  {issue}")
            lines.append("")

        if self.infos:
            lines.append("INFO (recommendations):")
            for issue in self.infos:
                lines.append(f"  {issue}")
            lines.append("")

        return "\n".join(lines)


class SpecValidator:
    """SpecKit quality gates validator"""

    def __init__(self, feature_dir: Path | str):
        """
        Initialize validator for a specific feature directory.

        Args:
            feature_dir: Path to .specify/specs/<feature-id> directory
        """
        self.feature_dir = Path(feature_dir)
        self.objetivo_file = self.feature_dir / "objetivo.yaml"
        self.spec_file = self.feature_dir / "spec.md"
        self.plan_file = self.feature_dir / "plan.md"
        self.tasks_file = self.feature_dir / "tasks.md"

        # Load JSON Schema for objetivo.yaml
        schema_path = (
            Path(__file__).parent.parent.parent
            / ".specify/schemas/objetivo-schema.json"
        )
        if schema_path.exists():
            with open(schema_path) as f:
                self.objetivo_schema = json.load(f)
        else:
            log.warning(f"Schema not found: {schema_path}")
            self.objetivo_schema = None

    def validate_layer_transition(
        self, from_layer: str | Layer, to_layer: str | Layer
    ) -> ValidationResult:
        """
        Validate quality gates for layer transition.

        Args:
            from_layer: Source layer ("business", "product", "architecture")
            to_layer: Target layer ("product", "architecture", "implementation")

        Returns:
            ValidationResult with pass/fail status and issues
        """
        if isinstance(from_layer, str):
            from_layer = Layer(from_layer)
        if isinstance(to_layer, str):
            to_layer = Layer(to_layer)

        result = ValidationResult(layer_from=from_layer, layer_to=to_layer, passed=True)

        # Validate specific transition
        if from_layer == Layer.BUSINESS and to_layer == Layer.PRODUCT:
            self._validate_business_to_product(result)
        elif from_layer == Layer.PRODUCT and to_layer == Layer.ARCHITECTURE:
            self._validate_product_to_architecture(result)
        elif from_layer == Layer.ARCHITECTURE and to_layer == Layer.IMPLEMENTATION:
            self._validate_architecture_to_implementation(result)
        else:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=from_layer,
                    rule="invalid-transition",
                    message=f"Invalid layer transition: {from_layer.value} → {to_layer.value}",
                )
            )

        return result

    def _validate_business_to_product(self, result: ValidationResult) -> None:
        """
        Validate Layer 1 (Business) → Layer 2 (Product) transition.

        Quality gates:
        - ✅ objetivo.yaml exists and is valid YAML
        - ✅ JSON Schema validation passes
        - ✅ No placeholder tokens ([FEATURE_ID], [FEATURE_NAME], etc.)
        - ✅ >=1 metrica_sucesso defined
        - ✅ >=1 persona identified (recommended, warning if missing)
        - ✅ visao_alto_nivel <=3 sentences
        - ✅ jornadas_criticas have priorities (P1/P2/P3)
        """
        layer = Layer.BUSINESS

        # Check objetivo.yaml exists
        if not self.objetivo_file.exists():
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="objetivo-missing",
                    message=f"objetivo.yaml not found in {self.feature_dir}",
                    suggestion="Run: speckit.clarify Mode 1 to generate objetivo.yaml",
                )
            )
            return

        # Load and parse YAML
        if yaml is None:
            result.add_issue(  # type: ignore[unreachable]  # yaml opcional (fallback None)
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="yaml-module-missing",
                    message="PyYAML not installed. Cannot validate objetivo.yaml",
                    suggestion="Install with: uv pip install pyyaml jsonschema",
                )
            )
            return

        try:
            with open(self.objetivo_file) as f:
                objetivo_data = yaml.safe_load(f)
        except Exception as e:
            # Check if it's a YAML error
            error_type = type(e).__name__
            if (
                "YAML" in error_type
                or "Scanner" in error_type
                or "Parser" in error_type
            ):
                result.add_issue(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        layer=layer,
                        rule="objetivo-invalid-yaml",
                        message=f"Invalid YAML syntax: {e}",
                        file=str(self.objetivo_file),
                    )
                )
            else:
                result.add_issue(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        layer=layer,
                        rule="objetivo-file-error",
                        message=f"Error reading objetivo.yaml: {e}",
                        file=str(self.objetivo_file),
                    )
                )
            return

        # JSON Schema validation
        # Draft7Validator vira None quando jsonschema está ausente (fallback acima)
        if self.objetivo_schema and Draft7Validator:  # type: ignore[truthy-function]  # None sem jsonschema
            try:
                validate(instance=objetivo_data, schema=self.objetivo_schema)
            except ValidationError as e:
                result.add_issue(
                    ValidationIssue(
                        severity=Severity.ERROR,
                        layer=layer,
                        rule="objetivo-schema-violation",
                        message=f"Schema validation failed: {e.message}",
                        file=str(self.objetivo_file),
                        suggestion=(
                            f"Check field: {'.'.join(str(p) for p in e.path)}"
                            if e.path
                            else None
                        ),
                    )
                )

        # Check for placeholder tokens
        objetivo_text = self.objetivo_file.read_text()
        placeholders = re.findall(r"\[([A-Z_]+)\]", objetivo_text)
        if placeholders:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="objetivo-placeholders",
                    message=f"Placeholder tokens found: {', '.join(set(placeholders))}",
                    file=str(self.objetivo_file),
                    suggestion="Replace all [PLACEHOLDER] tokens with actual values",
                )
            )

        # Quality gate: >=1 metrica_sucesso
        metricas = (
            objetivo_data.get("negocio", {})
            .get("valor", {})
            .get("metricas_sucesso", [])
        )
        if not metricas:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="metricas-missing",
                    message="No success metrics defined (negocio.valor.metricas_sucesso is empty)",
                    file=str(self.objetivo_file),
                    suggestion="Add at least 1 measurable success metric (metric + target)",
                )
            )

        # Quality gate: >=1 persona (recommended)
        personas = objetivo_data.get("produto", {}).get("personas", [])
        if not personas:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="personas-missing",
                    message="No personas defined (produto.personas is empty)",
                    file=str(self.objetivo_file),
                    suggestion="Add at least 1 persona (name, needs, pain_points) for better product definition",
                )
            )

        # Quality gate: visao_alto_nivel <=3 sentences
        visao = objetivo_data.get("produto", {}).get("visao_alto_nivel", "")
        sentence_count = len([s for s in visao.split(".") if s.strip()])
        if sentence_count > 3:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="visao-too-long",
                    message=f"Product vision has {sentence_count} sentences (recommended: <=3)",
                    file=str(self.objetivo_file),
                    suggestion="Simplify product vision to 1-3 clear sentences (high-level WHAT, not HOW)",
                )
            )

        # Quality gate: jornadas_criticas have P1/P2/P3 priorities
        jornadas = objetivo_data.get("produto", {}).get("jornadas_criticas", [])
        jornadas_without_priority = [
            j for j in jornadas if j.get("priority") not in ["P1", "P2", "P3"]
        ]
        if jornadas_without_priority:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="jornadas-no-priority",
                    message=f"{len(jornadas_without_priority)} critical journeys missing P1/P2/P3 priority",
                    file=str(self.objetivo_file),
                    suggestion="All jornadas_criticas must have priority: P1 (MVP must-have), P2 (important), or P3 (nice-to-have)",
                )
            )

        # Info: Report P1 count (MVP scope)
        p1_jornadas = [j for j in jornadas if j.get("priority") == "P1"]
        if p1_jornadas:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.INFO,
                    layer=layer,
                    rule="mvp-scope",
                    message=f"MVP scope: {len(p1_jornadas)} P1 critical journeys",
                )
            )

    def _validate_product_to_architecture(self, result: ValidationResult) -> None:
        """
        Validate Layer 2 (Product) → Layer 3 (Architecture) transition.

        Quality gates:
        - ✅ spec.md exists
        - ✅ >=1 user story P1 defined
        - ✅ All user stories have acceptance criteria (Given/When/Then pattern)
        - ✅ Functional requirements numbered (FR-001, FR-002, ...)
        - ✅ spec.md references objetivo.yaml (Business Context section)
        """
        layer = Layer.PRODUCT

        # Check spec.md exists
        if not self.spec_file.exists():
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="spec-missing",
                    message=f"spec.md not found in {self.feature_dir}",
                    suggestion="Run: speckit.specify to generate spec.md from objetivo.yaml",
                )
            )
            return

        spec_text = self.spec_file.read_text()

        # Quality gate: Business Context section references objetivo.yaml
        if "Business Context" not in spec_text and "objetivo.yaml" not in spec_text:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="spec-no-business-context",
                    message="spec.md does not reference Business Context or objetivo.yaml",
                    file=str(self.spec_file),
                    suggestion="Add Business Context section that references objetivo.yaml (problema, valor, metricas)",
                )
            )

        # Quality gate: >=1 P1 user story
        # Pattern: **P1**: or ## User Story US-001 *(P1)*
        p1_stories = re.findall(r"\*\*P1\*\*:|US-\d{3}\s+\*\(P1\)\*", spec_text)
        if not p1_stories:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="spec-no-p1-stories",
                    message="No P1 (must-have) user stories found in spec.md",
                    file=str(self.spec_file),
                    suggestion="Add at least 1 P1 user story (MVP must-have functionality)",
                )
            )
        else:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.INFO,
                    layer=layer,
                    rule="mvp-stories",
                    message=f"Found {len(p1_stories)} P1 user stories",
                )
            )

        # Quality gate: Acceptance criteria (Given/When/Then)
        # Pattern: Given...When...Then or **Given:**...
        criteria_patterns = [
            r"Given\s+.+When\s+.+Then",
            r"\*\*Given:\*\*|\*\*When:\*\*|\*\*Then:\*\*",
        ]
        has_acceptance_criteria = any(
            re.search(pattern, spec_text, re.IGNORECASE | re.DOTALL)
            for pattern in criteria_patterns
        )

        if not has_acceptance_criteria:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="spec-no-acceptance-criteria",
                    message="No acceptance criteria found (Given/When/Then pattern missing)",
                    file=str(self.spec_file),
                    suggestion="Add acceptance criteria for user stories using Given/When/Then format",
                )
            )

        # Quality gate: Functional requirements numbered (FR-001, FR-002, ...)
        fr_requirements = re.findall(r"FR-\d{3}", spec_text)
        if not fr_requirements:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="spec-no-functional-requirements",
                    message="No numbered functional requirements found (FR-001 format)",
                    file=str(self.spec_file),
                    suggestion="Number functional requirements as FR-001, FR-002, ... for traceability",
                )
            )
        else:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.INFO,
                    layer=layer,
                    rule="functional-requirements-count",
                    message=f"Found {len(set(fr_requirements))} functional requirements",
                )
            )

    def _validate_architecture_to_implementation(
        self, result: ValidationResult
    ) -> None:
        """
        Validate Layer 3 (Architecture) → Layer 4 (Implementation) transition.

        Quality gates:
        - ✅ plan.md exists
        - ✅ >=1 ADR documented (for architectural features)
        - ✅ All ADRs have "Alternatives Considered" section
        - ✅ ADRs reference objetivo.yaml → decisoes_iniciais (if applicable)
        - ✅ Component design defined
        - ✅ Implementation strategy clear (steps, order, dependencies)
        """
        layer = Layer.ARCHITECTURE

        # Check plan.md exists
        if not self.plan_file.exists():
            result.add_issue(
                ValidationIssue(
                    severity=Severity.ERROR,
                    layer=layer,
                    rule="plan-missing",
                    message=f"plan.md not found in {self.feature_dir}",
                    suggestion="Run: speckit.plan to generate plan.md from spec.md",
                )
            )
            return

        plan_text = self.plan_file.read_text()

        # Quality gate: >=1 ADR (for architectural features)
        # Pattern: ### ADR-001: or ## ADR-001:
        adrs = re.findall(r"###?\s+ADR-\d{3}:", plan_text)
        if not adrs:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="plan-no-adrs",
                    message="No Architecture Decision Records (ADRs) found in plan.md",
                    file=str(self.plan_file),
                    suggestion="Document architectural decisions as ADRs (format: ADR-001: Decision Title). If not architectural, mark as 'Not Applicable'.",
                )
            )
        else:
            result.add_issue(
                ValidationIssue(
                    severity=Severity.INFO,
                    layer=layer,
                    rule="adrs-count",
                    message=f"Found {len(adrs)} Architecture Decision Records",
                )
            )

            # Quality gate: All ADRs have "Alternatives Considered"
            for adr_match in re.finditer(
                r"###?\s+(ADR-\d{3}:.*?)(?=###?\s+ADR-\d{3}:|$)", plan_text, re.DOTALL
            ):
                adr_content = adr_match.group(1)
                # adr_content (grupo 1 do finditer) sempre começa com ADR-NNN
                adr_id = cast(
                    re.Match[str], re.search(r"ADR-\d{3}", adr_content)
                ).group()

                if (
                    "Alternatives Considered" not in adr_content
                    and "alternatives" not in adr_content.lower()
                ):
                    result.add_issue(
                        ValidationIssue(
                            severity=Severity.WARNING,
                            layer=layer,
                            rule="adr-no-alternatives",
                            message=f"{adr_id} missing 'Alternatives Considered' section",
                            file=str(self.plan_file),
                            suggestion="Document alternatives considered (even if only 1 option was viable)",
                        )
                    )

        # Quality gate: Component design section exists
        if "Component" not in plan_text and "component" not in plan_text.lower():
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="plan-no-component-design",
                    message="No component design section found in plan.md",
                    file=str(self.plan_file),
                    suggestion="Add Component Design section (modules, interfaces, data flow)",
                )
            )

        # Quality gate: Implementation strategy section exists
        # Quality gate: Implementation strategy section exists
        if (
            "Implementation" not in plan_text
            and "implementation" not in plan_text.lower()
        ):
            result.add_issue(
                ValidationIssue(
                    severity=Severity.WARNING,
                    layer=layer,
                    rule="plan-no-implementation-strategy",
                    message="No implementation strategy section found in plan.md",
                    file=str(self.plan_file),
                    suggestion="Add Implementation Strategy section (steps, order, dependencies, risks)",
                )
            )

        # Quality gate: References to objetivo.yaml decisoes_iniciais
        if self.objetivo_file.exists() and yaml is not None:
            try:
                with open(self.objetivo_file) as f:
                    objetivo_data = yaml.safe_load(f)

                decisoes_iniciais = objetivo_data.get("decisoes_iniciais", [])
            except Exception:
                # If we can't load objetivo.yaml, skip this check
                decisoes_iniciais = []

            if decisoes_iniciais:
                # Check if ADRs reference any decisoes_iniciais
                decisao_ids = [d.get("id") for d in decisoes_iniciais if d.get("id")]
                referenced_decisoes = [
                    d_id for d_id in decisao_ids if d_id in plan_text
                ]

                if not referenced_decisoes and len(decisoes_iniciais) > 0:
                    result.add_issue(
                        ValidationIssue(
                            severity=Severity.INFO,
                            layer=layer,
                            rule="plan-no-decisoes-reference",
                            message=f"objetivo.yaml has {len(decisoes_iniciais)} initial decisions, but plan.md doesn't reference them",
                            file=str(self.plan_file),
                            suggestion=f"Consider referencing decision IDs: {', '.join(decisao_ids[:3])}",
                        )
                    )


def validate_feature(
    feature_dir: Path | str, from_layer: str, to_layer: str, verbose: bool = False
) -> tuple[bool, ValidationResult]:
    """
    Convenience function to validate a feature transition.

    Args:
        feature_dir: Path to .specify/specs/<feature-id>
        from_layer: Source layer name ("business", "product", "architecture")
        to_layer: Target layer name ("product", "architecture", "implementation")
        verbose: Print detailed report

    Returns:
        Tuple of (passed: bool, result: ValidationResult)
    """
    validator = SpecValidator(feature_dir)
    result = validator.validate_layer_transition(from_layer, to_layer)

    if verbose:
        print(result.detailed_report())
    else:
        print(result.summary())

    return result.passed, result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print(
            "Usage: python -m scripts.lib.spec_validate <feature-dir> <from-layer> <to-layer> [--verbose]"
        )
        print(
            "Example: python -m scripts.lib.spec_validate .specify/specs/IMP-53 business product --verbose"
        )
        sys.exit(1)

    feature_dir = sys.argv[1]
    from_layer = sys.argv[2]
    to_layer = sys.argv[3]
    verbose = "--verbose" in sys.argv

    passed, result = validate_feature(
        feature_dir, from_layer, to_layer, verbose=verbose
    )
    sys.exit(0 if passed else 1)
