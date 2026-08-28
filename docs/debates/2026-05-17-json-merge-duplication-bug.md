# Debate Técnico: Bug de Duplicação no Sistema de Merge JSON

**Data**: 17 de maio de 2026
**Projeto**: scaffold-project (Enterprise Scaffold Project Template)
**Branch**: 061-recovery-017-correction
**Bug ID**: Duplicação de arrays em `.vscode/extensions.json`
**Participantes**: Software Engineer Agent, Principal Software Engineer, DevOps Expert, Python MCP Server Expert

---

## 📋 Executive Summary

### Problema Identificado
Sistema de merge JSON está duplicando arrays em `.vscode/extensions.json`, causando taxa de duplicação de 100% (20/20 extensões duplicadas).

### Root Cause
**Problema Arquitetural**: `JSONMerger` genérico usa `deepmerge.always_merger.merge()` que faz **union de arrays** por padrão. Isso causa duplicação em QUALQUER arquivo JSON do projeto, não apenas VSCode.

**Contexto do Usuário**: JSON é o padrão para arquivos de configuração no projeto. A estratégia user-wins sem union deve ser universal para todos os JSONs.

### Impacto nos Arquivos
- ❌ **TODOS os arquivos JSON**: Potencialmente afetados pelo union de arrays
- ✅ `mcp.json`, `settings.json`: Protegidos por `VSCodeJSONMerger` (solução paliativa)
- ❌ `extensions.json`: **CONFIRMADO** - duplicação (não estava na whitelist)
- ❓ `package.json`, `tsconfig.json`, outros JSONs do projeto: Status desconhecido

### Evidências
- **Log de duplicação**: `tmp/evidencia/json_diif_20260517_1116.log`
- **Arquivo afetado**: `tmp/evidencia/extensions.json` (41 itens = 21 únicos)
- **Taxa de duplicação**: 100% (todos os 20 arrays afetados)
- **Padrão**: Primeira metade limpa, segunda metade duplicada exatamente

---

## 🔬 Análise Técnica por Agente

### 1️⃣ Software Engineer Agent — Análise do Bug

#### Código Problemático Identificado

**Localização**: `scripts/lib/json_merge.py` (linhas 376-382)

```python
class VSCodeJSONMerger:
    def can_merge(self, file_path: Path) -> bool:
        """Verifica se é mcp.json ou settings.json em .vscode/."""
        return (
            file_path.name in ["mcp.json", "settings.json"] and  # ❌ Lista incompleta!
            ".vscode" in file_path.parts
        )
```

#### Por que o Problema Afeta Todos os JSONs?

1. **Estratégia errada no merger base**: `JSONMerger` usa `deep_merge_json()` com union de arrays
2. **Solução paliativa inadequada**: `VSCodeJSONMerger` criado apenas para VSCode, mas problema é sistêmico
3. **JSON é padrão do projeto**: Usado em configs gerais (package.json, tsconfig.json, etc.), não só VSCode
4. **Falta de documentação**: Não há guia sobre a estratégia de merge universal esperada

#### Fluxo de Execução que Causa o Bug

```
Scaffold encontra .vscode/extensions.json existente
  ↓
Chain of Responsibility percorre mergers:
  VSCodeJSONMerger.can_merge() → False (não está na lista)
  WorkspaceMerger.can_merge() → False (não é .code-workspace)
  JSONMerger.can_merge() → True ✅ (qualquer .json)
  ↓
JSONMerger.merge() é chamado
  ↓
Usa deep_merge_json() com always_merger.merge()
  ↓
always_merger faz UNION de arrays
  ↓
💥 DUPLICAÇÃO
  Template: ["ext1", "ext2"]
  User:     ["ext1", "ext2"]
  Result:   ["ext1", "ext2", "ext1", "ext2"]  ❌
```

#### Code Smells Identificados

| Smell | Localização | Severidade | Impacto |
|-------|-------------|------------|---------|
| **Magic Strings** | Lista hardcoded em `can_merge()` | HIGH | Frágil, não escalável |
| **Implicit Assumptions** | Sem doc sobre merge strategies | MEDIUM | Dificulta manutenção |
| **Missing Tests** | Sem cobertura `.vscode/*` | HIGH | Bugs não detectados |
| **Chain of Responsibility Abuse** | Ordem de mergers crítica mas implícita | MEDIUM | Bugs sutis possíveis |

#### Proposta de Correção

