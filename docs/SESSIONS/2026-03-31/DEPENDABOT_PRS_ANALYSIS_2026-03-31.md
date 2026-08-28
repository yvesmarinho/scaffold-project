# Análise dos PRs do Dependabot — scaffold-project

**Data:** 2026-03-31
**Total de PRs:** 13 abertos
**Status:** Análise P2 completa (IMP-03 e IMP-04)

---

## 🔴 PRs de Major Version (Breaking Changes) — Revisão Manual Obrigatória

### PR #12: `github/codeql-action` v3 → v4
**Status:** ✅ **JÁ APLICADO MANUALMENTE**
**Ação:** Fechar PR (mudança já incluída no commit `05165de`)

**Detalhes:**
- Mudança foi aplicada manualmente em `security-scan.yml` no commit de correção P1
- Upload SARIF atualizado de v3 para v4 em jobs `trivy-docker` e `checkov`
- Breaking changes: melhorias em incremental analysis, repository properties
- **Recomendação:** Fechar PR #12 via GitHub

---

### PR #9: `apache-airflow` 2.10.5 → 3.1.8
**Status:** ⚠️ **BLOQUEAR - MAJOR BREAKING CHANGES**
**Risco:** 🔴 CRÍTICO
**Escopo:** `.github/templates/data-pipeline-airflow/airflow/requirements.txt`

**Breaking changes (Airflow 2.x → 3.x):**
- API REST completamente reescrita
- DAG serialization format alterado
- Provider compatibility matrix mudou
- Scheduler behavior changes
- Metadata database schema changes (migrations complexas)

**Ação recomendada:**
1. **NÃO MERGEAR** sem testes de regressão completos
2. Criar issue separado: "Airflow 3.x Migration Plan"
3. Necessário:
   - Ambiente de staging para testes
   - Validação de todos os DAGs existentes
   - Testes de compatibilidade com providers
   - Plano de rollback
   - Documentação de migração
4. **Prioridade:** P2 (agendar para Q2 2026)

