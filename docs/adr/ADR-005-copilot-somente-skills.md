<!-- Criado em: 25/11/2026 14:42 -->
<!-- Modificado em: 25/11/2026 14:42 -->

# ADR-005: Projetos gerados miram só o Copilot — skills no lugar de prompt files e handoffs

- **Status**: Aceito
- **Data**: 2026-11-25
- **Decisores**: Yves Marinho (dono do projeto)
- **Contexto relacionado**: [ANALISE-vscode-copilot-customization.md](../analysis/ANALISE-vscode-copilot-customization.md), recomendações P0 1–3

## Contexto

Os prompt files (`.prompt.md`) e o campo `handoffs` dos agents só funcionam no harness Local
do VS Code, e a própria documentação recomenda converter prompt files em skills. Na
prática, os projetos gerados tinham estes problemas:
- agents com `handoffs` para agents `speckit.*` que não existem no projeto, porque o `specify init` gera skills;
- `chat.promptFilesRecommendations` apontando para prompts inexistentes;
- `chat.mcp.autostart: true`, quando a configuração aceita apenas `never`, `onlyNew` ou `newAndOutdated`;
- `github.copilot.chat.enableMcp`, configuração que não existe mais;
- rituais de sessão que não chegavam ao Copilot.

## Decisão

1. O alvo é **só o Copilot**: nenhum prompt file nem `handoffs` é gerado.
2. Rituais de sessão (`session-start`, `session-end` e `session-start-first`) e perfis de domínio passam a ser
   skills em `scaffold/templates/skills/<nome>/SKILL.md`, com frontmatter `name` igual ao diretório e `description`.
   O destino no projeto é `.github/skills/<nome>/SKILL.md`.
   - Perfis vão para todas as IAs.
   - Rituais vão só para `copilot`/`both`, porque o Claude já os recebe em `.claude/commands/`.
3. Agents herdados: saem os templates `speckit.*` (código morto, já não eram copiados) e os
   `handoffs` para eles; os demais agents continuam sendo copiados.
4. Settings: `chat.mcp.autostart` passa a `newAndOutdated`; saem `github.copilot.chat.enableMcp` e
   `chat.promptFilesRecommendations`.

## Consequências

### Positivas
- Nenhuma referência quebrada; os rituais de sessão passam a existir no Copilot.
- Os templates de skill são validados por teste: nome, tamanho e ausência de `mode`.

### Negativas
- Quem usa o harness Local perde os prompts.
- Projetos já gerados mantêm `.github/prompts/` antigos; o upgrade cria as skills, mas não apaga os prompts.
- O symlink `.copilot-rules.md` para `.copilot-shared` externo ainda cita `.github/prompts`; isso fica para a recomendação P2 #13.

## Alternativas consideradas
1. **Manter o Local até fev/2027, com aviso de descontinuação**: mantém duas superfícies. Descartada pelo usuário.
