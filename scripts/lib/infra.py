"""
lib/infra.py — Geração de arquivos de infraestrutura para projetos scaffold.

Gera:
  - .github/workflows/ci.yml   (pipeline CI por linguagem)
  - Dockerfile                  (multistage por linguagem)
  - docker-compose.yml          (app + postgres/redis opcionais comentados)
  - docs/RUNBOOK.md             (runbook operacional template)

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

from pathlib import Path

from .config import CreatedItem, ProjectConfig

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _write(path: Path, content: str) -> CreatedItem:
    """Escreve um arquivo se ainda não existir; retorna CreatedItem."""
    if path.exists():
        return CreatedItem(path=path, kind="file", status="skipped", message="já existe")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return CreatedItem(path=path, kind="file", status="created")


# ---------------------------------------------------------------------------
# CI Workflow templates
# ---------------------------------------------------------------------------

_CI_PYTHON = """\
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          version: "latest"
          enable-cache: true

      - name: Install dependencies
        run: uv sync --frozen

      - name: Lint
        run: uv run ruff check .

      - name: Format check
        run: uv run ruff format --check .

      - name: Tests
        run: uv run pytest --tb=short -q

      - name: Security scan
        run: uv run bandit -r src/ -ll || true

      - name: Dependency audit
        run: uv run pip-audit || true
"""

_CI_TYPESCRIPT = """\
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: pnpm/action-setup@v3
        with:
          version: latest

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "pnpm"

      - name: Install dependencies
        run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Format check
        run: pnpm format:check

      - name: Tests
        run: pnpm test:coverage

      - name: Dependency audit
        run: pnpm audit --audit-level=high || true
"""

_CI_GO = """\
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: "1.23"
          cache: true

      - name: Build
        run: go build ./...

      - name: Vet
        run: go vet ./...

      - name: Tests
        run: go test -race -coverprofile=coverage.out ./...

      - name: Coverage report
        run: go tool cover -func=coverage.out
"""

_CI_TEMPLATES: dict[str, str] = {
    "python":     _CI_PYTHON,
    "typescript": _CI_TYPESCRIPT,
    "go":         _CI_GO,
    "other":      _CI_PYTHON,  # fallback
}


def generate_ci_workflow(cfg: ProjectConfig) -> CreatedItem:
    """Gera .github/workflows/ci.yml com pipeline para a linguagem do projeto."""
    dest = cfg.target_dir / ".github" / "workflows" / "ci.yml"
    content = _CI_TEMPLATES.get(cfg.language, _CI_PYTHON)
    return _write(dest, content)


# ---------------------------------------------------------------------------
# Dockerfile templates
# ---------------------------------------------------------------------------

_DOCKERFILE_PYTHON = """\
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS builder

RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# ── Runner ────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runner

RUN addgroup --system --gid 1001 appgroup && \\
    adduser  --system --uid 1001 --ingroup appgroup appuser

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

_DOCKERFILE_NODE = """\
# syntax=docker/dockerfile:1
FROM node:20-slim AS base

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

# ── Deps ──────────────────────────────────────────────────────────────────────
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \\
    pnpm install --frozen-lockfile

# ── Builder ───────────────────────────────────────────────────────────────────
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build

# ── Runner ────────────────────────────────────────────────────────────────────
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs && \\
    adduser  --system --uid 1001 nodejs

COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=deps    /app/node_modules     ./node_modules

USER nodejs

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD node -e "require('http').get('http://localhost:3000/health', r => process.exit(r.statusCode === 200 ? 0 : 1))"

CMD ["node", "dist/index.js"]
"""

_DOCKERFILE_GO = """\
# syntax=docker/dockerfile:1
FROM golang:1.23-alpine AS builder

WORKDIR /app
COPY go.mod go.sum* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

# ── Runner ────────────────────────────────────────────────────────────────────
FROM gcr.io/distroless/static-debian12 AS runner

COPY --from=builder /app/server /server

USER nonroot:nonroot

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \\
  CMD ["/server", "healthcheck"]

ENTRYPOINT ["/server"]
"""

