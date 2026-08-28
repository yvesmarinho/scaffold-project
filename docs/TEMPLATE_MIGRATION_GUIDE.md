# IMP-65 Template Migration Guide

**Version**: 1.0
**Last Updated**: 2026-04-28
**Status**: Production Ready
**Audience**: Developers, Platform Engineers, DevOps

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Migration Scenarios](#migration-scenarios)
4. [Step-by-Step Migration](#step-by-step-migration)
5. [Validation & Testing](#validation--testing)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Post-Migration](#post-migration)

---

## Overview

### What is Template Synchronization?

The Template Synchronization System (IMP-65) allows projects to receive updates from upstream templates while preserving local customizations. This ensures:

- ✅ Projects stay current with template improvements
- ✅ Local customizations are never lost
- ✅ Breaking changes require explicit approval
- ✅ Automatic backups before every update

### Who Needs to Migrate?

**Migrate if your project**:
- ✅ Was created before 2026-04-15 (before IMP-65)
- ✅ Has `.scaffold-state.yaml` **without** `template_bases` section
- ✅ Wants to receive template updates automatically

**No migration needed if**:
- ❌ Project created after 2026-04-15 (already has template_bases)
- ❌ Project is read-only / archived
- ❌ Templates are heavily customized (not following standard structure)

---

## Prerequisites

### Check Project Status

```bash
cd your-project/

# 1. Check if .scaffold-state.yaml exists
ls -lh .scaffold-state.yaml  # Should exist

# 2. Check for template_bases section
grep -A5 "template_bases:" .scaffold-state.yaml

# If "template_bases:" NOT FOUND → Need to migrate
# If "template_bases:" EXISTS → Already migrated ✅
```

### Required Tools

```bash
# Python 3.11+
python3 --version  # → 3.11 or higher

# Git (for backups)
git --version  # → 2.0 or higher

# scaffold.py script
ls /path/to/scaffold-project/scripts/scaffold.py  # Should exist
```

### Create Backup

```bash
# Full project backup
cd ..
tar -czf your-project-backup-$(date +%Y%m%d).tar.gz your-project/

# Verify backup
tar -tzf your-project-backup-*.tar.gz | head
```

---

## Migration Scenarios

### Scenario 1: Standard Project (Most Common)

**Characteristics**:
- Project created with `scaffold.py new`
- Standard template structure in `.specify/templates/`
- Minor customizations only

**Migration**: [Standard Migration](#standard-migration-40-min)
**Risk**: 🟢 Low

---

### Scenario 2: Heavily Customized Templates

**Characteristics**:
- Templates heavily modified (>50% custom content)
- Custom sections added
- Original structure changed

**Migration**: [Custom Template Migration](#custom-template-migration-60-90-min)
**Risk**: 🟡 Medium

---

### Scenario 3: Missing Templates

**Characteristics**:
- Some templates deleted
- `.specify/templates/` partially empty
- Only using subset of template system

**Migration**: [Partial Template Migration](#partial-template-migration-20-30-min)
**Risk**: 🟢 Low

---

### Scenario 4: No SpecKit Project

**Characteristics**:
- `.specify/` directory doesn't exist
- Project doesn't use template system
- Created manually or from other source

**Migration**: Not applicable — project doesn't use templates
**Action**: Consider running `scaffold.py upgrade` to add SpecKit

---

## Step-by-Step Migration

### Standard Migration (40 min)

**Objective**: Add `template_bases` to `.scaffold-state.yaml` for standard projects.

#### Phase 1: Inventory (10 min)

```bash
cd your-project/

# 1. List current templates
ls -lh .specify/templates/
# Expected: spec-template.md, plan-template.md, tasks-template.md, etc.

# 2. Check template versions
grep "template_version" .specify/templates/*.md
# Example output:
#   spec-template.md:template_version: "1.0.0"
#   plan-template.md:template_version: "1.0.0"

# 3. Capture current state
cp .scaffold-state.yaml .scaffold-state.yaml.pre-migration
```

#### Phase 2: Generate Template Bases (15 min)

**Option A: Automatic (Recommended)**

```bash
# Use scaffold.py to populate template_bases automatically
python3 /path/to/scaffold-project/scripts/scaffold.py --populate-template-bases

# Verify template_bases added
grep -A10 "template_bases:" .scaffold-state.yaml
```

**Option B: Manual (if automatic fails)**

```python
#!/usr/bin/env python3
"""populate_template_bases.py - Manually add template bases to state file"""

import yaml
from pathlib import Path

def migrate_template_bases(project_dir: Path):
    """Add template_bases to .scaffold-state.yaml."""
    state_file = project_dir / ".scaffold-state.yaml"
    templates_dir = project_dir / ".specify" / "templates"

    # Load current state
    with open(state_file) as f:
        state = yaml.safe_load(f)

    # Add template_bases if not present
    if "template_bases" not in state:
        state["template_bases"] = {}

        # Read all templates
        for template_file in templates_dir.glob("*.md"):
            template_name = template_file.name
            content = template_file.read_text()
            state["template_bases"][template_name] = content

        # Write back
        with open(state_file, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Added {len(state['template_bases'])} template bases")
    else:
        print("⚠️ template_bases already exists")

if __name__ == "__main__":
    import sys
    project = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    migrate_template_bases(project)
```

**Run manual script**:

```bash
# Save script above as populate_template_bases.py
python3 populate_template_bases.py .

# Verify
grep -A2 "template_bases:" .scaffold-state.yaml | head -20
```

#### Phase 3: Validation (10 min)

```bash
# 1. Verify template_bases section exists
grep "template_bases:" .scaffold-state.yaml  # → Should find

# 2. Count template bases
python3 <<EOF
import yaml
with open(".scaffold-state.yaml") as f:
    state = yaml.safe_load(f)
print(f"Template bases: {len(state.get('template_bases', {}))}")
EOF
# Expected: 3-8 templates depending on profiles

# 3. Check drift detection works
python3 /path/to/scaffold-project/scripts/scaffold.py check-templates
# Expected: "✅ All templates up-to-date" OR "⚠️ X template(s) outdated"

# 4. Git commit migration
git add .scaffold-state.yaml
git commit -m "chore: add template_bases for IMP-65 compatibility

- Migrated .scaffold-state.yaml to include template_bases
- Enables automatic template synchronization
- All templates captured at current versions

Migration ref: IMP-65 P0-3"
```

#### Phase 4: Test Update (5 min)

```bash
# Test that template updates now work
python3 /path/to/scaffold-project/scripts/scaffold.py check-templates --json

# If drift detected, test diff command
python3 /path/to/scaffold-project/scripts/scaffold.py diff-template spec-template

# SUCCESS if:
# - check-templates runs without errors
# - diff-template shows changes (if any)
# - No "missing base" errors
```

---

### Custom Template Migration (60-90 min)

**For projects with heavily customized templates.**

#### Phase 1: Document Customizations (20 min)

```bash
# 1. Create customization inventory
cat > template-customizations.md <<EOF
# Template Customizations Inventory

## spec-template.md
- Added: Security Requirements section (lines 45-78)
- Modified: Overview section (added deployment context)
- Removed: None

## plan-template.md
- Added: Blue-Green Deployment Strategy (lines 120-150)
- Modified: Implementation Plan (added rollback steps)
- Removed: Default deployment section

## tasks-template.md
- Added: Custom task categories (Security, Performance, Compliance)
- Modified: Task format (added priority levels)
- Removed: None
EOF

# 2. Create diff snapshots
for template in .specify/templates/*.md; do
    name=$(basename "$template")
    # Compare with upstream (if available)
    diff -u /path/to/scaffold-project/.specify/templates/"$name" "$template" \
        > "customization-${name}.diff" 2>/dev/null || true
done
```

#### Phase 2: Snapshot Current State (10 min)

```bash
# Create complete snapshot before migration
mkdir -p .migration-snapshots/$(date +%Y%m%d)

# Copy all templates
cp -r .specify/templates/ .migration-snapshots/$(date +%Y%m%d)/

# Copy state file
cp .scaffold-state.yaml .migration-snapshots/$(date +%Y%m%d)/

# Git commit snapshot
git add .migration-snapshots/
git commit -m "snapshot: pre-IMP-65 migration backup"
```

#### Phase 3: Selective Base Capture (20 min)

```bash
# For each template, decide:
# - Use original upstream version as base (recommended)
# - Use current customized version as base (preserves all customizations)

python3 <<EOF
import yaml
from pathlib import Path

project = Path(".")
state_file = project / ".scaffold-state.yaml"
templates_dir = project / ".specify" / "templates"
upstream_dir = Path("/path/to/scaffold-project/.specify/templates")

# Load state
with open(state_file) as f:
    state = yaml.safe_load(f)

if "template_bases" not in state:
    state["template_bases"] = {}

# For each template, choose base strategy
for template_file in templates_dir.glob("*.md"):
    name = template_file.name

    # OPTION 1: Use upstream as base (recommended for clean merges)
    upstream_file = upstream_dir / name
    if upstream_file.exists():
        base_content = upstream_file.read_text()
        print(f"✅ {name}: using upstream as base")
    else:
        # OPTION 2: Use current as base (preserves all customizations)
        base_content = template_file.read_text()
        print(f"⚠️ {name}: using current as base (no upstream found)")

    state["template_bases"][name] = base_content

# Save
with open(state_file, "w") as f:
    yaml.dump(state, f, default_flow_style=False, sort_keys=False)

print(f"\n✅ Migration complete: {len(state['template_bases'])} bases captured")
EOF
```

#### Phase 4: Test Merge Behavior (10 min)

```bash
# Test that customizations are preserved during merge
python3 /path/to/scaffold-project/scripts/scaffold.py diff-template spec-template

# Verify output shows:
# - Your customizations highlighted
# - Upstream changes highlighted
# - Both can coexist

# Test merge (dry-run)
python3 /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template --dry-run

# Review output carefully before proceeding
```

---

### Partial Template Migration (20-30 min)

**For projects missing some templates.**

```bash
# 1. Inventory what exists
ls -1 .specify/templates/

# 2. Add only existing templates to template_bases
python3 <<EOF
import yaml
from pathlib import Path

state_file = Path(".scaffold-state.yaml")
templates_dir = Path(".specify/templates")

with open(state_file) as f:
    state = yaml.safe_load(f)

if "template_bases" not in state:
    state["template_bases"] = {}

# Add only existing templates
for template_file in templates_dir.glob("*.md"):
    name = template_file.name
    content = template_file.read_text()
    state["template_bases"][name] = content
    print(f"✅ Added: {name}")

with open(state_file, "w") as f:
    yaml.dump(state, f, default_flow_style=False, sort_keys=False)

print(f"\nTotal templates: {len(state['template_bases'])}")
EOF

# 3. Validate
python3 /path/to/scaffold-project/scripts/scaffold.py check-templates

# Missing templates will be reported but won't block migration
```

---

## Validation & Testing

### Post-Migration Checklist

```bash
# ✅ 1. template_bases section exists
grep -q "template_bases:" .scaffold-state.yaml && echo "✅ PASS" || echo "❌ FAIL"

# ✅ 2. Template count matches
python3 <<EOF
import yaml
with open(".scaffold-state.yaml") as f:
    state = yaml.safe_load(f)
templates = len(list(Path(".specify/templates").glob("*.md")))
bases = len(state.get("template_bases", {}))
print(f"Templates: {templates}, Bases: {bases}")
assert templates == bases, "Mismatch!"
print("✅ PASS: Counts match")
EOF

# ✅ 3. check-templates command works
python3 /path/to/scaffold-project/scripts/scaffold.py check-templates
echo "✅ PASS: check-templates runs"

# ✅ 4. diff-template command works
python3 /path/to/scaffold-project/scripts/scaffold.py diff-template spec-template
echo "✅ PASS: diff-template runs"

# ✅ 5. Git history clean
git status  # Should show no uncommitted changes
```

### Integration Test

```bash
# Perform actual template update on test template

# 1. Create test template with minor change
cat >> .specify/templates/spec-template.md <<EOF

## Test Section (Migration Validation)
This section was added post-migration to validate template sync.
EOF

# 2. Commit change
git add .specify/templates/spec-template.md
git commit -m "test: add test section for migration validation"

# 3. Simulate upstream update (if available)
# Copy updated template from upstream
# cp /path/to/scaffold-project/.specify/templates/spec-template.md /tmp/upstream-spec.md

# 4. Test merge preserves customizations
# python3 /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template --auto

# 5. Verify test section still exists
grep -q "Test Section (Migration Validation)" .specify/templates/spec-template.md \
    && echo "✅ PASS: Customizations preserved" \
    || echo "❌ FAIL: Customizations lost"
```

---

## Rollback Procedures

### Emergency Rollback

**If migration causes issues:**

```bash
# Option 1: Restore from pre-migration backup
cp .scaffold-state.yaml.pre-migration .scaffold-state.yaml
git checkout -- .scaffold-state.yaml

# Option 2: Restore from Git
git log --oneline | grep -i migration  # Find migration commit
git revert <commit-hash>

# Option 3: Restore from tar backup
cd ..
tar -xzf your-project-backup-*.tar.gz
cd your-project/

# Verify rollback
grep -q "template_bases:" .scaffold-state.yaml || echo "✅ Rollback complete"
```

### Selective Template Rollback

**Rollback only specific templates:**

```python
#!/usr/bin/env python3
"""rollback_template.py - Remove specific template from template_bases"""

import yaml
import sys
from pathlib import Path

def rollback_template(project_dir: Path, template_name: str):
    state_file = project_dir / ".scaffold-state.yaml"

    with open(state_file) as f:
        state = yaml.safe_load(f)

    if "template_bases" in state and template_name in state["template_bases"]:
        del state["template_bases"][template_name]

        with open(state_file, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Removed {template_name} from template_bases")
    else:
        print(f"❌ {template_name} not found in template_bases")

if __name__ == "__main__":
    template = sys.argv[1] if len(sys.argv) > 1 else "spec-template.md"
    rollback_template(Path("."), template)
```

---

## Troubleshooting

### Issue: "template_bases not found"

**Symptom**: `merge-template` fails with "cannot perform three-way merge without base"

**Solution**:
```bash
# Check if template_bases exists
grep "template_bases:" .scaffold-state.yaml

# If missing, re-run migration Phase 2
python3 populate_template_bases.py .
```

---

### Issue: "Template versions mismatch"

**Symptom**: `check-templates` reports incorrect versions

**Solution**:
```bash
# Verify template_versions and template_bases are consistent
python3 <<EOF
import yaml
with open(".scaffold-state.yaml") as f:
    state = yaml.safe_load(f)
versions = state.get("template_versions", {})
bases = state.get("template_bases", {})
for name in versions:
    if name not in bases:
        print(f"❌ Missing base for: {name}")
EOF

# Add missing bases manually
```

---

### Issue: "Merge conflicts after migration"

**Symptom**: First merge after migration produces conflicts

**Solution**:
```bash
# This is expected if templates diverged significantly
# Review conflicts carefully using interactive mode
python3 /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template --interactive

# Or merge with --force to accept all upstream changes
python3 /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template --force
```

---

### Issue: "Performance degradation"

**Symptom**: `.scaffold-state.yaml` file very large (>1MB)

**Solution**:
```bash
# Check file size
ls -lh .scaffold-state.yaml

# If >1MB, template_bases likely has redundant content
# Review and compress:
python3 <<EOF
import yaml
with open(".scaffold-state.yaml") as f:
    state = yaml.safe_load(f)
bases = state.get("template_bases", {})
print(f"Total bases: {len(bases)}")
for name, content in bases.items():
    print(f"{name}: {len(content)} bytes")
# Remove duplicates or outdated bases
EOF
```

---

## Post-Migration

### Regular Maintenance

**Weekly drift check** (5 min):
```bash
python3 /path/to/scaffold-project/scripts/scaffold.py check-templates

# If drift detected:
# 1. Review changes: scaffold.py diff-template <name>
# 2. Merge updates: scaffold.py merge-template <name> --auto
# 3. Commit: git commit -m "chore: sync templates from upstream"
```

**Monthly review** (15 min):
```bash
# Verify template_bases still accurate
python3 <<EOF
import yaml
from pathlib import Path

with open(".scaffold-state.yaml") as f:
    state = yaml.safe_load(f)

templates_dir = Path(".specify/templates")
for template_file in templates_dir.glob("*.md"):
    name = template_file.name
    if name not in state.get("template_bases", {}):
        print(f"⚠️ Missing base for: {name}")
EOF

# Add any missing bases
```

---

### Next Steps

After successful migration:

1. ✅ **Enable CI/CD drift detection** ([IMP-65 P1](../SESSIONS/2026-04-21/IMP-65_ACTION_ITEMS.md))
2. ✅ **Setup automated alerts** for template drift
3. ✅ **Document project-specific customizations** in template comments
4. ✅ **Train team** on merge workflow (diff → review → merge)

---

## FAQ

**Q: Can I migrate gradually (one template at a time)?**
A: Yes! Add templates to `template_bases` incrementally. Start with least-customized templates.

**Q: What if upstream template has breaking changes?**
A: Breaking changes require explicit `--force` flag. System prevents accidental auto-merge.

**Q: Can I use different base versions per template?**
A: Yes. Each template's base is independent. Mix old and new versions as needed.

**Q: How do I migrate from IMP-65 back to manual management?**
A: Remove `template_bases` section from `.scaffold-state.yaml`. Templates return to manual-only updates.

**Q: Does migration affect existing profiles?**
A: No. Migration only affects template sync. Profiles remain unchanged.

---

**Migration Support**: See [IMP-65 documentation](../SESSIONS/2026-04-21/) for detailed system overview and troubleshooting.
