# 📋 Guia de Gestão de Issues e Features

**Projeto**: Enterprise Scaffold Project Template
**Criado em**: 2026-04-03
**Público-alvo**: Desenvolvedores, DevOps, Mantenedores

---

## 🎯 Visão Geral

Este documento explica como gerenciar **bugs**, **features** e **melhorias** no projeto, seguindo práticas DevOps modernas.

---

## 📚 Conceitos

### 1. Bug (Defeito)

**O que é**: Comportamento incorreto ou não esperado do sistema que já existe.

**Quando usar**:
- ❌ Algo que deveria funcionar mas não funciona
- ❌ Erro, exception, crash
- ❌ Comportamento inconsistente com a documentação
- ❌ Regressão (algo que funcionava e parou)

**Template**: `.github/ISSUE_TEMPLATE/bug_report.md`

**Exemplo real deste projeto**:
```
[bug] BUG-01 Recurrence: Tilde expansion missing in CI mode
- Problema: Modo CI não expande ~ em --target-dir
- Sintoma: Cria estrutura literal ~/Documentos/...
- Prioridade: P0 (bloqueia CI mode)
```

---

### 2. Feature (Nova Funcionalidade)

**O que é**: Capacidade nova que o sistema **não tinha** antes.

**Quando usar**:
- ✨ Adicionar novo comando, API, ou módulo
- ✨ Integrar com ferramenta externa
- ✨ Nova opção de configuração
- ✨ Expandir domínio de funcionalidade

**Template**: `.github/ISSUE_TEMPLATE/feature_request.md`

**Exemplo real deste projeto**:
```
[feat] IMP-49: Sistema de documentação incremental — Integração
- Adiciona integração com prompts de sessão
- Adiciona job de CI para scan de documentação
- Cria CLI session-validate.py
```

---

### 3. Improvement (Melhoria / Tech Debt)

**O que é**: Refatoração, otimização ou redução de débito técnico sem mudar funcionalidade externa.

**Quando usar**:
- 🔧 Refatorar código existente
- 🔧 Melhorar performance
- 🔧 Atualizar dependências
- 🔧 Simplificar arquitetura
- 🔧 Melhorar testes ou documentação

**Template**: `.github/ISSUE_TEMPLATE/improvement.md`

**Exemplo real deste projeto**:
```
[improve] IMP-38: Refatorar scaffold.py — extrair flows
- Contexto: scaffold.py está com ~900 linhas
- Proposta: Extrair cada flow_*() para módulo dedicado
- Motivação: Maintainability + reduzir complexidade
```

---

## 🗂️ Onde Documentar Problemas e Features

### Opção 1: GitHub Issues (Recomendado para colaboração)

**Quando usar**:
- ✅ Projeto versionado no GitHub
- ✅ Precisa de discussão com time
- ✅ Precisa rastrear assignees, labels, milestones
- ✅ Integrar com CI/CD e automações

**Como criar**:

1. **Via GitHub Web Interface**:
   ```
   Repositório → Issues → New Issue → Escolher template
   ```

2. **Via GitHub CLI** (gh):
   ```bash
   # Bug
   gh issue create --template bug_report.md \
     --title "[bug] Descrição curta" \
     --label bug

   # Feature
   gh issue create --template feature_request.md \
     --title "[feat] Descrição curta" \
     --label enhancement

   # Improvement
   gh issue create --template improvement.md \
     --title "[improve] Descrição curta" \
     --label improvement
   ```

---

### Opção 2: docs/TODO.md (Tracking interno)

**Quando usar**:
- ✅ Trabalho solo ou pequeno time
- ✅ Não precisa de discussão externa
- ✅ Rastreamento rápido e markdown simples
- ✅ Integrado com sessões de trabalho

**Estrutura**:
```markdown
### 🔴 P0 — Quick wins (alta prioridade)

- [ ] **[BUG-03]** Descrição do bug
  - **Problema**: O que está errado
  - **Causa raiz**: Por que acontece
  - **Correção proposta**: Como resolver
  - **Impacto**: P0/P1/P2
  - *Reportado em*: YYYY-MM-DD

- [ ] **[IMP-52]** Descrição da melhoria
  - **Contexto**: Estado atual
  - **Proposta**: O que mudar
  - **Motivação**: Por que fazer agora
  - **Estimativa**: 2h/4h/8h
```

