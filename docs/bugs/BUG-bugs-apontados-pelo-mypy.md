<!-- Criado em: 25/11/2026 15:28 -->
<!-- Modificado em: 25/11/2026 15:28 -->

# BUG: dois defeitos reais revelados pelo mypy (PR #69)

- **Data**: 25/11/2026
- **Status**: ✅ corrigidos; mypy passou a ser gate (pre-commit e CI)

## 1. `IssueTemplateMerger` quebrava com template sem frontmatter
- **Sintoma**: o merge de `.github/ISSUE_TEMPLATE/*.md` retornava `status="error"` com mensagens como
  "argument of type 'NoneType' is not iterable" ou "'list' object has no attribute 'items'".
- **Quando acontecia**: o arquivo existente tinha frontmatter, e o template não tinha (ou o frontmatter do template era
  YAML inválido, lista ou escalar). Também acontecia quando o frontmatter do arquivo existente não era um mapeamento.
- **Causa**: `_merge_markdown` chamava `_deep_merge(template_fm, existing_fm)` com `template_fm=None`, e
  `_parse_frontmatter` aceitava qualquer valor YAML como frontmatter.
- **Correção**: `_parse_frontmatter` só aceita `dict`; o merge usa `template_fm or {}`, mantendo o frontmatter
  do usuário (user wins).

## 2. Painel de info do `manage.py` não atualizava após gerar arquivo
- **Sintoma**: ao gerar o arquivo exigido por um item, o painel continuava com o estado antigo.
- **Causa**: em `_save_generated_file`, `self._refresh_info(...)` é `async` e era chamado sem `await`. A
  coroutine era criada e descartada.
- **Correção**: `await self._refresh_info(...)`.

## Testes
`tests/test_bugs_apontados_mypy.py`:
- cinco cenários de frontmatter ausente ou inválido, mais um de regressão do merge normal;
- detector AST de chamadas `self.<async>()` sem `await` em `manage.py`, que ignora métodos com `@work` do
  Textual, porque esses devolvem um Worker. O teste roda sem o `textual` instalado.

## Gate
Hook local `mypy` no `.pre-commit-config.yaml` (`uv run mypy`, projeto inteiro) e passo "Type check (mypy)"
no job "Lint & Validate" do `ci-template.yml`.
