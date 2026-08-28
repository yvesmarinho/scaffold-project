# 🎭 IMP-01 — Debate de Funcionalidades: `scaffold.py`

**Data**: 2026-02-28
**Projeto**: Enterprise Scaffold Project Template
**Issue**: IMP-01 — Criar `scripts/scaffold.py` — CLI Python (ponto único de entrada do projeto)
**Status**: 🟠 Revisado (Tensão 2 resolvida — separação scaffold.py vs Makefile)
**Referência de Decisões**: [DOMAIN-PROFILES-DECISIONS.md](../../copilot/DOMAIN-PROFILES-DECISIONS.md) — D-01, D-11, D-15, D-16, D-19

---

## 🧭 Contexto

O `scaffold.py` é a peça mais crítica do IMP backlog. Ele substitui **três shell scripts** do template atual:

| Script absorvido | Responsabilidade atual |
|------------------|----------------------|
| `init-new-project.sh` | Cria estrutura de pastas, substitui placeholders, inicia Git |
| `setup-project-links.sh` | Cria symlinks `.copilot-*` do diretório compartilhado para o projeto |
| `check-project-links.sh` | Valida se os symlinks estão ativos e corretos |

**Decisão base (D-16/D-19)**: `scaffold.py` absorve tudo em Python. Scripts shell são aposentados.

**Stack tecnológico de referência**: O `scripts/manage.py` existente (herdado do `enterprise-ansible`) usa `Textual` + `Rich` — TUI completa com menus, árvore de componentes, log em tempo real.

---

## 🎭 Debate — Quatro Perspectivas

---

### 🏢 1. PROJECT MANAGER — Escopo, Prioridade, Riscos

#### 📌 Posição: "MVP focado — entregar valor no menor tempo possível"

**Análise de valor vs. esforço**:

| Funcionalidade | Valor | Esforço | Prioridade |
|----------------|-------|---------|-----------|
| Fluxo interativo de novo projeto (coleta nome, repo, domínio) | 🔴 Crítico | Médio | P0 |
| Criação de estrutura de pastas | 🔴 Crítico | Baixo | P0 |
| Setup de symlinks `.copilot-*` | 🔴 Crítico | Baixo | P0 |
| Geração de `.copilot-rules-[projeto].md` | 🟠 Alto | Médio | P1 |
| Check/diagnóstico de links | 🟡 Médio | Baixo | P2 |
| Integração com MCP `memory` para persistência | 🟡 Médio | Alto | P3 |
| TUI com Textual (menus visuais, árvore) | 🟢 Nice-to-have | Alto | P3 |

**Decisão do PM**:
> "O MVP do `scaffold.py` deve cobrir apenas P0 e P1. TUI completa com Textual é P3 — pode ser CLI simples com `input()` + `Rich` primeiro. Reduz dependências e curva de aprendizado."

**Riscos identificados**:
- 🔴 **Risco R1**: Usar `Textual` torna o script dependente de instalação de pacotes (`textual`, `rich`, `pyyaml`). Um projeto recém-clonado pode não ter as deps → script não roda.
- 🟠 **Risco R2**: Shell scripts atuais (`init-new-project.sh`) já funcionam. Se `scaffold.py` falhar, não há fallback.
- 🟡 **Risco R3**: O caminho do diretório centralizado `$HOME/Documentos/DevOps/.copilot-shared` é hardcoded no shell script. O `scaffold.py` precisa detecção configurável desse path.

**Mitigações propostas**:
- R1: Usar `uv run scripts/scaffold.py` (resolve deps automaticamente via PEP 723 `# /// script`)
- R2: Manter shell scripts como fallback até `scaffold.py` estável (deprecated, não removido)
- R3: Detectar o path do shared dir via argumento, variável de ambiente ou fallback para path padrão

---

### 👨‍💻 2. DEVELOPER — Arquitetura Técnica e Implementação

#### 📌 Posição: "Clean architecture desde o início — módulos coesos, fácil de estender"

**Estrutura de módulos proposta**:

```
scripts/
├── scaffold.py             ← Entry point principal (thin wrapper)
└── lib/                    ← Módulos internos
    ├── __init__.py
    ├── config.py           ← Constantes, paths, configurações
    ├── ui.py               ← I/O: prompts, Rich output, menus
    ├── project.py          ← Lógica de criação de projeto (absorve init-new-project.sh)
    ├── links.py            ← Lógica de symlinks (absorve setup/check-project-links.sh)
    ├── git.py              ← Operações Git (init, remote add)
    └── templates.py        ← Geração de arquivos modelo (.copilot-rules-[projeto].md)
```

