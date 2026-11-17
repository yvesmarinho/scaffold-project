<!-- Criado em: 17/11/2026 17:33 -->
<!-- Modificado em: 17/11/2026 17:33 -->

# BUG — `session-time-tracker` e release-manifest gravando em UTC

Decisão de contrato registrada em `docs/adr/ADR-002-timestamps-america-sao-paulo.md`.

## Sintoma

- `session-time-tracker.py`: `start_time`/`end_time`/pausas em UTC (`...Z`). O `session_date`
  e a detecção de **sessão órfã** (`start`, `status`, `cleanup`) usavam `datetime.utcnow()`.
  Uma sessão iniciada às 22:00 em São Paulo ficava registrada no dia seguinte, e às 21:00 o
  tracker podia considerar "órfã" uma sessão do mesmo dia local.
- `lib/publish.publish_template`: `created_at` do manifesto em UTC e slug `YYYYMMDD` dos
  arquivos de release (`enterprise-template-v*-YYYYMMDD.tar.gz`) pela data UTC.

## Causa raiz

`datetime.utcnow()` (tracker, 5 pontos) e `datetime.now(timezone.utc)` + `strftime("...Z")`
(publish), sem conversão para `America/Sao_Paulo`.

## Correção

- Tracker: `_now_local(now=None)`, `_iso_now(now=None)` (ISO com offset), `_today(now=None)`
  (data local) e `_hhmmss(iso)` (exibição da hora, aceita `Z` legado e offset). Os 4 usos de
  `utcnow().strftime("%Y-%m-%d")` agora chamam `_today()`.
- Publish: parâmetro `now`; `created_at` e `date_slug` a partir do horário de São Paulo.
- `datetime` sem timezone levanta `ValueError` nos dois.
- `tests/test_smoke_imp30.py`: o teste do CLI passa a exigir offset em vez de `Z` (novo contrato).

## Compatibilidade

Uma sessão iniciada antes da atualização (`start_time` com `Z`) e encerrada depois (`-03:00`)
calcula a duração corretamente, porque os dois formatos são parseados como datetimes aware.
Há um teste de integração para esse caso.

## Verificação

- `tests/test_timestamps_sao_paulo.py`: 11 testes (virada de dia 01:30 UTC → 22:30 do dia anterior,
  naive rejeitado, default sem `Z`, exibição, compatibilidade, nomes dos arquivos de release).
- Suíte completa: 1718 passed.
