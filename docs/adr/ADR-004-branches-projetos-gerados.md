<!-- Criado em: 25/11/2026 14:28 -->
<!-- Modificado em: 25/11/2026 14:28 -->

# ADR-004: Modelo de branches main / dev / release nos projetos gerados

- **Status**: Aceito
- **Data**: 2026-11-25
- **Decisores**: Yves Marinho (dono do projeto)
- **Escopo**: projetos **gerados** pelo scaffold, não este repositório

## Contexto

Os projetos gerados nasciam só com a `main`. Os workflows de segurança disparavam em
`develop`, uma branch que nunca era criada, e o `git-validation.yml` reprovava qualquer
PR cuja branch de origem não fosse `tipo/descricao`, inclusive um PR de integração para a `main`.
A proteção de branch era só documentada (`docs/BRANCH_PROTECTION_SETUP.md`).

## Decisão

1. Modelo: `main` estável; `dev` é a branch default e o destino dos PRs de feature;
   `dev` → `main` só por PR com CI verde; fases em `release/faseN`.
2. `--new` cria `dev` a partir da `main` depois do commit e da tag iniciais e deixa o checkout em `dev`.
3. Os workflows gerados (CI de infra, Security Scan e Dependency Review) disparam em
   `main`, `master`, `dev` e `release/**`. O `git-validation.yml` aceita `dev` e `release/faseN`.
4. Com `--repo` GitHub e `gh` autenticado, `scripts/lib/github_setup.py`:
   - envia `main`, `dev` e as tags;
   - define `dev` como default;
   - protege a `main`: PR obrigatório e checks (`Validation Summary` e `ci`, quando os workflows existirem) com `strict`.
5. Toda falha dessa etapa (sem `gh`, sem autenticação, repositório inexistente, timeout, erro de API) vira
   `skipped` com o motivo e nunca derruba a geração. `--no-github-setup` pula a etapa.

## Consequências

### Positivas
- O modelo de branches passa a existir na criação, não só na documentação.
- O CI cobre `dev` e as fases.

### Negativas
- Com `--repo`, a geração passa a enviar código ao GitHub. Use `--no-github-setup` para evitar.
- A proteção exige 0 aprovações, pensando em quem trabalha sozinho. Times devem subir esse número no GitHub.
- Projetos já gerados não recebem `dev` pelo upgrade; a migração é manual, pelo guia.

## Alternativas consideradas
1. **Só local + CI**: sem chamadas ao `gh`; a proteção ficaria manual. Descartada pelo usuário.
2. **Git Flow completo** (`develop`, `hotfix/*`, `release/x.y`): mais cerimônia que o necessário.