_DOCKERFILE_TEMPLATES: dict[str, str] = {
    "python":     _DOCKERFILE_PYTHON,
    "typescript": _DOCKERFILE_NODE,
    "go":         _DOCKERFILE_GO,
    "other":      _DOCKERFILE_NODE,  # fallback
}


def generate_dockerfile(cfg: ProjectConfig) -> CreatedItem:
    """Gera Dockerfile multistage para a linguagem do projeto."""
    dest = cfg.target_dir / "Dockerfile"
    content = _DOCKERFILE_TEMPLATES.get(cfg.language, _DOCKERFILE_NODE)
    return _write(dest, content)


# ---------------------------------------------------------------------------
# docker-compose.yml
# ---------------------------------------------------------------------------

_DOCKER_COMPOSE_TEMPLATE = """\
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    # depends_on:
    #   db:
    #     condition: service_healthy
    #   redis:
    #     condition: service_healthy

# ── Banco de dados (descomente se necessário) ─────────────────────────────────
#  db:
#    image: postgres:16-alpine
#    environment:
#      POSTGRES_USER: user
#      POSTGRES_PASSWORD: password
#      POSTGRES_DB: {project_name}
#    volumes:
#      - postgres_data:/var/lib/postgresql/data
#    healthcheck:
#      test: ["CMD-SHELL", "pg_isready -U user -d {project_name}"]
#      interval: 10s
#      timeout: 5s
#      retries: 5

# ── Cache / filas (descomente se necessário) ──────────────────────────────────
#  redis:
#    image: redis:7-alpine
#    healthcheck:
#      test: ["CMD", "redis-cli", "ping"]
#      interval: 10s
#      timeout: 3s
#      retries: 3

# volumes:
#   postgres_data:
"""


def generate_docker_compose(cfg: ProjectConfig) -> CreatedItem:
    """Gera docker-compose.yml com app + postgres/redis comentados."""
    dest = cfg.target_dir / "docker-compose.yml"
    content = _DOCKER_COMPOSE_TEMPLATE.format(project_name=cfg.project_name)
    return _write(dest, content)


# ---------------------------------------------------------------------------
# RUNBOOK.md
# ---------------------------------------------------------------------------

_RUNBOOK_TEMPLATE = """\
# Runbook — {project_title}

> **Projeto**: `{project_name}` | **Domínio**: {domain} | **Linguagem**: {language}
> **Gerado em**: {created_at}

---

## 1. Quick-start

```bash
git clone <repo>
cd {project_name}
cp .env.example .env   # preencher variáveis obrigatórias
make install           # instalar dependências
make dev               # iniciar servidor de desenvolvimento
```

---

## 2. Variáveis de ambiente obrigatórias

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `SECRET_KEY` | Chave secreta da aplicação | ✅ |
| `DATABASE_URL` | URL de conexão com o banco | Se usar banco |

> Copiar `.env.example` → `.env` e preencher os valores.
> **Nunca commitar o arquivo `.env`** — ele está no `.gitignore`.

---

## 3. Fluxo de desenvolvimento

```
main branch (produção)
  ├── feature/NNN-descricao  → PR → code review → merge → CI
  └── fix/descricao          → PR → code review → merge → CI
```

**Antes de abrir um PR**:
```bash
make ci    # lint + format-check + test + audit
```

---

## 4. CI/CD

O workflow `.github/workflows/ci.yml` executa automaticamente em:
- Push para `main`/`master`
- Pull Requests para `main`/`master`

**Passos do pipeline**: lint → format-check → testes → auditoria de deps

---

## 5. Deploy

### Local com Docker

```bash
make docker-build   # build da imagem
make docker-up      # sobe containers (app + deps)
make docker-down    # para containers
```

### Verificar saúde

```bash
curl http://localhost:8000/health
# Esperado: {{"status": "ok"}}
```

---

## 6. Observabilidade

| Item | Endpoint | Notas |
|------|----------|-------|
| Health check | `GET /health` | Retorna `{{"status": "ok"}}` |
| Logs | `docker compose logs -f app` | |

---

## 7. Procedimentos de emergência

### Rollback rápido

```bash
git log --oneline -10      # identificar último commit estável
git revert <commit>        # cria commit de rollback (recomendado)
```

### Inspecionar container em produção

```bash
docker ps
docker logs <container_id> --tail 200
docker exec -it <container_id> sh
```

---

## 8. Dependências externas

| Serviço | Propósito | Obrigatório | Fallback |
|---------|-----------|-------------|---------|
| PostgreSQL | Banco principal | Opcional | — |
| Redis | Cache / filas | Opcional | — |

---

*Gerado automaticamente pelo scaffold.py — mantenha atualizado conforme o projeto evolui.*
"""

