<!-- Criado em: 24/11/2026 11:50 -->
<!-- Modificado em: 24/11/2026 11:18 -->

# Análise: customização do VS Code Copilot vs. o que o scaffold gera

**Data da pesquisa:** 24/11/2026
**Item do backlog:** `docs/planning/lembrete.md` ("Analisar as informações dos sites...")
**Escopo:** só análise e recomendações. Nenhum template foi alterado.
**Método:**
- leitura das páginas oficiais (lista na seção "Fontes");
- geração de um projeto de exemplo com `scaffold.py new --ci --domain programming --language python --ai-assistant copilot` e inspeção dos arquivos gerados.

## Resumo executivo

1. A documentação do VS Code foi reorganizada em torno de **harnesses**: Copilot, Claude, Codex e **Local**. O harness Local está descontinuado, com remoção prevista para **fevereiro de 2027**. Prompt files, `handoffs` e os nomes antigos de ferramentas funcionam **apenas no Local**.
2. O scaffold ainda gera várias peças que dependem do Local:
   - `.github/prompts/*.prompt.md`;
   - agents com `handoffs` e nomes de ferramentas antigos;
   - um `copilot-instructions.md` que cita `create_file`, `read_file` e outras ferramentas antigas.
3. As skills do SpecKit em `.github/skills/` estão de acordo com a especificação. Há, porém, **referências quebradas**:
   - os handoffs apontam para agents `speckit.*`, que não são gerados;
   - `chat.promptFilesRecommendations` recomenda prompts que não existem.
4. O MCP é gerado em `.vscode/mcp.json`, o formato do editor. A doc passou a preferir `.mcp.json` na raiz (formato `mcpServers`) para novas configurações do Copilot. O GitHub MCP remoto via OAuth está correto, mas não restringe toolsets nem permissões.
5. Prioridades:
   - **P0:** corrigir as referências quebradas e migrar prompts para skills.
   - **P1:** adotar `.github/instructions/*.instructions.md` e modernizar o frontmatter dos agents.
   - **P1/P2:** decidir entre `.mcp.json` e `.vscode/mcp.json` e definir o recorte de toolsets do GitHub MCP.

## 1. Custom instructions

