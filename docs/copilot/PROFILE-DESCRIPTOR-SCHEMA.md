# Profile Descriptor Schema — Contrato Formal de Perfis

> **Versão do schema**: 1.1.0
> **Criado em**: 2026-03-07 (IMP-19a)
> **Atualizado em**: 2026-03-14 (IMP-41 — `security.enforces` estruturado)
> **Status**: Estável — perfis novos DEVEM seguir este contrato antes de serem integrados ao scaffold

---

## Visão Geral

Um **Profile Descriptor** é um arquivo YAML que descreve de forma declarativa tudo que um perfil de domínio gera, requer, exclui e combina. O contrato separa a **intenção** (o que um perfil representa) da **implementação** (como o `scaffold.py` gera os arquivos).

### Por que isso importa

| Sem descriptor | Com descriptor |
|----------------|----------------|
| "O que esse perfil gera?" → ler código | `generates.files` lista tudo |
| Conflitos descobertos em tempo de execução | `excludes_with` declarado e validado antes |
| Combos de perfis testados manualmente | `combines_with` + testes CI automáticos |
| Segurança ad-hoc por perfil | `security.enforces` auditável |
| Versão de um perfil: uma variável | `VERSION` + `LAST_TESTED_DATE` rastreados |

---

## Schema YAML (anotado)

```yaml
# ============================================================
# Profile Descriptor — Enterprise Scaffold Project Template
# Schema versão 1.0.0
# ============================================================

# ------------------------------------------------------------------
# Identificação
# ------------------------------------------------------------------
name: string                  # Slug único, kebab-case. Ex: devops-programming
                               # Deve coincidir com o nome do arquivo (sem .yaml)

description: string            # 1 frase descrevendo o perfil e seu propósito

VERSION: string                # Semver do descriptor. Ex: "1.0.0"
                               # Incrementar MINOR ao adicionar campos opcionais
                               # Incrementar MAJOR ao remover/renomear campos obrigatórios

LAST_TESTED_DATE: date         # ISO 8601 (YYYY-MM-DD). Atualizar ao rodar smoke tests.
                               # CI alerta se data > 90 dias (staleness check)

# ------------------------------------------------------------------
# Dependências
# ------------------------------------------------------------------
requires:                      # Lista de pré-condições que devem existir no projeto.
  - string                     # Formato livre ou chave:valor. Exemplos:
                               #   "python >= 3.11"
                               #   "uv installed"
                               #   "docker installed"
                               #   "github_repo: not null"
                               # Usado para: validação futura no scaffold.py e docs

# ------------------------------------------------------------------
# Artefatos gerados
# ------------------------------------------------------------------
generates:
  files:                       # Arquivos criados ou copiados por este perfil
    - path: string             # Caminho relativo ao projeto alvo. Ex: .github/prompts/domain/devops-programming.prompt.md
      source: string           # Arquivo fonte em .copilot-shared/ ou template inline
      description: string      # O que esse arquivo faz (1 frase)
      required: bool           # Se false: gerado apenas se condição satisfeita (ver 'when')
      when: string | null      # Condição opcional. Ex: "language == python"

  patches:                     # Modificações em arquivos já existentes (não cria, edita)
    - file: string             # Arquivo alvo no projeto. Ex: .gitignore
      description: string      # O que é adicionado/modificado (1 frase)
      operation: string        # "append" | "prepend" | "replace_section"

# ------------------------------------------------------------------
# Compatibilidade entre perfis
# ------------------------------------------------------------------
excludes_with:                 # Perfis que NÃO podem ser usados em conjunto com este
  - string                     # Ex: - devops-infrastructure (conflito de convenções de pasta)
                               # scaffold.py deve rejeitar a combinação com mensagem clara

combines_with:                 # Perfis testados e aprovados para uso conjunto
  - name: string               # Nome do perfil
    notes: string              # Observações sobre a combinação. Ex: "security é sempre transversal"

# ------------------------------------------------------------------
# Segurança
# ------------------------------------------------------------------
security:
  enforces:                    # Controles de segurança que este perfil exige/configura
    - control: string          # Identificador do controle. Ex: "OWASP-A06", "CWE-312", "CC6.1"
      description: string      # Descrição do controle (1 frase). Ex: "bandit -r src/ via 'make security'"
      tool: string             # Ferramenta que implementa o controle. Ex: "bandit", "gitleaks", "manual"
      severity: string         # "critical" | "high" | "medium" | "low"
      automated: bool          # true = executado automaticamente (CI/pre-commit); false = manual

# ------------------------------------------------------------------
# Metadados extras (opcionais)
# ------------------------------------------------------------------
tags:                          # Lista de tags para filtragem e documentação
  - string                     # Exemplos: python, testing, fastapi, layer2, transversal

layer: string                  # "core" | "layer2" | "transversal"
                               # core = perfis base (programming/infrastructure/analysis)
                               # layer2 = perfis específicos (python-fastapi, python-flask)
                               # transversal = cross-cutting (security)

maintainer: string             # Nome/handle do mantenedor deste descriptor
```

