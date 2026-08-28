# 🎭 Debate de Arquitetura — Melhorias no Sistema de Memórias e Session-Start

**Data**: 2026-05-18
**Participantes**:
- Principal Software Engineer
- SE: Architect
- DevOps Expert

**Tópicos**:
1. Análise e limpeza de memórias (`/memories/` e `.memory/`)
2. Implementação de processo de atualização segura de pacotes no session-start
3. Melhorias baseadas na validação do test-workspace-fix (BUG-20)

---

## 📋 Sumário Executivo

### Decisões Principais

| Decisão | Consenso | Ação | Prioridade |
|---------|----------|------|------------|
| **Limpar memórias contaminadas** | ✅ Unânime | Deletar enterprise-ansible.md + 37 arquivos de teste | 🔴 P0 |
| **Criar memória do projeto atual** | ✅ Unânime | Criar /memories/scaffold-project.md | 🔴 P0 |
| **Adicionar verificação de pacotes** | ✅ Com modificações | Passo 4.5 acionável (não apenas informativo) | 🔴 P0 |
| **Automação de cleanup** | ✅ Unânime | Script memory-cleanup.py com dry-run | 🔴 P0 |
| **Pre-commit hooks** | ✅ Unânime | Bloquear commit de arquivos de teste | 🟡 P1 |
| **CI/CD dependency check** | ✅ Unânime | GitHub Actions semanal + PR validation | 🟡 P1 |
| **Session-start quick mode** | ⚠️ Em discussão | Modo P0-only opcional | 🟢 P2 |

---

## 🎯 Problema 1: Memórias Contaminadas e Duplicadas

### Análise do Principal Software Engineer

**Descobertas críticas**:

1. **Memória de outro projeto** (`/memories/enterprise-ansible.md`):
   - Conteúdo: Projeto Ansible (VPS, SSH SPA, Cloudflare ZTA)
   - Impacto: ~800 tokens de contexto incorreto em TODAS as sessões
   - Severidade: 🔴 CRÍTICA (poluição cross-workspace)

2. **37 arquivos de teste duplicados** (`.memory/memories/project/`):
   - Datas: 2026-04-20, 04-28, 05-11, 05-12, 05-17
   - Conteúdo: "This is a test memory" (idêntico entre versões)
   - Impacto: ~2.300 tokens desperdiçados + poluição de índice FTS5
   - Severidade: 🔴 CRÍTICA (problema recorrente)

3. **Memórias de test-workspace** incorretas:
   - Referem-se a `/home/yves_marinho/DevOps/Projetos/test-workspace-fix`
   - Workspace atual: `...Projetos/scaffold-project`
   - Severidade: 🟠 ALTA (dados obsoletos)

**Recomendações P0**:
```
1. Deletar /memories/enterprise-ansible.md (memory tool)
2. Deletar 37 arquivos de teste via Python stdlib
3. Criar /memories/scaffold-project.md com dados corretos
4. Deletar /memories/repo/test-workspace*.md
```

**Impacto esperado**:
- Redução de ~3.420 tokens de ruído
- Aumento de precisão do Copilot (contexto correto)
- Prevenção de confusão entre projetos

---

### Perspectiva do SE: Architect

**Concordâncias**:
- ✅ Problema é real e quantificado (dados comprovam)
- ✅ Impacto no contexto do Copilot é significativo
- ✅ Necessidade de limpeza imediata

**Contribuições adicionais**:

**Estratégia de prevenção**:
1. **Test fixtures isolados** → testes NUNCA tocam `.memory/` real
2. **Memory scope enforcement** → detectar memórias repo-specific em user scope
3. **Documentação clara** → `docs/MEMORY_SYSTEM.md` com boas práticas

**Proposta de implementação**:
```python
# tests/conftest.py
@pytest.fixture
def temp_memory_dir(tmp_path):
    """Isolated memory directory for tests"""
    memory_dir = tmp_path / ".memory" / "memories"
    memory_dir.mkdir(parents=True)
    yield memory_dir
    # Cleanup automático via tmp_path
```

**Benefício**: Zero poluição futura de arquivos de teste.

---

### Perspectiva do DevOps Expert

**Concordâncias**:
- ✅ Problema validado (35+ arquivos comprovados)
- ✅ Escopo de memória violado (enterprise-ansible em user memory)
- ✅ Automação é essencial (problema sistêmico)

**Contribuições críticas**:

**🔴 RISCO IDENTIFICADO**: Se ocorreu aqui, ocorrerá em **todos os projetos** criados via scaffold.

**Proposta de automação defensiva**:

1. **Script `memory-cleanup.py`** com:
   - Dry-run por padrão (segurança)
   - Backup automático antes de executar
   - Detecção de duplicados por hash de conteúdo
   - Logs detalhados (auditoria)

