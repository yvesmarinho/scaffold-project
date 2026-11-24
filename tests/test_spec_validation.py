#!/usr/bin/env python3
"""
Tests for SpecKit Quality Gates Validation Engine

Tests cover:
- Layer 1 (Business) → Layer 2 (Product) validation
- Layer 2 (Product) → Layer 3 (Architecture) validation
- Layer 3 (Architecture) → Layer 4 (Implementation) validation
- JSON Schema validation for objetivo.yaml
- Quality gates enforcement
- Error handling and suggestions
"""

from textwrap import dedent

import pytest
import yaml

from scripts.lib.spec_validate import (
    Layer,
    Severity,
    SpecValidator,
    ValidationIssue,
    ValidationResult,
    validate_feature,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_feature_dir(tmp_path):
    """Create temporary feature directory structure"""
    feature_dir = tmp_path / ".specify" / "specs" / "TEST-001"
    feature_dir.mkdir(parents=True)
    return feature_dir


@pytest.fixture
def minimal_objetivo_yaml():
    """Minimal valid objetivo.yaml content"""
    return {
        "feature": {"id": "TEST-001", "name": "Test Feature", "created": "2026-04-14"},
        "negocio": {
            "problema": {
                "descricao": "Test problem description with enough length to pass validation",
                "impacto_atual": "Impact if not solved with sufficient detail",
                "stakeholders": ["Developers", "Product Managers"],
            },
            "valor": {
                "objetivos_estrategicos": ["Objective 1"],
                "metricas_sucesso": [{"metric": "Test metric", "target": "100%"}],
            },
        },
        "produto": {
            "visao_alto_nivel": "High level product vision in one sentence.",
            "personas": [
                {
                    "name": "Developer",
                    "needs": "Needs faster development workflow",
                    "pain_points": "Current workflow is slow and error-prone",
                }
            ],
            "jornadas_criticas": [
                {
                    "journey": "Complete feature implementation",
                    "priority": "P1",
                    "value": "Enables core functionality",
                }
            ],
        },
        "metadata": {"owner": "Test Owner", "team": "Test Team"},
    }


@pytest.fixture
def minimal_spec_md():
    """Minimal valid spec.md content"""
    return dedent("""
        # Feature Specification: Test Feature

        ## Business Context

        References objetivo.yaml for business context.

        ## User Scenarios

        ### User Story US-001 *(P1)*

        As a developer, I want to test validation.

        **Acceptance Criteria**:
        - **Given:** Initial state
        - **When:** Action occurs
        - **Then:** Expected outcome

        ## Functional Requirements

        - **FR-001**: First functional requirement
        - **FR-002**: Second functional requirement
    """)


@pytest.fixture
def minimal_plan_md():
    """Minimal valid plan.md content"""
    return dedent("""
        # Implementation Plan: Test Feature

        ## Architecture Decision Records

        ### ADR-001: Test Decision

        **Status**: Accepted
        **Date**: 2026-04-14

        **Context**: Need to make architectural decision
        **Decision**: Chose option A
        **Rationale**: Best trade-off

        **Consequences**:
        - ✅ Positive: Fast implementation
        - ⚠️ Negative: Limited scalability

        **Alternatives Considered**:
        1. **Option B**: Rejected due to complexity

        ## Component Design

        Components described here.

        ## Implementation Strategy

        Steps, order, dependencies described.
    """)


# ============================================================================
# Test Layer 1 (Business) → Layer 2 (Product) Validation
# ============================================================================


class TestBusinessToProduct:
    """Test L1→L2 validation (objetivo.yaml → spec.md)"""

    def test_missing_objetivo_yaml(self, temp_feature_dir):
        """Should fail if objetivo.yaml doesn't exist"""
        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert not result.passed
        assert len(result.errors) >= 1
        assert any("objetivo.yaml not found" in e.message for e in result.errors)
        assert any("speckit.clarify" in e.suggestion for e in result.errors)

    def test_invalid_yaml_syntax(self, temp_feature_dir):
        """Should fail if objetivo.yaml has invalid YAML syntax"""
        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text("invalid: yaml: syntax: [unclosed")

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert not result.passed
        assert any("Invalid YAML syntax" in e.message for e in result.errors)

    def test_placeholder_tokens_present(self, temp_feature_dir, minimal_objetivo_yaml):
        """Should fail if [PLACEHOLDER] tokens are present"""
        minimal_objetivo_yaml["feature"]["name"] = "[FEATURE_NAME]"
        minimal_objetivo_yaml["negocio"]["problema"]["descricao"] = "[BUSINESS_PROBLEM]"

        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert not result.passed
        assert any("Placeholder tokens found" in e.message for e in result.errors)
        assert any("FEATURE_NAME" in e.message for e in result.errors)

    def test_no_success_metrics(self, temp_feature_dir, minimal_objetivo_yaml):
        """Should fail if no success metrics defined"""
        minimal_objetivo_yaml["negocio"]["valor"]["metricas_sucesso"] = []

        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert not result.passed
        assert any("No success metrics" in e.message for e in result.errors)

    def test_no_personas_warning(self, temp_feature_dir, minimal_objetivo_yaml):
        """Should warn if no personas defined"""
        minimal_objetivo_yaml["produto"]["personas"] = []

        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        # Should pass (warning, not error) but have warning
        assert result.passed
        assert len(result.warnings) >= 1
        assert any("No personas" in w.message for w in result.warnings)

    def test_vision_too_long(self, temp_feature_dir, minimal_objetivo_yaml):
        """Should warn if product vision > 3 sentences"""
        minimal_objetivo_yaml["produto"][
            "visao_alto_nivel"
        ] = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."

        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert result.passed  # Warning, not blocking
        assert any("vision has" in w.message.lower() for w in result.warnings)

    def test_journeys_missing_priority(self, temp_feature_dir, minimal_objetivo_yaml):
        """Should fail if critical journeys missing P1/P2/P3 priority"""
        minimal_objetivo_yaml["produto"]["jornadas_criticas"][0]["priority"] = "HIGH"

        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert not result.passed
        assert any("priority" in e.message.lower() for e in result.errors)

    def test_valid_objetivo_passes(self, temp_feature_dir, minimal_objetivo_yaml):
        """Should pass with minimal valid objetivo.yaml"""
        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert result.passed
        assert len(result.errors) == 0
        # May have warnings (personas recommended, etc.)

    def test_mvp_scope_reported(self, temp_feature_dir, minimal_objetivo_yaml):
        """Should report MVP scope (P1 journey count) as info"""
        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("business", "product")

        assert any("MVP scope" in i.message for i in result.infos)


# ============================================================================
# Test Layer 2 (Product) → Layer 3 (Architecture) Validation
# ============================================================================


class TestProductToArchitecture:
    """Test L2→L3 validation (spec.md → plan.md)"""

    def test_missing_spec_md(self, temp_feature_dir):
        """Should fail if spec.md doesn't exist"""
        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        assert not result.passed
        assert any("spec.md not found" in e.message for e in result.errors)
        assert any("speckit.specify" in e.suggestion for e in result.errors)

    def test_no_business_context_warning(self, temp_feature_dir):
        """Should warn if spec.md doesn't reference objetivo.yaml"""
        spec_file = temp_feature_dir / "spec.md"
        # Include P1 story to avoid error, test only warning
        spec_file.write_text(dedent("""
            # Feature Spec

            No business context here.

            ## User Stories

            **P1**: As a user, I want something.
        """))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        # Should pass (warning only) but warn about missing context
        assert result.passed
        assert len(result.warnings) >= 1
        assert any("Business Context" in w.message for w in result.warnings)

    def test_no_p1_stories(self, temp_feature_dir):
        """Should fail if no P1 user stories found"""
        spec_file = temp_feature_dir / "spec.md"
        spec_file.write_text(dedent("""
            # Feature Spec

            ## User Stories

            ### US-001 *(P2)*
            As a user, I want something.
        """))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        assert not result.passed
        assert any("No P1" in e.message for e in result.errors)

    def test_no_acceptance_criteria_warning(self, temp_feature_dir):
        """Should warn if no Given/When/Then acceptance criteria"""
        spec_file = temp_feature_dir / "spec.md"
        spec_file.write_text(dedent("""
            # Feature Spec

            **P1**: As a user, I want something.

            Requirements: Must do X, Y, Z.
        """))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        assert result.passed  # Warning, not blocking
        assert any("acceptance criteria" in w.message.lower() for w in result.warnings)

    def test_no_functional_requirements_warning(self, temp_feature_dir):
        """Should warn if no FR-001 numbered requirements"""
        spec_file = temp_feature_dir / "spec.md"
        spec_file.write_text(dedent("""
            # Feature Spec

            **P1**: As a user, I want something.

            **Given:** State
            **When:** Action
            **Then:** Outcome

            Requirements:
            - Must do X
            - Must do Y
        """))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        assert result.passed
        assert any(
            "functional requirement" in w.message.lower() for w in result.warnings
        )

    def test_valid_spec_passes(self, temp_feature_dir, minimal_spec_md):
        """Should pass with valid spec.md"""
        spec_file = temp_feature_dir / "spec.md"
        spec_file.write_text(minimal_spec_md)

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        assert result.passed
        assert len(result.errors) == 0

    def test_reports_p1_story_count(self, temp_feature_dir, minimal_spec_md):
        """Should report P1 story count as info"""
        spec_file = temp_feature_dir / "spec.md"
        spec_file.write_text(minimal_spec_md)

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        assert any("P1 user stories" in i.message for i in result.infos)

    def test_reports_fr_count(self, temp_feature_dir, minimal_spec_md):
        """Should report functional requirements count as info"""
        spec_file = temp_feature_dir / "spec.md"
        spec_file.write_text(minimal_spec_md)

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("product", "architecture")

        assert any("functional requirement" in i.message.lower() for i in result.infos)


# ============================================================================
# Test Layer 3 (Architecture) → Layer 4 (Implementation) Validation
# ============================================================================


class TestArchitectureToImplementation:
    """Test L3→L4 validation (plan.md → tasks.md)"""

    def test_missing_plan_md(self, temp_feature_dir):
        """Should fail if plan.md doesn't exist"""
        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        assert not result.passed
        assert any("plan.md not found" in e.message for e in result.errors)
        assert any("speckit.plan" in e.suggestion for e in result.errors)

    def test_no_adrs_warning(self, temp_feature_dir):
        """Should warn if no ADRs found"""
        plan_file = temp_feature_dir / "plan.md"
        plan_file.write_text("# Implementation Plan\n\nNo ADRs here.")

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        assert result.passed  # Warning, not blocking
        assert any(
            "No Architecture Decision Records" in w.message for w in result.warnings
        )

    def test_adr_missing_alternatives(self, temp_feature_dir):
        """Should warn if ADR missing 'Alternatives Considered'"""
        plan_file = temp_feature_dir / "plan.md"
        plan_file.write_text(dedent("""
            # Plan

            ### ADR-001: Test Decision

            **Status**: Accepted
            **Decision**: We chose option A
            **Rationale**: It's the best
        """))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        assert result.passed
        assert any(
            "ADR-001" in w.message and "Alternatives" in w.message
            for w in result.warnings
        )

    def test_no_component_design_warning(self, temp_feature_dir):
        """Should warn if no component design section"""
        plan_file = temp_feature_dir / "plan.md"
        plan_file.write_text(dedent("""
            # Plan

            ### ADR-001: Test

            **Alternatives Considered**: Option B

            Implementation steps here.
        """))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        assert result.passed
        assert any("component design" in w.message.lower() for w in result.warnings)

    def test_no_implementation_strategy_warning(self, temp_feature_dir):
        """Should warn if no implementation strategy section"""
        plan_file = temp_feature_dir / "plan.md"
        plan_file.write_text(dedent("""
            # Plan

            ### ADR-001: Test
            **Alternatives Considered**: Option B

            ## Component Design
            Components here.
        """))

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        assert result.passed
        assert any(
            "implementation strategy" in w.message.lower() for w in result.warnings
        )

    def test_valid_plan_passes(self, temp_feature_dir, minimal_plan_md):
        """Should pass with valid plan.md"""
        plan_file = temp_feature_dir / "plan.md"
        plan_file.write_text(minimal_plan_md)

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        assert result.passed
        assert len(result.errors) == 0

    def test_reports_adr_count(self, temp_feature_dir, minimal_plan_md):
        """Should report ADR count as info"""
        plan_file = temp_feature_dir / "plan.md"
        plan_file.write_text(minimal_plan_md)

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        assert any("Architecture Decision Records" in i.message for i in result.infos)

    def test_references_decisoes_iniciais(
        self, temp_feature_dir, minimal_objetivo_yaml, minimal_plan_md
    ):
        """Should check if plan.md references objetivo.yaml decisoes_iniciais"""
        # Add decisoes_iniciais to objetivo.yaml
        minimal_objetivo_yaml["decisoes_iniciais"] = [
            {"id": "D-01", "question": "Test question", "decision": "Test decision"}
        ]
        objetivo_file = temp_feature_dir / "objetivo.yaml"
        objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

        # Plan WITHOUT reference to D-01
        plan_file = temp_feature_dir / "plan.md"
        plan_file.write_text(minimal_plan_md)

        validator = SpecValidator(temp_feature_dir)
        result = validator.validate_layer_transition("architecture", "implementation")

        # Should be info (not error or warning)
        assert any("doesn't reference" in i.message for i in result.infos)


# ============================================================================
# Test Validation Result Output
# ============================================================================


class TestValidationResult:
    """Test ValidationResult formatting and reporting"""

    def test_summary_passed(self):
        """Should format passed summary correctly"""
        result = ValidationResult(
            layer_from=Layer.BUSINESS, layer_to=Layer.PRODUCT, passed=True
        )

        summary = result.summary()
        assert "✅ PASSED" in summary
        assert "business → product" in summary

    def test_summary_failed(self):
        """Should format failed summary correctly"""
        result = ValidationResult(
            layer_from=Layer.BUSINESS, layer_to=Layer.PRODUCT, passed=False
        )
        result.add_issue(
            ValidationIssue(
                severity=Severity.ERROR,
                layer=Layer.BUSINESS,
                rule="test-rule",
                message="Test error",
            )
        )

        summary = result.summary()
        assert "❌ FAILED" in summary
        assert "1 errors" in summary

    def test_detailed_report_includes_all_sections(self):
        """Should include errors, warnings, and info in detailed report"""
        result = ValidationResult(
            layer_from=Layer.BUSINESS, layer_to=Layer.PRODUCT, passed=False
        )

        result.add_issue(
            ValidationIssue(
                severity=Severity.ERROR,
                layer=Layer.BUSINESS,
                rule="error-rule",
                message="Error message",
            )
        )
        result.add_issue(
            ValidationIssue(
                severity=Severity.WARNING,
                layer=Layer.BUSINESS,
                rule="warning-rule",
                message="Warning message",
            )
        )
        result.add_issue(
            ValidationIssue(
                severity=Severity.INFO,
                layer=Layer.BUSINESS,
                rule="info-rule",
                message="Info message",
            )
        )

        report = result.detailed_report()
        assert "ERRORS (blocking)" in report
        assert "WARNINGS (should fix)" in report
        assert "INFO (recommendations)" in report
        assert "Error message" in report
        assert "Warning message" in report
        assert "Info message" in report


# ============================================================================
# Test Validation Convenience Function
# ============================================================================


def test_validate_feature_convenience(temp_feature_dir, minimal_objetivo_yaml):
    """Test validate_feature() convenience function"""
    objetivo_file = temp_feature_dir / "objetivo.yaml"
    objetivo_file.write_text(yaml.dump(minimal_objetivo_yaml))

    passed, result = validate_feature(
        temp_feature_dir, "business", "product", verbose=False
    )

    assert passed is True
    assert isinstance(result, ValidationResult)
    assert result.passed


# ============================================================================
# Test Invalid Transitions
# ============================================================================


def test_invalid_layer_transition(temp_feature_dir):
    """Should error on invalid layer transition"""
    validator = SpecValidator(temp_feature_dir)
    result = validator.validate_layer_transition("business", "implementation")

    assert not result.passed
    assert any("Invalid layer transition" in e.message for e in result.errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
