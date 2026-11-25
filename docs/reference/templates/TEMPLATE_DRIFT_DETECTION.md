# Template Versioning and Drift Detection Guide

## Overview

**IMP-65 Fase 1** introduced a template versioning system to prevent projects from missing upstream improvements to SpecKit workflow templates. This guide explains how to detect and understand template drift.

## The Problem

When you create a project with `scaffold.py new`, templates from `.specify/templates/` are copied to your project. However:

- **One-time copy**: Templates are copied only once during project creation
- **No automatic updates**: Future improvements to upstream templates don't reach existing projects
- **Risk of staleness**: Projects can drift from best practices over time

## The Solution: Template Versioning

Each SpecKit template now includes version metadata in YAML frontmatter:

```yaml
---
template_version: "1.0.0"
last_updated: "2026-04-14"
breaking_changes: false
---
```

This allows detection of outdated templates through the `check-templates` command.

---

## Command: `scaffold.py check-templates`

Scans your project's `.specify/templates/` directory and compares versions with the upstream scaffold-project templates.

### Basic Usage

```bash
# Check templates in current directory
cd /path/to/your/project
python /path/to/scaffold-project/scripts/scaffold.py check-templates

# Check templates in specific directory
python scripts/scaffold.py check-templates --target-dir /path/to/project
```

### Output Formats

#### Text Output (Default)

```
Template Drift Detection
  Upstream: /home/user/scaffold-project/.specify/templates
  Local:    /home/user/my-project/.specify/templates
  Templates scanned: 6 upstream, 6 local

✅ All templates are up-to-date!
```

When drift is detected:

```
⚠️  Template Drift Detected: 2 template(s) need attention

📊 Outdated templates (1):
  • spec-template: 1.0.0 → 1.5.0

❌ Missing templates (1):
  • new-template: v1.0.0 (not found in project)

Run 'scaffold.py diff-template <name>' to see changes (Phase 2)
```

#### JSON Output

```bash
python scripts/scaffold.py check-templates --json
```

Output:

```json
{
  "drift_detected": true,
  "total_drifts": 2,
  "outdated_count": 1,
  "missing_count": 1,
  "breaking_changes": false,
  "templates": [
    {
      "name": "spec-template.md",
      "local_version": "1.0.0",
      "upstream_version": "1.5.0",
      "is_outdated": true,
      "is_missing": false,
      "breaking_changes": false
    },
    {
      "name": "new-template.md",
      "local_version": null,
      "upstream_version": "1.0.0",
      "is_outdated": false,
      "is_missing": true,
      "breaking_changes": false
    }
  ]
}
```

### Exit Codes

- **0**: All templates are up-to-date
- **1**: Drift detected (outdated or missing templates)
- **2**: Error during execution

Use in scripts:

```bash
if python scripts/scaffold.py check-templates; then
    echo "Templates are current"
else
    echo "Templates need attention"
fi
```

---

## Understanding Drift Types

### Outdated Templates

Template exists locally but is older than upstream version.

**Example:**
- Local: `spec-template.md` v1.0.0
- Upstream: `spec-template.md` v1.5.0

**Action**: Review changes and consider updating (Phase 3 will provide merge tools).

### Missing Templates

Template exists upstream but not in local project.

**Example:**
- Local: no `checklist-template.md`
- Upstream: `checklist-template.md` v1.0.0

**Action**: New workflow capability available — consider adding to project.

### Breaking Changes

Template update includes breaking changes that require manual intervention.

**Example:**
- Local: `plan-template.md` v1.5.0
- Upstream: `plan-template.md` v2.0.0 (breaking_changes: true)

**Action**: Carefully review changelog before updating.

---

## Version Tracking in `.scaffold-state.yaml`

When you create or update a project, template versions are tracked in `.scaffold-state.yaml`:

```yaml
scaffold_version: "1.0.0"
created_at: "2026-04-14T10:00:00Z"
updated_at: "2026-04-14T14:30:00Z"
project:
  name: my-api
  ...
template_versions:
  spec-template.md: "1.0.0"
  plan-template.md: "1.2.0"
  tasks-template.md: "1.0.0"
  agent-file-template.md: "1.0.0"
  checklist-template.md: "1.0.0"
  constitution-template.md: "1.0.0"
```

