# Checklist de Validação — Scaffold Upgrade

**Projeto**: test-workspace-fix
**Path**: `/home/yves_marinho/DevOps/Projetos/test-workspace-fix`
**Data de criação**: 2026-05-19
**Última atualização**: 2026-05-19

---

## 🎯 Como Usar Esta Checklist

### Opção 1: Validação Automatizada (Recomendado) ⚡

```bash
# Executar teste pytest
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project
pytest tests/test_validate_test_workspace_fix.py -v

# OU executar script standalone
python scripts/validate-workspace-upgrade.py /home/yves_marinho/DevOps/Projetos/test-workspace-fix
```

### Opção 2: Validação Manual 📋

Marque com `[x]` cada item conforme valida.

---

## ✅ 1. BUG-20: MCP GitHub HTTP Migration (P0 CRÍTICA)

**Objetivo**: Garantir que GitHub MCP server usa HTTP (não stdio CLI obsoleto)

### Validações Obrigatórias

- [ ] **1.1** Arquivo `.vscode/mcp.json` existe
  ```bash
  ls -l .vscode/mcp.json
  ```

- [ ] **1.2** mcp.json contém JSON válido (sem erros de sintaxe)
  ```bash
  python -m json.tool .vscode/mcp.json > /dev/null && echo "✅ JSON válido"
  ```

- [ ] **1.3** GitHub server está configurado em mcpServers
  ```bash
  jq '.mcpServers.github' .vscode/mcp.json
  ```

- [ ] **1.4** ❌ CRÍTICO: Campo `type` NÃO é `"stdio"`
  ```bash
  TYPE=$(jq -r '.mcpServers.github.type' .vscode/mcp.json)
  if [ "$TYPE" = "stdio" ]; then
    echo "❌ FALHOU: Ainda usando stdio (CLI obsoleto)"
  else
    echo "✅ OK: type=$TYPE"
  fi
  ```

- [ ] **1.5** Configuração HTTP tem campo `url` (se type=http)
  ```bash
  jq '.mcpServers.github.url' .vscode/mcp.json
  # Deve retornar URL contendo "github"
  ```

- [ ] **1.6** OU configuração npx tem args corretos (se usando npx wrapper)
  ```bash
  jq '.mcpServers.github | {command, args}' .vscode/mcp.json
  # command: "npx"
  # args: ["-y", "@modelcontextprotocol/server-github"]
  ```

- [ ] **1.7** Configuração HTTP NÃO tem campos obsoletos (command, args, env)
  ```bash
  # Se type=http, estes campos NÃO devem existir:
  jq '.mcpServers.github | has("command")' .vscode/mcp.json
  # Deve retornar: false
  ```

### Critérios de Aceitação

- ✅ **PASSOU**: `type != "stdio"` E (tem `url` OU comando é `npx`)
- ❌ **FALHOU**: `type == "stdio"` (configuração CLI antiga)

### Ação se Falhar

```bash
# Re-executar scaffold upgrade forçado
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project
python scripts/scaffold.py \
  --upgrade \
  --force \
  --target-dir /home/yves_marinho/DevOps/Projetos/test-workspace-fix \
  --log-dir /home/yves_marinho/DevOps/Projetos/test-workspace-fix/logs
```

---

## ✅ 2. BUG-17: Session Time Tracker Deployment

**Objetivo**: Garantir que time-tracker foi deployado com Passo 6.5

### Validações Obrigatórias

- [ ] **2.1** Script `session-time-tracker.py` existe
  ```bash
  ls -l scripts/session-time-tracker.py
  ```

- [ ] **2.2** session-start.prompt.md existe
  ```bash
  ls -l .github/prompts/session-start.prompt.md
  ```

- [ ] **2.3** session-start.prompt.md contém "Passo 6.5"
  ```bash
  grep -n "Passo 6.5" .github/prompts/session-start.prompt.md
  # Deve encontrar linha com "Passo 6.5"
  ```

