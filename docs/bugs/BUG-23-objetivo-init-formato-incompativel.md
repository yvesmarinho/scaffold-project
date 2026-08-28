# BUG-23: objetivo-init gera formato incompatível com pipeline v2.0

**Status**: 🔴 ABERTO
**Prioridade**: P0 CRÍTICA
**Criado**: 2026-05-21
**Descoberto durante**: Teste do pipeline Objetivo-Init (P1 HIGH task)
**Assignee**: yves_marinho

---

## 🐛 Descrição do Problema

O comando `scaffold.py objetivo-init` gera arquivo `objetivo-init.yaml` em **formato YAML puro** (legacy), mas os comandos subsequentes do pipeline (`objetivo-validate` e `objetivo-generate`) esperam **formato Markdown Híbrido v2.0**.

**Pipeline quebrado:**
```
objetivo-init wizard → objetivo-init.yaml (YAML puro)
                         ↓
                    [❌ FALHA]
                         ↓
                    objetivo-validate (espera Markdown Híbrido v2.0)
                         ↓
                    [❌ FALHA]
                         ↓
                    objetivo-generate (espera Markdown Híbrido v2.0)
```

---

## 📊 Impacto

**Severidade**: CRÍTICA
**Usuários afetados**: 100% dos usuários tentando usar pipeline objetivo-init
**Funcionalidade afetada**: Pipeline completo quebrado

**Consequências:**
- ❌ Pipeline documentado em `OBJETIVO_WIZARD_GUIDE.md` não funciona
- ❌ Usuários não conseguem validar output do wizard
- ❌ Usuários não conseguem gerar spec.yaml a partir do wizard
- ❌ Workflow Objetivo-Init → Validate → Generate → Scaffold inutilizável

---

## 🔍 Causa Raiz

Template usado pelo wizard está **desatualizado** (formato legacy pré-v2.0):

| Arquivo | Formato | Status |
|---------|---------|--------|
| `template-bases/objetivo-init-template.yaml` | YAML puro (`prompt:` structure) | ❌ LEGACY |
| `template-bases/examples/objetivo.yaml` | Markdown Híbrido v2.0 | ✅ CORRETO |

**Código afetado:**
```python
# scripts/lib/objetivo_wizard.py:127-129
self.template_path = template_path or (
    Path(__file__).parent.parent.parent / "template-bases" / "objetivo-init-template.yaml"
)
```

**Template legacy usado** (`objetivo-init-template.yaml`):
```yaml
prompt:
  role: user
  content:
    description: "{{DESCRIPTION}}"
    specification:
      - project_name: "{{PROJECT_NAME}}"
      - response: "{{RESPONSE}}"
      ...
```

**Formato esperado** (Markdown Híbrido v2.0):
```yaml
---
version: "2.0"
project:
  name: "{{PROJECT_NAME}}"
  ...
---

# 🎯 Objetivo: {{PROJECT_TITLE}}

## 1️⃣ O que este projeto faz?
...
```

---

## 🧪 Reprodução

### Passo a Passo

```bash
cd ~/Documentos/DevOps/Projetos/scaffold-project

# 1. Criar arquivo de respostas para teste
cat > tmp/test-answers.json << 'EOF'
{
  "project_name": "task-manager-api",
  "project_type": "api",
  "project_domain": "backend",
  "project_language": "python",
  "answers": {
    "q1_what": "REST API para gerenciar tarefas",
    "q3_scope_included": "CRUD de tarefas (P0)"
  }
}
EOF

# 2. Executar wizard (modo não-interativo)
python scripts/scaffold.py objetivo-init \
  --from-file tmp/test-answers.json \
  --output tmp/objetivo-test.yaml

# 3. Tentar validar (FALHA ESPERADA)
python scripts/scaffold.py objetivo-validate --file tmp/objetivo-test.yaml
# ❌ Erro: Failed to parse frontmatter
#    Missing or malformed YAML frontmatter. Expected format:
#    ---
#    version: "2.0"
#    ...
#    ---

# 4. Verificar formato gerado
head -20 tmp/objetivo-test.yaml
# Output: YAML puro (prompt:), NÃO Markdown Híbrido
```

