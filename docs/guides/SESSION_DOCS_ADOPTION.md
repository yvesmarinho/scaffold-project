# Session Documentation Adoption Guide

**Version**: 1.0.0
**Last Updated**: 2026-04-03
**Part of**: IMP-50 — Sistema de documentação incremental — Docs + Migração

---

## 🎯 Objetivo

Este guia orienta a adoção do sistema de documentação incremental de sessões em projetos existentes que já possuem histórico de desenvolvimento.

**Para quem é este guia:**
- ✅ Projetos existentes com histórico em `docs/SESSIONS/` ou similar
- ✅ Times migrando de formato freeform para formato estruturado
- ✅ Novos membros aprendendo o sistema de documentação
- ✅ Projetos derivados do Enterprise Scaffold Project Template

---

## 📋 Pré-requisitos

Antes de adotar o sistema:

### 1. Ferramentas Instaladas

```bash
# Python 3.10+
python --version  # >= 3.10

# Gitleaks (para security scan)
gitleaks version  # >= 8.18.0

# yamllint (opcional, para validação de configs)
yamllint --version
```

### 2. Arquivos Base Presentes

| Arquivo | Localização | Status |
|---------|-------------|--------|
| Style Guide | `docs/SESSION_DOCS_STYLE_GUIDE.md` | ✅ Obrigatório |
| Validator | `scripts/session-validate.py` | ✅ Obrigatório |
| Gitleaks Config | `.gitleaks-session-docs.toml` | ✅ Obrigatório |
| Makefile targets | `session-log`, `session-validate`, `session-sanitize` | ⚠️ Recomendado |
| Prompts | `.github/prompts/session-*.prompt.md` | 🔵 Opcional |

**Se algum arquivo estiver faltando:**
- Copiar do Enterprise Scaffold Project Template (versão mais recente)
- Ou gerar via `scaffold.py --upgrade` (se disponível)

---

## 🚀 Processo de Adoção (5 Fases)

### Fase 1: Preparação (30 minutos)

#### 1.1 — Backup do Histórico Existente

```bash
# Criar backup de segurança
cp -r docs/SESSIONS docs/SESSIONS.backup.$(date +%Y%m%d)

# Ou usar tar.gz
tar -czf docs-sessions-backup-$(date +%Y%m%d).tar.gz docs/SESSIONS/

# Verificar backup
ls -lh docs-sessions-backup-*.tar.gz
```

#### 1.2 — Inventariar Sessões Existentes

```bash
# Listar todas as sessões
find docs/SESSIONS -type d -name "20*" | sort

# Contar arquivos por sessão
for dir in docs/SESSIONS/20*/; do
  echo "$(basename $dir): $(find $dir -type f | wc -l) arquivos"
done
```

#### 1.3 — Verificar Qualidade dos Dados

```bash
# Verificar se há dados sensíveis no histórico
make session-sanitize

# Ou manualmente:
gitleaks detect \
  --config .gitleaks-session-docs.toml \
  --source docs/SESSIONS/ \
  --verbose
```

**Se encontrar violações:**
- ⚠️ **CRÍTICO**: Sanitizar antes de prosseguir
- Ver: `docs/SECURITY_SESSION_DOCS.md` para procedimentos

---

### Fase 2: Migração Gradual (1-3 horas)

#### 2.1 — Estratégia de Migração

Escolha uma estratégia:

| Estratégia | Quando Usar | Esforço |
|------------|-------------|---------|
| **Big Bang** | Histórico pequeno (< 10 sessões) | Alto, mas rápido |
| **Gradual** | Histórico médio (10-50 sessões) | Médio, distribuído |
| **Híbrida** | Histórico grande (> 50 sessões) | Baixo, pragmático |

**Recomendação padrão**: **Gradual**

#### 2.2 — Migração Gradual (Recomendada)

**Semana 1**: Novas sessões já usam formato estruturado

```bash
# Criar sessão de hoje com formato estruturado
mkdir -p docs/SESSIONS/$(date +%Y-%m-%d)
# Use session-manager agent para criação automática
```

**Semana 2+**: Migrar sessões antigas progressivamente (mais recentes primeiro)

