<!-- Criado em: 24/11/2026 15:34 -->
<!-- Modificado em: 24/11/2026 15:34 -->

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
