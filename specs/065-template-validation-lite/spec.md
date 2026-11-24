# IMP-65-LITE: Template Validation + Scaffold Logger

**Status**: 🟢 Ativo (simplificado)
**Prioridade**: P1
**Estimativa**: 3-4h
**Contexto**: Versão simplificada do IMP-65 original, focada no caso de uso real (scaffold one-time de novos projetos)

---

## 🎯 Objetivo

Validar templates antes de scaffold e manter registro histórico de projetos criados, **sem CI/CD automation** (over-engineering para uso atual).

**Diferença do IMP-65 original**:
- ❌ SEM drift check automático (projetos divergem intencionalmente após scaffold)
- ❌ SEM CI/CD workflows (não há sincronização contínua)
- ❌ SEM notificações Slack/Email
- ✅ Validação de templates antes de scaffold
- ✅ Log histórico de scaffolds criados
- ✅ Validação de breaking changes em templates (manual)

---

## 📋 Requisitos

### P0: Validação de Templates (1h)

**Objetivo**: Garantir templates válidos antes de scaffold

**Funcionalidades**:
1. **Lint YAML/JSON**:
   ```bash
   python scripts/validate-templates.py
   # Valida sintaxe de todos arquivos em .specify/templates/
   ```

2. **Check de variáveis obrigatórias**:
   ```yaml
   # spec.md frontmatter
   ---
   template: spec-template
   version: 2.0.0
   required_vars:
     - PROJECT_NAME
     - AUTHOR
   ---
   ```

3. **Validação de referências**:
   - Links internos em Markdown
   - Imports/includes entre templates
   - Caminhos de arquivos

**Entrega**:
- `scripts/validate-templates.py` (standalone)
- `make validate-templates` (Makefile)
- Exit 1 se inválido (pode rodar em pre-commit hook)

---

### P1: Scaffold Logger (2h)

**Objetivo**: Registrar histórico de projetos criados a partir do template

**Arquivo**: `logs/scaffolds.yaml`

**Estrutura**:
```yaml
scaffolds:
  - id: 1
    timestamp: "2026-04-28T14:30:00Z"
    project_name: "vya-api-users"
    template_version: "2.1.0"
    profile: "python-fastapi"
    created_by: "yves_marinho"
    path: "/home/yves/projects/vya-api-users"

  - id: 2
    timestamp: "2026-04-29T09:15:00Z"
    project_name: "vya-frontend-app"
    template_version: "2.1.0"
    profile: "typescript-next"
    created_by: "yves_marinho"
    path: "/home/yves/projects/vya-frontend-app"
```

**Integração com scaffold**:
```python
# scripts/scaffold.py
from scaffold_logger import ScaffoldLogger

logger = ScaffoldLogger("logs/scaffolds.yaml")

# Ao criar projeto
logger.log_scaffold(
    project_name="vya-api-users",
    template_version=get_template_version(),
    profile="python-fastapi",
    created_by=get_current_user(),
    path=target_path
)
```

**Queries**:
```bash
# Listar scaffolds recentes
python scripts/scaffold-query.py --last 30d

# Contar por perfil
python scripts/scaffold-query.py --stats

# Buscar por nome
python scripts/scaffold-query.py --project "vya-*"
```

**Entrega**:
- `scripts/scaffold_logger.py` (classe ScaffoldLogger)
- `scripts/scaffold-query.py` (CLI para queries)
- Integração com `scripts/scaffold.py` existente
- Testes básicos

---

## 🔄 Workflow Manual (sem CI/CD)

```
┌─────────────────────────────────────┐
│ 1. Developer melhora template base  │
│    (adiciona healthcheck, etc)      │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 2. Roda validação local:            │
│    make validate-templates          │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 3. Commita mudança no template      │
│    git commit -m "feat: add health" │
└────────────────┬────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────┐
│ 4. Próximo scaffold usa nova versão│
│    python scripts/scaffold.py ...   │
│    → Log registrado automaticamente │
└─────────────────────────────────────┘
```

**Importante**: Projetos existentes **NÃO** são atualizados automaticamente (cada um evolui independente).

---

## 📊 Comparação: IMP-65 vs IMP-65-LITE

| Componente | IMP-65 Original | IMP-65-LITE | Justificativa |
|-----------|----------------|-------------|---------------|
| **P0: Validação** | ✅ | ✅ | Sempre necessário |
| **Drift Detection** | ✅ Weekly CI | ❌ | Sem projetos sincronizados |
| **Breaking Detection** | ✅ Automática | ⚠️ Manual | Template evolution tracking |
| **Audit Trail** | ✅ Completo | ✅ Scaffold log | Log simplificado suficiente |
| **CI/CD Workflows** | ✅ 3 workflows | ❌ | Over-engineering |
| **Notificações** | ✅ Slack/Email | ❌ | Sem eventos automáticos |
| **Auto-update PRs** | ✅ | ❌ | Sem sincronização |
| **Scaffold Logger** | ❌ | ✅ | Uso real |
| **Estimativa** | 25h | 3-4h | 85% redução |

