"""
Template versioning and drift detection for SpecKit templates.

This module provides functionality to:
- Parse template versions from YAML frontmatter
- Compare local vs upstream template versions
- Detect template drift (outdated templates)
- Generate version reports
- Store and retrieve template base content for three-way merge (Phase 3)

Part of IMP-65 (Template Synchronization System) Phases 1-3.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class TemplateVersion:
    """Version information extracted from template frontmatter."""
    name: str
    version: str
    last_updated: str
    breaking_changes: bool
    path: Path


@dataclass
class TemplateDrift:
    """Comparison result between local and upstream template versions."""
    name: str
    local_version: Optional[str]
    upstream_version: str
    is_outdated: bool
    is_missing: bool
    breaking_changes: bool
    local_path: Optional[Path]
    upstream_path: Path


# ---------------------------------------------------------------------------
# Version Parsing
# ---------------------------------------------------------------------------

def parse_template_version(template_path: Path) -> Optional[TemplateVersion]:
    """
    Parse template version metadata from YAML frontmatter.

    Args:
        template_path: Path to template file

    Returns:
        TemplateVersion object if frontmatter exists, None otherwise

    Example frontmatter:
        ---
        template_version: "1.0.0"
        last_updated: "2026-04-14"
        breaking_changes: false
        ---
    """
    if not template_path.exists():
        log.warning("Template file not found: %s", template_path)
        return None

    try:
        content = template_path.read_text(encoding="utf-8")

        # Extract YAML frontmatter (between --- delimiters)
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            log.debug("No YAML frontmatter found in %s", template_path.name)
            return None

        frontmatter = yaml.safe_load(match.group(1))

        if not isinstance(frontmatter, dict):
            log.warning("Invalid frontmatter in %s", template_path.name)
            return None

        version = frontmatter.get("template_version")
        if not version:
            log.debug("No template_version in frontmatter of %s", template_path.name)
            return None

        return TemplateVersion(
            name=template_path.name,
            version=str(version),
            last_updated=frontmatter.get("last_updated", "unknown"),
            breaking_changes=frontmatter.get("breaking_changes", False),
            path=template_path,
        )

    except Exception as exc:
        log.error("Failed to parse template %s: %s", template_path.name, exc)
        return None


def parse_version_tuple(version_str: str) -> tuple[int, int, int] | None:
    """
    Parse semantic version string into (major, minor, patch) tuple.

    Args:
        version_str: Version string like "1.2.3"

    Returns:
        Tuple of (major, minor, patch) integers, or None if invalid
    """
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_str)
    if not match:
        return None
    return tuple(map(int, match.groups()))


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two semantic version strings.

    Args:
        v1: First version string
        v2: Second version string

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
         0 if either version is invalid
    """
    t1 = parse_version_tuple(v1)
    t2 = parse_version_tuple(v2)

    if t1 is None or t2 is None:
        log.error("Version comparison failed: invalid version string")
        return 0

    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    else:
        return 0


# ---------------------------------------------------------------------------
# Drift Detection
# ---------------------------------------------------------------------------

def scan_templates(template_dir: Path) -> dict[str, TemplateVersion]:
    """
    Scan directory for templates and extract version metadata.

    Args:
        template_dir: Path to directory containing template files

    Returns:
        Dictionary mapping template name to TemplateVersion
    """
    templates = {}

    if not template_dir.exists():
        log.warning("Template directory not found: %s", template_dir)
        return templates

    for template_file in sorted(template_dir.glob("*.md")):
        version_info = parse_template_version(template_file)
        if version_info:
            templates[version_info.name] = version_info

    log.info("Scanned %d templates from %s", len(templates), template_dir)
    return templates


def detect_drift(
    local_templates: dict[str, TemplateVersion],
    upstream_templates: dict[str, TemplateVersion],
) -> list[TemplateDrift]:
    """
    Detect drift between local and upstream templates.

    Args:
        local_templates: Templates from project's .specify/templates/
        upstream_templates: Templates from scaffold-project/.specify/templates/

    Returns:
        List of TemplateDrift objects for templates that are:
        - Outdated (local version < upstream version)
        - Missing (exists in upstream but not in local)
    """
    drifts = []

    for name, upstream in upstream_templates.items():
        local = local_templates.get(name)

        if local is None:
            # Template exists in upstream but not local (missing)
            drifts.append(TemplateDrift(
                name=name,
                local_version=None,
                upstream_version=upstream.version,
                is_outdated=False,
                is_missing=True,
                breaking_changes=upstream.breaking_changes,
                local_path=None,
                upstream_path=upstream.path,
            ))
        elif compare_versions(local.version, upstream.version) < 0:
            # Local version is older than upstream (outdated)
            drifts.append(TemplateDrift(
                name=name,
                local_version=local.version,
                upstream_version=upstream.version,
                is_outdated=True,
                is_missing=False,
                breaking_changes=upstream.breaking_changes,
                local_path=local.path,
                upstream_path=upstream.path,
            ))

    return drifts


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def generate_drift_report(drifts: list[TemplateDrift]) -> str:
    """
    Generate human-readable report of template drift.

    Args:
        drifts: List of TemplateDrift objects

    Returns:
        Formatted report string
    """
    if not drifts:
        return "✅ All templates are up-to-date!"

    lines = []
    lines.append(f"⚠️  Template Drift Detected: {len(drifts)} template(s) need attention\n")

    outdated = [d for d in drifts if d.is_outdated]
    missing = [d for d in drifts if d.is_missing]

    if outdated:
        lines.append(f"📊 Outdated templates ({len(outdated)}):")
        for drift in outdated:
            breaking = " 🔴 BREAKING" if drift.breaking_changes else ""
            lines.append(f"  • {drift.name}: {drift.local_version} → {drift.upstream_version}{breaking}")
        lines.append("")

    if missing:
        lines.append(f"❌ Missing templates ({len(missing)}):")
        for drift in missing:
            lines.append(f"  • {drift.name}: v{drift.upstream_version} (not found in project)")
        lines.append("")

    lines.append("Run 'scaffold.py diff-template <name>' to see changes (Phase 2)")

    return "\n".join(lines)


