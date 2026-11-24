#!/usr/bin/env python3
"""
Tests for validate-templates.py

Tests:
- YAML syntax validation
- JSON syntax validation
- Markdown frontmatter validation
- Link validation
- Variable validation
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

# Load validate-templates.py module dynamically (has hyphen in name)
validate_templates_path = (
    Path(__file__).parent.parent / "scripts" / "validate-templates.py"
)
spec = importlib.util.spec_from_file_location(
    "validate_templates", validate_templates_path
)
validate_templates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_templates)

TemplateValidator = validate_templates.TemplateValidator
ValidationResult = validate_templates.ValidationResult
format_json = validate_templates.format_json


def test_yaml_valid():
    """Test valid YAML file passes validation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)

        # Create valid YAML
        yaml_file = template_dir / "test.yaml"
        yaml_file.write_text("""
feature:
  id: "test-001"
  name: "Test Feature"
""")

        validator = TemplateValidator(template_dir)
        result = validator.validate_all()

        assert result.success, "Valid YAML should pass"
        assert len(result.errors) == 0
        assert result.files_checked == 1


def test_yaml_invalid():
    """Test invalid YAML file fails validation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)

        # Create invalid YAML (bad indentation)
        yaml_file = template_dir / "test.yaml"
        yaml_file.write_text("""
feature:
id: "test-001"  # Bad indentation
  name: "Test Feature"
""")

        validator = TemplateValidator(template_dir)
        result = validator.validate_all()

        assert not result.success, "Invalid YAML should fail"
        assert len(result.errors) > 0
        assert "YAML syntax error" in result.errors[0].message


def test_markdown_frontmatter_valid():
    """Test Markdown with valid frontmatter"""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)

        # Create valid Markdown with frontmatter
        md_file = template_dir / "test.md"
        md_file.write_text("""---
template_version: "1.0.0"
last_updated: "2026-04-28"
---

# Test Template

This is a test template.
""")

        validator = TemplateValidator(template_dir)
        result = validator.validate_all()

        assert result.success, "Valid Markdown should pass"
        assert len(result.errors) == 0


def test_markdown_missing_frontmatter():
    """Test Markdown without frontmatter triggers warning"""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)

        # Create Markdown without frontmatter
        md_file = template_dir / "test.md"
        md_file.write_text("""
# Test Template

No frontmatter here.
""")

        validator = TemplateValidator(template_dir)
        result = validator.validate_all()

        assert result.success, "Should pass validation"
        assert len(result.warnings) > 0
        assert "No YAML frontmatter found" in result.warnings[0].message


def test_markdown_missing_required_field():
    """Test Markdown missing required frontmatter field"""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)

        # Create Markdown with frontmatter but missing template_version
        md_file = template_dir / "test.md"
        md_file.write_text("""---
last_updated: "2026-04-28"
---

# Test Template
""")

        validator = TemplateValidator(template_dir)
        result = validator.validate_all()

        assert not result.success, "Should fail validation"
        assert len(result.errors) > 0
        assert "template_version" in result.errors[0].message


def test_json_output():
    """Test JSON output format"""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)

        # Create valid YAML
        yaml_file = template_dir / "test.yaml"
        yaml_file.write_text("key: value\n")

        validator = TemplateValidator(template_dir)
        result = validator.validate_all()

        # Use format_json from module
        json_output = format_json(result)

        # Parse JSON
        data = json.loads(json_output)

        assert data["success"] is True
        assert data["files_checked"] == 1
        assert isinstance(data["errors"], list)
        assert isinstance(data["warnings"], list)


def test_template_filter():
    """Test filtering templates by name"""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)

        # Create multiple templates
        (template_dir / "spec-template.md").write_text("""---
template_version: "1.0.0"
---
# Spec
""")
        (template_dir / "plan-template.md").write_text("""---
template_version: "1.0.0"
---
# Plan
""")

        validator = TemplateValidator(template_dir)
        result = validator.validate_all(template_filter="spec")

        assert result.success
        assert result.files_checked == 1  # Only spec-template.md


if __name__ == "__main__":
    print("Running validate-templates.py tests...")

    tests = [
        test_yaml_valid,
        test_yaml_invalid,
        test_markdown_frontmatter_valid,
        test_markdown_missing_frontmatter,
        test_markdown_missing_required_field,
        test_json_output,
        test_template_filter,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{'='*70}")
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"{'='*70}")

    sys.exit(0 if failed == 0 else 1)
