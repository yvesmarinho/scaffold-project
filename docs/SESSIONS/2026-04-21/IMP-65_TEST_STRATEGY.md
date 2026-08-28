# IMP-65 Test Strategy — Template Update System Validation

**Session**: 2026-04-21
**Objective**: Validate template synchronization system on real project with customizations
**Time Budget**: 3-5 hours
**Status**: Ready to Execute

---

## Table of Contents

1. [Overview](#overview)
2. [Test Scenarios](#test-scenarios)
3. [Test Environment Setup](#test-environment-setup)
4. [Validation Procedures](#validation-procedures)
5. [Expected vs Actual Behavior](#expected-vs-actual-behavior)
6. [Rollback Procedures](#rollback-procedures)
7. [Success Criteria](#success-criteria)

---

## Overview

### Objective

Validate that the IMP-65 template synchronization system correctly:
- Detects template drift between local and upstream versions
- Displays clear diffs of changes
- Merges upstream updates while preserving local customizations
- Handles conflicts gracefully with interactive resolution
- Updates version tracking correctly
- Creates reliable backups

### Scope

**In Scope**:
- ✅ Template versioning and drift detection
- ✅ Diff generation and visualization
- ✅ Three-way merge operations
- ✅ Interactive conflict resolution
- ✅ State tracking and version management
- ✅ Backup and restore mechanisms

**Out of Scope**:
- ❌ Profile generation (already tested)
- ❌ Block system (Phase 4, tested separately)
- ❌ Multi-project synchronization (future phase)
- ❌ Automated drift monitoring (future phase)

### Test Approach

**Strategy**: Realistic Simulation
- Use real profile (python-fastapi)
- Add realistic customizations (not toy examples)
- Simulate actual upstream updates
- Follow documented workflow exactly
- Measure actual metrics (time, steps, clarity)

**Validation Method**:
1. Baseline capture (before)
2. Execute update workflow
3. Validation checks (after)
4. Diff analysis (before vs after)
5. Regression test creation

---

## Test Scenarios

### Scenario 1: Clean Merge (Independent Changes) ✅

**Setup**:
- Local: Custom security section added to spec-template
- Upstream: New performance section added to spec-template
- Changes are in different sections (no overlap)

**Expected Behavior**:
- `check-templates` detects drift
- `diff-template` shows both changes clearly
- `merge-template --auto` succeeds without conflicts
- Both custom security AND new performance sections present in result
- Version updated to upstream version
- Backup created

**Validation**:
```bash
# Before
grep -A5 "Security Review" .specify/templates/spec-template.md  # → Exists
grep -A5 "Performance Criteria" .specify/templates/spec-template.md  # → Not found

# After
grep -A5 "Security Review" .specify/templates/spec-template.md  # → Still exists ✅
grep -A5 "Performance Criteria" .specify/templates/spec-template.md  # → Now exists ✅
```

**Success Criteria**:
- ✅ Exit code 0 (clean merge)
- ✅ Both sections present
- ✅ Version bumped correctly
- ✅ Backup created with timestamp

---

### Scenario 2: Merge with Conflict (Overlapping Changes) ⚠️

**Setup**:
- Local: "Technical Approach" section has custom deployment notes
- Upstream: "Technical Approach" section expanded with new examples
- Changes overlap in same section

**Expected Behavior**:
- `merge-template --auto` fails with conflict detected
- Conflict markers show LOCAL vs UPSTREAM clearly
- `merge-template --interactive` provides guided resolution
- User can choose: keep local, accept upstream, or combine both
- After resolution, version updated and backup created

**Validation**:
```bash
# Interactive mode should show:
# - Side-by-side diff of conflicting section
# - Clear options: [l] local, [u] upstream, [b] both, [e] edit
# - Immediate feedback after choice
# - Validation that conflict is resolved

# After resolution:
grep "<<<<<<< LOCAL" .specify/templates/spec-template.md  # → Not found ✅
grep "deployment notes" .specify/templates/spec-template.md  # → Still exists ✅
grep "new examples" .specify/templates/spec-template.md  # → Now exists ✅
```

**Success Criteria**:
- ✅ Conflict detected (not silently merged wrong)
- ✅ Interactive mode provides clear options
- ✅ User choice is applied correctly
- ✅ No conflict markers remain
- ✅ Both valuable changes preserved

---

### Scenario 3: Breaking Change Update 🚨

**Setup**:
- Local: spec-template v1.0.0 (stable)
- Upstream: spec-template v2.0.0 with `breaking_changes: true`
- Breaking change removes deprecated section

**Expected Behavior**:
- `check-templates` shows breaking change warning
- `diff-template` highlights removed section
- `merge-template --auto` should pause for confirmation
- User must explicitly approve breaking change
- Changelog/migration notes shown before applying

**Validation**:
```bash
# check-templates output:
# ⚠️  Breaking Change Detected
#   spec-template: 1.0.0 → 2.0.0
#   Review changes carefully before updating

# diff-template output:
# - ## Deprecated Section (removed in v2.0)

# merge-template requires --force or --breaking-ok flag
scaffold.py merge-template spec --auto  # → Fails with warning
scaffold.py merge-template spec --auto --breaking-ok  # → Succeeds
```

**Success Criteria**:
- ✅ Breaking change warning displayed
- ✅ Auto-merge blocked without explicit approval
- ✅ Removed section clearly shown in diff
- ✅ Migration guidance provided (if available)

---

### Scenario 4: Multiple Template Updates 📦

**Setup**:
- Drift detected in 3 templates: spec, plan, tasks
- Each has different update types (clean, conflict, breaking)

**Expected Behavior**:
- `check-templates` shows all 3 outdated
- User can update one-by-one or batch process
- Each template handled independently
- State tracking updated for each
- Aggregate summary at end

**Validation**:
```bash
# check-templates output:
# ⚠️ Template Drift Detected: 3 template(s)
#   spec-template: 1.0.0 → 1.5.0
#   plan-template: 1.0.0 → 1.2.0
#   tasks-template: 1.0.0 → 2.0.0 (breaking)

# Update each:
scaffold.py merge-template spec --auto        # → Clean merge
scaffold.py merge-template plan --interactive # → Conflict resolution
scaffold.py merge-template tasks --breaking-ok # → Breaking change

# Verify all updated:
scaffold.py check-templates  # → ✅ All templates up-to-date
```

**Success Criteria**:
- ✅ All templates detected
- ✅ Each template can be updated independently
- ✅ Different merge strategies work per template
- ✅ Final check confirms all updated

---

### Scenario 5: Missing Template Base (Pre-IMP-65 Project) 🔧

**Setup**:
- Project created before IMP-65 (no template bases in state file)
- Attempting three-way merge without base

**Expected Behavior**:
- `merge-template` detects missing base
- Graceful degradation to two-way diff
- Clear message explaining limitation
- Guidance on how to add base or proceed without

**Validation**:
```bash
# merge-template output:
# ⚠️  No base template stored
#   Cannot perform three-way merge without base
#   Showing two-way diff instead...
#
#   To enable three-way merge:
#   1. Manually add template base to .scaffold-state.yaml
#   2. Or use --two-way flag to proceed with diff-only merge

# Fallback behavior:
scaffold.py merge-template spec --two-way  # → Works with diff
```

**Success Criteria**:
- ✅ Missing base detected (not crash)
- ✅ Fallback to two-way diff works
- ✅ Clear error message with recovery steps
- ✅ Migration path documented

---

### Scenario 6: Customizations in Security-Critical Sections 🔒

**Setup**:
- Local: Custom OAuth2 + MFA requirements in spec-template
- Upstream: New security section added (different location)

**Expected Behavior**:
- Custom security requirements preserved
- New upstream security section added
- No silent deletion of security policies
- Clear visibility of all security-related changes

**Validation**:
```bash
# Before
grep -i "oauth2\|mfa" .specify/templates/spec-template.md  # → Found

# After merge
grep -i "oauth2\|mfa" .specify/templates/spec-template.md  # → Still found ✅
grep -i "new security section" .specify/templates/spec-template.md  # → Also found ✅

# Diff should highlight all security changes
scaffold.py diff-template spec | grep -i "security"  # → Shows all changes
```

**Success Criteria**:
- ✅ No security policy deletion
- ✅ All security changes visible
- ✅ Custom and upstream security requirements coexist

---

### Scenario 7: Backup and Rollback 🔄

**Setup**:
- Apply template update
- Discover issue after applying
- Need to rollback to previous version

**Expected Behavior**:
- Backup automatically created with timestamp
- Backup preserves exact previous state
- Rollback restores working state
- Version tracking updated on rollback

**Validation**:
```bash
# Before update
ls .specify/templates/*.backup-*  # → No backups yet

# After update
ls .specify/templates/*.backup-*  # → Backup exists with timestamp
# Example: spec-template.backup-20260421-103000.md

# Rollback test
cp .specify/templates/spec-template.backup-*.md .specify/templates/spec-template.md
# → Verify project works again

# Automated rollback (if implemented)
scaffold.py rollback-template spec  # → Restores from latest backup
```

**Success Criteria**:
- ✅ Backup created before every destructive operation
- ✅ Backup filename includes timestamp for traceability
- ✅ Backup content is exact copy (byte-for-byte)
- ✅ Rollback restores working state

---

### Scenario 8: Dry-Run Preview 👁️

**Setup**:
- Template has pending update
- User wants to preview before applying

**Expected Behavior**:
- `merge-template --dry-run` shows what would happen
- No files modified
- Clear preview of merged result
- User can review before committing

**Validation**:
```bash
# Capture original checksum
md5sum .specify/templates/spec-template.md > /tmp/before.md5

# Dry-run
scaffold.py merge-template spec --dry-run > /tmp/preview.txt

# Verify no changes
md5sum -c /tmp/before.md5  # → File unchanged ✅

# Preview should show:
cat /tmp/preview.txt | grep "DRY-RUN"  # → Clearly marked
cat /tmp/preview.txt | grep "Would apply"  # → Shows what would change
```

**Success Criteria**:
- ✅ No files modified during dry-run
- ✅ Preview shows complete merged result
- ✅ Clearly marked as preview/simulation
- ✅ User can make informed decision

---

## Test Environment Setup

### Prerequisites

```bash
# Required tools
python --version  # → 3.11+
git --version     # → 2.0+
uv --version      # → 0.5+

# Required files
ls scripts/scaffold.py  # → Exists
ls scripts/lib/template_*.py  # → 7 modules exist

# Test project location
TEST_PROJECT=/tmp/imp-65-test-project
```

### Setup Steps

#### Step 1: Create Test Project (15 min)

```bash
# Navigate to template repo
cd /path/to/scaffold-project

# Create test project with python-fastapi profile
python scripts/scaffold.py new \
  --name "imp-65-test-api" \
  --profile python-fastapi \
  --project-path "$TEST_PROJECT" \
  --non-interactive

# Verify project created
cd "$TEST_PROJECT"
ls .specify/templates/  # → spec, plan, tasks templates exist
cat .scaffold-state.yaml  # → Has template_versions section
```

#### Step 2: Add Realistic Customizations (15 min)

**Customize spec-template.md**:
```bash
cat >> .specify/templates/spec-template.md <<'EOF'

## Security Review Checklist

**Authentication**:
- [ ] OAuth2 with PKCE flow
- [ ] MFA required for admin users
- [ ] Token rotation every 24h

**Authorization**:
- [ ] Role-Based Access Control (RBAC)
- [ ] Principle of Least Privilege
- [ ] Admin actions require approval

**Data Protection**:
- [ ] AES-256 encryption at rest
- [ ] TLS 1.3 for data in transit
- [ ] PII encrypted in database

**Compliance**:
- [ ] LGPD requirements met
- [ ] Audit logging configured
- [ ] Data retention policy defined
EOF
```

**Customize plan-template.md**:
```bash
# Add custom deployment section
sed -i '/## Implementation Plan/a \
\n## Deployment Strategy\n\
\n**Blue-Green Deployment**:\n\
1. Deploy to green environment\n\
2. Run smoke tests\n\
3. Switch traffic gradually (10%, 50%, 100%)\n\
4. Monitor error rates\n\
5. Rollback if issues detected\n\
\n**Rollback Plan**:\n\
- Keep blue environment running for 24h\n\
- DNS TTL = 60s for quick switchback\n\
- Database migrations must be backward-compatible\n' \
  .specify/templates/plan-template.md
```

**Customize tasks-template.md**:
```bash
# Add custom task categories
cat >> .specify/templates/tasks-template.md <<'EOF'

## Custom Task Categories

### Security Tasks
Tasks related to authentication, authorization, encryption

### Performance Tasks
Tasks related to optimization, caching, scalability

### Compliance Tasks
Tasks related to LGPD, audit logging, data retention
EOF
```

#### Step 3: Commit Baseline (5 min)

```bash
cd "$TEST_PROJECT"
git init
git add .
git commit -m "Initial project with customizations

Customizations added:
- Security Review Checklist in spec-template
- Deployment Strategy in plan-template
- Custom task categories in tasks-template

Baseline for IMP-65 real-world test."
```

#### Step 4: Simulate Upstream Updates (15 min)

Create updated templates in upstream (scaffold-project):

**Update spec-template.md (v1.0.0 → v1.5.0)**:
```bash
cd /path/to/scaffold-project

# Update version in frontmatter
sed -i 's/template_version: "1.0.0"/template_version: "1.5.0"/' \
  .specify/templates/spec-template.md
sed -i 's/last_updated: ".*"/last_updated: "2026-04-21"/' \
  .specify/templates/spec-template.md

# Add new section (non-conflicting location)
sed -i '/## Overview/a \
\n## Performance Criteria\n\
\nDefine non-functional requirements:\n\
- **Response Time**: p95 < 200ms, p99 < 500ms\n\
- **Throughput**: Handle 1000 req/sec sustained\n\
- **Availability**: 99.9% uptime (SLO)\n\
- **Scalability**: Horizontal scaling to 10 pods\n\
- **Resource Usage**: < 512MB RAM per pod\n' \
  .specify/templates/spec-template.md
```

**Update plan-template.md (v1.0.0 → v1.2.0, CONFLICT)**:
```bash
# Update version
sed -i 's/template_version: "1.0.0"/template_version: "1.2.0"/' \
  .specify/templates/plan-template.md
sed -i 's/last_updated: ".*"/last_updated: "2026-04-21"/' \
  .specify/templates/plan-template.md

# Expand Implementation Plan section (same section as custom deployment)
sed -i '/## Implementation Plan/a \
\n**Standard Deployment Steps**:\n\
1. Run database migrations\n\
2. Deploy backend services\n\
3. Deploy frontend\n\
4. Verify health endpoints\n\
5. Enable monitoring alerts\n' \
  .specify/templates/plan-template.md

# This will conflict with custom "Deployment Strategy" section
```

**Update tasks-template.md (v1.0.0 → v2.0.0, BREAKING)**:
```bash
# Update version with breaking flag
sed -i 's/template_version: "1.0.0"/template_version: "2.0.0"/' \
  .specify/templates/tasks-template.md
sed -i 's/breaking_changes: false/breaking_changes: true/' \
  .specify/templates/tasks-template.md
sed -i 's/last_updated: ".*"/last_updated: "2026-04-21"/' \
  .specify/templates/tasks-template.md

# Add breaking change: remove "Dependencies" section, add "Prerequisites"
sed -i '/## Dependencies/,/^$/c\
## Prerequisites\n\
\nList what must be completed before starting tasks:\n\
- Infrastructure provisioned\n\
- Access credentials configured\n\
- Development environment setup\n' \
  .specify/templates/tasks-template.md
```

---

## Validation Procedures

### Pre-Execution Checklist

Before running test, verify:

- [ ] Test project exists at `$TEST_PROJECT`
- [ ] Customizations are committed to git (clean working tree)
- [ ] Upstream templates have version bumps
- [ ] Python environment is active (`uv venv`)
- [ ] All IMP-65 scripts are present
- [ ] Logging configured to capture details

### Execution Steps

#### Phase 1: Detection (5 min)

```bash
cd "$TEST_PROJECT"

# Step 1: Check for drift
python /path/to/scaffold-project/scripts/scaffold.py check-templates \
  --target-dir . \
  --json > /tmp/drift-check.json

# Verify output
cat /tmp/drift-check.json | jq .

# Expected:
# {
#   "drift_detected": true,
#   "total_drifts": 3,
#   "outdated_count": 3,
#   "templates": [
#     {"name": "spec-template.md", "local_version": "1.0.0", "upstream_version": "1.5.0", ...},
#     {"name": "plan-template.md", "local_version": "1.0.0", "upstream_version": "1.2.0", ...},
#     {"name": "tasks-template.md", "local_version": "1.0.0", "upstream_version": "2.0.0", "breaking_changes": true, ...}
#   ]
# }

# Verify exit code
echo $?  # → 1 (drift detected)
```

**Validation Checks**:
- ✅ Drift detected = true
- ✅ All 3 templates listed as outdated
- ✅ versions match expected (1.5.0, 1.2.0, 2.0.0)
- ✅ breaking_changes flag on tasks-template

#### Phase 2: Diff Review (10 min)

```bash
# Step 2a: Diff spec-template (clean merge expected)
python /path/to/scaffold-project/scripts/scaffold.py diff-template spec-template \
  --target-dir . \
  --format markdown \
  --output /tmp/diff-spec.md

# Review diff
cat /tmp/diff-spec.md

# Validate:
grep "Performance Criteria" /tmp/diff-spec.md  # → Found (new upstream section)
grep "Security Review Checklist" /tmp/diff-spec.md  # → Not in diff (local-only, preserved)

# Step 2b: Diff plan-template (conflict expected)
python /path/to/scaffold-project/scripts/scaffold.py diff-template plan-template \
  --target-dir . \
  --output /tmp/diff-plan.txt

# Validate:
grep "Deployment" /tmp/diff-plan.txt  # → Shows conflict area
grep "<<<<<<< LOCAL" /tmp/diff-plan.txt  # → May show conflict marker (depends on implementation)

# Step 2c: Diff tasks-template (breaking change)
python /path/to/scaffold-project/scripts/scaffold.py diff-template tasks-template \
  --target-dir . \
  --output /tmp/diff-tasks.txt

# Validate:
grep "breaking_changes: true" /tmp/diff-tasks.txt  # → Breaking flag shown
grep "Dependencies.*removed" /tmp/diff-tasks.txt  # → Shows removal
```

**Validation Checks**:
- ✅ spec diff shows only upstream additions (clean)
- ✅ plan diff shows overlapping changes (conflict)
- ✅ tasks diff shows breaking change warning

#### Phase 3: Merge Execution (45 min)

**3a: Clean Merge (spec-template)**

```bash
# Timestamp before
date > /tmp/merge-start-spec.txt

# Execute merge
python /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template \
  --target-dir . \
  --auto

# Timestamp after
date > /tmp/merge-end-spec.txt

# Verify result
grep "Performance Criteria" .specify/templates/spec-template.md  # → Found ✅
grep "Security Review Checklist" .specify/templates/spec-template.md  # → Found ✅
grep "template_version: \"1.5.0\"" .specify/templates/spec-template.md  # → Found ✅
ls .specify/templates/*.backup-* | grep spec  # → Backup exists ✅

# Verify state updated
grep "spec-template.md: \"1.5.0\"" .scaffold-state.yaml  # → Updated ✅
```

**Validation**:
- ✅ Merge completed without errors
- ✅ Both local AND upstream sections present
- ✅ Version bumped to 1.5.0
- ✅ Backup created
- ✅ Time < 2 minutes

**3b: Conflict Resolution (plan-template)**

```bash
# Attempt auto-merge (should fail)
python /path/to/scaffold-project/scripts/scaffold.py merge-template plan-template \
  --target-dir . \
  --auto

# Expected: exit code != 0, conflict detected

# Try interactive mode
python /path/to/scaffold-project/scripts/scaffold.py merge-template plan-template \
  --target-dir . \
  --interactive

# Follow prompts:
# → Shows conflict in "Implementation Plan" / "Deployment Strategy"
# → Options: [l] local, [u] upstream, [b] both, [e] edit
# → Choose [b] to keep both sections

# Verify result
grep "Blue-Green Deployment" .specify/templates/plan-template.md  # → Found ✅
grep "Standard Deployment Steps" .specify/templates/plan-template.md  # → Found ✅
grep "<<<<<<< LOCAL" .specify/templates/plan-template.md  # → NOT found ✅
```

**Validation**:
- ✅ Auto-merge correctly detected conflict
- ✅ Interactive mode provided clear options
- ✅ User choice ([b] both) applied correctly
- ✅ No conflict markers remain
- ✅ Both valuable sections preserved

**3c: Breaking Change (tasks-template)**

```bash
# Attempt auto-merge (should block)
python /path/to/scaffold-project/scripts/scaffold.py merge-template tasks-template \
  --target-dir . \
  --auto

# Expected: Warning about breaking change, requires explicit flag

# Apply with breaking change acknowledgment
python /path/to/scaffold-project/scripts/scaffold.py merge-template tasks-template \
  --target-dir . \
  --auto \
  --breaking-ok  # or similar flag

# Verify result
grep "## Prerequisites" .specify/templates/tasks-template.md  # → Found ✅
grep "## Dependencies" .specify/templates/tasks-template.md  # → NOT found (removed)
grep "Custom Task Categories" .specify/templates/tasks-template.md  # → Found ✅
```

**Validation**:
- ✅ Breaking change blocked auto-merge
- ✅ Explicit flag required
- ✅ Deprecated section removed
- ✅ Custom sections preserved
- ✅ Clear warning shown

#### Phase 4: Validation (30 min)

**4a: Project Still Works**

```bash
cd "$TEST_PROJECT"

# Run project tests
uv run pytest  # → All tests pass ✅

# Build project
make build  # → Builds successfully ✅

# Start dev server (if applicable)
make dev &
sleep 5
curl http://localhost:8000/health  # → Returns 200 ✅
kill %1
```

**4b: State Tracking Correct**

```bash
# Verify .scaffold-state.yaml updated
cat .scaffold-state.yaml | grep template_versions -A5

# Expected:
# template_versions:
#   spec-template.md: "1.5.0"
#   plan-template.md: "1.2.0"
#   tasks-template.md: "2.0.0"
```

**4c: No Regressions**

```bash
# Run full template drift check
python /path/to/scaffold-project/scripts/scaffold.py check-templates --target-dir .

# Expected: ✅ All templates up-to-date

# Verify no silent deletions
git diff HEAD .specify/templates/ | grep "^-" | grep -i "security\|oauth\|mfa"
# → Should be empty (no security content deleted)
```

**4d: Backups Restorable**

```bash
# List backups
ls -lh .specify/templates/*.backup-*

# Test restore of one backup
BACKUP=$(ls .specify/templates/spec-template.backup-* | head -1)
cp "$BACKUP" /tmp/restored-spec.md
diff /tmp/restored-spec.md .specify/templates/spec-template.md
# → Shows differences (expected, shows what changed)

# Verify backup content is valid markdown
cat "$BACKUP" | grep "^---"  # → Has frontmatter ✅
cat "$BACKUP" | grep "Security Review Checklist"  # → Has customizations ✅
```

#### Phase 5: Edge Cases (20 min)

**5a: Dry-Run Works**

```bash
# Revert a template to test dry-run
git checkout HEAD -- .specify/templates/spec-template.md

# Dry-run merge
python /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template \
  --target-dir . \
  --auto \
  --dry-run > /tmp/dry-run.txt

# Verify no changes
git status  # → No changes ✅

# Verify preview shown
cat /tmp/dry-run.txt | grep "Would apply"  # → Preview shown ✅
```

**5b: Idempotency**

```bash
# Apply merge
python /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template \
  --target-dir . \
  --auto

# Save result
cp .specify/templates/spec-template.md /tmp/first-merge.md

# Re-apply same merge
python /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template \
  --target-dir . \
  --auto

# Compare results
diff /tmp/first-merge.md .specify/templates/spec-template.md
# → No differences (idempotent) ✅
```

**5c: Error Recovery**

```bash
# Introduce corrupt template (missing frontmatter)
sed -i '1,5d' .specify/templates/spec-template.md  # Remove frontmatter

# Attempt merge
python /path/to/scaffold-project/scripts/scaffold.py merge-template spec-template \
  --target-dir . \
  --auto 2> /tmp/error.txt

# Verify graceful error
cat /tmp/error.txt | grep -i "error\|warning"  # → Clear error message ✅
cat /tmp/error.txt | grep -i "frontmatter"  # → Mentions missing metadata ✅

# Restore from backup
git checkout HEAD -- .specify/templates/spec-template.md
```

---

## Expected vs Actual Behavior

### Behavior Matrix

| Scenario | Expected | Validation | Pass/Fail |
|----------|----------|------------|-----------|
| Clean merge | Both sections present | grep both sections | ⬜ |
| Conflict detection | Auto-merge fails, interactive works | Exit codes, prompts | ⬜ |
| Breaking change | Blocked without flag | Error message | ⬜ |
| Version tracking | .scaffold-state.yaml updated | grep versions | ⬜ |
| Backups | Created with timestamp | ls backups | ⬜ |
| Dry-run | No files modified | git status clean | ⬜ |
| Idempotency | Same result on re-run | diff results | ⬜ |
| Error handling | Clear messages | grep errors | ⬜ |

### Metrics to Capture

| Metric | Target | Actual | Notes |
|--------|--------|--------|-------|
| Total time | < 5 min | _____ min | From start to working project |
| Manual steps | < 5 | _____ | Count decision points |
| Conflicts | Clearly explained | ⬜ Yes / ⬜ No | User understood? |
| Time to resolve conflict | < 2 min | _____ min | Interactive resolution |
| Documentation accuracy | 100% | _____ % | Matched real experience? |
| Error clarity | > 80% | _____ % | Errors were actionable? |

---

## Rollback Procedures

### If Test Fails Catastrophically

1. **Restore from Git**:
   ```bash
   cd "$TEST_PROJECT"
   git reset --hard HEAD
   git clean -fd
   ```

2. **Restore from Backups**:
   ```bash
   cd "$TEST_PROJECT"
   for backup in .specify/templates/*.backup-*; do
     original="${backup%.backup-*}.md"
     cp "$backup" "$original"
   done
   ```

3. **Re-create Test Project**:
   ```bash
   rm -rf "$TEST_PROJECT"
   # Re-run setup steps
   ```

### If Individual Template Merge Fails

```bash
# Restore single template from backup
BACKUP=$(ls .specify/templates/spec-template.backup-* | tail -1)
cp "$BACKUP" .specify/templates/spec-template.md

# Or restore from git
git checkout HEAD -- .specify/templates/spec-template.md

# Verify restoration
git diff .specify/templates/spec-template.md  # → No changes
```

---

## Success Criteria

### Must-Have (Blocking)

- ✅ All customizations preserved after merge
- ✅ No silent overwrites or deletions
- ✅ Conflicts detected and resolvable
- ✅ Version tracking accurate
- ✅ Backups created and restorable
- ✅ Project builds and tests pass after update

### Should-Have (Strong)

- ✅ Total time < 10 minutes
- ✅ Clear error messages (80%+ actionable)
- ✅ Documentation matches reality
- ✅ Dry-run works correctly
- ✅ Idempotent operations

### Nice-to-Have (Desired)

- ✅ Total time < 5 minutes
- ✅ Interactive mode is intuitive
- ✅ Progress indicators shown
- ✅ Automated changelog generated

### Failure Criteria (Test Failed)

- ❌ Any customization lost
- ❌ Silent overwrite of changes
- ❌ Incorrect version tracking
- ❌ No backup created
- ❌ Project broken after update
- ❌ Conflicts unresolvable
- ❌ Non-deterministic behavior

---

## Post-Test Activities

### Immediate

1. **Document Findings** (30 min)
   - Create `IMP-65_REAL_WORLD_TEST_REPORT.md`
   - List all edge cases discovered
   - Note UX issues encountered
   - Measure captured metrics

2. **Create Regression Tests** (2h)
   - One test per edge case found
   - Add to `tests/test_template_real_world.py`
   - Ensure 100% pass rate

3. **Update Documentation** (1h)
   - Fix inaccuracies in TEMPLATE_DRIFT_DETECTION.md
   - Add troubleshooting section
   - Add real-world examples from test

### Follow-Up

4. **File Issues for Bugs** (1h)
   - P0 bugs: Fix immediately
   - P1 bugs: Fix before release
   - P2 improvements: Backlog

5. **Implement Quick Wins** (varies)
   - Improve error messages
   - Add missing progress indicators
   - Fix documentation gaps

---

## Appendix

### Test Artifacts Locations

```
/tmp/imp-65-test-project/           # Test project root
├── .specify/templates/             # Templates with customizations
├── .scaffold-state.yaml            # State tracking
└── .specify/templates/*.backup-*   # Backups

/tmp/
├── drift-check.json                # Drift detection results
├── diff-spec.md                    # Diff output (markdown)
├── diff-plan.txt                   # Diff output (text)
├── diff-tasks.txt                  # Diff output (text)
├── dry-run.txt                     # Dry-run preview
├── merge-start-spec.txt            # Timing
├── merge-end-spec.txt              # Timing
└── error.txt                       # Error messages

docs/SESSIONS/2026-04-21/
├── IMP-65_REAL_WORLD_TEST_REPORT.md   # Test report (to create)
└── IMP-65_TEST_STRATEGY.md            # This document
```

### Commands Quick Reference

```bash
# Detection
scaffold.py check-templates --target-dir . --json

# Diff
scaffold.py diff-template <name> --target-dir . --format markdown

# Merge (auto)
scaffold.py merge-template <name> --target-dir . --auto

# Merge (interactive)
scaffold.py merge-template <name> --target-dir . --interactive

# Merge (breaking)
scaffold.py merge-template <name> --target-dir . --auto --breaking-ok

# Dry-run
scaffold.py merge-template <name> --target-dir . --dry-run

# Rollback
cp .specify/templates/<name>.backup-* .specify/templates/<name>.md
```

---

**Status**: ✅ Ready to Execute

**Next Step**: Begin test execution following Phase 1 (Detection).
