---
bug_id: BUG-16
title: "Arquivos JSON e .code-workspace não mergeados por padrão no scaffold"
status: "resolved"
severity: "medium"
priority: "P1"
created: 2026-05-14
reporter: "yves_marinho"
resolved: 2026-05-21
resolution: "fixed"
branch: "017-bug-16-merge-strategy"
commits:
  - "932100a - feat(BUG-16): implementar sistema de merge automático JSON/workspace/copilot-rules"
  - "7f018b2 - feat(BUG-16): completar implementação Fase 3-4 (consolidação + docs + testes)"
---

# BUG-16: Arquivos JSON e .code-workspace Não Mergeados por Padrão no Scaffold

## 📋 Descrição

Durante operações de `scaffold.py upgrade --force`, arquivos de configuração JSON (`.vscode/settings.json`, `.vscode/mcp.json`, `.vscode/extensions.json`) e `.code-workspace` são **sobrescritos completamente** ao invés de mergeados, causando perda de customizações do usuário.

## 🔍 Causa Raiz

**Arquivo**: `scripts/lib/project.py`
**Função**: `_copy_file()` (linhas ~2350-2400)

**Comportamento atual**:
```python
def _copy_file(src: Path, dst: Path, force: bool = False) -> CreatedItem:
    if dst.exists():
        if force:
            # Backup + sobrescrever COMPLETO (sem merge)
            backup_path = _create_backup(dst)
            shutil.copy2(src, dst)
            return CreatedItem("updated", str(dst), backup=backup_path)
        else:
            return CreatedItem("skipped", str(dst), reason="already exists")
```

**Problema**: Não há lógica de merge para arquivos estruturados (JSON, YAML, workspace).

## 📊 Evidências

### Cenário de Reprodução

1. Criar projeto via scaffold:
   ```bash
   python scripts/scaffold.py --new --name test-merge \
     --domain programming --language python
   ```

2. Customizar `.vscode/settings.json`:
   ```json
   {
     "chat.mcp.autostart": true,
     "python.analysis.extraPaths": ["./custom/lib"],  // CUSTOMIZAÇÃO
     "editor.rulers": [120]  // CUSTOMIZAÇÃO
   }
   ```

3. Executar upgrade:
   ```bash
   cd test-merge
   python ../scaffold-project/scripts/scaffold.py upgrade --force
   ```

4. **Resultado atual**:
   - ❌ Customizações perdidas (extraPaths, rulers desapareceram)
   - ⚠️ Backup criado em `.backups/`, mas usuário precisa merge manual

5. **Resultado esperado**:
   - ✅ Configurações do template aplicadas
   - ✅ Customizações do usuário preservadas
   - ✅ Conflitos resolvidos automaticamente (estratégia: usuário > template)

## 🎯 Impacto

**Severidade**: Média
**Frequência**: A cada upgrade de template
**Afeta**: Todos os usuários que customizam configurações

### Cenários afetados:

1. ✅ **`.vscode/settings.json`**: Configurações de editor, linter, formatters customizados
2. ✅ **`.vscode/mcp.json`**: Servidores MCP adicionais, env vars customizadas
3. ✅ **`.vscode/extensions.json`**: Extensões extras além das recomendadas
4. ✅ **`.code-workspace`**: Pastas adicionais, configurações de workspace
5. ✅ **`package.json`** (Node.js): Scripts, dependências customizadas
6. ✅ **`pyproject.toml`** (Python): Dependências, configurações de tools
7. ✅ **`.copilot-rules*` (raiz)**: Múltiplos arquivos de regras Copilot duplicados

### ⚠️ Caso Especial: Múltiplos Arquivos `.copilot-rules`

**Problema detectado**: Projetos podem conter múltiplos arquivos de regras Copilot na raiz:
- `.copilot-rules.md`
- `.copilot-strict-rules.md`
- `.copilot-strict-enforcement.md`
- `copilot-instructions.md` (padrão VS Code)

**Comportamento atual durante upgrade**:
- ❌ Cada arquivo pode ser sobrescrito independentemente
- ❌ Não há detecção de duplicatas ou conflitos
- ❌ Customizações podem ser perdidas se houver renomeação de arquivos