```bash
# Preview de migração (dry-run)
python scripts/migrate-daily-activities.py docs/SESSIONS/2026-03-20/ --dry-run

# Aplicar migração em uma sessão específica
python scripts/migrate-daily-activities.py docs/SESSIONS/2026-03-20/

# Migrar múltiplas sessões (recentes primeiro)
for dir in docs/SESSIONS/2026-03-*/; do
  python scripts/migrate-daily-activities.py "$dir"
done
```

**Características da migração**:
- ✅ **Backup automático**: Arquivo original preservado com sufixo `.backup`
- ✅ **Detecção de formato**: Pula arquivos já em formato canônico
- ✅ **Extração inteligente**: Converte campos legados para estrutura canônica
- ✅ **Preservação de conteúdo**: Nada é perdido, apenas reestruturado
- ✅ **Metadata tracking**: Adiciona nota de migração com data

**Exemplo de migração**:
Ver diretório de exemplo: `docs/SESSIONS/EXAMPLE-MIGRATION/`

**Mês 2+**: Manter sessões antigas em formato legado (marcar como legacy)

```bash
# Adicionar marcador em sessões muito antigas (< 2026)
for dir in docs/SESSIONS/202[0-5]-*/; do
  echo "⚠️ **Legacy Format** — This session was not migrated. See SESSION_DOCS_ADOPTION.md for migration guide." > "$dir/README.md"
done
```

#### 2.3 — Migração Big Bang (Histórico Pequeno)

```bash
# Preview: migrar todas as sessões de uma vez
python scripts/migrate-daily-activities.py --all --dry-run

# Aplicar migração completa
python scripts/migrate-daily-activities.py --all

# Validar resultado
python scripts/session-validate.py --all
```

**Quando usar Big Bang**:
- ✅ Histórico pequeno (< 10 sessões)
- ✅ Sessões recentes (últimos 3 meses)
- ✅ Time pequeno (1-2 pessoas)
- ✅ Disponibilidade para revisar todas de uma vez

#### 2.4 — Migração Híbrida (Histórico Grande), marcar)
│   └── README.md                 ← "⚠️ Legacy format"
├── 2026-01-01/ to 2026-02-29/   ← PARTIAL (migrar apenas críticas manualmente)
│   └── ...
└── 2026-03-01/ onwards          ← STRUCTURED (migrar todas)
    └── ...
```

**Implementação:**

```bash
# 1. Marcar sessões muito antigas como legacy
for dir in docs/SESSIONS/202[0-5]-*/; do
  echo "⚠️ **Legacy Format** — Not migrated. Historical reference only." > "$dir/README.md"
done

# 2. Migrar sessões críticas de Q1 2026 manualmente (seletivo)
# Identifique sessões importantes visualmente
ls -1 docs/SESSIONS/2026-0[1-2]-*/

# Migre apenas as importantes
python scripts/migrate-daily-activities.py docs/SESSIONS/2026-01-28/
python scripts/migrate-daily-activities.py docs/SESSIONS/2026-02-15/
# ... etc

# 3. Migrar automaticamente todas de Q2 2026 em diante
for dir in docs/SESSIONS/2026-0[3-9]-*/ docs/SESSIONS/2026-1[0-2]-*/; do
  if [ -d "$dir" ]; then
    python scripts/migrate-daily-activities.py "$dir"
  fi
done
```

**⚡ Performance tip**: Para históricos grandes (> 50 sessões), use dry-run primeiro:

```bash
# Conta quantas sessões serão migradas
python scripts/migrate-daily-activities.py --all --dry-run | grep "Migrated:"

# Se aprovado, rode em paralelo (bash 4.0+)
find docs/SESSIONS -type d -name "2026-*" | \
  parallel -j 4 python scripts/migrate-daily-activities.py {} \
  --end-date 2026-02-29 \
  --filter "IMP-|BUG-|RELEASE"  # apenas sessões com IMPs/BUGs

# 3. Migrar todas de 2026 Q2 em diante
python scripts/migrate-daily-activities.py \
  --start-date 2026-03-01
