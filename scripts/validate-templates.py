#!/usr/bin/env python3
"""
validate-templates.py — Template Validator for IMP-65-LITE

Validates the templates distributed by the scaffold (default: scaffold/templates/),
recursively:
  - YAML (multi-document) / JSON syntax validation
  - Go templates (Helm charts) are not parsed as YAML
  - Required frontmatter fields (opt-in: --require-frontmatter FIELD)
  - Variable substitution consistency
  - Markdown link validation (opt-in: --check-links — template links usually
    point to paths of the GENERATED project)

Usage:
    python scripts/validate-templates.py                    # Full validation
    python scripts/validate-templates.py --template-dir .specify/templates \
        --require-frontmatter template_version --check-links  # old IMP-65 mode
    python scripts/validate-templates.py --json             # JSON output for CI/CD
    python scripts/validate-templates.py --template spec    # Validate specific template
    python scripts/validate-templates.py --strict           # Fail on warnings

Exit codes:
    0 - All validations passed
    1 - Validation errors found
    2 - Warnings found (only with --strict)
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Templates distribuídos pelo scaffold. (`.specify/templates/` é do SpecKit,
# gerado pelo `specify init` — não é editado por este projeto.)
TEMPLATE_DIR = Path("scaffold/templates")
TEMPLATE_PATTERNS = ("*.md", "*.yaml", "*.yml", "*.json")
SKIP_DIR_NAMES = frozenset(
    {
        ".ruff_cache",
        ".mypy_cache",
        ".pytest_cache",
        "__pycache__",
        "node_modules",
        ".venv",
    }
)
# Templates Go (Helm): `{{ .Values.x }}`, `{{- include ... }}` — não são YAML válido.
# `{{ ... }}` quebrado em `{ { ... } }` por formatador de YAML: o Helm não renderiza.
BROKEN_GO_TEMPLATE_PATTERN = re.compile(
    r"\{ \{-?\s*(?:-\s*)?(?:\.|include\b|if\b|end\b|range\b|with\b|toYaml\b)"
)
# objetivo v2 ("Markdown híbrido"): frontmatter YAML + corpo Markdown, extensão .yaml
HYBRID_FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)
GO_TEMPLATE_PATTERN = re.compile(
    r"\{\{-?\s*(?:\.|include\b|if\b|else\b|end\b|range\b|with\b|define\b|template\b|toYaml\b)"
)

VARIABLE_PATTERN = re.compile(
    r"\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)\b|\[([A-Z_][A-Z0-9_]*)\]"
)
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass
class ValidationIssue:
    """Single validation issue (error or warning)"""

    severity: str  # "error" or "warning"
    file: str
    line: int | None
    message: str
    details: str | None = None


@dataclass
class ValidationResult:
    """Validation results for all templates"""

    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    files_checked: int = 0
    template_dir: str = ""

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------


class TemplateValidator:
    """Main template validation logic"""

    def __init__(
        self,
        template_dir: Path,
        required_frontmatter: tuple[str, ...] = ("template_version",),
        check_links: bool = True,
    ):
        """
        :param template_dir: raiz dos templates (busca recursiva).
        :param required_frontmatter: campos obrigatórios no frontmatter dos .md;
            vazio = frontmatter opcional (sem aviso quando ausente).
        :param check_links: valida links Markdown relativos.
        """
        self.template_dir = template_dir
        self.required_frontmatter = tuple(required_frontmatter)
        self.check_links = check_links
        self.result = ValidationResult(template_dir=str(template_dir))

    def validate_all(self, template_filter: str | None = None) -> ValidationResult:
        """Validate all templates or filtered subset"""
        if not self.template_dir.exists():
            self.result.errors.append(
                ValidationIssue(
                    severity="error",
                    file=str(self.template_dir),
                    line=None,
                    message=f"Template directory not found: {self.template_dir}",
                )
            )
            return self.result

        # Find all template files
        template_files = [
            path
            for pattern in TEMPLATE_PATTERNS
            for path in self.template_dir.rglob(pattern)
            if path.is_file()
            and not SKIP_DIR_NAMES.intersection(
                path.relative_to(self.template_dir).parts
            )
        ]

        # Filter if specified
        if template_filter:
            template_files = [f for f in template_files if template_filter in f.stem]

        if not template_files:
            self.result.warnings.append(
                ValidationIssue(
                    severity="warning",
                    file=str(self.template_dir),
                    line=None,
                    message="No template files found",
                )
            )
            return self.result

        # Validate each file
        for template_file in sorted(template_files):
            self.result.files_checked += 1
            self._validate_file(template_file)

        return self.result

    def _validate_file(self, file_path: Path):
        """Validate single template file"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            self.result.errors.append(
                ValidationIssue(
                    severity="error",
                    file=str(file_path),
                    line=None,
                    message=f"File encoding error: {e}",
                )
            )
            return
        except Exception as e:
            self.result.errors.append(
                ValidationIssue(
                    severity="error",
                    file=str(file_path),
                    line=None,
                    message=f"Failed to read file: {e}",
                )
            )
            return

        # Dispatch to specific validator
        if file_path.suffix in (".yaml", ".yml"):
            self._validate_yaml(file_path, content)
        elif file_path.suffix == ".json":
            self._validate_json(file_path, content)
        elif file_path.suffix == ".md":
            self._validate_markdown(file_path, content)

    def _validate_yaml(self, file_path: Path, content: str):
        """Validate YAML file syntax (multi-document; Go templates skipped)"""
        corrompido = BROKEN_GO_TEMPLATE_PATTERN.search(content)
        if corrompido:
            self.result.errors.append(
                ValidationIssue(
                    severity="error",
                    file=str(file_path),
                    line=content[: corrompido.start()].count("\n") + 1,
                    message="Go template corrompido: '{ {' em vez de '{{' (não renderiza no Helm)",
                    details="Provável formatador de YAML aplicado a template Go",
                )
            )
            return
        hibrido = HYBRID_FRONTMATTER_PATTERN.match(content)
        if hibrido and re.search(r"^#{1,6} ", hibrido.group(2), re.MULTILINE):
            content = hibrido.group(1)  # valida só o frontmatter; o corpo é Markdown
        if GO_TEMPLATE_PATTERN.search(content):
            return  # template Go (ex.: Helm) — validado pelo `helm lint`, não por YAML
        try:
            docs = [doc for doc in yaml.safe_load_all(content) if doc is not None]
            if not docs:
                self.result.warnings.append(
                    ValidationIssue(
                        severity="warning",
                        file=str(file_path),
                        line=None,
                        message="YAML file is empty",
                    )
                )
        except yaml.YAMLError as e:
            self.result.errors.append(
                ValidationIssue(
                    severity="error",
                    file=str(file_path),
                    line=getattr(e, "problem_mark", None) and e.problem_mark.line + 1,
                    message=f"YAML syntax error: {e}",
                )
            )

    def _validate_json(self, file_path: Path, content: str):
        """Validate JSON file syntax"""
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            self.result.errors.append(
                ValidationIssue(
                    severity="error",
                    file=str(file_path),
                    line=e.lineno,
                    message=f"JSON syntax error: {e.msg}",
                )
            )

    def _validate_markdown(self, file_path: Path, content: str):
        """Validate Markdown template"""
        # Extract frontmatter
        frontmatter = self._extract_frontmatter(content)

        # Validate frontmatter (só quando há campos obrigatórios configurados)
        if frontmatter:
            self._validate_frontmatter(file_path, frontmatter)
        elif self.required_frontmatter:
            self.result.warnings.append(
                ValidationIssue(
                    severity="warning",
                    file=str(file_path),
                    line=1,
                    message="No YAML frontmatter found",
                )
            )

        # Validate links
        if self.check_links:
            self._validate_markdown_links(file_path, content)

        # Validate variables
        self._validate_variables(file_path, content)

    def _extract_frontmatter(self, content: str) -> dict[str, Any] | None:
        """Extract YAML frontmatter from Markdown"""
        lines = content.split("\n")
        if not lines or lines[0].strip() != "---":
            return None

        frontmatter_lines = []
        for _i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                frontmatter_text = "\n".join(frontmatter_lines)
                try:
                    return yaml.safe_load(frontmatter_text) or {}
                except yaml.YAMLError:
                    return None
            frontmatter_lines.append(line)

        return None

    def _validate_frontmatter(self, file_path: Path, frontmatter: dict[str, Any]):
        """Validate frontmatter required fields"""
        # Check required fields
        for campo in self.required_frontmatter:
            if campo not in frontmatter:
                self.result.errors.append(
                    ValidationIssue(
                        severity="error",
                        file=str(file_path),
                        line=1,
                        message=f"Missing required frontmatter field: {campo}",
                        details=f"Required fields: {', '.join(self.required_frontmatter)}",
                    )
                )

        # Validate template_version format
        if "template_version" in frontmatter:
            version = frontmatter["template_version"]
            if not re.match(r"^\d+\.\d+\.\d+$", str(version)):
                self.result.warnings.append(
                    ValidationIssue(
                        severity="warning",
                        file=str(file_path),
                        line=1,
                        message=f"template_version should follow semver format (x.y.z): {version}",
                    )
                )

        # Warn on breaking_changes without justification
        if frontmatter.get("breaking_changes") is True:
            if (
                "breaking_reason" not in frontmatter
                and "breaking_change_notes" not in frontmatter
            ):
                self.result.warnings.append(
                    ValidationIssue(
                        severity="warning",
                        file=str(file_path),
                        line=1,
                        message="breaking_changes=true but no breaking_reason or breaking_change_notes campo",
                    )
                )

    def _validate_markdown_links(self, file_path: Path, content: str):
        """Validate Markdown links"""
        for match in MARKDOWN_LINK_PATTERN.finditer(content):
            link_text = match.group(1)
            link_url = match.group(2)

            # Skip external links (http/https)
            if link_url.startswith(("http://", "https://", "#")):
                continue

            # Validate file references
            if link_url.startswith(("./", "../", "/")):
                # Resolve relative path
                link_path = (file_path.parent / link_url).resolve()

                # Check if file exists
                if not link_path.exists():
                    # Extract line number
                    line_num = content[: match.start()].count("\n") + 1
                    self.result.warnings.append(
                        ValidationIssue(
                            severity="warning",
                            file=str(file_path),
                            line=line_num,
                            message=f"Broken link: [{link_text}]({link_url})",
                            details=f"Target file not found: {link_path}",
                        )
                    )

    def _validate_variables(self, file_path: Path, content: str):
        """Validate variable substitution placeholders"""
        # Extract all variables
        variables = set()
        for match in VARIABLE_PATTERN.finditer(content):
            var = match.group(1) or match.group(2) or match.group(3)
            if var:
                variables.add(var)

        # Check for common issues
        for var in variables:
            # Warn on lowercase variables (convention is uppercase)
            if var != var.upper():
                line_num = content[: content.find(var)].count("\n") + 1
                self.result.warnings.append(
                    ValidationIssue(
                        severity="warning",
                        file=str(file_path),
                        line=line_num,
                        message=f"Variable should be uppercase: {var}",
                        details="Convention: ${UPPERCASE_VAR}",
                    )
                )


