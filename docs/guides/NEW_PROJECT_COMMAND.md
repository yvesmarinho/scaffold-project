# 🚀 new-project — Comando Global

Script conveniente instalado em `~/.local/bin/new-project` para criar projetos usando o Enterprise Scaffold Project Template de qualquer lugar.

## Instalação

✅ **Já instalado!** O script está em:
- Localização: `~/.local/bin/new-project`
- Executável: ✅
- No PATH: ✅

## Uso Básico

```bash
# Modo interativo (recomendado para iniciantes)
# Agora com seleção de perfis Layer 2! (BUG-05 fix)
new-project

# Quick start com nome
new-project my-api

# Com perfil específico (modo simplificado - BUG-05 Phase 2)
new-project my-api --with-code-profile python-fastapi

# Frontend Next.js
new-project my-frontend --with-code-profile typescript-next

# Infraestrutura
new-project infra-aws --domain infrastructure --with-code-profile terraform-aws

# Alternativa (2 passos - ainda funciona)
new-project my-api
cd my-api
scaffold.py compose python-fastapi
```

## Comandos Úteis

```bash
# Ver ajuda completa
new-project --help

# Listar todos os perfis disponíveis
new-project --list-profiles

# Validar perfis do template
new-project --validate
```

## Exemplos Práticos

### Backend Python FastAPI

```bash
# Modo simplificado (1 comando - BUG-05 Phase 2)
new-project my-api --with-code-profile python-fastapi
cd my-api
make install-deps
make dev

# Modo completo não-interativo
scaffold.py new --ci --name my-api --domain programming --language python --with-code-profile python-fastapi
```

### Frontend TypeScript Next.js

```bash
new-project my-frontend --with-code-profile typescript-next
cd my-frontend
npm install
npm run dev
```

### Fullstack Monorepo

```bash
# Backend
new-project my-app-backend --with-code-profile python-fastapi --target-dir ~/workspace/my-app

# Frontend
new-project my-app-frontend --with-code-profile typescript-next --target-dir ~/workspace/my-app
```

### Infraestrutura Terraform

```bash
new-project infra-prod --domain infrastructure --with-code-profile terraform-aws
cd infra-prod
terraform init
```
     # programming | infrastructure | analysis
--language LANG            # python | typescript | go | other
--with-code-profile PROFILE # python-fastapi, python-flask, typescript-next, etc. (BUG-05)
--compose PROFILE          # [deprecated] usar --with-code-profile ou compose separado
--target-dir DIR           # Diretório pai onde criar o projeto
--ci                       # Modo não-interativo (requer --name, --domain, --language)
```

### Diferença entre --with-code-profile e compose separado

```bash
# Opção 1: Tudo em 1 comando (BUG-05 Phase 2 - RECOMENDADO)
scaffold.py new --ci --name my-api --domain programming --language python --with-code-profile python-fastapi

# Opção 2: 2 passos (ainda funciona)
scaffold.py new --ci --name my-api --domain programming --language python
cd my-api
scaffold.py compose python-fastapi
```

**Vantagens do --with-code-profile**:
- ✅ 1 único comando
- ✅ Estado do projeto configurado corretamente
- ✅ Validação de compatibilidade domínio + linguagem
- ✅ Usado automaticamente no modo interativo (pergunta [9])niciar wizard interativo
new-project

# O wizard agora pergunta:
# [1] Nome do projeto?
# [2] Título?
# [3] Descrição?
# [4] Domínio? (programming, infrastructure, analysis)
# [5] Linguagem? (python, typescript, go, other)
# [6] URL do repo?
# [7] Diretório compartilhado?
# [8] Perfis Layer 1 adicionais?
# [9] Adicionar perfil de código específico? ← NOVO! (BUG-05 fix)
#     - Mostra apenas perfis compatíveis com domínio + linguagem
#     - Ex: python + programming → [python-fastapi, python-flask]
#     - Ex: typescript + programming → [typescript-next]
```

## Opções Avançadas

```bash
--domain DOMAIN       # programming | infrastructure | analysis
--language LANG       # python | typescript | go | other
--compose PROFILE     # python-fastapi, python-flask, typescript-next, etc.
--target-dir DIR      # Diretório pai onde criar o projeto
```

## Validação de Nome

O script valida automaticamente o nome do projeto:
- ✅ Formato: `kebab-case` (letras minúsculas, números, hífens)
- ✅ Exemplos válidos: `my-api`, `api-v2`, `backend-service`
- ❌ Inválidos: `My_API`, `api v2`, `API-Service`

## Detecção de Conflitos

O script **previne automaticamente** a criação de estruturas duplicadas (BUG-01 resolvido):

```bash
# ❌ Antes (buggy)
cd my-project/
new-project my-project  # criava my-project/my-project/

# ✅ Agora (corrigido)
cd my-project/
new-project my-project  # ❌ Erro com mensagem clara
```

## Localização do Template

O script aponta para:
```bash
~/Documentos/DevOps/Projetos/scaffold-project
```

Se você moveu o template, edite a variável `TEMPLATE_DIR` no início do script:

```bash
nano ~/.local/bin/new-project
# Ajuste a linha:
# TEMPLATE_DIR="${HOME}/Seu/Caminho/scaffold-project"
```

## Troubleshooting

### Comando não encontrado

```bash
# Verificar se está no PATH
echo $PATH | grep -q "$HOME/.local/bin" && echo "✅ OK" || echo "❌ Adicionar ao PATH"

# Adicionar ao ~/.zshrc (se necessário)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Permissão negada

```bash
chmod +x ~/.local/bin/new-project
```

### Template não encontrado

```bash
# Verificar localização
ls ~/Documentos/DevOps/Projetos/scaffold-project/scripts/scaffold.py

# Ajustar caminho no script se necessário
nano ~/.local/bin/new-project
```

## Ver Também

- Template principal: `~/Documentos/DevOps/Projetos/scaffold-project`
- Quick Start: `~/Documentos/DevOps/Projetos/scaffold-project/QUICKSTART.md`
- Regras Copilot: `~/Documentos/DevOps/Projetos/scaffold-project/.copilot-rules.md`
- Perfis disponíveis: `new-project --list-profiles`
