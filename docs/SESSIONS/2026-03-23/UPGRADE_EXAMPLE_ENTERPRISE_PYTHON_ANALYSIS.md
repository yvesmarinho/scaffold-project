# 🔄 Exemplo Prático: Upgrade de Projeto Legacy

**Data**: 2026-03-23
**Projeto Analisado**: `enterprise-python-analysis`
**Cenário**: Projeto sem `.scaffold-state.yaml` com session manager desatualizado

---

## 📊 Contexto do Projeto

### Histórico
- **Criado**: ~2026-01-16 (inferido da primeira sessão)
- **Forma**: Manual ou scaffold antigo (sem `.scaffold-state.yaml`)
- **Última sessão**: 2026-03-23
- **Agentes**: Formato antigo (`session.start.agent.md`, `session.end.agent.md`)
- **Arquivos de sessão**: Formato parcial (2 arquivos em vez de 4)

### Estrutura Atual

```
enterprise-python-analysis/
├── ❌ .scaffold-state.yaml           (AUSENTE)
├── .github/
│   └── agents/
│       ├── ⚠️ session.start.agent.md    (v0.x - antigo)
│       ├── ⚠️ session.end.agent.md      (v0.x - antigo)
│       └── ✅ speckit.*.agent.md       (atualizados)
├── docs/
│   └── sessions/
│       ├── 2026-03-19/
│       │   ├── SESSION_RECOVERY_2026-03-19.md
│       │   ├── SESSION_REPORT_2026-03-19.md
│       │   ├── TODAY_ACTIVITIES_2026-03-19.md    (nomenclatura antiga)
│       │   └── FINAL_STATUS_2026-03-19.md
│       └── 2026-03-23/
│           ├── SESSION_RECOVERY_2026-03-23.md
│           └── TODAY_ACTIVITIES_2026-03-23.md    (incompleto - falta 2 arquivos)
└── [outros arquivos...]
```

---

## 🚨 Problemas Identificados

### 1. **Ausência de `.scaffold-state.yaml`** (🔴 CRÍTICO)

**Consequência:**
```bash
$ scaffold.py upgrade --target-dir enterprise-python-analysis
❌ Erro: .scaffold-state.yaml não encontrado em /path/to/enterprise-python-analysis
```

**Causa:**
- Projeto não foi criado com `scaffold.py --new`
- Ou arquivo foi removido acidentalmente
- Ou foi migrado de sistema anterior

---

### 2. **Session Manager Desatualizado** (⚠️ ATENÇÃO)

#### Comparação: Antigo vs Novo

| Aspecto | Antigo (v0.x) | Novo (v1.1.0) |
|---------|---------------|---------------|
| **Arquivos** | 2 agentes separados | 1 agente unificado |
| **Nome** | `session.start.agent.md`<br>`session.end.agent.md` | `session-manager.agent.md` |
| **Versão** | Não versionado | v1.1.0 explícito |
| **Docs criados** | 2 arquivos:<br>- SESSION_RECOVERY<br>- TODAY_ACTIVITIES | 4 arquivos:<br>- SESSION_RECOVERY<br>- DAILY_ACTIVITIES<br>- SESSION_REPORT<br>- FINAL_STATUS |
| **MCP Integration** | Básica | Avançada (memory graph) |
| **Security Scan** | Manual | Automatizado |
| **Git Integration** | Manual | Automatizado |
| **Pylance Tools** | Não mencionado | Prioridade explícita |

#### Impacto Prático

**Sessão com agente antigo:**
```bash
# Usuário invoca
@session.start

# Resultado:
✅ docs/sessions/2026-03-23/SESSION_RECOVERY_2026-03-23.md
✅ docs/sessions/2026-03-23/TODAY_ACTIVITIES_2026-03-23.md
❌ Falta SESSION_REPORT_2026-03-23.md
❌ Falta FINAL_STATUS_2026-03-23.md
```

**Sessão com agente novo:**
```bash
# Usuário invoca
@session-manager

# Resultado:
✅ docs/SESSIONS/2026-03-23/SESSION_RECOVERY_2026-03-23.md
✅ docs/SESSIONS/2026-03-23/DAILY_ACTIVITIES_2026-03-23.md
✅ docs/SESSIONS/2026-03-23/SESSION_REPORT_2026-03-23.md
✅ docs/SESSIONS/2026-03-23/FINAL_STATUS_2026-03-23.md
```

---

### 3. **Nomenclatura Inconsistente** (🟡 INFO)

**Observado:**
- `TODAY_ACTIVITIES_*.md` (padrão antigo)
- `DAILY_ACTIVITIES_*.md` (padrão novo)

