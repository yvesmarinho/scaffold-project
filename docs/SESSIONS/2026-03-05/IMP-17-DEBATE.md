# 🎭 IMP-17 — Debate: Issue Templates + Script MCP + VS Code Perfil/Workspace

**Data**: 2026-03-05
**Projeto**: Enterprise Scaffold Project Template
**Issue**: IMP-17 — GitHub Issue Templates · Script de carga do MCP · Geração de perfil e workspace VS Code
**Status**: 🔵 Em debate — D-26..D-34 abertas
**Referência anterior**: [IMP-14-DEBATE.md](IMP-14-DEBATE.md) | [TODO.md](../../TODO.md)

---

## 🧭 Contexto

### Três Gaps Identificados após IMP-14 Fase A

Com a conclusão da Fase A do IMP-14 (SpecKit no projeto filho + novos perfis), três lacunas
operacionais permaneceram sem solução:

#### Gap G1 — Sem Issue Templates

O template gera um repositório GitHub funcional, mas sem `.github/ISSUE_TEMPLATE/`. Qualquer Issue
aberta no repositório filho é texto livre, sem estrutura. Resultado: reports de bug com informações
insuficientes, pedidos de feature sem contexto de decisão.

O template **em si** (scaffold-project) também não tem Issue Templates — as IMPs são gerenciadas
manualmente em arquivos Markdown de sessão.

#### Gap G2 — MCP precisa de configuração manual de ambiente

O scaffold gera `.vscode/mcp.json` com os servidores corretos para o domínio, mas servidores que
precisam de tokens (`github`, `brave-search`) obrigam o desenvolvedor a configurar variáveis de
ambiente manualmente em cada sessão. Não existe um `load-mcp.sh` que:
- Carregue `.secrets/.env` antes de abrir o VS Code
- Valide que os tokens necessários estão presentes
- Informe quais variáveis faltam, com exemplo

#### Gap G3 — VS Code incompleto no projeto filho

O scaffold gera `settings.json`, `mcp.json`, `extensions.json` e `[nome].code-workspace`, mas:
- **`launch.json`** (configurações de debug) está ausente
- **`tasks.json`** (tarefas do VS Code) está ausente — os alvos do `Makefile` ficam
  invisíveis no Command Palette sem isso
- **`.code-profile`** (perfil exportável do VS Code) não é gerado — desenvolvedores em times
  precisam importar o mesmo perfil para ter ambiente consistente de extensões + configurações
- O arquivo `.code-workspace` gerado tem conteúdo mínimo — sem `tasks`, `launch`, ou
  `settings` de workspace-level úteis

---

## 🎭 Debate — Quatro Perspectivas

---

### 🏢 1. PROJECT MANAGER — Escopo, Prioridade, Riscos

#### 📌 Posição: "Tratar os três gaps em uma única IMP por coesão, mas com fases separadas"

**Análise de valor vs. esforço**:

| Entrega | Valor | Esforço | Prioridade |
|---------|-------|---------|------------|
| Issue Templates (`bug_report`, `feature_request`) | 🟠 Alto | Baixo | P1 |
| `load-mcp.sh` — carrega `.secrets/.env` e valida tokens | 🔴 Crítico | Baixo | P0 |
| `tasks.json` gerado pelo scaffold (alvos Makefile) | 🔴 Crítico | Médio | P0 |
| `launch.json` gerado pelo scaffold (debug por linguagem) | 🟠 Alto | Médio | P1 |
| `.code-profile` exportável | 🟡 Médio | Alto | P2 |
| Enriquecimento do `.code-workspace` | 🟠 Alto | Baixo | P1 |

**Riscos**:
- 🔴 **R1**: `load-mcp.sh` com lógica de carregamento de segredos pode expor tokens se
  logado ou incluído no histórico do terminal — precisa de tratamento explícito
- 🟠 **R2**: `launch.json` genérico demais pode não servir ao projeto filho — acoplamento excessivo
  com a stack escolhida
- 🟡 **R3**: `.code-profile` muda com frequência conforme extensões evoluem — arquivo gerado pelo
  scaffold fica obsoleto rapidamente

**Proposta de fases**:
```
Fase A (P0): load-mcp.sh + tasks.json  ← resolve os blocos diários imediatos
Fase B (P1): Issue Templates + launch.json + .code-workspace enriquecido
Fase C (P2): .code-profile exportável (baixa prioridade — alta volatilidade)
```

