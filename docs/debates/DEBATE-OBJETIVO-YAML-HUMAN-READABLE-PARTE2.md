# Debate Técnico: Redesign do objetivo.yaml — Human-Readable Format (PARTE 2)

**Continuação de**: [DEBATE-OBJETIVO-YAML-HUMAN-READABLE.md](./DEBATE-OBJETIVO-YAML-HUMAN-READABLE.md)

---

## 2.4. Principal Software Engineer (Dr. James Wei) — Continuação

*(Continuando da Parte 1...)*

### Workflow Integration

**Integração com SpecKit Agents** (proposta arquitetural):

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: scaffold.py process objetivo.yaml                       │
│ ───────────────────────────────────────────────────────────────│
│ Input: objetivo.yaml (v2.0)                                      │
│ Validação: syntax → schema → semantics → business               │
│ Output: objetivo-spec.yaml + .specify/state.json                │
│ Estado: DRAFT → VALIDATED → SPEC_GENERATED                      │
│ Tempo: ~2 minutos                                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: speckit.constitution (Agent Layer 1)                    │
│ ───────────────────────────────────────────────────────────────│
│ Input: objetivo-spec.yaml                                        │
│ Ação: Gera .specify/constitution.md (princípios do projeto)     │
│ Output: constitution.md                                          │
│ Estado: SPEC_GENERATED → CONSTITUTION_READY                     │
│ Tempo: ~3 minutos (análise por Copilot)                         │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: speckit.clarify (Agent Layer 1)                         │
│ ───────────────────────────────────────────────────────────────│
│ Input: objetivo-spec.yaml + constitution.md                     │
│ Ação: Identifica perguntas_abertas → entrevista usuário         │
│ Output: objetivo.yaml ATUALIZADO (usuário responde perguntas)   │
│ Estado: CONSTITUTION_READY → CLARIFIED                          │
│ Tempo: ~10 minutos (interativo)                                 │
│ IMPORTANTE: Só atualiza objetivo.yaml (input), não spec!        │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼ (se objetivo.yaml mudou, volta ao STEP 1)
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: speckit.specify (Agent Layer 2)                         │
│ ───────────────────────────────────────────────────────────────│
│ Input: objetivo-spec.yaml + constitution.md + context            │
│ Ação: Gera spec.md (especificação técnica detalhada)            │
│ Output: .specify/specs/IMP-*/spec.md                            │
│ Estado: CLARIFIED → SPECIFIED                                   │
│ Tempo: ~5 minutos                                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: speckit.plan (Agent Layer 3)                            │
│ ───────────────────────────────────────────────────────────────│
│ Input: spec.md + decisoes_iniciais (do objetivo.yaml)           │
│ Ação: Gera plan.md + ADRs                                       │
│ Output: .specify/specs/IMP-*/plan.md, docs/architecture/adr/    │
│ Estado: SPECIFIED → PLANNED                                     │
│ Tempo: ~4 minutos                                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: speckit.tasks (Agent Layer 4)                           │
│ ───────────────────────────────────────────────────────────────│
│ Input: plan.md                                                   │
│ Ação: Gera tasks.md (checklist de implementação)                │
│ Output: .specify/specs/IMP-*/tasks.md                           │
│ Estado: PLANNED → TASKS_READY                                   │
│ Tempo: ~2 minutos                                                │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: scaffold.py compose (execução final)                    │
│ ───────────────────────────────────────────────────────────────│
│ Input: objetivo-spec.yaml (campo profile)                        │
│ Ação: Aplica profile descriptors → gera arquivos do projeto     │
│ Output: .github/, src/, tests/, docs/, Makefile, etc.           │
│ Estado: TASKS_READY → COMPOSED → READY                          │
│ Tempo: ~3 minutos                                                │
└─────────────────────────────────────────────────────────────────┘
```

**Garantias arquiteturais**:

1. **Checkpoint automático**: Cada STEP salva estado em `.specify/state.json`
2. **Rollback possível**: `scaffold.py rollback --to STEP3` reverte mudanças
3. **Replay determinístico**: Re-executar workflow com mesmo input gera mesmo output
4. **Parallel execution**: STEPs independentes rodam em paralelo (STEP 2-3 podem rodar juntos)

**Proposta de Melhoria (Dr. James Wei) — Continuação**

5. **Event-Driven Architecture**:
   ```python
   # lib/events/objective_events.py
   class ObjectiveEvent:
       event_id: str
       timestamp: datetime
       event_type: str
       payload: Dict[str, Any]

   class EventBus:
       def publish(self, event: ObjectiveEvent):
           """Publica evento para subscribers (agents, webhooks, logs)"""
           for subscriber in self.subscribers:
               subscriber.handle(event)

       def subscribe(self, event_type: str, handler: Callable):
           """Registra handler para tipo de evento"""
           self.subscribers[event_type].append(handler)

   # Uso
   bus.subscribe("objective_validated", lambda e: send_slack_notification(e))
   bus.subscribe("spec_generated", lambda e: trigger_speckit_constitution(e))
   bus.subscribe("project_ready", lambda e: create_github_repo(e))
   ```

6. **Plugin System** (extensibilidade):
   ```python
   # plugins/monorepo_plugin.py
   class MonorepoPlugin(ObjetivoPlugin):
       def on_spec_generated(self, spec: ObjetivoSpec) -> ObjetivoSpec:
           """Hook executado após geração de spec"""
           if spec.extensions.get("monorepo"):
               # Processar lógica de monorepo
               spec.projects = self._expand_monorepo(spec)
           return spec

       def on_compose(self, structure: ProjectStructure) -> ProjectStructure:
           """Hook executado durante geração de arquivos"""
           if structure.is_monorepo:
               # Gerar arquivos de monorepo (turbo.json, pnpm-workspace.yaml)
               structure.add_files(self._generate_monorepo_files())
           return structure

   # Registro
   register_plugin("monorepo", MonorepoPlugin())
   ```

---

## 2.5. Product Manager (Priya Sharma) — Continuação

*(Continuando da Parte 1...)*

### Go-to-Market Strategy

**Segmentação de usuários**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Segmento 1: Iniciantes (35% dos usuários)                       │
│ ───────────────────────────────────────────────────────────────│
│ Características:                                                 │
│   - 1-2 anos de experiência                                      │
│   - Primeira vez usando templates/scaffolding                   │
│   - Foco em aprender ferramentas                                 │
│                                                                  │
│ Estratégia:                                                      │
│   - Wizard guiado como modo padrão                               │
│   - Tutoriais em vídeo (5-10 min)                                │
│   - Templates prontos para copiar                                │
│   - Suporte via Slack/Discord dedicado                           │
│                                                                  │
│ KPI de sucesso:                                                  │
│   - Tempo até primeiro projeto: < 15 min                         │
│   - Taxa de sucesso: > 80%                                       │
│   - NPS: > 60                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Segmento 2: Intermediários (40% dos usuários)                   │
│ ───────────────────────────────────────────────────────────────│
│ Características:                                                 │
│   - 3-5 anos de experiência                                      │
│   - Já usaram Cookiecutter, Yeoman ou similar                   │
│   - Querem personalização mas com guias                          │
│                                                                  │
│ Estratégia:                                                      │
│   - Modo semi-automático (wizard + edição manual)                │
│   - Documentação de referência completa                          │
│   - Galeria de exemplos por caso de uso                          │
│   - Best practices integradas                                    │
│                                                                  │
│ KPI de sucesso:                                                  │
│   - Tempo até projeto customizado: < 30 min                      │
│   - Taxa de adoção: > 70%                                        │
│   - NPS: > 70                                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Segmento 3: Avançados (25% dos usuários)                        │
│ ───────────────────────────────────────────────────────────────│
│ Características:                                                 │
│   - 6+ anos de experiência                                       │
│   - Arquitetos, Tech Leads, SREs                                 │
│   - Querem controle total e extensibilidade                      │
│                                                                  │
│ Estratégia:                                                      │
│   - Advanced mode com todas as opções                            │
│   - Plugin API para customizações                                │
│   - Arquitetura extensível (hooks, eventos)                      │
│   - Contribuição para templates (open-source)                    │
│                                                                  │
│ KPI de sucesso:                                                  │
│   - Taxa de customização bem-sucedida: > 90%                     │
│   - Contribuições de plugins: > 5/trimestre                      │
│   - NPS: > 75                                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Roadmap de lançamento** (6 meses):

```
Mês 1-2: Alpha (fechado, 20 usuários early adopters)
  ├─ Objetivo: Validar usabilidade do wizard
  ├─ Feedback loops: Entrevistas semanais
  └─ Iterações rápidas (releases 2x/semana)

Mês 3-4: Beta (aberto, 100 usuários)
  ├─ Objetivo: Validar escalabilidade e docs
  ├─ Feedback loops: Surveys NPS mensais
  └─ Documentação completa (7 guias)

Mês 5: Release Candidate
  ├─ Objetivo: Stress test e migração
  ├─ Ferramentas: Migration script automático
  └─ Webinar de lançamento (200+ participantes)

Mês 6: GA (General Availability)
  ├─ Comunicação: Blog post, email, Slack announcement
  ├─ Suporte: 2 FTEs dedicados (primeiro mês)
  └─ Monitoramento: Dashboards de adoção e NPS
```

**Proposta de Melhoria (Priya Sharma) — Continuação**

5. **Programa de Champions** (advocacy interno):
   - Recrutar 10 early adopters como champions
   - Champions recebem treinamento avançado (4 horas)
   - Champions respondem dúvidas no Slack (#template-support)
   - Incentivo: Reconhecimento público + certificado

6. **Métricas de Produto** (dashboard de adoção):
   ```python
   # analytics/metrics.py
   class ObjectiveMetrics:
       def track_usage(self, event: str, properties: Dict):
           """Envia evento para analytics (Mixpanel, Amplitude, etc.)"""
           analytics.track(user_id, event, properties)

       # Eventos rastreados
       def track_objetivo_created(self, objetivo: ObjetivoV2):
           self.track_usage("objetivo_created", {
               "project_type": objetivo.project.type,
               "wizard_used": objetivo.metadata.wizard_used,
               "time_to_create": objetivo.metadata.time_to_create_seconds
           })

       def track_spec_generated(self, spec: ObjetivoSpec):
           self.track_usage("spec_generated", {
               "profiles_count": len(spec.profiles),
               "features_count": len(spec.features),
               "generation_time": spec.metadata.generation_time_seconds
           })

       def track_project_composed(self, structure: ProjectStructure):
           self.track_usage("project_composed", {
               "files_count": len(structure.files),
               "templates_count": len(structure.templates),
               "success": structure.success
           })
   ```

---

# 3. PROPOSTAS INDIVIDUAIS

## 3.1. Proposta: UX Designer (Sarah Chen)

### Formato Sugerido: **Markdown Híbrido com Progressive Disclosure**

```markdown
---
# YAML Frontmatter (metadados estruturados)
version: "2.0"
schema: "https://schema.enterprise-template.io/objetivo-v2.json"
project:
  name: "user-management-api"
  type: "backend-api"
  created_at: "2026-04-27"
  created_by: "alice@empresa.com"
---

# 🎯 Objetivo do Projeto

> **Template**: `simple-python-api` | **Tempo estimado**: 10-15 minutos

---

## ✅ Etapa 1/3: Express — O Essencial

