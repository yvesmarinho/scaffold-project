# Integração de Best Practices GitHub no Template

Este documento descreve como as melhores práticas de Git/GitHub foram integradas no Enterprise Scaffold Project Template.

## 📋 Visão Geral

As melhores práticas do documento `docs/guides/GitHub_Melhores_praticas_de_atualizacao_repositprios.md` foram integradas em três camadas:

1. **Templates de Projeto** - Arquivos que serão copiados para novos projetos
2. **Validações Automatizadas** - Código que verifica conformidade
3. **Documentação** - Guias e referências

---

## 🎯 Componentes Criados

### 1. Templates de Projeto

Localizados em `.github/templates/common/`, prontos para serem copiados pelo scaffold:

#### CONTRIBUTING.md
- **Localização**: `.github/templates/common/CONTRIBUTING.md`
- **Propósito**: Guia completo de contribuição
- **Conteúdo**:
  - Workflow Git (GitHub Flow)
  - Convenções de branch (`feature/NNN-descricao`, `fix/descricao`, etc.)
  - Estratégias de merge (squash, merge commit, rebase)
  - Padrões de commits (Conventional Commits)
  - Checklist de PR
  - Proteção de branches
  - Recuperabilidade (tags, rollback)
- **Variáveis template**: `{{ project_name }}`, `{{ current_date }}`

#### PULL_REQUEST_TEMPLATE.md
- **Localização**: `.github/templates/common/PULL_REQUEST_TEMPLATE.md`
- **Propósito**: Template padrão para PRs
- **Conteúdo**:
  - Descrição e contexto
  - Tipo de mudança (feat/fix/chore/breaking)
  - Checklist completo (testes, docs, segurança)
  - Seção de screenshots
  - Plano de rollback
  - Impacto estimado
- **Variáveis template**: `{{ branch_name }}`

#### CODEOWNERS
- **Localização**: `.github/templates/common/CODEOWNERS`
- **Propósito**: Definir responsáveis por áreas do código
- **Conteúdo**:
  - Documentação (`/docs/`, `/README.md`)
  - Configurações de projeto (`package.json`, `pyproject.toml`)
  - CI/CD (`.github/workflows/`)
  - Segurança (`/SECURITY.md`, auth code)
  - Código fonte (backend, frontend)
  - Testes (unit, integration, e2e)
  - Schemas (database, GraphQL, OpenAPI)
- **Customização**: Placeholders `@tech-lead`, `@backend-team`, etc.

### 2. Validações Automatizadas

#### git_validators.py
- **Localização**: `scripts/lib/git_validators.py`
- **Propósito**: Validação de branches e commits
- **Funcionalidades**:
  - `validate_branch_name()`: Valida padrão `tipo/[NNN-]descricao`
  - `validate_commit_message()`: Valida Conventional Commits
  - `check_pr_readiness()`: Verifica se branch está pronta para PR
  - `suggest_branch_name()`: Sugere nomes de branch
  - `is_protected_branch()`: Identifica branches protegidas
- **Testes**: 42 testes em `tests/test_git_validators.py` (100% passando)

#### Integração com Session Manager
- **Arquivo modificado**: `scripts/session-time-tracker.py`
- **Mudança**: `cmd_start()` agora valida nome da branch
- **Comportamento**:
  - ✅ Branch válida: sessão inicia normalmente
  - ⚠️ Branch com warnings: exibe avisos mas permite continuar
  - ❌ Branch inválida: solicita confirmação para prosseguir
  - Exibe sugestões de correção (formato esperado, dicas)

### 3. Documentação

#### Guia de Branch Protection
- **Localização**: `docs/guides/BRANCH_PROTECTION_SETUP.md`
- **Propósito**: Tutorial de configuração do GitHub
- **Conteúdo**:
  - Passo a passo visual
  - 3 níveis de proteção (mínimo, recomendado, máximo)
  - Status checks recomendados
  - Configuração via API/Terraform
  - Troubleshooting
  - Checklist de validação

---

## 🔄 Fluxo de Integração no Scaffold

### Como o Scaffold Deve Copiar Templates

