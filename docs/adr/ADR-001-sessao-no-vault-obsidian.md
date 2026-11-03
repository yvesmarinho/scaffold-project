<!-- Criado em: 28/10/2026 16:49 -->
<!-- Modificado em: 28/10/2026 16:49 -->

# ADR-001 — Registros de sessão no vault Obsidian via MCP `obsidian-rest`

**Status**: Aceito
**Data**: 28/10/2026

## Contexto

Os rituais de sessão geravam `docs/SESSIONS/YYYY-MM-DD/` (`SESSION_RECOVERY`,
`DAILY_ACTIVITIES`, `SESSION_REPORT`, `FINAL_STATUS`) dentro de cada projeto. Com
isso, o histórico ficava espalhado por vários repositórios, o git ficava poluído
(234 arquivos e 3,2 MB só neste repo), dados sensíveis acabavam versionados e era
preciso manter um ecossistema próprio (índice FTS, chat capture, validador, migrador).
O usuário centraliza a memória entre sessões no vault Obsidian `claude_memory`.

## Decisão

1. Os registros de sessão passam a ficar **no vault**: `projects/<projeto>.md` (resumo
   durável) e `projects/<projeto>/sessions/YYYY-MM-DD.md` (log do dia, append-only).
2. A leitura e a gravação são feitas **pelo agente via MCP `obsidian-rest`**. O CLI em
   Python não fala MCP, então `session-manager.py` faz só os passos determinísticos
   (MCP, segurança, git, TODO) e devolve os caminhos no campo `vault`.
3. `obsidian-rest` passa a ser servidor MCP obrigatório (`REQUIRED_MCP_SERVERS`) e entra
   no `.vscode/mcp.json` gerado em todos os domínios, com credenciais apenas via
   `${env:OBSIDIAN_API_KEY}` e `${env:OBSIDIAN_HOST}`.
4. O histórico de `docs/SESSIONS/` foi migrado para o vault com redação de segredos e
   IPs. Scripts e libs que só existiam para esse modelo foram movidos para `tmp/`.

## Alternativas consideradas

- **O CLI gravar direto na Local REST API (`requests` + `.secrets/`)**: rejeitada,
  porque duplicaria a integração e não usaria o MCP.
- **Manter `docs/SESSIONS/` em paralelo**: rejeitada, porque ficariam duas fontes da verdade.

## Consequências

- (+) Uma única memória entre projetos e repositórios sem logs de sessão.
- (+) Cerca de 4,5 mil linhas de código legado fora do caminho de execução.
- (−) Uma sessão depende do Obsidian aberto com o plugin *Local REST API* e das variáveis
  de ambiente. Se o MCP estiver fora, o agente reporta e **não** grava no projeto.
- (−) A busca FTS em sessões (`session-search`) deixa de existir; use a busca do Obsidian
  (`obsidian_simple_search`).
- (−) `obsidian_patch_content` falha na versão atual do mcp-obsidian (erro 40084); por
  enquanto use `obsidian_append_content` como fallback.
