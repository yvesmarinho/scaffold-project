# 📐 IMP-01 — Especificação Técnica: `scaffold.py`

**Data**: 2026-02-28
**Versão**: 1.0.0
**Status**: 🟡 Rascunho — aguarda aprovação
**Debate de origem**: [IMP-01-DEBATE.md](IMP-01-DEBATE.md)
**Decisões de design**: [DOMAIN-PROFILES-DECISIONS.md](../../copilot/DOMAIN-PROFILES-DECISIONS.md)

---

## 1. Visão Geral

O `scaffold.py` é o **ponto único de entrada** para inicialização e scaffolding de projetos baseados no template `scaffold-project`. Substitui três shell scripts (`init-new-project.sh`, `setup-project-links.sh`, `check-project-links.sh`) com uma implementação Python modular, interativa e testável.

### 1.1 Objetivos

- Guiar o usuário na criação de um novo projeto com prompts claros
- Criar estrutura de pastas, arquivos base e symlinks de forma reproduzível
- Gerar arquivo de regras Copilot específico do projeto (`.copilot-rules-[projeto].md`)
- Inicializar repositório Git local e configurar remote (se URL informada)
- Ser utilizável em modo interativo (humano) e modo CI (automação)

### 1.2 Fora de Escopo (MVP)

- TUI visual com Textual (post-MVP)
- Criação automática de repositório no GitHub via `gh` CLI (post-MVP)
- Integração com MCP `memory` server (post-MVP)

---

## 2. Arquitetura

### 2.1 Estrutura de Arquivos

```
scripts/
├── scaffold.py              ← Entry point (~80 linhas, só orquestração)
└── lib/
    ├── __init__.py         ← Vazio
    ├── config.py           ← ProjectConfig dataclass, constantes, paths
    ├── ui.py               ← Prompts Rich, menus, validação
    ├── project.py          ← Criação de estrutura, substituição de placeholders
    ├── links.py            ← Setup e check de symlinks .copilot-*
    ├── git.py              ← git init, git remote add
    └── templates.py        ← Geração de .copilot-rules-[projeto].md
```

### 2.2 Diagrama de Fluxo Principal

```
CLI args parse
     │
     ├─ --check → links.check_symlinks() → print_report() → EXIT
     ├─ --help  → show_help() → EXIT
     │
     └─ (padrão / --new)
          │
          ├─ show_banner()
          ├─ show_menu()
          │    ├─ [1] Novo Projeto → flow_new_project()
          │    ├─ [2] Verificar Links → flow_check_links()
          │    ├─ [3] Gerar .copilot-rules → flow_generate_rules()
          │    └─ [4] Sair → EXIT 0
          │
          └─ flow_new_project()
               ├─ ui.collect_project_info()     → ProjectConfig
               ├─ ui.confirm_summary(config)    → bool
               ├─ project.create_structure(config)
               ├─ links.setup_symlinks(config)
               ├─ templates.generate_copilot_rules(config)
               ├─ git.init_repository(config)
               └─ ui.print_final_summary(results)
```

### 2.3 Dependências

```python
# PEP 723 — header no topo de scaffold.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "rich>=13.7",
# ]
# ///
```

**Dependências de sistema** (não gerenciadas pelo script):
- `git` no PATH
- Opcional: `uv` para execução sem instalação manual

---

## 3. Módulos — Contratos de Interface

### 3.1 `lib/config.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Valores padrão
DEFAULT_SHARED_DIR = Path.home() / "Documentos" / "DevOps" / ".copilot-shared"
SHARED_COPILOT_FILES = [
    ".copilot-rules.md",
    ".copilot-git-rules.md",
    ".copilot-strict-enforcement.md",
    ".copilot-strict-rules.md",
    ".copilot-file-rules.sh",
]

DomainType = Literal["programming", "infrastructure", "analysis"]
LanguageType = Literal["python", "typescript", "go", "other"]

@dataclass
class ProjectConfig:
    project_name: str           # slug kebab-case, ex: my-api-v2
    project_title: str          # legível, ex: My API v2
    description: str            # 1 frase
    domain: DomainType          # programming | infrastructure | analysis
    language: LanguageType      # python | typescript | go | other
    github_repo: str | None     # URL ou None
    shared_dir: Path            # caminho para .copilot-shared
    target_dir: Path            # onde o projeto será criado (default: cwd)
    created_at: str             # ISO8601 timestamp

