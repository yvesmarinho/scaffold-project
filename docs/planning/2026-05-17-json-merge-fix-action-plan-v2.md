# Plano de Ação: Estratégia Universal de Merge JSON

**Data de Criação**: 17 de maio de 2026 (v2.0 - Revisão Arquitetural)
**Projeto**: scaffold-project
**Branch**: 061-recovery-017-correction (NÃO criar nova branch)
**Mudança**: De correção pontual → Mudança arquitetural universal
**Debate Técnico**: [docs/debates/2026-05-17-json-merge-duplication-bug.md](../debates/2026-05-17-json-merge-duplication-bug.md)
**Documentação**: [docs/guides/json-merge-strategy.md](../guides/json-merge-strategy.md)

---

## 📋 Sumário Executivo

### Problema Arquitetural
Sistema de merge JSON fazendo **union de arrays** por padrão (via `deepmerge.always_merger`), causando duplicações em **TODOS os arquivos JSON do projeto**, não apenas VSCode.

### Root Cause
`JSONMerger` genérico usa estratégia inadequada para arquivos de configuração. Solução paliativa anterior (`VSCodeJSONMerger`) foi limitada demais (apenas 2 arquivos).

### Contexto do Usuário
> "JSON nos meus projetos é padrão para arquivos de configuração. Quero que o merge de JSON não fique limitado aos arquivos do VSCode."

### Solução Arquitetural
Modificar `deep_merge_json()` para usar **user-wins sem union** como padrão UNIVERSAL para todos os JSONs. Remover `VSCodeJSONMerger` (redundante).

### Critérios de Sucesso
- ✅ `deep_merge_json()` implementa user-wins sem union
- ✅ `VSCodeJSONMerger` removido (redundante)
- ✅ **Todos** os JSONs do projeto sem duplicações
- ✅ Testes abrangentes (não apenas VSCode)
- ✅ Documentação da estratégia universal

---

## 🎯 Objetivo

**Implementar estratégia universal de merge JSON** aplicando user-wins sem union para **TODOS os arquivos JSON do projeto**.

**Mudança de Escopo**:
- ❌ **ANTES**: Adicionar `extensions.json` à whitelist de `VSCodeJSONMerger`
- ✅ **AGORA**: Modificar `JSONMerger` para aplicar user-wins universalmente

**Filosofia**:
> JSON = Configuração = User Wins

Arrays em configs são customizações do usuário, não listas a serem concatenadas com template.

---

## 🚀 Phase 1: Mudança Arquitetural (P0)

**Prioridade**: CRÍTICA
**Duração estimada**: 45 minutos
**Deploy**: Hoje (2026-05-17)
**Bloqueador**: Não

---

### Task 1.1: Modificar `deep_merge_json()` para User-Wins Universal

**Arquivo**: `scripts/lib/json_merge.py`
**Função**: `deep_merge_json()`
**Mudança**: Substituir `always_merger.merge()` por implementação user-wins

#### Implementação

```python
# scripts/lib/json_merge.py

def deep_merge_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge com estratégia user-wins SEM union de arrays.

    Mudança arquitetural (v2.0): JSON é padrão de configuração no projeto.
    Todos os JSONs devem usar user-wins sem duplicação de arrays.

    Estratégia:
    - Overlay (usuário) sobrescreve base (template)
    - Arrays substituídos completamente (NÃO faz union)
    - Objetos aninhados mergeados recursivamente
    - Chaves novas do template são adicionadas

    Histórico:
    - v1.0: Usava always_merger.merge() (union de arrays) ❌ BUG
    - v2.0: Implementa user-wins sem union ✅ FIX ARQUITETURAL

    Args:
        base: Template (upstream)
        overlay: Usuário (customizações)

    Returns:
        Dicionário mergeado com estratégia user-wins
    """
    return _merge_user_wins_recursive(base, overlay)


def _merge_user_wins_recursive(base: Dict, overlay: Dict) -> Dict:
    """
    Implementação do merge user-wins recursivo.

    Algoritmo:
    1. Copiar todos valores do overlay (user wins)
    2. Para objetos aninhados: merge recursivo
    3. Adicionar chaves novas do base que não existem no overlay

    Comportamento por tipo:
    - Primitivos: overlay wins
    - Arrays: overlay wins (NÃO faz union)
    - Objects: merge recursivo

    Args:
        base: Template
        overlay: Usuário

    Returns:
        Dicionário mergeado
    """
    merged = {}

    # Passo 1: User wins - copiar tudo do overlay
    for key, overlay_value in overlay.items():
        base_value = base.get(key)

        # Se ambos são dicts, merge recursivo
        if isinstance(overlay_value, dict) and isinstance(base_value, dict):
            merged[key] = _merge_user_wins_recursive(base_value, overlay_value)
        else:
            # Primitivos e arrays: user wins completamente
            merged[key] = overlay_value

    # Passo 2: Adicionar chaves novas do template
    for key, base_value in base.items():
        if key not in merged:
            merged[key] = base_value

    return merged
```

