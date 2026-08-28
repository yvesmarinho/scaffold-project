# BUG-19: git_validators.py Missing Deployment

**Data**: 2026-05-18
**Status**: ✅ RESOLVED
**Severidade**: P0 CRÍTICO
**Projeto**: test-workspace-fix
**Relatado por**: Yves Marinho

---

## 📝 Resumo

Arquivo `scripts/lib/git_validators.py` não foi deployado durante scaffold upgrade, causando erro `ModuleNotFoundError` ao executar `session-time-tracker.py`.

---

## 🐛 Problema

### Sintomas

```bash
$ cd /home/yves_marinho/DevOps/Projetos/test-workspace-fix
$ uv run scripts/session-time-tracker.py start

Traceback (most recent call last):
  File ".../test-workspace-fix/scripts/session-time-tracker.py", line 41, in <module>
    from lib.git_validators import validate_branch_name, format_validation_errors
ModuleNotFoundError: No module named 'lib.git_validators'
```

### Impacto

- ❌ **Ritual de sessão bloqueado**: Passo 6.5 não executa
- ❌ **Time-tracker não inicia**: Validação de branch falhando
- ❌ **Session-start incompleto**: Prompt não valida branch names

---

## 🔍 Análise da Causa Raiz

### 1. Scaffold Upgrade Comportamento

**Log do scaffold**: `logs/scaffold_2026-05-18_15-07-11.log`

```
[SKIPPED] dir | .../test-workspace-fix/scripts/lib
```

**Problema identificado**:
- Pasta `scripts/lib/` já existia → scaffold pulou
- Arquivos **existentes** foram preservados
- Arquivos **novos** não foram copiados

### 2. Estado da Pasta scripts/lib/

**Projeto principal** (`scaffold-project`):
```bash
scripts/lib/
├── __init__.py
├── chat_capture.py
├── git_validators.py    # ← arquivo faltante
├── memory.py
├── search.py
└── ... (40+ arquivos)
```

**Test-workspace-fix** (antes da correção):
```bash
scripts/lib/
├── __init__.py
├── chat_capture.py
├── memory.py
└── search.py
```

### 3. Dependência do session-time-tracker.py

**Linha 41**:
```python
from lib.git_validators import validate_branch_name, format_validation_errors
```

**Uso**:
- Validação de branch name no início da sessão
- Formatação de erros de validação para usuário
- Enforcement de Conventional Commits

---

## 🛠️ Causa Root

**Scaffold upgrade com `--force` NÃO atualiza pastas existentes**:

1. Se pasta `scripts/lib/` existe → **SKIP**
2. Novos arquivos em `template-bases/core/scripts/lib/` → **NÃO copiados**
3. Resultado: pasta desatualizada com arquivos faltantes

### Por que aconteceu?

- Session-time-tracker.py foi atualizado (BUG-17) com nova dependência
- git_validators.py foi adicionado ao core template
- Scaffold upgrade não detecta arquivos novos em pastas existentes
- Merge strategy para `scripts/lib/` não está implementado

---

## ✅ Correção Aplicada

### Deploy Manual via Python stdlib

**Método**: Conforme `.copilot-rules.md` Seção 3

```python
import shutil
from pathlib import Path

src = Path("/home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project/scripts/lib/git_validators.py")
dst = Path("/home/yves_marinho/DevOps/Projetos/test-workspace-fix/scripts/lib/git_validators.py")

shutil.copy2(src, dst)
# ✅ 16443 bytes copiados
# ✅ Verificação: tamanhos idênticos
```

### Resultado

```bash
$ cd /home/yves_marinho/DevOps/Projetos/test-workspace-fix
$ uv run scripts/session-time-tracker.py start

✅ Sessão iniciada: 2026-05-18T15:10:16Z
📅 Data: 2026-05-18
```

**Status**: ✅ Funcionando corretamente

---

## 📊 Evidências

### Antes da Correção

**Comando**:
```bash
ls -la /home/yves_marinho/DevOps/Projetos/test-workspace-fix/scripts/lib/
```

**Resultado**:
```
total 16K
drwxr-xr-x  2 yves yves 4.0K May 18 15:07 .
drwxr-xr-x  3 yves yves 4.0K May 18 15:07 ..
-rw-r--r--  1 yves yves    0 May 18 15:07 __init__.py
-rw-r--r--  1 yves yves 2.1K May 18 15:07 chat_capture.py
-rw-r--r--  1 yves yves 1.8K May 18 15:07 memory.py
-rw-r--r--  1 yves yves 1.5K May 18 15:07 search.py
```

**Total**: 4 arquivos (git_validators.py ausente)

### Após a Correção

**Comando**:
```bash
ls -lh /home/yves_marinho/DevOps/Projetos/test-workspace-fix/scripts/lib/git_validators.py
```

**Resultado**:
```
-rw-r--r-- 1 yves yves 16K May 18 15:10 git_validators.py
```

