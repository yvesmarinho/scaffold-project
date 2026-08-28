# Template Validation Guide

**Version**: 1.0.0
**Implementation**: IMP-65-LITE
**Date**: 2026-04-28

---

## Overview

This guide covers **template validation** and **scaffold logging** for the Enterprise Scaffold Project Template. These tools ensure templates are valid before scaffold and maintain a history of all projects created.

**Components**:
- `scripts/validate-templates.py` — Validate `.specify/templates/`
- `scripts/scaffold_logger.py` — Log scaffold operations
- `scripts/scaffold-query.py` — Query scaffold history
- `logs/scaffolds.yaml` — Scaffold history database

---

## Template Validation

### Purpose

Validate all templates in `.specify/templates/` before scaffold to catch:
- YAML/JSON syntax errors
- Missing required frontmatter fields
- Broken links
- Invalid variable patterns

### Usage

**Basic validation**:
```bash
make validate-templates
# OR
python scripts/validate-templates.py
```

**Validate specific template**:
```bash
python scripts/validate-templates.py --template spec
# Only validates templates matching "spec" (e.g., spec-template.md)
```

**JSON output (for CI/CD)**:
```bash
python scripts/validate-templates.py --json
```

**Strict mode (fail on warnings)**:
```bash
python scripts/validate-templates.py --strict
# Exit code 2 if warnings found
```

### Validation Checks

#### 1. YAML/JSON Syntax

Validates syntax of all `.yaml` and `.json` files:

```yaml
# ✅ Valid YAML
feature:
  id: "001"
  name: "Test"

# ❌ Invalid YAML (indentation error)
feature:
id: "001"  # Bad indentation
  name: "Test"
```

#### 2. Markdown Frontmatter

Checks for required fields in Markdown frontmatter:

```markdown
---
template_version: "2.2.0"    # ✅ Required field present
last_updated: "2026-04-28"
breaking_changes: false
---

# Template Content
```

**Required fields**:
- `template_version` — Semver format (x.y.z)

**Optional but recommended**:
- `last_updated` — ISO date
- `breaking_changes` — Boolean
- `breaking_change_notes` or `breaking_reason` — Required if `breaking_changes: true`

#### 3. Link Validation

Checks Markdown links point to existing files:

```markdown
✅ [Valid link](./objective.yaml)           # File exists
✅ [External link](https://example.com)     # External links OK
❌ [Broken link](./missing.yaml)            # File doesn't exist
```

**Note**: Links in templates may reference files that only exist after scaffold (e.g., `./objetivo.yaml`). These warnings are expected.

#### 4. Variable Validation

Checks variable placeholder format:

```markdown
✅ ${PROJECT_NAME}              # Correct uppercase
✅ $PROJECT_NAME                # Also valid
✅ [PROJECT_NAME]               # Also valid
⚠️  ${project_name}              # Warning: should be uppercase
```

**Convention**: Use `UPPERCASE_SNAKE_CASE` for variables.

### Output

**Console output**:
```
======================================================================
TEMPLATE VALIDATION RESULTS
======================================================================
Files checked: 7

⚠️  WARNINGS (1):
----------------------------------------------------------------------
  .specify/templates/spec-template.md:13
    Broken link: [objetivo.yaml](./objetivo.yaml)
    Details: Target file not found: ...

======================================================================
✅ PASSED (with warnings)
======================================================================
```

**JSON output**:
```json
{
  "success": true,
  "files_checked": 7,
  "errors": [],
  "warnings": [
    {
      "severity": "warning",
      "file": ".specify/templates/spec-template.md",
      "line": 13,
      "message": "Broken link: [objetivo.yaml](./objetivo.yaml)",
      "details": "Target file not found: ..."
    }
  ]
}
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | Validation errors found |
| 2 | Warnings found (only with `--strict`) |

### Integration

**Pre-commit hook** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: local
    hooks:
      - id: validate-templates
        name: Validate .specify/templates/
        entry: python scripts/validate-templates.py
        language: system
        pass_filenames: false
        always_run: true
```

**GitHub Actions** (`.github/workflows/validate-templates.yml`):
```yaml
name: Validate Templates
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pyyaml
      - run: python scripts/validate-templates.py
```

---

## Scaffold Logging

### Purpose

Maintain a historical log of all projects created from this template for:
- Tracking template usage
- Identifying popular profiles
- Auditing project creation
- Analyzing template adoption

### How It Works

