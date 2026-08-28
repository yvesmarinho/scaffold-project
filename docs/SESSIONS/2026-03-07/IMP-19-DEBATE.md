# IMP-19 — Debate: Estado do Template e Roadmap de Evolução

**Data**: 2026-03-07
**Tipo**: Debate Multi-Perspectiva (Template Architect Agent)
**Referência**: `docs/GitHub Copilot - Default Porject Template Skills.md`
**Sessão**: `docs/SESSIONS/2026-03-07/`

---

## 📋 Contexto e Motivação

O documento-fonte analisado (`GitHub Copilot - Scaffold Project Template Skills.md`) descreve os **6 perfis profissionais** necessários para evoluir um template agnóstico com capacidade de instanciação focada por domínio/linguagem/plataforma.

Este debate avalia o **estado atual do projeto** (`scaffold-project`) contra esse mapa de skills, identifica gaps e propõe o próximo ciclo de evolução.

---

## 🗺️ Estado Atual — Inventário por Dimensão

### Dimensão 1: Core/Motor (Template Architect)

| Artefato | Status | Observação |
|----------|--------|------------|
| `scripts/scaffold.py` | ✅ | Entry point interativo — absoveu os 3 scripts shell |
| `scripts/lib/` (7 módulos) | ✅ | Arquitetura modular: config, ui, project, links, git, templates, vscode |
| `scripts/lib/templates.py` | ✅ | `generate_copilot_instructions()`, `generate_copilot_rules()`, etc. |
| `scripts/lib/config.py` | ✅ | Domínios, linguagens, SPECKIT_SYNC_DATE |
| Composição de perfis | ❌ | Seleção singular — não combina múltiplos perfis |
| Contrato formal (profile-descriptor) | ❌ | Não existe schema/contrato de perfil |
| Modo `--dry-run` | ❌ | Não implementado |
| Modo `--json` / `--non-interactive` | ❌ | Não implementado |
| Snapshot/fixture tests do gerador | ❌ | IMP-16 aberto há 2 sprints |

**Score**: 4/10 — Core existe e funciona, mas ainda é modo "copiar + substituir" sem composição.

---

### Dimensão 2: DevEx / CLI UX

| Feature | Status | Observação |
|---------|--------|------------|
| CLI interativo (prompts) | ✅ | `scripts/lib/ui.py` com `inquirer`/`prompt_toolkit` |
| Mensagens de erro claras | ⚠️ | Básico — sem contexto acionável |
| Modo `--dry-run` | ❌ | Não implementado |
| Modo `--explain` | ❌ | Não implementado |
| Modo `--json` (automação) | ❌ | Não implementado |
| Modo non-interactive (CI) | ❌ | Não implementado |
| `--list-profiles` | ❌ | Não implementado |
| Documentação "primeiros 10 min" | ⚠️ | README genérico, sem guia por perfil |
| Tempo até "projeto compilando" | ⚠️ | Não medido — estimativa: 8-15 min |

**Score**: 3/10 — O modo interativo existe mas falta toda a camada de automação/CI e ergonomia avançada.

---

### Dimensão 3: SRE / Infra Baseline

| Artefato | Status | Observação |
|----------|--------|------------|
| `.editorconfig` gerado | ✅ | Incluído nos templates |
| `.gitignore` por domínio | ✅ | Gerado por domínio + linguagem |
| `Makefile` com targets padrão | ✅ | Com `help`, `dev`, `test`, `lint`, `build`, `clean` |
| CI/CD mínimo (GitHub Actions) | ⚠️ | IMP-15 aberto (Dockerfile, docker-compose, workflows) |
| Runbook template | ❌ | Não gerado pelo scaffold |
| Observabilidade stub | ❌ | Não presente nos templates |
| Estrutura dev/staging/prod | ❌ | Não contemplada |

**Score**: 5/10 — Baseline parcial; CI/CD e observabilidade são gaps críticos.

---

### Dimensão 4: AppSec / Security

| Feature | Status | Observação |
|---------|--------|------------|
| `devops-security.prompt.md` | ✅ | Criado em IMP-14 |
| `.copilot-rules.md` com sec rules | ✅ | Regras de segurança nas 7 seções |
| Secret scanning (gitleaks) | ❌ | Não configurado nos projetos gerados |
| SAST nos projetos gerados | ❌ | Não configurado |
| Dependabot / Renovate config | ❌ | Não gerado pelo scaffold |
| SBOM (Software Bill of Materials) | ❌ | Não implementado |
| Hardening de containers | ❌ | Dockerfile não gerado ainda (IMP-15) |
| Threat model lite | ❌ | Não contemplado |

