# Estrat\u00e9gia Universal de Merge para Arquivos JSON

**Data**: 17 de maio de 2026
**Projeto**: scaffold-project (Enterprise Scaffold Project Template)
**Status**: Implementado
**Vers\u00e3o**: 2.0 (Arquitetural)

---

## \ud83c\udfaf Vis\u00e3o Geral

JSON \u00e9 o **padr\u00e3o de configura\u00e7\u00e3o** do projeto. Todos os arquivos `.json` usam a **mesma estrat\u00e9gia de merge**: **user-wins sem union de arrays**.

### Princ\u00edpio Fundamental

> **User Wins, No Array Union**
> Ao fazer merge de um template JSON com arquivo existente do usu\u00e1rio, as customiza\u00e7\u00f5es do usu\u00e1rio sempre prevalecem. Arrays s\u00e3o substitu\u00eddos completamente, nunca concatenados.

---

## \ud83d\udee0\ufe0f Estrat\u00e9gia de Merge

### Comportamento por Tipo de Dado

| Tipo | Template (Base) | Usu\u00e1rio (Overlay) | Resultado | Raz\u00e3o |
|------|----------------|---------------------|-----------|--------|
| **Primitivo** | `"value1"` | `"value2"` | `"value2"` | User wins |
| **Array** | `[1, 2, 3]` | `[4, 5]` | `[4, 5]` | User wins, **N\u00c3O** union |
| **Object** | `{a: 1, b: 2}` | `{b: 3, c: 4}` | `{a: 1, b: 3, c: 4}` | Merge recursivo |

### Regras Detalhadas

#### 1\ufe0f\u20e3 Primitivos (string, number, boolean, null)
```json
// Template
{
  "version": "1.0.0",
  "enabled": true
}

// Usu\u00e1rio
{
  "version": "2.0.0"
}

// Resultado (user wins)
{
  "version": "2.0.0",
  "enabled": true
}
```

\u2705 Valores do usu\u00e1rio sobrescrevem template
\u2705 Chaves novas do template s\u00e3o adicionadas

---

#### 2\ufe0f\u20e3 Arrays (NUNCA faz union)
```json
// Template
{
  "scripts": ["build", "test", "lint"]
}

// Usu\u00e1rio
{
  "scripts": ["dev", "build"]
}

// Resultado (user array wins completamente)
{
  "scripts": ["dev", "build"]
}
```

\u274c **N\u00c3O faz union**: `["build", "test", "lint", "dev"]` (\u274c ERRADO)
\u2705 **User wins**: `["dev", "build"]` (\u2705 CORRETO)

**Raz\u00e3o**: Arrays em configs representam listas customizadas pelo usu\u00e1rio. Union causaria duplica\u00e7\u00e3o e confus\u00e3o.

---

#### 3\ufe0f\u20e3 Objetos Aninhados (merge recursivo)
```json
// Template
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true
  }
}

// Usu\u00e1rio
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"]
  }
}

// Resultado (merge recursivo)
{
  "compilerOptions": {
    "target": "ES2022",      // user value
    "module": "commonjs",    // template value (novo)
    "strict": true,          // template value (novo)
    "lib": ["ES2022"]        // user value
  }
}
```

\u2705 Merge recursivo: valores do usu\u00e1rio + chaves novas do template
\u2705 Arrays dentro de objetos: seguem regra #2 (user wins)

---

## \ud83d\udcc1 Exemplos por Tipo de Arquivo

### `.vscode/extensions.json`

```json
// Template (base)
{
  "recommendations": [
    "ms-python.python",
    "github.copilot",
    "dbaeumer.vscode-eslint"
  ]
}

// Usu\u00e1rio (overlay)
{
  "recommendations": [
    "github.copilot",
    "ms-python.python",
    "astral-sh.uv"
  ]
}

// Resultado (user list wins)
{
  "recommendations": [
    "github.copilot",
    "ms-python.python",
    "astral-sh.uv"
  ]
}
```

\u2705 Lista do usu\u00e1rio \u00e9 preservada
\u274c Template **N\u00c3O** adiciona `dbaeumer.vscode-eslint`

---

### `.vscode/mcp.json`

```json
// Template
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}

// Usu\u00e1rio
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {
        "CUSTOM_VAR": "value"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    }
  }
}

// Resultado (merge de objetos, user arrays wins)
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],  // user array (sem duplica\u00e7\u00e3o)
      "env": {
        "CUSTOM_VAR": "value"  // user custom field
      }
    },
    "filesystem": {  // user custom server
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    }
  }
}
```

\u2705 Args do usu\u00e1rio preservados (sem duplica\u00e7\u00e3o)
\u2705 Custom env e servers do usu\u00e1rio preservados

---

### `package.json`