**Nota:** Ambos são válidos — é evolução natural do template. Arquivos de sessão **nunca** são modificados pelo upgrade.

---

## 🔄 Processo de Upgrade: Passo a Passo

### Etapa 1: Criar `.scaffold-state.yaml`

**Localização:** Raiz do projeto

**Conteúdo:**
```yaml
scaffold_version: "1.0.0"
created_at: "2026-01-16T00:00:00Z"  # Data da primeira sessão conhecida
updated_at: "2026-03-23T15:30:00Z"  # Data atual
project:
  name: enterprise-python-analysis
  title: Enterprise Python Analysis
  description: Análise de performance N8N e infraestrutura observável
  domain: analysis
  language: python
  github_repo: ""
paths:
  target_dir: /home/yves_marinho/Documentos/DevOps/Vya-Jobs
  shared_dir: /home/yves_marinho/Documentos/DevOps/.copilot-shared
profiles_applied: []
```

**Campos importantes:**

| Campo | Descrição | Como determinar |
|-------|-----------|-----------------|
| `scaffold_version` | Versão do template | Use `"1.0.0"` para retrocompatibilidade |
| `created_at` | Data de criação do projeto | Data da primeira sessão ou commit inicial |
| `updated_at` | Última atualização | Data atual |
| `project.domain` | Domínio do projeto | `programming`, `infrastructure` ou `analysis` |
| `project.language` | Linguagem principal | `python`, `typescript`, `go`, etc. |
| `profiles_applied` | Perfis aplicados | Lista vazia `[]` se nenhum perfil SpecKit foi usado |

---

### Etapa 2: Executar Upgrade

```bash
# Do diretório do template
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project

# Executar upgrade
python scripts/scaffold.py upgrade \
  --target-dir /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-analysis
```

**Output esperado:**
```
🔄 Executando upgrade para: enterprise-python-analysis
✅ Lendo .scaffold-state.yaml
🔄 Estrutura de pastas... skipped (já existem)
🔄 Symlinks... skipped (corretos)
🔄 Regras Copilot... skipped (arquivos idênticos)
🔄 Configuração VS Code... skipped (arquivos idênticos)
🔄 Assets SpecKit...
   ✅ Copiado: .github/agents/session-manager.agent.md
   ⏭️  Skipped: session.start.agent.md (já existe)
   ⏭️  Skipped: session.end.agent.md (já existe)
   ⏭️  Skipped: speckit.*.agent.md (já existem)
🔄 Constitution... skipped (idêntico)
🔄 Script MCP... skipped (idêntico)
✅ Atualizado .scaffold-state.yaml (updated_at)

✅ Upgrade concluído: 1 arquivo(s) novo(s) ou atualizado(s).
```

---

### Etapa 3: Verificar Mudanças

```bash
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-analysis

# Ver arquivos modificados
git status

# Ver diferenças
git diff .scaffold-state.yaml
git diff .github/agents/
```

**Esperado:**
```
Untracked files:
  .scaffold-state.yaml
  .github/agents/session-manager.agent.md

No changes to existing files (preservados)
```

---

### Etapa 4: Validar Novo Agente

```bash
# Commitar mudanças
git add .scaffold-state.yaml .github/agents/session-manager.agent.md
git commit -m "chore: add scaffold state and upgrade to session-manager v1.1.0"

# Próxima sessão: testar novo agente
# No VS Code, invocar:
@session-manager
```

**Validações:**
- ✅ Cria 4 arquivos de sessão (não 2)
- ✅ Nomenclatura: `DAILY_ACTIVITIES` (não `TODAY_ACTIVITIES`)
- ✅ Security scan automatizado
- ✅ MCP memory integration funcionando
- ✅ Git status e branch detection

---

## 🎯 Resultados do Upgrade

### Antes do Upgrade

```
enterprise-python-analysis/
├── ❌ .scaffold-state.yaml
└── .github/agents/
    ├── session.start.agent.md     (antigo)
    └── session.end.agent.md       (antigo)
```

### Depois do Upgrade

```
enterprise-python-analysis/
├── ✅ .scaffold-state.yaml         (CRIADO)
└── .github/agents/
    ├── session.start.agent.md     (preservado - coexiste)
    ├── session.end.agent.md       (preservado - coexiste)
    └── session-manager.agent.md   (NOVO - v1.1.0)
```

**Importante:** Agentes antigos **não são removidos** — coexistem com o novo. Isso permite:
- ✅ Transição gradual
- ✅ Rollback fácil se necessário
- ✅ Comparação lado a lado

---

## 🔍 Comportamento do Upgrade (Detalhado)

### O que o Upgrade FAZ