This enables:
- **Historical tracking**: Know what versions you started with
- **Audit trail**: Understand when templates were applied
- **Safe updates**: Check if custom modifications exist before applying upstream changes

---

## Automation and CI/CD

### Pre-commit Hook

Check for template drift before committing:

```bash
# .git/hooks/pre-commit
#!/bin/bash
if ! python scripts/scaffold.py check-templates; then
    echo "⚠️  Template drift detected. Run 'scaffold.py check-templates' for details."
    exit 1
fi
```

### GitHub Actions Workflow

```yaml
name: Check Template Drift
on: [push, pull_request]
jobs:
  check-templates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Checkout scaffold-project
        uses: actions/checkout@v3
        with:
          repository: your-org/scaffold-project
          path: upstream-template
      - name: Check drift
        run: |
          cd upstream-template
          python scripts/scaffold.py check-templates --target-dir ../. --json > drift.json
          cat drift.json
      - name: Fail on drift
        run: |
          if jq -e '.drift_detected == true' drift.json; then
            echo "::error::Template drift detected"
            exit 1
          fi
```

---

## Command: `scaffold.py diff-template`

**IMP-65 Fase 2** — Shows detailed differences between local and upstream template versions.

### Basic Usage

```bash
# Show colored diff in terminal
python scripts/scaffold.py diff-template spec-template

# Export diff to markdown file
python scripts/scaffold.py diff-template spec-template --format markdown --output drift-report.md

# Generate HTML side-by-side diff
python scripts/scaffold.py diff-template spec-template --format html --output diff.html

# Check template in specific project directory
python scripts/scaffold.py diff-template plan-template --target-dir /path/to/project
```

### Output Formats

#### 1. Colored Terminal (Default)

```bash
python scripts/scaffold.py diff-template spec-template
```

Output:

```
Parsing template versions...
Generating diff for spec-template.md...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Template Diff: spec-template.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Metadata
  Local version:    1.0.0
  Upstream version: 1.5.0
  Outdated:         TRUE

📊 Statistics
  + 12 lines added
  - 2 lines removed
  ~ 5 lines modified
  ━━━━━━━━━━━━━━━━━
  Total: 19 changes

⚠️ Customizations Detected
  Your template has local modifications
  Review diff carefully before updating

🔍 Unified Diff
───────────────────────────────────────────────────
--- local/spec-template.md (1.0.0)
+++ upstream/spec-template.md (1.5.0)
@@ -15,6 +15,18 @@
 ## Overview
 Brief description of the feature.

+## Performance Criteria
+Define performance requirements:
+- Response time
+- Throughput
+- Resource usage
+
+## Security Considerations
+- Authentication requirements
+- Authorization model
+- Data encryption
+- Audit logging
+
 ## Technical Approach
 How will it be built?
───────────────────────────────────────────────────

💡 Impact Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Template:  spec-template.md
Versions:  1.0.0 → 1.5.0
Changes:   19 total (12 added, 2 removed, 5 modified)

⚠️ Customizations Detected
  Local template has custom modifications
  Manual review required before updating

Recommendations:
  1. Review diff above to understand upstream changes
  2. Identify which customizations to preserve
  3. Use Phase 3 merge command (when available) to combine changes
  4. Test thoroughly after applying updates
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 2. Markdown Export

Perfect for documentation, PR reviews, and archival:

```bash
python scripts/scaffold.py diff-template spec-template --format markdown --output drift-analysis.md
```

Generates structured markdown:

```markdown
# Template Diff: spec-template.md

## Metadata
- **Template**: spec-template.md
- **Local Version**: 1.0.0
- **Upstream Version**: 1.5.0
- **Outdated**: TRUE
- **Customizations Detected**: TRUE

## Statistics
- Lines added: 12
- Lines removed: 2
- Lines modified: 5
- Total changes: 19

## Diff
\```diff
--- local/spec-template.md (1.0.0)
+++ upstream/spec-template.md (1.5.0)
@@ -15,6 +15,18 @@
 ## Overview
 Brief description of the feature.

+## Performance Criteria
+Define performance requirements:
+- Response time
+- Throughput
...
\```

## Impact Report
[Full impact analysis with recommendations]
```

#### 3. HTML Side-by-Side

Best for visual review:

