<!-- Criado em: 24/11/2026 11:19 -->
<!-- Modificado em: 24/11/2026 15:00 -->

# ADR-003: Separação dos templates de distribuição dos arquivos do próprio repositório

- **Status**: Proposto
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

## Decisão (proposta)

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

## Pontos para decisão do usuário
- Aprovar a estrutura-alvo, em especial `runtime/` e o uso de wrappers no lugar de duplicação.
- Confirmar `{{NOME}}` como o placeholder único.
- Confirmar que a fatia 1 (correção do publish) pode ser feita antes da aprovação deste ADR.
