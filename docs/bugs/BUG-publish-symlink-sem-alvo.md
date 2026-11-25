<!-- Criado em: 25/11/2026 16:36 -->
<!-- Modificado em: 25/11/2026 16:36 -->

# BUG: publish descartava o alvo real de arquivos acessados por symlink

- **Data**: 25/11/2026
- **Contexto**: ADR-003 fatia 4. Os scripts de uso duplo foram para `scaffold/templates/runtime/scripts/`, e
  `scripts/<arquivo>` virou symlink relativo para eles.
- **Status**: ✅ corrigido

## Sintoma
`test_tarball_gera_o_mesmo_projeto_que_o_repositorio` falhou. O projeto gerado a partir do tarball avisava
"origem não encontrada: .../scaffold/templates/runtime/scripts/git-hooks/commit-msg" e saía com código 1.

## Causa
`publish._collect_files` eliminava duplicatas pelo caminho **resolvido** (`path.resolve()`). Como
`scripts/*.py` vem antes de `scaffold/templates/**/*` em `_INCLUDE_PATTERNS`, entrava o symlink
`scripts/x`, e o arquivo real `scaffold/templates/runtime/scripts/x` era descartado como duplicata. O
`tarfile` grava symlinks como symlinks, então o pacote ficava com links apontando para arquivos ausentes.

## Correção
- A eliminação de duplicatas passa a usar o caminho **relativo**: symlink e alvo são entradas distintas.
- `tests/test_runtime_templates.py::test_publish_inclui_symlink_e_alvo_real` reproduz o caso.
- O contrato de `test_smoke_imp30::test_no_duplicates` passou a usar o caminho relativo, e o teste novo
  `test_symlinks_tem_alvo_no_pacote` garante que nenhum symlink do pacote fica sem alvo.