```json
// Template
{
  "scripts": {
    "build": "tsc",
    "test": "jest"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "jest": "^29.0.0"
  }
}

// Usu\u00e1rio
{
  "name": "my-project",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "vite build"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}

// Resultado
{
  "name": "my-project",        // user value
  "scripts": {
    "dev": "tsx watch src/index.ts",  // user value
    "build": "vite build",            // user value (sobrescreve template)
    "test": "jest"                     // template value (novo)
  },
  "devDependencies": {
    "typescript": "^5.3.0",    // user value (vers\u00e3o customizada)
    "jest": "^29.0.0",         // template value (novo)
    "vite": "^5.0.0"           // user value
  }
}
```

\u2705 Scripts customizados do usu\u00e1rio preservados
\u2705 Vers\u00f5es de depend\u00eancias do usu\u00e1rio preservadas
\u2705 Novos scripts/deps do template adicionados

---

### `tsconfig.json`

```json
// Template
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}

// Usu\u00e1rio
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*", "types/**/*"]
}

// Resultado
{
  "compilerOptions": {
    "target": "ES2022",           // user value
    "module": "ESNext",           // user value
    "strict": true,               // template value (novo)
    "esModuleInterop": true,      // template value (novo)
    "paths": {                    // user value
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*", "types/**/*"]  // user array wins
}
```

\u2705 Compiler options do usu\u00e1rio preservadas
\u2705 Novas op\u00e7\u00f5es do template adicionadas
\u274c Array `include` **N\u00c3O** concatena com template

---

## \ud83d\udc1e Problemas Evitados

### ❌ Bug: Union de Arrays (comportamento ANTIGO)

```json
// Template
{
  "recommendations": ["ext1", "ext2"]
}

// Usu\u00e1rio
{
  "recommendations": ["ext1", "ext2"]
}

// ❌ ERRADO (union com deepmerge.always_merger)
{
  "recommendations": ["ext1", "ext2", "ext1", "ext2"]  // DUPLICA\u00c7\u00c3O!
}

// ✅ CORRETO (user-wins)
{
  "recommendations": ["ext1", "ext2"]
}
```

---

## \ud83d\udcda Implementa\u00e7\u00e3o T\u00e9cnica

### C\u00f3digo: `scripts/lib/json_merge.py`

```python
def deep_merge_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge com estrat\u00e9gia user-wins SEM union de arrays.

    JSON \u00e9 padr\u00e3o de configura\u00e7\u00e3o no projeto. Esta fun\u00e7\u00e3o implementa
    merge universal para TODOS os arquivos JSON.

    Estrat\u00e9gia:
    - Overlay (usu\u00e1rio) sobrescreve base (template)
    - Arrays substitu\u00eddos completamente (N\u00c3O faz union)
    - Objetos aninhados mergeados recursivamente
    - Chaves novas do template s\u00e3o adicionadas

    Hist\u00f3rico:
    - v1.0: Usava always_merger.merge() (union de arrays) \u274c BUG
    - v2.0: Implementa user-wins sem union \u2705 FIX ARQUITETURAL
    """
    return _merge_user_wins_recursive(base, overlay)


def _merge_user_wins_recursive(base: Dict, overlay: Dict) -> Dict:
    """
    Implementa\u00e7\u00e3o do merge user-wins recursivo.

    Algoritmo:
    1. Copiar todos valores do overlay (user wins)
    2. Para objetos aninhados: merge recursivo
    3. Adicionar chaves novas do base que n\u00e3o existem no overlay
    """
    merged = {}

    # Passo 1: User wins - copiar tudo do overlay
    for key, overlay_value in overlay.items():
        base_value = base.get(key)

        # Se ambos s\u00e3o dicts: merge recursivo
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

### Merger: `JSONMerger`

```python
class JSONMerger:
    """
    Merger universal para TODOS os arquivos JSON.

    Aplica-se a:
    - .vscode/*.json (extensions, settings, mcp, launch, tasks)
    - package.json, tsconfig.json, jsconfig.json
    - .eslintrc.json, .prettierrc.json
    - jest.config.json, vite.config.json
    - Qualquer outro arquivo .json do projeto

    Estrat\u00e9gia:
    - User-wins sem union de arrays (via deep_merge_json)
    - Backup autom\u00e1tico antes de merge
    - Valida\u00e7\u00e3o de sintaxe JSON
    """

    def can_merge(self, file_path: Path) -> bool:
        """Aceita TODOS os arquivos .json (exceto .code-workspace)."""
        return (
            file_path.suffix == ".json" and
            not file_path.name.endswith(".code-workspace")
        )

    def merge(self, existing_path: Path, template_content: str, interactive: bool = True) -> CreatedItem:
        """Faz merge usando deep_merge_json (user-wins universal)."""
        # Implementa\u00e7\u00e3o usa deep_merge_json()
        ...
```

---

## \u2705 Crit\u00e9rios de Valida\u00e7\u00e3o

### Testes Autom\u00e1ticos

```python
# tests/test_json_merge.py

