# 🧪 Teste de Scaffold Upgrade - test-workspace-fix

**Data**: 2026-05-19
**Responsável**: @yves_marinho
**Objetivo**: Validar que o scaffold upgrade aplica corretamente o BUG-20 fix

---

## 📋 Problema Identificado

O comando `scaffold.py --upgrade --force --target-dir <PATH>` estava entrando em **modo interativo** pedindo escolha de paths, e nenhuma das tentativas de automatização funcionou:

❌ `echo "1" | python scripts/scaffold.py --upgrade --force`
❌ `python scripts/scaffold.py --upgrade --force --auto`
❌ `python scripts/scaffold.py --upgrade --force --target-dir <PATH>`

**Causa Raiz**: O código em [scripts/lib/flows/upgrade.py](../../scripts/lib/flows/upgrade.py#L89-L93) usa `rich.Prompt.ask()` que não aceita input via stdin/pipe.

---

## ✅ Correções Aplicadas Manualmente

Antes do teste do scaffold upgrade, foram aplicadas estas correções MANUAIS em `test-workspace-fix`:

### 1. .scaffold-state.yaml
- ✅ `target_dir` atualizado para `/home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix`
- ✅ `updated_at` atualizado para timestamp atual (2026-05-19T15:22:35Z)

### 2. .vscode/mcp.json
- ✅ Removido `type="stdio"` de servidores npx (memory, sequential-thinking, filesystem)
- ✅ GitHub migrado para HTTP: `{"type": "http", "url": "https://api.githubcopilot.com/mcp/"}`

### 3. Pasta logs/
- ✅ Criada em `/home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix/logs/`

**Resultado**: BUG-20 validação agora passa 7/7 ✅

---

## 🎯 Teste a Executar

### Opção 1: Usando --json (Recomendado - Não Interativo)

```bash
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project

python scripts/scaffold.py \
  --upgrade \
  --force \
  --json \
  --target-dir /home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix
```

**Vantagem**: Bypassa o prompt interativo (modo JSON assume paths atuais automaticamente).

---

### Opção 2: Executando do Workspace (Mais Limpo)

```bash
cd /home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix

python /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project/scripts/scaffold.py \
  upgrade \
  --force
```

**Vantagem**: Usa o novo subcommand syntax (sem deprecation warning).

---

### Opção 3: Modo Interativo (Responder "1")

```bash
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project

python scripts/scaffold.py \
  --upgrade \
  --force \
  --target-dir /home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix
```

Quando aparecer o prompt:
```
  Escolha uma opção:

    1 - Usar path atual e atualizar .scaffold-state.yaml
        /home/yves_marinho/Documentos/DevOps/Projetos

    2 - Cancelar upgrade (execute do diretório salvo)
        ...

  Sua escolha [1/2] (1):
```

**Digite**: `1` + ENTER

---

## 📊 Validação Pós-Upgrade

Após o scaffold upgrade, execute a validação:

```bash
python /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project/scripts/validate-workspace-upgrade.py \
  /home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix
```

### ✅ Expectativas de Sucesso

**BUG-20** (7/7 - já validado ✅):
- mcp.json existe e é JSON válido
- 4 servidores MCP configurados
- Nenhum type="stdio" obsoleto
- GitHub com type="http" e URL correta

**BUG-17** (2/2 - espera-se após scaffold):
- session-time-tracker.py existe
- session-start tem Step 6.5 atualizado

**BUG-18** (3/3 - já validado ✅):
- objetivo.yaml existe, válido e com project info

**BUG-19** (1/1 - espera-se após scaffold):
- git_validators.py existe

**Arquivos Críticos** (6/6 - 5/6 atualmente):
- .scaffold-state.yaml com estrutura e conteúdo corretos ✅
- .copilot-rules.md existe e tem regras P0 (espera-se após scaffold)
- .vscode/settings.json válido com configurações ✅

**Logs** (1/1 - espera-se após scaffold):
- Arquivo de log do scaffold upgrade criado em `logs/scaffold_*.log`

---

## 🎯 Meta de Validação

**Antes do scaffold upgrade**: 17/23 (73,9%)
**Após o scaffold upgrade**: **≥ 22/23** (95,7%)

**Única falha aceitável**: BUG-001 docstyle vazio (conteúdo do usuário, não do scaffold)

---

## 📝 Notas

1. **Path Correto**: Sempre use `/home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix` (com "Documentos")

2. **Subcommand Syntax**: O novo formato é `scaffold.py upgrade` (sem `--upgrade`), mas `--upgrade` ainda funciona com deprecation warning

3. **Modo --json**: Útil para CI/CD, mas não mostra output colorido

4. **Log de Scaffold**: Após upgrade, verifique `logs/scaffold_*.log` para detalhes das mudanças aplicadas

---

## 🐛 Reportar Problemas

Se o scaffold upgrade falhar ou se a validação não atingir 22/23 PASS, reporte:

1. Comando exato executado
2. Output completo (erros, warnings)
3. Resultado da validação (`validate-workspace-upgrade.py`)
4. Conteúdo de `logs/scaffold_*.log` (se criado)
