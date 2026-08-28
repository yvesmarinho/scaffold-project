# Objetivo.yaml Wizard Guide

**Guia completo do wizard interativo para criar arquivos objetivo.yaml v2.0**

---

## 📋 Índice

- [O que é o Wizard](#o-que-é-o-wizard)
- [Quando Usar](#quando-usar)
- [Como Usar](#como-usar)
- [Modos de Operação](#modos-de-operação)
- [Exemplos de Output](#exemplos-de-output)
- [Keyboard Navigation](#keyboard-navigation)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## O que é o Wizard

O **Objetivo Wizard** é uma ferramenta interativa que guia você na criação de arquivos `objetivo.yaml` v2.0 através de perguntas e respostas via terminal.

**Benefícios:**
- ✅ Não precisa editar YAML manualmente
- ✅ Perguntas guiadas com exemplos contextuais
- ✅ Validação em tempo real
- ✅ Progressive disclosure (P0 → P1 → P2)
- ✅ Suporte a Ctrl+C (draft save) e Ctrl+Z (undo)

**Formato gerado:** Markdown Híbrido (YAML frontmatter + seções numeradas com emoji)

---

## Quando Usar

### ✅ Use o Wizard se você:

- É **iniciante** no formato objetivo.yaml v2.0
- Prefere **interface guiada** a edição manual
- Quer **começar rápido** sem ler toda a especificação
- Precisa de **exemplos contextuais** enquanto preenche
- Está criando um **projeto simples** (1-3 features)

### ❌ NÃO use o Wizard se você:

- É **experiente** com objetivo.yaml e prefere edição direta
- Precisa de **controle total** sobre formatação
- Está criando um **projeto complexo** (5+ features, múltiplos domínios)
- Quer **reutilizar** conteúdo de outros arquivos
- Está **automatizando** em CI/CD (use `--from-file` ao invés)

---

## Como Usar

### Modo Interativo (Padrão)

```bash
# Iniciar wizard interativo
cd /path/to/your/project
scaffold.py objetivo-init

# OU com output customizado
scaffold.py objetivo-init --output meu-objetivo.yaml
```

**Fluxo:**
1. Wizard exibe banner e instruções
2. Coleta metadados do projeto (nome, tipo, domínio, linguagem)
3. Pergunta seções P0 (obrigatórias): 3 perguntas essenciais
4. Pergunta se quer adicionar seções P1 (opcionais)
5. Renderiza template com suas respostas
6. Salva em `objetivo.yaml`

**Tempo estimado:** 5-10 minutos

---

## Modos de Operação

### 1. Interactive (Default)

Wizard completo com perguntas e respostas:

```bash
scaffold.py objetivo-init
```

**Output:**
```
🧙 Wizard objetivo.yaml v2.0

Crie seu arquivo objetivo.yaml respondendo algumas perguntas.
(Ctrl+C: salvar draft | Ctrl+Z: voltar)

Metadados do Projeto

Nome do projeto (kebab-case)
Exemplo: user-management-api
  Resposta: payment-gateway-api

Título legível
Exemplo: API de Gerenciamento de Usuários
  Resposta: API Gateway de Pagamentos

...
```

### 2. Non-Interactive (CI/CD)

Para automação, use arquivo JSON com respostas pré-definidas:

```bash
# 1. Crie answers.json
cat > answers.json <<EOF
{
  "project_name": "payment-gateway-api",
  "project_title": "API Gateway de Pagamentos",
  "project_type": "backend-api",
  "project_domain": "programming",
  "project_language": "python",
  "created_by": "devops-team",
  "answers": {
    "{{ANSWER_1}}": "API RESTful para processar pagamentos via PIX, cartão de crédito e boleto",
    "{{ANSWER_2}}": "Merchants perdem vendas (12%) devido a checkout lento (>8s). Gateway atual tem downtime de 3%.",
    "{{ANSWER_3}}": "- Processamento PIX (P0)\n- Processamento cartão de crédito (P0)\n- Dashboard de transações (P1)"
  }
}
EOF

# 2. Execute wizard em modo non-interactive
scaffold.py objetivo-init --from-file answers.json
```

### 3. Template-Only

Apenas copia o template sem wizard:

```bash
scaffold.py objetivo-init --template-only
```

Útil se você:
- Quer editar manualmente
- Já conhece bem o formato
- Prefere controle total

---

## Exemplos de Output

### Exemplo 1: Backend API (Python)

**Input (wizard):**
- Nome: `user-auth-service`
- Tipo: `backend-api`
- Domínio: `programming`
- Linguagem: `python`
- P0 Q1: "Microserviço de autenticação com JWT e OAuth2"
- P0 Q2: "Sistema atual usa autenticação básica insegura, 20% das contas comprometidas"
- P0 Q3: "Login JWT (P0)\nOAuth2 Google/GitHub (P1)\n2FA (P2)"

**Output gerado (`objetivo.yaml`):**
```yaml
---
version: "2.0"
project:
  name: "user-auth-service"
  title: "Microserviço de Autenticação"
  type: "backend-api"
  domain: "programming"
  language: "python"
created_at: "2026-04-28"
created_by: "devops-team"
---

## 1️⃣ O que este projeto faz?

Microserviço de autenticação com JWT e OAuth2

## 2️⃣ Qual problema resolve?

Sistema atual usa autenticação básica insegura, 20% das contas comprometidas

## 3️⃣ Escopo do Projeto

### ✅ Incluído

- Login JWT (P0)
- OAuth2 Google/GitHub (P1)
- 2FA (P2)

### ❌ Excluído

(Não especificado - preencher manualmente se necessário)
```

---

## Keyboard Navigation

### Atalhos Disponíveis

| Tecla | Ação | Quando usar |
|-------|------|-------------|
| **Enter** | Confirmar resposta | Sempre (terminar input) |
| **Enter Enter** | Terminar multiline | Em perguntas multiline (Q2, Q3, Q4, Q5) |
| **Ctrl+C** | Salvar draft e sair | Se quiser pausar e continuar depois |
| **Ctrl+Z** | Voltar pergunta anterior | Se errou resposta anterior |
| **Tab** | Auto-complete exemplo | Se Rich disponível (experimental) |

### Comportamento Multiline

Perguntas que aceitam múltiplas linhas:
- **Q2:** Qual problema resolve? (1-2 parágrafos)
- **Q3:** O que está NO escopo? (lista de features)
- **Q4:** Há restrições técnicas?
- **Q5:** Há regras de negócio complexas?

**Como usar:**
1. Digite primeira linha
2. Pressione Enter
3. Digite segunda linha
4. Pressione Enter
5. **Pressione Enter novamente (linha vazia) para terminar**

**Exemplo:**
```
O que está NO escopo? (liste features incluídas, Enter vazio para terminar)
Exemplo: Processamento automático de dados (P0)...
(Digite Enter duas vezes para terminar)
  Autenticação JWT (P0)
  OAuth2 Google (P1)
  2FA por SMS (P2)

✓ Resposta salva
```

### Draft Save (Ctrl+C)

Se você pressionar **Ctrl+C** durante o wizard:

1. Wizard salva progresso atual em `objetivo-draft.yaml`
2. Exibe mensagem: "📝 Draft salvo: objetivo-draft.yaml"
3. Sai do wizard

**Para continuar depois:**
1. Abra `objetivo-draft.yaml`
2. Complete manualmente as seções faltantes
3. Valide: `scaffold.py objetivo-validate --file objetivo-draft.yaml`

---

## Troubleshooting

### Problema: Rich não disponível

**Sintoma:**
```
ImportError: No module named 'rich'
```

**Solução:**
O wizard funciona **sem Rich** usando print() simples. Você perderá:
- Cores e formatação
- Painel de banner
- Progress indicators

Mas **todas as funcionalidades** principais continuam funcionando.

**Instalar Rich (opcional):**
```bash
pip install rich
```

---

### Problema: Keyboard navigation não funciona

**Sintoma:**
- Ctrl+Z não volta pergunta anterior
- Ctrl+C não salva draft

**Causa:** Terminal não suporta sinais POSIX (Windows CMD, alguns terminais customizados)

**Solução:**
1. Use terminal compatível (bash, zsh, PowerShell 7+)
2. OU use modo non-interactive:
   ```bash
   scaffold.py objetivo-init --from-file answers.json
   ```

---

### Problema: Multiline input não termina

**Sintoma:**
Você pressiona Enter mas wizard continua esperando input.

**Causa:** Precisa pressionar **Enter duas vezes** (linha vazia).

**Solução:**
```
  Linha 1
  Linha 2
  <Enter>  ← primeira vez (nova linha)
  <Enter>  ← segunda vez (termina)
```

---

### Problema: Pergunta obrigatória aceita resposta vazia

**Sintoma:**
Wizard aceita Enter vazio em perguntas P0.

**Causa:** Bug conhecido em versões antigas.

**Solução:**
Atualize scaffold.py:
```bash
git pull origin 060-mini-engram-python
```

---

### Problema: Template não encontrado

**Sintoma:**
```
FileNotFoundError: Template not found: poc/objetivo-v2-template-base.md
```

**Causa:** Executando wizard fora do diretório do template.

**Solução:**
```bash
cd /path/to/scaffold-project
scaffold.py objetivo-init
```

---

## Pipeline Completo: Do Objetivo ao Scaffold

### Visão Geral do Workflow

O Objetivo Wizard é a **primeira etapa** de um pipeline completo que leva desde a descrição do projeto até o scaffold funcional:

```
┌─────────────────┐
│ objetivo-init   │ → objetivo.yaml (Markdown Híbrido v2.0)
│ (wizard)        │
└─────────────────┘
        ↓
┌─────────────────┐
│ objetivo-       │ → ✅ Validação de formato e conteúdo
│ validate        │
└─────────────────┘
        ↓
┌─────────────────┐
│ objetivo-       │ → objetivo-spec.yaml (profiles auto-detectados)
│ generate        │
└─────────────────┘
        ↓
┌─────────────────┐
│ scaffold new    │ → Projeto completo com estrutura e configurações
│ (com profiles)  │
└─────────────────┘
```

### Passo a Passo Completo

#### 1️⃣ Criar objetivo.yaml com Wizard

```bash
# Modo interativo (recomendado para primeiro uso)
scaffold.py objetivo-init

# OU modo não-interativo (CI/CD, automação)
scaffold.py objetivo-init --from-file answers.json --output objetivo.yaml
```

**Output:** `objetivo.yaml` (Markdown Híbrido v2.0)

**Estrutura gerada:**
```yaml
---
version: "2.0"
project:
  name: "task-manager-api"
  title: "Task Manager REST API"
  type: "backend-api"
  domain: "programming"
  language: "python"
created_at: "2026-05-21"
created_by: "yves_marinho"
---

## 1️⃣ O que este projeto faz?

REST API para gerenciar tarefas com autenticação JWT, CRUD completo, prioridades e tags

## 2️⃣ Qual problema resolve?

Sistema atual de gestão de tarefas é manual...

## 3️⃣ Escopo do Projeto

### Incluído ✅

- CRUD de tarefas (P0)
- Autenticação JWT (P0)
- Sistema de prioridades (P1)
```

---

#### 2️⃣ Validar objetivo.yaml

```bash
scaffold.py objetivo-validate --file objetivo.yaml
```

**Output esperado:**
```
Validação de objetivo.yaml

  ✅ Válido — sem erros ou avisos
```

**O que é validado:**
- ✅ Frontmatter YAML correto (`version: "2.0"`, campos obrigatórios)
- ✅ Seções P0 presentes (## 1️⃣, ## 2️⃣, ## 3️⃣)
- ✅ Formatação de listas (pelo menos 1 item em "Incluído ✅")
- ✅ Metadata completo (name, title, type, domain, language)

**Erros comuns:**
- ❌ `Missing or malformed YAML frontmatter` → Frontmatter YAML ausente ou inválido
- ❌ `Section 3 must have at least one item in 'Incluído ✅' list` → Nenhuma feature listada
- ❌ `Missing required field: project.name` → Campo obrigatório ausente

---

#### 3️⃣ Gerar Spec YAML com Profiles Auto-Detectados

```bash
scaffold.py objetivo-generate --input objetivo.yaml --output objetivo-spec.yaml
```

**Output:** `objetivo-spec.yaml`

**Estrutura gerada:**
```yaml
# ⚠️  GERADO AUTOMATICAMENTE — NÃO EDITAR!
# Fonte: objetivo.yaml
# Gerado em: 2026-05-21 09:49:54

---
specification:
  version: 2.0
  generated_from: objetivo.yaml
  generated_at: 2026-05-21T09:49:54.956277

project:
  name: task-manager-api
  title: Task Manager REST API
  type: backend-api
  domain: programming
  language: python

profiles:
  - programming           # Auto-detectado de domain: programming
  - python-fastapi       # Auto-detectado de language: python + type: backend-api

features:
  # Extração automática de features em desenvolvimento (futuro)

personas:
  # Opcional - adicionar manualmente se necessário

validation:
  level: strict
  warnings: 0
  require_p0: true
```

**Profiles auto-detectados:**
- `domain: programming` → profile `programming`
- `language: python` + `type: backend-api` → profile `python-fastapi`
- `language: typescript` + `type: frontend` → profile `typescript-next`
- `domain: infrastructure` + `language: terraform` → profile `terraform-aws`

---

#### 4️⃣ Scaffold Projeto com Profiles

```bash
# Usar profiles detectados na spec
scaffold.py --new --compose programming,python-fastapi

# OU deixar scaffold detectar automaticamente
scaffold.py --new --domain programming --language python
```

**Output:** Projeto completo com:
- ✅ Estrutura de pastas (`src/`, `tests/`, `docs/`)
- ✅ Configurações (`pyproject.toml`, `.copilot-rules.md`, `Makefile`)
- ✅ Templates SpecKit (`.specify/templates/`)
- ✅ Scripts utilitários (`scripts/`)
- ✅ CI/CD workflows (`.github/workflows/`)

---

### Exemplo Completo: Task Manager API

```bash
# Passo 1: Criar arquivo de respostas (modo não-interativo)
cat > task-manager-answers.json <<EOF
{
  "project_name": "task-manager-api",
  "project_title": "Task Manager REST API",
  "project_type": "backend-api",
  "project_domain": "programming",
  "project_language": "python",
  "created_by": "yves_marinho",
  "answers": {
    "q1_what": "REST API para gerenciar tarefas com autenticação JWT, CRUD completo, prioridades e tags",
    "q2_problem": "Sistema atual de gestão de tarefas é manual e propenso a erros",
    "q3_scope_included": "CRUD de tarefas (P0)\nAutenticação JWT (P0)\nSistema de prioridades (P1)\nTags e categorias (P1)",
    "q6_response": "Python 3.11+ com FastAPI, PostgreSQL para persistência, Redis para cache",
    "q8_infrastructure": "Servidor PostgreSQL 15 em RDS\nRedis 7 para cache\nDeploy em ECS Fargate"
  }
}
EOF

# Passo 2: Wizard gera objetivo.yaml
scaffold.py objetivo-init --from-file task-manager-answers.json --output objetivo.yaml
# ✅ Gerado: objetivo.yaml

# Passo 3: Validar formato e conteúdo
scaffold.py objetivo-validate --file objetivo.yaml
# ✅ Válido — sem erros ou avisos

# Passo 4: Gerar spec com profiles auto-detectados
scaffold.py objetivo-generate --input objetivo.yaml --output objetivo-spec.yaml
# ✅ Gerado: objetivo-spec.yaml
# Profiles detectados: programming, python-fastapi

# Passo 5: Scaffold projeto
scaffold.py --new --compose programming,python-fastapi --name task-manager-api
# ✅ Projeto criado em: ../task-manager-api/
```

**Resultado final:**
```
task-manager-api/
├── objetivo.yaml              # Descrição do projeto
├── objetivo-spec.yaml         # Spec gerada automaticamente
├── .copilot-rules.md         # Regras do Copilot
├── pyproject.toml            # Dependências Python
├── Makefile                  # Comandos make
├── src/                      # Código fonte
├── tests/                    # Testes
├── docs/                     # Documentação
└── .specify/                 # Templates SpecKit
    └── templates/
        ├── spec-template.md
        ├── plan-template.md
        └── tasks-template.md
```

**Tempo total:** ~3 minutos (modo não-interativo)

---

### Quando Usar Este Pipeline

✅ **Use o pipeline completo quando:**
- Está criando um **novo projeto** do zero
- Quer **documentação estruturada** desde o início
- Precisa de **profiles auto-detectados** sem configuração manual
- Quer **validação automática** de formato e conteúdo
- Está **automatizando** criação de projetos em CI/CD

⚠️ **Pule etapas intermediárias se:**
- Só precisa do scaffold básico → use `scaffold.py --new` direto
- Já tem objetivo.yaml válido → comece em `objetivo-validate`
- Quer criar spec manualmente → pule `objetivo-generate`

---

### Troubleshooting do Pipeline

#### ❌ Erro: "Failed to parse frontmatter"

```
Error: Failed to parse frontmatter in objetivo.yaml
```

**Causa:** Formato YAML puro (legacy) ao invés de Markdown Híbrido v2.0.

**Solução:** Use `objetivo-init` para gerar formato correto, ou edite manualmente:
```yaml
---
version: "2.0"
project:
  name: "my-project"
  ...
---

## 1️⃣ O que este projeto faz?
...
```

#### ❌ Erro: "Section 3 must have at least one item"

```
Error: Section 3 must have at least one item in 'Incluído ✅' list
```

**Causa:** Nenhuma feature listada na seção 3.

**Solução:** Adicione pelo menos uma feature:
```markdown
## 3️⃣ Escopo do Projeto

### Incluído ✅

- CRUD de entidades (P0)
```

#### ❌ Profiles vazios na spec gerada

```yaml
profiles:  # Vazio!
```

**Causa:** Campos `domain` ou `language` ausentes/inválidos.

**Solução:** Verifique objetivo.yaml:
```yaml
project:
  domain: "programming"     # Obrigatório
  language: "python"        # Obrigatório
```

---

## FAQ

### 1. Posso editar o arquivo gerado depois?

**Sim!** O wizard gera um arquivo objetivo.yaml válido que você pode editar manualmente. Recomendado:
1. Gerar com wizard (5 min)
2. Refinar manualmente (10 min)
3. Validar: `scaffold.py objetivo-validate`

---

### 2. Como adicionar seções P2 (avançadas)?

O wizard atualmente suporta apenas P0 (obrigatórias) e P1 (contextuais). Para adicionar P2:
1. Complete wizard normalmente
2. Edite `objetivo.yaml` manualmente
3. Adicione seções 6️⃣, 7️⃣, 8️⃣, 9️⃣ conforme necessário

---

### 3. Posso reusar respostas de outro projeto?

**Sim, use modo non-interactive:**
```bash
# 1. Extraia respostas de projeto anterior (manual ou script)
cat > answers.json <<EOF
{
  "project_name": "new-project",
  ...
}
EOF

# 2. Gere novo objetivo.yaml
scaffold.py objetivo-init --from-file answers.json
```

---

### 4. O wizard valida as respostas?

**Parcialmente:**
- ✅ Valida campos obrigatórios (não pode estar vazio)
- ✅ Valida tipos de projeto (deve estar na lista)
- ❌ NÃO valida conteúdo semântico

**Após wizard, sempre valide:**
```bash
scaffold.py objetivo-validate
```

---

### 5. Quanto tempo leva para completar?

| Perfil | P0 apenas | P0 + P1 |
|--------|-----------|---------|
| **Iniciante** | 8-10 min | 12-15 min |
| **Intermediário** | 5-7 min | 8-10 min |
| **Avançado** | 3-5 min | 5-7 min |

**Dica:** Se >15 min, considere edição manual ao invés do wizard.

---

### 6. Como funciona a geração de spec técnico?

Após criar objetivo.yaml com wizard:

```bash
# 1. Validar
scaffold.py objetivo-validate

# 2. Gerar spec técnico
scaffold.py objetivo-generate

# Output: objetivo-spec.yaml
```

O spec técnico é **gerado automaticamente** de objetivo.yaml e inclui:
- Profiles detectados (baseado em type + language)
- Features extraídas (seção 3 "Incluído")
- Personas (seção 5, se preenchida)

---

## Próximos Passos

Após completar o wizard:

1. **Validar:** `scaffold.py objetivo-validate`
2. **Gerar spec:** `scaffold.py objetivo-generate`
3. **Criar projeto:** `scaffold.py new --config objetivo-spec.yaml`

**Documentação relacionada:**
- [Spec 066: objetivo.yaml v2.0](../../specs/066-objetivo-yaml-v2/spec.md)
- [Comparação v1.0 vs v2.0](../debates/COMPARACAO-OBJETIVO-V1-V2.md)
- [README Principal](../../README.md)

---

**Versão:** 1.0 (2026-04-28)
**Spec:** 066-objetivo-yaml-v2
**Autor:** DevOps Team
