---
applyTo: "**"
---

# GitHub Copilot — Instruções do Projeto

**Projeto**: `scaffold-project` — Enterprise Scaffold Project Template
**Regras completas**: [`.copilot-rules.md`](../.copilot-rules.md) (7 seções)
**Rituais de sessão**: `python scripts/session-manager.py start --json` | `python scripts/session-manager.py end --json`

---

## 🌐 Idioma e Comunicação

**IMPORTANTE**: Este projeto é brasileiro. Todas as interações devem ser em **Português do Brasil (pt-BR)**.

### Regras de Idioma

1. **Respostas do Copilot**: Sempre em português (pt-BR)
2. **Código e variáveis**: Inglês (padrão internacional)
3. **Documentação e comentários**: Português
4. **Mensagens de commit**: Português (exceto tipos convencionais: `feat`, `fix`, `docs`, etc.)
5. **Nomes de arquivos**: Seguir padrão do projeto (ver seção 7 - Nomenclatura)

### Terminologia Técnica

- **Preferir termos em português** quando houver equivalente consagrado:
  - "arquivo" (não "file")
  - "pasta" (não "folder" ou "directory")
  - "ramificação" ou "branch" (ambos aceitos)
  - "confirmação" ou "commit" (ambos aceitos)

- **Manter em inglês** quando não houver tradução natural:
  - Nomes de tecnologias: Python, TypeScript, Docker, Kubernetes
  - Comandos: `git`, `make`, `pytest`, `pip`
  - Conceitos técnicos: merge, pull request, refactoring, debugging

---

## 🚨 Regras P0 — CRÍTICO (nunca violar)

### 1. Criar/editar arquivos — NUNCA via terminal

| Operação | ✅ Ferramenta obrigatória |
|----------|--------------------------|
| Criar arquivo novo | `create_file` |
| Editar arquivo existente | `replace_string_in_file` (mín. 3 linhas de contexto) |
| Múltiplas edições | `multi_replace_string_in_file` |

❌ **PROIBIDO**: `cat > heredoc`, `echo >> arquivo`, `echo | tee arquivo`, `tee`

---

### 2. Ler/buscar/listar arquivos — NUNCA via terminal

| Operação | ✅ Ferramenta obrigatória |
|----------|--------------------------|
| Ler conteúdo | `read_file` |
| Buscar texto/padrão | `grep_search` |
| Encontrar arquivos | `file_search` |
| Listar diretório | `list_dir` |
| Busca semântica | `semantic_search` |
| Verificar erros | `get_errors` |

❌ **PROIBIDO via `run_in_terminal`**: `cat`, `grep`, `find`, `ls`
✅ **`run_in_terminal` permitido apenas para**: `git`, `make`, `pytest`, `pip install`, `docker`, `systemctl`

---

### 3. Mover/copiar/excluir arquivos — SEMPRE Python stdlib

```python
import shutil, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

src = Path("/projeto/origem/arquivo.md")
dst = Path("/projeto/destino/arquivo.md")
dst.parent.mkdir(parents=True, exist_ok=True)
if src.exists():
    shutil.move(str(src), str(dst))
    log.info("✅ %s → %s", src, dst)
```

❌ **PROIBIDO via terminal**: `mv`, `cp`, `rm`, `mkdir`
✅ **Ferramenta**: `mcp_pylance_mcp_s_pylanceRunCodeSnippet` (sem shell, sem arquivos temp)

---

### 4. Git commits — SEMPRE via arquivo de mensagem

```bash
# Mensagem ≤ 5 linhas:
echo "feat(escopo): descrição" > /tmp/commit.txt
./scripts/git-commit-with-file.sh /tmp/commit.txt

# Mensagem ≥ 6 linhas → usar create_file("/tmp/commit.txt", ...)
```

❌ **PROIBIDO**: `git commit -m "..."` direto

---

## 📋 Regras P1 — Organização e Qualidade

### 5. Pastas corretas por tipo de arquivo

| Tipo | Localização |
|------|-------------|
| Documentação de sessão | `docs/SESSIONS/YYYY-MM-DD/` |
| Documentação técnica | `docs/` |
| Código Python source | `src/` |
| Scripts Python/Shell | `scripts/` |
| Testes | `tests/` |

❌ **NUNCA** criar arquivos de sessão/doc na raiz do projeto
❌ **NUNCA** modificar `.specify/` manualmente (uso exclusivo do SpecKit)

---

### 6. Documentos incrementais — nunca sobrescrever

| Arquivo | Comportamento obrigatório |
|---------|--------------------------|
| `README.md` | Atualizar seções; nunca apagar conteúdo anterior |
| `docs/INDEX.md` | Adicionar entradas; manter histórico de sessões |
| `docs/TODO.md` | Marcar `[x]`; adicionar itens; nunca remover itens |
| `docs/SESSIONS/*/DAILY_ACTIVITIES_*.md` | Append de blocos `---` por atividade |
| `docs/SESSIONS/*/SESSION_REPORT_*.md` | Append de seções; preservar relatórios anteriores |
| `docs/SESSIONS/*/FINAL_STATUS_*.md` | Adicionar linhas; nunca remover linhas |

**Regra prática**: em `replace_string_in_file`, substituir trecho **específico e localizado** — nunca o documento inteiro.

---

### 7. Nomenclatura de arquivos

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Python | `snake_case.py` | `project_config.py` |
| Markdown | `SCREAMING_SNAKE.md` | `SESSION_REPORT.md` |
| JSON | `kebab-case.json` | `mcp-config.json` |
| Shell | `kebab-case.sh` | `git-commit-with-file.sh` |
| Branch feat | `NNN-nome-da-feature` | `018-copilot-instructions` |
| Branch fix | `fix-descricao` | `fix-symlink-broken` |

---

## 🔒 Segurança

- Nunca armazenar credenciais, tokens ou chaves em arquivos versionados
- Nunca colocar tokens diretamente em `mcp.json` → usar `${env:VAR_NAME}` ou `.secrets/.env`
- `.secrets/` está no `.gitignore` ✅ — verificar em todo início de sessão
- Padrões de scan: `.env*`, `*.key`, `*.pem`, `*.crt`, `*secret*`, `*password*`, `*token*`

---

## ⚠️ Enforcement

Se uma ação viola estas regras, recusar e exibir:

```
❌ REGRA [N] violada: [nome da regra]
Motivo: [explicação]
Correto: [alternativa válida]
```

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
