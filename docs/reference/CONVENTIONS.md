# Technical Conventions & Standards

**Project Template**: Enterprise Scaffold Project
**Version**: 1.3.0
**Last Updated**: 2026-03-20

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Code Structure](#code-structure)
3. [Naming Conventions](#naming-conventions)
4. [Python Standards](#python-standards)
5. [Testing Standards](#testing-standards)
6. [Git Conventions](#git-conventions)
7. [Documentation Standards](#documentation-standards)
8. [Security Standards](#security-standards)
9. [File Organization](#file-organization)
10. [Automation Standards](#automation-standards)

---

## Overview

This document defines the technical conventions and standards for projects generated from this template. Following these conventions ensures:

- **Consistency**: Code is uniform across the project
- **Maintainability**: Easy to understand and modify
- **Quality**: High standards prevent common issues
- **Collaboration**: Team members follow same practices

### Enforcement

Conventions are enforced through:
- ✅ **Pre-commit hooks** (`.pre-commit-config.yaml`)
- ✅ **CI/CD pipelines** (GitHub Actions)
- ✅ **Code review** guidelines
- ✅ **Automated tooling** (Black, Ruff, MyPy, Bandit)

---

## Code Structure

### Python

Follow **PEP 8** with these specific settings:

```python
# Line length: 88 characters (Black default)
# Target Python version: 3.12+
# Use type hints for all public functions
# Docstrings required for public APIs
```

**Directory Structure**:
```
project/
├── src/                    # Source code
│   ├── __init__.py
│   ├── utils/             # Utility modules
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── cli/               # Command-line interfaces
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── fixtures/         # Test data
└── scripts/               # Automation scripts
    └── lib/              # Script modules
```

### Markdown

- **Headers**: Use ATX-style (`#` prefix)
- **Lists**: Use `-` for unordered lists
- **Code blocks**: Use triple backticks with language
- **Line length**: Soft limit of 80 characters
- **Links**: Use reference-style for repeated links

**Example**:
```markdown
# Main Title

## Section

- Item 1
- Item 2

```python
code here
```

See [link reference][ref].

[ref]: https://example.com
```

### YAML/Ansible

```yaml
# Indentation: 2 spaces (no tabs)
# Quote strings containing special characters
# Use --- document separator
# Comments: Explain non-obvious configurations

---
- name: Example playbook
  hosts: all
  become: true

  tasks:
    - name: Install package
      ansible.builtin.apt:
        name: nginx
        state: present
```

### Shell Scripts

```bash
#!/usr/bin/env bash
# Description at top
# shellcheck compliance required

set -euo pipefail  # Strict error handling

# Constants in UPPER_CASE
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Functions in snake_case
function do_something() {
    local input="$1"
    echo "Processing: ${input}"
}
```

---

## Naming Conventions

### Files & Directories

| Type | Convention | Example |
|------|------------|---------|
| Python modules | `snake_case.py` | `user_service.py` |
| Python classes | `PascalCase` | `UserService` |
| Python functions | `snake_case` | `get_user_data()` |
| Test files | `test_*.py` | `test_user_service.py` |
| Shell scripts | `kebab-case.sh` | `deploy-service.sh` |
| Ansible playbooks | `verb-noun.yml` | `deploy-docker-service.yml` |
| Ansible roles | `snake_case` | `docker_setup` |
| Config files | `kebab-case.ext` | `pytest.ini`, `mcp-config.json` |
| Markdown files | `SCREAMING_SNAKE.md` | `README.md`, `TODO.md` |
| Session docs | `TYPE_DATE.md` | `SESSION_REPORT_2026-03-20.md` |

### Variables

| Context | Convention | Example |
|---------|------------|---------|
| Python variables | `snake_case` | `user_name` |
| Python constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Environment vars | `UPPER_SNAKE_CASE` | `DATABASE_URL` |
| Ansible variables | `snake_case` | `mysql_port` |
| Ansible vault vars | `vault_*` prefix | `vault_mysql_password` |
| Private attributes | `_leading_underscore` | `_internal_state` |
| Class attributes | `snake_case` | `user_count` |

### Functions & Methods

```python
# Public function
def calculate_total(items: list) -> float:
    """Calculate total from items."""
    pass

# Private function
def _validate_input(data: dict) -> bool:
    """Internal validation."""
    pass

# Dunder methods
def __init__(self):
    """Constructor."""
    pass
```

---

## Python Standards

### Type Hints

**Required for all public APIs**:

```python
from typing import Optional, List, Dict, Any
from pathlib import Path

def process_file(
    file_path: Path,
    encoding: str = "utf-8",
    max_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process file and return results.

    Args:
        file_path: Path to input file
        encoding: File encoding (default: utf-8)
        max_size: Maximum file size in bytes

    Returns:
        Dictionary with processing results

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file exceeds max_size
    """
    result: Dict[str, Any] = {}
    # Implementation
    return result
```

### Docstrings

Use **Google Style** docstrings:

```python
def function(arg1: str, arg2: int = 0) -> bool:
    """
    Short description (one line).

    Longer description with more details about what
    the function does and any important behavior.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2 (default: 0)

    Returns:
        Description of return value

    Raises:
        ValueError: When arg1 is empty
        TypeError: When arg2 is not integer

    Examples:
        >>> function("test", 5)
        True

        >>> function("", 0)
        Traceback (most recent call last):
        ValueError: arg1 cannot be empty
    """
    if not arg1:
        raise ValueError("arg1 cannot be empty")
    return len(arg1) > arg2
```

### Imports

```python
"""Module docstring first."""

# Standard library imports (alphabetical)
import os
import sys
from pathlib import Path
from typing import Optional

# Third-party imports (alphabetical)
import pytest
import requests
from rich.console import Console

# Local imports (alphabetical, relative)
from .config import load_config
from .utils import validate_input
```

### Error Handling

```python
# Specific exceptions
try:
    result = risky_operation()
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
    raise
except ValueError as e:
    logger.warning(f"Invalid value: {e}")
    return default_value
except Exception as e:
    logger.exception("Unexpected error")
    raise RuntimeError(f"Operation failed: {e}") from e
finally:
    cleanup()

# Context managers for resources
with open(file_path) as f:
    data = f.read()

# Custom exceptions
class ValidationError(Exception):
    """Raised when validation fails."""
    pass
```

### Logging

```python
import logging

# Module-level logger
logger = logging.getLogger(__name__)

# Log levels (use appropriately)
logger.debug("Detailed debug information")     # Development only
logger.info("Normal operation message")        # Important events
logger.warning("Warning about potential issue") # Attention needed
logger.error("Error occurred")                 # Recoverable errors
logger.critical("Critical failure")            # System failure
logger.exception("Error with traceback")       # In except block

# Structured logging
logger.info(
    "User action",
    extra={
        "user_id": user.id,
        "action": "login",
        "status": "success"
    }
)
```

---

## Testing Standards

### Test Organization

```python
"""Test module docstring explaining what's being tested."""

import pytest
from unittest.mock import Mock, patch

# Test class per component
class TestUserService:
    """Tests for UserService class."""

    # Arrange-Act-Assert pattern
    def test_create_user_success(self):
        """Test successful user creation."""
        # Arrange
        service = UserService()
        user_data = {"name": "John", "email": "john@example.com"}

        # Act
        result = service.create_user(user_data)

        # Assert
        assert result.name == "John"
        assert result.email == "john@example.com"
        assert result.is_active is True

    def test_create_user_invalid_email_raises_error(self):
        """Test that invalid email raises ValueError."""
        service = UserService()

        with pytest.raises(ValueError, match="Invalid email"):
            service.create_user({"name": "John", "email": "invalid"})
```

### Test Coverage

- **Target**: ≥80% overall coverage
- **Critical modules**: ≥90% coverage
- **Exceptions allowed**: UI code, CLI output formatting

```bash
# Run with coverage
pytest --cov --cov-report=term-missing

# Check specific module
pytest --cov=src.services --cov-report=html
```

### Test Markers

```python
@pytest.mark.unit
def test_fast():
    """Fast isolated test."""
    pass

@pytest.mark.integration
@pytest.mark.requires_docker
def test_with_docker():
    """Integration test needing Docker."""
    pass

@pytest.mark.slow
def test_performance():
    """Slow test (>1 second)."""
    pass

@pytest.mark.security
def test_no_secrets_in_logs():
    """Security-related test."""
    pass
```

### Fixtures

```python
# Shared fixtures in conftest.py
@pytest.fixture
def sample_user():
    """Provide sample user for tests."""
    return User(name="Test", email="test@example.com")

# Scope for expensive setup
@pytest.fixture(scope="session")
def database():
    """Set up test database once per session."""
    db = create_test_db()
    yield db
    db.cleanup()

# Parameterized fixtures
@pytest.fixture(params=["sqlite", "postgres"])
def db_engine(request):
    """Test with multiple database engines."""
    return create_engine(request.param)
```

---

## Git Conventions

### Commit Messages

Follow **Conventional Commits**:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `security`: Security fixes

**Scopes** (examples):
- `api`, `cli`, `docs`, `tests`, `security`, `docker`, `ansible`, `python`

**Examples**:
```bash
feat(api): add user authentication endpoint

fix(security): prevent SQL injection in search

docs(readme): update installation instructions

test(auth): add integration tests for login flow

refactor(services): extract common validation logic

chore(deps): update pytest to 8.1.0
```

### Branch Naming

```bash
# Feature branches
NNN-short-description      # 018-user-authentication

# Bug fixes
fix-issue-description      # fix-login-timeout

# Security fixes
security-cve-number       # security-cve-2024-1234

# Documentation
docs-topic                 # docs-api-guide

# Current branch
git branch --show-current
```

### Pull Requests

**Title**: Same format as commit message
```
feat(api): add user authentication endpoint
```

**Description template**:
```markdown
## Description
Brief description of changes

## Changes
- Added feature X
- Fixed bug Y
- Updated documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows conventions
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No security issues
- [ ] Pre-commit hooks pass
```

---

## Documentation Standards

### README Structure

```markdown
# Project Title

Brief description (1-2 sentences)

## Features
- Feature 1
- Feature 2

## Installation
Step-by-step instructions

## Usage
Basic usage examples

## Configuration
Configuration options

## Development
Development setup

## Testing
How to run tests

## Deployment
Deployment instructions

## Contributing
Contribution guidelines

## License
License information
```

### Inline Documentation

```python
# Good: Explains WHY, not WHAT
# Calculate total using compound interest formula
# because simple interest doesn't account for monthly compounding
total = principal * (1 + rate/12) ** months

# Bad: States the obvious
# Add 1 to counter
counter = counter + 1
```

### Session Documentation

For project sessions, maintain:

```
docs/SESSIONS/YYYY-MM-DD/
├── SESSION_RECOVERY_YYYY-MM-DD.md    # Context recovery
├── DAILY_ACTIVITIES_YYYY-MM-DD.md   # Activity log
├── SESSION_REPORT_YYYY-MM-DD.md     # Technical report
└── FINAL_STATUS_YYYY-MM-DD.md       # Completion status
```

---

## Security Standards

### Credentials & Secrets

```bash
# NEVER commit secrets
# Store in .secrets/ directory (gitignored)

.secrets/
├── .env                 # Environment variables
├── .vault_pass         # Ansible vault password
├── ssh/
│   ├── id_rsa         # SSH private keys
│   └── id_rsa.pub
└── README.md           # Security guidelines

# Use environment variables
DATABASE_URL=${DATABASE_URL}
API_KEY=${API_KEY}

# Use Ansible Vault for sensitive data
vault_mysql_password: "encrypted_value"
```

### Input Validation

```python
def process_user_input(user_input: str) -> str:
    """Process user input safely."""
    # Validate input
    if not user_input:
        raise ValueError("Input cannot be empty")

    if len(user_input) > 1000:
        raise ValueError("Input too long")

    # Sanitize
    sanitized = user_input.strip()

    # Escape for SQL/shell if needed
    return sanitized

# Use parameterized queries
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# Avoid shell injection
subprocess.run(["command", arg], check=True)  # Good
subprocess.run(f"command {arg}", shell=True)   # Bad!
```

### File Permissions

```bash
# Secrets: owner read/write only
chmod 600 .secrets/.env
chmod 600 .secrets/.vault_pass
chmod 600 .secrets/ssh/id_rsa

# Scripts: executable by owner
chmod 700 scripts/*.sh

# Public files: readable by all
chmod 644 README.md docs/*.md
```

---

## File Organization

### Root Directory

```
project/
├── .github/              # GitHub configuration
│   ├── workflows/       # CI/CD pipelines
│   ├── agents/          # Copilot agents
│   └── prompts/         # Copilot prompts
├── .secrets/            # Secrets (gitignored)
├── .vscode/             # VS Code settings
├── docs/                # Documentation
├── scripts/             # Automation scripts
├── src/                 # Source code
├── tests/               # Test suite
├── .gitignore
├── .gitleaks.toml
├── .pre-commit-config.yaml
├── Makefile
├── pyproject.toml
├── pytest.ini
└── README.md
```

### Ignored Files

Must be in `.gitignore`:
```gitignore
# Secrets
.secrets/
*.key
*.pem
.env
.vault_pass

# Python
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/*
!.vscode/settings.json
!.vscode/extensions.json

# OS
.DS_Store
Thumbs.db
```

---

## Automation Standards

### Makefile Targets

```makefile
# Self-documenting help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Provide feedback
target: ## Target description
	@echo "🔨 Building..."
	# commands
	@echo "✅ Done"

# Error handling
target-with-check:
	@if [ ! -f required-file ]; then \
		echo "❌ Error: required-file not found"; \
		exit 1; \
	fi
```

### Script Headers

```bash
#!/usr/bin/env bash
#
# Script Name: deploy-service.sh
# Description: Deploy service to production
# Usage: ./deploy-service.sh <service-name> <version>
# Author: Team Name
# Date: 2026-03-20
#

set -euo pipefail  # Strict mode

# Script directory
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Usage message
usage() {
    cat <<EOF
Usage: ${0##*/} <service-name> <version>

Deploy service to production environment.

Arguments:
    service-name    Name of service to deploy
    version        Version tag to deploy

Examples:
    ${0##*/} api v1.2.3
    ${0##*/} frontend v2.0.0
EOF
}
```

---

## Additional Standards

### Performance

- **Avoid premature optimization**: Optimize after profiling
- **Cache expensive operations**: Use `@lru_cache` for pure functions
- **Lazy loading**: Load resources when needed
- **Batch operations**: Process in batches when possible

### Accessibility

- **CLI output**: Use colors judiciously, provide `--no-color` option
- **Error messages**: Clear, actionable, include solution hints
- **Progress indicators**: Show progress for long operations

### Internationalization

- **Strings**: Keep user-facing strings separate from code
- **Dates**: Use ISO 8601 format (YYYY-MM-DD)
- **Times**: Store in UTC, display in local timezone

---

## Enforcement Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Black** | Python formatting | `pyproject.toml` |
| **Ruff** | Python linting | `pyproject.toml` |
| **MyPy** | Type checking | `pyproject.toml` |
| **Bandit** | Security scanning | `pyproject.toml` |
| **pytest** | Testing | `pytest.ini` |
| **pre-commit** | Hook management | `.pre-commit-config.yaml` |
| **Gitleaks** | Secret scanning | `.gitleaks.toml` |
| **shellcheck** | Shell script linting | `.shellcheckrc` |

Run all checks:
```bash
# Local development
make lint
make test
make format

# Pre-commit
pre-commit run --all-files

# CI/CD
# Runs automatically via GitHub Actions
```

---

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)

---

**Last Updated**: 2026-03-20
**Maintainer**: GitHub Copilot + Session Manager Agent