**Automatic logging**:
When you create a new project via `scaffold.py`, it automatically logs:
- Project name
- Template version used
- Profile applied
- User who created it
- Path where created
- Timestamp
- Success status

**Log file**: `logs/scaffolds.yaml`

**Example log entry**:
```yaml
scaffolds:
  - id: 1
    timestamp: "2026-04-28T14:30:00Z"
    project_name: "vya-api-users"
    template_version: "2.2.0"
    profile: "python-fastapi"
    created_by: "yves_marinho"
    path: "/home/yves/projects/vya-api-users"
    success: true
    error_message: null
    metadata: {}
```

### Querying Scaffold History

**List recent scaffolds**:
```bash
python scripts/scaffold-query.py --last 30d
python scripts/scaffold-query.py --limit 10
```

**Filter by criteria**:
```bash
# By profile
python scripts/scaffold-query.py --profile python-fastapi

# By user
python scripts/scaffold-query.py --user yves_marinho

# By project name (supports wildcard)
python scripts/scaffold-query.py --project "vya-*"

# Only successful scaffolds
python scripts/scaffold-query.py --success

# Only failed scaffolds
python scripts/scaffold-query.py --failed
```

**Statistics**:
```bash
python scripts/scaffold-query.py --stats
```

Example output:
```
======================================================================
SCAFFOLD STATISTICS
======================================================================
Total scaffolds: 15
Success rate: 93.3%
Recent activity (30 days): 5

By Profile:
  python-fastapi                          8
  typescript-next                         4
  terraform-aws                           3

By User:
  yves_marinho                           12
  other_user                              3
======================================================================
```

**Export to CSV**:
```bash
python scripts/scaffold-query.py --export scaffolds.csv
```

**JSON output**:
```bash
python scripts/scaffold-query.py --json --limit 5
```

### Query Options

| Option | Description | Example |
|--------|-------------|---------|
| `--project NAME` | Filter by project name (wildcard `*` supported) | `--project "vya-*"` |
| `--profile PROFILE` | Filter by profile | `--profile python-fastapi` |
| `--user USER` | Filter by user | `--user yves_marinho` |
| `--success` | Show only successful scaffolds | `--success` |
| `--failed` | Show only failed scaffolds | `--failed` |
| `--last PERIOD` | Last N days/weeks/months | `--last 30d`, `--last 2w` |
| `--limit N` | Limit results | `--limit 10` |
| `--stats` | Show statistics | `--stats` |
| `--export FILE` | Export to CSV | `--export scaffolds.csv` |
| `--json` | Output as JSON | `--json` |

---

## Common Workflows

### Before Creating New Project

**Validate templates**:
```bash
make validate-templates
# OR
python scripts/validate-templates.py
```

If validation fails, fix errors before scaffold.

### After Improving Templates

**Re-validate**:
```bash
python scripts/validate-templates.py
```

**Commit with validation**:
```bash
make validate-templates && git add .specify/templates/ && git commit -m "feat(templates): improve spec template"
```

### Analyzing Template Usage

**Which profiles are most popular?**
```bash
python scripts/scaffold-query.py --stats
```

**How many projects created this month?**
```bash
python scripts/scaffold-query.py --last 30d
```

**Find all Python FastAPI projects**:
```bash
python scripts/scaffold-query.py --profile python-fastapi
```

**Export for analysis**:
```bash
python scripts/scaffold-query.py --export /tmp/scaffolds.csv
# Open in Excel/Google Sheets for analysis
```

---

## Troubleshooting

### Validation Fails with "YAML syntax error"

**Problem**: Template has invalid YAML.

**Solution**: Check indentation and quotes:
```yaml
# ❌ Bad
feature:
id: "001"  # Wrong indentation

# ✅ Good
feature:
  id: "001"
```

### Validation Warns "Broken link"

**Problem**: Link points to non-existent file.

**Solution**:
- If link is correct but file created during scaffold, ignore warning
- If link is broken, fix it

### Scaffold Logger Not Working

**Problem**: `logs/scaffolds.yaml` not updated after scaffold.

**Solution**:
1. Check file permissions: `ls -la logs/scaffolds.yaml`
2. Verify integration: `grep scaffold_logger scripts/lib/flows/new_project.py`
3. Check for errors in scaffold output

### Query Returns No Results

**Problem**: No scaffolds match filter criteria.

**Solution**:
1. List all scaffolds: `python scripts/scaffold-query.py --limit 100`
2. Check filter syntax: `--project "vya-*"` (with quotes)
3. Verify log file exists: `cat logs/scaffolds.yaml`

---

## Best Practices

