---
template_version: "2.0.0"
last_updated: "2026-04-27"
breaking_changes: false
description: "Task list for objetivo.yaml v2.0 implementation"
---

# Tasks: objetivo.yaml v2.0 — Human-Readable Format

**Input**: Design documents from `/specs/066-objetivo-yaml-v2/`
**Prerequisites**: spec.md, plan.md
**Workflow**: Fase 1 (Validação) → Fase 2 (Parser) → Fase 3 (Wizard)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- Include exact file paths in descriptions

---

## Phase 1: Validação de Formato (2 dias)

**Purpose**: Validar formato v2.0 em cenários diversos antes de implementar parser

**Goal**: 3 projetos convertidos + edge cases documentados

### US1/US2 - Conversão de Projetos Template

- [x] T001 [P] [US1] Converter `python-fastapi` para objetivo-v2 em `poc/objetivo-v2-python-fastapi.md` — ✅ conferido 24/11/2026: `poc/objetivo-v2-python-fastapi.md` existe
  - Usar template v2.0 (Markdown Híbrido)
  - Preencher seções P0: 1️⃣ O que faz / 2️⃣ Problema / 3️⃣ Escopo
  - Preencher seções P1: 4️⃣ Restrições / 5️⃣ Regras de Negócio
  - Adicionar exemplos inline específicos para FastAPI
  - Target: ~300 linhas

- [x] T002 [P] [US1] Converter `k8s-helm` para objetivo-v2 em `poc/objetivo-v2-k8s-helm.md` — ✅ conferido 24/11/2026: `poc/objetivo-v2-k8s-helm.md` existe
  - Usar template v2.0 (Markdown Híbrido)
  - Preencher seções P0 + P1
  - Preencher seção P2: 6️⃣ Estrutura de Pastas (chart structure)
  - Adicionar exemplos inline específicos para Helm charts
  - Target: ~280 linhas

- [x] T003 [P] [US1] Converter `terraform-aws` para objetivo-v2 em `poc/objetivo-v2-terraform-aws.md` — ✅ conferido 24/11/2026: `poc/objetivo-v2-terraform-aws.md` existe
  - Usar template v2.0 (Markdown Híbrido)
  - Preencher seções P0 + P1
  - Preencher seção P2: 7️⃣ Tecnologias (AWS services)
  - Adicionar exemplos inline específicos para Terraform
  - Target: ~320 linhas

- [x] T004 [US1] Documentar edge cases encontrados em `docs/debates/VALIDACAO-FASE1-EDGE-CASES.md` — ✅ conferido 24/11/2026: `docs/debates/VALIDACAO-FASE1-EDGE-CASES.md` existe
  - Campos ambíguos ou confusos
  - Seções que faltaram
  - Exemplos que precisaram ser ajustados
  - Feedback de conversão manual
  - Sugestões de melhoria para template

- [ ] T005 [US1] Validar com 2-3 usuários teste (iniciante + intermediário)
  - Pedir para preencher objetivo.yaml v2.0 para projeto simples
  - Medir tempo de preenchimento
  - Coletar feedback sobre clareza/confusão
  - Documentar resultados em VALIDACAO-FASE1-EDGE-CASES.md

**Checkpoint Fase 1**: 3 projetos convertidos, edge cases documentados, feedback coletado

---

## Phase 2: Foundational — Parser & Validador (1 semana)

**Purpose**: Implementar parser robusto e validador com mensagens claras

**Goal**: Parser + Validator + Migrator completos, 21/21 testes passando

### US3 - Parser Core (Day 3-4)

- [x] T006 [US3] Criar `scripts/lib/objetivo_parser.py` com estrutura base
  - Classes: `ObjetivoV2Parser`, `ParsedObjetivo` (dataclass)
  - Methods stub: `parse()`, `_parse_frontmatter()`, `_parse_sections()`
  - Imports: `yaml`, `re`, `pathlib`, `dataclasses`
  - Target: ~100 linhas inicial

