# 🎭 IMP-14 — Debate: SpecKit no Projeto Filho + Novos Perfis de Conhecimento

**Data**: 2026-03-05
**Projeto**: Enterprise Scaffold Project Template
**Issue**: IMP-14 — SpecKit instalado no projeto gerado + Novos Domain Profiles + Perfis Profissionais
**Status**: 🟢 Completo — D-20..D-25 todas respondidas (2026-03-05)
**Referência anterior**: [IMP-01-DEBATE.md](../2026-02-28/IMP-01-DEBATE.md) | [DOMAIN-PROFILES-DECISIONS.md](../../copilot/DOMAIN-PROFILES-DECISIONS.md) (D-01..D-19)

---

## 🧭 Contexto

### O Problema Dual-Use

O `scaffold-project` tem **dois papéis simultâneos** que nunca foram separados explicitamente:

```
scaffold-project/
│
├── [MODO META — Desenvolvimento do Template]
│    Copilot + SpecKit ajudam a CONSTRUIR o template.
│    Agents: speckit.specify, speckit.plan, speckit.tasks, ...
│    Usados para criar scaffold.py, templates, prompts.
│
└── [MODO OUTPUT — Projeto Gerado]
     scaffold.py GERA um novo projeto a partir do template.
     O projeto filho TAMBÉM precisa de SpecKit — mas nasce sem ele.
     Problema: copy_speckit() não existe em project.py.
```

**Gap identificado (2026-03-05)**:
- `scaffold.py` cria estrutura, symlinks, regras Copilot, VS Code — mas **não copia agents nem prompts SpecKit**
- O projeto filho nasce sem `speckit.specify`, sem `session-start`, sem domain profiles
- Toda a infraestrutura de raciocínio estruturado (SpecKit) fica "presa" no template

### O Segundo Problema — Perfis Faltantes

Os perfis profissionais e domain profiles identificados na sessão 2026-03-05 revelam lacunas:

**Domain Profiles existentes**: `devops-programming`, `devops-infrastructure`, `devops-analysis`

**Domain Profiles faltantes** (identificados nesta sessão):
- `devops-security` — DevSecOps, IaC security, secrets scanning
- `devops-cicd` — Pipelines, GitHub Actions, artefatos de CI
- `devops-review` — Code/PR review por domínio
- `devops-runbook` — SRE, resposta a incidentes, runbooks operacionais

**Perfis profissionais faltantes** no template:
- Arquiteto de Software → `constitution.md` (em branco)
- DevOps/Platform Eng. → CI/CD, Docker, geração de infra
- QA/SDET → sem testes para scaffold.py
- Security Engineer → pre-commit hooks, checklist de segurança
- Technical Writer → documentação de uso do scaffold.py
- UX/Product Designer → fluxo de perguntas do `ui.py`

---

## 🎭 Debate — Quatro Perspectivas

---

### 🏢 1. PROJECT MANAGER — Escopo, Prioridade, Riscos

#### 📌 Posição: "Separar o IMP-14 em entregas independentes para reduzir risco"

**Análise de valor vs. esforço**:

| Entrega | Valor | Esforço | Prioridade |
|---------|-------|---------|-----------|
| `copy_speckit()` em `project.py` — copia agents + prompts para filho | 🔴 Crítico | Médio | P0 |
| `constitution.md` preenchida no projeto filho (placeholders resolvidos) | 🔴 Crítico | Baixo | P0 |
| SpecKit version tracking em `config.py` (`SPECKIT_VERSION`) | 🟠 Alto | Baixo | P1 |
| Domain Profile `devops-security` | 🔴 Crítico | Médio | P0 |
| Domain Profile `devops-cicd` | 🟠 Alto | Médio | P1 |
| Domain Profile `devops-review` | 🟡 Médio | Baixo | P2 |
| Domain Profile `devops-runbook` | 🟡 Médio | Médio | P2 |
| `constitution.md` do template preenchida (princípios arquiteturais) | 🔴 Crítico | Alto | P0 |
| Testes para `scaffold.py` + `scripts/lib/` | 🟠 Alto | Alto | P1 |
| Documentação de uso do `scaffold.py` para usuário final | 🟠 Alto | Médio | P1 |