**P0 — Solução Arquitetural (Deploy Imediato)**:
```python
# scripts/lib/json_merge.py

def deep_merge_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge com estratégia user-wins SEM union de arrays.

    Mudança arquitetural: JSON é padrão de configuração no projeto.
    Todos os JSONs devem usar user-wins sem duplicação de arrays.

    Estratégia:
    - Overlay (usuário) sobrescreve base (template)
    - Arrays substituídos completamente (NÃO faz union)
    - Objetos aninhados mergeados recursivamente
    - Chaves novas do template são adicionadas
    """
    return _merge_user_wins_recursive(base, overlay)

def _merge_user_wins_recursive(base: Dict, overlay: Dict) -> Dict:
    """Implementação do merge user-wins (movida de VSCodeJSONMerger)."""
    merged = {}

    # User wins: copiar tudo do overlay primeiro
    for key, overlay_value in overlay.items():
        base_value = base.get(key)
        if isinstance(overlay_value, dict) and isinstance(base_value, dict):
            merged[key] = _merge_user_wins_recursive(base_value, overlay_value)
        else:
            # Arrays e primitivos: overlay wins completamente
            merged[key] = overlay_value

    # Adicionar chaves novas do template
    for key, base_value in base.items():
        if key not in merged:
            merged[key] = base_value

    return merged
```

**Remover VSCodeJSONMerger**:
```python
# scripts/lib/file_merge.py
# ANTES: _MERGERS = [..., VSCodeJSONMerger(), JSONMerger(), ...]
# DEPOIS: _MERGERS = [..., JSONMerger(), ...]  # VSCodeJSONMerger removido (redundante)
```

---

### 2️⃣ Principal Software Engineer — Visão Arquitetural

#### Falha no Design Pattern Atual

**Pattern utilizado**: Chain of Responsibility modificado

```
Request → Handler1.can_merge() → Handler2.can_merge() → Handler3.can_merge()
            ↓ True                  ↓ False                ↓ True
         Handler1.merge()                              Handler3.merge()
```

**Problemas arquiteturais identificados**:

1. **Implicit Priority Order**: Ordem de registro é crítica mas não documentada
2. **Negative Matching**: `JSONMerger` aceita "qualquer .json" (catch-all perigoso)
3. **Insufficient Granularity**: Falta nível intermediário "arquivos VSCode genéricos"
4. **Configuration Drift**: Cada merger tem própria lista de arquivos (DRY violation)

#### Estratégia de Mitigação em 3 Camadas

**Layer 1: Immediate Fix (P0 — Hoje)**
- ✅ Adicionar `extensions.json` na whitelist
- ✅ Script de detecção de duplicações
- ✅ Testes unitários mínimos

**Layer 2: Architecture Hardening (P1 — Esta Semana)**
- 📋 Centralizar configuração em `constants.py`
- 📋 Docstrings detalhados em cada merger
- 📋 Matriz de decisão (arquivo → merger → estratégia)
- 📋 Validação de duplicação pós-merge

**Layer 3: Future-Proofing (P2 — Próximo Sprint)**
- 🔮 Migrar para Strategy Pattern com registry explícito
- 🔮 Pre-commit hook para detectar duplicações
- 🔮 DSL declarativo para merge rules

#### Recomendações de Longo Prazo

| Princípio | Implementação | Benefício |
|-----------|---------------|-----------|
| **Explicit over Implicit** | Registry pattern com prioridades documentadas | Comportamento previsível |
| **Fail-Fast** | Lançar exceção se múltiplos mergers aplicáveis | Detecta ambiguidades |
| **Configuration as Code** | YAML/JSON com merge rules | Extensível sem código |
| **Defense in Depth** | Validação pré + pós-merge | Catch erros cedo |

---

### 3️⃣ DevOps Expert — Impacto Operacional

#### Superfície de Ataque do Bug

**Arquivos potencialmente afetados**:

```bash
PROJETO INTEIRO (todos os JSONs):
├── .vscode/
│   ├── extensions.json     ❌ CONFIRMADO: 20 extensões duplicadas
│   ├── mcp.json            ✅ OK (protegido por VSCodeJSONMerger)
│   ├── settings.json       ✅ OK (protegido por VSCodeJSONMerger)
│   ├── launch.json         ❓ RISCO (usa JSONMerger genérico)
│   └── tasks.json          ❓ RISCO (usa JSONMerger genérico)
├── package.json            ❓ RISCO (configs npm, scripts, dependencies)
├── tsconfig.json           ❓ RISCO (compiler options, paths)
├── .eslintrc.json          ❓ RISCO (rules, extends)
├── jest.config.json        ❓ RISCO (test configs)
└── **/*.json               ❓ RISCO (qualquer JSON de configuração)
```

**Estimativa de impacto**:
- ✅ Arquivos protegidos: 2 (mcp.json, settings.json) - solução paliativa
- ❌ Arquivos afetados: 1 confirmado (extensions.json)
- ❓ Arquivos em risco: **TODOS OS DEMAIS JSONs do projeto**
- 🎯 **Problema sistêmico**: Requer mudança arquitetural, não whitelist