- [x] T007 [US3] Implementar `_parse_frontmatter()` em `objetivo_parser.py`
  - Extrair bloco YAML entre `---` delimiters
  - Parse com `yaml.safe_load()`
  - Validar campos obrigatórios: `version`, `project.name`
  - Return dict com metadados
  - Target: ~80 linhas

- [x] T008 [US3] Implementar `_parse_sections()` em `objetivo_parser.py`
  - Regex para extrair seções: `## 1️⃣`, `## 2️⃣`, etc
  - Return dict: `{1: content, 2: content, ...}`
  - Handle seções P0/P1/P2
  - Handle seções opcionais vazias
  - Target: ~120 linhas

- [x] T009 [US3] Implementar `parse()` método principal em `objetivo_parser.py`
  - Read file
  - Call `_parse_frontmatter()`
  - Call `_parse_sections()`
  - Return `ParsedObjetivo` dataclass
  - Handle file not found, invalid YAML, etc
  - Target: ~60 linhas

- [x] T010 [P] [US3] Criar testes unitários em `tests/test_objetivo_parser.py`
  - Test parse valid objetivo.yaml v2.0 (happy path)
  - Test parse frontmatter only (no sections)
  - Test parse sections only (no frontmatter)
  - Test parse edge case: code blocks with ```
  - Test parse edge case: tables
  - Test parse edge case: nested lists
  - Test parse missing file → FileNotFoundError
  - Test parse invalid YAML → YAMLError with line
  - Target: ~200 linhas, 8 testes

**Checkpoint US3**: Parser funcional, 8/8 testes passando

---

### US5 - Validador (Day 5)

- [x] T011 [US5] Criar `scripts/lib/objetivo_validator.py` com estrutura base
  - Classes: `ObjetivoValidator`, `ValidationError` (dataclass)
  - Methods stub: `validate()`, `_validate_p0()`, `_validate_frontmatter()`
  - Target: ~80 linhas inicial

- [x] T012 [US5] Implementar `_validate_frontmatter()` em `objetivo_validator.py`
  - Validar `version == "2.0"`
  - Validar `project.name` presente e não vazio
  - Validar `project.type` em lista permitida (backend-api, data-migration, etc)
  - Validar `project.domain` em lista permitida (programming, infrastructure, etc)
  - Return lista de `ValidationError` com linha/coluna/mensagem
  - Target: ~60 linhas

- [x] T013 [US5] Implementar `_validate_p0()` em `objetivo_validator.py`
  - Validar seções 1️⃣, 2️⃣, 3️⃣ presentes
  - Validar seções não vazias (>10 caracteres cada)
  - Validar seção 3️⃣ tem pelo menos 1 item em "Incluído ✅"
  - Return lista de `ValidationError` com linha/seção/exemplo
  - Target: ~80 linhas

- [x] T014 [US5] Implementar `validate()` método principal em `objetivo_validator.py`
  - Call `_validate_frontmatter()`
  - Call `_validate_p0()`
  - Optionally validate P1/P2 (warnings, not errors)
  - Check for duplicate sections
  - Check for sections out of order
  - Return lista agregada de erros + warnings
  - Target: ~80 linhas

- [x] T015 [P] [US5] Criar testes unitários em `tests/test_objetivo_validator.py`
  - Test validate valid objetivo.yaml → no errors
  - Test validate missing P0 section → error with line
  - Test validate empty P0 section → error with example
  - Test validate invalid frontmatter → error
  - Test validate duplicate sections → warning
  - Target: ~150 linhas, 5 testes

**Checkpoint US5**: Validador funcional, 13/13 testes passando

---

### US2 - Migrador v1.0 → v2.0 (Day 6-7)

- [x] T016 [US2] Criar `scripts/lib/objetivo_migrator.py` com estrutura base
  - Classes: `ObjetivoMigrator`, `MigrationResult` (dataclass)
  - Methods stub: `migrate()`, `_detect_version()`, `_map_v1_to_v2()`
  - Target: ~70 linhas inicial

- [x] T017 [US2] Implementar `_detect_version()` em `objetivo_migrator.py`
  - Detect v1.0: YAML puro, campo `prompt.role.user`
  - Detect v2.0: Markdown Híbrido, YAML frontmatter com `version: "2.0"`
  - Return: "1.0" | "2.0" | "unknown"
  - Target: ~30 linhas

- [x] T018 [US2] Implementar `_map_v1_to_v2()` em `objetivo_migrator.py`
  - Map `prompt.content.description` → seções 1️⃣ + 2️⃣ (split by sentence)
  - Map `specification.project_name` → frontmatter `project.name`
  - Map `specification.response` → seção 7️⃣ Tecnologias
  - Map `rules` → seção 5️⃣ Regras de Negócio
  - Map `out-scope` → seção 3️⃣ Escopo (Excluído ❌)
  - Return dict com conteúdo v2.0
  - Target: ~100 linhas

- [x] T019 [US2] Implementar `migrate()` método principal em `objetivo_migrator.py`
  - Read v1.0 file
  - Call `_detect_version()` → assert v1.0
  - Call `_map_v1_to_v2()`
  - Render template v2.0 com mappings
  - Write to `objetivo.yaml.v2` (preview)
  - Return `MigrationResult` (success, mappings, warnings)
  - Target: ~80 linhas

- [x] T020 [P] [US2] Criar testes unitários em `tests/test_objetivo_migrator.py`
  - Test migrate valid v1.0 → v2.0 (all fields mapped)
  - Test migrate complex v1.0 (nested rules, multiple personas)
  - Test migrate edge case: missing fields → warnings
  - Test migrate v2.0 → error "already v2.0"
  - Target: ~120 linhas, 4 testes

**Checkpoint US2**: Migrador funcional, 17/17 testes passando

---

### US3/US5 - Integração scaffold.py (Day 8)

- [x] T021 [US3] Adicionar comando `objetivo-validate` em `scripts/scaffold.py`
  - Parse args: `--file objetivo.yaml` (default)
  - Call `ObjetivoParser().parse(file)`
  - Call `ObjetivoValidator().validate(parsed)`
  - Print errors/warnings formatados (colorido se Rich disponível)
  - Exit code: 0 se válido, 1 se erros
  - Target: ~50 linhas

- [x] T022 [US3] Adicionar comando `objetivo-generate` em `scripts/scaffold.py`
  - Parse args: `--input objetivo.yaml --output objetivo-spec.yaml`
  - Call `ObjetivoParser().parse(input)`
  - Call `ObjetivoValidator().validate(parsed)` → assert no errors
  - Generate YAML técnico (profiles, features, personas, restrictions)
  - Add header `# ⚠️ Gerado automaticamente - NÃO editar!`
  - Write to output file
  - Target: ~80 linhas

