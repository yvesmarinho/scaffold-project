<!-- Criado em: 24/11/2026 10:45 -->
<!-- Modificado em: 24/11/2026 10:43 -->

# BUG — CI sem rodar desde junho e tracker quebrando em ambiente de CI

**Data**: 24/11/2026 · **Severidade**: Média (sem rede de segurança no merge) · **Status**: ✅ Corrigido (branch `fix/ci-main`)

## Sintoma

- Nenhum workflow de teste rodou na `main` desde o rename `master → main` (09/11); os últimos runs de `Scaffold Tests` (até 07/06, na `master`) falharam.
- Ao simular o checkout de PR do GitHub Actions (detached HEAD), 5 testes do `session-time-tracker` falhavam com `EOFError`.

## Causa raiz

1. **GitHub Actions desabilitado no repositório** (`actions/permissions → enabled: false`), desligado em 31/03/2026 de propósito (banner do README). Só os runs de Dependabot apareciam.
2. **`scaffold-tests.yml` quebrado**: `pip install -r requirements.txt` (arquivo inexistente) e matrix Python 3.10/3.11, enquanto `requires-python = ">=3.12"`.
3. **`ci-template.yml` inadequado para check obrigatório**: filtro de `paths` (um required check que não dispara deixa o PR travado em "Expected"); `pip` em vez de `uv`; smoke `--new --dry-run` sem `--ci` caía no prompt interativo (`EOFError`).
4. **`uv.lock` no `.gitignore`**: impedia build reprodutível (`uv sync --locked`).
5. **Tracker**:
   - `_get_current_branch()` devolvia `"HEAD"` em detached HEAD, tratado como branch fora do padrão;
   - sem TTY, o `input()` de confirmação estourava `EOFError` com traceback;
   - os testes rodavam o tracker com `cwd` na raiz do repo, então o resultado dependia da **branch real** (falhava também em branch fora da convenção, como `fix-ci-main`).

## Correção

- `ci-template.yml` reescrito: uv + Python 3.12, `uv sync --locked`, sem filtro de paths, jobs `Tests`, `CLI Smoke Tests` (`--ci`, publish em `$RUNNER_TEMP`) e `Lint & Validate` (inclui `ruff check .` no repo inteiro — decisão do usuário; falha até a limpeza dos achados pré-existentes).
- `scaffold-tests.yml` removido (coberto pela suíte completa).
- `uv.lock` passa a ser versionado.
- Tracker: detached HEAD → `None` (sem validação de branch); `EOFError` no prompt → recusa limpa ("Sessão não iniciada").
- Testes do tracker executam com `cwd` fora de repositório git (diretório temporário isolado).
- Actions reabilitado via `gh api` (autorizado pelo usuário).

## Testes

`tests/test_tracker_branch_ci.py`:
- `test_detached_head_nao_e_branch` / `test_branch_normal_continua_detectada`
- `test_start_em_detached_head_inicia_sessao`
- `test_branch_fora_do_padrao_sem_tty_recusa_sem_traceback`
- `test_suite_do_tracker_independe_da_branch_real` (roda as suítes do tracker numa cópia do repo em branch `Nome_Ruim`)

Fase vermelha: 5 falhas confirmadas antes da correção.

## Lições

- Required check precisa disparar em todo PR (sem filtro de paths).
- Testes que chamam scripts dependentes de git não podem herdar o estado git do repositório real.
- Todo prompt interativo deve tratar `EOFError` (CI, pipes).
