<!--
Criado em: 09/11/2026 16:15
Modificado em: 09/11/2026 16:15
-->

# BUG — log de operação em UTC e sem a seção de drift

**Status**: ✅ Corrigido em 09/11/2026 (branch `fix/scaffold-log-details-timezone`)
**Origem**: `docs/planning/lembrete.md` (seção BUG/Correção)

## Sintomas

1. O nome do arquivo (`logs/scaffold_<timestamp>.log`) e o cabeçalho `# Timestamp:` usavam
   hora UTC (ex.: `18-52-50` para uma execução às 15:52 em São Paulo).
2. O log não registrava a seção "DRIFT DETECTADO" nem os caminhos relativos exibidos no
   final do stdout. Só aparecia a contagem `drift: N` e as linhas em `Detailed Items`,
   com caminho absoluto.

## Causa

`scripts/lib/ui.py::save_operation_log` gerava o timestamp com
`datetime.now(timezone.utc)`, e `_write_log_to_dir` só gravava estatísticas e itens.

## Correção

- `log_timestamp(now)`: converte para `America/Sao_Paulo`; recusa datetime sem timezone.
- Nome do arquivo em hora local; cabeçalho em ISO 8601 com offset
  (`2026-11-09T15:52:50-03:00`).
- Novas seções `## Drift (N)` e `## Errors (N)`, com caminho relativo e mensagem.
- `save_operation_log(..., now=...)` para testes determinísticos.

## Testes

`tests/test_operation_log.py` (9 testes): timezone, datetime sem timezone, nome do arquivo,
cabeçalho, seções de drift e de erros, lista vazia e diretório sem permissão (não derruba).

## Fora do escopo

`ui._iso_now()` ainda grava `...Z` (UTC) em outro ponto. Avaliar separadamente.
