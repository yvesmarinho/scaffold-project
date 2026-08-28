# BUG-12: Memory System Not Initialized in New Projects

**Status**: 🔴 ABERTO
**Severidade**: P1 (Alta — feature crítica não funciona em novos projetos)
**Data Descoberta**: 2026-05-13
**Descoberto Por**: Usuário (validação pós BUG-11)
**Relacionado**: [BUG-11](BUG-11-session-start-first-incomplete-init.md) (mesmo padrão de problema)

---

## 📋 Sintomas

Após executar `session-start-first.prompt.md` em **novo projeto**:

1. ❌ Diretório `.memory/` criado mas **vazio** (apenas README.md)
2. ❌ **Não existe** `.memory/index/memory.db`
3. ❌ **Não existem** subdiretorios `.memory/memories/{project,team,sessions,.templates}`
4. ❌ Scripts `mem_*.py` **não copiados** para `scripts/`
5. ❌ Script `create_memory_structure.py` **não copiado** para `scripts/`
6. ❌ **Nenhuma instrução** em session-start-first para inicializar memory system

**Resultado**: Memory system configurado mas não funcional.

---

## 🔍 Análise de Causa Raiz

### Arquitetura Memory System

O sistema de memories depende de:

| Componente | Função | Status em Novo Projeto |
|------------|--------|------------------------|
| `.memory/index/memory.db` | SQLite FTS5 database para busca | ❌ NÃO CRIADO |
| `.memory/memories/{project,team,sessions,.templates}` | Estrutura de diretórios | ❌ NÃO CRIADOS |
| `scripts/create_memory_structure.py` | Script de inicialização | ❌ NÃO COPIADO |
| `scripts/mem_context.py` | CLI para buscar memories por contexto | ❌ NÃO COPIADO |
| `scripts/mem_search.py` | CLI para buscar memories por query | ❌ NÃO COPIADO |
| `scripts/mem_save.py` | CLI para salvar novo memory | ❌ NÃO COPIADO |
| `.vscode/mcp.json` → server `memory` | MCP server configurado | ✅ CRIADO |

### O Que o Scaffold Faz Atualmente

**Em `scripts/lib/project.py`:**

```python
# Linha 1793 — create_scaffolded_project()
directories = [
    ".memory",  # ← cria diretório vazio
    ...
]

# Linha 1821 — create_scaffolded_project()
files = [
    (".memory/README.md", _MEMORY_README),  # ← apenas README
]
```

**Resultado**: `.memory/` criado mas **NÃO FUNCIONAL**.

### O Que Está Faltando

1. **Cópia de Scripts**: Não existe `copy_memory_scripts()` (análogo ao `copy_session_scripts()` do BUG-11)
2. **Inicialização no Ritual**: `session-start-first.prompt.md` Passo 8 não menciona memory
3. **Checklist**: Não verifica `.memory/index/memory.db` criado

---

## ✅ Solução Implementada

### 1. Criar `copy_memory_scripts()` em `project.py`

**Localização**: `scripts/lib/project.py` (após `copy_session_scripts()`)

**Scripts a copiar**:
- `create_memory_structure.py` — inicialização de `.memory/`
- `mem_context.py` — busca por contexto
- `mem_search.py` — busca por query
- `mem_save.py` — salvar memory

### 2. Integrar em `new_project.py`

**Localização**: `scripts/lib/flows/new_project.py` (após step 5b)

Adicionar step **5c. Memory Scripts**:
```python
# 5c. Memory Scripts: create_memory_structure, mem_context, mem_search, mem_save
console.print("  [blue]🧠 Copiando scripts de memory...[/blue]")
results.extend(project.copy_memory_scripts(cfg))
```

### 3. Atualizar `session-start-first.prompt.md`

**Localização**: `.github/prompts/session-start-first.prompt.md` Passo 8

Adicionar subpasso **8.4 — Inicializar Memory System**:

```markdown
#### 8.4 — Inicializar Memory System

\`\`\`bash
# Criar estrutura .memory/ com diretórios e templates
python scripts/create_memory_structure.py
\`\`\`

**Resultado esperado**:
- `.memory/index/.gitignore` criado
- `.memory/memories/{project,team,sessions,.templates}/` criados
- `.memory/memories/.templates/example_decision.md` criado
```

### 4. Atualizar Checklist

Adicionar item:
```markdown
- [ ] **Memory system inicializado**: `.memory/memories/` structure criada
```

---

## 🧪 Validação

### Teste em Novo Projeto

```bash
# 1. Criar novo projeto com scaffold
python scripts/scaffold.py

# 2. Seguir session-start-first.prompt.md Passo 8.4
python scripts/create_memory_structure.py

# 3. Verificar estrutura criada
ls -la .memory/index/
ls -la .memory/memories/

# 4. Verificar scripts disponíveis
ls scripts/mem*.py scripts/create_memory_structure.py
```

**Resultado esperado**:
```
✅ .memory/index/.gitignore (12 bytes)
✅ .memory/memories/project/ (dir)
✅ .memory/memories/team/ (dir)
✅ .memory/memories/sessions/ (dir)
✅ .memory/memories/.templates/ (dir)
✅ .memory/memories/.templates/example_decision.md (~400 bytes)
✅ scripts/create_memory_structure.py (presente)
✅ scripts/mem_context.py (presente)
✅ scripts/mem_search.py (presente)
✅ scripts/mem_save.py (presente)
```

---

## 📊 Impacto

### Antes da Correção
- 🔴 **Memory system NÃO FUNCIONAL** em novos projetos
- 🔴 Scripts `mem_*.py` ausentes
- 🔴 Usuários precisam copiar manualmente de `scaffold-project`

### Depois da Correção
- 🟢 **Memory system FUNCIONAL** desde primeira sessão
- 🟢 Todos scripts copiados automaticamente
- 🟢 Ritual session-start-first completo e autocontido

---

## 🔗 Arquivos Modificados

| Arquivo | Modificação | Linhas |
|---------|-------------|--------|
| `scripts/lib/project.py` | `+ copy_memory_scripts()` | +40 |
| `scripts/lib/flows/new_project.py` | `+ step 5c` | +4 |
| `.github/prompts/session-start-first.prompt.md` | `+ Passo 8.4` | +25 |
| `.github/prompts/session-start-first.prompt.md` | `+ checklist item` | +1 |
| `docs/bugs/BUG-12-memory-system-not-initialized.md` | Nova documentação | +200 |

---

## 📝 Commits

```bash
# Commit 1: Implementação
fix(memory): BUG-12 - Inicialização completa do memory system

- Adiciona copy_memory_scripts() para copiar 4 scripts
- Integra em new_project.py como step 5c
- Atualiza session-start-first.prompt.md com Passo 8.4
- Atualiza checklist com verificação memory

Relacionado: BUG-11 (mesmo padrão para session-*)

# Commit 2: Documentação
docs: Documenta BUG-12 memory system não inicializado
```

---

## 🎯 Próximos Passos

1. ✅ Implementar `copy_memory_scripts()`
2. ✅ Integrar em `new_project.py`
3. ✅ Atualizar `session-start-first.prompt.md`
4. ✅ Atualizar checklist
5. ⏳ Testar em novo projeto
6. ⏳ Aplicar fix em projeto `teste_projetos` existente

---

**Tags**: `memory`, `scaffold`, `initialization`, `session-start-first`, `bug`
