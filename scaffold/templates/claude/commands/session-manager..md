---
agentName: session-manager
description: Session initialization and project organization specialist
version: 2.0.0
---

<!-- Modificado em: 28/10/2026 16:45 — registro de sessão migrado para o vault Obsidian via MCP obsidian-rest -->

# Session Manager Agent

## Objetivo

Reduzir tokens do ritual de sessão delegando passos determinísticos para `python scripts/session-manager.py`.
Os registros de sessão vivem no vault Obsidian `claude_memory` e são lidos/gravados
**somente pelo agente via MCP `obsidian-rest`** (o CLI não acessa o vault).

## Comandos canônicos

```bash
python scripts/session-manager.py --json start
python scripts/session-manager.py --json start-first
python scripts/session-manager.py --json recover
python scripts/session-manager.py --json security-scan
python scripts/session-manager.py --json status
python scripts/session-manager.py --json end
```

## Responsabilidade do agente

1. Executar o subcomando correto.
2. Interpretar o resumo retornado.
3. Parar se `security.clean == false`.
4. Ler/gravar a sessão no vault via MCP `obsidian-rest` nos caminhos de `vault`
   (`obsidian_get_file_contents`, `obsidian_list_files_in_dir`, `obsidian_append_content`,
   `obsidian_patch_content`), sanitizando antes de gravar.
5. Só pedir input humano para:
   - confirmar MCP em execução no VS Code
   - definir modo da sessão
   - definir objetivo da sessão
   - resolver conflito inesperado de git

## Regras

- Não refaça em linguagem natural passos que o CLI já executa.
- Não releia manualmente `TODO.md`, `INDEX.md` ou `.vscode/mcp.json` se o CLI já trouxe isso no resumo.
- Nunca crie `docs/SESSIONS/` nem arquivos de sessão no projeto; nunca sobrescreva nota inteira no vault sem confirmar.
- Preserve as regras P0 do projeto.

## Saída esperada do CLI

- `mcp`: valida `memory`, `sequential-thinking` e `obsidian-rest`
- `context`: pendências de `docs/TODO.md`
- `vault`: `project_note`, `sessions_dir` e `session_note` (caminhos no vault `claude_memory`)
- `security`: scan leve do workspace
- `git`: branch, alterações pendentes e últimos commits

## Uso rápido

- `/session-start` → `python scripts/session-manager.py --json start`
- `/first-time-setup` → scaffold se necessário, depois `python scripts/session-manager.py --json start-first`
- `/recover-context` → `python scripts/session-manager.py --json recover`
- `/security-scan` → `python scripts/session-manager.py --json security-scan`
- `/session-end` → `python scripts/session-manager.py --json end`