#### Critérios de Aceite
- ✅ `deep_merge_json()` implementa user-wins sem union
- ✅ Arrays do overlay substituem base completamente
- ✅ Objetos aninhados mergeados recursivamente
- ✅ Chaves novas do template adicionadas
- ✅ Docstring completa com histórico de mudanças

#### Validação
```python
# Teste rápido
base = {"items": [1, 2, 3], "config": {"a": 1}}
overlay = {"items": [4, 5], "config": {"b": 2}}

result = deep_merge_json(base, overlay)

assert result["items"] == [4, 5], "Array deve ser substituído, não concatenado"
assert result["config"] == {"a": 1, "b": 2}, "Objetos devem mergear"
print("✅ deep_merge_json() funcionando")
```

---

### Task 1.2: Remover `VSCodeJSONMerger` (Redundante)

**Arquivos afetados**:
- `scripts/lib/json_merge.py`: Remover classe `VSCodeJSONMerger`
- `scripts/lib/file_merge.py`: Remover import e registro

#### Implementação

##### 1.2.1: Remover classe em `json_merge.py`

```python
# scripts/lib/json_merge.py

# ❌ REMOVER COMPLETAMENTE (linhas 365-511):
# class VSCodeJSONMerger:
#     ...
#     def _merge_user_wins(self, base, overlay):
#         ...

# ✅ Código movido para _merge_user_wins_recursive() usada por deep_merge_json()
```

**Linhas removidas**: ~146 linhas (365-511)

##### 1.2.2: Remover import em `file_merge.py`

```python
# scripts/lib/file_merge.py

# ❌ ANTES:
from .json_merge import JSONMerger, WorkspaceMerger, VSCodeJSONMerger

# ✅ DEPOIS:
from .json_merge import JSONMerger, WorkspaceMerger
```

##### 1.2.3: Remover registro em `file_merge.py`

```python
# scripts/lib/file_merge.py

# ❌ ANTES:
_MERGERS = [
    WorkspaceMerger(),
    VSCodeJSONMerger(),  # ❌ REMOVER
    JSONMerger(),
    MarkdownMerger(),
    # ...
]

# ✅ DEPOIS:
_MERGERS = [
    WorkspaceMerger(),
    JSONMerger(),        # Agora universal (user-wins para todos)
    MarkdownMerger(),
    # ...
]
```

#### Critérios de Aceite
- ✅ Classe `VSCodeJSONMerger` removida completamente
- ✅ Import removido em `file_merge.py`
- ✅ Registro removido da lista `_MERGERS`
- ✅ Sem erros de import ou referências quebradas
- ✅ `JSONMerger` agora é merger universal para todos JSONs

#### Validação
```bash
# Verificar imports
python -c "from scripts.lib.file_merge import _MERGERS; print([type(m).__name__ for m in _MERGERS])"
# Saída esperada: ['WorkspaceMerger', 'JSONMerger', 'MarkdownMerger', ...]
# NÃO deve conter 'VSCodeJSONMerger'

# Verificar que json_merge não exporta VSCodeJSONMerger
python -c "from scripts.lib.json_merge import VSCodeJSONMerger" 2>&1 | grep ImportError
# Saída esperada: ImportError: cannot import name 'VSCodeJSONMerger'
```

---

