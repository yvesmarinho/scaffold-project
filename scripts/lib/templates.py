"""
lib/templates.py — Geração de .copilot-rules-[projeto].md e .github/copilot-instructions.md.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

from .config import SCAFFOLD_VERSION, CreatedItem, ProjectConfig

# ---------------------------------------------------------------------------
# Mapeamento domínio → domain profile
# ---------------------------------------------------------------------------

DOMAIN_MAP: dict[str, str] = {
    "programming":    "devops-programming",
    "infrastructure": "devops-infrastructure",
    "analysis":       "devops-analysis",
}

# ---------------------------------------------------------------------------
# Regras P0 específicas por domínio
# ---------------------------------------------------------------------------

_DOMAIN_P0_RULES: dict[str, str] = {
    "programming": """\
- **P0**: Todo código novo deve ter testes unitários correspondentes em `tests/`
- **P0**: Sem valores hardcoded — configurações via variáveis de ambiente ou `config/`
- **P0**: Imports organizados: stdlib → third-party → interno (isort/ruff)
- **P1**: Docstrings obrigatórias em funções públicas e classes
- **P1**: Nenhum `TODO` ou `FIXME` deve ir para `main`/`master` sem issue registrada""",

    "infrastructure": """\
- **P0**: IaC declarativo — nunca modificar estado de infraestrutura fora do código versionado
- **P0**: Toda operação destrutiva (`destroy`, `delete`, `drop`) requer confirmação explícita do usuário
- **P0**: Scripts de infra devem ser idempotentes — executar N vezes = mesmo resultado
- **P1**: Secrets nunca em código IaC — usar Vault, SSM Parameter Store ou `.secrets/`
- **P1**: Nenhuma alteração em produção sem `plan`/`dry-run` revisado primeiro""",

    "analysis": """\
- **P0**: Dados brutos nunca commitados — apenas em `.data/` (gitignored) ou bucket externo
- **P0**: Notebooks devem ter saídas limpas antes do commit (`jupyter nbconvert --clear-output`)
- **P0**: Análises devem ser reproduzíveis: seed fixo, versões de deps fixadas em `requirements.txt`
- **P1**: Separar exploração (`notebooks/exploration/`) de entregáveis (`notebooks/reports/`)
- **P1**: Funções reutilizáveis em `src/` — não duplicar lógica entre notebooks""",
}

# ---------------------------------------------------------------------------
# Convenções por linguagem
# ---------------------------------------------------------------------------

_LANGUAGE_CONVENTIONS: dict[str, str] = {
    "python": """\
| Aspecto | Convenção |
|---------|-----------|
| Estilo | PEP 8 — formatado com `ruff format` ou `black` |
| Nomenclatura | `snake_case` para funções/variáveis, `PascalCase` para classes |
| Type hints | Obrigatório em funções públicas (`from __future__ import annotations`) |
| Imports | `isort` ou `ruff --select I` — agrupamento stdlib/third-party/interno |
| Linter | `ruff check` ou `flake8` |
| Testes | `pytest` — cobertura mínima 80% — rodar com `uv run pytest` |
| Gerenciador | **`uv`** (➕ preferêncial) — `uv venv`, `uv add`, `uv run`, `uv sync` |
| Virtual env | `.venv/` na raiz (gitignored) — criado com `uv venv` |
| Dependências | `pyproject.toml` (PEP 621) — lock em `uv.lock` (commitar) |
| Scripts | Executar via `uv run <script>` — não ativar `.venv` manualmente |""",

    "typescript": """\
| Aspecto | Convenção |
|---------|-----------|
| Estilo | Prettier — `.prettierrc` na raiz |
| Nomenclatura | `camelCase` para variáveis/funções, `PascalCase` para classes/interfaces |
| Tipos | Strict mode (`"strict": true` em `tsconfig.json`) — sem `any` implícito |
| Imports | ESLint `import/order` — node → external → internal |
| Linter | ESLint com `@typescript-eslint` |
| Testes | Jest ou Vitest — cobertura mínima 80% |
| Módulos | ESM (`"module": "ESNext"`) — sem `require()` |
| Build | `dist/` gerado, nunca commitado |""",

    "go": """\
