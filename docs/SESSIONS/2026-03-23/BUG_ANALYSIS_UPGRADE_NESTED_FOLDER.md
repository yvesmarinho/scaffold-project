# 🐛 Bug Report: Upgrade Cria Pasta Aninhada do Projeto

**Data**: 2026-03-23
**Severidade**: 🔴 CRÍTICO
**Afeta**: Modo `scaffold.py upgrade`
**Status**: ⚠️ REPRODUZIDO

---

## 📋 Sumário

Ao executar `scaffold.py upgrade` no projeto `enterprise-python-analysis`, o comando criou uma pasta aninhada:

```
enterprise-python-analysis/
└── enterprise-python-analysis/  ← DUPLICAÇÃO INDEVIDA
    ├── .github/
    ├── docs/
    └── ... estrutura completa duplicada
```

---

## 🔍 Análise Detalhada

### Estrutura Observada

**Antes do upgrade:**
```
/home/yves_marinho/Documentos/DevOps/Vya-Jobs/
└── enterprise-python-analysis/
    ├── .scaffold-state.yaml  ← CRIADO MANUALMENTE
    ├── .github/
    ├── docs/
    └── ... arquivos existentes
```

**Depois do `upgrade`:**
```
/home/yves_marinho/Documentos/DevOps/Vya-Jobs/
└── enterprise-python-analysis/
    ├── .scaffold-state.yaml
    ├── .github/
    ├── docs/
    ├── ... arquivos existentes (preservados)
    └── enterprise-python-analysis/  ← NOVA PASTA ANINHADA
        ├── .github/
        │   └── agents/
        │       └── session-manager.agent.md  ← CRIADO AQUI
        ├── docs/
        ├── scripts/
        └── .scaffold-state.yaml  ← DUPLICADO
```

---

## 🐛 Causa Raiz

### 1. Design do `ProjectConfig.project_path`

**Arquivo:** `scripts/lib/config.py:141-143`

```python
@property
def project_path(self) -> Path:
    """Retorna o caminho completo do projeto: target_dir / project_name."""
    return self.target_dir / self.project_name
```

**Comportamento:**
- `project_path` SEMPRE concatena `target_dir + project_name`
- Funciona perfeitamente para modo `--new` (onde `target_dir` é o diretório PAI)
- Quebra no modo `upgrade` (onde `target_dir` pode ser o próprio projeto)

---

### 2. `.scaffold-state.yaml` Criado Incorretamente

**Arquivo criado:** `/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-analysis/.scaffold-state.yaml`

```yaml
scaffold_version: "1.0.0"
created_at: "2026-01-16T00:00:00Z"
updated_at: "2026-03-23T15:30:00Z"
project:
  name: enterprise-python-analysis
  # ...
paths:
  target_dir: /home/yves_marinho/Documentos/DevOps/Vya-Jobs  ← DIRETÓRIO PAI
  shared_dir: /home/yves_marinho/Documentos/DevOps/.copilot-shared
```

**Problema:**
- `target_dir` aponta para o diretório PAI
- Comando executado: `scaffold.py upgrade --target-dir /path/to/enterprise-python-analysis`
- `override_target` = `/path/to/enterprise-python-analysis`

---

### 3. Fluxo de Execução do Upgrade

**Arquivo:** `scripts/lib/flows/upgrade.py:30-48`

```python
def flow_upgrade(args: argparse.Namespace) -> int:
    # Linha 33: target vem de --target-dir ou cwd
    target = Path(args.target_dir) if args.target_dir else Path.cwd()

    # Linha 35: lê .scaffold-state.yaml de 'target'
    state = read_scaffold_state(target)

    # Linha 48: reconstrói config COM OVERRIDE
    cfg = config_from_state(state, override_target=target)
```

**Arquivo:** `scripts/lib/project.py:906-935`

```python
def config_from_state(state: dict, override_target: Path | None = None) -> ProjectConfig:
    proj = state.get("project", {})
    paths = state.get("paths", {})

    # Linha 920: OVERRIDE sobrescreve target_dir do state
    target = override_target or Path(paths.get("target_dir", "."))

    return ProjectConfig(
        project_name=proj.get("name", "unknown"),  # "enterprise-python-analysis"
        # ...
        target_dir=target,  # /path/to/enterprise-python-analysis
        # ...
    )
```

**Resultado:**
- `cfg.target_dir` = `/home/.../Vya-Jobs/enterprise-python-analysis`
- `cfg.project_name` = `enterprise-python-analysis`
- `cfg.project_path` = `target_dir / project_name`
                      = `/home/.../enterprise-python-analysis/enterprise-python-analysis` ❌