### Task 1.3: Scan e Limpeza de Duplicações em Todos os JSONs

**Escopo**: **Todos** os arquivos `.json` do projeto (não apenas `.vscode/`)

**Ferramenta**: `scripts/tmp/json_diff_visual.py` (análise de duplicações)

#### 1.3.1: Scan de Duplicações

```bash
# Listar todos JSONs do projeto
find . -name "*.json" -not -path "*/node_modules/*" -not -path "*/.git/*" > /tmp/json-files.txt

# Analisar cada arquivo
while read -r file; do
    echo "=== $file ==="
    python scripts/tmp/json_diff_visual.py "$file" "$file" | grep -A 10 "Análise de Duplicações"
done < /tmp/json-files.txt > /tmp/json-duplications-scan.log

# Revisar resultados
cat /tmp/json-duplications-scan.log
```

#### 1.3.2: Limpeza de Duplicações

```python
# scripts/tmp/fix-json-duplications.py (CRIAR)

import json
from pathlib import Path
from collections import Counter
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def remove_duplicates_from_arrays(data):
    """Remove duplicações em arrays, preservando ordem da primeira ocorrência."""
    if isinstance(data, dict):
        return {k: remove_duplicates_from_arrays(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Preservar ordem: primeira ocorrência
        seen = set()
        unique = []
        for item in data:
            # Usar JSON string como chave (funciona para primitivos e objetos)
            key = json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else item
            if key not in seen:
                seen.add(key)
                unique.append(remove_duplicates_from_arrays(item))
        return unique
    else:
        return data


def fix_json_file(file_path: Path) -> bool:
    """Remove duplicações de um arquivo JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Backup
        backup = file_path.with_suffix(file_path.suffix + ".backup")
        with open(backup, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Fix
        fixed = remove_duplicates_from_arrays(data)

        # Salvar se mudou
        if json.dumps(fixed, sort_keys=True) != json.dumps(data, sort_keys=True):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(fixed, f, indent=2, ensure_ascii=False)
                f.write("\n")
            log.info(f"✅ Fixed: {file_path} (backup: {backup.name})")
            return True
        else:
            backup.unlink()  # Sem mudanças, remover backup
            log.info(f"✨ OK: {file_path} (sem duplicações)")
            return False

    except Exception as e:
        log.error(f"❌ Error in {file_path}: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Aceitar arquivo ou diretório
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    if target.is_file():
        files = [target]
    else:
        files = list(target.rglob("*.json"))
        files = [f for f in files if ".git" not in f.parts and "node_modules" not in f.parts]

    log.info(f"🔍 Scanning {len(files)} JSON files...")

    fixed_count = 0
    for file in files:
        if fix_json_file(file):
            fixed_count += 1

    log.info(f"✅ Completed: {fixed_count} files fixed, {len(files)-fixed_count} already clean")
```

#### Executar Limpeza

```bash
# Limpar TODOS os JSONs do projeto
python scripts/tmp/fix-json-duplications.py .

# Revisar mudanças
git status
git diff .vscode/extensions.json package.json tsconfig.json
```

#### Critérios de Aceite
- ✅ Scan detecta TODOS os JSONs com duplicações
- ✅ Script remove duplicações preservando ordem
- ✅ Backup criado antes de modificar
- ✅ Log mostra files fixed vs already clean
- ✅ Validação: nenhuma duplicação remanescente

---

### Task 1.4: Criar Testes Abrangentes para JSONMerger

**Arquivo**: `tests/test_json_merge_universal.py` (CRIAR)

**Cobertura**:
- ✅ Arrays substituídos (não concatenados)
- ✅ Objetos aninhados mergeados
- ✅ Chaves novas do template adicionadas
- ✅ Diferentes tipos de JSON (extensions, mcp, package, tsconfig)

#### Implementação