| Aspecto | Convenção |
|---------|-----------|
| Estilo | `gofmt` / `goimports` — formatação automática obrigatória |
| Nomenclatura | `camelCase` para internos, `PascalCase` para exportados |
| Erros | Tratamento explícito — sem `_` para ignorar `error` |
| Panics | Proibido em código de biblioteca — apenas em `main()` com justificativa |
| Linter | `golangci-lint` com config em `.golangci.yml` |
| Testes | `go test ./...` — cobertura mínima 80% |
| Módulos | `go.mod` na raiz — versão Go fixada |
| Contexto | `context.Context` como primeiro arg em funções que fazem I/O |""",

    "other": """\
| Aspecto | Convenção |
|---------|-----------|
| Estilo | Definir linter/formatter na primeira sessão e registrar aqui |
| Nomenclatura | Definir e registrar aqui |
| Testes | Framework a definir — cobertura mínima 80% |
| Documentação | Inline e em `docs/` |""",
}

# ---------------------------------------------------------------------------
# Estrutura de pastas por domínio + linguagem
# ---------------------------------------------------------------------------

_FOLDER_STRUCTURE: dict[str, dict[str, str]] = {
    "programming": {
        "python": """\
{project_name}/
├── src/                    # Código fonte Python
│   ├── core/              # Lógica de negócio (models, services)
│   ├── api/               # Endpoints / handlers
│   └── shared/            # Utilitários compartilhados
├── tests/                  # Testes (espelha src/)
│   ├── unit/
│   └── integration/
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── SESSIONS/
├── scripts/               # Automação
├── .venv/                 # Virtual env (gitignored)
├── pyproject.toml
└── .vscode/""",

        "typescript": """\
{project_name}/
├── src/                    # Código TypeScript
│   ├── core/              # Lógica de negócio
│   ├── api/               # Endpoints / controllers
│   └── shared/            # Utilitários compartilhados
├── tests/                  # Testes
│   ├── unit/
│   └── integration/
├── dist/                  # Build (gitignored)
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── SESSIONS/
├── package.json
├── tsconfig.json
└── .vscode/""",

        "go": """\
{project_name}/
├── cmd/                    # Entry points (main packages)
│   └── {project_name}/
├── internal/              # Código privado do módulo
│   ├── core/
│   └── handlers/
├── pkg/                   # Código exportável (libs)
├── tests/
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── SESSIONS/
├── go.mod
└── .vscode/""",

        "other": """\
{project_name}/
├── src/
├── tests/
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── SESSIONS/
├── scripts/
└── .vscode/""",
    },

    "infrastructure": {
        "_default": """\
{project_name}/
├── terraform/             # IaC Terraform (se aplicável)
│   ├── modules/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── variables.tf
├── ansible/               # Playbooks Ansible (se aplicável)
│   ├── roles/
│   └── playbooks/
├── docker/                # Dockerfiles e compose
│   ├── Dockerfile
│   └── docker-compose.yml
├── k8s/                   # Manifests Kubernetes (se aplicável)
│   ├── base/
│   └── overlays/
├── scripts/               # Scripts de automação de infra
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   ├── RUNBOOK.md         # Procedures operacionais
│   └── SESSIONS/
└── .vscode/""",
    },

    "analysis": {
        "_default": """\
{project_name}/
├── notebooks/
│   ├── exploration/       # Análises exploratórias (rascunho)
│   └── reports/           # Entregáveis finais
├── src/                   # Funções reutilizáveis (importadas pelos notebooks)
│   ├── data/             # Loaders, limpeza
│   ├── features/         # Feature engineering
│   └── visualization/    # Plots, dashboards
├── .data/                 # Dados brutos (gitignored)
├── outputs/               # Resultados, modelos exportados (gitignored)
├── tests/
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── SESSIONS/
├── requirements.txt
└── .vscode/""",
    },
}

# ---------------------------------------------------------------------------
# Template principal do arquivo de regras Copilot (enriquecido — IMP-09)
# ---------------------------------------------------------------------------

_COPILOT_RULES_TEMPLATE = """\
# Copilot Rules — {project_title}