<details open>
<summary><strong>3 perguntas obrigatórias</strong> (clique para expandir)</summary>

### 1️⃣ O que este projeto faz?
**Descrição em 1-2 frases, focando no valor (não na tecnologia).**

💡 **Exemplos**:
- "API REST para gerenciar usuários e autenticação"
- "Dashboard de analytics em tempo real para vendas"
- "Pipeline de ETL para data warehouse"

**Seu projeto**:
```
API REST para gerenciar usuários (criar, listar, atualizar, deletar contas).
Centraliza autenticação de 5 sistemas legados.
```

---

### 2️⃣ Por que este projeto existe?
**Qual problema resolve? Quem é afetado se não fizermos?**

💡 **Exemplo**:
```
Atualmente, criar usuário exige 15 clics em 3 sistemas diferentes (LDAP, DB, Wiki).
Isso consome 30 minutos por usuário e gera erros em 20% dos casos.
Com esta API, reduzimos para 1 chamada REST (2 minutos, 0% erros).
```

**Seu projeto**:
```
<!-- Escreva aqui -->
```

---

### 3️⃣ Quem vai usar?
**Liste stakeholders/personas principais (máx 3).**

💡 **Exemplo**:
- **DevOps Engineers**: Automatizar criação de usuários via CI/CD
- **Admins de Sistema**: Interface web para gestão manual
- **Desenvolvedores**: SDK Python/TypeScript para integração

**Seu projeto**:
- <!-- Persona 1 -->
- <!-- Persona 2 -->
- <!-- Persona 3 -->

</details>

---

## 📝 Etapa 2/3: Detail — Contexto Adicional

<details>
<summary><strong>5 perguntas opcionais</strong> (recomendado preencher)</summary>

### 4️⃣ Como será implementado?
**Linguagem, framework, arquitetura.**

💡 **Deixe em branco para sugestão automática** baseada em `project.type`.

**Seu projeto** (opcional):
```yaml
language: Python
framework: FastAPI
database: PostgreSQL
architecture: REST API + async workers
```

---

### 5️⃣ Restrições conhecidas?
**Deadline, orçamento, compliance, dependências legadas.**

**Seu projeto** (opcional):
- Deadline: 2026-06-30
- Compliance: LGPD (dados de usuários brasileiros)
- Dependências: Integração com LDAP corporativo (read-only)

---

### 6️⃣ Como saberemos que deu certo?
**Métricas de sucesso, critérios de aceitação.**

💡 **Exemplo**:
- Tempo de criação de usuário: < 2 minutos (vs 30 min atual)
- Taxa de erro: < 1% (vs 20% atual)
- Adoção: 80% dos times em 3 meses

**Seu projeto** (opcional):
- <!-- Métrica 1 -->
- <!-- Métrica 2 -->

---

### 7️⃣ Riscos conhecidos?
**O que pode dar errado? Plano B?**

**Seu projeto** (opcional):
```
Risco 1: LDAP corporativo tem downtime frequente (média 2x/semana).
Mitigação: Cache local de usuários + sync job assíncrono.

Risco 2: Time de segurança pode bloquear integração.
Mitigação: Iniciar review de segurança na Semana 1.
```

---

### 8️⃣ Dependências externas?
**Serviços, APIs, times, ferramentas que precisamos.**

**Seu projeto** (opcional):
- LDAP corporativo (time de infraestrutura)
- PostgreSQL (já provisionado)
- Aprovação de segurança (SLA: 2 semanas)

</details>

---

## ⚙️ Etapa 3/3: Constrain — Avançado

<details>
<summary><strong>Apenas para usuários avançados</strong> (opcional)</summary>

### 9️⃣ Bounded Contexts (DDD)
**Se aplicável, definir contextos de domínio.**

```yaml
bounded_contexts:
  - name: "User Management"
    entities: ["User", "Role", "Permission"]
    ubiquitous_language:
      User: "Pessoa com conta no sistema"
      Role: "Conjunto de permissões atribuídas"

  - name: "Authentication"
    entities: ["Session", "Token", "Credential"]
```

---

### 🔟 Architecture Decision Records (ADRs)
**Decisões arquiteturais importantes tomadas.**

```markdown
## ADR-001: Usar PostgreSQL em vez de MongoDB

**Contexto**: Precisamos armazenar usuários com relações (roles, permissions).

**Decisão**: Usar PostgreSQL com SQLAlchemy ORM.

**Razão**:
- Relações complexas (FK, joins)
- ACID transactions necessárias
- Time já tem expertise em PostgreSQL

**Consequências**:
- ✅ Integridade referencial garantida
- ❌ Menos flexibilidade de schema (vs NoSQL)
```

---

### Extensões Customizadas
**Apenas se necessário (plugins).**

```yaml
extensions:
  ldap_integration:
    server: "ldap://ldap.empresa.com"
    base_dn: "ou=users,dc=empresa,dc=com"
    sync_interval: "1h"
```

</details>

---

## 🚀 Próximos Passos

**Após preencher, execute**:
```bash
# Validar antes de gerar
scaffold.py validate objetivo.yaml --explain

# Gerar especificação técnica
scaffold.py process objetivo.yaml

# Gerar projeto completo
scaffold.py compose
```

---

## 🆘 Precisa de Ajuda?

- 📖 **Documentação completa**: [docs/objetivo-guide.md](docs/objetivo-guide.md)
- 💬 **Suporte no Slack**: #template-support
- 🎥 **Tutorial em vídeo**: [youtube.com/...](...)
- 🐛 **Reportar problema**: [github.com/.../issues](...)
```

### Estrutura de Seções

```yaml
# Hierarquia proposta
nivel_1_express:       # P0 — Obrigatório (3 campos)
  - what               # String (10-500 chars)
  - why                # String (10-1000 chars)
  - who                # List[String] (1-5 items)

nivel_2_detail:        # P1 — Recomendado (5 campos)
  - how                # Dict (language, framework, architecture)
  - constraints        # List[String] (deadline, budget, compliance)
  - success_criteria   # List[String] (métricas)
  - risks              # List[Dict] (risco, mitigação)
  - dependencies       # List[String] (serviços externos)

nivel_3_constrain:     # P2 — Avançado (3 campos)
  - bounded_contexts   # List[Dict] (DDD)
  - adrs               # List[Dict] (decisões arquiteturais)
  - extensions         # Dict[String, Any] (plugins customizados)
```

### Exemplo Concreto: Projeto Simples (Python FastAPI)

```markdown
---
version: "2.0"
project:
  name: "todo-api"
  type: "backend-api"
---

# 🎯 Objetivo: Todo API

## ✅ Express

### O que?
API REST para gerenciar lista de tarefas (CRUD de todos + usuários).

### Por quê?
Projeto de aprendizado de FastAPI + PostgreSQL para portfólio.

### Quem?
- Eu (desenvolvedor júnior aprendendo backend)

## 📝 Detail

### Como?
```yaml
language: Python
framework: FastAPI
database: PostgreSQL
```

### Restrições?
- Deadline: Nenhum (projeto pessoal)
- Orçamento: Free tier (Render.com)

### Sucesso?
- API rodando em produção
- Testes automatizados (>80% coverage)
- Documentação completa (Swagger)
```

### Fluxo: Human → Machine-Readable

```
┌──────────────────────────────────────────────────────────────┐
│ FASE 1: Usuário preenche objetivo.yaml (Markdown híbrido)    │
│ Formato: Markdown + YAML frontmatter                         │
│ Tempo: 10-15 minutos (com wizard)                            │
│ Validação: Inline (via JSON Schema autocomplete)             │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ FASE 2: scaffold.py parse objetivo.yaml                      │
│ Parser: Extrai YAML frontmatter + converte Markdown → struct │
│ Output: Python dict validado por Pydantic                    │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ FASE 3: Copilot processa struct Python                       │
│ IA: Infere profiles, features, dependencies                  │
│ Output: objetivo-spec.yaml (YAML puro, machine-readable)     │
└────────┬─────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│ FASE 4: scaffold.py compose objetivo-spec.yaml               │
│ Template engine: Aplica profiles, gera arquivos              │
│ Output: Projeto completo (47+ arquivos)                      │
└──────────────────────────────────────────────────────────────┘
```

---

## 3.2. Proposta: Technical Writer (Marcus Silva)

### Formato Sugerido: **YAML com JSON Schema + Documentação Inline**

```yaml
# objetivo.yaml v2.0 (JSON Schema validated)
$schema: "https://schema.enterprise-template.io/objetivo-v2.json"
version: "2.0"

project:
  name: "user-api"
    #@ Tipo: String (kebab-case)
    #@ Padrão: ^[a-z0-9-]+$
    #@ Exemplo: "user-management-api", "payment-service"
    #@ Usado para: nome do diretório, repo Git, Docker image

  type: "backend-api"
    #@ Tipo: Enum
    #@ Valores: [backend-api, frontend-web, infrastructure, data-pipeline]
    #@ Determina: Perfis sugeridos, templates aplicados

  metadata:
    created_at: "2026-04-27T14:32:00Z"
    created_by: "alice@empresa.com"
    wizard_version: "2.0.1"

express:
  #@ Seção: Express — O Essencial (P0)
  #@ Tempo estimado: 3-5 minutos
  #@ Campos obrigatórios: what, why, who

  what: "API REST para gerenciar usuários"
    #@ Tipo: String (10-500 chars)
    #@ Descrição: O que este projeto faz? (1-2 frases)
    #@ Foco: Valor (não tecnologia)
    #@ Exemplos:
    #@   - "API REST para gerenciar usuários e autenticação"
    #@   - "Dashboard de analytics em tempo real"

  why: "Centralizar autenticação de 5 sistemas legados"
    #@ Tipo: String (10-1000 chars)
    #@ Descrição: Por que este projeto existe? Qual problema resolve?
    #@ Inclua: Dor atual, impacto, consequência de não fazer

  who:
    #@ Tipo: List[String] (1-5 items)
    #@ Descrição: Quem vai usar? Stakeholders/personas principais
    #@ Formato: "Persona: Necessidade"
    - "DevOps: Automatizar criação via CI/CD"
    - "Admins: Interface web para gestão manual"

detail:
  #@ Seção: Detail — Contexto Adicional (P1)
  #@ Tempo estimado: 5-8 minutos
  #@ Campos opcionais mas recomendados

  how:
    #@ Tipo: Dict
    #@ Descrição: Como será implementado? (tecnologia)
    #@ Se vazio: Sugestão automática baseada em project.type
    language: "Python"
      #@ Enum: [Python, TypeScript, Go, Rust, Java]
    framework: "FastAPI"
      #@ Enum (filtrado por language):
      #@   Python: [FastAPI, Flask, Django]
      #@   TypeScript: [NestJS, Next.js, Express]
    database: "PostgreSQL"
      #@ Enum: [PostgreSQL, MySQL, MongoDB, Redis, SQLite]

  constraints:
    #@ Tipo: List[Dict]
    #@ Descrição: Restrições conhecidas (deadline, budget, compliance)
    - type: "deadline"
      value: "2026-06-30"
      description: "Go-live de novo sistema"
    - type: "compliance"
      value: "LGPD"
      description: "Dados de usuários brasileiros"

  success_criteria:
    #@ Tipo: List[Dict]
    #@ Descrição: Como saberemos que deu certo? (métricas)
    - metric: "Tempo de criação de usuário"
      current: "30 minutos"
      target: "< 2 minutos"
      measurement: "Média semanal via logs"
    - metric: "Taxa de erro"
      current: "20%"
      target: "< 1%"
      measurement: "% de requisições 5xx"

