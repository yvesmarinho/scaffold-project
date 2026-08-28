# Profile Descriptors

Este diretório contém os descritores declarativos de cada perfil de domínio do Enterprise Scaffold Project Template.

**Schema**: [docs/copilot/PROFILE-DESCRIPTOR-SCHEMA.md](../docs/copilot/PROFILE-DESCRIPTOR-SCHEMA.md)

## Perfis disponíveis (22 perfis)

### Core Profiles (Base — Layer 0/1)

| Arquivo | Layer | Descrição |
|---------|-------|-----------|
| `devops-programming.yaml` | core | Perfil base para projetos de programação (Python, TS, Go) |
| `devops-infrastructure.yaml` | core | Perfil base para projetos de infraestrutura/IaC |
| `devops-analysis.yaml` | core | Perfil base para projetos de análise de dados |
| `devops-security.yaml` | transversal | Controles de segurança — aplicado em todos os perfis |

### Backend & Data (Layer 2)

| Arquivo | Layer | Descrição |
|---------|-------|-----------|
| `python-fastapi.yaml` | layer2 | FastAPI async API — app factory, pydantic-settings, pytest-asyncio |
| `python-flask.yaml` | layer2 | Flask microframework — blueprints, Flask-WTF (CSRF), Flask-Talisman |
| `database-expert.yaml` | layer2 | DBA professional, SQL expert developer, Spec-Driven Development |
| `data-warehouse-dbt.yaml` | layer2 | Data warehouse transformation — dbt, SQL, dimensional modeling |
| `backend-architect.yaml` | layer2 | Backend architecture — API design, microservices, scalability |

### Frontend & Design (Layer 2)

| Arquivo | Layer | Descrição |
|---------|-------|-----------|
| `typescript-next.yaml` | layer2 | Next.js 15 + TypeScript strict — App Router, Server Components |
| `frontend-architect.yaml` | layer2 | Frontend architecture — SPA, SSR, state management, performance |
| `ui-design-expert.yaml` | layer2 | UI design — design systems, WCAG accessibility, prototyping |
| `ux-design-expert.yaml` | layer2 | UX design — user research, journey mapping, usability testing |

### Infrastructure & Platform (Layer 2)

| Arquivo | Layer | Descrição |
|---------|-------|-----------|
| `systems-engineer.yaml` | layer2 | Systems engineering — distributed systems, Linux, networking |
| `sre-platform-engineer.yaml` | layer2 | SRE/Platform — reliability, observability, incident management |
| `k8s-helm.yaml` | layer2 | Kubernetes + Helm — orchestration, operators, GitOps |
| `terraform-aws.yaml` | layer2 | Terraform + AWS — infrastructure as code, multi-region |

### Security & Quality (Layer 2)

| Arquivo | Layer | Descrição |
|---------|-------|-----------|
| `appsec-engineer.yaml` | layer2 | Application security — SAST, DAST, threat modeling, OWASP |
| `qa-automation-engineer.yaml` | layer2 | QA automation — test pyramid, CI/CD integration, performance testing |
| `lgpd-baseline.yaml` | layer2 | LGPD compliance — data privacy, consent, minimization |
| `soc2-baseline.yaml` | layer2 | SOC 2 Type II compliance — security, availability, confidentiality |

## Integration Matrix

### Common Combinations

| Use Case | Profile Combination |
|----------|---------------------|
| **Full-stack Web App** | `frontend-architect` + `ui-design-expert` + `backend-architect` + `database-expert` + `devops-infrastructure` |
| **Microservices Platform** | `backend-architect` + `systems-engineer` + `sre-platform-engineer` + `k8s-helm` + `appsec-engineer` |
| **E-commerce Frontend** | `typescript-next` + `frontend-architect` + `ui-design-expert` + `ux-design-expert` + `qa-automation-engineer` |
| **Data Pipeline** | `devops-analysis` + `data-warehouse-dbt` + `database-expert` + `devops-infrastructure` |
| **Secure API** | `python-fastapi` + `backend-architect` + `appsec-engineer` + `database-expert` + `devops-security` |
| **Internal Platform** | `sre-platform-engineer` + `systems-engineer` + `k8s-helm` + `terraform-aws` + `devops-infrastructure` |

## How Profiles Work

1. **Layer 0 (Core)**: Base profiles (`devops-programming`, `devops-infrastructure`, `devops-analysis`)
2. **Layer 1 (Transversal)**: Cross-cutting concerns (`devops-security`, applied to all)
3. **Layer 2 (Specialized)**: Domain-specific expertise (backend, frontend, data, security, etc.)

Each profile descriptor defines:
- **`expertise_domains`**: 5-6 domains with 8-10 skills each
- **`stack`**: Tools, frameworks, versions
- **`combines_with`**: Which profiles work together
- **`workflows`**: Step-by-step processes (3-7 steps each)
- **`best_practices`**: 10-12 guiding principles
- **`examples`**: Real-world use cases with ADRs
- **`quality_gates`**: Validation criteria (8-10 requirements)

> **Note**: All profiles follow schema v1.0.0 — see [PROFILE-DESCRIPTOR-SCHEMA.md](../docs/copilot/PROFILE-DESCRIPTOR-SCHEMA.md) for details.