**Riscos identificados**:
- 🔴 **R1**: Atualização do SpecKit (como ocorreu em 2026-03-05) pode quebrar compatibilidade com o que foi copiado para projetos filhos já existentes — sem versionamento, não há como saber
- 🟠 **R2**: Copiar **todos** os agents e prompts pode levar conteúdo obsoleto/incompleto para o filho se o template não estiver 100% estável
- 🟠 **R3**: Novos domain profiles criados sem a visão de um Security Engineer podem ser superficiais — risco de falsa sensação de segurança
- 🟡 **R4**: `constitution.md` preenchida incorretamente pode conflitar com os princípios reais que o SpecKit vai aplicar

**Mitigações propostas**:
- R1: `SPECKIT_VERSION` em `config.py` + registrado em `docs/INDEX.md` do projeto filho
- R2: Flag `--speckit-snapshot` que copia o estado atual dos agents + freeze da versão
- R3: `devops-security` deve ter seção explícita de limitações (o que o perfil NÃO cobre)
- R4: `speckit.constitution` agent deve ser executado antes de qualquer `speckit.specify` num projeto novo

**Proposta de fases**:
```
Fase A (P0): copy_speckit() + constitution.md filho + SPECKIT_VERSION + devops-security
Fase B (P1): devops-cicd + testes scaffold + documentação de uso
Fase C (P2): devops-review + devops-runbook + constitution.md template
```

---

### 👨‍💻 2. DEVELOPER / ARQUITETO — Arquitetura Técnica

#### 📌 Posição: "Resolver o dual-use com camadas claras e sem duplicação de código"

**Separação de camadas proposta**:

```
Camada A — Permanece no Template (NUNCA copiado para filho)
──────────────────────────────────────────────────────────
docs/SESSIONS/           ← histórico de desenvolvimento do template
docs/copilot/            ← decisões de design (D-01..D-35+)
scripts/scaffold.py      ← o filho não é um template
scripts/lib/             ← idem
.specify/memory/         ← constituição do template (não do filho)

Camada B — Copiado para o Filho (copy_speckit)
──────────────────────────────────────────────
.specify/templates/      ← em branco, prontos para uso
.specify/config.json     ← configuração SpecKit
.github/agents/          ← todos os speckit.*.agent.md
.github/prompts/
  ├── speckit.*.prompt.md          ← todos os 9 prompts
  ├── session-start.prompt.md      ← ritual de início
  ├── session-start-first.prompt.md← primeira sessão
  ├── session-end.prompt.md        ← encerramento
  └── domain/
      └── devops-[DOMAIN].prompt.md ← APENAS o domain selecionado

Camada C — Gerado pelo Scaffold (já existe parcialmente)
──────────────────────────────────────────────────────────
.copilot-rules-[projeto].md  ← gerado por templates.py ✅
.vscode/settings.json        ← gerado por vscode.py ✅
.vscode/mcp.json             ← gerado por vscode.py ✅
.specify/memory/constitution.md ← NOVO: gerado com placeholders
```

**Nova função `copy_speckit(cfg)` em `project.py`**:

```python
def copy_speckit(cfg: ProjectConfig) -> list[CreatedItem]:
    """
    Copia agents, prompts e templates SpecKit do template para o projeto filho.
    Apenas o domain profile correspondente a cfg.domain é copiado.
    """
    template_root = Path(__file__).parent.parent.parent  # raiz do scaffold-project
    target = cfg.target_dir / cfg.project_name
    results = []

    # 1. .specify/templates/ (todos os templates em branco)
    # 2. .specify/config.json
    # 3. .github/agents/speckit.*.agent.md (todos os 9)
    # 4. .github/prompts/speckit.*.prompt.md (todos os 9)
    # 5. .github/prompts/session-*.prompt.md (3 arquivos)
    # 6. .github/prompts/domain/devops-[cfg.domain].prompt.md (só o domínio escolhido)
    # 7. Gera .specify/memory/constitution.md com placeholders resolvidos
```

