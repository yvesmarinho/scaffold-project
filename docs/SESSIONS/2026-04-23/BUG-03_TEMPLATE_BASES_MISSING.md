---
bug_id: BUG-03
title: "compose.py doesn't initialize template_bases in .scaffold-state.yaml"
severity: P0-blocking
discovered: 2026-04-23
session: 2026-04-23
discovered_during: IMP-65 Scenario 1 testing
status: documented
assigned_to: null
---

# BUG-03: Missing template_bases Initialization in compose.py

## Problem Description

When creating a new project with `scaffold.py compose`, the system does not save the base template content to `.scaffold-state.yaml`. This prevents the template merge functionality (IMP-65 Phase 3) from working correctly.

### Expected Behavior

After `scaffold.py compose` completes:
- `.scaffold-state.yaml` should contain a `template_bases` section
- Each template should have its initial version and content saved
- Future `merge-template` commands can perform three-way merges (base, local, upstream)

### Actual Behavior

- `.scaffold-state.yaml` only contains: `scaffold_version`, `created_at`, `updated_at`, `project`, `paths`, `profiles_applied`, `template_versions`
- Missing: `template_bases` section
- When running `merge-template`, the system fails with:
  ```
  ⚠️  No base template stored
    Cannot perform three-way merge without base
    Showing diff instead...
  ```

## Impact

- **Severity**: P0-blocking for IMP-65 merge functionality
- **Scope**: All new projects created with compose
- **Workaround**: Manual initialization using `save_all_template_bases()` (see below)

## Root Cause

`scripts/flows/compose.py` does not call `template_version.save_all_template_bases()` after copying templates to the new project directory.

The required function exists (`scripts/lib/template_version.py::save_all_template_bases`), but is never invoked during project creation.

## Reproduction

```bash
# 1. Create new project
cd scaffold-project
python3 scripts/scaffold.py compose \
  --ci \
  --project-name "test-bug03" \
  --domain programming \
  --language python \
  --target-dir ../test-bug03 \
  --shared-dir ~/.copilot-shared

# 2. Check .scaffold-state.yaml
cd ../test-bug03
grep "template_bases" .scaffold-state.yaml  # ❌ Not found

# 3. Try to merge a template
python3 ../scaffold-project/scripts/scaffold.py merge-template spec-template
# ❌ Error: "No base template stored"
```

## Workaround

For existing projects, run this script to initialize template bases:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path("../scaffold-project/scripts")))

from scripts.lib import template_version

project_dir = Path(".")
template_dir = project_dir / ".specify" / "templates"

count = template_version.save_all_template_bases(
    project_dir=project_dir,
    template_dir=template_dir,
)

print(f"✅ Saved {count} template bases")
```

## Solution

### Required Changes

**File**: `scripts/flows/compose.py`

**Location**: After template copy completes (around line where `.scaffold-state.yaml` is created)

**Add**:
```python
from ..lib import template_version

# ... existing code ...

# After copying templates to target_dir/.specify/templates/
template_dir = target_dir / ".specify" / "templates"
template_version.save_all_template_bases(
    project_dir=target_dir,
    template_dir=template_dir,
)
log.info("✅ Saved template bases for merge tracking")
```

### Testing

After fix:
1. Create new project with `compose`
2. Verify `.scaffold-state.yaml` contains `template_bases` section
3. Verify all 6 templates have `version` and `content` stored
4. Modify upstream template (bump version)
5. Run `merge-template --auto` successfully

## Related

- **IMP-65**: Template synchronization system (Phases 1-3)
- **IMP-65 Scenario 1**: Clean merge testing (where bug was discovered)
- **docs/SESSIONS/2026-04-21/IMP-65_TEST_STRATEGY.md**: Test plan that exposed this issue

## Discovery Details

While executing IMP-65 Scenario 1 (Clean Merge - Independent Changes):
1. Created drift by updating upstream spec-template.md to v1.5.0
2. `check-templates` detected drift correctly ✅
3. `diff-template` showed changes correctly ✅
4. `merge-template --auto` failed with "No base template stored" ❌
5. Inspected `.scaffold-state.yaml` and found missing `template_bases`
6. Used workaround script to populate bases manually
7. Re-ran `merge-template --auto` → SUCCESS ✅

## Test Results (Post-Workaround)

```
✅ check-templates: Detected drift (1.0.0 → 1.5.0)
✅ diff-template: Showed +33 lines, ~2 modified
✅ merge-template --auto: Clean merge, no conflicts
✅ Backup created: spec-template.backup-20260423-101134.md
✅ Version updated: 1.0.0 → 1.5.0
✅ New section added: "Performance Criteria"
✅ check-templates: No drift after merge
```

## Next Steps

1. ✅ Document bug (this file)
2. Add TODO item in [docs/TODO.md](../TODO.md)
3. Create GitHub issue (optional)
4. Implement fix in `compose.py`
5. Add test to verify `template_bases` initialization
6. Continue IMP-65 Scenario 2 testing

---

**Status**: Documented, workaround available
**Assignee**: TBD
**Estimated Effort**: 1-2 hours (implementation + tests)