```python
# tests/test_json_merge_universal.py

import pytest
from scripts.lib.json_merge import deep_merge_json, JSONMerger
from pathlib import Path


class TestDeepMergeJsonUserWins:
    """Testa estratégia user-wins universal para merge JSON."""

    def test_arrays_are_replaced_not_merged(self):
        """Arrays do usuário substituem template completamente."""
        base = {"items": [1, 2, 3]}
        overlay = {"items": [4, 5]}

        result = deep_merge_json(base, overlay)

        assert result["items"] == [4, 5], \
            "Array deve ser substituído, NÃO concatenado"
        assert result["items"] != [1, 2, 3, 4, 5], \
            "NÃO deve fazer union de arrays"

    def test_nested_objects_are_merged(self):
        """Objetos aninhados fazem merge recursivo."""
        base = {"config": {"a": 1, "b": 2}}
        overlay = {"config": {"b": 3, "c": 4}}

        result = deep_merge_json(base, overlay)

        assert result == {"config": {"a": 1, "b": 3, "c": 4}}

    def test_new_template_keys_are_added(self):
        """Chaves novas do template são adicionadas."""
        base = {"new_key": "new_value", "nested": {"new": "data"}}
        overlay = {"existing": "value"}

        result = deep_merge_json(base, overlay)

        assert "new_key" in result
        assert "existing" in result
        assert result["nested"] == {"new": "data"}

    def test_user_values_override_template(self):
        """Valores primitivos do usuário sobrescrevem template."""
        base = {"version": "1.0.0", "enabled": True}
        overlay = {"version": "2.0.0"}

        result = deep_merge_json(base, overlay)

        assert result["version"] == "2.0.0"
        assert result["enabled"] is True


class TestJSONMergerUniversal:
    """Testa JSONMerger aplicando user-wins para TODOS os JSONs."""

    def test_accepts_vscode_extensions_json(self):
        """JSONMerger aceita extensions.json."""
        merger = JSONMerger()
        path = Path(".vscode/extensions.json")

        assert merger.can_merge(path) is True

    def test_accepts_vscode_mcp_json(self):
        """JSONMerger aceita mcp.json."""
        merger = JSONMerger()
        path = Path(".vscode/mcp.json")

        assert merger.can_merge(path) is True

    def test_accepts_package_json(self):
        """JSONMerger aceita package.json."""
        merger = JSONMerger()
        path = Path("package.json")

        assert merger.can_merge(path) is True

    def test_accepts_tsconfig_json(self):
        """JSONMerger aceita tsconfig.json."""
        merger = JSONMerger()
        path = Path("tsconfig.json")

        assert merger.can_merge(path) is True

    def test_rejects_code_workspace(self):
        """JSONMerger rejeita .code-workspace (tem merger específico)."""
        merger = JSONMerger()
        path = Path("project.code-workspace")

        assert merger.can_merge(path) is False


class TestRealWorldScenarios:
    """Testa cenários reais de merge."""

    def test_extensions_json_merge(self):
        """Simula merge de extensions.json sem duplicação."""
        base = {
            "recommendations": [
                "ms-python.python",
                "github.copilot"
            ]
        }
        overlay = {
            "recommendations": [
                "github.copilot",
                "ms-python.python",
                "astral-sh.uv"
            ]
        }

        result = deep_merge_json(base, overlay)

        # User list wins completamente
        assert result["recommendations"] == [
            "github.copilot",
            "ms-python.python",
            "astral-sh.uv"
        ]
        # NÃO deve ter duplicações ou concatenação
        assert len(result["recommendations"]) == 3

    def test_mcp_json_merge_args_not_duplicated(self):
        """Simula merge de mcp.json sem duplicar args."""
        base = {
            "mcpServers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"]
                }
            }
        }
        overlay = {
            "mcpServers": {
                "memory": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-memory"],
                    "env": {"CUSTOM": "value"}
                },
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"]
                }
            }
        }

        result = deep_merge_json(base, overlay)

        # Args do usuário não duplicam
        assert result["mcpServers"]["memory"]["args"] == [
            "-y", "@modelcontextprotocol/server-memory"
        ]
        # Custom env preservado
        assert result["mcpServers"]["memory"]["env"] == {"CUSTOM": "value"}
        # Custom server preservado
        assert "filesystem" in result["mcpServers"]

    def test_package_json_scripts_merge(self):
        """Simula merge de package.json scripts."""
        base = {
            "scripts": {
                "build": "tsc",
                "test": "jest"
            }
        }
        overlay = {
            "scripts": {
                "dev": "tsx watch src/index.ts",
                "build": "vite build"
            }
        }

        result = deep_merge_json(base, overlay)

        # User script sobrescreve template
        assert result["scripts"]["build"] == "vite build"
        # Template script adicionado
        assert result["scripts"]["test"] == "jest"
        # User script preservado
        assert result["scripts"]["dev"] == "tsx watch src/index.ts"

    def test_tsconfig_paths_merge(self):
        """Simula merge de tsconfig.json."""
        base = {
            "compilerOptions": {
                "target": "ES2020",
                "module": "commonjs"
            },
            "include": ["src/**/*"]
        }
        overlay = {
            "compilerOptions": {
                "target": "ES2022",
                "paths": {"@/*": ["src/*"]}
            },
            "include": ["src/**/*", "types/**/*"]
        }

        result = deep_merge_json(base, overlay)

        # User target wins
        assert result["compilerOptions"]["target"] == "ES2022"
        # Template module adicionado
        assert result["compilerOptions"]["module"] == "commonjs"
        # User paths preservado
        assert result["compilerOptions"]["paths"] == {"@/*": ["src/*"]}
        # User include wins (NÃO concatena)
        assert result["include"] == ["src/**/*", "types/**/*"]
```

