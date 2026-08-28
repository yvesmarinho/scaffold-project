# Domínio: Infrastructure — Guia Humano

> Documentação de referência para o domínio **infrastructure** do Enterprise Scaffold Project Template.
> Para o perfil machine-readable do Copilot, veja: [`.github/prompts/domain/devops-infrastructure.prompt.md`](../../.github/prompts/domain/devops-infrastructure.prompt.md)

**Última atualização**: 2026-03-07
**Perfis Layer 2 disponíveis**: *(pendente — IMP-22 k8s-helm, IMP-23 terraform-aws)*
**Status**: core configurado, perfis layer2 em planejamento

---

## 1. O que é este domínio?

O domínio `infrastructure` cobre todo trabalho cujo **artefato central são configurações declarativas** que representam o estado desejado de ambientes de TI. O resultado esperado é infraestrutura funcionando com SLOs definidos.

Exemplos de trabalho neste domínio:
- Provisionar recursos na AWS com Terraform (VPC, ECS, RDS, Lambda)
- Escrever Chart Helm para deploy de aplicação em Kubernetes
- Configurar cluster K8s (EKS, GKE, K3s, on-prem)
- Criar playbook Ansible para configurar servidores
- Escrever manifests Kubernetes (Deployment, Service, Ingress, HPA)
- Configurar pipeline CI/CD (GitHub Actions, ArgoCD)
- Operar e responder a incidentes de infraestrutura

**Não** é domínio infrastructure:
- Escrever código da aplicação → domínio `programming`
- Analisar logs para diagnóstico de bug → domínio `analysis`
- Escrever testes unitários → domínio `programming`

---

## 2. Princípio fundamental — Plano antes de Execução

> ⚠️ **Regra de ouro**: em qualquer ambiente diferente de `dev` local, o plano vem **antes** da execução.

| Ação | Ambiente dev | Staging | Produção |
|------|:-----------:|:-------:|:--------:|
| `terraform apply` | OK | Requer plan revisado | Requer plan revisado + aprovação |
| `helm upgrade` | OK | Requer `--dry-run` revisado | Requer `--dry-run` + janela de manutenção |
| `kubectl delete` | OK | Confirmação explícita | Confirmação + backup |
| `ansible-playbook` | OK | Confirmação + `--check` first | Confirmação + rollback tested |

---

## 3. Quando escolher este domínio no scaffold

Ao executar `uv run scripts/scaffold.py`, escolha `infrastructure` quando o projeto principal for IaC ou automação de infra:

```
Domínio → infrastructure
```

O scaffold vai configurar:
- Regras Copilot com foco em: idempotência, segurança de credenciais, plano-antes-de-executar
- Domain profile: `devops-infrastructure.prompt.md`
- Estrutura de pastas: orientada a IaC em vez de `src/`
- `.gitignore` com entradas: `.terraform/`, `*.tfstate`, `*.tfstate.backup`, `*.tfvars` (com segredos)

---

## 4. Perfis Layer 2 planejados

| Perfil | Status | IMP | O que gera |
|--------|--------|-----|-----------|
| `k8s-helm` | 🔜 planejado | IMP-22 | `helm/Chart.yaml`, `helm/values.yaml`, deployment/service/ingress/HPA templates |
| `terraform-aws` | 🔜 planejado | IMP-23 | módulos Terraform: VPC, ECS/Lambda, RDS, IAM least privilege |

Até os perfis layer2 estarem disponíveis, o domínio `infrastructure` provê apenas o perfil core (`devops-infrastructure.prompt.md`).

---

## 5. Convenções universais do domínio

### IaC — Terraform

```hcl
# Módulos: reutilizar quando repetição ≥ 2x
module "vpc" {
  source  = "./modules/vpc"
  env     = var.env
  cidr    = var.vpc_cidr
}

# Variáveis tipadas com description
variable "env" {
  type        = string
  description = "Ambiente: dev | staging | prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env deve ser dev, staging ou prod"
  }
}

# Outputs documentados
output "vpc_id" {
  description = "ID da VPC criada"
  value       = module.vpc.vpc_id
}
```

### IaC — Helm

```yaml
# values.yaml: parametrizar o que muda por ambiente
replicaCount: 1
image:
  repository: my-app
  tag: "{{ .Chart.AppVersion }}"
  pullPolicy: IfNotPresent
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### K8s Manifests

```yaml
# Sempre incluir resources.requests e resources.limits
# Sempre incluir liveness/readiness probes
# Nunca usar `latest` como image tag em staging/prod
```

### Credenciais — Regras P0

- **NUNCA** commitar `.tfvars` com valores reais (apenas `.tfvars.example`)
- **NUNCA** hardcodar credenciais em playbooks Ansible (usar `ansible-vault`)
- AWS: usar IAM roles (não access keys) em produção
- K8s: usar `ExternalSecrets` ou `Sealed Secrets` (não `kubectl create secret` manual)
- Arquivos com segredos ficam em `.secrets/` (gitignored)

### Nomenclatura de recursos

```
# Padrão: {produto}-{componente}-{ambiente}
# Exemplos:
myapp-api-prod
myapp-db-staging
myapp-vpc-dev
```

---

## 6. Fluxo de trabalho típico

```
1. scaffold.py → cria projeto infrastructure
2. (futuro) --compose k8s-helm → cria estrutura helm/
3. (futuro) --compose terraform-aws → cria módulos terraform/
4. --infra → gera ci.yml com steps: fmt, validate, plan, security scan (tfsec/checkov)
5. terraform init → inicializar providers
6. terraform plan -out=tfplan → revisar antes de apply
7. terraform apply tfplan → executar
```

---

## 7. Checklist de segurança para infra

Antes de qualquer PR de infra, verificar:

- [ ] Nenhuma credencial hardcoded (scan com `git secrets` ou `trufflehog`)
- [ ] `terraform plan` revisado — sem destruição não intencional (`-/+` resources)
- [ ] IAM permissions seguem least privilege
- [ ] Security groups: sem `0.0.0.0/0` em portas sensíveis (SSH 22, DB 5432/3306)
- [ ] Recursos com tags: `env`, `team`, `product`, `managed-by=terraform`
- [ ] State backend configurado (S3 + DynamoDB lock, não local)
- [ ] Módulos com versão fixada (`source = "terraform-aws-modules/vpc/aws" version = "5.x.x"`)

---

## 8. Referências

- [devops-infrastructure.prompt.md](../../.github/prompts/domain/devops-infrastructure.prompt.md) — perfil machine-readable
- [DOMAIN-PROFILES-DECISIONS.md](DOMAIN-PROFILES-DECISIONS.md) — decisões de arquitetura
- [COMPATIBILITY-MATRIX.md](../COMPATIBILITY-MATRIX.md) — compatibilidade com perfis layer2