**Estratégia de consolidação automática** (Fase 1):
```python
def _consolidate_copilot_rules(project_root: Path) -> Path:
    """
    Detecta e consolida múltiplos arquivos .copilot-rules* automaticamente.

    Estratégia:
    1. Detecta todos os arquivos .copilot-rules* na raiz
    2. Se múltiplos encontrados:
       - Mergeia conteúdo (ordem: .copilot-rules.md > outros alfabético)
       - Preserva seções únicas de cada arquivo
       - Remove duplicatas de seções
       - Salva backup de cada arquivo original
    3. Retorna Path do arquivo consolidado (.copilot-rules.md)

    Returns:
        Path do arquivo consolidado (ou único existente)
    """
    patterns = [
        ".copilot-rules.md",
        ".copilot-strict-rules.md",
        ".copilot-strict-enforcement.md",
        "copilot-instructions.md",
        ".copilot-instructions.md"
    ]

    found_files = []
    for pattern in patterns:
        matches = list(project_root.glob(pattern))
        found_files.extend(matches)

    if len(found_files) == 0:
        return None  # Nenhum arquivo encontrado

    if len(found_files) == 1:
        return found_files[0]  # Apenas 1, sem consolidação necessária

    # Múltiplos arquivos - consolidar automaticamente
    log.info(
        f"🔄 Consolidando {len(found_files)} arquivos de regras Copilot: "
        f"{[f.name for f in found_files]}"
    )

    # Priorizar .copilot-rules.md como base, resto alfabético
    primary = project_root / ".copilot-rules.md"
    others = sorted([f for f in found_files if f != primary])
    files_to_merge = [primary] if primary.exists() else []
    files_to_merge.extend(others)

    # Merge de conteúdo (preservar seções únicas)
    consolidated_content = _merge_markdown_sections(files_to_merge)

    # Backup de originais
    for file in found_files:
        backup_path = _create_backup(file)
        log.info(f"   📦 Backup: {file.name} → {backup_path}")

    # Salvar consolidado
    output_file = project_root / ".copilot-rules.md"
    output_file.write_text(consolidated_content)
    log.info(f"   ✅ Consolidado em: {output_file.name}")

    # Remover duplicatas (manter apenas consolidado)
    for file in found_files:
        if file != output_file:
            file.unlink()
            log.info(f"   🗑️  Removido: {file.name}")

    return output_file
```

**Processo automático de consolidação**:
1. **Detectar** todos os arquivos `.copilot-rules*` na raiz
2. **Mergear** conteúdo preservando seções únicas (sem duplicação)
3. **Backup** de todos os arquivos originais em `.backups/`
4. **Consolidar** em `.copilot-rules.md` (arquivo canônico)
5. **Remover** duplicatas automaticamente
6. **Log** detalhado de todas as ações

## 🛠️ Solução Proposta

### Fase 1: Merge de JSON (P1, 8h)

**Implementar função `_merge_json()`**:

```python
def _merge_json(base: Path, overlay: Path, strategy: str = "user-wins") -> dict:
    """
    Merge dois arquivos JSON com estratégia configurável.

    Args:
        base: Arquivo do template (upstream)
        overlay: Arquivo do usuário (customizações)
        strategy: "user-wins" (default) | "template-wins" | "interactive"

    Returns:
        dict mergeado
    """
    import json

    base_data = json.loads(base.read_text())
    overlay_data = json.loads(overlay.read_text())

    if strategy == "user-wins":
        # Deep merge: template como base, usuário sobrescreve
        merged = deep_merge(base_data, overlay_data)
    elif strategy == "template-wins":
        # Deep merge: usuário como base, template sobrescreve
        merged = deep_merge(overlay_data, base_data)
    elif strategy == "interactive":
        # Detectar conflitos e pedir confirmação
        merged = interactive_merge(base_data, overlay_data)

    return merged
```

**Integração em `_copy_file()`**:

```python
if dst.suffix == ".json" and dst.exists() and force:
    # Merge JSON ao invés de sobrescrever
    merged = _merge_json(src, dst, strategy="user-wins")
    backup_path = _create_backup(dst)
    dst.write_text(json.dumps(merged, indent=2))
    return CreatedItem("merged", str(dst), backup=backup_path)
```

### Fase 2: Merge de .code-workspace (P1, 4h)

**Estratégia**:
- Mesclar array `folders` (união, sem duplicatas)
- Mesclar dict `settings` (deep merge, user-wins)
- Mesclar dict `extensions` (união de recommendations)

### Fase 3: Merge de YAML (P2, 4h)

**Arquivos**:
- `pyproject.toml` (TOML, não YAML)
- `objetivo.yaml` (especial: não sobrescrever se preenchido)