constrain:
  #@ Seção: Constrain — Avançado (P2)
  #@ Apenas para usuários experientes
  #@ Todos os campos são opcionais

  bounded_contexts:
    #@ Tipo: List[Dict]
    #@ Descrição: Bounded Contexts (Domain-Driven Design)
    #@ Referência: https://martinfowler.com/bliki/BoundedContext.html
    - name: "User Management"
      entities: ["User", "Role", "Permission"]
      ubiquitous_language:
        User: "Pessoa com conta no sistema"
        Role: "Conjunto de permissões atribuídas"

  adrs:
    #@ Tipo: List[Dict]
    #@ Descrição: Architecture Decision Records
    #@ Template: docs/architecture/adr-template.md
    - id: "ADR-001"
      title: "Usar PostgreSQL em vez de MongoDB"
      context: "Precisamos armazenar usuários com relações"
      decision: "Usar PostgreSQL com SQLAlchemy ORM"
      consequences:
        - "✅ Integridade referencial garantida"
        - "❌ Menos flexibilidade de schema"
```

### JSON Schema Completo

```json
{
  "$id": "https://schema.enterprise-template.io/objetivo-v2.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Enterprise Scaffold Project Template — Objetivo v2.0",
  "description": "Especificação de projeto para geração automática",
  "type": "object",
  "required": ["version", "project", "express"],
  "properties": {
    "$schema": {
      "type": "string",
      "const": "https://schema.enterprise-template.io/objetivo-v2.json"
    },
    "version": {
      "type": "string",
      "const": "2.0",
      "description": "Versão do schema (Semantic Versioning)"
    },
    "project": {
      "$ref": "#/$defs/ProjectMetadata"
    },
    "express": {
      "$ref": "#/$defs/ExpressSection"
    },
    "detail": {
      "$ref": "#/$defs/DetailSection"
    },
    "constrain": {
      "$ref": "#/$defs/ConstrainSection"
    }
  },
  "$defs": {
    "ProjectMetadata": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-z0-9-]+$",
          "minLength": 3,
          "maxLength": 50,
          "description": "Nome do projeto (kebab-case)",
          "examples": ["user-api", "payment-service-v2"]
        },
        "type": {
          "type": "string",
          "enum": ["backend-api", "frontend-web", "infrastructure", "data-pipeline", "ml-training"],
          "description": "Tipo de projeto (determina perfis sugeridos)"
        }
      }
    },
    "ExpressSection": {
      "type": "object",
      "required": ["what", "why", "who"],
      "properties": {
        "what": {
          "type": "string",
          "minLength": 10,
          "maxLength": 500,
          "description": "O que este projeto faz? (1-2 frases, foco em valor)",
          "examples": ["API REST para gerenciar usuários e autenticação"]
        },
        "why": {
          "type": "string",
          "minLength": 10,
          "maxLength": 1000,
          "description": "Por que existe? Problema que resolve?",
          "examples": ["Centralizar autenticação de 5 sistemas legados"]
        },
        "who": {
          "type": "array",
          "minItems": 1,
          "maxItems": 5,
          "items": {"type": "string"},
          "description": "Quem vai usar? (stakeholders/personas)",
          "examples": [["DevOps Engineers", "Platform Admins"]]
        }
      }
    },
    "DetailSection": {
      "type": "object",
      "properties": {
        "how": {
          "$ref": "#/$defs/TechStack"
        },
        "constraints": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/Constraint"
          }
        },
        "success_criteria": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/SuccessCriterion"
          }
        }
      }
    }
  }
}
```

### Contextual Help System (Syntax `#@`)

```python
# lib/parsers/yaml_with_help.py
import yaml
import re

class YAMLWithHelpParser:
    """Parser YAML que extrai comentários de ajuda inline"""

    HELP_MARKER = "#@"

    def parse(self, file_path: str) -> tuple[dict, dict]:
        """Retorna (data, help_blocks)"""
        with open(file_path) as f:
            lines = f.readlines()

        # Extrair help blocks
        help_blocks = {}
        current_field = None

        for i, line in enumerate(lines):
            # Detectar campo
            if ':' in line and not line.strip().startswith('#'):
                field_match = re.match(r'^(\s*)(\w+):', line)
                if field_match:
                    indent = len(field_match.group(1))
                    field_name = field_match.group(2)
                    current_field = field_name

            # Detectar help comment
            if line.strip().startswith(self.HELP_MARKER):
                if current_field:
                    if current_field not in help_blocks:
                        help_blocks[current_field] = []
                    help_text = line.split(self.HELP_MARKER, 1)[1].strip()
                    help_blocks[current_field].append(help_text)

        # Parse YAML (removendo comentários de ajuda)
        clean_yaml = '\n'.join(
            line for line in lines
            if not line.strip().startswith(self.HELP_MARKER)
        )
        data = yaml.safe_load(clean_yaml)

        return data, help_blocks

# Uso
parser = YAMLWithHelpParser()
data, help_blocks = parser.parse("objetivo.yaml")

print(help_blocks["what"])
# Output:
# [
#   "Tipo: String (10-500 chars)",
#   "Descrição: O que este projeto faz? (1-2 frases)",
#   "Foco: Valor (não tecnologia)",
#   ...
# ]
```

### Fluxo: Human → Machine

```
objetivo.yaml (YAML com #@ comments)
    │
    ├─→ JSON Schema validation (ajv)
    │   ├─ Syntax check
    │   ├─ Type checking
    │   ├─ Required fields
    │   └─ Regex patterns
    │
    ├─→ YAMLWithHelpParser.parse()
    │   ├─ Extract help blocks
    │   ├─ Parse clean YAML
    │   └─ Return (data, help)
    │
    └─→ Pydantic ObjetivoV2(**data)
        ├─ Custom validators
        ├─ Cross-field validation
        └─ Business rules
```

---

## 3.3. Proposta: DevOps Expert (Elena Rodriguez)

### Formato Sugerido: **Two-File Architecture (Input/Output Separation)**

**Arquivo 1: `objetivo.yaml` (Input — Human-Writable)**

```yaml
# objetivo.yaml v2.0 — INPUT (editável pelo usuário)
version: "2.0"
_hash: null  # Calculado automaticamente por scaffold.py

project:
  name: "user-api"
  type: "backend-api"
  metadata:
    created_at: "2026-04-27T14:32:00Z"
    created_by: "alice@empresa.com"

express:
  what: "API REST para gerenciar usuários"
  why: "Centralizar autenticação de 5 sistemas legados"
  who:
    - "DevOps Engineers"
    - "Platform Admins"

detail:
  how:
    language: "Python"
    framework: "FastAPI"
    database: "PostgreSQL"

  constraints:
    - type: "deadline"
      value: "2026-06-30"
    - type: "compliance"
      value: "LGPD"

  success_criteria:
    - metric: "Tempo de criação de usuário"
      target: "< 2 minutos"

# FIM DO INPUT HUMANO
# Campos abaixo SÃO GERADOS automaticamente (não editar!)
_computed:
  hash: "a1b2c3d4e5f6..."  # SHA256 de objetivo.yaml
  processed_at: "2026-04-27T14:35:12Z"
  scaffold_version: "2.0.1"
```

**Arquivo 2: `objetivo-spec.yaml` (Output — Machine-Generated)**

```yaml
# objetivo-spec.yaml v2.0 — OUTPUT (gerado por Copilot, NÃO editar!)
# Gerado a partir de: objetivo.yaml (hash: a1b2c3d4e5f6...)
# Gerado em: 2026-04-27T14:35:12Z
# Gerado por: scaffold.py v2.0.1 + Copilot

version: "2.0"
_input_hash: "a1b2c3d4e5f6..."  # Referência ao objetivo.yaml
_generated_at: "2026-04-27T14:35:12Z"

# Inferências automáticas (IA)
profiles:
  backend:
    - "python-fastapi"
  database:
    - "postgresql-expert"
  infrastructure:
    - "docker-compose"
    - "github-actions"

features:
  - id: "F-001"
    name: "User CRUD endpoints"
    priority: "P0"
    estimated_effort: "3 days"

  - id: "F-002"
    name: "Authentication (JWT)"
    priority: "P0"
    estimated_effort: "2 days"

  - id: "F-003"
    name: "Role-based access control"
    priority: "P1"
    estimated_effort: "4 days"

dependencies:
  internal:
    - name: "PostgreSQL"
      type: "database"
      version: ">=14.0"

  external:
    - name: "LDAP corporativo"
      type: "service"
      criticality: "high"
      owner: "infra-team"

folder_structure:
  - ".github/workflows/ci.yml"
  - "src/api/users.py"
  - "src/api/auth.py"
  - "src/models/user.py"
  - "tests/test_users.py"
  - "Dockerfile"
  - "docker-compose.yml"
  - "Makefile"
  - "README.md"
  # ... (47 arquivos totais)

pending_tasks:
  - id: "T-001"
    description: "Setup PostgreSQL schema"
    assignee: "Copilot"
    status: "pending"

  - id: "T-002"
    description: "Implement User CRUD"
    assignee: "alice@empresa.com"
    status: "pending"

# Metadata de geração
_generation_metadata:
  copilot_model: "claude-sonnet-4.5"
  processing_time_seconds: 127
  confidence_score: 0.92
  warnings:
    - "LDAP integration não tem exemplo — requer customização"
```

### Garantias Arquiteturais

```python
# lib/processors/two_file_processor.py
class TwoFileProcessor:
    """Processa objetivo.yaml → objetivo-spec.yaml com garantias"""

    def process(self, input_file: str, output_file: str) -> ProcessResult:
        # 1. Validar input
        objetivo = self.validate_input(input_file)

        # 2. Calcular hash (idempotência)
        input_hash = self.compute_hash(objetivo)

        # 3. Verificar se output existe e está atualizado
        if self.is_up_to_date(output_file, input_hash):
            return ProcessResult(
                status="unchanged",
                message="objetivo-spec.yaml já está atualizado",
                hash=input_hash
            )

        # 4. Gerar spec via Copilot
        spec = self.generate_spec_with_copilot(objetivo)
        spec["_input_hash"] = input_hash
        spec["_generated_at"] = datetime.utcnow().isoformat()

        # 5. Salvar output (atomically)
        self.save_atomically(output_file, spec)

        # 6. Atualizar state machine
        self.update_state(ObjectiveState.SPEC_GENERATED)

        return ProcessResult(
            status="generated",
            message=f"objetivo-spec.yaml gerado (hash: {input_hash[:8]})",
            hash=input_hash,
            files_generated=len(spec["folder_structure"])
        )

    def compute_hash(self, objetivo: ObjetivoV2) -> str:
        """Hash determinístico (ignora campos _computed)"""
        # Remove campos computados
        clean_data = objetivo.dict(exclude={"_computed", "_hash"})

        # Normalizar (sort keys, formato)
        normalized = json.dumps(clean_data, sort_keys=True)

        return hashlib.sha256(normalized.encode()).hexdigest()

    def save_atomically(self, file_path: str, data: dict):
        """Salva arquivo atomicamente (evita corrupção)"""
        temp_file = f"{file_path}.tmp"

        with open(temp_file, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

        # Atomic rename (substitui arquivo antigo)
        os.replace(temp_file, file_path)
```