**Refs:**
- [Airflow 3.0 Migration Guide](https://airflow.apache.org/docs/apache-airflow/3.0.0/migration-guide.html)
- [Breaking Changes Checklist](https://airflow.apache.org/docs/apache-airflow/3.0.0/release_notes.html#breaking-changes)

---

### PR #11: `zod` 3.25.76 → 4.3.6
**Status:** ⚠️ **REVISAR COM TESTES**
**Risco:** 🟠 MÉDIO
**Escopo:** `.github/templates/typescript-next/package.json`

**Breaking changes principais (Zod 3.x → 4.x):**
- API de validação mudou em alguns métodos
- `.message()` deprecado em favor de objeto de erro estruturado
- Algumas regras de inferência de tipo mudaram
- Performance improvements (pode afetar edge cases)

**Release highlights (v4.3):**
- `defineConfig` e `mergeConfig` helpers (type-safe)
- Melhor suporte para ESM
- Timer tick mode configurável

**Ação recomendada:**
1. ✅ **Pode ser merged** com validação
2. Pré-requisitos:
   - Rodar suite de testes do template TypeScript-Next
   - Validar schemas de validação existentes
   - Checar migrações de `.message()` para novo formato
3. **Prioridade:** P1 (mergear após testes)
4. Se nenhum teste quebrar: **APROVADO PARA MERGE**

**Comando de teste:**
```bash
cd .github/templates/typescript-next
npm install zod@4.3.6
npm test
```

---

### PR #10: `@types/jest` 29.5.14 → 30.0.0
**Status:** ✅ **SAFE TO MERGE**
**Risco:** 🟢 BAIXO
**Escopo:** `.github/templates/typescript-next/package.json` (devDependencies)

**Análise:**
- TypeScript type definitions para Jest 30.x
- Alinhado com PR #8 (jest 29→30)
- Apenas definições de tipos, sem mudanças de runtime
- Breaking changes limitados a novas assinaturas de tipos

**Ação recomendada:**
1. **MERGEAR JUNTO COM PR #8** (jest 30.3.0)
2. Ordem sugerida: mergear #8 primeiro, depois #10
3. **Prioridade:** P1 (safe to merge)

---

### PR #8: `jest` 29.7.0 → 30.3.0
**Status:** ✅ **SAFE TO MERGE**
**Risco:** 🟢 BAIXO
**Escopo:** `.github/templates/typescript-next/package.json` (devDependencies)

**Features highlight (v30):**
- `defineConfig` e `mergeConfig` helpers (type-safe config)
- `setTimerTickMode` para configurar avanço de timers
- Suporte para JSDOM v27
- Node.js 24 support
- Reduced LLM token usage

**Breaking changes (minor):**
- Requer Actions Runner v2.327.1+ (não afeta nosso CI)
- `jest.mock()` agora case-sensitive paths
- Algumas mudanças em fake-timers

**Ação recomendada:**
1. ✅ **MERGEAR** - breaking changes são mínimos
2. **Prioridade:** P1 (safe to merge)
3. Validar migration guide: [Jest v30 Migration](https://jestjs.io/docs/upgrading-to-jest30)

---

## 🟢 PRs de Minor/Patch — Baixo Risco

### PR #13: `actions/upload-artifact` v4 → v7
**Status:** ⚠️ **REVISAR ANTES DO MERGE**
**Risco:** 🟠 MÉDIO
**Escopo:** Workflows globais do GitHub Actions

**Mudanças principais:**
- **v7.0.0:** Suporte para direct file uploads (arquivos únicos sem zip)
  - Novo parâmetro `archive: false`
  - ESM module upgrade
- **v6.0.0:** Node.js 24 runtime (requer Actions Runner 2.327.1+)
- **v5.0.0:** Preliminary Node 24 support

**Arquivos impactados:**
```bash
grep -r "actions/upload-artifact@v4" .github/workflows/
```

**Resultados esperados:**
- `security-scan.yml`: job `bandit` usa upload-artifact@v4
- Outros workflows podem usar

**Ação recomendada:**
1. ⚠️ **MERGEAR COM VALIDAÇÃO DE RUNNERS**
2. Verificar versão dos self-hosted runners (se houver): >= 2.327.1
3. Testar workflow de segurança após merge
4. **Prioridade:** P1 (verificar runners primeiro)

**Breaking changes:**
- Requer Actions Runner >= 2.327.1
- Mudanças na API de artifact-id/run-id (checar se workflows usam)

**Comando de validação:**
```bash
# Verificar uso de artifact-id ou run-id nos workflows
grep -r "artifact.*id" .github/workflows/
```

---

### PRs Faltantes (não listados nos 13 PRs visualizados)

Baseado no ERROR_REPORT, esperávamos ver também:
- PR #1: apache-airflow 2.9.3 → 3.1.7
- PR #2: apache-airflow-providers-common-sql
- PR #3: apache-airflow-providers-http
- PR #4: apache-airflow-providers-amazon
- PR #5: actions/cache v4 → v5
- PR #6: actions/setup-python v5 → v6
- PR #7: actions/checkout v4 → v6

**Status:** Verificar se foram mesclados, fechados ou não aparecem nos primeiros 13 resultados.

---

## 📊 Sumário Executivo

| PR | Pacote | Decisão | Prioridade | Risco |
|----|--------|---------|-----------|-------|
| #12 | codeql-action v3→v4 | ✅ Fechar (já aplicado) | P0 | - |
| #13 | upload-artifact v4→v7 | ⚠️ Validar runners | P1 | 🟠 |
| #8 | jest 29→30 | ✅ Mergear | P1 | 🟢 |
| #10 | @types/jest 29→30 | ✅ Mergear com #8 | P1 | 🟢 |
| #11 | zod 3→4 | ⚠️ Testar antes | P1 | 🟠 |
| #9 | apache-airflow 2→3 | ❌ Bloquear | P2 | 🔴 |

---

## 🎯 Plano de Ação

### Ação Imediata (hoje)
1. ✅ Fechar PR #12 (já aplicado manualmente)
2. ⚠️ Comentar em PR #9 explicando bloqueio e criando issue de migração

### Ação P1 (esta semana)
3. Testar e mergear PR #8 (jest) + PR #10 (@types/jest)
4. Testar e mergear PR #11 (zod) após validação
5. Validar runners e mergear PR #13 (upload-artifact)

### Ação P2 (próximo sprint)
6. Criar issue: "Airflow 3.x Migration Plan"
7. Investigar PRs faltantes (#1-#7)
8. Criar processo de review automatizado para Dependabot PRs

---

## 🤖 Automações Sugeridas

### 1. Auto-merge para patches seguros
Configurar Dependabot automerge para:
- Patch/minor de devDependencies (TypeScript, Jest, linters)
- Patch de GitHub Actions (mantendo major versions pinadas)

### 2. CI checks obrigatórios para PRs do Dependabot
- Workflow completo deve passar antes do merge
- Coverage não pode diminuir
- Testes de integração devem passar

### 3. Labels automáticos
- `dependencies:breaking` - Major bumps
- `dependencies:safe` - Minor/patch de devDeps
- `dependencies:actions` - GitHub Actions updates

---

**Gerado por:** GitHub Copilot (@copilot)
**Análise baseada em:** ERROR_REPORT_2026-03-31.md + lista de PRs do GitHub API
**Commits relacionados:** 05165de (P1 fixes), dce227b (P2 refactor)