Quando criar um novo projeto, o scaffold deve:

```python
# Pseudocódigo do fluxo esperado

def setup_github_best_practices(project_path: Path, project_name: str):
    """
    Integra templates de GitHub best practices no projeto.
    """
    templates_dir = Path(".github/templates/common")
    project_github_dir = project_path / ".github"

    # 1. Criar estrutura .github
    project_github_dir.mkdir(exist_ok=True)
    (project_github_dir / "ISSUE_TEMPLATE").mkdir(exist_ok=True)

    # 2. Copiar e processar CONTRIBUTING.md
    contributing_template = templates_dir / "CONTRIBUTING.md"
    contributing_dest = project_path / "CONTRIBUTING.md"

    content = contributing_template.read_text()
    content = content.replace("{{ project_name }}", project_name)
    content = content.replace("{{ current_date }}", datetime.now().strftime("%Y-%m-%d"))
    contributing_dest.write_text(content)

    # 3. Copiar PR template
    pr_template_src = templates_dir / "PULL_REQUEST_TEMPLATE.md"
    pr_template_dest = project_github_dir / "PULL_REQUEST_TEMPLATE.md"
    shutil.copy(pr_template_src, pr_template_dest)

    # 4. Copiar CODEOWNERS
    codeowners_src = templates_dir / "CODEOWNERS"
    codeowners_dest = project_github_dir / "CODEOWNERS"
    shutil.copy(codeowners_src, codeowners_dest)

    # 5. Copiar guia de branch protection para docs/
    guide_src = Path("docs/guides/BRANCH_PROTECTION_SETUP.md")
    guide_dest = project_path / "docs" / "BRANCH_PROTECTION_SETUP.md"
    shutil.copy(guide_src, guide_dest)
```

### Variáveis Template Suportadas

| Variável | Exemplo | Onde Usar |
|----------|---------|-----------|
| `{{ project_name }}` | `my-awesome-api` | CONTRIBUTING.md |
| `{{ current_date }}` | `2026-05-17` | CONTRIBUTING.md, CODEOWNERS |
| `{{ branch_name }}` | `feature/042-auth` | PULL_REQUEST_TEMPLATE.md |

---

## ✅ Checklist de Integração

Quando scaffold criar novo projeto:

- [ ] Copiar `.github/templates/common/CONTRIBUTING.md` → raiz do projeto
- [ ] Processar variáveis `{{ project_name }}` e `{{ current_date }}`
- [ ] Copiar `.github/templates/common/PULL_REQUEST_TEMPLATE.md` → `.github/`
- [ ] Copiar `.github/templates/common/CODEOWNERS` → `.github/`
- [ ] Copiar `docs/guides/BRANCH_PROTECTION_SETUP.md` → `docs/` do projeto
- [ ] Adicionar referências no README do projeto:
  - Link para CONTRIBUTING.md
  - Link para BRANCH_PROTECTION_SETUP.md
- [ ] Criar `.github/ISSUE_TEMPLATE/` vazio (estrutura futura)

---

## 🧪 Validações Implementadas

### Validação de Branch Name

**Padrão esperado**: `tipo/[NNN-]descricao`

**Tipos permitidos**:
- `feature` - novas funcionalidades (issue obrigatório)
- `fix` - correção de bugs
- `hotfix` - correções urgentes
- `chore` - manutenção
- `docs` - documentação
- `refactor` - refatoração
- `test` - testes

**Regras**:
- ✅ Apenas lowercase
- ✅ Hífens para separar palavras (não underscores)
- ✅ Descrição entre 3-50 caracteres
- ✅ Issue number opcional (exceto features)

**Exemplos válidos**:
```bash
feature/042-user-authentication
fix/memory-leak-in-parser
hotfix/critical-security-patch
chore/update-dependencies
```

**Exemplos inválidos**:
```bash
FEATURE/bad-case              # uppercase
invalid-branch-name            # sem tipo/
feature/user_authentication    # underscores
fix/ab                         # muito curto
```

### Validação de Commit Message

**Padrão esperado**: `tipo(escopo): descrição`

