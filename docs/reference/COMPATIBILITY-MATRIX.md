# COMPATIBILITY-MATRIX — Perfis × Perfis

> Matriz de compatibilidade entre todos os perfis do Enterprise Scaffold Project Template.
> Gerada automaticamente a partir dos campos `combines_with` e `excludes_with` dos descritores.
>
> **Atualizar** sempre que um novo perfil for adicionado ou a compatibilidade mudar.
> **Referência**: [docs/TEMPLATE-VERSIONS.md](TEMPLATE-VERSIONS.md) | [docs/DEPRECATION-POLICY.md](DEPRECATION-POLICY.md)

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Compatível — pode ser combinado |
| ❌ | Conflito — `excludes_with` declarado — motor de composição bloqueia |
| ⚠️ | Compatível com restrições (ver notas) |
| ➕ | Obrigatório — perfil base requerido |
| — | Não relevante (mesmo perfil) |
| 🔜 | Planejado — perfil ainda não implementado |

---

## Matriz Completa (perfis implementados)

|  | `devops-programming` | `devops-infrastructure` | `devops-analysis` | `devops-security` | `python-fastapi` | `python-flask` | `typescript-next` | `k8s-helm` | `terraform-aws` | `data-warehouse-dbt` | `lgpd-baseline` | `soc2-baseline` |
|--|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **`devops-programming`** | — | ❌ | ❌ | ✅ | ✅ ➕ | ✅ ➕ | ✅ ➕ | ✅ | ✅ | — | ✅ | ✅ |
| **`devops-infrastructure`** | ❌ | — | ❌ | ✅ | — | — | — | ✅ | ✅ | — | ✅ | ✅ |
| **`devops-analysis`** | ❌ | ❌ | — | ✅ | — | — | — | — | — | ✅ | ✅ | ✅ |
| **`devops-security`** | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **`python-fastapi`** | ✅ ➕ | — | — | ✅ | — | ❌ | ⚠️ (1) | ✅ | ✅ | — | ✅ | ✅ |
| **`python-flask`** | ✅ ➕ | — | — | ✅ | ❌ | — | ⚠️ (1) | ✅ | ✅ | — | ✅ | ✅ |
| **`typescript-next`** | ✅ ➕ | — | — | ✅ | ⚠️ (1) | ⚠️ (1) | — | ✅ | ✅ | — | ✅ | ✅ |
| **`k8s-helm`** | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | — | ⚠️ (2) | — | ✅ | ✅ |
| **`terraform-aws`** | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ | ⚠️ (2) | — | — | ✅ | ✅ |
| **`data-warehouse-dbt`** | — | — | ✅ | ✅ | — | — | — | — | — | — | ✅ | ✅ |
| **`lgpd-baseline`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — | ✅ |
| **`soc2-baseline`** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | — |

### Notas

**(1)** `python-fastapi` (ou `python-flask`) + `typescript-next` são tecnicamente combinável em projetos fullstack (backend Python + frontend Next.js), mas requerem estrutura de monorepo com subdiretórios separados (`backend/` e `frontend/`). O motor de composição permite a combinação — cabe ao desenvolvedor organizar o layout. Não há `excludes_with` entre eles.

---

## Regras de Composição por Layer

```
Projeto válido:
  core (obrigatório)
    └── 1..N layer2 (sem conflitos entre si)
          └── 0..N layer3 (plataforma: k8s, terraform, etc.)
                └── transversal (devops-security — sempre aplicado)
```

### Regras
- **core** é sempre obrigatório — todo projeto precisa de exatamente 1 perfil core
- **layer2** requer o core correspondente (ex: `python-fastapi` exige `devops-programming`)
- Dois perfis layer2 do **mesmo ecossistema** com `excludes_with` declarado são bloqueados (ex: fastapi ↔ flask)
- **layer3** (k8s, terraform) são agnósticos de linguagem — combinam com qualquer layer2
- **transversal** (`devops-security`) é aplicado silenciosamente em todos os projetos — sem `excludes_with`, combina com qualquer combinação de perfis

---

## Combinações Válidas (exemplos)

```yaml
# Backend Python API
profiles:
  - devops-programming   # core
  - python-fastapi       # layer2

# Frontend Next.js
profiles:
  - devops-programming   # core
  - typescript-next      # layer2

# Fullstack (monorepo)
profiles:
  - devops-programming   # core
  - python-fastapi       # layer2 - backend/
  - typescript-next      # layer2 - frontend/

# Backend Flask
profiles:
  - devops-programming   # core
  - python-flask         # layer2
```

## Combinações Inválidas (bloqueadas pelo motor)

```yaml
# ❌ Dois frameworks Python no mesmo projeto
profiles:
  - python-fastapi
  - python-flask         # CONFLITO: excludes_with declarado

# ❌ Layer2 sem o core correspondente
profiles:
  - python-fastapi       # AVISO: devops-programming não incluído
```

---

## Matriz Futuro (perfis planejados)

|  | `go-chi` 🔜 |
|--|:--:|
| **`devops-programming`** | ✅ ➕ |
| **`devops-security`** | ✅ |
| **`python-fastapi`** | — |
| **`k8s-helm`** | ✅ |
| **`terraform-aws`** | ✅ |

**(2)** `k8s-helm` + `terraform-aws` são compatíveis (Terraform provisiona infra, Helm deploy app), mas requerem configuração adicional de state backend e providers. Sem `excludes_with` — decisão do desenvolvedor.

---

## Como esta matriz é mantida

1. Ao criar um novo perfil, adicionar coluna e linha nesta tabela
2. Preencher `combines_with` e `excludes_with` no descriptor YAML do novo perfil
3. Executar `uv run pytest tests/test_smoke_composer.py -v` — o motor de composição valida os conflicts
4. Atualizar seção "Combinações válidas/inválidas" com novos exemplos
