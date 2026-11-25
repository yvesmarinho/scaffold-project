# Copilot Rules — Test Project

> Arquivo gerado automaticamente por `scripts/scaffold.py` em {{CREATED_AT}}
> Regras genéricas compartilhadas: ver `.copilot-rules.md` (symlink para shared)

---

## 🎯 Identidade do Projeto

| Campo | Valor |
|-------|-------|
| **Nome** | `test-project` |
| **Título** | Test Project |
| **Descrição** | A test project for smoke testing |
| **Domínio** | programming |
| **Linguagem principal** | python |
| **Repositório** | (não informado) |
| **Criado em** | {{CREATED_AT}} |

---

## 🎭 Perfis de Domínio Ativos

| Perfil | Arquivo | Tipo |
|--------|---------|------|
| **Principal** | `.github/skills/devops-programming/SKILL.md` | Domínio padrão |
| **Segurança** | `.github/skills/devops-security/SKILL.md` | Transversal |


Para declarar o modo ativo no início de cada sessão:

```
Modo: PROGRAMMING. Projeto: test-project. Perfil: devops-programming.
```

Ritual canônico: `python scripts/session-manager.py --json start`

---

## 📁 Estrutura de Pastas

```
test-project/
├── src/                    # Código fonte Python
│   ├── core/              # Lógica de negócio (models, services)
│   ├── api/               # Endpoints / handlers
│   └── shared/            # Utilitários compartilhados
├── tests/                  # Testes (espelha src/)
│   ├── unit/
│   └── integration/
├── docs/
│   ├── INDEX.md
│   └── TODO.md
├── scripts/               # Automação
├── .venv/                 # Virtual env (gitignored)
├── pyproject.toml
└── .vscode/
```

---

## 🔧 Regras Específicas — Domínio `programming`

> Pré-preenchidas com base no domínio. Edite e acrescente conforme o projeto evoluir.

- **P0**: Todo código novo deve ter testes unitários correspondentes em `tests/`
- **P0**: Sem valores hardcoded — configurações via variáveis de ambiente ou `config/`
- **P0**: Imports organizados: stdlib → third-party → interno (isort/ruff)
- **P1**: Docstrings obrigatórias em funções públicas e classes
- **P1**: Nenhum `TODO` ou `FIXME` deve ir para `main`/`master` sem issue registrada

---

## 💻 Convenções de Linguagem — `python`

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
| Scripts | Executar via `uv run <script>` — não ativar `.venv` manualmente |

---

## 🔐 Segurança

- Credenciais, tokens e chaves: **NUNCA** em arquivos versionados
- Usar `.secrets/.env` + `${env:VAR_NAME}` em `mcp.json`
- `.secrets/` está no `.gitignore` ✅
- Scan obrigatório a cada início de sessão: `.env*`, `*.key`, `*.pem`, `*.crt`, `*secret*`, `*password*`, `*token*`

---

## 📋 Decisões Técnicas do Projeto

> Registre aqui decisões arquiteturais e técnicas tomadas ao longo do projeto.

| Data | Decisão | Resultado |
|------|---------|-----------|
| {{CREATED_AT}} | Scaffold inicial criado | Domínio: programming, Linguagem: python |

---

## 🔗 Referências

- [README.md](README.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/TODO.md](docs/TODO.md)
- [.copilot-rules.md](.copilot-rules.md) ← regras genéricas compartilhadas
- [.github/skills/devops-programming/SKILL.md](.github/skills/devops-programming/SKILL.md)

---

*Gerado por scripts/scaffold.py v1.7.1 | {{CREATED_AT}}*