**Contratos de interface — novos módulos**:

```python
# lib/project.py — adições
def copy_speckit(cfg: ProjectConfig) -> list[CreatedItem]: ...
def generate_constitution(cfg: ProjectConfig) -> CreatedItem: ...

# lib/config.py — adições
SPECKIT_VERSION: str = "x.y.z"   # atualizar a cada sync com SpecKit upstream

# Mapeamento domain → profile file (expandido com novos perfis)
DOMAIN_PROFILE_MAP: dict[str, list[str]] = {
    "programming": ["devops-programming"],
    "infrastructure": ["devops-infrastructure", "devops-cicd"],
    "analysis": ["devops-analysis", "devops-review"],
    "security": ["devops-security"],            # NOVO
}
```

**Estrutura dos novos domain profiles** (padrão a seguir):

```markdown
# Domain Profile: [NOME] — [Título Legível]

**Arquivo**: `.github/prompts/domain/devops-[nome].prompt.md`
**Quando usar**: [trigger declarativo]
**Domínios relacionados**: [lista]

## Contexto e Linguagem
[O que o Copilot deve saber sobre este domínio]

## Artefatos Produzidos
[O que este domínio entrega como output]

## Critérios de Done por Fase SpecKit
| Fase | Critérios |
|------|-----------|
| clarify | ... |
| specify | ... |
| plan | ... |
| tasks | ... |
| implement | ... |
| checklist | ... |

## ⚠️ Limitações deste Perfil
[O que este perfil explicitamente NÃO cobre]
```

**Decisão de arquitetura — `constitution.md` do template**:

O template (`scaffold-project`) tem sua própria `constitution.md` em `.specify/memory/constitution.md` com placeholders genéricos. Precisamos de dois documentos:

| Arquivo | Escopo | Quem preenche |
|---------|--------|--------------|
| `.specify/memory/constitution.md` (template) | Regras do template em si | Arquiteto + `speckit.constitution` agent |
| `[filho]/.specify/memory/constitution.md` | Regras do projeto gerado | Usuario + `speckit.constitution` agent no projeto filho |

---

### 🧩 3. FEATURE ENGINEER — Funcionalidades Detalhadas

#### 📌 Posição: "Mapear o que cada novo perfil entrega de concreto"

---

#### FEATURE-07: `copy_speckit()` — Instalação de SpecKit no Projeto Filho

**Gatilho**: Etapa automática no `flow_new_project()`, após FEATURE-03 (estrutura)

**Arquivos copiados**:
```
Template Source              → Destino no Filho
─────────────────────────────────────────────────
.specify/templates/*.md      → .specify/templates/*.md
.specify/config.json         → .specify/config.json
.github/agents/*.agent.md   → .github/agents/*.agent.md
.github/prompts/speckit.*.prompt.md → .github/prompts/speckit.*.prompt.md
.github/prompts/session-*.prompt.md → .github/prompts/session-*.prompt.md
.github/prompts/domain/devops-[domain].prompt.md → .github/prompts/domain/devops-[domain].prompt.md
```

**Arquivos gerados** (não copiados — criados com dados do projeto):
```
.specify/memory/constitution.md   ← placeholders resolvidos com nome/domínio/data
```

**Perguntas adicionais no fluxo interativo**:
- "Incluir múltiplos domain profiles? [s/n]" → se s, lista os disponíveis para o domínio
- "Versão do SpecKit a embalar: [auto-detectada]" → confirmar ou sobreescrever

---

#### FEATURE-08: Domain Profile `devops-security`

**Quando usar**: `Modo: SEGURANÇA. Contexto: [tarefa]`

**Cobertura**:
- Revisão de IaC (Terraform, Ansible) com foco em segurança
- Análise de secrets em código (truffleHog, gitleaks, git-secrets)
- SAST — Static Application Security Testing
- Threat modeling básico de componentes
- Geração de `.pre-commit-config.yaml` com hooks de segurança
- Checklists de segurança pré-merge / pré-deploy

