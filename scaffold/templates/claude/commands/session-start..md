---
mode: agent
description: Ritual de início de sessão recorrente. Execute no começo de cada sessão de trabalho.
---

<!-- Modificado em: 28/10/2026 16:45 — registro de sessão migrado para o vault Obsidian via MCP obsidian-rest -->

# 🚀 Session Start — Ritual de Início de Sessão

> Use este ritual no início de cada sessão recorrente.
> Os registros de sessão **não ficam no repositório**: vivem no vault Obsidian
> `claude_memory` e são lidos/gravados **somente** via MCP `obsidian-rest`.

## Execução

1. Rode os passos determinísticos (MCP, segurança, git, TODO):

```bash
python scripts/session-manager.py --json start
```

2. Interprete o retorno:
   - `mcp.ok == true` → `memory`, `sequential-thinking` e `obsidian-rest` configurados
   - `security.clean == true` → sem arquivos sensíveis fora de `.secrets/`
   - `context.pending_todos` → prioridades imediatas de `docs/TODO.md`
   - `vault.project_note` / `vault.sessions_dir` / `vault.session_note` → caminhos no vault

3. Se `security.clean == false`, pare e reporte.

4. Recupere o contexto da última sessão **via MCP `obsidian-rest`**:
   - `obsidian_get_file_contents` em `vault.project_note` (decisões e pendências duráveis)
   - `obsidian_list_files_in_dir` em `vault.sessions_dir` → leia a nota mais recente
     anterior a hoje com `obsidian_get_file_contents`
   - Se a pasta não existir, é a primeira sessão registrada no vault — siga em frente.

5. Se o MCP `obsidian-rest` não responder, **não** crie arquivos de sessão no projeto:
   reporte ao usuário e confira `OBSIDIAN_API_KEY`/`OBSIDIAN_HOST` no ambiente e o plugin
   *Local REST API* ativo no Obsidian.

6. Depois do resumo, peça ao usuário apenas:
   - modo da sessão: `PROGRAMMING | INFRASTRUCTURE | ANALYSIS`
   - objetivo da sessão em 1 frase

## Referências

- Status rápido: `python scripts/session-manager.py --json status`
- Recuperação isolada: `python scripts/session-manager.py --json recover`
- Encerramento: `/session-end`