#### Estratégia de Remediação em 3 Fases

**Fase 1: Detecção (15min)**

Criar script `scripts/detect-json-duplications.py`:
- Escanear todos `.vscode/*.json`
- Detectar duplicações em arrays recursivamente
- Gerar relatório formatado + JSON para CI/CD
- Output: console + `duplications-report.json`

**Fase 2: Correção Automática (10min)**

Criar script `scripts/fix-json-duplications.py`:
- Remove duplicações preservando ordem
- Cria backup antes de modificar
- Valida JSON após correção
- Log detalhado de ações

**Fase 3: Prevenção (CI/CD Integration)**

- **Pre-commit hook**: Bloqueia commits com duplicações
- **GitHub Actions**: Valida PRs antes de merge
- **Monitoring**: Alerta se duplicações aparecerem

#### Automação de Monitoramento

**Pre-commit hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
for file in $(git diff --cached --name-only | grep '\.json$'); do
    python scripts/detect-json-duplications.py "$file" || exit 1
done
```

**GitHub Actions** (`.github/workflows/validate-json.yml`):
```yaml
on: [push, pull_request]
jobs:
  check-duplications:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan JSON duplications
        run: python scripts/detect-json-duplications.py
```

---

### 4️⃣ Python MCP Server Expert — Análise de Código Python

#### Problemas no Pattern `can_merge()`

**Anti-pattern identificado**: Brittle String Matching

```python
# ❌ FRÁGIL
def can_merge(self, file_path: Path) -> bool:
    return (
        file_path.name in ["mcp.json", "settings.json"] and  # Lista hardcoded
        ".vscode" in file_path.parts  # String matching frágil
    )
```

**Problemas**:
1. **Magic Strings**: Sem constantes, fácil esquecer ao adicionar arquivos
2. **No Type Validation**: Aceita qualquer `Path`, sem validação
3. **Implicit Contract**: Sem interface explícita, comportamento não verificável
4. **Poor Testability**: Difícil testar todos os casos

#### Solução com Type Hints e Validação

**Proposta P1 — Type-Safe Config**:
```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

class MergeStrategy(Enum):
    """Estratégias de merge disponíveis."""
    USER_WINS_NO_UNION = "user_wins_no_union"  # VSCode files
    DEEP_MERGE = "deep_merge"                   # Generic JSON
    WORKSPACE_SPECIALIZED = "workspace"         # .code-workspace

@dataclass(frozen=True)
class MergeConfig:
    """Configuração imutável de merge para um arquivo."""
    file_pattern: str
    strategy: MergeStrategy
    description: str
    examples: list[str]

MERGE_CONFIGS: dict[str, MergeConfig] = {
    "vscode_extensions": MergeConfig(
        file_pattern=".vscode/extensions.json",
        strategy=MergeStrategy.USER_WINS_NO_UNION,
        description="Extension recommendations - user list, no duplication",
        examples=["recommendations"]
    ),
    # ... outros configs
}

class Merger(Protocol):
    """Interface explícita para mergers."""
    def can_merge(self, file_path: Path) -> bool: ...
    def merge(self, existing: Path, template: str, interactive: bool = True) -> CreatedItem: ...
    @property
    def strategy(self) -> MergeStrategy: ...
```

#### Testing Strategy Proposta

**Cobertura mínima obrigatória**:

```python
# tests/test_json_merge_extensions.py

class TestExtensionsJsonMerge:
    def test_can_merge_extensions_json(self):
        """VSCodeJSONMerger reconhece extensions.json."""
        merger = VSCodeJSONMerger()
        assert merger.can_merge(Path(".vscode/extensions.json")) is True

    def test_no_array_union_in_recommendations(self, tmp_path):
        """Merge NÃO faz union de arrays."""
        # Template: ["ext1", "ext2"]
        # User: ["ext2", "ext3"]
        # Expected: ["ext2", "ext3"] (user wins, no union)
        ...

    def test_current_extensions_json_is_clean(self):
        """Arquivo atual não tem duplicações."""
        data = json.loads(Path(".vscode/extensions.json").read_text())
        counts = Counter(data["recommendations"])
        duplicates = [ext for ext, count in counts.items() if count > 1]
        assert len(duplicates) == 0
```

**Meta-teste para garantir sincronização**:
```python
def test_all_vscode_files_have_tests(self):
    """Garante que VSCODE_USER_WINS_FILES está completo."""
    tested_files = {"mcp.json", "settings.json", "extensions.json", ...}
    assert VSCODE_USER_WINS_FILES == tested_files
