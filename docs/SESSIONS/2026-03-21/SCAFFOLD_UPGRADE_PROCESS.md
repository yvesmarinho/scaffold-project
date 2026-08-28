# 🔄 Processo de `scaffold.py upgrade`

**Data**: 2026-03-21
**Versão do Scaffold**: 1.0.0
**Arquivo de Implementação**: `scripts/lib/flows/upgrade.py`

---

## 📖 Visão Geral

O comando `scaffold.py upgrade` **re-aplica o template** a um projeto já existente, permitindo que projetos criados anteriormente recebam atualizações do template sem perder customizações.

```bash
# Sintaxe básica
scaffold.py upgrade [--force]

# ou (forma legada)
scaffold.py --upgrade [--force]
```

---

## 🎯 Objetivo

**Problema resolvido**: "O projeto foi gerado há 6 meses, o template evoluiu. Como atualizo sem sobrescrever minhas customizações?"

**Solução**: Operações idempotentes baseadas em arquivo de estado (`.scaffold-state.yaml`)

---

## 📋 Pré-requisitos

### 1. Arquivo `.scaffold-state.yaml` Presente

O projeto **deve ter sido criado com scaffold.py >= 1.0.0** ou ter o arquivo `.scaffold-state.yaml` na raiz.

**Estrutura do arquivo:**
```yaml
scaffold_version: 1.0.0
created_at: '2026-03-20T18:44:10Z'
updated_at: '2026-03-20T18:45:03Z'
project:
  name: enterprise-update-lab-n8n
  title: Enterprise Update Lab N8N
  description: Laboratório para atualização de versão do N8N
  domain: infrastructure
  language: python
  github_repo: ''
paths:
  target_dir: /home/yves_marinho/Documentos/DevOps/Vya-Jobs
  shared_dir: /home/yves_marinho/Documentos/DevOps/.copilot-shared
profiles_applied: []
```

### 2. Executar do Diretório do Projeto

```bash
cd /path/to/projeto
uv run /path/to/scaffold-project/scripts/scaffold.py upgrade
```

ou especificar diretório:

```bash
scaffold.py upgrade --target-dir /path/to/projeto
```

---

## 🔄 Fluxo de Execução

### Etapa 1: Leitura do Estado

```python
# scripts/lib/flows/upgrade.py:35-52
state = read_scaffold_state(target)
if state is None:
    return 1  # Erro: arquivo não encontrado

cfg = config_from_state(state, override_target=target)
profiles_applied = state.get("profiles_applied", [])
```

**Validações:**
- ✅ Arquivo `.scaffold-state.yaml` existe
- ✅ YAML é válido e contém campos obrigatórios
- ❌ Se não existe → erro com mensagem clara

---

### Etapa 2: Re-aplicação Idempotente (7 passos)

Todos os passos são **idempotentes** (seguros para executar múltiplas vezes):

#### 2.1. 📁 Estrutura de Pastas

```python
results.extend(project.create_structure(cfg))
```

**Diretórios criados** (se ausentes):
- `docs/`, `docs/SESSIONS/`, `docs/copilot/`
- `.github/`, `.github/agents/`, `.github/prompts/`, `.github/prompts/domain/`
- `.secrets/`, `.specify/`, `.specify/memory/`, `.vscode/`
- `scripts/`, `scripts/lib/`, `scripts/logs/`
- `src/`, `tests/`

**Comportamento:**
- ✅ Pasta já existe → skipped
- ✅ Pasta não existe → created

---

#### 2.2. 🔗 Symlinks `.copilot-*`

```python
results.extend(links.setup_symlinks(cfg))
```

**Symlinks gerenciados:**
- `.copilot-rules.md` → `../../.copilot-shared/.copilot-rules.md`
- (outros symlinks compartilhados)

**Comportamento:**
- ✅ Symlink correto → skipped
- ⚠️ Symlink quebrado → recriado
- ✅ Ausente → created

---

#### 2.3. 📝 Regras Copilot Específicas do Projeto

```python
results.append(templates.generate_copilot_rules(cfg))
results.append(templates.generate_copilot_instructions(cfg))
```

