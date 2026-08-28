# 📅 Daily Activities — 2026-07-15

**Data**: 2026-07-15

---

## Conclusão das pendências do TODO — suite verde + objetivo-init + specify init

**Horário**: 15/07/2026 09:15–10:05 · **Status**: ✅ Concluído
**Modo**: PROGRAMMING · **Branch**: `fix/pendencias-todo-sessao`

### Objetivo

Concluir as pendências listadas em `docs/TODO.md` (exceto `scaffold adopt`, que aguarda decisão do usuário).

### Contexto

Ritual de início apontou 5 pendências e o scan de segurança acusou 37 falsos positivos estruturais (templates de exemplo, `tmp/test-runs/`, cache mypy) — aceitos como falsos positivos. A suite tinha 18 falhas acumuladas após os refactors recentes (paths de templates, hooks reescritos em pt-BR no commit `280f58f`).

### Passos e Resultado

1. **Suite de testes (18 falhas → 0)** — `1684 passed, 28 skipped`:
   - `test_github_best_practices_p2`: contagem 13→16 arquivos (3 issue templates `.md` novos);
   - `test_integration_structural` (airflow): `==` → `>=` (versões mínimas seguras da revisão de 26/06);
   - Hooks pre-commit: testes alinhados às mensagens pt-BR; padrão `credentials` **restaurado** nos dois hooks (regressão real da reescrita); dicas `make memory-cleanup` e `conftest.py` restauradas;
   - `test_session_time_tracker` (10 testes): causa era o nome da branch fora da convenção — branch renomeada para `fix/pendencias-todo-sessao`;
   - Smoke tests: paths canônicos `scaffold/profiles/` e `scaffold/templates/project/`; `last_tested` de 9 perfis atualizado para 2026-07-15 (revalidados pela suite);
   - Snapshots copilot regenerados (`--json start` — nova ordem do CLI).
2. **TODO 1 — objetivo-init no fluxo oficial**: seções "Persistência" (grava `objetivo-init.yaml` na raiz do projeto alvo) e "Integração com o Fluxo Oficial do Scaffold" (agent ⇄ wizard intercambiáveis) adicionadas ao agent (`.github/agents/` + `scaffold/templates/speckit/agents/`); README atualizado.
3. **TODO 2 — consolidação objetivo-init-minimal**: descoberto que os YAML da raiz eram artefatos dos testes POC escrevendo em `Path.cwd()`; testes corrigidos para `tmp_path` e artefatos removidos do repositório.
4. **TODO 5 — specify init**: novo `tests/test_run_speckit_init.py` (7 testes, subprocess mockado: claude/copilot/both/none + returncode≠0, FileNotFoundError, timeout) + validação real do CLI `specify 0.12.12` para claude e copilot ✅.

### Decisões

- Padrão `credentials` recolocado em `SENSITIVE_NAME_PATTERNS`/`SENSITIVE_PATTERNS` dos hooks (perdido na otimização de tokens).
- Destino dos artefatos legados da raiz: **remoção** (o canônico é `docs/templates/objetivo-init-minimal.yaml`; exemplos em `scaffold/templates/objetivo/examples/`).
- Persistência do YAML do agent: raiz do projeto alvo, mesmo destino do wizard CLI.
- Erros de ruff (1295) e diagnósticos mypy são pré-existentes ao repositório — fora do escopo; arquivos novos/alterados verificados sem novos erros.

### Arquivos modificados

Ver diff do commit desta sessão (testes, hooks, agent objetivo-init, README, TODO.md, perfis YAML, snapshots).

---

## Feature: comando `scaffold adopt` para projetos legados (Opção A)

**Horário**: 15/07/2026 10:10–14:40 · **Status**: ✅ Concluído
**Branch**: `feature/067-scaffold-adopt` (stacked sobre `fix/pendencias-todo-sessao`)

### Objetivo

Implementar a Opção A da pendência "scaffold adopt": comando automático que adota projetos existentes (sem `.scaffold-state.yaml`) no scaffold.

### Contexto

Usuário escolheu a Opção A (comando automático) em vez da Opção B (guia manual). O `upgrade` já tinha o pipeline idempotente completo; faltava só o bootstrap do state para projetos legados.

### Passos e Resultado

1. `scripts/lib/flows/adopt.py`: `detect_language()` (pyproject/package.json/go.mod → python/typescript/go, precedência python>ts), `detect_domain()` (marcadores IaC → infrastructure), `_kebab()` para o slug, validações (alvo inexistente, state já existente → usar upgrade), confirmação interativa fora de `--ci`/`--json`, escrita do state e **delegação ao `flow_upgrade`** (reuso total do pipeline idempotente).
2. CLI: subcomando `adopt` + flag `--adopt` registrados em `scaffold.py`.
3. `tests/test_flow_adopt.py`: 16 testes (detecção, kebab, validações, delegação mockada, integração real preservando arquivos do legado). Suite completa: **1700 passed**.
4. Validação manual end-to-end em projeto simulado: 118 arquivos criados, `pyproject.toml` preservado, re-adopt bloqueado.

### Decisões

- Adopt = bootstrap de state + delegação ao upgrade (zero duplicação de pipeline).
- `touch` prévio do state garante modo in-place quando o nome do diretório não é kebab-case (bug pego pelos testes: `project_path` resolveria para subdiretório).
- Detecção conservadora: default `programming`/`other`; overrides via `--name/--domain/--language/--ai`.

---

## BUG-26: `adopt --dry-run` executava de verdade + alias `--logdir`

**Horário**: 15/07/2026 15:30–16:30 · **Status**: ✅ Concluído
**Branch**: `feature/067-scaffold-adopt` (PR #27)

### Objetivo

Corrigir dois problemas relatados pelo usuário ao testar o adopt em projeto real.

### Contexto

Usuário executou `scaffold adopt --dry-run --logdir /var/log/scaffold` em `~/VyaJobs/enterprise-observability`: (1) `--logdir` era rejeitado (flag registrada era `--log-dir`); (2) o `--dry-run` foi ignorado e a adoção executou de verdade, criando `.scaffold-state.yaml` e aplicando o template.

### Passos e Resultado

1. **Alias `--logdir`** (`2158a3e`): aceito junto com `--log-dir`, mesmo dest.
2. **BUG-26** (`c570c50`): `flow_adopt` agora trata `dry_run` internamente — exibe plano de detecção e retorna sem escrever nada (o dispatch avalia `--adopt` antes de `--dry-run`, então a flag era silenciosamente ignorada). 2 testes novos garantem que o diretório fica intocado; suite **1702 passed**.
3. Relatório: `docs/bugs/BUG-26-adopt-dry-run-executa-de-verdade.md` (`acbd771`), com passos de recuperação via git para o projeto afetado.

### Decisões

- Dry-run do adopt mostra plano de alto nível (state + template idempotente); preview arquivo-a-arquivo fica como melhoria futura.
- Limpeza do `enterprise-observability` deixada ao usuário (git restore/clean revisado) por ser destrutiva.

