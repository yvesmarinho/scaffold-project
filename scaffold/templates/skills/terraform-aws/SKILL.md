---
name: terraform-aws
description: "Layer 3 Profile — Terraform AWS. Ative declarando 'Modo: TERRAFORM-AWS. Projeto: [nome].'"
---

# 🌍 Layer 3 Profile — Terraform AWS

> **Como ativar**: no início da sessão declare:
> ```
> Modo: TERRAFORM-AWS. Projeto: [nome]. Env: [dev|staging|prod]. Region: [us-east-1|sa-east-1|...].
> ```
> Este perfil complementa `devops-infrastructure` — ambos devem estar ativos.

---

## 🎯 Contexto do Perfil

Você está no modo **Terraform AWS**. O trabalho envolve provisionar e gerenciar infraestrutura na AWS usando Terraform com módulos reutilizáveis. O foco é em:

- **Módulos reutilizáveis**: VPC, ECS Fargate, RDS PostgreSQL — parametrizados por ambiente
- **IAM Least Privilege**: toda role com apenas as permissões mínimas necessárias — nunca `Resource: "*"` em serviços sensíveis
- **State remoto**: S3 + DynamoDB locking — nunca state local em produção
- **Segurança por padrão**: RDS sem `publicly_accessible`, SGs com ingress mínimo, encryption at rest

Diferente de escrever manifests Kubernetes, aqui o artefato é infraestrutura AWS declarada em HCL com ciclo `plan → review → apply`.

---

## 📋 O que o Copilot precisa saber neste modo

| Informação | Exemplos | Obrigatório? |
|------------|----------|-------------|
| **Região AWS** | `us-east-1`, `sa-east-1`, `us-west-2` | ✅ |
| **Ambiente alvo** | `dev`, `staging`, `prod` | ✅ |
| **Conta AWS** | ID da conta (para ARNs de IAM) | ✅ |
| **State backend** | S3 bucket + DynamoDB table já existentes | ✅ |
| **Módulos a usar** | vpc, ecs, rds, lambda — quais são necessários | ✅ |
| **CIDR VPC** | `10.0.0.0/16`, `172.16.0.0/16` | Recomendado |
| **Container image** | Registry URL + tag | Recomendado (se ECS) |
| **DB instance class** | `db.t3.micro` (staging), `db.t3.medium` (prod) | Recomendado (se RDS) |
| **Domínio / ACM cert** | ARN do certificado TLS | Recomendado (se ALB) |
| **Tags obrigatórias** | `env`, `team`, `product`, `managed-by` | Recomendado |

---

## 🏗️ Estrutura de Módulos

```
{project_name}/
├── terraform/
│   ├── versions.tf              # required_providers (aws, random) com versões fixadas
│   ├── main.tf                  # módulos vpc + ecs + rds (condicionais)
│   ├── variables.tf             # variáveis tipadas com description e validation
│   ├── outputs.tf               # outputs documentados (vpc_id, alb_dns, db_endpoint)
│   ├── modules/
│   │   ├── vpc/
│   │   │   ├── main.tf          # VPC, subnets públicas/privadas, IGW, NAT, route tables
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   ├── ecs/
│   │   │   ├── main.tf          # ECS Fargate cluster, task def, service, ALB, IAM roles
│   │   │   ├── variables.tf
│   │   │   └── outputs.tf
│   │   └── rds/
│   │       ├── main.tf          # RDS PostgreSQL, subnet group, SG, no public access
│   │       ├── variables.tf
│   │       └── outputs.tf
│   └── envs/
│       ├── staging.tfvars.example   # valores staging sem dados reais
│       └── prod.tfvars.example      # valores prod sem dados reais
└── Makefile.terraform           # targets: init, fmt, validate, plan, apply, destroy, scan
```

---

## 🔧 Comportamento Esperado do Copilot

### Ao escrever módulos Terraform