### CI/CD Integration

```yaml
# .github/workflows/objetivo-validation.yml
name: Validate objetivo.yaml Changes

on:
  pull_request:
    paths:
      - 'objetivo.yaml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Histórico completo para diff

      - name: Install dependencies
        run: pip install -r requirements.txt

      # Validação em 4 camadas
      - name: Layer 1 — Syntax validation
        run: scaffold.py validate objetivo.yaml --level syntax

      - name: Layer 2 — Schema validation
        run: scaffold.py validate objetivo.yaml --level schema

      - name: Layer 3 — Semantic validation
        run: scaffold.py validate objetivo.yaml --level semantics

      - name: Layer 4 — Business validation
        run: scaffold.py validate objetivo.yaml --level business --warn-only

      # Diff analysis
      - name: Detect breaking changes
        id: diff
        run: |
          scaffold.py diff objetivo.yaml origin/main --format json > diff.json
          echo "has_breaking_changes=$(jq '.breaking_changes | length > 0' diff.json)" >> $GITHUB_OUTPUT

      - name: Comment breaking changes on PR
        if: steps.diff.outputs.has_breaking_changes == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const diff = JSON.parse(fs.readFileSync('diff.json', 'utf8'));
            const breaking = diff.breaking_changes.map(c => `- ${c.field}: ${c.description}`).join('\n');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## ⚠️ Breaking Changes Detected\n\n${breaking}\n\nSee: docs/objetivo-guide/migration.md`
            });

      # Regenerar spec (dry-run)
      - name: Generate spec preview
        run: |
          scaffold.py process objetivo.yaml --dry-run --output objetivo-spec.preview.yaml

      - name: Upload spec preview
        uses: actions/upload-artifact@v4
        with:
          name: objetivo-spec-preview
          path: objetivo-spec.preview.yaml
```

---

*(Continuará na próxima seção com as propostas de Dr. James Wei e Priya Sharma, seguido do Debate e Convergência...)*

---

# 4. DEBATE E CONVERGÊNCIA

## 4.1. Moderador (Template Architect Agent)

**[Moderador]**: Obrigado pelas 3 propostas detalhadas. Vamos agora compará-las e identificar pontos de consenso e divergências.

### Tabela Comparativa

| Critério | Sarah (UX) | Marcus (Tech Writer) | Elena (DevOps) |
|----------|------------|----------------------|----------------|
| **Formato base** | Markdown + YAML frontmatter | YAML puro + JSON Schema | YAML puro (two-file) |
| **Separação input/output** | Não (tudo em objetivo.yaml) | Não (tudo em objetivo.yaml) | ✅ Sim (objetivo.yaml + objetivo-spec.yaml) |
| **Progressive disclosure** | ✅ Sim (3 níveis via `<details>`) | ⚠️ Parcial (comentários `#@`) | ❌ Não (flat structure) |
| **Validação inline** | ✅ Sim (exemplos em Markdown) | ✅ Sim (JSON Schema + `#@`) | ✅ Sim (Pydantic + hash) |
| **Human-readable** | ⭐⭐⭐⭐⭐ (Markdown narrativo) | ⭐⭐⭐ (YAML técnico) | ⭐⭐⭐ (YAML limpo) |
| **Machine-readable** | ⭐⭐⭐ (parsing Markdown) | ⭐⭐⭐⭐⭐ (YAML puro) | ⭐⭐⭐⭐⭐ (YAML puro) |
| **Idempotência** | ⚠️ Não documentada | ⚠️ Não documentada | ✅ Sim (hash tracking) |
| **Backward compatibility** | ❌ Não mencionada | ⚠️ Versionamento via schema | ✅ Sim (dual support 6 meses) |
| **CI/CD integration** | ⚠️ Não detalhada | ⚠️ Mencionada | ✅ Sim (workflow completo) |
| **Wizard support** | ✅ Sim (Markdown gerado por wizard) | ⚠️ Não detalhado | ✅ Sim (gera YAML) |
| **Complexidade para iniciantes** | ⭐⭐ (Baixa — Markdown familiar) | ⭐⭐⭐⭐ (Alta — YAML técnico) | ⭐⭐⭐ (Média — YAML estruturado) |

### Pontos de Consenso

**[Todos os especialistas concordam]**:

1. ✅ **Separar campos obrigatórios vs opcionais** (express vs detail vs constrain)
2. ✅ **Validação em múltiplas camadas** (syntax → schema → semantics → business)
3. ✅ **Versionamento semântico** do schema (v2.0)
4. ✅ **Exemplos inline** em todos os campos
5. ✅ **Wizard guiado** como modo padrão para iniciantes
6. ✅ **Documentação como código** (não apenas comentários)

### Divergências Principais

**Divergência #1: Formato (Markdown vs YAML)**

**[Sarah Chen — UX]**: "Markdown é mais acessível para iniciantes. 72% dos desenvolvedores júnior já usam Markdown diariamente (README.md, issues, PRs). YAML é intimidador."

**[Marcus Silva — Tech Writer]**: "Markdown não é estruturadamente validável. Como faço autocomplete em editores? JSON Schema funciona perfeitamente com YAML, mas não com Markdown."

**[Elena Rodriguez — DevOps]**: "Parsear Markdown é não-determinístico. Preciso de garantias de que dois parsers (Python e TypeScript, por exemplo) geram mesmo output. YAML é padrão."

**[Dr. James Wei — Principal Engineer]**: "Concordo com Elena. Mas... e se fizermos **híbrido**? Markdown para seções narrativas (express.why), YAML frontmatter para metadados estruturados?"

**[Priya Sharma — PM]**: "Dados de adoção: 65% dos usuários preferem Markdown em pesquisa qualitativa. Mas 78% dos usuários avançados querem YAML puro para automação. **Precisamos de ambos**."

**Divergência #2: Separação de arquivos (1 arquivo vs 2)**

**[Sarah Chen]**: "Um único arquivo é mais simples. Usuário não precisa entender 'input vs output'."

**[Elena Rodriguez]**: "Um único arquivo gera **acoplamento temporal**. Se Copilot escreve no mesmo arquivo que o usuário, temos race conditions em Git. Já vi 47 merge conflicts em objetivo.yaml nos últimos 3 meses."

**[Dr. James Wei]**: "Elena está correta. Separation of Concerns é fundamental. Mas podemos fazer transição gradual: objetivo.yaml (v2.0) ainda é single-file, mas objetivo-spec.yaml é **opcional** (gerado apenas se usuário rodar `scaffold.py process --separate-spec`)."

**[Marcus Silva]**: "Documentação precisa deixar claríssimo: objetivo.yaml é INPUT (editável), objetivo-spec.yaml é OUTPUT (read-only). Se não ficar óbvio, usuários vão editar ambos."

**[Priya Sharma]**: "Dados: 82% dos usuários iniciantes não entendem diferença entre 'input' e 'output' sem treinamento. Proposta: wizard gera objetivo.yaml single-file; modo avançado (`--advanced`) gera two-file."

### Votação (Resolução de Divergências)

**[Moderador]**: Vamos votar nas 2 divergências principais.

#### Votação #1: Formato base

| Opção | Votos | Justificativa |
|-------|-------|---------------|
| **A) Markdown puro** | 0 | — |
| **B) YAML puro** | 0 | — |
| **C) Markdown + YAML frontmatter (híbrido)** | 5/5 | ✅ **VENCEDOR** — Melhor de ambos |

**Decisão**: **Markdown híbrido** com YAML frontmatter para metadados.

```markdown
---
# YAML frontmatter (estruturado, validável)
version: "2.0"
project:
  name: "user-api"
  type: "backend-api"
---

# Markdown body (narrativo, human-friendly)
## 🎯 O que este projeto faz?

API REST para gerenciar usuários...
```

#### Votação #2: Separação de arquivos

| Opção | Votos | Justificativa |
|-------|-------|---------------|
| **A) Single-file sempre** | 1 | Sarah (simplicidade) |
| **B) Two-file sempre** | 2 | Elena, James (separation) |
| **C) Single-file por padrão, two-file opcional** | 2 | Marcus, Priya (progressive) |

**Empate**: 2-2-1. **Moderador decide** por **Opção C** (progressive approach).

**Decisão**: **Single-file por padrão** (objetivo.yaml contém tudo), **two-file opcional** (`--separate-spec` flag).

```bash
# Modo padrão (single-file)
$ scaffold.py process objetivo.yaml
[✓] objetivo.yaml updated (added _computed section)

# Modo avançado (two-file)
$ scaffold.py process objetivo.yaml --separate-spec
[✓] objetivo-spec.yaml generated
[!] objetivo.yaml is now read-only input (do not edit _computed)
```

---

## 4.2. Proposta Unificada (Consenso)

### Two-File Progressive Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ objetivo.yaml (Markdown + YAML frontmatter)                      │
│ ──────────────────────────────────────────────────────────────  │
│ Ownership: Usuário (versionado, editável)                       │
│ Formato: Markdown body + YAML frontmatter                       │
│ Validação: JSON Schema (frontmatter) + linting (Markdown)       │
│ Modo: Single-file (padrão) ou Input (two-file mode)             │
└────────┬────────────────────────────────────────────────────────┘
         │
         │ (two-file mode: --separate-spec)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ objetivo-spec.yaml (YAML puro)                                   │
│ ──────────────────────────────────────────────────────────────  │
│ Ownership: Copilot/SpecKit (gerado, read-only)                  │
│ Formato: YAML puro (machine-readable)                           │
│ Validação: Pydantic models                                      │
│ Modo: Output (opcional, regenerável)                            │
└─────────────────────────────────────────────────────────────────┘
```

### Especificação Completa

```markdown
---
# ========================================
# YAML Frontmatter — Metadados Estruturados
# ========================================
$schema: "https://schema.enterprise-template.io/objetivo-v2.json"
version: "2.0"

project:
  name: "user-management-api"
  type: "backend-api"
  metadata:
    created_at: "2026-04-27T14:32:00Z"
    created_by: "alice@empresa.com"
    wizard_version: "2.0.1"

express:
  what: "API REST para gerenciar usuários (CRUD + autenticação)"
  why: "Centralizar autenticação de 5 sistemas legados"
  who:
    - "DevOps Engineers"
    - "Platform Admins"
    - "Desenvolvedores frontend"

detail:
  how:
    language: "Python"
    framework: "FastAPI"
    database: "PostgreSQL"
  constraints:
    - type: "deadline"
      value: "2026-06-30"
    - type: "compliance"
      value: "LGPD"
  success_criteria:
    - metric: "Tempo de criação de usuário"
      target: "< 2 minutos"
      measurement: "Média semanal via logs"
---

# ========================================
# Markdown Body — Narrativa Human-Friendly
# ========================================

# 🎯 Objetivo: User Management API

> **Status**: Draft | **Última atualização**: 2026-04-27

---

## 1️⃣ O que este projeto faz?

API REST completa para gerenciar usuários com as seguintes capacidades:

- **CRUD de usuários**: Criar, listar, atualizar, deletar contas
- **Autenticação JWT**: Login/logout com tokens stateless
- **Gestão de roles**: Atribuir permissões (admin, user, guest)
- **Integração LDAP**: Sincronizar com diretório corporativo

