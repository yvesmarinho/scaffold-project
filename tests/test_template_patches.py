"""
Tests for template patch system (IMP-65 Phase 4.2).

Tests cover:
- Patch metadata parsing and validation
- Patch operation parsing
- Patch application (INSERT_AFTER, INSERT_BEFORE, REPLACE, DELETE)
- Multiple patch application
- Conflict detection
- Error handling
"""

from pathlib import Path

import pytest

from scripts.lib.template_patches import (
    Patch,
    PatchApplicationError,
    PatchConflictError,
    PatchMetadata,
    PatchNotFoundError,
    PatchOperation,
    PatchOperationType,
    PatchValidationError,
    apply_patch,
    apply_patch_operation,
    apply_patches,
    list_patches,
    load_patch,
    parse_patch_frontmatter,
    parse_patch_operations,
    validate_patch_file,
)

# Test fixtures


@pytest.fixture
def temp_patches_dir(tmp_path):
    """Create temporary patches directory."""
    patches_dir = tmp_path / "patches"
    patches_dir.mkdir()
    return patches_dir


@pytest.fixture
def sample_patch_content():
    """Sample patch content with valid frontmatter and operations."""
    return """---
patch_name: "add-security-review"
patch_version: "1.0.0"
target_template: "spec-template"
target_block: "user-scenarios"
target_version: "^2.0.0"
created: "2026-04-15"
description: "Add security review checklist"
author: "test@example.com"
---

@@ After: ## User Scenarios @@
+ ## Security Review Checklist
+
+ - [ ] Input validation
+ - [ ] Authentication checks
@@ END @@
"""


@pytest.fixture
def sample_template():
    """Sample template content for testing patches."""
    return """# Feature Specification

## User Scenarios

Story 1: User logs in
Story 2: User creates account

## Requirements

FR-001: System must authenticate users
"""


# Tests: parse_patch_frontmatter


def test_parse_patch_frontmatter_valid():
    """Test parsing valid patch frontmatter."""
    content = """---
patch_name: "test-patch"
patch_version: "1.0.0"
---

@@ After: Test @@
+ Content
@@ END @@
"""
    metadata, body = parse_patch_frontmatter(content)

    assert metadata is not None
    assert metadata["patch_name"] == "test-patch"
    assert "@@ After" in body


def test_parse_patch_frontmatter_no_frontmatter():
    """Test parsing patch without frontmatter."""
    content = "No frontmatter here"

    metadata, body = parse_patch_frontmatter(content)

    assert metadata is None
    assert body == content


def test_parse_patch_frontmatter_invalid_yaml():
    """Test parsing invalid YAML in frontmatter."""
    content = """---
invalid: yaml: broken:
---

Body
"""

    with pytest.raises(PatchValidationError):
        parse_patch_frontmatter(content)


# Tests: PatchMetadata


def test_patch_metadata_from_dict():
    """Test creating PatchMetadata from dict."""
    data = {
        "patch_name": "test-patch",
        "patch_version": "1.0.0",
        "target_template": "spec-template",
        "target_block": "user-scenarios",
        "target_version": "^2.0.0",
        "created": "2026-04-15",
        "description": "Test patch",
        "author": "test@example.com",
    }

    meta = PatchMetadata.from_dict(data)

    assert meta.patch_name == "test-patch"
    assert meta.patch_version == "1.0.0"
    assert meta.target_template == "spec-template"


def test_patch_metadata_validate_valid():
    """Test validation of valid patch metadata."""
    meta = PatchMetadata(
        patch_name="test-patch",
        patch_version="1.0.0",
        target_template="spec-template",
        target_block="user-scenarios",
        target_version="^2.0.0",
        created="2026-04-15",
        description="Test patch",
        author="test@example.com",
    )

    errors = meta.validate()
    assert len(errors) == 0


def test_patch_metadata_validate_missing_name():
    """Test validation fails for missing patch_name."""
    meta = PatchMetadata(
        patch_name="",
        patch_version="1.0.0",
        target_template="spec-template",
        target_block=None,
        target_version=None,
        created="2026-04-15",
        description="Test",
        author=None,
    )

    errors = meta.validate()
    assert any("Missing patch_name" in e for e in errors)


def test_patch_metadata_validate_invalid_version():
    """Test validation fails for invalid version format."""
    meta = PatchMetadata(
        patch_name="test-patch",
        patch_version="v1.0",  # Invalid
        target_template="spec-template",
        target_block=None,
        target_version=None,
        created="2026-04-15",
        description="Test",
        author=None,
    )

    errors = meta.validate()
    assert any("Invalid patch_version" in e for e in errors)


