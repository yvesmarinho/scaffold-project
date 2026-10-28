---
mode: agent
description: Ritual de encerramento de sessão. Execute ao finalizar o trabalho do dia.
---

<!-- Modificado em: 28/10/2026 16:45 — registro de sessão migrado para o vault Obsidian via MCP obsidian-rest -->

# 🏁 Session End — Ritual de Encerramento de Sessão

> Use este ritual ao final da sessão. O registro da sessão é gravado no vault
> Obsidian `claude_memory` **via MCP `obsidian-rest`** — nunca em `docs/` do projeto.

## Execução

1. Rode o encerramento determinístico (segurança + git):

```bash
python scripts/session-manager.py --json end
```

2. Interprete o retorno:
   - `workspace_security.clean`
   - `git` (branch, alterações pendentes, últimos commits)
   - `vault.session_note` e `vault.project_note` (destino do registro)

3. Se `workspace_security.clean == false`, pare e reporte antes de qualquer commit.

4. **Sanitize antes de gravar**: nenhum token, senha, chave, IP interno, hostname interno
   ou endpoint com credenciais no texto. Use placeholders (`<TOKEN>`, `<PRIVATE_IP>`).

5. Grave o registro da sessão **via MCP `obsidian-rest`**:
   - `obsidian_append_content` em `vault.session_note` (cria a nota se não existir).
     Na criação, inclua frontmatter YAML (`tags: [session, <projeto>]`, `created`, `updated`).
   - Conteúdo, em blocos `---` por atividade: título, horário (`DD/MM/AAAA HH:MM`,
     America/Sao_Paulo), status, objetivo, contexto, passos, resultado, decisões,
     arquivos modificados e commits.
   - Fatos **duráveis** (decisões arquiteturais, pendências) vão em `vault.project_note`
     com `obsidian_patch_content` (edição pontual), atualizando `updated` no frontmatter.
     Se o patch falhar (erro 40084 — versão do mcp-obsidian), use `obsidian_append_content`
     com uma seção datada no fim da nota.
   - Nunca sobrescreva uma nota inteira (`obsidian_put_content`) sem confirmar com o usuário.

6. Se o usuário quiser publicar alterações de código do repositório:

```bash
python scripts/session-manager.py --json end --commit --push
```

## Referências

- Scan isolado: `python scripts/session-manager.py --json security-scan`
- Status rápido: `python scripts/session-manager.py --json status`
