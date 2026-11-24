"""
Tests for template block system (IMP-65 Phase 4.1).

Tests cover:
- YAML frontmatter parsing
- Block metadata validation
- Template composition
- Error handling
- Edge cases
"""

import pytest

from scripts.lib.template_blocks import (
    BlockMetadata,
    BlockNotFoundError,
    BlockValidationError,
    CompositionError,
    TemplateMetadata,
    compose_template,
    get_template_blocks,
    load_block,
    parse_frontmatter,
    validate_block_file,
)

# Test fixtures


@pytest.fixture
def temp_blocks_dir(tmp_path):
    """Create temporary blocks directory with sample blocks."""
    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()
    return blocks_dir


@pytest.fixture
def sample_block_content():
    """Sample block content with valid frontmatter."""
    return """---
block_type: "template_fragment"
block_name: "test-block"
block_version: "1.0.0"
last_updated: "2026-04-15"
compatible_with:
  - "test-template >= 1.0.0"
dependencies: []
breaking_changes: false
changelog:
  - version: "1.0.0"
    date: "2026-04-15"
    changes:
      - "Initial block"
---

## Test Block Content

This is test content.
"""


@pytest.fixture
def sample_template_content():
    """Sample template content with @include directives."""
    return """---
template_version: "1.0.0"
template_type: "composition"
last_updated: "2026-04-15"
blocks:
  - name: "test-block"
    version: "1.0.0"
    source: "test-block-v1.0.md"
---

# Test Template

<!-- @include test-block-v1.0.md -->

## Additional Content

More content here.
"""


# Tests: parse_frontmatter


def test_parse_frontmatter_valid():
    """Test parsing valid YAML frontmatter."""
    content = """---
key: "value"
number: 123
---

Body content here.
"""
    metadata, body = parse_frontmatter(content)

    assert metadata is not None
    assert metadata["key"] == "value"
    assert metadata["number"] == 123
    assert body.strip() == "Body content here."


def test_parse_frontmatter_no_frontmatter():
    """Test parsing content without frontmatter."""
    content = "Just regular content\nNo frontmatter here."

    metadata, body = parse_frontmatter(content)

    assert metadata is None
    assert body == content


def test_parse_frontmatter_invalid_yaml():
    """Test parsing invalid YAML in frontmatter."""
    content = """---
invalid: yaml: broken
---

Body
"""

    with pytest.raises(BlockValidationError):
        parse_frontmatter(content)


def test_parse_frontmatter_empty():
    """Test parsing empty frontmatter."""
    content = """---
---

Body
"""
    metadata, body = parse_frontmatter(content)

    assert metadata is None or metadata == {}
    assert "Body" in body


# Tests: BlockMetadata


def test_block_metadata_from_dict():
    """Test creating BlockMetadata from dict."""
    data = {
        "block_type": "template_fragment",
        "block_name": "test-block",
        "block_version": "1.0.0",
        "last_updated": "2026-04-15",
        "compatible_with": ["template >= 1.0.0"],
        "dependencies": [],
        "breaking_changes": False,
        "changelog": [],
    }

    meta = BlockMetadata.from_dict(data)

    assert meta.block_name == "test-block"
    assert meta.block_version == "1.0.0"
    assert meta.block_type == "template_fragment"


def test_block_metadata_validate_valid():
    """Test validation of valid block metadata."""
    meta = BlockMetadata(
        block_type="template_fragment",
        block_name="test-block",
        block_version="1.0.0",
        last_updated="2026-04-15",
        compatible_with=[],
        dependencies=[],
        breaking_changes=False,
        changelog=[],
    )

    errors = meta.validate()
    assert len(errors) == 0


def test_block_metadata_validate_missing_name():
    """Test validation fails for missing block_name."""
    meta = BlockMetadata(
        block_type="template_fragment",
        block_name="",
        block_version="1.0.0",
        last_updated="2026-04-15",
        compatible_with=[],
        dependencies=[],
        breaking_changes=False,
        changelog=[],
    )

    errors = meta.validate()
    assert any("Missing block_name" in e for e in errors)


def test_block_metadata_validate_invalid_version():
    """Test validation fails for invalid version format."""
    meta = BlockMetadata(
        block_type="template_fragment",
        block_name="test-block",
        block_version="v1.0",  # Invalid: not semver
        last_updated="2026-04-15",
        compatible_with=[],
        dependencies=[],
        breaking_changes=False,
        changelog=[],
    )

    errors = meta.validate()
    assert any("Invalid block_version" in e for e in errors)


