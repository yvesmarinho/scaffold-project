<!-- Criado em: 24/11/2026 11:19 -->
<!-- Modificado em: 26/11/2026 11:39 -->

# ADR-003: Separação dos templates de distribuição dos arquivos do próprio repositório

- **Status**: Aceito (25/11/2026, pelo dono do projeto, sem ajustes)
- **Data**: 2026-11-24
- **Decisores**: mantenedor do scaffold-project
- **Contexto relacionado**: [INVENTARIO-templates.md](../analysis/INVENTARIO-templates.md); item do backlog em `docs/planning/lembrete.md`

## Contexto

O scaffold copia ou renderiza arquivos de **quatro tipos de origem**:
1. `scaffold/templates/` (templates puros);
2. strings Python em `project.py`, `templates.py` e `infra.py` (cerca de 70 KB);
3. arquivos do próprio repositório reaproveitados: `scripts/*.py`, `scripts/lib/*`, `.claude/*`, `.github/copilot-instructions.md`, `.specify/templates/`;
4. um diretório externo (`~/Documentos/DevOps/.copilot-shared`).

Por isso:
- não há como saber, olhando a árvore, o que é distribuído;
- o `--publish` empacota por glob fixo e gera um tarball **que não roda** (faltam `scripts/lib/flows/` e `scripts/lib/ai/`);
- alterar um arquivo de uso do repositório muda sem querer todos os projetos gerados, e o inverso também acontece.

## Decisão

1. **`scaffold/` passa a ser a única fonte do que é distribuído.**
   - `scaffold/profiles/`: descritores.
   - `scaffold/templates/`, organizado por destino:
     - `base/`: arquivos que hoje são strings, como `README`, `Makefile`, `.gitignore`, `docs/*/README.md` e `.secrets/`;
     - `security/`, `copilot/`, `claude/`, `infra/`, `speckit/`, `objetivo/`, `project/<perfil>/` (já existente);
     - `runtime/`: scripts e libs copiados para o projeto gerado.
2. **Scripts de uso duplo** (session-manager, tracker, `mem_*`, `lib/memory` e afins) ficam em `scaffold/templates/runtime/` como fonte única. O repositório continua a usá-los por meio de wrapper ou symlink em `scripts/`, sem duplicar arquivos.
3. **Configs do repositório** (`.claude/`, `.github/agents`, `.github/copilot-instructions.md`, `.specify/`) deixam de ser fonte de template. Quando o conteúdo for o mesmo, a versão de distribuição fica em `scaffold/templates/` e o repositório pode apontar para ela.
4. **Um único estilo de placeholder:** `{{NOME}}`, renderizado por uma só função. Strings extraídas para arquivos `*.tmpl` precisam produzir saída **byte a byte igual**, garantida pelos snapshots existentes.
5. **`--publish` empacota a partir de `git ls-files`**, limitado a `scripts/` (o gerador, de forma recursiva) e `scaffold/`. Um teste verifica que o tarball extraído executa `scaffold.py --list-profiles`.
6. A dependência externa `.copilot-shared` vira um conteúdo versionado em `scaffold/templates/copilot/`.

## Consequências

### Positivas
- Fica explícito o que é distribuído.
- O tarball passa a ser instalável e testado.
- Mudanças no repositório deixam de vazar para os projetos gerados.

### Negativas
- A migração é grande: cerca de 15 caminhos fixos, descritores, Makefile, testes e allowlist do security-scan.
- Os symlinks ou wrappers dos scripts de uso duplo acrescentam uma indireção.
- Projetos já gerados só recebem as mudanças via upgrade, e o upgrade hoje não reaplica agents nem os templates GitHub.

## Alternativas consideradas
1. **Manter como está e só corrigir o glob do publish**
   - prós: mudança mínima.
   - contras: o acoplamento continua e o publish volta a quebrar sempre que surgir um diretório novo.
2. **Pacote Python separado (`scaffold-templates`)**
   - prós: distribuição via pip/uv.
   - contras: complexidade prematura para um único consumidor.