---

## Campos Obrigatórios vs. Opcionais

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `name` | ✅ | Identificador único, deve coincidir com nome do arquivo |
| `description` | ✅ | 1 frase |
| `VERSION` | ✅ | Semver do descriptor |
| `LAST_TESTED_DATE` | ✅ | Data do último smoke test (ISO 8601) |
| `requires` | ✅ | Pode ser lista vazia `[]` se sem pré-requisitos |
| `generates.files` | ✅ | Pode ser lista vazia se perfil só faz patches |
| `generates.patches` | ✅ | Pode ser lista vazia se perfil não edita arquivos |
| `excludes_with` | ✅ | Pode ser lista vazia |
| `combines_with` | ✅ | Pode ser lista vazia |
| `security.enforces` | ✅ | Pode ser lista vazia — mas deve ser preenchido para perfis com deps |
| `tags` | Opcional | Facilita `--list-profiles` (IMP-19b) |
| `layer` | Opcional | Até IMP-19b ser implementado |
| `maintainer` | Opcional | |

---

## Regras de Versionamento

| Mudança | Ação |
|---------|------|
| Adicionar campo opcional | Incrementar `MINOR` |
| Adicionar campo obrigatório | Incrementar `MAJOR` |
| Remover ou renomear campo | Incrementar `MAJOR` |
| Adicionar arquivo em `generates.files` | Incrementar `MINOR` + atualizar `LAST_TESTED_DATE` |
| Corrigir bug sem alteração de campos | Incrementar `PATCH` |

---

## Integração com scaffold.py (roadmap)

O `scaffold.py` atual **não lê** os descriptors ainda — eles servem como contrato documental e baseline para IMP-19b e além. A integração incremental planejada é:

| IMP | O que integra |
|-----|---------------|
| **IMP-19b** | `--list-profiles` lê `name` + `description` + `tags` dos descriptors |
| **IMP-24** | Validação de `excludes_with` antes de gerar |
| **IMP-25** | `LAST_TESTED_DATE` verificado no CI (staleness alert) |
| **[futuro]** | Motor de geração lê `generates.files` em vez de código hardcoded |

---

## Localização dos Descriptors

```
profile-descriptors/
├── devops-programming.yaml      ← perfil de referência (core)
├── devops-infrastructure.yaml
├── devops-analysis.yaml
├── devops-security.yaml
├── python-fastapi.yaml          ← [IMP-20] a criar
├── python-flask.yaml            ← [IMP-20b] a criar
└── README.md                    ← aponta para este schema
```

---

## Referências

- [IMP-19 Debate](../SESSIONS/2026-03-07/IMP-19-DEBATE.md) — origem desta proposta
- [docs/TODO.md](../TODO.md) — roadmap de implementação
- Descriptor de referência: [profile-descriptors/devops-programming.yaml](../../profile-descriptors/devops-programming.yaml)
