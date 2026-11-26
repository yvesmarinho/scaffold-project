<!-- Criado em: 26/11/2026 11:58 -->
<!-- Modificado em: 26/11/2026 11:58 -->

# BUG: constitution.md dos projetos gerados nunca era preenchida

- **Data**: 26/11/2026
- **Contexto**: achado ao trocar a fonte do SpecKit para o instalador oficial (ADR-006).
- **Arquivo**: `scripts/lib/project.py` (`generate_constitution`).
- **Status**: ✅ corrigido

## Sintoma
Nos projetos gerados com `claude`, `copilot` ou `both`, `.specify/memory/constitution.md` começava com
`# [PROJECT_NAME] Constitution`. Ficavam sem preencher nome, datas e versão, e não havia o cabeçalho de
metadados do scaffold. O log mostrava `skipped (já existe)` na etapa "Gerando constitution.md".

## Causa
O `specify init` (etapa 5) já cria `.specify/memory/constitution.md` como cópia crua do template.
`generate_constitution` (etapa 6) saltava qualquer constitution existente. Assim, o preenchimento só
acontecia com `ai_assistant=none`, que era o único caso em que o `specify` não rodava.

## Correção
- `generate_constitution` lê o template **instalado no projeto** e preenche a constitution enquanto ela for
  idêntica ao template (status `updated`).
- Uma constitution editada pelo usuário continua intocada (`skipped`).
- Sem template instalado, o resultado é `error`, com mensagem citando o `specify`.
- Testes em `tests/test_speckit_via_instalador.py`: igual ao template → preenchida; ausente → criada;
  editada → intocada; sem template → erro.

## Observação
O cabeçalho usa `SPECKIT_SYNC_DATE` (`2026-03-05`), que é a data de sincronização antiga e não a data de
geração. Esse comportamento já existia e não foi alterado.