def test_block_metadata_validate_invalid_block_type():
    """Test validation fails for invalid block_type."""
    meta = BlockMetadata(
        block_type="invalid_type",
        block_name="test-block",
        block_version="1.0.0",
        last_updated="2026-04-15",
        compatible_with=[],
        dependencies=[],
        breaking_changes=False,
        changelog=[],
    )

    errors = meta.validate()
    assert any("Invalid block_type" in e for e in errors)


# Tests: TemplateMetadata


def test_template_metadata_from_dict():
    """Test creating TemplateMetadata from dict."""
    data = {
        "template_version": "1.0.0",
        "template_type": "composition",
        "last_updated": "2026-04-15",
        "blocks": [{"name": "block1", "version": "1.0.0", "source": "block1.md"}],
    }

    meta = TemplateMetadata.from_dict(data)

    assert meta.template_version == "1.0.0"
    assert meta.template_type == "composition"
    assert len(meta.blocks) == 1


def test_template_metadata_validate_valid():
    """Test validation of valid template metadata."""
    meta = TemplateMetadata(
        template_version="1.0.0",
        template_type="composition",
        last_updated="2026-04-15",
        blocks=[],
    )

    errors = meta.validate()
    assert len(errors) == 0


def test_template_metadata_validate_invalid_version():
    """Test validation fails for invalid version."""
    meta = TemplateMetadata(
        template_version="v1",  # Invalid
        template_type="composition",
        last_updated="2026-04-15",
        blocks=[],
    )

    errors = meta.validate()
    assert any("Invalid template_version" in e for e in errors)


# Tests: load_block


def test_load_block_success(temp_blocks_dir, sample_block_content):
    """Test loading a valid block file."""
    block_file = temp_blocks_dir / "test-block-v1.0.md"
    block_file.write_text(sample_block_content)

    metadata, content = load_block(block_file)

    assert metadata.block_name == "test-block"
    assert metadata.block_version == "1.0.0"
    assert "## Test Block Content" in content
    assert "---" not in content  # Frontmatter removed


def test_load_block_not_found(temp_blocks_dir):
    """Test loading nonexistent block raises BlockNotFoundError."""
    block_file = temp_blocks_dir / "nonexistent.md"

    with pytest.raises(BlockNotFoundError):
        load_block(block_file)


def test_load_block_missing_frontmatter(temp_blocks_dir):
    """Test loading block without frontmatter raises error."""
    block_file = temp_blocks_dir / "no-frontmatter.md"
    block_file.write_text("Just content, no frontmatter")

    with pytest.raises(BlockValidationError, match="missing frontmatter"):
        load_block(block_file)


def test_load_block_invalid_metadata(temp_blocks_dir):
    """Test loading block with invalid metadata raises error."""
    invalid_content = """---
block_type: "template_fragment"
block_name: ""
block_version: "invalid"
---

Content
"""
    block_file = temp_blocks_dir / "invalid.md"
    block_file.write_text(invalid_content)

    with pytest.raises(BlockValidationError):
        load_block(block_file)


# Tests: compose_template


def test_compose_template_success(
    tmp_path, sample_block_content, sample_template_content
):
    """Test successful template composition."""
    # Setup
    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()

    block_file = blocks_dir / "test-block-v1.0.md"
    block_file.write_text(sample_block_content)

    template_file = tmp_path / "template.md"
    template_file.write_text(sample_template_content)

    # Compose
    result = compose_template(template_file, blocks_dir)

    # Verify
    assert "## Test Block Content" in result
    assert "This is test content." in result
    assert "## Additional Content" in result
    assert "@include" not in result  # Directive replaced
    assert "---" not in result  # Frontmatter removed


def test_compose_template_multiple_blocks(tmp_path):
    """Test composition with multiple blocks."""
    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()

    # Create two blocks
    block1 = """---
block_type: "template_fragment"
block_name: "block1"
block_version: "1.0.0"
last_updated: "2026-04-15"
---

## Block 1
Content 1
"""

    block2 = """---
block_type: "template_fragment"
block_name: "block2"
block_version: "1.0.0"
last_updated: "2026-04-15"
---

## Block 2
Content 2
"""

    (blocks_dir / "block1-v1.0.md").write_text(block1)
    (blocks_dir / "block2-v1.0.md").write_text(block2)

    # Create template with both blocks
    template = """---
template_version: "1.0.0"
template_type: "composition"
last_updated: "2026-04-15"
blocks:
  - name: "block1"
    version: "1.0.0"
  - name: "block2"
    version: "1.0.0"
---

<!-- @include block1-v1.0.md -->

<!-- @include block2-v1.0.md -->
"""

    template_file = tmp_path / "template.md"
    template_file.write_text(template)

    # Compose
    result = compose_template(template_file, blocks_dir)

    # Verify both blocks included
    assert "## Block 1" in result
    assert "Content 1" in result
    assert "## Block 2" in result
    assert "Content 2" in result