**Artefatos produzidos**:
| Artefato | Formato | Fase SpecKit |
|----------|---------|-------------|
| Threat model simplificado | Markdown table | specify |
| Lista de controls verificados | Checklist | checklist |
| `.pre-commit-config.yaml` | YAML | tasks/implement |
| Security acceptance criteria | Seção em spec | specify |

**⚠️ Limitações explícitas**:
- Não substitui pentest
- Não valida criptografia de algoritmos
- Não cobre compliance regulatório (PCI-DSS, LGPD, SOC2)

---

#### FEATURE-09: Domain Profile `devops-cicd`

**Quando usar**: `Modo: CICD. Contexto: [tarefa de pipeline]`

**Cobertura**:
- GitHub Actions: workflows, jobs, steps, secrets, environments
- GitLab CI: stages, jobs, artifacts, cache
- Artefatos de release: Docker images, packages, binaries
- Estratégias de deploy: blue-green, canary, rolling
- Pipeline as Code — versionamento e review de pipelines

**Artefatos produzidos**:
| Artefato | Formato | Fase SpecKit |
|----------|---------|-------------|
| `.github/workflows/*.yml` | YAML | implement |
| Pipeline spec (stages, triggers, env) | Markdown | specify |
| Checklist de segurança do pipeline | Checklist | checklist |

---

#### FEATURE-10: Domain Profile `devops-review`

**Quando usar**: `Modo: REVIEW. Contexto: [PR/MR #N ou componente]`

**Cobertura**:
- Review de código (Python, TypeScript, Go) com foco em qualidade
- Review de IaC (Terraform, Ansible, Helm)
- Review de documentação técnica
- Geração de comentários de PR estruturados
- Critérios de aceite por tipo de mudança (feat, fix, refactor, docs, infra)

---

#### FEATURE-11: Domain Profile `devops-runbook`

**Quando usar**: `Modo: RUNBOOK. Contexto: [sistema/incidente]`

**Cobertura**:
- Resposta a incidentes (incident response)
- Criação de runbooks operacionais
- Análise post-mortem (blameless)
- SLO/SLI/Error budget — definição e revisão
- Escalation paths e on-call rotations

---

#### FEATURE-12: `constitution.md` do Template Preenchida

**Escopo**: Definir os princípios arquiteturais do próprio `scaffold-project`

**Princípios candidatos** (a validar com usuário):

| Princípio | Descrição |
|-----------|-----------|
| I. Template-as-Code | Toda configuração é versionada; nada manual sem rastro |
| II. SpecKit-First | Todo trabalho substantivo passa por clarify → specify → plan → tasks |
| III. Scaffold Idempotente | Executar scaffold.py N vezes = mesmo resultado |
| IV. Zero-Trust nos Secrets | Nenhuma credencial em código ou commits |
| V. Docs como Cidadãos de Primeira Classe | Docs de sessão, decisões e IMPs são parte do produto |
| VI. Extensibilidade > Perfeição | Perfis e templates são pontos de extensão, não dogmas |

---

### 📐 4. SPECIFICATIONS ENGINEER — Critérios de Aceite e Contratos

#### 📌 Posição: "Definir fronteiras claras entre o que o template provê e o que o filho deve completar"

---

#### SPEC-06: Critérios — FEATURE-07 (`copy_speckit`)

- [ ] Todos os 9 agents `speckit.*.agent.md` copiados para `.github/agents/` do filho
- [ ] Todos os 9 prompts `speckit.*.prompt.md` copiados para `.github/prompts/` do filho
- [ ] `session-start.prompt.md`, `session-start-first.prompt.md`, `session-end.prompt.md` copiados
- [ ] Apenas o domain profile do `cfg.domain` copiado em `.github/prompts/domain/`
- [ ] `constitution.md` gerada com `{{PROJECT_NAME}}`, `{{CREATED_AT}}`, `{{DOMAIN}}` resolvidos
- [ ] `SPECKIT_VERSION` registrado em `docs/INDEX.md` do filho na linha de criação
- [ ] Se arquivo já existe no destino → skip com aviso (não sobrescreve)
- [ ] Operação é idempotente: segunda execução não gera erro nem duplica arquivos

---

