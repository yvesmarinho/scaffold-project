<!-- Criado em: 15/07/2026 16:20 -->
<!-- Modificado em: 15/07/2026 16:20 -->

# BUG-26 — `scaffold adopt --dry-run` executava a adoção de verdade

**Data**: 15/07/2026 · **Severidade**: Alta (escreve em projeto alheio) · **Status**: ✅ Corrigido (`c570c50`, PR #27)

## Sintoma

`scaffold adopt --dry-run` executado em `~/VyaJobs/enterprise-observability` **criou** `.scaffold-state.yaml` e aplicou o template (Makefile, `.git-hooks/`, docs, etc.) em vez de apenas simular.

## Causa raiz

No dispatch de `scripts/scaffold.py`, `--adopt` é avaliado **antes** de `--dry-run`; o `flow_adopt` (recém-criado no PR #27) não lia `args.dry_run`, então a flag era silenciosamente ignorada e a adoção rodava de verdade.

## Correção

`flow_adopt` agora trata `dry_run` internamente ([scripts/lib/flows/adopt.py](../../scripts/lib/flows/adopt.py)): exibe o plano (nome/domínio/linguagem detectados e o que seria criado; JSON estruturado com `--json`) e retorna **sem escrever nada** — nem state, nem template.

## Testes

- `test_adopt_dry_run_writes_nothing`: dry-run não cria state, não delega ao upgrade, não toca o diretório.
- `test_adopt_dry_run_json_plan`: plano JSON com detecção correta.
- Suite completa: 1702 passed.

## Recuperação do projeto afetado

O adopt não sobrescreve arquivos existentes, então o dano é limitado a **arquivos novos** + `.scaffold-state.yaml`. Em repositório git:

```bash
git status               # revisar o que foi adicionado/alterado
git restore .            # desfaz alterações em arquivos rastreados
git clean -nd            # LISTA os arquivos novos (dry-run do clean)
git clean -fd            # remove os arquivos novos (após revisar a lista!)
```

## Lições

- Todo novo flow de escrita deve tratar `--dry-run` explicitamente (ou o dispatch deve rejeitar a combinação).
- Testes de flows destrutivos devem incluir o caso "dry-run não escreve nada".
