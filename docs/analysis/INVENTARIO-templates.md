<!-- Criado em: 24/11/2026 11:18 -->
<!-- Modificado em: 24/11/2026 15:00 -->

# Inventário de templates do scaffold-project

**Data:** 24/11/2026
**Item do backlog:** "Separar arquivos de template dos arquivos do projeto (distribuição)"
**Decisão relacionada:** [ADR-003](../adr/ADR-003-separacao-templates-distribuicao.md) (Proposto)
**Escopo:** só levantamento. Nenhum arquivo foi movido.

A base de todos os caminhos de origem é `_TEMPLATE_ROOT` (`scripts/lib/project.py:29`), que aponta para a raiz do repositório.

**Observação:** `.github/templates/*` e `profile-descriptors` são **symlinks versionados de compatibilidade**. `.github/templates/*` aponta para `scaffold/templates/base-configs/common` e `scaffold/templates/project/*`; `profile-descriptors` aponta para `scaffold/profiles`. Vários testes ainda usam esses caminhos.

## 1. Origens que o código copia ou renderiza para o projeto gerado

| Origem | Usado por | Destino no projeto gerado | Também usado pelo próprio repo? |
|---|---|---|---|
| `scaffold/templates/speckit/prompts/domain/*.prompt.md` | `_copy_domain_profile` | `.github/prompts/domain/` | não |
| `scaffold/templates/speckit/agents/*.agent.md` (exceto `speckit.*`) | `copy_custom_agents` | `.github/agents/` | não |
| `scaffold/templates/docs/objetivo-manifest-template.yaml`, `mcp-questions-template.yaml` | `setup_project_docs` | `objetivo.yaml`, `mcp-questions.yaml` | não |
| `scaffold/templates/base-configs/common/**` (CONTRIBUTING, PR/ISSUE templates, workflows, BADGES) | `copy_github_templates` | `.github/`, raiz | não |
| `scaffold/templates/project/<perfil>/**` | `ProfileComposer._apply_profile` (`composer.py`) | caminhos declarados no descritor | não |
| `scaffold/templates/objetivo/objetivo-v2-template.yaml` | `objetivo_wizard.py`, `flows/objetivo_init.py` | `objetivo-init.yaml` | não |
| `.github/ISSUE_TEMPLATE/*.md` | `copy_github_templates` | `.github/ISSUE_TEMPLATE/` | **sim** |
| `docs/guides/BRANCH_PROTECTION_SETUP.md` | `copy_github_templates` | `docs/` | **sim** |
| `scripts/git-hooks/commit-msg`, `scripts/setup-branch-protection.py` | `copy_github_templates` | `scripts/` | **sim** |
| `scripts/session-manager.py`, `session-time-tracker.py` | `copy_session_scripts` | `scripts/` | **sim** |
| `scripts/mem_*.py`, `create_memory_structure.py`, `test_memory_smoke.py` | `copy_memory_scripts` | `scripts/` | **sim** |
| `scripts/*.sh` (activate-mcp, git-commit-with-file, cleanup-tmp, validate-docs-links) | `copy_utility_scripts` | `scripts/` | **sim** |
| `scripts/lib/{memory,git_validators,sanitize,session_*,git_session}.py` | `copy_session_libs` | `scripts/lib/` | **sim** (mesmo pacote `lib` do gerador) |
| `.github/copilot-instructions.md`, `.copilot-rules.md` | `copy_copilot_instructions` | raiz, `.github/` | **sim** |
| `.claude/commands/*.md`, `.claude/skills/*/` | `copy_claude_config` | `.claude/` | **sim** |
| `.specify/templates/constitution-template.md` | `generate_constitution` | `.specify/memory/constitution.md` | **sim** |
| `~/Documentos/DevOps/.copilot-shared/rules/.copilot-rules.md` | `links.setup_symlinks` | symlink `.copilot-rules.md` | externo ao repositório |

## 2. Templates embutidos como strings Python