def test_arrays_are_replaced_not_merged():
    """Arrays do usu\u00e1rio substituem template completamente."""
    base = {"items": [1, 2, 3]}
    overlay = {"items": [4, 5]}

    result = deep_merge_json(base, overlay)

    assert result["items"] == [4, 5], \
        "Array deve ser substitu\u00eddo, N\u00c3O concatenado"
    assert result["items"] != [1, 2, 3, 4, 5], \
        "N\u00c3O deve fazer union de arrays"


def test_nested_objects_are_merged():
    """Objetos aninhados fazem merge recursivo."""
    base = {"config": {"a": 1, "b": 2}}
    overlay = {"config": {"b": 3, "c": 4}}

    result = deep_merge_json(base, overlay)

    assert result == {"config": {"a": 1, "b": 3, "c": 4}}


def test_new_template_keys_are_added():
    """Chaves novas do template s\u00e3o adicionadas."""
    base = {"new_key": "new_value"}
    overlay = {"existing": "value"}

    result = deep_merge_json(base, overlay)

    assert "new_key" in result
    assert "existing" in result
```

### Detec\u00e7\u00e3o de Duplica\u00e7\u00f5es

```bash
# Script: scripts/detect-json-duplications.py
python scripts/detect-json-duplications.py

# Output esperado ap\u00f3s fix:
# \u2705 .vscode/extensions.json: Sem duplica\u00e7\u00f5es
# \u2705 .vscode/mcp.json: Sem duplica\u00e7\u00f5es
# \u2705 package.json: Sem duplica\u00e7\u00f5es
# \u2705 tsconfig.json: Sem duplica\u00e7\u00f5es
```

---

## \ud83d\udcca Compara\u00e7\u00e3o: Antes vs Depois

| Aspecto | v1.0 (ANTIGO) | v2.0 (NOVO) |
|---------|---------------|-------------|
| **Estrat\u00e9gia** | Union de arrays | User-wins sem union |
| **Biblioteca** | `deepmerge.always_merger` | Custom `_merge_user_wins_recursive` |
| **Escopo** | VSCode files (whitelist) | TODOS os JSONs |
| **Duplica\u00e7\u00f5es** | Sim (\u274c BUG) | N\u00e3o (\u2705 FIX) |
| **Manuten\u00e7\u00e3o** | Whitelist manual | Universal, zero config |
| **Previsibilidade** | Baixa (depende do arquivo) | Alta (comportamento universal) |

---

## \ud83d\udee1\ufe0f Seguran\u00e7a e Backup

### Backup Autom\u00e1tico

Antes de qualquer merge, um backup \u00e9 criado:

```
.vscode/extensions.json        # original do usu\u00e1rio
.vscode/extensions.json.backup  # backup criado automaticamente
```

### Rollback Manual

```bash
# Se merge deu errado, restaurar backup:
mv .vscode/extensions.json.backup .vscode/extensions.json
```

---

## \ud83d\udcdd Documenta\u00e7\u00e3o Adicional

- **Debate T\u00e9cnico**: [docs/debates/2026-05-17-json-merge-duplication-bug.md](../debates/2026-05-17-json-merge-duplication-bug.md)
- **Plano de A\u00e7\u00e3o**: [docs/planning/2026-05-17-json-merge-fix-action-plan.md](../planning/2026-05-17-json-merge-fix-action-plan.md)
- **C\u00f3digo**: `scripts/lib/json_merge.py` (fun\u00e7\u00e3o `deep_merge_json`)
- **Testes**: `tests/test_json_merge.py`

---

## \u2753 FAQ

### Por que n\u00e3o fazer union de arrays?

**R**: Arrays em arquivos de configura\u00e7\u00e3o s\u00e3o listas **customizadas** pelo usu\u00e1rio. Fazer union causaria:
- Duplica\u00e7\u00f5es indesejadas
- Ordem inesperada
- Perda de controle do usu\u00e1rio

### E se eu QUISER adicionar itens do template ao array do usu\u00e1rio?

**R**: Adicione manualmente. A estrat\u00e9gia user-wins garante que **voc\u00ea tem controle total** sobre suas configura\u00e7\u00f5es. Template n\u00e3o deve modificar listas do usu\u00e1rio sem permiss\u00e3o expl\u00edcita.

### Isso afeta .code-workspace?

**R**: N\u00e3o. Arquivos `.code-workspace` t\u00eam merger especializado (`WorkspaceMerger`) com l\u00f3gica pr\u00f3pria.

### E arquivos YAML/TOML?

**R**: Este documento \u00e9 espec\u00edfico para JSON. YAML e TOML t\u00eam mergers pr\u00f3prios se necess\u00e1rio.

---

**\u00daltima atualiza\u00e7\u00e3o**: 17 de maio de 2026
**Vers\u00e3o**: 2.0 (Arquitetural - User-wins universal)