### Output Real vs Esperado

**Output Real** (gerado atualmente):
```yaml
prompt:
  role: user
  content:
    description: ""
    specification:
      - project_name: "task-manager-api"
      - response: ""
      ...
```

**Output Esperado** (Markdown Híbrido v2.0):
```yaml
---
version: "2.0"
project:
  name: "task-manager-api"
  title: "Task Manager API"
  type: "backend-api"
  domain: "programming"
  language: "python"
---

# 🎯 Objetivo: Task Manager API

## 1️⃣ O que este projeto faz?

REST API para gerenciar tarefas com autenticação JWT

...
```

---

## ✅ Critérios de Aceitação

Pipeline completo deve funcionar end-to-end:

```bash
# 1. Wizard gera formato v2.0
python scripts/scaffold.py objetivo-init --from-file answers.json --output objetivo.yaml
# ✅ Output: Markdown Híbrido v2.0

# 2. Validação aceita formato
python scripts/scaffold.py objetivo-validate --file objetivo.yaml
# ✅ Output: "objetivo.yaml válido! 3/3 campos P0 preenchidos"

# 3. Geração de spec funciona
python scripts/scaffold.py objetivo-generate --input objetivo.yaml --output objetivo-spec.yaml
# ✅ Output: "Gerado: objetivo-spec.yaml"

# 4. Verificar formato do spec
cat objetivo-spec.yaml
# ✅ Contém: project:, profiles:, features:
```

---

## 🛠️ Solução Proposta

### Opção A: Criar template v2.0 (RECOMENDADA)

**Passos:**
1. Criar `template-bases/objetivo-v2-template.yaml` (Markdown Híbrido)
2. Copiar estrutura de `template-bases/examples/objetivo.yaml`
3. Substituir valores por placeholders (`{{PROJECT_NAME}}`, `{{DESCRIPTION}}`, etc.)
4. Atualizar `objetivo_wizard.py:127` para usar novo template
5. Validar com testes existentes (`tests/test_objetivo_wizard.py`)

**Arquivos a modificar:**
- ✅ `template-bases/objetivo-v2-template.yaml` (CRIAR)
- ✅ `scripts/lib/objetivo_wizard.py` (ATUALIZAR template_path default)
- ✅ `tests/test_objetivo_wizard.py` (VALIDAR formato output)

**Estimativa:** 1-2h

### Opção B: Deprecar objetivo-init e usar apenas objetivo.yaml

**Passos:**
1. Remover comando `objetivo-init`
2. Documentar que usuários devem copiar `template-bases/examples/objetivo.yaml`
3. Atualizar `OBJETIVO_WIZARD_GUIDE.md`

**Arquivos a modificar:**
- ❌ Quebra backward compatibility
- ❌ Remove feature útil (wizard interativo)

**Estimativa:** 30min (NÃO RECOMENDADA)

---

## 📋 Checklist de Implementação

### Fase 1: Criar Template v2.0
- [ ] Criar `template-bases/objetivo-v2-template.yaml`
  - [ ] Copiar frontmatter YAML de `examples/objetivo.yaml`
  - [ ] Substituir valores fixos por `{{PLACEHOLDERS}}`
  - [ ] Incluir seções P0 (1-3) obrigatórias
  - [ ] Incluir seções P1 (4-5) opcionais comentadas
  - [ ] Adicionar comentários `<!-- REQUIRED -->` e `<!-- OPTIONAL -->`

### Fase 2: Atualizar Wizard
- [ ] Modificar `scripts/lib/objetivo_wizard.py`
  - [ ] Linha 127-129: trocar `objetivo-init-template.yaml` → `objetivo-v2-template.yaml`
  - [ ] Atualizar `_render_template()` se necessário
  - [ ] Atualizar placeholders se necessário

