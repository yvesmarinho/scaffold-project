# Template Examples

Esta pasta contém exemplos práticos de uso dos templates do projeto.

## Arquivos de Exemplo

### objetivo-*.yaml
Exemplos de arquivos objetivo.yaml para diferentes tipos de projetos:

- **objetivo.yaml** - Exemplo completo: knowledge-harvester-library
  - Projeto de biblioteca Python para coleta de conhecimento
  - Demonstra todas as seções de um objetivo.yaml

- **objetivo-init.yaml** - Exemplo: sistema-deploy-automatizado
  - Sistema de deployment automatizado
  - Demonstra estrutura para projetos de infraestrutura

- **objetivo-init-minimal.yaml** - Exemplo mínimo: poc-minimal
  - Proof of Concept com estrutura mínima
  - Demonstra configuração mais enxuta

## Uso

Estes arquivos são **apenas referência** e não devem ser editados diretamente.

Para criar um novo projeto:

1. Copie o template ativo de `scaffold/templates/objetivo/objetivo-v2-template.yaml` (usado por padrão pelo `ObjetivoWizard`)
2. Ou use um dos exemplos como ponto de partida
3. Substitua os placeholders `{{...}}` pelos valores do seu projeto
4. Coloque o arquivo na raiz do **seu projeto** (não neste template)

> **Nota:** `objetivo-init-template.yaml`, `objetivo-init_template.yaml`, `objetivo-init-minimal.yaml` (raiz de `scaffold/templates/objetivo/`) e `spec_template.md` não são lidos por nenhum código do scaffold — foram movidos para `docs/templates/` como referência histórica/manual (ver [docs/templates/](../../../docs/templates/)).

## Templates vs Exemplos

| Arquivo | Tipo | Local | Uso |
|---------|------|-------|-----|
| `scaffold/templates/objetivo/objetivo-v2-template.yaml` | Template | Template base (ativo) | Usado por padrão pelo `ObjetivoWizard` (`scripts/lib/objetivo_wizard.py`) |
| `docs/reference/objetivo-examples/*.yaml` | Exemplo | Este diretório | Referência de estrutura completa |
| `docs/templates/objetivo-init-template.yaml` | Template | Docs (não usado pelo código) | Referência manual/histórica |
| `docs/templates/objetivo-init-minimal.yaml` | Template | Docs (não usado pelo código) | Referência manual/histórica, enriquecida |
| `docs/templates/objetivo-manifest-template.yaml` | Template | Docs | Template de manifesto objetivo |
| `.specify/templates/objetivo-template.yaml` | Template | SpecKit | Template para specs de features |

## Veja Também

- [docs/guides/](../../docs/guides/) - Guias de uso dos templates
- [docs/templates/](../../docs/templates/) - Templates de documentação
- [.specify/templates/](.specify/templates/) - Templates SpecKit
