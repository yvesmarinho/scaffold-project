<!--
Criado em: 26/06/2026 00:00
Modificado em: 26/06/2026 00:00
-->

# 🔄 Session Recovery — 2026-06-26

**Sessão anterior**: 2026-06-24
**Branch**: master (up to date com origin/master)
**Status dos IMPs**: Ativo / Desenvolvimento

## Contexto Recuperado

### Última sessão (2026-06-24)

A sessão focou em 3 entregas principais:

1. **BUG-FIX: AttributeError `Namespace` em compose.py** — `flow_new_project` passava `argparse.Namespace` incompleto para `flow_compose_profiles`. Fix: adicionados todos os atributos obrigatórios (`name`, `title`, `description`, `domain`, `language`, `repo`, `shared_dir`, `target_dir`, `ai_assistant`).

2. **validate-test-runs.py** — Script criado em `scripts/bin/` para validar automaticamente as pastas geradas pelo scaffold (264 checks, 12/12 projetos PASS).

3. **Separação template/DEV** — `copy_speckit()` lia agents/prompts diretamente de `.github/` do scaffold project. Solução: criado `scaffold/templates/speckit/` via `git mv` com agents, prompts e specify-templates separados do código de desenvolvimento.

### Estado do git

- Branch: `master` (up to date com origin/master)
- **~50+ arquivos modificados não commitados** (`.specify/`, `.claude/skills/`, `scaffold/profiles/`, `scripts/lib/`, templates)
- Arquivos não monitorados: `.claude/skills/speckit-converge/`, `.github/agents/`, `.github/prompts/`, `CLAUDE.md`, etc.
- Último commit: `298d10c` — docs(session): atividades de 2026-06-24

### Pendências identificadas

De `docs/TODO.md` → **Próxima Sessão (2026-06-24+)**:

1. **Rodar suite de testes completa** — verificar se git mv + refactor de `project.py` não quebrou testes existentes (`uv run pytest`)
2. **Commit das mudanças pendentes** — staged renames + unstaged modifications (`.specify/`, `.claude/skills/`, `scaffold/profiles/`, `scripts/lib/`)
3. **Validar `specify init` no projeto novo** — confirmar que `run_speckit_init()` funciona para todos os valores de `ai_assistant` (claude, copilot, both, none)

## Itens P0 para Esta Sessão

- [ ] Rodar `uv run pytest` — confirmar que refactor não quebrou testes (1666 passed era baseline)
- [ ] Fazer commit das mudanças pendentes (~50 arquivos)
- [ ] Validar `specify init` end-to-end com cada valor de `ai_assistant`