# ---------------------------------------------------------------------------
# Output Formatters
# ---------------------------------------------------------------------------


def format_console(result: ValidationResult) -> str:
    """Format validation results for console output"""
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("TEMPLATE VALIDATION RESULTS")
    lines.append("=" * 70)
    lines.append(f"Template dir: {result.template_dir}")
    lines.append(f"Files checked: {result.files_checked}")
    lines.append("")

    # Errors
    if result.errors:
        lines.append(f"❌ ERRORS ({len(result.errors)}):")
        lines.append("-" * 70)
        for issue in result.errors:
            location = f"{issue.file}"
            if issue.line:
                location += f":{issue.line}"
            lines.append(f"  {location}")
            lines.append(f"    {issue.message}")
            if issue.details:
                lines.append(f"    Details: {issue.details}")
            lines.append("")

    # Warnings
    if result.warnings:
        lines.append(f"⚠️  WARNINGS ({len(result.warnings)}):")
        lines.append("-" * 70)
        for issue in result.warnings:
            location = f"{issue.file}"
            if issue.line:
                location += f":{issue.line}"
            lines.append(f"  {location}")
            lines.append(f"    {issue.message}")
            if issue.details:
                lines.append(f"    Details: {issue.details}")
            lines.append("")

    # Summary
    lines.append("=" * 70)
    if result.success:
        if result.has_warnings:
            lines.append("✅ PASSED (with warnings)")
        else:
            lines.append("✅ PASSED")
    else:
        lines.append("❌ FAILED")
    lines.append("=" * 70)

    return "\n".join(lines)


