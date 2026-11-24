<!-- Criado em: 24/11/2026 14:34 -->
<!-- Modificado em: 24/11/2026 14:34 -->

# BUG: a suíte de testes sobrescrevia a identidade git global da máquina

**Data**: 24/11/2026 · **Severidade**: Alta (altera configuração do usuário fora do projeto; autoria errada em commits de todos os repositórios) · **Status**: ✅ Corrigido (branch `fix/testes-alteram-gitconfig-global`) · **Introduzido em**: `39a3e66` (20/05/2026)

## Sintoma

- `git config --global user.name` retornava `Test User` e `user.email` retornava `test@example.com` no `~/.gitconfig` real.
- O problema afetava **todos os repositórios** da máquina.
- No scaffold-project, 76 commits desde 20/05/2026 saíram com o autor `Test User <test@example.com>`, inclusive os da sessão de 24/11. Esses commits não ficam associados à conta no GitHub.

O problema foi encontrado durante a limpeza do lint: o F821 apontou `monkeypatch` indefinido dentro da fixture.

## Causa raiz

Em `tests/conftest.py`, a fixture `configure_git_for_tests` (`scope="session"`, `autouse=True`) executava:

```
git config --global user.email test@example.com
git config --global user.name  "Test User"
```

A fixture `isolate_tests`, que isola o `HOME` num diretório temporário, é **por teste**. A de sessão roda **antes** dela, ainda com o `HOME` real, e por isso gravava no `~/.gitconfig` do usuário a cada execução da suíte.

Por erro de merge, a mesma fixture ainda carregava o corpo de `mock_subprocess`, com `monkeypatch` indefinido (F821). Com isso, a fixture `mock_subprocess` não fazia nada e retornava `None`.

## Correção

- `configure_git_for_tests` cria um `.gitconfig` temporário da sessão com a identidade de teste e aponta `GIT_CONFIG_GLOBAL` para ele. Os subprocessos herdam essa variável, e o valor anterior é restaurado no fim da sessão. O `~/.gitconfig` real não é mais lido nem escrito pelos testes.
- O corpo de `_factory` voltou para `mock_subprocess`.
- A identidade global da máquina foi restaurada para `Yves Marinho <yvesmarinho@gmail.com>`, com aprovação do usuário. O backup do arquivo anterior foi guardado no scratchpad da sessão.
- O histórico foi tratado com um `.mailmap`, que mapeia as variantes de `Test User` para a identidade canônica. O histórico **não** foi reescrito, então não houve force-push na `main`. A atribuição no GitHub continua a mesma.

## Testes

`tests/test_conftest_nao_altera_gitconfig.py`:
- `test_suite_nao_altera_gitconfig_global`: roda uma suíte num subprocesso, com um `HOME` falso cujo `.gitconfig` tem uma identidade conhecida, e exige que o arquivo saia intacto. Na fase vermelha, o teste reproduziu o bug: a identidade "Pessoa Real" virou "Test User".
- `test_identidade_de_teste_disponivel_na_sessao`: confirma que os commits dos testes têm identidade, via `GIT_CONFIG_GLOBAL`.
- `test_mock_subprocess_funciona`.

Na suíte completa, 1750 testes passaram, e o `mtime` do `~/.gitconfig` real ficou igual antes e depois da execução.

## Lições

- Fixture de sessão com `autouse` roda antes do isolamento por teste. Ela não pode tocar em nada global.
- Para git em testes, usar `GIT_CONFIG_GLOBAL` (ou `GIT_AUTHOR_*` e `GIT_COMMITTER_*`) e **nunca** `git config --global`.
- Os outros repositórios da máquina também receberam commits com autor `Test User` entre 20/05 e 24/11/2026. Vale revisá-los, com `.mailmap` onde fizer sentido.