@dataclass
class CreatedItem:
    path: Path
    kind: Literal["dir", "file", "symlink", "git"]
    status: Literal["created", "skipped", "error"]
    message: str = ""

@dataclass
class LinkStatus:
    name: str
    target: Path | None
    status: Literal["ok", "broken", "missing"]
```

---

### 3.2 `lib/ui.py`

```python
def show_banner() -> None:
    """Exibe banner Rich com nome do projeto e versão."""

def show_menu() -> str:
    """Exibe menu principal e retorna a opção escolhida ('1'-'4')."""

def collect_project_info(ci_mode: bool = False, **overrides) -> ProjectConfig:
    """
    Coleta informações do projeto via prompts interativos (default)
    ou via overrides (modo CI).

    Em modo interativo:
    - Exibe cada campo com valor padrão sugerido
    - Valida inline antes de aceitar
    - Permite rever/corrigir antes de confirmar

    Em modo CI (ci_mode=True):
    - Todos os campos fornecidos por overrides
    - Campos opcionais usam defaults se ausentes
    - Campos obrigatórios ausentes levantam ValueError
    """

def confirm_summary(config: ProjectConfig) -> bool:
    """Exibe resumo da config e pede confirmação (s/n)."""

def print_final_summary(items: list[CreatedItem | LinkStatus]) -> None:
    """Exibe tabela Rich com status de cada item criado/verificado."""
```

**Campos obrigatórios** (falham sem valor em modo CI):
- `project_name`, `domain`, `language`

**Campos opcionais** (têm defaults em modo CI):
- `project_title` → `project_name` em title-case
- `description` → `""`
- `github_repo` → `None`
- `shared_dir` → `DEFAULT_SHARED_DIR`
- `target_dir` → `Path.cwd()`

---

### 3.3 `lib/project.py`

```python
def create_structure(config: ProjectConfig) -> list[CreatedItem]:
    """
    Cria a estrutura de pastas e arquivos base do projeto.

    Pastas criadas:
    - docs/, docs/SESSIONS/, docs/copilot/
    - .github/agents/, .github/prompts/domain/
    - .secrets/, .vscode/, scripts/lib/
    - src/ (vazio, opcional)

    Arquivos criados (de templates internos):
    - README.md (com placeholders substituídos)
    - docs/INDEX.md
    - docs/TODO.md
    - docs/TODAY_ACTIVITIES.md
    - .gitignore (cópia do template)
    - .secrets/README.md
    - .vscode/mcp.json (template base)
    - .vscode/settings.json (template base)
    - Makefile (template base)
    - [project_name].code-workspace

    Comportamento:
    - Não sobrescreve arquivos existentes → skipped
    - Pastas já existentes → skipped (sem erro)
    - Retorna lista de CreatedItem com status de cada operação
    """

PLACEHOLDERS: dict[str, str] = {
    "{{PROJECT_NAME}}": "config.project_name",
    "{{PROJECT_TITLE}}": "config.project_title",
    "{{PROJECT_DESCRIPTION}}": "config.description",
    "{{CREATED_AT}}": "config.created_at",
    "{{DOMAIN}}": "config.domain",
    "{{LANGUAGE}}": "config.language",
    "{{GITHUB_REPO}}": "config.github_repo or ''",
}
```

---

### 3.4 `lib/links.py`

```python
def setup_symlinks(config: ProjectConfig) -> list[CreatedItem]:
    """
    Cria symlinks relativos dos arquivos .copilot-* do shared_dir para target_dir.

    Para cada arquivo em SHARED_COPILOT_FILES:
    - Se shared_dir não existe → aviso, skip todos
    - Se arquivo não existe no shared_dir → aviso, skip esse arquivo
    - Se symlink já existe e está ok → skip
    - Se symlink existe e está quebrado → recria
    - Se não existe → cria symlink relativo

    Symlinks são RELATIVOS (não absolutos) para portabilidade.
    """

def check_symlinks(target_dir: Path, shared_dir: Path) -> list[LinkStatus]:
    """
    Verifica status de cada symlink .copilot-* em target_dir.

    Retorna lista de LinkStatus com:
    - 'ok': symlink existe e aponta para arquivo real
    - 'broken': symlink existe mas target não existe
    - 'missing': symlink não existe no target_dir

    Código de saída: 0 se tudo ok, 1 se qualquer broken/missing.
    """