---

### 👨‍💻 2. DEVELOPER / ARQUITETO — Arquitetura Técnica

#### 📌 Posição: "Gerar dinamicamente a partir de `mcp.json` e `Makefile` — não templates hardcodados"

**Análise técnica dos três gaps**:

**Gap G1 — Issue Templates**

GitHub suporta dois formatos:
```
Formato clássico (Markdown):
  .github/ISSUE_TEMPLATE/bug_report.md
  .github/ISSUE_TEMPLATE/feature_request.md

GitHub Issue Forms (YAML — mais estruturado):
  .github/ISSUE_TEMPLATE/bug_report.yml
  .github/ISSUE_TEMPLATE/feature_request.yml
  .github/ISSUE_TEMPLATE/config.yml          ← habilita/desabilita Issues livres
```

Issue Forms (YAML) são superiores para triagem estruturada mas têm maior complexidade de manutenção.
Para um template enterprise, a escolha impacta todos os projetos filhos.

Os templates devem ser **estáticos mais seguros de manter** — não gerados dinamicamente.
Devem ser copiados pelo `copy_speckit()` via padrão glob `ISSUE_TEMPLATE/*`.

**Gap G2 — Script MCP**

O script deve fazer exatamente 3 coisas:
1. Verificar se `.secrets/.env` existe — se não, criar e orientar o usuário
2. Carregar as variáveis (source) e validar que as obrigatórias não estão vazias
3. Imprimir o comando para abrir o VS Code já com o ambiente carregado

```bash
# Estrutura proposta: scripts/load-mcp.sh
#!/usr/bin/env bash
set -euo pipefail

SECRETS_ENV=".secrets/.env"

if [[ ! -f "$SECRETS_ENV" ]]; then
  echo "⚠️  .secrets/.env não encontrado."
  echo "   Crie o arquivo com os tokens necessários:"
  echo "   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_..."
  echo "   BRAVE_API_KEY=BSA..."
  exit 1
fi

# Carrega sem exportar direto para o ambiente do usuário
set -a; source "$SECRETS_ENV"; set +a

# Valida variáveis usadas em mcp.json
MISSING=()
# [injetado pelo scaffold com base nos servers do domínio]
[[ -z "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" ]] && MISSING+=("GITHUB_PERSONAL_ACCESS_TOKEN")

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo "❌ Variáveis obrigatórias ausentes em $SECRETS_ENV:"
  printf '   %s\n' "${MISSING[@]}"
  exit 1
fi

echo "✅ Ambiente MCP carregado. Execute:"
echo "   code ."
```

O script deve ser **gerado dinamicamente** pelo scaffold, com a lista de variáveis obrigatórias
derivada dos servidores selecionados para o domínio (que podem ter `"env"` em `mcp.json`).

**Gap G3 — VS Code Perfil e Workspace**

Três artefatos distintos, tratados separadamente:

```python
# lib/vscode.py — novas funções
def generate_tasks(config: ProjectConfig) -> CreatedItem:
    """Gera .vscode/tasks.json com os alvos do Makefile como tarefas VS Code."""

def generate_launch(config: ProjectConfig) -> CreatedItem:
    """Gera .vscode/launch.json com configs de debug por linguagem."""

def generate_workspace(config: ProjectConfig) -> CreatedItem:
    """Já existe como [name].code-workspace — enriquecer com tasks + launch section."""
```

O `.code-profile` deve ser tratado como **Fase C** — é um arquivo binário/JSON complexo que muda
conforme extensões evoluem. Alternativa mais robusta: documentar quais extensões usar e deixar o
VS Code sincronizar via profile link.