### Caso de uso principal

```
Administrador acessa painel web → Cria novo usuário → Sistema:
  1. Valida dados (email único, senha forte)
  2. Cria registro no PostgreSQL
  3. Sincroniza com LDAP corporativo
  4. Envia email de boas-vindas
  5. Retorna 201 Created com link de ativação
```

---

## 2️⃣ Por que este projeto existe?

### Problema atual

Atualmente, criar um usuário requer:

1. **15 clics em 3 sistemas** (LDAP, DB admin, Wiki)
2. **30 minutos de trabalho manual**
3. **20% de taxa de erro** (permissões erradas, typos em email)

**Impacto anual**:
- 120 horas desperdiçadas (40 usuários/ano × 30 min)
- R$ 18.000 em custos operacionais (120h × R$ 150/h)
- 8 incidentes de segurança (usuários com permissões erradas)

### Solução proposta

Com esta API, reduzimos para:

1. **1 chamada REST** (ou 1 clique no painel web)
2. **2 minutos** de tempo total
3. **< 1% de taxa de erro** (validações automatizadas)

**ROI esperado**:
- 98% de redução de tempo (30 min → 2 min)
- R$ 16.800/ano de economia (93% de redução de custos)
- Zero incidentes de permissões erradas

---

## 3️⃣ Quem vai usar?

### Persona 1: DevOps Engineer (Carlos, 4 anos exp)

**Necessidade**: Automatizar criação de usuários via CI/CD

**Fluxo**:
```bash
# Em pipeline GitLab CI
curl -X POST https://api.empresa.com/users \
  -H "Authorization: Bearer $CI_TOKEN" \
  -d '{"email": "novo@empresa.com", "role": "developer"}'
```

**Pain point resolvido**: Não precisa mais abrir ticket para infra team.

---

### Persona 2: Admin de Sistema (Maria, 6 anos exp)

**Necessidade**: Interface web para gestão manual de usuários

**Fluxo**: Acessa painel web → Formulário intuitivo → Usuário criado em 2 cliques

**Pain point resolvido**: Não precisa mais SSH em servidor para rodar comandos SQL.

---

### Persona 3: Desenvolvedor Frontend (João, 2 anos exp)

**Necessidade**: SDK TypeScript para integrar com app React

**Fluxo**:
```typescript
import { UserAPI } from '@empresa/user-sdk';

const api = new UserAPI({ token: process.env.API_TOKEN });
await api.users.create({ email: 'novo@empresa.com' });
```

**Pain point resolvido**: Não precisa construir cliente HTTP do zero.

---

## 4️⃣ Como será implementado?

### Stack técnico

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| **Backend** | Python 3.11 + FastAPI | Async, performance, auto-docs Swagger |
| **ORM** | SQLAlchemy 2.0 | Type hints, async, migrations |
| **Database** | PostgreSQL 14+ | ACID, relações complexas, JSONB |
| **Auth** | JWT (PyJWT) | Stateless, escalável, padrão RFC 7519 |
| **Testing** | pytest + pytest-asyncio | Coverage >80%, fixtures reutilizáveis |
| **Linting** | ruff | 10x mais rápido que flake8+black |
| **CI/CD** | GitHub Actions | Gratuito, integrado, matrix testing |
| **Deploy** | Docker + docker-compose | Portável, reproduzível |

### Arquitetura

```
┌─────────────┐
│  Frontend   │ (React app)
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────┐
│  FastAPI    │ (async REST API)
│  + JWT Auth │
└──────┬──────┘
       │
       ├──→ ┌──────────────┐
       │    │ PostgreSQL   │ (users, roles, sessions)
       │    └──────────────┘
       │
       └──→ ┌──────────────┐
            │ LDAP Server  │ (sync users)
            └──────────────┘
```

---

## 5️⃣ Restrições e riscos

### Restrições

| Tipo | Descrição | Impacto |
|------|-----------|---------|
| **Deadline** | 2026-06-30 (go-live novo sistema) | Alto — não negociável |
| **Compliance** | LGPD (dados de usuários BR) | Alto — multa até R$ 50 milhões |
| **Integração** | LDAP corporativo (read-only) | Médio — dependência de infra team |

### Riscos

#### Risco 1: LDAP corporativo tem downtime frequente (2x/semana)

**Probabilidade**: Alta (80%)
**Impacto**: Médio (sync falha, mas API continua funcionando)

**Mitigação**:
- Cache local de usuários LDAP (refresh a cada 1h)
- Sync job assíncrono com retry exponential backoff
- Alerta no Slack se sync falhar por >4 horas

#### Risco 2: Time de segurança pode bloquear integração

**Probabilidade**: Média (40%)
**Impacto**: Alto (projeto bloqueado até aprovação)

**Mitigação**:
- Iniciar Security Review na **Semana 1** (não esperar código pronto)
- Threat model workshop com security team (2 horas)
- Implementar todos os controles OWASP Top 10

---

## 6️⃣ Como saberemos que deu certo?

### Métricas de sucesso

| Métrica | Baseline (atual) | Target (6 meses) | Medição |
|---------|------------------|------------------|---------|
| **Tempo de criação** | 30 min | < 2 min | Logs de API (p95) |
| **Taxa de erro** | 20% | < 1% | % de 5xx responses |
| **Adoção** | 0% | 80% dos times | Survey mensal |
| **Uptime** | N/A | 99.5% | Datadog SLO |
| **Satisfação** | N/A | NPS > 50 | Survey trimestral |

### Critérios de aceitação (go-live)

- [ ] API responde em < 200ms (p95)
- [ ] Testes automatizados com >80% coverage
- [ ] Security review aprovado
- [ ] Documentação completa (Swagger + README)
- [ ] Runbook de incidentes
- [ ] Treinamento dado para 3 times piloto

---

## 7️⃣ Dependências

### Internas

| Dependência | Owner | Criticality | Status |
|-------------|-------|-------------|--------|
| **PostgreSQL** | DBA team | Alta | ✅ Provisionado |
| **LDAP access** | Infra team | Alta | ⏳ Pendente aprovação |
| **GitHub Actions** | DevOps | Média | ✅ Disponível |

### Externas

| Dependência | Vendor | SLA | Backup |
|-------------|--------|-----|--------|
| **LDAP corporativo** | Interno | 95% uptime | Cache local |
| **Email SMTP** | SendGrid | 99.9% uptime | Queue retry |

---

## 🚀 Próximos Passos

**Após revisar este documento**:

1. Validar: `scaffold.py validate objetivo.yaml`
2. Gerar spec: `scaffold.py process objetivo.yaml`
3. Gerar projeto: `scaffold.py compose`
4. Rodar localmente: `make dev`

**Precisa de ajuda?**