### Fase 4: Validação e Logging (P2, 6h)

**Objetivo**: Reportar resultados de merge de forma clara

**Implementação**:
```python
def _report_merge_results(results: list[MergeResult]) -> None:
    """
    Reporta resultados de merge de forma estruturada.

    Args:
        results: Lista de resultados (arquivo, ação, conflitos, backup)
    """
    print("\n📊 Resultados do Merge:")
    print("=" * 60)

    for result in results:
        icon = {
            "merged": "🔄",
            "skipped": "⏭️",
            "updated": "✅",
            "conflict": "⚠️"
        }.get(result.action, "❓")

        print(f"{icon} {result.file}")
        print(f"   Ação: {result.action}")

        if result.backup:
            print(f"   Backup: {result.backup}")

        if result.conflicts:
            print(f"   ⚠️  Conflitos ({len(result.conflicts)}):")
            for key, values in result.conflicts.items():
                print(f"      • {key}: user={values['user']}, template={values['template']}")
                print(f"        Resolução: {values['resolution']} (user-wins)")

    print("=" * 60)
```

**Logs gerados**:
- Arquivo de log: `.backups/merge-YYYY-MM-DD-HHmmss.log`
- Sumário no console: arquivos processados, conflitos, ações
- Diff disponível: `git diff .backups/YYYY-MM-DD/`

## 📚 Referências

### Ferramentas de Merge Existentes