**Por que essa estrutura?**
- `scaffold.py` permanece legível (< 100 linhas de orquestração)
- Cada módulo testável independentemente
- Fácil de adicionar novos fluxos sem tocar no entry point

**Fluxo de execução principal**:

```
scaffold.py
  ├─ args: --mode [new|check|help]
  │
  ├─ Modo: new (padrão)
  │    ├─ ui.collect_project_info()     → ProjectConfig
  │    ├─ project.create_structure()   ← cria pastas e arquivos base
  │    ├─ links.setup_symlinks()       ← cria symlinks .copilot-*
  │    ├─ templates.generate_rules()   ← gera .copilot-rules-[projeto].md
  │    ├─ git.init_repository()        ← git init + remote add
  │    └─ ui.print_summary()           ← resumo do que foi feito
  │
  └─ Modo: check
       └─ links.check_symlinks()       ← valida symlinks + relatório
```

**Escolha de UI — debate interno**:

| Opção | Pro | Contra | Decisão |
|-------|-----|--------|---------|
| `Textual` (TUI completa) | Visual rico, navegação por teclado | Deps pesadas, overhead para script simples | **P3 — futuro** |
| `Rich` + `input()` | Deps já presente, saída bonita, sem interação complexa | Linear, sem menus dinâmicos | **MVP — agora** |
| `argparse` puro | Zero dep extra | Output feio, pouca usabilidade | **fallback CI** |

**Decisão técnica do Developer**:
> "MVP com `Rich` + `input()` interativo + validação. O código é estruturado de forma que substituir `input()` por `Textual` depois seja localizado em `lib/ui.py` sem tocar no resto."

**Dependências**:
```toml
# PEP 723 — uv resolve automaticamente
# requires-python = ">=3.10"
# dependencies = ["rich>=13.7"]
# Opcional futuramente: textual>=0.80, pyyaml>=6.0
```

**Compatibilidade com `make init`**:
```makefile
init:
    @echo " ⚠️  Use: uv run scripts/scaffold.py"
# (make init agora é apenas redirect — lógica está em scaffold.py)
```

---

### 🧩 3. FEATURE ENGINEER — Funcionalidades Detalhadas e Fluxos

#### 📌 Posição: "Mapear todos os fluxos que o usuário vai precisar — não só o happy path"

**Funcionalidades identificadas (completo)**:

#### FEATURE-01: Criar Novo Projeto (absorve `init-new-project.sh`)

**Gatilho**: `uv run scripts/scaffold.py` (modo interativo padrão)

**Fluxo interativo**:
```
┌─────────────────────────────────────────────────‐──────────────────────────────────┐
│ 🚀 Enterprise Project Scaffold                                                      │
│ ─────────────────────────────────────────────────────────────────────────────────── │
│                                                                                     │
│  [1] Criar novo projeto                                                             │
│  [2] Verificar links do projeto atual                                               │
│  [3] Gerar .copilot-rules para este projeto                                         │
│  [4] Sair                                                                           │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

**Dados coletados**:
| Campo | Pergunta | Validação | Exemplo |
|-------|----------|-----------|---------|
| `project_name` | "Nome do projeto (slug kebab-case):" | `^[a-z0-9-]+$` | `my-api-v2` |
| `project_title` | "Título legível do projeto:" | não-vazio | `My API v2` |
| `description` | "Descrição breve (1 frase):" | não-vazio | `REST API for payments` |
| `github_repo` | "URL do repositório GitHub (ou Enter para pular):" | URL ou vazio | `https://github.com/user/my-api-v2` |
| `domain` | "Domínio de trabalho: [1] Programação [2] Infraestrutura [3] Análise" | 1/2/3 | `2` |
| `language` | "Linguagem principal: [1] Python [2] TypeScript [3] Go [4] Outro" | 1-4 | `1` |
| `shared_dir` | "Dir. compartilhado .copilot-shared (Enter = padrão):" | path existe ou padrão | `~/DevOps/.copilot-shared` |

**Ações executadas**:
1. Criar estrutura de pastas (ver FEATURE-03)
2. Substituir placeholders em README, INDEX, TODO
3. Setup de symlinks `.copilot-*` (→ FEATURE-02)
4. Geração de `.copilot-rules-[projeto].md` (→ FEATURE-04)
5. `git init` + `git remote add origin <url>` (se URL fornecida)
6. Exibir resumo colorido (Rich)

---

#### FEATURE-02: Setup de Symlinks (absorve `setup-project-links.sh`)

