"""
Template Patch System for IMP-65 Phase 4.2.

This module implements a patch system for template customizations. Patches allow
users to store their template customizations separately from the standard block
content, enabling:
- Clean separation of custom vs standard content
- Survival of customizations through upstream updates
- Portable customizations (export/import across projects)
- Version control of customizations

Architecture:
- **Patches**: YAML-frontmatter files with anchor-based insertion points
- **Application**: Apply patches on top of composed templates
- **Conflict Detection**: Detect when patches can't be applied cleanly

Patch Format:
    ---
    patch_name: "add-security-review"
    patch_version: "1.0.0"
    target_template: "spec-template"
    target_block: "user-scenarios"
    description: "Add security checklist"
    ---

    @@ After: ## User Scenarios @@
    + ## Security Review
    + - [ ] Input validation
    @@ END @@

Example:
    >>> from scripts.lib.template_patches import apply_patches
    >>> from pathlib import Path
    >>>
    >>> template_content = "## User Scenarios\\n\\nContent"
    >>> patches_dir = Path('.specify/templates/patches/spec-template')
    >>>
    >>> result = apply_patches(template_content, patches_dir)
    >>> '## Security Review' in result
    True
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import yaml


class PatchOperationType(Enum):
    """Types of patch operations."""

    INSERT_AFTER = "after"
    INSERT_BEFORE = "before"
    REPLACE = "replace"
    DELETE = "delete"


@dataclass
class PatchMetadata:
    """Metadata for a patch file.

    Attributes:
        patch_name: Unique identifier (e.g., 'add-security-review')
        patch_version: Semantic version (e.g., '1.0.0')
        target_template: Template this patch applies to
        target_block: Block this patch modifies (optional)
        target_version: Compatible block/template version (optional)
        created: ISO date string
        description: Human-readable description
        author: Author email/identifier (optional)
    """

    patch_name: str
    patch_version: str
    target_template: str
    target_block: str | None
    target_version: str | None
    created: str
    description: str
    author: str | None

    @classmethod
    def from_dict(cls, data: dict) -> "PatchMetadata":
        """Create PatchMetadata from parsed YAML dict."""
        return cls(
            patch_name=data.get("patch_name", ""),
            patch_version=data.get("patch_version", ""),
            target_template=data.get("target_template", ""),
            target_block=data.get("target_block"),
            target_version=data.get("target_version"),
            created=data.get("created", ""),
            description=data.get("description", ""),
            author=data.get("author"),
        )

    def validate(self) -> list[str]:
        """Validate patch metadata.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not self.patch_name:
            errors.append("Missing patch_name")
        elif not re.match(r"^[a-z0-9][a-z0-9-]*$", self.patch_name):
            errors.append(
                f"Invalid patch_name: {self.patch_name} (must match ^[a-z0-9][a-z0-9-]*$)"
            )

        if not self.patch_version:
            errors.append("Missing patch_version")
        elif not re.match(r"^\d+\.\d+\.\d+$", self.patch_version):
            errors.append(
                f"Invalid patch_version: {self.patch_version} (must be semver x.y.z)"
            )

        if not self.target_template:
            errors.append("Missing target_template")

        if not self.created:
            errors.append("Missing created date")

        if not self.description:
            errors.append("Missing description")

        return errors

    def __repr__(self):
        return (
            f"Patch({self.patch_name} v{self.patch_version} → {self.target_template})"
        )


@dataclass
class PatchOperation:
    """A single patch operation.

    Attributes:
        operation_type: Type of operation (INSERT_AFTER, etc.)
        anchor: Text to search for in template
        content: Content to add/replace
        line_offset: Optional line offset from anchor
    """

    operation_type: PatchOperationType
    anchor: str
    content: str
    line_offset: int = 0

    def __repr__(self):
        return f"PatchOp({self.operation_type.value} @ '{self.anchor[:30]}...')"


@dataclass
class Patch:
    """A complete patch with metadata and operations.

    Attributes:
        metadata: Patch metadata
        operations: List of patch operations to apply
        source_file: Path to source patch file
    """

    metadata: PatchMetadata
    operations: list[PatchOperation]
    source_file: Path

    def __repr__(self):
        return f"Patch({self.metadata.patch_name}, {len(self.operations)} ops)"


class PatchError(Exception):
    """Base exception for patch-related errors."""

    pass