**Score**: 3/10 — O perfil de segurança existe para *guiar o Copilot*, mas os projetos gerados não têm tooling de segurança embutido.

---

### Dimensão 5: Domain Profiles

| Perfil | Tipo | Status |
|--------|------|--------|
| `devops-programming` | Layer 1 — domínio | ✅ |
| `devops-infrastructure` | Layer 1 — domínio | ✅ |
| `devops-analysis` | Layer 1 — domínio | ✅ |
| `devops-security` | Layer 1 — domínio | ✅ |
| `python-fastapi` | Layer 2 — linguagem/framework | ❌ |
| `python-django` | Layer 2 — linguagem/framework | ❌ |
| `python-flask` | Layer 2 — linguagem/framework | ❌ |
| `typescript-next` | Layer 2 — linguagem/framework | ❌ |
| `go-chi` | Layer 2 — linguagem/framework | ❌ |
| `rust-axum` | Layer 2 — linguagem/framework | ❌ |
| `k8s-helm` | Layer 3 — plataforma | ❌ |
| `terraform-aws` | Layer 3 — plataforma | ❌ |
| `data-pipeline` | Layer 3 — especialidade | ❌ |
| `mlops-serving` | Layer 3 — especialidade | ❌ |
| `lgpd-baseline` | Layer 4 — compliance | ❌ |
| Composição de perfis | Motor | ❌ |
| SpecKit integrado | Ferramenta | ✅ |
| Profile descriptor (contrato) | Motor | ❌ |

**Score**: 3/10 — Layer 1 completo. Layers 2, 3, 4 e o motor de composição estão ausentes.

---

### Dimensão 6: Governança / Release

| Feature | Status | Observação |
|---------|--------|------------|
| Versionamento semântico do template | ❌ | Não existe |
| Matriz de compatibilidade de perfis | ❌ | Não existe (necessário ao escalar) |
| Changelog estruturado | ⚠️ | Implícito no `docs/TODO.md` mas não formal |
| Política de depreciação | ❌ | Não definida |
| Snapshot/fixture tests | ❌ | IMP-16 aberto |
| Estratégia de migração | ❌ | Não definida |
| Documentação gerada por perfil | ⚠️ | Genérica — não específica por perfil ativo |

**Score**: 1/10 — O maior gap estratégico. Sem governança, o template não escala.

---

## 🔬 Respostas às 4 Perguntas Fundamentais

> (Do documento-fonte: questões que orientam "quem contratar/consultar primeiro")

### 1. Motor: "copiar pasta e substituir variáveis" ou "operações declarativas com composição"?

**Resposta atual**: Principalmente "copiar + substituir". O `scaffold.py` aplica lógica condicional por domínio/linguagem, mas ainda não tem um sistema de perfis compostos. Cada decisão está hardcoded nos módulos `templates.py` e `project.py`.

**Caminho necessário**: Migrar para um modelo de **profile-descriptor declarativo** onde cada perfil define o que gera, o que patcha e com quem é compatível. O motor lê os descriptors e compõe deterministicamente.

### 2. Suporte: "só criação inicial" ou "re-aplicar perfil" (upgrade/migração)?

**Resposta atual**: Apenas criação inicial. Não existe `scaffold.py upgrade` ou `scaffold.py add-profile`.

**Caminho necessário**: Arquitetura idempotente com **drift detection** — o motor sabe o que já existe e aplica apenas o delta. Essencial para a longevidade do template.

### 3. Quais são os "não-negociáveis" do core?

**Identificados no projeto atual**:
- `.editorconfig`
- `.gitignore` (por domínio)
- `Makefile` com targets padrão
- `README.md` com estrutura
- `.copilot-rules-[projeto].md`
- `.github/copilot-instructions.md`
- `docs/` estrutura base
- SpecKit (`.specify/`)
- Pasta de sessão `docs/SESSIONS/`

**Faltando no core** (deveria ser gerado sempre):
- CI/CD skeleton (GitHub Actions mínimo)
- Runbook template
- Secret scanning config
- `CHANGELOG.md` inicial

### 4. Qual é o público primário?