```bash
python scripts/scaffold.py diff-template spec-template --format html --output review.html
```

Opens in browser showing color-coded side-by-side comparison.

### Use Cases

#### 1. Before Updating Template

```bash
# Check what changed in upstream
python scripts/scaffold.py diff-template spec-template

# If changes look good:
# (Phase 3 — coming soon)
# python scripts/scaffold.py merge-template spec-template
```

#### 2. Code Review Documentation

```bash
# Generate diff report for PR
python scripts/scaffold.py diff-template plan-template \
  --format markdown \
  --output docs/SESSIONS/2026-04-14/template-drift-review.md

# Commit to repository
git add docs/SESSIONS/2026-04-14/template-drift-review.md
git commit -m "docs: template drift analysis for plan-template"
```

#### 3. CI/CD Validation

```bash
# In CI pipeline
python scripts/scaffold.py diff-template spec-template --format markdown > drift.md

# Parse statistics from markdown
if grep -q "Total changes: 0" drift.md; then
  echo "✅ Template up-to-date"
else
  echo "⚠️ Template drift detected"
  cat drift.md >> $GITHUB_STEP_SUMMARY
fi
```

#### 4. Batch Analysis

```bash
# Check all templates
for template in spec-template plan-template tasks-template; do
  echo "Analyzing $template..."
  python scripts/scaffold.py diff-template $template \
    --format markdown \
    --output "drift-reports/${template}-diff.md"
done
```

### Customization Detection

The diff command uses heuristics to distinguish between:

1. **Upstream improvements**: New sections, updated guidance
2. **Your customizations**: Project-specific content you added

**Phase 2 Heuristic**: Compares local-only vs upstream-only content
**Phase 3**: Three-way merge with base template tracking (see merge-template below)

### Integration with check-templates

Workflow pattern:

```bash
# 1. Detect drift
python scripts/scaffold.py check-templates

# Output:
# ⚠️ Template Drift Detected: 2 template(s) need attention
# 📊 Outdated templates (1):
#   • spec-template: 1.0.0 → 1.5.0

# 2. Analyze specific template
python scripts/scaffold.py diff-template spec-template

# 3. Export for review
python scripts/scaffold.py diff-template spec-template \
  --format markdown \
  --output docs/template-review.md

# 4. Merge changes (Phase 3)
python scripts/scaffold.py merge-template spec-template --auto
```

---

## Command: `scaffold.py merge-template`

**IMP-65 Fase 3** — Automatic three-way merge of upstream improvements while preserving local customizations.

### How It Works

The merge uses **git merge-file** to perform intelligent three-way merges:

1. **Base**: Original template content at project creation (stored in `.scaffold-state.yaml`)
2. **Local**: Current template with your customizations
3. **Upstream**: Latest template from scaffold-project

This enables automatic merging of independent changes and intelligent conflict detection.

### Basic Usage

```bash
# Dry-run: preview merge without applying
python scripts/scaffold.py merge-template spec-template --dry-run

# Auto-apply if no conflicts
python scripts/scaffold.py merge-template spec-template --auto

# Force apply even with conflicts (manual resolution required)
python scripts/scaffold.py merge-template spec-template --force

# Interactive conflict resolution (IMP-65 Phase 3.1)
python scripts/scaffold.py merge-template spec-template --interactive
python scripts/scaffold.py merge-template spec-template --interactive
```

### Merge Scenarios

#### 1. Clean Merge (No Conflicts)

When local and upstream modified different sections:

```bash
$ python scripts/scaffold.py merge-template spec-template --auto

Merging template: spec-template.md...
Parsing template versions...
  Local version:    1.0.0
  Upstream version: 1.5.0
  Base version:     1.0.0

Performing three-way merge...
✅ Merge completed cleanly (no conflicts)

✅ Merge applied successfully
  Backup: .specify/templates/spec-template.backup-20260414-183000.md
  Updated: .specify/templates/spec-template.md
  Version: 1.0.0 → 1.5.0
```

#### 2. Merge with Conflicts

When local and upstream modified the same sections:

