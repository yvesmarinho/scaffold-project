# QUICKSTART — Enterprise Scaffold Project Template

> **3 minutos para o seu primeiro projeto.**
> Guia direto ao ponto: pré-requisitos, primeiro uso e fluxos mais comuns.

---

## 🚀 Via Rápida (Comando Global)

### 1. Instalar comando global (uma vez)

```bash
# Clone o template
git clone <url-do-repositorio> scaffold-project
cd scaffold-project

# Instalar comando global
cp scripts/bin/new-project ~/.local/bin/new-project
chmod +x ~/.local/bin/new-project
```

### 2. Criar projeto (de qualquer lugar)

```bash
# Quick start Python
new-project my-api

# Com perfil específico
new-project my-api --compose python-fastapi

# Ver opções
new-project --help
new-project --list-profiles
```

📖 **Guia completo**: [docs/NEW_PROJECT_COMMAND.md](docs/NEW_PROJECT_COMMAND.md)

---

## 📘 Via Tradicional (Scaffold Direto)

### Pré-requisitos

| Requisito | Versão mínima | Instalação |
|-----------|--------------|------------|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| uv | 0.5+ | `pip install uv` ou `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| git | 2.38+ | `sudo apt install git` / `brew install git` |

Verifique rapidamente:

```bash
python --version   # Python 3.10+
uv --version       # uv 0.5+
git --version      # git 2.38+
```

### GitHub Token (Opcional — para MCP GitHub Server)

O servidor MCP `github` permite ao Copilot criar issues, PRs, buscar código e comentar em threads.

**Se você NÃO configurar**:
- ✅ Servidores `memory`, `sequential-thinking`, `filesystem` funcionam normalmente
- ❌ Servidor `github` não inicia (falha graciosamente)

**Para ativar**:

1. **Criar token**: https://github.com/settings/tokens
   - Scopes necessários: `repo`, `read:org`
   - Tipo: Personal Access Token (classic)

2. **Exportar variável de ambiente**:
   ```bash
   # Linux/macOS (adicionar ao ~/.bashrc ou ~/.zshrc)
   echo 'export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."' >> ~/.bashrc
   source ~/.bashrc

   # Ou usar arquivo .secrets/.env (recomendado para projetos)
   echo 'GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...' >> .secrets/.env
   ```

3. **Restart VS Code** para carregar a variável

**Verificar se funciona**:
```bash
# No terminal do VS Code
echo $GITHUB_PERSONAL_ACCESS_TOKEN  # Deve mostrar seu token
```

📖 **Mais detalhes**: `.vscode/mcp.json` (comentários inline)

---

## Passo 1 — Clonar o template

```bash
git clone <url-do-repositorio> scaffold-project
cd scaffold-project
```

---

## Passo 2 — Ver perfis disponíveis

```bash
python scripts/scaffold.py --list-profiles
```

Saída esperada (12 perfis):

```
┌──────────────────────────┬────────────────┬────────┬──────────────────┬──────────
│ Nome                     │ Layer          │ Versão │ Última validação │ Descrição
├──────────────────────────┼────────────────┼────────┼──────────────────┼──────────
│ devops-programming       │ core           │ 1.0.0  │ 2026-03-07       │ Perfil ba
│ devops-infrastructure    │ core           │ 1.0.0  │ 2026-03-14       │ Perfil ba
│ devops-analysis          │ core           │ 1.0.0  │ 2026-03-14       │ Perfil ba
│ devops-security          │ transversal    │ 1.0.0  │ 2026-03-14       │ Perfil tr
│ python-fastapi           │ layer2         │ 1.0.0  │ 2026-03-07       │ Layer 2 P
│ python-flask             │ layer2         │ 1.0.0  │ 2026-03-07       │ Layer 2 P
│ typescript-next          │ 2              │ 1.0.0  │ 2026-03-07       │ Layer 2 T
│ k8s-helm                 │ 3              │ 1.0.0  │ 2026-03-07       │ Layer 3 K
│ terraform-aws            │ 3              │ 1.0.0  │ 2026-03-07       │ Layer 3 T
│ data-warehouse-dbt       │ 3              │ 1.0.0  │ 2026-03-07       │ Layer 3 d
│ lgpd-baseline            │ 4              │ 1.0.0  │ 2026-03-07       │ Layer 4 c
│ soc2-baseline            │ 4              │ 1.0.0  │ 2026-03-07       │ Layer 4 c
└──────────────────────────┴────────────────┴────────┴──────────────────┴──────────

  12 perfil(s) em profile-descriptors/