**Tipos permitidos**:
- `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`

**Regras**:
- ✅ Escopo opcional
- ✅ `!` para breaking change
- ✅ Subject 5-72 caracteres
- ✅ Subject em lowercase
- ✅ Sem ponto final no subject
- ✅ Body e footer opcionais

**Exemplos válidos**:
```bash
feat(api): add user endpoint
fix: memory leak in parser
feat(api)!: change response format
docs: update README

feat(api): add user endpoint

This endpoint allows creating new users with validation.

BREAKING CHANGE: campo 'userId' renomeado para 'user_id'
Closes #123
```

**Exemplos inválidos**:
```bash
invalid commit message         # sem padrão
feat: abc                      # muito curto
feat: Add New Feature.         # uppercase, ponto final
```

---

## 📊 Níveis de Proteção de Branch

Conforme `docs/guides/BRANCH_PROTECTION_SETUP.md`:

### Nível 1: Mínimo
- Require pull request
- Require 1 approval
- Require status checks
- Block force push e deletion

**Para**: Projetos pessoais, equipes pequenas

### Nível 2: Recomendado
- Tudo do nível 1
- Dismiss stale approvals
- Require Code Owners review
- Require conversation resolution
- Do not allow bypassing

**Para**: Projetos profissionais em produção

### Nível 3: Máximo
- Tudo do nível 2
- Require 2+ approvals
- Require signed commits
- Require linear history (opcional)
- Require deployments to succeed

**Para**: Sistemas críticos, compliance (SOC2, PCI-DSS)

---

## 🚀 Próximos Passos

### P0 - Crítico (✅ COMPLETO)
- ✅ Templates criados (CONTRIBUTING, PR, CODEOWNERS)
- ✅ Validadores implementados (git_validators.py)
- ✅ Integração com session manager
- ✅ Testes (42 passando)
- ✅ Documentação (BRANCH_PROTECTION_SETUP)

### P1 - Importante (✅ COMPLETO)
- ✅ Modificar scaffold para copiar templates (copy_github_templates)
- ✅ Processar variáveis template ({{ project_name }}, {{ current_date }})
- ✅ Adicionar seção no README template (workflow Git/GitHub)
- ✅ Função _copy_file_with_vars() para substituição de variáveis
- ✅ Integração no flow_new_project
- ✅ Testado e validado (projeto de teste criado com sucesso)

### P2 - Desejável (✅ COMPLETO)
- ✅ Issue templates (bug_report, feature_request, documentation, question, config)
- ✅ GitHub Actions workflow para validar branches/commits/PRs (git-validation.yml)
- ✅ Pre-commit hook para validar commits (commit-msg)
- ✅ Script de setup automático de branch protection (setup-branch-protection.py)
- ✅ Badge de conformidade (BADGES.md com guia completo)
- ✅ Integração no scaffold (copy_github_templates atualizado)

#### Issue Templates Criados

Localizados em `.github/templates/common/ISSUE_TEMPLATE/`:

**bug_report.yml**
- Formulário estruturado para reportar bugs
- Campos: descrição, passos, comportamento esperado/atual
- Dropdown de severidade (crítica → baixa)
- Informações de versão e ambiente
- Checklist de verificação

**feature_request.yml**
- Formulário para requisitar funcionalidades
- Campos: problema/necessidade, solução proposta, alternativas
- Dropdown de prioridade e impacto
- Campo para mockups/exemplos
- Checklist de validação

**documentation.yml**
- Template para melhorias de documentação
- Dropdown de tipo (erro, melhoria, novo conteúdo)
- Localização e problema atual
- Sugestão de melhoria
- Exemplos e checklist

**question.yml**
- Template para questões/dúvidas
- Campo de pergunta e contexto
- O que já foi tentado
- Informações de ambiente
- Checklist de pesquisa prévia

**config.yml**
- Configuração de issue templates
- Desabilita issues em branco
- Links para Discussions, Docs, Security

#### GitHub Actions Workflow

**git-validation.yml** (`.github/templates/common/workflows/`)