```

#### 2.5 — Guia Prático do Migration Script

**Nome do script**: `scripts/migrate-daily-activities.py`

**Sintaxe**:
```bash
python scripts/migrate-daily-activities.py <path> [options]
```

**Opções disponíveis**:

| Opção | Descrição |
|-------|-----------|
| `<path>` | Arquivo ou diretório para migrar |
| `--all` | Migrar todas as sessões em `docs/SESSIONS/` |
| `--dry-run` | Preview sem modificar arquivos |
| `--force` | Forçar migração mesmo se já canônico |

**Casos de uso**:

```bash
# 1. Migrar um arquivo específico
python scripts/migrate-daily-activities.py \
  docs/SESSIONS/2026-03-20/DAILY_ACTIVITIES_2026-03-20.md

# 2. Migrar todos arquivos de um diretório de sessão
python scripts/migrate-daily-activities.py \
  docs/SESSIONS/2026-03-20/

# 3. Preview de migração completa (recomendado primeiro)
python scripts/migrate-daily-activities.py --all --dry-run

# 4. Migração completa de todas sessões
python scripts/migrate-daily-activities.py --all

# 5. Forçar re-migração de arquivo já migrado
python scripts/migrate-daily-activities.py \
  docs/SESSIONS/2026-03-20/ --force
```

**Comportamento do script**:

1. **Detecção de formato**: Identifica automaticamente se arquivo é:
   - `TODAY_ACTIVITIES` (formato muito antigo)
   - `DAILY_ACTIVITIES` legado (formato antigo estruturado)
   - `DAILY_ACTIVITIES` semi-canônico (campos mas sem separadores)
   - `DAILY_ACTIVITIES` canônico (formato atual)

2. **Backup automático**: Cria arquivo `.backup` antes de modificar

3. **Extração e conversão**:
   - Extrai blocos de atividade do formato legado
   - Converte para formato canônico com separadores `---`
   - Adiciona campos obrigatórios faltantes (inferidos ou placeholder)
   - Preserva todo conteúdo original

4. **Metadata**: Adiciona nota de migração com data no cabeçalho

5. **Validação**: Pode ser validado após com `session-validate.py`

**Output do script**:

```
Processing: docs/SESSIONS/2026-01-28/TODAY_ACTIVITIES_2026-01-28.md
✓ Backup created: TODAY_ACTIVITIES_2026-01-28.md.backup
✓ Migrated: 4 block(s) → canonical format

============================================================
Migration Summary
============================================================
✓ Migrated: 1
⊘ Skipped:  0
✗ Failed:   0
Total:     1
```

**Ver exemplo completo**: [docs/SESSIONS/EXAMPLE-MIGRATION/](SESSIONS/EXAMPLE-MIGRATION/)

---

### Fase 3: Validação (30 minutos)

#### 3.1 — Validar Formato Estruturado

```bash
# Validar todas as sessões migradas
make session-validate

# Ou validar intervalo específico
python scripts/session-validate.py docs/SESSIONS/2026-03-*
```

**Resultado esperado:**
```
✅ All validations passed!
Files validated: 15
Blocks validated: 87
Errors: 0
Warnings: 2
```

**Se houver erros:**
- Revisar mensagens de erro no output
- Corrigir manualmente ou ajustar script de migração
- Re-validar após correções

#### 3.2 — Scan de Segurança Pós-Migração

```bash
# Verificar se migração não introduziu exposições
make session-sanitize

# Ou específico para sessões migradas
gitleaks detect \
  --config .gitleaks-session-docs.toml \
  --source docs/SESSIONS/2026-03-* \
  --verbose
```

#### 3.3 — Smoke Tests

```bash
# 1. Verificar que blocos foram criados corretamente
grep -r "^### " docs/SESSIONS/2026-03-*/DAILY_ACTIVITIES_*.md | wc -l
# Esperado: número de atividades migradas

# 2. Verificar que campos obrigatórios estão presentes
grep -r "\*\*Objetivo\*\*:" docs/SESSIONS/2026-03-*/DAILY_ACTIVITIES_*.md | wc -l
grep -r "\*\*Contexto\*\*:" docs/SESSIONS/2026-03-*/DAILY_ACTIVITIES_*.md | wc -l
grep -r "\*\*Status\*\*:" docs/SESSIONS/2026-03-*/DAILY_ACTIVITIES_*.md | wc -l