```

Para output em JSON (útil em pipelines CI):

```bash
python scripts/scaffold.py --list-profiles --json
```

---

## Passo 3 — Gerar um projeto (modo CI/não-interativo)

> ⚠️ **IMPORTANTE**: Execute o scaffold do **diretório PAI** onde deseja criar o projeto.
>
> ```bash
> # ✅ CORRETO — executar de /path/to/projetos/
> cd /path/to/projetos/
> python /path/to/scaffold-project/scripts/scaffold.py --ci --name meu-projeto --domain programming --language python
> # Cria: /path/to/projetos/meu-projeto/
>
> # ❌ ERRADO — executar de /path/to/projetos/meu-projeto/
> cd /path/to/projetos/meu-projeto/
> python /path/to/scaffold-project/scripts/scaffold.py --ci --name meu-projeto --domain programming --language python
> # Cria: /path/to/projetos/meu-projeto/meu-projeto/ (DUPLICADO!)
> ```
>
> **Alternativa**: Use `--target-dir` para especificar onde criar:
>
> ```bash
> python scripts/scaffold.py --ci --name meu-projeto --domain programming --language python --target-dir /path/to/projetos/
> ```
>
> Veja detalhes em: [`docs/SESSIONS/2026-04-01/BUG_SCAFFOLD_DUPLICATE_DIRECTORY.md`](docs/SESSIONS/2026-04-01/BUG_SCAFFOLD_DUPLICATE_DIRECTORY.md)

### Projeto Python básico

```bash
python scripts/scaffold.py \
  --ci \
  --name meu-projeto \
  --domain programming \
  --language python
```

### Projeto Python com FastAPI (Layer 2)

```bash
python scripts/scaffold.py \
  --ci \
  --name minha-api \
  --domain programming \
  --language python \
  --compose python-fastapi
```

### Projeto TypeScript com Next.js

```bash
python scripts/scaffold.py \
  --ci \
  --name meu-frontend \
  --domain programming \
  --language typescript \
  --compose typescript-next
```

### Ver o que seria gerado sem criar arquivos (dry-run)

```bash
python scripts/scaffold.py \
  --ci \
  --name minha-api \
  --domain programming \
  --language python \
  --compose python-fastapi \
  --dry-run
```

---

## Passo 4 — Infra e CI/CD

Adicionar infraestrutura (GitHub Actions, Dockerfile, docker-compose, RUNBOOK.md):

```bash
python scripts/scaffold.py \
  --ci \
  --name minha-api \
  --domain programming \
  --language python \
  --compose python-fastapi \
  --infra
```

---

## Passo 5 — Validar os descritores

```bash
python scripts/scaffold.py --validate
```

Saída esperada:

```
  13 perfil(s) verificado(s) | 0 erro(s) | 0 aviso(s)
  ✅ Todos os descriptors são válidos.
```

---

## Fluxos completos por domínio

### Backend Python (FastAPI)

```bash
# 1. Gerar projeto
python scripts/scaffold.py \
  --ci \
  --name user-service \
  --title "User Service" \
  --description "Microserviço de autenticação e autorização" \
  --domain programming \
  --language python \
  --compose python-fastapi \
  --infra

# 2. Entrar no diretório e instalar dependências
cd <target-dir>/user-service
uv sync

# 3. Rodar testes
uv run pytest tests/ -q

# 4. Iniciar servidor de desenvolvimento
uv run uvicorn app.main:app --reload
```

### Backend Python (Flask)

```bash
python scripts/scaffold.py \
  --ci \
  --name webhook-handler \
  --domain programming \
  --language python \
  --compose python-flask \
  --infra
```

### Frontend TypeScript (Next.js)

```bash
python scripts/scaffold.py \
  --ci \
  --name dashboard-app \
  --domain programming \
  --language typescript \
  --compose typescript-next \
  --infra
```

### Infra Kubernetes + Helm

```bash
python scripts/scaffold.py \
  --ci \
  --name platform-infra \
  --domain programming \
  --language python \
  --compose k8s-helm \
  --infra
```

---

## Usar arquivo de configuração (YAML)

Para projetos recorrentes ou pipelines automatizados, use um arquivo de config:

```yaml
# config/minha-api.yaml
name: minha-api
title: "Minha API FastAPI"
description: "API REST com FastAPI, autenticação JWT e PostgreSQL"
domain: programming
language: python
profiles:
  - python-fastapi
infra: true
```

```bash
python scripts/scaffold.py --config config/minha-api.yaml
```

---

## Atualizar um projeto existente

Para re-aplicar o template a um projeto já existente sem sobrescrever arquivos customizados:

```bash
cd /caminho/para/meu-projeto
python /caminho/para/scaffold-project/scripts/scaffold.py --upgrade
```

Para forçar sobrescrita de arquivos com divergência:

```bash
python /caminho/para/scaffold-project/scripts/scaffold.py --upgrade --force
```

---

## Referências

| Documento | Descrição |
|-----------|-----------|
| [docs/TEMPLATE_USAGE.md](docs/TEMPLATE_USAGE.md) | Guia completo de uso do template |
| [docs/TEMPLATE-VERSIONS.md](docs/TEMPLATE-VERSIONS.md) | Versionamento e status de cada perfil |
| [docs/COMPATIBILITY-MATRIX.md](docs/COMPATIBILITY-MATRIX.md) | Matriz de compatibilidade entre perfis |
| [profile-descriptors/](profile-descriptors/) | Descritores YAML de cada perfil |
| [docs/copilot/](docs/copilot/) | Estratégia e decisões de domain profiles |
