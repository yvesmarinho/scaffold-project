# 🔴 Relatório de Erros — `yvesmarinho/scaffold-project`

> **Data de geração**: 2026-03-31  
> **Repositório**: [yvesmarinho/scaffold-project](https://github.com/yvesmarinho/scaffold-project)  
> **Descrição**: estrutura básica para qualquer linguagem de programação  
> **Composição**: Python 84.3% · Shell 11.8% · Makefile 3.9%  
> **Gerado por**: GitHub Copilot (@copilot)

---

## 📊 Sumário Executivo

| Categoria | Quantidade | Severidade |
|-----------|-----------|------------|
| Erros de CI/CD (GitHub Actions) | 3 workflows distintos com falhas recorrentes | 🔴 CRÍTICO |
| Pull Requests de dependências pendentes | 13 PRs abertos | 🟠 ALTO |
| Dependências desatualizadas (breaking changes) | 5 pacotes com major bump | 🔴 CRÍTICO |
| Problemas de configuração (`pytest.ini`) | 1 erro estrutural | 🔴 CRÍTICO |
| Problemas em `security-scan.yml` | 2 jobs com falha permanente | 🟠 ALTO |
| Ausência de `pytest-cov` no pipeline | 2 workflows afetados | 🔴 CRÍTICO |

---

## 🔴 BLOCO 1 — Erros de CI/CD (GitHub Actions)

### 1.1 — Workflow: `Test Scaffold` (`test-scaffold.yml`)

**Status**: ❌ Falha recorrente em todos os runs  
**Run de referência**: [#23713994870](https://github.com/yvesmarinho/scaffold-project/actions/runs/23713994870)

**Erro capturado nos logs**:
```
ERROR: usage: pytest [options] [file_or_dir] [file_or_dir] [...]
pytest: error: unrecognized arguments:
  --cov=src
  --cov=scripts/lib
  --cov-report=html:htmlcov
  --cov-report=term-missing:skip-covered
  --cov-report=xml:coverage.xml
  --cov-fail-under=80

inifile: /home/runner/work/scaffold-project/scaffold-project/pytest.ini
Process completed with exit code 4.
```

**Causa raiz**: O `pytest.ini` define em `addopts` os flags `--cov=*` e `--cov-report=*` que exigem o plugin **`pytest-cov`**. O workflow `test-scaffold.yml` instala apenas `pytest rich pyyaml` — **`pytest-cov` não é instalado**. O pytest rejeita os argumentos desconhecidos e sai com código 4.

**Arquivo problemático**: `.github/workflows/test-scaffold.yml` linha 32  
**Arquivo de configuração**: `pytest.ini` linhas 14–19

**Correção necessária**:
```yaml
# .github/workflows/test-scaffold.yml — linha 32
# ANTES:
- name: Install test dependencies
  run: pip install pytest rich pyyaml

# DEPOIS:
- name: Install test dependencies
  run: pip install pytest pytest-cov rich pyyaml
```

**Alternativa mais segura**: Sobrescrever `addopts` na chamada para evitar dependência de `pytest-cov` nesse workflow específico:
```yaml
- name: Run full test suite
  run: pytest tests/ --tb=short -q --no-header -p no:cacheprovider --override-ini="addopts="
```

---

### 1.2 — Workflow: `CI — Template Test Suite` (`ci-template.yml`) — Job `lint`

**Status**: ❌ Falha recorrente  
**Run de referência**: [#23713994861](https://github.com/yvesmarinho/scaffold-project/actions/runs/23713994861)

**Erro capturado nos logs**:
```
Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'yaml'
Process completed with exit code 1.
```

**Causa raiz**: O job `lint` no `ci-template.yml` executa no step **"Check profile descriptors are valid YAML"** (linha 176–192) um inline Python que importa `yaml`. O step anterior instala apenas os módulos necessários para `py_compile` (nenhuma instalação de dependências). O módulo `pyyaml` **não é instalado** antes da execução desse step.

**Arquivo problemático**: `.github/workflows/ci-template.yml` — job `lint`, entre linhas 133–192

**Análise detalhada do job `lint`**:
```yaml
lint:
  name: Syntax check (py_compile)
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5   # Python 3.12
    # ⚠️ AUSENTE: nenhum step de "pip install" antes de usar yaml!
    - name: Check Python syntax        # py_compile: OK (stdlib only)
      run: python -m py_compile ...
    - name: Check profile descriptors are valid YAML
      run: python -c "import yaml ..."  # ❌ FALHA: yaml não instalado
```

**Correção necessária** — adicionar step de instalação antes do step de validação YAML:
```yaml
# Inserir após o step "Set up Python 3.12" no job lint:
- name: Install lint dependencies
  run: pip install pyyaml
```

---

### 1.3 — Workflow: `CI — Template Test Suite` — Job `test` (matriz)

**Status**: ❌ Mesmo problema do item 1.1, mas no workflow principal  
**Run de referência**: [#23712947361](https://github.com/yvesmarinho/scaffold-project/actions/runs/23712947361)

O job `test` do `ci-template.yml` instala `pytest rich pyyaml` (linha 60), mas **não instala `pytest-cov`**. O `pytest.ini` injeta automaticamente os flags `--cov` via `addopts`, causando a mesma falha.

**Correção necessária**:
```yaml
# .github/workflows/ci-template.yml — linha 60
# ANTES:
run: pip install pytest rich pyyaml

# DEPOIS:
run: pip install pytest pytest-cov rich pyyaml
```

---

### 1.4 — Workflow: `Security Scan` (`security-scan.yml`) — Jobs `gitleaks` e `trivy-docker`/`checkov`

**Status**: ❌ Falha recorrente  
**Runs de referência**: [#23748317221](https://github.com/yvesmarinho/scaffold-project/actions/runs/23748317221), [#23748273131](https://github.com/yvesmarinho/scaffold-project/actions/runs/23748273131)

**Problemas identificados no arquivo** `security-scan.yml`:

#### 1.4.1 — Job `gitleaks`: `GITLEAKS_LICENSE` ausente
```yaml
- name: Run Gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}  # ← Secret não configurado
```
O secret `GITLEAKS_LICENSE` não está definido no repositório. A action `gitleaks/gitleaks-action@v2` para repositórios **não-públicos** exige uma licença. O job falha silenciosamente por ausência da licença.

**Correção**: ou configurar o secret `GITLEAKS_LICENSE` nas configurações do repositório, ou alternar para a action em modo sem licença usando `gitleaks/gitleaks-action@v2` apenas com `GITHUB_TOKEN` (funciona para repositórios públicos), ou usar diretamente o binário `gitleaks` via `run:`.

#### 1.4.2 — Jobs `trivy-docker` e `checkov`: usam `@v3` de `codeql-action/upload-sarif`
```yaml
# Linha 138 e 161:
uses: github/codeql-action/upload-sarif@v3
```
O Dependabot abriu o PR [#12](https://github.com/yvesmarinho/scaffold-project/pull/12) para bump `codeql-action` de v3 para v4. A v3 está em processo de deprecação e pode ser a causa de warnings/falhas nos runs mais recentes.

#### 1.4.3 — Job `trufflehog`: usa `@main` (branch flutuante)
```yaml
uses: trufflesecurity/trufflehog@main
```
Usar `@main` é **má prática de segurança e estabilidade**: a action pode mudar a qualquer momento, quebrando o workflow ou introduzindo código não auditado. Deve-se usar uma versão pinada (ex: `@v3.82.0`).

#### 1.4.4 — Jobs `trivy-docker` e `checkov`: usam `@master` (branch flutuante)
```yaml
uses: aquasecurity/trivy-action@master       # linha 130
uses: bridgecrewio/checkov-action@master     # linha 152
```
Mesma má prática: branches flutuantes. Devem ser substituídos por versões pinadas com SHA ou tag semântica.

---

## 🟠 BLOCO 2 — Problema Estrutural no `pytest.ini`

**Arquivo**: [`pytest.ini`](https://github.com/yvesmarinho/scaffold-project/blob/master/pytest.ini)

### 2.1 — `addopts` inclui flags de `pytest-cov` sem garantia de instalação

```ini
addopts =
    --verbose
    --strict-markers
    --tb=short
    --color=yes
    --cov=src                              # ← Requer pytest-cov
    --cov=scripts/lib                      # ← Requer pytest-cov
    --cov-report=html:htmlcov              # ← Requer pytest-cov
    --cov-report=term-missing:skip-covered # ← Requer pytest-cov
    --cov-report=xml:coverage.xml          # ← Requer pytest-cov
    --cov-fail-under=80                    # ← Requer pytest-cov
    --maxfail=5
    --durations=10
```

**Problema**: Qualquer execução de `pytest` (local ou CI) sem `pytest-cov` instalado **falhará imediatamente** com `exit code 4`. Isso impede até execuções locais rápidas de testes unitários.

**Recomendação**: O `pytest.ini` deve declarar `pytest-cov` como dependência obrigatória de desenvolvimento. Alternativamente, mover os flags de cobertura para um arquivo `pyproject.toml` sob `[tool.pytest.ini_options]` com seção separada, ou usar um perfil de `addopts` condicional.

**Correção sugerida para o `pytest.ini`**:
```ini
# Separar os flags de cobertura — torná-los opcionais via Makefile/CI explícito
addopts =
    --verbose
    --strict-markers
    --tb=short
    --color=yes
    --maxfail=5
    --durations=10
```
E nas chamadas de CI onde a cobertura é desejada:
```bash
pytest tests/ --cov=src --cov=scripts/lib --cov-report=xml:coverage.xml --cov-fail-under=80
```

---

## 🟠 BLOCO 3 — Pull Requests Dependabot Pendentes (13 PRs)

Todos os PRs abaixo foram criados pelo **Dependabot** e estão sem revisão. Nenhum tem assignee ou reviewer designado.

### 3.1 — Breaking Changes (Major Version Bumps) — Revisão Manual Obrigatória

| PR | Pacote | De | Para | Escopo | Link |
|----|--------|-----|------|--------|------|
| #1 | `apache-airflow` | `2.9.3` | `3.1.7` | `data-pipeline-airflow` | [PR #1](https://github.com/yvesmarinho/scaffold-project/pull/1) |
| #9 | `apache-airflow` | `2.10.5` | `3.1.8` | `data-pipeline-airflow` | [PR #9](https://github.com/yvesmarinho/scaffold-project/pull/9) |
| #11 | `zod` | `3.25.76` | `4.3.6` | `typescript-next` | [PR #11](https://github.com/yvesmarinho/scaffold-project/pull/11) |
| #7 | `actions/checkout` | `v4` | `v6` | GitHub Actions global | [PR #7](https://github.com/yvesmarinho/scaffold-project/pull/7) |
| #6 | `actions/setup-python` | `v5` | `v6` | GitHub Actions global | [PR #6](https://github.com/yvesmarinho/scaffold-project/pull/6) |

> ⚠️ **`apache-airflow` 2.x → 3.x** é uma mudança **major com breaking changes extensivos**: API REST reescrita, DAG serialization changes, provider compatibility matrix alterada. Requer testes de regressão completos antes do merge.

> ⚠️ **`zod` 3.x → 4.x** possui breaking changes na API de validação. Ver [zod v4 migration guide](https://zod.dev/v4).

> ⚠️ **`actions/checkout@v6`** e **`actions/setup-python@v6`** ainda não têm documentação estável publicada — verificar release notes antes de mergear.

### 3.2 — Minor/Patch Bumps (Menor Risco)

| PR | Pacote | De | Para | Escopo | Link |
|----|--------|-----|------|--------|------|
| #2 | `apache-airflow-providers-common-sql` | `1.14.1` | `1.24.1` | `data-pipeline-airflow` | [PR #2](https://github.com/yvesmarinho/scaffold-project/pull/2) |
| #3 | `apache-airflow-providers-http` | `4.11.0` | `6.0.0` | `data-pipeline-airflow` | [PR #3](https://github.com/yvesmarinho/scaffold-project/pull/3) |
| #4 | `apache-airflow-providers-amazon` | `8.24.0` | `9.22.0` | `data-pipeline-airflow` | [PR #4](https://github.com/yvesmarinho/scaffold-project/pull/4) |
| #5 | `actions/cache` | `v4` | `v5` | GitHub Actions global | [PR #5](https://github.com/yvesmarinho/scaffold-project/pull/5) |
| #8 | `jest` | `29.7.0` | `30.3.0` | `typescript-next` | [PR #8](https://github.com/yvesmarinho/scaffold-project/pull/8) |
| #10 | `@types/jest` | `29.5.14` | `30.0.0` | `typescript-next` | [PR #10](https://github.com/yvesmarinho/scaffold-project/pull/10) |
| #12 | `github/codeql-action` | `v3` | `v4` | GitHub Actions — security | [PR #12](https://github.com/yvesmarinho/scaffold-project/pull/12) |
| #13 | `actions/upload-artifact` | `v4` | `v7` | GitHub Actions global | [PR #13](https://github.com/yvesmarinho/scaffold-project/pull/13) |

> ⚠️ **`apache-airflow-providers-http` 4.x → 6.x** é um salto major (pula v5). Verificar breaking changes.  
> ⚠️ **`actions/upload-artifact` v4 → v7** pula duas versões major. Verificar compatibilidade de `artifact-id` e `run-id` na API.

---

## 🔵 BLOCO 4 — Más Práticas de Segurança nos Workflows

### 4.1 — Actions com branches flutuantes (sem versão pinada)

| Arquivo | Action | Versão atual | Risco |
|---------|--------|-------------|-------|
| `security-scan.yml:38` | `trufflesecurity/trufflehog` | `@main` | 🔴 Supply chain attack |
| `security-scan.yml:130` | `aquasecurity/trivy-action` | `@master` | 🔴 Supply chain attack |
| `security-scan.yml:152` | `bridgecrewio/checkov-action` | `@master` | 🔴 Supply chain attack |

**Correção**: Substituir por versões pinadas com SHA completo (best practice OSSF/SLSA) ou com tag semântica:
```yaml
# Exemplo seguro:
uses: trufflesecurity/trufflehog@v3.82.6
uses: aquasecurity/trivy-action@0.28.0
uses: bridgecrewio/checkov-action@v12.2926.0
```

### 4.2 — `security-scan.yml` usa `actions/checkout@v4` e `actions/setup-python@v5` (desatualizados)

Enquanto os PRs #7 e #6 aguardam para bump dessas actions, o workflow de segurança ainda usa versões antigas. Paradoxalmente, o workflow de **segurança** está usando versões antigas de actions.

---

## 🔵 BLOCO 5 — Inconsistências de Configuração

### 5.1 — Redundância de Workflows: `test-scaffold.yml` vs `ci-template.yml`

Ambos os workflows fazem:
- Checkout do código
- Setup Python
- `pip install pytest rich pyyaml`
- `pytest tests/ --tb=short -q`

O `test-scaffold.yml` é um **subconjunto funcional** do `ci-template.yml`. Isso gera:
- Dupla execução nos mesmos eventos de push/PR
- Consumo desnecessário de minutos do GitHub Actions
- Manutenção duplicada

**Recomendação**: Avaliar se `test-scaffold.yml` pode ser removido e seus gatilhos absorvidos pelo `ci-template.yml`.

### 5.2 — `ci-template.yml` não dispara em `pull_request` sem filtro de branch

```yaml
on:
  pull_request:
    paths:
      - "scripts/**"
      ...
  push:
    branches:
      - main
      - master    # ← push tem filtro de branch
    paths: ...    # pull_request NÃO tem filtro de branch
```

`pull_request` dispara em **qualquer branch** com os paths especificados, enquanto `push` só dispara em `main`/`master`. Isso pode causar execuções inesperadas em branches de feature para PRs abertos.

### 5.3 — `security-scan.yml`: jobs condicionais podem nunca executar

Os jobs `bandit`, `safety`, `ansible-lint`, `trivy-docker` e `checkov` usam `hashFiles()` como condição. Se os arquivos relevantes não existirem **na raiz** (e não nos subdiretórios de template), os jobs são pulados — mas o workflow ainda é marcado como "falhou" por causa do job `gitleaks`.

---

## 📋 Plano de Ação — Priorização

### 🔴 P0 — Crítico (bloqueia CI — corrigir imediatamente)

| ID | Ação | Arquivo | Responsável |
|----|------|---------|-------------|
| FIX-01 | Adicionar `pytest-cov` no `pip install` do `test-scaffold.yml` | `.github/workflows/test-scaffold.yml:32` | Agente CI |
| FIX-02 | Adicionar `pytest-cov` no `pip install` do job `test` em `ci-template.yml` | `.github/workflows/ci-template.yml:60` | Agente CI |
| FIX-03 | Adicionar step `pip install pyyaml` no job `lint` de `ci-template.yml` | `.github/workflows/ci-template.yml:133` | Agente CI |

### 🟠 P1 — Alto (corrigir antes do próximo release)

| ID | Ação | Arquivo | Responsável |
|----|------|---------|-------------|
| FIX-04 | Resolver secret `GITLEAKS_LICENSE` ou migrar para modo sem licença | `security-scan.yml:26` + Repo Settings | DevOps |
| FIX-05 | Pinar versões de `trufflehog`, `trivy-action`, `checkov-action` | `security-scan.yml:38,130,152` | Agente Security |
| FIX-06 | Fazer merge do PR #12 (`codeql-action` v3→v4) | PR #12 | Agente CI |
| FIX-07 | Revisar e mergear PRs de providers Airflow (#2, #3, #4) | PRs #2,#3,#4 | Agente Python |

### 🔵 P2 — Médio (melhorias de qualidade)

| ID | Ação | Arquivo | Responsável |
|----|------|---------|-------------|
| IMP-01 | Remover flags `--cov` do `addopts` do `pytest.ini` e mover para Makefile/CI explícito | `pytest.ini` | Agente Python |
| IMP-02 | Avaliar remoção/consolidação do `test-scaffold.yml` | `.github/workflows/` | Agente CI |
| IMP-03 | Revisar e mergear PRs de major bump com testes de regressão (#1, #9, #11, #7, #6) | PRs #1,#9,#11,#7,#6 | Agente Python + Agente TS |
| IMP-04 | Mergear PRs de patch/minor de menor risco (#5, #8, #10, #13) | PRs #5,#8,#10,#13 | Agente CI |

---

## 🗂️ Referências Diretas

| Recurso | Link |
|---------|------|
| Actions — todos os runs | [github.com/…/actions](https://github.com/yvesmarinho/scaffold-project/actions) |
| `pytest.ini` | [blob/master/pytest.ini](https://github.com/yvesmarinho/scaffold-project/blob/master/pytest.ini) |
| `ci-template.yml` | [blob/master/.github/workflows/ci-template.yml](https://github.com/yvesmarinho/scaffold-project/blob/master/.github/workflows/ci-template.yml) |
| `test-scaffold.yml` | [blob/master/.github/workflows/test-scaffold.yml](https://github.com/yvesmarinho/scaffold-project/blob/master/.github/workflows/test-scaffold.yml) |
| `security-scan.yml` | [blob/master/.github/workflows/security-scan.yml](https://github.com/yvesmarinho/scaffold-project/blob/master/.github/workflows/security-scan.yml) |
| Todos os PRs abertos | [github.com/…/pulls](https://github.com/yvesmarinho/scaffold-project/pulls) |

---

*Relatório gerado automaticamente por GitHub Copilot em 2026-03-31. Total de 58 workflow runs analisados (30 exibidos na primeira página). Para runs adicionais: [ver no GitHub](https://github.com/yvesmarinho/scaffold-project/actions?query=event%3Apush+is%3Afailure).*