#### Executar Testes

```bash
# Rodar testes
pytest tests/test_json_merge_universal.py -v

# Cobertura esperada:
# ✅ test_arrays_are_replaced_not_merged PASSED
# ✅ test_nested_objects_are_merged PASSED
# ✅ test_new_template_keys_are_added PASSED
# ✅ test_user_values_override_template PASSED
# ✅ test_accepts_vscode_extensions_json PASSED
# ✅ test_accepts_package_json PASSED
# ✅ test_extensions_json_merge PASSED
# ✅ test_mcp_json_merge_args_not_duplicated PASSED
# ✅ test_package_json_scripts_merge PASSED
# ✅ test_tsconfig_paths_merge PASSED
# (10+ testes)
```

#### Critérios de Aceite
- ✅ Testes cobrem user-wins behavior
- ✅ Testes cobrem diferentes tipos de JSON
- ✅ Testes cobrem cenários reais (extensions, mcp, package, tsconfig)
- ✅ Todos os testes passam
- ✅ Cobertura ≥ 90% para `deep_merge_json()` e `_merge_user_wins_recursive()`

---

### Task 1.5: Commit com Mudança Arquitetural

**Tipo**: `refactor(json-merge)`
**Scope**: Arquitetural
**Breaking Change**: Sim (comportamento de merge mudou)

#### Mensagem de Commit

```
refactor(json-merge)!: estratégia user-wins universal para todos os JSONs

BREAKING CHANGE: JSONMerger agora usa user-wins sem union de arrays
para TODOS os arquivos JSON do projeto.

Contexto:
- JSON é padrão de configuração no projeto
- Arrays em configs são customizações do usuário
- Union de arrays causava duplicações indesejadas

Mudanças:
- deep_merge_json(): substituir always_merger por user-wins recursivo
- Remover VSCodeJSONMerger (redundante após mudança)
- Remover import/registro em file_merge.py
- Limpar duplicações em TODOS os JSONs do projeto
- Criar testes abrangentes (10+ casos)
- Documentar estratégia em docs/guides/json-merge-strategy.md

Arquivos modificados:
- scripts/lib/json_merge.py: deep_merge_json() user-wins
- scripts/lib/file_merge.py: remover VSCodeJSONMerger
- .vscode/extensions.json: limpar duplicações
- package.json: limpar duplicações (se houver)
- tsconfig.json: limpar duplicações (se houver)
- tests/test_json_merge_universal.py: testes abrangentes (NOVO)
- docs/guides/json-merge-strategy.md: documentação (NOVO)

Relacionado:
- Debate: docs/debates/2026-05-17-json-merge-duplication-bug.md
- Plano: docs/planning/2026-05-17-json-merge-fix-action-plan-v2.md

Tests:
- 10+ testes passando
- Cobertura ≥ 90% em deep_merge_json()
- Validação: zero duplicações em JSONs do projeto
```

#### Executar Commit

