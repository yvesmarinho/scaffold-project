# Objetivo Wizard — Exemplos para Copy/Paste

**Guia rápido**: Respostas prontas para preencher o wizard `objetivo-init` de forma rápida.

Copie e cole as respostas abaixo durante a execução interativa do wizard.

---

## 📋 Metadados do Projeto


### Nome do Projeto (kebab-case)
```
sistema-deploy-automatizado
```

### Título do Projeto
```
Sistema de Deploy Automatizado para Plataforma Cloud
```
### Pasta do projeto
```
/home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project/poc
```

### Tipo de Iniciativa
```
new
```
*Opções: `new` (novo) | `update` (melhoria)*

### Domínio Primário
```
devops
```
*Opções: `programming` | `infrastructure` | `security` | `data` | `devops`*

### Linguagem Principal
```
python
```
*Opções: `python` | `typescript` | `go` | `terraform` | `java` | `rust`*

### Criado Por
```
Yves Marinho
```

---

## 🎯 Q1: O que este projeto faz? (P0 — Obrigatório)

**Prompt**: *O que este projeto faz? (descreva em 1 frase clara)*

### Exemplo 1 — Sistema de Deploy
```
Sistema automatizado de deploy que permite equipes DevOps configurar e executar deploys via interface web/CLI, com rollback automático em caso de falha e monitoramento integrado.
```

### Exemplo 2 — API de Gestão
```
API REST para gestão de inventário que centraliza dados de produtos, fornecedores e pedidos com sincronização em tempo real e relatórios analíticos.
```

### Exemplo 3 — Data Pipeline
```
Pipeline de processamento de dados que extrai informações de múltiplas fontes (APIs, DBs, arquivos), transforma via dbt e carrega em data warehouse para análise de BI.
```

---

## 🔄 Q2: Qual problema está sendo melhorado? (P0 Condicional)

**Prompt**: *Qual limitação/problema atual está sendo melhorado? (1-2 parágrafos)*

**IMPORTANTE**: Apenas para `tipo_iniciativa: update`. Deixe em branco se for `new`.

### Exemplo — Melhoria de Sistema Legado
```
Sistema atual: deploys manuais levam 2-3h com 15% de taxa de erro. Performance degrada em 50% durante picos de acesso, causando perda de receita de ~R$ 30k/mês. Falta automação, padronização e observabilidade adequada.

Equipe gasta 40h/mês em troubleshooting de deploys falhados, documentação desatualizada dificulta onboarding de novos membros (3-4 semanas), e ausência de rollback automático já causou 2 incidents P0 nos últimos 6 meses.
```

---

## ✅ Q3: O que está NO escopo? (P0 — Obrigatório, Multiline)

**Prompt**: *O que está NO escopo? (liste features incluídas, Enter vazio para terminar)*

**IMPORTANTE**:
- Digite cada feature em uma linha separada
- Pressione Enter DUAS VEZES para finalizar
- Indique prioridade: (P0), (P1), (P2)

### Exemplo 1 — Sistema de Deploy (6 features)
```
Processamento automático de deploy com validação de pré-requisitos (P0)
Interface web para configuração e monitoramento de deploys (P1)
API REST para integração com CI/CD pipelines (P0)
Sistema de rollback automático baseado em health checks (P0)
Notificações por email/Slack em eventos críticos (P2)
Dashboard de métricas e histórico de deploys (P1)
```

### Exemplo 2 — API de Gestão (4 features)
```
CRUD completo de produtos, fornecedores e pedidos (P0)
Sistema de autenticação e autorização via OAuth2 + RBAC (P0)
Sincronização em tempo real com sistema ERP legado (P1)
Geração de relatórios mensais em PDF (P2)
```

### Exemplo 3 — Infraestrutura (3 features)
```
Provisionamento automatizado de clusters Kubernetes via Terraform (P0)
Monitoramento centralizado com Prometheus + Grafana (P0)
Backup automatizado de bancos de dados PostgreSQL (P1)
```

---

## 🚧 Q4: Restrições técnicas? (P1 — Opcional, Multiline)

**Prompt**: *Há restrições técnicas? (performance, segurança, compliance — Enter vazio para pular)*

**IMPORTANTE**: Pressione Enter DUAS VEZES para finalizar, ou apenas Enter vazio para pular.

### Exemplo 1 — Completo (6 restrições)
```
Budget: R$ 80k para desenvolvimento + R$ 5k/mês infraestrutura
Prazo: 4 meses para MVP (3 sprints de 4 semanas)
Compatibilidade obrigatória com LGPD e SOC2
Performance: API deve responder em <200ms p95
Disponibilidade: 99.9% SLA (máx 43min downtime/mês)
Segurança: autenticação via OAuth2 + RBAC, secrets em Vault
```

### Exemplo 2 — Mínimo (3 restrições)
```
Budget: R$ 30k total
Prazo: 2 meses
Deve seguir padrões PCI-DSS para processar pagamentos
```

### Exemplo 3 — Pular
```
[Pressione Enter vazio para pular]
```

---

