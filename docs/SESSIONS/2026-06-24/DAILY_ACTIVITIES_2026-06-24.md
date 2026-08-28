<!--
Criado em: 24/06/2026 00:00
Modificado em: 24/06/2026 17:00
-->

# 📋 Daily Activities — 2026-06-24

**Branch**: master
**Objetivo da sessão**: Separar template files de DEV files no scaffold, corrigir erros de `--with-code-profile`, criar script de validação e melhorar o script de rotação de testes.

---

### ✅ BUG-FIX — AttributeError `Namespace` sem atributo `name` em compose.py

**16:00 — CONCLUÍDO**

**Objetivo**: Corrigir `AttributeError: 'Namespace' object has no attribute 'name'` ao usar `--with-code-profile` no scaffold.

**Contexto**: O `flow_new_project` chamava `flow_compose_profiles` passando um `argparse.Namespace` incompleto — sem `name`, `title`, `description`, `domain`, `language`, `repo`, `shared_dir`, `target_dir` e `ai_assistant`.

**Passos executados**:
1. Identificado que `compose.py:30` acessa `args.name` mas o namespace criado em `new_project.py` não incluía esses campos
2. Adicionados todos os atributos obrigatórios ao `argparse.Namespace(...)` usando valores de `cfg`
3. Adicionado `ai_assistant` ao dict `overrides` em `compose.py` para preservar valor correto no `.scaffold-state.yaml`

**Resultado**: `--with-code-profile python-fastapi` passa sem erro.

**Decisões técnicas**: `target_dir=str(cfg.project_path)` (não `.parent`) — usando o diretório do projeto como destino dos templates, não o diretório pai.

**Arquivos modificados**:
- `scripts/lib/flows/new_project.py` (+12/-2)
- `scripts/lib/flows/compose.py` (+2/-0)

**Status**: ✅ Completo

---

### ✅ FEAT — Script de validação de projetos gerados (validate-test-runs.py)

**16:15 — CONCLUÍDO**

**Objetivo**: Criar script para avaliar automaticamente se todas as pastas geradas pelo scaffold estão corretas.

**Contexto**: Após execução do rotation script com 12 combinações, havia necessidade de validar a estrutura de cada projeto de forma sistemática, sem inspecionar manualmente.

**Passos executados**:
1. Criado `scripts/bin/validate-test-runs.py` com:
   - `discover_projects()` — encontra subpastas com `.scaffold-state.yaml`
   - `_check_base_structure()` — 18 itens sempre obrigatórios
   - `_check_ai_assets()` — CLAUDE.md/.claude para claude/both; .copilot-rules.md para copilot/both
   - `_check_profile_files()` — lê descriptors YAML e verifica `required=true` files
   - Filtros: skip paths terminando em `/`, skip sources inline, skip `.copilot-shared/`
2. Adicionados flags `--verbose` / `--only-failed`
3. Saída: tabela por projeto + resumo final com contagens

**Resultado**: 264 checks, 12/12 projetos PASS após todas as correções.

**Arquivos criados**:
- `scripts/bin/validate-test-runs.py` (265 linhas)

**Status**: ✅ Completo

---

### ✅ REFACTOR — Separação template files ↔ DEV files (scaffold/templates/speckit/)

**16:30 — CONCLUÍDO**

**Objetivo**: `copy_speckit()` estava lendo agents e prompts de `.github/` do projeto padrão — os próprios arquivos de desenvolvimento. O template tinha de ser separado do código.

**Contexto**: Ao criar `test-000-prog-py-claude`, os agents e prompts copiados vinham de `.github/agents/` e `.github/prompts/` do scaffold project — mesclando DEV files com template. Decisão do usuário: "O template tem de ser separado. O código deve ser modular."

**Passos executados**:
1. Criado `scaffold/templates/speckit/` via `git mv`:
   - `.github/agents/` → `scaffold/templates/speckit/agents/`
   - `.github/prompts/` → `scaffold/templates/speckit/prompts/`
   - `.specify/templates/` → `scaffold/templates/speckit/specify-templates/`
2. Restaurado `.github/` do scaffold project executando `specify init --here --force --integration claude` e `specify init --here --force --integration copilot`
3. Adicionado `_SPECKIT_TEMPLATES` constant em `project.py` apontando para `scaffold/templates/speckit/`
4. Adicionado `_AI_TO_SPECIFY` mapping: `claude→["claude"]`, `copilot→["copilot"]`, `both→["claude","copilot"]`, `none→[]`
5. Adicionado `run_speckit_init(config)` que chama `specify init` via subprocess no projeto novo
6. Refatorado `copy_speckit()` para usar `_SPECKIT_TEMPLATES`, pular `speckit.*` agents (instalados pelo `specify init`), copiar apenas agents customizados e prompts de sessão/git/domínio
7. Atualizado `_copy_domain_profile()` para usar `_SPECKIT_TEMPLATES / "prompts" / "domain"`
8. Atualizado `source:` nos 6 profile descriptors de domínio: `.github/prompts/domain/` → `scaffold/templates/speckit/prompts/domain/`

**Resultado**: Projetos gerados usam arquivos do template separado; `.github/` do scaffold project contém apenas os arquivos oficiais via `specify init`.

**Decisões técnicas**:
- `specify init` (claude): instala `CLAUDE.md`, `.claude/skills/speckit-*/SKILL.md`, `.specify/` — NÃO instala `.github/agents/`
- `specify init` (copilot): instala `.github/agents/speckit.*.agent.md`, `.github/prompts/speckit.*.prompt.md`, `.github/copilot-instructions.md`, `.specify/`

**Arquivos modificados/criados**:
- `scripts/lib/project.py` (+60/-20) — `run_speckit_init`, `_SPECKIT_TEMPLATES`, `_AI_TO_SPECIFY`, refactor `copy_speckit` + `_copy_domain_profile`
- `scaffold/templates/speckit/` — novo diretório (via git mv de ~100+ arquivos)
- `scaffold/profiles/devops-analysis.yaml`, `devops-infrastructure.yaml`, `devops-programming.yaml`, `devops-security.yaml`, `python-fastapi.yaml`, `python-flask.yaml` — source path atualizado

**Status**: ✅ Completo

---

### ✅ FEAT — test-scaffold-rotation.sh: `--reset` apaga logs e projetos

**16:50 — CONCLUÍDO**

**Objetivo**: `--reset` deve apagar projetos de teste, `tmp/stdout.txt` E logs `logs/scaffold*.log`.

**Contexto**: Os logs de scaffold acumulavam entre testes, dificultando análise. `--reset` só apagava projetos e stdout.

**Passos executados**:
1. Adicionado bloco ao `--reset` em `test-scaffold-rotation.sh`:
   ```bash
   logs_dir="${PROJECT_ROOT}/logs"
   if ls "${logs_dir}"/scaffold*.log 2>/dev/null | grep -q .; then
       rm -f "${logs_dir}"/scaffold*.log
       echo "  ✅ Logs de scaffold removidos de ${logs_dir}/."
   fi
   ```
2. Corrigido: `local logs_dir=...` → `logs_dir=...` (keyword `local` é inválido fora de funções bash)

**Resultado**: `--reset` limpa projetos, stdout e logs de scaffold.

**Arquivos modificados**:
- `scripts/bin/test-scaffold-rotation.sh` (+8/-0)

**Status**: ✅ Completo

---