```bash
$ python scripts/scaffold.py merge-template spec-template

Merging template: spec-template.md...
...
⚠️  1 conflict(s) detected

Conflict #1 (lines 23-31):
  Type: both_modified
  Suggestion: Both local and upstream modified this section.
              Review carefully and choose the best combination.

To resolve conflicts:
  1. Open the merged file in your editor
  2. Search for conflict markers (<<<<<<, =======, >>>>>>>)
  3. Choose or combine the best content
  4. Remove all conflict markers
  5. Save the file

💡 Resolution options:
  --force        Apply merge with conflict markers (manual resolution)
  --interactive  Interactive conflict resolution
  --dry-run      Preview merge without applying
```

#### 3. Force Apply with Conflicts

```bash
$ python scripts/scaffold.py merge-template spec-template --force

⚠️  Force-applying merge with conflicts...
✅ Merge applied (with conflicts)
  Backup: .specify/templates/spec-template.backup-20260414-183500.md
  Open .specify/templates/spec-template.md to resolve conflicts
```

The file will contain conflict markers:

```markdown
## Overview

<<<<<<< LOCAL
Brief description with custom security notes.
||||||| BASE
Brief description of the feature.
=======
Brief description including business value and success metrics.
>>>>>>> UPSTREAM

## Technical Approach
```

Resolve by choosing the best content and removing markers:

```markdown
## Overview

Brief description including business value, success metrics, and custom security notes.

## Technical Approach
```

#### 4. Interactive Conflict Resolution (Phase 3.1)

**IMP-65 Phase 3.1** — Step-by-step guided conflict resolution with side-by-side diff visualization.

```bash
$ python scripts/scaffold.py merge-template spec-template --interactive

Merging template: spec-template.md...
⚠️  1 conflict(s) detected

Start interactive resolution? [Y/n]: y

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conflict 1/1
Lines 23-31 • Type: both_modified

LOCAL (your changes)                    UPSTREAM (template updates)
────────────────────────────────────────────────────────────────────
Brief description with custom          Brief description including
security notes.                         business value and success
                                        metrics.

┌──────────────────────────────────────────────────────────────────┐
│ 💡 Both versions modified this section.                          │
│ Review carefully and choose the best content or combine both.    │
└──────────────────────────────────────────────────────────────────┘

Resolution options:
  l  Keep LOCAL (your changes)
  u  Accept UPSTREAM (template updates)
  b  Keep BOTH (local first, then upstream)
  e  Edit manually (open editor)
  s  Skip (leave conflict marker for later)
  ?  Show diff again

Choose resolution [u]: b

✅ Resolved as: BOTH

Resolution Summary:
  ✅ Resolved: 1/1

🎉 All conflicts resolved!

✅ Merge applied successfully
  Backup: .specify/templates/spec-template.backup-20260414-200000.md
  Updated: .specify/templates/spec-template.md
  Version: 1.0.0 → 1.5.0
```

**Interactive Mode Features:**

1. **Side-by-side diff visualization**: See local and upstream changes clearly
2. **Conflict analysis**: Automatic suggestions based on conflict type
3. **Multiple resolution options**:
   - **Keep LOCAL** (`l`): Preserve your customization
   - **Accept UPSTREAM** (`u`): Get new template features
   - **Keep BOTH** (`b`): Combine both changes (local first)
   - **Edit manually** (`e`): Type your own resolution
   - **Skip** (`s`): Leave marker for later manual resolution
4. **Preview and validation**: Automatic validation before applying
5. **Progress tracking**: Track resolution across multiple conflicts
6. **Automatic backup**: Safe rollback capability

**When to use interactive mode:**

- ✅ Complex conflicts requiring careful review
- ✅ Need to combine parts from both versions
- ✅ Want guided assistance during resolution
- ✅ Multiple conflicts needing individual attention

**When to use other modes:**

- `--auto`: Clean merge with no conflicts (fastest, fully automatic)
- `--force`: Apply with markers for later IDE-based resolution
- `--dry-run`: Preview only, no changes applied

---

### Prerequisites

#### Template Bases Must Be Stored

Merge requires base template content. If not available:

```bash
$ python scripts/scaffold.py merge-template spec-template

⚠️  No base template stored
  Cannot perform three-way merge without base
  Showing diff instead...
```

**Solution**: Bases are automatically saved when creating new projects with `scaffold.py new`. For existing projects:

1. Manually edit `.scaffold-state.yaml` to add template_bases:

