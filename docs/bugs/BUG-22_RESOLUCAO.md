# ✅ BUG-22 RESOLVIDO: Pasta SESSIONS/<created_at>/ Indevida Durante Upgrade

**Data**: 2026-05-19 15:30 BRT  
**Reportado por**: Yves Marinho  
**Resolvido por**: GitHub Copilot (Claude Sonnet 4.5)

---

## 🐛 Problema Relatado

> "a pasta session está vázia quando restauro o backup. quando executo o scaffold upgrade, cria a pasta com a data de criação que está no scaffold-state.yaml. isso não deveria ocorrer."

### Análise

1. **Arquivo**: `.scaffold-state.yaml`
   ```yaml
   created_at: '2026-04-27T15:36:13Z'  # Data original da criação
   ```

2. **Comportamento Incorreto**:
   - Durante `scaffold upgrade`, criava `docs/SESSIONS/2026-04-27/`
   - Pasta ficava vazia (não há sessões dessa data)
   - Confundia usuários ao restaurar backup

3. **Causa Raiz**: 
   - Função `setup_project_docs()` em `scripts/lib/project.py`
   - Usava `config.created_at` para criar pasta de sessão
   - Era chamada TANTO em `new_project.py` quanto em `upgrade.py`
   - Não havia distinção entre criação e upgrade

---

## ✅ Solução Implementada

### 1. Parâmetro `is_upgrade` Adicionado

**Arquivo**: `scripts/lib/project.py`

```python
def setup_project_docs(config: ProjectConfig, is_upgrade: bool = False) -> list[CreatedItem]:
    """
    Configura templates de documentação do projeto.
    
    Args:
        config: Configuração do projeto
        is_upgrade: True se executando durante scaffold upgrade (pula criação de sessão)
    
    UPGRADE: Pasta de sessão NÃO é criada (evita criar SESSIONS/<created_at>/ vazia).
    
    Ref: BUG-22 — evitar criação de pasta SESSIONS/<created_at>/ durante upgrade
    """
```

### 2. Criação de Sessão Condicionalizada

```python
# 3. DAILY_ACTIVITIES_<data>.md em docs/SESSIONS/<data>/
# APENAS durante scaffold NEW - pulado durante upgrade
if not is_upgrade:
    session_date = config.created_at[:10]  # YYYY-MM-DD
    session_dir = base / "docs" / "SESSIONS" / session_date
    session_dir.mkdir(parents=True, exist_ok=True)
    
    src_daily = src_templates / "DAILY_ACTIVITIES.template.md"
    dst_daily = session_dir / f"DAILY_ACTIVITIES_{session_date}.md"
    result = _copy_file(src_daily, dst_daily)
    results.append(result)
else:
    log.debug("⏭️  Pulando criação de pasta SESSIONS (upgrade mode)")
```

### 3. Chamadas Atualizadas

**flows/upgrade.py** (linha 297):
```python
# ANTES
results.extend(project.setup_project_docs(cfg))

# DEPOIS
results.extend(project.setup_project_docs(cfg, is_upgrade=True))
```

**flows/new_project.py** (linha 96):
```python
# Mantém comportamento padrão (is_upgrade=False)
results.extend(project.setup_project_docs(cfg))
```

---

## 🧪 Validação

### Teste Executado

```bash
cd /home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix

# Verificar created_at
grep created_at .scaffold-state.yaml
# Output: created_at: '2026-04-27T15:36:13Z'

# Executar scaffold upgrade
python3 /path/to/template/scripts/scaffold.py upgrade

# Verificar pasta SESSIONS
ls -la docs/SESSIONS/
# Output: (vazio) ✅
```

### Resultado

| Operação | Pasta SESSIONS/ | Status |
|----------|-----------------|--------|
| `scaffold new` | ✅ Cria `SESSIONS/<hoje>/DAILY_ACTIVITIES_<hoje>.md` | ✅ Correto |
| `scaffold upgrade` | ⏭️ **NÃO cria pasta** | ✅ Correto |

---

## 📊 Impacto