# 3. Verificar separadores
grep -r "^---$" docs/SESSIONS/2026-03-*/DAILY_ACTIVITIES_*.md | wc -l
```

---

### Fase 4: Integração com Workflow (1 hora)

#### 4.1 — Atualizar .copilot-rules.md

Adicionar ou atualizar regra P1:

```markdown
### P1 — Documentação de Sessão

- **SEMPRE** usar formato estruturado definido em `docs/SESSION_DOCS_STYLE_GUIDE.md`
- **NUNCA** criar blocos sem campos obrigatórios (Objetivo, Contexto, Passos, Resultado, Status)
- **SEMPRE** validar antes de commitar: `make session-validate`
- **SEMPRE** sanitizar antes de commitar: `make session-sanitize`
```

#### 4.2 — Configurar Git Hooks (Opcional)

**Pre-commit hook** para validação automática:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Validar session docs se houver mudanças em docs/SESSIONS/
if git diff --cached --name-only | grep -q "docs/SESSIONS/.*\.md$"; then
  echo "🔍 Validating session documentation..."

  if ! make session-validate > /dev/null 2>&1; then
    echo "❌ Session documentation validation failed"
    echo "Run 'make session-validate' to see errors"
    exit 1
  fi

  if ! make session-sanitize > /dev/null 2>&1; then
    echo "❌ Sensitive data detected in session docs"
    echo "Run 'make session-sanitize' to see details"
    exit 1
  fi

  echo "✅ Session documentation validated"
fi
```

**Ativar hook:**

```bash
chmod +x .git/hooks/pre-commit
```

#### 4.3 — CI/CD Integration (Se aplicável)

Se o projeto usa GitHub Actions, adicionar job:

```yaml
# .github/workflows/ci.yml
session-docs-scan:
  name: Session Docs Security Scan
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Install gitleaks
      run: |
        wget -qO- https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz | tar xvz
        sudo mv gitleaks /usr/local/bin/
    - name: Scan session docs
      run: make session-sanitize
```

Ver template completo em: `.github/templates/ci-jobs/SESSION_DOCS_SCAN_JOB.md`

---

### Fase 5: Treinamento e Roll-out (variável)

#### 5.1 — Treinamento do Time

**Sessão de onboarding** (1 hora recomendada):

1. **Apresentar o problema** (10 min)
   - Por que documentação estruturada?
   - Custos de contexto perdido

2. **Demonstrar o sistema** (20 min)
   - Live coding: criar bloco de atividade
   - Mostrar validação: `make session-validate`
   - Mostrar security scan: `make session-sanitize`

3. **Hands-on** (20 min)
   - Cada membro cria 1 bloco fictício
   - Validar em tempo real

4. **Q&A** (10 min)

**Material de referência:**
- `docs/SESSION_DOCS_STYLE_GUIDE.md` (sempre aberto durante sessões)
- `.github/prompts/session-start.prompt.md` (ritual de início)
- `.github/prompts/session-end.prompt.md` (ritual de fim)

#### 5.2 — Comunicação de Roll-out

**Anúncio interno** (template):

```
📢 Novo Sistema de Documentação de Sessões

A partir de [DATA], estamos adotando documentação estruturada de sessões.

O que muda:
- Formato: blocos estruturados com campos obrigatórios
- Validação: automática antes de commits
- Segurança: scan automático de dados sensíveis

Benefícios:
✅ Contexto nunca perdido
✅ Reprodutibilidade de trabalhos
✅ Onboarding mais rápido

Documentação: docs/SESSION_DOCS_STYLE_GUIDE.md
Dúvidas: @lead-engineer
```

#### 5.3 — Monitoramento Pós-Adoção

**Primeiras 2 semanas:**

```bash
# Verificar adoção semanal
for week in 1 2; do
  echo "Week $week:"
  find docs/SESSIONS/2026-04-* -name "DAILY_ACTIVITIES_*.md" | \
    xargs python scripts/session-validate.py 2>&1 | \
    grep -E "(validated|Errors|Warnings)"
done
```

**Métricas de sucesso:**
- ✅ 100% de sessões novas em formato estruturado
- ✅ < 5 warnings por sessão em média
- ✅ 0 exposições de dados sensíveis

