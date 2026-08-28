# Teste de Upgrade — Instruções

**Data**: 2026-05-13
**Template**: scaffold-project (060-mini-engram-python)
**Commit**: 4cf4470

---

## 🎯 Objetivo

Validar que o upgrade copia TODOS os scripts necessários para projetos existentes.

---

## 📋 Pré-requisitos

1. ✅ Template atualizado e pushed (commit 4cf4470)
2. ✅ test-workspace-fix restaurado para estado PRÉ-upgrade
3. ✅ Scripts de diagnóstico copiados manualmente

---

## 🚀 Passo a Passo

### 1. Verificar Estado Atual (PRÉ-upgrade)

```bash
cd /home/yves_marinho/DevOps/Projetos/test-workspace-fix

# Verificar scripts ausentes
ls -1 scripts/*.py 2>/dev/null | wc -l
# Esperado: poucos scripts ou apenas load-mcp.sh

# Verificar .scaffold-state.yaml
cat .scaffold-state.yaml | grep "created_at\|updated_at"
```

---

### 2. Executar Upgrade

```bash
# Do diretório test-workspace-fix
uv run /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project/scripts/scaffold.py upgrade
```

**Observar logs esperados**:
```
🔄 Upgrade: test-workspace-fix | domínio: programming | linguagem: python

📁 Verificando estrutura...
🔗 Verificando symlinks...
📝 Verificando regras Copilot...
🔧 Verificando configuração VS Code...
🤖 Verificando assets SpecKit...
🧑‍💻 Verificando instruções do Copilot...      ← NOVO (BUG-13)
📊 Verificando scripts de sessão...             ← NOVO (BUG-11)
🧠 Verificando scripts de memory...             ← NOVO (BUG-12)
📋 Verificando templates de documentação...     ← NOVO (BUG-09)
📜 Verificando constitution.md...
🔑 Verificando load-mcp.sh...
```

---

### 3. Verificar Scripts Copiados (PÓS-upgrade)

```bash
# Contar scripts
ls -1 scripts/*.py 2>/dev/null | wc -l
# Esperado: >= 10 scripts

# Listar scripts copiados
ls -1 scripts/*.py
```

**Esperado (mínimo 10 scripts)**:
```
scripts/create_memory_structure.py
scripts/mem_context.py
scripts/mem_save.py
scripts/mem_search.py
scripts/session-chat.py
scripts/session-index.py
scripts/session-search.py
scripts/session-time-tracker.py
scripts/session-validate.py
scripts/test_memory_smoke.py
```

---

### 4. Verificar Copilot Instructions

```bash
# Copilot instructions
ls -lh .github/copilot-instructions.md
# Esperado: arquivo existe

# Copilot rules
ls -lh .copilot-rules.md
# Esperado: arquivo existe
```

---

### 5. Inicializar Sistemas

```bash
# Usar script de diagnóstico
python3 scripts/tmp/init_all_systems.py
```

**Esperado**:
```
🚀 Inicializando sistemas de rastreamento...
   Projeto: test-workspace-fix

1️⃣  Session Index...
   ✅ Criado: index.db (XX KB)

2️⃣  Session Time Tracker...
   ▶️  Iniciando sessão...
   ⏹️  Parando sessão...
   ✅ Criado: history.csv

3️⃣  Memory System...
   ✅ Criadas 4 pastas: ...

============================================================
✅ TODOS OS SISTEMAS INICIALIZADOS COM SUCESSO!
============================================================
```

---

### 6. Verificar Conformidade

```bash
python3 scripts/tmp/verify_first_session.py
```

**Esperado**:
```
📊 Verificando conformidade: test-workspace-fix

1️⃣  Infraestrutura
  ✅ Ambiente virtual: pyvenv.cfg
  ✅ MCP config: mcp.json
  ✅ .gitignore: .gitignore
  ✅ .copilot-rules.md: .copilot-rules.md

2️⃣  Sistemas de Rastreamento
  ✅ Session Index DB: index.db
  ✅ Session Time CSV: history.csv
  ✅ Memory System

3️⃣  Scripts de Rastreamento
  ✅ Script: session-index.py
  ✅ Script: session-time-tracker.py
  ✅ Script: create_memory_structure.py

...

============================================================
📊 Score: 16/16 (100%)
============================================================
✅ CONFORMIDADE TOTAL — Session Start (First Time) completo!
```

---

## ✅ Critérios de Sucesso

### Upgrade PASSOU se:

1. ✅ Logs mostram verificação de Copilot, sessão e memory
2. ✅ Scripts copiados: session-index, session-time-tracker, session-search, session-chat, session-validate
3. ✅ Scripts copiados: create_memory_structure, mem_context, mem_search, mem_save, test_memory_smoke
4. ✅ Arquivos copiados: .github/copilot-instructions.md, .copilot-rules.md
5. ✅ init_all_systems.py executa SEM erros
6. ✅ verify_first_session.py mostra score >= 85%

### Upgrade FALHOU se:

1. ❌ Scripts de sessão ausentes após upgrade
2. ❌ Scripts de memory ausentes após upgrade
3. ❌ copilot-instructions.md ausente
4. ❌ init_all_systems.py falha (scripts não encontrados)
5. ❌ verify_first_session.py mostra score < 50%

---

## 🐛 Troubleshooting

### Problema: Scripts não copiados

**Sintomas**:
```
python3 scripts/tmp/init_all_systems.py
# ❌ Script não encontrado: /path/to/scripts/session-index.py
```

**Causa**: Upgrade não executou copy_session_scripts()

**Verificar**:
```bash
# Ver logs do upgrade novamente
# Deve mostrar "📊 Verificando scripts de sessão..."
```

**Solução**:
```bash
# Re-executar upgrade
uv run /path/to/scaffold-project/scripts/scaffold.py upgrade --force
```

---

### Problema: Score baixo (< 50%)

**Causa**: Sistemas não inicializados

**Solução**:
```bash
# Executar inicialização
python3 scripts/tmp/init_all_systems.py

# Verificar novamente
python3 scripts/tmp/verify_first_session.py
```

---

## 📊 Relatório de Teste

**Após executar todos os passos, preencher**:

### Resultados

- [ ] Upgrade executou sem erros
- [ ] Logs mostraram verificação de Copilot/sessão/memory
- [ ] 10+ scripts copiados
- [ ] copilot-instructions.md criado
- [ ] .copilot-rules.md criado
- [ ] init_all_systems.py executou com sucesso
- [ ] verify_first_session.py score: ____%

### Observações

(adicionar qualquer problema, warning ou observação aqui)

---

### Conclusão

- [ ] ✅ TESTE PASSOU — Upgrade funciona corretamente
- [ ] ❌ TESTE FALHOU — (descrever problema)

---

**Data do teste**: ___________
**Testado por**: ___________
**Template commit**: 4cf4470