def generate_drift_json(drifts: list[TemplateDrift]) -> dict:
    """
    Generate machine-readable JSON report of template drift.

    Args:
        drifts: List of TemplateDrift objects

    Returns:
        Dictionary suitable for JSON serialization
    """
    return {
        "drift_detected": len(drifts) > 0,
        "total_drifts": len(drifts),
        "outdated_count": sum(1 for d in drifts if d.is_outdated),
        "missing_count": sum(1 for d in drifts if d.is_missing),
        "breaking_changes": any(d.breaking_changes for d in drifts),
        "templates": [
            {
                "name": d.name,
                "local_version": d.local_version,
                "upstream_version": d.upstream_version,
                "is_outdated": d.is_outdated,
                "is_missing": d.is_missing,
                "breaking_changes": d.breaking_changes,
            }
            for d in drifts
        ],
    }


# ---------------------------------------------------------------------------
# Template Base Storage (Phase 3: Three-Way Merge Support)
# ---------------------------------------------------------------------------

def save_template_base(
    project_dir: Path,
    template_name: str,
    version: str,
    content: str,
) -> None:
    """
    Save base template content to .scaffold-state.yaml for three-way merge.

    This stores the original template content at the time of project creation
    or last merge, enabling three-way merge (base, local, upstream) in Phase 3.

    Args:
        project_dir: Path to project root directory
        template_name: Name of template file (e.g., "spec-template.md")
        version: Template version being saved
        content: Full template content including frontmatter

    Side effects:
        Updates .scaffold-state.yaml with template_bases field
    """
    state_path = project_dir / ".scaffold-state.yaml"

    # Load existing state
    state = {}
    if state_path.exists():
        try:
            with state_path.open(encoding="utf-8") as f:
                state = yaml.safe_load(f) or {}
        except Exception as exc:
            log.warning("Failed to read scaffold state: %s", exc)
            return

    # Ensure template_bases field exists
    if "template_bases" not in state:
        state["template_bases"] = {}

    # Store base content
    state["template_bases"][template_name] = {
        "version": version,
        "content": content,
    }

    # Write back to state file
    try:
        with state_path.open("w", encoding="utf-8") as f:
            yaml.dump(state, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        log.info("✅ Saved base for %s (v%s) to scaffold state", template_name, version)
    except Exception as exc:
        log.error("Failed to save template base: %s", exc)


def load_template_base(project_dir: Path, template_name: str) -> Optional[tuple[str, str]]:
    """
    Load base template content from .scaffold-state.yaml.

    Args:
        project_dir: Path to project root directory
        template_name: Name of template file (e.g., "spec-template.md")

    Returns:
        Tuple of (version, content) if base exists, None otherwise
    """
    state_path = project_dir / ".scaffold-state.yaml"

    if not state_path.exists():
        log.debug("No scaffold state file found at %s", state_path)
        return None

    try:
        with state_path.open(encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}

        template_bases = state.get("template_bases", {})
        base_data = template_bases.get(template_name)

        if not base_data:
            log.debug("No base stored for template %s", template_name)
            return None

        version = base_data.get("version")
        content = base_data.get("content")

        if not version or not content:
            log.warning("Incomplete base data for template %s", template_name)
            return None

        log.debug("Loaded base for %s (v%s)", template_name, version)
        return (version, content)

    except Exception as exc:
        log.error("Failed to load template base: %s", exc)
        return None


def save_all_template_bases(
    project_dir: Path,
    template_dir: Path,
) -> int:
    """
    Save base content for all templates in a directory.

    Useful for initializing template bases for an existing project that
    doesn't have them yet.

    Args:
        project_dir: Path to project root directory
        template_dir: Path to directory containing template files

    Returns:
        Number of templates saved
    """
    if not template_dir.exists():
        log.warning("Template directory not found: %s", template_dir)
        return 0

    count = 0
    for template_file in sorted(template_dir.glob("*.md")):
        version_info = parse_template_version(template_file)
        if not version_info:
            continue

        content = template_file.read_text(encoding="utf-8")
        save_template_base(
            project_dir=project_dir,
            template_name=template_file.name,
            version=version_info.version,
            content=content,
        )
        count += 1

    log.info("✅ Saved %d template bases", count)
    return count
