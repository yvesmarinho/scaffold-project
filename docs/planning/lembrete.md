# Projeto Scaffold Project
# Relação das alterações/correções necessárias.

<!--
Criado em: 01/01/2026 00:00
Modificado em: 28/08/2026 11:07
-->

---

## Duvidas

---

## BUG/Correção

- o log não exibe os detalhes exibidos no final do stdout. tmabém não exibe os drifts.
- alterar nomenclatura do arquivo log para usar a data da maquina, já com timezone. está com UTC.
- gitignore ignorar os arquivos gerados pelo copilot, claude e speckit. exceção para os arquivos que contem dados do projeto.

---

### TaskList — Bugs e Melhorias Gerais

#### Scaffold

- [ ] **Como usar o scaffold para projetos legados (anteriores ao scaffold)?**
  - Existe `scaffold.py --objetivo-migrate` para migrar `objetivo.yaml` v1→v2
  - Não há fluxo de "adoção" de projeto legado (equivalente ao `scaffold new` mas retroativo)
  - Decidir: criar comando `scaffold adopt` ou documentar processo manual

---

## Alterações Futuras

- estrutura do respositório deve ser main, dev e fases. Na automação git, validar se o código está correto para ir para o main.

- shell integration:
  [Code shell integration](https://code.visualstudio.com/docs/terminal/shell-integration)
  ```
  [[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code --locate-shell-integration-path zsh)"
  ```

- Questionar prioridade do projeto em objetivo-init.yaml

- todos os arquivos de template devem estar separados dos arquivos usados no
  projeto, para facilitar distribuição.

- corrigir o objetivo-init-V2.yaml
    - para adiconar a sessão "infrastructure" e "architeture".
    - adiconar padrão de nomenclatura de pastas e arquivos.
    - adicionar padrão de nomenclatura de objetos, classes e funções

- na pasta `./docs` falta as sub-pastas `implemantations`e `bugs`.

- é possivel integrar a atualizações do spec-kit no projeto comando "specify init --here --force --integration copilot"?

- Analisar as informações dos sites abaixo para fazer as devidas atualizações.
  - [Github Copilot Instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
  - [Agent Skills in VS Vode](https://code.visualstudio.com/docs/copilot/customization/agent-skills) para melhorar a atuação dos agentes.
  - [Custom Agents ](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
  - [manage MCP servers in VS Code](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) habilitar Github MCP para acesso aos repositórios.
  - [Github Copilot in Visual Studio](https://github.blog/changelog/2026-04-30-github-copilot-in-visual-studio-april-update/)

---
