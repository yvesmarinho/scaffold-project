<!-- Criado em: 17/11/2026 16:14 -->
<!-- Modificado em: 17/11/2026 16:14 -->

# BUG — `created_at` dos projetos gerados em UTC

## Sintoma

O campo `created_at` do `ProjectConfig`, preenchido por `ui._iso_now()`, saía em
UTC (`2026-11-17T19:11:51Z`). Esse valor aparece nos arquivos gerados ("Criado em",
"Gerado por scaffold.py em ...", `{{CREATED_AT}}`) com 3 horas de diferença do
horário local, o que viola a regra de timezone America/Sao_Paulo.

## Causa raiz

`_iso_now()` usava `datetime.now(tz=timezone.utc).strftime("...Z")`. O log de operação
já tinha sido migrado para America/Sao_Paulo (`_local()`, PR #40), mas essa
função ficou para trás.

## Correção

- `scripts/lib/ui.py`: `_iso_now(now=None)` reaproveita `_local()` e devolve ISO 8601
  com offset (`2026-11-17T16:11:51-03:00`). O parâmetro opcional `now` permite testar
  de forma determinística, e `datetime` sem timezone levanta `ValueError`.
- `tests/test_ui_iso_now.py`: conversão UTC→SP, virada de dia, rejeição de `datetime`
  sem timezone e default sem `Z` com offset `-03:00`.

## Impacto

Nenhum código faz parsing do `created_at` (só interpolação em texto), então a
mudança de formato não quebra contrato. Projetos já gerados mantêm o valor antigo.

## Fora do escopo (pendente no TODO)

`scripts/session-time-tracker.py::_iso_now` e `scripts/lib/publish.py` (`created_at`
do manifesto) continuam em UTC. O formato `Z` do manifesto é exigido por
`tests/test_smoke_imp30.py`.