- 📖 [Documentação completa](docs/objetivo-guide.md)
- 💬 [Slack: #template-support](https://empresa.slack.com/...)
- 🐛 [Reportar issue](https://github.com/org/repo/issues)

---

**Versão**: 2.0 | **Última atualização**: 2026-04-27 14:32 UTC
```

---

# 5. ESPECIFICAÇÃO FINAL

## 5.1. Schema Completo (JSON Schema)

```json
{
  "$id": "https://schema.enterprise-template.io/objetivo-v2.json",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Enterprise Scaffold Project Template — Objetivo v2.0",
  "description": "Especificação de projeto para geração automática via scaffold.py + Copilot",
  "version": "2.0.0",
  "type": "object",
  "required": ["version", "project", "express"],

  "properties": {
    "$schema": {
      "type": "string",
      "const": "https://schema.enterprise-template.io/objetivo-v2.json",
      "description": "Referência ao JSON Schema (para autocomplete em editores)"
    },

    "version": {
      "type": "string",
      "const": "2.0",
      "description": "Versão do schema (Semantic Versioning)"
    },

    "project": {
      "$ref": "#/$defs/ProjectMetadata",
      "description": "Metadados identificadores do projeto"
    },

    "express": {
      "$ref": "#/$defs/ExpressSection",
      "description": "Seção Express — O Essencial (P0, obrigatório)"
    },

    "detail": {
      "$ref": "#/$defs/DetailSection",
      "description": "Seção Detail — Contexto Adicional (P1, recomendado)"
    },

    "constrain": {
      "$ref": "#/$defs/ConstrainSection",
      "description": "Seção Constrain — Avançado (P2, opcional)"
    }
  },

  "$defs": {
    "ProjectMetadata": {
      "type": "object",
      "required": ["name", "type"],
      "properties": {
        "name": {
          "type": "string",
          "pattern": "^[a-z0-9-]+$",
          "minLength": 3,
          "maxLength": 50,
          "description": "Nome do projeto (kebab-case)",
          "examples": [
            "user-management-api",
            "payment-service-v2",
            "analytics-dashboard"
          ],
          "errorMessage": {
            "pattern": "Nome deve conter apenas letras minúsculas, números e hífens (kebab-case)",
            "minLength": "Nome deve ter pelo menos 3 caracteres",
            "maxLength": "Nome não pode exceder 50 caracteres"
          }
        },

        "type": {
          "type": "string",
          "enum": [
            "backend-api",
            "frontend-web",
            "infrastructure",
            "data-pipeline",
            "ml-training",
            "mobile-app",
            "desktop-app",
            "library",
            "cli-tool"
          ],
          "description": "Tipo de projeto (determina perfis sugeridos e templates aplicados)",
          "examples": ["backend-api", "frontend-web"],
          "$comment": "Cada tipo mapeia para um conjunto de profiles em profile-descriptors/"
        },

        "metadata": {
          "type": "object",
          "properties": {
            "created_at": {
              "type": "string",
              "format": "date-time",
              "description": "Timestamp ISO 8601 de criação"
            },
            "created_by": {
              "type": "string",
              "format": "email",
              "description": "Email do criador do projeto"
            },
            "wizard_version": {
              "type": "string",
              "pattern": "^\\d+\\.\\d+\\.\\d+$",
              "description": "Versão do wizard que gerou este arquivo (semver)"
            },
            "wizard_used": {
              "type": "boolean",
              "description": "Se foi criado via wizard (true) ou manualmente (false)"
            }
          }
        }
      }
    },

    "ExpressSection": {
      "type": "object",
      "required": ["what", "why", "who"],
      "properties": {
        "what": {
          "type": "string",
          "minLength": 10,
          "maxLength": 500,
          "description": "O que este projeto faz? (1-2 frases, foco no VALOR não na tecnologia)",
          "examples": [
            "API REST para gerenciar usuários e autenticação",
            "Dashboard de analytics em tempo real para vendas",
            "Pipeline de ETL para data warehouse"
          ],
          "$comment": "Validador custom: não permitir > 2 termos técnicos (asyncio, orm, jwt, etc.)"
        },

        "why": {
          "type": "string",
          "minLength": 10,
          "maxLength": 1000,
          "description": "Por que este projeto existe? Qual problema resolve? Quem é afetado se não fizermos?",
          "examples": [
            "Centralizar autenticação de 5 sistemas legados (atualmente 30 min/usuário com 20% erros)"
          ],
          "$comment": "Deve incluir: dor atual, impacto quantificado, consequência de não fazer"
        },

        "who": {
          "type": "array",
          "minItems": 1,
          "maxItems": 5,
          "items": {
            "type": "string",
            "minLength": 5,
            "maxLength": 200
          },
          "description": "Quem vai usar? (stakeholders/personas principais)",
          "examples": [
            ["DevOps Engineers", "Platform Admins", "Frontend Developers"]
          ],
          "$comment": "Formato preferido: 'Persona: Necessidade' (ex: 'DevOps: Automatizar criação via CI/CD')"
        }
      }
    },

    "DetailSection": {
      "type": "object",
      "properties": {
        "how": {
          "$ref": "#/$defs/TechStack",
          "description": "Como será implementado? (tecnologia, arquitetura)"
        },

        "constraints": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/Constraint"
          },
          "description": "Restrições conhecidas (deadline, orçamento, compliance)"
        },

        "success_criteria": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/SuccessCriterion"
          },
          "description": "Métricas de sucesso (como saberemos que deu certo?)"
        },

        "risks": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/Risk"
          },
          "description": "Riscos conhecidos e mitigações"
        },

        "dependencies": {
          "$ref": "#/$defs/Dependencies",
          "description": "Dependências internas e externas"
        }
      }
    },

    "TechStack": {
      "type": "object",
      "properties": {
        "language": {
          "type": "string",
          "enum": [
            "Python",
            "TypeScript",
            "JavaScript",
            "Go",
            "Rust",
            "Java",
            "Kotlin",
            "C#",
            "Ruby",
            "PHP"
          ],
          "description": "Linguagem principal de programação"
        },

        "framework": {
          "type": "string",
          "description": "Framework principal (validado dinamicamente por language)",
          "$comment": "Enums dinâmicos: Python=[FastAPI,Flask,Django], TypeScript=[NestJS,Next.js,Express], etc."
        },

        "database": {
          "type": "string",
          "enum": [
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Redis",
            "SQLite",
            "DynamoDB",
            "Cassandra",
            "Elasticsearch"
          ],
          "description": "Banco de dados principal"
        },

        "architecture": {
          "type": "string",
          "description": "Arquitetura geral (livre, narrativo)",
          "examples": [
            "REST API + async workers",
            "Microservices com event bus",
            "Serverless (Lambda + DynamoDB)"
          ]
        }
      }
    },

    "Constraint": {
      "type": "object",
      "required": ["type", "value"],
      "properties": {
        "type": {
          "type": "string",
          "enum": [
            "deadline",
            "budget",
            "compliance",
            "performance",
            "security",
            "integration",
            "other"
          ]
        },
        "value": {
          "type": "string",
          "description": "Valor da restrição (formato depende de type)",
          "examples": ["2026-06-30", "R$ 50.000", "LGPD", "< 200ms p95"]
        },
        "description": {
          "type": "string",
          "description": "Explicação adicional (opcional)"
        },
        "severity": {
          "type": "string",
          "enum": ["blocker", "critical", "major", "minor"],
          "default": "major"
        }
      }
    },

    "SuccessCriterion": {
      "type": "object",
      "required": ["metric", "target"],
      "properties": {
        "metric": {
          "type": "string",
          "description": "Nome da métrica",
          "examples": [
            "Tempo de criação de usuário",
            "Taxa de erro",
            "Uptime",
            "NPS"
          ]
        },
        "current": {
          "type": "string",
          "description": "Valor atual (baseline)"
        },
        "target": {
          "type": "string",
          "description": "Valor alvo"
        },
        "measurement": {
          "type": "string",
          "description": "Como será medido",
          "examples": [
            "Logs de API (p95)",
            "% de 5xx responses",
            "Datadog SLO"
          ]
        }
      }
    },

    "Risk": {
      "type": "object",
      "required": ["description", "probability", "impact"],
      "properties": {
        "description": {
          "type": "string",
          "description": "Descrição do risco"
        },
        "probability": {
          "type": "string",
          "enum": ["low", "medium", "high"],
          "description": "Probabilidade de ocorrer"
        },
        "impact": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical"],
          "description": "Impacto se ocorrer"
        },
        "mitigation": {
          "type": "string",
          "description": "Plano de mitigação"
        }
      }
    },

    "Dependencies": {
      "type": "object",
      "properties": {
        "internal": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/Dependency"
          },
          "description": "Dependências internas (times, serviços, infraestrutura)"
        },
        "external": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/Dependency"
          },
          "description": "Dependências externas (vendors, APIs, SaaS)"
        }
      }
    },

    "Dependency": {
      "type": "object",
      "required": ["name", "type", "criticality"],
      "properties": {
        "name": {
          "type": "string"
        },
        "type": {
          "type": "string",
          "enum": [
            "service",
            "database",
            "api",
            "team",
            "infrastructure",
            "library",
            "saas",
            "other"
          ]
        },
        "criticality": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical"]
        },
        "owner": {
          "type": "string",
          "description": "Responsável pela dependência"
        },
        "status": {
          "type": "string",
          "enum": ["available", "pending", "blocked"],
          "default": "available"
        },
        "sla": {
          "type": "string",
          "description": "SLA da dependência (se aplicável)",
          "examples": ["99.9% uptime", "2 semanas para aprovação"]
        }
      }
    },

    "ConstrainSection": {
      "type": "object",
      "description": "Seção Constrain — Apenas para usuários avançados",
      "properties": {
        "bounded_contexts": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/BoundedContext"
          },
          "description": "Bounded Contexts (Domain-Driven Design)"
        },

        "adrs": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/ADR"
          },
          "description": "Architecture Decision Records"
        },

        "extensions": {
          "type": "object",
          "additionalProperties": true,
          "description": "Extensões customizadas (plugins)"
        }
      }
    },

    "BoundedContext": {
      "type": "object",
      "required": ["name", "entities"],
      "properties": {
        "name": {
          "type": "string",
          "description": "Nome do bounded context"
        },
        "entities": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Entidades principais deste contexto"
        },
        "ubiquitous_language": {
          "type": "object",
          "additionalProperties": {"type": "string"},
          "description": "Definições de termos do domínio"
        }
      }
    },

    "ADR": {
      "type": "object",
      "required": ["id", "title", "context", "decision", "consequences"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^ADR-\\d{3}$",
          "description": "ID único (formato: ADR-001)"
        },
        "title": {
          "type": "string",
          "description": "Título da decisão"
        },
        "context": {
          "type": "string",
          "description": "Contexto e problema"
        },
        "decision": {
          "type": "string",
          "description": "Decisão tomada"
        },
        "consequences": {
          "type": "array",
          "items": {"type": "string"},
          "description": "Consequências da decisão (positivas e negativas)"
        },
        "status": {
          "type": "string",
          "enum": ["proposed", "accepted", "deprecated", "superseded"],
          "default": "accepted"
        },
        "date": {
          "type": "string",
          "format": "date",
          "description": "Data da decisão (YYYY-MM-DD)"
        }
      }
    }
  }
}
```

---

*(Documento continua com mais ~1500 linhas cobrindo seções 6-7: Migração e Implementação...)*

---

# 6. ESTRATÉGIA DE MIGRAÇÃO

## 6.1. Script de Conversão Automática

```python
#!/usr/bin/env python3
"""
migrate-objetivo.py — Migração automática objetivo.yaml v1.0 → v2.0

Uso:
    python scripts/migrate-objetivo.py objetivo.yaml --to-v2
    python scripts/migrate-objetivo.py objetivo.yaml --to-v2 --dry-run
    python scripts/migrate-objetivo.py objetivo.yaml --to-v2 --backup
"""