**Estrutura de `tasks.json` por domínio**:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "make: install-deps",
      "type": "shell",
      "command": "make install-deps",
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "make: dev",
      "type": "shell",
      "command": "make dev",
      "group": { "kind": "build", "isDefault": true },
      "problemMatcher": []
    },
    {
      "label": "make: test",
      "type": "shell",
      "command": "make test",
      "group": { "kind": "test", "isDefault": true },
      "problemMatcher": []
    },
    {
      "label": "make: lint",
      "type": "shell",
      "command": "make lint",
      "group": "test",
      "problemMatcher": []
    },
    {
      "label": "make: format",
      "type": "shell",
      "command": "make format",
      "group": "build",
      "problemMatcher": []
    }
  ]
}
```

**Estrutura de `launch.json` por linguagem**:

```json
// Python
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: módulo atual",
      "type": "debugpy",
      "request": "launch",
      "module": "${fileBasenameNoExtension}",
      "justMyCode": true
    },
    {
      "name": "Python: pytest",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["${workspaceFolder}/tests", "-v"],
      "justMyCode": false
    }
  ]
}
```

---

### 🔧 3. FEATURE ENGINEER — Funcionalidades e Casos de Uso

#### 📌 Posição: "Cada gap resolve um problema real e recorrente — os três têm usuários concretos"

**Casos de uso concretos**:

**F-13 — Issue Template: Bug Report**

```
QUEM: Qualquer colaborador do projeto filho
QUANDO: Encontra comportamento inesperado em produção ou dev
O QUÊ: Preenche template com: versão, passos para reproduzir, comportamento esperado vs. atual,
       logs relevantes, ambiente (OS, Python/Node version)
VALOR: Triagem 3x mais rápida — sem rondas de "me manda o log de erro"
```

**F-14 — Issue Template: Feature Request / Melhoria**

```
QUEM: PM, dev, ou stakeholder
QUANDO: Identifica lacuna funcional ou melhoria de DX
O QUÊ: Preenche template com: problema que resolve, proposta de solução, alternativas consideradas,
       impacto estimado, critérios de sucesso
VALOR: Issue já vem como mini-spec — pode ser direto para speckit.specify
```

**F-15 — Script `load-mcp.sh`**

```
QUEM: Desenvolvedor abrindo o projeto pela primeira vez (ou em nova máquina)
QUANDO: Antes de `code .` para garantir que os MCP servers vão funcionar
O QUÊ: Executa `./scripts/load-mcp.sh` — verifica .env, carrega, abre VS Code
VALOR: Elimina o problema de "MCP server github não funciona" por token ausente
```

**F-16 — `tasks.json` — Makefile visível no VS Code**

```
QUEM: Desenvolvedor usando VS Code
QUANDO: Quer rodar make test / make dev sem abrir terminal
O QUÊ: Command Palette → "Run Task" → lista os targets do Makefile
VALOR: DX — zero configuração adicional, build tasks mapeados automaticamente
```

**F-17 — `launch.json` — Debug configurado**

```
QUEM: Desenvolvedor depurando código
QUANDO: Precisa de breakpoint ou step-through
O QUÊ: F5 já abre a configuração correta (pytest / módulo / servidor)
VALOR: Elimina setup manual de debug — pronto no primeiro `git clone`
```

**F-18 — `.code-profile` — Ambiente consistente no time**

```
QUEM: Time de 2+ devs trabalhando no mesmo projeto
QUANDO: Onboarding de novo membro
O QUÊ: Importa `.vscode/[projeto].code-profile` — extensões + settings sincronizados
VALOR: Fim do "funciona na minha máquina" para extensões e formatters
```

---

### 📐 4. SPEC ENGINEER — Especificações e Contratos

#### 📌 Posição: "Definir os contratos antes de implementar — especialmente para o script MCP"

**Contratos de interface para as novas funções**:

```python
# lib/vscode.py — adições
def generate_tasks(config: ProjectConfig) -> CreatedItem:
    """
    Gera .vscode/tasks.json com os targets do Makefile como tasks VS Code.
    Tasks incluídas: install-deps, dev, build, test, lint, format, clean.
    Idempotente — skip se já existe.
    """

def generate_launch(config: ProjectConfig) -> CreatedItem:
    """
    Gera .vscode/launch.json com configurações de debug para config.language.
    Python: debugpy (módulo + pytest), TypeScript: js-debug (node + jest),
    Go: dlv (teste + execução direta), other: genérico (shell run).
    Idempotente — skip se já existe.
    """

# lib/project.py — adição
def generate_load_mcp(config: ProjectConfig) -> CreatedItem:
    """
    Gera scripts/load-mcp.sh dinamicamente com base nos servers do domínio.
    - Lê os servidores com campo "env" em vscode._ALL_MCP_SERVERS
    - Gera validação de cada variável de ambiente necessária
    - Inclui instrução de uso no cabeçalho do script
    - Torna executável (chmod +x via os.chmod)
    - Idempotente — skip se já existe.
    """