> Arquivo gerado automaticamente por `scripts/scaffold.py` em {created_at}
> Regras genéricas compartilhadas: ver `.copilot-rules.md` (symlink para shared)

---

## 🎯 Identidade do Projeto

| Campo | Valor |
|-------|-------|
| **Nome** | `{project_name}` |
| **Título** | {project_title} |
| **Descrição** | {description} |
| **Domínio** | {domain} |
| **Linguagem principal** | {language} |
| **Repositório** | {github_repo} |
| **Criado em** | {created_at} |

---

## 🎭 Perfis de Domínio Ativos

| Perfil | Arquivo | Tipo |
|--------|---------|------|
| **Principal** | `.github/prompts/domain/{domain_profile}.prompt.md` | Domínio padrão |
| **Segurança** | `.github/prompts/domain/devops-security.prompt.md` | Transversal |
{extra_profiles_rows}

Para declarar o modo ativo no início de cada sessão:

```
Modo: {domain_upper}. Projeto: {project_name}. Perfil: {domain_profile}.
```

Ritual canônico: `python scripts/session-manager.py --json start`

---

## 📁 Estrutura de Pastas

```
{folder_structure}
```

---

## 🔧 Regras Específicas — Domínio `{domain}`

> Pré-preenchidas com base no domínio. Edite e acrescente conforme o projeto evoluir.

{domain_rules}

---

## 💻 Convenções de Linguagem — `{language}`

{language_conventions}

---

## 🔐 Segurança

- Credenciais, tokens e chaves: **NUNCA** em arquivos versionados
- Usar `.secrets/.env` + `${{env:VAR_NAME}}` em `mcp.json`
- `.secrets/` está no `.gitignore` ✅
- Scan obrigatório a cada início de sessão: `.env*`, `*.key`, `*.pem`, `*.crt`, `*secret*`, `*password*`, `*token*`

---

## 📋 Decisões Técnicas do Projeto

> Registre aqui decisões arquiteturais e técnicas tomadas ao longo do projeto.

| Data | Decisão | Resultado |
|------|---------|-----------|
| {created_at} | Scaffold inicial criado | Domínio: {domain}, Linguagem: {language} |

---

## 🔗 Referências

- [README.md](README.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/TODO.md](docs/TODO.md)
- [.copilot-rules.md](.copilot-rules.md) ← regras genéricas compartilhadas
- [.github/prompts/domain/{domain_profile}.prompt.md](.github/prompts/domain/{domain_profile}.prompt.md)

---

*Gerado por scripts/scaffold.py v{scaffold_version} | {created_at}*
"""


# ---------------------------------------------------------------------------
# Template do copilot-instructions.md (injetado automaticamente em toda sessão)
# ---------------------------------------------------------------------------

_COPILOT_INSTRUCTIONS_TEMPLATE = """\
---
applyTo: "**"
---

# GitHub Copilot — Instruções do Projeto

**Projeto**: `{project_name}` — {project_title}
**Domínio**: {domain} | **Linguagem**: {language}
**Regras completas**: `.copilot-rules-{project_name}.md`
**Rituais de sessão**: `python scripts/session-manager.py --json start` | `python scripts/session-manager.py --json end`
**Domain Profile ativo**: `.github/prompts/domain/{domain_profile}.prompt.md`

---

## 🚨 Regras P0 — CRÍTICO (nunca violar)

### 1. Criar/editar arquivos — NUNCA via terminal