Jobs implementados:
1. **validate-branch**: Valida nome da branch contra padrão
2. **validate-commits**: Valida todas mensagens de commit (Conventional Commits)
3. **validate-pr-title**: Valida título do PR
4. **pr-size-check**: Avisa sobre PRs grandes (>1000 linhas ou >20 arquivos)
5. **summary**: Job final com resultado geral

Features:
- Triggers: pull_request (opened, synchronize, reopened)
- Python 3.12 + checkout@v4 + setup-python@v5
- Validação de branches protegidas (main, develop, staging, production)
- Warnings não-bloqueantes para estilo
- Badge status no README

#### Pre-commit Hook

**commit-msg** (`scripts/git-hooks/`)

Features:
- Validação local de commits antes do push
- Mesmo padrão do workflow (Conventional Commits)
- Permite mensagens de merge/revert
- Warnings para estilo (não bloqueiam commit)
- Feedback descritivo de erros
- Permissões executáveis (chmod 755)

Instalação automática pelo scaffold:
```bash
# Hook é copiado para projeto_path/scripts/git-hooks/
# Para ativar no repositório:
cd projeto
ln -s ../../scripts/git-hooks/commit-msg .git/hooks/commit-msg
```

#### Script de Branch Protection

**setup-branch-protection.py** (`scripts/`)

Features:
- Configura proteção via GitHub API
- 3 níveis pré-configurados (minimum, recommended, maximum)
- Suporte a variáveis de ambiente (GITHUB_TOKEN)
- Dry-run mode para visualizar configuração
- Validação de status checks
- Configuração de required signatures
- Interface CLI com rich tables

Uso:
```bash
# Dry run
python scripts/setup-branch-protection.py owner/repo --dry-run

# Aplicar nível recomendado
export GITHUB_TOKEN=ghp_xxxxx
python scripts/setup-branch-protection.py owner/repo --level recommended

# Branch específica
python scripts/setup-branch-protection.py owner/repo --branch develop --level maximum
```

Configurações por nível:

**Minimum**:
- 1 aprovação
- Status checks: build, test
- Sem force push/delete

**Recommended**:
- 1 aprovação
- Dismiss stale reviews
- Code owner reviews
- Status checks: build, test, lint, validate-git
- Require conversation resolution
- Enforce admins

**Maximum**:
- 2 aprovações
- Tudo do recommended
- Require last push approval
- Signed commits
- Linear history
- Status checks: build, test, lint, validate-git, security-scan

#### Badges de Conformidade

**BADGES.md** (`.github/templates/common/`)

Guia completo de badges para README, incluindo:
- Git Validation workflow status
- Conventional Commits badge
- GitHub Flow badge
- Branch Protection level
- Code Owners badge
- Signed Commits badge
- PR Size guidelines
- Required Approvals
- Pre-commit hooks

Exemplo de uso no README:
```markdown
[![Git Validation](https://github.com/owner/repo/workflows/Git%20Validation/badge.svg)](https://github.com/owner/repo/actions)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![GitHub Flow](https://img.shields.io/badge/Workflow-GitHub%20Flow-blue.svg)](https://docs.github.com/en/get-started/quickstart/github-flow)
![Branch Protection](https://img.shields.io/badge/Branch%20Protection-Recommended-green)
```

Template README atualizado automaticamente com badges no topo.

---

## ✅ Uso Automático pelo Scaffold

O scaffold agora copia automaticamente todos os templates (P1 + P2) ao criar um novo projeto:

```bash
# Criar novo projeto (templates são copiados automaticamente)
uv run scripts/scaffold.py new --name my-project --domain programming --language python

# Arquivos criados automaticamente (P1):
# ✅ CONTRIBUTING.md (raiz)
# ✅ .github/PULL_REQUEST_TEMPLATE.md
# ✅ .github/CODEOWNERS
# ✅ docs/BRANCH_PROTECTION_SETUP.md
# ✅ README.md com badges e seção "Contribuindo"

# Arquivos criados automaticamente (P2):
# ✅ .github/ISSUE_TEMPLATE/bug_report.yml
# ✅ .github/ISSUE_TEMPLATE/feature_request.yml
# ✅ .github/ISSUE_TEMPLATE/documentation.yml
# ✅ .github/ISSUE_TEMPLATE/question.yml
# ✅ .github/ISSUE_TEMPLATE/config.yml
# ✅ .github/workflows/git-validation.yml
# ✅ scripts/git-hooks/commit-msg (chmod 755)
# ✅ .github/BADGES.md
# ✅ scripts/setup-branch-protection.py (chmod 755)
```

