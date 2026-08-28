# IMP-65 Phase 4: Modular Templates Architecture

**Feature ID**: IMP-65-PHASE4
**Created**: 2026-04-15
**Status**: Design / Planning
**Estimated Effort**: 120h (distributed across 4 sub-phases)

---

## Executive Summary

Phase 4 transforms SpecKit templates from monolithic files into a modular block-based system. This enables:
- **Granular versioning**: Update individual sections without touching entire templates
- **Cleaner customizations**: Patches stored separately, not mixed with standard content
- **Better conflict resolution**: Merge happens at block level, not file level
- **Reusability**: Share common blocks across multiple templates

---

## Problem Statement

### Current State (Phases 1-3.1)
- ✅ Templates have version metadata
- ✅ Can detect drift with `check-templates`
- ✅ Can diff templates with `diff-template`
- ✅ Can merge templates with three-way merge

### Remaining Pain Points
1. **Monolithic templates**: A 300-line template has 10 sections; upstream updates 1 section → entire file must be merged
2. **Customization tracking**: User adds custom section → indistinguishable from standard content in diff
3. **Granularity**: Can't say "update just the User Scenarios section, keep everything else"
4. **Reuse**: Multiple templates share similar sections (e.g., frontmatter, success criteria) but duplicate content

---

## Solution: Modular Block System

### Core Concepts

#### 1. **Blocks**: Reusable Template Fragments

Self-contained markdown sections with independent versioning.

**Example**: `user-scenarios-v2.0.md`
```yaml
---
block_type: "template_fragment"
block_name: "user-scenarios"
block_version: "2.0.0"
last_updated: "2026-04-15"
compatible_with:
  - "spec-template >= 1.0.0"
dependencies: []
breaking_changes: false
changelog:
  - version: "2.0.0"
    date: "2026-04-15"
    changes:
      - "Added priority levels (P1/P2/P3)"
      - "Added independent test descriptions"
  - version: "1.0.0"
    date: "2026-04-01"
    changes:
      - "Initial block creation"
---

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED...
-->

### User Story 1 - [Brief Title] (Priority: P1)
...
```

**Key Properties**:
- Independent semantic versioning
- Changelog tracking
- Compatibility declarations
- Can be used in multiple parent templates

#### 2. **Templates**: Compositions of Blocks

Templates become lightweight "orchestrators" that include blocks.

**Example**: `spec-template.md` (new structure)
```yaml
---
template_version: "2.0.0"
template_type: "composition"
last_updated: "2026-04-15"
blocks:
  - name: "frontmatter-spec"
    version: "^1.0.0"
    source: "blocks/frontmatter-spec-v1.0.md"
  - name: "user-scenarios"
    version: "^2.0.0"
    source: "blocks/user-scenarios-v2.0.md"
  - name: "requirements"
    version: "^1.5.0"
    source: "blocks/requirements-v1.5.md"
  - name: "success-criteria"
    version: "^1.0.0"
    source: "blocks/success-criteria-v1.0.md"
---

<!-- @include blocks/frontmatter-spec-v1.0.md -->

<!-- @include blocks/user-scenarios-v2.0.md -->

<!-- @include blocks/requirements-v1.5.md -->

<!-- @include blocks/success-criteria-v1.0.md -->
```

**Composition Engine**:
- Resolves `@include` directives
- Validates block versions against compatibility
- Assembles full template from blocks
- Caches assembled templates for performance

#### 3. **Patches**: Isolated Customizations

User customizations stored as separate patch files (like git patches).

**Example**: `.specify/templates/patches/spec-template/001-add-security-review.patch`
```yaml
---
patch_name: "add-security-review"
patch_version: "1.0.0"
target_template: "spec-template"
target_block: "user-scenarios"
target_version: "^2.0.0"
created: "2026-04-15"
description: "Add security review checklist to user scenarios"
author: "user@example.com"
---

@@ After: User Scenarios & Testing *(mandatory)* @@
+
+ ### Security Review Checklist
+
+ All scenarios must pass security review before implementation:
+ - [ ] Input validation for all user inputs
+ - [ ] Authentication/authorization checks
+ - [ ] Data encryption (at rest and in transit)
+ - [ ] OWASP Top 10 mitigation
+ - [ ] Security logging for audit trail
+
@@ END @@
```