---

## 🎓 Aprendizado dos POCs (referência futura)

**POCs 1-4 permanecem como documentação** para cenários futuros:

### Quando CI/CD faz sentido:
- ✅ Empresa com 10+ projetos ativos sincronizados
- ✅ Template central compartilhado multi-times
- ✅ Necessidade de propagar fixes de segurança rapidamente
- ✅ Monorepo com múltiplos serviços

### Quando CI/CD é over-engineering:
- ❌ Template usado one-time para scaffold
- ❌ Projetos divergem intencionalmente após criação
- ❌ Poucos projetos ativos (< 5)
- ❌ Updates de template raros (< mensais)

**Documentação**: `docs/reference/POC-LEARNINGS.md`

---

## ✅ Definition of Done

- [x] `scripts/validate-templates.py` funcional — ✅ escopo corrigido para `scaffold/templates/` no PR #64 (antes mirava `.specify/templates/` e sempre falhava) (conferido 24/11/2026)
- [x] Validação de YAML/JSON syntax — ✅ inclui YAML multi-documento, objetivo v2 híbrido e templates Go (PR #64) (conferido 24/11/2026)
- [x] Check de variáveis obrigatórias — ✅ `_validate_variables` (conferido 24/11/2026)
- [x] Validação de links/referências — ✅ opt-in `--check-links` (links dos templates apontam para o projeto gerado) (conferido 24/11/2026)
- [x] `make validate-templates` no Makefile — ✅ e no CI (job Lint & Validate, PR #64) (conferido 24/11/2026)
- [x] `scripts/scaffold_logger.py` implementado — ✅ (conferido 24/11/2026)
- [x] `logs/scaffolds.yaml` criado — ✅ (conferido 24/11/2026)
- [x] Integração com `scripts/scaffold.py` — ✅ via `scripts/lib/flows/new_project.py` (conferido 24/11/2026)
- [x] `scripts/scaffold-query.py` para consultas — ✅ (conferido 24/11/2026)
- [x] Testes básicos (4-5 testes) — ✅ `test_validate_templates*.py`, `test_scaffold_logger.py`, `test_scaffold_logs_dir.py` (conferido 24/11/2026)
- [x] Documentação em `docs/guides/TEMPLATE_VALIDATION.md` — ✅ (conferido 24/11/2026)
- [x] POCs documentados em `docs/reference/POC-LEARNINGS.md` — ✅ (conferido 24/11/2026)

---

## 📦 Entregáveis

```
scripts/
  validate-templates.py      # P0: Template validation
  scaffold_logger.py         # P1: Scaffold logging
  scaffold-query.py          # P1: Query scaffolds
  scaffold.py               # Existing, add logger integration

logs/
  scaffolds.yaml            # Scaffold history

tests/
  test_validate_templates.py
  test_scaffold_logger.py

docs/
  guides/
    TEMPLATE_VALIDATION.md  # Como usar validação
  reference/
    POC-LEARNINGS.md        # Quando usar CI/CD
```

---

## 🚀 Implementação (3-4h)

### Fase 1: Validação (1h)
1. Criar `validate-templates.py`
2. Implementar lint YAML/JSON
3. Implementar check variáveis
4. Adicionar validação de links
5. Integrar com Makefile

### Fase 2: Scaffold Logger (2h)
1. Criar `scaffold_logger.py`
2. Implementar ScaffoldLogger class
3. Criar `logs/scaffolds.yaml` structure
4. Integrar com `scaffold.py`
5. Criar `scaffold-query.py`

### Fase 3: Documentação (1h)
1. `TEMPLATE_VALIDATION.md`
2. `POC-LEARNINGS.md` (consolidar POCs 1-4)
3. Atualizar `README.md`
4. Tests

---

## 📝 Notas

- **POCs 1-4** não são deletados, servem como referência
- **IMP-65 original** permanece como spec alternativa
- **Scaffold logger** usa YAML por simplicidade (sem performance issue para ~100 scaffolds/ano)
- **Breaking changes** detectadas manualmente (via diff visual de templates)
- **Futuro**: Se projeto escalar para 10+ projetos ativos sincronizados, reavaliar CI/CD

---

## 🔗 Referências

- **IMP-65 Original**: `specs/065-template-validation/spec.md`
- **POC-1**: `poc/imp65-p1-validation/POC-1_drift_detection/POC-1_RESULTS.md`
- **POC-2**: `poc/imp65-p1-validation/POC-2_breaking_changes/POC-2_RESULTS.md`
- **POC-3**: `poc/imp65-p1-validation/POC-3_audit_trail/POC-3_RESULTS.md`
- **POC-4**: `poc/imp65-p1-validation/POC-4_e2e_cicd/POC-4_RESULTS.md`