import yaml
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ObjetivoMigrator:
    """Migra objetivo.yaml v1.0 → v2.0"""

    def migrate_v1_to_v2(self, v1_file: Path) -> Dict[str, Any]:
        """Converte estrutura v1.0 para v2.0"""

        with open(v1_file) as f:
            v1_data = yaml.safe_load(f)

        # Detectar versão
        if not self._is_v1(v1_data):
            raise ValueError(f"{v1_file} não parece ser v1.0")

        # Mapear campos
        v2_data = {
            "version": "2.0",
            "project": self._map_project(v1_data),
            "express": self._map_express(v1_data),
            "detail": self._map_detail(v1_data),
            "constrain": self._map_constrain(v1_data)
        }

        # Gerar Markdown body
        markdown_body = self._generate_markdown_body(v1_data, v2_data)

        return {
            "frontmatter": v2_data,
            "markdown": markdown_body,
            "migration_report": self._generate_report(v1_data, v2_data)
        }

    def _is_v1(self, data: Dict) -> bool:
        """Detecta se é v1.0 (não tem campo version, tem prompt.role)"""
        return (
            "version" not in data and
            "prompt" in data and
            "role" in data.get("prompt", {})
        )

    def _map_project(self, v1: Dict) -> Dict:
        """Mapeia project metadata"""
        spec = v1.get("prompt", {}).get("content", {}).get("specification", [])

        # Extrair project_name (primeiro item de specification)
        project_name = "unknown-project"
        if spec and isinstance(spec[0], dict):
            project_name = spec[0].get("project_name", "unknown-project")

        # Inferir type baseado em description
        description = v1.get("prompt", {}).get("content", {}).get("description", "")
        project_type = self._infer_type_from_description(description)

        return {
            "name": project_name,
            "type": project_type,
            "metadata": {
                "created_at": datetime.utcnow().isoformat() + "Z",
                "migrated_from": "v1.0",
                "migration_date": datetime.utcnow().isoformat() + "Z"
            }
        }

    def _map_express(self, v1: Dict) -> Dict:
        """Mapeia seção Express"""
        content = v1.get("prompt", {}).get("content", {})

        description = content.get("description", "")
        what, why = self._split_description_to_what_why(description)

        # Extrair "who" de profiles (se existir)
        profiles = content.get("profile", [])
        who = [p.get("description", "") for p in profiles if p.get("description")]

        if not who:
            who = ["Usuários não especificados (favor preencher)"]

        return {
            "what": what,
            "why": why,
            "who": who
        }

    def _map_detail(self, v1: Dict) -> Dict:
        """Mapeia seção Detail"""
        spec = v1.get("prompt", {}).get("content", {}).get("specification", [])

        # Extrair tech stack
        how = {}
        for item in spec:
            if isinstance(item, dict):
                if "response" in item:
                    # Exemplo: "código python, com conexão em PostgreSQL..."
                    response = item["response"].lower()
                    if "python" in response:
                        how["language"] = "Python"
                    if "fastapi" in response:
                        how["framework"] = "FastAPI"
                    if "postgresql" in response:
                        how["database"] = "PostgreSQL"

        # Extrair constraints
        constraints = []
        if "infrastructure" in v1.get("prompt", {}).get("content", {}):
            constraints.append({
                "type": "integration",
                "value": "Dependências de infraestrutura (ver v1.0)",
                "description": "Migrado automaticamente — revisar manualmente"
            })

        # Extrair success_criteria de expected_outcome
        expected = v1.get("prompt", {}).get("content", {}).get("expected_outcome", [])
        success_criteria = []
        for item in expected:
            if isinstance(item, dict):
                for key, value in item.items():
                    success_criteria.append({
                        "metric": key.replace("_", " ").title(),
                        "target": value[:100] if isinstance(value, str) else str(value),
                        "measurement": "Especificar método de medição"
                    })

        return {
            "how": how if how else None,
            "constraints": constraints if constraints else None,
            "success_criteria": success_criteria if success_criteria else None
        }

    def _map_constrain(self, v1: Dict) -> Dict | None:
        """Mapeia seção Constrain (apenas se houver dados avançados)"""
        # v1.0 não tinha bounded_contexts ou ADRs
        return None

    def _generate_markdown_body(self, v1: Dict, v2: Dict) -> str:
        """Gera corpo Markdown a partir de v1 e v2"""
        md = f"""# 🎯 Objetivo: {v2['project']['name']}

> **ATENÇÃO**: Este arquivo foi migrado automaticamente de v1.0 → v2.0.
> Revise todas as seções e preencha campos faltantes.

---

## 1️⃣ O que este projeto faz?

{v2['express']['what']}

---

## 2️⃣ Por que este projeto existe?

{v2['express']['why']}

---

## 3️⃣ Quem vai usar?

"""
        for persona in v2['express']['who']:
            md += f"- {persona}\n"

        md += "\n---\n\n## 4️⃣ Como será implementado?\n\n"

        if v2['detail'] and v2['detail'].get('how'):
            how = v2['detail']['how']
            md += f"""### Stack técnico

| Camada | Tecnologia |
|--------|-----------|
| **Linguagem** | {how.get('language', 'Não especificado')} |
| **Framework** | {how.get('framework', 'Não especificado')} |
| **Database** | {how.get('database', 'Não especificado')} |

"""

        md += f"""
---

## 🚀 Próximos Passos

1. Revisar este arquivo e preencher campos `[PREENCHER]`
2. Validar: `scaffold.py validate objetivo.yaml`
3. Gerar spec: `scaffold.py process objetivo.yaml`

---

**Versão**: 2.0 (migrado de v1.0) | **Data**: {datetime.utcnow().strftime('%Y-%m-%d')}
"""

        return md

    def _generate_report(self, v1: Dict, v2: Dict) -> str:
        """Gera relatório de migração"""
        report = f"""# Relatório de Migração — objetivo.yaml v1.0 → v2.0

**Data**: {datetime.utcnow().isoformat()}

## Mapeamentos Realizados

### ✅ Campos Migrados com Sucesso

| Campo v1.0 | Campo v2.0 | Status |
|------------|------------|--------|
| `prompt.content.description` | `express.what` + `express.why` | ✅ Migrado |
| `prompt.content.specification[].project_name` | `project.name` | ✅ Migrado |
| `prompt.content.specification[].response` | `detail.how` | ⚠️ Parcial |
| `prompt.content.expected_outcome` | `detail.success_criteria` | ✅ Migrado |
| `prompt.content.profile` | `express.who` | ⚠️ Parcial |

### ⚠️ Campos Requerem Revisão Manual

1. **`detail.how`**: Inferido automaticamente — confirmar linguagem/framework
2. **`express.why`**: Extraído de `description` — expandir com problema/impacto
3. **`express.who`**: Mapeado de `profile.description` — adicionar personas reais
4. **`detail.constraints`**: Não existia em v1.0 — preencher manualmente
5. **`detail.dependencies`**: Não existia em v1.0 — preencher manualmente

### ❌ Campos Removidos (não mapeáveis)

| Campo v1.0 | Motivo |
|------------|--------|
| `prompt.role` | Metadado interno, não relevante para v2.0 |
| `prompt.content.workflow-objetivo` | Documentação interna, movida para docs/ |
| `features_to_implement` | Agora gerado em `objetivo-spec.yaml` (separado) |
| `pending_tasks` | Agora gerado em `objetivo-spec.yaml` (separado) |

## Ações Requeridas

- [ ] Revisar `express.what` e `express.why` (expandir se necessário)
- [ ] Preencher `express.who` com personas reais (não apenas roles)
- [ ] Validar `detail.how` (tech stack correto?)
- [ ] Adicionar `detail.constraints` (deadline, compliance, etc.)
- [ ] Adicionar `detail.dependencies` (serviços, times, APIs)
- [ ] Rodar `scaffold.py validate objetivo.yaml` para verificar schema
- [ ] Gerar novo `objetivo-spec.yaml` com `scaffold.py process objetivo.yaml`

## Referências

- [Guia de Migração](docs/objetivo-guide/v2.0/migration-from-v1.md)
- [Schema v2.0](https://schema.enterprise-template.io/objetivo-v2.json)
- [Exemplos](docs/examples/objetivo-templates/)
"""
        return report

    # Métodos auxiliares

    def _infer_type_from_description(self, description: str) -> str:
        """Infere project.type baseado em keywords na descrição"""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["api", "rest", "backend", "fastapi", "flask"]):
            return "backend-api"
        elif any(kw in desc_lower for kw in ["frontend", "react", "next", "vue", "angular"]):
            return "frontend-web"
        elif any(kw in desc_lower for kw in ["terraform", "ansible", "k8s", "helm"]):
            return "infrastructure"
        elif any(kw in desc_lower for kw in ["etl", "pipeline", "airflow", "dbt"]):
            return "data-pipeline"
        elif any(kw in desc_lower for kw in ["ml", "machine learning", "model", "training"]):
            return "ml-training"
        else:
            return "backend-api"  # Default seguro

    def _split_description_to_what_why(self, description: str) -> tuple[str, str]:
        """Tenta split description em what (o quê) e why (por quê)"""

        # Heurística: se tem "para" ou "resolve", split ali
        if " para " in description.lower():
            parts = description.split(" para ", 1)
            what = parts[0].strip()
            why = "Para " + parts[1].strip() if len(parts) > 1 else "[PREENCHER: Por que este projeto existe?]"
        elif " que resolve " in description.lower():
            parts = description.split(" que resolve ", 1)
            what = parts[0].strip()
            why = "Resolve " + parts[1].strip() if len(parts) > 1 else "[PREENCHER: Por que este projeto existe?]"
        else:
            # Fallback: primeira frase é what, resto é why
            sentences = description.split(". ")
            what = sentences[0].strip()
            why = ". ".join(sentences[1:]).strip() if len(sentences) > 1 else "[PREENCHER: Por que este projeto existe?]"

        return what, why

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Migra objetivo.yaml v1.0 → v2.0")
    parser.add_argument("file", type=Path, help="Arquivo objetivo.yaml v1.0")
    parser.add_argument("--to-v2", action="store_true", required=True, help="Migrar para v2.0")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar output sem salvar")
    parser.add_argument("--backup", action="store_true", help="Criar backup antes de sobrescrever")
    parser.add_argument("--output", type=Path, help="Arquivo de saída (padrão: mesmo arquivo)")

    args = parser.parse_args()

    migrator = ObjetivoMigrator()

    # Migrar
    logger.info(f"Migrando {args.file} (v1.0 → v2.0)...")
    result = migrator.migrate_v1_to_v2(args.file)

    # Gerar arquivo v2.0 (Markdown + YAML frontmatter)
    output_content = "---\n"
    output_content += yaml.dump(result["frontmatter"], sort_keys=False, allow_unicode=True)
    output_content += "---\n\n"
    output_content += result["markdown"]

    # Dry-run
    if args.dry_run:
        print("\n" + "="*80)
        print("DRY-RUN OUTPUT (não salvo):")
        print("="*80 + "\n")
        print(output_content)
        print("\n" + "="*80)
        print("MIGRATION REPORT:")
        print("="*80 + "\n")
        print(result["migration_report"])
        return

    # Backup
    output_file = args.output or args.file
    if args.backup and output_file.exists():
        backup_file = output_file.with_suffix(output_file.suffix + ".v1.backup")
        import shutil
        shutil.copy2(output_file, backup_file)
        logger.info(f"✅ Backup criado: {backup_file}")

    # Salvar
    with open(output_file, 'w') as f:
        f.write(output_content)
    logger.info(f"✅ Arquivo migrado salvo: {output_file}")

    # Salvar relatório
    report_file = output_file.parent / f"{output_file.stem}-migration-report.md"
    with open(report_file, 'w') as f:
        f.write(result["migration_report"])
    logger.info(f"✅ Relatório de migração salvo: {report_file}")

    print("\n" + "="*80)
    print("✅ MIGRAÇÃO CONCLUÍDA")
    print("="*80)
    print(f"\nPróximos passos:")
    print(f"  1. Revisar {output_file} e preencher campos [PREENCHER]")
    print(f"  2. Validar: scaffold.py validate {output_file}")
    print(f"  3. Gerar spec: scaffold.py process {output_file}")
    print(f"\nVer relatório completo: {report_file}")

if __name__ == "__main__":
    main()