## 📜 Q5: Regras de negócio complexas? (P1 — Opcional, Multiline)

**Prompt**: *Há regras de negócio complexas? (Enter vazio para pular)*

**IMPORTANTE**: Pressione Enter DUAS VEZES para finalizar, ou apenas Enter vazio para pular.

### Exemplo 1 — Sistema de Deploy (6 regras)
```
Apenas usuários com role 'deployer' podem executar deploys em produção
Deploys em produção requerem aprovação de 2 reviewers
Janela de deploy em produção: seg-qui 9h-17h, sexta até 15h
Rollback automático se >5% de health checks falharem em 2min
Logs de deploy devem ser retidos por 2 anos (compliance)
Rate limit: máximo 10 deploys simultâneos por cluster
```

### Exemplo 2 — E-commerce (4 regras)
```
Usuários premium têm acesso a features avançadas e frete grátis
Dados de clientes devem ser retidos por 7 anos (LGPD)
Cálculo de desconto progressivo: 10% para >100 unidades, 20% para >1000
Estoque reservado por 15min durante checkout, depois liberado
```

### Exemplo 3 — Pular
```
[Pressione Enter vazio para pular]
```

---

## 🛠️ Q6: Tipo de solução técnica (P0 — Obrigatório)

**Prompt**: *Tipo de solução técnica (linguagem, framework, padrões)*

### Exemplo 1 — Python/FastAPI (Backend)
```
código Python 3.11+ com FastAPI, PostgreSQL para persistência, Redis para cache/queue, Celery para tasks assíncronas, Docker/Kubernetes para deploy, padrão hexagonal/clean architecture
```

### Exemplo 2 — TypeScript/Next.js (Frontend)
```
código TypeScript com Next.js 14, React Server Components, TailwindCSS para estilização, Zustand para state management, deploy em Vercel/AWS CloudFront
```

### Exemplo 3 — Terraform/AWS (Infraestrutura)
```
infraestrutura como código com Terraform 1.6+, provisionamento em AWS (EKS, RDS, S3, CloudFront), módulos reutilizáveis, remote state no S3+DynamoDB
```

### Exemplo 4 — Data Engineering
```
pipeline de dados com Apache Airflow, transformações em dbt, armazenamento em Snowflake/BigQuery, orquestração com Kubernetes, monitoramento com Great Expectations
```

---

## 📖 Q7: Padrão de documentação (P1 — Opcional)

**Prompt**: *Padrão de documentação (Enter vazio para pular)*

### Exemplo 1 — Python
```
Google Style Docstrings com type hints completos, Sphinx para geração de docs, ADRs para decisões arquiteturais, OpenAPI/Swagger para documentação de API
```

### Exemplo 2 — TypeScript
```
TSDoc comments em todos os exports públicos, Storybook para componentes React, README.md com setup e troubleshooting
```

### Exemplo 3 — Infraestrutura
```
Terraform docs auto-gerados via terraform-docs, runbooks em Markdown, diagramas de arquitetura em Draw.io/Mermaid
```

### Exemplo 4 — Pular
```
[Pressione Enter vazio para pular]
```

---

## 🏗️ Q8: Infraestrutura necessária (P1 — Opcional, Multiline)

**Prompt**: *Infraestrutura necessária (servidores, DBs, containers)*

**IMPORTANTE**: Pressione Enter DUAS VEZES para finalizar, ou apenas Enter vazio para pular.

### Exemplo 1 — Cloud AWS (6 componentes)
```
Cluster Kubernetes 1.28+ em AWS EKS (3 nodes t3.medium)
Banco PostgreSQL 15 em RDS (db.t3.medium, 100GB storage)
Redis 7.x em ElastiCache (cache.t3.micro)
S3 bucket para artefatos de deploy e backups
CloudWatch/Prometheus para monitoramento
Application Load Balancer com WAF habilitado
```

### Exemplo 2 — On-Premise (4 componentes)
```
Servidor PostgreSQL em wfdb02.vya.digital (16GB RAM, 500GB SSD)
Aplicação em container Docker no wf001 (8GB RAM, 4 cores)
NGINX como reverse proxy e load balancer
Backup diário para NAS local (2TB disponível)
```

### Exemplo 3 — Minimal (2 componentes)
```
Docker Compose local para desenvolvimento
PostgreSQL 15 em container
```

### Exemplo 4 — Pular
```
[Pressione Enter vazio para pular]
```

---

## 👥 Q9: Perfis/roles necessários (P1 — Opcional, Multiline)

**Prompt**: *Perfis/roles necessários (dba, devops, etc)*

**IMPORTANTE**: Pressione Enter DUAS VEZES para finalizar, ou apenas Enter vazio para pular.

**Nota**: Este campo NÃO está no template atual, respostas serão ignoradas.

### Exemplo 1 — Equipe Completa (5 roles)
```
backend-architect (Python/FastAPI expert, senior 5+ anos)
devops-engineer (K8s/AWS expert, senior 3+ anos)
database-expert (PostgreSQL performance tuning, pleno 2+ anos)
qa-automation (pytest/integration tests, pleno)
tech-writer (documentação técnica, júnior)
```

