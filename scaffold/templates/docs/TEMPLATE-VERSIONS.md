# TEMPLATE-VERSIONS — Versionamento por Perfil

> Rastreabilidade de versão, status e histórico de cada perfil do Enterprise Scaffold Project Template.
> Atualizar esta tabela sempre que um perfil receber nova versão ou mudar de status.

**Schema de referência**: [docs/copilot/PROFILE-DESCRIPTOR-SCHEMA.md](copilot/PROFILE-DESCRIPTOR-SCHEMA.md)
**Política de depreciação**: [docs/DEPRECATION-POLICY.md](DEPRECATION-POLICY.md)
**Changelog do template**: [CHANGELOG.md](../CHANGELOG.md)

---

## Índice de Perfis

| Perfil | Layer | Versão | Status | Última validação | Testado com |
|--------|-------|--------|--------|-----------------|-------------|
| `devops-programming` | core | 1.0.0 | ✅ stable | 2026-03-07 | Python 3.12, TS 5.5, Go 1.23 |
| `devops-infrastructure` | core | 1.0.0 | 🔵 stub | 2026-03-14 | Terraform 1.5+, Kubernetes 1.27+, Helm 3.12+ |
| `devops-analysis` | core | 1.0.0 | 🔵 stub | 2026-03-14 | Python 3.12, Jupyter, dbt |
| `devops-security` | transversal | 1.0.0 | ✅ stable | 2026-03-14 | Todos os domínios (transversal) |
| `python-fastapi` | layer2 | 1.0.0 | ✅ stable | 2026-03-07 | FastAPI 0.115, Python 3.12, uv 0.5 |
| `python-flask` | layer2 | 1.0.0 | ✅ stable | 2026-03-07 | Flask 3.1, Python 3.12, uv 0.5 |
| `typescript-next` | layer2 | 1.0.0 | ✅ stable | 2026-03-07 | Next.js 15, TypeScript 5.5, Node 20 |
| `k8s-helm` | layer3 | 1.0.0 | ✅ stable | 2026-03-07 | Helm 3.12+, Kubernetes 1.25+ |
| `terraform-aws` | layer3 | 1.0.0 | ✅ stable | 2026-03-07 | Terraform 1.7+, AWS provider 5.x |
| `data-warehouse-dbt` | layer3 | 1.0.0 | ✅ stable | 2026-03-07 | dbt-core 1.7+, dbt-bigquery/snowflake |
| `lgpd-baseline` | layer4 | 1.0.0 | ✅ stable | 2026-03-07 | Qualquer stack Python/TS |
| `soc2-baseline` | layer4 | 1.0.0 | ✅ stable | 2026-03-07 | Qualquer stack Python/TS |

> **Perfis planejados** (ainda não implementados):
> - `go-chi` (layer2) — backlog

---

## Detalhamento por Perfil

### `devops-programming` — v1.0.0

