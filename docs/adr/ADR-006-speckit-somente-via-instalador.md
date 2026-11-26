<!-- Criado em: 26/11/2026 11:58 -->
<!-- Modificado em: 26/11/2026 11:58 -->

# ADR-006: Arquivos do SpecKit nos projetos gerados vêm só do instalador oficial

- **Status**: Aceito
- **Data**: 2026-11-26
- **Decisores**: Yves Marinho (dono do projeto)
- **Contexto relacionado**: [ADR-003](ADR-003-separacao-templates-distribuicao.md), fatia 5

## Contexto

A criação de projeto já rodava `specify init --here --force --integration <IA>` (`run_speckit_init`). Mesmo assim, o plugin do Claude copiava em seguida uma versão estática do SpecKit que vinha do `.claude/` do repositório. Depois da fatia 5 do ADR-003, essa cópia ficou em `scaffold/templates/`.

Medido em 26/11/2026 com o specify 1.4.6:
- A cópia estática acrescentava aos projetos com Claude:
  - 14 comandos antigos `.claude/commands/speckit.*..md`;
  - 2 skills que o `specify` atual não instala (`speckit-agent-context-update`, `speckit-taskstoissues`).
- Com `ai_assistant=none`, o `specify` não rodava. A `constitution.md` vinha da cópia estática do template.
- O `upgrade` não rodava o `specify`. Projetos antigos nunca recebiam um SpecKit novo.
- Como o `specify init` já cria `.specify/memory/constitution.md` sem preencher, `generate_constitution` sempre a pulava. A constitution ficava com `[PROJECT_NAME]` (ver `docs/bugs/BUG-constitution-nunca-preenchida.md`).

Com cópias estáticas, atualizar o SpecKit não chega aos projetos gerados, e não há nenhum aviso.

## Decisão

1. **O instalador é a única fonte** dos arquivos do SpecKit no projeto gerado. Não há cópia estática `speckit*` em `scaffold/templates/`.
2. **Integração por IA**: `claude` → `claude`; `copilot` → `copilot`; `both` → `claude` e `copilot`. `none` → `generic`, com `--integration-options=--commands-dir .specify/commands/`, para não criar pastas novas na raiz.
3. **O upgrade roda o instalador.** O `--force` do specify repõe templates, scripts, comandos e skills, e preserva `.specify/memory/` e `specs/` (verificado em teste e2e).
4. **`generate_constitution`** lê o `constitution-template.md` instalado no projeto e preenche a constitution enquanto ela for idêntica ao template. Constitution editada nunca é tocada. Sem template instalado, o resultado é erro explícito, sem fallback estático.
5. **`--check-templates` e `--diff-template <nome>`**: o scaffold não tem mais um upstream de templates SpecKit. Os dois informam que a sincronização é feita pelo `--upgrade` e saem com código 2. O `--diff-template <caminho/relativo>` continua funcionando.
6. O que é do próprio scaffold continua em `scaffold/templates/claude/commands/` (rituais `session-*`).

## Consequências

### Positivas
- Atualizar o `specify` chega aos projetos novos na criação e aos antigos pelo upgrade.
- Some a mistura de comandos antigos com skills novas nos projetos com Claude.
- A constitution sai preenchida com nome, data e versão.
- Projetos sem IA também recebem o SpecKit completo.

### Negativas
- A geração depende do `specify` instalado em todos os casos, inclusive `none`. Sem ele, o projeto sai sem SpecKit e com erro registrado no resumo, como já acontecia nas outras IAs.
- O upgrade sobrescreve customizações feitas em `.specify/templates/` e `.specify/scripts/` do projeto.
- `--check-templates` deixa de detectar drift. O fluxo IMP-65 para templates SpecKit fica sem uso.

## Alternativas consideradas
1. **Manter as cópias estáticas e sincronizá-las por teste ou Makefile**
   - prós: geração sem depender do `specify`.
   - contras: duas fontes para o mesmo conteúdo, com sincronização manual.
2. **Symlink de `scaffold/templates/` para o `.claude/` do repo**
   - prós: um arquivo só.
   - contras: as mudanças do repo voltam a vazar para os projetos gerados, que é o problema do ADR-003.