2. **Pre-commit hook** (`validate-memory`):
   - Bloquear commit de `test-*.md` em `.memory/`
   - Validar YAML frontmatter antes de commit
   - Exit code 1 se violações detectadas

3. **Makefile targets**:
```makefile
memory-cleanup:        ## Dry-run (mostra o que seria removido)
	python scripts/memory-cleanup.py

memory-cleanup-force:  ## Executar com backup automático
	python scripts/memory-cleanup.py --execute --backup
```

**Rollback rápido** (<10s):
```bash
# Se algo der errado
./scripts/memory-rollback.sh
# Restaura último backup automaticamente
```

**Observabilidade**:
- Logs em `logs/memory-cleanup.log`
- Métricas: arquivos removidos, duplicados detectados, tempo de execução

---

## 🎯 Problema 2: Atualização de Pacotes no Session-Start

### Análise do SE: Architect

**Contexto do sistema**:
- 1 dependência principal: `deepmerge>=1.1.0`
- 7 deps de dev: pytest, black, ruff, mypy, etc.
- 2 deps de security: bandit, safety
- ❌ **Lock file ausente** (pip install sem versões fixas)

**Prós e contras avaliados**:

| Aspecto | Prós | Contras |
|---------|------|---------|
| **Segurança** | ✅ Patches automáticos | ❌ Breaking changes inesperados |
| **Consistência** | ✅ Ambientes atualizados | ❌ Sem lock file = imprevisível |
| **DX** | ✅ Detecção precoce | ❌ Lentidão no start |

**Cenário catastrófico identificado**:
```
09:00 → session-start atualiza pytest 8.0 → 9.0 (breaking)
09:15 → Desenvolve feature
10:00 → CI/CD falha (prod ainda usa pytest 8.0)
10:30 → Rollback manual, perda de 1.5h
```

**Alternativas avaliadas**:

1. **Pre-commit hook local**: Avisos antes de commit (passivo)
2. **CI/CD weekly job**: Automatizado, não impacta dev (recomendado)
3. **Manual mensal**: Controle total mas frequentemente esquecido
4. **Check informativo**: Zero risco mas requer ação manual

**Decisão arquitetural proposta**: ADR-001 — Verificação Híbrida

```yaml
Status: Proposto
Decisão: Passo 4.5 INFORMATIVO + CI/CD semanal automatizado

Implementação:
  session-start:
    - Verificar pacotes desatualizados (JSON parsing)
    - Alertar sobre bandit/safety/pytest desatualizados
    - NÃO atualizar automaticamente
    - Sugerir 'make update-deps-safe'

  ci-cd:
    - Weekly check (segundas 02:00)
    - Auto-merge security patches (após CI verde)
    - PR para minor/major updates (revisão manual)

Duração: ~3-5s (aceitável)
```

**Novo Makefile target**:
```makefile
update-deps-safe:
	@echo "🔍 Atualizando dependências de segurança..."
	pip install --upgrade bandit safety
	pytest tests/test_memory_smoke.py -v
```

**Justificativa**:
- Segurança proativa ✅
- Zero risco de breaking changes durante sessão ✅
- Controle total sobre quando atualizar ✅
- Escalável para CI/CD futuro ✅

---

### Perspectiva do DevOps Expert

**Concordâncias**:
- ✅ Verificação de pacotes é importante (segurança)
- ✅ Session-start é lugar certo (preventivo > reativo)

**❌ DISCORDÂNCIA (respeitosa)**:

**Problema com "Passo 4.5 informativo"**:
- Informar sem ação → **fadiga de checklist**
- Usuário ignora warnings repetitivos
- Session-start já tem 8 passos (~15s de execução)

**Proposta alternativa**: Passo 4.5 **ACIONÁVEL**

```bash
# session-start Passo 4.5
make deps-check
# Se vulnerabilidades P0 → FALHA (bloqueia sessão)
# Se vulnerabilidades P1/P2 → WARNING (permite continuar)
# Se tudo OK → ✅ (silencioso)
```

**Implementação**:
```bash
pip list --outdated --format=json | python -c "
import sys, json
data = json.load(sys.stdin)
critical = [p for p in data if p['name'] in ['bandit', 'safety']]
if critical:
    print('🚨 VULNERABILIDADES CRÍTICAS!')
    for p in critical:
        print(f\"  {p['name']}: {p['version']} → {p['latest_version']}\")
    print('\n⚠️  Execute: make update-deps-safe')
    sys.exit(1)  # Bloqueia sessão
print('✅ Dependências de segurança atualizadas')
"
```

**Benefícios sobre abordagem informativa**:
1. **Força ação** quando há vulnerabilidades críticas
2. **Não interrompe** quando tudo está OK
3. **Visibilidade clara** do problema (exit code 1)
4. **Automatizável** em CI/CD (mesma lógica)