```yaml
template_bases:
  spec-template.md:
    version: "1.0.0"
    content: |
      ---
      template_version: "1.0.0"
      ---
      # Specification
      ...full original content...
```

2. Or use Python helper (for projects with unmodified templates):

```python
from pathlib import Path
from scripts.lib import template_version

template_version.save_all_template_bases(
    project_dir=Path("."),
    template_dir=Path(".specify/templates"),
)
```

### Use Cases

#### 1. Apply Upstream Improvements

```bash
# After check-templates shows outdated template
python scripts/scaffold.py check-templates
# → spec-template: 1.0.0 → 1.5.0

# Review changes
python scripts/scaffold.py diff-template spec-template

# Apply if clean
python scripts/scaffold.py merge-template spec-template --auto
```

#### 2. Preserve Customizations During Update

```bash
# Your spec-template has custom "Security Review" section
# Upstream adds "Performance Criteria" section
# → Three-way merge combines both automatically

python scripts/scaffold.py merge-template spec-template --auto
# ✅ Both sections preserved
```

#### 3. Batch Update Multiple Templates

```bash
#!/bin/bash
# update-templates.sh

for template in spec-template plan-template tasks-template; do
  echo "Updating $template..."
  python scripts/scaffold.py merge-template "$template" --auto

  if [ $? -ne 0 ]; then
    echo "⚠️ $template had conflicts - review manually"
  fi
done
```

### Safety Features

1. **Automatic backups**: Original file saved as `.backup-TIMESTAMP.md`
2. **Dry-run preview**: See merge result before applying
3. **Version tracking**: Base template updated in state file after merge
4. **Conflict detection**: Never silently overwrites conflicting changes

### Integration with Workflow

Complete drift resolution workflow:

```bash
# 1. Detect drift
python scripts/scaffold.py check-templates
# → ⚠️ 2 templates outdated

# 2. Review each template
python scripts/scaffold.py diff-template spec-template
python scripts/scaffold.py diff-template plan-template

# 3. Merge non-breaking changes
python scripts/scaffold.py merge-template spec-template --auto
python scripts/scaffold.py merge-template plan-template --auto

# 4. Verify merged templates
git diff .specify/templates/

# 5. Test project after updates
make test

# 6. Commit if all good
git add .specify/templates/
git commit -m "chore: update SpecKit templates to latest upstream"
```

---

## Roadmap: Future Phases

### Phase 3.1: Interactive Conflict Resolution ✅ **COMPLETE**

```bash
# Interactive resolution (implemented in Phase 3.1)
python scripts/scaffold.py merge-template spec-template --interactive
```

Provides:
- Step-by-step conflict resolution prompts
- Side-by-side diff view
- Accept local / upstream / both / edit options
- Immediate validation after resolution

### Phase 4: Automated Drift Monitoring (IMP-65 Fase 4)

- Weekly automated checks
- Slack/email notifications
- Dashboard with drift status across all projects
- Batch update tools

---

## Best Practices

1. **Check Regularly**: Run `check-templates` monthly or before major releases
2. **Track Versions**: Commit `.scaffold-state.yaml` to version control
3. **Review Before Merging**: Use `diff-template` to understand changes
4. **Test After Updates**: Run full test suite after applying template updates
5. **Backup Safety Net**: Keep template backups for at least one git commit
6. **Document Customizations**: Add comments explaining custom sections for easier conflict resolution

---

## Troubleshooting

### "No templates found"

**Cause**: `.specify/templates/` directory missing or empty.

**Solution**: Ensure you're in a project created with scaffold.py and templates exist:

```bash
ls .specify/templates/
```

### "Version metadata missing"

**Cause**: Templates created before IMP-65 Fase 1 don't have frontmatter.

**Solution**: Templates will be treated as unversioned (v0.0.0 implied). Consider re-generating from latest upstream.

### "No base template stored"

**Cause**: Project created before IMP-65 Fase 3 doesn't have template bases in `.scaffold-state.yaml`.

**Solution**:
1. Review diff with `diff-template` to understand changes
2. If template is unmodified, safe to copy upstream version directly
3. If template has customizations, manually add base to state file

### "git merge-file not found"

**Cause**: Git not installed or not in PATH.

**Solution**: Install git:

```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Verify
git --version
```

### "Conflict detected but content looks identical"

**Cause**: Whitespace or invisible character differences.

