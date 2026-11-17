<!-- Criado em: 17/11/2026 17:05 -->
<!-- Modificado em: 17/11/2026 17:05 -->

# BUG — Suíte de testes grava em `.memory/` e `.session-time/` do repo (e apaga a sessão real)

## Sintoma

- `.memory/memories/**` acumulava memórias fictícias (`test-basic-save`, `search-test-*`...)
  e o índice `.memory/index/memory.db` era reescrito a cada execução.
- `.session-time/history.csv` acumulava sessões de 1 a 4 segundos (`café`, `almoço`...).
- **Mais grave:** o `setup_teardown` de `tests/test_session_time_tracker.py` apagava
  `.session-time/current.json`. Rodar a suíte durante uma sessão real de tracking
  descartava a sessão em andamento.

## Causa raiz

- `scripts/lib/memory.py`: `MEMORY_DIR`/`INDEX_DIR`/`DB_PATH` fixos em `<projeto>/.memory`,
  calculados na importação e usados no `Memory.file_path`, no `MemoryStore` e no `rebuild_index`.
- `scripts/session-time-tracker.py`: `STATE_FILE`/`HISTORY_CSV` fixos em `<projeto>/.session-time`.
- A fixture `isolated_memory` do conftest definia a variável `MEMORY_DIR`, que **nenhum código lia**,
  e nenhum teste a usava. O isolamento nunca existiu de fato.

## Correção

- `memory.py`: `_memory_root()`, `_memory_dir()` e `_db_path()`, resolvidos na chamada a partir de
  **`SCAFFOLD_MEMORY_ROOT`** (raiz com `memories/` e `index/`). `MemoryStore()` sem argumento usa
  `_db_path()`, e `_ensure_structure` cria `db_path.parent` (não mais o `INDEX_DIR` real quando
  o `db_path` é explícito).
- `session-time-tracker.py`: `STATE_DIR` a partir de **`SCAFFOLD_SESSION_TIME_DIR`**.
- Sem as variáveis, o comportamento não muda.
- `tests/conftest.py`: as duas variáveis em `tmp_path` (autouse function + fallback de sessão);
  `isolated_memory` corrigida para `SCAFFOLD_MEMORY_ROOT`.
- `tests/test_session_time_tracker.py`: lê e limpa o estado no diretório isolado.

## Verificação

- `tests/test_isolamento_memory_session_time.py`: 11 testes.
- Suíte completa: 1707 passed; **0 escritas** em `.memory/`, `.session-time/` e `logs/`, medido
  com `find -newer <marcador>`.

## Efeito colateral da fase vermelha (corrigido)

Antes da implementação, os testes novos escreveram uma memória `Isolada` e um `current.json`
reais. Os dois arquivos foram removidos (o `current.json` era desta execução, `start_time` 17:01)
e o índice foi reconstruído a partir dos `.md` (27 memórias, entrada órfã removida).

## Pendência

As entradas fictícias acumuladas antes desta correção continuam em `.memory/memories/` e em
`.session-time/history.csv`. Precisam de revisão antes de apagar (registrado no TODO).
