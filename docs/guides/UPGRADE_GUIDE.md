# Guia de Upgrade de Templates

Guia de referência para upgrades seguros de templates e scaffolds neste projeto.

---

## 📋 Visão Geral

### Sistema de Merge Automático

Este projeto implementa um **sistema de merge inteligente** para atualizações de scaffold/template que **preserva suas customizações** ao incorporar melhorias do template base.

**Antes do BUG-16**:
```
template upgrade → sobrescreve → ❌ perde customizações
```

**Depois do BUG-16**:
```
template upgrade → merge automático → ✅ preserva customizações + adiciona melhorias
```

---

## 🎯 Arquivos com Merge Automático

### JSON Files

| Arquivo | Estratégia de Merge | O que é preservado |
|---------|--------------------|--------------------|
| `.vscode/settings.json` | Deep merge (user-wins) | Todas suas configs de editor |
| `.vscode/mcp.json` | Deep merge (user-wins) | Servidores MCP customizados |
| `.vscode/extensions.json` | União de arrays | Extensões recomendadas (suas + template) |
| `package.json` | Deep merge dependencies | Pacotes instalados + novos do template |
| `tsconfig.json` | Deep merge | Configurações TypeScript customizadas |

**Exemplo de merge**: `.vscode/settings.json`
```json
// Seu arquivo atual
{
  "editor.rulers": [120],
  "python.linting.enabled": true
}

// Template novo
{
  "editor.rulers": [80],
  "editor.formatOnSave": true
}

// Resultado do merge (user-wins)
{
  "editor.rulers": [120],            // Sua customização preservada ✅
  "python.linting.enabled": true,    // Sua config preservada ✅
  "editor.formatOnSave": true        // Melhoria do template adicionada ✅
}
```

---

### Workspace Files

| Arquivo | Estratégia | O que é preservado |
|---------|-----------|-------------------|
| `*.code-workspace` | Merge folders + settings | Pastas abertas + configs + extensões |

**Exemplo de merge**: `scaffold-project.code-workspace`
```json
// Seu workspace
{
  "folders": [{"path": "."}, {"path": "../libs"}],
  "settings": {"editor.rulers": [120]}
}

// Template
{
  "folders": [{"path": "."}],
  "settings": {"editor.formatOnSave": true}
}

// Resultado (união)
{
  "folders": [{"path": "."}, {"path": "../libs"}],  // União ✅
  "settings": {
    "editor.rulers": [120],         // Preservado ✅
    "editor.formatOnSave": true     // Adicionado ✅
  }
}
```

---

### Copilot Rules Files

| Padrão de Arquivo | Consolidação Automática |
|------------------|------------------------|
| `.copilot-rules*.md` | ✅ Automática |
| `copilot-instructions.md` | ✅ Automática |

**Consolidação automática**:

Se você tem múltiplos arquivos de regras (ex: `.copilot-rules.md`, `.copilot-strict-rules.md`):

1. **Backup automático** em `.backups/copilot-rules/`
2. **Merge de seções** (por headers `##`)
3. **Priorização**: `.copilot-rules.md` > demais (ordem alfabética)
4. **Deduplicação**: seções duplicadas preservam conteúdo do primeiro arquivo
5. **Consolidação**: tudo vira `.copilot-rules.md`
6. **Limpeza**: arquivos antigos são removidos

**Exemplo**:
```
Antes:
  .copilot-rules.md
  .copilot-strict-rules.md
  copilot-instructions.md

Depois:
  .copilot-rules.md (consolidado)
  .backups/copilot-rules/.copilot-rules.md
  .backups/copilot-rules/.copilot-strict-rules.md
  .backups/copilot-rules/copilot-instructions.md
```

---

### TOML Files

| Arquivo | Merger | O que é preservado |
|---------|--------|-------------------|
| `pyproject.toml` | PyprojectMerger | Dependencies + build-system + tool.* |

**Merge inteligente** de seções `[project]`, `[build-system]`, `[tool.*]`.

---

## 🔧 Processo de Upgrade

### Comando
```bash
make scaffold-upgrade
# ou
python scripts/scaffold.py upgrade
```

### Passos Automáticos

1. **Detecção de mudanças** (git diff template)
2. **Consolidação** de .copilot-rules (se múltiplos arquivos)
3. **Merge arquivo por arquivo**:
   - Verificar se arquivo aceita merge (via `can_merge()`)
   - Criar backup `.backup` do original
   - Executar merge com estratégia apropriada
   - Validar sintaxe do resultado
   - Rollback automático em caso de erro
