---
name: devops-infrastructure
description: "Domain Profile — DevOps Infraestrutura. Ative declarando \"Modo: INFRASTRUCTURE.\""
---

# 🏗️ Domain Profile — DevOps Infrastructure

> **Como ativar**: no início da sessão declare:
> ```
> Modo: INFRASTRUCTURE. Projeto: [nome]. Cloud/plataforma: [aws|gcp|azure|on-prem|k8s].
> ```

---

## 🎯 Contexto do Domínio

Você está no modo **infraestrutura**. O trabalho envolve provisionar recursos, configurar ambientes, escrever IaC, operar clusters, ou gerenciar pipelines de deploy. O artefato central são **configurações declarativas** (Terraform, Helm, Kubernetes manifests, Ansible playbooks) e **ambientes funcionais**.

Diferente de código (saída é software) ou análise (saída é conhecimento), aqui a saída é **infraestrutura rodando** com SLO definido, alertas configurados e runbook documentado.

> ⚠️ **Princípio de ouro**: qualquer ação em ambiente produtivo ou staging requer confirmação explícita. O plano vem antes da execução — sempre.

---

## 📋 O que o Copilot precisa saber neste modo

Antes de qualquer tarefa, colete (via `speckit.clarify` ou declaração direta):

| Informação | Exemplos | Obrigatório? |
|------------|----------|-------------|
| **Cloud / plataforma** | AWS, GCP, Azure, on-prem, bare metal | ✅ |
| **Ambiente alvo** | dev, staging, production | ✅ |
| **Ferramenta IaC** | Terraform, Pulumi, CloudFormation, Ansible | ✅ |
| **Orquestrador** | Kubernetes (EKS/GKE/K3s), Docker Compose, Nomad | ✅ |
| **Namespace / projeto** | `monitoring`, `default`, `prod-services` | ✅ |
| **Política de acesso** | IAM roles, RBAC, service accounts | Recomendado |
| **Padrão de naming/tagging** | `env=prod,team=platform,product=X` | Recomendado |
| **Módulos IaC existentes** | onde estão, versões dos providers | Recomendado |
| **Ingress controller** | nginx, traefik, aws-alb | Se K8s |
| **Repositório de charts** | internal Harbor, ArtifactHub, Bitnami | Se Helm |

---

## 🔧 Comportamento Esperado do Copilot

### Ao planejar mudanças
- **Primeiro**: verificar o estado atual (`terraform plan`, `kubectl get`, `helm status`)
- **Nunca** supor que um recurso não existe — confirmar antes
- Apresentar plano detalhado antes de qualquer `apply` ou `helm upgrade`
- Incluir rollback plan para toda mudança em staging/prod

### Ao escrever IaC
- Terraform: usar módulos quando repetição ≥ 2x; variáveis tipadas; outputs documentados
- Helm: `helm lint` antes de qualquer proposta; parametrizar o que muda por ambiente
- K8s manifests: sempre incluir `resources.requests` e `resources.limits`
- Ansible: tasks idempotentes com `changed_when`; vault para secrets

### Ao lidar com credenciais
- **NUNCA** propor código com credenciais hardcodadas
- Usar: variáveis de ambiente, AWS SSM/Secrets Manager, K8s Secrets, Vault
- Referenciar `.secrets/` do projeto para armazenamento local (git-ignored)
- Documentar variáveis necessárias no `.env.example`

### Ao operar em produção
- Exigir confirmação explícita antes de gerar qualquer comando destrutivo
- Propor janela de manutenção para mudanças que afetam disponibilidade
- Verificar alertas configurados antes de marcar como concluído

---

## ✅ Definition of Done — Infraestrutura

Uma tarefa de infra está **concluída** quando:

### IaC (Terraform / Pulumi)
- [ ] `terraform validate` sem erros
- [ ] `terraform plan` revisado e aprovado (nenhum `destroy` surpresa)
- [ ] `terraform apply` executado com sucesso
- [ ] State remoto atualizado (S3, GCS, Terraform Cloud)
- [ ] Outputs documentados no README do módulo
- [ ] Tagging completo conforme padrão do projeto

### Kubernetes / Helm
- [ ] `helm lint` sem erros
- [ ] `kubectl apply --dry-run=server` sem erros (se manifests)
- [ ] Deploy realizado com sucesso
- [ ] Pods em estado `Running` / `Completed` (sem `CrashLoopBackOff`)
- [ ] Health check / readiness probe configurado e passando
- [ ] `kubectl rollout status` OK

### Operacional (todos)
- [ ] Alerta criado/atualizado no sistema de observabilidade (Prometheus/Grafana/Datadog)
- [ ] Runbook criado ou atualizado em `docs/`
- [ ] Change record registrado (se processo formal)
- [ ] Testado no ambiente inferior (dev → staging → prod)
- [ ] Rollback validado (testado ou pelo menos documentado)

---

## 🌍 Referência por Cloud

### AWS
```bash
# Validação antes de aplicar
aws iam simulate-principal-policy ...   # validar permissões
terraform plan -out=tfplan              # revisar mudanças
aws cloudformation validate-template    # se CFn

# Recursos mais comuns
# EC2, RDS, ECS/EKS, Lambda, S3, VPC, IAM, ALB, CloudFront
# Security Groups: princípio do menor privilégio
# IAM: usar roles, nunca users com access keys em apps
```

### Kubernetes
```bash
# Estado atual
kubectl get pods -n [namespace] -o wide
kubectl describe pod [nome] -n [namespace]
kubectl logs [pod] -n [namespace] --previous

# Deploy
kubectl apply -f manifests/ --dry-run=server
kubectl apply -f manifests/
kubectl rollout status deployment/[nome] -n [namespace]
kubectl rollout undo deployment/[nome] -n [namespace]   # rollback

# Helm
helm lint charts/[nome]/
helm upgrade --install [release] charts/[nome]/ \
  -f values/[env].yaml --dry-run
helm history [release] -n [namespace]
```

