# Domínio: Analysis — Guia Humano

> Documentação de referência para o domínio **analysis** do Enterprise Scaffold Project Template.
> Para o perfil machine-readable do Copilot, veja: [`.github/prompts/domain/devops-analysis.prompt.md`](../../.github/prompts/domain/devops-analysis.prompt.md)

**Última atualização**: 2026-03-07
**Perfis Layer 2 disponíveis**: *(pendente — IMP-26 data-pipeline-airflow, data-warehouse-dbt)*
**Status**: core configurado, perfis layer2 em backlog (P3)

---

## 1. O que é este domínio?

O domínio `analysis` cobre todo trabalho cujo **artefato central é conhecimento estruturado** derivado de dados, logs, métricas ou código. A saída é uma decisão documentada, um diagnóstico, um relatório ou um pipeline reproduzível.

Exemplos de trabalho neste domínio:
- Investigar incidente de produção (análise de logs, traces, métricas)
- Explorar dataset para entender padrão de comportamento de usuários
- Construir pipeline ETL/ELT (Airflow, dbt, Spark)
- Criar dashboard de métricas operacionais
- Escrever jupyter notebook com análise exploratória
- Auditar qualidade de dados em warehouse (dbt tests)
- Análise de capacidade e sizing de infraestrutura

**Não** é domínio analysis:
- Implementar feature na API → domínio `programming`
- Provisionar o cluster de dados → domínio `infrastructure`
- Criar playbook Ansible → domínio `infrastructure`

---

## 2. Princípio fundamental — Reprodutibilidade

> **Regra de ouro**: toda análise deve ser reproduzível por outro engenheiro a partir do zero.

| Requisito | Implementação |
|-----------|---------------|
| Seed fixo em modelos | `random.seed(42)`, `np.random.seed(42)`, `set_seed(42)` |
| Versões fixadas | `requirements.txt` com `==` ou `uv.lock` |
| Dados não commitados | `.data/` no `.gitignore` — usar path relativo documentado |
| Notebooks limpos | `jupyter nbconvert --ClearOutputPreprocessor.enabled=True --to notebook` antes do commit |
| Parâmetros documentados | `## Parâmetros` no topo do notebook com todos os valores alteráveis |

---

## 3. Quando escolher este domínio no scaffold

Ao executar `uv run scripts/scaffold.py`, escolha `analysis` quando o projeto principal for análise de dados ou investigação:

```
Domínio → analysis
```

O scaffold vai configurar:
- Regras Copilot com foco em: reprodutibilidade, separação exploração/entregáveis, dados gitignored
- Domain profile: `devops-analysis.prompt.md`
- Estrutura de pastas: `notebooks/`, `src/`, `data/` (gitignored), `reports/`
- `.gitignore` com entradas: `.data/`, `*.csv`, `*.parquet`, `*.pkl`, `data/`

---

## 4. Estrutura de pastas para projetos analysis

```
projeto/
├── notebooks/
│   ├── exploration/         # Exploração ad-hoc (não precisa estar limpo)
│   └── reports/             # Entregáveis (devem estar limpos — sem outputs)
├── src/                     # Funções reutilizáveis (não duplicar entre notebooks)
│   ├── data/                # Loaders, transformações
│   ├── features/            # Engenharia de features
│   └── models/              # Pipelines de modelo
├── tests/                   # Testes unitários das funções em src/
├── .data/                   # Dados brutos (gitignored)
│   ├── raw/
│   └── processed/
├── reports/                 # Outputs exportados (PDF, HTML, imagens)
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── DATA-DICTIONARY.md   # Dicionário de dados (manter atualizado)
├── pyproject.toml           # Gerenciado com uv
├── Makefile
└── .env.example             # DATABASE_URL, DATA_PATH, etc.
```

---

## 5. Perfis Layer 2 planejados

| Perfil | Status | IMP | O que gera |
|--------|--------|-----|-----------|
| `data-pipeline-airflow` | 🔜 backlog | IMP-26 | DAGs Airflow, operadores, testes de pipeline |
| `data-warehouse-dbt` | 🔜 backlog | IMP-26 | modelos dbt, testes, documentação de schema |

