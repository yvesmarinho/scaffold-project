<!-- Criado em: 17/11/2026 15:53 -->
<!-- Modificado em: 17/11/2026 15:54 -->

# BUG — Snapshots de templates desatualizados e árvore `docs/` malformada no perfil infra

## Sintoma

Três testes de `tests/test_templates_snapshot.py` falhavam com `Regressão detectada`:

- `test_copilot_rules_snapshot_programming_python`
- `test_copilot_instructions_snapshot_programming_python`
- `test_copilot_rules_snapshot_infrastructure_python`

## Causa raiz

1. **Baseline desatualizado (mudança intencional):** o commit `6d76e00`
   (feature/068, migração da sessão para o vault Obsidian) removeu
   `docs/SESSIONS/` dos templates gerados (`scripts/lib/templates.py`), mas os
   snapshots em `tests/snapshots/` não foram regenerados.
2. **Regressão real (perfil infrastructure):** na mesma remoção, o conector da
   árvore ficou trocado. `docs/` passou a ser gerado como:

   ```text
   ├── docs/
   │   ├── INDEX.md
   │   └── TODO.md
   │   ├── RUNBOOK.md         # Procedures operacionais
   ```

   ou seja, `└──` antes do último item. O correto é `├── TODO.md` / `└── RUNBOOK.md`.

## Correção

- `scripts/lib/templates.py`: conectores da árvore do perfil infra corrigidos.
- Snapshots regenerados com `pytest tests/test_templates_snapshot.py --update-snapshots`.
  Só os 3 arquivos acima mudaram, e o diff foi revisado: remoção de `SESSIONS/`,
  referência ao vault e árvore de infra corrigida.
- Verificado que nenhuma outra árvore em `templates.py` tem `└──` seguido de `├──`
  no mesmo nível.

## Prevenção

Ao alterar templates em `scripts/lib/templates.py`, rodar
`uv run pytest tests/test_templates_snapshot.py` e, se a mudança for
intencional, revisar o diff antes de regenerar com `--update-snapshots`.
