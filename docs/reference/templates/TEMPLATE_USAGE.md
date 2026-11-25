# 📘 Como Usar Este Template

Este documento explica como usar o **scaffold-project** como template para criar novos projetos rapidamente, mantendo todas as melhores práticas e configurações compartilhadas.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Método 1: Script Automático](#método-1-script-automático-recomendado)
- [Método 2: Manualmente](#método-2-manualmente)
- [O Que Acontece na Inicialização](#o-que-acontece-na-inicialização)
- [Estrutura de Arquivos](#estrutura-de-arquivos)
- [Configurações Compartilhadas](#configurações-compartilhadas)
- [Próximos Passos](#próximos-passos)
- [Solução de Problemas](#solução-de-problemas)

## 🎯 Visão Geral

Este template fornece uma estrutura completa e pronta para:

- ✅ Múltiplas linguagens (Python, TypeScript, Go, etc.)
- ✅ Configurações compartilhadas via symlinks
- ✅ Makefile com 40+ comandos úteis
- ✅ Docker e CI/CD pré-configurados
- ✅ Padrões de arquitetura (MVP, Repository, Service Layer)
- ✅ Testes, linting e formatação configurados
- ✅ Documentação estruturada

## 📦 Pré-requisitos

### 1. Configurações Compartilhadas

Antes de criar um novo projeto, você precisa ter o repositório de configurações compartilhadas:

```bash
# Verificar se existe
ls -la ~/Documentos/DevOps/.copilot-shared/

# Se não existir, criar
make setup-shared-configs
```

### 2. Ferramentas Necessárias

```bash
# Git
git --version

# Make
make --version

# Python (opcional, para projetos Python)
python --version

# Node.js (opcional, para projetos Node.js)
node --version

# Docker (opcional, para containerização)
docker --version
```

## 🚀 Método 1: Script Automático (Recomendado)

### Passo 1: Clone o Template

```bash
# Clone o repositório do template
cd ~/Documentos/DevOps/
git clone <url-do-template> my-new-project
cd my-new-project
```

### Passo 2: Execute o Script de Inicialização

**Método Recomendado (scaffold.py):**
```bash
# Modo interativo
uv run scripts/scaffold.py new

# Ou modo não-interativo
uv run scripts/scaffold.py new --name my-awesome-app --domain devops --language python
```

**Método Legado (DEPRECATED):**
```bash
# Execute o script legado (será removido em versões futuras)
./setup/init-new-project.sh my-awesome-app
```

O script irá:
1. ✅ Validar o nome do projeto
2. ✅ Configurar symlinks para arquivos compartilhados
3. ✅ Substituir placeholders pelo nome do projeto
4. ✅ Limpar arquivos específicos do template
5. ✅ Remover histórico Git e criar novo repositório
6. ✅ Executar `make init` para configurar estrutura

### Passo 3: Configure o Projeto

```bash
# 1. Configure variáveis de ambiente
cp .env.example .env
code .env  # Edite conforme necessário

# 2. Escolha a linguagem principal
make setup-python  # Para Python
# ou
make setup-node    # Para Node.js

# 3. Instale dependências
make install

# 4. Execute testes
make test
```

### Passo 4: Configure Git Remote

```bash
# Adicione o repositório remoto
git remote add origin <url-do-seu-repositorio>
git branch -M main
git push -u origin main
```

## 🔧 Método 2: Manualmente

Se preferir fazer manualmente ou entender o processo:

### Passo 1: Clone e Limpe

```bash
# Clone
git clone <url-do-template> my-new-project
cd my-new-project

# Remove Git do template
rm -rf .git

# Inicializa novo Git
git init
```

### Passo 2: Configure Symlinks

```bash
# Execute o script de configuração de links
~/Documentos/DevOps/.copilot-shared/scripts/setup-project-links.sh .

# Verifique os links
~/Documentos/DevOps/.copilot-shared/scripts/check-project-links.sh .
```

### Passo 3: Substitua Placeholders

Edite os seguintes arquivos manualmente, substituindo `scaffold-project` pelo nome do seu projeto:

- `README.md`
- `setup.py`
- `*.code-workspace`
- `.env.example`
- `docker/Dockerfile`
- `docker-compose.yml`
- `.github/workflows/ci.yml`
- `Makefile`

```bash
# Ou use sed (cuidado!)
find . -type f -name "*.md" -o -name "*.py" -o -name "*.yml" | \
  xargs sed -i 's/scaffold-project/my-new-project/g'
```

### Passo 4: Limpe Arquivos do Template

```bash
# Remove documentação de sessões
rm -rf docs/SESSIONS

# Remove documentação específica do template
rm -f docs/SHARED_CONFIGS_SOLUTION.md
rm -f docs/MAKEFILE.md
rm -f docs/TEMPLATE_USAGE.md  # Este arquivo!

# Remove exemplos (se houver)
find src -name "example_*.py" -delete
find tests -name "test_example_*.py" -delete
```

### Passo 5: Primeiro Commit

```bash
git add .
git commit -m "feat: Initial commit from scaffold-project template"
git remote add origin <url>
git push -u origin main
```

## 🔍 O Que Acontece na Inicialização

### 1. Configuração de Symlinks

Os seguintes arquivos são substituídos por symlinks para o repositório compartilhado:

```
.copilot-rules.md               -> ~/.copilot-shared/rules/
.copilot-git-rules.md          -> ~/.copilot-shared/rules/
.copilot-strict-enforcement.md -> ~/.copilot-shared/rules/
.copilot-strict-rules.md       -> ~/.copilot-shared/rules/
.copilot-file-rules.sh         -> ~/.copilot-shared/rules/
```

**Benefícios:**
- ✅ Atualizações centralizadas
- ✅ Consistência entre projetos
- ✅ Economia de espaço (90% redução)
- ✅ Facilidade de manutenção

### 2. Substituição de Placeholders

O script substitui placeholders em vários formatos:

| Placeholder | Exemplo | Onde é Usado |
|------------|---------|--------------|
| `scaffold-project` | `my-app` | URLs, caminhos, imports |
| `SCAFFOLD_PROJECT` | `MY_APP` | Variáveis de ambiente |
| `Scaffold Project` | `My App` | Títulos, descrições |
| `scaffold_project` | `my_app` | Python modules, funções |

### 3. Limpeza de Arquivos

Remove arquivos específicos do template:
- Documentação de sessões antigas
- Documentação do próprio template
- Arquivos de exemplo
- Histórico Git

### 4. Estrutura Criada

Executa `make init` que cria:
```
src/
├── core/
│   ├── models/
│   ├── services/
│   └── repositories/
├── infrastructure/
│   ├── database/
│   ├── cache/
│   └── external/
├── presentation/
│   ├── api/
│   ├── cli/
│   └── presenters/
└── shared/
    ├── utils/
    ├── constants/
    └── exceptions/

tests/
├── unit/
├── integration/
└── e2e/

docs/
├── INDEX.md
├── TODO.md
└── TODAY_ACTIVITIES.md
```

## 📂 Estrutura de Arquivos

### Arquivos Compartilhados (Symlinks)

```
.copilot-rules.md              # Regras gerais do Copilot
.copilot-git-rules.md          # Regras de commit
.copilot-strict-enforcement.md # Enforcement rules
.copilot-strict-rules.md       # Regras estritas
.copilot-file-rules.sh         # Script de regras de arquivos
```

### Arquivos Locais do Projeto

```
README.md                      # Documentação principal
Makefile                       # Comandos de automação
setup.py                       # Configuração Python
requirements.txt               # Dependências Python
package.json                   # Dependências Node.js (se aplicável)
docker-compose.yml             # Orquestração Docker
.env.example                   # Template de variáveis
.gitignore                     # Regras do Git
.editorconfig                  # Configuração do editor
*.code-workspace               # Workspace VS Code
```

### Diretórios

```
src/                           # Código fonte
tests/                         # Testes automatizados
docs/                          # Documentação
scripts/                       # Scripts úteis
config/                        # Configurações
docker/                        # Dockerfiles
.github/                       # GitHub Actions
.vscode/                       # Configurações VS Code
.secrets/                      # Secrets (git-ignored)
```

## ⚙️ Configurações Compartilhadas

### Como Funciona

1. **Repositório Central**: `~/Documentos/DevOps/.copilot-shared/`
2. **Symlinks Relativos**: Cada projeto aponta para o central
3. **Atualização Única**: Altera em um lugar, reflete em todos

### Verificar Status

```bash
# Verificar symlinks do projeto atual
~/Documentos/DevOps/.copilot-shared/scripts/check-project-links.sh .

# Output esperado:
# ✓ .copilot-rules.md → ../../.copilot-shared/rules/
# ✓ .copilot-git-rules.md → ../../.copilot-shared/rules/
# ...
# Summary: 5 links, 0 local, 0 broken
```

### Atualizar Configurações

```bash
# Editar no repositório compartilhado
cd ~/Documentos/DevOps/.copilot-shared/
code rules/.copilot-rules.md

# Commit e push
git add .
git commit -m "feat: update copilot rules"
git push

# Mudanças aparecem automaticamente em todos os projetos!
```

## 📝 Próximos Passos

Após inicializar o projeto:

### 1. Configure o Ambiente

```bash
# Copie e edite variáveis de ambiente
cp .env.example .env
code .env
```

Edite:
- URLs de banco de dados
- Chaves de API
- Configurações de ambiente
- Secrets

### 2. Escolha a Linguagem

```bash
# Para Python
make setup-python
make install-python

# Para Node.js
make setup-node
make install-node

# Para ambos
make setup-python setup-node
```

### 3. Configure Docker (Opcional)

```bash
# Build da imagem
make docker-build

# Suba os containers
make docker-up

# Verifique
make docker-logs
```

### 4. Configure CI/CD

```bash
# GitHub Actions já está configurado em:
.github/workflows/ci.yml

# Edite conforme necessário:
code .github/workflows/ci.yml
```

Adicione secrets no GitHub:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- Outras credenciais necessárias

### 5. Comece a Desenvolver

```bash
# Veja todos os comandos
make help

# Crie estrutura de feature
make create-feature NAME=user-auth

# Execute testes
make test

# Faça build
make build

# Execute linting
make lint
```

## 🐛 Solução de Problemas

### Symlinks Quebrados

```bash
# Verificar status
~/Documentos/DevOps/.copilot-shared/scripts/check-project-links.sh .

# Recriar symlinks
~/Documentos/DevOps/.copilot-shared/scripts/setup-project-links.sh .
```

### Script de Inicialização Falhou

```bash
# Verificar se compartilhado existe
ls -la ~/Documentos/DevOps/.copilot-shared/

# Se não existir
cd <projeto-template-original>
make setup-shared-configs

# Tentar novamente
./scripts/init-new-project.sh my-project
```

### Nome do Projeto Inválido

O nome deve:
- ✅ Usar apenas letras minúsculas (a-z)
- ✅ Usar números (0-9)
- ✅ Usar hífens (-) para separar palavras
- ❌ NÃO usar espaços
- ❌ NÃO usar underscores
- ❌ NÃO usar caracteres especiais

Exemplos válidos:
- `my-project`
- `api-v2`
- `data-processor-2024`

### Make Não Encontrado

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Verificar
make --version
```

### Git Não Inicializado

```bash
# Inicializar manualmente
git init
git add .
git commit -m "feat: Initial commit"
```

## 📚 Recursos Adicionais

### Documentação

- [README.md](../README.md) - Visão geral do projeto
- [docs/INDEX.md](INDEX.md) - Índice da documentação
- [docs/TODO.md](TODO.md) - Lista de tarefas
- [docs/MAKEFILE.md](MAKEFILE.md) - Documentação do Makefile

### Comandos Úteis

```bash
# Ver todos os comandos
make help

# Status do projeto
make status

# Estrutura completa
make structure

# Testes
make test

# Limpar builds
make clean

# Docker
make docker-build
make docker-up
make docker-down

# CI/CD
make ci-test
make ci-build
```

### Suporte

- 📧 Email: [seu-email]
- 💬 Issues: [link-para-issues]
- 📖 Wiki: [link-para-wiki]
- 👥 Discussions: [link-para-discussions]

---

## ✅ Checklist de Inicialização

Use este checklist ao criar um novo projeto:

- [ ] Repositório de configurações compartilhadas existe
- [ ] Template clonado
- [ ] Script de inicialização executado
- [ ] Symlinks verificados
- [ ] Placeholders substituídos
- [ ] Arquivos do template limpos
- [ ] Novo repositório Git criado
- [ ] `.env` configurado
- [ ] Linguagem principal configurada
- [ ] Dependências instaladas
- [ ] Testes executados com sucesso
- [ ] Primeiro commit realizado
- [ ] Remote configurado
- [ ] Pushed para repositório
- [ ] CI/CD verificado
- [ ] Documentação atualizada

---

**🎉 Pronto! Seu projeto está configurado e pronto para desenvolvimento!**

Para ver todos os comandos disponíveis: `make help`
