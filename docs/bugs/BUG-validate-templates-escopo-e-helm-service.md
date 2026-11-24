<!-- Criado em: 24/11/2026 15:34 -->
<!-- Modificado em: 24/11/2026 16:26 -->

# BUG: validador de templates olhava o lugar errado, e o Service do perfil k8s-helm estava quebrado

**Data**: 24/11/2026 · **Severidade**: Média (validador inútil) e Alta (manifesto Helm inválido em todo projeto k8s-helm) · **Status**: ✅ Corrigido (branch `fix/validate-templates-escopo`)

## Sintoma

- `make validate-templates` sempre terminava em **FAILED**: 1 erro (`template_version` ausente) e 4 avisos.
- Ele validava só `.specify/templates/`, que são os arquivos do SpecKit gerados pelo `specify init` e que o projeto não edita. Os **124 templates reais** em `scaffold/templates/` nunca eram validados.
- Com o validador apontado para o lugar certo, apareceu um bug real: o `helm/templates/service.yaml` do perfil k8s-helm tinha `{ { include ... } }` no lugar de `{{ include ... }}`. O Helm não interpreta isso como template, e o `Service` de todo projeto gerado com esse perfil saía inválido. O arquivo estava assim desde `298d10c` (24/06/2026), provavelmente porque um formatador de YAML foi aplicado a um template Go.

## Causa raiz

1. `TEMPLATE_DIR = Path(".specify/templates")`, com busca **não recursiva**, enquanto `scaffold/templates/` é aninhado.
2. Exigir `template_version` no frontmatter é regra do IMP-65, que tratava da sincronização dos templates do SpecKit. O upstream não tem esse campo e os templates do scaffold também não.
3. Não havia suporte a:
   - YAML com vários documentos;
   - YAML "Markdown híbrido" do objetivo v2 (frontmatter YAML com corpo em Markdown, extensão `.yaml`);
   - templates Go do Helm, que não são YAML.
4. Os links nos templates apontam para caminhos do **projeto gerado**. Validá-los contra a árvore de templates gerava 41 falsos positivos.

## Correção

- A CLI agora valida `scaffold/templates/` por padrão, de forma recursiva, incluindo `*.yml` e ignorando caches.
- YAML com vários documentos é aceito. No formato híbrido, só o frontmatter é validado.
- Templates Go são ignorados como YAML. O formato corrompido `{ {` vira **erro**.
- Frontmatter obrigatório e checagem de links viraram opções (`--require-frontmatter`, `--check-links`). A classe mantém o padrão antigo, então os testes existentes continuam válidos.
- O `service.yaml` foi restaurado com o padrão do `helm create`, igual ao `deployment.yaml`.
- No pre-commit, o `check-yaml` passou a ignorar `helm/templates/`, que não é YAML.
- O `make validate-templates` agora usa `uv run` e aponta para `scaffold/templates/`. O CI roda a validação no job obrigatório `Lint & Validate`.

## Testes

`tests/test_validate_templates_escopo.py`, com 11 testes:
- busca recursiva;
- YAML com vários documentos;
- template Go do Helm ignorado;
- frontmatter opcional;
- links desligados;
- caches ignorados;
- Go template corrompido vira erro;
- YAML híbrido válido e inválido;
- CLI, com e sem `--json`, sobre os templates reais.

Na fase vermelha, todos falharam. O exemplo híbrido foi corrigido para refletir o arquivo real, que tem um comentário HTML de várias linhas. A suíte completa passou com 1762 testes.

## Lições

- Um validador que sempre falha deixa de ser olhado. Ele precisa rodar no CI desde o primeiro dia.
- Formatadores de YAML não podem ser aplicados a templates Go.
- O `helm` não está instalado nesta máquina, então o `service.yaml` foi validado pela estrutura (padrão do `helm create` e helpers existentes), não renderizado. Rodar `helm lint` no CI fica como sugestão.

## Complemento (24/11/2026 16:13): projetos já gerados

- **Busca por projetos afetados:** nenhum foi encontrado.
  - Busca local: `helm/templates/service.yaml` em todo o `$HOME`.
  - Busca no GitHub: `gh search code` nos repositórios do usuário. Os helpers `my-app.*` só aparecem no próprio scaffold. A busca de código do GitHub cobre apenas a branch padrão de cada repositório.
- **Limitação encontrada:** o `scaffold upgrade` não corrigia arquivos de perfil já existentes. O `ProfileComposer._apply_profile` pulava qualquer destino existente, mesmo com `--force`, porque o flag não era repassado ao composer.
- **Correção:**
  - `compose(..., force=)` e `upgrade`/`compose` passam a repassar `--force`.
  - **Sem `--force`**, o arquivo continua preservado e a mensagem avisa quando ele difere do template.
  - **Com `--force`**, um arquivo divergente ganha backup em `<arquivo>.backup` e é sobrescrito com status `updated`. Um arquivo idêntico não é tocado.
  - O rollback restaura os itens `updated` a partir do backup. Antes, ele só apagava os `created`.
- **Testes** (`tests/test_composer_force.py`, 6 no total):
  - 4 testes unitários: sem force, com force, arquivo idêntico, rollback.
  - 2 testes ponta a ponta: gera um projeto k8s-helm, corrompe o `service.yaml` como no bug e roda `upgrade`. Sem `--force`, o arquivo é preservado. Com `--force`, ele é corrigido e o `.backup` fica igual ao original corrompido.
  - Sem o repasse do `force` no upgrade, o teste ponta a ponta falhava.

## Ajuste (24/11/2026 16:26): flag explícita no lugar do `--force` (decisão do usuário)

O PR #66 fez o `--force` também sobrescrever arquivos de perfil, como `src/main.py`, `Dockerfile` e `conftest.py`. São arquivos que o usuário costuma editar, então um `--force` usado para atualizar o SpecKit trocaria essas customizações.

**Decisão:** o `--force` voltou a **não** tocar arquivos de perfil. Para atualizá-los, é preciso usar a flag explícita **`--update-profile-files`**:
- no `upgrade` e no `compose`, os arquivos divergentes são **listados antes** da atualização, e cada um ganha backup `<arquivo>.backup`;
- sem a flag, o upgrade preserva os arquivos e mostra quais diferem do template, sugerindo a flag;
- o novo `ProfileComposer.divergent_files()` lista os arquivos divergentes sem escrever nada.

**Para corrigir um projeto k8s-helm antigo:** `scaffold upgrade --update-profile-files`.