- [ ] **2.4** Passo 6.5 menciona "Rastreamento de Sessão" ou "session-time"
  ```bash
  grep -A 5 "Passo 6.5" .github/prompts/session-start.prompt.md | grep -i "rastreamento\|session-time"
  ```

- [ ] **2.5** Diretório `.session-time/` pode ser criado (ou já existe)
  ```bash
  ls -ld .session-time 2>/dev/null || echo "Será criado ao executar time-tracker"
  ```

### Critérios de Aceitação

- ✅ **PASSOU**: Script existe E Passo 6.5 presente no prompt
- ❌ **FALHOU**: Script ausente OU Passo 6.5 ausente

---

## ✅ 3. BUG-18: Objetivo.yaml Deployment

**Objetivo**: Garantir que objetivo.yaml foi deployado na raiz

### Validações Obrigatórias

- [ ] **3.1** Arquivo `objetivo.yaml` existe na raiz
  ```bash
  ls -l objetivo.yaml
  ```

- [ ] **3.2** objetivo.yaml contém YAML válido
  ```bash
  python -c "import yaml; yaml.safe_load(open('objetivo.yaml'))" && echo "✅ YAML válido"
  ```

- [ ] **3.3** objetivo.yaml tem seção `project`
  ```bash
  python -c "import yaml; d=yaml.safe_load(open('objetivo.yaml')); print('✅ OK' if 'project' in d else '❌ FALTA project')"
  ```

- [ ] **3.4** Nome do projeto é "test-workspace-fix"
  ```bash
  python -c "import yaml; d=yaml.safe_load(open('objetivo.yaml')); print(d['project']['name'])"
  # Deve retornar: test-workspace-fix
  ```

### Critérios de Aceitação

- ✅ **PASSOU**: Arquivo existe E YAML válido E nome correto
- ❌ **FALHOU**: Arquivo ausente OU YAML inválido

---

## ✅ 4. BUG-19: Git Validators Deployment

**Objetivo**: Garantir que git_validators.py foi deployado

### Validações Obrigatórias

- [ ] **4.1** Script `scripts/lib/git_validators.py` existe
  ```bash
  ls -l scripts/lib/git_validators.py
  ```

- [ ] **4.2** git_validators.py contém código Python válido
  ```bash
  grep -E "^(def |class )" scripts/lib/git_validators.py
  # Deve encontrar funções ou classes
  ```

- [ ] **4.3** git_validators.py pode ser importado (sem syntax errors)
  ```bash
  python -c "import sys; sys.path.insert(0, 'scripts'); from lib import git_validators" && echo "✅ Importável"
  ```

### Critérios de Aceitação

- ✅ **PASSOU**: Arquivo existe E contém código Python
- ❌ **FALHOU**: Arquivo ausente

---

## ✅ 5. Arquivos Críticos do Projeto

### Validações Obrigatórias

- [ ] **5.1** `.scaffold-state.yaml` existe (criado pelo upgrade)
  ```bash
  ls -l .scaffold-state.yaml
  ```

- [ ] **5.2** .scaffold-state.yaml contém campos obrigatórios
  ```bash
  python -c "import yaml; d=yaml.safe_load(open('.scaffold-state.yaml')); print('✅ OK' if all(k in d for k in ['scaffold_version', 'updated_at', 'project']) else '❌ Campos ausentes')"
  ```

- [ ] **5.3** `.copilot-rules.md` existe e não está vazio
  ```bash
  [ -s .copilot-rules.md ] && echo "✅ OK" || echo "❌ Ausente ou vazio"
  ```

- [ ] **5.4** `.vscode/settings.json` existe
  ```bash
  ls -l .vscode/settings.json
  ```

- [ ] **5.5** settings.json contém JSON válido
  ```bash
  python -m json.tool .vscode/settings.json > /dev/null && echo "✅ JSON válido"
  ```

- [ ] **5.6** `.vscode/tasks.json` existe
  ```bash
  ls -l .vscode/tasks.json
  ```

- [ ] **5.7** `.vscode/extensions.json` existe
  ```bash
  ls -l .vscode/extensions.json
  ```

### Critérios de Aceitação

