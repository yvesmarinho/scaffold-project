"""
objetivo_parser.py — Parser for objetivo.yaml v2.0 (Markdown Híbrido format)

Parses objetivo.yaml files in the v2.0 format which consists of:
- YAML frontmatter (metadata between --- delimiters)
- Markdown sections (## 1️⃣, ## 2️⃣, etc.)

Usage:
    from scripts.lib.objetivo_parser import ObjetivoV2Parser

    parser = ObjetivoV2Parser()
    parsed = parser.parse("objetivo.yaml")
    print(parsed.frontmatter["project"]["name"])
    print(parsed.sections[1])  # Section 1️⃣ content

Spec: specs/066-objetivo-yaml-v2/spec.md
Tasks: T006-T009
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ParsedObjetivo:
    """Dataclass representing a parsed objetivo.yaml v2.0 file.

    Attributes:
        frontmatter: Dict containing YAML frontmatter (version, project, etc.)
        sections: Dict mapping section number to content (1 -> Section 1️⃣ content)
        raw_content: Original file content
        file_path: Path to the source file
        version: Format version (extracted from frontmatter)
    """

    frontmatter: dict[str, Any]
    sections: dict[int, str]
    raw_content: str
    file_path: Path
    version: str = field(init=False)

    def __post_init__(self) -> None:
        """Extract version from frontmatter."""
        self.version = self.frontmatter.get("version", "unknown")

    @property
    def is_valid_v2(self) -> bool:
        """Check if this is a valid v2.0 format."""
        return self.version == "2.0"

    @property
    def project_name(self) -> str | None:
        """Convenience property to get project name."""
        name: str | None = self.frontmatter.get("project", {}).get("name")
        return name

    @property
    def project_type(self) -> str | None:
        """Convenience property to get project type."""
        project_type: str | None = self.frontmatter.get("project", {}).get("type")
        return project_type

    @property
    def p0_sections(self) -> dict[int, str]:
        """Get P0 sections (1-3)."""
        return {k: v for k, v in self.sections.items() if k in [1, 2, 3]}

    @property
    def p1_sections(self) -> dict[int, str]:
        """Get P1 sections (4-5)."""
        return {k: v for k, v in self.sections.items() if k in [4, 5]}

    @property
    def p2_sections(self) -> dict[int, str]:
        """Get P2 sections (6-9)."""
        return {k: v for k, v in self.sections.items() if k in [6, 7, 8, 9]}


class ObjetivoV2Parser:
    """Parser for objetivo.yaml v2.0 (Markdown Híbrido format).

    Parses files with YAML frontmatter + Markdown sections.
    Handles progressive disclosure levels (P0/P1/P2).

    Example:
        parser = ObjetivoV2Parser()
        parsed = parser.parse("objetivo.yaml")
        if parsed.is_valid_v2:
            print(f"Project: {parsed.project_name}")
    """

    # Regex patterns
    FRONTMATTER_PATTERN = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n", re.MULTILINE | re.DOTALL
    )

    # Match sections like "## 1️⃣ O que este projeto faz?"
    SECTION_PATTERN = re.compile(
        r"^##\s+(\d)️⃣\s+(.+?)(?=\n##\s+\d️⃣|\Z)", re.MULTILINE | re.DOTALL
    )

    def __init__(self) -> None:
        """Initialize parser."""
        pass

    def parse(self, file_path: str | Path) -> ParsedObjetivo:
        """Parse objetivo.yaml v2.0 file.

        Args:
            file_path: Path to objetivo.yaml file

        Returns:
            ParsedObjetivo dataclass with frontmatter and sections

        Raises:
            FileNotFoundError: If file does not exist
            yaml.YAMLError: If frontmatter YAML is invalid
            ValueError: If file format is invalid

        Implementation:
            1. Read file content
            2. Extract and parse frontmatter (_parse_frontmatter)
            3. Extract sections (_parse_sections)
            4. Return ParsedObjetivo dataclass
        """
        # Convert to Path object
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path}\n" f"Current directory: {Path.cwd()}"
            )

        # Read file content
        try:
            raw_content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"File is not valid UTF-8: {path}\n" f"Error: {e}") from e
        except Exception as e:
            raise OSError(f"Failed to read file: {path}\n" f"Error: {e}") from e

        # Parse frontmatter
        try:
            frontmatter = self._parse_frontmatter(raw_content)
        except (yaml.YAMLError, ValueError) as e:
            raise ValueError(f"Failed to parse frontmatter in {path.name}:\n{e}") from e

        # Parse sections
        # Extract content after frontmatter for section parsing
        frontmatter_match = self.FRONTMATTER_PATTERN.match(raw_content)
        if frontmatter_match:
            content_after_frontmatter = raw_content[frontmatter_match.end() :]
        else:
            content_after_frontmatter = raw_content

        sections = self._parse_sections(content_after_frontmatter)

        # Create and return ParsedObjetivo
        return ParsedObjetivo(
            frontmatter=frontmatter,
            sections=sections,
            raw_content=raw_content,
            file_path=path,
        )

    def _parse_frontmatter(self, content: str) -> dict[str, Any]:
        """Extract and parse YAML frontmatter.

        Args:
            content: Full file content

        Returns:
            Dict with parsed YAML frontmatter

        Raises:
            yaml.YAMLError: If YAML is invalid
            ValueError: If frontmatter is missing or malformed

        Implementation:
            1. Use FRONTMATTER_PATTERN regex to extract YAML block
            2. Parse with yaml.safe_load()
            3. Validate required fields (version, project.name)
            4. Return parsed dict
        """
        # Extract YAML block between --- delimiters
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            raise ValueError(
                "Missing or malformed YAML frontmatter. "
                'Expected format:\n---\nversion: "2.0"\n...\n---'
            )

        yaml_content = match.group(1)

        # Parse YAML
        try:
            frontmatter = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Invalid YAML in frontmatter: {e}\n"
                f"Check syntax near line {getattr(e, 'problem_mark', 'unknown')}"
            ) from e

        if not isinstance(frontmatter, dict):
            raise ValueError(
                f"Frontmatter must be a YAML dictionary, got {type(frontmatter).__name__}"
            )

        # Validate required fields
        if "version" not in frontmatter:
            raise ValueError(
                "Missing required field 'version' in frontmatter.\n"
                'Add: version: "2.0"'
            )

        if "project" not in frontmatter:
            raise ValueError(
                "Missing required field 'project' in frontmatter.\n"
                "Add: project:\n  name: your-project-name"
            )

        project = frontmatter.get("project", {})
        if not isinstance(project, dict):
            raise ValueError(
                f"Field 'project' must be a dictionary, got {type(project).__name__}"
            )

        if not project.get("name"):
            raise ValueError(
                "Missing required field 'project.name' in frontmatter.\n"
                "Add: project:\n  name: your-project-name"
            )

        return frontmatter

    def _parse_sections(self, content: str) -> dict[int, str]:
        """Extract Markdown sections by number.

        Args:
            content: Full file content (after frontmatter)

        Returns:
            Dict mapping section number (1-9) to section content

        Notes:
            - Handles sections with emoji numbers (1️⃣, 2️⃣, etc.)
            - Section content includes everything until next section or EOF
            - Empty sections are included with empty string value
            - Content is stripped of leading/trailing whitespace

        Implementation:
            1. Use SECTION_PATTERN regex to find all sections
            2. Extract section number and content
            3. Build dict {1: content, 2: content, ...}
            4. Handle edge cases (code blocks, tables, nested lists)
        """
        sections = {}

        # Find all section matches
        # Pattern: ## 1️⃣ Title
        # Captures: (1) number, (2) title + content until next section
        matches = list(self.SECTION_PATTERN.finditer(content))

        for i, match in enumerate(matches):
            section_num = int(match.group(1))
            match.group(2).strip()

            # Extract content from after the title line until next section or EOF
            # The match.group(0) contains the full match including ## prefix
            # We need to extract content after the title line

            # Find where this section starts and ends
            start = match.start()

            # Find the end - either next section or end of file
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(content)

            # Extract full section text
            full_section = content[start:end]

            # Remove the header line (## 1️⃣ Title)
            # Split by first newline and take everything after
            lines = full_section.split("\n", 1)
            if len(lines) > 1:
                section_content = lines[1].strip()
            else:
                section_content = ""

            sections[section_num] = section_content

        return sections