**Patch Application**:
- Applied on top of composed template
- Stored separately in `.specify/templates/patches/`
- Survives upstream block updates
- Can be exported/shared across projects
- Versioned independently from blocks

---

## File Structure

```
.specify/
├── templates/
│   ├── blocks/                          # Upstream reusable blocks
│   │   ├── frontmatter-spec-v1.0.md
│   │   ├── user-scenarios-v2.0.md
│   │   ├── requirements-v1.5.md
│   │   ├── success-criteria-v1.0.md
│   │   ├── frontmatter-plan-v1.0.md
│   │   ├── architecture-decisions-v1.0.md
│   │   ├── technical-context-v1.0.md
│   │   └── complexity-tracking-v1.0.md
│   │
│   ├── patches/                         # User customizations
│   │   ├── spec-template/
│   │   │   ├── 001-add-security-review.patch
│   │   │   └── 002-custom-metrics.patch
│   │   ├── plan-template/
│   │   │   └── 001-add-cost-estimation.patch
│   │   └── README.md                    # Patch management guide
│   │
│   ├── spec-template.md                 # Composition orchestrator
│   ├── plan-template.md                 # Composition orchestrator
│   ├── tasks-template.md                # Composition orchestrator
│   ├── objetivo-template.yaml           # (remains monolithic - YAML)
│   └── README.md                        # Template system documentation
│
└── .scaffold-state.yaml                 # Extended with block_versions, patches
```

---

## Technical Design

### 1. Block Metadata Schema

JSON Schema: `.specify/schemas/block-metadata-schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["block_type", "block_name", "block_version", "last_updated"],
  "properties": {
    "block_type": {
      "type": "string",
      "enum": ["template_fragment"]
    },
    "block_name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9-]*$"
    },
    "block_version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    },
    "last_updated": {
      "type": "string",
      "format": "date"
    },
    "compatible_with": {
      "type": "array",
      "items": {"type": "string"}
    },
    "dependencies": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["block", "version"],
        "properties": {
          "block": {"type": "string"},
          "version": {"type": "string"}
        }
      }
    },
    "breaking_changes": {
      "type": "boolean"
    },
    "changelog": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["version", "date", "changes"],
        "properties": {
          "version": {"type": "string"},
          "date": {"type": "string", "format": "date"},
          "changes": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    }
  }
}
```

### 2. Composition Syntax

**Include Directive**: `<!-- @include <path> -->`

- **Explicit path**: `<!-- @include blocks/user-scenarios-v2.0.md -->`
- **Version range** (future): `<!-- @include blocks/user-scenarios@^2.0.0 -->`

**Processing**:
1. Parse template file
2. Extract all `@include` directives
3. Resolve block paths (relative to `.specify/templates/`)
4. Validate block versions against template requirements
5. Load block content
6. Replace `@include` with block content
7. Return assembled template

### 3. Patch Application Engine

**Patch Format** (simplified unified diff):

```yaml
---
# Patch metadata (YAML frontmatter)
---

@@ Anchor: <search text> @@
+ <lines to add>
- <lines to remove (optional)>
@@ END @@

@@ Anchor: <another section> @@
+ <more additions>
@@ END @@
```

**Application Algorithm**:
1. Load composed template (blocks assembled)
2. Load all patches for this template (from `.specify/templates/patches/<template-name>/`)
3. Sort patches by filename (001, 002, 003, ...)
4. For each patch:
   a. Find anchor text in template
   b. Apply additions/removals
   c. Validate result (no broken markdown)
5. Return patched template