### Template Validation

✅ **DO**:
- Run `make validate-templates` before committing template changes
- Add pre-commit hook for automatic validation
- Use `--strict` mode in CI/CD
- Fix errors immediately (don't ignore)

❌ **DON'T**:
- Commit templates without validation
- Ignore validation warnings
- Disable validation checks

### Scaffold Logging

✅ **DO**:
- Keep `logs/scaffolds.yaml` in version control
- Export to CSV periodically for backup
- Review statistics monthly

❌ **DON'T**:
- Delete `logs/scaffolds.yaml` (historical data)
- Manually edit log file (corruption risk)
- Store sensitive data in log (e.g., credentials)

---

## Performance

### Validation

- **7 templates**: ~0.1s
- **50 templates**: ~1s
- **Bottleneck**: Link validation (file I/O)

### Logging

- **Write**: ~1ms per scaffold
- **Query**: <1ms (100 entries), ~10ms (1000 entries)
- **Bottleneck**: YAML serialization (for 1000+ entries, consider JSON)

---

## Intelligent File Merge System

**Version**: 2.0.0 (Bug fix: BUG-#1.1)
**Implementation**: Sprint 1 — Security Critical
**Date**: 2026-04-28

### Overview

The **Intelligent File Merge System** solves a critical bug where pre-existing files were unconditionally skipped during scaffold, causing:
- 🔴 **Security vulnerability**: `.gitignore` missing `.secrets/` → credential leakage risk
- 🟡 **Lost features**: Essential Makefile targets, README sections not applied
- 🟡 **Incomplete projects**: Template protections/workflows missing

**Solution**: Smart merge for critical files when scaffold runs on pre-existing repositories (e.g., GitHub repos).

### How It Works

#### Before (Problematic)

```python
# OLD: Unconditional skip (lines 1583-1588 in project.py)
if file_path.exists():
    results.append(CreatedItem(
        path=file_path, kind="file", status="skipped"
    ))
    continue  # ❌ Lost .secrets/, Makefile targets, README sections
```

**Result**: GitHub repos scaffolded without security protections.

#### After (Intelligent Merge)

```python
# NEW: Try merge first, fallback to skip (project.py + file_merge.py)
if file_path.exists():
    merge_result = file_merge.merge_or_skip(
        file_path=file_path,
        template_content=content,
        interactive=False
    )
    results.append(merge_result)
    continue  # ✅ Merges .gitignore, Makefile, README
```

**Result**: Security patterns added, features preserved, customizations maintained.

### Supported Mergers

#### 1. GitignoreMerger (P0 — Security Critical)

**Purpose**: Add security patterns to existing `.gitignore`.

**Strategy**:
1. Detect critical patterns missing (`.secrets/`, `*.key`, `*.pem`, etc.)
2. Add security header + missing patterns at top
3. Preserve original content below

**Example**:

```bash
# Before (GitHub default)
__pycache__/
*.pyc

# After scaffold
# === Enterprise Template Security (Auto-Added) ===
# CRITICAL: Never commit credentials, tokens, or keys
.secrets/
*.key
*.pem
.env

# === Original Content Below ===
__pycache__/
*.pyc
```

**Test**:
```bash
cd tests/
python -m pytest test_file_merge.py::test_gitignore_merge_adds_security_patterns -v
```

#### 2. MakefileMerger (P1 — Workflow Important)

**Purpose**: Add essential targets while preserving custom ones.

**Strategy**:
1. Extract targets from template (`help`, `test`, `lint`, etc.)
2. Extract targets from existing Makefile
3. Add only missing essential targets
4. Preserve all custom targets

**Example**:

```bash
# Before (user's Makefile)
deploy:
\t./scripts/deploy.sh

# After scaffold
# === Enterprise Template Targets (Auto-Added) ===
help:
\t@echo "Available targets:"

test:
\tpytest tests/

# === Original Targets Below ===
deploy:
\t./scripts/deploy.sh
```

**Test**:
```bash
python -m pytest test_file_merge.py::test_makefile_merge_adds_essential_targets -v
```

#### 3. ReadmeMerger (P1 — Documentation Important)

**Purpose**: Add template sections while preserving user intro.

**Strategy**:
1. Extract introduction (before first `##`) from existing README
2. Detect template sections missing (`## Project Status`, `## Stack`, etc.)
3. Merge: intro + missing sections + original sections

**Example**:

```markdown
<!-- Before (GitHub README) -->
# My Custom Project

This is my awesome project that does amazing things.

<!-- After scaffold -->
# My Custom Project

This is my awesome project that does amazing things.

---

<!-- Enterprise Template Sections (Auto-Added) -->

## Project Status

🟢 Active development

## Stack

- Python 3.12+
- pytest

---

<!-- Original Sections Below -->
```

**Test**:
```bash
python -m pytest test_file_merge.py::test_readme_merge_adds_template_sections -v
```

### Common Workflows

#### Workflow 1: GitHub-First (Most Common)

**Scenario**: Create repo on GitHub UI, clone, then scaffold.

```bash
# 1. Create repo on GitHub (with .gitignore, README)
# 2. Clone locally
git clone git@github.com:user/new-project.git
cd new-project

# 3. Scaffold
uv run ../scaffold-project/scripts/scaffold.py new \
  --name=new-project \
  --domain=programming \
  --language=python

# ✅ RESULT:
# - .gitignore: .secrets/ ADDED (security)
# - README.md: Template sections ADDED (intro preserved)
# - Makefile: Targets ADDED (if created later)
```

**Validation**:
```bash
grep ".secrets/" .gitignore  # ✅ Should be present
grep "## Project Status" README.md  # ✅ Should be present
make help  # ✅ Should work
```

#### Workflow 2: Template-First (Also Works)

**Scenario**: Empty directory, scaffold first, GitHub later.

```bash
# 1. Empty directory
mkdir new-project && cd new-project

# 2. Scaffold
uv run ../scaffold-project/scripts/scaffold.py new

# 3. Push to GitHub
git remote add origin git@github.com:user/new-project.git
git push -u origin main

# ✅ RESULT:
# - All files created normally (no merge needed)
# - 100% template applied
```

#### Workflow 3: Fork/Clone Another Template

**Scenario**: Fork another company template, scaffold to migrate.

```bash
# 1. Clone/fork other template
git clone git@github.com:company/another-template.git my-project
cd my-project

# 2. Scaffold our template
uv run ../scaffold-project/scripts/scaffold.py new

# ✅ RESULT:
# - Essential patterns MERGED (security)
# - Essential targets MERGED (workflow)
# - Essential sections MERGED (docs)
# - Custom content PRESERVED
```

### Extensibility

#### Adding Custom Mergers

Create a new merger for specific file types:

```python
# Example: docker-compose.yml merger
from pathlib import Path
from scripts.lib.file_merge import register_merger, FileMerger
from scripts.lib.config import CreatedItem

class DockerComposeMerger:
    """Merge docker-compose services."""

    def can_merge(self, file_path: Path) -> bool:
        return file_path.name == "docker-compose.yml"

    def merge(
        self,
        existing_path: Path,
        template_content: str,
        interactive: bool = True
    ) -> CreatedItem:
        # ... YAML merge logic ...
        return CreatedItem(
            path=existing_path,
            kind="file",
            status="created",
            message="Merged services"
        )

# Register
register_merger(DockerComposeMerger())
```

**Use case**: Projects with custom Docker services need template services added.

#### Registry

```python
from scripts.lib.file_merge import get_registered_mergers

# List all mergers
print(get_registered_mergers())
# ['GitignoreMerger', 'MakefileMerger', 'ReadmeMerger']
```

### Testing

**Run all merge tests**:
```bash
python -m pytest tests/test_file_merge.py -v
```

**Test coverage**:
- 15 tests total
- 100% coverage of merge logic
- Integration test simulating full GitHub scenario

**Key tests**:
1. `test_gitignore_merge_adds_security_patterns` — Security (P0)
2. `test_makefile_merge_adds_essential_targets` — Workflow (P1)
3. `test_readme_merge_adds_template_sections` — Docs (P1)
4. `test_merge_or_skip_skips_unsupported_files` — Fallback safety
5. `test_full_github_repo_scaffold_scenario` — End-to-end

### Troubleshooting

#### Merge Not Applied

**Problem**: `.gitignore` still missing `.secrets/` after scaffold.

**Solution**:
1. Check file exists: `ls -la .gitignore`
2. Check merge logs: `grep "🔒" <scaffold_output>`
3. Verify patterns: `grep ".secrets/" .gitignore`
4. Manual fix if needed: `echo ".secrets/" >> .gitignore`

#### Custom Content Lost

**Problem**: User's custom Makefile target removed.

**Solution**:
- This **should not happen** (merge preserves custom content)
- Check git diff: `git diff Makefile`
- Report bug with details

#### Merger Not Triggered

**Problem**: Expected merge didn't happen (file skipped).

**Solution**:
1. Verify file name matches: `.gitignore` (exact match)
2. Check registered mergers: `python -c "from scripts.lib.file_merge import get_registered_mergers; print(get_registered_mergers())"`
3. Review logs for "Skip" message

### Performance

- **Merge operation**: ~1-5ms per file
- **No merge (skip)**: <1ms per file
- **Bottleneck**: Regex parsing for Makefile/README

**Scalability**:
- Tested with 100+ file scaffolds: negligible overhead
- Merge only happens for ~3 files (.gitignore, Makefile, README)

### Security Considerations

**GitignoreMerger is critical**:
- Prevents credential leakage
- Auto-adds `.secrets/`, `*.key`, `*.pem`, `.env`
- **No user confirmation required** (security override)

**Other mergers are helpful**:
- MakefileMerger: workflow convenience
- ReadmeMerger: documentation completeness
- **Non-critical** (can be skipped if problematic)

### Best Practices

✅ **DO**:
- Run scaffold on pre-existing repos (GitHub, GitLab, etc.)
- Trust the merge system for `.gitignore` (security)
- Review merge results: `git diff`
- Report bugs if custom content lost

❌ **DON'T**:
- Manually edit `.gitignore` after scaffold (merge may re-add)
- Disable GitignoreMerger (security risk)
- Skip validation after merge: `git diff .gitignore`

---

## Secrets Protection and Pre-Commit Hook

**Version**: 1.0.0 (Bug fix: BUG-#4)
**Implementation**: Sprint 3 — Security Enhancement
**Date**: 2026-04-28

### Overview

The template includes an **automatic pre-commit hook** that prevents accidental commits of sensitive files to version control.

**Key Features**:
- 🔒 **Auto-activated**: Hook installed automatically during scaffold (no manual setup)
- 🛡️ **Blocks secrets**: Prevents commits of `.secrets/`, `*.key`, `.env`, etc.
- ⚙️ **Customizable**: Edit `.git-hooks/pre-commit.secrets` for project-specific patterns
- 🚫 **Git-aware**: Only activated if `.git/hooks/` directory exists

### How It Works

#### Activation (Automatic)

The hook is activated during scaffold execution:

```bash
# During scaffold (step 8b):
📁 Criando estrutura...
🗃️  Inicializando repositório Git...
🔒 Configurando segurança de .secrets/...
INFO ✅ Pre-commit hook ativado automaticamente  # ← BUG-#4 fix
```

**Before BUG-#4 fix**: Hook created but never activated (required manual `cp` command).
**After BUG-#4 fix**: Hook automatically copied to `.git/hooks/pre-commit` with `chmod 755`.

#### Hook Template Location

- **Source**: `.git-hooks/pre-commit.secrets` (versioned template)
- **Destination**: `.git/hooks/pre-commit` (active hook, not versioned)

**Why separate?**
- `.git-hooks/` → versioned, can be updated via `git pull`
- `.git/hooks/` → local only (`.git/` in `.gitignore`)

#### Protected Patterns (Default)

The hook blocks commits of files matching:

```bash
# Critical patterns (from _PRE_COMMIT_SECRETS_HOOK constant)
.secrets/          # All files in secrets directory
*.key              # Private keys
*.pem              # Certificates
.env               # Environment variables
*secret*           # Files with "secret" in name
*password*         # Files with "password" in name
*token*            # Files with "token" in name
```

### Usage Examples

#### Normal Workflow (No Secrets)

```bash
# Create and commit normal files
echo "# My API" > README.md
git add README.md
git commit -m "docs: add README"  # ✅ Allowed
```

#### Blocked Commit (Secrets Detected)

```bash
# Accidentally try to commit secret
echo "API_KEY=secret123" > .secrets/config.env
git add .secrets/config.env
git commit -m "chore: add config"

# Output:
# ❌ BLOQUEADO: Arquivos sensíveis detectados
# Arquivos bloqueados:
#   .secrets/config.env
#
# Para ignorar este aviso (não recomendado):
#   git commit --no-verify -m "..."
```

#### Customizing Patterns

Edit `.git-hooks/pre-commit.secrets` to add project-specific patterns:

```bash
# Add custom pattern
echo '*.credentials' >> .git-hooks/pre-commit.secrets

# Re-activate hook (if needed)
cp .git-hooks/pre-commit.secrets .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Troubleshooting

#### Hook Not Working

**Symptom**: Secrets committed without blocking.

**Diagnosis**:
```bash
# Check hook exists and is executable
ls -la .git/hooks/pre-commit
# Expected: -rwxr-xr-x ... .git/hooks/pre-commit

# Test hook manually
.git/hooks/pre-commit
```

**Solution**:
```bash
# Re-activate hook
cp .git-hooks/pre-commit.secrets .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

#### Hook Too Strict (False Positives)

**Symptom**: Legitimate files blocked (e.g., `test_password_validation.py`).

**Solution**: Edit `.git-hooks/pre-commit.secrets` to exclude specific patterns:

```bash
# Before (blocks all *password*)
git commit test_password_validation.py  # ❌ Blocked

# After (exclude tests/)
# Edit .git-hooks/pre-commit.secrets:
#   if [[ "$file" != tests/* ]]; then
#       # check password pattern
#   fi

git commit test_password_validation.py  # ✅ Allowed
```

#### Bypass Hook (Emergency)

**⚠️ USE WITH CAUTION** — Only for emergencies:

```bash
# Skip hook for single commit
git commit --no-verify -m "emergency fix"

# Disable hook permanently (NOT RECOMMENDED)
rm .git/hooks/pre-commit
```

**Better approach**: Fix the issue properly and re-commit normally.

### Technical Details

#### Implementation

**File**: `scripts/lib/project.py`
**Function**: `setup_secrets_security()` (lines 1987-2102)

```python
# 4. Ativar pre-commit hook automaticamente (BUG-#4 fix)
hook_template = base / ".git-hooks" / "pre-commit.secrets"
hook_target = base / ".git" / "hooks" / "pre-commit"

if hook_template.exists():
    try:
        hooks_dir = base / ".git" / "hooks"
        if hooks_dir.exists():
            shutil.copy2(hook_template, hook_target)
            hook_target.chmod(0o755)  # rwxr-xr-x
            log.info("✅ Pre-commit hook ativado automaticamente")
        else:
            log.warning("⚠️  .git/hooks/ não existe — pulando ativação de hook")
    except Exception as e:
        log.warning("⚠️  Falha ao ativar pre-commit hook: %s", e)
```

**Execution Order** (critical for BUG-#4 fix):

1. **Step 1**: `create_structure()` → creates `.git-hooks/pre-commit.secrets`
2. **Step 8**: `git.init_repository()` → creates `.git/hooks/` directory
3. **Step 8b**: `setup_secrets_security()` → **activates hook** ✅

**Before BUG-#4 fix**: `setup_secrets_security()` called before `git.init_repository()` → `.git/hooks/` didn't exist → hook not activated.

#### Tests

**Test Suite**: `tests/test_sprint3_precommit.py`

```bash
# Run tests
pytest tests/test_sprint3_precommit.py -v

# Expected output:
# ✅ test_pre_commit_hook_content_in_constant PASSED
# ✅ test_setup_secrets_security_activates_hook PASSED
# ✅ test_hook_activation_without_git_hooks_dir PASSED
# ✅ test_hook_activation_handles_copy_error PASSED
```

**Coverage**:
- Hook template content validation
- Automatic activation on scaffold
- Graceful degradation (no .git/hooks/)
- Error handling (permission denied)

### Best Practices

✅ **DO**:
- Keep `.git-hooks/pre-commit.secrets` versioned
- Review patterns regularly (add project-specific secrets)
- Test hook with `git commit` (should block secrets)
- Document custom patterns in `.git-hooks/README.md`

❌ **DON'T**:
- Delete `.git/hooks/pre-commit` (defeats purpose)
- Use `--no-verify` habitually (security risk)
- Store real secrets in tests (use fake values)
- Commit `.git/hooks/` directory (local only)

### Related Bugs

- **BUG-#1**: `.gitignore` missing `.secrets/` → fixed by GitignoreMerger (Sprint 1)
- **BUG-#4**: Pre-commit hook not activated → **fixed in Sprint 3** ✅

---

## Next Steps

- **P2 Enhancement**: Add email notifications for failed scaffolds
- **P2 Enhancement**: Dashboard for scaffold analytics
- **P2 Enhancement**: Integration with project tracking system

---

## References

- **IMP-65-LITE Spec**: [specs/065-template-validation-lite/spec.md](../../specs/065-template-validation-lite/spec.md)
- **POC Learnings**: [docs/reference/POC-LEARNINGS.md](../reference/POC-LEARNINGS.md) (when CI/CD makes sense)
- **POC-1 to POC-4**: [poc/imp65-p1-validation/](../../poc/imp65-p1-validation/) (reference implementation)
