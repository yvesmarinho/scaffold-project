<!--
Criado em: 23/06/2026 00:00
Modificado em: 23/06/2026 00:00
-->

# 🔄 Session Recovery — 2026-06-23

**Sessão anterior**: 2026-06-22
**Branch**: master
**Status do Projeto**: v1.7.1 — Production Stable

---

## Contexto Recuperado

### Última Sessão (2026-06-22)

**IMP-Claude: Integração Claude Code no Framework Scaffold** — ✅ COMPLETO (~60min)

- Template `_CLAUDE_MD` com placeholders criado em `project.py`
- Template `_CLAUDE_SETTINGS_JSON` limpo (sem paths hardcoded)
- Diretórios `.claude/`, `.claude/commands/`, `.claude/skills/` adicionados ao scaffold
- Função `copy_claude_config()` implementada (padrão de `copy_copilot_instructions()`)
- Flows `new_project.py` (passo 5aa) e `upgrade.py` atualizados
- 75/75 testes passando sem regressões
- **Commit**: f650251 (push pendente ao fim da sessão)

---

## ⚠️ Estado Git — Investigar

O git status mostra alterações inesperadas que precisam ser avaliadas:

**Arquivos deletados (não staged)**:
- `CLAUDE.md`
- `WORKFLOWS_REMOVED_TEMPORARILY.md`
- `docs/BUG-22_RESOLUCAO.md`
- `docs/IMP-65_P0_TESTING_SUMMARY.md`
- `objetivo-init-minimal.yaml`
- `objetivo-init.yaml`

**Arquivos não rastreados (novos)**:
- `.continue/`
- `.memory/memories/project/`
- `.memory/memories/team/2026-06-22__search-test-team-onboarding.md`
- `.memory/memories/team/2026-06-22__test-team-memory.md`
- `docs/bugs/BUG-22_RESOLUCAO.md`
- `docs/implementations/IMP-65_P0_TESTING_SUMMARY.md`

**Hipótese**: Arquivos foram movidos (docs/ → docs/bugs/ e docs/implementations/) sem git tracking. Investigar antes de qualquer commit.

---

## Itens P1 para Esta Sessão

1. **Investigar git status**: Entender as deleções/novos arquivos não rastreados
2. **BUG-08**: Configurar knowledge-harvester MCP (30min)
3. **Linting Cleanup**: Resolver warnings (black, flake8, mypy) (1h)
4. **IMP-63**: Template Migration System (3h)
5. **Testes para IMP-Claude**: Adicionar testes unitários para `copy_claude_config()`

---

## Regras Ativas

- `.copilot-rules.md`: 371 linhas, 8 seções
- P0: Nunca heredoc/echo para criar arquivos
- P0: Nunca cat/grep/find/ls via terminal
- P0: Operações de arquivo via Python stdlib
- P0: Git com arquivo de mensagem (≥6 linhas)
- P1: Docs de sessão em `docs/SESSIONS/YYYY-MM-DD/`

---

*Session Recovery | 2026-06-23 | Enterprise Scaffold Project Template*
