# Guia de Restauração CI/CD

**Status:** 🔴 Workflows temporariamente removidos
**Data de remoção:** 2026-03-31
**Motivo:** Foco em desenvolvimento core durante fase inicial do template
**Previsão de retorno:** Após conclusão do desenvolvimento base (IMPs 49-51)

---

## 📋 Contexto da Remoção

### Decisão Tomada
Durante a sessão de 2026-03-31, após debate entre agentes (Template Architect e Session Manager), decidiu-se remover temporariamente os workflows de CI/CD para:

1. **Reduzir ruído** durante desenvolvimento ativo
2. **Economizar GitHub Actions minutes** (100%)
3. **Focar no core** (scaffold.py, MCP, documentação incremental)

### Estado dos Workflows no Momento da Remoção

Os workflows estavam **TOTALMENTE FUNCIONAIS** após correções P0/P1:

- ✅ `ci-template.yml` - Testes com matriz Python 3.10-3.12
- ✅ `security-scan.yml` - Gitleaks, TruffleHog, Trivy, Checkov, CodeQL
- ✅ Todos workflows passando sem erros

**Commits de correção:**
- `05165de` - fix(ci): corrigir falhas críticas nos workflows do GitHub Actions
- `dce227b` - refactor(ci): refatorar cobertura de testes e consolidar workflows

---

## 🔄 Roteiro de Restauração

### Passo 1: Restaurar Workflows do Git (15 minutos)

```bash
# 1. Restaurar arquivos do commit dce227b
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project

# 2. Checkout dos workflows corrigidos
git checkout dce227b -- .github/workflows/

# 3. Verificar arquivos restaurados
ls -la .github/workflows/
# Deve mostrar:
# - ci-template.yml
# - security-scan.yml
# - DEPRECATED-test-scaffold.md

# 4. Revisar mudanças
git diff --staged

# 5. Commit de restauração
cat > /tmp/commit_restore_workflows.txt << 'EOF'
feat(ci): restaurar workflows CI/CD corrigidos

Restaura workflows removidos temporariamente em 2026-03-31.

Workflows restaurados:
- ci-template.yml: Testes com pytest + coverage (Python 3.10-3.12)
- security-scan.yml: Gitleaks, TruffleHog, Trivy, Checkov, CodeQL v4

Estado: TOTALMENTE FUNCIONAIS (corrigidos em commits 05165de + dce227b)

Origem: git checkout dce227b -- .github/workflows/
Ref: docs/CI-CD-RESTORATION-GUIDE.md
Debate: docs/SESSIONS/2026-03-31/DEBATE_CONSOLIDADO_REMOCAO_AUTOMACOES_2026-03-31.md
EOF

./scripts/git-commit-with-file.sh /tmp/commit_restore_workflows.txt

# 6. Push para remote
git push origin master
```

### Passo 2: Validar Workflows Restaurados (10 minutos)

```bash
# 1. Trigger manual dos workflows via GitHub UI
# Acessar: https://github.com/yvesmarinho/scaffold-project/actions

# 2. Ou fazer commit trivial para trigger automático
echo "# Workflow restoration test" >> README.md
git add README.md
git commit -m "test: trigger CI após restauração de workflows"
git push origin master

# 3. Monitorar execução
# GitHub Actions → Ver runs em tempo real

# 4. Validar resultados
# Espera: ✅ ci-template.yml PASS
# Espera: ✅ security-scan.yml PASS
```

### Passo 3: Atualizar Documentação (5 minutos)

```bash
# 1. Atualizar README.md
# Remover aviso de "workflows temporariamente desabilitados"

# 2. Atualizar docs/INDEX.md
# Marcar CI-CD-RESTORATION-GUIDE.md como [OBSOLETO]

# 3. Atualizar este arquivo
# Modificar status de 🔴 para 🟢 RESTAURADO

# 4. Commit de atualização docs
git add README.md docs/INDEX.md docs/CI-CD-RESTORATION-GUIDE.md
git commit -m "docs: atualizar documentação após restauração CI/CD"
git push origin master
```

---

## 📊 Estado dos Workflows (Snapshot 2026-03-31)

### ci-template.yml

**Propósito:** Testes automatizados em Python 3.10, 3.11, 3.12

**Triggers:**
```yaml
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
```

**Jobs:**
1. **test** - Matriz Python 3.10-3.12
   - Instala: pytest, pytest-cov, rich, pyyaml
   - Executa: `pytest tests/ --cov=src --cov=scripts/lib --cov-report=xml`
   - Upload: coverage.xml para Codecov

2. **lint** - Validação de sintaxe
   - Python: `python -m py_compile scripts/**/*.py`
   - YAML: validação de workflows e configs

**Dependências críticas:**
- `pytest>=7.0.0`
- `pytest-cov>=4.0.0` (obrigatório para --cov flags)
- `pyyaml` (para lint job)

**Status no momento da remoção:** ✅ PASSING

---

### security-scan.yml

**Propósito:** Análise de segurança multi-ferramenta