**Análise do projeto**: O template atualmente favore **DevOps/Programador Pleno-Senior** que trabalha com Python, usa VS Code + GitHub Copilot, e tem familiaridade com make/git/docker.

**Lacuna**: Não serve bem para:
- Analistas de dados (sem Layer 3 de dados)
- SREs/Infra-focados (Layer 3 de plataforma ausente)
- Times com compliance (Layer 4 ausente)
- Desenvolvedores Go/Typescript/Rust (Layer 2 ausente)

---

## 🗣️ Debate Multi-Perspectiva

---

### 🔵 Proposta A: Implementar Motor de Composição de Perfis (Profile Composer)

#### 🏛️ Perspectiva 1 — Arquitetura/Core

**A favor**: É o salto mais impactante do roadmap. Sem composição, cada perfil novo tem risco de poluir o core. Com o contrato `profile-descriptor.yaml`, o core permanece agnóstico: ele apenas orquestra, nunca decide.

**Risco**: Complexidade de implementação elevada. O motor precisa lidar com:
- Conflitos entre perfis (ex: `python-fastapi` + `go-chi`)
- Ordem de aplicação dos patches
- Rollback em caso de erro parcial

**Restrição**: O core atual (`scaffold.py`) não foi projetado para composição — será necessária uma refatoração significativa com risco de regressão.

**Proposta**: Fazer em 2 fases — primeiro o contrato (schema YAML) sem o motor, depois migrar um perfil existente como prova de conceito.

#### 🖥️ Perspectiva 2 — DevEx/UX

**A favor**: Para o usuário, composição significa `scaffold.py create --profile python-fastapi --with k8s-helm --with lgpd` — UX muito mais expressiva que o fluxo interativo atual.

**Risco**: A UX de composição é complexa. Quantas combinações são válidas? Como mostrar conflitos ao usuário de forma clara? O `--list-profiles` precisa existir antes da composição para o usuário saber o que combinar.

**Proposta**: Entregar primeiro o `--list-profiles` e `--dry-run` para validar UX com os perfis existentes antes de implementar composição.

#### 🔒 Perspectiva 3 — Segurança

**A favor**: Com profile descriptors, o perfil de segurança (`lgpd-baseline`, `soc2-baseline`) pode ser declarado como **obrigatório** para certos perfis de plataforma (ex: `terraform-aws` implica `lgpd-baseline` se região BR).

**Risco**: Perfis compostos podem criar configurações de segurança contraditórias (ex: dois perfis de IAM diferentes).

**Proposta**: Ao definir o contrato de perfil, incluir campo `security.enforces` e `security.conflicts_with` desde o início.

#### 📦 Perspectiva 4 — Governança

**Alerta crítico**: Composição sem governança é a receita para o caos. Antes de lançar composição de perfis para o "público", é preciso ter:
1. Matriz de compatibilidade documentada
2. Testes automáticos de todas as combinações válidas
3. Política de versionamento por perfil (um perfil pode ter sua própria versão)

**Proposta**: Implementar governance tooling paralelo ao compositor.

#### ✅ Consenso — Proposta A
- Composição é o norte estratégico correto
- Ordem de implementação matters: **contrato antes de motor**
- **Não lançar composição sem testes de combinações**
- Entregar DevEx mínimo (`--dry-run`, `--list-profiles`) antes do motor completo

#### 💡 Próximos Passos — Proposta A
1. Definir e documentar `profile-descriptor.yaml` schema (sem implementar o motor)
2. Implementar `--list-profiles` e `--dry-run` no `scaffold.py` existente
3. Migrar perfil `devops-programming` como prova de conceito do descriptor

---

### 🟢 Proposta B: Layer 2 — Perfis de Linguagem/Framework

#### 🏛️ Perspectiva 1 — Arquitetura/Core

**A favor**: Perfis Layer 2 são a extensão mais natural do que já existe. O motor atual suporta "domínio + linguagem" — basta formalizar isso como perfis standalone.

**Risco baixo**: Não requer mudança no motor — apenas novos templates e lógica condicional em `templates.py`.

**Proposta**: Os 3 perfis Python têm cases distintos e não competem entre si — todos são válidos:

| Perfil | Paradigma | Caso de Uso Principal |
|--------|-----------|----------------------|
| `python-fastapi` | Async API-first | APIs REST/GraphQL modernas, alta performance, OpenAPI automático |
| `python-flask` | Microframework | Apps e APIs menores, prototipagem rápida, projetos com controle total da stack |
| `python-django` | Full-stack batteries-included | Apps com admin, ORM, autenticação, CMS |

