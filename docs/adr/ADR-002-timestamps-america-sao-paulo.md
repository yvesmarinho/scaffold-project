<!-- Criado em: 17/11/2026 17:33 -->
<!-- Modificado em: 17/11/2026 17:34 -->

# ADR-002 — Timestamps gravados em America/Sao_Paulo com offset (inclusive no release-manifest)

**Status**: Aceito
**Data**: 17/11/2026
**Decisores**: Yves Marinho (dono do projeto)

## Contexto

A regra global de localização exige `America/Sao_Paulo` em toda data/hora exibida, logada
ou gravada e, em armazenamento/APIs, ISO 8601 **com offset** (`2026-07-12T14:30:00-03:00`).
O scaffold ainda gravava UTC com sufixo `Z` em três lugares:

| Local | Efeito |
|---|---|
| `lib/ui._iso_now` (`created_at` dos projetos) | corrigido no PR #46 |
| `session-time-tracker.py` | `session_date` e detecção de sessão órfã pela data **UTC**: sessão iniciada após 21h caía no dia seguinte |
| `lib/publish.publish_template` (release-manifest) | `created_at` em UTC; data do nome dos arquivos (`YYYYMMDD`) também em UTC |

O manifesto é um artefato publicado, e `tests/test_smoke_imp30.py` exigia o `Z`, ou seja,
um contrato explícito. Por isso a mudança dependia de decisão do dono do projeto.

## Decisão

Todos os timestamps gravados pelo scaffold usam `America/Sao_Paulo` em ISO 8601 com offset
(`datetime.isoformat(timespec="seconds")`), **incluindo o `created_at` do release-manifest**.
Datas derivadas (`session_date`, slug `YYYYMMDD` dos arquivos de release) usam a data local.

Funções que geram timestamp aceitam `now: datetime | None` (timezone-aware) para testes
determinísticos. `datetime` sem timezone levanta `ValueError`.

## Consequências

### Positivas
- Coerência com a regra global e com o log de operação (PR #40) e o `created_at` (PR #46).
- Fim do erro de data após 21h no tracker e nos nomes dos arquivos de release.
- O offset explícito mantém o instante inequívoco, e `datetime.fromisoformat` lê os dois formatos.

### Negativas
- **Mudança de contrato do manifesto**: um consumidor externo que espere `Z` literal precisa
  aceitar offset. Nenhum consumidor interno faz parsing desse campo.
- O `history.csv` do tracker passa a misturar linhas antigas (`Z`) e novas (`-03:00`). A leitura
  e a exibição (`_hhmmss`) aceitam os dois formatos.

## Alternativas consideradas
1. Manter UTC (`Z`) no manifesto
   - prós: convenção comum em artefatos de release; sem mudança de contrato.
   - contras: exceção à regra global; data do nome do arquivo segue errada após 21h.
2. UTC no JSON e data local só no nome do arquivo
   - prós: corrige o nome sem mudar o campo.
   - contras: dois fusos no mesmo artefato.

## Plano de migração
- Não há migração de dados. Artefatos antigos continuam válidos, e leitores devem usar parsing ISO 8601.
