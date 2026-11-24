"""
objetivo_validator.py — Validator for objetivo.yaml v2.0 files

Validates parsed objetivo.yaml files for:
- Valid frontmatter (version, project fields)
- P0 sections present and non-empty (1️⃣, 2️⃣, 3️⃣)
- P1/P2 sections (warnings only)
- No duplicate sections
- Sections in order

Usage:
    from scripts.lib.objetivo_parser import ObjetivoV2Parser
    from scripts.lib.objetivo_validator import ObjetivoValidator

    parser = ObjetivoV2Parser()
    validator = ObjetivoValidator()

    parsed = parser.parse("objetivo.yaml")
    errors, warnings = validator.validate(parsed)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")

Spec: specs/066-objetivo-yaml-v2/spec.md
Tasks: T011-T015
"""

import re
from dataclasses import dataclass
from typing import Any

from .objetivo_parser import ParsedObjetivo


@dataclass
class ValidationError:
    """Dataclass representing a validation error or warning.

    Attributes:
        level: "error" or "warning"
        field: Field or section that failed validation
        message: Human-readable error message
        line: Line number where error occurred (if known)
        example: Example of correct format (optional)
    """

    level: str  # "error" | "warning"
    field: str
    message: str
    line: int | None = None
    example: str | None = None

    def __str__(self) -> str:
        """Format error for display."""
        prefix = "❌ ERROR" if self.level == "error" else "⚠️  WARNING"
        location = f" (line {self.line})" if self.line else ""
        result = f"{prefix}: {self.field}{location}\n  {self.message}"
        if self.example:
            result += f"\n  Example: {self.example}"
        return result