**Convenção transversal a todos os perfis Python**: `uv` como gerenciador de ambiente e pacotes.
- `uv venv` (criar env) + `uv add` (adicionar dep) + `uv run` (executar, inclusive `uv run pytest`) + `uv sync` (sincronizar lock)
- Lock file `uv.lock` commitado ao repositório para reprodução determinista
- `pyproject.toml` (PEP 621) como fonte de verdade de dependências
- `requirements.txt` gerável via `uv export` quando necessário (ex: Dockerfile)

Prioridade de implementação: `python-fastapi` → `python-flask` (uso declarado pelo mantenedor) → `python-django`.

#### 🖥️ Perspectiva 2 — DevEx/UX

**A favor**: É o que mais impacta o tempo-até-rodar. Um perfil `python-fastapi` geraria estrutura pronta para rodar com `make dev` em < 3 minutos.

**Impacto do `uv`**: A adoção de `uv` reduz drasticamente o setup inicial:
- `uv sync` (+env +deps) ≈ 5s vs `pip install -r requirements.txt` ≈ 60-120s
- Zero decisão de "qual pip usar" — `uv` resolve Python version + deps + env em um comando
- `uv run pytest` / `uv run ruff` eliminam a necessidade de ativar env manualmente

**Proposta**: Quick Start de cada perfil Python deve ser exatamente:
```bash
git clone <repo> && cd <projeto>
uv sync          # cria .venv + instala deps
make dev         # ou: uv run uvicorn src.main:app --reload
```

#### 🔒 Perspectiva 3 — Segurança

**Alerta**: Perfis de linguagem são onde as vulnerabilidades mais entram. Cada framework Python tem vetor de ataque principal:

| Perfil | Vetores Específicos | Mitigação no Template |
|--------|--------------------|-----------------------|
| `python-fastapi` | Validação Pydantic bypassada, JWT sem expiração | `bandit`, `safety`, `python-jose` com expiração padrão |
| `python-flask` | SSTI (Jinja2), CSRF sem proteção, SQLAlchemy raw queries | `flask-wtf` (CSRF), `bandit`, `flask-talisman` (headers), proibir `text=` em queries |
| `python-django` | Mass assignment, querysets `__raw`, DEBUG=True em prod | `bandit`, `django-security` checklist, `DEBUG=False` forçado |

Regras **transversais** a todos os perfis Python:
- `bandit` no Makefile e CI (`uv run bandit -r src/`)
- `pip-audit` para scanning de dependências (`uv run pip-audit`)
- `.env.example` com documentação de variáveis (sem valores reais)
- Nenhum segredo hardcoded nos templates gerados
- `uv.lock` commitado: auditoria de supply chain viável (`uv export | pip-audit --stdin`)

#### 📦 Perspectiva 4 — Governança

**A favor**: Perfis Layer 2 são mais fáceis de versionar e depreçiar que o core. Podem ter ciclo de vida próprio.

**Proposta**: Cada perfil Layer 2 deve ter `VERSION` e `LAST_TESTED_DATE` no descriptor.

#### ✅ Consenso — Proposta B
- Layer 2 é implementável agora sem refatoração do motor
- **3 perfis Python são prioritários** (uso declarado pelo mantenedor): FastAPI → Flask → Django
- **`uv` é o gerenciador oficial** de todos os perfis Python: `uv sync`, `uv run`, `uv.lock` commitado
- Incluir security baseline específico por framework em todo perfil Layer 2
- Quick Start padronizado: `git clone` → `uv sync` → `make dev` (3 comandos)
- Definir "Layer 2 profile checklist" antes do 2º perfil para não divergir

#### 💡 Próximos Passos — Proposta B
1. Criar `python-fastapi` prompt + template files completos (IMP-20)
2. Criar `python-flask` prompt + template files (IMP-20b) — uso confirmado pelo mantenedor
3. Definir "Layer 2 profile checklist" para padronizar perfis seguintes
4. Criar `typescript-next` como primeiro perfil não-Python (IMP-21)

---

### 🔴 Proposta C: Governança e Template Tests (Prioridade Alta Ignorada)

#### 🏛️ Perspectiva 1 — Arquitetura/Core

**Alerta vermelho**: O template já tem 18+ tasks implementadas SEM nenhum teste de regressão. Toda mudança em `scaffold.py` é um risco de regressão silenciosa.