Até os perfis layer2 estarem disponíveis, o domínio `analysis` provê apenas o perfil core (`devops-analysis.prompt.md`).

---

## 6. Convenções universais do domínio

### Notebooks

```python
# Topo de todo notebook — bloco de parâmetros
# ============================================================
# Parâmetros
# ============================================================
DATA_PATH = ".data/raw/dataset.csv"
RANDOM_SEED = 42
TARGET_COLUMN = "churn"
TEST_SIZE = 0.2
# ============================================================

import pandas as pd
import numpy as np
np.random.seed(RANDOM_SEED)
```

### Separação de responsabilidades

```
notebooks/exploration/  → exploração livre, pode ter saídas, não é entregável
notebooks/reports/      → entregável, sem saídas commitadas, código limpo
src/                    → funções reutilizadas em ≥ 2 notebooks vão aqui
```

### Funções em src/ com testes

```python
# src/features/temporal.py
def extract_day_of_week(df: pd.DataFrame, col: str) -> pd.Series:
    """Extrai dia da semana de uma coluna datetime."""
    return df[col].dt.dayofweek

# tests/test_temporal.py
def test_extract_day_of_week_monday():
    df = pd.DataFrame({"date": pd.to_datetime(["2026-03-02"])})  # segunda
    result = extract_day_of_week(df, "date")
    assert result.iloc[0] == 0
```

### Dados — Regras P0

- **NUNCA** commitar dados reais ou com PII (`*.csv`, `*.parquet`, `*.pkl` gitignored)
- Se dado é público e pequeno (<5MB), pode ser commitado em `tests/fixtures/`
- Dados de produção com PII: anonimizar antes de qualquer análise local
- Conexões com banco: via variável de ambiente `DATABASE_URL` (nunca hardcoded)

### Incidente — Análise estruturada

Para análise de incidentes, seguir estrutura:

```markdown
## Incidente [ID] — [data]

### Linha do tempo (UTC)
- HH:MM — [evento]

### Causa raiz
[descrição]

### Impacto
[SLO afetado, usuários, duração]

### Ações imediatas tomadas
[o que foi feito para mitigar]

### Ações preventivas (post-mortem)
- [ ] [ação] — responsável — prazo
```

---

## 7. Fluxo de trabalho típico

```
# Exploração
1. scaffold.py → cria projeto analysis
2. uv add jupyter pandas numpy scikit-learn
3. make dev → abre jupyter lab
4. notebooks/exploration/ → análise ad-hoc

# Pipeline reproduzível
5. mover funções validadas para src/
6. escrever testes em tests/
7. notebooks/reports/ → notebook limpo, reproduzível
8. make lint format test → validar antes de PR

# Produção
9. (futuro) --compose data-pipeline-airflow → DAGs Airflow
```

---

## 8. Checklist de qualidade para análises

Antes de compartilhar qualquer análise (PR, apresentação, relatório):

- [ ] Notebook sem outputs commitados (executar `make clean-notebooks` ou equivalente)
- [ ] Seed fixo declarado no topo do notebook
- [ ] Versões de todas as dependências fixadas (`uv.lock` commitado)
- [ ] Sem PII nos dados de exemplo ou outputs
- [ ] Funções reutilizadas estão em `src/` com testes
- [ ] `DATA-DICTIONARY.md` atualizado com novos campos usados
- [ ] Análise pode ser reproduzida com `make reproduce` ou instruções no README

---

## 9. Referências

- [devops-analysis.prompt.md](../../.github/prompts/domain/devops-analysis.prompt.md) — perfil machine-readable
- [DOMAIN-PROFILES-DECISIONS.md](DOMAIN-PROFILES-DECISIONS.md) — decisões de arquitetura
- [COMPATIBILITY-MATRIX.md](../COMPATIBILITY-MATRIX.md) — compatibilidade com perfis layer2