## Plano de migração (fatias verticais, um PR cada)
1. **Correção imediata do publish:** glob recursivo `scripts/lib/**/*.py` e um teste "o tarball roda". Independe deste ADR.
2. Remover órfãos e a definição duplicada de `_SECURITY_MD_WITHOUT_GITHUB`. Corrigir ou marcar os 9 descritores com `templates_path` inexistente.
3. Extrair as strings de `project.py` para `scaffold/templates/base/*.tmpl`, com snapshots iguais.
4. Mover os scripts de uso duplo para `scaffold/templates/runtime/`, com wrappers em `scripts/`, e ajustar Makefile, testes e `SCAN_ALLOWLIST`.
5. Separar as configs do repositório (`.claude`, `.github/copilot-instructions.md`, `.specify/templates`) das versões de distribuição.
6. Trocar o publish para `git ls-files` sobre `scripts/` e `scaffold/`, e fazer o upgrade reaplicar agents e templates GitHub.
7. Remover os symlinks de compatibilidade (`.github/templates/*`, `profile-descriptors`) depois de migrar os testes.

## Execução

| Fatia | Status |
|---|---|
| 1. Correção do publish | ✅ 24/11/2026 (`git ls-files`, teste "o tarball roda") |
| 2. Órfãos, constante duplicada, descritores quebrados | ✅ 25/11/2026 (ver abaixo) |
| 3. Strings de `project.py` → `scaffold/templates/base/*.tmpl` | ✅ 25/11/2026 (ver abaixo) |
| 4. Scripts de uso duplo → `scaffold/templates/runtime/` | ✅ 25/11/2026 (ver abaixo) |
| 5. Configs do repositório → versões de distribuição | ✅ 26/11/2026 (ver abaixo) |
| 6–7 | pendentes |

Fatia 2:
- **Constante**: removida a primeira definição de `_SECURITY_MD_WITHOUT_GITHUB`. Era idêntica à segunda, que é a que vale em runtime.
- **Docs internos e exemplos**: `scaffold/templates/docs/*.md` (4 docs internos) foi para `docs/reference/templates/`, e `objetivo/examples/` foi para `docs/reference/objetivo-examples/`.
- **Removidos**:
  - `speckit/specify-templates/`: cópias desatualizadas do `.specify/templates/`;
  - `project/ansible/` e o hook `ansible-lint`: nenhum perfil os declarava.
- **9 descritores** sem templates escritos foram marcados com `templates_status: pendente`:
  - o composer não tenta copiar esses templates;
  - o guia de perfil os mostra como "pendente";
  - `--validate` dá erro quando o `templates_path` não existe e a marca está ausente.
- **`typescript-next`**: saiu a entrada `sbom.json`, porque o arquivo é gerado por `make sbom`.

Fatia 3:
- **Extração**: 30 constantes de `project.py` (cerca de 1.670 linhas) viraram `scaffold/templates/base/**/*.tmpl`, carregadas por `lib/base_templates.py` (`load_base_template`).
  - Erros nomeados: `TemplateNotFoundError` (template ausente) e `InvalidTemplateNameError` (nome inválido).
  - Os nomes das constantes em `project.py` continuam os mesmos.
- **Placeholder único**: o estilo `{{NOME}}` é renderizado por `render()` em uma só passada. `@OWNER`/`OWNER` e `{profiles_section}`/`{git_remote_section}` foram convertidos.
- **Verificação byte a byte**: 3 projetos foram gerados antes e depois da mudança (programming/python/copilot com `--repo`, infrastructure/go/claude, analysis/other/both com `--repo`).
  - Os 441 arquivos ficaram idênticos, fora timestamps e `target_dir`.
  - As permissões também ficaram idênticas.
- **Layout**: as pastas espelham o destino, sem o ponto inicial. O `.gitignore` ganhou `!scaffold/templates/base/*/`, porque `secrets/` e `logs/` eram ignorados. Um teste garante que nenhum template fique ignorado.
- **Hooks**: `trailing-whitespace`/`end-of-file-fixer` ignoram `scaffold/templates/base/`, porque os bytes são contrato (o `Makefile.tmpl` não tem newline final).

Fatia 4:
- **Movidos com `git mv`**: 21 arquivos de uso duplo agora ficam em `scaffold/templates/runtime/scripts/`:
  - 8 libs de sessão e memória;
  - `session-manager`, `session-time-tracker`, `mem_*`, `create_memory_structure`, `test_memory_smoke`;
  - 4 shell scripts, `git-hooks/commit-msg` e `setup-branch-protection.py`.
