<!--
Criado em: 28/08/2026 11:20
Modificado em: 28/08/2026 11:20
-->

# Atividades — 28/08/2026

## Rename estrutural: default-project → scaffold-project

- **Horário/status**: 11:00–11:20 — concluído (PR aberto, aguardando merge)
- **Objetivo**: alinhar o repositório ao novo nome após o rename no GitHub
  (`yvesmarinho/default-project` → `yvesmarinho/scaffold-project`) e mover o
  clone para `~/Documentos/DevOps/Projetos/scaffold-project`.
- **Contexto**: o clone antigo vivia em `~/VyaJobs/a-default-project` com remote,
  pacote, workspace, `pyproject.toml` e ~165 arquivos referenciando o nome antigo;
  estado git com branches e worktree pendentes.
- **Passos**:
  1. Commit de `docs/planning/lembrete.md` e push de todas as branches
     (`feature/067-scaffold-adopt`, `worktree-agent-a11d9f5d8c2bbb800`) para não
     perder trabalho local antes do clone limpo.
  2. `git clone` do repo renomeado no novo local; branch
     `chore/rename-default-project-to-scaffold-project` a partir de
     `feature/067-scaffold-adopt`.
  3. `git mv` do pacote, do `.code-workspace` e do arquivo de estrutura.
  4. Substituição global ordenada (mais específico primeiro): caminhos absolutos,
     URLs de org, `a-default-project`, `default_project`, `DEFAULT_PROJECT`,
     `default-project`, `Default Project`, `default project`.
  5. Ajuste manual de `pyproject.toml` (`name`, `packages`).
  6. Quality gates: `ruff` (1295 erros pré-existentes, iguais antes/depois — zero
     novos) e `pytest` (1702 passed, 28 skipped).
- **Resultado**: 247 arquivos alterados, 656/656 linhas. PR
  https://github.com/yvesmarinho/scaffold-project/pull/29.
- **Decisões**:
  - Novo nome `scaffold-project` aplicado em tudo (pasta, workspace, pacote
    `scaffold_project`, `pyproject`, URLs).
  - Substituição global incluindo `docs/SESSIONS/**` históricos e links de PR
    (decisão explícita do usuário; GitHub redireciona URLs antigas).
  - Scripts em `~/DevOps/Python/Snippests/rename-project` avaliados como
    referência apenas (o `.py` só imprime um plano; o `.sh` tem alvo errado
    `enterprise-scaffold` e sed ingênuo) — não executados.
- **Arquivos**: `pyproject.toml`, `README.md`, `QUICKSTART.md`, `CHANGELOG.md`,
  `Makefile`, `scripts/lib/*.py`, `src/scaffold_project/`, `tests/*.sh`,
  `.github/`, `.scaffold-config.README.md`, `docs/**`.
- **Commits**: `1820a21` (rename), `f1c6554` (commit prévio de `lembrete.md` no
  repo antigo).
- **Pendências**:
  - Merge do PR #29.
  - Remover o clone antigo `~/VyaJobs/a-default-project` (após merge, com
    `git worktree remove` primeiro).
  - Atualizar nota do vault Obsidian `projects/` e `00-projetos-map.md`.
  - `rich`/`pyyaml` ausentes de `pyproject.toml` (pré-existente).