**Layer**: core
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/devops-programming.yaml`](../scaffold/profiles/devops-programming.yaml)
**Prompt**: [`.github/prompts/domain/devops-programming.prompt.md`](../.github/prompts/domain/devops-programming.prompt.md)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-01 | Versão inicial — criação do schema 1.0.0, descriptor, prompt domain |

**Requer**: git, uv (Python), node >= 20 (TS), go >= 1.22 (Go)
**Exclui com**: `devops-infrastructure`, `devops-analysis`
**Combina com**: qualquer perfil layer2 de programação

---

### `devops-infrastructure` — v1.0.0 (stub)

**Layer**: core
**Status**: 🔵 stub (descriptor para resolver referências cruzadas)
**Descriptor**: [`scaffold/profiles/devops-infrastructure.yaml`](../scaffold/profiles/devops-infrastructure.yaml)
**Prompt**: `.github/prompts/domain/devops-infrastructure.prompt.md` _(pendente)_

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-14 | Stub criado — resolve referências em excludes_with de outros perfis core; expansão planejada |

**Requer**: terraform >= 1.5, kubectl >= 1.27, helm >= 3.12
**Exclui com**: `devops-programming`, `devops-analysis`
**Combina com**: `devops-security`, `k8s-helm`, `terraform-aws`

---

### `devops-analysis` — v1.0.0 (stub)

**Layer**: core
**Status**: 🔵 stub (descriptor para resolver referências cruzadas)
**Descriptor**: [`scaffold/profiles/devops-analysis.yaml`](../scaffold/profiles/devops-analysis.yaml)
**Prompt**: `.github/prompts/domain/devops-analysis.prompt.md` _(pendente)_

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-14 | Stub criado — resolve referências em excludes_with de outros perfis core; expansão planejada |

**Requer**: Python >= 3.11, dbt >= 1.7
**Exclui com**: `devops-programming`, `devops-infrastructure`
**Combina com**: `devops-security`, `data-warehouse-dbt`, `lgpd-baseline`, `soc2-baseline`

---

### `devops-security` — v1.0.0

**Layer**: transversal
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/devops-security.yaml`](../scaffold/profiles/devops-security.yaml)
**Prompt**: [`.github/prompts/domain/devops-security.prompt.md`](../.github/prompts/domain/devops-security.prompt.md)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-14 | Versão inicial — 5 escopos (IaC, código, segredos, threat-model, pre-commit), `generate_load_mcp()`, pr#descriptor completo |

**Perfil transversal** — aplicado a todos os projetos, independente do domínio.
**Exclui com**: nenhum
**Combina com**: todos os perfis (programação, infra, análise, layer2, layer3, layer4)

---

### `k8s-helm` — v1.0.0

**Layer**: layer3
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/k8s-helm.yaml`](../scaffold/profiles/k8s-helm.yaml)
**Templates**: [`scaffold/templates/project/k8s-helm/`](../scaffold/templates/project/k8s-helm/)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — Chart v2, Deployment/Service/Ingress/HPA/ConfigMap/ServiceAccount, values por ambiente |

**Stack**: Helm >= 3.12, Kubernetes >= 1.25
**Requer**: kubectl configurado + cluster acessível
**Combina com**: qualquer perfil layer2, `devops-security`

---

### `terraform-aws` — v1.0.0

**Layer**: layer3
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/terraform-aws.yaml`](../scaffold/profiles/terraform-aws.yaml)
**Templates**: [`scaffold/templates/project/terraform-aws/`](../scaffold/templates/project/terraform-aws/)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — módulos VPC/S3/ECS/RDS/IAM, remote state, tfsec + checkov |

**Stack**: Terraform >= 1.7, AWS provider 5.x
**Requer**: AWS CLI configurado, credenciais via .secrets/.env
**Combina com**: qualquer perfil layer2, `devops-security`

---

### `data-warehouse-dbt` — v1.0.0

**Layer**: layer3
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/data-warehouse-dbt.yaml`](../scaffold/profiles/data-warehouse-dbt.yaml)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — profiles.yml, sources.yml, staging/mart structure, generic tests |

**Stack**: dbt-core >= 1.7, adapters: bigquery / snowflake / redshift
**Combina com**: `devops-analysis` (core), `devops-security`

---

### `lgpd-baseline` — v1.0.0

**Layer**: layer4
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/lgpd-baseline.yaml`](../scaffold/profiles/lgpd-baseline.yaml)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — DATA-MAPPING.md, PRIVACY-NOTICE.md, DPA-CHECKLIST.md |

**Combina com**: qualquer layer2, `devops-security`

---

### `soc2-baseline` — v1.0.0

