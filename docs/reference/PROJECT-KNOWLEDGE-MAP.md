# 🗺️ Project Knowledge Map — Enterprise Scaffold Project Template

**Versão**: 1.1
**Gerado em**: 2026-03-01
**Atualizado em**: 2026-03-01
**Projeto**: `scaffold-project`
**Propósito**: Referência consolidada de funcionalidades, menus e estruturas para validação de conhecimento

---

## Índice

1. [Estrutura de Arquivos e Pastas](#1-estrutura-de-arquivos-e-pastas)
2. [Makefile — Menus e Comandos](#2-makefile--menus-e-comandos)
3. [scaffold.py — Funcionalidades e Menu Interativo](#3-scaffoldpy--funcionalidades-e-menu-interativo)
4. [Módulos `scripts/lib/` — Contratos e Responsabilidades](#4-módulos-scriptslib--contratos-e-responsabilidades)
5. [MCP — Configuração e Servidores](#5-mcp--configuração-e-servidores)
6. [Regras Copilot — `.copilot-rules.md`](#6-regras-copilot--copilot-rulesmd)
7. [Segurança e `.secrets/`](#7-segurança-e-secrets)
8. [IMPs — Rastreamento de Implementações](#8-imps--rastreamento-de-implementações)
9. [Convenções de Nomenclatura](#9-convenções-de-nomenclatura)
10. [Fluxo de Sessão de Trabalho](#10-fluxo-de-sessão-de-trabalho)

---

## 1. Estrutura de Arquivos e Pastas

### 1.1 Raiz do Projeto

```
scaffold-project/
├── .copilot-rules.md               ← Regras Copilot (único arquivo ativo, 193 linhas, 7 seções)
├── .gitignore                      ← Ignora .secrets/, *.key, *.pem, .env, etc.
├── .secrets/                       ← Arquivos sensíveis (git-ignored)
│   └── README.md                  ← Instruções de uso do diretório
├── .specify/                       ← Configuração SpecKit — NUNCA editar manualmente
│   ├── config.json
│   └── templates/
│       └── spec-template.md
├── .vscode/
│   ├── mcp.json                   ← Configuração dos servidores MCP
│   └── settings.json              ← Preferências do editor
├── scaffold-project.code-workspace ← Workspace VS Code
├── docs/                           ← Toda documentação humana
├── Makefile                        ← 40+ comandos de automação
├── README.md                       ← Documentação pública do template
└── scripts/                        ← Scripts de automação
    ├── scaffold.py                 ← [PENDENTE IMP-01] Entry point de scaffolding
    ├── manage.py                   ← Script legado (infra Ansible, referência)
    ├── init-new-project.sh         ← Shell script legado (a ser absorvido)
    ├── setup-project-links.sh      ← Shell script legado (a ser absorvido)
    ├── check-project-links.sh      ← Shell script legado (a ser absorvido)
    ├── lib/                        ← [PENDENTE IMP-01] Módulos Python
    │   ├── __init__.py
    │   ├── config.py
    │   ├── ui.py
    │   ├── project.py
    │   ├── links.py
    │   ├── git.py
    │   ├── templates.py
    │   └── vscode.py               ← Geração de settings.json, mcp.json, extensions.json
    ├── build/
    ├── deploy/
    └── setup/
```

### 1.2 Documentação (`docs/`)

```
docs/
├── INDEX.md                    ← Índice central do projeto (sempre atualizado)
├── TODO.md                     ← Lista de tarefas e IMPs
├── TODAY_ACTIVITIES.md         ← Atividades do dia atual
├── MAKEFILE.md                 ← Documentação dos comandos Makefile
├── TEMPLATE_USAGE.md           ← Guia de uso do template
├── PROJECT-KNOWLEDGE-MAP.md    ← Este arquivo
├── GitHub Copilot Recursos de Agents etc.md  ← Recursos gerais GitHub Copilot
├── copilot/
│   ├── DOMAIN-PROFILES-STRATEGY.md    ← Estratégia de Domain Profiles (3 camadas)
│   └── DOMAIN-PROFILES-DECISIONS.md  ← 19 decisões de design (D-01 a D-19)
└── SESSIONS/
    └── YYYY-MM-DD/             ← Pasta de cada sessão de trabalho
        ├── SESSION_RECOVERY_YYYY-MM-DD.md  ← Contexto para recuperação
        ├── DAILY_ACTIVITIES_YYYY-MM-DD.md  ← Atividades cronológicas
        ├── SESSION_REPORT_YYYY-MM-DD.md    ← Relatório da sessão
        └── FINAL_STATUS_YYYY-MM-DD.md      ← Estado final dos artefatos
```

### 1.3 Estrutura de Código Fonte (criada pelo scaffold.py)

```
[novo-projeto]/
├── src/
│   ├── core/
│   │   ├── models/         ← Entidades de domínio
│   │   ├── interfaces/     ← Contratos / ports
│   │   └── services/       ← Lógica de negócio
│   ├── data/
│   │   ├── repositories/   ← Acesso a dados (Repository Pattern)
│   │   ├── factories/      ← Criação de objetos (Factory Pattern)
│   │   └── migrations/     ← Migrações de banco
│   ├── presentation/
│   │   ├── views/          ← Camada de visualização (MVP)
│   │   ├── presenters/     ← Lógica de apresentação (MVP)
│   │   └── viewmodels/     ← Modelos de apresentação
│   ├── infrastructure/
│   │   ├── config/         ← Configurações do sistema
│   │   ├── logging/        ← Infraestrutura de logs
│   │   └── security/       ← Autenticação, autorização
│   └── shared/
│       ├── constants/
│       ├── helpers/
│       └── validators/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── config/
    ├── development.json
    ├── staging.json
    └── production.json
```

---

## 2. Makefile — Menus e Comandos

Execute `make help` para listar todos os targets disponíveis.

### 2.1 Inicialização e Estrutura

| Comando | Descrição |
|---------|-----------|
| `make help` | Lista todos os comandos disponíveis |
| `make init` | ⚠️ **[DEPRECATED]** Redireciona para `uv run scripts/scaffold.py` |
| `make structure` | Cria estrutura completa de diretórios |
| `make dirs` | Cria diretórios base (`.vscode/`, `.secrets/`) |
| `make github` | Cria `.github/workflows/` e `.github/ISSUE_TEMPLATE/` |
| `make specify` | Cria `.specify/specs/` |
| `make docs` | Cria `docs/architecture/`, `docs/api/`, `docs/guides/` |
| `make src` | Cria toda a hierarquia `src/` |
| `make tests` | Cria `tests/unit/`, `tests/integration/`, `tests/e2e/` |
| `make scripts` | Cria `scripts/setup/`, `scripts/build/`, `scripts/deploy/` |
| `make config` | Cria `config/` |
| `make docker` | Cria `docker/` |

### 2.2 Criação de Arquivos Base

| Comando | Arquivos Gerados |
|---------|-----------------|
| `make create-base-files` | Executa todos os targets abaixo |
| `make create-gitignore` | `.gitignore` (se não existe) |
| `make create-env-example` | `.env.example` com variáveis documentadas |
| `make create-editorconfig` | `.editorconfig` (UTF-8, 2/4 espaços, LF) |
| `make create-github-files` | `.github/workflows/ci.yml`, `PULL_REQUEST_TEMPLATE.md` |
| `make create-speckit-config` | `.specify/config.json` |
| `make create-docker-files` | `docker/Dockerfile`, `docker/docker-compose.yml` |
| `make create-config-files` | `config/development.json`, `staging.json`, `production.json` |
| `make create-readme-files` | READMEs em `src/core/`, `src/data/`, `src/presentation/`, `tests/` |

### 2.3 Setup de Linguagem

| Comando | Descrição | Arquivos Gerados |
|---------|-----------|-----------------|
| `make setup-python` | Configura projeto Python | `requirements.txt`, `requirements-dev.txt`, `setup.py` |
| `make setup-node` | Configura projeto Node.js/TS | `package.json`, `tsconfig.json` |
| `make install-deps` | Instala dependências | `npm install` ou `pip install -r requirements.txt` |

**Dependências Python padrão** (requirements.txt):
```
fastapi>=0.104.0, uvicorn>=0.24.0, pydantic>=2.5.0
pytest>=7.4.0, pytest-cov>=4.1.0, black>=23.11.0, flake8>=6.1.0, mypy>=1.7.0
```

**Scripts Node.js padrão** (package.json → scripts):
```json
"dev", "build", "start", "test", "test:watch", "test:coverage", "lint", "format"
```

### 2.4 Desenvolvimento

| Comando | Descrição |
|---------|-----------|
| `make dev` | Inicia servidor de desenvolvimento (`npm run dev` ou `uvicorn main:app --reload`) |
| `make build` | Build de produção (`npm run build` ou `python setup.py build`) |
| `make test` | Executa testes (`npm test` ou `pytest`) |
| `make lint` | Lint do código (`eslint src/**/*.ts` ou `flake8 src/`) |
| `make format` | Formata código (`prettier` ou `black src/`) |
| `make status` | Exibe estrutura do projeto e arquivos de configuração |

### 2.5 Docker

| Comando | Descrição |
|---------|-----------|
| `make docker-build` | `docker build -f docker/Dockerfile -t scaffold-project:latest .` |
| `make docker-up` | `docker-compose -f docker/docker-compose.yml up -d` |
| `make docker-down` | `docker-compose -f docker/docker-compose.yml down` |

### 2.6 Limpeza

| Comando | O que remove |
|---------|-------------|
| `make clean` | `dist/`, `build/`, `*.egg-info/`, `__pycache__/`, `.pytest_cache/`, `coverage/`, `node_modules/`, `*.pyc` |

### 2.7 Template Management

| Comando | Descrição |
|---------|-----------|
| `make init-new-project NAME=nome` | Cria novo projeto a partir do template (chama `init-new-project.sh`) |
| `make setup-shared-configs` | Cria `~/Documentos/DevOps/.copilot-shared/` com regras e scripts |
| `make setup-project-links` | Cria symlinks `.copilot-*` apontando para shared |
| `make check-project-links` | Verifica status dos symlinks |

**Estrutura do shared** (criada por `make setup-shared-configs`):
```
~/Documentos/DevOps/.copilot-shared/
├── rules/      ← .copilot-rules.md, .copilot-git-rules.md, etc.
├── scripts/    ← setup-project-links.sh, check-project-links.sh
├── templates/  ← Templates de projetos
└── docs/       ← Documentação compartilhada
```

---

## 3. `scaffold.py` — Funcionalidades e Menu Interativo

> **Status atual**: 📋 Especificado — NÃO implementado (IMP-01 pendente)
> **Executar com**: `uv run scripts/scaffold.py` ou `python scripts/scaffold.py`

### 3.1 Menu Principal (modo interativo)

```
┌──────────────────────────────────────────┐
│  🚀 Enterprise Project Scaffold v1.0.0   │
└──────────────────────────────────────────┘

  [1]  Novo Projeto
  [2]  Verificar Links (.copilot-*)
  [3]  Gerar .copilot-rules-[projeto].md
  [4]  Sair
```

### 3.2 Fluxo [1] — Novo Projeto

```
collect_project_info()
  ├── project_name     (kebab-case, obrigatório)
  ├── project_title    (legível, opcional → title-case do nome)
  ├── description      (1 frase, opcional)
  ├── domain           (programming | infrastructure | analysis)
  ├── language         (python | typescript | go | other)
  ├── github_repo      (URL ou Enter para pular)
  ├── shared_dir       (default: ~/Documentos/DevOps/.copilot-shared)
  └── target_dir       (default: diretório atual)

confirm_summary(config) → s/n

  ↓ confirmado
project.create_structure(config)         → cria pastas + arquivos base
links.setup_symlinks(config)             → cria symlinks .copilot-*
templates.generate_copilot_rules(config) → .copilot-rules-[nome].md
vscode.generate_settings(config)         → .vscode/settings.json (personalizado por linguagem)
vscode.generate_mcp(config)              → .vscode/mcp.json (servidores pré-selecionados por domínio)
vscode.generate_extensions(config)       → .vscode/extensions.json (extensões por domínio + linguagem)
git.init_repository(config)              → git init + git remote add

print_final_summary(results)             → tabela com status de cada operação
```

### 3.7 VS Code — Arquivos Gerados por Domínio

#### `.vscode/extensions.json` — Extensões por Categoria

**Base (todos os domínios e linguagens)**:

| ID da Extensão | Nome | Função |
|----------------|------|--------|
| `github.copilot` | GitHub Copilot | Autocompletar com IA |
| `github.copilot-chat` | GitHub Copilot Chat | Chat com IA no editor |
| `eamodio.gitlens` | GitLens | Histórico Git inline, blame, explorador |
| `mhutchie.git-graph` | Git Graph | Visualização gráfica de branches |
| `usernamehw.errorlens` | Error Lens | Erros e avisos inline na linha |
| `EditorConfig.EditorConfig` | EditorConfig | Aplica `.editorconfig` automaticamente |
| `streetsidesoftware.code-spell-checker` | Code Spell Checker | Correção ortográfica em código e docs |
| `yzhang.markdown-all-in-one` | Markdown All in One | Preview, atalhos, TOC automático |
| `christian-kohler.path-intellisense` | Path IntelliSense | Autocomplete de caminhos de arquivo |
| `donjayamanne.githistory` | Git History | Log e diff visual do Git |
| `ms-vscode.live-server` | Live Server | Live reload para HTML/JS |

**Domínio `programming` + linguagem `python`**:

| ID da Extensão | Nome | Função |
|----------------|------|--------|
| `ms-python.python` | Python | Suporte completo Python (run, debug, env) |
| `ms-python.pylance` | Pylance | Language server: IntelliSense, type checking |
| `ms-python.black-formatter` | Black Formatter | Formatter automático (PEP 8) |
| `ms-python.flake8` | Flake8 | Linter de estilo e erros |
| `ms-python.mypy-type-checker` | Mypy | Type checker estático |
| `ms-python.debugpy` | Debugpy | Debugger Python com breakpoints |
| `njpwerner.autodocstring` | autoDocstring | Geração automática de docstrings |
| `ms-python.isort` | isort | Ordenação automática de imports |
| `KevinRose.vsc-python-indent` | Python Indent | Indentação inteligente Python |

**Domínio `programming` + linguagem `typescript`**:

| ID da Extensão | Nome | Função |
|----------------|------|--------|
| `dbaeumer.vscode-eslint` | ESLint | Linter JS/TS |
| `esbenp.prettier-vscode` | Prettier | Formatter JS/TS/JSON/CSS/MD |
| `ms-vscode.vscode-typescript-next` | TypeScript Next | TypeScript mais recente |
| `orta.vscode-jest` | Jest | Runner e debug de testes Jest |
| `bradlc.vscode-tailwindcss` | Tailwind CSS IntelliSense | Autocomplete Tailwind (se aplicável) |
| `ms-vscode.js-debug` | JS Debugger | Debugger nativo Node.js/Chrome |

**Domínio `infrastructure`**:

| ID da Extensão | Nome | Função |
|----------------|------|--------|
| `ms-azuretools.vscode-docker` | Docker | Gerenciar imagens, containers, registries |
| `p1c2u.docker-compose` | Docker Compose | Syntax highlight e autocomplete `docker-compose.yml` |
| `exiasr.hadolint` | Hadolint | Linter para `Dockerfile` (boas práticas) |
| `ms-vscode-remote.remote-containers` | Dev Containers | Abrir projeto dentro de container |
| `ms-vscode-remote.remote-ssh` | Remote SSH | Desenvolvimento em servidor remoto via SSH |
| `HashiCorp.terraform` | Terraform | Syntax, autocomplete, linting HCL |
| `redhat.vscode-yaml` | YAML | Validação YAML com schema (k8s, docker-compose, CI) |
| `ms-kubernetes-tools.vscode-kubernetes-tools` | Kubernetes | Explorador de cluster, manifests, helm |
| `tim-koehler.helm-intellisense` | Helm IntelliSense | Autocomplete para charts Helm |
| `signageos.signageos-vscode-sops` | SOPS | Edição de secrets criptografados com SOPS |
| `fcrespo82.mac-night-owl` | Ansible | (usar `redhat.ansible`) Suporte a playbooks Ansible |
| `redhat.ansible` | Ansible | Syntax, autocomplete, linting playbooks Ansible |

**Domínio `analysis`**:

| ID da Extensão | Nome | Função |
|----------------|------|--------|
| `ms-toolsai.jupyter` | Jupyter | Notebooks Jupyter no VS Code |
| `ms-toolsai.vscode-jupyter-slideshow` | Jupyter Slideshow | Apresentações a partir de notebooks |
| `ms-toolsai.jupyter-keymap` | Jupyter Keymap | Atalhos de teclado do Jupyter |
| `mechatroner.rainbow-csv` | Rainbow CSV | Visualização colorida de arquivos CSV |
| `GrapeCity.gc-excelviewer` | Excel Viewer | Visualizar `.csv` e `.xlsx` como tabela |
| `ms-python.python` | Python | (inclui os mesmos da stack Python acima) |

#### `.vscode/settings.json` — Configurações por Linguagem

**Python**:
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "editor.defaultFormatter": "ms-python.black-formatter",
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.analysis.typeCheckingMode": "basic",
  "editor.rulers": [88],
  "isort.args": ["--profile", "black"]
}
```

**TypeScript**:
```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": { "source.fixAll.eslint": true },
  "typescript.preferences.importModuleSpecifier": "relative",
  "editor.rulers": [100]
}
```

**Infrastructure**:
```json
{
  "editor.defaultFormatter": "redhat.vscode-yaml",
  "editor.formatOnSave": true,
  "yaml.schemas": {
    "https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json": "docker-compose*.yml"
  },
  "docker.showStartPage": false,
  "editor.rulers": [120]
}
```

#### `.vscode/mcp.json` — Servidores Pré-selecionados por Domínio

| Domínio | Servidores ativos por padrão |
|---------|-----------------------------|
| `programming` | `memory`, `sequential-thinking`, `filesystem`, `github` |
| `infrastructure` | `memory`, `sequential-thinking`, `filesystem`, `github`, `sqlite` |
| `analysis` | `memory`, `sequential-thinking`, `filesystem`, `sqlite`, `brave-search` |

---

### 3.3 Fluxo [2] — Verificar Links

```
links.check_symlinks(target_dir, shared_dir)
  └── Para cada .copilot-* em SHARED_COPILOT_FILES:
        ✅ ok      → symlink existe e aponta para arquivo real
        ⚠️  broken → symlink existe mas target não existe
        ❌ missing → symlink não existe
```

### 3.4 Fluxo [3] — Gerar Regras Copilot

```
templates.generate_copilot_rules(config)
  └── Gera: .copilot-rules-[project_name].md
      Conteúdo: identidade, domain profile ativo, estrutura, regras específicas
      Comportamento: não sobrescreve se já existe (status: skipped)
```

### 3.5 Interface CLI (flags)

```bash
scaffold.py [opções]

Flags de ação:
  --new              Pula menu, entra direto no fluxo de novo projeto
  --check            Verifica symlinks e sai (sem menu)

Flags de modo:
  --ci               Modo não-interativo — usa args, sem prompts

Campos (usados com --ci):
  --name NAME        Nome kebab-case (obrigatório em --ci)
  --title TITLE      Título legível
  --description DESC Descrição breve
  --domain           programming | infrastructure | analysis
  --language         python | typescript | go | other
  --repo REPO        URL GitHub
  --shared-dir PATH  Caminho para .copilot-shared
  --target-dir PATH  Onde criar o projeto (default: cwd)
```

**Exemplo CI/CD**:
```bash
uv run scripts/scaffold.py --ci \
  --name my-api-v2 \
  --domain programming \
  --language python \
  --repo https://github.com/org/my-api-v2
```

### 3.6 Comportamento de Erros

| Situação | Comportamento | Exit |
|----------|--------------|------|
| `shared_dir` não existe | Aviso amarelo, prossegue sem symlinks | 0 |
| `project_name` inválido (interativo) | Repede o campo | retry |
| `project_name` inválido (`--ci`) | Erro vermelho | 1 |
| `git` não no PATH | Aviso amarelo, pula etapa Git | 0 |
| Pasta já existe | Aviso amarelo, mantém existente | 0 |
| Erro de permissão | Erro vermelho, para execução | 1 |
| `CTRL+C` | "Cancelado" — saída limpa | 130 |

---

## 4. Módulos `scripts/lib/` — Contratos e Responsabilidades

### 4.1 `config.py` — Dados e Constantes

```python
# Caminho padrão para shared
DEFAULT_SHARED_DIR = Path.home() / "Documentos" / "DevOps" / ".copilot-shared"

# Arquivos copilot gerenciados (pós IMP-13: apenas 1 arquivo ativo)
SHARED_COPILOT_FILES = [".copilot-rules.md"]

# Tipos
DomainType  = Literal["programming", "infrastructure", "analysis"]
LanguageType = Literal["python", "typescript", "go", "other"]

# Dataclasses
ProjectConfig   → campos do projeto (nome, domínio, linguagem, paths...)
CreatedItem     → resultado de criação (path, kind, status, message)
LinkStatus      → resultado de check de symlink (name, target, status)
```

### 4.2 `ui.py` — Interface com Usuário (Rich)

| Função | Responsabilidade |
|--------|-----------------|
| `show_banner()` | Banner Rich com nome + versão |
| `show_menu()` | Menu principal, retorna `'1'`–`'4'` |
| `collect_project_info(ci_mode, **overrides)` | Coleta dados via prompts ou args |
| `confirm_summary(config)` | Exibe resumo, pede confirmação s/n |
| `print_final_summary(items)` | Tabela Rich com status de cada item |

**Campos obrigatórios** (falham em `--ci` se ausentes): `project_name`, `domain`, `language`
**Campos com defaults em `--ci`**: `project_title` (title-case), `description` (`""`), `github_repo` (`None`), `shared_dir`, `target_dir` (`cwd`)

### 4.3 `project.py` — Criação de Estrutura

| Função | Responsabilidade |
|--------|-----------------|
| `create_structure(config)` | Cria pastas + arquivos base; retorna `list[CreatedItem]` |

**Pastas criadas**: `docs/`, `docs/SESSIONS/`, `docs/copilot/`, `.github/agents/`, `.github/prompts/domain/`, `.secrets/`, `.vscode/`, `scripts/lib/`, `src/`

**Arquivos criados** (de templates internos com placeholders substituídos):
`README.md`, `docs/INDEX.md`, `docs/TODO.md`, `docs/TODAY_ACTIVITIES.md`, `.gitignore`, `.secrets/README.md`, `.vscode/mcp.json`, `.vscode/settings.json`, `Makefile`, `[nome].code-workspace`

**Placeholders**:

| Placeholder | Valor |
|-------------|-------|
| `{{PROJECT_NAME}}` | `config.project_name` |
| `{{PROJECT_TITLE}}` | `config.project_title` |
| `{{PROJECT_DESCRIPTION}}` | `config.description` |
| `{{CREATED_AT}}` | `config.created_at` (ISO8601) |
| `{{DOMAIN}}` | `config.domain` |
| `{{LANGUAGE}}` | `config.language` |
| `{{GITHUB_REPO}}` | `config.github_repo or ''` |

### 4.4 `links.py` — Gestão de Symlinks

| Função | Responsabilidade |
|--------|-----------------|
| `setup_symlinks(config)` | Cria symlinks relativos `.copilot-*` de shared → target |
| `check_symlinks(target_dir, shared_dir)` | Retorna `list[LinkStatus]` com ok/broken/missing |

**Comportamento de setup**:
- shared_dir não existe → aviso, skipa todos
- arquivo ausente no shared_dir → aviso, skipa esse
- symlink ok existente → skipped
- symlink quebrado → recria
- não existe → cria (symlink RELATIVO para portabilidade)

### 4.5 `git.py` — Repositório Git

| Função | Responsabilidade |
|--------|-----------------|
| `init_repository(config)` | `git init`; `git remote add origin` se URL fornecida |
| `is_git_repo(path)` | `True` se `.git/` existe no path |

**Não falha** se `.git/` já existe — reporta `skipped`. Usa `subprocess` com `check=True` e `timeout=30s`.

### 4.6 `templates.py` — Geração de Arquivos Copilot

| Função | Responsabilidade |
|--------|-----------------|
| `generate_copilot_rules(config)` | Gera `.copilot-rules-[projeto].md` em `target_dir` |

**Domain map**:
```python
{"programming": "devops-programming",
 "infrastructure": "devops-infrastructure",
 "analysis": "devops-analysis"}
```

---
### 4.7 `vscode.py` — Configuração VS Code por Domínio/Linguagem

| Função | Responsabilidade |
|--------|------------------|
| `generate_settings(config)` | Gera `.vscode/settings.json` personalizado por linguagem |
| `generate_mcp(config)` | Gera `.vscode/mcp.json` com servidores pré-selecionados por domínio |
| `generate_extensions(config)` | Gera `.vscode/extensions.json` com extensões por domínio + linguagem |

**Lógica de seleção de extensões**:
```python
def generate_extensions(config: ProjectConfig) -> CreatedItem:
    """
    Combina extensões de 3 camadas:
    1. BASE_EXTENSIONS      → sempre incluídas (copilot, gitlens, errorlens, ...)
    2. DOMAIN_EXTENSIONS    → por domínio (programming / infrastructure / analysis)
    3. LANGUAGE_EXTENSIONS  → por linguagem (python / typescript / go / other)

    Resultado: .vscode/extensions.json com lista deduplicada e ordenada.
    Não sobrescreve se já existe → status: skipped.
    """
```

**Constantes**:
```python
BASE_EXTENSIONS = [
    "github.copilot", "github.copilot-chat", "eamodio.gitlens",
    "mhutchie.git-graph", "usernamehw.errorlens", "EditorConfig.EditorConfig",
    "streetsidesoftware.code-spell-checker", "yzhang.markdown-all-in-one",
    "christian-kohler.path-intellisense", "donjayamanne.githistory",
]

DOMAIN_EXTENSIONS: dict[DomainType, list[str]] = {
    "programming":    [],   # linguagem define os extras
    "infrastructure": [
        "ms-azuretools.vscode-docker",        # Docker: imagens, containers, registries
        "p1c2u.docker-compose",               # Docker Compose: syntax + autocomplete
        "exiasr.hadolint",                    # Dockerfile linter
        "ms-vscode-remote.remote-containers", # Dev Containers
        "ms-vscode-remote.remote-ssh",        # Remote SSH
        "HashiCorp.terraform",                # Terraform HCL
        "redhat.vscode-yaml",                 # YAML + schema validation
        "ms-kubernetes-tools.vscode-kubernetes-tools",  # Kubernetes
        "tim-koehler.helm-intellisense",      # Helm charts
        "redhat.ansible",                     # Ansible playbooks
        "signageos.signageos-vscode-sops",    # SOPS secrets
    ],
    "analysis": [
        "ms-toolsai.jupyter",
        "ms-toolsai.vscode-jupyter-slideshow",
        "ms-toolsai.jupyter-keymap",
        "mechatroner.rainbow-csv",
        "GrapeCity.gc-excelviewer",
    ],
}

LANGUAGE_EXTENSIONS: dict[LanguageType, list[str]] = {
    "python": [
        "ms-python.python", "ms-python.pylance", "ms-python.black-formatter",
        "ms-python.flake8", "ms-python.mypy-type-checker", "ms-python.debugpy",
        "njpwerner.autodocstring", "ms-python.isort", "KevinRose.vsc-python-indent",
    ],
    "typescript": [
        "dbaeumer.vscode-eslint", "esbenp.prettier-vscode",
        "ms-vscode.vscode-typescript-next", "orta.vscode-jest",
        "bradlc.vscode-tailwindcss", "ms-vscode.js-debug",
    ],
    "go": ["golang.go"],
    "other": [],
}
```

---
## 5. MCP — Configuração e Servidores

**Arquivo**: `.vscode/mcp.json`

### 5.1 Servidores Disponíveis

| Servidor | Função | Dependência |
|----------|--------|-------------|
| `memory` | Memória persistente entre sessões | `npx @modelcontextprotocol/server-memory` |
| `sequential-thinking` | Raciocínio estruturado em etapas | `npx @modelcontextprotocol/server-sequential-thinking` |
| `filesystem` | Leitura/escrita de arquivos com escopo | `npx @modelcontextprotocol/server-filesystem` |
| `github` | Issues, PRs, code search | `npx @modelcontextprotocol/server-github` + `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `sqlite` | Query SQLite local | `npx @modelcontextprotocol/server-sqlite` |
| `brave-search` | Busca web | `npx @modelcontextprotocol/server-brave-search` + `BRAVE_API_KEY` |
| `postgres` | Query PostgreSQL | URL de conexão |
| `puppeteer` | Scraping Web / browser automation | `npx @modelcontextprotocol/server-puppeteer` |

### 5.2 Ativar um Servidor MCP

1. Descomente o bloco do servidor em `.vscode/mcp.json`
2. Configure variáveis de ambiente em `.secrets/.env`
3. Command Palette → **"MCP: Refresh Servers"**

> ⚠️ **NUNCA** armazenar credenciais no `mcp.json`. Usar `${env:VARIAVEL}` ou `.secrets/`.

---

## 6. Regras Copilot — `.copilot-rules.md`

Arquivo único ativo desde IMP-13 (193 linhas, 7 seções).

### 6.1 Seção 1 — Ferramentas de Arquivo (P0 CRÍTICO)

| ❌ Proibido | ✅ Obrigatório |
|------------|--------------|
| `cat > arquivo << 'EOF'` | `create_file` (novo arquivo) |
| `echo "x" >> arquivo` | `replace_string_in_file` (editar existente) |
| `echo "x" \| tee arquivo` | `multi_replace_string_in_file` (múltiplas edições) |

### 6.2 Seção 2 — Ferramentas Nativas VS Code (P0 CRÍTICO)

| Operação | ❌ CLI Proibido | ✅ Ferramenta |
|----------|---------------|--------------|
| Ler arquivo | `cat arquivo` | `read_file` |
| Buscar texto | `grep -rn` | `grep_search` |
| Encontrar arquivos | `find . -name` | `file_search` |
| Busca semântica | `grep -r "conceito"` | `semantic_search` |
| Listar diretório | `ls -la` | `list_dir` |
| Verificar erros | `python -m py_compile` | `get_errors` |

`run_in_terminal` **permitido apenas para**: `git`, `make`, `pytest`, `pip install`, `docker`, `systemctl`

### 6.3 Seção 3 — Mover Múltiplos Arquivos (P0)

- **1–2 arquivos**: `mv` via terminal aceitável
- **3+ arquivos**: OBRIGATÓRIO Python + JSON manifesto via `mcp_pylance_mcp_s_pylanceRunCodeSnippet`

### 6.4 Seção 4 — Git Workflow (P0)

- **≤ 5 linhas**: `echo` ou `python3 -c` no terminal
- **≥ 6 linhas**: OBRIGATÓRIO `create_file` para mensagem de commit
- Conventional Commits: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `style`, `ci`

### 6.5 Seção 5 — Organização de Pastas (P1)

| Tipo de arquivo | Localização |
|-----------------|-------------|
| Docs de sessão | `docs/SESSIONS/YYYY-MM-DD/` |
| Documentação técnica | `docs/` |
| Código Python | `src/` |
| Scripts | `scripts/` |
| Testes | `tests/` |
| Configurações | raiz (`.gitignore`, `pyproject.toml`) |

❌ **NUNCA** criar documentação na raiz | ❌ **NUNCA** modificar `.specify/` manualmente

### 6.6 Seção 6 — Nomenclatura (P1)

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Python | `snake_case.py` | `project_config.py` |
| Markdown | `SCREAMING_SNAKE.md` ou `kebab-case.md` | `SESSION_RECOVERY.md` |
| JSON | `kebab-case.json` | `mcp-config.json` |
| Shell | `kebab-case.sh` | `git-commit-with-file.sh` |
| Branch feat | `NNN-nome-da-feature` | `001-scaffold-py` |
| Branch fix | `fix-descricao` | `fix-symlink-broken` |

### 6.7 Seção 7 — Enforcement

Se regra violada, exibir e recusar:
```
❌ REGRA [N] violada: [nome]
Motivo: [explicação]
Correto: [alternativa válida]
```

---

## 7. Segurança e `.secrets/`

### 7.1 O que vai em `.secrets/`

| Tipo | Exemplos |
|------|----------|
| Variáveis de ambiente | `.env`, `.env.production`, `.env.staging` |
| Chaves SSH | `id_rsa`, `id_ed25519`, `*.pem` |
| Certificados TLS/SSL | `*.crt`, `*.key`, `*.p12`, `*.pfx` |
| Tokens de API | `api-tokens.txt`, `github-token.txt` |
| Credenciais cloud | `aws-credentials`, `gcp-service-account.json` |
| Segredos Kubernetes | `kubeconfig`, `k8s-secrets.yaml` |

### 7.2 Regras de Ouro

1. ❌ NUNCA commitar arquivos de `.secrets/`
2. ❌ NUNCA referenciar paths completos com credenciais em código
3. ❌ NUNCA logar ou imprimir valores sensíveis
4. ✅ SEMPRE usar variáveis de ambiente ou vault em produção
5. ✅ SEMPRE usar `.env.example` (sem valores reais) para documentar

### 7.3 `.gitignore` — Padrões Sensíveis Protegidos

```gitignore
.secrets/          # diretório completo
*.key              # chaves privadas
*.pem              # certificados
*.crt              # certificados
*.p12              # keystores
*.pfx              # keystores
*.jks              # Java keystores
*.keystore
secrets/
credentials/
*.credentials
.env
.venv
```

---

## 8. IMPs — Rastreamento de Implementações

### 8.1 Status Atual (2026-03-01)

| IMP | Título | Status | Dependência |
|-----|--------|--------|-------------|
| **IMP-01** | Criar `scripts/scaffold.py` | 🟠 **PRÓXIMO P0** | — |
| IMP-02 | `.github/prompts/session-start.prompt.md` | 🔵 Pendente | IMP-01 |
| IMP-03 | `.github/prompts/session-start-first.prompt.md` | 🔵 Pendente | IMP-01 |
| IMP-04 | `.github/prompts/session-end.prompt.md` | 🔵 Pendente | IMP-01 |
| IMP-05 | Domain Profile: devops-programming | 🔵 Pendente | — |
| IMP-06 | Domain Profile: devops-infrastructure | 🔵 Pendente | — |
| IMP-07 | Domain Profile: devops-analysis | 🔵 Pendente | — |
| IMP-08 | Redefinir `make init` como redirect | 🟠 Pendente | IMP-01 P0 |
| IMP-09 | Template `.copilot-rules-[projeto].md` | 🔵 Pendente | IMP-01 |
| IMP-10 | Validação Makefile completo | 🔵 Pendente | — |
| IMP-11 | Renomear manager.py → scaffold.py em docs | ✅ Concluído | — |
| IMP-12 | Arquitetura de módulos `scaffold.py` | ✅ Concluído | — |
| IMP-13 | Consolidar arquivos `.copilot-*` | ✅ Concluído | — |

### 8.2 Artefatos do IMP-01 (prontos)

| Artefato | Arquivo |
|----------|---------|
| Debate (4 perspectivas) | `docs/SESSIONS/2026-02-28/IMP-01-DEBATE.md` |
| Especificação técnica | `docs/SESSIONS/2026-02-28/IMP-01-SPEC.md` |
| User Stories (7 MVP + 4 futuras) | `docs/SESSIONS/2026-02-28/IMP-01-USER-STORIES.md` |

### 8.3 IMP-01 — Sub-tarefas de Implementação

```
[ ] scripts/lib/__init__.py
[ ] scripts/lib/config.py        ← ProjectConfig dataclass, constantes, paths
[ ] scripts/lib/ui.py            ← Prompts Rich, menu, validação
[ ] scripts/lib/project.py       ← Criação de estrutura + placeholders
[ ] scripts/lib/links.py         ← Setup e check de symlinks
[ ] scripts/lib/git.py           ← git init + remote add
[ ] scripts/lib/templates.py     ← Geração de .copilot-rules-[projeto].md
[ ] scripts/lib/vscode.py        ← Geração de settings.json, mcp.json, extensions.json
[ ] scripts/scaffold.py          ← Entry point + argparse + orquestração
[ ] Atualizar Makefile (make init → redirect)
```

---

## 9. Convenções de Nomenclatura

### 9.1 Arquivos de Sessão

| Arquivo | Conteúdo |
|---------|----------|
| `SESSION_RECOVERY_YYYY-MM-DD.md` | Estado recuperado para nova sessão |
| `DAILY_ACTIVITIES_YYYY-MM-DD.md` | Log cronológico de atividades |
| `SESSION_REPORT_YYYY-MM-DD.md` | Relatório narrativo da sessão |
| `FINAL_STATUS_YYYY-MM-DD.md` | Estado final de todos os artefatos |

### 9.2 Branches Git

```
feat/NNN-nome-da-feature    → ex: feat/001-scaffold-py
fix/descricao               → ex: fix/symlink-broken
docs/descricao              → ex: docs/readme-update
refactor/descricao          → ex: refactor/ui-module
```

### 9.3 Conventional Commits

```
feat(escopo): adiciona nova funcionalidade
fix(escopo): corrige bug
docs(escopo): atualiza documentação
refactor(escopo): refatora sem mudar comportamento
test(escopo): adiciona/corrige testes
chore(escopo): manutenção, dependências
perf(escopo): melhoria de performance
style(escopo): formatação
ci(escopo): mudanças no CI/CD
```

---

## 10. Fluxo de Sessão de Trabalho

### 10.1 Início de Sessão (checklist)

```
[ ] Verificar .vscode/mcp.json — MCP ativo?
[ ] Ler docs/SESSIONS/[última sessão]/FINAL_STATUS.md
[ ] Ler docs/SESSIONS/[última sessão]/SESSION_RECOVERY.md
[ ] Ler README.md, docs/INDEX.md, docs/TODO.md
[ ] Carregar .copilot-rules.md na memória
[ ] Scan de segurança (credenciais expostas?)
[ ] Verificar organização da raiz (arquivos fora do lugar?)
[ ] Criar docs/SESSIONS/YYYY-MM-DD/ com SESSION_RECOVERY e DAILY_ACTIVITIES
[ ] Atualizar docs/INDEX.md e docs/TODO.md
```

### 10.2 Durante a Sessão

```
[ ] Marcar IMP em progresso no TODO.md
[ ] Usar ferramentas nativas (NÃO cat/grep/find via terminal)
[ ] Arquivos de sessão → docs/SESSIONS/YYYY-MM-DD/
[ ] Código → src/ | Scripts → scripts/ | Docs → docs/
[ ] Commits com mensagem convencional
```

### 10.3 Encerramento de Sessão (checklist)

```
[ ] Criar/atualizar DAILY_ACTIVITIES_YYYY-MM-DD.md
[ ] Criar SESSION_REPORT_YYYY-MM-DD.md
[ ] Criar FINAL_STATUS_YYYY-MM-DD.md
[ ] Atualizar docs/INDEX.md (Last Updated + Last Session)
[ ] Atualizar docs/TODO.md (marcar concluídos, adicionar pendentes)
[ ] Commit + push (git add -A && git commit && git push)
```

### 10.4 Separação de Domínios: Makefile vs. scaffold.py

| Ferramenta | Domínio | Exemplos |
|------------|---------|----------|
| `scaffold.py` | Scaffolding de projetos | estrutura, symlinks, copilot-rules, git init |
| `Makefile` | Build / Test / CI / Deploy | `test`, `lint`, `build`, `docker-up` |

> ⚠️ **Sem duplicidade**: `make init` é APENAS redirect para `uv run scripts/scaffold.py`

---

*Gerado em 2026-03-01 | Projeto: `scaffold-project` | Branch: master*