**O que a doc recomenda**
- Fontes: [custom-instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions) e [reference](https://code.visualstudio.com/docs/agents/reference/custom-instructions-reference).
- Instruções gerais ficam em `.github/copilot-instructions.md` ou `AGENTS.md`.
- Instruções por padrão de arquivo ficam em `.github/instructions/**/*.instructions.md`, com frontmatter `applyTo` (globs) e `description`.
- O harness Claude usa `CLAUDE.md` e `.claude/rules/*.md` (com `paths`).
- Boas práticas: regras concisas, sem duplicar o que o linter já cobre, e validadas num chat novo.

**O que o scaffold gera**
- `.github/copilot-instructions.md`, gerado por `scripts/lib/templates.py` (`_COPILOT_INSTRUCTIONS_TEMPLATE`), com `applyTo: "**"` e regras P0 que citam ferramentas do Local.
- `.copilot-rules-<nome>.md` e um symlink `.copilot-rules.md` que aponta para `~/Documentos/DevOps/.copilot-shared/...`, fora do repositório.
- Não gera `.github/instructions/`, `AGENTS.md` nem `CLAUDE.md` no modo copilot.

**Gaps**
1. `applyTo` só tem efeito em arquivos `*.instructions.md`; no arquivo geral ele não faz nada.
2. Os nomes de ferramentas são do Local. No Copilot, os nomes atuais são `read`, `edit`, `search`, `execute` etc.
3. Não há regras por linguagem com `applyTo` por glob. O conteúdo de `.copilot-rules*` **não é carregado automaticamente** pelo Copilot.
4. O symlink fora do repositório quebra no clone, no CI e no cloud agent.
5. Não há `AGENTS.md`, que serviria ao Copilot e ao Codex com um único arquivo.
6. As regras citam `pip install`, o que conflita com a política de uso do `uv`.

## 2. Agent skills

**O que a doc recomenda**
- Fonte: [agent-skills](https://code.visualstudio.com/docs/copilot/customization/agent-skills).
- Local: `.github/skills/<nome>/SKILL.md`. Também são lidos `.claude/skills/` e `.agents/skills/`.
- Frontmatter:
  - `name`: obrigatório, no formato `[a-z0-9-]`, até 64 caracteres e igual ao nome do diretório. Se for inválido, a skill falha em silêncio.
  - `description`: obrigatório, até 1024 caracteres.
  - Opcionais: `argument-hint`, `user-invocable` e `disable-model-invocation`.
- A [página de prompt files](https://code.visualstudio.com/docs/agent-customization/prompt-files) recomenda **converter prompt files em skills** antes da remoção do Local.

**O que o scaffold gera**
- As skills `speckit-*`, criadas via `specify init`, estão conformes.
- Os rituais de sessão (`session-start`, `session-end`, `session-start-first`) existem só como prompts em `scaffold/templates/speckit/prompts/` e **não vão** para o projeto gerado.
- No modo copilot, `.claude/skills/` e `.claude/commands/` são criados vazios.

**Gaps**
1. Os workflows próprios do scaffold não viraram skills.
2. `speckit-taskstoissues` não está entre as skills geradas. É preciso confirmar se isso é intencional.
3. Os diretórios `.claude/` vazios no modo copilot são ruído.
4. Nenhuma skill usa `disable-model-invocation`. Seria o caso das skills com efeito colateral.

## 3. Custom agents

**O que a doc recomenda**
- Fonte: [custom-agent-file-reference](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference).
- Local: `.github/agents/*.agent.md`.
- Frontmatter:
  - `description` é obrigatório no Copilot.
  - Outros campos: `name`, `tools`, `model` (string ou lista ordenada), `model-policy`, `target` e `hooks`.
  - Campos só do Copilot: `skills`, `github` (com `toolsets` e `permissions` do GitHub MCP) e `mcp-servers`.
- Nomes de ferramentas (aliases): `execute`, `read`, `edit`, `search`, `agent`, `web`, `todo` e `<server>/*`.
- `handoffs` **só funciona no Local**.
- `user-invocable` e `disable-model-invocation` substituem `infer`.

**O que o scaffold gera**
- 22 agents copiados por `copy_custom_agents()` (`scripts/lib/project.py`).
- Campos fora do schema: `agentName`, `version` e `mode: agent`.
- Alguns agents não têm `name` ou `description`.
- Ferramentas com nomes antigos: `codebase`, `runCommands`, `githubRepo`, `edit/editFiles` e outros.
- Modelos fixados em versões antigas (`GPT-4.1`, `Claude Sonnet 4`).
- **Handoffs para `speckit.*`**, que não existem como agents no projeto gerado.
- Agents específicos do próprio scaffold ou de outro contexto (`template-architect`, `scaffold-verifier`, `test.engineer`) são copiados para todo projeto filho.

**Gaps:** handoffs quebrados, ferramentas antigas que podem ser ignoradas, campos obrigatórios ausentes, modelos desatualizados, recursos novos (`skills`, `github.toolsets`) sem uso e agents irrelevantes poluindo o dropdown.

## 4. MCP servers e GitHub MCP

**O que a doc recomenda**
- Fontes: [mcp-servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers), [mcp-configuration](https://code.visualstudio.com/docs/agents/reference/mcp-configuration) e [github-mcp-server](https://github.com/github/github-mcp-server).
- Há dois formatos:
  - o do editor (`servers`), em `.vscode/mcp.json`;
  - o portátil do Copilot (`mcpServers`), em `.mcp.json` na raiz ou em `~/.copilot/mcp-config.json`. A doc **prefere os destinos nativos** para novas configurações do Copilot.
- Configurações com `${input:...}` não são repassadas ao harness Copilot.
- Servidores stdio aceitam `sandbox` (Linux/macOS).
- GitHub MCP:
  - servidor remoto: `{"type":"http","url":"https://api.githubcopilot.com/mcp/"}`, com OAuth;
  - alternativa: PAT via `inputs` com `password: true`;
  - toolsets padrão: `context`, `repos`, `issues`, `pull_requests` e `users`;
  - restrição por agent: campo `github` no frontmatter.

**O que o scaffold gera**
- `.vscode/mcp.json` (`scripts/lib/vscode.py`) com `memory`, `sequential-thinking`, `obsidian-rest`, `filesystem` e `github`.
  - `github` usa o servidor HTTP remoto com OAuth, que está **correto**.
  - Os pacotes `npx` não têm versão fixada.
- Os mesmos servidores aparecem repetidos no `*.code-workspace`.
- Settings `chat.mcp.autostart`, `github.copilot.chat.enableMcp` e `chat.promptFilesRecommendations`, este último apontando para prompts inexistentes.
- Entrada Docker do GitHub MCP (fora do domínio programming): o token vai em `args`, não em `env`, e não há `inputs` com `password`.

**Gaps**
1. O destino não é o preferido pelo harness Copilot.
2. O GitHub MCP não tem recorte de toolsets nem modo somente leitura.
3. A entrada Docker diverge do README oficial.
4. Há duplicação entre `.vscode/mcp.json` e o workspace.
5. Settings desatualizados ou não confirmados.
6. Não há sandbox nem versões fixadas nos servidores stdio.

## Changelog de abril/2026 (Visual Studio, não VS Code)

- Fonte: [GitHub Copilot in Visual Studio — April update](https://github.blog/changelog/2026-04-30-github-copilot-in-visual-studio-april-update/).
- Agents de usuário em `%USERPROFILE%/.github/agents/`.
- Skills lidas também de `.claude/skills/` e `.agents/skills/`.
- Cloud agent e debugger agent.
- O changelog não trata de instructions, MCP nem prompts.
- **Impacto:** reforça manter as skills em `.github/skills/` e favorece configurações portáveis (`.mcp.json`).

## Recomendações priorizadas

| # | Prioridade | Recomendação | Esforço | Arquivos afetados |
|---|---|---|---|---|
| 1 | P0 | Remover ou ajustar os handoffs para `speckit.*` inexistentes | ≈1h | `scaffold/templates/speckit/agents/*.agent.md` |
| 2 | P0 | Remover `chat.promptFilesRecommendations` com prompts inexistentes; revisar `github.copilot.chat.enableMcp` e `chat.mcp.autostart` | ≈1h | `scripts/lib/vscode.py` |
| 3 | P0 | Migrar `session-start`, `session-end`, `session-start-first` e os perfis de domínio para `.github/skills/<nome>/SKILL.md` | ≈1 dia | `scaffold/templates/speckit/prompts/*`, `scripts/lib/project.py`, `scripts/lib/ai/plugins/copilot.py` |
| 4 | P1 | Reescrever as regras P0 de `copilot-instructions.md` sem nomes de ferramentas do Local; remover `applyTo`; trocar `pip` por `uv` | ≈2h | `scripts/lib/templates.py` |
| 5 | P1 | Gerar `.github/instructions/<linguagem>.instructions.md` com `applyTo` por glob | Médio | `scripts/lib/templates.py`, `copilot_rules_consolidate.py` |
| 6 | P1 | Normalizar o frontmatter dos agents (`name`/`description`, aliases atuais, sem `agentName`/`version`/`mode`) e criar um teste de lint do frontmatter | Médio | `scaffold/templates/speckit/agents/*` |
| 7 | P1 | Restringir o GitHub MCP com o campo `github: {toolsets, permissions}` nos agents | Baixo/Médio | `scripts/lib/vscode.py` e agents |
| 8 | P1 | Corrigir a entrada Docker do GitHub MCP: token em `env` e `inputs` com `password: true` | Baixo | `scripts/lib/vscode.py` |
| 9 | P1 | Parar de copiar agents específicos do scaffold para projetos filhos | Baixo | `copy_custom_agents` |
| 10 | P2 | Avaliar `.mcp.json` na raiz e eliminar a duplicação no `.code-workspace` | Médio | `generate_mcp`, `generate_workspace` |
| 11 | P2 | Gerar `AGENTS.md`; espelhar skills em `.agents/skills` e `.claude/skills` no modo `both` | Médio | `project.py`, `templates.py` |
| 12 | P2 | Fixar versões dos pacotes `npx` e usar `sandbox` nos servidores stdio | Baixo | `scripts/lib/vscode.py` |
| 13 | P2 | Trocar o symlink `.copilot-rules.md` por conteúdo versionado | Baixo/Médio | `scripts/lib/links.py` |
| 14 | P2 | Usar `disable-model-invocation`, `argument-hint` e `user-invocable` nas skills próprias | Baixo | novos `SKILL.md` |

## Decisões pendentes do usuário

1. **Harness:** manter suporte ao Local até fevereiro de 2027 (handoffs e prompts com aviso de descontinuação) ou mirar só no Copilot?
2. **`.vscode/mcp.json` ou `.mcp.json`:** a escolha afeta `.gitignore`, `normalize_github_mcp`, testes e o upgrade de projetos existentes.
3. **Escopo padrão do GitHub MCP:** somente leitura, ou escrita em issues e PRs?
4. **Agents herdados:** corrigir, reduzir o conjunto ou parar de copiá-los?
5. **Skills do SpecKit:** são geridas pelo `specify init`. Ajustá-las exige upstream ou uma camada de patch.

## Não confirmado nesta pesquisa (verificar no VS Code antes de implementar)

- O tipo de valor aceito por `chat.mcp.autostart` e o status de `github.copilot.chat.enableMcp`.
- Os headers `X-MCP-Toolsets` e `X-MCP-Readonly` do servidor remoto.
- Se nomes antigos de ferramentas são ignorados em silêncio ou geram erro.
- O motivo de `speckit-taskstoissues` ficar fora das skills geradas.
- A página `docs/agents/reference/custom-agents` retornou 404 e foi substituída pela `custom-agent-file-reference`.
- O README do github-mcp-server foi lido até cerca de 70% do conteúdo.
