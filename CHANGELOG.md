# Changelog

All notable changes to the **Enterprise Scaffold Project Template** will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning 2.0.0](https://semver.org/).

---

## [Unreleased]

---

## [1.7.1] — 2026-05-21

---

## [1.7.1] — 2026-05-21

### Added

#### Scaffold Test Automation — End-to-End Testing (May 2026)
- **Test Suite**: Comprehensive automated testing for scaffold new/upgrade commands (~1,300 lines):
  - Created `tests/test_scaffold_new.py` (10 tests, 100% passing):
    - test_scaffold_new_basic: Directory structure, Git init
    - test_scaffold_new_vscode_config: .vscode/settings.json, mcp.json validation
    - test_scaffold_new_copilot_instructions: .github/copilot-instructions.md deployment
    - test_scaffold_new_critical_files: Integration with validate_critical_files()
    - test_scaffold_new_scaffold_state: .scaffold-state.yaml metadata validation
    - test_scaffold_new_git_initialized: .git/, initial commit, branch verification
    - test_scaffold_new_combinations: Parametrized test for domain×language matrix (4 combos)
  - Created `tests/test_scaffold_upgrade.py` (11 tests, 100% passing):
    - test_scaffold_upgrade_basic: Upgrade execution, logs, backups
    - test_scaffold_upgrade_all_validations: **CRITICAL** — Executes 11 suites, 51 checks
    - test_scaffold_upgrade_bug20_mcp_http: BUG-20 validation
    - test_scaffold_upgrade_bug001_objetivo_init: BUG-001 fixes validation
    - test_scaffold_upgrade_bug19_gitvalidators: BUG-19 git_validators.py + sanitize.py
    - test_scaffold_upgrade_copilot_instructions: BUG-13 copilot-instructions.md
    - test_scaffold_upgrade_merge_strategy: BUG-16 JSON/workspace merge validation
    - test_scaffold_upgrade_session_memory_init: BUG-11 + BUG-12 systems
    - test_scaffold_upgrade_logs_created: Logs validation
    - test_scaffold_upgrade_idempotent: 3× upgrade idempotency test
    - test_scaffold_upgrade_no_old_sessions_folder: BUG-22 regression test
  - Integration with `scripts/validate_workspace_upgrade.py` (51 validations across 11 suites)
  - Modified `tests/conftest.py`: Added configure_git_for_tests() fixture (session-scoped, auto-use)

- **CI/CD Integration**: Created `.github/workflows/scaffold-tests.yml` (~200 lines):
  - Job 1: test-scaffold-new (matrix Python 3.10/3.11/3.12 × 4 domain/language combos)
  - Job 2: test-scaffold-upgrade (matrix Python 3.10/3.11/3.12)
  - Job 3: test-scaffold-smoke (full workflow: new → upgrade → validate 51 checks)
  - Job 4: summary (aggregates results, creates GitHub step summary)
  - Triggers: push (master/main/develop), pull_request, workflow_dispatch, schedule (Sundays 02:00 UTC)
  - Dependencies: requirements.txt, pytest, pytest-timeout, pyyaml

- **Impact**:
  - ✅ Test coverage: 21/21 tests passing (100%)
  - ✅ Validation coverage: 51/51 checks passing (100%)
  - ✅ Regression detection: 3 bugs detected and fixed (BUG-22, BUG-16, BUG-18)

#### Pre-Commit Hook: Memory System Validation (May 2026)
- **Hook Implementation**: Created `scripts/git-hooks/pre-commit` (~240 lines):
  - Blocks commits of test files in .memory/ (__test-*.md, __auto-generated-title.md, __search-test-*.md)
  - Validates YAML frontmatter in .memory/*.md files
  - Enforces valid categories: project, team, sessions, user
  - Exit code 1 if violations detected
  - Helpful error messages with remediation commands (make memory-cleanup, conftest.py fixtures)

- **Test Suite**: Created `tests/test_precommit_validate_memory.py` (10 tests, 100% passing):
  - test_hook_blocks_test_files: Verifies __test-*.md rejection
  - test_hook_blocks_auto_generated_title: Verifies __auto-generated-title.md rejection
  - test_hook_blocks_search_test_files: Verifies __search-test-*.md rejection
  - test_hook_validates_frontmatter_invalid_category: Rejects invalid categories
  - test_hook_validates_frontmatter_missing_closing: Rejects malformed frontmatter
  - test_hook_allows_valid_memory_file: Accepts valid files with frontmatter
  - test_hook_allows_file_without_frontmatter: Accepts files without frontmatter (optional)
  - test_hook_skips_non_memory_files: Ignores non-.memory/ files
  - test_hook_allows_valid_categories: Accepts all 4 valid categories
  - test_hook_error_messages_helpful: Verifies error messages include remediation

- **Makefile Integration**: Target `git-hooks-install` already existed (installs pre-commit + commit-msg)

- **Impact**:
  - ✅ Prevents test file pollution in .memory/ (regression prevention)
  - ✅ Enforces YAML frontmatter quality standards
  - ✅ Complements IMP-65 P0 memory cleanup work
  - ✅ Zero false positives: frontmatter is optional, only validates when present
  - ✅ CI/CD automation: scaffold-tests.yml active for continuous validation

#### GitHub Actions: Dependency Check Automation (May 2026)
- **Workflow**: Created `.github/workflows/dependency-check.yml` (~200 lines):
  - Schedule: Mondays 9h UTC (cron: '0 9 * * MON')
  - Triggers: schedule, workflow_dispatch (manual), pull_request (on dependency files)
  - Permissions: contents:read, issues:write
  - Job: check-dependencies (ubuntu-latest, Python 3.12)
  - Steps:
    1. Checkout code
    2. Setup Python 3.12
    3. Install project dependencies (`pip install -e ".[dev,security]"`)
    4. Install pip-audit
    5. Check outdated dependencies (pip list --outdated → outdated.json)
    6. Execute pip-audit CVE scan (pip-audit --format=json → audit.json)
    7. Upload artifacts (outdated.json, audit.json, retention: 30 days)
    8. Create P0 issue if vulnerabilities found (labels: security, dependencies, P0, automated)

- **Helper Scripts**: Created `.github/scripts/` (~75 lines total):
  - `process_outdated.py` (~30 lines): Processes pip outdated JSON → markdown table
  - `process_audit.py` (~45 lines): Processes pip-audit JSON → security summary + vuln_count.txt

- **Test Suite**: Created `tests/test_dependency_check_workflow.py` (17 tests, 100% passing):
  - test_dependency_check_workflow_exists: Verifies workflow file existence
  - test_dependency_check_workflow_valid_yaml: Validates YAML syntax
  - test_dependency_check_workflow_has_schedule: Verifies Monday 9h UTC schedule
  - test_dependency_check_workflow_has_manual_trigger: Verifies workflow_dispatch
  - test_dependency_check_workflow_has_pr_trigger: Verifies PR trigger on dependency files
  - test_dependency_check_workflow_has_permissions: Verifies permissions (contents:read, issues:write)
  - test_dependency_check_workflow_has_main_job: Verifies check-dependencies job
  - test_dependency_check_workflow_has_steps: Verifies 6+ steps exist
  - test_process_outdated_script_exists: Verifies helper script existence
  - test_process_outdated_script_executable: Verifies shebang
  - test_process_outdated_script_processes_json: Tests JSON processing with test data
  - test_process_audit_script_exists: Verifies helper script existence
  - test_process_audit_script_executable: Verifies shebang
  - test_process_audit_script_processes_json_no_vulns: Tests no vulnerabilities case
  - test_process_audit_script_processes_json_with_vulns: Tests vulnerabilities case (exit code 1)
  - test_dependency_check_workflow_creates_artifacts: Verifies artifacts upload config
  - test_dependency_check_workflow_creates_issues: Verifies P0 issue creation logic

- **Impact**:
  - ✅ Weekly automated security scanning (CVE detection via pip-audit)
  - ✅ Dependency freshness monitoring (outdated packages)
  - ✅ Automatic P0 issue creation for critical vulnerabilities
  - ✅ Artifacts retention for audit trail (30 days)
  - ✅ Manual trigger for on-demand scans
  - ✅ PR integration for dependency file changes

#### Documentation: MEMORY_SYSTEM.md v1.1.0 (May 2026)
- **Updated Documentation**: Updated `docs/MEMORY_SYSTEM.md` v1.0.0 → v1.1.0:
  - Version: 1.1.0 (IMP-65 P1 Complete)
  - Last update: 2026-05-20
  - Status: ✅ Estável → ✅ Produção
  - Expanded sections:
    1. **Validation**: Added pre-commit hook details (IMP-65 P1, ~240 lines)
       - Blocks test files (__test-*.md, __auto-generated-title.md, __search-test-*.md)
       - Validates YAML frontmatter (6 valid categories)
       - Tests: tests/test_precommit_validate_memory.py (10 tests, 100%)
    2. **Troubleshooting: Outdated Dependencies**: Added dependency-check workflow automation
       - Weekly automated scanning (Mondays 9h UTC)
       - pip-audit CVE scanning
       - Automatic P0 issue creation
       - Artifacts: outdated.json, audit.json (retention 30 days)
       - Tests: tests/test_dependency_check_workflow.py (17 tests, 100%)
    3. **Changelog**: Added v1.1.0 entry with IMP-65 P1 complete details
  - Original 7 sections maintained (~700 lines):
    - Directory structure, scopes, best practices, naming, frontmatter, commands, troubleshooting

- **Impact**:
  - ✅ Complete memory system documentation (production-ready)
  - ✅ Integrated with IMP-65 P1 implementations (pre-commit hook, dependency-check)
  - ✅ Developer onboarding resource (all memory patterns documented)
  - ✅ Troubleshooting guide (6 common scenarios)

#### Session-Start Prompt: Quick Mode (IMP-65 P2, May 2026)
- **Feature**: Added Quick Mode to session-start ritual for fast debugging sessions
- **File Modified**: `.github/prompts/session-start.prompt.md` (v1.0 → v2.0)
- **Changes**:
  - New section "Modo de Execução" at top of document
  - User prompt: "Modo de execução: [quick | completo]" before starting ritual
  - Mode comparison table with 8 steps (quick vs completo)
  - Marked steps 5-8 with ⏭️ emoji (skip in quick mode)
  - Separated checklists: Quick (5 items) vs Completo (11 items)
  - New section "Quando Usar Cada Modo" with guidelines (5 examples each)
  - Updated anti-patterns with mode selection guidance
  - Version updated to v2.0 | IMP-65 P2 | 2026-05-20

- **Quick Mode Behavior** (~5s duration):
  - ✅ Step 1: Verify MCP config (memory, sequential-thinking)
  - ✅ Step 2: Recover context (TODO.md, INDEX.md, FINAL_STATUS)
  - ✅ Step 3: Load Copilot rules (.copilot-rules.md enforcement)
  - ✅ Step 4: Security scan (credentials check)
  - ✅ Step 4.5: Dependencies check (vulnerabilities)
  - ❌ Step 5: SKIP git status/log
  - ❌ Step 6: SKIP session docs creation
  - ❌ Step 6.5: SKIP time tracker
  - ❌ Step 7: SKIP scope/domain profile
  - ❌ Step 8: SKIP index/TODO update

- **Completo Mode Behavior** (~15s duration):
  - ✅ All 8 steps (same as before v2.0)
  - Backward compatible (no breaking changes)

- **Use Cases**:
  - **Quick Mode**: Debugging (<30min), quick queries, hotfix, read-only sessions
  - **Completo Mode**: Features (IMP-*), bugs (BUG-*), long sessions (>1h), documented work

- **Impact**:
  - ⚡ 67% time reduction for quick sessions (15s → 5s)
  - 📖 Clear guidelines for mode selection
  - 🎯 User flexibility (choose appropriate mode)
  - ✅ Zero breaking changes (completo mode preserved)
  - ✅ Estimativa 3h → Real 45min (simpler than expected)

#### BUG-16 Manual Validation: Scaffold Merge System (May 2026)
- **Objective**: End-to-end validation of BUG-16 merge system with real project customizations
- **Priority**: P1 HIGH (final production validation)
- **Duration**: 30 min (estimate matched actual)
- **Test Project**: Created `~/Documentos/DevOps/Vya-Jobs/bug16-manual-test`

- **Procedure**:
  1. ✅ Created test project (158 files via scaffold.py --new)
  2. ✅ Applied user customizations:
     - settings.json: 4 custom configs (extraPaths, rulers, autofetch, customUserSetting)
     - mcp.json: 1 custom server (custom-database with env vars)
     - .copilot-rules: 3 duplicate files for consolidation test
  3. ✅ Executed upgrade --force --ci (21 files updated, 125 skipped)
  4. ✅ Validated merge results and backups

- **Results** (100% APPROVED):
  - **settings.json** (48 → 54 lines):
    - ✅ All 4 user customizations preserved (extraPaths, rulers, autofetch, customUserSetting)
    - ✅ All 48 template configurations added (mcp.autostart, python paths, formatting, etc.)
    - ✅ Backup created: .vscode/settings.json.backup
  - **mcp.json**:
    - ✅ User server preserved (custom-database with env vars)
    - ✅ Template servers added (memory, sequential-thinking, filesystem, github)
    - ✅ Backup created: .vscode/mcp.json.backup
  - **.copilot-rules consolidation**:
    - ✅ 4 files consolidated → 1 file (723 lines) at .copilot-shared/rules/.copilot-rules.md
    - ✅ Symlink created: .copilot-rules.md → ../../.copilot-shared/rules/.copilot-rules.md
    - ✅ Original files moved to .backups/copilot-rules/ (3 files)
    - ✅ Consolidation header in file: "Consolidado de 4 arquivos: ..."
  - **Backups**:
    - ✅ 10 backup files created in .backups/
    - ✅ All modified files have .backup counterpart

- **Metrics**:
  - Test coverage: 8/8 files validated (100%)
  - Customizations tested: 5 (4 settings + 1 mcp server)
  - Merge strategy: "user-wins" — all customizations preserved + template added ✅
  - Consolidation: 4 → 1 file with symlink ✅

- **Report**: docs/SESSIONS/2026-05-20/BUG-16_MANUAL_VALIDATION_REPORT.md

- **Impact**:
  - ✅ BUG-16 merge system validated in production scenario
  - ✅ Confirms automated tests (test_scaffold_upgrade_merge_strategy.py) match real-world behavior
  - ✅ Zero data loss — all user customizations preserved
  - ✅ System ready for production use

### Fixed

#### BUG-22 CRITICAL: docs/SESSIONS/ Old Folder Created During Upgrade (May 2026)
- **Problem**: scaffold upgrade was creating `docs/SESSIONS/<created_at>/` during upgrade despite migration to `.session-docs/`
- **Root Cause**: 3 locations had legacy code referencing `docs/SESSIONS`:
  - scripts/lib/project.py line 1831 (DIRS_TO_CREATE)
  - scripts/lib/project.py line 2281 (setup_project_docs())
  - scripts/lib/flows/dry_run.py line 25 (manifest path)
- **Fix**: Changed all references from `"docs/SESSIONS"` to `".session-docs"` (3 files modified)
- **Validation**: test_scaffold_upgrade_no_old_sessions_folder now passing
- **Commit**: `1b2bb50`

#### BUG-16: .copilot-rules Consolidation with Symlinks (May 2026)
- **Problem**: detect_copilot_rules_files() counted symlinks as duplicate files
- **Scenario**: 1 real file (.copilot-rules-<project>.md) + 1 symlink (.copilot-rules.md → .copilot-shared/)
- **Root Cause**: scripts/lib/copilot_rules_consolidate.py didn't filter symlinks and missed `.copilot-rules-*.md` pattern
- **Fix**: Added symlink filter `[f for f in matches if not f.is_symlink()]` and pattern `.copilot-rules-*.md`
- **Validation**: test_scaffold_upgrade_merge_strategy now passing
- **Commit**: `8ff4199`

#### BUG-18: objetivo.yaml Project Info Validation (May 2026)
- **Problem**: validate_bug18_objetivo() had hardcoded project name check `project_name == "test-workspace-fix"`
- **Type**: Bug in validation, not in scaffold (objetivo.yaml was correct)
- **Fix**: Changed to generic validation: `bool(project_name) and project_name != "CHANGE_ME"`
- **Impact**: Tests now accept any valid project name, not just hardcoded value
- **Validation**: test_scaffold_upgrade_all_validations and test_scaffold_upgrade_idempotent now passing (51/51)
- **Commit**: `5df0c16`

#### Scaffold Upgrade --ci Flag Fix (May 2026)
- **Problem**: _validate_and_fix_paths() ignored --ci flag causing EOFError (Prompt.ask() with no stdin)
- **Fix**: Added ci_mode parameter to _validate_and_fix_paths() in scripts/lib/flows/upgrade.py
- **Impact**: All upgrade tests now running successfully in non-interactive mode
- **Related**: Part of test automation infrastructure (commit `39a3e66`)

#### BUG-05: Interactive Layer 2 Profile Selection (Apr 2026)
- **Phase 1 (Core)**: Interactive mode now shows Layer 2 profiles (python-fastapi, typescript-next, etc.):
  - Added `_get_compatible_layer2_profiles()` in `scripts/lib/ui.py`:
    - Reads profile-descriptors/*.yaml dynamically
    - Filters by domain + language compatibility
    - Supports both old (requires) and new (meta) descriptor formats
    - Handles language aliases (hcl→terraform, yaml→kubernetes)
    - Domain inference from tags (web/api→programming, iac/cloud→infrastructure, data/etl→analysis)
  - Added `_select_layer2_profile()` in `scripts/lib/ui.py`:
    - New question [9] in interactive wizard
    - Shows only compatible profiles for selected domain + language
    - Numbered menu with profile descriptions
    - Default option: "No, just base structure"
  - Modified `_collect_extra_profiles()` to integrate Layer 2 selection:
    - Layer 1 profiles (devops-programming, devops-infrastructure, devops-analysis) remain separate (question [8])
    - Layer 2 profiles shown dynamically based on domain + language (question [9])
    - Returns combined list: Layer 1 extras + selected Layer 2 profile
  - Resolves: "novice users cannot select python-fastapi in interactive mode" (original bug report)

- **Phase 2 (Enhancement)**: Added `--with-code-profile` flag to `new` command:
  - New argument in `scaffold.py`: `--with-code-profile PROFILE`
  - One-step project creation with code profile: `scaffold.py new --ci --name my-api --domain programming --language python --with-code-profile python-fastapi`
  - Equivalent to: `scaffold.py new ... && cd project && scaffold.py compose python-fastapi`
  - Integration in `scripts/lib/flows/new_project.py`:
    - Executes `flow_compose_profiles()` after project creation if flag provided
    - Always non-interactive when using --with-code-profile
    - Complete error handling with rollback on compose failure
  - Benefits:
    - ✅ Single command workflow
    - ✅ Validates domain + language compatibility
    - ✅ Proper state persistence in .scaffold-state.yaml
    - ✅ Used automatically by interactive mode (question [9])

- **Phase 3 (Documentation)**:
  - Updated `docs/guides/NEW_PROJECT_COMMAND.md`:
    - New section: "Modo Interativo com Layer 2" explaining question [9]
    - Updated examples to use `--with-code-profile` (recommended over 2-step workflow)
    - Added comparison: `--with-code-profile` vs `compose` separate command
    - Documented workflow: 1 command vs 2 steps with pros/cons
  - Updated help text in `scaffold.py`:
    - Clear usage example for `--with-code-profile`
    - Explains equivalence to separate compose command
  - Resolves: UX confusion for novice users (no documentation for Layer 2 profiles)

Impact:
- ✅ Novice users can now discover and select Layer 2 profiles interactively
- ✅ CLI power users get single-command workflow with `--with-code-profile`
- ✅ Backward compatible: 2-step workflow (new → compose) still works
- ✅ Dynamic profile discovery: new profiles automatically appear in wizard
- ✅ Smart filtering: only shows profiles compatible with selected domain + language

**Status**: Phases 1-3 complete (9h work), Phase 4 (Tests) in progress
**Priority**: P1 — UX blocker for novice users
**Related**: IMP-65 (template synchronization), BUG-02/BUG-03 (fixed)

### Changed

#### Session Manager Agent v1.2.0 (Mar 2026)
- **Session End Workflow (D-17)**: `git push` agora é obrigatório no encerramento de sessão
  - Modificado: `.github/agents/session-manager.agent.md` — passo 7 "Git Repository Update"
  - Comportamento anterior: push era opcional ("Optionally push if requested")
  - Comportamento novo: push é mandatório com retry automático em caso de falha
  - Se push falhar: executa `git pull --rebase` automaticamente e tenta novamente
  - Session Closure Report atualizado: "Git: [N] commits created and pushed"
  - Alinhamento com `.github/prompts/session-end.prompt.md` que já documentava push obrigatório
  - Impacto: garante que repositório remoto esteja sempre sincronizado ao final da sessão
  - Benefício: elimina risco de perda de trabalho; melhora rastreabilidade; facilita colaboração

### Added

#### Sprint 5: Estrutura P2 (ACTION_PLAN_TO_10 — Mar 2026)
- `tmp/` directory structure — project-local temporary files:
  - Created `tmp/README.md` with usage guidelines
  - Purpose: Store temporary files during script execution, safer alternative to /tmp/
  - Automatic cleanup on session end via cleanup script
  - All files git-ignored except README.md

- `scripts/cleanup-tmp.sh` — automated temporary files cleanup (~145 lines):
  - Options: --dry-run (preview), --verbose (detailed output), --help
  - Removes all files in tmp/ except README.md
  - Removes all subdirectories in tmp/
  - Reports: file count, directory count, total size before/after cleanup
  - Exit codes: 0 (success), 1 (errors)
  - Safe: preserves tmp/README.md documentation

- `.gitignore` — updated temporary files section:
  - Changed from `tmp/` to `tmp/*` with exception `!tmp/README.md`
  - Ensures tmp/README.md is tracked while all other tmp/ contents are ignored

- `.github/prompts/session-end.prompt.md` — added cleanup step:
  - New Passo 10: "Limpar Diretório Temporário"
  - Commands to verify (dry-run) and execute cleanup
  - Checklist updated with cleanup verification
  - Guidance on when NOT to clean (active session files)

- `README.md` — documented tmp/ usage:
  - New subsection "Temporary Files Management" in Development Workflow
  - Purpose and benefits explained
  - Usage examples for scripts (./tmp/ instead of /tmp/)
  - Cleanup commands reference
  - Note about automatic session-end cleanup

Impact:
- Eliminates need for system /tmp/ directory access (better security)
- Prevents accidental inclusion of temporary files in git
- Automatic cleanup ensures clean state between sessions
- Improved developer experience with clear guidelines

#### Sprint 4: Ansible P1 (ACTION_PLAN_TO_10 — Mar 2026)
- `docs/ANSIBLE_BEST_PRACTICES.md` — comprehensive Ansible best practices guide (~1000 lines):
  - 12 major sections covering all Ansible aspects
  - Core Principles: Idempotency with examples, declarative over imperative comparison, module hierarchy (5 levels), keep playbooks simple guidelines, DRY principle with implementation patterns
  - Project Structure: Complete recommended layout (ansible/ directory with 7 subdirectories: inventory/group_vars/host_vars/playbooks/roles/plugins/scripts/docs), file naming conventions table (7 types), directory structure diagram
  - Inventory Management: Static inventory (INI and YAML formats with examples), dynamic inventory (AWS EC2 plugin example), 6 best practices
  - Playbook Design: Basic structure template, task organization (descriptive names with good/bad examples), conditionals (simple/multiple/OR/complex examples), loops (simple/dictionary/dict2items/until-retry patterns), tags (usage with 3 examples)
  - Role Development: Complete role structure (14 components explained), defaults/main.yml example (12 variables), tasks/main.yml with import patterns, templates with Jinja2, handlers with conditional execution, meta/main.yml with galaxy_info, README.md template for roles
  - Variable Management: Variable precedence (complete 21-level hierarchy documented), naming conventions (good/bad examples), organizing variables (group_vars structure), vault integration examples
  - Security Best Practices: Ansible Vault (create/encrypt/edit/view commands), .gitignore patterns (9 entries), environment-specific vaults structure, privilege escalation limits, SSH keys configuration, input validation examples, no_log usage
  - Testing and Validation: Syntax check commands, ansible-lint configuration (.ansible-lint with skip_list/warn_list/exclude_paths), dry run (--check --diff), Molecule testing reference, unit testing with Python/pytest/testinfra
  - Performance Optimization: Gather facts selectively (gather_subset example), pipelining configuration, fact caching (jsonfile backend), parallel execution (forks=20), loop optimization (good/bad comparison), async for long-running tasks (5-minute example)
  - Error Handling: failed_when conditions (multi-condition example), ignore_errors usage, block/rescue/always pattern (complete deployment example), assertions (prerequisite validation)
  - Documentation: Playbook documentation template (header with purpose/author/requirements/usage/variables), role README.md template (11 sections)
  - CI/CD Integration: GitHub Actions workflow (3 jobs: lint/syntax-check/molecule with matrix strategy), GitLab CI (.gitlab-ci.yml with 3 stages: lint/test/deploy)

- `docs/MOLECULE_TESTING_GUIDE.md` — complete Molecule testing framework guide (~1000 lines):
  - 12 comprehensive sections covering Molecule framework
  - What is Molecule: Definition (testing framework for Ansible roles), features (automate testing, multiple platforms, multiple drivers, lint integration, verification, CI/CD ready), benefits comparison table (without vs with Molecule: 5 comparisons)
  - Installation: Requirements (Python 3.8+, Docker, Ansible 2.10+), pip install commands (5 variations: basic/docker/vagrant/all), verify installation (molecule --version, molecule drivers)
  - Quick Start: Initialize new role (molecule init role, molecule init scenario), directory structure created (14 files explained), run tests (molecule test, molecule create/converge/verify/destroy)
  - Project Structure: Complete file-by-file breakdown (molecule.yml: 140+ lines example with dependency/driver/platforms/provisioner/verifier/lint/scenario sections fully configured, converge.yml: role execution playbook with vars, prepare.yml: prerequisites setup, verify.yml: Ansible assertions, tests/test_default.py: Testinfra tests skeleton)
  - Configuration: Platform-specific configs (Ubuntu/CentOS/Alpine with full YAML), multiple platform matrix (5 platforms: ubuntu2004/ubuntu2204/debian11/centos8/rockylinux8), custom Dockerfile.j2 (multi-distro support)
  - Testing Workflow: Complete test sequence (14 steps explained), manual step-by-step workflow, development workflow (keep instance running), specific platform testing
  - Writing Tests: Extensive Testinfra examples (File Tests: 6 functions, Package Tests: 2 functions, Service Tests: 3 functions, Socket Tests: 2 functions, Process Tests: 2 functions, Command Tests: 2 functions, User Tests: 1 function, System Info Tests: 2 functions, Parameterized Tests: 2 examples, Ansible Verify Playbook alternative)
  - Drivers: Comparison of 4 drivers (Docker: fast <5s recommended, Podman: similar, Vagrant: full VM slow minutes, Cloud: EC2/GCE with configuration examples)
  - Scenarios: Multiple scenarios concept (default/with-ssl/cluster), directory structure (4 scenarios), create scenario command, run specific scenario, 3 detailed examples (default/SSL with certificate/cluster with 3 nodes)
  - CI/CD Integration: GitHub Actions (complete workflow with matrix strategy for scenarios/platforms), GitLab CI (parallel matrix example with docker:dind)
  - Best Practices: 7 guidelines (use pre-built images with good/bad examples, test idempotence, organize tests by component, use fixtures example, keep scenarios focused, document scenarios, use markers for long tests)
  - Troubleshooting: 5 common issues with solutions (Docker daemon not running, Testinfra import failed, platform already exists, idempotence test failed with fix example, tests pass locally but fail in CI with retry logic)

- `docs/ANSIBLE_PLAYBOOK_TEMPLATES.md` — ready-to-use playbook templates (~800 lines):
  - 8 categories of production-ready playbooks
  - Docker Management: Docker installation (Ubuntu/Debian with GPG keys, repository setup, engine installation, user groups), Docker Compose deployment (project directory setup, environment templating, health checks, rollback), Docker cleanup (containers/images/networks/volumes pruning with disk usage reporting), Docker health check (service status, container health, disk usage verification)
  - Database Operations: PostgreSQL backup (compressed dumps with custom format, backup rotation, size reporting, verification), PostgreSQL restore (backup file verification, connection termination, database recreation, restore execution, table count validation), MySQL database management (database creation with encoding/collation, user management with privileges, MySQL tuning configuration)
  - Application Deployment: Zero-downtime deployment (load balancer removal, graceful shutdown, version deployment, health checks, rollback on failure), Blue-green deployment (deploy to inactive environment, health check, smoke tests, load balancer switch, environment management)
  - Backup and Restore: Comprehensive system backup (filesystem archive with exclusions, package list, crontabs, systemd services, backup manifest generation)
  - Monitoring and Health Checks: Comprehensive health check (disk/memory/CPU monitoring, service status, Docker health, network connectivity, SSL certificate expiry, health report generation)
  - Maintenance Operations: System update and reboot (package upgrade, reboot detection, graceful server removal from load balancer, service verification after reboot)
  - Security Operations: Security hardening (package updates, firewall configuration, fail2ban setup, SSH hardening, file permissions, package cleanup)
  - Usage: Copy templates, customize variables, test with --check, run in production

- `.github/templates/ansible/` — production-ready playbook examples (5 files):
  - `README.md` — template usage guide (~120 lines): Available templates description (8 templates), Quick start (3 steps: copy/customize/run), Usage guidelines (before running: review/test/limit/backup, security: vault/credentials/environment-specific, best practices: tags/error handlers/descriptive names/blocks/verbose), Customization (vault support, notifications, error handling), Further reading links, Important notes
  - `deploy-app.yml` — zero-downtime application deployment (~250 lines): Serial deployment (1 server at a time), Load balancer integration (remove/add server), Graceful shutdown and version download, Health checks with retry logic, Automatic rollback on failure (restore backup, restart service), Cleanup old backups (keep last 5)
  - `docker-deploy.yml` — Docker Compose stack deployment (~200 lines): Project directory setup with subdirectories, Compose files deployment, Environment file templating (with secrets protection), Image pulling and stack deployment, Health checks for multiple services (port verification), Rollback on failure (stop failed deployment, restore environment file)
  - `health-check-system.yml` — comprehensive system health check (~340 lines): Resource checks (disk/memory/swap/CPU/IO wait), Service status verification, Docker health checks (daemon, containers, health status, disk usage), Network connectivity tests, SSL certificate expiry checks, Health report generation (structured YAML with all metrics), Critical alerting (disk/services/containers), Warning thresholds (disk/memory/SSL expiry), Report summary with color-coded status
  - `backup-database.yml` — PostgreSQL database backup (~230 lines): Compressed custom format dumps, Database size reporting before backup, Backup file verification, Backup manifest generation, Automatic rotation (configurable retention days), Optional remote upload (S3), Notification webhooks (Slack), Rollback on failure (cleanup partial backups), Backup logging

#### Sprint 3: Documentation P1 (ACTION_PLAN_TO_10 — Mar 2026)
- `docs/TROUBLESHOOTING.md` — comprehensive troubleshooting guide:
  - 8 major sections covering all common issues
  - 24 specific problems with symptoms and multiple solutions each
  - Categories: Setup & Initialization (symlinks, project init), Git & Version Control (pre-commit, Gitleaks, large files), Python Environment (pytest imports, Black/Ruff conflicts, MyPy errors), Testing (fixtures, coverage, performance), Security & Pre-commit (secrets committed, Bandit warnings, Ansible Vault), Documentation & Links (broken links, rendering), Scripts & Automation (Makefile, permissions, environment variables), VS Code Integration (settings, interpreter)
  - Additional resources: useful commands reference, log locations, documentation index
- `docs/CONVENTIONS.md` — technical standards and conventions guide:
  - 10 comprehensive sections defining project standards
  - Code Structure: Python (PEP 8, Black 88 chars, Python 3.12+), Markdown (ATX headers, line 80), YAML (2 spaces), Shell (bash, shellcheck)
  - Naming Conventions: comprehensive table with 15+ patterns (snake_case, PascalCase, kebab-case)
  - Python Standards: Type hints (required for public APIs), Docstrings (Google style), Imports (3 groups), Error handling (specific exceptions), Logging (module logger, 5 levels)
  - Testing Standards: Organization (AAA pattern), Coverage (≥80% target), Markers (9 markers: unit/integration/slow/smoke/security/skip_ci/requires_docker/requires_ssh/requires_network), Fixtures (shared conftest, 4 scopes)
  - Git Conventions: Conventional Commits (9 types with scopes), Branch naming (NNN-description, fix-, security-), PR templates
  - Documentation Standards: README structure (11 sections), Inline docs (explain WHY), Session docs (4 files per session)
  - Security Standards: Credentials (.secrets/ directory), Input validation, File permissions (600 secrets, 700 scripts)
  - File Organization: Root directory structure, .gitignore patterns
  - Automation Standards: Makefile (self-documenting help), Script headers (comprehensive template)
  - Enforcement Tools: Black, Ruff, MyPy, Bandit, pytest, pre-commit, Gitleaks, shellcheck
- `scripts/validate-docs-links.sh` — automated markdown link validation:
  - Extract markdown links: [text](url) and [ref]: url patterns
  - Validate relative/absolute links (skip external URLs: http/https/ftp/mailto)
  - Check file/directory existence with path normalization
  - Suggest fixes: find similar filenames, show relative paths
  - Summary: counters for files/links/broken with color-coded output (RED/GREEN/YELLOW/BLUE)
  - Options: --fix (suggestions), --help, --verbose
  - Exclusions: .git, node_modules, .venv, venv
  - Exit codes: 0 (valid), 1 (broken), 2 (invalid usage)

#### Sprint 2: Testing P0 (ACTION_PLAN_TO_10 — Mar 2026)
- `pytest.ini` — comprehensive pytest configuration:
  - 70 lines with markers, verbose output, coverage settings
  - 9 custom markers: unit, integration, slow, smoke, security, skip_ci, requires_docker, requires_ssh, requires_network
  - Coverage configuration: ≥80% threshold, term-missing, --cov-report=html
  - Discovery patterns: test_*.py and *_test.py
  - Python warnings and doctest integration
- `tests/conftest.py` — expanded shared fixtures (150+ lines):
  - 7 new fixtures: temp_file, temp_dir, mock_env, monkeypatch_dict, capture_logs, benchmark_timer, project_root
  - Each fixture with docstring and practical examples
  - Scopes: function (default), module, session
  - Integration with existing fixtures
- `tests/test_example.py` — comprehensive test examples (320+ lines):
  - Demonstrates all testing patterns and best practices
  - Sections: Fixtures usage, Parametrization (pytest.mark.parametrize with 3+ cases), Mocking (unittest.mock, pytest-mock), Exception testing (pytest.raises with match), Markers (all 9 custom markers with examples), AAA pattern (Arrange-Act-Assert), Coverage edge cases, Integration tests, Performance/Benchmark tests
  - Real-world scenarios for each pattern
  - Comments explaining best practices
- `docs/TESTING_GUIDE.md` — complete testing guide (650+ lines):
  - 12 comprehensive sections
  - Quick Start: installation, basic commands, first test
  - Testing Philosophy: AAA pattern, test isolation, coverage goals
  - Test Organization: directory structure, naming conventions, test classes
  - Fixtures Deep Dive: built-in fixtures, custom fixtures, scopes, parametrization
  - Markers Explained: all 9 markers with usage examples and CLI commands
  - Mocking Strategies: unittest.mock vs pytest-mock, patching, side effects
  - Coverage Requirements: targets (≥80% overall, ≥90% critical, ≥95% utils), measurement, reports
  - Running Tests: 13 Makefile commands, pytest CLI, filtering, parallel execution
  - CI/CD Integration: GitHub Actions examples, status badges
  - Debugging Tests: pytest options (-vv, --pdb, --lf, --sw), logging
  - Best Practices: 12 guidelines (one assert per test, descriptive names, test data builders, avoid test interdependence)
  - Troubleshooting: 8 common issues with solutions
- `Makefile` — 13 new testing commands (90+ lines):
  - test: run all tests with coverage
  - test-unit / test-integration / test-smoke / test-security: filtered by marker
  - test-slow: only slow tests
  - test-fast: exclude slow tests
  - test-watch: continuous testing with pytest-watch
  - test-parallel: run tests in parallel with pytest-xdist
  - test-failed: rerun only failed tests (--lf)
  - coverage: detailed coverage report
  - coverage-html: generate HTML report and open in browser
  - benchmark: run performance tests
  - test-debug: run with --pdb for debugging
  - Each command with colored output, emojis, helpful messages
- `docs/INDEX.md` — added Testing Documentation section with 4 references

#### Sprint 1: Security P0 (ACTION_PLAN_TO_10 — Mar 2026)
- `.gitleaks.toml` — secret scanning configuration (60 lines):
  - 6 rule categories: generic-api-key, aws-access-key, private-key, password-in-url, vault-token, github-token
  - Entropy threshold: 3.5 for base64/hex detection
  - Path allowlist: tests/, docs/, .example files
  - Comprehensive regex patterns for secret detection
- `.pre-commit-config.yaml` — pre-commit hooks (70 lines):
  - 7 repos with multiple hooks: pre-commit-hooks (8 hooks: trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files 500KB, check-merge-conflict, check-case-conflict, mixed-line-ending, detect-private-key), gitleaks (secret scanning), shellcheck (shell script linting), black (Python formatting 88 chars), ruff (Python linting with security rules: S, flake8-bandit), mypy (type checking strict mode), bandit (Python security scanning)
  - Security focus: secret detection, large file prevention, security linting
  - Python 3.12+ compatibility
- `.github/workflows/security-scan.yml` — GitHub Actions security workflow (180 lines):
  - 7 security scanning jobs running in parallel
  - gitleaks-scan: Secret detection with gitleaks/gitleaks-action@v2, scans full history
  - dependency-check: Python Safety (pip-audit), Node.js audit (npm audit)
  - bandit-scan: Python security issues with bandit, SARIF output
  - checkov-scan: IaC security (Terraform, Docker, K8s) with bridgecrewio/checkov-action
  - trivy-scan: Container vulnerabilities with aquasecurity/trivy-action, CRITICAL/HIGH only
  - sast-codeql: Static analysis with github/codeql-action for Python/JavaScript
  - All jobs upload results to GitHub Security tab (SARIF format)
  - Triggers: push to main/develop, pull_request, schedule (weekly on Sundays 2 AM UTC)
- `docs/ANSIBLE_VAULT_GUIDE.md` — comprehensive Ansible Vault guide (600+ lines):
  - 8 major sections: What is Ansible Vault, When to Use, Quick Start, Encryption/Decryption, Editing Encrypted Files, Viewing Encrypted Files, Ansible Playbook Integration, Security Best Practices
  - 15 command examples with detailed explanations
  - Vault password management: file-based (.secrets/.vault_pass), environment variable, prompt
  - File permissions: chmod 600 for vault password files
  - Vault ID system: production, staging, development vaults
  - Rekeying procedures: rotating vault passwords
  - CI/CD integration: GitHub Actions secrets, GitLab CI variables
  - Security best practices: 12 guidelines (never commit unencrypted secrets, use .gitignore, rotate passwords quarterly, use vault IDs per environment, audit access logs)
  - Troubleshooting: 6 common issues with solutions
  - Real-world examples: encrypting group_vars, playbook execution with vault
- `docs/CREDENTIAL_ROTATION.md` — credential rotation procedures (500+ lines):
  - 6 major sections: Overview, Why Rotate, Rotation Schedule, Rotation Procedures, Automation, Compliance & Audit
  - Rotation schedules: Critical (quarterly), High (semi-annually), Medium (annually), Low (bi-annually)
  - 8 detailed rotation procedures: SSH keys, API tokens, Database passwords, Ansible Vault passwords, Cloud provider credentials (AWS/GCP/Azure), SSL/TLS certificates, Service account credentials, GitHub tokens
  - Each procedure: identification, generation, update, testing, revocation, verification (6 steps)
  - Automation section: scripts, tools (ansible-vault rekey, aws-vault, 1Password CLI), CI/CD integration
  - Compliance tracking: rotation log template, audit checklist, violation response
  - Emergency rotation: breach response, incident detection, forensics
- `pyproject.toml` — complete Python tooling configuration (140 lines):
  - Black: line-length=88, Python 3.12+, exclude patterns
  - Ruff: line-length=88, Python 3.12, 12 rule categories (E/F/I/N/D/UP/S/B/A/C4/SIM/RUF), ignore=["D203", "D213"], per-file-ignores for tests
  - MyPy: strict mode, Python 3.12, ignore missing imports, no implicit optionals
  - Bandit: exclude tests/docs, skips=["B101", "B601"]
  - isort: Black-compatible profile, known_first_party
  - pytest: markers, testpaths, python_files, addopts
  - coverage: source paths, omit patterns (tests, .venv, migrations), reporting
- `docs/INDEX.md` — added Security Documentation section with 5 references

### Changed
- `docs/INDEX.md` — restructured with 3 new sections: Security Documentation (5 items), Testing Documentation (4 items), Documentation Standards (3 items)

---

## [9.9.9] — 2026-03-14

---

## [9.9.9] — 2026-03-14

### Added

#### Validação de Profile Descriptors (IMP-32)
- `scripts/lib/validate.py` — módulo de validação de profile-descriptors:
  - `validate_descriptors(dir) → ValidationReport` — valida todos os `.yaml` em `profile-descriptors/`
  - 6 regras por descriptor: `name`, `description`, `version` (semver X.Y.Z), `last_tested`, `layer`, sintaxe YAML
  - Validação cruzada: nomes duplicados + `combines_with`/`excludes_with` com perfis inexistentes (warning)
  - Compatível com schema antigo (`VERSION`/`LAST_TESTED_DATE`) e novo (`version`/`last_tested`)
  - `combines_with` aceita lista de strings e lista de objetos `{name, notes}`
  - Exit code 0 se `valid=True` (erros=0; avisos são permitidos); exit code 1 se há erros
- `scripts/scaffold.py --validate` — flag CLI de validação; `--validate --json` para CI/automação
- `tests/test_smoke_imp32.py` — 42 testes (410 total)

#### CI/CD do Template (IMP-31)
- `.github/workflows/ci-template.yml` — workflow GitHub Actions completo com 3 jobs:
  - **test** — matrix Python 3.10 / 3.11 / 3.12 rodando `pytest tests/ --tb=short -q`
  - **cli-smoke** — `--list-profiles --json`, `--dry-run`, `--publish --json` contra código real
  - **lint** — `py_compile` em todos `scripts/lib/*.py` + `yaml.safe_load` em todos `profile-descriptors/*.yaml`
- Disparo em `pull_request` e `push` com filtro de paths (`scripts/**`, `tests/**`, `profile-descriptors/**`)
- `concurrency` com `cancel-in-progress: true` para PRs
- `tests/test_smoke_imp31.py` — 26 testes (368 total)

#### Release Publishing (IMP-30)
- `scripts/lib/publish.py` — módulo de publicação de release:
  - `publish_template(output_dir, project_root)` — gera `enterprise-template-v{version}-{YYYYMMDD}.tar.gz`
  - `_collect_files(project_root)` — coleta arquivos por padrões de inclusão, excluindo `__pycache__`, `.venv`, `.git`, `.secrets`, `dist`, `*.pyc`
  - Manifesto JSON (`release-manifest-v{version}-{YYYYMMDD}.json`) com `version`, `file_count`, `size_bytes`, `files`
  - Idempotente por data: chamadas múltiplas no mesmo dia sobrescrevem o tarball anterior
- `scripts/scaffold.py --publish` — flag CLI para gerar release tarball
- `scripts/scaffold.py --output-dir PATH` — diretório de saída configurável (default: `dist/`)
- `tests/test_smoke_imp30.py` — 35 testes (342 total)

#### Documentação por Perfil (IMP-29)
- `scripts/lib/templates.py` — `generate_profile_guide()` — gera `docs/PROFILE-GUIDE-{combo}.md` no projeto destino:
  - Tabela de perfis ativos com camada e descrição
  - Inventário de arquivos gerados por perfil (de `generates.files` / `templates`)
  - Requisitos de segurança consolidados (de `security.enforces`)
  - Quick Start com pré-requisitos e pré-requisitos agregados
  - Referências por stack (baseadas nas `tags` dos perfis)
  - Idempotente — não sobrescreve se já existe
- `_compute_combo_slug()` — slug derivado dos perfis layer2+ (exclui core e transversais)
- `_layer_order_int()` / `_layer_display_name()` — helpers de mapeamento de camada
- `scripts/scaffold.py` — integração: guia gerado após composição e após `--upgrade`
- `tests/test_smoke_imp29.py` — 33 testes (307 total)

---

## [1.3.0] — 2026-03-07

### Added

#### Infraestrutura e Composição (IMP-15, IMP-24)
- `scripts/lib/infra.py` — motor de geração de artefatos de infraestrutura:
  - `generate_ci_workflow()` — `.github/workflows/ci.yml` por linguagem (Python/uv, TypeScript/pnpm, Go)
  - `generate_dockerfile()` — Dockerfile multistage por linguagem (python:3.12-slim, node:20-slim/pnpm, golang:1.23-alpine+distroless)
  - `generate_docker_compose()` — `docker-compose.yml` com app + PostgreSQL/Redis comentados
  - `generate_runbook()` — `docs/RUNBOOK.md` template operacional
- `scripts/scaffold.py --infra` — nova flag para gerar artefatos de infra em CI
- `scripts/lib/composer.py` — Motor de Composição de Perfis:
  - `load_all_descriptors()` — carrega todos os `*.yaml` de `profile-descriptors/`
  - `resolve_order()` — ordena por camada (core → layer2 → layer3 → transversal)
  - `check_conflicts()` — detecta pares proibidos via `excludes_with`
  - `get_template_entries()` — normaliza Schema A (`templates_path`) e Schema B (`generates.files`)
  - `ProfileComposer.compose()` — copia templates com rollback em erro parcial
- `scripts/scaffold.py --compose PROFILES` — aplica perfis ao projeto alvo
- 21 novos testes (`test_smoke_infra.py`) + 18 novos testes (`test_smoke_composer.py`)

#### Governança (IMP-25)
- `docs/TEMPLATE-VERSIONS.md` — versionamento por perfil com histórico e convenções semver
- `docs/COMPATIBILITY-MATRIX.md` — matriz perfis × perfis com regras de composição
- `CHANGELOG.md` — este arquivo (histórico desde v0.1.0)
- `docs/DEPRECATION-POLICY.md` — política de depreciação com períodos de aviso e procedimento

#### Perfis Layer 2 (IMP-20, IMP-20b, IMP-21)
- `profile-descriptors/python-fastapi.yaml` — descriptor v1.0.0
- `profile-descriptors/python-flask.yaml` — descriptor v1.0.0
- `profile-descriptors/typescript-next.yaml` — descriptor v1.0.0
- `.github/prompts/domain/layer2-python-fastapi.prompt.md`
- `.github/prompts/domain/layer2-python-flask.prompt.md`
- `.github/prompts/domain/layer2-typescript-next.prompt.md`
- `.github/templates/python-fastapi/` — 11 arquivos (src, tests, pyproject.toml, Dockerfile, docker-compose.yml, Makefile, .env.example)
- `.github/templates/python-flask/` — 12 arquivos
- `.github/templates/typescript-next/` — 14 arquivos (app, lib, tests, tsconfig, jest, eslint, prettier, Dockerfile, docker-compose.yml, Makefile)

#### Profile Descriptor Schema (IMP-19a)
- `docs/copilot/PROFILE-DESCRIPTOR-SCHEMA.md` — schema 1.0.0 com todos os campos anotados
- `profile-descriptors/devops-programming.yaml` — descriptor do perfil core
- `profile-descriptors/README.md` — índice de perfis disponíveis

#### scaffold.py flags (IMP-19b)
- `--list-profiles` — tabela Rich ou JSON com perfis disponíveis
- `--dry-run` — manifesto de operações sem criar arquivos
- `--json` — output JSON para CI/automação
- `--config FILE` — configuração não-interativa via YAML

### Changed
- Suite de testes: 58 → 97 testes passando
- `profile-descriptors/README.md` — atualizado com typescript-next

---

## [1.2.0] — 2026-03-05

### Added

#### Testes (IMP-16)
- `tests/test_smoke.py` — 54 smoke tests: 9 combos domínio × linguagem × 2 funções × 3 assertions
- `tests/test_templates_snapshot.py` — 4 snapshot tests para `programming × python`
- `tests/conftest.py` — fixtures `make_project_config` e `update_snapshots`
- `tests/snapshots/` — baseline snapshots para CI

#### Scaffold Python (IMP-05, IMP-06, IMP-07, IMP-08, IMP-09)
- `scripts/scaffold.py` — script interativo com fluxo condicional
- `scripts/lib/config.py` — `ProjectConfig` dataclass, constantes, paths
- `scripts/lib/templates.py` — `generate_copilot_rules()`, `generate_copilot_instructions()`
- `scripts/lib/project.py` — `create_structure()`, `copy_speckit()`, `generate_constitution()`
- `scripts/lib/links.py` — `setup_symlinks()`, `check_symlinks()`
- `scripts/lib/git.py` — `init_repository()`
- `scripts/lib/vscode.py` — `generate_settings()`, `generate_mcp()`, `generate_extensions()`
- `scripts/lib/ui.py` — `collect_project_info()`, `show_banner()`, `show_menu()`

---

## [1.1.0] — 2026-02-28

### Added
- `.github/prompts/domain/devops-programming.prompt.md` — domain profile de programação
- `.github/prompts/domain/devops-infrastructure.prompt.md`
- `.github/prompts/domain/devops-analysis.prompt.md`
- `.github/prompts/domain/devops-security.prompt.md` — transversal
- `.github/prompts/session-start.prompt.md` — ritual de início de sessão
- `.github/prompts/session-end.prompt.md` — ritual de encerramento
- `.github/copilot-instructions.md` — instrução auto-injetada
- `.github/agents/template-architect.agent.md`
- `.specify/` — integração SpecKit

### Changed
- `.copilot-rules.md` consolidado (5 arquivos → 1 arquivo) — IMP-13

---

## [1.0.0] — 2026-01-27

### Added
- Estrutura inicial do template: `docs/`, `scripts/`, `Makefile`, `README.md`
- `Makefile` com 40+ targets: init, setup-python, setup-node, dev, build, test, lint, format, docker-*, status, clean
- `scripts/init-new-project.sh` — inicialização de projetos
- `scripts/setup-project-links.sh` — gestão de symlinks `.copilot-*`
- `scripts/check-project-links.sh` — verificação de symlinks
- `docs/INDEX.md`, `docs/TODO.md` — documentação incremental
- `scaffold-project.code-workspace` — workspace VS Code

---

[Unreleased]: https://github.com/yvesmarinho/scaffold-project/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/yvesmarinho/scaffold-project/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/yvesmarinho/scaffold-project/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/yvesmarinho/scaffold-project/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yvesmarinho/scaffold-project/releases/tag/v1.0.0