**Métricas propostas**:
- Tempo de execução do Passo 4.5 (meta: <5s)
- Frequência de vulnerabilidades detectadas
- MTTR (Mean Time To Remediation)

**CI/CD complementar**:
```yaml
# .github/workflows/dependency-check.yml
schedule:
  - cron: '0 9 * * MON'  # Segundas 9h

jobs:
  check-deps:
    - pip list --outdated --format=json
    - pip-audit --format json  # CVE scanning
    - Se vulnerabilities > 0 → criar issue P0
```

**Rollback strategy**:
```bash
# Se update quebrou
git revert <commit-hash>
pip install -r requirements.txt
```

**Pinning estratégico**:
```toml
[project.dependencies]
deepmerge = "^1.1.0"     # Stable, permite minor updates
pytest = "~7.4.0"        # Pin minor, apenas patches
fastapi = "0.104.1"      # Exact (breaking changes comuns)
black = "*"              # Formatter, pode atualizar livremente
```

---

### Consenso Final (Problema 2)

**Decisão aprovada por 3/3 agentes**:

✅ **Implementar Passo 4.5 acionável** (proposta DevOps)
✅ **CI/CD semanal automatizado** (proposta Architect)
✅ **Makefile target update-deps-safe** (proposta Architect)
✅ **Rollback automation** (proposta DevOps)

**Modificação da proposta original**:
- ❌ Informativo → ✅ **Acionável** (exit 1 se vulnerabilidades P0)
- ✅ Mantém duração <5s
- ✅ Adiciona métricas de observabilidade

---

## 🎯 Problema 3: Melhorias Baseadas em BUG-20

### Contexto

**BUG-20**: Scaffold upgrade não aplicou MCP GitHub HTTP update
**Causa raiz provável**: Merge strategy shallow (preserva chaves existentes)
**Impacto**: Performance 88% pior, Memória 95% maior, Segurança PAT vs OAuth

### Análise do Principal Software Engineer

**Lições aprendidas**:
1. Merge strategy precisa detectar **breaking changes estruturais**
2. Logs podem ser enganosos ("merged" mas não aplicou)
3. Backups prometidos devem ser criados (validação pós-merge)

**Recomendações para session-start**:
- Validar que arquivos críticos estão atualizados
- Detectar configurações obsoletas (ex: MCP CLI vs HTTP)

---

### Perspectiva do DevOps Expert

**Proposta de health check**:

```bash
# Passo 1.5 — Verificar configurações críticas
make config-validate

# Implementação
config-validate:
	@python scripts/validate-configs.py \
		--check mcp.json \
		--check pyproject.toml \
		--check .copilot-rules.md
```

**Script `validate-configs.py`**:
```python
def validate_mcp_config():
    """Detect obsolete MCP configurations"""
    mcp_file = Path(".vscode/mcp.json")
    config = json.loads(mcp_file.read_text())

    # Check GitHub server
    github = config.get("servers", {}).get("github", {})

    if github.get("type") == "stdio" and "command" in github:
        log.error("❌ MCP GitHub usando configuração CLI obsoleta")
        log.info("💡 Execute: make mcp-update-github-http")
        return False

    if github.get("type") == "http":
        log.info("✅ MCP GitHub configuração HTTP (moderna)")
        return True
```

**Benefícios**:
- Detecção proativa de configurações obsoletas
- Previne problemas como BUG-20
- Automatizável (CI/CD pode rodar mesma validação)

---

## 📊 Tabela Consolidada de Decisões

| # | Decisão | Consenso | Prioridade | Estimativa | Owner |
|---|---------|----------|------------|------------|-------|
| 1 | Deletar `/memories/enterprise-ansible.md` | ✅ 3/3 | 🔴 P0 | 5 min | Agent |
| 2 | Limpar 37 arquivos de teste (`.memory/project/`) | ✅ 3/3 | 🔴 P0 | 10 min | Agent |
| 3 | Criar `/memories/scaffold-project.md` | ✅ 3/3 | 🔴 P0 | 20 min | Agent |
| 4 | Deletar `/memories/repo/test-workspace*.md` | ✅ 3/3 | 🔴 P0 | 5 min | Agent |
| 5 | Criar `scripts/memory-cleanup.py` | ✅ 3/3 | 🔴 P0 | 2h | DevOps |
| 6 | Implementar Passo 4.5 (deps check acionável) | ✅ 3/3 | 🔴 P0 | 1h | Architect |
| 7 | Criar Makefile target `update-deps-safe` | ✅ 3/3 | 🔴 P0 | 30 min | DevOps |
| 8 | Implementar test fixtures isolados | ✅ 3/3 | 🔴 P0 | 1h | SE |
| 9 | Pre-commit hook `validate-memory` | ✅ 3/3 | 🟡 P1 | 1h | DevOps |
| 10 | GitHub Actions dependency check | ✅ 3/3 | 🟡 P1 | 2h | DevOps |
| 11 | Script `validate-configs.py` (BUG-20) | ✅ 3/3 | 🟡 P1 | 1.5h | DevOps |
| 12 | Documentar `docs/MEMORY_SYSTEM.md` | ✅ 3/3 | 🟡 P1 | 1h | SE |
| 13 | Session-start quick mode (opcional) | ⚠️ 2/3 | 🟢 P2 | 3h | Architect |
| 14 | Dashboard de métricas (Grafana/HTML) | ⚠️ 2/3 | 🟢 P2 | 8h | DevOps |