**Layer**: layer4
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/soc2-baseline.yaml`](../scaffold/profiles/soc2-baseline.yaml)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — Trust Services Criteria CC6-CC8, evidências de controle, EVIDENCE-LOG.md |

**Combina com**: qualquer layer2, `devops-security`

---

### `python-fastapi` — v1.0.0

**Layer**: layer2
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/python-fastapi.yaml`](../scaffold/profiles/python-fastapi.yaml)
**Templates**: [`scaffold/templates/project/python-fastapi/`](../scaffold/templates/project/python-fastapi/)
**Prompt**: [`.github/prompts/domain/python-fastapi.prompt.md`](../.github/prompts/domain/python-fastapi.prompt.md)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — app factory + lifespan, pydantic-settings, pytest-asyncio, Dockerfile multistage, Makefile 12 targets |

**Stack**: FastAPI ^0.115, Uvicorn, Pydantic-settings, pytest-asyncio, httpx (AsyncClient), ruff, bandit, pip-audit
**Requer**: devops-programming + language == python
**Exclui com**: `python-flask`

---

### `python-flask` — v1.0.0

**Layer**: layer2
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/python-flask.yaml`](../scaffold/profiles/python-flask.yaml)
**Templates**: [`scaffold/templates/project/python-flask/`](../scaffold/templates/project/python-flask/)
**Prompt**: [`.github/prompts/domain/python-flask.prompt.md`](../.github/prompts/domain/python-flask.prompt.md)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — application factory, blueprints, flask-wtf CSRF, flask-talisman, gunicorn, Dockerfile multistage |

**Stack**: Flask ^3.1, Flask-WTF, Flask-Talisman, Gunicorn, pytest, ruff, bandit, pip-audit
**Requer**: devops-programming + language == python
**Exclui com**: `python-fastapi`

---

### `typescript-next` — v1.0.0

**Layer**: layer2
**Status**: ✅ stable
**Descriptor**: [`scaffold/profiles/typescript-next.yaml`](../scaffold/profiles/typescript-next.yaml)
**Templates**: [`scaffold/templates/project/typescript-next/`](../scaffold/templates/project/typescript-next/)
**Prompt**: [`.github/prompts/domain/layer2-typescript-next.prompt.md`](../.github/prompts/domain/layer2-typescript-next.prompt.md)

| Versão | Data | O que mudou |
|--------|------|-------------|
| 1.0.0 | 2026-03-07 | Versão inicial — App Router, Server Components, TypeScript strict, Jest + RTL, Dockerfile multistage pnpm |

**Stack**: Next.js ^15, React ^19, TypeScript ^5.5, zod, Jest ^29, ESLint 9, Prettier 3, pnpm
**Requer**: devops-programming + language == typescript

---

## Convenções de Versionamento

Este projeto segue **Semantic Versioning 2.0.0** (semver.org) adaptado para templates:

| Tipo de mudança | MAJOR | MINOR | PATCH |
|----------------|-------|-------|-------|
| Mudança no schema do descriptor que quebra compatibilidade | ✅ | | |
| Remoção de campo obrigatório de template | ✅ | | |
| Novo perfil adicionado | | ✅ | |
| Novo campo opcional em descriptor | | ✅ | |
| Nova template adicionada a perfil existente | | ✅ | |
| Atualização de dependência (sem quebrar) | | | ✅ |
| Correção de bug em template | | | ✅ |
| Atualização de documentação | | | ✅ |

**Regra de ouro**: se um projeto gerado com versão anterior parar de funcionar após atualizar o perfil → é MAJOR.

---

## Procedimento de Atualização

Ao lançar nova versão de um perfil:

1. Atualizar `VERSION` / `version` no descriptor YAML
2. Atualizar `LAST_TESTED_DATE` / `last_tested` no descriptor
3. Adicionar entrada na tabela de histórico deste arquivo
4. Adicionar entrada no `CHANGELOG.md` (seção `[Unreleased]` → nova versão)
5. Atualizar `COMPATIBILITY-MATRIX.md` se a compatibilidade mudou
6. Executar `uv run pytest tests/ -q` — todos os testes devem passar
7. Commit com mensagem: `chore(profile): bump {nome}-profile to vX.Y.Z`
