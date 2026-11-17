<!-- Criado em: 17/11/2026 16:32 -->
<!-- Modificado em: 17/11/2026 16:32 -->

# BUG — Suíte de testes grava no `logs/` real do scaffold-project

## Sintoma

Cada execução de `uv run pytest` criava cerca de 40 arquivos `logs/scaffold_*.log` e
acrescentava entradas fictícias ao histórico `logs/scaffolds.yaml`. Com o tempo, foram
mais de 650 arquivos, e o `security-scan` do `session-manager.py start` passou a
reportar `clean: false` por causa deles. O histórico real também ficou misturado
com projetos de teste.

## Causa raiz

Os caminhos de log eram fixos, e o isolamento dos testes não chegava neles:

| Ponto de escrita | Caminho | Por que escapava |
|---|---|---|
| `lib/ui.save_operation_log` | `<scaffold-project>/logs/` (`_SCAFFOLD_LOGS_DIR`) | caminho absoluto do repo; só `test_operation_log.py` fazia monkeypatch, e não chega a subprocessos |
| `scaffold_logger.ScaffoldLogger` | `logs/scaffolds.yaml` (relativo ao cwd) | testes rodam com cwd na raiz do repo |
| `flows/objetivo_init._log_objetivo_init` | `logs/scaffolds.yaml` (cópia própria) | idem |

Além disso, fixtures `scope="module"` (ex.: `test_docs_subfolders.py`) rodam antes
da fixture autouse de escopo function e escapariam de qualquer isolamento feito só nela.

## Correção

- Variável de ambiente **`SCAFFOLD_LOGS_DIR`**, lida no momento da chamada pelos três pontos
  de escrita. Sem ela, o comportamento não muda.
  - `ui._scaffold_logs_dir()` → `$SCAFFOLD_LOGS_DIR` ou `<scaffold-project>/logs`
  - `ScaffoldLogger()` sem argumento → `$SCAFFOLD_LOGS_DIR/scaffolds.yaml` ou `logs/scaffolds.yaml`
    (caminho explícito continua tendo prioridade)
  - `_log_objetivo_init` → mesma regra
- `tests/conftest.py`:
  - `isolate_scaffold_logs_session` (session, autouse): fallback para fixtures module/class/session
  - `isolate_tests` (function, autouse): `SCAFFOLD_LOGS_DIR=tmp_path/scaffold-logs`.
    Subprocessos (`scaffold.py` via `subprocess.run`) herdam a variável.
- `test_operation_log.py` passou a isolar via `setenv` (a variável tem prioridade sobre a constante).
- `test_bug001_objetivo_init.py::test_log_file_created_after_objetivo_init` remove a
  variável, porque testa justamente o caminho padrão relativo ao cwd.

## Verificação

- `tests/test_scaffold_logs_dir.py`: 11 testes (override, default, valor vazio,
  `save_operation_log`, isolamento do conftest, herança em subprocesso, `ScaffoldLogger`
  e `objetivo_init`).
- Suíte completa: 1681 passed; **0 arquivos novos ou alterados em `logs/`**, medido com
  `find logs -newer <marcador>`.

## Pendências

- Os logs antigos já gravados em `logs/` não foram apagados por esta correção.
- Testes ainda escrevem em `.memory/` e `.session-time/history.csv` do repo, ambos no
  `.gitignore` (registrado no TODO).