```

---

## 📝 Análise Consolidada — Consenso dos 4 Agentes

### Root Causes Identificados

| Causa | Categoria | Severidade | Consenso |
|-------|-----------|------------|----------|
| Lista hardcoded incompleta em `can_merge()` | Code Smell | **CRITICAL** | 4/4 ✅ |
| Falta de testes para arquivos VSCode | Testing Gap | **HIGH** | 4/4 ✅ |
| Ausência de documentação sobre strategies | Documentation | **MEDIUM** | 3/4 ✅ |
| Pattern Chain of Responsibility frágil | Architecture | **MEDIUM** | 2/4 ⚠️ |

### Consenso: Solução Arquitetural P0

**Todos os 4 agentes concordam** com mudança arquitetural:

1. ✅ Modificar `deep_merge_json()` para user-wins sem union (afeta TODOS os JSONs)
2. ✅ Remover `VSCodeJSONMerger` (redundante após mudança)
3. ✅ Criar script de detecção de duplicações em TODOS os JSONs do projeto
4. ✅ Limpar duplicações existentes em todos os JSONs afetados
5. ✅ Adicionar testes para comportamento universal do JSONMerger

### Divergências (Pontos de Debate)

| Questão | Software Eng | Principal Eng | DevOps | Python MCP |
|---------|--------------|---------------|---------|------------|
| Refatorar para Registry pattern? | 👍 P2 (futuro) | 👍 P1 (semana) | 🤷 Opcional | 👍 P1 (type-safe) |
| Adicionar launch.json/tasks.json? | 👍 Sim, agora | 👍 Sim + testes | ⚠️ Investigar | 👍 Sim + testes |
| CI/CD validation? | 🤷 Nice to have | 👍 Essencial | 👍 **CRÍTICO** | 👍 Pre-commit |

---

## 🎯 Conclusões e Recomendações

### Conclusão Principal

**Problema arquitetural identificado**: A solução inicial (`VSCodeJSONMerger`) foi uma **solução paliativa** para um problema sistêmico. JSON é o **padrão de configuração** do projeto, não apenas arquivos VSCode.

**Decisão arquitetural**: Modificar `JSONMerger` genérico para usar estratégia user-wins sem union como padrão para **TODOS os arquivos JSON**. Isso elimina:
- Necessidade de whitelists por arquivo
- `VSCodeJSONMerger` (redundante)
- Risco de novos JSONs caírem no merger errado
- Duplicações em package.json, tsconfig.json, etc.

### Recomendações Priorizadas

#### P0 — Crítico (Deploy Hoje — 45min)
1. ✅ Modificar `deep_merge_json()` para usar user-wins sem union (afeta TODOS os JSONs)
2. ✅ Remover `VSCodeJSONMerger` e import em `file_merge.py` (redundante)
3. ✅ Scan e limpeza de duplicações em TODOS os JSONs do projeto
4. ✅ Criar testes para `JSONMerger` genérico (user-wins behavior)
5. ✅ Commit com mudança arquitetural completa

#### P1 — Importante (Esta Semana — 2-3h)
1. 📋 Script `detect-json-duplications.py` (scan recursivo no projeto)
2. 📋 Script `fix-json-duplications.py` (correção automática)
3. 📋 Validação pós-merge em `save_json_formatted()` (detecta duplicações)
4. 📋 Documentação em `docs/guides/json-merge-strategy.md` (estratégia universal)
5. 📋 Exemplos de merge para diferentes tipos de JSON (package.json, tsconfig, etc.)

#### P2 — Desejável (Próximo Sprint — 3-4h)
1. 🔮 Pre-commit hook para validação
2. 🔮 GitHub Actions workflow
3. 🔮 Refatoração para Strategy Pattern (opcional, se consenso)
4. 🔮 Type-safe configuration com Protocols/dataclasses

### Próximos Passos Imediatos

1. **Executar plano P0** (ver arquivo `docs/planning/2026-05-17-json-merge-fix-action-plan.md`)
2. **Validar testes** passam após correção
3. **Commit com evidências** preservadas
4. **Planejar P1** para próxima sessão

---

## 📚 Referências

- **Commit relacionado**: `9595ac9` — fix(json-merge): Corrigir duplicação em mcp.json
- **Evidências**: `tmp/evidencia/json_diif_20260517_1116.log`
- **Código afetado**: `scripts/lib/json_merge.py` (classe VSCodeJSONMerger)
- **Sistema de merge**: Chain of Responsibility pattern em `scripts/lib/file_merge.py`
- **Biblioteca de merge**: `deepmerge.always_merger` (causa union de arrays)

---

**Fim do Debate Técnico**
