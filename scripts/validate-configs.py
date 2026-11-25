#!/usr/bin/env python3
"""
Configuration validation script.

IMP-65 P0: Detect obsolete configurations to prevent BUG-20 recurrence

Validates:
1. MCP GitHub server configuration (CLI vs HTTP)
2. pyproject.toml critical dependencies pinning
3. .copilot-rules.md exists and is not empty

Usage:
    python scripts/validate-configs.py                    # Validate all
    python scripts/validate-configs.py --check mcp.json   # Validate specific
    make config-validate                                  # Via Makefile

Exit codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Critical dependencies that should be pinned
CRITICAL_DEPS = ["bandit", "safety", "pytest"]


def validate_mcp_github() -> bool:
    """
    Validate MCP GitHub server configuration.

    Check that GitHub server uses HTTP (not obsolete CLI).

    Returns:
        True if valid, False otherwise
    """
    mcp_config_path = PROJECT_ROOT / ".vscode" / "mcp.json"

    if not mcp_config_path.exists():
        log.error("❌ .vscode/mcp.json not found")
        return False

    try:
        with open(mcp_config_path) as f:
            mcp_config = json.load(f)
    except json.JSONDecodeError as e:
        log.error(f"❌ Invalid JSON in mcp.json: {e}")
        return False

    # Check if GitHub server is configured
    github_server = mcp_config.get("mcpServers", {}).get("github")

    if not github_server:
        log.warning("⚠️  GitHub MCP server not configured (acceptable)")
        return True  # Not configured is OK

    # Check command - should be "npx" for HTTP, not "python" or "uvx" for CLI
    command = github_server.get("command", "")

    if command == "npx":
        # HTTP configuration (correct)
        args = github_server.get("args", [])
        if "-y" in args and "@modelcontextprotocol/server-github" in args:
            log.info("✅ MCP GitHub: HTTP configuration (correct)")
            return True
        else:
            log.warning("⚠️  MCP GitHub: npx command but unexpected args")
            return True  # Assume OK

    elif command in ["python", "uvx", "uv"]:
        # CLI configuration (obsolete)
        log.error("❌ MCP GitHub: Using obsolete CLI configuration")
        log.error("   Update to HTTP: npx -y @modelcontextprotocol/server-github")
        log.error("   See: docs/guides/MCP-GITHUB-HTTP-UPDATE.md")
        return False

    else:
        log.warning(f"⚠️  MCP GitHub: Unknown command '{command}'")
        return True  # Assume OK if unknown


def validate_pyproject_toml() -> bool:
    """
    Validate pyproject.toml for critical dependency pinning.

    Returns:
        True if valid, False otherwise
    """
    pyproject_path = PROJECT_ROOT / "pyproject.toml"

    if not pyproject_path.exists():
        log.error("❌ pyproject.toml not found")
        return False

    try:
        import tomllib
    except ImportError:
        # Python < 3.11
        try:
            import tomli as tomllib  # type: ignore[import-not-found, no-redef]  # fallback Python<3.11 (requires-python>=3.12)
        except ImportError:
            log.warning(
                "⚠️  toml library not available (skipping pyproject.toml check)"
            )
            return True  # Skip validation if no TOML parser

    try:
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
    except Exception as e:
        log.error(f"❌ Failed to parse pyproject.toml: {e}")
        return False

    # Check optional dependencies (dev, security groups)
    optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
    all_deps = []

    for _group_name, deps in optional_deps.items():
        all_deps.extend(deps)

    # Check if critical deps are present and pinned
    issues = []
    for dep_name in CRITICAL_DEPS:
        # Find dep in list (format: "package>=1.0.0" or "package==1.0.0")
        found = False
        for dep_str in all_deps:
            if dep_str.startswith(f"{dep_name}==") or dep_str.startswith(
                f"{dep_name}>="
            ):
                found = True
                log.info(f"✅ {dep_name}: {dep_str}")
                break

        if not found:
            issues.append(f"❌ {dep_name}: not found or not pinned")

    if issues:
        log.error("❌ Critical dependencies not properly pinned:")
        for issue in issues:
            log.error(f"   {issue}")
        return False

    log.info("✅ Critical dependencies properly configured")
    return True


def validate_copilot_rules() -> bool:
    """
    Validate .copilot-rules.md exists and is not empty.

    Returns:
        True if valid, False otherwise
    """
    copilot_rules_path = PROJECT_ROOT / ".copilot-rules.md"

    if not copilot_rules_path.exists():
        log.error("❌ .copilot-rules.md not found")
        log.error("   Critical file missing - Copilot rules won't be enforced")
        return False

    # Check file is not empty
    content = copilot_rules_path.read_text()
    if len(content.strip()) < 100:
        log.error("❌ .copilot-rules.md is too small (likely empty or corrupted)")
        return False

    # Check has critical sections
    critical_sections = ["P0", "P1", "Criar/Editar Arquivos", "Git Commits"]
    missing_sections = []

    for section in critical_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        log.warning(
            f"⚠️  .copilot-rules.md missing sections: {', '.join(missing_sections)}"
        )
        # Warning only, not failure

    log.info(
        f"✅ .copilot-rules.md exists ({len(content)} chars, {content.count('##')} sections)"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configuration validation script (IMP-65 P0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/validate-configs.py               # Validate all
  python scripts/validate-configs.py --check mcp   # Validate MCP only
  make config-validate                             # Via Makefile
        """,
    )
    parser.add_argument(
        "--check",
        choices=["mcp", "pyproject", "copilot", "all"],
        default="all",
        help="Which configuration to validate (default: all)",
    )

    args = parser.parse_args()

    # Banner
    log.info("=" * 70)
    log.info("Configuration Validation (IMP-65 P0)")
    log.info("=" * 70)
    log.info("")

    results = {}

    # Run validations
    if args.check in ["mcp", "all"]:
        log.info("Validating MCP GitHub configuration...")
        results["mcp"] = validate_mcp_github()
        log.info("")

    if args.check in ["pyproject", "all"]:
        log.info("Validating pyproject.toml...")
        results["pyproject"] = validate_pyproject_toml()
        log.info("")

    if args.check in ["copilot", "all"]:
        log.info("Validating .copilot-rules.md...")
        results["copilot"] = validate_copilot_rules()
        log.info("")

    # Summary
    log.info("=" * 70)
    log.info("Summary")
    log.info("=" * 70)

    failed = [name for name, passed in results.items() if not passed]
    passed = [name for name, passed in results.items() if passed]

    if passed:
        log.info(f"✅ Passed: {', '.join(passed)}")

    if failed:
        log.error(f"❌ Failed: {', '.join(failed)}")
        log.error("")
        log.error("Configuration validation FAILED")
        log.error("Fix the issues above before proceeding")
        log.info("=" * 70)
        return 1
    else:
        log.info("")
        log.info("✅ All validations passed")
        log.info("=" * 70)
        return 0


if __name__ == "__main__":
    sys.exit(main())