**Verificação**:
```bash
$ python -c "from scripts.lib.git_validators import validate_branch_name; print('✅ Import OK')"
✅ Import OK
```

---

## 🔧 Proposta de Correção Definitiva

### Opção A: Merge Strategy para scripts/lib/ (RECOMENDADO)

**Implementação**:

1. **Criar merger para Python packages**:
   ```python
   # scripts/lib/python_package_merge.py
   def merge_python_package(src_dir, dst_dir):
       """
       Merge inteligente de packages Python:
       - Copia arquivos novos
       - Preserva customizações existentes
       - Atualiza __init__.py se necessário
       """
   ```

2. **Registrar merger no scaffold**:
   ```python
   # scaffold.py
   MERGE_STRATEGIES = {
       "scripts/lib": python_package_merge,
       # ...
   }
   ```

3. **Scaffold upgrade detecta arquivos novos**:
   - Lista arquivos em `template-bases/core/scripts/lib/`
   - Compara com `test-workspace-fix/scripts/lib/`
   - Copia arquivos faltantes
   - Relata no log: `[ADDED] file | scripts/lib/git_validators.py`

### Opção B: Scaffold --sync-libs Flag

**Uso**:
```bash
python scripts/scaffold.py upgrade --force --sync-libs
```

**Comportamento**:
- Flag especial para sincronizar `scripts/lib/`
- Copia arquivos faltantes
- Preserva customizações
- Backup antes de modificar

### Opção C: Dependency Checker Pre-Upgrade

**Script**: `scripts/check-dependencies.py`

**Uso**:
```bash
# Antes do upgrade
python scripts/check-dependencies.py test-workspace-fix/
```

**Saída**:
```
❌ Dependências faltantes:
  - scripts/lib/git_validators.py (usado por session-time-tracker.py)
  - scripts/lib/spec_validate.py (usado por scaffold.py)

💡 Recomendação: Execute scaffold upgrade com --sync-libs
```

---

## 📚 Arquivos Relacionados

1. **BUG-17**: Time-tracker Missing Deployment
   - Problema anterior: session-start.prompt.md sem Passo 6.5
   - Relação: time-tracker atualizado → nova dependência git_validators

2. **BUG-18**: objetivo-init.yaml Missing Deployment
   - Mesmo padrão: arquivos raiz não copiados no upgrade

3. **Scaffold Log**: `logs/scaffold_2026-05-18_15-07-11.log`
   - Evidência: `[SKIPPED] dir | scripts/lib`

4. **Copilot Rules**: `.copilot-rules.md` Seção 3
   - Regra aplicada: Python stdlib para file operations

---

## 🎯 Lições Aprendidas

### 1. Scaffold Upgrade Gap

**Problema**: Pastas existentes não recebem arquivos novos

**Mitigação**:
- Implementar merge strategy para Python packages
- Adicionar dependency checker
- Documentar arquivos core obrigatórios

### 2. Session-time-tracker Dependencies

**Problema**: Nova dependência não documentada

**Mitigação**:
- Adicionar `requirements.txt` para `scripts/`
- Dependency checker valida imports
- Documentar módulos obrigatórios

### 3. Testing Coverage Gap

**Problema**: Upgrade não testado em projeto real

**Mitigação**:
- Criar suite de testes para upgrade
- Validar imports após upgrade
- Smoke test de scripts críticos

---

## ✅ Checklist de Resolução

- [x] Arquivo `git_validators.py` copiado para test-workspace-fix
- [x] Import `from lib.git_validators import ...` funcionando
- [x] `session-time-tracker.py start` executando sem erros
- [x] Tamanho verificado: 16443 bytes (idêntico ao original)
- [x] BUG report documentado
- [x] Causa root identificada (scaffold upgrade skip)
- [x] Proposta de correção definitiva elaborada

---

## 📝 Notas

### Warnings de Deprecação

```python
DeprecationWarning: datetime.datetime.utcnow() is deprecated
```

**Não relacionado a este BUG**:
- Avisos do Python 3.12+ sobre `datetime.utcnow()`
- Solução: usar `datetime.now(datetime.UTC)` (Python 3.11+)
- Criar issue separado para modernização

### Rich Library

```
⚠️  Install 'rich' for better output: pip install rich
```

**Opcional**:
- Script funciona sem Rich
- Output em texto simples se Rich não disponível
- Não bloqueia funcionalidade

---

## 🔗 Referências

- **Log de Scaffold**: `logs/scaffold_2026-05-18_15-07-11.log`
- **Copilot Rules**: `.copilot-rules.md` (Seção 3: File Operations)
- **BUG-17**: Time-tracker Missing Deployment
- **BUG-18**: objetivo-init.yaml Missing Deployment
- **Git Validators**: `scripts/lib/git_validators.py`
- **Session Time Tracker**: `scripts/session-time-tracker.py`

---

**Resolução**: ✅ COMPLETO
**Commit**: Pendente (incluir no próximo commit de correções)
**Próximo passo**: Implementar Opção A (merge strategy) no scaffold
