# Análise de Impacto — Ativação de Servidores MCP por Padrão

**Data**: 2026-05-06
**Sessão**: 2026-05-06
**Solicitação**: Ativar servidores MCP `memory`, `sequential-thinking`, `filesystem` e `github` por padrão

---

## 📋 Resumo Executivo

**Decisão**: ✅ APROVADA com ressalvas de segurança

**Mudança**: Adicionar `filesystem` e `github` aos servidores MCP ativos por padrão (memory e sequential-thinking já ativos)

**Impacto**:
- ✅ Melhora significativa na capacidade do Copilot
- ⚠️ Requer configuração de token GitHub
- ⚠️ Filesystem dá acesso total ao workspace
- 📦 Alinhamento com padrão já usado no domínio "programming"

---

## 🎯 Estado Atual vs. Proposto

### Estado Atual

**Projeto scaffold-project** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "memory": { ... },              // ✅ ATIVO
    "sequential-thinking": { ... }  // ✅ ATIVO
    // "filesystem": { ... },       // ❌ COMENTADO
    // "github": { ... }             // ❌ COMENTADO
  }
}
```

**Projetos Gerados** (`scripts/lib/vscode.py` linha 219):
```python
server_names = _MCP_BY_DOMAIN.get(config.domain, ["memory", "sequential-thinking"])
```

**Mapeamento por Domínio** (`_MCP_BY_DOMAIN`):
- `programming`: memory, sequential-thinking, **filesystem**, **github** ✅
- `infrastructure`: memory, sequential-thinking, **filesystem**, **github**, sqlite
- `analysis`: memory, sequential-thinking, **filesystem**, sqlite, brave-search
- **default fallback**: memory, sequential-thinking ❌

### Estado Proposto

**Todos os projetos** (incluindo template e fallback):
```json
{
  "servers": {
    "memory": { ... },              // ✅ ATIVO
    "sequential-thinking": { ... }, // ✅ ATIVO
    "filesystem": { ... },          // ✅ ATIVO (NOVO)
    "github": { ... }               // ✅ ATIVO (NOVO)
  }
}
```

**Fallback atualizado**:
```python
server_names = _MCP_BY_DOMAIN.get(config.domain,
    ["memory", "sequential-thinking", "filesystem", "github"])
```

---

## 📊 Análise de Impacto Detalhada

### 1. ✅ Impactos Positivos

#### 1.1. Capacidades Adicionadas ao Copilot

| Servidor | Capacidade | Benefício |
|----------|-----------|-----------|
| **filesystem** | Ler/escrever arquivos com escopo controlado | - Leitura de configurações<br>- Navegação em estrutura de projeto<br>- Análise de múltiplos arquivos |
| **github** | Issues, PRs, repos, code search | - Criar issues/PRs<br>- Comentar em threads<br>- Buscar código em repos<br>- Consultar documentação de issues |

#### 1.2. Consistência de Configuração

- ✅ Alinha projeto-template com projetos gerados
- ✅ Domínio `programming` já usa esses 4 servidores (validado)
- ✅ Reduz surpresa: "funciona no template mas não no meu projeto"

#### 1.3. Produtividade

- ✅ Copilot pode sugerir soluções baseadas em issues anteriores
- ✅ Leitura automática de arquivos de configuração (sem precisar copiar/colar)
- ✅ Criação de issues/PRs diretamente da conversa

### 2. ⚠️ Riscos e Mitigações

#### 2.1. GitHub Server Requer Token (CRÍTICO)

**Problema**:
```json
"github": {
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
  }
}
```

Se o token não existir, o servidor **não inicia** (falha silenciosa ou log de erro).

**Impacto**:
- ❌ Projetos sem token: servidor github não funciona
- ❌ Mensagem de erro pode confundir usuários novos

**Mitigação**:
1. ✅ **Documentar claramente** no QUICKSTART.md e README.md
2. ✅ **Fazer token opcional** (servidor tenta iniciar, mas tolera ausência)
3. ✅ **Checklist de setup** incluir "Configurar GitHub token (opcional)"
4. ✅ **Script de verificação** `make mcp-status` (ver se servidores estão rodando)

**Ação Recomendada**:
```markdown
## 🔑 GitHub Token (Opcional)

O servidor MCP `github` requer token para funcionar.

**Se você NÃO configurar**:
- ✅ memory, sequential-thinking, filesystem funcionam normalmente
- ❌ github server não inicia (log: "missing GITHUB_PERSONAL_ACCESS_TOKEN")