| Operação | ✅ Ferramenta obrigatória |
|----------|--------------------------|
| Criar arquivo novo | `create_file` |
| Editar arquivo existente | `replace_string_in_file` (mín. 3 linhas de contexto) |
| Múltiplas edições | `multi_replace_string_in_file` |

❌ **PROIBIDO**: `cat > heredoc`, `echo >> arquivo`, `echo | tee arquivo`

---

### 2. Ler/buscar/listar arquivos — NUNCA via terminal

| Operação | ✅ Ferramenta obrigatória |
|----------|--------------------------|
| Ler conteúdo | `read_file` |
| Buscar texto | `grep_search` |
| Encontrar arquivos | `file_search` |
| Listar diretório | `list_dir` |
| Busca semântica | `semantic_search` |
| Verificar erros | `get_errors` |

❌ **PROIBIDO via terminal**: `cat`, `grep`, `find`, `ls`
✅ **`run_in_terminal` apenas para**: `git`, `make`, `pytest`, `pip install`, `docker`, `systemctl`

---

### 3. Mover/copiar/excluir arquivos — SEMPRE Python stdlib

```python
import shutil, logging
from pathlib import Path

log = logging.getLogger(__name__)
src, dst = Path("origem/arq.md"), Path("destino/arq.md")
dst.parent.mkdir(parents=True, exist_ok=True)
if src.exists():
    shutil.move(str(src), str(dst))
    log.info("✅ %s → %s", src, dst)
```

❌ **PROIBIDO**: `mv`, `cp`, `rm`, `mkdir` via terminal

---

### 4. Git commits — SEMPRE via arquivo de mensagem

```bash
echo "feat(escopo): descrição" > /tmp/commit.txt
./scripts/git-commit-with-file.sh /tmp/commit.txt
```

❌ **PROIBIDO**: `git commit -m "..."` direto

---

## 📋 Regras P1 — Organização

### 5. Pastas corretas

| Tipo | Localização |
|------|-------------|
| Docs de sessão | `docs/SESSIONS/YYYY-MM-DD/` |
| Docs técnicos | `docs/` |
| Python source | `src/` |
| Scripts | `scripts/` |

❌ **NUNCA** arquivos de sessão/doc na raiz

---

### 6. Documentos incrementais — nunca sobrescrever

`README.md`, `docs/INDEX.md`, `docs/TODO.md`, `docs/SESSIONS/*/DAILY_ACTIVITIES_*.md`,
`docs/SESSIONS/*/SESSION_REPORT_*.md`, `docs/SESSIONS/*/FINAL_STATUS_*.md` →
sempre **acrescentar**, nunca reescrever do zero.

---

### 7. Nomenclatura

| Tipo | Padrão |
|------|--------|
| Python | `snake_case.py` |
| Markdown | `SCREAMING_SNAKE.md` |
| JSON | `kebab-case.json` |
| Shell | `kebab-case.sh` |

---

## 🔒 Segurança

- Credenciais/tokens: NUNCA em arquivos versionados
- `mcp.json`: usar `${{env:VAR_NAME}}` ou `.secrets/.env`
- `.secrets/` está no `.gitignore` ✅

---

## ⚠️ Enforcement

```
❌ REGRA [N] violada: [nome]
Motivo: [explicação]
Correto: [alternativa válida]
```