**Solution**: Use diff tool to see exact differences:

```bash
diff -u .specify/templates/spec-template.md \
  /path/to/scaffold-project/plate: spec-template.md...
...
⚠️  1 conflict(s) detected

Conflict #1 (lines 23-31):
  Type: both_modified
  Suggestion: Both local and upstream modified this section.
              Review carefully and choose the best combination.

To resolve conflicts:
  1. Open the merged file in your editor
  2. Search for conflict markers (<<<<<<, =======, >>>>>>>)
  3. Choose or combine the best content
  4. Remove all conflict markers
  5. Save the file

💡 Resolution options:
  --force        Apply merge with conflict markers (manual resolution)
  --interactive  Interactive conflict resolution (coming soon)
  --dry-run      Preview merge without applying
```

#### 3. Force Apply with Conflicts

```bash
$ python scripts/scaffold.py merge-template spec-template --force

⚠️  Force-applying merge with conflicts...
✅ Merge applied (with conflicts)
  Backup: .specify/templates/spec-template.backup-20260414-183500.md
  Open .specify/templates/spec-template.md to resolve conflicts
```

The file will contain conflict markers:

```markdown
## Overview

<<<<<<< LOCAL
Brief description with custom security notes.
||||||| BASE
Brief description of the feature.
=======
Brief description including business value and success metrics.
>>>>>>> UPSTREAM

## Technical Approach
```

Resolve by choosing the best content and removing markers:

```markdown
## Overview

Brief description including business value, success metrics, and custom security notes.

## Technical Approach
```

### Prerequisites

#### Template Bases Must Be Stored

Merge requires base template content. If not available:

```bash
$ python scripts/scaffold.py merge-template spec-template

⚠️  No base template stored
  Cannot perform three-way merge without base
  Showing diff instead...
```

**Solution**: Bases are automatically saved when creating new projects with `scaffold.py new`. For existing projects:

1. Manually edit `.scaffold-state.yaml` to add template_bases:

```yaml
template_bases:
  spec-template.md:
    version: "1.0.0"
    content: |
      ---
      template_version: "1.0.0"
      ---
      # Specification
      ...full original content...
```

2. Or use Python helper (for projects with unmodified templates):

```python
from pathlib import Path
from scripts.lib import template_version

template_version.save_all_template_bases(
    project_dir=Path("."),
    template_dir=Path(".specify/templates"),
)
```

### Use Cases

#### 1. Apply Upstream Improvements

```bash
# After check-templates shows outdated template
python scripts/scaffold.py check-templates
# → spec-template: 1.0.0 → 1.5.0

# Review changes
python scripts/scaffold.py diff-template spec-template

# Apply if clean
python scripts/scaffold.py merge-template spec-template --auto
```

#### 2. Preserve Customizations During Update

```bash
# Your spec-template has custom "Security Review" section
# Upstream adds "Performance Criteria" section
# → Three-way merge combines both automatically

python scripts/scaffold.py merge-template spec-template --auto
# ✅ Both sections preserved
```

#### 3. Batch Update Multiple Templates

```bash
#!/bin/bash
# update-templates.sh

for template in spec-template plan-template tasks-template; do
  echo "Updating $template..."
  python scripts/scaffold.py merge-template "$template" --auto

  if [ $? -ne 0 ]; then
    echo "⚠️ $template had conflicts - review manually"
  fi
done
```

### Safety Features

1. **Automatic backups**: Original file saved as `.backup-TIMESTAMP.md`
2. **Dry-run preview**: See merge result before applying
3. **Version tracking**: Base template updated in state file after merge
4. **Conflict detection**: Never silently overwrites conflicting changes

### Integration with Workflow

Complete drift resolution workflow:

```bash
# 1. Detect drift
python scripts/scaffold.py check-templates
# → ⚠️ 2 templates outdated

# 2. Review each template
python scripts/scaffold.py diff-template spec-template
python scripts/scaffold.py diff-template plan-template

# 3. Merge non-breaking changes
python scripts/scaffold.py merge-template spec-template --auto
python scripts/scaffold.py merge-template plan-template --auto

# 4. Verify merged templates
git diff .specify/templates/

# 5. Test project after updates
make test

# 6. Commit if all good
git add .specify/templates/
git commit -m "chore: update SpecKit templates to latest upstream"
```