```bash
# Criar arquivo de mensagem
cat > /tmp/commit-json-merge-universal.txt << 'EOF'
[Mensagem acima...]
EOF

# Adicionar arquivos
git add \
  scripts/lib/json_merge.py \
  scripts/lib/file_merge.py \
  .vscode/extensions.json \
  package.json \
  tsconfig.json \
  tests/test_json_merge_universal.py \
  docs/guides/json-merge-strategy.md \
  docs/debates/2026-05-17-json-merge-duplication-bug.md \
  docs/planning/2026-05-17-json-merge-fix-action-plan-v2.md

# Commit
./scripts/git-commit-with-file.sh /tmp/commit-json-merge-universal.txt

# Validar
git log --oneline -1
git show --stat
```

#### Critérios de Aceite
- ✅ Commit message segue Conventional Commits
- ✅ BREAKING CHANGE documentado
- ✅ Todos arquivos modificados incluídos
- ✅ Testes passando
- ✅ Sem duplicações em JSONs

---

## ✅ Validação Completa do P0

### Checklist Final

- [ ] `deep_merge_json()` implementa user-wins sem union
- [ ] `VSCodeJSONMerger` removido completamente
- [ ] Imports e registros atualizados
- [ ] **Todos** os JSONs do projeto sem duplicações
- [ ] 10+ testes passando
- [ ] Documentação completa em `docs/guides/json-merge-strategy.md`
- [ ] Commit criado com BREAKING CHANGE

### Testes de Validação

```bash
# 1. Verificar comportamento de deep_merge_json
python -c "
from scripts.lib.json_merge import deep_merge_json
result = deep_merge_json({'a': [1,2]}, {'a': [3,4]})
assert result['a'] == [3,4], 'User-wins falhou!'
print('✅ deep_merge_json() user-wins OK')
"

# 2. Verificar que VSCodeJSONMerger não existe
python -c "from scripts.lib.json_merge import VSCodeJSONMerger" 2>&1 | grep ImportError
# Esperado: ImportError

# 3. Verificar registro de mergers
python -c "
from scripts.lib.file_merge import _MERGERS
names = [type(m).__name__ for m in _MERGERS]
assert 'VSCodeJSONMerger' not in names, 'VSCodeJSONMerger ainda registrado!'
assert 'JSONMerger' in names, 'JSONMerger não encontrado!'
print('✅ Registry OK:', names)
"

# 4. Scan de duplicações
python scripts/tmp/json_diff_visual.py .vscode/extensions.json .vscode/extensions.json \
  | grep "Taxa de duplicação" \
  | grep "0.00%"
# Esperado: Taxa de duplicação: 0.00%

# 5. Rodar testes
pytest tests/test_json_merge_universal.py -v
# Esperado: 10+ PASSED

# 6. Verificar documentação
test -f docs/guides/json-merge-strategy.md && echo "✅ Documentação criada"
```

---

## 🔄 Phase 2: Hardening e Ferramentas (P1)

**Prioridade**: ALTA
**Duração estimada**: 2-3 horas
**Deploy**: Esta semana (2026-05-18 a 2026-05-20)
**Bloqueador**: Não (pode executar em paralelo com outros trabalhos)

---

### Task 2.1: Script `detect-json-duplications.py`

**Objetivo**: Scan recursivo de duplicações em todos JSONs do projeto

#### Implementação