def test_compose_template_missing_block(tmp_path, sample_template_content):
    """Test composition fails when block is missing."""
    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()

    template_file = tmp_path / "template.md"
    template_file.write_text(sample_template_content)

    # Try to compose without creating the required block
    with pytest.raises(CompositionError, match="Cannot compose"):
        compose_template(template_file, blocks_dir)


def test_compose_template_legacy_monolithic(tmp_path):
    """Test composition of legacy monolithic template (no frontmatter)."""
    template_content = """# Legacy Template

This template has no frontmatter.

## Section 1
Content here.
"""

    template_file = tmp_path / "legacy.md"
    template_file.write_text(template_content)

    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()

    # Should return content as-is
    result = compose_template(template_file, blocks_dir)

    assert result == template_content


def test_compose_template_not_composition_type(tmp_path):
    """Test template with frontmatter but not composition type."""
    template = """---
template_version: "1.0.0"
template_type: "monolithic"
last_updated: "2026-04-15"
---

Content here.
"""

    template_file = tmp_path / "template.md"
    template_file.write_text(template)

    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()

    # Should return as-is
    result = compose_template(template_file, blocks_dir)

    assert "Content here." in result


# Tests: get_template_blocks


def test_get_template_blocks(tmp_path, sample_template_content):
    """Test getting blocks list from template."""
    template_file = tmp_path / "template.md"
    template_file.write_text(sample_template_content)

    blocks = get_template_blocks(template_file)

    assert len(blocks) == 1
    assert blocks[0]["name"] == "test-block"
    assert blocks[0]["version"] == "1.0.0"


def test_get_template_blocks_no_frontmatter(tmp_path):
    """Test getting blocks from template without frontmatter."""
    template_file = tmp_path / "template.md"
    template_file.write_text("No frontmatter")

    blocks = get_template_blocks(template_file)

    assert blocks == []


def test_get_template_blocks_nonexistent(tmp_path):
    """Test getting blocks from nonexistent template."""
    template_file = tmp_path / "nonexistent.md"

    blocks = get_template_blocks(template_file)

    assert blocks == []


# Tests: validate_block_file


def test_validate_block_file_valid(temp_blocks_dir, sample_block_content):
    """Test validation of valid block file."""
    block_file = temp_blocks_dir / "test.md"
    block_file.write_text(sample_block_content)

    is_valid, errors = validate_block_file(block_file)

    assert is_valid
    assert len(errors) == 0


def test_validate_block_file_invalid(temp_blocks_dir):
    """Test validation of invalid block file."""
    invalid_content = """---
block_name: ""
block_version: "invalid"
---

Content
"""
    block_file = temp_blocks_dir / "invalid.md"
    block_file.write_text(invalid_content)

    is_valid, errors = validate_block_file(block_file)

    assert not is_valid
    assert len(errors) > 0


def test_validate_block_file_not_found(temp_blocks_dir):
    """Test validation of nonexistent block file."""
    block_file = temp_blocks_dir / "nonexistent.md"

    is_valid, errors = validate_block_file(block_file)

    assert not is_valid
    assert len(errors) > 0
    assert "not found" in errors[0].lower()


# Tests: Error handling edge cases


def test_compose_template_verbose_output(
    tmp_path, sample_block_content, sample_template_content, capsys
):
    """Test verbose output during composition."""
    blocks_dir = tmp_path / "blocks"
    blocks_dir.mkdir()

    block_file = blocks_dir / "test-block-v1.0.md"
    block_file.write_text(sample_block_content)

    template_file = tmp_path / "template.md"
    template_file.write_text(sample_template_content)

    # Compose with verbose=True
    compose_template(template_file, blocks_dir, verbose=True)

    captured = capsys.readouterr()
    assert "Composing template" in captured.out
    assert "Loading block" in captured.out


def test_block_metadata_repr():
    """Test __repr__ of BlockMetadata."""
    meta = BlockMetadata(
        block_type="template_fragment",
        block_name="test",
        block_version="1.0.0",
        last_updated="2026-04-15",
        compatible_with=[],
        dependencies=[],
        breaking_changes=False,
        changelog=[],
    )

    repr_str = repr(meta)
    assert "test" in repr_str
    assert "1.0.0" in repr_str


def test_template_metadata_repr():
    """Test __repr__ of TemplateMetadata."""
    meta = TemplateMetadata(
        template_version="1.0.0",
        template_type="composition",
        last_updated="2026-04-15",
        blocks=[{}, {}],  # 2 blocks
    )

    repr_str = repr(meta)
    assert "1.0.0" in repr_str
    assert "2 blocks" in repr_str
