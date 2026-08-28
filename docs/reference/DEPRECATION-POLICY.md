# Política de Depreciação — Enterprise Scaffold Project Template

> Este documento define os critérios, períodos de aviso e procedimentos para depreciar
> perfis, campos de descriptor e artefatos de template.

**Versão**: 1.0.0 — 2026-03-07
**Referências**: [CHANGELOG.md](../CHANGELOG.md) | [docs/TEMPLATE-VERSIONS.md](TEMPLATE-VERSIONS.md)

---

## 1. Princípios

1. **Sem remoção surpresa** — qualquer remoção de perfil, campo ou artefato deve ser anunciada com antecedência mínima de 1 versão MINOR.
2. **Sem quebra silenciosa** — mudanças que causem falha em projetos existentes são MAJOR e devem ter guia de migração.
3. **Comunicação clara** — depreciações aparecem em: descriptor YAML (`status: deprecated`), CHANGELOG, e README do perfil.
4. **Rollback possível** — projetos gerados com versão anterior continuam funcionando durante o período de aviso.

---

## 2. Ciclo de Vida de um Perfil

```
draft → stable → deprecated → removed
```

| Status | Significado | Ação do motor de composição |
|--------|-------------|----------------------------|
| `draft` | Em desenvolvimento — não usar em produção | Aviso no console |
| `stable` | Produção — use com confiança | Normal |
| `deprecated` | Será removido — migrar para substituto | Aviso obrigatório no console + log |
| `removed` | Não disponível mais | Erro fatal + guia de migração |

---

## 3. Períodos de Aviso

| Escopo | Período mínimo | Exemplo |
|--------|---------------|---------|
| Campo opcional de descriptor | 1 release PATCH | `last_tested` renomeado — 1 PATCH de aviso |
| Campo obrigatório de descriptor | 1 release MINOR | `name` movido — 1 MINOR de aviso |
| Template file de perfil | 1 release MINOR | Arquivo removido de perfil — 1 MINOR de aviso |
| Perfil layer2 completo | 1 release MINOR | Perfil deprecated — 1 MINOR antes de removed |
| Perfil core | 1 release MAJOR | Perfil core deprecated — 1 MAJOR antes de removed |
| Flag de CLI do scaffold.py | 1 release MINOR | `--dry-run` renomeada — 1 MINOR de aviso |

---

## 4. Procedimento de Depreciação

### 4.1 Depreciar um Perfil

1. **Descriptor YAML**: mudar `status: stable` → `status: deprecated` e adicionar:
   ```yaml
   deprecated_since: "YYYY-MM-DD"
   deprecated_reason: "Substituído por {novo_perfil} em vX.Y.Z"
   migration_guide: "docs/migrations/migrate-{perfil}-to-{novo}.md"
   ```

2. **CHANGELOG.md**: adicionar entrada `### Deprecated` na próxima versão.

3. **docs/TEMPLATE-VERSIONS.md**: atualizar status na tabela para `⚠️ deprecated`.

4. **Motor de composição** (`scripts/lib/composer.py`): emitir `console.print("[yellow]⚠ Perfil '{name}' está deprecated...")` ao tentar compor.

5. **Remover na versão seguinte**: após 1 release com status `deprecated`, mover para `status: removed`.

### 4.2 Depreciar um Campo de Descriptor

1. Adicionar comentário no schema: `# DEPRECATED: use {novo_campo} (removido em vX.Y.Z)`
2. No loader `_load_yaml()`, emitir aviso se campo antigo for encontrado
3. Atualizar `docs/copilot/PROFILE-DESCRIPTOR-SCHEMA.md`

### 4.3 Depreciar uma Flag de CLI

1. Manter a flag funcionando (sem erro) mas emitir:
   ```
   ⚠ --old-flag está deprecated e será removido em vX.Y.Z. Use --new-flag.
   ```
2. Remover na versão MINOR seguinte.

---

## 5. Guias de Migração

Guias de migração ficam em `docs/migrations/`:

```
docs/
└── migrations/
    └── migrate-PERFIL-ANTIGO-to-PERFIL-NOVO.md
```

**Template de guia de migração**:

```markdown
# Migração: {perfil-antigo} → {perfil-novo}

## Por que migrar?
{razão da depreciação}

## Diferenças principais
| Aspecto | {perfil-antigo} | {perfil-novo} |
|---------|----------------|---------------|
| ...     | ...            | ...           |

## Passo a passo
1. ...

## O que NÃO muda
- ...
```

---

## 6. O que NUNCA deprecia

Os seguintes elementos são considerados **API estável** e não serão removidos ou quebrados:

- `name`, `layer`, `version`, `description` nos descriptors
- Flag `--new` do `scaffold.py`
- Flag `--ci` do `scaffold.py`
- Flag `--list-profiles` do `scaffold.py`
- Campos `excludes_with` e `combines_with` nos descriptors
- Schema version `1.0.0` (qualquer mudança gera `2.0.0`)

---

## 7. Histórico de Depreciações

| Versão | Item depreciado | Motivo | Removido em |
|--------|----------------|--------|-------------|
| — | *(nenhuma depreciação ainda)* | | |