```python
# scripts/detect-json-duplications.py (CRIAR)

import json
from pathlib import Path
from collections import Counter
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def analyze_array_duplicates(arr, path="root"):
    """Analisa duplicações em um array."""
    if not isinstance(arr, list):
        return None

    # Contar itens
    items = []
    for item in arr:
        key = json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else item
        items.append(key)

    counts = Counter(items)
    duplicates = {k: v for k, v in counts.items() if v > 1}

    if duplicates:
        return {
            "path": path,
            "total": len(arr),
            "unique": len(counts),
            "duplicates": duplicates,
            "duplication_rate": (len(arr) - len(counts)) / len(arr) * 100
        }

    return None


def scan_json_structure(data, path="root"):
    """Scan recursivo de duplicações em estrutura JSON."""
    issues = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}"
            issues.extend(scan_json_structure(value, new_path))
    elif isinstance(data, list):
        result = analyze_array_duplicates(data, path)
        if result:
            issues.append(result)
        # Scan recursivo em itens
        for i, item in enumerate(data):
            issues.extend(scan_json_structure(item, f"{path}[{i}]"))

    return issues


def scan_file(file_path: Path):
    """Scan de duplicações em um arquivo JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        issues = scan_json_structure(data, file_path.name)

        if issues:
            log.warning(f"⚠️  {file_path}")
            for issue in issues:
                log.warning(f"   Array: {issue['path']}")
                log.warning(f"   Items: {issue['total']} ({issue['unique']} únicos)")
                log.warning(f"   Taxa: {issue['duplication_rate']:.1f}%")
                for item, count in issue['duplicates'].items():
                    preview = item[:50] + "..." if len(item) > 50 else item
                    log.warning(f"   - {count}x: {preview}")
            return True
        else:
            log.info(f"✅ {file_path}")
            return False

    except Exception as e:
        log.error(f"❌ {file_path}: {e}")
        return False


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    # Listar JSONs
    files = list(root.rglob("*.json"))
    files = [f for f in files if ".git" not in f.parts and "node_modules" not in f.parts]

    log.info(f"🔍 Scanning {len(files)} JSON files...\n")

    issues_count = 0
    for file in sorted(files):
        if scan_file(file):
            issues_count += 1

    log.info(f"\n{'='*60}")
    if issues_count > 0:
        log.warning(f"⚠️  {issues_count} files com duplicações")
        sys.exit(1)
    else:
        log.info(f"✅ Todos os {len(files)} arquivos estão limpos")
        sys.exit(0)
```

#### Uso

```bash
# Scan do projeto inteiro
python scripts/detect-json-duplications.py .

# Scan de pasta específica
python scripts/detect-json-duplications.py .vscode/
```

---

### Task 2.2: Script `fix-json-duplications.py`

**Objetivo**: Correção automática de duplicações em JSONs

(Ver implementação na Task 1.3.2)

---

### Task 2.3: Validação Pós-Merge em `save_json_formatted()`

**Objetivo**: Detectar duplicações imediatamente após merge

#### Implementação

```python
# scripts/lib/json_merge.py

def save_json_formatted(path: Path, data: Dict[str, Any]) -> None:
    """
    Salva JSON formatado com validação anti-duplicação.

    Validações:
    - Sintaxe JSON válida
    - Detecção de arrays duplicados (warning)
    """
    # Validar duplicações antes de salvar
    issues = _detect_duplications(data)
    if issues:
        log.warning(f"⚠️  Duplicações detectadas em {path.name}:")
        for issue in issues:
            log.warning(f"   {issue['path']}: {issue['duplication_rate']:.1f}% duplicado")
        log.warning("   Execute: python scripts/fix-json-duplications.py")

    # Salvar
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _detect_duplications(data, path="root"):
    """Detecta duplicações em estrutura JSON (versão simplificada)."""
    issues = []

    if isinstance(data, dict):
        for key, value in data.items():
            issues.extend(_detect_duplications(value, f"{path}.{key}"))
    elif isinstance(data, list):
        # Contar itens
        items = [json.dumps(i, sort_keys=True) if isinstance(i, (dict, list)) else i for i in data]
        counts = Counter(items)
        duplicates = {k: v for k, v in counts.items() if v > 1}

        if duplicates:
            issues.append({
                "path": path,
                "duplication_rate": (len(data) - len(counts)) / len(data) * 100
            })

    return issues
```

---

### Task 2.4: Documentação em `docs/guides/json-merge-strategy.md`

✅ **Já criada** na Task 1.3 (antes do commit)

---

### Task 2.5: Exemplos de Merge para Diferentes Tipos de JSON

**Arquivo**: `docs/guides/json-merge-examples.md` (CRIAR)

#### Conteúdo

```markdown
# Exemplos de Merge JSON por Tipo de Arquivo

Exemplos práticos de como o merge user-wins funciona para diferentes
tipos de arquivos JSON do projeto.

## .vscode/extensions.json

[... exemplo ...]

## .vscode/mcp.json

[... exemplo ...]

## package.json

[... exemplo ...]

## tsconfig.json

[... exemplo ...]

## .eslintrc.json

[... exemplo ...]
```