4. **Logging** de todas as ações
5. **Relatório** de sucesso/erros

---

## 📦 Backups Automáticos

### Localização
```
.backups/
├── copilot-rules/          # Consolidação .copilot-rules
│   ├── .copilot-rules.md
│   └── .copilot-strict-rules.md
├── *.json.backup           # Backup de JSONs
└── *.code-workspace.backup # Backup de workspaces
```

### Quando são criados
- **Antes de cada merge** (automático)
- **Durante consolidação** .copilot-rules
- **Timestamp** no nome do arquivo (se configurado)

---

## 🚨 Troubleshooting

### Problema: Merge deu errado

**Solução 1**: Restaurar backup
```bash
# Backup está em .backups/ ou arquivo.backup
cp .backups/settings.json.backup .vscode/settings.json
```

**Solução 2**: Revisar log de merge
```bash
cat .backups/merge-2026-05-21-143022.log
```

---

### Problema: Perdi customização importante

**Solução**: Verificar backup antes do merge
```bash
# Comparar versões
diff .vscode/settings.json .vscode/settings.json.backup

# Recuperar campo específico
jq '.editor.rulers' .vscode/settings.json.backup
```

---

### Problema: Consolidação removeu seção importante

**Solução**: Restaurar de backup e consolidar manualmente
```bash
# Restaurar backup
cp .backups/copilot-rules/.copilot-strict-rules.md .

# Editar .copilot-rules.md para adicionar seção
# (seções são mergeadas por headers ##)
```

---

## 🔍 Validação Pós-Upgrade

### Checklist

- [ ] **JSON válido**: Abrir arquivos `.vscode/*.json` no editor (verificar erros)
- [ ] **Workspace funcional**: Fechar e reabrir workspace (verificar pastas)
- [ ] **Copilot rules**: Testar `@workspace /explain` (verificar se regras carregaram)
- [ ] **Dependencies**: `make install-deps` (verificar pyproject.toml)

### Comandos de validação

```bash
# Validar sintaxe JSON
jq empty .vscode/settings.json
jq empty .vscode/mcp.json

# Validar TOML
python -c "import tomllib; tomllib.loads(open('pyproject.toml').read())"

# Listar backups
ls -lh .backups/
```

---

## 📝 Referências

- **BUG-16**: Documentação completa em `docs/bugs/BUG-16-json-workspace-merge-strategy.md`
- **Código fonte**: `scripts/lib/json_merge.py`, `scripts/lib/copilot_rules_consolidate.py`
- **Testes**: `tests/test_json_merge.py` (12 cenários validados)

---

## ❓ FAQ

### 1. O merge é destrutivo?

**Não**. Todos os arquivos recebem backup automático antes do merge. Se algo der errado, você pode restaurar de `.backup` ou `.backups/`.

---

### 2. Posso desabilitar merge automático?

**Sim**. Edite `scripts/lib/file_merge.py` e remova o merger específico da lista `_MERGERS`.

---

### 3. Como funciona "user-wins"?

Suas customizações **sempre** têm prioridade sobre o template. Se você tem `editor.rulers: [120]` e o template tem `editor.rulers: [80]`, o resultado é `[120]` (seu valor).

---

### 4. Arrays são mergeados ou concatenados?

**União de valores**. Se você tem `["ext1"]` e template tem `["ext2"]`, resultado é `["ext1", "ext2"]`. Pode haver duplicatas se valores já existiam.

---

### 5. O que acontece com arquivos não listados?

Arquivos sem merger registrado em `file_merge.py` continuam com comportamento padrão (pode sobrescrever). Para adicionar merge a um tipo de arquivo, implemente um `FileMerger` e registre em `_MERGERS`.

---

### 6. Posso fazer merge manual?

**Sim**. Use as funções diretamente:

```python
from pathlib import Path
from scripts.lib.json_merge import JSONMerger

merger = JSONMerger()
result = merger.merge(
    existing_path=Path(".vscode/settings.json"),
    template_content='{"editor.formatOnSave": true}',
    interactive=False
)
print(result.status)  # "merged" ou "error"
```

---

**Última atualização**: 2026-05-21 (Sprint 2026-W21, BUG-16 Fase 4)