```

**Especificação dos Issue Templates**:

```
CAMINHO: .github/ISSUE_TEMPLATE/
FORMATO: Markdown clássico (não GitHub Forms YAML) — compatível com todos os planos GitHub
ARQUIVOS:
  bug_report.md      → reprodução + logs + ambiente
  feature_request.md → problema + proposta + alternativas + critério de sucesso
  config.yml         → desabilita Issues em branco (blank_issues_enabled: false)

CÓPIA pelo scaffold:
  - Adicionado ao glob de copy_speckit() → .github/ISSUE_TEMPLATE/*
  - Copiado para todo projeto filho (independe do domínio)
```

**Contratos de segurança do `load-mcp.sh`**:

```
NUNCA: echoar o valor do token na saída (apenas o nome da variável)
NUNCA: criar .secrets/.env com tokens de exemplo hardcodados
SEMPRE: usar `set -euo pipefail` no início
SEMPRE: verificar existência de .secrets/ antes de tentar criar
SEMPRE: sair com código != 0 se variáveis obrigatórias ausentes
RECOMENDADO: adicionar `#!/usr/bin/env bash` (portabilidade)
```

---

## 📊 Sumário de Features

| ID | Feature | Gap | Complexidade | Fase |
|----|---------|-----|-------------|------|
| F-13 | Issue Template: Bug Report | G1 | Baixa | B |
| F-14 | Issue Template: Feature Request | G1 | Baixa | B |
| F-15 | `scripts/load-mcp.sh` dinâmico | G2 | Média | A |
| F-16 | `.vscode/tasks.json` por domínio | G3 | Média | A |
| F-17 | `.vscode/launch.json` por linguagem | G3 | Média | B |
| F-18 | `.code-profile` exportável | G3 | Alta | C |
| F-19 | `.code-workspace` enriquecido | G3 | Baixa | B |

---

## ❓ Decisões em Aberto

---

### D-26 — Formato dos Issue Templates: Markdown vs. GitHub Forms (YAML)?

**Contexto**: GitHub suporta dois formatos. Forms (YAML) têm campos estruturados e validação;
Markdown clássico é mais portável e editável diretamente.

| Opção | Prós | Contras |
|-------|------|---------|
| **A) Markdown clássico** | Suportado em todos os planos GitHub; editável sem saber YAML | Sem validação de campos; Issues livres precisam ser desabilitadas via config.yml separado |
| **B) GitHub Forms (YAML)** | Campos obrigatórios, dropdowns, checkboxes; triagem automática por labels | Requer plano pago para private repos em algumas features; curva de aprendizado |
| **C) Híbrido** | Markdown para bug + Forms para feature_request | Inconsistência de experiência |

**Sugestão do developer**: Opção **A (Markdown)** — universal, sem dependência de features pagas,
editável por qualquer contribuinte sem conhecer a spec de Forms.

**→ Sua decisão**: ___

---

### D-27 — Quais templates criar? (além de bug_report e feature_request)

**Contexto**: O template serve projetos enterprise. Pode fazer sentido incluir templates adicionais.

| Templates candidatos | Valor |
|----------------------|-------|
| `bug_report.md` | ✅ Essencial |
| `feature_request.md` | ✅ Essencial |
| `improvement.md` (melhoria técnica: refatoração, dívida técnica) | 🟠 Recomendado |
| `task.md` (tarefa operacional: upgrade de dependência, update de doc) | 🟡 Opcional |
| `security.md` (reporte de vulnerabilidade — pode ser SECURITY.md na raiz) | 🟡 Considerar |

**→ Sua decisão**: ___

---

### D-28 — Os Issue Templates devem ser copiados para o projeto filho?

**Opções**:
- **A) Sim** — copiados pelo `copy_speckit()` como `.github/ISSUE_TEMPLATE/*`
  (filho herda os templates automaticamente)
- **B) Não** — apenas no template-meta; projetos filhos mantêm os seus
- **C) Opcional** — pergunta `[9]` no fluxo scaffold: "Incluir Issue Templates?"

**→ Sua decisão**: ___

---

### D-29 — O que o `load-mcp.sh` deve fazer além de carregar `.env`?

**Opções**:
- **A) Minimal** — apenas `source .secrets/.env` + validar vars obrigatórias + imprimir `code .`
- **B) Standard** — A + verificar se `npx` e `node` estão instalados
- **C) Full** — A+B + verificar conectividade dos servers (`npx --yes @modelcontextprotocol/...`)
- **D) Full + auto-open** — A+B+C + executar `code .` automaticamente ao final

**Sugestão do developer**: Opção **B (Standard)** — valida dependências sem ser invasivo.

**→ Sua decisão**: ___

---

### D-30 — Onde vive o `load-mcp.sh`?

| Localização | Prós | Contras |
|-------------|------|---------|
| `scripts/load-mcp.sh` | Junto com scripts do projeto; documentado no README | Requer `chmod +x` explícito; mistura com scripts de build |
| `.vscode/load-mcp.sh` | Coeso com config VS Code | Pasta `.vscode` normalmente só JSON; menos convencional |
| `Makefile: target mcp` | `make mcp` — ergonomia; sem chmod; já no PATH | Depende de `make` estar instalado |

**Sugestão do developer**: `scripts/load-mcp.sh` como arquivo primário **e** `make mcp` como
alias no Makefile gerado pelo scaffold — melhor ergonomia para os dois perfis de usuário.

**→ Sua decisão**: ___

---

### D-31 — O `load-mcp.sh` é gerado dinamicamente ou é um template estático?

**Opções**:
- **A) Template estático** — copiado do template pelo `copy_speckit()` — mesma lógica para
  todos os projetos; lista de vars hardcodada
- **B) Gerado dinamicamente** — `generate_load_mcp(cfg)` em `project.py` lê os servidores
  do domínio em `_MCP_BY_DOMAIN` e injeta apenas as vars necessárias para aquele projeto
- **C) Template + customização** — template base copiado; seção `# VARS OBRIGATÓRIAS` gerada
  dinamicamente pelo scaffold e inserida no arquivo

**Sugestão do developer**: Opção **B (dinâmico)** — um projeto `analysis` não precisa de
`GITHUB_PERSONAL_ACCESS_TOKEN`; gerar só as vars relevantes elimina falsos erros de configuração.

**→ Sua decisão**: ___

---

### D-32 — O que incluir no `.vscode/tasks.json`?

**Opções**:
- **A) Minimal** — apenas `make dev` e `make test`
- **B) Standard** — todos os targets de uso frequente: `install-deps`, `dev`, `build`, `test`,
  `lint`, `format`, `clean`
- **C) Standard + domínio** — B + tasks específicas por domínio (ex: para `infrastructure`:
  `terraform plan`, `helm lint`; para `analysis`: `jupyter notebook`)

**Sugestão do developer**: Opção **B (Standard)** para Fase A; C pode ser adicionado em Fase B
sem breaking changes.

**→ Sua decisão**: ___

---

### D-33 — Incluir `launch.json` gerado pelo scaffold?

**Contexto**: `launch.json` tem forte dependência da estrutura do projeto filho
(onde fica o `main.py`? qual é o entry point?). Um genérico pode ser mais confuso que útil.

**Opções**:
- **A) Sim, genérico por linguagem** — Python: `debugpy` para arquivo atual + pytest;
  TypeScript: `js-debug` para arquivo atual + jest; Go: `dlv` genérico
- **B) Não** — documentar no README como configurar; lançar como IMP-16 junto com testes
- **C) Sim, mas como exemplo** — gerar como `.vscode/launch.json.example` para não interferir
  com configurações existentes

**Sugestão do developer**: Opção **A** — um `launch.json` genérico por linguagem é melhor que
nada e não conflita com customizações específicas do projeto (raro ter `launch.json` pré-existente
em repositório novo).

**→ Sua decisão**: ___

---

### D-34 — Gerar `.code-profile` exportável?

**Contexto**: Perfil VS Code inclui extensões, settings, snippets, keybindings. Muda ao longo do
tempo. Gerar um arquivo estático que fica obsoleto pode ser pior que não ter.

**Opções**:
- **A) Sim, gerar `.vscode/[projeto].code-profile`** — snapshot do ambiente no momento do scaffold
- **B) Não, documentar** — seção no README sobre como importar o perfil via VS Code Settings Sync
  ou profile export manual
- **C) Link de perfil** — gerar URL de importação de perfil VS Code (feature experimental) que
  aponta para o `extensions.json` já gerado

**Sugestão do developer**: Opção **B (documentar)** para Fase A — `.code-profile` é independente
das outras entregas e tem alto custo de manutenção. Fase C pode revisitar se houver demanda.

**→ Sua decisão**: ___

---

## 🗂️ Sub-tarefas — Mapa de Implementação

### Fase A — P0 (resolver blocos diários imediatos)

| ID | Tarefa | Arquivo | Depende de |
|----|--------|---------|-----------|
| A.1 | Criar `.github/ISSUE_TEMPLATE/bug_report.md` | `.github/ISSUE_TEMPLATE/` | D-26, D-27 |
| A.2 | Criar `.github/ISSUE_TEMPLATE/feature_request.md` | `.github/ISSUE_TEMPLATE/` | D-26, D-27 |
| A.3 | Criar `.github/ISSUE_TEMPLATE/improvement.md` | `.github/ISSUE_TEMPLATE/` | D-27 |
| A.4 | Criar `.github/ISSUE_TEMPLATE/config.yml` | `.github/ISSUE_TEMPLATE/` | D-26 |
| A.5 | Implementar `generate_load_mcp(cfg)` em `project.py` | `scripts/lib/project.py` | D-29, D-30, D-31 |
| A.6 | Implementar `generate_tasks(cfg)` em `vscode.py` | `scripts/lib/vscode.py` | D-32 |
| A.7 | Integrar A.5 + A.6 em `scaffold.py` (passos 7+8) | `scripts/scaffold.py` | A.5, A.6 |
| A.8 | Adicionar target `mcp` no `_MAKEFILE` template de `project.py` | `scripts/lib/project.py` | D-30 |
| A.9 | Atualizar `copy_speckit()` para incluir `ISSUE_TEMPLATE/*` | `scripts/lib/project.py` | D-28, A.1–A.4 |

### Fase B — P1

| ID | Tarefa | Arquivo | Depende de |
|----|--------|---------|-----------|
| B.1 | Implementar `generate_launch(cfg)` em `vscode.py` | `scripts/lib/vscode.py` | D-33 |
| B.2 | Enriquecer `_CODE_WORKSPACE` com `tasks` e `launch` sections | `scripts/lib/project.py` | B.1 |
| B.3 | Integrar B.1 em `scaffold.py` | `scripts/scaffold.py` | B.1 |

### Fase C — P2

| ID | Tarefa | Arquivo | Depende de |
|----|--------|---------|-----------|
| C.1 | Investigar e implementar `.code-profile` gerado | `scripts/lib/vscode.py` | D-34 |

---

## 🧩 SPEC — Pontos Críticos

### SPEC-11 — `load-mcp.sh` não vaza tokens

```bash
# ✅ CORRETO — apenas o nome da variável, não o valor
echo "❌ Variáveis ausentes: GITHUB_PERSONAL_ACCESS_TOKEN"

# ❌ PROIBIDO — vaza o token no terminal
echo "Token atual: $GITHUB_PERSONAL_ACCESS_TOKEN"
```

### SPEC-12 — `tasks.json` com labels humanamente legíveis

Tasks devem aparecer no Command Palette com nomes claros, não apenas `make test`.
Prefixo `make:` é o padrão:

```
"make: test" → executa make test → grupo test, isDefault: true
"make: dev"  → executa make dev  → grupo build, isDefault: true
```

### SPEC-13 — Issue Templates em português ou inglês?

O `scaffold-project` é bilíngue na prática (README em PT-BR, código em EN).
Issue Templates devem ser em **inglês** para maximizar colaboração e compatibilidade com
integrações (GitHub Actions, Copilot Workspace, issue parsers).

### SPEC-14 — `load-mcp.sh` deve ser idempotente

`generate_load_mcp()` segue o mesmo padrão de `copy_speckit()`:
- Verifica se `scripts/load-mcp.sh` já existe no destino
- Se sim → `status="skipped"` (não sobrescreve customizações do projeto filho)
- Se não → gera com as variáveis corretas para o domínio

---

*IMP-17 | Em debate | 2026-03-05 | Referência: IMP-14-DEBATE.md*