**Arquivos gerados:**
- `.copilot-rules-{projeto}.md` (regras específicas do projeto)
- `.github/copilot-instructions.md` (instruções de contexto)

**Comportamento:**
- Arquivo existe com **conteúdo idêntico** → skipped
- Arquivo existe com **conteúdo diferente**:
  - **Sem `--force`**: skipped (preserva customizações) ⚠️
  - **Com `--force`**: sobrescrito

---

#### 2.4. 🔧 Configuração VS Code

```python
results.append(vscode.generate_settings(cfg))
results.append(vscode.generate_mcp(cfg))
results.append(vscode.generate_extensions(cfg))
results.append(vscode.generate_tasks(cfg))
results.append(vscode.generate_launch(cfg))
```

**Arquivos gerenciados:**
- `.vscode/settings.json`
- `.vscode/mcp.json`
- `.vscode/extensions.json`
- `.vscode/tasks.json`
- `.vscode/launch.json`

**Comportamento:** Idempotente (mesma lógica da etapa 2.3)

---

#### 2.5. 🤖 Assets SpecKit

```python
results.extend(project.copy_speckit(cfg))
```

**Arquivos copiados:**

| Origem (template) | Destino (projeto) |
|-------------------|-------------------|
| `.github/agents/*.agent.md` | `.github/agents/` |
| `.github/prompts/speckit.*.prompt.md` | `.github/prompts/` |
| `.github/prompts/session-*.prompt.md` | `.github/prompts/` |
| `.specify/templates/**/*` | `.specify/templates/` |
| `.specify/config.json` | `.specify/` |
| `.github/prompts/domain/{domain}.prompt.md` | `.github/prompts/domain/` |
| `.github/prompts/domain/devops-security.prompt.md` | (transversal) |

**Comportamento:**
- ✅ Arquivo existe → skipped
- ✅ Arquivo ausente → copiado com `shutil.copy2()` (preserva timestamps)

**🐛 Bug corrigido hoje (2026-03-21):**
- Antes: padrão `"speckit.*.agent.md"` não copiava `session-manager` e `template-architect`
- Agora: padrão `"*.agent.md"` copia **todos os agentes**

---

#### 2.6. 📜 Constitution

```python
results.append(project.generate_constitution(cfg))
```

**Arquivo:** `.specify/memory/constitution.md`

**Comportamento:** Idempotente (mesma lógica da etapa 2.3)

---

#### 2.7. 🔑 MCP Script

```python
results.append(project.generate_load_mcp(cfg))
```

**Arquivo:** `scripts/load-mcp.sh`

**Comportamento:** Idempotente (mesma lógica da etapa 2.3)

---

### Etapa 3: Re-aplicação de Perfis

```python
if profiles_applied:
    composer.compose(profiles_applied, cfg)
    templates.generate_profile_guide(cfg, profiles_applied, composer.descriptors)
```

**Ação:**
- Re-aplica todos os perfis registrados em `profiles_applied` no `.scaffold-state.yaml`
- Gera/atualiza `docs/PROFILE_GUIDE_{projeto}.md`

**Comportamento:**
- Operação idempotente (arquivos duplicados são ignorados)
- Novos arquivos de perfis são adicionados

---

### Etapa 4: Atualização do Estado

```python
write_scaffold_state(cfg, profiles_applied=profiles_applied)
```

**Ação:**
- Atualiza campo `updated_at` no `.scaffold-state.yaml`
- Preserva `profiles_applied` e demais metadados

---

## 🎛️ Flags e Opções

### `--force`

**Comportamento:**
```bash
scaffold.py upgrade --force
```

- ❌ **Sem `--force`** (padrão): arquivos existentes com conteúdo diferente são **preservados** (skipped)
- ⚠️ **Com `--force`**: arquivos existentes são **sobrescritos** mesmo com divergências

**Use quando:**
- Quer forçar sobrescrever customizações locais
- Revertir modificações manuais inválidas
- Aplicar mudanças breaking do template

---

### `--json`

**Comportamento:**
```bash
scaffold.py upgrade --json
```