*Gerado por scaffold.py em {created_at} — Projeto: {project_name}*
"""


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def generate_copilot_instructions(config: ProjectConfig) -> CreatedItem:
    """
    Gera `.github/copilot-instructions.md` no projeto filho.

    Este arquivo é automaticamente injetado pelo VS Code Copilot como instrução
    de sistema em toda conversa — garante que as regras P0/P1 estão sempre ativas
    sem depender do ritual manual de sessão.

    Não sobrescreve se já existe — retorna status 'skipped'.
    """
    dest = config.project_path / ".github" / "copilot-instructions.md"
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        return CreatedItem(
            path=dest,
            kind="file",
            status="skipped",
            message="arquivo já existe",
        )

    domain_profile = DOMAIN_MAP.get(config.domain, config.domain)
    content = _COPILOT_INSTRUCTIONS_TEMPLATE.format(
        project_name=config.project_name,
        project_title=config.project_title,
        domain=config.domain,
        language=config.language,
        domain_profile=domain_profile,
        created_at=config.created_at,
    )

    try:
        dest.write_text(content, encoding="utf-8")
        return CreatedItem(
            path=dest,
            kind="file",
            status="created",
            message=f"auto-injeção Copilot ativa | domain: {domain_profile}",
        )
    except OSError as e:
        return CreatedItem(
            path=dest,
            kind="file",
            status="error",
            message=str(e),
        )


def generate_copilot_rules(config: ProjectConfig) -> CreatedItem:
    """
    Gera `.copilot-rules-[project_name].md` em config.project_path.

    Conteúdo enriquecido (IMP-09):
    - Identidade do projeto
    - Tabela de perfis ativos (domínio + segurança + extras)
    - Estrutura de pastas por domínio + linguagem
    - Regras P0/P1 pré-preenchidas por domínio
    - Convenções de linguagem com tabela detalhada
    - Seção de decisões técnicas

    Não sobrescreve se já existe — retorna status 'skipped'.
    """
    filename = f".copilot-rules-{config.project_name}.md"
    dest = config.project_path / filename

    if dest.exists():
        return CreatedItem(
            path=dest,
            kind="file",
            status="skipped",
            message="arquivo já existe",
        )

    domain_profile = DOMAIN_MAP.get(config.domain, config.domain)

    # Perfis extras além do domínio padrão + segurança
    extra_profiles_rows = ""
    for profile in config.extra_profiles:
        label = profile.replace("devops-", "").capitalize()
        extra_profiles_rows += (
            f"| **{label}** | `.github/prompts/domain/{profile}.prompt.md` | Extra |\n"
        )

    # Estrutura de pastas: tenta domínio+linguagem, fallback para _default
    lang = config.language
    domain_folders = _FOLDER_STRUCTURE.get(config.domain, {})
    raw_structure = domain_folders.get(lang) or domain_folders.get("_default") or (
        f"{config.project_name}/\n├── src/\n├── tests/\n├── docs/\n└── .vscode/"
    )
    folder_structure = raw_structure.format(project_name=config.project_name)

    # Regras de domínio e convenções de linguagem
    domain_rules = _DOMAIN_P0_RULES.get(config.domain, "- **P0**: [Adicionar regra crítica aqui]\n- **P1**: [Adicionar regra importante aqui]")
    language_conventions = _LANGUAGE_CONVENTIONS.get(lang, _LANGUAGE_CONVENTIONS["other"])

    content = _COPILOT_RULES_TEMPLATE.format(
        project_name=config.project_name,
        project_title=config.project_title,
        description=config.description or "(sem descrição)",
        domain=config.domain,
        language=config.language,
        github_repo=config.github_repo or "(não informado)",
        created_at=config.created_at,
        domain_profile=domain_profile,
        domain_upper=config.domain.upper(),
        extra_profiles_rows=extra_profiles_rows,
        folder_structure=folder_structure,
        domain_rules=domain_rules,
        language_conventions=language_conventions,
        scaffold_version=SCAFFOLD_VERSION,
    )

    try:
        dest.write_text(content, encoding="utf-8")
        return CreatedItem(
            path=dest,
            kind="file",
            status="created",
            message=f"domain: {domain_profile} | lang: {lang} | extras: {len(config.extra_profiles)}",
        )
    except OSError as e:
        return CreatedItem(
            path=dest,
            kind="file",
            status="error",
            message=str(e),
        )


# ---------------------------------------------------------------------------
# IMP-29 — Guia de documentação gerado por combinação de perfis ativos
# ---------------------------------------------------------------------------

# Mapeamento de ordem de camada → display (espelha composer._LAYER_ORDER)
_LAYER_SORT_ORDER: dict = {
    "core":        0, 0:  0,
    "layer2":      1, 1:  1, 2:  1,
    "layer3":      2, 3:  2,
    "layer4":      3, 4:  3,
    "transversal": 99,
}

_LAYER_DISPLAY: dict[int, str] = {
    0:  "Core / Layer 1",
    1:  "Layer 2 (Framework)",
    2:  "Layer 3 (Platform)",
    3:  "Layer 4 (Compliance)",
    99: "Transversal",
}

_TAG_REFERENCES: dict[str, list[str]] = {
    "python":     ["[Python 3 Docs](https://docs.python.org/3)", "[uv Docs](https://docs.astral.sh/uv)"],
    "fastapi":    ["[FastAPI Docs](https://fastapi.tiangolo.com)", "[pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)"],
    "flask":      ["[Flask Docs](https://flask.palletsprojects.com)", "[Flask-WTF](https://flask-wtf.readthedocs.io)"],
    "typescript": ["[TypeScript Handbook](https://www.typescriptlang.org/docs)"],
    "next":       ["[Next.js Docs](https://nextjs.org/docs)"],
    "docker":     ["[Docker Docs](https://docs.docker.com)"],
    "k8s":        ["[Kubernetes Docs](https://kubernetes.io/docs/home/)"],
    "helm":       ["[Helm Docs](https://helm.sh/docs)"],
    "terraform":  ["[Terraform Docs](https://developer.hashicorp.com/terraform/docs)", "[AWS Provider Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)"],
    "aws":        ["[AWS SDK Boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)"],
    "airflow":    ["[Apache Airflow Docs](https://airflow.apache.org/docs)"],
    "dbt":        ["[dbt Docs](https://docs.getdbt.com)"],
    "lgpd":       ["[Lei 13.709/2018 — LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)", "[ANPD](https://www.gov.br/anpd/pt-br)"],
    "soc2":       ["[SOC 2 — AICPA](https://www.aicpa.org/resources/landing/system-and-organization-controls-soc-suite-of-services)"],
    "async":      ["[Python asyncio](https://docs.python.org/3/library/asyncio.html)"],
    "go":         ["[Go Docs](https://go.dev/doc)"],
    "uv":         ["[uv Docs](https://docs.astral.sh/uv)"],
    "api":        ["[REST API Best Practices](https://restfulapi.net)"],
}

_PROFILE_GUIDE_TEMPLATE = """\
# 📖 Profile Guide — {combo_title}