### Exemplo 2 — Solo Developer
```
full-stack-developer (Python + TypeScript, senior 3+ anos)
```

### Exemplo 3 — Pular
```
[Pressione Enter vazio para pular]
```

---

## 🎯 Q10: Resultados esperados mensuráveis (P0 — Obrigatório, Multiline)

**Prompt**: *Resultados esperados mensuráveis*

**IMPORTANTE**:
- Digite cada resultado em uma linha separada
- Pressione Enter DUAS VEZES para finalizar
- Use métricas quantificáveis

### Exemplo 1 — Sistema de Deploy (8 resultados)
```
100% dos deploys via sistema automatizado (zero deploys manuais)
Tempo médio de deploy reduzido de 2-3h para <15min
Taxa de erro de deploy reduzida de 15% para <2%
Rollback automático em <5min quando necessário
Economia operacional de R$ 30k/mês em horas-homem
Aumento de 50% na frequência de deploys (de 10/mês para 15/mês)
SLA de 99.9% alcançado consistentemente
Zero incidentes de segurança relacionados a deploys
```

### Exemplo 2 — API de Gestão (5 resultados)
```
API respondendo em <100ms p95 para 95% das requisições
Cobertura de testes automatizados >80%
Onboarding de novos desenvolvedores reduzido de 3 semanas para 5 dias
Sincronização com ERP em <30s após mudanças
Zero exposição de dados sensíveis (compliance LGPD)
```

### Exemplo 3 — Data Pipeline (4 resultados)
```
100% dos dados migrados com zero erros de FK
Tempo de migração <2h para dataset de 10M registros
Pipeline executando 3x/dia com <5% de falhas
Redução de 70% no tempo de geração de relatórios (de 1h para 20min)
```

### Exemplo 4 — Minimal (3 resultados)
```
Sistema funcional com todas as features P0 implementadas
Testes automatizados passando com >70% cobertura
Documentação básica (README + API docs) completa
```

---

## 🚀 Exemplo de Execução Completa

```bash
$ python3 scripts/scaffold.py objetivo-init

# Responda cada pergunta copiando e colando os textos acima
# Após multiline (Q3, Q4, Q5, Q8, Q9, Q10), pressione Enter DUAS VEZES

✅ Arquivo gerado: objetivo-init.yaml
```

---

## 📝 Dicas de Uso

### Para Pular Questões Opcionais (P1)
- **Q2**: Apenas Enter (se for projeto `new`)
- **Q4**: Apenas Enter (se não houver restrições)
- **Q5**: Apenas Enter (se não houver regras complexas)
- **Q7**: Apenas Enter (se não especificar padrão de doc)
- **Q8**: Apenas Enter (se infraestrutura for trivial)
- **Q9**: Apenas Enter (perfis serão ignorados)

### Para Questões Multiline
1. Cole TODAS as linhas de uma vez (Ctrl+Shift+V)
2. Pressione Enter DUAS VEZES para finalizar
3. Se errar, Ctrl+Z desfaz última resposta

### Para Projetos Diferentes
- **Microserviço**: Use Exemplo 1 (Python/FastAPI)
- **Frontend SPA**: Use Exemplo 2 (TypeScript/Next.js)
- **Infraestrutura**: Use Exemplo 3 (Terraform)
- **Data Engineering**: Use Exemplo 4 (Airflow/dbt)

---

## 📚 Templates por Tipo de Projeto

### Template: Microserviço Backend
- **Q1**: API REST para [domínio] com autenticação e [features principais]
- **Q3**: CRUD completo, autenticação OAuth2, integração com [sistemas], monitoramento
- **Q6**: Python 3.11+ FastAPI, PostgreSQL, Redis, Docker/K8s
- **Q8**: EKS, RDS, ElastiCache, CloudWatch

### Template: Frontend Web
- **Q1**: Interface web para [domínio] com [funcionalidades UX]
- **Q3**: Páginas de [listagem/cadastro/detalhes], autenticação, responsividade mobile
- **Q6**: TypeScript Next.js, TailwindCSS, Zustand, Vercel
- **Q8**: Vercel/CloudFront, CDN, analytics

### Template: Pipeline de Dados
- **Q1**: Pipeline ETL que [extrai de onde], [transforma como] e [carrega onde]
- **Q3**: Extração de [fontes], transformação [dbt/Spark], qualidade de dados, agendamento
- **Q6**: Python Airflow, dbt, Snowflake/BigQuery, Great Expectations
- **Q8**: Airflow em K8s, Snowflake cluster, S3 staging

### Template: Infraestrutura como Código
- **Q1**: Provisionamento automatizado de [recursos] em [cloud provider]
- **Q3**: Terraform modules para [recursos], CI/CD para infra, monitoring setup
- **Q6**: Terraform 1.6+, módulos AWS/GCP/Azure, remote state S3
- **Q8**: AWS Control Tower, S3 state backend, CloudFormation drift detection

---

**Última atualização**: 2026-04-29
**Versão**: 1.0 (compatível com objetivo-init wizard v2.0)
