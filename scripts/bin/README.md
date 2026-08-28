# Scripts Globais — Instalação

Este diretório contém scripts utilitários que podem ser instalados globalmente para uso conveniente.

## 🚀 new-project

Script wrapper para criar projetos usando o Enterprise Scaffold Project Template de qualquer diretório.

### Instalação

```bash
# Criar diretório se não existir
mkdir -p ~/.local/bin

# Copiar script
cp scripts/bin/new-project ~/.local/bin/new-project

# Tornar executável
chmod +x ~/.local/bin/new-project

# Verificar se ~/.local/bin está no PATH
echo $PATH | grep -q "$HOME/.local/bin" && echo "✅ OK" || echo "⚠️ Adicionar ao PATH"
```

### Adicionar ao PATH (se necessário)

Para **zsh** (padrão no macOS e muitas distros Linux):
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

Para **bash**:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Verificação

```bash
# Testar comando
new-project --help

# Ver perfis disponíveis
new-project --list-profiles
```

### Uso

Veja documentação completa em: [`docs/NEW_PROJECT_COMMAND.md`](../../docs/NEW_PROJECT_COMMAND.md)

Quick start:
```bash
new-project my-api --compose python-fastapi
new-project my-frontend --compose typescript-next
```

---

## Scripts Futuros

Outros scripts globais úteis podem ser adicionados aqui no futuro:
- `project-validate` — validar estrutura de projeto existente
- `project-upgrade` — atualizar projeto para nova versão do template
- etc.
