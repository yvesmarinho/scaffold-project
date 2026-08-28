# Debate: Integração Engram MCP para Memória Persistente

**Data**: 2026-04-05
**Contexto**: Avaliar integração do Engram (Gentleman-Programming/engram) ao template para aumentar eficiência e qualidade da memória no Copilot
**Referências**:
- [Engram Repository](https://github.com/Gentleman-Programming/engram)
- [GitHub Copilot - Engram how to.md](../GitHub%20Copilot%20-%20Engram%20how%20to.md)
- **IMP-45**: Engram MCP — memória persistente por projeto (opt-in)
- **IMP-51**: MCP Search Integration ✅ CONCLUÍDO (session history search)
- **IMP-55**: Sistema de captura CHAT-*.md 🔵 PENDENTE (P2)

**Status**: 🔵 Em debate ativo
**Participantes**:
- template-architect (arquitetura)
- session-manager (integração com sessões)
- speckit.constitution (governança e princípios)
- Platform Tooling Engineer (build e dependências)
- DevEx Engineer (experiência do desenvolvedor)
- AppSec Engineer (segurança e vazamento de dados)
- SRE/Infra (operações e manutenibilidade)

---

## 📋 Sumário Executivo

Este debate analisa **o momento ideal para integrar o Engram MCP** ao Enterprise Scaffold Project Template, considerando:

1. **Timing**: IMP-51 (session search com SQLite + FTS5) foi concluído há 24h
2. **Overlap funcional**: Engram oferece FTS5 similar ao sistema já implementado
3. **Proposta de valor**: Memória persistente cross-session vs search histórico local
4. **Trade-offs**: Complexidade (binário externo) vs benefícios (memória RAG-like)
5. **Segurança**: Compliance com Principle IV (Zero-Trust on Secrets)
6. **Integração**: Como Engram se relaciona com IMP-53 (objetivo.yaml), IMP-55 (CHAT-*.md)

**Questão central**: É **ESTE O MOMENTO** para integrar Engram, ou devemos esperar mais dados de uso do sistema atual (IMP-51)?

---

## 🔍 Contexto: Estado Atual da Memória no Template

### Sistema Implementado (IMP-51 — Concluído 2026-04-05)

**Componentes**:
- `scripts/lib/search.py`: SessionIndexer + SessionSearcher (~550 linhas)
- `scripts/session-index.py`: CLI para indexação incremental
- `scripts/session-search.py`: CLI para busca interativa
- `.session-index/index.db`: SQLite + FTS5 (Porter + Unicode61 tokenization)
- 21 testes, 100% passing

**Capacidades**:
- Full-text search em `docs/SESSIONS/*/DAILY_ACTIVITIES_*.md`
- Busca boolean (AND, OR, NOT, NEAR), phrase search, date filters
- Performance: <0.1s/query, indexação inicial ~1s para 107 blocos
- Formato: **somente histórico local de sessões**

**Gaps conhecidos**:
- ❌ Não indexa conversas do Copilot Chat (IMP-55 ainda pendente)
- ❌ Não indexa specs/plans/tasks do SpecKit
- ❌ Não oferece "busca antes de começar tarefa" nativo (workflow manual)
- ❌ Escopo limitado a DAILY_ACTIVITIES (não indexa README, TODO, SESSION_REPORT)

### O Que Engram Adicionaria

**Engram** (Gentleman-Programming/engram) — binário Go, MCP server, SQLite + FTS5:

**Capacidades únicas**:
1. **Memória persistente estruturada**: título + conteúdo + tipo + timestamp
2. **Workflow RAG-like**:
   - `mem_search` antes de começar tarefa → contexto relevante
   - `mem_save` após conclusão → salvar decisões/learnings
   - `mem_context` → "o que estava rolando no projeto"
3. **Integração MCP nativa**: Copilot chama tools automaticamente (via `.vscode/mcp.json`)
4. **Formato text-first**: `.engram/memory/*.md` (fonte de verdade commitável), `.engram/index/engram.db` (cache reconstruível)
5. **Escopo flexível**: pode indexar qualquer `.md` (specs, plans, docs, etc.)

**Sobreposição com IMP-51**:
- Ambos usam SQLite + FTS5
- Ambos indexam texto markdown
- Ambos oferecem busca full-text

**Diferença crítica**:
- **IMP-51**: Busca **histórico passivo** (o que foi feito)
- **Engram**: Memória **ativa** (o que aprender → usar em próxima tarefa)

---

## 🗣️ Debate: 7 Perspectivas Profissionais

---

### 1️⃣ template-architect — Arquitetura e Coerência

**Posição**: ⚠️ **AGUARDAR** — Integrar agora cria redundância e confusão.

**Argumento**:

1. **Timing problemático**:
   - IMP-51 (session search) concluído há **24 horas**
   - **Zero dados de uso real** ainda — não sabemos se atende ou não
   - Adicionar Engram agora = introduzir segunda solução de busca antes de validar a primeira

2. **Sobreposição arquitetural**:
   ```
   IMP-51:    DAILY_ACTIVITIES → .session-index/index.db → session-search.py
   Engram:    .engram/memory/*.md → .engram/index/engram.db → MCP tools (mem_search, mem_save)
   ```
   - **2 DBs SQLite + FTS5** no mesmo projeto
   - **2 sistemas de indexação** (session-index.py vs engram import)
   - **2 workflows de busca** (CLI vs MCP)

3. **Risco de fragmentação**:
   - "Onde eu busco?" → "Depende do que você quer"
   - Usuário precisa entender diferença entre "histórico" e "memória"
   - Times vão usar **um ou outro**, não ambos (desperdício)

4. **Decisão prematura**:
   - Engram pode fazer sentido **SE** IMP-51 não atender
   - Mas ainda não sabemos se IMP-51 atende ou não
   - Integrar agora = commit arquitetural pesado sem validação

**Proposta**:
- ✅ **Esperar 2–4 semanas** de uso do IMP-51 em projetos reais
- ✅ **Coletar feedback**: "session-search é suficiente ou precisamos de memória ativa?"
- ✅ **Se IMP-51 não atender**, então debater Engram com dados
- ✅ **Alternativa**: Estender IMP-51 para indexar mais docs (README, TODO, specs) em vez de adicionar Engram

**Alerta**: Prioridade **P1** — Evitar complexidade desnecessária no template.

---

### 2️⃣ session-manager — Integração com Sistema de Sessões

**Posição**: ⚠️ **CONDICIONAL** — Engram faz sentido, mas precisa de integração clara com IMP-51.

**Argumento**:

1. **Engram complementa IMP-51, não substitui**:
   - **IMP-51**: Busca em histórico estruturado (`DAILY_ACTIVITIES_*.md`)
   - **Engram**: Memória curada pelo agente (decisões, learnings, ADRs inline)
   - **Caso de uso diferente**: IMP-51 = "o que fizemos?", Engram = "o que aprendemos?"

2. **Workflow ideal** (se Engram for integrado):
   ```
   Início de sessão:
     1. Agente lê session-start.prompt.md
     2. Agente usa `mem_search projeto ADRs decisões` (Engram) → context pré-existente
     3. Agente usa `session-search.py --query "IMP-XX"` (IMP-51) → histórico específico

   Fim de sessão:
     1. Agente atualiza DAILY_ACTIVITIES (IMP-48/49)
     2. `make session-index` (IMP-51) → indexar histórico
     3. Agente cria `mem_save` (Engram) → salvar learnings/decisões
   ```

3. **Benefício real**:
   - **IMP-51 sozinho**: agente precisa revisar histórico manualmente (ler arquivos)
   - **Engram + IMP-51**: agente busca contexto relevante automaticamente (RAG)
   - **Resultado**: Menos tokens desperdiçados em leitura de histórico irrelevante

4. **Mas... riscos de sobreposição**:
   - Se usuário salvar **tudo** no Engram, IMP-51 fica obsoleto
   - Se usuário usar **só IMP-51**, Engram fica vazio (setup desperdicio)
   - Precisa de **política de uso clara**: "O que vai no Engram vs DAILY_ACTIVITIES?"

**Proposta**:
- ✅ **Política de uso** (`.engram/AGENT_MEMORY_POLICY.md`):
  - **DAILY_ACTIVITIES**: histórico cronológico de atividades (tudo que foi feito)
  - **Engram memory**: decisões arquiteturais, learnings, padrões, convenções (curated knowledge)
- ✅ **Integração obrigatória**:
  - `session-start.prompt.md` → adicionar step: "Buscar contexto em `mem_search`"
  - `session-end.prompt.md` → adicionar step: "Salvar learnings em `mem_save`"
- ⚠️ **Condição**: Engram **SÓ** se houver policy clara; caso contrário, só estender IMP-51

**Alerta**: Prioridade **P2** — Integração bem definida é crítica para evitar confusão.

---

### 3️⃣ speckit.constitution — Governança e Princípios

**Posição**: 🚨 **BLOQUEADOR DETECTADO** — Engram viola Principle IV (Zero-Trust on Secrets) se não for cuidadosamente controlado.

**Argumento**:

**Principle IV: Zero-Trust on Secrets**
> No credential, token, API key, password, or secret of any kind ever enters the codebase — not in source files, not in templates, not in domain profiles, not in generated scaffold output.

1. **Risco CRÍTICO com Engram**:
   - Engram indexa **qualquer texto** salvo via `mem_save`
   - Se agente salvar output de comando com credencial (ex: `kubectl get secret -o yaml`), isso entra no `.engram/memory/*.md`
   - Se `.engram/memory/` for commitado (recomendação do Engram no README), **secrets vazam para Git**

2. **Exemplo de violação**:
   ```markdown
   # .engram/memory/2026-04-05__database__connection-string.md
   Data: 2026-04-05
   Tags: #database #setup

   ## Database Connection

   Connection string: postgresql://admin:MyP@ssw0rd123@db.prod.company.com:5432/app_db
   ```
   - Arquivo commitado → **SECRET LEAKED**

3. **Controle existente no template**:
   - `.gitignore` padrão: `.secrets/` (OK)
   - Gitleaks scan: `.gitleaks-session-docs.toml` (detecta secrets em `docs/SESSIONS/`)
   - Mas Engram cria **novo vetor**: `.engram/memory/`

4. **Mitigação necessária** (se Engram for integrado):
   ```gitignore
   # .gitignore — adicionar
   .engram/index/           # já está (cache SQLite)
   .engram/memory/*secret*  # CRÍTICO: bloquear arquivos com "secret" no nome
   .engram/memory/*password*
   .engram/memory/*token*
   .engram/memory/*key*
   ```

   ```toml
   # .gitleaks-engram.toml — novo arquivo
   [extend]
   useDefault = true

   [[rules]]
   id = "engram-memory-scan"
   description = "Scan .engram/memory/ for secrets"
   regex = '''(password|token|secret|key|credential)[\s:=]+[^\s]+'''
   path = '''\.engram/memory/.*\.md'''
   ```

   ```yaml
   # .github/workflows/ci-template.yml — adicionar job
   engram-scan:
     runs-on: ubuntu-latest
     steps:
       - uses: gitleaks/gitleaks-action@v2
         with:
           config-path: .gitleaks-engram.toml
           source: .engram/memory/
   ```

5. **Policy obrigatória**:
   - `.engram/AGENT_MEMORY_POLICY.md` **DEVE** incluir seção "Secrets Management":
     ```markdown
     ## 🚨 NEVER Save in Engram Memory

     - ❌ Connection strings (database, cache, queue)
     - ❌ API keys, tokens, passwords
     - ❌ Output de comandos: `kubectl get secret`, `cat .env`, `printenv`
     - ❌ Logs contendo credenciais

     ## ✅ HOW to Reference Secrets in Memory

     - ✅ "Database connection available via env var `DB_URL`"
     - ✅ "API key stored in `.secrets/.api_key` (gitignored)"
     - ✅ "Credentials managed via Vault path `secret/myapp/db`"
     ```

**Proposta**:
- 🚨 **Bloqueador**: Engram NÃO PODE ser integrado sem:
  1. `.gitignore` com padrões de secrets em `.engram/memory/`
  2. `.gitleaks-engram.toml` configurado
  3. CI job de scan obrigatório
  4. `.engram/AGENT_MEMORY_POLICY.md` com seção "Secrets Management"
  5. Test de segurança (`tests/test_engram_security.py`) validando que secrets não entram

- ✅ **Se mitigações forem implementadas**: Aprovado para integração
- ❌ **Se não houver mitigações**: VETO absoluto

**Alerta**: Prioridade **P0** — Violação de Principle IV é **não-negociável**.

---

### 4️⃣ Platform Tooling Engineer — Build e Dependências

**Posição**: ⚠️ **CUSTO vs BENEFÍCIO** — Engram adiciona dependência binária externa com custo de manutenção.

**Argumento**:

1. **Nova dependência externa**:
   - **Atual**: Python stdlib + uv (já necessário para o template)
   - **Engram**: Binário Go (precisa instalar separadamente)
   - **Instalação**:
     ```bash
     # macOS
     brew install gentleman-programming/tap/engram

     # Linux
     curl -sSL https://github.com/Gentleman-Programming/engram/releases/download/vX.Y.Z/engram-linux-amd64 \
       -o /usr/local/bin/engram && chmod +x /usr/local/bin/engram

     # Windows
     # ... (mais complexo)
     ```
   - **Problema**: Nem todo desenvolvedor terá `engram` instalado automaticamente

2. **Blockers de adoção**:
   - Engram é **opt-in** (IMP-45), mas se usuário quiser usar, precisa:
     1. Instalar binário manualmente
     2. Adicionar ao PATH
     3. Configurar `.vscode/mcp.json`
     4. Testar `engram mcp --help`
   - **Feedback de usuário**: "Por que não funciona out-of-the-box?" → Frustração

3. **Manutenibilidade**:
   - **IMP-51** (session search): Python puro, zero deps externas, funciona em qualquer máquina com Python 3.10+
   - **Engram**: Depende de releases do upstream (Gentleman-Programming/engram)
   - Se Gentleman-Programming parar de manter → template herda binário "órfão"

4. **Versioning e compatibilidade**:
   - Engram ainda é relativamente novo (primeiro release recente)
   - MCP protocol ainda em evolução
   - Breaking changes no Engram = projetos do template quebram

5. **Alternativa**: Implementar **Engram-like em Python puro**:
   - Reusar `scripts/lib/search.py` (já existe!)
   - Adicionar `mem_save()`, `mem_search()`, `mem_context()` como funções Python
   - Criar MCP server Python simples (usando `mcp` package)
   - **Benefício**: Zero deps externas, 100% controle, mantido pelo template

**Proposta**:
- ⚠️ **Reavaliar necessidade**: Engram oferece valor suficiente para justificar dependência externa?
- ✅ **Se SIM**: Adicionar checks no `scaffold.py`:
  ```python
  # scripts/lib/validate.py
  def check_engram_binary():
      """Validate engram is installed and functional."""
      try:
          result = subprocess.run(["engram", "version"], capture_output=True, text=True)
          if result.returncode != 0:
              return ValidationError("engram binary not found or not working")
      except FileNotFoundError:
          return ValidationError("engram not installed. Install via: brew install gentleman-programming/tap/engram")
  ```
- ✅ **Se NÃO**: Implementar mini-Engram em Python (reusar IMP-51 lib)

**Alerta**: Prioridade **P1** — Dependências externas aumentam fricção de onboarding.

---

### 5️⃣ DevEx Engineer — Experiência do Desenvolvedor

**Posição**: ✅ **A FAVOR** — Engram melhora dramaticamente a experiência se bem integrado.

**Argumento**:

1. **Problema real que Engram resolve**:
   - **Hoje** (sem Engram):
     ```
     Desenvolvedor: "Como eu configurei o Terraform na última vez?"
     → Busca manual em docs/SESSIONS/2025-11-*/
     → Lê 3 arquivos DAILY_ACTIVITIES
     → Reencontra comando: `terraform init -backend-config=...`
     → **Tempo perdido**: 10–15 minutos
     ```

   - **Com Engram**:
     ```
     Copilot: *automaticamente busca `mem_search terraform init`*
     → Encontra memória: "2025-11-12__terraform__backend-config.md"
     → Sugere comando diretamente
     → **Tempo perdido**: 0 minutos (automático)
     ```

2. **Casos de uso valiosos**:
   - **Onboarding de novos membros**: `mem_search "como rodar testes"`, `mem_search "deploy staging"`
   - **Retomada após pausa**: desenvolvedor volta de férias → `mem_context` → "o que estava acontecendo?"
   - **Reuso de decisões**: `mem_search ADR database` → recupera decisões passadas sem ler docs inteiros
   - **Debugging recorrente**: `mem_search "erro SSL certificate"` → "última vez, resolvemos com X"

3. **IMP-51 NÃO resolve esses casos**:
   - IMP-51 é **passivo**: desenvolvedor precisa saber que há algo no histórico
   - Engram é **ativo**: Copilot busca automaticamente quando relevante
   - **Diferença crítica**: proativo vs reativo

4. **Fricção de setup** (contra-argumento ao Platform Tooling):
   - Sim, instalar `engram` é manual **hoje**
   - Mas pode ser automatizado:
     ```makefile
     # Makefile — target de setup
     setup-engram:
     	@echo "Installing Engram MCP server..."
     	@if command -v brew &> /dev/null; then \
     		brew install gentleman-programming/tap/engram; \
     	else \
     		curl -sSL https://install-engram.sh | bash; \
     	fi
     	@engram version
     	@echo "✅ Engram installed successfully"
     ```
   - Adicionar ao `README.md`: "Opcional: `make setup-engram` para habilitar memória persistente"

5. **Value proposition forte**:
   - **ROI**: 15 minutos salvos por dia × 20 dias úteis = **5 horas/mês** por desenvolvedor
   - **Custo de setup**: 10 minutos one-time
   - **Payback**: 2 dias de uso

**Proposta**:
- ✅ **Integrar Engram como opt-in** (IMP-45)
- ✅ **Adicionar `make setup-engram`** para automação de instalação
- ✅ **Documentar casos de uso** em `.engram/README.md`
- ✅ **Criar memórias exemplo** (templates) para usuários verem valor imediatamente:
  ```
  .engram/memory/.examples/
    2026-01-01__exemplo__como-rodar-testes.md
    2026-01-01__exemplo__deploy-staging.md
    2026-01-01__exemplo__decisao-arquitetural.md
  ```

**Alerta**: Prioridade **P1** — DevEx é core value proposition do template.

---

### 6️⃣ AppSec Engineer — Segurança e Vazamento de Dados

**Posição**: 🚨 **ALTO RISCO** — Engram aumenta superfície de ataque se não houver controles.

**Argumento**:

1. **Vetores de vazamento de dados**:

   **Vetor 1: Secrets em memórias**
   - Já discutido por speckit.constitution
   - Agente salva output de comando com secret → leak

   **Vetor 2: PII (Personally Identifiable Information)**
   - Agente salva debug log com dados de usuário:
     ```markdown
     # .engram/memory/2026-04-05__debug__user-login-error.md
     User email: john.doe@company.com
     User CPF: 123.456.789-00
     Error: Invalid password for user_id = 42
     ```
   - Arquivo commitado → **GDPR/LGPD violation**

   **Vetor 3: Propriedade intelectual**
   - Agente salva código-fonte completo como "memória":
     ```markdown
     # .engram/memory/2026-04-05__implementacao__algoritmo-proprietario.md

     ```python
     def proprietary_algorithm(data):
         # Algoritmo secreto da empresa
         ...
     ```
     ```
   - Se `.engram/memory/` for sincronizado acidentalmente em repo público → **IP leak**

2. **Controles necessários** (além dos de speckit.constitution):

   **A. Sanitização obrigatória**:
   ```python
   # scripts/lib/engram.py — novo módulo

   REDACT_PATTERNS = [
       (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),  # email
       (r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '[CPF_REDACTED]'),  # CPF
       (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),  # SSN
       (r'password[\s:=]+[^\s]+', 'password: [REDACTED]'),
       (r'token[\s:=]+[^\s]+', 'token: [REDACTED]'),
   ]

   def sanitize_memory(text: str) -> str:
       """Apply redaction patterns before saving to Engram."""
       for pattern, replacement in REDACT_PATTERNS:
           text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
       return text
   ```

   **B. Pre-commit hook** (bloquear commits com dados sensíveis):
   ```bash
   # .git/hooks/pre-commit
   #!/usr/bin/env bash

   # Scan .engram/memory/ antes de commit
   if git diff --cached --name-only | grep -q '^\.engram/memory/'; then
       echo "🔍 Scanning Engram memory for secrets..."
       gitleaks protect --staged --config .gitleaks-engram.toml
       if [ $? -ne 0 ]; then
           echo "❌ COMMIT BLOCKED: Secrets detected in .engram/memory/"
           exit 1
       fi
   fi
   ```

   **C. Review process** (para memórias commitadas):
   - `.engram/memory/` deve ter `.github/CODEOWNERS`:
     ```
     # Approval obrigatório para memórias
     .engram/memory/**  @security-team @tech-leads
     ```

3. **Risk matrix**:

   | Vetor | Probabilidade | Impacto | Risco | Mitigação |
   |-------|---------------|---------|-------|-----------|
   | Secrets em memória | ALTA | CRÍTICO | 🔴 ALTO | Gitleaks + .gitignore + policy |
   | PII em memória | MÉDIA | ALTO | 🟠 MÉDIO | Sanitização + pre-commit hook |
   | IP leak | BAIXA | ALTO | 🟡 MÉDIO-BAIXO | Code review + CODEOWNERS |
   | Acesso não autorizado ao DB | BAIXA | MÉDIO | 🟢 BAIXO | `.engram/index/` no .gitignore |

4. **Compliance**:
   - **LGPD** (Brasil): Art. 46 — dados pessoais requerem consentimento explícito
   - **GDPR** (UE): Art. 25 — privacy by design
   - Se Engram salvar PII sem sanitização → **violação regulatória**

**Proposta**:
- 🚨 **Blockers de integração** (todos obrigatórios):
  1. ✅ `scripts/lib/engram.py` com sanitização
  2. ✅ `.gitleaks-engram.toml` configurado
  3. ✅ Pre-commit hook instalado automaticamente
  4. ✅ `.engram/memory/` em `.github/CODEOWNERS`
  5. ✅ Test de segurança: `tests/test_engram_security.py` (simular saves com secrets/PII, verificar que são bloqueados)
  6. ✅ `.engram/AGENT_MEMORY_POLICY.md` com seção "Data Privacy" (além de Secrets Management)

- ❌ **Se qualquer blocker não for implementado**: VETO para integração

**Alerta**: Prioridade **P0** — Segurança e compliance são non-negotiable.

---

### 7️⃣ SRE/Infra — Operações e Manutenibilidade

**Posição**: ⚠️ **CONDICIONAL** — Engram adiciona ponto de falha operacional; precisa de monitoramento.

**Argumento**:

1. **Pontos de falha**:

   **A. Binário Engram crashando**:
   - MCP server (`engram mcp`) roda como processo background
   - Se crashar durante operação do Copilot → perda de contexto
   - Necessário: **health check** e **restart automático**

   **B. Corrupção do DB SQLite**:
   - `.engram/index/engram.db` pode corromper (power loss, disk full, etc.)
   - Se corromper → `mem_search` falha → Copilot fica sem contexto
   - Necessário: **backup automático** + **rebuild from source**

   **C. Sincronização Git de `.engram/memory/`**:
   - Se 2 desenvolvedores commitarem memórias ao mesmo tempo → **merge conflict**
   - Arquivos `.md` são mergeáveis, mas pode gerar duplicatas ou inconsistências
   - Necessário: **merge strategy** ou **evitar sync** (recomendação: não commitar)

2. **Monitoramento necessário**:
   ```bash
   # Makefile — target de saúde
   engram-health:
   	@echo "🔍 Checking Engram health..."
   	@engram version || echo "❌ Engram binary not available"
   	@test -f .engram/index/engram.db && echo "✅ Index DB exists" || echo "⚠️  Index DB missing"
   	@sqlite3 .engram/index/engram.db "PRAGMA integrity_check" ||\
         echo "❌ DB corrupted - run 'make engram-rebuild'"
   	@echo "Memory files: $(shell find .engram/memory -name '*.md' 2>/dev/null | wc -l)"
   ```

3. **Disaster recovery**:
   ```bash
   # Makefile — target de recovery
   engram-rebuild:
   	@echo "🔧 Rebuilding Engram index from memory files..."
   	@test -f .engram/index/engram.db && \
         mv .engram/index/engram.db .engram/index/engram.db.backup.$$(date +%s)
   	@engram import --source .engram/memory --format markdown
   	@echo "✅ Index rebuilt successfully"
   ```

4. **Observabilidade**:
   - Atualmente **zero visibilidade** de quantas memórias existem, quando foram criadas, etc.
   - Útil: **dashboard** ou comando `make engram-stats`:
     ```
     📊 Engram Statistics
     Total memories: 47
     Oldest: 2025-11-03
     Newest: 2026-04-05
     Tags: #terraform (12), #kubernetes (8), #python (15), #debugging (7)
     Size: 2.3 MB (memory files), 450 KB (index DB)
     ```

5. **Custo operacional**:
   - **Setup**: ~10 min (instalar binário + config)
   - **Manutenção**: ~5 min/mês (rebuild se DB corromper)
   - **Debugging**: ~30 min (se algo quebrar e precisar investigar)
   - **Total**: ~1h/ano por projeto

   **Comparação**:
   - **IMP-51** (session search): Zero manutenção (Python puro, sem daemon)
   - **Trade-off**: Custo operacional vs benefício de memória ativa

**Proposta**:
- ✅ **Se Engram for integrado**:
  1. Adicionar `make engram-health` (health check)
  2. Adicionar `make engram-rebuild` (disaster recovery)
  3. Adicionar `make engram-stats` (observability)
  4. Adicionar `.github/workflows/engram-health.yml` (CI check semanal — opcional)
  5. Documentar em `.engram/OPERATIONS.md`: troubleshooting, recovery procedures

- ⚠️ **Recomendação**: NÃO commitar `.engram/memory/` se houver múltiplos desenvolvedores
  - Usar Engram **por desenvolvedor** (memory local, não sincronizada)
  - Ou: Usar sistema central (S3 bucket, NFS share) se precisar compartilhar memórias

**Alerta**: Prioridade **P2** — Operabilidade é importante, mas não bloqueante.

---

## 🎯 Síntese do Debate: Convergências e Divergências

### ✅ Consenso (todos concordam)

1. **Engram tem valor real** — memória ativa (RAG-like) é útil para projetos longos e onboarding
2. **Segurança é crítica** — não pode violar Principle IV (Zero-Trust on Secrets)
3. **Overlap com IMP-51 existe** — ambos usam SQLite + FTS5, mas propósitos diferentes
4. **Opt-in é correto** — Engram não deve ser default, mas disponível para quem precisar

### ⚠️ Divergências (pontos de debate)

| Tópico | Posição A | Posição B |
|--------|-----------|-----------|
| **Timing** | ⏳ Esperar 2–4 semanas (template-architect) | ✅ Integrar agora (DevEx) |
| **Dependência externa** | ⚠️ Risco de manutenibilidade (Platform Tooling) | ✅ Aceitável com automação (DevEx) |
| **Redundância** | ⚠️ 2 sistemas de FTS é confuso (template-architect) | ✅ Propósitos diferentes, não redundante (session-manager) |
| **Commit de `.engram/memory/`** | ❌ Não commitar (SRE) | ✅ Commitar com controles (Engram README) |

---

## 📊 Matriz de Decisão

### Cenário 1: ✅ **INTEGRAR AGORA** (posição DevEx + session-manager)

**Pré-requisitos OBRIGATÓRIOS**:
1. ✅ Security controls:
   - `.gitignore`: patterns de secrets em `.engram/memory/`
   - `.gitleaks-engram.toml`: configurado e testado
   - `scripts/lib/engram.py`: sanitização de PII/secrets
   - Pre-commit hook: scan automático
   - `.engram/AGENT_MEMORY_POLICY.md`: seção "Secrets Management" + "Data Privacy"
   - `tests/test_engram_security.py`: test de segurança

2. ✅ Operational controls:
   - `make setup-engram`: automação de instalação
   - `make engram-health`: health check
   - `make engram-rebuild`: disaster recovery
   - `make engram-stats`: observability
   - `.engram/OPERATIONS.md`: troubleshooting guide

3. ✅ Integration with existing systems:
   - `.engram/AGENT_MEMORY_POLICY.md`: policy clara (Engram vs DAILY_ACTIVITIES)
   - `session-start.prompt.md`: adicionar `mem_search` step
   - `session-end.prompt.md`: adicionar `mem_save` step
   - `.engram/memory/.examples/`: templates de memórias

4. ✅ Validation:
   - `tests/test_engram_integration.py`: integração com session system
   - `tests/test_engram_security.py`: security compliance
   - `docs/COMPATIBILITY-MATRIX.md`: adicionar coluna "Engram MCP"

**Benefícios**:
- ✅ Memória ativa para projetos complexos
- ✅ Onboarding acelerado (novos membros usam `mem_search`)
- ✅ Redução de re-work (decisões acessíveis via `mem_context`)
- ✅ Integração com IMP-55 (CHAT-*.md pode ir para Engram)

**Custos**:
- ⚠️ ~80h de implementação (security + ops + docs + tests)
- ⚠️ Dependência externa (binário Go)
- ⚠️ Curva de aprendizado (usuários precisam entender quando usar Engram vs session search)

**Riscos**:
- 🚨 Se controles de segurança forem mal implementados → leak de secrets/PII
- ⚠️ Se policy de uso não for clara → confusão (usuários não sabem onde salvar)
- ⚠️ Se Gentleman-Programming parar de manter → binário "órfão"

**Estimativa de esforço**:
- Security controls: 32h
- Operational controls: 16h
- Integration: 16h
- Documentation: 8h
- Tests: 8h
- **Total**: ~80h (~2 semanas de trabalho concentrado)

---

### Cenário 2: ⏳ **ESPERAR** (posição template-architect)

**Rationale**:
- IMP-51 (session search) foi concluído há 24h — **zero dados de uso real**
- Adicionar Engram agora = introduzir solução antes de validar o problema
- Risco de sobre-engenharia ("solution looking for a problem")

**Proposta**:
1. **Usar IMP-51 por 2–4 semanas** em projetos reais
2. **Coletar feedback**:
   - "session-search é suficiente ou falta algo?"
   - "Você sente falta de memória ativa (RAG-like)?"
   - "Você busca manualmente em docs muito frequentemente?"
3. **Se feedback indicar necessidade** → proceder com Cenário 1
4. **Se feedback indicar que IMP-51 atende** → **estender IMP-51** (indexar README, TODO, specs) em vez de adicionar Engram

**Benefícios**:
- ✅ Decisão baseada em dados (não em suposições)
- ✅ Evita complexidade desnecessária
- ✅ Reduz risco de abandono (usuários não usam Engram → esforço desperdiçado)

**Custos**:
- ⏳ Delay de 2–4 semanas para integração (se necessário)
- ⏳ Perda de benefícios de memória ativa durante período de espera

**Riscos**:
- ⚠️ Feedback pode ser inconclusivo (poucos usuários)
- ⚠️ Viés de status quo ("IMP-51 é suficiente porque não conhecem Engram")

---

### Cenário 3: 🔀 **HÍBRIDO** — Estender IMP-51 + Preparar Engram (posição intermediária)

**Proposta**:
1. **Fase 1** (imediato — ~16h):
   - Estender IMP-51 para indexar mais arquivos:
     - `docs/README.md`
     - `docs/TODO.md`
     - `docs/SESSIONS/*/SESSION_REPORT_*.md`
     - `.specify/specs/*/spec.md`
     - `.specify/specs/*/plan.md`
   - Adicionar `session-search.py --scope [sessions|all]`
   - Resultado: **memória passiva ampliada**

2. **Fase 2** (paralelo — ~40h):
   - Implementar **mini-Engram em Python puro**:
     - Reusar `scripts/lib/search.py` (SQLite + FTS5)
     - Adicionar `scripts/mem_save.py --title "..." --content "..."`
     - Adicionar `scripts/mem_search.py --query "..."`
     - Criar MCP server Python (package `mcp`)
   - Benefícios:
     - Zero dependência externa (100% Python)
     - 100% controle e manutenibilidade
     - Aproveita código existente (IMP-51)

3. **Fase 3** (opcional — ~80h):
   - **SE** mini-Engram Python não atender → integrar Engram oficial (Cenário 1)
   - **SE** mini-Engram Python atender → manter solução Python

**Benefícios**:
- ✅ Solução incremental (não all-or-nothing)
- ✅ Validação de valor antes de commit com dependência externa
- ✅ Fallback caso Engram oficial seja problemático

**Custos**:
- ⏳ Esforço maior total (~136h em 3 fases) se ambas soluções forem implementadas
- ⚠️ Risco de "reescrever Engram" (reinventar a roda)

**Riscos**:
- ⚠️ Mini-Engram Python pode ficar inferior ao Engram oficial (menos features, mais bugs)
- ⚠️ Fragmentação de esforço (time gasta tempo duplicando funcionalidade)

---

## 🗳️ Recomendação Final: Votação dos Agentes

### Votação

| Agente | Voto | Cenário Preferido | Justificativa |
|--------|------|-------------------|---------------|
| **template-architect** | ⏳ | Cenário 2 (Esperar) | Validar IMP-51 antes de adicionar complexidade |
| **session-manager** | 🔀 | Cenário 3 (Híbrido) | Estender IMP-51 + avaliar mini-Engram Python |
| **speckit.constitution** | ⚠️ | Cenário 1 (se security OK) | Aprovado SE todos controles implementados |
| **Platform Tooling** | 🔀 | Cenário 3 (Híbrido) | Preferir Python puro; Engram só se necessário |
| **DevEx** | ✅ | Cenário 1 (Integrar) | Valor imediato, automação de instalação resolve fricção |
| **AppSec** | 🚨 | Cenário 1 (bloqueado até security OK) | NÃO integrar sem controles P0 |
| **SRE/Infra** | ⏳ | Cenário 2 (Esperar) | Evitar ponto de falha operacional até validar necessidade |

**Resultado**:
- **Cenário 1** (Integrar agora): 1 voto (DevEx) + 2 condicionais (constitution, AppSec)
- **Cenário 2** (Esperar): 2 votos (template-architect, SRE)
- **Cenário 3** (Híbrido): 2 votos (session-manager, Platform Tooling)

**Empate técnico** → Necessário critério de desempate.

---

## 🎯 Decisão Final (Critério de Desempate: Princípio de Responsabilidade)

**Princípio aplicado**: *Quem é responsável por manutenibilidade e segurança a longo prazo?*

Resposta: **template-architect** (arquitetura), **speckit.constitution** (governança), **AppSec** (segurança).

**Posições desses agentes**:
- template-architect: **Esperar**
- constitution: **Condicional** (só com security OK)
- AppSec: **Bloqueado** (até security OK)

**Interpretação**:
- Maioria dos "responsáveis" prefere **aguardar ou exigir controles rigorosos**
- DevEx tem argumento forte, mas **não é responsável por manutenibilidade/segurança**

---

## ✅ Decisão Consensual: **Cenário 3 (Híbrido) — Implementação Faseada**

### Fase 1: Estender IMP-51 (Imediato — ~16h)

**Objetivo**: Aumentar cobertura de memória passiva antes de introduzir memória ativa.

**Tarefas**:
1. Atualizar `scripts/lib/search.py`:
   - Adicionar `index_file(file_path)` genérico (além de `index_session`)
   - Suportar indexação de qualquer `.md` (não só DAILY_ACTIVITIES)

2. Atualizar `scripts/session-index.py`:
   - Adicionar flag `--scope [sessions|docs|specs|all]`
   - `--scope sessions`: comportamento atual (só DAILY_ACTIVITIES)
   - `--scope docs`: indexar `docs/*.md`, `docs/SESSIONS/*/*.md`
   - `--scope specs`: indexar `.specify/specs/*/*.md`
   - `--scope all`: indexar tudo

3. Atualizar `session-search.py`:
   - Adicionar flag `--scope` para filtrar por tipo de documento
   - Adicionar coluna `document_type` nos resultados

4. Documentação:
   - Atualizar `docs/SESSION_SEARCH_GUIDE.md` com novos scopes
   - Adicionar exemplos: "Buscar decisões em specs", "Buscar TODOs"

**Entrega**: IMP-51 v2.0 — memória passiva ampliada

**Estimativa**: 16h

---

### Fase 2: Avaliar Necessidade de Memória Ativa (2–4 semanas após Fase 1)

**Objetivo**: Coletar dados de uso real para decisão fundamentada.

**Critérios de avaliação**:
1. **Frequência de busca manual**: usuários fazem `session-search` ≥5x/dia → necessidade alta
2. **Queixas de perda de contexto**: "Esqueci como fazer X" ≥3x/semana → necessidade alta
3. **Onboarding lento**: novos membros levam >2h para encontrar informações → necessidade alta

**Método de coleta**:
- Survey com usuários do template (5 perguntas)
- Análise de uso: `make session-search | tee usage.log` → contar queries
- Entrevistas com 3–5 desenvolvedores

**Decision gate**:
- **SE ≥2 critérios indicarem necessidade alta** → Prosseguir para Fase 3a (mini-Engram Python)
- **SE <2 critérios** → Manter IMP-51 v2.0, não implementar memória ativa

---

### Fase 3a: Mini-Engram Python (Condicional — ~40h)

**Objetivo**: Implementar memória ativa (RAG-like) sem dependência externa.

**Arquitetura**:
```
.memory/
  memories/
    2026-04-05__terraform__backend-config.md
    2026-04-05__python__testing-patterns.md
  index/
    memory.db  # SQLite + FTS5 (reusar lib de IMP-51)
  scripts/
    mem_save.py
    mem_search.py
    mem_mcp_server.py  # MCP server Python
  MEMORY_POLICY.md
```

**Componentes**:
1. `scripts/mem_save.py`:
   ```python
   # CLI wrapper para salvar memórias
   python scripts/mem_save.py \
     --title "Terraform backend config" \
     --tags "terraform,backend,s3" \
     --content "Use terraform init -backend-config=..."
   ```

2. `scripts/mem_search.py`:
   ```python
   # CLI para buscar memórias
   python scripts/mem_search.py --query "terraform backend"
   ```

3. `scripts/mem_mcp_server.py`:
   ```python
   # MCP server Python (usando package `mcp`)
   # Expõe tools: mem_save, mem_search, mem_context
   ```

4. `.vscode/mcp.json`:
   ```json
   {
     "servers": {
       "memory": {
         "command": "python",
         "args": ["scripts/mem_mcp_server.py"]
       }
     }
   }
   ```

**Security controls** (reusar de Cenário 1):
- `.memory/MEMORY_POLICY.md`: policy de uso
- `scripts/lib/sanitize.py`: sanitização de PII/secrets
- `.gitleaks-memory.toml`: scan de `.memory/memories/`
- `tests/test_memory_security.py`: test de segurança

**Estimativa**: 40h

**Entrega**: Sistema de memória ativa em Python puro

---

### Fase 3b: Engram Oficial (Fallback — ~80h)

**Objetivo**: Integrar Engram oficial SE mini-Engram Python não atender.

**Critérios para fallback**:
- Mini-Engram Python tem bugs críticos
- Performance inadequada (>1s para queries)
- Manutenibilidade difícil (código complexo)

**Implementação**: Seguir Cenário 1 (todos controles de security + ops)

**Estimativa**: 80h

---

## 📋 Roadmap de Implementação

### Sprint 1 (Semana 1–2): Fase 1 — Estender IMP-51

| Task ID | Tarefa | Responsável | Estimativa | Prioridade |
|---------|--------|-------------|-----------|-----------|
| **ENG-01** | Atualizar `search.py` para indexar `.md` genérico | Platform Tooling | 4h | P1 |
| **ENG-02** | Adicionar `--scope` em `session-index.py` | Platform Tooling | 4h | P1 |
| **ENG-03** | Adicionar `--scope` em `session-search.py` | DevEx | 3h | P1 |
| **ENG-04** | Atualizar docs (SESSION_SEARCH_GUIDE.md) | Technical Writer | 2h | P1 |
| **ENG-05** | Tests (`test_search_scope.py`) | Platform Tooling | 3h | P1 |
| **Total** | | | **16h** | |

**Blocker**: Nenhum

---

### Sprint 2–4 (Semana 3–8): Fase 2 — Avaliar Necessidade

| Task ID | Tarefa | Responsável | Estimativa | Prioridade |
|---------|--------|-------------|-----------|-----------|
| **ENG-06** | Criar survey de usuários (5 perguntas) | DevEx | 2h | P1 |
| **ENG-07** | Coletar dados de uso (logs + entrevistas) | DevEx | 8h | P1 |
| **ENG-08** | Análise de dados + report | DevEx | 4h | P1 |
| **ENG-09** | Decision gate (go/no-go para Fase 3) | template-architect | 2h | P0 |
| **Total** | | | **16h** (distribuído em 4 semanas) | |

**Blocker**: Depende de Fase 1 (IMP-51 v2.0 em produção)

---

### Sprint 5–7 (Semana 9–14): Fase 3a — Mini-Engram Python (Condicional)

**Pré-condição**: Decision gate da Fase 2 = GO

| Task ID | Tarefa | Responsável | Estimativa | Prioridade |
|---------|--------|-------------|-----------|-----------|
| **ENG-10** | Criar estrutura `.memory/` | Platform Tooling | 2h | P0 |
| **ENG-11** | Implementar `mem_save.py` | Platform Tooling | 6h | P0 |
| **ENG-12** | Implementar `mem_search.py` | Platform Tooling | 4h | P0 |
| **ENG-13** | Implementar `mem_mcp_server.py` | Platform Tooling | 8h | P0 |
| **ENG-14** | Security: `sanitize.py` + policy | AppSec | 8h | P0 |
| **ENG-15** | Security: `.gitleaks-memory.toml` | AppSec | 2h | P0 |
| **ENG-16** | Tests: `test_memory_*.py` (20 tests) | Platform Tooling | 6h | P0 |
| **ENG-17** | Docs: `.memory/MEMORY_POLICY.md` | Technical Writer | 2h | P1 |
| **ENG-18** | Integration: update session prompts | session-manager | 2h | P1 |
| **Total** | | | **40h** | |

**Blocker**: Decision gate Fase 2

---

### Sprint 8+ (Semana 15+): Fase 3b — Engram Oficial (Fallback)

**Pré-condição**: Mini-Engram Python inadequado OU decision de usar Engram oficial

Implementação completa conforme Cenário 1 (~80h).

**Blockers**: Todos controles de security implementados (AppSec sign-off obrigatório)

---

## 📊 Estimativa Total de Esforço

| Fase | Cenário | Estimativa | Probabilidade |
|------|---------|-----------|---------------|
| **Fase 1** | Estender IMP-51 | 16h | 100% (certeza) |
| **Fase 2** | Avaliar necessidade | 16h | 100% (certeza) |
| **Fase 3a** | Mini-Engram Python | 40h | 60% (condicional) |
| **Fase 3b** | Engram oficial | 80h | 20% (fallback) |

**Esperado (valor esperado estatístico)**:
- 16h + 16h + (40h × 0.6) + (80h × 0.2) = **72h** (~2 semanas de trabalho)

**Pior caso** (ambas Fase 3a e 3b):
- 16h + 16h + 40h + 80h = **152h** (~4 semanas de trabalho)

**Melhor caso** (só Fase 1 + 2, decision = NO-GO):
- 16h + 16h = **32h** (~4 dias de trabalho)

---

## 🎯 Conclusão e Próximos Passos

### Veredicto Final: ✅ **APROVADO COM CONDIÇÕES** — Implementação Faseada (Cenário 3)

**Rationale**:
1. ✅ **Valor reconhecido**: Todos concordam que memória ativa tem benefícios
2. ⚠️ **Timing incerto**: IMP-51 muito recente para invalidar
3. 🚨 **Segurança crítica**: Não pode violar Principle IV
4. 🔀 **Abordagem prudente**: Incrementar capacidade antes de adicionar complexidade

**Decisão consensual**:
- **Fase 1** (imediato): Estender IMP-51 para cobrir mais documentos
- **Fase 2** (2–4 semanas): Avaliar necessidade com dados reais
- **Fase 3a** (condicional): Implementar mini-Engram Python se necessário
- **Fase 3b** (fallback): Integrar Engram oficial se Python inadequado

---

### Próximos Passos Imediatos

#### 1. Criar Issue para Fase 1 (Sprint 1)

**Issue**: `[IMP-57] Estender IMP-51: Indexação de Documentos Além de DAILY_ACTIVITIES`

**Escopo**:
- Atualizar `search.py` para indexar `.md` genérico
- Adicionar flag `--scope [sessions|docs|specs|all]`
- Testes + documentação

**Estimativa**: 16h
**Prioridade**: P1
**Responsável**: Platform Tooling Engineer
**Blocker**: Nenhum

---

#### 2. Criar Survey de Usuários (Fase 2)

**Survey**: "Uso de Busca e Memória no Template"

**Perguntas**:
1. Quantas vezes por dia você busca informações em `docs/SESSIONS/`?
2. Você sente que perde contexto entre sessões de trabalho? (escala 1–5)
3. Quanto tempo leva para novos membros do time encontrarem informações operacionais? (horas)
4. Você gostaria de um sistema de "memória ativa" (salvar learnings importantes para reuso fácil)? (sim/não)
5. O que você mais busca? (opções: comandos, decisões arquiteturais, troubleshooting, configurações)

**Distribuição**: Após Fase 1 completar (semana 3)

---

#### 3. Atualizar TODO.md

Adicionar:
- `[IMP-57]` Estender IMP-51 (Fase 1)
- `[IMP-58]` Avaliar necessidade de memória ativa (Fase 2)
- `[IMP-59]` Mini-Engram Python (Fase 3a — condicional)
- `[IMP-45]` Engram oficial (renomear para Fase 3b — fallback)

---

#### 4. Comunicar Decisão

**Para**: Usuários do template, stakeholders

**Mensagem**:
```markdown
# Decisão: Integração Engram — Abordagem Faseada

Após debate técnico com 7 perspectivas (arquitetura, sessões, segurança, DevEx, Platform, SRE),
decidimos adotar uma **abordagem faseada** para memória persistente:

**Fase 1** (próximas 2 semanas): Estender sistema de busca atual (IMP-51) para indexar mais documentos.

**Fase 2** (semana 3–8): Avaliar com dados reais se precisamos de memória ativa (Engram).

**Fase 3** (condicional): Implementar solução de memória ativa SE necessário.

Essa abordagem balanceia **prudência arquitetural** (não adicionar complexidade prematuramente)
com **valor para usuários** (memória ativa quando validada).

Feedback bem-vindo em: [issue #IMP-58]
```

---

## 📚 Referências e Recursos

### Documentos Relacionados

1. **IMP-51**: [SESSION_SEARCH_GUIDE.md](../SESSION_SEARCH_GUIDE.md)
2. **IMP-45**: [TODO.md linha 579](../TODO.md#L579) — Engram MCP original
3. **IMP-55**: [TODO.md linha 192](../TODO.md#L192) — Sistema CHAT-*.md
4. **Constitution**: [.specify/memory/constitution.md](../../.specify/memory/constitution.md)
5. **Engram How-To**: [GitHub Copilot - Engram how to.md](../GitHub%20Copilot%20-%20Engram%20how%20to.md)

### Links Externos

- [Engram Repository](https://github.com/Gentleman-Programming/engram)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [SQLite FTS5](https://www.sqlite.org/fts5.html)

---

**Debate concluído em**: 2026-04-05
**Status**: ✅ Consenso atingido — Implementação faseada aprovada
**Próxima revisão**: Após Fase 2 (semana 8)
