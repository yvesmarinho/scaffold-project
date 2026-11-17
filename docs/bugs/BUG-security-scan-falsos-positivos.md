<!-- Criado em: 17/11/2026 16:41 -->
<!-- Modificado em: 17/11/2026 16:41 -->

# BUG — `security-scan` da sessão com `clean: false` só por falsos positivos

## Sintoma

Depois da limpeza dos logs de teste, o `session-manager.py --json start` ainda reportava
`clean: false` com 25 achados, sem nenhum segredo real:

| Achados | Arquivos | Padrão que casou |
|---|---|---|
| 8 | `.mypy_cache/**/token*.json` | `*token*` |
| 2 | `scripts/secrets_scan.py`, `tests/test_secrets_scan.py` | `*secret*` |
| 1 | `scaffold/templates/.../secret-scan.yml` | `*secret*` |
| 1 | `tmp/commit-secrets-scan.txt` | `*secret*` |
| 13 | `.env.example` / `.env.airflow.example` em `scaffold/templates/` | `.env*` e valores de exemplo |

## Causa raiz

O scan é por **nome** de arquivo, e `EXCLUDED_DIR_NAMES` não cobria caches de ferramentas
(`.mypy_cache`, `.ruff_cache`) nem o `tmp/` local (convenção para mensagens de commit).
Os exemplos de `scaffold/templates/` já eram tratados como falso positivo aceito, mas
só por convenção, não no código.

## Correção (`scripts/lib/session_security.py`)

- `EXCLUDED_DIR_NAMES` += `.mypy_cache`, `.ruff_cache`, `tmp`.
- `SCAN_ALLOWLIST` por caminho relativo: `scripts/secrets_scan.py`,
  `tests/test_secrets_scan.py` e `scaffold/templates/*`. É aplicada tanto aos
  `sensitive-file` quanto aos `env-example-value`, porque os dois passam por `_should_skip_path`.

## Verificação

- `tests/test_session_security_allowlist.py`: 7 falsos positivos ignorados e 8 casos reais
  que **continuam** sendo acusados (`*.key`, `*password*`, `*token*`, `*.log`,
  `scripts/secrets.json`, `tests/fixtures/token.txt`, `src/templates/secret.yml`, `.env.example`
  da raiz com valor real).
- `session-manager.py --json start`: `clean: true`, `ready: true`.
- Suíte completa: 1697 passed.

## Trade-off

`tmp/` deixa de ser verificado. Um segredo salvo ali por engano não seria acusado por este
scan, mas continua coberto pelo `scripts/secrets_scan.py` (gitleaks) no modo `staged`/`history`
se for commitado. Isso vale também para os projetos gerados, que recebem este módulo.