---

## Roadmap: Future Phases

### Phase 3.1: Interactive Conflict Resolution ✅ **COMPLETE**

```bash
# Interactive resolution (implemented in Phase 3.1)
python scripts/scaffold.py merge-template spec-template --interactive
```

Provides:
- Step-by-step conflict resolution prompts
- Side-by-side diff view
- Accept local / upstream / both / edit options
- Immediate validation after resolution

### Phase 4: Automated Drift Monitoring (IMP-65 Fase 4)

- Weekly automated checks
- Slack/email notifications
- Dashboard with drift status across all projects
- Batch update tools

---

## Best Practices

1. **Check Regularly**: Run `check-templates` monthly or before major releases
2. **Track Versions**: Commit `.scaffold-state.yaml` to version control
3. **Review Before Merging**: Use `diff-template` to understand changes
4. **Test After Updates**: Run full test suite after applying template updates
5. **Backup Safety Net**: Keep template backups for at least one git commit
6. **Document Customizations**: Add comments explaining custom sections for easier conflict resolution

---

## Troubleshooting

### "No templates found"

**Cause**: `.specify/templates/` directory missing or empty.

**Solution**: Ensure you're in a project created with scaffold.py and templates exist:

```bash
ls .specify/templates/
```

### "Version metadata missing"

**Cause**: Templates created before IMP-65 Fase 1 don't have frontmatter.

**Solution**: Templates will be treated as unversioned (v0.0.0 implied). Consider re-generating from latest upstream.

### "No base template stored"

**Cause**: Project created before IMP-65 Fase 3 doesn't have template bases in `.scaffold-state.yaml`.

**Solution**:
1. Review diff with `diff-template` to understand changes
2. If template is unmodified, safe to copy upstream version directly
3. If template has customizations, manually add base to state file

### "git merge-file not found"

**Cause**: Git not installed or not in PATH.

**Solution**: Install git:

```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Verify
git --version
```

### "Conflict detected but content looks identical"

**Cause**: Whitespace or invisible character differences.

**Solution**: Use diff tool to see exact differences:

```bash
diff -u .specify/templates/spec-template.md \
  /path/to/scaffold-project/.specify/templates/spec-template.md
```

---

## Modular Templates and Drift Detection

**IMP-65 Phase 4** introduced a modular template system that fundamentally changes how drift is detected and managed.

### Overview

Instead of monolithic template files, the modular system uses:
- **Blocks**: Reusable, versioned template sections (`.specify/blocks/`)
- **Templates**: Composition files with `@include` directives
- **Patches**: Project-specific customizations (`.specify/patches/`)

### How Drift Detection Changes

#### Traditional Monolithic Templates
```
spec-template.md (v1.0.0) → spec-template.md (v1.5.0)
└─ Entire file comparison
   └─ High risk of conflicts with customizations
```

#### Modular Templates
```
spec-template.md
├─ @include blocks/user-scenarios-v1.0.md  → v2.0.md
├─ @include blocks/success-criteria-v1.0.md → v1.0.md (unchanged)
└─ Custom sections in .specify/patches/spec/001-custom.patch
```

**Benefits**:
- **Granular drift**: Track changes per block, not per file
- **Safer updates**: Update unchanged blocks automatically
- **Custom preservation**: Patches separate from standard content
- **Clearer conflicts**: Know exactly which block changed

### Checking Block Drift

```bash
# Check all blocks in project
./scripts/bin/list-patches .specify/patches/ --verbose

# Validate block versions
./scripts/bin/validate-block .specify/blocks/user-scenarios-v1.0.md --verbose

# Compare block with upstream
diff .specify/blocks/user-scenarios-v1.0.md \
  /path/to/scaffold-project/.specify/blocks/user-scenarios-v2.0.md
```

### Detecting Block Version Changes

**In Template Files**:
```markdown
# Before
@include blocks/user-scenarios-v1.0.md

# After (upstream update)
@include blocks/user-scenarios-v2.0.md
```

**Detection**:
```bash
# Show which blocks are included
grep "@include" .specify/templates/spec-template.md

# Compare with upstream
diff <(grep "@include" .specify/templates/spec-template.md) \
     <(grep "@include" /path/to/upstream/.specify/templates/spec-template.md)
```