---

## 🤖 Phase 3: Automação CI/CD (P2)

**Prioridade**: MÉDIA
**Duração estimada**: 3-4 horas
**Deploy**: Próxima semana (2026-05-21 a 2026-05-24)
**Bloqueador**: Não

---

### Task 3.1: Pre-commit Hook

**Objetivo**: Prevenir commits com duplicações

#### Implementação

```bash
# .git/hooks/pre-commit

#!/usr/bin/env bash

echo "🔍 Verificando duplicações em arquivos JSON..."

# Listar JSONs staged
json_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.json$' || true)

if [ -z "$json_files" ]; then
    echo "✅ Nenhum arquivo JSON modificado"
    exit 0
fi

# Scan de duplicações
has_issues=false
for file in $json_files; do
    if [ -f "$file" ]; then
        python scripts/detect-json-duplications.py "$file" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "⚠️  Duplicações em $file"
            has_issues=true
        fi
    fi
done

if [ "$has_issues" = true ]; then
    echo ""
    echo "❌ Commit bloqueado: duplicações detectadas em arquivos JSON"
    echo "Execute: python scripts/fix-json-duplications.py ."
    echo "Ou force commit com: git commit --no-verify"
    exit 1
fi

echo "✅ Todos os arquivos JSON estão limpos"
exit 0
```

---

### Task 3.2: GitHub Actions Workflow

**Objetivo**: CI que valida JSONs em PRs

#### Implementação

```yaml
# .github/workflows/validate-json-merge.yml

name: Validate JSON Files

on:
  pull_request:
    paths:
      - '**.json'
  push:
    branches:
      - main
      - develop

jobs:
  check-duplications:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Scan for JSON duplications
        run: |
          python scripts/detect-json-duplications.py .

      - name: Report results
        if: failure()
        run: |
          echo "⚠️  Duplicações encontradas em arquivos JSON"
          echo "Execute: python scripts/fix-json-duplications.py ."
          exit 1
```

---

## 📊 Métricas de Sucesso

### Indicadores P0 (Crítico)

| Métrica | Meta | Validação |
|---------|------|-----------|
| Taxa de duplicação em JSONs | 0% | `detect-json-duplications.py` |
| Cobertura de testes | ≥ 90% | `pytest --cov` |
| Testes passando | 100% | `pytest` |
| Documentação completa | Sim | `docs/guides/json-merge-strategy.md` |

### Indicadores P1 (Hardening)

| Métrica | Meta | Validação |
|---------|------|-----------|
| Scripts de detecção | Implementado | `detect-json-duplications.py` |
| Scripts de correção | Implementado | `fix-json-duplications.py` |
| Validação pós-merge | Implementado | `save_json_formatted()` |

### Indicadores P2 (Automação)

| Métrica | Meta | Validação |
|---------|------|-----------|
| Pre-commit hook | Implementado | `.git/hooks/pre-commit` |
| CI/CD workflow | Implementado | `.github/workflows/` |
| Bloqueio automático | Sim | Testes em PR |

---

## 🔄 Retrospectiva

### O Que Funcionou
- ✅ Detecção precoce do problema via `json_diff_visual.py`
- ✅ Debate multi-agent revelou escopo inadequado da solução inicial
- ✅ Input do usuário direcionou para solução arquitetural correta

### O Que Aprendemos
- 📚 JSON = configuração = user-wins (filosofia universal)
- 📚 Soluções paliativas (whitelists) são frágeis e inadequadas
- 📚 Merge strategy deve alinhar com use case (config vs data)
- 📚 Testes devem cobrir escopo completo, não subset

### Próximas Ações
- 🎯 Aplicar mesma filosofia user-wins para YAML/TOML se necessário
- 🎯 Documentar filosofia de merge para outros tipos de arquivo
- 🎯 Criar guias de "quando usar qual merger"

---

**Última atualização**: 17 de maio de 2026
**Versão**: 2.0 (Arquitetural - User-wins universal)