#### SPEC-07: Critérios — FEATURE-08 (`devops-security`)

- [ ] Arquivo em `.github/prompts/domain/devops-security.prompt.md`
- [ ] Seção "Quando usar" com trigger declarativo explícito
- [ ] Seção "⚠️ Limitações" presente e honesta
- [ ] Critérios de Done para cada fase SpecKit (clarify, specify, plan, tasks, implement, checklist)
- [ ] Exemplo de uso concreto (threat model de um componente real)
- [ ] Integração com `DOMAIN_MAP` em `config.py`

---

#### SPEC-08: Critérios — FEATURE-12 (`constitution.md` Template)

- [ ] 5-7 princípios, cada um com nome, descrição e consequência prática
- [ ] Seção "Governance" com regras de alteração da constitution
- [ ] Version, Ratified date, Last Amended date preenchidos
- [ ] Gerado via `speckit.constitution` agent (não manualmente)
- [ ] Consistente com as 19 decisões D-01..D-19 já tomadas

---

#### SPEC-09: Contratos de Interface — Novos em `config.py`

```python
# Adições necessárias em lib/config.py

SPECKIT_VERSION: str = "x.y.z"  # sincronizar com upstream em cada update

# Domain profiles disponíveis (expandido de 3 para 7)
VALID_DOMAIN_PROFILES: list[str] = [
    "devops-programming",
    "devops-infrastructure",
    "devops-analysis",
    "devops-security",    # NOVO — Fase A
    "devops-cicd",        # NOVO — Fase B
    "devops-review",      # NOVO — Fase C
    "devops-runbook",     # NOVO — Fase C
]

# Mapeamento domínio → profile(s) padrão copiados para o filho
DOMAIN_DEFAULT_PROFILES: dict[str, list[str]] = {
    "programming":    ["devops-programming", "devops-review"],
    "infrastructure": ["devops-infrastructure", "devops-cicd", "devops-security"],
    "analysis":       ["devops-analysis", "devops-review"],
}
```

---

#### SPEC-10: Perfis Profissionais — Entregáveis Concretos

O debate reconhece os seguintes perfis profissionais como **geradores de conteúdo específico** para o template:

| Perfil Profissional | IMP Relacionado | Entregável |
|--------------------|-----------------|-----------|
| Arquiteto de Software | FEATURE-12 | `constitution.md` preenchida |
| DevOps/Platform Eng. | IMP-15 (futuro) | Geração de `Dockerfile`, `docker-compose.yml`, workflows CI |
| QA/SDET | IMP-16 (futuro) | Testes para `scaffold.py` + `scripts/lib/` |
| Security Engineer | FEATURE-08 | `devops-security.prompt.md` + pre-commit hooks |
| Technical Writer | IMP-10 (existente) | `docs/copilot/DOMAIN-*.md` humanamente legíveis |
| UX/Product Designer | IMP-09 (existente) | Melhoria do fluxo de perguntas em `ui.py` |

---

## 🧩 Decisões Necessárias (D-20..D-35)

> As respostas abaixo serão registradas em `docs/copilot/DOMAIN-PROFILES-DECISIONS.md`

---

### D-20 — Qual domínio de destino padrão para `devops-security`?

**Contexto**: O perfil de segurança não se encaixa em um único domínio — é transversal.

| Opção | Descrição |
|-------|-----------|
| **A** | Profile independente — o usuário declara explicitamente `Modo: SEGURANÇA` |
| **B** | Incluído por padrão em `infrastructure` (domínio mais sensível) |
| **C** | Incluído em todos os domínios como overlay |

**Pergunta**: Ao criar novo projeto, o `devops-security` deve ser copiado para o filho em qual situação?

**Resposta**: ✅ **Opção A — Copiado sempre.** Todo projeto filho recebe `devops-security.prompt.md` independente do domínio selecionado.

---

### D-21 — `copy_speckit()` copia todos os domain profiles ou apenas o do domínio selecionado?

**Contexto concreto — quantos arquivos cada opção copia**:

Com D-20 (security sempre) e D-24 (review/runbook como extensões dos existentes) decididos,
os arquivos de domain profile passam a ser:

