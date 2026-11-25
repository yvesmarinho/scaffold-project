---
name: k8s-helm
description: "Layer 3 Profile — Kubernetes + Helm. Ative declarando 'Modo: K8S-HELM. Projeto: [nome].'"
---

# ⎈ Layer 3 Profile — Kubernetes + Helm

> **Como ativar**: no início da sessão declare:
> ```
> Modo: K8S-HELM. Projeto: [nome]. Cluster: [eks|gke|k3s|minikube]. Namespace: [namespace].
> ```
> Este perfil complementa `devops-infrastructure` — ambos devem estar ativos.

---

## 🎯 Contexto do Perfil

Você está no modo **Kubernetes + Helm**. O trabalho envolve empacotar, configurar e operar aplicações em clusters Kubernetes usando Helm como gerenciador de releases. O foco é em:

- **Parametrização por ambiente**: values.yaml base + overrides staging/prod
- **Segurança por padrão**: non-root, readOnlyRootFilesystem, sem hardcode de segredos, TLS habilitado
- **Observabilidade**: liveness/readiness probes obrigatórios, recursos definidos
- **Idempotência**: `helm upgrade --install` como padrão — o mesmo comando instala ou atualiza

Diferente de escrever manifests Kubernetes raw, este perfil usa Helm para parametrização e gerenciamento de ciclo de vida (install, upgrade, rollback, uninstall).

---

## 📋 O que o Copilot precisa saber neste modo

| Informação | Exemplos | Obrigatório? |
|------------|----------|-------------|
| **Cluster / distribuição** | EKS 1.29, GKE Autopilot, K3s, minikube | ✅ |
| **Namespace** | `default`, `prod-services`, `monitoring` | ✅ |
| **Ingress controller** | nginx-ingress, traefik, aws-alb | ✅ |
| **Porta da aplicação** | `8000` (FastAPI), `3000` (Next.js), `8080` (Go) | ✅ |
| **Health endpoint** | `/api/health`, `/healthz`, `/health` | ✅ |
| **Gestão de segredos** | ExternalSecrets, sealed-secrets, Vault, manual | Recomendado |
| **Registry de imagens** | AWS ECR, GCR, Docker Hub, Harbor | Recomendado |
| **TLS management** | cert-manager + Let's Encrypt, AWS ACM, manual | Recomendado |
| **Domínio** | `my-app.example.com`, `api.prod.company.com` | Recomendado |
| **HPA habilitado** | sim (prod), não (dev/staging) | Opcional |

---

## 🏗️ Estrutura do Chart

```
{project_name}/
├── helm/
│   ├── Chart.yaml                  # Metadata: name, version, appVersion
│   ├── values.yaml                 # Defaults completos (todos os campos documentados)
│   ├── values-staging.yaml         # Overrides staging: réplica 1, recursos reduzidos
│   ├── values-prod.yaml            # Overrides prod: réplica 2, HPA habilitado
│   └── templates/
│       ├── _helpers.tpl            # Named templates: fullname, labels, selectorLabels
│       ├── deployment.yaml         # Deployment com probes, resources, envFrom configmap
│       ├── service.yaml            # Service ClusterIP / LoadBalancer
│       ├── ingress.yaml            # Ingress com TLS (condicional)
│       ├── hpa.yaml                # HPA autoscaling/v2 (condicional)
│       ├── configmap.yaml          # ConfigMap para env vars não-sensíveis
│       ├── serviceaccount.yaml     # ServiceAccount (condicional)
│       └── NOTES.txt               # URL de acesso pós-instalação
├── .helmignore                     # Padrões ignorados pelo helm package
└── Makefile.helm                   # Targets: lint, dry-run, install, upgrade, diff, rollback
```

---

## 🔧 Comportamento Esperado do Copilot

### Ao criar Chart novo
- Usar `helm/` como diretório padrão (não `charts/`)
- Chart.yaml: `apiVersion: v2`, version semântica, appVersion separada da chart version
- Todos os campos de values.yaml devem ter comentário explicativo
- Parametrizar o que muda por ambiente — nunca hardcodar host, porta ou réplicas

### Ao configurar Deployment
- Sempre incluir `resources.requests` e `resources.limits` — sem eles o scheduler não tem baseline
- Liveness/readiness obrigatórios — sem probes o K8s não sabe se o pod está saudável
- `securityContext.runAsNonRoot: true` e `allowPrivilegeEscalation: false` por padrão
- Usar `envFrom: configMapRef` para vars não-sensíveis; **nunca** `env[].value` com segredos

### Ao configurar Ingress
- TLS habilitado por padrão — gerar entrada em `ingress.tls[]` mesmo que vazia
- Anotar corretamente para o ingress controller do cluster (`nginx.ingress.kubernetes.io/...`)
- Sempre parametrizar o host via `values.yaml` — nunca hardcodar

### Ao gerenciar segredos
- **NUNCA** colocar valores de segredos em values.yaml — nem comentado
- Recomendar ExternalSecrets (AWS Secrets Manager / Vault) em produção
- Para dev local: `kubectl create secret generic` documentado em RUNBOOK
- `sealed-secrets` para GitOps (segredos cifrados commitáveis)

### Ao fazer upgrade
- Sempre rodar `helm-dry-run` antes de `helm-upgrade` em staging/prod
- Verificar `helm-diff` para visualizar mudanças nos manifests
- Incluir `--wait` para aguardar pods ficarem prontos
- Documentar rollback: `helm rollback {release} --namespace {ns}`

### Ao lidar com HPA
- HPA desabilitado por padrão em staging (reduz complexidade de debugging)
- Em produção: min ≥ 2 réplicas para alta disponibilidade
- `apiVersion: autoscaling/v2` (não v2beta2 — depreciada em K8s 1.26+)

---

## ⚠️ Anti-patterns — nunca propor

| Anti-pattern | Por quê | Alternativa |
|--------------|---------|-------------|
| `imagePullPolicy: Always` em prod | Dependência de registry no restart | `IfNotPresent` + tags imutáveis |
| Sem `resources.limits` | Pod pode consumir todo nó | Sempre definir limits |
| Sem `readinessProbe` | Pod recebe tráfego antes de estar pronto | Probe HTTP no health endpoint |
| `runAsUser: 0` (root) | Execução privilegiada no container | `runAsNonRoot: true` + `runAsUser: 1000` |
| Segredos em values.yaml | Versionado em Git = credenciais expostas | ExternalSecrets / sealed-secrets |
| `tag: latest` | Builds não-reprodutíveis | Tag semântica ou digest SHA |
| `automountServiceAccountToken: true` | Expõe token K8s ao pod desnecessariamente | `false` por padrão |
| HPA sem `minReplicas ≥ 2` em prod | Single point of failure | `minReplicas: 2` |

---

## 🔗 Compatibilidade de Perfis

Este perfil **Layer 3** pode ser composto com qualquer perfil Layer 2 de programação:

| Perfil Layer 2 | Porta padrão | Health endpoint | Compatível? |
|----------------|:-----------:|:---------------:|:-----------:|
| `python-fastapi` | `8000` | `/api/health` | ✅ |
| `python-flask` | `5000` | `/api/health` | ✅ |
| `typescript-next` | `3000` | `/api/health` | ✅ |
| `go-chi` (planejado) | `8080` | `/health` | ✅ (futuro) |

---

## 📖 Referências

- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Kubernetes Security Context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [devops-infrastructure](../devops-infrastructure/SKILL.md) — perfil base de infra
- [docs/copilot/DOMAIN-INFRASTRUCTURE.md](../../docs/copilot/DOMAIN-INFRASTRUCTURE.md) — guia humano