---

## 🛠️ Troubleshooting

### Problema 1: Migração falha com erros de parsing

**Sintoma:**
```
ERROR: Failed to parse block at line 42: invalid markdown structure
```

**Solução:**
```bash
# 1. Identificar sessão problemática
python scripts/migrate-daily-activities.py --debug [caminho-sessao]

# 2. Corrigir manualmente o arquivo original
# 3. Re-executar migração
```

### Problema 2: Muitos warnings após migração

**Sintoma:**
```
⚠️ Warnings: 45
```

**Solução:**
- Warnings são aceitáveis em migração de legado
- Priorizar correção de **erros** (formato quebrado)
- Warnings podem ser corrigidos gradualmente

### Problema 3: Scan de segurança detecta falsos positivos

**Sintoma:**
```
❌ private_ip_10: 10.0.0.1 detected
```

**Solução:**

Se for exemplo válido (sanitizado):

```bash
# Adicionar ao allowlist em .gitleaks-session-docs.toml
[allowlist]
regexes = [
  # ... existing patterns
  '''10\.0\.0\.1''',  # example IP from migration
]
```

### Problema 4: Time não está adotando o formato

**Sintoma:**
- Sessões continuam em formato freeform
- Commits sem validação

**Solução:**

1. **Reforçar com automation:**
   ```bash
   # Ativar pre-commit hook obrigatório
   chmod +x .git/hooks/pre-commit
   ```

2. **Revisão de código:**
   - PR reviews devem verificar formato
   - Usar template de PR checklist

3. **Incentivos:**
   - Reconhecer boas práticas em reuniões
   - Mostrar casos de sucesso (contexto recuperado rapidamente)

---

## 📊 Checklist de Adoção Completa

### Preparação
- [ ] Backup do histórico existente criado
- [ ] Inventário de sessões completo
- [ ] Scan de segurança no histórico executado
- [ ] Ferramentas instaladas (Python, gitleaks, yamllint)

### Migração
- [ ] Estratégia de migração escolhida (Big Bang / Gradual / Híbrida)
- [ ] Script de migração testado com `--dry-run`
- [ ] Sessões migradas com sucesso
- [ ] Sessões legadas marcadas (se aplicável)

### Validação
- [ ] `make session-validate` passou sem erros
- [ ] `make session-sanitize` passou sem violações
- [ ] Smoke tests executados e aprovados

### Integração
- [ ] `.copilot-rules.md` atualizado com regra P1
- [ ] Git hooks configurados (opcional)
- [ ] CI/CD integrado com session-docs-scan (opcional)

### Treinamento
- [ ] Sessão de onboarding realizada
- [ ] Material de referência distribuído
- [ ] Comunicação de roll-out enviada

### Monitoramento
- [ ] Métricas de adoção definidas
- [ ] Monitoramento semanal configurado
- [ ] Processo de feedback ativo

---

## 🎓 Próximos Passos

Após adoção completa:

1. **Melhoria Contínua**
   - Revisar style guide trimestralmente
   - Atualizar allowlist de gitleaks conforme necessário
   - Coletar feedback do time

2. **Expansão**
   - Considerar IMP-51: Busca e indexação MCP (memória aprimorada)
   - Integrar com ferramentas de relatório (Confluence, Notion)

3. **Governança**
   - Definir responsável pela manutenção do sistema
   - Documentar alterações no CHANGELOG.md
   - Versionamento do style guide

---

## 📚 Referências

- [SESSION_DOCS_STYLE_GUIDE.md](SESSION_DOCS_STYLE_GUIDE.md) - Formato canônico
- [SECURITY_SESSION_DOCS.md](SECURITY_SESSION_DOCS.md) - Exemplos de segurança
- [CI-CD-RESTORATION-GUIDE.md](CI-CD-RESTORATION-GUIDE.md) - Integração CI
- [.gitleaks-session-docs.toml](../.gitleaks-session-docs.toml) - Config de scan
- [scripts/session-validate.py](../scripts/session-validate.py) - Validador
- [scripts/migrate-daily-activities.py](../scripts/migrate-daily-activities.py) - Migração

---

*Adoption Guide v1.0 | IMP-50 | 2026-04-03*