**Situação real**: Se qualquer módulo em `scripts/lib/` for modificado por qualquer futura task, não há como verificar se outra combinação de domínio/linguagem quebrou.

#### 🖥️ Perspectiva 2 — DevEx/UX

**Impacto no usuário**: Um template que gera arquivos com bug (ex: indentação errada, variável não substituída) é mais prejudicial que um template que não gera nada.

**Proposta**: Antes de criar novos perfis, garantir que os existentes são testados.

#### 🔒 Perspectiva 3 — Segurança

**Alerta**: Sem testes, uma mudança em `templates.py` pode acidentalmente gerar templates com secrets hardcoded ou configurações inseguras. Isso é **risco de supply chain**.

#### 📦 Perspectiva 4 — Governança

**Crítico**: IMP-16 (testes) está aberto **há 2 sprints inteiros** (desde 2026-03-01). Isso representa débito técnico crescente: cada nova feature sem cobertura aumenta o custo de testar depois.

**Proposta firme**:
- IMP-16 deve ser P0 nas próximas 3 tasks
- Mínimo: 1 smoke test por combinação domínio/linguagem
- Alvo: fixture test comparando output gerado vs. snapshot esperado

#### ✅ Consenso — Proposta C
- **Testes são bloqueadores para crescimento de perfis**
- IMP-16 deve ser executado ANTES de adicionar perfis Layer 2 novos
- Governança (versioning, changelog, matrix) deve começar junto com IMP-16

#### 💡 Próximos Passos — Proposta C
1. Implementar IMP-16: smoke tests (1 por combinação domínio/linguagem, total ~9 combos)
2. Adicionar snapshot tests para `python + programming` combo como baseline
3. Criar `TEMPLATE-VERSIONS.md` com matriz de compatibilidade inicial

---

## 🎯 Síntese — Ordem de Prioridade Consensual

```
P0 — BLOQUEADORES (deve resolver antes de crescer)
├── IMP-16: Testes do scaffold.py (smoke + snapshots)
└── IMP-19a: Profile-descriptor schema (contrato formal dos perfis)

P1 — ALTO IMPACTO (próximo sprint)
├── IMP-19b: scaffold.py --dry-run + --list-profiles
├── IMP-20:  Layer 2 — python-fastapi profile completo
├── IMP-20b: Layer 2 — python-flask profile (uso declarado pelo mantenedor)
├── IMP-21:  Layer 2 — typescript-next profile
└── IMP-15:  Dockerfile + docker-compose + CI workflow gerados

P2 — IMPORTANTE (sprint +2)
├── IMP-22: Layer 3 — k8s-helm platform profile
├── IMP-23: Layer 3 — terraform-aws profile
├── IMP-24: Composição de perfis (motor)
└── IMP-25: Governança — CHANGELOG, versioning, deprecation policy

P3 — FUTURO (backlog)
├── IMP-26: Layer 3 — data-pipeline / MLOps profiles
├── IMP-27: Layer 4 — lgpd-baseline compliance profile
├── IMP-28: Modo de upgrade/re-apply (projetos já gerados)
└── IMP-29: Documentação gerada por perfil ativo
```

---

## 📊 Scorecard Final por Dimensão

| Dimensão | Score Atual | Score Alvo (P1+P2) | Gap |
|----------|-------------|---------------------|-----|
| Core/Motor | 4/10 | 7/10 | Schema de perfis + testes |
| DevEx/CLI | 3/10 | 7/10 | --dry-run, --json, --list-profiles |
| SRE Baseline | 5/10 | 8/10 | CI/CD, Runbook, observabilidade |
| AppSec | 3/10 | 7/10 | SAST, secret scan, SBOM por perfil |
| Domain Profiles | 3/10 | 6/10 | Layer 2 (2-3 perfis) |
| Governança | 1/10 | 5/10 | IMP-16, versioning, matrix |
| **TOTAL** | **19/60** | **40/60** | **+21 pontos** |

---

## 🔗 Referências

- Documento-fonte: `docs/GitHub Copilot - Default Porject Template Skills.md`
- Agente criado: `.github/agents/template-architect.agent.md`
- TODO: `docs/TODO.md` (IMP-16, IMP-20 a IMP-29 adicionados)
- Sessão: `docs/SESSIONS/2026-03-07/DAILY_ACTIVITIES_2026-03-07.md`
