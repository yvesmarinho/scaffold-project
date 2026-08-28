# Modular Templates System

**Version**: 1.0.0
**Part of**: IMP-65 Phase 4 - Template Synchronization System
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Block System](#block-system)
5. [Patch System](#patch-system)
6. [Migration Guide](#migration-guide)
7. [CLI Commands](#cli-commands)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Modular Templates System transforms how we manage template evolution and customization in the Enterprise Scaffold Project Template.

### Problems Solved

**Before** (Monolithic Templates):
- 🔴 Large templates hard to maintain
- 🔴 Updates risk overwriting customizations
- 🔴 No clear separation between standard and custom content
- 🔴 Difficult to share common sections across templates
- 🔴 Merge conflicts in large files

**After** (Modular System):
- ✅ Small, focused, reusable blocks
- ✅ Safe updates via composition
- ✅ Patches clearly separate customizations
- ✅ Blocks shared across templates
- ✅ Conflicts scoped to specific blocks

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Template                        │
│  (composed.md or template.md with @include directives)  │
└───────────────┬─────────────────────────────────────────┘
                │
                ├─► Composition Engine
                │   • Resolves @include directives
                │   • Assembles blocks in order
                │   • Validates versions
                │
                ├─► Blocks (.specify/blocks/)
                │   • Reusable template sections
                │   • Versioned independently
                │   • Shared across templates
                │
                └─► Patches (.specify/patches/)
                    • Project-specific customizations
                    • Anchor-based insertion
                    • Non-destructive modifications
```

---

## Quick Start

### Install (Already Included)

The modular templates system is built into the Enterprise Scaffold Project Template. No installation needed!

### 5-Minute Tutorial

#### 1. Create Your First Block

```bash
mkdir -p .specify/blocks
cat > .specify/blocks/user-scenarios-v1.0.md <<'EOF'
---
block_name: user-scenarios
version: 1.0.0
description: Standard user scenarios section
tags: [spec, common]
---

## User Scenarios

### As a user, I want to...

Describe user scenarios here.
EOF
```

#### 2. Create a Template Using Blocks

```bash
cat > templates/my-spec.md <<'EOF'
---
template_type: spec
version: 1.0.0
---

# Objetivo

Business objective goes here.

@include blocks/user-scenarios-v1.0.md

## Success Criteria

Success criteria here.
EOF
```

#### 3. Compose the Template

```bash
./scripts/bin/compose-template templates/my-spec.md .specify/ -o output.md --verbose
```

#### 4. Add a Custom Section (Patch)

```bash
cat > .specify/patches/my-spec/001-add-security.patch <<'EOF'
---
patch_name: add-security-review
version: 1.0.0
target_template: my-spec
target_block: user-scenarios
created: 2026-04-15
description: Add security review checklist
author: security-team@example.com
---

@@ AFTER: ## User Scenarios

## Security Review

- [ ] Authentication requirements
- [ ] Authorization model
- [ ] Data encryption needs

@@ END
EOF
```

#### 5. Apply Patches

```bash
./scripts/bin/apply-patches output.md .specify/patches/ -t my-spec -o final.md --verbose
```

**Done!** You now have a composed template with custom sections.

---

## Core Concepts

### 1. Blocks

**Definition**: Self-contained, reusable template sections with versioned metadata.

**Key Properties**:
- Independent versioning (semantic versioning)
- Reusable across multiple templates
- Immutable once published
- Clear dependencies and compatibility

**File Structure**:
```
.specify/blocks/
├── frontmatter-spec-v1.0.md          # Spec template frontmatter
├── user-scenarios-v1.0.md            # User scenarios section
├── user-scenarios-v2.0.md            # Updated version
├── success-criteria-v1.0.md          # Success criteria
└── architecture-overview-v1.0.md    # Architecture section
```

### 2. Templates

**Definition**: Composition files that reference blocks via `@include` directives.

**Two Modes**:

**Mode A: Template with Includes** (Recommended)
```markdown
---
template_type: spec
version: 1.0.0
---

# Objetivo

@include blocks/user-scenarios-v1.0.md
@include blocks/success-criteria-v1.0.md
```

**Mode B: Standalone Composition** (Advanced)
```bash
# Generate composed template on-demand
compose-template spec-template.md .specify/ -o spec.md
```

### 3. Patches

**Definition**: Project-specific customizations applied after template composition.

**Key Properties**:
- Non-destructive (original blocks unchanged)
- Anchor-based positioning
- Template-specific (in `.specify/patches/<template-name>/`)
- Versioned and documented

**File Structure**:
```
.specify/patches/
├── spec-template/
│   ├── 001-add-security.patch
│   └── 002-add-monitoring.patch
└── plan-template/
    └── 001-custom-deployment.patch
```

---

## Block System

### Block File Format

```markdown
---
block_name: user-scenarios          # Required: unique identifier
version: 1.0.0                      # Required: semantic version
description: User scenarios section # Optional: human-readable description
tags: [spec, common]                # Optional: categorization
dependencies: []                     # Optional: required blocks
compatibility:                       # Optional: compatible templates
  - spec-template
  - plan-template
---

## User Scenarios

Content of the block goes here.
Multiple sections allowed.
```

### Block Naming Convention

**Pattern**: `{block-name}-v{version}.md`

**Examples**:
- `user-scenarios-v1.0.md`
- `user-scenarios-v2.0.md`
- `architecture-overview-v1.0.md`

### Block Versioning

Follow **Semantic Versioning**:

- **MAJOR** (v2.0.0): Breaking changes, incompatible with v1.x
- **MINOR** (v1.1.0): New features, backward compatible
- **PATCH** (v1.0.1): Bug fixes, backward compatible

**Version Upgrade Example**:
```
user-scenarios-v1.0.md  →  Added basic scenarios
user-scenarios-v1.1.md  →  Added API integration scenarios (compatible)
user-scenarios-v2.0.md  →  Restructured format (breaking change)
```

### Creating Blocks

#### CLI Method

```bash
./scripts/bin/validate-block .specify/blocks/my-block-v1.0.md --verbose
```

#### Manual Method

1. Create file: `.specify/blocks/my-block-v1.0.md`
2. Add frontmatter with required fields
3. Add content
4. Validate: `validate-block .specify/blocks/my-block-v1.0.md`

### Block Library Organization

**Recommended Structure**:

```
.specify/blocks/
├── common/                 # Shared across all template types
│   ├── frontmatter-v1.0.md
│   └── notes-v1.0.md
├── spec/                   # Spec-specific blocks
│   ├── user-scenarios-v1.0.md
│   ├── success-criteria-v1.0.md
│   └── out-of-scope-v1.0.md
├── plan/                   # Plan-specific blocks
│   ├── architecture-v1.0.md
│   ├── data-model-v1.0.md
│   └── testing-strategy-v1.0.md
└── tasks/                  # Tasks-specific blocks
    ├── layer-1-business-v1.0.md
    └── layer-2-product-v1.0.md
```

---

## Patch System

### Patch File Format

```markdown
---
patch_name: add-security-review     # Required: unique identifier
version: 1.0.0                      # Required: semantic version
target_template: spec-template      # Required: which template
target_block: user-scenarios        # Optional: which block (if specific)
created: 2026-04-15                 # Required: creation date
description: Add security checklist # Required: what this patch does
author: security-team@example.com   # Optional: who created it
tags: [security, compliance]        # Optional: categorization
---

@@ AFTER: ## User Scenarios

## Security Review

- [ ] Authentication requirements
- [ ] Authorization model

@@ END
```

### Patch Operations

#### 1. AFTER (Insert After Anchor)

```markdown
@@ AFTER: ## User Scenarios

## My Custom Section

Custom content here.

@@ END
```

**Result**: Content inserted immediately after the anchor.

#### 2. BEFORE (Insert Before Anchor)

```markdown
@@ BEFORE: ## Success Criteria

## My Preparatory Section

Content before success criteria.

@@ END
```

**Result**: Content inserted immediately before the anchor.

#### 3. REPLACE (Replace Section)

```markdown
@@ REPLACE: ## User Scenarios

## Enhanced User Scenarios

New comprehensive scenarios.

@@ END
```

**Result**: Entire section from anchor to next heading replaced.

#### 4. DELETE (Remove Section)

```markdown
@@ DELETE: ## Out of Scope

@@ END
```

**Result**: Section removed entirely.

#### 5. PREPEND (Insert at Start)

```markdown
@@ PREPEND: START

# Executive Summary

High-level overview at the top.

@@ END
```

**Result**: Content added at the beginning of the document.

#### 6. APPEND (Insert at End)

```markdown
@@ APPEND: END

## Appendix

Additional resources.

@@ END
```

**Result**: Content added at the end of the document.

### Patch Naming Convention

**Pattern**: `{number}-{descriptive-name}.patch`

**Examples**:
- `001-add-security.patch`
- `002-custom-deployment.patch`
- `003-remove-unused-sections.patch`

**Numbering**: Use sequential 3-digit numbers (001, 002, ...). Patches are applied in filename order.

### Creating Patches

#### CLI Method

```bash
./scripts/bin/validate-patch .specify/patches/spec-template/001-my-patch.patch --verbose
```

#### Manual Method

1. Create directory: `.specify/patches/spec-template/`
2. Create file: `001-my-patch.patch`
3. Add frontmatter with required fields
4. Add one or more `@@ OPERATION` blocks
5. Validate: `validate-patch .specify/patches/spec-template/001-my-patch.patch`

### Patch Application Order

1. **By Template**: Only patches matching `target_template` are applied
2. **By Filename**: Patches applied in ascending filename order (001, 002, ...)
3. **Within Patch**: Operations applied top-to-bottom as written

**Example**:
```
001-add-security.patch       # Applied first
002-add-monitoring.patch     # Applied second
003-remove-unused.patch      # Applied third
```

---

## Migration Guide

### Migrating from Monolithic Templates

#### Step 1: Analyze Current Template

```bash
# Dry run to see what would be migrated
./scripts/bin/migrate-template templates/spec-template.md --dry-run --verbose
```

**Output**:
- Detected custom sections
- Proposed patches
- Warnings and recommendations

#### Step 2: Perform Migration

```bash
# Actual migration with guide generation
./scripts/bin/migrate-template templates/spec-template.md --guide migration-guide.md
```

**Creates**:
- Backup: `.specify/migration-backups/spec-template_YYYYMMDD_HHMMSS.md`
- Patches: `.specify/patches/spec-template/*.patch`
- Guide: `migration-guide.md`

#### Step 3: Review Generated Patches

```bash
# List generated patches
./scripts/bin/list-patches .specify/patches/ -t spec-template --verbose

# Validate each patch
./scripts/bin/validate-patch .specify/patches/spec-template/001-custom-section.patch --verbose
```

#### Step 4: Extract Standard Blocks

**Manual Step**: Identify standard sections to extract into reusable blocks.

```bash
# Create block directory
mkdir -p .specify/blocks

# Extract user scenarios section
cat > .specify/blocks/user-scenarios-v1.0.md <<'EOF'
---
block_name: user-scenarios
version: 1.0.0
description: Standard user scenarios template section
---

## User Scenarios

### As a user, I want to...

Describe user scenarios here.
EOF

# Validate
./scripts/bin/validate-block .specify/blocks/user-scenarios-v1.0.md
```

#### Step 5: Create New Composed Template

```bash
cat > templates/spec-template-modular.md <<'EOF'
---
template_type: spec
version: 2.0.0
---

# Objetivo

Business objective.

@include blocks/user-scenarios-v1.0.md
@include blocks/success-criteria-v1.0.md

## Out of Scope

EOF
```

#### Step 6: Test Composition

```bash
# Compose template
./scripts/bin/compose-template templates/spec-template-modular.md .specify/ -o test-output.md --verbose

# Apply patches
./scripts/bin/apply-patches test-output.md .specify/patches/ -t spec-template -o final-output.md --verbose

# Compare with original
diff templates/spec-template.md final-output.md
```

#### Step 7: Replace Original

```bash
# Once verified, replace original
mv templates/spec-template.md templates/spec-template-old.md
mv templates/spec-template-modular.md templates/spec-template.md

# Update any references
grep -r "spec-template-modular" . --exclude-dir=.git
```

### Batch Migration

```bash
# Migrate all templates in directory
./scripts/bin/migrate-template --batch templates/ --verbose
```

### Migration Checklist

- [ ] Backup originals
- [ ] Run dry-run migration
- [ ] Review generated patches
- [ ] Extract reusable blocks
- [ ] Create composed template
- [ ] Test composition
- [ ] Apply patches
- [ ] Verify output matches original + customizations
- [ ] Update template references
- [ ] Update documentation
- [ ] Test scaffold/spec/plan workflows
- [ ] Commit changes

---

## CLI Commands

### compose-template

**Purpose**: Assemble template from blocks.

```bash
compose-template <template> <blocks-dir> [options]

Options:
  -o, --output PATH    Write composed template to file (default: stdout)
  -v, --verbose        Show detailed composition information

Examples:
  # Compose to stdout
  compose-template templates/spec.md .specify/

  # Compose to file with details
  compose-template templates/spec.md .specify/ -o output.md --verbose
```

### apply-patches

**Purpose**: Apply patches to composed template.

```bash
apply-patches <template> <patches-dir> [options]

Options:
  -t, --template-name NAME  Only apply patches for specific template
  -o, --output PATH         Write patched template to file (default: stdout)
  -v, --verbose             Show patch operations and statistics

Examples:
  # Apply all patches
  apply-patches output.md .specify/patches/ -o final.md

  # Apply only spec-template patches
  apply-patches output.md .specify/patches/ -t spec-template -o final.md -v
```

### validate-block

**Purpose**: Validate block file format and metadata.

```bash
validate-block <block-path> [options]

Options:
  -v, --verbose        Show block metadata and statistics

Examples:
  # Validate block
  validate-block .specify/blocks/user-scenarios-v1.0.md

  # Validate with details
  validate-block .specify/blocks/user-scenarios-v1.0.md --verbose
```

### validate-patch

**Purpose**: Validate patch file format and operations.

```bash
validate-patch <patch-path> [options]

Options:
  -v, --verbose        Show patch metadata and operations

Examples:
  # Validate patch
  validate-patch .specify/patches/spec/001-custom.patch

  # Validate with details
  validate-patch .specify/patches/spec/001-custom.patch --verbose
```

### list-patches

**Purpose**: List all patches for template(s).

```bash
list-patches <patches-dir> [options]

Options:
  -t, --template-name NAME  Only show patches for specific template
  -v, --verbose             Show patch operations and details

Examples:
  # List all patches
  list-patches .specify/patches/

  # List spec-template patches with details
  list-patches .specify/patches/ -t spec-template --verbose
```

### migrate-template

**Purpose**: Migrate monolithic template to modular system.

```bash
migrate-template <template-path> [options]

Options:
  --dry-run             Show what would happen without creating files
  --name NAME           Specify template name (default: filename)
  --guide PATH          Write migration guide to file
  --list                List all templates in project
  --batch DIR           Migrate all templates in directory
  -v, --verbose         Show detailed migration information

Examples:
  # Dry run
  migrate-template templates/spec.md --dry-run

  # Migrate with guide
  migrate-template templates/spec.md --guide migration-guide.md

  # Batch migrate
  migrate-template --batch templates/ --verbose
```

---

## Best Practices

### Block Design

✅ **DO**:
- Keep blocks focused on single sections
- Use semantic versioning consistently
- Document dependencies clearly
- Include descriptive metadata
- Make blocks self-contained
- Use tags for categorization

❌ **DON'T**:
- Create monolithic blocks (defeats purpose)
- Change published block content (create new version instead)
- Use non-semantic version numbers
- Omit required metadata fields
- Create circular dependencies

### Template Composition

✅ **DO**:
- Use @include for reusable sections
- Order includes logically (top to bottom)
- Pin block versions explicitly
- Document template structure
- Test composition regularly

❌ **DON'T**:
- Mix monolithic and modular styles
- Use relative paths outside .specify/
- Include deprecated blocks
- Nest @include directives
- Assume block order doesn't matter

### Patch Management

✅ **DO**:
- Use clear, descriptive patch names
- Number patches sequentially
- Document patch purpose in frontmatter
- Test patches in isolation
- Keep patches small and focused
- Review patch application order

❌ **DON'T**:
- Create overlapping patches (conflicts)
- Modify patches after deployment
- Use fragile anchors (they may change)
- Patch blocks directly (create new version)
- Skip patch validation

### Version Control

✅ **DO**:
- Commit blocks separately from templates
- Tag block versions in git
- Include .specify/ in repository
- Document breaking changes
- Maintain migration backups temporarily

❌ **DON'T**:
- Commit migration backups to git
- Delete old block versions prematurely
- Modify published blocks
- Force-push block changes

---

## Troubleshooting

### Common Issues

#### Issue: "Block not found"

**Symptom**: `@include blocks/my-block-v1.0.md` fails with "not found"

**Solution**:
```bash
# Verify block exists
ls -la .specify/blocks/my-block-v1.0.md

# Check path in @include (must be relative to blocks-dir)
# Correct: @include blocks/my-block-v1.0.md
# Wrong: @include .specify/blocks/my-block-v1.0.md
```

#### Issue: "Patch anchor not found"

**Symptom**: Patch fails with "anchor '## Section' not found"

**Solution**:
```bash
# Verify anchor exists in composed template
grep "## Section" output.md

# Check for typos or whitespace issues
# Anchors are case-sensitive and whitespace-sensitive
```

#### Issue: "Patch creates duplicate section"

**Symptom**: Applying patch results in duplicate headers

**Solution**:
```bash
# Use REPLACE instead of AFTER if section already exists
@@ REPLACE: ## Existing Section
## Updated Section
Content
@@ END
```

#### Issue: "Circular dependency detected"

**Symptom**: Template composition fails with dependency error

**Solution**:
```bash
# Review block dependencies
validate-block .specify/blocks/block-a-v1.0.md --verbose
validate-block .specify/blocks/block-b-v1.0.md --verbose

# Remove circular references from frontmatter
```

#### Issue: "Version conflict"

**Symptom**: Patches target block version not in composed template

**Solution**:
```bash
# Check block version in template
grep "@include" templates/my-template.md

# Update patch to match or use wildcard
# target_block: user-scenarios (any version)
# OR
# target_block: user-scenarios-v1.0 (specific version)
```

### Getting Help

1. **Validate First**: Run validate-block or validate-patch
2. **Use Verbose Mode**: Add --verbose to see detailed information
3. **Check Logs**: Review terminal output for error messages
4. **Test Incrementally**: Compose first, then apply patches one at a time
5. **Review Documentation**: This guide and IMP-65_PHASE4_DESIGN.md

---

## Advanced Topics

### Dynamic Block Selection

**Use Case**: Different environments or profiles need different blocks.

```bash
# Development environment
compose-template templates/spec.md .specify/ \
  --blocks "user-scenarios-v1.0.md,dev-testing-v1.0.md"

# Production environment
compose-template templates/spec.md .specify/ \
  --blocks "user-scenarios-v1.0.md,prod-deployment-v1.0.md"
```

### Conditional Patches

**Use Case**: Apply patches based on project type or profile.

```markdown
---
patch_name: security-review
conditions:
  profile: [appsec-engineer, soc2-baseline]
  environment: [production, staging]
---

@@ AFTER: ## User Scenarios
## Security Review
...
@@ END
```

### Block Inheritance

**Use Case**: Extend base block with additional content.

```markdown
---
block_name: user-scenarios-extended
version: 1.0.0
extends: user-scenarios-v1.0
---

@include blocks/user-scenarios-v1.0.md

## Additional Scenarios

Extended scenarios here.
```

### Template Variants

**Use Case**: Generate multiple variants from same blocks.

```bash
# Minimal variant
compose-template templates/spec-minimal.md .specify/

# Full variant
compose-template templates/spec-full.md .specify/

# Custom variant
compose-template templates/spec-custom.md .specify/
```

---

## Resources

- **Design Document**: [IMP-65_PHASE4_DESIGN.md](IMP-65_PHASE4_DESIGN.md)
- **Implementation Plan**: IMP-65 Phase 4 (TODO.md)
- **Source Code**: `scripts/lib/template_blocks.py`, `scripts/lib/template_patches.py`, `scripts/lib/template_migration.py`
- **Tests**: `tests/test_template_blocks.py`, `tests/test_template_patches.py`, `tests/test_template_migration.py`

---

## Feedback and Contributions

This system is part of the Enterprise Scaffold Project Template.

**Questions?** See [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)
**Issues?** Check [docs/ISSUE_MANAGEMENT_GUIDE.md](ISSUE_MANAGEMENT_GUIDE.md)
**Contributing?** See [CONVENTIONS.md](CONVENTIONS.md)

---

**Version History**:
- **1.0.0** (2026-04-15): Initial release with Phase 4.1-4.4 complete
