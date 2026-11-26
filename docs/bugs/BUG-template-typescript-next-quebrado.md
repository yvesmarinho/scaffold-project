<!-- Criado em: 26/11/2026 15:05 -->
<!-- Modificado em: 26/11/2026 16:54 -->

# BUG: projeto gerado com o perfil `typescript-next` falhava em tsc, jest, lint e build

- **Data**: 26/11/2026
- **Arquivos**: `scaffold/templates/project/typescript-next/**`, `scaffold/profiles/typescript-next.yaml`, `scaffold/templates/skills/typescript-next/SKILL.md`
- **Status**: ✅ corrigido
- **Como apareceu**: ao avaliar os PRs #80–#82 do dependabot, o template foi instalado com `pnpm` num diretório isolado. Até a versão da `main` falhava.

## Sintomas e causas

| Checagem | Erro | Causa |
|---|---|---|
| `tsc`, `next build` | `setupFilesAfterEach does not exist` | chaves erradas no `jest.config.ts`. O correto é `setupFilesAfterEnv` e `coverageThreshold` |
| `tsc` | `fakeTimers`/`Temporal` incompatíveis | `jest-environment-jsdom` 29 junto com `jest` 30 |
| `jest` | `ReferenceError: Request is not defined` | o teste da rota (`next/server`) rodava em jsdom |
| `lint`, `next build` | `Invalid Options: useEslintrc, extensions...` | `next lint` (obsoleto) com ESLint 10, que removeu as opções antigas |
| `next build` (projeto gerado) | `globals.css` não encontrado | `app/globals.css` não estava no descritor, e o composer copia só o que está declarado |
| `pnpm install` | `"pnpm.overrides" ignored` | o pnpm 10 em diante não lê o campo `pnpm` do `package.json` |

Nenhum teste instalava e rodava o template, por isso nada disso foi percebido.

## Correção
- **`jest.config.ts`**: usa `setupFilesAfterEnv` e `coverageThreshold`. O teste da rota recebe `@jest-environment node`.
- **Dependências**: `jest-environment-jsdom ^30.5.2` (o mesmo do PR #80) e `eslint-config-next ^16.4.6` (o mesmo do PR #81, com flat config nativo).
- **ESLint**: fixado em `^9.39.0`. Os plugins `import`, `react` e `jsx-a11y` ainda não declaram suporte ao ESLint 10, e com o 9 o `pnpm peers check` fica limpo.
- **Lint**:
  - `.eslintrc.json` foi trocado por `eslint.config.mjs`, mantendo as mesmas regras;
  - os scripts `lint` e `lint:fix` passaram a usar `eslint .`;
  - o `next.config.ts` ganhou `eslint.ignoreDuringBuilds`, porque o lint interno do build ainda usa as opções antigas.
- **Overrides**: foram para `pnpm-workspace.yaml`. O `Dockerfile` copia esse arquivo antes do `pnpm install`.
- **Descritor**: passa a declarar `app/globals.css`, `eslint.config.mjs` e `pnpm-workspace.yaml`.
- **SKILL.md**: deixou de ensinar a configuração quebrada.

## Testes
`tests/test_template_typescript_next.py`:
- **10 testes estáticos**, que sempre rodam;
- **1 teste de ponta a ponta**, opcional (`SCAFFOLD_TEST_NODE_TEMPLATES=1`, exige `pnpm` e rede). Ele copia os arquivos declarados no descritor e roda install, tsc, jest, lint e build.

O teste de ponta a ponta falhava antes da correção, no `tsc`. Um projeto gerado com `scaffold.py new --with-code-profile typescript-next` passou nas cinco etapas.

## Fora do escopo (problemas encontrados que já existiam)
- O `Dockerfile` copia `/app/public` e `.next/standalone`. O template não tem `public/` e o `next.config.ts` não tem `output: "standalone"`, então o `docker build` falharia.
- O `.gitignore` do template nunca é copiado, porque o do projeto vem dos templates base.
- A dependência TypeScript 7 (PR #82) não é compatível com o `@typescript-eslint` 8, que aceita TS abaixo de 6.1.