### Upgrading to Modular System

If your project uses traditional monolithic templates, migrate to the modular system:

#### Step 1: Detect Customizations

```bash
# Analyze current template for customizations
./scripts/bin/migrate-template .specify/templates/spec-template.md --dry-run --verbose
```

#### Step 2: Migrate Template

```bash
# Perform migration (creates patches for customizations)
./scripts/bin/migrate-template .specify/templates/spec-template.md \
  --guide migration-guide.md
```

**Creates**:
- Backup in `.specify/migration-backups/`
- Patches for custom sections in `.specify/patches/`
- Migration guide documenting changes

#### Step 3: Adopt Block System

```bash
# Extract standard sections as blocks
mkdir -p .specify/blocks

# Create blocks for common sections
# (See MODULAR_TEMPLATES.md for details)

# Update template to use @include directives
# (Replaces content with references to blocks)
```

#### Step 4: Verify

```bash
# Compose template from blocks
./scripts/bin/compose-template .specify/templates/spec-template.md .specify/ -o composed.md

# Apply your custom patches
./scripts/bin/apply-patches composed.md .specify/patches/ -t spec-template -o final.md

# Compare with original
diff .specify/templates/spec-template.md final.md
```

### Block Versioning Best Practices

1. **Pin block versions in templates**:
   ```markdown
   @include blocks/user-scenarios-v1.0.md  ✅ Explicit version
   @include blocks/user-scenarios.md        ❌ Ambiguous
   ```

2. **Track block updates in .scaffold-state.yaml**:
   ```yaml
   blocks:
     user-scenarios:
       current_version: "1.0.0"
       upstream_version: "2.0.0"
       last_checked: "2026-04-15"
   ```

3. **Use semantic versioning**:
   - v1.0.0 → v1.1.0: Safe minor update (new features, backward compatible)
   - v1.1.0 → v2.0.0: Breaking change (review required)

4. **Document block changes**:
   - Include CHANGELOG in block frontmatter
   - Tag git commits with block version: `blocks/user-scenarios-v2.0.0`

### Patch Drift Detection

**Patches can become outdated** if upstream blocks change significantly.

#### Detecting Patch Issues

```bash
# Validate patches still apply cleanly
./scripts/bin/validate-patch .specify/patches/spec/001-custom.patch --verbose

# Try applying patches to current composed template
./scripts/bin/apply-patches composed.md .specify/patches/ -t spec --verbose
```

**Common Issues**:
- **Anchor not found**: Upstream removed or renamed the section patch anchors to
- **Duplicate content**: Patch adds content now in upstream block
- **Conflicts**: Patch modifies content changed in upstream

#### Fixing Outdated Patches

1. **Update anchor** if section renamed:
   ```markdown
   # Before
   @@ AFTER: ## User Scenarios

   # After (if upstream renamed section)
   @@ AFTER: ## User Stories
   ```

2. **Remove patch** if content now in upstream:
   ```bash
   # If upstream added your custom content, delete patch
   rm .specify/patches/spec/001-custom-feature.patch
   ```

3. **Regenerate patch** after block update:
   ```bash
   # Re-create patch based on new block version
   # (Manual process - copy custom content, update operations)
   ```

### Future Enhancements

**Planned for IMP-65 Phase 5** (not yet implemented):
- `check-blocks` command: Detect outdated blocks in project
- `upgrade-block` command: Safely upgrade block with conflict resolution
- `patch-compat` command: Test patch compatibility with new block versions
- Auto-migration of patches when blocks are upgraded

### Migration Compatibility

The modular system **coexists with traditional templates**:
- Can use both monolithic and modular templates in same project
- Drift detection works for both types
- Migrate templates incrementally as needed

**No forced migration** - traditional templates continue to work.

---

## See Also

- [IMP-65 Full Specification](TODO.md#imp-65) - Implementation plan for all 4 phases
- [MODULAR_TEMPLATES.md](MODULAR_TEMPLATES.md) - Complete guide to modular template system
- [TEMPLATE_USAGE.md](TEMPLATE_USAGE.md) - General template usage guide
- [SCAFFOLD_GUIDE.md](SCAFFOLD_GUIDE.md) - Complete scaffold.py reference
- [SpecKit Documentation](docs/copilot/) - Workflow automation guides