def test_patch_metadata_repr():
    """Test __repr__ of PatchMetadata."""
    meta = PatchMetadata(
        patch_name="test",
        patch_version="1.0.0",
        target_template="spec-template",
        target_block=None,
        target_version=None,
        created="2026-04-15",
        description="Test",
        author=None,
    )

    repr_str = repr(meta)
    assert "test" in repr_str
    assert "1.0.0" in repr_str
    assert "spec-template" in repr_str


# Tests: parse_patch_operations


def test_parse_patch_operations_insert_after():
    """Test parsing INSERT_AFTER operation."""
    body = """
@@ After: ## Section @@
+ New content here
+ Second line
@@ END @@
"""

    operations = parse_patch_operations(body)

    assert len(operations) == 1
    assert operations[0].operation_type == PatchOperationType.INSERT_AFTER
    assert operations[0].anchor == "## Section"
    assert "New content here" in operations[0].content


def test_parse_patch_operations_insert_before():
    """Test parsing INSERT_BEFORE operation."""
    body = """
@@ Before: ## Section @@
+ New content
@@ END @@
"""

    operations = parse_patch_operations(body)

    assert len(operations) == 1
    assert operations[0].operation_type == PatchOperationType.INSERT_BEFORE


def test_parse_patch_operations_replace():
    """Test parsing REPLACE operation."""
    body = """
@@ Replace: Old text @@
+ New text
@@ END @@
"""

    operations = parse_patch_operations(body)

    assert len(operations) == 1
    assert operations[0].operation_type == PatchOperationType.REPLACE


def test_parse_patch_operations_delete():
    """Test parsing DELETE operation."""
    body = """
@@ Delete: Line to remove @@
@@ END @@
"""

    operations = parse_patch_operations(body)

    assert len(operations) == 1
    assert operations[0].operation_type == PatchOperationType.DELETE


def test_parse_patch_operations_multiple():
    """Test parsing multiple operations."""
    body = """
@@ After: Section 1 @@
+ Content 1
@@ END @@

@@ After: Section 2 @@
+ Content 2
@@ END @@
"""

    operations = parse_patch_operations(body)

    assert len(operations) == 2
    assert operations[0].anchor == "Section 1"
    assert operations[1].anchor == "Section 2"


def test_parse_patch_operations_no_operations():
    """Test parsing fails when no operations found."""
    body = "Just plain text, no operations"

    with pytest.raises(PatchValidationError, match="No patch operations found"):
        parse_patch_operations(body)


def test_parse_patch_operations_invalid_type():
    """Test parsing fails for invalid operation type."""
    body = """
@@ InvalidOp: Test @@
+ Content
@@ END @@
"""

    with pytest.raises(PatchValidationError, match="Invalid operation type"):
        parse_patch_operations(body)


# Tests: load_patch


def test_load_patch_success(temp_patches_dir, sample_patch_content):
    """Test loading a valid patch file."""
    patch_file = temp_patches_dir / "001-test.patch"
    patch_file.write_text(sample_patch_content)

    patch = load_patch(patch_file)

    assert patch.metadata.patch_name == "add-security-review"
    assert patch.metadata.patch_version == "1.0.0"
    assert len(patch.operations) == 1
    assert patch.source_file == patch_file


def test_load_patch_not_found(temp_patches_dir):
    """Test loading nonexistent patch raises error."""
    patch_file = temp_patches_dir / "nonexistent.patch"

    with pytest.raises(PatchNotFoundError):
        load_patch(patch_file)


def test_load_patch_missing_frontmatter(temp_patches_dir):
    """Test loading patch without frontmatter raises error."""
    patch_file = temp_patches_dir / "no-frontmatter.patch"
    patch_file.write_text("@@ After: Test @@\n+ Content\n@@ END @@")

    with pytest.raises(PatchValidationError, match="missing frontmatter"):
        load_patch(patch_file)


def test_load_patch_invalid_metadata(temp_patches_dir):
    """Test loading patch with invalid metadata raises error."""
    invalid_content = """---
patch_name: ""
patch_version: "invalid"
---

@@ After: Test @@
+ Content
@@ END @@
"""
    patch_file = temp_patches_dir / "invalid.patch"
    patch_file.write_text(invalid_content)

    with pytest.raises(PatchValidationError):
        load_patch(patch_file)


def test_load_patch_no_operations(temp_patches_dir):
    """Test loading patch without operations raises error."""
    content = """---
patch_name: "test"
patch_version: "1.0.0"
target_template: "spec-template"
created: "2026-04-15"
description: "Test"
---

No operations here
"""
    patch_file = temp_patches_dir / "no-ops.patch"
    patch_file.write_text(content)

    with pytest.raises(PatchValidationError, match="No patch operations"):
        load_patch(patch_file)


# Tests: apply_patch_operation