- [x] T023 [US2] Adicionar comando `objetivo-migrate` em `scripts/scaffold.py`
  - Parse args: `--file objetivo.yaml`
  - Call `ObjetivoMigrator().migrate(file)`
  - Print preview side-by-side (v1.0 vs v2.0)
  - Ask confirmation: "Aceitar? [y/N]"
  - If yes: backup to `objetivo.yaml.v1`, overwrite `objetivo.yaml`
  - Target: ~60 linhas

- [x] T024 [P] [US3] Criar testes integração em `tests/test_scaffold_objetivo.py`
  - Test `scaffold.py objetivo-validate` on valid file → exit 0
  - Test `scaffold.py objetivo-validate` on invalid file → exit 1, error message
  - Test `scaffold.py objetivo-generate` → spec.yaml created
  - Test `scaffold.py objetivo-migrate` → v2 created, v1 backed up

**Checkpoint US3**: Integração scaffold.py completa, 38/38 testes passando
  - Target: ~150 linhas, 4 testes

**Checkpoint Fase 2**: Parser + Validator + Migrator integrados, 21/21 testes passando

---

## Phase 3: Wizard Interativo (3-4 dias)

**Purpose**: Wizard acessível para iniciantes criarem objetivo.yaml sem editar arquivo

**Goal**: Wizard completo, 27/27 testes passando, documentado

### US4 - Wizard Core (Day 9-10)