**Legenda**:
- 🔴 P0: Executar imediatamente (< 24h)
- 🟡 P1: Executar esta sprint (< 1 semana)
- 🟢 P2: Backlog (próximos 2 meses)

---

## 🚀 Próximos Passos Imediatos

### Sprint Atual (Esta Sessão)

**P0 — Executar AGORA** (Estimativa: 1-2h):

1. ✅ Limpar memórias contaminadas (items 1-4)
2. ✅ Criar `scripts/memory-cleanup.py` (item 5)
3. ✅ Implementar Passo 4.5 em `session-start.prompt.md` (item 6)
4. ✅ Criar Makefile target `update-deps-safe` (item 7)
5. ✅ Implementar test fixtures isolados (item 8)

**Commits esperados**:
- `fix: Limpar memórias contaminadas + criar scaffold-project.md`
- `feat(session-start): Adicionar Passo 4.5 deps check acionável`
- `feat(devops): Script memory-cleanup.py com dry-run e backup`
- `test: Fixtures isolados para evitar poluição de .memory/`

### Próxima Sprint (Semana 2026-05-19)

**P1 — Implementar** (Estimativa: 6-8h):

1. Pre-commit hooks (item 9)
2. GitHub Actions CI/CD (item 10)
3. Validação de configs (item 11)
4. Documentação sistema de memória (item 12)

**Deliverables**:
- `.git/hooks/pre-commit.d/validate-memory`
- `.github/workflows/dependency-check.yml`
- `scripts/validate-configs.py`
- `docs/MEMORY_SYSTEM.md`

---

## 📝 Notas de Implementação

### Regras Críticas a Seguir

**Do .copilot-rules.md**:

1. ❌ **NUNCA** criar arquivos via terminal (heredoc, echo, tee)
   - ✅ Usar: `create_file`, `replace_string_in_file`

2. ❌ **NUNCA** mover/copiar via terminal (mv, cp, rm)
   - ✅ Usar: Python stdlib (shutil, pathlib, logging)

3. ❌ **NUNCA** ler arquivos via terminal (cat, grep, find, ls)
   - ✅ Usar: `read_file`, `grep_search`, `file_search`, `list_dir`

4. ✅ **Git commits** ≥6 linhas via `./scripts/git-commit-with-file.sh`

5. ✅ **Documentação incremental** → NUNCA sobrescrever `TODO.md`, `INDEX.md`, `DAILY_ACTIVITIES_*.md`

---

## 🎯 Métricas de Sucesso

### Antes da Implementação

| Métrica | Valor Atual | Meta |
|---------|-------------|------|
| Tokens de ruído em memórias | ~3.420 tokens | 0 tokens |
| Arquivos de teste em `.memory/` | 37 arquivos | 0 arquivos |
| Memórias de outros projetos | 1 (enterprise-ansible) | 0 |
| Tempo session-start | ~15s | ~18s (com Passo 4.5) |
| Vulnerabilidades não detectadas | ? | 0 (detecção P0) |
| Configurações obsoletas | 1 (MCP CLI) | 0 (validação automática) |

### Após Implementação (Validar em 1 Semana)

- ✅ Zero arquivos de teste em `.memory/`
- ✅ Memória `scaffold-project.md` presente e correta
- ✅ Passo 4.5 executando em <5s
- ✅ Pre-commit hook bloqueando arquivos inválidos
- ✅ CI/CD reportando vulnerabilidades semanalmente

---

## 🏁 Conclusão do Debate

**Status**: ✅ Consenso alcançado em 13/14 decisões (93%)
**Divergências**: Apenas item 13 (quick mode) e 14 (dashboard) em discussão
**Prioridade**: P0 com escopo bem definido (8 items, ~6-8h)

**Próxima ação**: Executar items P0 1-8 nesta sessão.

---

**Participantes aprovam início da implementação**:
- [x] Principal Software Engineer
- [x] SE: Architect
- [x] DevOps Expert

**Documento revisado e aprovado em**: 2026-05-18