- **`scripts/lib/project.py`**, cerca de 51 KB:
  - `README.md`, `docs/INDEX.md`, `docs/TODO.md`, `.gitignore`;
  - `.secrets/*`, `.git-hooks/pre-commit.secrets` (8 KB, bash com Python embutido);
  - os 8 `docs/*/README.md` e `PROJECT_CREATION_SUMMARY.md`;
  - `Makefile`, `SECURITY.md`, `CODEOWNERS`, `dependabot.yml`;
  - os workflows `security-scan.yml` e `dependency-review.yml`;
  - `CLAUDE.md`, `.claude/settings.json` e os READMEs de `logs/`, `tmp/`, `.memory/` e `.session-time/`;
  - `_SECURITY_MD_WITHOUT_GITHUB` está **definida duas vezes**, e a segunda definição sobrescreve a primeira.
- **`scripts/lib/templates.py`**, cerca de 12 KB: `copilot-instructions.md`, `.copilot-rules-<nome>.md`, `PROFILE-GUIDE-*.md` e fragmentos (regras P0, convenções, estrutura de pastas).
- **`scripts/lib/infra.py`**, cerca de 9,5 KB: `ci.yml` por linguagem, `Dockerfile`, `docker-compose.yml` e `RUNBOOK.md`.
- **`scripts/lib/vscode.py`**: dicts serializados para `.vscode/*.json` e `*.code-workspace`.

Placeholders em uso: `{{PROJECT_NAME}}`, `{{ project_name }}`, `{project_name}`, `.format()` e `replace`. São estilos diferentes convivendo no mesmo projeto.

## 3. Possíveis órfãos

- `scaffold/templates/docs/*.md` (4 docs internos), `objetivo/examples/*` e `speckit/specify-templates/*`. Este último é idêntico ao `.specify/templates/`, que é o arquivo de fato usado.
- `speckit/prompts/*.prompt.md` na raiz (17 arquivos). Só `prompts/domain/` é copiado, embora `flows/dry_run.py` anuncie também `session-start` e `session-end`.
- `project/ansible/*` e alguns `.gitignore` e `globals.css` de perfis que nenhum descritor declara.
- `docs/templates/` (6 arquivos) é usado só pelo agent `objetivo-init` do próprio repo.
- **Referências quebradas:**
  - 9 descritores têm `templates_path` apontando para pastas inexistentes: appsec-engineer, backend-architect, database-expert, frontend-architect, qa-automation-engineer, sre-platform-engineer, systems-engineer, ui-design-expert e ux-design-expert. O composer só registra `skipped`.
  - `typescript-next` declara `sbom.json`, que não existe.
  - Os descritores `devops-*` usam `source: ".copilot-shared/..."`.

## 4. `--publish`: bug confirmado

`scripts/lib/publish.py` monta o tarball a partir de `_INCLUDE_PATTERNS` (glob fixo) e não consulta o git.

- **Confirmado em 24/11/2026:** o tarball gerado tem **0 arquivos de `scripts/lib/flows/`**, porque o glob `scripts/lib/*.py` não é recursivo. Também faltam `scripts/lib/ai/**`, e `scaffold.py` importa `lib.flows`, então **o pacote distribuído não roda**.
- Também faltam fontes que o código copia: scripts de sessão e memory, `.claude/*`, `.github/copilot-instructions.md`, `.specify/templates/constitution-template.md` e `scripts/bin/`.
- Entram arquivos indevidos: o CI do próprio repo, prompts `speckit.*` do repo, todos os `tests/*.py` e `.ruff_cache` não versionado dentro de `scaffold/templates/project/*`.

## 5. Riscos de migração

1. Caminhos hardcoded em cerca de 15 pontos de `project.py`, nos flows, em `ui.py`, em `session_security.py` (`SCAN_ALLOWLIST`), no `.pre-commit-config.yaml` e nos campos `templates_path`/`source` dos descritores.
2. Scripts e libs de uso duplo. Eles rodam aqui pelo Makefile e pelos testes e também são copiados. `memory.py` deduz `PROJECT_ROOT` por `parent.parent.parent`.
3. Configs do repo reaproveitadas como template. Separá-las cria duas cópias que podem divergir, e isso já acontece entre `.github/agents` e `scaffold/templates/speckit/agents`.
4. Testes de snapshot dependem byte a byte das strings de `templates.py`. Vários testes usam os symlinks de compatibilidade.
5. Colisões de destino: `.github/CODEOWNERS` e `.github/copilot-instructions.md` são escritos duas vezes, e `.claude/commands/speckit.*` são copiados e também gerados pelo `specify init`.
6. O upgrade não reaplica `copy_custom_agents` nem `copy_github_templates`.