def test_apply_patch_operation_insert_after():
    """Test INSERT_AFTER operation."""
    content = """## Section

Original content
"""

    operation = PatchOperation(
        operation_type=PatchOperationType.INSERT_AFTER,
        anchor="## Section",
        content="New content",
    )

    result, success = apply_patch_operation(content, operation)

    assert success
    assert "## Section" in result
    assert "New content" in result
    assert result.index("## Section") < result.index("New content")


def test_apply_patch_operation_insert_before():
    """Test INSERT_BEFORE operation."""
    content = """## Section

Original content
"""

    operation = PatchOperation(
        operation_type=PatchOperationType.INSERT_BEFORE,
        anchor="## Section",
        content="New content",
    )

    result, success = apply_patch_operation(content, operation)

    assert success
    assert "New content" in result
    assert result.index("New content") < result.index("## Section")


def test_apply_patch_operation_replace():
    """Test REPLACE operation."""
    content = """Old line
Other content
"""

    operation = PatchOperation(
        operation_type=PatchOperationType.REPLACE, anchor="Old line", content="New line"
    )

    result, success = apply_patch_operation(content, operation)

    assert success
    assert "New line" in result
    assert "Old line" not in result


def test_apply_patch_operation_delete():
    """Test DELETE operation."""
    content = """Line to keep
Line to delete
Another line to keep
"""

    operation = PatchOperation(
        operation_type=PatchOperationType.DELETE, anchor="Line to delete", content=""
    )

    result, success = apply_patch_operation(content, operation)

    assert success
    assert "Line to delete" not in result
    assert "Line to keep" in result


def test_apply_patch_operation_anchor_not_found():
    """Test operation fails when anchor not found."""
    content = "Content without anchor"

    operation = PatchOperation(
        operation_type=PatchOperationType.INSERT_AFTER,
        anchor="Nonexistent anchor",
        content="New content",
    )

    with pytest.raises(PatchApplicationError, match="Anchor not found"):
        apply_patch_operation(content, operation)


def test_apply_patch_operation_multiple_anchors():
    """Test operation fails when anchor matches multiple times."""
    content = """## Section
Content 1
## Section
Content 2
"""

    operation = PatchOperation(
        operation_type=PatchOperationType.INSERT_AFTER,
        anchor="## Section",
        content="New content",
    )

    with pytest.raises(PatchConflictError, match="multiple locations"):
        apply_patch_operation(content, operation)


# Tests: apply_patch


def test_apply_patch_single_operation(sample_template):
    """Test applying patch with single operation."""
    operation = PatchOperation(
        operation_type=PatchOperationType.INSERT_AFTER,
        anchor="## User Scenarios",
        content="## Security Review\n- [ ] Input validation",
    )

    metadata = PatchMetadata(
        patch_name="test",
        patch_version="1.0.0",
        target_template="spec-template",
        target_block=None,
        target_version=None,
        created="2026-04-15",
        description="Test",
        author=None,
    )

    patch = Patch(
        metadata=metadata, operations=[operation], source_file=Path("/tmp/test.patch")
    )

    result = apply_patch(sample_template, patch)

    assert "## Security Review" in result
    assert "Input validation" in result


def test_apply_patch_multiple_operations(sample_template):
    """Test applying patch with multiple operations."""
    operations = [
        PatchOperation(
            operation_type=PatchOperationType.INSERT_AFTER,
            anchor="## User Scenarios",
            content="## Security Review",
        ),
        PatchOperation(
            operation_type=PatchOperationType.INSERT_AFTER,
            anchor="## Requirements",
            content="## Performance Criteria",
        ),
    ]

    metadata = PatchMetadata(
        patch_name="test",
        patch_version="1.0.0",
        target_template="spec-template",
        target_block=None,
        target_version=None,
        created="2026-04-15",
        description="Test",
        author=None,
    )

    patch = Patch(
        metadata=metadata, operations=operations, source_file=Path("/tmp/test.patch")
    )

    result = apply_patch(sample_template, patch)

    assert "## Security Review" in result
    assert "## Performance Criteria" in result


def test_apply_patch_operation_failure():
    """Test patch application fails if operation fails."""
    content = "Content"

    operation = PatchOperation(
        operation_type=PatchOperationType.INSERT_AFTER,
        anchor="Nonexistent",
        content="New",
    )

    metadata = PatchMetadata(
        patch_name="test",
        patch_version="1.0.0",
        target_template="spec-template",
        target_block=None,
        target_version=None,
        created="2026-04-15",
        description="Test",
        author=None,
    )

    patch = Patch(
        metadata=metadata, operations=[operation], source_file=Path("/tmp/test.patch")
    )

    with pytest.raises(PatchApplicationError):
        apply_patch(content, patch)


# Tests: apply_patches