**Conflict Detection**:
- Anchor not found → CONFLICT
- Multiple anchor matches → CONFLICT
- Overlapping patches → CONFLICT
- Invalid markdown after patch → CONFLICT

### 4. State Tracking Extensions

**`.scaffold-state.yaml` additions**:

```yaml
# Existing fields
project_name: "my-project"
template_versions:
  spec-template.md: "2.0.0"
  plan-template.md: "2.0.0"

# NEW: Block versions used in this project
block_versions:
  user-scenarios: "2.0.0"
  requirements: "1.5.0"
  success-criteria: "1.0.0"
  frontmatter-spec: "1.0.0"

# NEW: Block base content for three-way merge
block_bases:
  user-scenarios-2.0.0: |
    ## User Scenarios & Testing *(mandatory)*
    ...

# NEW: Active patches
patches:
  spec-template:
    - name: "001-add-security-review"
      version: "1.0.0"
      created: "2026-04-15"
      active: true
  plan-template:
    - name: "001-add-cost-estimation"
      version: "1.0.0"
      created: "2026-04-15"
      active: true
```

---

## Implementation Roadmap

### Phase 4.1: Block Foundation (20h, 2-3 days)

**Goal**: Extract blocks, implement composition engine

**Tasks**:
1. Create JSON schema for block metadata
2. Extract common sections from existing templates:
   - `frontmatter-spec-v1.0.md`
   - `user-scenarios-v2.0.md`
   - `requirements-v1.5.md`
   - `success-criteria-v1.0.md`
   - `frontmatter-plan-v1.0.md`
   - `architecture-decisions-v1.0.md`
3. Create `scripts/lib/template_blocks.py`:
   - `parse_block_metadata()`
   - `validate_block()`
   - `compose_template()` — assemble from blocks
4. Update templates to use `@include` directives
5. Tests: 20+ tests for composition, validation, errors

**Deliverables**:
- `.specify/templates/blocks/` with 6-8 blocks
- `scripts/lib/template_blocks.py` (~350 lines)
- `tests/test_template_blocks.py` (~400 lines)
- Updated `spec-template.md`, `plan-template.md`

### Phase 4.2: Patch System (40h, 1 week)

**Goal**: Implement patch storage and application

**Tasks**:
1. Create JSON schema for patch metadata
2. Create `scripts/lib/template_patches.py`:
   - `parse_patch()`
   - `apply_patch()` — apply single patch
   - `apply_patches()` — apply all patches for template
   - `detect_patch_conflicts()`
   - `validate_patched_template()`
3. Create `.specify/templates/patches/` structure
4. Extend `.scaffold-state.yaml` with patches field
5. Tests: 25+ tests for patch parsing, application, conflicts

**Deliverables**:
- Patch system implementation (~450 lines)
- `tests/test_template_patches.py` (~500 lines)
- Example patches for spec-template, plan-template

### Phase 4.3: CLI Commands (30h, 3-4 days)

**Goal**: User-facing commands for block management

**Tasks**:
1. `scaffold.py compose-template <name>` — show assembled template
2. `scaffold.py check-blocks` — detect block drift (like check-templates)
3. `scaffold.py diff-block <name>` — diff upstream vs local block
4. `scaffold.py update-blocks [--block NAME]` — pull upstream block updates
5. `scaffold.py create-patch <template> <name>` — interactive patch creation
6. `scaffold.py apply-patches <template>` — manual patch application
7. Integration with existing flows (merge-template, diff-template)

**Deliverables**:
- 6 new CLI commands
- `scripts/lib/flows/compose_template.py` (~150 lines)
- `scripts/lib/flows/check_blocks.py` (~180 lines)
- `scripts/lib/flows/update_blocks.py` (~200 lines)
- `tests/test_flows_blocks.py` (~350 lines)

### Phase 4.4: Migration & Compatibility (30h, 1 week)

**Goal**: Migrate existing projects, maintain backward compatibility