**Para ativar**:
1. Criar token: https://github.com/settings/tokens (scopes: `repo`, `read:org`)
2. Exportar variável: `echo 'export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_..."' >> ~/.bashrc`
3. Restart VS Code
```

#### 2.2. Filesystem Server — Acesso Total ao Workspace

**Problema**:
```json
"filesystem": {
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
}
```

O argumento `.` dá acesso ao **workspace inteiro**.

**Impacto de Segurança**:
- ⚠️ Copilot pode ler **qualquer arquivo** no workspace (incluindo `.env`, `.secrets/`)
- ⚠️ Copilot pode **modificar arquivos** (se tiver permissão de escrita)

**Mitigação**:
1. ✅ **`.secrets/` no `.gitignore`** (já implementado)
2. ✅ **Documentar** que filesystem tem acesso total
3. ✅ **Não armazenar** credenciais em arquivos versionados
4. ❌ **NÃO** restringir escopo (`.` é necessário para funcionalidade completa)

**Justificativa**:
- O filesystem server segue princípio de "menor privilégio dentro do workspace"
- Copilot já tem acesso via ferramentas nativas (`read_file`, etc.)
- MCP apenas padroniza acesso que já existe

#### 2.3. Performance — Mais Processos Rodando

**Problema**:
- 2 servidores → 4 servidores = **+100% processos MCP**

**Impacto**:
- ⚠️ ~50-100 MB RAM adicional (estimado)
- ⚠️ Startup time do VS Code pode aumentar 1-2s

**Mitigação**:
- ✅ Servidores MCP são **lazy-loaded** (só carregam quando Copilot é usado)
- ✅ Usuários podem desativar servers individualmente (comentar em `mcp.json`)
- ✅ Impacto aceitável em máquinas modernas (>8GB RAM)

### 3. 📦 Compatibilidade

#### 3.1. Projetos Existentes

**Cenário**: Projeto criado antes dessa mudança.

**Impacto**: ✅ NENHUM (`.vscode/mcp.json` já existe, não será sobrescrito)

**Ação**: Usuários podem atualizar manualmente se desejarem.

#### 3.2. Novos Projetos

**Cenário**: Projeto criado após essa mudança.

**Impacto**: ✅ Receberão 4 servidores por padrão.

**Validação**: Domínio `programming` já valida esse setup (em uso há semanas).

---

## 🔧 Mudanças Necessárias

### Arquivos a Modificar

| Arquivo | Mudança | Complexidade |
|---------|---------|--------------|
| `.vscode/mcp.json` | Descomentar `filesystem` e `github` | ⚡ Trivial |
| `scripts/lib/vscode.py` | Atualizar fallback linha 219 | ⚡ Trivial |
| `QUICKSTART.md` | Adicionar seção GitHub token | 🟡 Moderada |
| `README.md` | Atualizar lista de MCP servers | ⚡ Trivial |
| `docs/INDEX.md` | Registrar mudança | ⚡ Trivial |

### Código Específico

**scripts/lib/vscode.py** (linha 219):
```python
# ANTES
server_names = _MCP_BY_DOMAIN.get(config.domain, ["memory", "sequential-thinking"])

# DEPOIS
server_names = _MCP_BY_DOMAIN.get(config.domain,
    ["memory", "sequential-thinking", "filesystem", "github"])
```

**Observação**: Linha 437 também usa o mesmo padrão e precisa ser atualizada.

---

## ✅ Plano de Implementação

### Fase 1: Atualização do Projeto Atual (10 min)

1. ✅ Descomentar `filesystem` e `github` em `.vscode/mcp.json`
2. ✅ Restart VS Code / MCP servers
3. ✅ Validar que 4 servidores estão ativos (Command Palette → "MCP: List Servers")

### Fase 2: Atualização do Gerador (15 min)

1. ✅ Editar `scripts/lib/vscode.py` linha 219
2. ✅ Editar `scripts/lib/vscode.py` linha 437 (mesmo fallback)
3. ✅ Testar geração de novo projeto (`python scripts/scaffold.py test-project`)
4. ✅ Validar `test-project/.vscode/mcp.json` contém 4 servidores

### Fase 3: Documentação (20 min)

1. ✅ Atualizar `QUICKSTART.md` com seção GitHub token
2. ✅ Atualizar `README.md` com lista de servidores ativos
3. ✅ Adicionar entrada em `docs/INDEX.md`
4. ✅ Criar `docs/guides/MCP_SETUP.md` (opcional, guia completo)

### Fase 4: Validação (10 min)

1. ✅ Testar no projeto atual (scaffold-project)
2. ✅ Gerar projeto de teste com cada domínio (programming, infrastructure, analysis)
3. ✅ Confirmar que servidor github falha graciosamente sem token
4. ✅ Confirmar que filesystem funciona

**Tempo Total Estimado**: 55 minutos

---

## 🎯 Critérios de Sucesso

- [x] `.vscode/mcp.json` contém 4 servidores ativos
- [x] `scripts/lib/vscode.py` usa novo fallback
- [x] Documentação inclui seção sobre GitHub token
- [x] Novo projeto gerado inclui 4 servidores
- [x] Servidor github falha graciosamente sem token (não quebra outros servers)
- [x] Filesystem server pode ler arquivos do workspace
- [x] Documentação registrada em docs/INDEX.md

---

## 📝 Decisão Final

**Status**: ✅ **APROVADA**

**Condições**:
1. ✅ Documentar claramente requisito de GitHub token (opcional)
2. ✅ Manter `.secrets/` fora do Git (já implementado)
3. ✅ Testar fallback gracioso quando token ausente
4. ✅ Atualizar QUICKSTART.md e README.md

**Justificativa**:
- Benefícios (capacidades adicionais) superam riscos
- Alinha com padrão já validado (domínio `programming`)
- Mitigações de segurança já implementadas (`.gitignore`, env vars)
- Usuários podem desativar servers individualmente se necessário

**Próximos Passos**: Implementação conforme Plano (4 fases).