**Prioridades no TODO.md**:
- 🔴 **P0** — Bloqueadores, bugs críticos (executar imediatamente)
- 🟡 **P1** — Importante, alto impacto (próximo sprint)
- 🔵 **P2** — Qualidade técnica (sprint +2)
- ⚪ **P3** — Futuro, breaking changes, opt-in

---

### Opção 3: tmp/lembrete.md (Rascunho temporário)

**Quando usar**:
- ✅ Captura rápida durante uma sessão
- ✅ Ideias não estruturadas ainda
- ✅ Precisa revisão antes de virar issue/todo

**Processo**:
1. Anotar em `tmp/lembrete.md` durante o trabalho
2. Ao final da sessão: converter para TODO.md ou GitHub Issue
3. Limpar o lembrete.md (mover para doc permanente)

---

## 🔄 Workflow Recomendado

### 1. Captura (Durante o Trabalho)

```bash
# Usar lembrete.md para captura rápida
echo "- adicionar validação de YAML em scaffold" >> tmp/lembrete.md
```

### 2. Triagem (Fim da Sessão)

Revisar `tmp/lembrete.md` e decidir:

| Critério | Destino |
|----------|---------|
| Bug crítico que bloqueia | → TODO.md P0 + GitHub Issue |
| Bug não-crítico | → TODO.md P1 |
| Feature grande com discussão | → GitHub Issue |
| Melhoria técnica | → TODO.md P1 ou P2 |
| Ideia vaga | → Manter no lembrete ou descartar |

### 3. Documentação (Formato Padronizado)

**Para TODO.md**:
```markdown
- [ ] **[BUG-03]** Título curto e claro
  - **Problema**: O que está errado
  - **Causa raiz**: Por que acontece
  - **Correção proposta**: Como resolver
  - **Arquivos modificados**: lista de arquivos
  - **Testes**: como validar a correção
  - **Impacto**: P0 (bloqueador) / P1 (importante) / P2 (pode esperar)
  - *Reportado em*: 2026-04-03
```

**Para GitHub Issue**:
- Usar os templates em `.github/ISSUE_TEMPLATE/`
- Preencher **todas** as seções
- Adicionar labels apropriadas
- Linkar issues relacionadas

### 4. Implementação → Documentação

Ao resolver um item:
```markdown
- [x] **[BUG-03]** Título ✅ **RESOLVIDO** (YYYY-MM-DD)
  - **Problema**: ...
  - **Correção implementada**: O que foi feito
  - **Arquivos modificados**: lista
  - **Commit**: hash do commit
  - *Reportado em*: YYYY-MM-DD | *Resolvido em*: YYYY-MM-DD
```

---

## 🔍 Análise do lembrete.md Atual

**Arquivo**: `tmp/lembrete.md` (2026-04-03)

```
1 - adicionar instruções para usar as ferramentas jsonschema e yamllint já disponíveis.
2 - não foi gerado o .github/copilot-instructions.md com as instruções básicas existentes.
3 -
```

### Triagem e Conversão

#### Item 1: Instruções para jsonschema e yamllint

**Tipo**: 🔧 Improvement (documentação)
**Prioridade**: P1
**Destino recomendado**: TODO.md

**Formato sugerido**:
```markdown
- [ ] **[IMP-52]** Adicionar instruções de uso para jsonschema e yamllint
  - **Contexto**: Ferramentas já estão disponíveis no projeto mas não há doc de uso
  - **Proposta**: Criar seção no README.md ou docs/DEVELOPMENT_GUIDE.md
  - **Seções necessárias**:
    - Instalar: `pip install jsonschema yamllint` ou `npm install -D ...`
    - Validar YAML: `yamllint .github/workflows/`
    - Validar JSON schema: `jsonschema -i arquivo.json schema.json`
    - Integrar com make lint
  - **Estimativa**: 2h
  - *Reportado em*: 2026-04-03
```