```

---

### 3.5 `lib/git.py`

```python
def init_repository(config: ProjectConfig) -> CreatedItem:
    """
    Executa git init no target_dir (se não já inicializado).
    Se config.github_repo fornecido, adiciona como remote 'origin'.

    Não falha se já há um .git/ — apenas reporta 'skipped'.
    Usa subprocess com check=True e timeout=30s.
    """

def is_git_repo(path: Path) -> bool:
    """Retorna True se path contém um repositório git (.git/ existe)."""
```

---

### 3.6 `lib/templates.py`

```python
DOMAIN_MAP = {
    "programming": "devops-programming",
    "infrastructure": "devops-infrastructure",
    "analysis": "devops-analysis",
}

COPILOT_RULES_TEMPLATE = """
# Copilot Rules — {project_title}

> Arquivo gerado automaticamente pelo scripts/scaffold.py em {created_at}
> Regras genéricas: ver .copilot-rules.md (symlink para shared)

## 🎯 Identidade do Projeto

| Campo | Valor |
|-------|-------|
| **Nome** | {project_name} |
| **Título** | {project_title} |
| **Descrição** | {description} |
| **Domínio** | {domain} |
| **Linguagem principal** | {language} |
| **Repositório** | {github_repo} |
| **Criado em** | {created_at} |

## 🎭 Domain Profile Ativo

→ Arquivo: `.github/prompts/domain/{domain_profile}.prompt.md`

Para ativar, declare no início da sessão:
```
Modo: {DOMAIN_UPPER}. Projeto: {project_name}.
```

## 📁 Estrutura de Pastas Relevante

[Preencher manualmente conforme o projeto evoluir]

## 🔧 Regras Específicas Este Projeto

[Preencher manualmente — convenções, padrões, decisões específicas]

## 🔗 Referências

- [README.md](README.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/TODO.md](docs/TODO.md)
"""

def generate_copilot_rules(config: ProjectConfig) -> CreatedItem:
    """
    Gera .copilot-rules-[project_name].md em config.target_dir.
    Localização: config.target_dir / f".copilot-rules-{config.project_name}.md"

    Não sobrescreve se já existe — retorna status 'skipped'.
    """
```

---

## 4. Interface CLI

### 4.1 Argparse — Definição

```bash
usage: scaffold.py [-h] [--version] [--new] [--check] [--ci]
                  [--name NAME] [--title TITLE] [--description DESC]
                  [--domain {programming,infrastructure,analysis}]
                  [--language {python,typescript,go,other}]
                  [--repo REPO] [--shared-dir PATH] [--target-dir PATH]

Enterprise Project Scaffold

options:
  -h, --help            mostra esta ajuda
  --version             mostra versão e sai
  --new                 inicia fluxo de novo projeto diretamente (sem menu)
  --check               verifica symlinks do projeto no diretório atual
  --ci                  modo não-interativo (usa args direto, sem prompts)

campos do projeto (usados com --ci ou --new):
  --name NAME           nome kebab-case do projeto (obrigatório em --ci)
  --title TITLE         título legível
  --description DESC    descrição breve
  --domain {programming,infrastructure,analysis}
  --language {python,typescript,go,other}
  --repo REPO           URL do repositório GitHub
  --shared-dir PATH     caminho para .copilot-shared (default: ~/Documentos/DevOps/.copilot-shared)
  --target-dir PATH     local onde criar o projeto (default: diretório atual)
```

### 4.2 Relação com o Makefile — Separação de Domínios

> **Princípio**: O `scaffold.py` é o único dono da lógica de scaffolding do projeto.
> O `Makefile` é o dono de build, test, lint e CI. **Não há duplicidade.**

| Ferramenta | Domínio | Exemplos |
|------------|---------|----------|
| `scaffold.py` | Scaffolding do projeto | criar estrutura, symlinks, copilot-rules, git init |
| `Makefile` | Build / Test / CI / Deploy | `make test`, `make lint`, `make build`, `make docker-up` |

**Entrada única do usuário**:
```bash
# Sempre via Python — nunca via make para funções de projeto
uv run scripts/scaffold.py          # recomendado
python scripts/scaffold.py          # alternativa (deps já instaladas)
```

**O que acontece com `make init` existente**:
```makefile
## [DEPRECATED] — use: uv run scripts/scaffold.py
init:
	@echo ""
	@echo " ⚠️  Para criar/configurar o projeto, use diretamente:"
	@echo "      uv run scripts/scaffold.py"
	@echo "      python scripts/scaffold.py"
	@echo ""