---

### 4. `create_structure` Usa `project_path`

**Arquivo:** `scripts/lib/project.py:454-467`

```python
def create_structure(config: ProjectConfig) -> list[CreatedItem]:
    """Cria a estrutura de pastas e arquivos base do projeto."""
    results: list[CreatedItem] = []
    base = config.project_path  # ← USA project_path!
    base.mkdir(parents=True, exist_ok=True)  # ← CRIA PASTA ANINHADA!

    # Continua criando estrutura dentro de 'base'
    for dir_rel in DIRS_TO_CREATE:
        dir_path = base / dir_rel
        # ...
```

**Resultado final:**
```
/home/.../enterprise-python-analysis/enterprise-python-analysis/ ← CRIADO AQUI
```

---

## 🎯 Comparação: Modo `--new` vs `upgrade`

### Modo `--new` (✅ FUNCIONA)

```bash
scaffold.py --new --target-dir /home/user/projects
```

**Fluxo:**
1. `target_dir` = `/home/user/projects` (diretório PAI informado)
2. Usuário informa nome: `my-api`
3. `project_name` = `my-api`
4. `project_path` = `/home/user/projects/my-api` ✅ CORRETO
5. Estrutura criada em `/home/user/projects/my-api/` ✅

---

### Modo `upgrade` (❌ QUEBRADO)

```bash
cd /home/user/projects/my-api
scaffold.py upgrade --target-dir /home/user/projects/my-api
```

**Fluxo:**
1. `target_dir` (do state) = `/home/user/projects` (histórico)
2. `override_target` = `/home/user/projects/my-api` (passado via CLI)
3. `config_from_state` substitui `target_dir` por `override_target`
4. `cfg.target_dir` = `/home/user/projects/my-api`
5. `cfg.project_name` = `my-api` (do state)
6. `cfg.project_path` = `/home/user/projects/my-api/my-api` ❌ DUPLICADO
7. Estrutura criada em `/home/user/projects/my-api/my-api/` ❌

---

## 🛠️ Soluções Possíveis

### Opção A: Corrigir `config_from_state` (Recomendado)

**Localização:** `scripts/lib/project.py:906`

**Estratégia:** Detectar se `override_target` já inclui o nome do projeto e ajustar `target_dir` para ser o pai.

```python
def config_from_state(state: dict, override_target: Path | None = None) -> ProjectConfig:
    proj = state.get("project", {})
    paths = state.get("paths", {})
    project_name = proj.get("name", "unknown")

    if override_target:
        # Modo upgrade: override_target É O PRÓPRIO PROJETO
        # Extrai target_dir como o diretório pai
        if override_target.name == project_name:
            target = override_target.parent
        else:
            # Fallback: assume que override_target é o diretório pai
            target = override_target
    else:
        # Modo normal: usa target_dir do state
        target = Path(paths.get("target_dir", "."))

    shared = Path(paths.get("shared_dir", str(
        Path.home() / "Documentos" / "DevOps" / ".copilot-shared"
    )))

    return ProjectConfig(
        project_name=project_name,
        # ...
        target_dir=target,
        # ...
    )
```

**Vantagem:** Corrige o problema na raiz
**Desvantagem:** Lógica adicional de detecção

---

### Opção B: Criar `.scaffold-state.yaml` Correto

**Estratégia:** O `.scaffold-state.yaml` deve sempre ter `target_dir` apontando para o diretório PAI, não para o projeto.

**Correto:**
```yaml
paths:
  target_dir: /home/yves_marinho/Documentos/DevOps/Vya-Jobs  # PAI
```

**Comando de upgrade:**
```bash
scaffold.py upgrade --target-dir /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-analysis
```

**Resultado:**
- `override_target` = `.../enterprise-python-analysis`
- Se `override_target.name == project_name` → extrai pai
- `target_dir` = `.../Vya-Jobs`
- `project_path` = `.../Vya-Jobs/enterprise-python-analysis` ✅

**Vantagem:** Simples, não altera código
**Desvantagem:** Depende de documentação correta

---

### Opção C: Adicionar Flag `is_upgrade` ao `ProjectConfig`

**Estratégia:** Modificar `project_path` para não concatenar no modo upgrade.

```python
@dataclass
class ProjectConfig:
    # ... campos existentes ...
    is_upgrade: bool = False  # Novo campo

    @property
    def project_path(self) -> Path:
        """Retorna o caminho completo do projeto."""
        if self.is_upgrade:
            # Modo upgrade: target_dir JÁ É o projeto
            return self.target_dir
        else:
            # Modo new: target_dir é o pai
            return self.target_dir / self.project_name
```