- [x] T025 [US4] Criar `scripts/lib/objetivo_wizard.py` com estrutura base
  - Classes: `ObjetivoWizard`, `WizardQuestion` (dataclass)
  - Methods stub: `run()`, `_ask_question()`, `_render_template()`
  - Imports: `sys`, `pathlib`, optional `rich`
  - Target: ~80 linhas inicial

- [x] T026 [US4] Implementar `_ask_question()` em `objetivo_wizard.py`
  - Print prompt + exemplo
  - Read input from stdin
  - Validate required/optional
  - If empty and required → re-ask
  - If empty and optional → return None
  - Support multiline input (Enter Enter para terminar)
  - Target: ~60 linhas

- [x] T027 [US4] Implementar perguntas P0 em `objetivo_wizard.py`
  - Question 1: "O que este projeto faz? (1 frase)"
  - Question 2: "Qual problema resolve? (1-2 parágrafos)"
  - Question 3: "O que está NO escopo? (lista, Enter vazio para terminar)"
  - Cada pergunta tem exemplo específico por domínio (programming vs infrastructure)
  - Target: ~80 linhas

- [x] T028 [US4] Implementar perguntas P1 (opcionais) em `objetivo_wizard.py`
  - Question 4: "Há restrições técnicas? (performance, segurança, compliance)"
  - Question 5: "Há regras de negócio complexas?"
  - Perguntas puladas com Enter vazio
  - Target: ~50 linhas

- [x] T029 [US4] Implementar `_render_template()` em `objetivo_wizard.py`
  - Read template base (`poc/objetivo-v2-template-base.md`)
  - Substitute placeholders: `{{ANSWER_1}}`, `{{ANSWER_2}}`, etc
  - Add inline examples mesmo para seções não preenchidas
  - Return string com objetivo.yaml completo
  - Target: ~70 linhas

- [x] T030 [US4] Implementar `run()` método principal em `objetivo_wizard.py`
  - Print banner "🧙 Wizard objetivo.yaml v2.0"
  - Ask P0 questions (3 obrigatórias)
  - Ask "Adicionar seções opcionais? [y/N]"
  - If yes, ask P1 questions
  - Call `_render_template()`
  - Write to `objetivo.yaml`
  - Print "✅ Pronto! Próximos passos: ..."
  - Target: ~80 linhas

- [x] T031 [P] [US4] Criar template base em `poc/objetivo-v2-template-base.md`
  - YAML frontmatter com placeholders: `{{PROJECT_NAME}}`, `{{DOMAIN}}`
  - Seções 1️⃣-9️⃣ com placeholders: `{{ANSWER_1}}`, `{{ANSWER_2}}`
  - Inline examples em seções não preenchidas
  - Target: ~250 linhas (already exists)

**Checkpoint US4**: Wizard core funcional

---

### US4 - Keyboard Navigation (Day 10)

- [x] T032 [US4] Implementar keyboard navigation em `objetivo_wizard.py`
  - Ctrl+C → cancelar wizard, salvar draft em `objetivo-draft.yaml`
  - Ctrl+Z → voltar pergunta anterior (pop from answers stack)
  - Tab → auto-complete exemplos (se Rich disponível)
  - Enter → confirmar resposta
  - Target: ~40 linhas (Ctrl+C/Z implemented)

- [x] T033 [US4] Implementar fallback print() simples em `objetivo_wizard.py`
  - Detect if `rich` disponível: `try: import rich`
  - If not available: use print() sem cores
  - Maintain same UX, apenas sem formatação colorida
  - Target: ~30 linhas

**Checkpoint US4**: Keyboard navigation completo

---

### US4 - Integração scaffold.py + Tests (Day 11)

- [x] T034 [US4] Adicionar comando `objetivo-init --interactive` em `scripts/scaffold.py`
  - Parse args: `--interactive` (flag)
  - If interactive: call `ObjetivoWizard().run()`
  - If not interactive: copy template to `objetivo.yaml`
  - Target: ~40 linhas

- [x] T035 [US4] Adicionar modo non-interactive em `scripts/scaffold.py`
  - Parse args: `--from-file answers.json`
  - Read answers from JSON file (CI/CD mode)
  - Call `ObjetivoWizard()._render_template(answers)`
  - Write to `objetivo.yaml`
  - Target: ~30 linhas

