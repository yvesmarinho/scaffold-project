# 🧪 Enterprise Scaffold Project Template - Test Suite

Bateria completa de testes para validação do Enterprise Scaffold Project Template.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Estrutura de Testes](#estrutura-de-testes)
- [Execução Rápida](#execução-rápida)
- [Testes por Categoria](#testes-por-categoria)
- [Coverage](#coverage)
- [CI/CD Integration](#cicd-integration)

---

## 🎯 Visão Geral

Esta suite de testes valida:
- ✅ **Core Features**: Scaffold, Git validators, GitHub templates
- ✅ **Integration**: Session management, security, structural
- ✅ **Smoke Tests**: Validação rápida de componentes críticos
- ✅ **Mergers**: JSON, YAML, Copilot rules, workflows
- ✅ **Objetivo & Spec**: Parsers, validators, wizards
- ✅ **Memory**: Context, save, search, security

**Total**: 80+ arquivos de teste | 500+ casos de teste

---

## 🚀 Execução Rápida

### Rodar TODOS os testes

```bash
# Básico
./tests/run_all_tests.sh

# Com coverage
./tests/run_all_tests.sh --coverage

# Modo verbose
./tests/run_all_tests.sh --verbose

# Paralelo (mais rápido)
./tests/run_all_tests.sh --parallel
```

### Rodar apenas testes P2 (GitHub Best Practices)

```bash
# Básico
./tests/run_p2_tests.sh

# Com coverage
./tests/run_p2_tests.sh --coverage

# Verbose
./tests/run_p2_tests.sh --verbose
```

### Rodar apenas smoke tests (rápido)

```bash
pytest tests/ -m smoke -v
```

### Rodar teste específico

```bash
# Arquivo completo
pytest tests/test_github_best_practices_p2.py -v

# Função específica
pytest tests/test_github_best_practices_p2.py::test_copy_github_templates_copies_all_p1_files -v

# Com output detalhado
pytest tests/test_github_best_practices_p2.py::test_workflow_has_five_jobs -vv -s
```

---

## 📂 Estrutura de Testes

### Por Categoria

```
tests/
├── 🔧 Core Features
│   ├── test_git_validators.py              # Validação Git (42 testes)
│   ├── test_github_best_practices_p2.py    # GitHub templates P1+P2 (35+ testes)
│   ├── test_scaffold_*.py                  # Sistema de scaffold
│   └── test_new_project_script.sh          # Script de novo projeto
│
├── 🔗 Integration
│   ├── test_integration_security.py        # Testes de segurança
│   ├── test_integration_structural.py      # Validação estrutural
│   ├── test_session_integration.py         # Integração de sessões
│   └── test_bug*.py                        # Regression tests
│
├── 💨 Smoke Tests
│   ├── test_smoke.py                       # Smoke geral
│   ├── test_smoke_imp*.py                  # Por implementação
│   ├── test_smoke_composer.py              # Composer
│   ├── test_smoke_k8s_helm.py              # Kubernetes Helm
│   └── test_smoke_terraform_aws.py         # Terraform AWS
│
├── 🎯 Objetivo & Spec
│   ├── test_objetivo_parser.py             # Parser de objetivo.yaml
│   ├── test_objetivo_validator.py          # Validador
│   ├── test_objetivo_wizard*.py            # Wizard interativo
│   ├── test_spec_validation.py             # Validação de specs
│   └── test_sprint*.py                     # Sprints
│
├── 🔄 Mergers
│   ├── test_json_merge*.py                 # Merge JSON universal
│   ├── test_copilot_*_merger.py            # Copilot files
│   ├── test_github_workflow_merger.py      # GitHub Actions
│   ├── test_issue_template_merge.py        # Issue templates
│   ├── test_pyproject_merger.py            # pyproject.toml
│   └── test_precommit_merge.py             # Pre-commit config
│
├── 🧠 Memory & Session
│   ├── test_memory_*.py                    # Sistema de memória
│   ├── test_session_*.py                   # Tracking de sessões
│   └── test_chat_capture.py               # Captura de conversas
│
├── 📝 Templates
│   ├── test_template_*.py                  # Template system
│   └── test_templates_snapshot.py          # Snapshot testing
│
└── 🛠️ Test Utilities
    ├── conftest.py                         # Pytest fixtures
    ├── run_all_tests.sh                    # Bateria completa ✨
    ├── run_p2_tests.sh                     # Testes P2 ✨
    └── README.md                           # Este arquivo
```

---

## 🧪 Testes por Categoria

### 1. GitHub Best Practices P2 (NOVO)

```bash
# Todos os testes P2
pytest tests/test_github_best_practices_p2.py -v

# Apenas validação de templates
pytest tests/test_github_best_practices_p2.py -k "template" -v

# Apenas workflow
pytest tests/test_github_best_practices_p2.py -k "workflow" -v

# Apenas git hooks
pytest tests/test_github_best_practices_p2.py -k "hook" -v
```

**Cobertura**:
- ✅ 13 arquivos copiados (P1: 4 + P2: 9)
- ✅ Issue templates YAML válidos
- ✅ Workflow git-validation.yml (5 jobs)
- ✅ Pre-commit hook commit-msg
- ✅ Script setup-branch-protection.py
- ✅ Badge guide BADGES.md
- ✅ Variáveis template substituídas
- ✅ Permissões executáveis aplicadas

### 2. Git Validators

```bash
pytest tests/test_git_validators.py -v
```

**Cobertura**:
- ✅ Validação de branch names (42 testes)
- ✅ Validação de commit messages (Conventional Commits)
- ✅ Sugestões de correção
- ✅ Protected branches

### 3. Scaffold System (AUTOMATED - 100% Coverage)

```bash
# Todos os testes de scaffold
pytest tests/test_scaffold_*.py -v

# Apenas scaffold new (10 testes)
pytest tests/test_scaffold_new.py -v

# Apenas scaffold upgrade (11 testes)
pytest tests/test_scaffold_upgrade.py -v

# Teste crítico de 51 validações
pytest tests/test_scaffold_upgrade.py::test_scaffold_upgrade_all_validations -v
```

**Cobertura test_scaffold_new.py** (10 testes, 100%):
- ✅ test_scaffold_new_basic: Estrutura de diretórios, Git init
- ✅ test_scaffold_new_vscode_config: .vscode/settings.json, mcp.json
- ✅ test_scaffold_new_copilot_instructions: .github/copilot-instructions.md
- ✅ test_scaffold_new_critical_files: Validação com validate_critical_files()
- ✅ test_scaffold_new_scaffold_state: .scaffold-state.yaml metadata
- ✅ test_scaffold_new_git_initialized: .git/, commit inicial, branch master/main
- ✅ test_scaffold_new_combinations: Parametrizado 4 combos (domain×language)

**Cobertura test_scaffold_upgrade.py** (11 testes, 100%):
- ✅ test_scaffold_upgrade_basic: Execução básica, logs, backups
- ✅ test_scaffold_upgrade_all_validations: **CRÍTICO** — 11 suites, 51 validações
- ✅ test_scaffold_upgrade_bug20_mcp_http: BUG-20 MCP GitHub HTTP migration
- ✅ test_scaffold_upgrade_bug001_objetivo_init: BUG-001 fixes (docstyle, out-scope, logging)
- ✅ test_scaffold_upgrade_bug19_gitvalidators: BUG-19 git_validators.py + sanitize.py
- ✅ test_scaffold_upgrade_copilot_instructions: BUG-13 copilot-instructions.md
- ✅ test_scaffold_upgrade_merge_strategy: BUG-16 JSON/workspace merge
- ✅ test_scaffold_upgrade_session_memory_init: BUG-11 (session) + BUG-12 (memory)
- ✅ test_scaffold_upgrade_logs_created: Validação de logs
- ✅ test_scaffold_upgrade_idempotent: Upgrade 3× (idempotency test)
- ✅ test_scaffold_upgrade_no_old_sessions_folder: BUG-22 regression test

**Integração com validate_workspace_upgrade.py**:
- 11 suites de validação
- 51 checks totais (100% passing)
- Validações de BUG-20, BUG-001, BUG-11, BUG-12, BUG-13, BUG-16, BUG-17, BUG-18, BUG-19, arquivos críticos, logs

**CI/CD**: `.github/workflows/scaffold-tests.yml`
- 4 jobs: test-scaffold-new, test-scaffold-upgrade, test-scaffold-smoke, summary
- Matrix testing: Python 3.10, 3.11, 3.12
- Triggers: push, PR, schedule (Sundays 02:00 UTC)

### 4. Pre-Commit Hooks (IMP-65 P1)

```bash
# Todos os testes de hooks
pytest tests/test_precommit_validate_memory.py -v

# Teste específico de bloqueio
pytest tests/test_precommit_validate_memory.py::test_hook_blocks_test_files -v

# Teste de validação de frontmatter
pytest tests/test_precommit_validate_memory.py::test_hook_validates_frontmatter_invalid_category -v
```

**Cobertura** (10 testes, 100%):
- ✅ test_hook_blocks_test_files: Bloqueia __test-*.md em .memory/
- ✅ test_hook_blocks_auto_generated_title: Bloqueia __auto-generated-title.md
- ✅ test_hook_blocks_search_test_files: Bloqueia __search-test-*.md
- ✅ test_hook_validates_frontmatter_invalid_category: Rejeita categorias inválidas
- ✅ test_hook_validates_frontmatter_missing_closing: Rejeita frontmatter malformado
- ✅ test_hook_allows_valid_memory_file: Aceita arquivos válidos com frontmatter
- ✅ test_hook_allows_file_without_frontmatter: Aceita arquivos sem frontmatter (opcional)
- ✅ test_hook_skips_non_memory_files: Ignora arquivos fora de .memory/
- ✅ test_hook_allows_valid_categories: Valida 4 categorias válidas (project, team, sessions, user)
- ✅ test_hook_error_messages_helpful: Mensagens de erro incluem comandos de remediação

**Implementação**: `scripts/git-hooks/pre-commit` (~240 linhas)
**Instalação**: `make git-hooks-install`
**Manual test**: Stage um arquivo __test-*.md em .memory/ e tente commit

**Funcionalidades**:
- Bloqueia commits de test files (__test-*, __auto-generated-title, __search-test-*)
- Valida YAML frontmatter (categorias válidas: project, team, sessions, user)
- Exit code 1 se violações detectadas
- Mensagens úteis com comandos: `make memory-cleanup`, `conftest.py` fixtures

### 5. GitHub Actions: Dependency Check (IMP-65 P1)

```bash
# Todos os testes do dependency-check workflow
pytest tests/test_dependency_check_workflow.py -v

# Teste de workflow YAML
pytest tests/test_dependency_check_workflow.py::test_dependency_check_workflow_valid_yaml -v

# Testes de scripts helper
pytest tests/test_dependency_check_workflow.py::test_process_outdated_script_processes_json -v
pytest tests/test_dependency_check_workflow.py::test_process_audit_script_processes_json_with_vulns -v
```

**Cobertura** (17 testes, 100%):
- ✅ test_dependency_check_workflow_exists: Verifica existência do workflow
- ✅ test_dependency_check_workflow_valid_yaml: Valida sintaxe YAML
- ✅ test_dependency_check_workflow_has_schedule: Verifica schedule segundas 9h UTC
- ✅ test_dependency_check_workflow_has_manual_trigger: Verifica workflow_dispatch
- ✅ test_dependency_check_workflow_has_pr_trigger: Verifica trigger em PRs (dependency files)
- ✅ test_dependency_check_workflow_has_permissions: Verifica permissions (contents:read, issues:write)
- ✅ test_dependency_check_workflow_has_main_job: Verifica job check-dependencies
- ✅ test_dependency_check_workflow_has_steps: Verifica 6+ steps existem
- ✅ test_process_outdated_script_exists: Verifica script process_outdated.py
- ✅ test_process_outdated_script_executable: Verifica shebang do script
- ✅ test_process_outdated_script_processes_json: Testa processamento de JSON outdated
- ✅ test_process_audit_script_exists: Verifica script process_audit.py
- ✅ test_process_audit_script_executable: Verifica shebang do script
- ✅ test_process_audit_script_processes_json_no_vulns: Testa caso sem vulnerabilidades (exit 0)
- ✅ test_process_audit_script_processes_json_with_vulns: Testa caso com vulnerabilidades (exit 1)
- ✅ test_dependency_check_workflow_creates_artifacts: Verifica upload de artifacts
- ✅ test_dependency_check_workflow_creates_issues: Verifica criação de issues P0

**Implementação**:
- Workflow: `.github/workflows/dependency-check.yml` (~200 linhas)
- Helper scripts: `.github/scripts/process_outdated.py` (~30 linhas), `.github/scripts/process_audit.py` (~45 linhas)

**Trigger manual**:
```bash
gh workflow run dependency-check.yml
```

**Funcionalidades**:
- Schedule semanal: segundas 9h UTC (cron: '0 9 * * MON')
- pip-audit para CVE scanning (pip-audit --format=json)
- pip list --outdated para dependency freshness
- Artifacts upload (outdated.json, audit.json, retention: 30 dias)
- Criação automática de issues P0 se vulnerabilidades (labels: security, dependencies, P0, automated)
- GitHub step summary com markdown tables
- Trigger em PRs que modificam pyproject.toml, requirements*.txt

### 6. Integration Tests

```bash
pytest tests/test_integration_*.py -v
```

### 7. Smoke Tests (Rápidos)

```bash
# Todos smoke tests
pytest tests/test_smoke*.py -v

# Smoke específico
pytest tests/test_smoke_imp17.py -v  # Issue templates antigos
pytest tests/test_smoke_k8s_helm.py -v
pytest tests/test_smoke_terraform_aws.py -v
```

---

## 📊 Coverage

### Gerar coverage report

```bash
# Terminal + HTML
pytest tests/ --cov=scripts/lib --cov-report=term-missing --cov-report=html

# Apenas HTML
pytest tests/ --cov=scripts/lib --cov-report=html

# Ver report HTML
python -m http.server 8000 --directory htmlcov
# Acesse: http://localhost:8000
```

### Coverage por módulo

```bash
# Apenas lib/project.py
pytest tests/ --cov=scripts/lib/project --cov-report=term-missing

# Apenas lib/flows
pytest tests/ --cov=scripts/lib/flows --cov-report=term-missing

# Apenas git_validators
pytest tests/test_git_validators.py --cov=scripts/lib/git_validators --cov-report=term-missing
```

---

## ⚡ Testes Rápidos

### Quick Smoke Test

```bash
# Apenas smoke tests críticos (~2 min)
pytest tests/ -m smoke --tb=short

# Apenas P2 (~30s)
pytest tests/test_github_best_practices_p2.py -q

# Apenas validadores Git (~15s)
pytest tests/test_git_validators.py -q
```

### Failed First (Debugging)

```bash
# Rodar testes falhados primeiro
./tests/run_all_tests.sh --failed-first

# Ou direto com pytest
pytest tests/ --ff -v
```

### Stop on First Failure

```bash
pytest tests/ -x  # Para no primeiro erro
pytest tests/ -x -v --tb=short  # Com traceback curto
```

---

## 🔍 Debugging Tests

### Modo verbose detalhado

```bash
# Nível 1: -v
pytest tests/test_github_best_practices_p2.py -v

# Nível 2: -vv (muito detalhado)
pytest tests/test_github_best_practices_p2.py -vv

# Com print output
pytest tests/test_github_best_practices_p2.py -vv -s
```

### Rodar com pdb (debugger)

```bash
# Parar no primeiro erro
pytest tests/test_github_best_practices_p2.py --pdb

# Parar em falha
pytest tests/test_github_best_practices_p2.py -x --pdb
```

### Mostrar warnings

```bash
pytest tests/ -W all
```

---

## 🎯 Markers (Tags)

```bash
# Smoke tests
pytest tests/ -m smoke

# Integration tests
pytest tests/ -m integration

# Slow tests
pytest tests/ -m slow

# Skip slow
pytest tests/ -m "not slow"
```

Para listar todos markers disponíveis:

```bash
pytest --markers
```

---

## 🔧 Fixtures Disponíveis

Ver `tests/conftest.py` para todas fixtures:

- `make_project_config`: Factory para ProjectConfig
- `temp_file`: Criar arquivos temporários
- `mock_env`: Mock de variáveis de ambiente
- `capture_logs`: Capturar logs
- `mock_subprocess`: Mock de subprocess calls
- `benchmark_timer`: Medir performance

**Exemplo de uso**:

```python
def test_example(make_project_config):
    cfg = make_project_config("programming", "python")
    assert cfg.domain == "programming"
```

---

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          ./tests/run_all_tests.sh --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/test_git_validators.py tests/test_github_best_practices_p2.py -q
```

---

## 📈 Estatísticas de Testes

| Categoria | Arquivos | Testes | Tempo Médio |
|-----------|----------|--------|-------------|
| Git Validators | 1 | 42 | ~5s |
| GitHub P2 | 1 | 35+ | ~10s |
| Scaffold | 8 | 80+ | ~30s |
| Integration | 6 | 50+ | ~20s |
| Smoke | 20+ | 150+ | ~60s |
| Mergers | 10+ | 100+ | ~40s |
| Objetivo | 8 | 70+ | ~25s |
| **TOTAL** | **80+** | **500+** | **~5min** |

---

## 🛠️ Troubleshooting

### "ModuleNotFoundError: No module named 'lib'"

```bash
# Adicione ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/scripts"
pytest tests/
```

Ou use os scripts `run_*.sh` que já configuram o ambiente.

### "Permission denied" nos scripts

```bash
chmod +x tests/run_all_tests.sh
chmod +x tests/run_p2_tests.sh
```

### Testes de permissões executáveis falhando

```bash
# No template-base, aplicar permissões
chmod +x scripts/git-hooks/commit-msg
chmod +x scripts/setup-branch-protection.py
```

---

## 📚 Referências

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest markers](https://docs.pytest.org/en/stable/example/markers.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions Testing](https://docs.github.com/en/actions/automating-builds-and-tests)

---

## ✨ Quick Commands Cheatsheet

```bash
# Rodar tudo
./tests/run_all_tests.sh

# Apenas P2
./tests/run_p2_tests.sh

# Com coverage
./tests/run_all_tests.sh --coverage

# Smoke rápido
pytest tests/ -m smoke -q

# Debug teste específico
pytest tests/test_github_best_practices_p2.py::test_workflow_has_five_jobs -vv -s

# Paralelo (rápido)
./tests/run_all_tests.sh --parallel

# Failed first
./tests/run_all_tests.sh --failed-first
```

---

**Última Atualização**: 2026-05-17 (P2 Complete)
**Versão**: 1.6.0
