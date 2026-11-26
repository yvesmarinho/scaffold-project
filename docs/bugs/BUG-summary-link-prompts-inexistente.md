<!-- Criado em: 26/11/2026 14:40 -->
<!-- Modificado em: 26/11/2026 16:39 -->

# BUG: `PROJECT_CREATION_SUMMARY.md` linkava `.github/prompts/`, que não é mais gerada

- **Data**: 26/11/2026
- **Arquivo**: `scaffold/templates/base/docs/PROJECT_CREATION_SUMMARY.md.tmpl`
- **Status**: ✅ corrigido

## Sintoma
O `docs/PROJECT_CREATION_SUMMARY.md` dos projetos gerados apontava para `.github/prompts/`, pasta que não existe mais. O link ficava quebrado. O arquivo também anunciava "9 prompts" na árvore e nas características, e trazia uma seção "Prompts de Sessão".

## Causa
O ADR-005 (25/11/2026) trocou os prompt files por skills em `.github/skills/`. O template do resumo, extraído na fatia 3 do ADR-003, não foi revisto nessa mudança. Também ficou desatualizado o texto "11 agentes + 9 prompts" do SpecKit, que desde o ADR-006 vem do `specify init`.

## Correção
- Na árvore e no link, `prompts/` virou `skills/`.
- "Prompts de Sessão" virou "Rituais de Sessão", com a coluna "Comando".
- "SpecKit configurado (via `specify init`)".
- Teste: `tests/test_summary_sem_prompts.py`.

## Fora do escopo
A tabela de agents `@speckit.*` desse resumo também está desatualizada (ADR-005). Ficou para uma correção própria.

## Impacto
Vale só para projetos novos. O upgrade não regenera o resumo, que é `skipped` quando o arquivo já existe.
