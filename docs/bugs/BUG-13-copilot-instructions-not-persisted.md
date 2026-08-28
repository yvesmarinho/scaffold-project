# BUG-13: Copilot Perde Instruções Constantemente Durante Sessões

**Status**: 🔴 ABERTO
**Severidade**: P0 (Crítica — impacta todas as sessões de trabalho)
**Data Descoberta**: 2026-05-13
**Descoberto Por**: Usuário (docs/planning/lembrete.md linha 14-16)
**Relacionado**: [BUG-03](../planning/lembrete.md#L73) (copilot-instructions.md não gerado)

---

## 📋 Sintomas

Durante sessões de trabalho com GitHub Copilot:

1. ❌ **Regras P0 são violadas repetidamente**:
   - Copilot sugere `cat > arquivo.txt` (heredoc) ao invés de `create_file`
   - Copilot sugere `grep -r "padrão"` ao invés de `grep_search`
   - Copilot sugere `git commit -m` ao invés de arquivo de mensagem

2. ❌ **Instruções não persistem entre interações**:
   - Usuário precisa re-explicar as regras múltiplas vezes
   - Mesmo após correção, próxima resposta volta a violar

3. ❌ **Session-start ritual não garante persistência**:
   - Passo 3 de `session-start.prompt.md` diz "Confirmar que .copilot-rules.md está ativo"
   - Mas não há mecanismo técnico para **manter** regras ativas durante toda sessão

**Resultado**: Perda de produtividade e violações constantes das convenções do projeto.

---

## 🔍 Análise de Causa Raiz

### Arquitetura Atual de Instruções

O projeto possui múltiplos arquivos de instruções:

| Arquivo | Propósito | Status no Template | Carregado Pelo Copilot? |
|---------|-----------|-------------------|------------------------|
| `.copilot-rules.md` | Regras comportamentais (7 seções) | ✅ Existe (raiz) | ❓ Não confirmado |
| `.github/.copilot-instructions.md` | Resumo P0+P1 (applyTo: "**") | ✅ Existe (4.6KB) | ❌ **NOME INCORRETO** |
| `.github/copilot-instructions.md` | Padrão VS Code Copilot | ❌ **NÃO EXISTE** | ❓ Esperado pelo VS Code |
| `.copilot-rules-[projeto].md` | Regras específicas do projeto | ⚠️ Gerado pelo scaffold | ❓ Não confirmado |

### Problema 1: Nome de Arquivo Incorreto

**Padrão VS Code Copilot**: `.github/copilot-instructions.md` (SEM ponto inicial)
**Nome atual no template**: `.github/.copilot-instructions.md` (COM ponto inicial)

```bash
# Atual (incorreto)
.github/.copilot-instructions.md

# Esperado pelo VS Code
.github/copilot-instructions.md
```

**Impacto**: VS Code pode não estar carregando o arquivo automaticamente porque o nome não corresponde ao padrão oficial.

**Referência**: [VS Code Copilot Customization Docs](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)

---

### Problema 2: Falta de Integração no Scaffold

**Em `scripts/lib/flows/new_project.py`:**

```bash
# Busca por "copilot-instructions"
grep -n "copilot-instructions" scripts/lib/flows/new_project.py
# (resultado: sem matches)
```

**Conclusão**: O arquivo `.github/.copilot-instructions.md` **NÃO É COPIADO** para novos projetos pelo scaffold.

**Evidência**:
- BUG-03 no lembrete.md: "Não foi gerado o .github/copilot-instructions.md com as instruções básicas existentes"
- Arquivo existe no scaffold-project mas não está integrado no workflow de cópia

---

### Problema 3: Ritual Session-Start Apenas Informativo

**Em `.github/prompts/session-start.prompt.md` Passo 3:**

```markdown
### Passo 3 — Carregar Regras Copilot

Confirmar que `.copilot-rules.md` está ativo e suas regras P0 estão na memória:

| Regra | Verificado |
|-------|-----------|
| P0: Nunca heredoc/echo para criar arquivos | ✅ |
| P0: Nunca cat/grep/find/ls via terminal | ✅ |
```

**Problema**: Essa é uma **checklist manual** que o agente executa, mas:
- ❌ Não há chamada técnica para `read_file(.copilot-rules.md)`
- ❌ Não há verificação se Copilot **realmente carregou** as regras
- ❌ Agente apenas marca "✅" sem ação técnica de persistência

---

## ✅ Solução Proposta

### Correção Completa em 3 Frentes

#### 1. Renomear Arquivo para Padrão VS Code

**Mudança**:
```bash
# DE (nome incorreto)
.github/.copilot-instructions.md

# PARA (padrão VS Code)
.github/copilot-instructions.md
```

**Justificativa**: Nome oficial reconhecido automaticamente pelo VS Code Copilot.

**Implementação**:
- Mover arquivo no scaffold-project
- Atualizar referências em documentação
- Testar carregamento automático

---

#### 2. Integrar no Scaffold (copy_copilot_instructions)

**Criar função em `scripts/lib/project.py`:**

```python
def copy_copilot_instructions(config: ProjectConfig) -> CreatedItem:
    """
    Copia .github/copilot-instructions.md para o novo projeto.

    Arquivo contém:
      - Resumo das regras P0 (críticas)
      - Referência para .copilot-rules.md completo
      - Frontmatter applyTo para escopo

    Arquivo base no template: .github/copilot-instructions.md
    Destino: [projeto]/.github/copilot-instructions.md

    Ref: BUG-13 — copilot instructions not persisted
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT

    src_file = src_root / ".github" / "copilot-instructions.md"
    dst_file = base / ".github" / "copilot-instructions.md"

    result = _copy_file(src_file, dst_file)
    return result
```

**Integração em `scripts/lib/flows/new_project.py`:**

```python
# 5. SpecKit: agents, prompts e perfis de domínio
console.print("  [blue]🤖 Copiando assets SpecKit...[/blue]")
results.extend(project.copy_speckit(cfg))

# 5a. Copilot Instructions: .github/copilot-instructions.md
console.print("  [blue]📋 Copiando instruções do Copilot...[/blue]")
results.append(project.copy_copilot_instructions(cfg))
```

---

#### 3. Atualizar Ritual Session-Start (Passo 3)

**Mudança em `.github/prompts/session-start.prompt.md`:**

```markdown
### Passo 3 — Carregar Regras Copilot (AÇÃO TÉCNICA OBRIGATÓRIA)

**IMPORTANTE**: Não apenas confirmar mentalmente — EXECUTAR as leituras abaixo:

1. Ler `.copilot-rules.md` (fonte de verdade, 7 seções)
2. Ler `.github/copilot-instructions.md` (resumo P0+P1)
3. Se existir `.copilot-rules-[projeto].md`, ler também

**Ação técnica**:
```bash
# Usar read_file para CARREGAR na memória ativa
read_file(.copilot-rules.md, 1, 500)
read_file(.github/copilot-instructions.md, 1, 200)
```

**Ao final, declarar**:
```
✅ Regras carregadas na memória:
- .copilot-rules.md: [N] linhas, 7 seções
- .github/copilot-instructions.md: [N] linhas
- Regras P0 ativas: [listar principais]
```

**Checklist de conformidade durante a sessão**:
- [ ] Nunca heredoc/echo para criar arquivos
- [ ] Nunca cat/grep/find/ls via terminal
- [ ] 3+ arquivos para mover → Python + JSON
- [ ] Git commit ≥6 linhas → arquivo de mensagem
```

---

## 🧪 Validação

### Teste 1: Renomear Arquivo

```bash
# Renomear no scaffold-project
mv .github/.copilot-instructions.md .github/copilot-instructions.md

# Verificar VS Code reconhece
# (abrir projeto, verificar Copilot carrega automaticamente)
```

**Resultado esperado**: VS Code Copilot mostra "Custom instructions loaded" na interface.

---

### Teste 2: Scaffold Copy

```bash
# Criar novo projeto com scaffold atualizado
python scripts/scaffold.py --new --ci \
  --name test-bug13 \
  --domain programming --language python \
  --target-dir /tmp/test-bug13

# Verificar arquivo copiado
ls -lh /tmp/test-bug13/.github/copilot-instructions.md
```

**Resultado esperado**: Arquivo presente (4.6KB, ~100 linhas).

---

### Teste 3: Session-Start Enforcement

```bash
# Executar session-start.prompt.md Passo 3
# Verificar que read_file é EXECUTADO (não apenas marcado ✅)
```

**Resultado esperado**: Log mostra "Lendo .copilot-rules.md... 450 linhas carregadas".

---

## 📊 Impacto

### Antes da Correção
- 🔴 **Instruções perdidas constantemente**
- 🔴 Regras P0 violadas múltiplas vezes por sessão
- 🔴 Usuário precisa re-explicar regras repetidamente
- 🔴 Novos projetos sem copilot-instructions.md

### Depois da Correção
- 🟢 **Instruções persistem durante sessão inteira**
- 🟢 VS Code Copilot carrega automaticamente (nome padrão)
- 🟢 Ritual session-start GARANTE carregamento técnico
- 🟢 Novos projetos já incluem instruções

---

## 🔗 Arquivos Modificados

| Arquivo | Modificação | Linhas |
|---------|-------------|--------|
| `.github/.copilot-instructions.md` | Renomear → `copilot-instructions.md` | 0 (rename) |
| `scripts/lib/project.py` | `+ copy_copilot_instructions()` | +30 |
| `scripts/lib/flows/new_project.py` | `+ step 5a` | +4 |
| `.github/prompts/session-start.prompt.md` | `Passo 3: read_file enforcement` | +20 |
| `docs/bugs/BUG-13-copilot-instructions-not-persisted.md` | Nova documentação | +300 |

---

## 📝 Commits

```bash
# Commit 1: Renomear arquivo
refactor(copilot): Renomear .copilot-instructions.md para padrão VS Code

- .github/.copilot-instructions.md → .github/copilot-instructions.md
- Nome padrão reconhecido automaticamente pelo VS Code Copilot
- Relacionado: BUG-13

# Commit 2: Implementação scaffold
fix(copilot): BUG-13 - Copiar copilot-instructions.md em novos projetos

- Adiciona copy_copilot_instructions() em project.py
- Integra em new_project.py como step 5a
- Garante que novos projetos incluam instruções do Copilot
- Relacionado: BUG-03, BUG-13

# Commit 3: Atualizar ritual
fix(session): Garantir carregamento técnico de regras no session-start

- Atualiza Passo 3 de session-start.prompt.md
- Adiciona ação técnica obrigatória: read_file das regras
- Checklist de conformidade durante sessão
- Relacionado: BUG-13
```

---

## 🎯 Próximos Passos

1. ✅ Documentar BUG-13
2. ⏳ Renomear `.github/.copilot-instructions.md` → `copilot-instructions.md`
3. ⏳ Implementar `copy_copilot_instructions()`
4. ⏳ Integrar em `new_project.py`
5. ⏳ Atualizar `session-start.prompt.md` Passo 3
6. ⏳ Testar em novo projeto
7. ⏳ Validar persistência das instruções durante sessão

---

## 🔗 Referências

- [VS Code Copilot Custom Instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
- [GitHub Copilot Instructions File Format](https://code.visualstudio.com/docs/copilot/customization/custom-instructions#_file-format)
- `.copilot-rules.md` — Regras completas do projeto (7 seções)
- `.github/prompts/session-start.prompt.md` — Ritual de início de sessão

---

**Tags**: `copilot`, `instructions`, `persistence`, `session-start`, `bug`, `P0`