```
> `make init` é redefinido como **guia de redirect**, não como executor. Preserva o hábito sem duplicar lógica.

---

## 5. Comportamento de Erros

| Situação | Comportamento | Código de Saída |
|----------|--------------|----------------|
| `shared_dir` não existe | Aviso amarelo — prossegue sem symlinks | 0 |
| `project_name` inválido | Erro vermelho — repede o campo (modo interativo) | N/A (retry) |
| `project_name` inválido em `--ci` | Erro vermelho — exit | 1 |
| `git` não encontrado no PATH | Aviso amarelo — pula etapa Git | 0 |
| Pasta já existe no `target_dir` | Aviso amarelo — pula criação, mantém existente | 0 |
| Erro de permissão ao criar arquivo | Erro vermelho — para execução | 1 |
| `CTRL+C` durante coleta | Mensagem "Cancelado" — saída limpa | 130 |

---

## 6. Testes e Validação

### 6.1 Testes manuais (antes de implementar testes automatizados)

```bash
# Teste 1: Novo projeto completo (modo interativo)
mkdir /tmp/test-proj && cd /tmp/test-proj
uv run /path/to/scripts/scaffold.py
# → Preencher todos os campos
# → Verificar estrutura criada com ls -la
# → Verificar .copilot-rules-test-proj.md gerado

# Teste 2: Modo CI
mkdir /tmp/test-ci && cd /tmp/test-ci
uv run /path/to/scripts/scaffold.py --ci \
  --name test-ci-project \
  --domain infrastructure \
  --language python
# → Deve criar sem nenhum prompt

# Teste 3: Check de links
cd /tmp/test-proj
uv run /path/to/scripts/scaffold.py --check
# → Mostrar status de cada symlink

# Teste 4: Verificar redirect do Makefile
make init
# → Deve exibir mensagem de redirect para scaffold.py (sem executar nada)
```

### 6.2 Critério de "Feito" (Definition of Done)

- [ ] `uv run scripts/scaffold.py` executa sem erros em repositório limpo (recém-clonado)
- [ ] `make init` exibe mensagem de redirect (sem executar lógica própria)
- [ ] Estrutura de pastas conforme FEATURE-03 criada corretamente
- [ ] Symlinks `.copilot-*` criados (ou aviso se shared_dir ausente)
- [ ] `.copilot-rules-[projeto].md` gerado com dados corretos
- [ ] `git init` executado; `git remote add origin` se URL informada
- [ ] `make check-links` exibe status de todos os symlinks
- [ ] Modo `--ci` funciona sem interação humana
- [ ] Nenhum arquivo existente sobrescrito sem confirmação
- [ ] Log em `scripts/logs/scaffold.log` após execução

---

## 7. Faseamento de Implementação

### Fase 1 — MVP (IMP-01, esta sessão ou próxima)
- `lib/config.py` — dataclasses e constantes
- `lib/ui.py` — prompts e saída Rich
- `lib/project.py` — criação de estrutura
- `lib/links.py` — setup + check de symlinks
- `lib/git.py` — git init + remote
- `lib/templates.py` — geração de .copilot-rules
- `scaffold.py` — entry point + argparse + orquestração
- Atualização do `Makefile` (redefinição de `make init` como redirect)

### Fase 2 — Qualidade (pós-IMP-01)
- Testes unitários para cada módulo (`scripts/tests/`)
- Logging estruturado em JSON (opcional)
- `--dry-run` flag para simular sem criar arquivos

### Fase 3 — TUI (backlog P3)
- Migrar `lib/ui.py` para Textual
- Menu visual com navegação por teclado
- Árvore de estrutura criada em tempo real

---

## 8. Referências

| Documento | Link |
|-----------|------|
| Debate de funcionalidades | [IMP-01-DEBATE.md](IMP-01-DEBATE.md) |
| User Stories | [IMP-01-USER-STORIES.md](IMP-01-USER-STORIES.md) |
| Decisões de design (D-01 a D-19) | [DOMAIN-PROFILES-DECISIONS.md](../../copilot/DOMAIN-PROFILES-DECISIONS.md) |
| Script de referência (enterprise-ansible) | `scripts/manage.py` (existente no template) |
| Shell script absorvido | `scripts/init-new-project.sh` |
| Shell scripts absorvidos | `scripts/setup-project-links.sh`, `scripts/check-project-links.sh` |

---

*Arquivo gerado em 2026-02-28 | Specifications Engineer | Sessão: [DAILY_ACTIVITIES_2026-02-28.md](DAILY_ACTIVITIES_2026-02-28.md)*
