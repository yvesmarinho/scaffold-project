"""
Test BUG-05 fix: Wizard objetivo-init must replace placeholders with user answers

This test verifies that the wizard correctly:
1. Collects user answers
2. Maps answers to correct placeholders
3. Expands multiline answers to numbered placeholders
4. Generates valid YAML without {{PLACEHOLDER}} remnants
"""

import sys
from pathlib import Path

# Add parent directory to path to import lib modules
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.objetivo_wizard import ObjetivoWizard, WizardAnswers


def test_simple_placeholder_replacement():
    """Test that simple placeholders are replaced correctly"""
    wizard = ObjetivoWizard()

    # Create test answers
    answers = WizardAnswers(
        project_name="test-project",
        project_title="Test Project",
        project_type="backend-api",
        project_domain="programming",
        project_language="python",
        created_by="test-user",
        answers={
            "{{DESCRIPTION}}": "This is a test project for validating placeholder replacement",
            "{{RESPONSE}}": "Python 3.12+ with FastAPI and PostgreSQL",
            "{{DOCSTYLE}}": "Google Python Style Guide",
        },
    )

    # Render template
    content = wizard._render_template(answers)

    # Verify replacements
    assert "test-project" in content, "PROJECT_NAME should be replaced"
    assert "This is a test project" in content, "DESCRIPTION should be replaced"
    assert "Python 3.12+" in content, "RESPONSE should be replaced"
    assert "Google Python Style Guide" in content, "DOCSTYLE should be replaced"

    # Verify NO unreplaced placeholders remain
    assert "{{DESCRIPTION}}" not in content, "DESCRIPTION placeholder should be gone"
    assert "{{RESPONSE}}" not in content, "RESPONSE placeholder should be gone"
    assert "{{DOCSTYLE}}" not in content, "DOCSTYLE placeholder should be gone"

    print("✅ Simple placeholder replacement works")


def test_multiline_placeholder_expansion():
    """Test that multiline answers expand to numbered placeholders"""
    wizard = ObjetivoWizard()

    # Create test answers with multiline values
    answers = WizardAnswers(
        project_name="test-project",
        answers={
            "{{FEATURE}}": "Feature 1: User authentication\nFeature 2: Data processing\nFeature 3: API endpoints",
            "{{EXPECTED_OUTCOME}}": "100% test coverage\nZero security vulnerabilities\n<200ms response time",
            "{{INFRASTRUCTURE}}": "PostgreSQL database\nDocker containers\nNginx reverse proxy",
        },
    )

    # Render template
    content = wizard._render_template(answers)

    # Verify expansions (should create FEATURE_1, FEATURE_2, FEATURE_3, etc)
    assert "Feature 1: User authentication" in content, "FEATURE_1 should be expanded"
    assert "Feature 2: Data processing" in content, "FEATURE_2 should be expanded"
    assert "Feature 3: API endpoints" in content, "FEATURE_3 should be expanded"

    assert "100% test coverage" in content, "EXPECTED_OUTCOME_1 should be expanded"
    assert (
        "Zero security vulnerabilities" in content
    ), "EXPECTED_OUTCOME_2 should be expanded"

    assert "PostgreSQL database" in content, "INFRASTRUCTURE_1 should be expanded"
    assert "Docker containers" in content, "INFRASTRUCTURE_2 should be expanded"

    # Verify NO unexpanded base placeholders remain
    assert "{{FEATURE}}" not in content, "Base FEATURE placeholder should be gone"
    assert (
        "{{EXPECTED_OUTCOME}}" not in content
    ), "Base EXPECTED_OUTCOME placeholder should be gone"

    print("✅ Multiline placeholder expansion works")


def test_default_placeholders():
    """Test that placeholders without questions get default values"""
    wizard = ObjetivoWizard()

    # Create minimal answers
    answers = WizardAnswers(project_name="test-project", answers={})

    # Render template
    content = wizard._render_template(answers)

    # Verify defaults are applied
    assert (
        "Workflow baseado em objetivo.yaml" in content
    ), "WORKFLOW_OBJETIVO should have default"
    assert "Geração automática" in content, "WORKFLOW_SPECIFY should have default"

    print("✅ Default placeholder values work")


def test_no_unreplaced_placeholders():
    """Test that the final output has no {{PLACEHOLDER}} remnants"""
    wizard = ObjetivoWizard()

    # Create complete answers
    answers = WizardAnswers(
        project_name="test-project",
        project_title="Test",
        project_type="backend-api",
        project_domain="programming",
        project_language="python",
        created_by="test",
        answers={
            "{{DESCRIPTION}}": "Test description",
            "{{RESPONSE}}": "Python code",
            "{{DOCSTYLE}}": "Google",
            "{{FEATURE}}": "Feature 1\nFeature 2\nFeature 3",
            "{{EXPECTED_OUTCOME}}": "Outcome 1\nOutcome 2\nOutcome 3",
        },
    )

    # Render template
    content = wizard._render_template(answers)

    # Check for ANY unreplaced placeholders (regex pattern {{WORD}})
    import re

    unreplaced = re.findall(r"\{\{[A-Z_0-9]+\}\}", content)

    if unreplaced:
        print(f"❌ Found unreplaced placeholders: {unreplaced}")
        print("\n--- Generated content (first 1000 chars) ---")
        print(content[:1000])
        raise AssertionError(f"Template has unreplaced placeholders: {unreplaced}")

    print("✅ No unreplaced placeholders in output")


if __name__ == "__main__":
    print("\n=== Testing BUG-05 Fix: Objetivo Wizard Placeholder Replacement ===\n")

    test_simple_placeholder_replacement()
    test_multiline_placeholder_expansion()
    test_default_placeholders()
    test_no_unreplaced_placeholders()

    print("\n🎉 All tests passed! BUG-05 fix is working correctly.\n")
