---
mode: agent
description: Ritual de primeira sessão em um projeto novo ou recém-clonado. Use apenas na primeira vez.
---

<!-- Modificado em: 28/10/2026 16:45 — registro de sessão migrado para o vault Obsidian via MCP obsidian-rest -->

# 🌱 Session Start (First Time) — Ritual de Primeira Sessão

> Use este ritual apenas na primeira sessão de um projeto novo ou recém-clonado.

## Execução

1. Se a estrutura do projeto ainda não existe, inicialize com o scaffold:

```bash
uv run scripts/scaffold.py new
```

2. Depois rode o ritual enxuto:

```bash
python scripts/session-manager.py --json start-first
```

3. Interprete o retorno:
   - `mcp` valida `.vscode/mcp.json` (`memory`, `sequential-thinking`, `obsidian-rest`)
   - `security` faz o scan inicial
   - `context.pending_todos` mostra os primeiros itens do `docs/TODO.md`
   - `vault` traz os caminhos da nota do projeto e da nota da sessão no vault

4. Prepare o vault **via MCP `obsidian-rest`**:
   - `obsidian_get_file_contents` em `vault.project_note`; se não existir, crie-a com
     `obsidian_append_content` (frontmatter YAML `tags`, `aliases`, `created`, `updated`
     + resumo do projeto) e adicione o link `[[<projeto>]]` em `00-index.md`.

5. Se o usuário estiver num projeto já scaffoldado, pule o passo 1.

6. Só peça input humano para:
   - domínio/modo da sessão
   - objetivo da primeira sessão
   - definir `OBSIDIAN_API_KEY`/`OBSIDIAN_HOST` no ambiente, se `mcp.ok == false`

## Referências

- Verificação de links do scaffold: `uv run scripts/scaffold.py check`
- Status rápido após scaffold: `python scripts/session-manager.py --json status`