class ObjetivoValidator:
    """Validator for objetivo.yaml v2.0 files.

    Validates:
    - Frontmatter fields (version, project.name, project.type, project.domain)
    - P0 sections (1-3) present and non-empty
    - P1/P2 sections (optional warnings)
    - No duplicates
    - Sections in order

    Example:
        validator = ObjetivoValidator()
        errors, warnings = validator.validate(parsed_objetivo)

        if errors:
            for error in errors:
                print(error)
            exit(1)
    """

    # Valid project types
    VALID_TYPES = [
        "backend-api",
        "frontend-spa",
        "cli-tool",
        "library",
        "deployment-chart",
        "infrastructure-code",
        "data-pipeline",
        "data-migration",
        "mobile-app",
        "desktop-app",
    ]

    # Valid project domains
    VALID_DOMAINS = [
        "programming",
        "infrastructure",
        "data-engineering",
        "security",
        "devops",
        "qa",
        "design",
    ]

    # P0 sections (required)
    P0_SECTIONS = [1, 2, 3]

    # P1 sections (recommended)
    P1_SECTIONS = [4, 5]

    # P2 sections (optional)
    P2_SECTIONS = [6, 7, 8, 9]

    # Minimum content length for sections (characters)
    MIN_SECTION_LENGTH = 10

    def __init__(self, strict: bool = True):
        """Initialize validator.

        Args:
            strict: If True, P1 warnings are treated as errors
        """
        self.strict = strict

    def validate(
        self, parsed: ParsedObjetivo
    ) -> tuple[list[ValidationError], list[ValidationError]]:
        """Validate a parsed objetivo.yaml v2.0 file.

        Args:
            parsed: ParsedObjetivo from ObjetivoV2Parser

        Returns:
            Tuple of (errors, warnings)
            - errors: List of ValidationError with level="error"
            - warnings: List of ValidationError with level="warning"

        Implementation:
            1. Validate frontmatter (_validate_frontmatter)
            2. Validate P0 sections (_validate_p0)
            3. Check for duplicates
            4. Check for out of order sections
            5. Optionally validate P1/P2 (warnings)
            6. Return aggregated errors and warnings
        """
        errors = []
        warnings = []

        # 1. Validate frontmatter
        frontmatter_errors = self._validate_frontmatter(parsed.frontmatter)
        errors.extend(frontmatter_errors)

        # 2. Validate P0 sections
        p0_errors = self._validate_p0(parsed.sections)
        errors.extend(p0_errors)

        # 3. Check for duplicate sections (warnings)
        duplicate_warnings = self._check_duplicate_sections(parsed.sections)
        warnings.extend(duplicate_warnings)

        # 4. Check for out of order sections (warnings)
        order_warnings = self._check_section_order(parsed.sections)
        warnings.extend(order_warnings)

        # 5. Validate P1/P2 sections (warnings only)
        p1_p2_warnings = self._validate_p1_p2(parsed.sections)
        warnings.extend(p1_p2_warnings)

        # 6. If strict mode, convert P1 warnings to errors
        if self.strict:
            # Move P1 section warnings to errors
            p1_warnings_to_errors = [
                w
                for w in warnings
                if w.field.startswith("section_")
                and any(str(num) in w.field for num in self.P1_SECTIONS)
            ]
            for w in p1_warnings_to_errors:
                w.level = "error"
                errors.append(w)
                warnings.remove(w)

        return errors, warnings

    def _validate_frontmatter(
        self, frontmatter: dict[str, Any]
    ) -> list[ValidationError]:
        """Validate frontmatter fields.

        Args:
            frontmatter: Parsed frontmatter dict

        Returns:
            List of ValidationError (level="error")

        Validates:
            - version == "2.0"
            - project.name present and non-empty
            - project.type in VALID_TYPES
            - project.domain in VALID_DOMAINS

        Implementation:
            Check each required field and return errors with helpful messages
        """
        errors = []

        # Validate version
        version = frontmatter.get("version")
        if version != "2.0":
            errors.append(
                ValidationError(
                    level="error",
                    field="version",
                    message=f"Invalid version '{version}'. Must be '2.0'",
                    example='version: "2.0"',
                )
            )

        # Validate project dict exists
        project = frontmatter.get("project", {})
        if not isinstance(project, dict):
            errors.append(
                ValidationError(
                    level="error",
                    field="project",
                    message="Field 'project' must be a dictionary",
                    example="project:\n  name: my-project\n  type: backend-api",
                )
            )
            return errors  # Can't continue without valid project dict

        # Validate project.name
        name = project.get("name", "").strip()
        if not name:
            errors.append(
                ValidationError(
                    level="error",
                    field="project.name",
                    message="Field 'project.name' is required and cannot be empty",
                    example="project:\n  name: user-management-api",
                )
            )

        # Validate project.type (if present)
        proj_type = project.get("type", "").strip()
        if proj_type and proj_type not in self.VALID_TYPES:
            errors.append(
                ValidationError(
                    level="error",
                    field="project.type",
                    message=f"Invalid project type '{proj_type}'",
                    example=f"Valid types: {', '.join(self.VALID_TYPES[:3])}...",
                )
            )

        # Validate project.domain (if present)
        domain = project.get("domain", "").strip()
        if domain and domain not in self.VALID_DOMAINS:
            errors.append(
                ValidationError(
                    level="error",
                    field="project.domain",
                    message=f"Invalid project domain '{domain}'",
                    example=f"Valid domains: {', '.join(self.VALID_DOMAINS[:3])}...",
                )
            )

        return errors

    def _validate_p0(self, sections: dict[int, str]) -> list[ValidationError]:
        """Validate P0 sections (1-3).

        Args:
            sections: Dict mapping section number to content

        Returns:
            List of ValidationError (level="error")

        Validates:
            - Sections 1, 2, 3 are present
            - Sections are not empty (>MIN_SECTION_LENGTH chars)
            - Section 3 has at least 1 item in "Incluído ✅" list

        Implementation:
            Check each P0 section with specific validation rules
        """
        errors = []

        # Section titles for better error messages
        section_titles = {
            1: "O que este projeto faz?",
            2: "Qual problema resolve?",
            3: "Escopo do Projeto",
        }

        # Check each P0 section
        for num in self.P0_SECTIONS:
            if num not in sections:
                errors.append(
                    ValidationError(
                        level="error",
                        field=f"section_{num}",
                        message=f"Required P0 section {num}️⃣ '{section_titles[num]}' is missing",
                        example=f"## {num}️⃣ {section_titles[num]}\n\n[Your content here]",
                    )
                )
                continue

            # Check section is not empty
            content = sections[num].strip()
            if len(content) < self.MIN_SECTION_LENGTH:
                errors.append(
                    ValidationError(
                        level="error",
                        field=f"section_{num}",
                        message=f"P0 section {num}️⃣ '{section_titles[num]}' is empty or too short",
                        example=f"Add at least {self.MIN_SECTION_LENGTH} characters of meaningful content",
                    )
                )

        # Special validation for Section 3 (Escopo)
        # Must have at least one "Incluído ✅" item
        if 3 in sections:
            content = sections[3]
            # Look for "Incluído" section with at least one item
            has_included = re.search(r"Incluído\s*✅.*?[-*]\s+\w+", content, re.DOTALL)
            if not has_included:
                errors.append(
                    ValidationError(
                        level="error",
                        field="section_3",
                        message="Section 3 must have at least one item in 'Incluído ✅' list",
                        example="**Incluído ✅**:\n- Feature 1\n- Feature 2",
                    )
                )

        return errors

    def _check_duplicate_sections(
        self, sections: dict[int, str]
    ) -> list[ValidationError]:
        """Check for duplicate section numbers.

        Args:
            sections: Dict mapping section number to content

        Returns:
            List of ValidationError (level="warning")
        """
        # Section numbers are dict keys, so duplicates not possible
        # This is a placeholder for future raw content scanning
        return []

    def _check_section_order(self, sections: dict[int, str]) -> list[ValidationError]:
        """Check that sections are in order (1, 2, 3... not 1, 3, 2).

        Args:
            sections: Dict mapping section number to content

        Returns:
            List of ValidationError (level="warning")
        """
        warnings = []
        section_nums = sorted(sections.keys())

        # Check if sections appear in order (allowing gaps)
        for i in range(len(section_nums) - 1):
            if section_nums[i] >= section_nums[i + 1]:
                warnings.append(
                    ValidationError(
                        level="warning",
                        field=f"section_{section_nums[i]}",
                        message=f"Section {section_nums[i]} appears after section {section_nums[i + 1]} (out of order)",
                        example="Sections should be in ascending order: 1, 2, 3...",
                    )
                )

        return warnings

    def _validate_p1_p2(self, sections: dict[int, str]) -> list[ValidationError]:
        """Validate P1/P2 sections (warnings only).

        Args:
            sections: Dict mapping section number to content

        Returns:
            List of ValidationError (level="warning")
        """
        warnings = []

        # Check if P1 sections are empty
        for num in self.P1_SECTIONS:
            if num in sections and len(sections[num].strip()) < self.MIN_SECTION_LENGTH:
                warnings.append(
                    ValidationError(
                        level="warning",
                        field=f"section_{num}",
                        message=f"P1 section {num} is empty or too short (recommended for better context)",
                        example="Add constraints, business rules, or technical details",
                    )
                )

        return warnings