1. **✅ Cria arquivos ausentes**
   - Novos agentes SpecKit
   - Arquivos de configuração VS Code faltantes
   - Estrutura de diretórios faltante

2. **✅ Atualiza `.scaffold-state.yaml`**
   - Campo `updated_at` → timestamp atual
   - Preserva todos os outros campos

3. **✅ Preserva customizações**
   - Arquivos modificados → **não sobrescritos**
   - Arquivos de sessão → **nunca tocados**
   - Código do projeto → **intocado**

### O que o Upgrade NÃO FAZ

1. **❌ Não migra nomenclatura antiga**
   - `TODAY_ACTIVITIES` → **não renomeia** para `DAILY_ACTIVITIES`
   - Histórico permanece com nomes originais

2. **❌ Não remove agentes obsoletos**
   - `session.start.agent.md` → **permanece**
   - `session.end.agent.md` → **permanece**

3. **❌ Não refatora sessões antigas**
   - Sessões com 2 arquivos → **não completadas** para 4
   - Conteúdo de sessões → **imutável**

4. **❌ Não atualiza invocações**
   - Você deve mudar manualmente de `@session.start` para `@session-manager`

---

## 🛠️ Limpeza Opcional (Após Validação)

Após 2-3 sessões bem-sucedidas com o novo agente:

```bash
# Opcional: remover agentes antigos
rm .github/agents/session.start.agent.md
rm .github/agents/session.end.agent.md

git add -A
git commit -m "chore: remove deprecated session agents (migrated to session-manager)"
```

**Critério para remoção:**
- ✅ 2-3 sessões completas com novo agente
- ✅ Nenhum problema identificado
- ✅ Equipe familiarizada com nova invocação (`@session-manager`)

---

## 📋 Checklist de Migração

```markdown
### Preparação
- [x] Analisar estrutura do projeto
- [x] Identificar problemas (.scaffold-state.yaml ausente)
- [x] Documentar agentes atuais
- [x] Verificar último backup/commit

### Execução
- [ ] Criar .scaffold-state.yaml com metadados corretos
- [ ] Executar `scaffold.py upgrade`
- [ ] Verificar `git status` e `git diff`
- [ ] Commitar mudanças

### Validação
- [ ] Próxima sessão: invocar `@session-manager`
- [ ] Verificar criação dos 4 arquivos de sessão
- [ ] Confirmar que MCP memory está funcionando
- [ ] Validar security scan automatizado
- [ ] Confirmar git integration

### Limpeza (Opcional - após 2-3 sessões)
- [ ] Remover `session.start.agent.md` (se não mais necessário)
- [ ] Remover `session.end.agent.md` (se não mais necessário)
- [ ] Atualizar documentação interna sobre novo workflow
```

---

## 💡 Lições Aprendidas

### ✅ Pontos Fortes do Design

1. **Preservação de histórico** — Nada é perdido involuntariamente
2. **Coexistência** — Novo e antigo podem conviver durante transição
3. **Idempotência** — Seguro executar múltiplas vezes
4. **Não-destrutivo** — Preferência por opt-in vs mudanças forçadas

### 🎓 Boas Práticas

1. **Sempre criar `.scaffold-state.yaml`** em projetos novos
2. **Versionar o estado** — é seguro e necessário
3. **Documentar data de criação** — facilita troubleshooting
4. **Testar upgrade em branch separada** primeiro
5. **Validar antes de limpar** — manter agentes antigos por período de transição

### ⚠️ Armadilhas Comuns

1. ❌ **Esquecer `.scaffold-state.yaml`** → upgrade não funciona
2. ❌ **Usar `--force` sem necessidade** → perde customizações
3. ❌ **Remover agentes antigos imediatamente** → sem rollback
4. ❌ **Não testar nova sessão** → descobrir problemas tarde demais

---

## 🎯 Conclusão

O processo de upgrade do Enterprise Scaffold Project Template foi projetado para ser:
- **Seguro** — preserva customizações e histórico
- **Gradual** — permite transição suave
- **Versionado** — rastreável via `.scaffold-state.yaml`
- **Idempotente** — executável múltiplas vezes

Para projetos legacy como `enterprise-python-analysis`, a estratégia recomendada é:
1. ✅ Criar `.scaffold-state.yaml` manualmente
2. ✅ Executar upgrade
3. ✅ Validar novo agente
4. ✅ Manter coexistência durante transição
5. ✅ Limpar agentes antigos após validação

---

**Documento gerado em**: 2026-03-23
**Template version**: 1.0.0
**Session-manager version**: 1.1.0
**Autor**: GitHub Copilot (Session Manager Agent)