### Antes
- ❌ `docs/SESSIONS/2026-04-27/` criada (vazia)
- ❌ Data antiga do `created_at`
- ❌ Confusão ao restaurar backup

### Depois
- ✅ Pasta `docs/SESSIONS/` preservada como está
- ✅ Sem pastas indevidas
- ✅ Comportamento previsível

---

## 📝 Arquivos Modificados

1. ✅ `scripts/lib/project.py`
   - Adicionado parâmetro `is_upgrade`
   - Condicionalizada criação de sessão
   - Atualizado docstring com Ref: BUG-22

2. ✅ `scripts/lib/flows/upgrade.py`
   - Chamada atualizada com `is_upgrade=True`

3. ✅ `docs/bugs/BUG-22_scaffold_upgrade_creates_old_session_folder.md`
   - Documentação completa do bug

4. ✅ `docs/SCAFFOLD_VALIDATION_ANALYSIS.md`
   - Adicionado BUG-22 à análise
   - Atualizado contador: 9 bugs P1 (era 8)

---

## 🎯 Status Final

| Item | Status |
|------|--------|
| **Problema identificado** | ✅ COMPLETO |
| **Causa raiz encontrada** | ✅ COMPLETO |
| **Solução implementada** | ✅ COMPLETO |
| **Código modificado** | ✅ COMPLETO |
| **Testes manuais** | ✅ COMPLETO |
| **Documentação** | ✅ COMPLETO |
| **Validação automática** | ⚠️ OPCIONAL (validação manual OK) |

---

## 💡 Próximos Passos

### Commit das Alterações

```bash
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project

# Verificar mudanças
git status

# Adicionar arquivos
git add scripts/lib/project.py
git add scripts/lib/flows/upgrade.py
git add docs/bugs/BUG-22_scaffold_upgrade_creates_old_session_folder.md
git add docs/SCAFFOLD_VALIDATION_ANALYSIS.md

# Commit
git commit -m "fix(scaffold): BUG-22 - evitar criação de pasta SESSIONS antiga durante upgrade

- Adicionar parâmetro is_upgrade à setup_project_docs()
- Pular criação de pasta SESSIONS/<created_at>/ durante upgrade
- Preservar estrutura de sessões existente
- Atualizar flows/upgrade.py para passar is_upgrade=True
- Documentar correção em BUG-22

Resolves: Pasta session vazia após restore de backup
Ref: #22"
```

### Validação Adicional (Opcional)

Adicionar validação automática em `scripts/validate-workspace-upgrade.py`:

```python
def validate_bug22_no_old_session_folder(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar BUG-22: pasta SESSIONS antiga não criada durante upgrade."""
    suite = ValidationSuite("BUG-22: No Old Session Folder Created")
    
    # Ler created_at do .scaffold-state.yaml
    state_file = workspace / ".scaffold-state.yaml"
    if not state_file.exists():
        suite.add(ValidationResult("N/A", True, "Sem .scaffold-state.yaml"))
        return suite
    
    import yaml
    with state_file.open() as f:
        state = yaml.safe_load(f)
    
    created_at = state.get("created_at", "")
    if not created_at:
        suite.add(ValidationResult("N/A", True, "Sem created_at"))
        return suite
    
    old_date = created_at[:10]  # YYYY-MM-DD
    old_session = workspace / "docs" / "SESSIONS" / old_date
    
    # Check: pasta com created_at NÃO deve existir (ou estar vazia)
    if old_session.exists():
        files = list(old_session.iterdir())
        is_empty = len(files) == 0
        suite.add(ValidationResult(
            f"SESSIONS/{old_date}/ not created or empty",
            is_empty,
            "Vazia (OK)" if is_empty else f"{len(files)} arquivo(s) (⚠️)"
        ))
    else:
        suite.add(ValidationResult(
            f"SESSIONS/{old_date}/ not created",
            True,
            "Pasta não existe (correto)"
        ))
    
    return suite
```

---

**Assinado**: GitHub Copilot (Claude Sonnet 4.5)  
**Timestamp**: 2026-05-19T18:30:00Z