- **Variáveis sempre tipadas**: `type = string`, `type = number`, `type = bool`, `type = list(string)`, etc.
- **Validações no lugar certo**: `validation { condition = ... error_message = ... }` para enums (env, region)
- **Descriptions obrigatórias** em toda variável e output — são a documentação gerada
- **Versões fixadas**: `version = "~> 5.0"` no `required_providers` — nunca sem versão
- **Reutilizar antes de criar**: preferir `terraform-aws-modules/*` quando o módulo for estável e bem mantido

### Ao configurar IAM

```hcl
# ✅ CORRETO — recurso específico
resource "aws_iam_role_policy" "ecs_task_s3" {
  policy = jsonencode({
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject"]
      Resource = ["arn:aws:s3:::${var.s3_bucket_name}/*"]
    }]
  })
}

# ❌ ERRADO — nunca fazer
# Resource = ["*"]  # para S3, SSM, Secrets Manager, etc.
```

### Ao configurar networking

- VPC com subnets **públicas** para ALB/NAT e **privadas** para ECS tasks e RDS
- Security Groups com ingress mínimo: ECS apenas da SG do ALB, RDS apenas da SG do ECS
- Sem `0.0.0.0/0` em portas de banco (5432, 3306, 1433)
- NAT Gateway em subnets públicas para saída de tráfego das subnets privadas

### Ao gerenciar state

- Backend S3 com `encrypt = true` e bucket versioning habilitado
- DynamoDB table para locking (evitar apply simultâneo)
- Nunca commitar `*.tfstate` ou `*.tfstate.backup` — `.gitignore` obrigatório
- Workspaces ou diretórios separados por ambiente (preferir diretórios — mais explícito)

### Ao planejar mudanças

- **Sempre** rodar `make tf-plan` antes de propor `make tf-apply`
- Analisar recursos com `-/+` (replace) — costumam causar downtime
- Para mudanças em produção: incluir `--target` para aplicação gradual quando possível
- Documentar rollback: o Terraform não tem rollback nativo — documentar como restaurar

### Ao criar recursos de banco (RDS)

- `publicly_accessible = false` sempre
- `storage_encrypted = true` sempre
- `deletion_protection = true` em produção
- `backup_retention_period ≥ 7` em produção
- Password via `aws_secretsmanager_secret` ou `random_password` + SSM — nunca em `.tfvars`

---

## ⚠️ Anti-patterns — nunca propor

| Anti-pattern | Por quê | Alternativa |
|--------------|---------|-------------|
| `Resource: "*"` em IAM para S3/SSM/Secrets | Sobre-permissão | ARN específico do recurso |
| `publicly_accessible = true` em RDS | Expõe banco à internet | `false` + bastion ou VPN |
| Password de RDS em `.tfvars` | Segredo em VCS | `random_password` + SSM Parameter Store |
| State local (`terraform.tfstate`) em produção | Sem lock, sem history | Backend S3 + DynamoDB |
| `version = "latest"` ou sem versão em providers | Builds não-reprodutíveis | `version = "~> X.Y"` |
| `0.0.0.0/0` em Security Group ingress de banco | DB exposto | Apenas SG do ECS/Lambda |
| `deletion_protection = false` em RDS prod | Deleção acidental | `true` em prod |
| AMI hardcoded | Quebra em nova região ou deprecação | Data source `aws_ami` |

---

## 🔗 Compatibilidade de Perfis

Este perfil **Layer 3** pode ser composto com qualquer perfil Layer 2 de programação:

| Perfil Layer 2 | Protocol | Porta | Compatível? |
|----------------|:--------:|:-----:|:-----------:|
| `python-fastapi` | HTTP | `8000` | ✅ |
| `python-flask` | HTTP | `5000` | ✅ |
| `typescript-next` | HTTP | `3000` | ✅ |
| `go-chi` (planejado) | HTTP | `8080` | ✅ (futuro) |

---

## 📖 Referências

- [Terraform AWS Provider v5 Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Security Best Practices for IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [devops-infrastructure](../devops-infrastructure/SKILL.md) — perfil base de infra
- [docs/copilot/DOMAIN-INFRASTRUCTURE.md](../../docs/copilot/DOMAIN-INFRASTRUCTURE.md) — guia humano