- **Uso pelo repositório**: `scripts/<rel>` virou **symlink relativo** para o arquivo real. Foi escolhido symlink, e não wrapper, porque `__file__` e `BASH_SOURCE` não são resolvidos, então a raiz continua correta.
- **Conjunto autocontido**: os arquivos só importam libs do próprio conjunto (verificado por AST).
- **Código**: `project.RUNTIME_SCRIPTS_DIR` e `RUNTIME_FILES` centralizam a lista. As funções de cópia leem do runtime.
- **Formatação**: black/ruff formataram 4 arquivos que nunca tinham passado pelo hook. O AST ficou idêntico, exceto `f"..."` sem placeholder que virou `"..."`, com a mesma saída.
- **Verificação**: os projetos gerados ficaram idênticos à linha de base, inclusive tipo e permissão de arquivo, sem nenhum symlink vazado. A exceção são esses 4 arquivos formatados.
- **Bug no publish**: a eliminação de duplicatas pelo caminho resolvido descartava o alvo dos symlinks. Ver `docs/bugs/BUG-publish-symlink-sem-alvo.md`.

Fatia 5:
- **Novas fontes de distribuição** (cópias independentes, sem symlink para o repo):

  | Antes (repositório) | Agora (`scaffold/templates/`) |
  |---|---|
  | `.claude/commands/*.md` | `claude/commands/` |
  | `.claude/skills/<dir>/**` | `claude/skills/` |
  | `.github/copilot-instructions.md` | `copilot/copilot-instructions.md` |
  | `.copilot-rules.md` | `copilot/copilot-rules.md` |
  | `.specify/templates/*.md` | `speckit/templates/` |
  | `.github/ISSUE_TEMPLATE/*.md` | `base-configs/common/ISSUE_TEMPLATE/` |
  | `docs/guides/BRANCH_PROTECTION_SETUP.md` | `base-configs/common/BRANCH_PROTECTION_SETUP.md` |

  As duas últimas linhas não estavam na lista original, mas eram do mesmo tipo (arquivo do repo usado como template).
- **Por que cópia e não symlink**: o objetivo é que mudar `.claude/` ou `.specify/` do repo não altere os projetos gerados. Um symlink traria esse vazamento de volta. Além disso, o `.specify/` do repo é gerenciado pelo SpecKit.
- **Código**: `project.py` ganhou `_CLAUDE_TEMPLATES`, `_COPILOT_TEMPLATES` e `SPECKIT_UPSTREAM_TEMPLATES`. O `check-templates` e o `diff-template` (quando recebem só o nome) usam `SPECKIT_UPSTREAM_TEMPLATES` como upstream.
- **Publish**: as configs do repo saíram de `_INCLUDE_PATTERNS`.
- **Hooks**: `trailing-whitespace` e `end-of-file-fixer` também ignoram `scaffold/templates/claude/` e `scaffold/templates/speckit/templates/`. Cinco arquivos herdados do SpecKit têm espaços no fim de linha, e os bytes da saída são contrato (mesma regra de `base/` na fatia 3).
- **Teste novo** (`tests/test_templates_distribuicao_isolados.py`): uma árvore com só os arquivos versionados de `scripts/` e `scaffold/` gera o mesmo projeto que o repositório completo. Antes da mudança, a geração falhava nessa árvore.
- **Verificação**: os 3 projetos de referência (os mesmos da fatia 3) ficaram idênticos à linha de base: 438 arquivos com conteúdo, tipo e permissão iguais, fora timestamps e o diretório de destino.
- **Observação (comportamento que já existia)**: no plugin do Copilot (`ai/plugins/copilot.py`), `templates.generate_copilot_instructions` gera `.github/copilot-instructions.md` antes de `copy_copilot_instructions`.
  - Na criação, a cópia fica como `skipped`.
  - No upgrade com `--force`, a cópia sobrescreve o arquivo recém-gerado com a versão estática.

  Isso não foi alterado nesta fatia. Fica para avaliar na fatia 6, que trata do upgrade.

## Pontos para decisão do usuário (resolvidos em 25/11/2026)
- Aprovar a estrutura-alvo, em especial `runtime/` e o uso de wrappers no lugar de duplicação.
- Confirmar `{{NOME}}` como o placeholder único.
- Confirmar que a fatia 1 (correção do publish) pode ser feita antes da aprovação deste ADR.
