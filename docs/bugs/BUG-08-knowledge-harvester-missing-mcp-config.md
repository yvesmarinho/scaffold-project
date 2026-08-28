# BUG-08: Projeto knowledge-harvester-library sem configuração MCP

**Data**: 2026-04-29
**Severidade**: 🟡 Média (funcionalidade limitada)
**Status**: 🟡 Reportado
**Afeta**: `knowledge-harvester-library`
**Projeto**: `/home/yves_marinho/DevOps/Projetos/knowledge-harvester-library`

---

## 📝 Descrição

O projeto `knowledge-harvester-library` foi identificado sem a configuração MCP (Model Context Protocol) necessária para integração com GitHub Copilot e outros serviços MCP.

---

## 🔍 Diagnóstico

### Arquivos Ausentes

❌ **`.vscode/mcp.json`** - Configuração MCP do projeto
❌ **`activate-mcp.sh`** - Script de ativação MCP (provavelmente)

### Impacto

Sem a configuração MCP, o projeto não tem acesso a:
- Memory server (persistência de contexto)
- Sequential-thinking server (raciocínio estruturado)
- GitHub tools (integração com issues/PRs)
- Pylance MCP tools (análise Python avançada)

---

## 🎯 Resolução Esperada

### 1. Criar `.vscode/mcp.json`

Template mínimo baseado no scaffold-project:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ]
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    },
    "pylance-mcp-server": {
      "command": "pylance-langserver-mcp",
      "args": []
    }
  }
}
```

### 2. Criar `activate-mcp.sh`

```bash
#!/bin/bash
# Activate MCP - placeholder script
echo "MCP configuration check..."
```

### 3. Verificar Integração

```bash
cd ~/DevOps/Projetos/knowledge-harvester-library
./activate-mcp.sh
code .  # Reabrir VS Code para carregar MCP
```

---

## 📋 Checklist de Fix

- [ ] Criar `.vscode/mcp.json` com configuração básica
- [ ] Criar `activate-mcp.sh` (se não existir)
- [ ] Adicionar `.vscode/mcp.json` ao `.gitignore` (se contiver secrets)
- [ ] Testar ativação MCP no projeto
- [ ] Validar acesso a memory/sequential-thinking servers
- [ ] Documentar setup no README do projeto

---

## 🔗 Referências

- Template MCP: `scaffold-project/.vscode/mcp.json`
- Documentação MCP: [Model Context Protocol](https://modelcontextprotocol.io/)
- Copilot instructions: `.github/copilot-instructions.md`

---

## 👤 Reportado por

GitHub Copilot - Session 2026-04-29

---

## 📌 Notas

Este bug foi identificado durante análise de projetos ativos em 2026-04-28.
O knowledge-harvester-library é um projeto Python que se beneficiaria significativamente da integração MCP, especialmente os servidores memory e pylance-mcp.
