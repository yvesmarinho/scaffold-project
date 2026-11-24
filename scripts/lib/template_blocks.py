"""
Template Block System for IMP-65 Phase 4.

This module implements a modular template system where templates are composed
from versioned, reusable blocks. This enables:
- Granular template updates (update specific sections, not entire files)
- Clear separation of customizations (patches) from standard content
- Better conflict resolution (merge at block level, not file level)
- Reusability of common sections across multiple templates

Architecture:
- **Blocks**: Reusable template fragments with independent versioning
- **Templates**: Compositions of blocks via @include directives
- **Patches**: User customizations stored separately

Example:
    >>> from scripts.lib.template_blocks import compose_template
    >>> from pathlib import Path
    >>>
    >>> template_path = Path('.specify/templates/spec-template.md')
    >>> blocks_dir = Path('.specify/templates/blocks')
    >>>
    >>> result = compose_template(template_path, blocks_dir)
    >>> print(result)  # Fully composed template with blocks resolved
"""

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class BlockMetadata:
    """Metadata for a template block.

    Attributes:
        block_type: Type of block (always 'template_fragment')
        block_name: Unique identifier (e.g., 'user-scenarios')
        block_version: Semantic version (e.g., '2.0.0')
        last_updated: ISO date string (e.g., '2026-04-15')
        compatible_with: List of template compatibility specs
        dependencies: List of required blocks
        breaking_changes: Whether this version has breaking changes
        changelog: Version history with changes
    """

    block_type: str
    block_name: str
    block_version: str
    last_updated: str
    compatible_with: list[str]
    dependencies: list[dict[str, str]]
    breaking_changes: bool
    changelog: list[dict[str, any]]

    @classmethod
    def from_dict(cls, data: dict) -> "BlockMetadata":
        """Create BlockMetadata from parsed YAML dict."""
        return cls(
            block_type=data.get("block_type", ""),
            block_name=data.get("block_name", ""),
            block_version=data.get("block_version", ""),
            last_updated=data.get("last_updated", ""),
            compatible_with=data.get("compatible_with", []),
            dependencies=data.get("dependencies", []),
            breaking_changes=data.get("breaking_changes", False),
            changelog=data.get("changelog", []),
        )

    def validate(self) -> list[str]:
        """Validate block metadata.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.block_type:
            errors.append("Missing block_type")
        elif self.block_type != "template_fragment":
            errors.append(
                f"Invalid block_type: {self.block_type} (must be 'template_fragment')"
            )

        if not self.block_name:
            errors.append("Missing block_name")
        elif not re.match(r"^[a-z][a-z0-9-]*$", self.block_name):
            errors.append(
                f"Invalid block_name: {self.block_name} (must match ^[a-z][a-z0-9-]*$)"
            )

        if not self.block_version:
            errors.append("Missing block_version")
        elif not re.match(r"^\d+\.\d+\.\d+$", self.block_version):
            errors.append(
                f"Invalid block_version: {self.block_version} (must be semver x.y.z)"
            )

        if not self.last_updated:
            errors.append("Missing last_updated")

        return errors

    def __repr__(self):
        return f"Block({self.block_name} v{self.block_version})"


@dataclass
class TemplateMetadata:
    """Metadata for a composed template.

    Attributes:
        template_version: Semantic version of the template
        template_type: Type of template ('composition' for modular templates)
        last_updated: ISO date string
        blocks: List of block specifications (name, version, source)
    """

    template_version: str
    template_type: str
    last_updated: str
    blocks: list[dict[str, str]]

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateMetadata":
        """Create TemplateMetadata from parsed YAML dict."""
        return cls(
            template_version=data.get("template_version", ""),
            template_type=data.get("template_type", ""),
            last_updated=data.get("last_updated", ""),
            blocks=data.get("blocks", []),
        )

    def validate(self) -> list[str]:
        """Validate template metadata.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.template_version:
            errors.append("Missing template_version")
        elif not re.match(r"^\d+\.\d+\.\d+$", self.template_version):
            errors.append(f"Invalid template_version: {self.template_version}")

        # template_type is optional; if present, it can be any value
        # Only 'composition' type triggers block composition

        if not self.last_updated:
            errors.append("Missing last_updated")

        return errors

    def __repr__(self):
        return f"Template(v{self.template_version}, {len(self.blocks)} blocks)"


class BlockError(Exception):
    """Base exception for block-related errors."""

    pass


class BlockNotFoundError(BlockError):
    """Raised when a required block cannot be found."""

    pass


class BlockValidationError(BlockError):
    """Raised when block metadata validation fails."""

    pass


class CompositionError(BlockError):
    """Raised when template composition fails."""

    pass


def parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Full file content with YAML frontmatter

    Returns:
        Tuple of (metadata_dict, body_content_without_frontmatter)

    Example:
        >>> content = '''---
        ... block_name: "test"
        ... block_version: "1.0.0"
        ... ---
        ...
        ... ## Content here
        ... '''
        >>> metadata, body = parse_frontmatter(content)
        >>> metadata['block_name']
        'test'
        >>> body.strip()
        '## Content here'
    """
    # Match YAML frontmatter: ---\n<yaml>\n---
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return None, content

    yaml_text = match.group(1)
    body = match.group(2)

    try:
        metadata = yaml.safe_load(yaml_text)
        return metadata, body
    except yaml.YAMLError as e:
        raise BlockValidationError(f"YAML parse error: {e}") from e


def load_block(block_path: Path) -> tuple[BlockMetadata, str]:
    """Load a block file and parse its metadata.

    Args:
        block_path: Path to block file

    Returns:
        Tuple of (BlockMetadata, content_without_frontmatter)

    Raises:
        BlockNotFoundError: If block file doesn't exist
        BlockValidationError: If block has invalid metadata

    Example:
        >>> block_path = Path('.specify/templates/blocks/user-scenarios-v2.0.md')
        >>> metadata, content = load_block(block_path)
        >>> metadata.block_name
        'user-scenarios'
        >>> metadata.block_version
        '2.0.0'
    """
    if not block_path.exists():
        raise BlockNotFoundError(f"Block not found: {block_path}")

    content = block_path.read_text(encoding="utf-8")
    metadata_dict, body = parse_frontmatter(content)

    if not metadata_dict:
        raise BlockValidationError(f"Block missing frontmatter: {block_path.name}")

    metadata = BlockMetadata.from_dict(metadata_dict)

    # Validate metadata
    errors = metadata.validate()
    if errors:
        raise BlockValidationError(
            f"Block validation failed for {block_path.name}: {'; '.join(errors)}"
        )

    return metadata, body


def compose_template(
    template_path: Path, blocks_dir: Path, verbose: bool = False
) -> str:
    """Compose a template by resolving @include directives.

    This is the core function of the block system. It:
    1. Parses template metadata
    2. Finds all @include directives
    3. Loads referenced blocks
    4. Replaces directives with block content
    5. Returns fully composed template

    Args:
        template_path: Path to template file with @include directives
        blocks_dir: Directory containing block files
        verbose: If True, print composition details

    Returns:
        Fully composed template content (string)

    Raises:
        CompositionError: If template composition fails
        BlockNotFoundError: If a required block is missing
        BlockValidationError: If a block has invalid metadata

    Example:
        >>> template = Path('.specify/templates/spec-template.md')
        >>> blocks = Path('.specify/templates/blocks')
        >>> result = compose_template(template, blocks)
        >>> '## User Scenarios' in result
        True
    """
    if not template_path.exists():
        raise CompositionError(f"Template not found: {template_path}")

    content = template_path.read_text(encoding="utf-8")
    metadata_dict, body = parse_frontmatter(content)

    if not metadata_dict:
        # Template without frontmatter - might be legacy monolithic template
        # Just return as-is (no composition needed)
        if verbose:
            print(
                f"ℹ️  Template {template_path.name} has no frontmatter (legacy monolithic template)"
            )
        return content

    template_meta = TemplateMetadata.from_dict(metadata_dict)

    # Validate template metadata
    errors = template_meta.validate()
    if errors:
        raise CompositionError(f"Template validation failed: {'; '.join(errors)}")

    # If not a composition template, return as-is
    if template_meta.template_type != "composition":
        if verbose:
            print(
                f"ℹ️  Template {template_path.name} is not a composition (type: {template_meta.template_type})"
            )
        return content

    # Find all @include directives
    include_pattern = r"<!--\s*@include\s+([^\s]+)\s*-->"
    includes = re.findall(include_pattern, body)

    if verbose:
        print(f"📋 Composing template: {template_path.name}")
        print(f"   Version: {template_meta.template_version}")
        print(f"   Blocks declared: {len(template_meta.blocks)}")
        print(f"   @include directives found: {len(includes)}")

    if not includes:
        if verbose:
            print("   ⚠️  No @include directives found")
        return body  # Return body without frontmatter

    # Compose by replacing @include directives
    composed = body
    loaded_blocks = {}

    for include_file in includes:
        block_path = blocks_dir / include_file

        if verbose:
            print(f"   Loading block: {include_file}")

        try:
            # Check cache first
            if include_file in loaded_blocks:
                block_meta, block_content = loaded_blocks[include_file]
                if verbose:
                    print(
                        f"     ✅ {block_meta.block_name} v{block_meta.block_version} (cached)"
                    )
            else:
                block_meta, block_content = load_block(block_path)
                loaded_blocks[include_file] = (block_meta, block_content)
                if verbose:
                    print(
                        f"     ✅ {block_meta.block_name} v{block_meta.block_version}"
                    )

            # Replace the @include directive with block content
            directive = f"<!-- @include {include_file} -->"
            # Strip block content to avoid extra whitespace
            composed = composed.replace(directive, block_content.strip())

        except BlockNotFoundError as e:
            raise CompositionError(f"Cannot compose {template_path.name}: {e}") from e
        except BlockValidationError as e:
            raise CompositionError(f"Cannot compose {template_path.name}: {e}") from e

    return composed


def get_template_blocks(template_path: Path) -> list[dict[str, str]]:
    """Get list of blocks declared in a template's frontmatter.

    Args:
        template_path: Path to template file

    Returns:
        List of block specifications (name, version, source)

    Example:
        >>> blocks = get_template_blocks(Path('spec-template.md'))
        >>> blocks[0]['name']
        'frontmatter-spec'
        >>> blocks[0]['version']
        '1.0.0'
    """
    if not template_path.exists():
        return []

    content = template_path.read_text(encoding="utf-8")
    metadata_dict, _ = parse_frontmatter(content)

    if not metadata_dict:
        return []

    template_meta = TemplateMetadata.from_dict(metadata_dict)
    return template_meta.blocks


def validate_block_file(block_path: Path) -> tuple[bool, list[str]]:
    """Validate a block file.

    Args:
        block_path: Path to block file

    Returns:
        Tuple of (is_valid, error_messages)

    Example:
        >>> valid, errors = validate_block_file(Path('user-scenarios-v2.0.md'))
        >>> if not valid:
        ...     print(f"Validation errors: {errors}")
    """
    try:
        metadata, _ = load_block(block_path)
        return True, []
    except BlockNotFoundError as e:
        return False, [str(e)]
    except BlockValidationError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Unexpected error: {e}"]