### Terraform
```bash
# Ciclo padrão
terraform fmt -recursive
terraform validate
terraform plan -out=tfplan -var-file=envs/[env].tfvars
terraform show tfplan                  # revisar antes de aplicar
terraform apply tfplan
terraform output                       # verificar outputs
```

### Docker / Compose
```bash
hadolint Dockerfile                    # lint
docker build -t [imagem]:[tag] .
docker-compose config                  # validar docker-compose.yml
docker-compose up -d
docker-compose ps                      # verificar status
docker-compose logs -f [serviço]
```

### Ansible
```bash
ansible-lint playbooks/                # lint
ansible-playbook playbooks/[nome].yml --check   # dry-run
ansible-playbook playbooks/[nome].yml -vv       # verbose
```

---

## 🔒 Segurança — Checklist Mínimo

Para qualquer recurso em staging ou prod:

- [ ] Princípio do menor privilégio nas IAM roles / RBAC
- [ ] Portas expostas minimizadas (nenhuma porta desnecessária para 0.0.0.0/0)
- [ ] Secrets não em variáveis de ambiente planas — usar secrets manager
- [ ] TLS/HTTPS habilitado para todos os endpoints externos
- [ ] Logs de auditoria habilitados (CloudTrail, K8s audit log)
- [ ] Backup configurado para dados persistentes

---

## 🔀 Cruzamento com Outros Domínios (D-09)

```
Modo: INFRASTRUCTURE (primário).
Contexto secundário: o módulo Terraform usa um Lambda escrito em Python.
Para o código do Lambda, aplicar regras do modo PROGRAMMING:
- testes unitários, type hints, black formatter.
- O Dockerfile deve passar no hadolint.
```

---

## ⚠️ Anti-Patterns — Nunca Fazer

| ❌ Proibido | ✅ Correto |
|------------|-----------|
| `terraform apply` sem revisar o plan | Sempre `plan` antes, ler cada `+/-/~` |
| Security Groups com `0.0.0.0/0` sem justificativa | Especificar CIDR necessário |
| Secrets em variáveis de ambiente no pod spec | K8s Secret + secretRef |
| Módulos Terraform sem `versions.tf` | Fixar versão do provider |
| Deploy direto em prod sem staging | Sempre staging → prod |
| Imagens Docker sem tag de versão (`:latest`) | Tag semântica ou SHA |
| Recursos sem tags de ownership/ambiente | Tagging obrigatório |
| `kubectl exec` em prod para "consertar" estado | Corrigir IaC, não o pod |

---

## 🗓️ Ritual de Sessão

### Início
```
Modo: INFRASTRUCTURE. Projeto: [nome].
Cloud: [aws|gcp|azure|on-prem]. Ambiente: [dev|staging|prod].
Ferramenta IaC: [terraform|helm|ansible].
Objetivo desta sessão: [1 frase].
```

### Durante
- Documentar cada mudança aplicada no `docs/TODAY_ACTIVITIES.md`
- `terraform plan` / `helm upgrade --dry-run` antes de qualquer apply
- Screenshot ou output de cada `kubectl rollout status` OK

### Encerramento
- Verificar alertas ativos
- Atualizar runbook se comportamento mudou
- `git push` com IaC atualizado
- Registrar change em `docs/TODO.md`

---

---

## 🔍 Modo Review — Revisão de IaC e Configurações

> Ative com: `Modo: INFRASTRUCTURE + REVIEW. Escopo: [terraform|helm|k8s|ansible|dockerfile].`

### Processo
1. Declarar claramente o escopo (terraform module, helm chart, namespace específico)
2. Verificar estado atual antes de comentar (`terraform show`, `helm status`, `kubectl get`)
3. Classificar achados por severidade (mesmo padrão do modo PROGRAMMING + REVIEW)

### Checklist de IaC Review

- [ ] **Segurança**: IAM least-privilege, portas mínimas expostas, TLS habilitado, secrets via Vault/SSM?
- [ ] **Idempotência**: `apply` repetido produz o mesmo estado?
- [ ] **Recursos com limites**: K8s tem `resources.requests`/`limits`; RDS tem Multi-AZ se prod?
- [ ] **Tagging/labeling**: padrão de tags aplicado (env, team, product)?
- [ ] **Rollback**: mudança é revertível? Runbook de rollback documentado?
- [ ] **Estado remoto**: backend configurado (não local) para Terraform?
- [ ] **Hardcode de ambiente**: valores de dev não foram deixados em valores de prod?
- [ ] **Secrets em código**: nenhuma credencial hardcodada em values.yaml, tfvars, playbooks?

### Formato de Comentário

```
[BLOCKER] terraform/modules/s3/main.tf:28
O bucket está com `acl = "public-read"`. Qualquer dado armazenado
neste bucket fica acessível publicamente.
Correção: remover `acl` e usar bucket policy restritiva. Adicionar
`block_public_acls = true` no `aws_s3_bucket_public_access_block`.
```

---

## 🔗 Referências

- [.copilot-rules.md](../../../.copilot-rules.md) — Regras base da Camada 1 (sempre prevalecem)
- [docs/copilot/DOMAIN-PROFILES-STRATEGY.md](../../../docs/copilot/DOMAIN-PROFILES-STRATEGY.md)
- `.copilot-rules-[projeto].md` — Regras específicas do projeto ativo
- `.secrets/` — Credenciais locais (git-ignored)

---

*Domain Profile v1.1 | Atualizado em 2026-03-05 | IMP-06 + IMP-14 (A.7)*