| Arquivo | Domínio base | Sempre? |
|---------|-------------|--------|
| `devops-programming.prompt.md` (+ seção Review) | programming | — |
| `devops-infrastructure.prompt.md` (+ seção Review) | infrastructure | — |
| `devops-analysis.prompt.md` (+ seção Runbook) | analysis | — |
| `devops-security.prompt.md` | transversal | ✅ sempre (D-20) |
| `devops-cicd.prompt.md` | infrastructure/programming | — |

**Cenários comparados**: usuário cria projeto com `domain=programming`

| Opção | Arquivos copiados em `.github/prompts/domain/` |
|-------|----------------------------------------------|
| **A — Só o domínio** | `devops-programming.prompt.md` + `devops-security.prompt.md` = **2 arquivos** |
| **B — Todos** | todos os 5 arquivos = **5 arquivos** |
| **C — Interativa** | depende da escolha — entre 2 e 5 arquivos + 1 pergunta a mais |

**Impacto prático da Opção A**: se o usuário precisar de `devops-cicd` depois (ex: criar pipeline), ele precisa copiar manualmente ou re-executar scaffold.

**Impacto prático da Opção B**: o Copilot vê todos os profiles e pode citar/misturar contextos de domínios diferentes. Risco baixo mas pode gerar confusão.

**Impacto prático da Opção C**: uma pergunta a mais no scaffold — "Perfis adicionais? [cicd/nenhum]" — UX aceitável se for só 1 pergunta com múltipla escolha.

**Resposta**: ✅ **Opção C — Seleção interativa.** `copy_speckit()` copia domínio selecionado + `devops-security` (sempre, por D-20) + os perfis que o usuário escolher na pergunta adicional. Resolvido em conjunto com D-25 (Cenário Y).

---

### D-22 — A `constitution.md` do template deve ser preenchida antes ou depois dos novos domain profiles?

**Contexto**: A constituição define princípios que os profiles devem respeitar. Se profiles forem criados antes, podem ser inconsistentes com a constituição.

| Opção | Descrição |
|-------|-----------|
| **A** | Constituição primeiro (bloqueante) — nenhum profile criado sem ela |
| **B** | Paralelo — profiles e constituição criados na mesma sessão, revisados juntos |
| **C** | Profiles primeiro, constituição depois (como feedback do que funcionou) |

**Resposta**: ✅ **Opção B — Paralelo.** `constitution.md` e novos domain profiles criados na mesma sessão, revisados em conjunto ao final.

---

### D-23 — `SPECKIT_VERSION` deve ser detectada automaticamente ou declarada manualmente?

**Contexto**: A versão do SpecKit embarcada no template precisa ser rastreada.

| Opção | Implementação |
|-------|--------------|
| **A — Manual** | Desenvolvedor atualiza `SPECKIT_VERSION` em `config.py` após cada sync |
| **B — Auto via git tag** | Script lê a tag mais recente do repositório SpecKit |
| **C — Auto via hash** | Usa o hash git dos arquivos `.github/agents/` como versão |

**Informações adicionais para decidir**:

**Opção A — Manual**:
```python
# scripts/lib/config.py
SPECKIT_VERSION = "1.2.0"   # atualizado manualmente pelo dev após cada sync
```
- Simples, sem dependências extras
- Risco: esquece de atualizar → versão desatualizada silenciosamente
- Funciona sem acesso ao `.git` do SpecKit upstream

**Opção B — Auto via git tag**:
```python
# Requer que o SpecKit upstream tenha tags de versão (ex: v1.2.0)
# Funciona se o template atualiza via `git subtree` ou `git submodule`
import subprocess
SPECKIT_VERSION = subprocess.run(
    ["git", "describe", "--tags", "--abbrev=0", "HEAD:.github/agents"],
    capture_output=True, text=True
).stdout.strip() or "unknown"
```
- Automático, mas **depende de o SpecKit usar tags git**
- Hoje o SpecKit não é um sub-repositório — é um conjunto de arquivos copiados diretamente
- Não aplicável no estado atual