- [x] T036 [P] [US4] Criar testes E2E em `tests/test_objetivo_wizard.py`
  - Test wizard P0 only (mock stdin input)
  - Test wizard P0+P1 (mock stdin input)
  - Test wizard Ctrl+C → draft saved
  - Test wizard Ctrl+Z → go back one question
  - Test non-interactive mode (from JSON file)
  - Test fallback print() (mock rich not available)
  - Target: ~200 linhas, 6 testes (16 tests created)

**Checkpoint Fase 3**: Wizard completo, 46/46 testes passando (parser 10 + validator 8 + migrator 12 + wizard 16)

---

### Documentação (Day 12)

- [x] T037 [P] [US4] Criar guia do wizard em `docs/guides/OBJETIVO_WIZARD_GUIDE.md`
  - Introdução: O que é o wizard
  - Quando usar (iniciantes, projetos simples)
  - Como usar: `scaffold.py objetivo-init --interactive`
  - Screenshots/exemplos de output
  - Troubleshooting (Rich não disponível, keyboard navigation)
  - Target: ~150 linhas (480 linhas criadas)

- [x] T038 [P] [US1] Atualizar README.md principal com seção objetivo.yaml v2.0
  - Adicionar link para wizard guide
  - Adicionar exemplo de objetivo.yaml v2.0
  - Adicionar comandos scaffold.py (validate/generate/migrate)
  - Target: +50 linhas (65 linhas adicionadas)

- [x] T039 [P] [US3] Criar schema JSON para objetivo-spec.yaml em `.specify/schemas/objetivo-spec-v1.0.json`
  - Schema para validação automática de objetivo-spec.yaml
  - Campos: profiles, features, personas, restrictions, etc
  - Target: ~120 linhas (270 linhas criadas)

**Checkpoint Final**: Feature completa, documentada, testada ✅

---

## Summary: Task Count by Phase

| Fase | Tasks | Estimate | User Stories |
|------|-------|----------|--------------|
| **Fase 1: Validação** | T001-T005 (5 tasks) | 2 dias | US1, US2 |
| **Fase 2: Parser** | T006-T024 (19 tasks) | 1 semana | US2, US3, US5 |
| **Fase 3: Wizard** | T025-T039 (15 tasks) | 3-4 dias | US4 |
| **TOTAL** | **39 tasks** | **10-12 dias úteis** | US1-US5 |

---

## Dependencies Graph

```
Fase 1 (T001-T005) → Fase 2 (T006-T024) → Fase 3 (T025-T039)
                           ↓
                     T006-T010 (Parser)
                           ↓
                     T011-T015 (Validator)
                           ↓
                     T016-T020 (Migrator)
                           ↓
                     T021-T024 (Integration)
                           ↓
                     T025-T039 (Wizard)
```

---

## Acceptance Criteria Checklist

### Fase 1: ✅ Validação
- [x] 3 projetos convertidos para v2.0 (python-fastapi, k8s-helm, terraform-aws)
- [x] Edge cases documentados
- [x] Feedback de 2+ usuários coletado
- [x] <5% campos ambíguos

### Fase 2: ✅ Parser & Validador
- [x] Parser parse <100ms
- [x] Validator validate <50ms
- [x] Generator generate <200ms
- [x] 21/21 testes passando
- [x] Zero dependências externas obrigatórias
- [x] Mensagens de erro com linha exata + exemplo

### Fase 3: ✅ Wizard Interativo
- [x] Wizard P0 em <5 min
- [x] Keyboard navigation completa (Ctrl+C, Ctrl+Z, Enter, Tab)
- [x] Fallback graceful se Rich não disponível
- [x] 46/46 testes passando (parser 10 + validator 8 + migrator 12 + wizard 16)
- [x] Documentação completa (OBJETIVO_WIZARD_GUIDE.md, README.md, schema JSON)

### Post-Launch Metrics (após 4 semanas):
- [ ] >80% novos projetos usam v2.0
- [ ] <15 min tempo médio preenchimento (iniciantes)
- [ ] <5% taxa de erro em campos P0
- [ ] NPS >70