### Fase 3: Validar Testes
- [ ] Executar `pytest tests/test_objetivo_wizard.py -v`
  - [ ] Verificar que output contém frontmatter YAML
  - [ ] Verificar que output contém seções markdown (## 1️⃣, ## 2️⃣, etc.)
  - [ ] Verificar que formato é Markdown Híbrido v2.0

### Fase 4: Validar Pipeline Completo
- [ ] Testar wizard → validate → generate → scaffold
  - [ ] `scaffold.py objetivo-init --from-file test.json`
  - [ ] `scaffold.py objetivo-validate --file objetivo.yaml` (deve passar)
  - [ ] `scaffold.py objetivo-generate --input objetivo.yaml` (deve gerar spec)
  - [ ] Verificar `objetivo-spec.yaml` gerado

### Fase 5: Documentação
- [ ] Atualizar `docs/guides/OBJETIVO_WIZARD_GUIDE.md`
  - [ ] Confirmar exemplos de output (Markdown Híbrido v2.0)
  - [ ] Adicionar nota sobre formato legacy descontinuado
- [ ] Atualizar `specs/066-objetivo-yaml-v2/README.md`
  - [ ] Marcar template legacy como deprecated
- [ ] Criar entry em `CHANGELOG.md`
  - [ ] `## [Unreleased] - 2026-05-21`
  - [ ] `### Fixed - BUG-23: objetivo-init agora gera Markdown Híbrido v2.0`

---

## 🧪 Casos de Teste

### Teste 1: Wizard Non-Interactive (modo CI/CD)

```bash
# Given: arquivo de respostas JSON
cat > tmp/answers.json << 'EOF'
{
  "project_name": "test-project",
  "answers": {
    "q1_what": "Test description"
  }
}
EOF

# When: executar wizard
python scripts/scaffold.py objetivo-init --from-file tmp/answers.json --output tmp/objetivo.yaml

# Then: formato deve ser Markdown Híbrido v2.0
grep -q "^---$" tmp/objetivo.yaml
grep -q 'version: "2.0"' tmp/objetivo.yaml
grep -q "^# 🎯 Objetivo:" tmp/objetivo.yaml
grep -q "^## 1️⃣" tmp/objetivo.yaml
```

### Teste 2: Pipeline Completo

```bash
# 1. Gerar objetivo.yaml via wizard
python scripts/scaffold.py objetivo-init --from-file tmp/answers.json --output tmp/objetivo.yaml

# 2. Validar (deve passar)
python scripts/scaffold.py objetivo-validate --file tmp/objetivo.yaml
# Expected exit code: 0

# 3. Gerar spec (deve criar arquivo)
python scripts/scaffold.py objetivo-generate --input tmp/objetivo.yaml --output tmp/spec.yaml
# Expected: tmp/spec.yaml criado com project:, profiles:, features:
```

### Teste 3: Testes Existentes (Regressão)

```bash
# Executar suite completa
pytest tests/test_objetivo_wizard.py -v

# Esperado: 16/16 testes passando
# Nota: alguns testes podem precisar atualização para validar novo formato
```

---

## 📚 Referências

- **Spec Original**: [specs/066-objetivo-yaml-v2/spec.md](../../specs/066-objetivo-yaml-v2/spec.md)
- **Tasks**: [specs/066-objetivo-yaml-v2/tasks.md](../../specs/066-objetivo-yaml-v2/tasks.md) (T034, T035)
- **Guia do Wizard**: [docs/guides/OBJETIVO_WIZARD_GUIDE.md](../guides/OBJETIVO_WIZARD_GUIDE.md)
- **Exemplo v2.0 Correto**: [template-bases/examples/objetivo.yaml](../../template-bases/examples/objetivo.yaml)
- **Template Legacy**: [template-bases/objetivo-init-template.yaml](../../template-bases/objetivo-init-template.yaml)

---

## 🏷️ Tags

`bug` `p0` `objetivo-init` `wizard` `formato-incompatível` `pipeline-quebrado` `markdown-híbrido` `v2.0`

---

**Última atualização**: 2026-05-21
**Testado em**: Python 3.12, scaffold.py v1.6.0