def test_apply_patches_single_patch(
    temp_patches_dir, sample_patch_content, sample_template
):
    """Test applying single patch from directory."""
    # Create spec-template subdirectory
    template_dir = temp_patches_dir / "spec-template"
    template_dir.mkdir()

    patch_file = template_dir / "001-security.patch"
    patch_file.write_text(sample_patch_content)

    result = apply_patches(sample_template, temp_patches_dir, "spec-template")

    assert "## Security Review Checklist" in result


def test_apply_patches_multiple_patches(temp_patches_dir, sample_template):
    """Test applying multiple patches in order."""
    template_dir = temp_patches_dir / "spec-template"
    template_dir.mkdir()

    # Patch 1
    patch1 = """---
patch_name: "patch1"
patch_version: "1.0.0"
target_template: "spec-template"
created: "2026-04-15"
description: "Patch 1"
---

@@ After: ## User Scenarios @@
+ ## Security Review
@@ END @@
"""
    (template_dir / "001-patch1.patch").write_text(patch1)

    # Patch 2
    patch2 = """---
patch_name: "patch2"
patch_version: "1.0.0"
target_template: "spec-template"
created: "2026-04-15"
description: "Patch 2"
---

@@ After: ## Requirements @@
+ ## Performance
@@ END @@
"""
    (template_dir / "002-patch2.patch").write_text(patch2)

    result = apply_patches(sample_template, temp_patches_dir, "spec-template")

    assert "## Security Review" in result
    assert "## Performance" in result


def test_apply_patches_no_patches_dir(sample_template, tmp_path):
    """Test applying patches when directory doesn't exist."""
    nonexistent = tmp_path / "nonexistent"

    # Should return content unchanged
    result = apply_patches(sample_template, nonexistent)

    assert result == sample_template


def test_apply_patches_no_patches(temp_patches_dir, sample_template):
    """Test applying patches when no patches exist."""
    template_dir = temp_patches_dir / "spec-template"
    template_dir.mkdir()

    # Empty directory
    result = apply_patches(sample_template, temp_patches_dir, "spec-template")

    assert result == sample_template


# Tests: validate_patch_file


def test_validate_patch_file_valid(temp_patches_dir, sample_patch_content):
    """Test validation of valid patch file."""
    patch_file = temp_patches_dir / "test.patch"
    patch_file.write_text(sample_patch_content)

    is_valid, errors = validate_patch_file(patch_file)

    assert is_valid
    assert len(errors) == 0


def test_validate_patch_file_invalid(temp_patches_dir):
    """Test validation of invalid patch file."""
    invalid_content = """---
patch_name: ""
---

@@ After: Test @@
+ Content
@@ END @@
"""
    patch_file = temp_patches_dir / "invalid.patch"
    patch_file.write_text(invalid_content)

    is_valid, errors = validate_patch_file(patch_file)

    assert not is_valid
    assert len(errors) > 0


def test_validate_patch_file_not_found(temp_patches_dir):
    """Test validation of nonexistent patch file."""
    patch_file = temp_patches_dir / "nonexistent.patch"

    is_valid, errors = validate_patch_file(patch_file)

    assert not is_valid
    assert len(errors) > 0


# Tests: list_patches


def test_list_patches_empty(temp_patches_dir):
    """Test listing patches from empty directory."""
    template_dir = temp_patches_dir / "spec-template"
    template_dir.mkdir()

    patches = list_patches(temp_patches_dir, "spec-template")

    assert len(patches) == 0


def test_list_patches_multiple(temp_patches_dir, sample_patch_content):
    """Test listing multiple patches."""
    template_dir = temp_patches_dir / "spec-template"
    template_dir.mkdir()

    (template_dir / "001-patch1.patch").write_text(sample_patch_content)
    (template_dir / "002-patch2.patch").write_text(sample_patch_content)

    patches = list_patches(temp_patches_dir, "spec-template")

    assert len(patches) == 2
    assert all(isinstance(p, Patch) for p in patches)


def test_list_patches_skips_invalid(temp_patches_dir, sample_patch_content):
    """Test list_patches skips invalid patches."""
    template_dir = temp_patches_dir / "spec-template"
    template_dir.mkdir()

    # Valid patch
    (template_dir / "001-valid.patch").write_text(sample_patch_content)

    # Invalid patch
    (template_dir / "002-invalid.patch").write_text("Invalid content")

    patches = list_patches(temp_patches_dir, "spec-template")

    # Should only return valid patch
    assert len(patches) == 1
    assert patches[0].metadata.patch_name == "add-security-review"


def test_list_patches_nonexistent_dir(tmp_path):
    """Test listing patches from nonexistent directory."""
    patches = list_patches(tmp_path / "nonexistent", "spec-template")

    assert len(patches) == 0