**Opção C — Auto via hash dos agents**:
```python
import hashlib, pathlib
_agents = sorted(pathlib.Path(".github/agents").glob("*.md"))
_content = b"".join(f.read_bytes() for f in _agents)
SPECKIT_VERSION = hashlib.sha1(_content).hexdigest()[:8]  # ex: "a3f9c12b"
```
- Sempre reflete o estado real dos agents
- A "versão" parece um hash, não um número semântico (ex: `a3f9c12b` vs `1.2.0`)
- Ideal para rastrear se houve mudança, mas difícil de comunicar para o usuário

**Cenário real**: quando o SpecKit atualiza (como aconteceu hoje em 2026-03-05), o que você quer ver no `docs/INDEX.md` do projeto filho?
- `SpecKit: 1.2.0` (semântico, mas manual)
- `SpecKit: a3f9c12b` (automático, mas críptico)
- `SpecKit: 2026-03-05` (data do sync — mais legível que hash)

**Sugestão do Developer**: **Opção A com data de sync** — `SPECKIT_SYNC_DATE = "2026-03-05"` em vez de número de versão. Fácil de atualizar, legível, honesto sobre o que está versionado.

**Resposta**: ✅ **Seguir sugestão — `SPECKIT_SYNC_DATE`.** Adicionar `SPECKIT_SYNC_DATE = "2026-03-05"` em `config.py`. Atualizado manualmente a cada sync do SpecKit. Registrado em `docs/INDEX.md` do projeto filho como `SpecKit sync: 2026-03-05`.

---

### D-24 — Os perfis `devops-review` e `devops-runbook` são profiles independentes ou extensões de profiles existentes?

**Contexto**: `devops-review` compartilha muito com `devops-programming` e `devops-infrastructure`. `devops-runbook` compartilha com `devops-analysis`.

| Opção | Descrição |
|-------|-----------|
| **A** | Profiles independentes (`devops-review.prompt.md`, `devops-runbook.prompt.md`) |
| **B** | Seções adicionais nos profiles existentes (`devops-programming` ganha seção "Review") |
| **C** | Profiles compostos — um arquivo que inclui/referencia outro |

**Resposta**: ✅ **Opção B — Extensões.** `devops-review` vira seção em `devops-programming` e `devops-infrastructure`. `devops-runbook` vira seção em `devops-analysis`. Nenhum arquivo novo independente.

---

### D-25 — Quais novas perguntas o fluxo interativo do `scaffold.py` deve fazer em relação ao SpecKit?

**Contexto**: Hoje o fluxo não pergunta nada sobre SpecKit. Com `copy_speckit()`, surgem perguntas potenciais.

**Fluxo atual** — 7 perguntas hoje (código confirmado em `ui.py`):
```
[1] Nome do projeto       (obrigatório)
[2] Título legível        (opcional, default=auto)
[3] Descrição             (opcional)
[4] Domínio               (programming | infrastructure | analysis)
[5] Linguagem principal   (python | typescript | go | other)
[6] Repositório GitHub    (opcional)
[7] Diretório compartilhado  (opcional, default=~/Documentos/DevOps/.copilot-shared)
```

**Cenários propostos com novas perguntas**:

**Cenário X — Zero perguntas novas** (SpecKit sempre copiado, silenciosamente):
```
Mesmo fluxo de 7 perguntas. copy_speckit() roda automaticamente.
Saída: "✅ SpecKit instalado (sync: 2026-03-05)"
```
→ UX mais limpa. Desvantagem: usuário não sabe o que foi copiado.

**Cenário Y — 1 pergunta nova** (apenas se quiser profiles extras além do domínio):
```
[8] Perfis adicionais?  [1] Só meu domínio  [2] Todos disponíveis
    (inclui sempre: domínio selecionado + devops-security)
```
→ 8 perguntas total. Resolve D-21 junto com esta pergunta.

**Cenário Z — 2 perguntas novas** (controle total):
```
[8] Perfis adicionais?  [1] Só meu domínio  [2] Todos  [3] Selecionar
[9] Inicializar constitution.md agora? [s/n]
```
→ 9 perguntas total. Máximo razoável antes de parecer um wizard.

