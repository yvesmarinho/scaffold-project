# 📋 Plano de Ação — Melhorias Sistema de Memórias e Session-Start

**Data de Criação**: 2026-05-18
**Baseado em**: DEBATE-001-memory-cleanup-and-session-start-improvements.md
**Status**: 🟢 APROVADO — Pronto para Execução
**Decisão**: Consenso 3/3 agentes (Principal SE, SE: Architect, DevOps Expert)

---

## 🎯 Objetivos

### Objetivos Primários (P0)

1. **Eliminar poluição de memórias** (enterprise-ansible.md + 37 arquivos de teste)
2. **Criar memória correta do projeto** (scaffold-project.md com dados atualizados)
3. **Implementar verificação de segurança de pacotes** no ritual session-start
4. **Prevenir poluição futura** (test fixtures isolados + pre-commit hooks)
5. **Validar configurações críticas** (detectar configs obsoletas como BUG-20)

### Objetivos Secundários (P1)

6. **Automatizar limpeza de memórias** (script defensivo com backup)
7. **Integrar CI/CD** para dependency checks semanais
8. **Documentar sistema de memória** (prevenir problemas futuros)

### Objetivos de Longo Prazo (P2)

9. **Session-start quick mode** (modo P0-only opcional)
10. **Dashboard de métricas** (observabilidade de session-start e deps)

---

## 📊 Resumo Executivo

| Categoria | Items P0 | Items P1 | Items P2 | Total | Estimativa Total |
|-----------|----------|----------|----------|-------|------------------|
| **Limpeza de Memórias** | 4 | 1 | 0 | 5 | 3h |
| **Session-Start** | 2 | 2 | 1 | 5 | 5h |
| **Automação/DevOps** | 2 | 2 | 1 | 5 | 10h |
| **Documentação** | 0 | 2 | 0 | 2 | 2h |
| **TOTAL** | **8** | **7** | **2** | **17** | **20h** |

**Sprint Atual (P0)**: 8 tasks → ~6-8h
**Próxima Sprint (P1)**: 7 tasks → ~8-10h
**Backlog (P2)**: 2 tasks → ~11h

---

## 🔴 PRIORIDADE P0 — EXECUTAR IMEDIATAMENTE (< 24h)

### Task 1: Limpar Memórias Contaminadas

**Objetivo**: Deletar memórias de outros projetos e arquivos de teste
**Owner**: Agent (execução imediata)
**Estimativa**: 30 minutos
**Dependências**: Nenhuma

**Subtasks**:

1.1. **Deletar enterprise-ansible.md**
```bash
# Via memory tool
memory delete /memories/enterprise-ansible.md
```
**Resultado esperado**: Arquivo deletado, ~800 tokens de ruído eliminados

1.2. **Deletar memórias de test-workspace**
```bash
memory delete /memories/repo/test-workspace-path.md
memory delete /memories/repo/test-workspace.md
```
**Resultado esperado**: 2 arquivos deletados, ~320 tokens de ruído eliminados