### O Que É Processado Automaticamente

1. **Variáveis substituídas**:
   - `{{ project_name }}` → nome do projeto
   - `{{ current_date }}` → data de criação (YYYY-MM-DD)
   - `{{ github_repo }}` → nome do repositório
   - `{{ github_owner }}` → owner do repositório

2. **README.md gerado** com:
   - Badges de conformidade (Conventional Commits, GitHub Flow, Branch Protection)
   - Seção completa de contribuição
   - Links para CONTRIBUTING.md e BRANCH_PROTECTION_SETUP.md

3. **CODEOWNERS** com placeholders para customização:
   - `@tech-lead`, `@backend-team`, `@frontend-team`, etc.
   - Ajustar conforme estrutura da equipe

4. **Permissões executáveis** aplicadas automaticamente:
   - `scripts/git-hooks/commit-msg` → chmod 755
   - `scripts/setup-branch-protection.py` → chmod 755

### Próximos Passos Após Criar Projeto

1. **Ativar git hook**:
   ```bash
   cd projeto
   ln -s ../../scripts/git-hooks/commit-msg .git/hooks/commit-msg
   ```

2. **Customizar CODEOWNERS**:
   - Editar `.github/CODEOWNERS`
   - Substituir placeholders por times/usuários reais

3. **Configurar branch protection no GitHub**:
   ```bash
   export GITHUB_TOKEN=ghp_xxxxx
   python scripts/setup-branch-protection.py owner/repo --level recommended
   ```

4. **Ajustar issue templates** (opcional):
   - Editar `.github/ISSUE_TEMPLATE/*.yml` conforme necessidade do projeto

---

## 🛠️ Uso Manual (Projetos Legados)

Para aplicar em projeto existente que não foi criado pelo scaffold:

```bash
# 1. Copiar templates
cp .github/templates/common/CONTRIBUTING.md ./CONTRIBUTING.md
cp .github/templates/common/PULL_REQUEST_TEMPLATE.md ./.github/
cp .github/templates/common/CODEOWNERS ./.github/

# 2. Processar variáveis
sed -i 's/{{ project_name }}/my-project/g' CONTRIBUTING.md
sed -i "s/{{ current_date }}/$(date +%Y-%m-%d)/g" CONTRIBUTING.md

# 3. Customizar CODEOWNERS
# Editar .github/CODEOWNERS e substituir @placeholders

# 4. Copiar guia
cp docs/guides/BRANCH_PROTECTION_SETUP.md ./docs/

# 5. Configurar branch protection no GitHub
# Seguir passos em docs/BRANCH_PROTECTION_SETUP.md
```

---

## 📚 Referências

### Documentação Interna
- [GitHub_Melhores_praticas_de_atualizacao_repositprios.md](GitHub_Melhores_praticas_de_atualizacao_repositprios.md) - Documento base
- [BRANCH_PROTECTION_SETUP.md](../BRANCH_PROTECTION_SETUP.md) - Guia de configuração
- [scripts/lib/git_validators.py](../../scripts/lib/git_validators.py) - Código dos validadores
- [tests/test_git_validators.py](../../tests/test_git_validators.py) - Testes

### Documentação Externa
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)
- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

---

**Última atualização**: 2026-05-17
**Responsável**: DevEx Team
**Status**: ✅ P0 e P1 completos - Templates integrados no scaffold

**Implementação**:
- `scripts/lib/project.py`: Função `copy_github_templates()` + `_copy_file_with_vars()`
- `scripts/lib/flows/new_project.py`: Chamada integrada no fluxo de criação
- Template README atualizado com seção "Contribuindo"
- Testes validados com projeto de exemplo