**Vantagem:** Solução explícita e clara
**Desvantagem:** Adiciona complexidade ao dataclass

---

### Opção D: Documentar Comportamento Atual

**Estratégia:** Aceitar que `target_dir` no state deve sempre ser o PAI.

**Documentação:**
```markdown
### `.scaffold-state.yaml` - Campo `paths.target_dir`

⚠️ **IMPORTANTE**: `target_dir` deve SEMPRE apontar para o diretório PAI do projeto,
NÃO para o próprio diretório do projeto.

**Correto:**
```yaml
paths:
  target_dir: /home/user/projects  # Diretório PAI
```

**Incorreto:**
```yaml
paths:
  target_dir: /home/user/projects/my-api  # NÃO incluir nome do projeto
```

Quando executar `scaffold.py upgrade`, passe o caminho completo do projeto:
```bash
scaffold.py upgrade --target-dir /home/user/projects/my-api
```

O código extrairá automaticamente o diretório pai.
```

**Vantagem:** Sem mudança de código
**Desvantagem:** Não resolve projetos já criados incorretamente

---

## 🔧 Solução Imediata (Workaround)

Para o projeto `enterprise-python-analysis` atual:

### 1. Remover Pasta Aninhada

```python
import shutil
from pathlib import Path

nested = Path("/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-analysis/enterprise-python-analysis")
if nested.exists():
    shutil.rmtree(nested)
    print(f"✅ Removida pasta aninhada: {nested}")
```

### 2. Corrigir `.scaffold-state.yaml`

```bash
# Não precisa alterar - já está correto:
# target_dir: /home/yves_marinho/Documentos/DevOps/Vya-Jobs
```

### 3. Re-executar Upgrade Corretamente

**OPÇÃO 1: Passar diretório PAI**
```bash
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project
python scripts/scaffold.py upgrade \
  --target-dir /home/yves_marinho/Documentos/DevOps/Vya-Jobs
# ❌ Mas isso não sabe qual projeto atualizar!
```

**OPÇÃO 2: Executar do dentro do projeto SEM --target-dir**
```bash
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-analysis
python ../scaffold-project/scripts/scaffold.py upgrade
# ✅ Usa Path.cwd() como target
```

Porém, isso ainda quebrará pelo mesmo motivo!

---

## 🎓 Lição Aprendida

### O Problema Fundamental

O design atual mistura duas semânticas para `target_dir`:

| Contexto | Significado de `target_dir` |
|----------|----------------------------|
| Modo `--new` | Diretório PAI onde criar o projeto |
| `.scaffold-state.yaml` | Diretório PAI (histórico da criação) |
| `upgrade --target-dir` | Caminho DO PRÓPRIO PROJETO (atual) |
| `project_path` | Sempre concatena `target_dir + name` |

**Inconsistência:** `upgrade` assume que `target_dir` pode ser o projeto, mas `project_path` sempre concatena.

---

## 📋 Recomendação

### Implementar **Opção A** (Corrigir `config_from_state`)

**Por quê:**
1. ✅ Resolve o problema na raiz
2. ✅ Mantém compatibilidade com states existentes
3. ✅ Permite `upgrade --target-dir /path/to/project` (intuitivo)
4. ✅ Não quebra modo `--new`

**Onde aplicar:**
- Arquivo: `scripts/lib/project.py`
- Função: `config_from_state()`
- Linhas: ~920

**Teste após correção:**
```bash
# 1. Criar state correto
# 2. Executar upgrade
scaffold.py upgrade --target-dir /path/to/project
# 3. Verificar: NÃO deve criar pasta aninhada
# 4. Verificar: session-manager.agent.md criado no lugar certo
```

---

## 📎 Arquivos Relacionados

- `scripts/lib/config.py:141-143` — Definição de `project_path`
- `scripts/lib/project.py:454-467` — Uso de `project_path` em `create_structure`
- `scripts/lib/project.py:906-935` — Função `config_from_state`
- `scripts/lib/flows/upgrade.py:30-48` — Fluxo do comando upgrade
- `docs/TODO.md:45-51` — Menção ao bug "Projeto criado em diretório incorreto"

---

**🏷️ Tags**: #bug #upgrade #scaffold #project-path #critical
**🔗 Related**: IMP-13 (Bug fix CRÍTICO: Projeto criado em diretório incorreto)

---

*Análise criada em 2026-03-23 por GitHub Copilot*