**Tasks**:
1. `scaffold.py migrate-to-blocks` command:
   - Detect custom sections in monolithic templates
   - Auto-generate patches from customizations
   - Backup originals
   - Update `.scaffold-state.yaml`
2. Backward compatibility layer:
   - Support both monolithic and modular templates
   - Transparent composition for old commands
3. Migration guide documentation
4. Update TEMPLATE_DRIFT_DETECTION.md
5. Tests: 15+ tests for migration, compatibility

**Deliverables**:
- Migration command (~300 lines)
- `docs/MODULAR_TEMPLATES.md` (~600 lines)
- Updated TEMPLATE_DRIFT_DETECTION.md
- `tests/test_migration_blocks.py` (~300 lines)

---

## Benefits

### For Template Maintainers (scaffold-project)
- **Granular updates**: Update just "User Scenarios" block → all projects get it
- **Reusability**: Share blocks across spec/plan/tasks templates
- **Easier evolution**: Change small blocks, not massive files
- **Clear impact**: "Block X changed in v2.1" vs "template.md changed"

### For Project Users
- **Cleaner customizations**: Patches clearly separate from standard content
- **Safer updates**: Update individual blocks without touching custom sections
- **Conflict reduction**: Merge happens per-block, not per-file (smaller scope)
- **Transparency**: See exactly what's custom vs standard

### For Automation
- **Better drift detection**: Report "user-scenarios v1.0 → v2.0" not "template changed"
- **Selective updates**: Update only non-customized blocks automatically
- **Conflict prediction**: Know which blocks have patches → higher merge risk

---

## Risks & Mitigation

### Risk 1: Migration Complexity
**Impact**: High (affects all existing projects)
**Mitigation**:
- Phase 4.4 dedicated to migration
- Backward compatibility layer
- Automatic patch generation from customizations
- Comprehensive migration guide

### Risk 2: Performance Overhead
**Impact**: Medium (composition + patch application on every template access)
**Mitigation**:
- Cache composed templates
- Lazy composition (only when template actually used)
- Profile and optimize in Phase 4.1

### Risk 3: User Adoption
**Impact**: Medium (users may stick with monolithic templates)
**Mitigation**:
- Backward compatibility (both modes work)
- Clear migration documentation
- Show value with examples (easier updates, cleaner diffs)
- Make migration command simple and automatic

### Risk 4: Increased Complexity
**Impact**: Medium (more files, more concepts to understand)
**Mitigation**:
- Excellent documentation
- Simple defaults (most users won't create patches)
- CLI commands hide complexity (compose happens transparently)
- Examples and tutorials

---

## Success Criteria

### Phase 4.1
- [ ] All existing templates decomposed into 6-8 blocks
- [ ] Composition engine produces identical output to monolithic templates
- [ ] Tests: 100% passing (20+ tests)
- [ ] Performance: Composition <50ms for 6 blocks

### Phase 4.2
- [ ] Patch system successfully applies 3+ example patches
- [ ] Conflict detection catches overlapping patches
- [ ] Tests: 100% passing (25+ tests)
- [ ] `.scaffold-state.yaml` correctly tracks patches

### Phase 4.3
- [ ] 6 new CLI commands implemented and documented
- [ ] `check-blocks` detects block drift across templates
- [ ] `update-blocks` successfully merges upstream changes
- [ ] Tests: 100% passing (20+ tests for flows)

### Phase 4.4
- [ ] Migration command successfully converts 3+ real projects
- [ ] Zero regressions in existing workflows
- [ ] Documentation complete (~600 lines)
- [ ] Backward compatibility: old commands work unchanged

---

## Next Steps

1. **Review this design** — get feedback on architecture
2. **Validate approach** — create small POC with 1 template + 2 blocks
3. **Implement Phase 4.1** — blocks + composition engine
4. **Iterate** — refine based on Phase 4.1 learnings

---

**Status**: ⏸️ DESIGN COMPLETE — Awaiting review and approval