1. **json-merge-patch** (RFC 7386):
   - `pip install json-merge-patch`
   - Merge determinístico de objetos JSON
   - [RFC 7386](https://tools.ietf.org/html/rfc7386)

2. **deepmerge** (Python):
   - `pip install deepmerge`
   - Deep merge recursivo de dicionários
   - [GitHub](https://github.com/toumorokoshi/deepmerge)

3. **dynaconf** (merging):
   - `pip install dynaconf`
   - Merge de múltiplas fontes de configuração
   - [Docs](https://www.dynaconf.com/)

4. **git merge-file** (three-way merge):
   - Nativo do Git
   - Merge three-way de arquivos texto
   - `git merge-file current.json base.json other.json`

### Estratégias de Merge em Projetos Similares

1. **Renovate** (dependency updates):
   - Merge automático de package.json
   - Preserva customizações do usuário
   - [Docs](https://docs.renovatebot.com/configuration-options/)

2. **Yeoman** (scaffolding):
   - Merge de arquivos via estratégias configuráveis
   - `.yo-rc.json` com preferências de merge
   - [Docs](https://yeoman.io/authoring/storage.html)

3. **Angular CLI** (ng update):
   - Three-way merge de angular.json
   - Backup automático + resolução de conflitos
   - [Docs](https://angular.io/cli/update)

## ✅ Critérios de Aceite

- [ ] JSON files são mergeados por padrão (não sobrescritos)
- [ ] Customizações do usuário preservadas (user-wins strategy)
- [ ] Backup criado antes de merge
- [ ] Conflitos não-resolúveis logados claramente
- [ ] Testes unitários cobrindo cenários de merge
- [ ] Documentação atualizada em `UPGRADE_GUIDE.md`
- [ ] `.copilot-rules*` consolidados automaticamente sem prompt
- [ ] Logs detalhados de todas as operações de merge

---

## 📋 Plano de Implementação

### Fase 1: Merge de JSON (P1, 8h)

**Objetivo**: Implementar merge automático de arquivos JSON

**Entregas**:
1. Função `_merge_json()` com estratégia user-wins
2. Função `_deep_merge()` para merge recursivo de dicionários
3. Integração em `_copy_file()` para detectar extensão `.json`
4. Backup automático antes de merge
5. Testes unitários (10+ cenários)

**Arquivos modificados**:
- `scripts/lib/project.py` (+150 linhas)
- `tests/test_project_merge.py` (novo, 200 linhas)

**Dependências**:
- `pip install deepmerge` (adicionar a pyproject.toml)

---

### Fase 2: Merge de .code-workspace (P1, 4h)

**Objetivo**: Implementar merge de arquivos workspace

**Entregas**:
1. Função `_merge_workspace()` especializada
2. Merge de `folders` array (união sem duplicatas)
3. Merge de `settings` dict (deep merge, user-wins)
4. Merge de `extensions.recommendations` (união)
5. Testes unitários (5+ cenários)

**Arquivos modificados**:
- `scripts/lib/project.py` (+80 linhas)
- `tests/test_project_merge.py` (+100 linhas)

---

### Fase 3: Consolidação .copilot-rules + Merge YAML (P1, 6h)

**Objetivo**: Consolidar arquivos Copilot e mergear YAML/TOML

**Entregas**:
1. Função `_consolidate_copilot_rules()` (detecção + merge + cleanup)
2. Função `_merge_markdown_sections()` para merge de Markdown
3. Função `_merge_toml()` para pyproject.toml
4. Proteção especial para `objetivo.yaml` (não sobrescrever se preenchido)
5. Testes unitários (8+ cenários)

**Arquivos modificados**:
- `scripts/lib/project.py` (+120 linhas)
- `scripts/lib/flows/upgrade.py` (+30 linhas, chamar consolidação)
- `tests/test_copilot_rules_merge.py` (novo, 150 linhas)

**Dependências**:
- `pip install toml` (já presente)

---

### Fase 4: Validação e Logging (P2, 6h)

**Objetivo**: Sistema robusto de logs e validação

**Entregas**:
1. Função `_report_merge_results()` para sumário formatado
2. Arquivo de log `.backups/merge-YYYY-MM-DD-HHmmss.log`
3. Diff disponível via Git (backups em pasta datada)
4. Validação pós-merge (JSON/YAML válidos)
5. Documentação em `docs/guides/UPGRADE_GUIDE.md`

**Arquivos criados/modificados**:
- `scripts/lib/project.py` (+60 linhas)
- `docs/guides/UPGRADE_GUIDE.md` (novo, 300 linhas)
- `scripts/lib/flows/upgrade.py` (+20 linhas, logging)

---

## 📝 Task List Completa

### 🔴 Fase 1: Merge de JSON (8h)

- [ ] **Task 1.1** (2h): Implementar `_deep_merge(dict, dict) -> dict`
  - Merge recursivo de dicionários aninhados
  - Estratégia: valores do segundo dict sobrescrevem primeiro
  - Suporte a listas (união sem duplicatas)
  - Suporte a valores primitivos

- [ ] **Task 1.2** (2h): Implementar `_merge_json(base: Path, overlay: Path) -> dict`
  - Carregar ambos arquivos JSON
  - Validar sintaxe JSON
  - Aplicar `_deep_merge(base_data, overlay_data)`
  - Retornar dict mergeado

- [ ] **Task 1.3** (1h): Integrar em `_copy_file()`
  - Detectar extensão `.json`
  - Se `force=True` e arquivo existe: chamar `_merge_json()`
  - Criar backup antes de merge
  - Escrever resultado mergeado
  - Retornar `CreatedItem("merged", ...)`

- [ ] **Task 1.4** (2h): Testes unitários `test_project_merge.py`
  - Cenário 1: Merge simples (flat dict)
  - Cenário 2: Merge aninhado (nested dict)
  - Cenário 3: Merge com arrays (união)
  - Cenário 4: Merge com conflitos (user-wins)
  - Cenário 5: Merge de settings.json real
  - Cenário 6: Merge de mcp.json real
  - Cenário 7: Merge de extensions.json
  - Cenário 8: JSON inválido (error handling)
  - Cenário 9: Arquivo não existe (skip)
  - Cenário 10: Backup criado corretamente

- [ ] **Task 1.5** (1h): Adicionar dependência `deepmerge`
  - Atualizar `pyproject.toml`: `deepmerge = "^1.1.0"`
  - Rodar `pip install deepmerge`
  - Validar import em `project.py`

---

### 🟡 Fase 2: Merge de .code-workspace (4h)

- [ ] **Task 2.1** (2h): Implementar `_merge_workspace(base: Path, overlay: Path) -> dict`
  - Carregar ambos arquivos JSON (workspace é JSON)
  - Mergear `folders` array:
    - União de paths (sem duplicatas)
    - Preservar ordem (overlay primeiro, depois base)
  - Mergear `settings` dict:
    - Deep merge (user-wins)
  - Mergear `extensions.recommendations` array:
    - União de IDs (sem duplicatas)
  - Retornar dict mergeado

- [ ] **Task 2.2** (1h): Integrar em `_copy_file()`
  - Detectar extensão `.code-workspace`
  - Chamar `_merge_workspace()` se `force=True`
  - Criar backup
  - Escrever resultado

- [ ] **Task 2.3** (1h): Testes unitários
  - Cenário 1: Merge de folders (sem duplicatas)
  - Cenário 2: Merge de settings (deep)
  - Cenário 3: Merge de extensions (união)
  - Cenário 4: Workspace completo (real)
  - Cenário 5: Folders com paths relativos vs absolutos

---

### 🟢 Fase 3: .copilot-rules + YAML (6h)

- [ ] **Task 3.1** (2h): Implementar `_consolidate_copilot_rules(project_root: Path) -> Path`
  - Detectar todos os padrões: `.copilot-rules*.md`, `copilot-instructions.md`
  - Se 0: retornar None
  - Se 1: retornar Path (sem consolidação)
  - Se > 1:
    - Chamar `_merge_markdown_sections()`
    - Criar backups de todos
    - Salvar em `.copilot-rules.md`
    - Remover duplicatas
    - Log de ações

- [ ] **Task 3.2** (1.5h): Implementar `_merge_markdown_sections(files: list[Path]) -> str`
  - Parsear cada arquivo em seções (por headers `##`)
  - Detectar seções duplicadas (mesmo título)
  - Priorizar conteúdo do primeiro arquivo (user-wins)
  - Preservar seções únicas de todos os arquivos
  - Ordenar seções alfabeticamente
  - Retornar Markdown consolidado

- [ ] **Task 3.3** (1h): Implementar `_merge_toml(base: Path, overlay: Path) -> str`
  - Carregar ambos arquivos TOML
  - Deep merge de tabelas aninhadas
  - Merge de arrays `dependencies` (união, preservar versões do overlay)
  - Retornar string TOML formatada

- [ ] **Task 3.4** (0.5h): Proteção de `objetivo.yaml`
  - Detectar se `objetivo.yaml` foi preenchido (> 50% campos não-placeholder)
  - Se preenchido: skip merge, apenas log warning
  - Se vazio: permitir merge normal

- [ ] **Task 3.5** (1h): Testes unitários
  - Cenário 1: 2 arquivos .copilot-rules (merge)
  - Cenário 2: 4 arquivos (consolidação completa)
  - Cenário 3: Seções duplicadas (priorizar user)
  - Cenário 4: Seções únicas (preservar todas)
  - Cenário 5: pyproject.toml merge
  - Cenário 6: objetivo.yaml preenchido (skip)
  - Cenário 7: objetivo.yaml vazio (merge)
  - Cenário 8: Backups criados corretamente

---

### 🔵 Fase 4: Validação e Logging (6h)

- [ ] **Task 4.1** (1.5h): Implementar `_report_merge_results(results: list[MergeResult])`
  - Classe `MergeResult` (dataclass): file, action, conflicts, backup, duration
  - Formatação bonita no console (tabela)
  - Ícones por tipo de ação (🔄 merged, ⏭️ skipped, ✅ updated, ⚠️ conflict)
  - Sumário: total de arquivos, merges, conflitos, tempo total

- [ ] **Task 4.2** (1.5h): Implementar logging para arquivo
  - Criar `.backups/merge-YYYY-MM-DD-HHmmss.log`
  - Log estruturado (formato: timestamp | level | file | action | details)
  - Incluir diff de cada arquivo mergeado
  - Incluir lista de conflitos resolvidos
  - Incluir comandos para restore (`cp .backups/... ./`)

- [ ] **Task 4.3** (1h): Validação pós-merge
  - Validar JSON/YAML gerados (sintaxe)
  - Validar schemas conhecidos (settings.json, mcp.json)
  - Se inválido: restaurar backup automaticamente + error
  - Log de validações executadas

- [ ] **Task 4.4** (2h): Documentação `UPGRADE_GUIDE.md`
  - Seção "Merge Automático": como funciona
  - Seção "Estratégia user-wins": exemplos
  - Seção "Backups": onde ficam, como restaurar
  - Seção "Consolidação .copilot-rules": processo automático
  - Seção "Troubleshooting": conflitos, validação, rollback
  - Exemplos práticos: antes/depois de merge
  - FAQ: 10+ perguntas comuns

---

## 🏷️ Tags

`scaffold`, `upgrade`, `merge`, `json`, `workspace`, `configuration`, `copilot-rules`, `P1`, `enhancement`, `automation`

---

**Estimativa total**: 24h (4 fases)
**Prioridade**: P1 (próximo ciclo de desenvolvimento)
**Bloqueador**: Não (workaround: restore manual do backup)
**ETA**: Sprint 2026-W21 (19-23 maio)