**Triggers:**
```yaml
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  schedule:
    - cron: '0 0 * * 1'  # Segunda-feira 00:00 UTC
```

**Jobs:**

1. **gitleaks** - Scan de credenciais
   - Action: `gitleaks/gitleaks-action@v2`
   - Config: `.gitleaks.toml`
   - Status: ✅ Funcional (não requer GITLEAKS_LICENSE)

2. **trufflehog** - Scan de secrets
   - Action: `trufflesecurity/trufflehog@v3.82.6` (PINNED)
   - Scan: filesystem + git history
   - Status: ✅ Funcional

3. **trivy** - Scan de vulnerabilidades
   - Action: `aquasecurity/trivy-action@0.28.0` (PINNED)
   - Scan: filesystem
   - Format: SARIF para GitHub Security
   - Status: ✅ Funcional

4. **checkov** - IaC security scan
   - Action: `bridgecrewio/checkov-action@v12.2926.0` (PINNED)
   - Scan: .github/, scripts/, docker/
   - Status: ✅ Funcional

5. **codeql** - Análise semântica
   - Action: `github/codeql-action@v4` (UPGRADED from v3)
   - Languages: python
   - Status: ✅ Funcional

**Mudanças críticas aplicadas:**
- ✅ Todas actions pinadas (supply chain hardening)
- ✅ GITLEAKS_LICENSE removido (não necessário)
- ✅ CodeQL v3→v4 upgrade

**Status no momento da remoção:** ✅ PASSING

---

## ⚠️ Riscos Durante Período Sem CI/CD

### 🔴 ALTO - Security Vulnerabilities
- **6 CVEs pendentes** (1 critical, 2 high, 3 moderate)
- **10 PRs Dependabot** sem validação automática
- **Risco:** Merge de código vulnerável sem detecção

**Mitigação:**
- Revisar manualmente todos PRs de segurança
- Checar dashboard: https://github.com/yvesmarinho/scaffold-project/security/dependabot

### 🟠 MÉDIO - Code Quality
- **Testes não executados** automaticamente
- **Coverage não medido**
- **Risco:** Regressões não detectadas

**Mitigação:**
- Executar `make test-cov` manualmente antes de commits
- Revisar cobertura local via `htmlcov/index.html`

### 🟡 BAIXO - Compliance
- **Baseline enterprise comprometida**
- **Projetos scaffolded nascem sem CI**
- **Risco:** Expectativa de usuários frustrada

**Mitigação:**
- Documentar claramente que template está em desenvolvimento
- Adicionar aviso em README.md

---

## 📚 Referências

### Documentos de Análise
- [DEBATE_CONSOLIDADO_REMOCAO_AUTOMACOES_2026-03-31.md](SESSIONS/2026-03-31/DEBATE_CONSOLIDADO_REMOCAO_AUTOMACOES_2026-03-31.md)
- [SESSION_REPORT_2026-03-31.md](SESSIONS/2026-03-31/SESSION_REPORT_2026-03-31.md)
- [ERROR_REPORT_2026-03-31.md](SESSIONS/2026-03-31/ERROR_REPORT_2026-03-31.md)

### Commits Relevantes
- `05165de` - fix(ci): corrigir falhas críticas nos workflows
- `dce227b` - refactor(ci): refatorar cobertura de testes
- `96c1e52` - docs(dependabot): análise completa dos 13 PRs
- `[TBD]` - chore(ci): remover workflows temporariamente (este commit)

### Issues e PRs
- Issue #14: Migration Plan: Apache Airflow 2.x → 3.x
- 10 PRs Dependabot pendentes (análise em docs/SESSIONS/2026-03-31/)

---

## ✅ Checklist de Restauração

Quando for restaurar os workflows, siga esta checklist:

- [ ] Executar Passo 1 (git checkout de workflows)
- [ ] Executar Passo 2 (validar workflows via GitHub Actions)
- [ ] Executar Passo 3 (atualizar documentação)
- [ ] Processar 10 PRs Dependabot COM CI validando
- [ ] Revisar 6 vulnerabilidades de segurança
- [ ] Atualizar este documento para status 🟢 RESTAURADO
- [ ] Notificar equipe sobre restauração

---

## 🎯 Quando Restaurar

**Gatilhos para restauração:**

1. ✅ **Desenvolvimento core completo**
   - scaffold.py estável (v1.0.0)
   - MCP integração funcional
   - Documentação incremental implementada

2. ✅ **Template usado em produção**
   - Projetos reais sendo scaffolded
   - Expectativa de CI/CD desde o início

3. ✅ **Vulnerabilidades críticas**
   - CVE crítico requer validação imediata
   - Supply chain attack detectado

4. ✅ **Baseline enterprise necessária**
   - Auditoria ou compliance requer CI/CD ativo
   - Certificação de qualidade necessária

**Previsão:** Q2 2026 (após IMPs 49-51)

---

**Última atualização:** 2026-03-31
**Status:** 🔴 WORKFLOWS REMOVIDOS - Aguardando desenvolvimento core
**Próxima revisão:** Após conclusão de IMPs 49-51