**Gatilho**: Executado automaticamente no final de FEATURE-01, ou manualmente via menu

**Arquivos compartilhados esperados em `shared_dir`**:
```
.copilot-shared/
├── .copilot-rules.md
├── .copilot-git-rules.md
├── .copilot-strict-enforcement.md
├── .copilot-strict-rules.md
└── .copilot-file-rules.sh
```

**Comportamento**:
- Se `shared_dir` não existe → aviso + pula (não falha o setup)
- Se arquivo compartilhado não existe → aviso por arquivo + log
- Se symlink já existe → skip (não sobrescreve)
- Se symlink existente está quebrado → recria + aviso

---

#### FEATURE-03: Estrutura de Pastas do Novo Projeto

**Baseada nas decisões D-02/D-18** — domain profiles ficam no repo:

```
[project_name]/
├── .copilot-rules-[project_name].md    ← gerado pelo scaffold.py (D-14)
├── .copilot-rules.md                   ← symlink → shared
├── .copilot-git-rules.md               ← symlink → shared
├── .copilot-strict-enforcement.md      ← symlink → shared
├── .copilot-strict-rules.md            ← symlink → shared
├── .copilot-file-rules.sh              ← symlink → shared
├── .git/
├── .github/
│   ├── agents/                         ← speckit agents
│   └── prompts/
│       ├── session-start.prompt.md     ← IMP-02
│       ├── session-start-first.prompt.md ← IMP-03
│       ├── session-end.prompt.md       ← IMP-04
│       └── domain/
│           ├── devops-programming.prompt.md   ← IMP-05
│           ├── devops-infrastructure.prompt.md ← IMP-06
│           └── devops-analysis.prompt.md      ← IMP-07
├── .gitignore
├── .secrets/
│   └── README.md
├── .specify/
├── .vscode/
│   ├── mcp.json
│   └── settings.json
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   ├── TODAY_ACTIVITIES.md
│   └── SESSIONS/
├── Makefile
├── README.md
├── [project_name].code-workspace
└── scripts/
    ├── scaffold.py
    └── lib/
```

---

#### FEATURE-04: Geração de `.copilot-rules-[projeto].md` (absorve criação manual)

**Conteúdo gerado com base nos dados coletados**:
```markdown
# Copilot Rules — [project_title]

## Identidade do Projeto
- **Nome**: [project_name]
- **Domínio**: [domain] (programação | infraestrutura | análise)
- **Linguagem**: [language]
- **Repositório**: [github_repo]
- **Criado em**: [data]

## Domain Profile Ativo
→ Ver `.github/prompts/domain/devops-[domain].prompt.md`

## Regras Específicas do Projeto
[seção editável — vazia na geração, preenchida pelo dev]
```

---

#### FEATURE-05: Verificação de Links (absorve `check-project-links.sh`)

**Gatilho**: `uv run scripts/scaffold.py --check` ou menu item [2]

**Output esperado**:
```
✅ .copilot-rules.md          → /home/user/DevOps/.copilot-shared/.copilot-rules.md
✅ .copilot-git-rules.md      → /home/user/DevOps/.copilot-shared/.copilot-git-rules.md
❌ .copilot-strict-rules.md   → QUEBRADO (target não existe)
⚠️  .copilot-file-rules.sh   → NÃO ENCONTRADO (symlink não criado)
```

---

#### FEATURE-06: Argumentos CLI (para uso em CI ou automação)

```bash
uv run scripts/scaffold.py                    # interativo (padrão)
uv run scripts/scaffold.py --check           # só verifica links
uv run scripts/scaffold.py --new             # pula menu, vai direto ao fluxo de novo projeto
uv run scripts/scaffold.py --help            # ajuda
uv run scripts/scaffold.py --version         # versão
```

---

### 📐 4. SPECIFICATIONS ENGINEER — Critérios de Aceite e Contratos

#### 📌 Posição: "Definir o que 'feito' significa para cada feature antes de começar a codificar"

---

#### SPEC-01: Critérios de Aceite Globais

- [ ] O script executa com `uv run scripts/scaffold.py` sem intervenção manual de instalação
- [ ] O script executa com `python scripts/scaffold.py` se deps já instaladas
- [ ] `make init` exibe mensagem redirecionando para `uv run scripts/scaffold.py`
- [ ] Toda saída usa `Rich` — cores, ícones de status, tabelas
- [ ] Erros são exibidos em vermelho com mensagem clara e código de saída não-zero
- [ ] Nenhuma operação destrutiva (sobrescrever arquivos existentes) sem confirmação
- [ ] Log em `scripts/logs/scaffold.log` com timestamp, nível e mensagem
- [ ] O script é idempotente: rodar duas vezes não gera estado inconsistente