def format_json(result: ValidationResult) -> str:
    """Format validation results as JSON"""
    data = {
        "success": result.success,
        "template_dir": result.template_dir,
        "files_checked": result.files_checked,
        "errors": [
            {
                "severity": issue.severity,
                "file": issue.file,
                "line": issue.line,
                "message": issue.message,
                "details": issue.details,
            }
            for issue in result.errors
        ],
        "warnings": [
            {
                "severity": issue.severity,
                "file": issue.file,
                "line": issue.line,
                "message": issue.message,
                "details": issue.details,
            }
            for issue in result.warnings
        ],
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Validate scaffold templates (default: scaffold/templates/)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--template",
        help="Validate specific template (e.g., 'spec' matches spec-template.md)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--strict", action="store_true", help="Fail on warnings (exit code 2)"
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        default=TEMPLATE_DIR,
        help=f"Template directory (default: {TEMPLATE_DIR})",
    )

    parser.add_argument(
        "--require-frontmatter",
        action="append",
        default=[],
        metavar="FIELD",
        help="Campo obrigatório no frontmatter dos .md (repetível; padrão: nenhum)",
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="Valida links Markdown relativos (padrão: desligado)",
    )

    args = parser.parse_args()

    # Run validation
    validator = TemplateValidator(
        args.template_dir,
        required_frontmatter=tuple(args.require_frontmatter),
        check_links=args.check_links,
    )
    result = validator.validate_all(template_filter=args.template)

    # Output results
    if args.json:
        print(format_json(result))
    else:
        print(format_console(result))

    # Exit code
    if not result.success:
        sys.exit(1)
    elif args.strict and result.has_warnings:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