```

---

# 7. PLANO DE IMPLEMENTAÇÃO

## 7.1. Checklist Técnico

### Fase 1 — Foundation (2 semanas, 80 horas)

**Sprint 1.1 — Parser e Validação (5 dias, 40h)**

- [ ] **IMP-101**: Implementar parser Markdown + YAML frontmatter
  - Biblioteca: `python-frontmatter` ou custom parser
  - Input: `objetivo.yaml` (Markdown híbrido)
  - Output: `(frontmatter: dict, markdown: str)`
  - Testes: 15 casos de teste (válidos + inválidos)
  - **Responsável**: Backend Engineer
  - **Estimativa**: 12h

- [ ] **IMP-102**: Criar JSON Schema completo v2.0
  - Arquivo: `schemas/objetivo-v2-schema.json`
  - Validação: `ajv` (CLI) + `jsonschema` (Python)
  - Testes: 20 casos de teste (todos os campos)
  - **Responsável**: Platform Engineer
  - **Estimativa**: 8h

- [ ] **IMP-103**: Implementar validadores Pydantic
  - Arquivo: `lib/schemas/objetivo_v2.py`
  - Classes: `ObjetivoV2`, `ExpressSection`, `DetailSection`, `ConstrainSection`
  - Validadores customizados: 8 validações (cross-field, business rules)
  - Testes: `test_objetivo_schema.py` (30 casos)
  - **Responsável**: Backend Engineer
  - **Estimativa**: 16h

- [ ] **IMP-104**: CLI de validação (4 camadas)
  - Comando: `scaffold.py validate objetivo.yaml --level [syntax|schema|semantics|business]`
  - Output: JSON (para CI/CD) ou human-readable (para terminal)
  - Testes: E2E (5 cenários)
  - **Responsável**: DevOps Engineer
  - **Estimativa**: 4h

**Sprint 1.2 — Processor e Two-File Architecture (5 dias, 40h)**

- [ ] **IMP-105**: Implementar `TwoFileProcessor`
  - Arquivo: `lib/processors/two_file_processor.py`
  - Método: `process(input_file, output_file, separate_spec=False)`
  - Hash tracking: SHA256 de input (idempotência)
  - State machine: `.specify/state.json`
  - Testes: 12 casos (single-file, two-file, regeneration)
  - **Responsável**: Principal Engineer
  - **Estimativa**: 20h

- [ ] **IMP-106**: Integração com Copilot (geração de spec)
  - Stub: `generate_spec_with_copilot(objetivo: ObjetivoV2) -> ObjetivoSpec`
  - Placeholder: Gerar spec determinístico (sem IA ainda)
  - Testes: Snapshot tests (5 exemplos)
  - **Responsável**: AI Integration Engineer
  - **Estimativa**: 12h

- [ ] **IMP-107**: CLI `scaffold.py process`
  - Comandos:
    - `scaffold.py process objetivo.yaml` (single-file)
    - `scaffold.py process objetivo.yaml --separate-spec` (two-file)
    - `scaffold.py process objetivo.yaml --dry-run` (preview)
  - Testes: E2E (8 cenários)
  - **Responsável**: DevOps Engineer
  - **Estimativa**: 8h

### Fase 2 — Migration (1 semana, 40 horas)

**Sprint 2.1 — Migration Script (3 dias, 24h)**

- [ ] **IMP-201**: Implementar `ObjetivoMigrator` (v1.0 → v2.0)
  - Arquivo: `scripts/migrate-objetivo.py`
  - Métodos:
    - `migrate_v1_to_v2(v1_file) -> (frontmatter, markdown, report)`
    - `_map_project(v1) -> ProjectMetadata`
    - `_map_express(v1) -> ExpressSection`
    - `_map_detail(v1) -> DetailSection`
  - Testes: 8 casos (projetos reais v1.0)
  - **Responsável**: Backend Engineer
  - **Estimativa**: 16h

- [ ] **IMP-202**: Backward compatibility layer (6 meses)
  - Detector de versão: `detect_objetivo_version(file_path) -> "1.0" | "2.0"`
  - Wrapper: `scaffold.py` processa v1.0 via auto-migration
  - Warnings: Emitir deprecation warning se v1.0 detectado
  - Testes: 6 casos (v1.0 deve funcionar sem erros)
  - **Responsável**: Platform Engineer
  - **Estimativa**: 8h

**Sprint 2.2 — Documentation (2 dias, 16h)**

- [ ] **IMP-203**: Documentação de breaking changes
  - Arquivo: `docs/objetivo-guide/v2.0/BREAKING_CHANGES.md`
  - Seções: Campos removidos, campos renomeados, novos campos obrigatórios
  - Tabela de migração: v1.0 → v2.0 (campo por campo)
  - **Responsável**: Technical Writer
  - **Estimativa**: 6h

- [ ] **IMP-204**: Guia de migração
  - Arquivo: `docs/objetivo-guide/v2.0/migration-from-v1.md`
  - Seções:
    - Passo a passo (manual)
    - Script automático (`migrate-objetivo.py`)
    - FAQ (10 perguntas comuns)
  - **Responsável**: Technical Writer
  - **Estimativa**: 8h

- [ ] **IMP-205**: Deprecation timeline
  - Arquivo: `docs/objetivo-guide/DEPRECATION_TIMELINE.md`
  - Fases: Dual support (6 meses) → v1.0 removal
  - Datas: 2026-05-15 (v2.0 release) → 2026-11-15 (v1.0 EOL)
  - **Responsável**: Product Manager
  - **Estimativa**: 2h

### Fase 3 — Integration (2 semanas, 80 horas)

**Sprint 3.1 — scaffold.py Integration (5 dias, 40h)**

- [ ] **IMP-301**: Atualizar `scaffold.py` para suportar v2.0
  - Função: `scaffold_from_objetivo_v2(objetivo: ObjetivoV2)`
  - Workflow:
    1. Parse objetivo.yaml
    2. Validate (4 layers)
    3. Generate objetivo-spec.yaml (se --separate-spec)
    4. Apply profiles
    5. Generate files
  - Testes: E2E (3 projetos completos)
  - **Responsável**: Principal Engineer + Backend Engineer
  - **Estimativa**: 24h

- [ ] **IMP-302**: Integração com SpecKit agents
  - Agents: `constitution`, `clarify`, `specify`, `plan`, `tasks`
  - Input: `objetivo-spec.yaml` (em vez de `objetivo.yaml` antigo)
  - Testes: Integration tests (1 projeto por agent)
  - **Responsável**: AI Integration Engineer
  - **Estimativa**: 16h

**Sprint 3.2 — Profile Descriptors Update (3 dias, 24h)**

- [ ] **IMP-303**: Atualizar 22 profile descriptors
  - Adicionar compatibilidade com `detail.how` (language, framework, database)
  - Validar que todos os perfis funcionam com v2.0
  - Testes: Snapshot tests (22 perfis × 1 exemplo = 22 testes)
  - **Responsável**: Platform Engineer
  - **Estimativa**: 16h

- [ ] **IMP-304**: Criar templates prontos (8 casos de uso)
  - Diretório: `docs/examples/objetivo-templates/`
  - Templates:
    1. `01-simple-python-api/objetivo.yaml`
    2. `02-simple-typescript-next/objetivo.yaml`
    3. `03-medium-k8s-helm/objetivo.yaml`
    4. `04-medium-terraform-aws/objetivo.yaml`
    5. `05-complex-migration/objetivo.yaml`
    6. `06-complex-monorepo/objetivo.yaml`
    7. `07-data-pipeline-dbt/objetivo.yaml`
    8. `08-ml-training/objetivo.yaml`
  - **Responsável**: Technical Writer + Domain Experts
  - **Estimativa**: 8h (1h por template)

**Sprint 3.3 — Tests End-to-End (2 dias, 16h)**

- [ ] **IMP-305**: Testes E2E (3 casos de uso completos)
  - Caso 1: Simple Python API (iniciante, wizard)
  - Caso 2: Medium K8s Helm (intermediário, semi-automático)
  - Caso 3: Complex Chatwoot Migration (avançado, two-file mode)
  - Validar: Projeto gerado compila/roda/passa testes
  - **Responsável**: QA Engineer
  - **Estimativa**: 16h

### Fase 4 — Rollout (1 semana, 40 horas)

**Sprint 4.1 — Documentação de Usuário Final (3 dias, 24h)**

- [ ] **IMP-401**: Getting Started Guide
  - Arquivo: `docs/objetivo-guide/v2.0/getting-started.md`
  - Seções:
    - Quickstart (5 min)
    - Wizard guiado (10 min)
    - Primeiro projeto (15 min)
  - Testes: 5 usuários beta testam guia
  - **Responsável**: Technical Writer
  - **Estimativa**: 12h

- [ ] **IMP-402**: Reference Documentation
  - Arquivo: `docs/objetivo-guide/v2.0/reference.md`
  - Seções:
    - Todos os campos (express, detail, constrain)
    - Tipos e validações
    - Exemplos inline
  - **Responsável**: Technical Writer
  - **Estimativa**: 8h

- [ ] **IMP-403**: Advanced Features Guide
  - Arquivo: `docs/objetivo-guide/v2.0/advanced-features.md`
  - Seções:
    - Two-file mode
    - Bounded contexts (DDD)
    - ADRs
    - Extensions (plugins)
  - **Responsável**: Technical Writer
  - **Estimativa**: 4h

**Sprint 4.2 — Tutorials e Rollout (2 dias, 16h)**

- [ ] **IMP-404**: Tutorial em vídeo (3 níveis)
  - Vídeo 1: Iniciante (5 min) — Wizard guiado
  - Vídeo 2: Intermediário (10 min) — Edição manual
  - Vídeo 3: Avançado (15 min) — Two-file mode + customização
  - Publicar: YouTube + docs/
  - **Responsável**: DevRel + Video Producer
  - **Estimativa**: 8h

- [ ] **IMP-405**: Rollout e comunicação
  - Blog post: "Announcing objetivo.yaml v2.0"
  - Email: Todos os usuários ativos (300+)
  - Slack: Announcement em #general
  - Webinar: Live demo + Q&A (1 hora)
  - **Responsável**: Product Manager + DevRel
  - **Estimativa**: 8h

---

## 7.2. Estimativa de Esforço

| Fase | Duração | Horas | FTEs | Responsáveis |
|------|---------|-------|------|--------------|
| **Fase 1 — Foundation** | 2 semanas | 80h | 2 FTE | Backend Eng, Platform Eng, DevOps |
| **Fase 2 — Migration** | 1 semana | 40h | 1 FTE | Backend Eng, Tech Writer |
| **Fase 3 — Integration** | 2 semanas | 80h | 2 FTE | Principal Eng, AI Eng, QA |
| **Fase 4 — Rollout** | 1 semana | 40h | 1 FTE | Tech Writer, PM, DevRel |
| **TOTAL** | **6 semanas** | **240h** | **2-3 FTE** | — |

**Custo estimado** (assumindo R$ 200/hora):
- **Total**: 240h × R$ 200 = **R$ 48.000**
- **Payback**: 2.8 meses (economia de R$ 17.200/mês em suporte + produtividade)

---

## 7.3. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Usuários não migram** | Média (40%) | Alto | Backward compatibility por 6 meses + migration script automático |
| **Bugs em parser Markdown** | Alta (60%) | Médio | Testes extensivos (50+ casos) + fallback para YAML puro |
| **Integração com Copilot quebra** | Média (30%) | Alto | Stub determinístico primeiro, IA depois |
| **Documentação insuficiente** | Baixa (20%) | Médio | 3 níveis de docs + tutoriais em vídeo |
| **Timeline estoura** | Média (50%) | Médio | Buffer de 1 semana (6→7 semanas total) |

---

## 7.4. Definition of Done

Uma implementação está **concluída** quando:

- [ ] Código implementado com >80% test coverage
- [ ] Testes E2E passam (3 casos de uso completos)
- [ ] Documentação escrita e revisada
- [ ] Code review aprovado por 2 reviewers
- [ ] Deploy em staging testado por 5 usuários beta
- [ ] Breaking changes documentados em CHANGELOG.md
- [ ] Migration script testado em 10 projetos reais v1.0
- [ ] Performance validada (geração de projeto <3 min)

---

# CONCLUSÃO

## Proposta Vencedora: Two-File Progressive Architecture

Após 6 horas de debate, os 5 especialistas chegaram a **consenso unânime** sobre o novo formato de `objetivo.yaml`:

### Formato Final

**Markdown híbrido** (YAML frontmatter + Markdown body) com **separação opcional input/output**:

```markdown
---
# YAML frontmatter (estruturado, validável por JSON Schema)
version: "2.0"
project:
  name: "user-api"
  type: "backend-api"
express:
  what: "API REST para gerenciar usuários"
  why: "Centralizar autenticação de 5 sistemas legados"
  who: ["DevOps", "Admins", "Developers"]
---

# Markdown body (narrativo, human-friendly, com emojis e formatação rica)
## 🎯 O que este projeto faz?

[Narrativa expandida com exemplos, diagramas, casos de uso...]
```

### Benefícios Principais

1. **Acessibilidade para iniciantes**: Markdown é familiar (↓75% em tempo de setup)
2. **Validação forte**: YAML frontmatter validado por JSON Schema
3. **Progressive disclosure**: 3 níveis (express → detail → constrain)
4. **Separação de concerns**: Input (editável) vs Output (gerado)
5. **Backward compatibility**: Suporte v1.0 por 6 meses + migration script

### Impacto Esperado

- **Adoção**: 45% → 80% (↑77%)
- **NPS**: 32 → >70 (↑119%)
- **Setup time**: 47 min → 10 min (↓79%)
- **Suporte**: R$ 8.800/mês → R$ 3.600/mês (↓59%)

### Próximos Passos Imediatos

1. ✅ **Aprovar proposta** (stakeholders + arquitetura)
2. 📋 **Criar épicos** no backlog (6 semanas, 240 horas)
3. 🚀 **Iniciar Fase 1** (Foundation — parsers e validação)
4. 📹 **Gravar demo** (5 min) para comunicação interna

---

**Documento gerado em**: 2026-04-27
**Total de linhas**: ~4.500 linhas
**Participantes**: Sarah Chen, Marcus Silva, Elena Rodriguez, Dr. James Wei, Priya Sharma
**Moderador**: Template Architect Agent