> Guia gerado automaticamente por `scripts/scaffold.py` em {created_at}.
> **Combinação ativa**: {profiles_display}
> **Projeto**: `{project_name}` ({domain} / {language})

---

## 🎯 Combinação de Perfis

| Perfil | Camada | Descrição |
|--------|--------|-----------|
{profiles_table}

---

## 📁 Arquivos Gerados

{files_sections}

---

## 🔐 Segurança — Requisitos Ativos

{security_sections}

---

## ⚡ Quick Start

### Pré-requisitos

{requires_section}

### Comandos Principais

```bash
# Instalar dependências
make install-deps

# Desenvolvimento
make dev

# Testes
make test

# Lint e formatação
make lint && make format
```

---

## 🔗 Referências por Stack

{references_section}

---

*Gerado por scripts/scaffold.py v{scaffold_version} | {created_at}*
"""


def _layer_order_int(raw_layer: object) -> int:
    """Maps a raw layer value (str or int) to sort order integer."""
    order = _LAYER_SORT_ORDER.get(raw_layer)  # type: ignore[call-overload]
    if order is None:
        order = _LAYER_SORT_ORDER.get(str(raw_layer).lower(), 1)
    return order


def _layer_display_name(raw_layer: object) -> str:
    """Converts raw layer value to human-readable display string."""
    return _LAYER_DISPLAY.get(_layer_order_int(raw_layer), str(raw_layer))


def _compute_combo_slug(profiles_applied: list[str], descriptors: dict[str, dict]) -> str:
    """
    Computes a filesystem-safe slug for the profile combination.

    Excludes:
    - Known transversal profiles (SPECKIT_TRANSVERSAL_PROFILES, e.g. devops-security)
      — these may not have a descriptor YAML but are always-on.
    - Profiles whose descriptor declares layer order 0 (core) or 99 (transversal).

    Only layer2, layer3, layer4 profiles appear in the slug.
    If no significant profiles remain, returns 'core'.
    """
    from .config import SPECKIT_TRANSVERSAL_PROFILES

    significant: list[str] = []
    for name in profiles_applied:
        if name in SPECKIT_TRANSVERSAL_PROFILES:
            continue
        raw_layer = descriptors.get(name, {}).get("layer", "layer2")
        if _layer_order_int(raw_layer) not in (0, 99):
            significant.append(name)
    return "-".join(significant) if significant else "core"


def _get_guide_file_entries(descriptor: dict) -> list[tuple[str, str]]:
    """
    Returns all file entries from a descriptor for display in the guide.

    Unlike get_template_entries() in composer.py, includes inline/generated entries
    since the guide is human documentation (shows what will be created).
    """
    entries: list[tuple[str, str]] = []

    # Schema A: templates_path + templates[]
    if "templates_path" in descriptor and "templates" in descriptor:
        for e in (descriptor.get("templates") or []):
            if isinstance(e, dict) and e.get("path"):
                entries.append((str(e["path"]), str(e.get("description", ""))))
        return entries

    # Schema B: generates.files[]
    generates = descriptor.get("generates")
    if isinstance(generates, dict):
        for f in (generates.get("files") or []):
            if isinstance(f, dict) and f.get("path"):
                entries.append((str(f["path"]), str(f.get("description", ""))))
    return entries


def generate_profile_guide(
    config: ProjectConfig,
    profiles_applied: list[str],
    descriptors: dict[str, dict],
) -> CreatedItem:
    """
    Gera docs/PROFILE-GUIDE-{combo_slug}.md no projeto destino.

    O guia inclui:
    - Tabela de perfis ativos com camada e descrição
    - Arquivos gerados por cada perfil (de generates.files / templates)
    - Requisitos de segurança ativos (de security.enforces)
    - Quick Start com pré-requisitos e comandos
    - Referências por stack (baseadas nas tags dos perfis)

    Não sobrescreve se já existe — retorna status 'skipped'.
    """
    if not profiles_applied:
        return CreatedItem(
            path=config.project_path / "docs" / "PROFILE-GUIDE-core.md",
            kind="file",
            status="skipped",
            message="sem perfis aplicados — guia não gerado",
        )

    combo_slug = _compute_combo_slug(profiles_applied, descriptors)
    dest = config.project_path / "docs" / f"PROFILE-GUIDE-{combo_slug}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        return CreatedItem(
            path=dest,
            kind="file",
            status="skipped",
            message="guia já existe",
        )

    # -- Profiles table
    profiles_table_lines: list[str] = []
    for name in profiles_applied:
        desc = descriptors.get(name, {})
        raw_layer = desc.get("layer", "layer2")
        description = str(desc.get("description") or "").strip().replace("\n", " ")
        if len(description) > 80:
            description = description[:77] + "..."
        profiles_table_lines.append(
            f"| `{name}` | {_layer_display_name(raw_layer)} | {description} |"
        )
    profiles_table = "\n".join(profiles_table_lines)

    # -- Files generated sections (per profile)
    files_parts: list[str] = []
    for name in profiles_applied:
        desc = descriptors.get(name, {})
        entries = _get_guide_file_entries(desc)
        if entries:
            cap = 15
            rows = "\n".join(f"| `{p}` | {d} |" for p, d in entries[:cap])
            more = (
                f"\n\n*(+{len(entries) - cap} mais — ver `scaffold/profiles/{name}.yaml`)*"
                if len(entries) > cap
                else ""
            )
            files_parts.append(
                f"### `{name}`\n\n| Arquivo | Descrição |\n|---------|----------|\n{rows}{more}"
            )
    files_sections = (
        "\n\n".join(files_parts)
        if files_parts
        else "*(sem arquivos declarados nos descriptors)*"
    )

    # -- Security requirements sections (per profile)
    security_parts: list[str] = []
    for name in profiles_applied:
        desc = descriptors.get(name, {})
        security = desc.get("security") or {}
        enforces: list = security.get("enforces") or []
        if enforces:
            if isinstance(enforces[0], dict):
                # Structured objects → render as table
                header = (
                    "| Controle | Ferramenta | Severidade | Auto | Descrição |\n"
                    "|----------|-----------|-----------|------|-----------|"
                )
                rows = []
                for ctrl in enforces:
                    c = ctrl.get("control", "")
                    t = ctrl.get("tool", "")
                    s = ctrl.get("severity", "")
                    a = "✅" if ctrl.get("automated") else "❌"
                    d = str(ctrl.get("description", "")).replace("\n", " ")
                    if len(d) > 70:
                        d = d[:67] + "..."
                    rows.append(f"| `{c}` | `{t}` | {s} | {a} | {d} |")
                table = header + "\n" + "\n".join(rows)
                security_parts.append(f"### `{name}`\n\n{table}")
            else:
                # Legacy string list fallback
                rules = "\n".join(f"- {r}" for r in enforces)
                security_parts.append(f"### `{name}`\n\n{rules}")
    security_sections = (
        "\n\n".join(security_parts)
        if security_parts
        else "*(sem regras de segurança declaradas nos descriptors)*"
    )

    # -- Requires section (aggregate, deduplicated)
    all_requires: list[str] = []
    seen_req: set[str] = set()
    for name in profiles_applied:
        desc = descriptors.get(name, {})
        for req in (desc.get("requires") or []):
            req_str = str(req).strip()
            if req_str and req_str not in seen_req:
                seen_req.add(req_str)
                all_requires.append(f"- `{req_str}`")
    requires_section = "\n".join(all_requires) if all_requires else "*(sem pré-requisitos declarados)*"

    # -- References section (from tags, deduplicated)
    all_tags: list[str] = []
    for name in profiles_applied:
        desc = descriptors.get(name, {})
        for tag in (desc.get("tags") or []):
            tag_str = str(tag)
            if tag_str not in all_tags:
                all_tags.append(tag_str)

    ref_links: list[str] = []
    seen_refs: set[str] = set()
    for tag in all_tags:
        for ref in (_TAG_REFERENCES.get(tag) or []):
            if ref not in seen_refs:
                seen_refs.add(ref)
                ref_links.append(f"- {ref}")
    references_section = (
        "\n".join(ref_links)
        if ref_links
        else "*(sem referências mapeadas para estas tags)*"
    )

    # -- Header display strings
    profiles_display = " + ".join(f"`{p}`" for p in profiles_applied)
    title_parts = [
        p.replace("devops-", "").replace("-", " ").title()
        for p in profiles_applied
        if p != "devops-security"
    ]
    combo_title = " + ".join(title_parts) if title_parts else "Core"

    content = _PROFILE_GUIDE_TEMPLATE.format(
        combo_title=combo_title,
        created_at=config.created_at,
        profiles_display=profiles_display,
        project_name=config.project_name,
        domain=config.domain,
        language=config.language,
        profiles_table=profiles_table,
        files_sections=files_sections,
        security_sections=security_sections,
        requires_section=requires_section,
        references_section=references_section,
        scaffold_version=SCAFFOLD_VERSION,
    )

    try:
        dest.write_text(content, encoding="utf-8")
        return CreatedItem(
            path=dest,
            kind="file",
            status="created",
            message=f"combinação: {combo_slug} | {len(profiles_applied)} perfil(is)",
        )
    except OSError as e:
        return CreatedItem(
            path=dest,
            kind="file",
            status="error",
            message=str(e),
        )