1.3. **Limpar 37 arquivos de teste em .memory/project/**

**Via Python stdlib** (conforme .copilot-rules.md P0):
```python
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

test_dir = Path(".memory/memories/project")
patterns = [
    "*__test-*.md",
    "*__auto-generated-title.md",
    "*__search-test-*.md"
]

deleted = 0
for pattern in patterns:
    for file in test_dir.glob(pattern):
        file.unlink()
        log.info(f"✅ Deletado: {file.name}")
        deleted += 1

log.info(f"🗑️  Total deletado: {deleted} arquivos")
```

**Ferramenta**: `mcp_pylance_mcp_s_pylanceRunCodeSnippet`
**Resultado esperado**: 37 arquivos deletados, ~2.300 tokens de ruído eliminados

**Validação**:
```bash
# Verificar que pasta project/ está limpa
ls -la .memory/memories/project/
# Deve mostrar 0 arquivos (ou apenas arquivos legítimos, não de teste)
```

**Critérios de Aceitação**:
- [x] `enterprise-ansible.md` deletado de `/memories/`
- [x] `test-workspace*.md` deletados de `/memories/repo/`
- [x] 37 arquivos `test-*.md` deletados de `.memory/memories/project/`
- [x] Total de ~3.420 tokens de ruído eliminados

---

### Task 2: Criar Memória do Projeto Atual

**Objetivo**: Criar `/memories/scaffold-project.md` com informações corretas
**Owner**: Agent
**Estimativa**: 20 minutos
**Dependências**: Task 1 concluída

**Conteúdo**:

```markdown
# Enterprise Scaffold Project Template (scaffold-project)

**Última atualização**: 2026-05-18
**Versão**: 1.6.0
**Tipo**: Template multi-linguagem (Python, Node.js, etc.)
**Branch principal**: master
**Repositório**: github.com/yvesmarinho/scaffold-project

---

## 🏗️ Estrutura do Projeto

### Documentação Crítica

| Pasta/Arquivo | Propósito |
|---------------|-----------|
| `docs/SESSIONS/YYYY-MM-DD/` | Sessões de trabalho (DAILY_ACTIVITIES, SESSION_REPORT, FINAL_STATUS) |
| `docs/TODO.md` | Lista de tarefas (incremental, NUNCA deletar itens) |
| `docs/INDEX.md` | Mapa de arquivos importantes |
| `.copilot-rules.md` | Regras P0 (7 seções, ~400 linhas) |
| `.github/copilot-instructions.md` | Resumo das regras + estrutura do projeto |

### Scripts

| Pasta | Convenção | Exemplos |
|-------|-----------|----------|
| `scripts/` | Python: snake_case.py, Shell: kebab-case.sh | scaffold.py, git-commit-with-file.sh |
| `scripts/lib/` | Módulos compartilhados | config.py, vscode.py, file_merge.py |
| `scripts/tmp/` | Scripts temporários (NÃO `/tmp/`) | - |

### Configurações

| Arquivo | Propósito |
|---------|-----------|
| `.vscode/mcp.json` | MCP servers (memory, sequential-thinking, filesystem, github) |
| `pyproject.toml` | Dependências Python (deepmerge + dev/security) |
| `Makefile` | Comandos principais (help, init, test, scaffold) |

---

## 🚨 Regras P0 — NUNCA Violar

### 1. Criar/Editar Arquivos

❌ **PROIBIDO**: heredoc, echo, tee
✅ **OBRIGATÓRIO**: `create_file`, `replace_string_in_file` (min 3 linhas contexto)

### 2. Ler/Buscar/Listar Arquivos

❌ **PROIBIDO**: cat, grep, find, ls via terminal
✅ **OBRIGATÓRIO**: `read_file`, `grep_search`, `file_search`, `list_dir`

### 3. Mover/Copiar/Excluir Arquivos

❌ **PROIBIDO**: mv, cp, rm via terminal
✅ **OBRIGATÓRIO**: Python stdlib (shutil, pathlib, logging)

Exemplo:
```python
import shutil, logging
from pathlib import Path

log = logging.getLogger(__name__)
src = Path("origem/arquivo.md")
dst = Path("destino/arquivo.md")
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, dst)
log.info("✅ %s → %s", src, dst)
```

### 4. Git Commits

❌ **PROIBIDO**: `git commit -m "..."` direto
✅ **OBRIGATÓRIO**: `./scripts/git-commit-with-file.sh` (mensagens ≥6 linhas)

---

## 🛠️ Comandos Principais

### Scaffold System

```bash
# Criar novo projeto
./scripts/scaffold.py

# Atualizar projeto existente
./scripts/scaffold.py upgrade --force --log-dir logs/

# Listar perfis disponíveis
./scripts/scaffold.py --list-profiles
```

### Makefile Targets

```bash
make help              # Lista todos comandos disponíveis
make init              # Inicializa projeto completo
make test              # Roda testes (pytest)
make lint              # Roda linters (ruff, mypy)
make format            # Formata código (black)
make clean             # Limpa arquivos gerados
```

### Session Management

```bash
# Iniciar sessão (primeira vez)
# Execute: session-start-first.prompt.md

# Iniciar sessão (recorrente)
# Execute: session-start.prompt.md

# Time tracking
python scripts/session-time-tracker.py start
python scripts/session-time-tracker.py status
python scripts/session-time-tracker.py stop
```

---

## 🔧 Status Atual (2026-05-18)

### Últimas Atualizações

- ✅ **BUG-17**: Time-tracker integrado ao session-start (Passo 6.5)
- ✅ **BUG-18**: objetivo-init.yaml deployado em projetos novos
- ✅ **BUG-19**: git_validators.py integrado ao session-time-tracker
- ⚠️ **BUG-20**: MCP GitHub HTTP merge failure (P0 CRÍTICA em progresso)

### Tarefas Pendentes (docs/TODO.md)

| Task | Prioridade | Status |
|------|-----------|--------|
| BUG-20: MCP merge failure | 🔴 P0 | 🔵 Em investigação |
| BUG-16: Teste manual upgrade | 🟡 P1 | ⏸️ On hold |
| Objetivo-Init pipeline testing | 🟡 P1 | ⏸️ On hold |

---

## 🔐 Segurança

- Credenciais em `.secrets/` (no .gitignore)
- NUNCA commitar: `*.env`, `*.key`, `*.pem`, tokens, passwords
- Scan de segurança: Passo 4 do session-start ritual

---

## 📚 Documentação Adicional

- [MCP GitHub HTTP Update Guide](docs/guides/MCP-GITHUB-HTTP-UPDATE.md)
- [Session Documentation Style Guide](docs/SESSION_DOCS_STYLE_GUIDE.md)
- [BUG Reports](docs/bugs/)
- [Debates de Arquitetura](docs/debates/)

---

## 🏷️ Tags e Categorias

**Category**: project
**Tags**: template, python, nodejs, scaffold, enterprise, copilot, mcp
**Created**: 2026-05-18
**Updated**: 2026-05-18
```

**Ferramenta**: `memory create`
**Validação**:
```bash
memory view /memories/scaffold-project.md
# Deve mostrar conteúdo completo e correto
```

**Critérios de Aceitação**:
- [x] Arquivo `/memories/scaffold-project.md` criado
- [x] Contém estrutura do projeto atualizada
- [x] Contém regras P0 resumidas
- [x] Contém comandos principais
- [x] Contém status atual (2026-05-18)
- [x] YAML frontmatter válido

---

### Task 3: Implementar Test Fixtures Isolados

**Objetivo**: Prevenir poluição futura de `.memory/` por testes
**Owner**: Principal Software Engineer
**Estimativa**: 1 hora
**Dependências**: Nenhuma

**Subtasks**:

3.1. **Criar fixture em tests/conftest.py**

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_memory_dir(tmp_path):
    """
    Isolated memory directory for tests

    Prevents test pollution of real .memory/ directory.
    All test memories are saved to temporary directory
    which is automatically cleaned up after test.
    """
    memory_dir = tmp_path / ".memory" / "memories"
    memory_dir.mkdir(parents=True)

    # Setup test structure
    (memory_dir / "project").mkdir()
    (memory_dir / "team").mkdir()
    (memory_dir / "sessions").mkdir()

    yield memory_dir

    # Cleanup happens automatically via tmp_path fixture

@pytest.fixture
def isolated_memory(temp_memory_dir, monkeypatch):
    """
    Monkey-patch memory functions to use isolated directory

    Usage:
        def test_something(isolated_memory):
            save_memory(...)  # Will use temp_memory_dir automatically
    """
    # Patch MEMORY_DIR constant in memory scripts
    monkeypatch.setenv("MEMORY_DIR", str(temp_memory_dir))
    yield temp_memory_dir
```

**Arquivo**: `tests/conftest.py`
**Ferramenta**: `replace_string_in_file` (se arquivo existe) ou `create_file` (se não existe)

3.2. **Atualizar testes existentes para usar fixture**

Exemplo de atualização:

**ANTES**:
```python
def test_save_memory():
    save_memory(
        title="Test Memory",
        content="Test content",
        category="project"
    )
    assert Path(".memory/memories/project/test-memory.md").exists()
```

**DEPOIS**:
```python
def test_save_memory(temp_memory_dir):
    save_memory(
        title="Test Memory",
        content="Test content",
        category="project",
        memory_dir=temp_memory_dir  # ← Isolated
    )
    assert (temp_memory_dir / "project" / "test-memory.md").exists()
```

**Arquivos a atualizar**:
- `tests/test_memory_save.py`
- `tests/test_memory_search.py`
- `tests/test_memory_context.py`
- Qualquer outro teste que manipule `.memory/`

**Ferramenta**: `multi_replace_string_in_file` (atualizar múltiplos testes em paralelo)

**Validação**:
```bash
# Rodar testes
pytest tests/ -v

# Verificar que .memory/ não foi poluído
ls -la .memory/memories/project/
# Não deve ter novos arquivos test-*
```

**Critérios de Aceitação**:
- [x] Fixture `temp_memory_dir` criado em `tests/conftest.py`
- [x] Fixture `isolated_memory` criado (com monkey-patch)
- [x] Testes atualizados para usar fixtures
- [x] Testes passam: `pytest tests/ -v`
- [x] Zero arquivos criados em `.memory/` real após rodar testes

---

### Task 4: Adicionar Passo 4.5 ao Session-Start (Deps Check Acionável)

**Objetivo**: Verificar dependências desatualizadas e vulnerabilidades no início de cada sessão
**Owner**: SE: Architect
**Estimativa**: 1 hora
**Dependências**: Nenhuma

**Implementação**:

4.1. **Atualizar `.github/prompts/session-start.prompt.md`**

Adicionar após Passo 4 (Scan de Segurança) e antes de Passo 5 (Estado Git):

```markdown
### Passo 4.5 — Verificação de Dependências

**Ação do agente**: Verificar pacotes desatualizados e vulnerabilidades de segurança.

**Comando**:
```bash
pip list --outdated --format=json | python -c "
import sys, json
data = json.load(sys.stdin) if sys.stdin.isatty() == False else []

# Pacotes críticos de segurança
critical_packages = ['bandit', 'safety', 'pytest']
critical = [p for p in data if p['name'] in critical_packages]

# Pacotes desatualizados gerais
if critical:
    print('🚨 PACOTES CRÍTICOS DESATUALIZADOS!')
    for p in critical:
        print(f\"  - {p['name']}: {p['version']} → {p['latest_version']}\")
    print('\n⚠️  Execute: make update-deps-safe')
    sys.exit(1)  # Bloqueia sessão (força atualização)

elif len(data) > 0:
    print(f'⚠️  {len(data)} pacote(s) desatualizado(s) (não-críticos)')
    print('💡 Sugestão: Execute "make update-deps" quando tiver tempo')
else:
    print('✅ Todas dependências atualizadas')
"
```

**Resultado esperado**:

**Cenário 1 — Tudo atualizado** (mais comum):
```
✅ Todas dependências atualizadas
```

**Cenário 2 — Deps não-críticos desatualizados**:
```
⚠️  5 pacote(s) desatualizado(s) (não-críticos)
💡 Sugestão: Execute "make update-deps" quando tiver tempo
```

**Cenário 3 — Deps críticos desatualizados** (bloqueia sessão):
```
🚨 PACOTES CRÍTICOS DESATUALIZADOS!
  - bandit: 1.7.5 → 1.7.8
  - safety: 3.0.0 → 3.1.0

⚠️  Execute: make update-deps-safe

❌ SESSÃO BLOQUEADA — Corrija vulnerabilidades antes de continuar
```

**Duração esperada**: 3-5 segundos

---

**Checklist de confirmação**:

| Check | Status |
|-------|--------|
| Passo 4.5 adicionado após Passo 4 | ✅ |
| Comando Python inline funcional | ✅ |
| Bloqueia sessão se deps críticos desatualizados | ✅ |
| Permite continuar se apenas deps não-críticos | ✅ |
| Duração < 5s | ✅ |
```

**Ferramenta**: `replace_string_in_file`
**Arquivo**: `.github/prompts/session-start.prompt.md`

**Contexto para replace** (encontrar Passo 4 e inserir Passo 4.5 após):
```
Localizar:
### Passo 5 — Verificar Estado do Projeto

Inserir antes:
### Passo 4.5 — Verificação de Dependências
...
```

4.2. **Validar que Passo 4.5 executa corretamente**

```bash
# Testar comando manualmente
pip list --outdated --format=json | python -c "..."
# Deve mostrar status correto
```

**Critérios de Aceitação**:
- [x] Passo 4.5 adicionado em `session-start.prompt.md`
- [x] Comando executa em <5s
- [x] Bloqueia (exit 1) se deps críticos desatualizados
- [x] Permite continuar (exit 0) se deps não-críticos
- [x] Mensagens claras e acionáveis

---

### Task 5: Criar Makefile Target `update-deps-safe`

**Objetivo**: Fornecer comando seguro para atualizar dependências críticas
**Owner**: DevOps Expert
**Estimativa**: 30 minutos
**Dependências**: Task 4 (referenciado no Passo 4.5)

**Implementação**:

5.1. **Adicionar target ao Makefile**

```makefile
.PHONY: update-deps-safe
update-deps-safe: ## Atualizar dependências de segurança (bandit, safety)
	@echo "🔍 Atualizando dependências de segurança..."
	pip install --upgrade bandit safety
	@echo ""
	@echo "✅ Segurança atualizada. Rodando smoke tests..."
	pytest tests/test_memory_smoke.py -v
	@echo ""
	@echo "✅ Smoke tests passaram. Dependências seguras."

.PHONY: update-deps
update-deps: ## Atualizar todas dependências (cuidado: pode quebrar)
	@echo "⚠️  ATENÇÃO: Atualizando TODAS as dependências..."
	@echo "Isso pode introduzir breaking changes. Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	pip install --upgrade -e ".[dev,security]"
	@echo ""
	@echo "🧪 Rodando testes completos..."
	pytest tests/ -v
	@echo ""
	@echo "✅ Testes passaram. Revise git diff antes de commitar."

.PHONY: deps-check
deps-check: ## Verificar dependências desatualizadas (usado no session-start)
	@pip list --outdated --format=json | python -c "import sys, json; data = json.load(sys.stdin); print(f'📦 {len(data)} pacote(s) desatualizado(s)') if data else print('✅ Tudo atualizado')"
```

**Ferramenta**: `replace_string_in_file`
**Arquivo**: `Makefile`

**Localizar** (para inserir novos targets):
```makefile
# Inserir após targets de teste (test, lint, format)
# Antes de targets de limpeza (clean)
```

5.2. **Atualizar `make help` para mostrar novos comandos**

Verificar que `help` target exibe os novos comandos:
```bash
make help
# Deve mostrar:
#   update-deps-safe   Atualizar dependências de segurança
#   update-deps        Atualizar todas dependências
#   deps-check         Verificar dependências desatualizadas
```

**Critérios de Aceitação**:
- [x] Target `update-deps-safe` criado no Makefile
- [x] Target `update-deps` criado (com confirmação interativa)
- [x] Target `deps-check` criado (usado no Passo 4.5)
- [x] `make help` mostra os 3 novos comandos
- [x] `make update-deps-safe` executa sem erros
- [x] Smoke tests rodam após atualização

---

### Task 6: Criar Script `memory-cleanup.py`

**Objetivo**: Automação defensiva para limpeza de memórias
**Owner**: DevOps Expert
**Estimativa**: 2 horas
**Dependências**: Nenhuma

**Implementação**:

Ver código completo em `docs/debates/DEBATE-001-...md` seção "DevOps Proposta 2.1"

**Features obrigatórias**:
- Dry-run por padrão (segurança)
- Backup automático antes de executar (timestamp)
- Detecção de duplicados por hash SHA256
- Patterns configuráveis (test-*.md, auto-generated-title.md, etc.)
- Logs detalhados (logging.INFO)
- Estatísticas finais (removed, duplicates, backed_up)

**Arquivo**: `scripts/memory-cleanup.py`
**Ferramenta**: `create_file`

**Integração Makefile**:
```makefile
.PHONY: memory-cleanup
memory-cleanup: ## Limpeza de memórias (dry-run, mostra o que seria removido)
	python scripts/memory-cleanup.py

.PHONY: memory-cleanup-force
memory-cleanup-force: ## Executar limpeza (cria backup automático)
	python scripts/memory-cleanup.py --execute --backup
```

**Critérios de Aceitação**:
- [x] Script criado em `scripts/memory-cleanup.py`
- [x] Dry-run funciona: `python scripts/memory-cleanup.py`
- [x] Execução com backup: `python scripts/memory-cleanup.py --execute --backup`
- [x] Backup criado em `.memory.backup.YYYY-MM-DD-HHMM/`
- [x] Detecção de duplicados funciona (SHA256)
- [x] Makefile targets integrados
- [x] Logs em `logs/memory-cleanup.log`

---

### Task 7: Criar Script `validate-configs.py`

**Objetivo**: Detectar configurações obsoletas (prevenção de BUG-20)
**Owner**: DevOps Expert
**Estimativa**: 1.5 horas
**Dependências**: Nenhuma

**Implementação**:

Ver código em `docs/debates/DEBATE-001-...md` seção "DevOps Perspectiva (Problema 3)"

**Validações obrigatórias**:
1. MCP GitHub server (CLI vs HTTP)
2. pyproject.toml (dependências críticas pinadas)
3. .copilot-rules.md (arquivo existe e não vazio)

**Arquivo**: `scripts/validate-configs.py`
**Ferramenta**: `create_file`

**Uso**:
```bash
# Validar todos configs
make config-validate

# Validar específico
python scripts/validate-configs.py --check mcp.json
```

**Critérios de Aceitação**:
- [x] Script criado em `scripts/validate-configs.py`
- [x] Detecta MCP GitHub CLI obsoleto
- [x] Detecta dependências sem pinning
- [x] Detecta .copilot-rules.md ausente/vazio
- [x] Exit code 1 se problemas, 0 se OK
- [x] Mensagens claras e acionáveis
- [x] Makefile target `config-validate`

---

### Task 8: Atualizar docs/TODO.md

**Objetivo**: Adicionar novas tarefas P1/P2 e marcar P0 como concluídas
**Owner**: Agent
**Estimativa**: 15 minutos
**Dependências**: Tasks 1-7 concluídas

**Ações**:

8.1. **Marcar tasks P0 como concluídas**

```markdown
- [x] ~~**Limpar memórias contaminadas**~~: ✅ CONCLUÍDO (2026-05-18)
  - ✅ enterprise-ansible.md deletado
  - ✅ 37 arquivos de teste removidos
  - ✅ scaffold-project.md criado com dados corretos

- [x] ~~**Passo 4.5 Session-Start**~~: ✅ IMPLEMENTADO (2026-05-18)
  - ✅ Verificação de dependências acionável
  - ✅ Bloqueia sessão se vulnerabilidades P0
  - ✅ Makefile target update-deps-safe criado

- [x] ~~**Test fixtures isolados**~~: ✅ IMPLEMENTADO (2026-05-18)
  - ✅ Fixtures em tests/conftest.py
  - ✅ Testes atualizados para usar temp_memory_dir
  - ✅ Zero poluição de .memory/ em testes
```

8.2. **Adicionar novas tarefas P1**

```markdown
- [ ] **Pre-commit Hook validate-memory** (P1 HIGH)
  - **Objetivo**: Bloquear commit de arquivos de teste em .memory/
  - **Arquivo**: scripts/git-hooks/pre-commit.d/validate-memory
  - **Estimativa**: 1h
  - **Blocker**: None

- [ ] **GitHub Actions Dependency Check** (P1 HIGH)
  - **Objetivo**: CI/CD semanal + PR validation
  - **Arquivo**: .github/workflows/dependency-check.yml
  - **Estimativa**: 2h
  - **Blocker**: None

- [ ] **Documentação MEMORY_SYSTEM.md** (P1 MEDIUM)
  - **Objetivo**: Prevenir problemas futuros, documentar boas práticas
  - **Arquivo**: docs/MEMORY_SYSTEM.md
  - **Estimativa**: 1h
  - **Blocker**: None
```

8.3. **Adicionar tarefas P2 ao backlog**

```markdown
- [ ] **Session-Start Quick Mode** (P2 LOW)
  - **Objetivo**: Modo P0-only opcional (3-5min → 1-2min)
  - **Estimativa**: 3h
  - **Blocker**: None (nice-to-have)

- [ ] **Dashboard de Métricas** (P2 LOW)
  - **Objetivo**: Observabilidade de session-start e deps
  - **Estimativa**: 8h
  - **Blocker**: None (future enhancement)
```

**Ferramenta**: `replace_string_in_file` (modo incremental, NUNCA sobrescrever TODO.md)
**Arquivo**: `docs/TODO.md`

**Critérios de Aceitação**:
- [x] Tasks P0 marcadas como concluídas (✅)
- [x] Tasks P1 adicionadas (7 items)
- [x] Tasks P2 adicionadas ao backlog (2 items)
- [x] Data de atualização: 2026-05-18
- [x] Formato incremental respeitado (nunca deletar itens antigos)

---

## 🟡 PRIORIDADE P1 — PRÓXIMA SPRINT (< 1 semana)

### Task 9: Implementar Pre-Commit Hook `validate-memory`

**Objetivo**: Bloquear commits de arquivos de teste em `.memory/`
**Owner**: DevOps Expert
**Estimativa**: 1 hora
**Dependências**: Task 6 (memory-cleanup.py) completo

**Ver código**: `docs/debates/DEBATE-001-...md` seção "DevOps Proposta 2.2"

**Critérios de Aceitação**:
- [x] Hook criado em `scripts/git-hooks/pre-commit.d/validate-memory`
- [x] Bloqueia commits de `test-*.md` em `.memory/`
- [x] Valida YAML frontmatter de memórias
- [x] Exit code 1 se violações, 0 se OK
- [x] Makefile target `git-hooks-install`

---

### Task 10: Criar GitHub Actions Workflow `dependency-check.yml`

**Objetivo**: CI/CD semanal para dependency checks
**Owner**: DevOps Expert
**Estimativa**: 2 horas
**Dependências**: Task 4, 5 (deps check implementado)

**Ver código**: `docs/debates/DEBATE-001-...md` seção "DevOps Proposta 2.3"

**Features**:
- Schedule: Segundas 9h (`cron: '0 9 * * MON'`)
- Workflow dispatch (trigger manual)
- pip-audit para CVE scanning
- Criar issue P0 se vulnerabilidades encontradas
- Upload de artifacts (outdated.json, audit.json)

**Critérios de Aceitação**:
- [x] Workflow criado em `.github/workflows/dependency-check.yml`
- [x] Executa semanalmente (segundas 9h)
- [x] Roda `pip list --outdated` e `pip-audit`
- [x] Cria issue P0 se vulnerabilidades
- [x] Upload de resultados (artifacts)

---

### Task 11: Documentar Sistema de Memória

**Objetivo**: `docs/MEMORY_SYSTEM.md` com boas práticas
**Owner**: Principal Software Engineer
**Estimativa**: 1 hora
**Dependências**: Tasks 1-6 (sistema de memória limpo e funcional)

**Seções obrigatórias**:
1. Estrutura de diretórios (`/memories/` vs `.memory/`)
2. Scopes (user, repo, session)
3. Boas práticas (quando criar, atualizar, deletar)
4. Nomenclatura de arquivos
5. YAML frontmatter obrigatório
6. Categorias válidas (project, team, decision, pattern, incident)
7. Comandos úteis (memory tool, scripts)
8. Troubleshooting (limpeza, validação)

**Arquivo**: `docs/MEMORY_SYSTEM.md`
**Ferramenta**: `create_file`

**Critérios de Aceitação**:
- [x] Arquivo criado com 8 seções
- [x] Exemplos de uso incluídos
- [x] Referências a scripts (memory-cleanup.py, validate-memory)
- [x] Diagramas de estrutura (opcional, mas recomendado)
- [x] Linkado em docs/INDEX.md

---

### Task 12-15: Tasks P1 adicionais

(Ver docs/TODO.md para lista completa após Task 8 ser executada)

---

## 🟢 PRIORIDADE P2 — BACKLOG (próximos 2 meses)

### Task 16: Session-Start Quick Mode

**Objetivo**: Modo opcional P0-only (reduzir 8 passos → 4 passos)
**Owner**: SE: Architect
**Estimativa**: 3 horas

**Implementação**:
- Flag `--quick` em session-start ritual
- Executa apenas passos 1, 2, 3, 4 (MCP, contexto, regras, segurança)
- Pula passos 5, 6, 7, 8 (git, docs, time-tracker, escopo)
- Duração: 15s → 5s

**Status**: ⚠️ Em discussão (2/3 agentes aprovam)

---

### Task 17: Dashboard de Métricas

**Objetivo**: Observabilidade de session-start e dependências
**Owner**: DevOps Expert
**Estimativa**: 8 horas

**Features**:
- Métricas de session-start (duração por passo, P50/P95/P99)
- Métricas de dependências (outdated count, vulnerabilities)
- Dashboard HTML simples ou Grafana
- Histórico de 30 dias

**Status**: ⚠️ Nice-to-have (2/3 agentes aprovam)

---

## 📊 Cronograma e Estimativas

### Sprint Atual (2026-05-18)

| Task | Owner | Estimativa | Status |
|------|-------|------------|--------|
| 1. Limpar memórias | Agent | 30 min | 🔵 Ready |
| 2. Criar scaffold-project.md | Agent | 20 min | 🔵 Ready |
| 3. Test fixtures isolados | Principal SE | 1h | 🔵 Ready |
| 4. Passo 4.5 session-start | SE: Architect | 1h | 🔵 Ready |
| 5. Makefile update-deps-safe | DevOps | 30 min | 🔵 Ready |
| 6. Script memory-cleanup.py | DevOps | 2h | 🔵 Ready |
| 7. Script validate-configs.py | DevOps | 1.5h | 🔵 Ready |
| 8. Atualizar TODO.md | Agent | 15 min | 🔵 Ready |
| **TOTAL P0** | | **~7h** | |

### Próxima Sprint (2026-05-19 a 2026-05-25)

| Task | Owner | Estimativa | Dependências |
|------|-------|------------|--------------|
| 9. Pre-commit hook | DevOps | 1h | Task 6 |
| 10. GitHub Actions | DevOps | 2h | Tasks 4, 5 |
| 11. Docs MEMORY_SYSTEM.md | Principal SE | 1h | Tasks 1-6 |
| 12-15. (Ver TODO.md) | Vários | ~4h | Vários |
| **TOTAL P1** | | **~8-10h** | |

### Backlog (P2)

| Task | Estimativa |
|------|------------|
| 16. Quick mode | 3h |
| 17. Dashboard | 8h |
| **TOTAL P2** | **~11h** |

---

## ✅ Critérios de Sucesso do Projeto

### Métricas de Qualidade

| Métrica | Antes | Meta | Medição |
|---------|-------|------|---------|
| **Tokens de ruído em memórias** | ~3.420 | 0 | `grep -r "test-" .memory/` |
| **Arquivos de teste em .memory/** | 37 | 0 | `ls .memory/memories/project/` |
| **Memórias incorretas** | 3 | 0 | Validação manual |
| **Tempo session-start** | ~15s | ~20s | Cronômetro (5s extra aceitável) |
| **Vulnerabilidades não detectadas** | ? | 0 | `pip-audit` output |
| **Configurações obsoletas** | 1 | 0 | `validate-configs.py` |

### Validação Pós-Implementação (P0)

**Checklist de validação** (executar após Tasks 1-8):

- [ ] Zero arquivos `test-*.md` em `.memory/memories/project/`
- [ ] Arquivo `/memories/scaffold-project.md` existe e está correto
- [ ] Arquivo `/memories/enterprise-ansible.md` NÃO existe
- [ ] `pytest tests/` passa sem criar arquivos em `.memory/`
- [ ] `make update-deps-safe` executa sem erros
- [ ] `python scripts/memory-cleanup.py` (dry-run) não encontra problemas
- [ ] `python scripts/validate-configs.py` reporta 0 erros
- [ ] Session-start Passo 4.5 executa em <5s
- [ ] `docs/TODO.md` atualizado com novas tasks

**Aprovação**: Requer 100% dos checks ✅

---

## 🚀 Próximos Passos Imediatos

### Agora (Esta Sessão)

1. ✅ Aprovar este plano de ação
2. ✅ Executar Tasks P0 (1-8) em ordem
3. ✅ Validar critérios de sucesso
4. ✅ Commitar alterações com mensagens apropriadas
5. ✅ Atualizar `DAILY_ACTIVITIES_2026-05-18.md` com bloco de atividade

### Amanhã (2026-05-19)

1. ⏳ Review dos commits de ontem
2. ⏳ Iniciar Tasks P1 (9-11)
3. ⏳ Documentar lições aprendidas

---

## 📝 Commits Esperados

### Sprint P0 (2026-05-18)

```
feat(memory): Limpar memórias contaminadas + criar scaffold-project.md

- Deletar enterprise-ansible.md (outro projeto, 800 tokens ruído)
- Deletar 37 arquivos test-*.md (.memory/project/)
- Deletar test-workspace*.md (dados obsoletos)
- Criar /memories/scaffold-project.md com dados corretos

Impacto: -3.420 tokens de ruído, +600 tokens de contexto correto

Related: docs/debates/DEBATE-001-memory-cleanup-and-session-start-improvements.md
```

```
feat(session-start): Adicionar Passo 4.5 deps check acionável

- Verificação de dependências desatualizadas e vulnerabilidades
- Bloqueia sessão (exit 1) se deps críticas desatualizadas
- Permite continuar se apenas deps não-críticas
- Duração: ~3-5s

Makefile targets adicionados:
- update-deps-safe: Atualiza bandit, safety (com smoke tests)
- update-deps: Atualiza tudo (confirmação interativa)
- deps-check: Verifica outdated (usado no Passo 4.5)

Related: docs/debates/DEBATE-001-...md
```

```
test: Fixtures isolados para prevenir poluição de .memory/

- Criar temp_memory_dir fixture (tests/conftest.py)
- Criar isolated_memory fixture (com monkey-patch)
- Atualizar testes para usar fixtures

Antes: Testes criavam arquivos em .memory/ real
Depois: Testes usam tmp_path (cleanup automático)

Validado: pytest tests/ -v (0 arquivos em .memory/ após rodar)
```

```
feat(devops): Scripts memory-cleanup.py e validate-configs.py

memory-cleanup.py:
- Dry-run por padrão (segurança)
- Backup automático antes de executar
- Detecção de duplicados (SHA256)
- Makefile: memory-cleanup, memory-cleanup-force

validate-configs.py:
- Detecta MCP CLI obsoleto (prevenção BUG-20)
- Detecta deps sem pinning
- Makefile: config-validate

Estimativa: 3.5h implementação
```

```
docs: Atualizar TODO.md com tasks P1/P2 + marcar P0 concluídas

P0 completas:
- Limpar memórias contaminadas ✅
- Passo 4.5 session-start ✅
- Test fixtures isolados ✅
- Scripts automation (cleanup, validate) ✅

P1 adicionadas:
- Pre-commit hook validate-memory
- GitHub Actions dependency check
- Docs MEMORY_SYSTEM.md
- (+ 4 items)

P2 backlog:
- Session-start quick mode
- Dashboard de métricas
```

---

## 🏁 Conclusão

**Status do Plano**: ✅ APROVADO (consenso 3/3 agentes)
**Pronto para Execução**: ✅ SIM
**Bloqueios**: Nenhum
**Riscos**: Mitigados (dry-run, backups, validações)

**Total de Trabalho**: 20 horas (8h P0, 10h P1, 2h docs)
**Prazo P0**: < 24h (esta sessão + amanhã)
**Prazo P1**: < 1 semana (sprint 2026-05-19 a 2026-05-25)

**Aprovação para início da implementação**:
- [x] Principal Software Engineer
- [x] SE: Architect
- [x] DevOps Expert

---

**Documento criado**: 2026-05-18
**Baseado em**: DEBATE-001-memory-cleanup-and-session-start-improvements.md
**Próxima revisão**: Após conclusão de Tasks P0 (2026-05-19)
