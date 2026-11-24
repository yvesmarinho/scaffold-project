<!-- Criado em: 24/11/2026 12:25 -->
<!-- Modificado em: 24/11/2026 12:00 -->

# BUG: o tarball do `--publish` não rodava (gerador incompleto)

**Data**: 24/11/2026 · **Severidade**: Alta (o pacote distribuído não executa) · **Status**: ✅ Corrigido (branch `fix/publish-tarball-incompleto`) · **ADR**: fatia 1 do [ADR-003](../adr/ADR-003-separacao-templates-distribuicao.md)

## Sintoma

O `scaffold.py` extraído do tarball de release falhava no import:

```
File ".../scripts/scaffold.py", line 40, in <module>
    from lib.flows import (
ModuleNotFoundError: No module named 'lib.flows'
```

O problema foi achado no inventário de templates (`docs/analysis/INVENTARIO-templates.md`) e confirmado: o tarball tinha 0 arquivos de `scripts/lib/flows/`.

## Causa raiz

`scripts/lib/publish.py` monta o pacote a partir de `_INCLUDE_PATTERNS`, uma lista fixa de globs.

1. O padrão `scripts/lib/*.py` não é recursivo. Por isso `scripts/lib/flows/` e `scripts/lib/ai/` ficavam de fora.
2. Faltavam fontes que o gerador copia do próprio repositório para o projeto gerado:
   - os scripts de sessão, memória e utilitários em `scripts/`, além de `scripts/git-hooks/` e `scripts/bin/`;
   - `.claude/commands` e `.claude/skills`;
   - `.github/copilot-instructions.md`;
   - `.specify/templates/`;
   - `docs/guides/BRANCH_PROTECTION_SETUP.md`.
3. Caches locais (`.ruff_cache` dentro de `scaffold/templates/project/*`) entravam no pacote.

O teste IMP-30 só verificava se alguns arquivos estavam presentes. Nunca executava o pacote.

## Correção

- Os padrões passam a incluir o gerador inteiro: `scripts/*.py`, `scripts/*.sh`, `scripts/lib/**/*.py`, `scripts/bin/*` e `scripts/git-hooks/*`. `scripts/tmp/` continua fora.
- Também entram as fontes que o código lê do repositório.
- `.ruff_cache`, `.mypy_cache`, `.pytest_cache` e `htmlcov` passam a ser excluídos.
- O pacote foi de 407 para 489 arquivos (≈ 864 KB).

A seleção continua sendo feita por glob. A troca por `git ls-files` e a separação entre templates e arquivos do repositório ficam para as próximas fatias do ADR-003.

## Testes

`tests/test_publish_tarball_executavel.py`. O tarball é publicado e extraído, e então:
- `test_tarball_extraido_lista_perfis`: `scaffold.py --list-profiles --json` retorna rc 0;
- `test_tarball_gera_o_mesmo_projeto_que_o_repositorio`: `new --ci`, rodado a partir do tarball e a partir do repositório com os mesmos argumentos, termina com rc 0 nos dois casos e gera **exatamente os mesmos arquivos** (mais de 100);
- `test_tarball_sem_caches_locais`.

Na fase vermelha, os 3 testes falharam sem a correção. A suíte completa ficou em 1735 passed.

## Lições

- O teste de um artefato de distribuição precisa **executar** o artefato. Checar a presença de alguns arquivos não basta.
- Comparar o resultado gerado pelo pacote com o resultado gerado pelo repositório pega automaticamente qualquer fonte nova que esteja faltando.
- O `conftest` isola o `HOME`. Subprocessos que fazem commit precisam de identidade git explícita (`GIT_AUTHOR_*` e `GIT_COMMITTER_*`).