---

#### SPEC-02: Critérios — FEATURE-01 (Criar Novo Projeto)

- [ ] Todos os campos exibem valor padrão entre colchetes quando aplicável
- [ ] Validação de `project_name`: regex `^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$`
- [ ] Se `github_repo` vazio: `git init` sem `remote add` — sem erro
- [ ] Se `shared_dir` não detectado: aviso amarelo — setup prossegue sem symlinks
- [ ] Ao final: exibir tabela Rich com todos os arquivos criados e seus status (✅/⚠️/❌)
- [ ] Ao final: exibir próximos passos (next steps) sugeridos

---

#### SPEC-03: Critérios — FEATURE-02 (Symlinks)

- [ ] Symlinks relativos (não absolutos) — portável entre máquinas
- [ ] Symlink quebrado detectado → recriado com aviso (não falha silenciosamente)
- [ ] Symlink já correto → skip com mensagem "já existe, ok"
- [ ] Permissão `+x` mantida em `.copilot-file-rules.sh` após symlink

---

#### SPEC-04: Critérios — FEATURE-05 (Check de Links)

- [ ] Saída é legível por humanos (Rich table) e por máquinas (`--json` flag opcional)
- [ ] Código de saída 0 se todos os links ok; 1 se algum quebrado/faltando
- [ ] Pode ser chamado como `make check-links` (Makefile target independente)

---

#### SPEC-05: Contratos de Interface (assinaturas dos módulos)

```python
# lib/config.py
@dataclass
class ProjectConfig:
    project_name: str
    project_title: str
    description: str
    github_repo: str | None
    domain: Literal["programming", "infrastructure", "analysis"]
    language: Literal["python", "typescript", "go", "other"]
    shared_dir: Path
    target_dir: Path  # onde o projeto será criado

# lib/project.py
def create_structure(config: ProjectConfig) -> list[CreatedItem]: ...

# lib/links.py
def setup_symlinks(config: ProjectConfig) -> list[LinkResult]: ...
def check_symlinks(project_dir: Path, shared_dir: Path) -> list[LinkStatus]: ...

# lib/templates.py
def generate_copilot_rules(config: ProjectConfig) -> Path: ...

# lib/git.py
def init_repository(project_dir: Path, remote_url: str | None = None) -> bool: ...

# lib/ui.py
def collect_project_info() -> ProjectConfig: ...
def print_summary(items: list[CreatedItem | LinkResult]) -> None: ...
```

---

## 🔴 Pontos de Tensão no Debate

### Tensão 1: TUI completa vs. CLI simples

| Perspectiva | Posição |
|-------------|---------|
| **PM** | "CLI simples agora, TUI depois. Não bloqueie IMP-02 a IMP-10 por causa de UI." |
| **Developer** | "Estrutura modular agora = TUI depois sem reescrita. `lib/ui.py` é a camada de isolamento." |
| **Feature Eng.** | "O valor está nos fluxos, não no visual. Rich + input() entrega 80% do valor." |
| **Spec Eng.** | "A spec não prescreve UI — prescreve comportamento e contratos. UI é detalhe de implementação." |

**Resolução**: ✅ **MVP com Rich + input(). Textual é backlog P3. Estrutura modular desde o início.**

---

### Tensão 2: `scaffold.py` vs. `Makefile` — onde fica a responsabilidade de inicialização?

| Perspectiva | Posição |
|-------------|--------|
| **PM** | "O Makefile que temos hoje já tem 40+ targets — build, test, lint, docker, deploy. Adicionar `make init` como capa do `scaffold.py` cria ambiguidade: dois caminhos para a mesma ação. Isso gera confusão em novos colaboradores." |
| **Developer** | "o `Makefile` é um executor de tarefas de **build/CI**. O `scaffold.py` é um **scaffolding interativo de projetos**. São ferramentas com domínios distintos. Não se deve misturar." |
| **Feature Eng.** | "Do ponto de vista do usuário: se existe `make init`, ele esperará que TUDO sobre inicialização fique ali. Se parte está no Python e parte no Makefile, há dois lugares para procurar. Isso viola o princípio do menor espanto." |

**Resolução**: ✅ **Separação total de domínios:**

| Ferramenta | Domínio | Exemplos de comandos |
|------------|---------|---------------------|
| `scaffold.py` | Scaffolding de projeto | criar projeto, verificar links, gerar regras copilot |
| `Makefile` | Build, teste, deploy, CI | `test`, `lint`, `build`, `docker-build`, `format` |