_RUNBOOK_SECTION_K8S_HELM = """
---

## Kubernetes / Helm

### Status do release

```bash
helm status {project_name} -n <NAMESPACE>
kubectl get pods -n <NAMESPACE> -l app={project_name}
```

### Rollback

```bash
# Listar histórico de revisões
helm history {project_name} -n <NAMESPACE>

# Reverter para revisão anterior
helm rollback {project_name} <REVISION> -n <NAMESPACE>

# Ou via kubectl (último ReplicaSet)
kubectl rollout undo deployment/{project_name} -n <NAMESPACE>
```

### Verificar rollout

```bash
kubectl rollout status deployment/{project_name} -n <NAMESPACE>
```
"""

_RUNBOOK_SECTION_TERRAFORM_AWS = """
---

## Terraform / AWS

### Verificar estado da infraestrutura

```bash
terraform plan -var-file=envs/prod.tfvars
```

### Deploy seletivo (sem afetar outros recursos)

```bash
terraform apply -target=module.ecs -var-file=envs/prod.tfvars
```

### Status dos serviços ECS

```bash
aws ecs describe-services \\
  --cluster {project_name}-prod \\
  --services {project_name}-api
```

### Rollback de task definition

```bash
# Listar task definitions anteriores
aws ecs list-task-definitions --family-prefix {project_name} --sort DESC

# Reverter serviço para task definition anterior
aws ecs update-service \\
  --cluster {project_name}-prod \\
  --service {project_name}-api \\
  --task-definition <PREVIOUS_ARN>
```
"""

_RUNBOOK_SECTION_PYTHON_FASTAPI = """
---

## Python FastAPI

### Testes e cobertura

```bash
uv run pytest --cov=src --cov-report=term-missing -q
```

### Health check manual

```bash
curl -f http://localhost:8000/health
# Esperado: {{"status": "ok"}}  → HTTP 200

curl -f http://localhost:8000/api/v1/health
# Health detalhado com dependências
```

### Checklist de health endpoint

- [ ] `GET /health` retorna `200 {{"status": "ok"}}`
- [ ] Tempo de resposta < 500 ms
- [ ] Conexão com banco verificada (se usado)
- [ ] Variáveis de ambiente obrigatórias carregadas

### Iniciar servidor local

```bash
uv run uvicorn src.main:app --reload --port 8000
```
"""


def generate_runbook(cfg: ProjectConfig) -> CreatedItem:
    """Gera docs/RUNBOOK.md com template de runbook operacional.

    Seções adicionais são injetadas conforme os perfis em cfg.extra_profiles:
    - ``k8s-helm``       → comandos Helm/kubectl (status, rollback, rollout)
    - ``terraform-aws``  → terraform plan/apply, aws ecs describe-services
    - ``python-fastapi`` → uv run pytest --cov, health endpoint checklist
    """
    dest = cfg.target_dir / "docs" / "RUNBOOK.md"
    content = _RUNBOOK_TEMPLATE.format(
        project_name=cfg.project_name,
        project_title=cfg.project_title,
        domain=cfg.domain,
        language=cfg.language,
        created_at=cfg.created_at,
    )

    profiles = cfg.extra_profiles or []
    if "python-fastapi" in profiles:
        content += _RUNBOOK_SECTION_PYTHON_FASTAPI.format(
            project_name=cfg.project_name,
        )
    if "k8s-helm" in profiles:
        content += _RUNBOOK_SECTION_K8S_HELM.format(
            project_name=cfg.project_name,
        )
    if "terraform-aws" in profiles:
        content += _RUNBOOK_SECTION_TERRAFORM_AWS.format(
            project_name=cfg.project_name,
        )

    return _write(dest, content)