- ✅ **PASSOU**: Todos os arquivos existem E são válidos
- ❌ **FALHOU**: Um ou mais arquivos ausentes ou inválidos

---

## ✅ 6. Logs de Scaffold Upgrade

### Validações Obrigatórias

- [ ] **6.1** Diretório `logs/` existe
  ```bash
  ls -ld logs
  ```

- [ ] **6.2** Existe pelo menos um log de scaffold
  ```bash
  ls -lt logs/scaffold_*.log | head -1
  ```

- [ ] **6.3** Log mais recente contém estatísticas de upgrade
  ```bash
  LATEST=$(ls -t logs/scaffold_*.log | head -1)
  grep -E "created:|skipped:|merged:" "$LATEST" && echo "✅ Estatísticas encontradas"
  ```

- [ ] **6.4** Log indica "merged" para mcp.json
  ```bash
  LATEST=$(ls -t logs/scaffold_*.log | head -1)
  grep "mcp.json" "$LATEST" | grep -i "merged"
  ```

### Critérios de Aceitação

- ✅ **PASSOU**: Logs existem E contêm estatísticas
- ⚠️  **WARNING**: Logs ausentes (upgrade pode não ter sido executado)

---

## 📊 Resumo de Validação

### Contadores

- [ ] **BUG-20** (MCP HTTP): ___/7 validações passaram
- [ ] **BUG-17** (Time Tracker): ___/5 validações passaram
- [ ] **BUG-18** (Objetivo.yaml): ___/4 validações passaram
- [ ] **BUG-19** (Git Validators): ___/3 validações passaram
- [ ] **Arquivos Críticos**: ___/7 validações passaram
- [ ] **Logs**: ___/4 validações passaram

**TOTAL**: ___/30 validações

### Status Final

- [ ] ✅ **TODAS PASSARAM** (30/30) — Upgrade bem-sucedido
- [ ] ⚠️  **PARCIAL** (25-29/30) — Revisar itens falhados
- [ ] ❌ **CRÍTICO** (< 25/30) — Re-executar scaffold upgrade --force

---

## 🚨 Ações Corretivas

### Se BUG-20 (MCP) falhar

**Problema**: mcp.json ainda usa configuração stdio (CLI obsoleta)

**Solução**:
```bash
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project
python scripts/scaffold.py \
  --upgrade \
  --force \
  --target-dir /home/yves_marinho/DevOps/Projetos/test-workspace-fix \
  --log-dir /home/yves_marinho/DevOps/Projetos/test-workspace-fix/logs
```

### Se BUG-17/18/19 falharem

**Problema**: Arquivos não deployados

**Solução**: Mesmo comando acima (scaffold upgrade --force)

### Se arquivos críticos falharem

**Problema**: Corrupção ou merge incompleto

**Solução**:
1. Verificar logs de scaffold para erros
2. Re-executar upgrade com `--force`
3. Se persistir: criar issue com detalhes

---

## 📝 Histórico de Validações

| Data | Validador | Total Passado | Falhas Críticas | Notas |
|------|-----------|---------------|-----------------|-------|
| 2026-05-19 | ___________ | ___/30 | _____________ | __________ |

---

## 🔗 Referências

- **Commits de correção**:
  - BUG-20: `ad7eaed` — fix(merge): Template-wins para mudanças de schema MCP
  - BUG-001: `ec46cfe` — fix(scaffold): resolve BUG-001 objetivo-init 3 issues

- **Documentação**:
  - [BUG-20 Report](../../docs/bugs/BUG-20-mcp-github-http-merge-failure.md)
  - [BUG-001 Report](../../docs/bugs/BUG-001-scaffold-objetivo-init-issues.md)
  - [Validation Report 2026-05-18](../../docs/SESSIONS/2026-05-18/VALIDATION_REPORT_test-workspace-fix_2026-05-18.md)

- **Scripts de validação**:
  - `tests/test_validate_test_workspace_fix.py` (pytest)
  - `scripts/validate-workspace-upgrade.py` (standalone)
  - `scripts/validate-configs.py` (configs específicas)