**Referência de UX**: ferramentas como `create-react-app`, `cookiecutter`, `poetry new` usam no máximo 6-8 perguntas antes de oferecer modo `--advanced`.

**Sugestão do Developer**: Cenário Y (1 pergunta nova) que resolve D-21 e D-25 juntos. Se quiser controle total, usar `--advanced` flag.

**Resposta**: ✅ **Cenário Y — 1 pergunta nova (8 perguntas total).** Nova pergunta `[8]` no fluxo interativo:
```
[8] Perfis adicionais além de [domínio]?
    [1] Apenas meu domínio  [2] Todos disponíveis  [3] Selecionar
    (devops-security incluído sempre — não aparece nesta escolha)
```
Resolve D-21 e D-25 conjuntamente. Modo `--ci` aceita `--extra-profiles all|none|lista`.

---

## 📋 Resumo das Sub-tarefas Identificadas

### Fase A — IMP-14 Core (P0)

| Sub-tarefa | Arquivo modificado/criado | Dep. | Decisão base |
|------------|--------------------------|------|-------------|
| A.1 — Adicionar `SPECKIT_SYNC_DATE` e `DOMAIN_DEFAULT_PROFILES` | `scripts/lib/config.py` | — | D-23 ✅ |
| A.2 — Implementar `copy_speckit(cfg)` com pergunta de perfis extras | `scripts/lib/project.py` | A.1 | D-21 ✅ D-20 ✅ |
| A.3 — Implementar `generate_constitution(cfg)` | `scripts/lib/project.py` | — | D-22 ✅ |
| A.4 — Adicionar pergunta `[8]` ao `_collect_interactive()` | `scripts/lib/ui.py` | A.2 | D-25 ✅ |
| A.5 — Integrar `copy_speckit()` e `generate_constitution()` em `scaffold.py` | `scripts/scaffold.py` | A.2, A.3, A.4 | — |
| A.6 — Criar `devops-security.prompt.md` | `.github/prompts/domain/` | — | D-20 ✅ |
| A.7 — Expandir profiles existentes com seções Review/Runbook | `.github/prompts/domain/devops-*.prompt.md` | A.6 | D-24 ✅ |
| A.8 — Preencher `constitution.md` do template via `speckit.constitution` | `.specify/memory/constitution.md` | — | D-22 ✅ |

### Fase B — IMP-14 Complementar (P1)

| Sub-tarefa | Arquivo modificado/criado | Dependência |
|------------|--------------------------|-------------|
| B.1 — Criar `devops-cicd.prompt.md` | `.github/prompts/domain/` | Fase A concluída |
| B.2 — Testes para `copy_speckit()` | `tests/test_project.py` | A.2 |
| B.3 — Documentação de uso do `scaffold.py` | `docs/SCAFFOLD_USAGE.md` | Fase A |

### Fase C — IMP-14 Expansão (P2)

| Sub-tarefa | Arquivo modificado/criado | Dependência |
|------------|--------------------------|-------------|
| C.1 — Criar `devops-review.prompt.md` | `.github/prompts/domain/` | D-24 |
| C.2 — Criar `devops-runbook.prompt.md` | `.github/prompts/domain/` | D-24 |
| C.3 — Atualizar `scripts/lib/ui.py` com perguntas de SpecKit | `scripts/lib/ui.py` | D-25, Fase A |

---

## 🔗 Dependências com IMPs Existentes

| IMP | Título | Relação com IMP-14 |
|-----|--------|-------------------|
| IMP-09 | Template `.copilot-rules-[projeto].md` | A.4 depende de IMP-09 estar estável |
| IMP-10 | `docs/copilot/DOMAIN-*.md` humanos | IMP-14 Fase B.3 complementa IMP-10 |
| IMP-15 (futuro) | Geração Dockerfile / CI/CD | `devops-cicd` profile (B.1) é precursor |
| IMP-16 (futuro) | Testes scaffold.py | B.2 inicia os testes |

---

*Gerado em 2026-03-05 | Sessão: Debate estruturado IMP-14 | Aguardando D-20..D-25*