`scaffold.py` é invocado **diretamente**: `python scripts/scaffold.py` ou `uv run scripts/scaffold.py`.
O Makefile **não tem** target de inicialização. **Zero duplicidade. Zero ambiguidade.**

> **Nota sobre `make init` existente**: o target atual no Makefile será **redefinido** — em vez de inicializar o projeto, passará a exibir uma mensagem direcionando para `scaffold.py`. Isso preserva o hábito de quem digita `make init` sem duplicar lógica.

---

### Tensão 3: Onde criar o novo projeto — dentro do template ou em outro diretório?

| Perspectiva | Posição |
|-------------|---------|
| **PM** | "Precisa ser claro para o usuário. O script deve perguntar ou ter um padrão óbvio." |
| **Developer** | "O `manage.py` existente opera no seu próprio ROOT. O novo scaffold.py deve ter um `target_dir` configurável." |
| **Feature Eng.** | "Dois casos de uso distintos: (A) inicializar o repo ATUAL como projeto novo; (B) criar pasta nova em outro diretório. O scaffold.py deve suportar ambos." |
| **Spec Eng.** | "O contrato é: se `--target-dir` não informado, inicializa no `cwd`. Se informado, cria o projeto lá." |

**Resolução**: ✅ **Padrão: inicializa o diretório atual (`cwd`). Flag `--target-dir [path]` para criar em outro local.**

---

### Tensão 4: Automação vs. Interatividade

| Perspectiva | Posição |
|-------------|---------|
| **PM** | "CI/CD não pode travar esperando `input()`. O script deve ter modo não-interativo." |
| **Developer** | "`argparse` com todos os campos como flags + modo `--interactive` (padrão). Se todos os args fornecidos, pula os prompts." |
| **Feature Eng.** | "Modo `--ci` com valores obrigatórios por argumento. Falha clara se campo obrigatório não fornecido em modo CI." |
| **Spec Eng.** | "Definir campos obrigatórios vs. opcionais. Obrigatórios em modo CI: `--name`, `--domain`, `--language`. Opcionais: `--repo`, `--shared-dir`, `--title`, `--description`." |

**Resolução**: ✅ **Modo interativo (padrão) + modo CI via flags. `--ci` flag torna todos os campos opcionais resolvidos por defaults se não fornecidos.**

---

## ✅ Consenso Final do Debate

### O que IMP-01 entrega (MVP — Fase 1)

1. **`scripts/scaffold.py`** — entry point com `argparse` + modo interativo padrão
2. **`scripts/lib/config.py`** — `ProjectConfig` dataclass + constantes
3. **`scripts/lib/ui.py`** — prompts com `Rich` + validação inline
4. **`scripts/lib/project.py`** — criação de estrutura de pastas + substituição de placeholders
5. **`scripts/lib/links.py`** — setup + check de symlinks `.copilot-*`
6. **`scripts/lib/git.py`** — `git init` + `git remote add`
7. **`scripts/lib/templates.py`** — geração de `.copilot-rules-[projeto].md`
8. **Redefinir `make init` no Makefile** — de lógica de init para mensagem: *"Use: uv run scripts/scaffold.py"*

**Separação de domínios (decisão final)**:
- `scaffold.py` = dono do scaffolding e ciclo de vida do projeto
- `Makefile` = dono do build/test/CI — sem lógica de inicialização

### O que NÃO está no MVP (Fase 2+)

- TUI com Textual (visual interativo, navegação por teclado) — **P3**
- Integração com `gh` CLI para criar repositório no GitHub — **P3**
- Integração com MCP `memory` server — **P3**
- Suporte a múltiplos projetos simultâneos — **fora do escopo**

---

## 📋 Próximos Passos

| Ação | Responsável (papel) | Próximo arquivo |
|------|--------------------|----|
| Gerar spec técnica detalhada (IMP-01-SPEC.md) | Spec Engineer | [IMP-01-SPEC.md](IMP-01-SPEC.md) |
| Gerar user stories (IMP-01-USER-STORIES.md) | Feature Engineer | [IMP-01-USER-STORIES.md](IMP-01-USER-STORIES.md) |
| Implementar `scripts/lib/` + `scaffold.py` | Developer | `scripts/scaffold.py` (novo) |
| Atualizar `Makefile` target `init` | Developer | `Makefile` |

---

*Arquivo gerado em 2026-02-28 | Sessão: [DAILY_ACTIVITIES_2026-02-28.md](DAILY_ACTIVITIES_2026-02-28.md)*