---

#### Item 2: copilot-instructions.md não gerado

**Tipo**: ❌ Bug (geração de arquivo)
**Prioridade**: P0 (funcionalidade do scaffold quebrada)
**Destino recomendado**: TODO.md P0 + investigação imediata

**Formato sugerido**:
```markdown
- [ ] **[BUG-03]** .github/copilot-instructions.md não é gerado durante scaffold
  - **Problema**: Projeto gerado não contém `.github/copilot-instructions.md`
  - **Comportamento esperado**: Arquivo deve ser criado com instruções básicas do template
  - **Causa raiz investigada**:
    - Verificar `scripts/lib/templates.py:generate_copilot_instructions()`
    - Verificar se há template source em template root
    - Verificar logs de criação de projeto
  - **Reprodução**:
    ```bash
    python scripts/scaffold.py new --ci --name test-project \
      --domain programming --language python --target-dir ./tmp
    ls -la ./tmp/test-project/.github/copilot-instructions.md
    # Resultado: arquivo não existe
    ```
  - **Impacto**: P0 (projetos gerados sem instruções básicas para Copilot)
  - **Arquivos para investigar**:
    - `scripts/lib/templates.py`
    - `scripts/lib/flows/new_project.py`
    - `.github/copilot-instructions.md` (template source)
  - *Reportado em*: 2026-04-03
```

---

#### Item 3: (vazio)

**Ação**: Descartar ou aguardar preenchimento

---

## 📊 Labels Recomendadas (GitHub)

| Label | Uso | Cor |
|-------|-----|-----|
| `bug` | Defeito, erro | 🔴 `d73a4a` |
| `enhancement` | Nova feature | 🟢 `a2eeef` |
| `improvement` | Refactor, tech debt | 🟡 `fbca04` |
| `documentation` | Melhorias de docs | 📘 `0075ca` |
| `p0-critical` | Bloqueador | 🔥 `b60205` |
| `p1-high` | Alta prioridade | 🟠 `d93f0b` |
| `p2-medium` | Média prioridade | 🟡 `fbca04` |
| `p3-low` | Baixa prioridade | ⚪ `c5def5` |
| `good-first-issue` | Fácil para iniciantes | 🌱 `7057ff` |
| `help-wanted` | Precisa de ajuda | 💬 `008672` |

---

## 🛠️ Ferramentas e Automações

### GitHub CLI (gh)

```bash
# Instalar gh
brew install gh   # macOS
sudo apt install gh  # Ubuntu

# Autenticar
gh auth login

# Criar issue
gh issue create --template bug_report.md

# Listar issues
gh issue list --label p0-critical

# Fechar issue
gh issue close 123 --comment "Resolvido no commit abc123"
```

### Makefile Targets (Sugestão)

```makefile
# Adicionar ao Makefile do projeto
.PHONY: issue-bug issue-feat issue-improve

issue-bug:
	@gh issue create --template bug_report.md --label bug,p1-high

issue-feat:
	@gh issue create --template feature_request.md --label enhancement

issue-improve:
	@gh issue create --template improvement.md --label improvement
```

---

## 📝 Checklist de Boa Prática

Ao criar um Bug/Feature/Improvement:

- [ ] Título claro e conciso (< 80 chars)
- [ ] Descrição completa (contexto + proposta)
- [ ] Passos de reprodução (para bugs)
- [ ] Critérios de sucesso definidos
- [ ] Prioridade atribuída (P0/P1/P2/P3)
- [ ] Estimativa de esforço (2h/4h/8h/1d/1w)
- [ ] Arquivos/componentes afetados listados
- [ ] Links para documentação relevante
- [ ] Labels apropriadas (GitHub)
- [ ] Assignee definido (se aplicável)

---

## 🎓 Referências

- [GitHub Issues Documentation](https://docs.github.com/en/issues)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- Documentação do projeto: `docs/TODO.md`, `CHANGELOG.md`

---

**Última atualização**: 2026-04-03
**Mantenedor**: Enterprise Scaffold Project Template Team
