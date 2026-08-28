# Domínio: Programming — Guia Humano

> Documentação de referência para o domínio **programming** do Enterprise Scaffold Project Template.
> Para o perfil machine-readable do Copilot, veja: [`.github/prompts/domain/devops-programming.prompt.md`](../../.github/prompts/domain/devops-programming.prompt.md)

**Última atualização**: 2026-03-07
**Perfis Layer 2 disponíveis**: `python-fastapi`, `python-flask`, `typescript-next`
**Perfis Layer 2 planejados**: `go-chi`, `typescript-express` (backlog)

---

## 1. O que é este domínio?

O domínio `programming` cobre todo trabalho cujo **artefato central é código-fonte** versionado em Git, com ciclo de feedback via testes automatizados.

Exemplos de trabalho neste domínio:
- Criar uma API REST (FastAPI, Flask, Express)
- Implementar feature em aplicação web (Next.js, React)
- Escrever scripts de automação (Python, TypeScript)
- Refatorar módulo existente com cobertura de testes
- Fazer code review orientado por padrões do template

**Não** é domínio programming:
- Escrever Terraform para provisionar infraestrutura → domínio `infrastructure`
- Analisar logs de produção para diagnóstico → domínio `analysis`
- Escrever playbook Ansible para configurar servidor → domínio `infrastructure`

---

## 2. Quando escolher este domínio no scaffold

Ao executar `uv run scripts/scaffold.py`, escolha `programming` quando:

```
Domínio → programming
```

O scaffold vai configurar:
- Regras Copilot com foco em: qualidade de código, testes, type safety
- Domain profile: `devops-programming.prompt.md`
- Estrutura de pastas: `src/`, `tests/`, `docs/`
- `.gitignore` com entradas: `.venv/`, `node_modules/`, `dist/`, `__pycache__/`
- `pyproject.toml` ou `package.json` conforme a linguagem escolhida

---

## 3. Perfis Layer 2 disponíveis

Após criar o projeto base com `programming`, aplique um perfil Layer 2 via `--compose`:

```bash
# Python + FastAPI (API async com pydantic-settings)
uv run scripts/scaffold.py --compose python-fastapi \
  --ci --name meu-projeto --domain programming --language python \
  --target-dir /caminho/do/projeto

# Python + Flask (microframework com blueprints)
uv run scripts/scaffold.py --compose python-flask \
  --ci --name meu-projeto --domain programming --language python \
  --target-dir /caminho/do/projeto

# TypeScript + Next.js 15 (App Router, Server Components)
uv run scripts/scaffold.py --compose typescript-next \
  --ci --name meu-projeto --domain programming --language typescript \
  --target-dir /caminho/do/projeto
```

### Comparativo dos perfis Layer 2

| Aspecto | `python-fastapi` | `python-flask` | `typescript-next` |
|---------|:----------------:|:--------------:|:-----------------:|
| **Linguagem** | Python | Python | TypeScript |
| **Paradigma** | Async / ASGI | Sync / WSGI | SSR / App Router |
| **Caso de uso** | API REST / GraphQL | Web app / API leve | Frontend / Fullstack |
| **Auth** | JWT / OAuth2 via middleware | Flask-Login / JWT | NextAuth.js / Clerk |
| **ORM** | SQLAlchemy async | SQLAlchemy / Flask-SQLAlchemy | Prisma / Drizzle |
| **Testes** | pytest-asyncio + httpx | pytest + test_client | Jest + RTL |
| **Container** | Dockerfile multistage (uv) | Dockerfile multistage (gunicorn) | Dockerfile multistage (pnpm) |
| **Exclui com** | `python-flask` | `python-fastapi` | — |

---

## 4. Convenções universais do domínio

Independente do perfil Layer 2 escolhido, as seguintes convenções são aplicadas:

### Estrutura de commits

```
tipo(escopo): descrição curta em português

feat(auth): adicionar JWT refresh token
fix(api): corrigir validação de CNPJ
test(health): cobrir cenário de timeout
refactor(config): extrair settings para pydantic-settings
docs(readme): atualizar quick-start
chore(deps): bump fastapi 0.115 → 0.116
```

### Nomenclatura de branches

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Feature nova | `NNN-nome-da-feature` | `018-jwt-refresh` |
| Correção | `fix-descricao` | `fix-cors-production` |
| Chore / deps | `chore-descricao` | `chore-bump-deps-march` |

### Regras P0 (invioláveis)

- Todo código novo tem testes correspondentes em `tests/`
- Sem valores hardcoded — configurações via variáveis de ambiente ou `config/`
- Imports organizados: stdlib → third-party → interno
- Nenhum `TODO` ou `FIXME` vai para `main` sem issue registrada

### Regras P1 (fortemente recomendadas)

- Type annotations obrigatórias em funções públicas
- Cobertura mínima 80% (`make test-coverage`)
- `make ci` deve passar antes de abrir PR (lint + format-check + test + audit)

---

## 5. Fluxo de trabalho típico

```
1. scaffold.py → cria projeto base (programming + linguagem)
2. --compose    → aplica perfil layer2 (fastapi | flask | typescript-next)
3. --infra      → gera Dockerfile + ci.yml + docker-compose.yml + RUNBOOK.md
4. git init     → (já feito pelo scaffold)
5. make install → instala dependências
6. make dev     → inicia desenvolvimento
7. make ci      → valida antes de PR
```

---

## 6. Artefatos gerados (resumo)

```
projeto/
├── src/                    # Código-fonte (Python) ou app/ (Next.js)
├── tests/                  # Testes unitários e de integração
├── docs/                   # Documentação incremental
│   ├── INDEX.md
│   ├── TODO.md
│   └── SESSIONS/
├── Makefile                # Targets: install, dev, test, lint, format, ci, docker-*
├── pyproject.toml          # Ou package.json
├── Dockerfile              # Multistage por linguagem
├── docker-compose.yml      # App + deps opcionais (postgres, redis)
├── .github/
│   ├── copilot-instructions.md
│   ├── workflows/ci.yml
│   └── prompts/domain/     # Domain profiles ativos
├── .vscode/
│   ├── settings.json
│   └── extensions.json
└── .copilot-rules-{nome}.md
```

---

## 7. Decisões de design documentadas

Para o histórico de decisões sobre a estratégia de Domain Profiles, ver:
- [DOMAIN-PROFILES-STRATEGY.md](DOMAIN-PROFILES-STRATEGY.md) — contexto e arquitetura de 3 camadas
- [DOMAIN-PROFILES-DECISIONS.md](DOMAIN-PROFILES-DECISIONS.md) — 19 decisões respondidas (D-01 a D-19)
- [PROFILE-DESCRIPTOR-SCHEMA.md](PROFILE-DESCRIPTOR-SCHEMA.md) — schema técnico dos descriptors