**Output JSON:**
```json
{
  "project": "enterprise-update-lab-n8n",
  "upgrade": true,
  "created": 2,
  "skipped": 45,
  "errors": 0,
  "profiles_applied": []
}
```

**Útil para:**
- CI/CD pipelines
- Automação de atualizações em múltiplos projetos
- Monitoramento programático

---

## 📊 Resumo Final

Após execução, o comando exibe:

```
✅ Upgrade concluído: 2 arquivo(s) novo(s) ou atualizado(s).
```

ou

```
✅ Projeto já está atualizado — nenhuma mudança necessária.
```

**Categorias reportadas:**
- 🟢 **created**: arquivos novos criados
- 🟡 **skipped**: arquivos já existentes (idênticos ou preservados)
- 🔴 **error**: erros durante a operação

---

## 🔍 Casos de Uso

### Caso 1: Atualizar Projeto com Novos Agentes

**Contexto:** Template ganhou novos agentes (`session-manager`, `template-architect`)

```bash
cd enterprise-update-lab-n8n
uv run ../scaffold-project/scripts/scaffold.py upgrade
```

**Resultado:**
- ✅ Novos agentes copiados para `.github/agents/`
- ✅ Arquivos existentes preservados
- ✅ `.scaffold-state.yaml` atualizado com `updated_at`

---

### Caso 2: Forçar Atualização de Regras Copilot

**Contexto:** Você modificou `.copilot-rules-projeto.md` mas quer voltar ao padrão

```bash
scaffold.py upgrade --force
```

**Resultado:**
- ⚠️ Arquivo sobrescrito com versão do template
- ✅ Customizações perdidas (use git para recuperar se necessário)

---

### Caso 3: Auditoria em CI/CD

**Contexto:** Verificar se projeto está atualizado com template

```bash
scaffold.py upgrade --json | jq '.created'
# Output: 0 (nenhuma mudança == atualizado)
```

---

## 🚨 Limitações e Cuidados

### ❌ Não Funciona Se:

1. **Projeto não criado com scaffold.py**
   - Erro: `.scaffold-state.yaml` ausente
   - Solução: Adicionar arquivo manualmente ou usar `scaffold.py new`

2. **`.scaffold-state.yaml` corrompido/inválido**
   - Erro: Parse YAML falha
   - Solução: Corrigir YAML ou recriar arquivo

### ⚠️ Cuidados:

1. **`--force` sobrescreve customizações**
   - Use git/backup antes de `--force`
   - Revise mudanças com `git diff`

2. **Perfis não são adicionados automaticamente**
   - `upgrade` re-aplica perfis existentes
   - Para adicionar novos perfis: use `scaffold.py compose`

3. **Arquivos deletados manualmente são recriados**
   - Se você deletou um arquivo do template, upgrade o recria
   - Solução: manter arquivo vazio ou adicionar ao `.gitignore` local

---

## 📚 Arquivos Relacionados

| Arquivo | Responsabilidade |
|---------|------------------|
| `scripts/lib/flows/upgrade.py` | Lógica principal do upgrade |
| `scripts/lib/project.py` | Funções `read_scaffold_state()`, `write_scaffold_state()` |
| `scripts/lib/links.py` | Gerenciamento de symlinks |
| `scripts/lib/templates.py` | Geração de templates (regras, instructions) |
| `scripts/lib/vscode.py` | Geração de configs VS Code |
| `scripts/lib/composer.py` | Re-aplicação de perfis |
| `.scaffold-state.yaml` | Estado persistido do projeto |

---

## 🎯 Conclusão

O `scaffold.py upgrade` é uma ferramenta **idempotente e segura** para manter projetos atualizados com a evolução do template, equilibrando:

- ✅ **Segurança**: preserva customizações por padrão
- ✅ **Flexibilidade**: `--force` quando necessário
- ✅ **Rastreabilidade**: `.scaffold-state.yaml` registra estado
- ✅ **Automação**: suporte a `--json` para CI/CD

**Recomendação:** Execute periodicamente após atualizações do template principal.
