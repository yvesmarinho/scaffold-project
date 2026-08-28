---
bug_id: BUG-18
title: "objetivo-init.yaml e objetivo-init-minimal.yaml não deployados no test-workspace-fix"
status: "open"
severity: "medium"
priority: "P2"
created: 2026-05-18
reporter: "yves_marinho"
resolved: null
resolution: null
branch: null
commits: []
---

# BUG-18: objetivo-init.yaml e objetivo-init-minimal.yaml Não Deployados no test-workspace-fix

## 📋 Descrição

Os arquivos de template **objetivo-init.yaml** e **objetivo-init-minimal.yaml** não foram deployados no projeto de testes `test-workspace-fix`. Estes arquivos são **essenciais** para:
- Inicialização de novos projetos via `scaffold.py objetivo-init`
- Demonstração de exemplos práticos de objetivo.yaml
- Testes de validação do wizard interativo

## 🔍 Causa Raiz

**Arquivos ausentes** em `/home/yves_marinho/DevOps/Projetos/test-workspace-fix/`:
- ❌ `objetivo-init.yaml` (exemplo completo)
- ❌ `objetivo-init-minimal.yaml` (exemplo mínimo)

**Arquivos presentes no projeto principal** (`scaffold-project`):
- ✅ `/objetivo-init.yaml` (raiz do projeto)
- ✅ `/objetivo-init-minimal.yaml` (raiz do projeto)
- ✅ `/template-bases/examples/objetivo-init.yaml`
- ✅ `/template-bases/examples/objetivo-init-minimal.yaml`
- ✅ `/docs/guides/objetivo-init.yaml`

**Provável causa**: Scaffold upgrade não inclui arquivos de exemplo da raiz por padrão (apenas estrutura de pastas obrigatórias).

## 📊 Evidências

### Verificação de Arquivos

```bash
# Test-workspace-fix (AUSENTES) ❌
ls -l /home/yves_marinho/DevOps/Projetos/test-workspace-fix/objetivo-init*.yaml
ls: cannot access 'objetivo-init*.yaml': No such file or directory

# Projeto principal (PRESENTES) ✅
ls -l /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project/objetivo-init*.yaml
-rw-r--r-- 1 user user 15234 mai 15 14:30 objetivo-init.yaml
-rw-r--r-- 1 user user  2341 mai 15 14:30 objetivo-init-minimal.yaml
```

### Dependências Afetadas

**Comandos que falharão sem estes arquivos**:

1. **Inicialização via template**:
   ```bash
   cd test-workspace-fix
   python scripts/scaffold.py objetivo-init --template-only
   # ❌ ERRO: objetivo-init.yaml não encontrado
   ```

2. **Validação de exemplos**:
   ```bash
   python scripts/manage.py objetivo validate objetivo-init.yaml
   # ❌ ERRO: arquivo não encontrado
   ```

3. **Testes de wizard**:
   ```bash
   pytest tests/test_objetivo_wizard.py
   # ⚠️ Testes pulados (SKIP) por falta de fixtures
   ```

## 🎯 Impacto

**Severidade**: Média
**Frequência**: A cada teste de inicialização de projeto
**Usuários afetados**: Desenvolvedores testando scaffold objetivo-init
**Área afetada**: Validação de templates, testes E2E, documentação por exemplos

**Impacto operacional**:
- Impossível testar `scaffold.py objetivo-init` no workspace de testes
- Testes de validação incompletos
- Documentação de exemplos não reproduzível
- Drift entre projeto principal e workspace de testes

## 🔧 Análise de Dependências

### Arquivos Necessários

| Arquivo | Propósito | Tamanho | Essencial |
|---------|-----------|---------|-----------|
| `objetivo-init.yaml` | Exemplo completo (4 camadas) | ~15KB | ✅ Sim |
| `objetivo-init-minimal.yaml` | Exemplo mínimo (POC) | ~2KB | ✅ Sim |
| `template-bases/objetivo-init-template.yaml` | Template base | ~8KB | ⚠️ Já existe |

### Referências no Código

**scaffold.py** (linha 554):
```python
# --objetivo-init: initialize objetivo.yaml via wizard or template
if args.objetivo_init:
    from scripts.lib.flows.objetivo_init import run_objetivo_init

    # Procura por objetivo-init.yaml na raiz
    template_path = project_root / "objetivo-init.yaml"
    if not template_path.exists():
        raise FileNotFoundError(f"Template não encontrado: {template_path}")
```

**README.md** (linha 128):
```bash
# Wizard interativo
scaffold.py objetivo-init

# Modo não-interativo (requer objetivo-init.yaml)
scaffold.py objetivo-init --from-file answers.json

# Apenas copiar template
scaffold.py objetivo-init --template-only
```

## 💡 Proposta de Correção

### Opção A: Deploy Manual (Rápido)

```python
import shutil
from pathlib import Path

src_root = Path("/home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project")
dst_root = Path("/home/yves_marinho/DevOps/Projetos/test-workspace-fix")

files_to_copy = [
    "objetivo-init.yaml",
    "objetivo-init-minimal.yaml"
]

for file in files_to_copy:
    src = src_root / file
    dst = dst_root / file
    shutil.copy2(src, dst)
    print(f"✅ {file} → test-workspace-fix/")
```

**Vantagens**:
- ✅ Correção imediata
- ✅ Sem mudanças no scaffold.py

**Desvantagens**:
- ❌ Requer deploy manual a cada atualização
- ❌ Drift entre projetos persiste

### Opção B: Incluir no Scaffold Upgrade (Sustentável)

Modificar `scripts/lib/flows/upgrade.py` para copiar arquivos de exemplo:

```python
def _copy_example_files(template_root: Path, project_root: Path):
    """Copy example files if they don't exist."""
    examples = [
        "objetivo-init.yaml",
        "objetivo-init-minimal.yaml"
    ]

    for example in examples:
        src = template_root / example
        dst = project_root / example

        if not dst.exists() and src.exists():
            shutil.copy2(src, dst)
            log.info(f"✅ Example copied: {example}")
```

**Vantagens**:
- ✅ Automático em próximos upgrades
- ✅ Paridade garantida com template

**Desvantagens**:
- ⚠️ Requer mudança no código scaffold
- ⚠️ Aumenta escopo do upgrade

### Recomendação: **Opção A** (deploy manual imediato)

**Justificativa**:
1. Bug P2 (não crítico) — correção rápida suficiente
2. Opção B pode ser implementada em IMP futuro (melhoria de scaffold)
3. Permite testes imediatos sem mudanças estruturais

## 🔄 Próximos Passos

- [ ] Executar deploy manual (Opção A)
- [ ] Validar `scaffold.py objetivo-init --template-only`
- [ ] Executar testes de validação
- [ ] Atualizar documentação
- [ ] (Opcional) Criar IMP para Opção B

## 📚 Documentação Relacionada

- [objetivo-init.yaml](../../objetivo-init.yaml) — Exemplo completo
- [template-bases/examples/README.md](../../template-bases/examples/README.md)
- [docs/guides/OBJETIVO_WIZARD_GUIDE.md](../guides/OBJETIVO_WIZARD_GUIDE.md)
- [.copilot-rules.md](../../.copilot-rules.md) — Seção 3 (Python stdlib)

## 🏷️ Tags

`deployment` `test-workspace` `templates` `objetivo-init` `examples` `documentation`
