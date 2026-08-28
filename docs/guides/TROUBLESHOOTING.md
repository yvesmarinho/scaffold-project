# Troubleshooting Guide

**Project Template**: Enterprise Scaffold Project
**Version**: 1.3.0
**Last Updated**: 2026-03-20

---

## 📖 Table of Contents

1. [Setup & Initialization Issues](#setup--initialization-issues)
2. [Git & Version Control](#git--version-control)
3. [Python Environment](#python-environment)
4. [Testing Issues](#testing-issues)
5. [Security & Pre-commit](#security--pre-commit)
6. [Documentation & Links](#documentation--links)
7. [Scripts & Automation](#scripts--automation)
8. [VS Code Integration](#vs-code-integration)

---

## Setup & Initialization Issues

### Problem: scaffold.py fails with "module not found"

**Symptoms**:
```bash
$ python scripts/scaffold.py
ModuleNotFoundError: No module named 'lib'
```

**Solutions**:
1. Ensure you're running from project root:
   ```bash
   cd /path/to/scaffold-project
   python scripts/scaffold.py --help
   ```

2. Or use `uv run` (PEP 723):
   ```bash
   uv run scripts/scaffold.py --help
   ```

3. Verify sys.path includes scripts directory:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
   ```

---

### Problem: Symlinks not working on Windows

**Symptoms**:
- Broken symlinks in `.vscode/`, `config/`
- Files show as missing despite existing

**Solutions**:
1. Enable Developer Mode in Windows 10/11:
   - Settings → Update & Security → For Developers → Developer Mode

2. Run terminal as Administrator

3. Alternative: Copy files instead of symlinks:
   ```bash
   # Modify scripts/lib/links.py
   # Change symlink creation to file copy on Windows
   ```

4. Use WSL2 for development (recommended)

---

### Problem: Project initialization incomplete

**Symptoms**:
- Missing directories or files
- Incomplete structure

**Solutions**:
1. Run initialization again:
   ```bash
   make init
   ```

2. Check for errors in output

3. Manually create missing directories:
   ```bash
   mkdir -p src tests docs scripts .secrets
   ```

4. Verify with:
   ```bash
   make status
   ```

---

## Git & Version Control

### Problem: Pre-commit hooks not running

**Symptoms**:
- Commits succeed without running checks
- No Gitleaks or Black output

**Solutions**:
1. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

2. Verify installation:
   ```bash
   pre-commit run --all-files
   ```

3. Check `.git/hooks/pre-commit` exists

4. Re-install if needed:
   ```bash
   pre-commit uninstall
   pre-commit install
   ```

---

### Problem: Gitleaks reports false positives

**Symptoms**:
```
Warning: secret detected in docs/example.md
```

**Solutions**:
1. Add path to allowlist in `.gitleaks.toml`:
   ```toml
   [allowlist]
   paths = [
       '''docs/examples/''',
       '''tests/fixtures/''',
   ]
   ```

2. Add regex pattern for known false positives:
   ```toml
   [allowlist]
   regexes = [
       '''example_(key|token|password)''',
   ]
   ```

3. Skip commit temporarily (NOT recommended):
   ```bash
   SKIP=gitleaks git commit -m "message"
   ```

---

### Problem: Large files blocked by pre-commit

**Symptoms**:
```
error: File size exceeds 1MB limit
```

**Solutions**:
1. Check file size:
   ```bash
   ls -lh path/to/file
   ```

2. Add to `.gitignore` if not needed:
   ```bash
   echo "large_file.bin" >> .gitignore
   ```

3. Increase limit in `.pre-commit-config.yaml`:
   ```yaml
   - id: check-added-large-files
     args: ['--maxkb=5000']  # Increase to 5MB
   ```

4. Use Git LFS for large binary files:
   ```bash
   git lfs track "*.bin"
   git lfs track "*.zip"
   ```

---

## Python Environment

### Problem: pytest not found

**Symptoms**:
```bash
$ pytest
command not found: pytest
```

**Solutions**:
1. Install dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Or install pytest directly:
   ```bash
   pip install pytest pytest-cov pytest-mock
   ```

3. Verify installation:
   ```bash
   pytest --version
   which pytest
   ```

---

### Problem: Import errors in tests

**Symptoms**:
```python
ModuleNotFoundError: No module named 'src'
```

**Solutions**:
1. Install package in editable mode:
   ```bash
   pip install -e .
   ```

2. Check PYTHONPATH:
   ```bash
   echo $PYTHONPATH
   ```

3. Verify project structure:
   ```bash
   ls -la src/
   ls -la src/__init__.py
   ```

4. Add to pytest.ini if needed:
   ```ini
   [pytest]
   pythonpath = .
   ```

---

### Problem: Black/Ruff formatting conflicts

**Symptoms**:
- Pre-commit fails with formatting issues
- Files change back and forth

**Solutions**:
1. Run Black first:
   ```bash
   black src/ scripts/
   ```

2. Then Ruff:
   ```bash
   ruff check src/ scripts/ --fix
   ```

3. Check line length consistency:
   - Black: 88 (default)
   - Ruff: Should match Black

   ```toml
   # pyproject.toml
   [tool.black]
   line-length = 88

   [tool.ruff]
   line-length = 88
   ```

4. Ignore specific Ruff rules if needed:
   ```toml
   [tool.ruff]
   ignore = ["E501"]  # Line too long
   ```

---

### Problem: MyPy type checking errors

**Symptoms**:
```
error: Function is missing a return type annotation
```

**Solutions**:
1. Add type hints to functions:
   ```python
   def function(param: str) -> int:
       return len(param)
   ```

2. Use `# type: ignore` for specific lines:
   ```python
   result = legacy_function()  # type: ignore
   ```

3. Configure mypy to be less strict:
   ```toml
   [tool.mypy]
   disallow_untyped_defs = false  # Allow some untyped
   ```

4. Install type stubs:
   ```bash
   pip install types-requests types-PyYAML
   ```

---

## Testing Issues

### Problem: Tests fail with "fixture not found"

**Symptoms**:
```
E   fixture 'temp_file' not found
```

**Solutions**:
1. Ensure `conftest.py` exists in tests directory

2. Check fixture is defined:
   ```bash
   grep -n "def temp_file" tests/conftest.py
   ```

3. Verify test discovery:
   ```bash
   pytest --collect-only
   ```

4. Check imports in conftest.py:
   ```python
   import pytest
   from pathlib import Path
   ```

---

### Problem: Coverage too low

**Symptoms**:
```
FAIL Required coverage of 80% not reached. Total coverage: 65%
```

**Solutions**:
1. Identify uncovered code:
   ```bash
   pytest --cov --cov-report=term-missing
   ```

2. View HTML report:
   ```bash
   pytest --cov --cov-report=html
   open htmlcov/index.html
   ```

3. Add tests for uncovered lines

4. Temporarily lower threshold (not recommended):
   ```ini
   [pytest]
   addopts = --cov-fail-under=65
   ```

5. Exclude files from coverage:
   ```ini
   [coverage:run]
   omit =
       */tests/*
       */scripts/tmp/*
   ```

---

### Problem: Slow test execution

**Symptoms**:
- Tests take > 30 seconds
- Feedback loop too long

**Solutions**:
1. Run only fast tests:
   ```bash
   pytest -m "not slow"
   ```

2. Run only unit tests:
   ```bash
   pytest -m unit
   ```

3. Use parallel execution:
   ```bash
   pip install pytest-xdist
   pytest -n auto
   ```

4. Profile slow tests:
   ```bash
   pytest --durations=10
   ```

5. Use test markers effectively:
   ```python
   @pytest.mark.slow
   def test_slow_operation():
       pass
   ```

---

## Security & Pre-commit

### Problem: Secrets accidentally committed

**Symptoms**:
- GitHub security alert
- Gitleaks detects secrets in history

**Solutions**:
1. **Immediate action**: Rotate credentials
   - Change passwords
   - Regenerate API keys
   - Update tokens

2. Remove from Git history:
   ```bash
   # Use git-filter-repo (recommended)
   pip install git-filter-repo
   git filter-repo --path .secrets --invert-paths

   # Or use BFG Repo-Cleaner
   java -jar bfg.jar --delete-files .env .
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```

3. Update remote:
   ```bash
   git push --force --all
   git push --force --tags
   ```

4. Notify team to re-clone repository

---

### Problem: Bandit security warnings

**Symptoms**:
```
[B101:assert_used] Use of assert detected
```

**Solutions**:
1. Review warning and fix if valid

2. Skip specific check:
   ```python
   def test_function():
       assert True  # nosec B101
   ```

3. Configure Bandit in pyproject.toml:
   ```toml
   [tool.bandit]
   skips = ["B101"]  # Allow asserts
   ```

4. Exclude test files:
   ```toml
   [tool.bandit]
   exclude_dirs = ["tests"]
   ```

---

### Problem: Ansible Vault password not found

**Symptoms**:
```
ERROR! Attempting to decrypt but no vault secrets found
```

**Solutions**:
1. Create vault password file:
   ```bash
   mkdir -p .secrets
   echo "your_secure_password" > .secrets/.vault_pass
   chmod 600 .secrets/.vault_pass
   ```

2. Check ansible.cfg:
   ```ini
   [defaults]
   vault_password_file = .secrets/.vault_pass
   ```

3. Verify file permissions:
   ```bash
   ls -la .secrets/.vault_pass
   # Should show: -rw-------
   ```

4. Test vault access:
   ```bash
   ansible-vault view path/to/vault.yml
   ```

---

## Documentation & Links

### Problem: Broken links in markdown

**Symptoms**:
- 404 when clicking documentation links
- References to non-existent files

**Solutions**:
1. Run link validation script:
   ```bash
   bash scripts/validate-docs-links.sh
   ```

2. Find broken links manually:
   ```bash
   find docs/ -name "*.md" -exec grep -H '\[.*\](.*)' {} \;
   ```

3. Fix relative paths:
   ```markdown
   # Wrong
   [link](file.md)

   # Correct
   [link](../path/to/file.md)
   ```

4. Use absolute paths from repo root:
   ```markdown
   [link](/docs/file.md)
   ```

---

### Problem: Markdown not rendering correctly

**Symptoms**:
- Tables broken
- Code blocks not formatted
- Images not showing

**Solutions**:
1. Check table syntax:
   ```markdown
   | Column 1 | Column 2 |
   |----------|----------|
   | Data 1   | Data 2   |
   ```

2. Use fenced code blocks:
   ````markdown
   ```python
   code here
   ```
   ````

3. Verify image paths:
   ```markdown
   ![alt text](./images/screenshot.png)
   ```

4. Test with markdown preview:
   ```bash
   # VS Code: Ctrl+Shift+V (Cmd+Shift+V on Mac)
   ```

---

## Scripts & Automation

### Problem: Makefile commands fail

**Symptoms**:
```bash
$ make test
make: *** No rule to make target 'test'. Stop.
```

**Solutions**:
1. Verify Makefile exists:
   ```bash
   ls -la Makefile
   ```

2. Check available targets:
   ```bash
   make help
   ```

3. Ensure proper indentation (tabs not spaces):
   ```makefile
   test:
   	pytest  # This must be a TAB character
   ```

4. Run with verbose output:
   ```bash
   make -d test
   ```

---

### Problem: Script permission denied

**Symptoms**:
```bash
$ ./scripts/setup.sh
Permission denied
```

**Solutions**:
1. Add execute permission:
   ```bash
   chmod +x scripts/setup.sh
   ```

2. Run with bash explicitly:
   ```bash
   bash scripts/setup.sh
   ```

3. Check file permissions:
   ```bash
   ls -la scripts/setup.sh
   # Should show: -rwxr-xr-x
   ```

---

### Problem: Environment variables not loading

**Symptoms**:
- Scripts can't find configuration
- Connection errors

**Solutions**:
1. Create .env file from template:
   ```bash
   cp .env.example .env
   ```

2. Source .env file:
   ```bash
   source .env
   # Or
   set -a; source .env; set +a
   ```

3. Use direnv (recommended):
   ```bash
   # Install direnv
   brew install direnv  # macOS
   apt install direnv   # Ubuntu

   # Add to shell rc file
   eval "$(direnv hook bash)"

   # Allow directory
   direnv allow .
   ```

4. Check variable is set:
   ```bash
   echo $VAR_NAME
   env | grep VAR
   ```

---

## VS Code Integration

### Problem: VS Code settings not applied

**Symptoms**:
- Formatter not running
- Linter not showing errors

**Solutions**:
1. Reload VS Code window:
   - Cmd+Shift+P / Ctrl+Shift+P
   - "Developer: Reload Window"

2. Check settings.json:
   ```bash
   cat .vscode/settings.json
   ```

3. Verify extensions installed:
   ```bash
   code --list-extensions
   ```

4. Install recommended extensions:
   - Python (ms-python.python)
   - Pylance (ms-python.vscode-pylance)
   - Black Formatter (ms-python.black-formatter)
   - Ruff (charliermarsh.ruff)

---

### Problem: Python interpreter not detected

**Symptoms**:
- Import errors in VS Code
- No auto-completion

**Solutions**:
1. Select Python interpreter:
   - Cmd+Shift+P / Ctrl+Shift+P
   - "Python: Select Interpreter"
   - Choose virtual environment

2. Check Python path:
   ```bash
   which python
   python --version
   ```

3. Recreate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

4. Update settings.json:
   ```json
   {
     "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
   }
   ```

---

## Additional Resources

### Useful Commands

```bash
# Check project status
make status

# Clean all artifacts
make clean

# Reinstall dependencies
pip install -e ".[dev]" --force-reinstall

# Full test suite
pytest -v

# Security scan
pytest -m security
pre-commit run gitleaks --all-files

# Documentation preview
python -m http.server 8000 --directory docs/
```

### Log Locations

- **Test logs**: `pytest.log`
- **Coverage reports**: `htmlcov/index.html`
- **Pre-commit logs**: `.git/hooks/pre-commit.log`

### Getting Help

1. **Check documentation**:
   - [README.md](../README.md)
   - [TESTING_GUIDE.md](TESTING_GUIDE.md)
   - [CONVENTIONS.md](CONVENTIONS.md)

2. **Search issues**: GitHub Issues for common problems

3. **Enable debug mode**:
   ```bash
   export DEBUG=1
   pytest -vv
   ```

---

**Last Updated**: 2026-03-20
**Maintainer**: GitHub Copilot + Session Manager Agent