class PatchNotFoundError(PatchError):
    """Raised when a patch file cannot be found."""

    pass


class PatchValidationError(PatchError):
    """Raised when patch validation fails."""

    pass


class PatchApplicationError(PatchError):
    """Raised when patch application fails."""

    pass


class PatchConflictError(PatchError):
    """Raised when patch conflicts are detected."""

    pass


def parse_patch_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from patch content.

    Args:
        content: Full patch file content

    Returns:
        Tuple of (metadata_dict, body_content)
    """
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
        raise PatchValidationError(f"YAML parse error: {e}") from e


def parse_patch_operations(body: str) -> list[PatchOperation]:
    """Parse patch operations from patch body.

    Patch operations have format:
        @@ After: <anchor text> @@
        + <line to add>
        + <another line to add>
        @@ END @@

    Args:
        body: Patch body content (without frontmatter)

    Returns:
        List of PatchOperation objects

    Raises:
        PatchValidationError: If patch syntax is invalid
    """
    operations = []

    # Find all operation blocks: @@ ... @@ ... @@ END @@
    # Match any word for operation type, validate later
    op_pattern = r"@@\s*(\w+):\s*(.+?)\s*@@\s*\n(.*?)@@\s*END\s*@@"
    matches = re.findall(op_pattern, body, re.DOTALL | re.IGNORECASE)

    if not matches:
        raise PatchValidationError("No patch operations found (expected @@ ... @@)")

    for op_type_str, anchor, content_block in matches:
        # Map operation type string to enum
        op_type_lower = op_type_str.lower()
        if op_type_lower == "after":
            op_type = PatchOperationType.INSERT_AFTER
        elif op_type_lower == "before":
            op_type = PatchOperationType.INSERT_BEFORE
        elif op_type_lower == "replace":
            op_type = PatchOperationType.REPLACE
        elif op_type_lower == "delete":
            op_type = PatchOperationType.DELETE
        else:
            raise PatchValidationError(f"Invalid operation type: {op_type_str}")

        # Parse content (lines starting with + or -)
        content_lines = []
        for line in content_block.split("\n"):
            line = line.rstrip()
            if line.startswith("+ "):
                content_lines.append(line[2:])  # Remove '+ ' prefix
            elif line.startswith("+"):
                content_lines.append(line[1:])  # Remove '+' prefix
            elif line.startswith("- "):
                # For delete operations
                content_lines.append(line[2:])
            elif line.startswith("-"):
                content_lines.append(line[1:])
            elif line.strip():
                # Non-prefixed non-empty line - include as-is
                content_lines.append(line)

        content = "\n".join(content_lines)

        operation = PatchOperation(
            operation_type=op_type, anchor=anchor.strip(), content=content
        )
        operations.append(operation)

    return operations


def load_patch(patch_path: Path) -> Patch:
    """Load a patch file and parse its metadata and operations.

    Args:
        patch_path: Path to patch file

    Returns:
        Patch object with metadata and operations

    Raises:
        PatchNotFoundError: If patch file doesn't exist
        PatchValidationError: If patch has invalid format
    """
    if not patch_path.exists():
        raise PatchNotFoundError(f"Patch not found: {patch_path}")

    content = patch_path.read_text(encoding="utf-8")
    metadata_dict, body = parse_patch_frontmatter(content)

    if not metadata_dict:
        raise PatchValidationError(f"Patch missing frontmatter: {patch_path.name}")

    metadata = PatchMetadata.from_dict(metadata_dict)

    # Validate metadata
    errors = metadata.validate()
    if errors:
        raise PatchValidationError(
            f"Patch validation failed for {patch_path.name}: {'; '.join(errors)}"
        )

    # Parse operations
    operations = parse_patch_operations(body)

    if not operations:
        raise PatchValidationError(f"Patch has no operations: {patch_path.name}")

    return Patch(metadata=metadata, operations=operations, source_file=patch_path)


def apply_patch_operation(content: str, operation: PatchOperation) -> tuple[str, bool]:
    """Apply a single patch operation to content.

    Args:
        content: Template content
        operation: Patch operation to apply

    Returns:
        Tuple of (modified_content, success)

    Raises:
        PatchApplicationError: If operation cannot be applied
    """
    lines = content.split("\n")

    # Find anchor line
    anchor_indices = []
    for i, line in enumerate(lines):
        if operation.anchor in line:
            anchor_indices.append(i)

    if len(anchor_indices) == 0:
        raise PatchApplicationError(f"Anchor not found: '{operation.anchor}'")

    if len(anchor_indices) > 1:
        raise PatchConflictError(
            f"Anchor matches multiple locations ({len(anchor_indices)}): '{operation.anchor}'"
        )

    anchor_idx = anchor_indices[0]

    # Apply operation based on type
    if operation.operation_type == PatchOperationType.INSERT_AFTER:
        # Insert content after anchor line
        insert_idx = anchor_idx + 1
        patch_lines = operation.content.split("\n")
        lines = lines[:insert_idx] + [""] + patch_lines + lines[insert_idx:]

    elif operation.operation_type == PatchOperationType.INSERT_BEFORE:
        # Insert content before anchor line
        insert_idx = anchor_idx
        patch_lines = operation.content.split("\n")
        lines = lines[:insert_idx] + patch_lines + [""] + lines[insert_idx:]

    elif operation.operation_type == PatchOperationType.REPLACE:
        # Replace anchor line with content
        patch_lines = operation.content.split("\n")
        lines = lines[:anchor_idx] + patch_lines + lines[anchor_idx + 1 :]

    elif operation.operation_type == PatchOperationType.DELETE:
        # Delete anchor line
        lines = lines[:anchor_idx] + lines[anchor_idx + 1 :]

    return "\n".join(lines), True


def apply_patch(content: str, patch: Patch) -> str:
    """Apply a complete patch to content.

    Args:
        content: Template content
        patch: Patch to apply

    Returns:
        Modified content with patch applied

    Raises:
        PatchApplicationError: If patch cannot be applied
        PatchConflictError: If conflicts are detected
    """
    result = content

    for i, operation in enumerate(patch.operations):
        try:
            result, success = apply_patch_operation(result, operation)
            if not success:
                raise PatchApplicationError(
                    f"Failed to apply operation {i+1} of patch {patch.metadata.patch_name}"
                )
        except (PatchApplicationError, PatchConflictError) as e:
            # Re-raise with patch context
            raise PatchApplicationError(
                f"Patch {patch.metadata.patch_name} operation {i+1} failed: {e}"
            ) from e

    return result


def apply_patches(content: str, patches_dir: Path, template_name: str = None) -> str:
    """Apply all patches from a directory to content.

    Patches are applied in filename order (001-..., 002-..., etc.).

    Args:
        content: Template content
        patches_dir: Directory containing patch files
        template_name: Template name (if patches_dir contains multiple templates)

    Returns:
        Content with all patches applied

    Raises:
        PatchApplicationError: If any patch fails to apply
    """
    if not patches_dir.exists():
        return content  # No patches directory = no patches to apply

    # If template_name provided, look in subdirectory
    if template_name:
        patches_dir = patches_dir / template_name
        if not patches_dir.exists():
            return content  # No patches for this template

    # Find all patch files (*.patch)
    patch_files = sorted(patches_dir.glob("*.patch"))

    if not patch_files:
        return content  # No patches to apply

    result = content
    for patch_file in patch_files:
        try:
            patch = load_patch(patch_file)
            result = apply_patch(result, patch)
        except (PatchNotFoundError, PatchValidationError, PatchApplicationError) as e:
            raise PatchApplicationError(
                f"Failed to apply {patch_file.name}: {e}"
            ) from e

    return result


def validate_patch_file(patch_path: Path) -> tuple[bool, list[str]]:
    """Validate a patch file.

    Args:
        patch_path: Path to patch file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        load_patch(patch_path)
        return True, []
    except PatchNotFoundError as e:
        return False, [str(e)]
    except PatchValidationError as e:
        return False, [str(e)]
    except Exception as e:
        return False, [f"Unexpected error: {e}"]


def list_patches(patches_dir: Path, template_name: str = None) -> list[Patch]:
    """List all patches for a template.

    Args:
        patches_dir: Base patches directory
        template_name: Template name (optional, for filtering)

    Returns:
        List of Patch objects
    """
    if not patches_dir.exists():
        return []

    if template_name:
        patches_dir = patches_dir / template_name
        if not patches_dir.exists():
            return []

    patches = []
    for patch_file in sorted(patches_dir.glob("*.patch")):
        try:
            patch = load_patch(patch_file)
            patches.append(patch)
        except (PatchNotFoundError, PatchValidationError):
            # Skip invalid patches
            continue

    return patches
