"""
lib/project.py — Criação de estrutura de pastas e arquivos base.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

from .config import (
    DOMAIN_DEFAULT_PROFILES,
    SPECKIT_SYNC_DATE,
    SPECKIT_TRANSVERSAL_PROFILES,
    CreatedItem,
    ProjectConfig,
)
from . import vscode
from . import file_merge

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Raiz do template (scaffold-project/) deduzida a partir da localização deste módulo
_TEMPLATE_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Placeholders e substituição
# ---------------------------------------------------------------------------

PLACEHOLDERS = {
    "{{PROJECT_NAME}}",
    "{{PROJECT_TITLE}}",
    "{{PROJECT_DESCRIPTION}}",
    "{{CREATED_AT}}",
    "{{DOMAIN}}",
    "{{LANGUAGE}}",
    "{{GITHUB_REPO}}",
}


def _apply_placeholders(text: str, config: ProjectConfig) -> str:
    """Substitui todos os placeholders pelo valor real da config."""
    # Valor para GitHub repo: mostrar link se configurado, senão "(não configurado)"
    github_repo_display = config.github_repo if config.github_repo else "(não configurado)"

    replacements = {
        "{{PROJECT_NAME}}":        config.project_name,
        "{{PROJECT_TITLE}}":       config.project_title,
        "{{PROJECT_DESCRIPTION}}": config.description,
        "{{CREATED_AT}}":          config.created_at,
        "{{DOMAIN}}":              config.domain,
        "{{LANGUAGE}}":            config.language,
        "{{GITHUB_REPO}}":         github_repo_display,
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text


# ---------------------------------------------------------------------------
# Templates internos
# ---------------------------------------------------------------------------

_README_MD = """\
# {{PROJECT_TITLE}}

[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![GitHub Flow](https://img.shields.io/badge/Workflow-GitHub%20Flow-blue.svg)](https://docs.github.com/en/get-started/quickstart/github-flow)
![Branch Protection](https://img.shields.io/badge/Branch%20Protection-Recommended-green)

> {{PROJECT_DESCRIPTION}}

**Domínio**: {{DOMAIN}} | **Linguagem**: {{LANGUAGE}}
**Criado em**: {{CREATED_AT}}
{github_section}

---

## 🚀 Início Rápido

```bash
# Instalar dependências
make install-deps

# Iniciar desenvolvimento
make dev
```

## 📚 Documentação

- [Índice](docs/INDEX.md)
- [Tarefas](docs/TODO.md)

## 🤝 Contribuindo

Este projeto segue as melhores práticas de Git/GitHub para garantir qualidade e colaboração eficiente.

### Workflow Git

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para:
- Convenções de branches (`feature/NNN-descricao`, `fix/descricao`)
- Padrões de commits (Conventional Commits)
- Processo de Pull Request
- Estratégias de merge
- Proteção de branches

### Configuração de Branch Protection

Para configurar proteção de branches no GitHub, consulte [docs/BRANCH_PROTECTION_SETUP.md](docs/BRANCH_PROTECTION_SETUP.md).

## 🏗️ Estrutura

Consulte os [documentos de arquitetura](docs/) para detalhes.
"""

_SESSION_DOCS_README = """\
# Session Docs Workspace

Esta pasta guarda artefatos de sessão criados sob demanda pelos scripts do projeto.

## Regras

- Não criar subpastas datadas durante o scaffold.
- Os arquivos `DAILY_ACTIVITIES_YYYY-MM-DD.md` devem nascer apenas em sessões reais.
- O fluxo canônico é `python scripts/session-manager.py --json start|start-first|end`.
"""

_DOCS_INDEX_MD = """\
# 📚 Índice — {{PROJECT_TITLE}}

**Projeto**: `{{PROJECT_NAME}}`
**Criado em**: {{CREATED_AT}}
**Last Updated**: {{CREATED_AT}}
**Last Session**: N/A

---

## Documentação Principal

| Arquivo | Descrição |
|---------|-----------|
| [README.md](../README.md) | Documentação pública |
| [TODO.md](TODO.md) | Tarefas pendentes |
| [TODAY_ACTIVITIES.md](TODAY_ACTIVITIES.md) | Atividades do dia |

## Sessões de Trabalho

```
SESSIONS/
└── YYYY-MM-DD/
    ├── SESSION_RECOVERY_YYYY-MM-DD.md
    ├── DAILY_ACTIVITIES_YYYY-MM-DD.md
    ├── SESSION_REPORT_YYYY-MM-DD.md
    └── FINAL_STATUS_YYYY-MM-DD.md
```

---

*Gerado por scaffold.py em {{CREATED_AT}}*
"""

_DOCS_TODO_MD = """\
# 📝 TODO — {{PROJECT_TITLE}}

**Last Updated**: {{CREATED_AT}}
**Status**: 🟢 Em andamento

---

## 🟠 Em Progresso

*(nenhum)*

## 🔵 Pendente

- [ ] Configurar estrutura inicial do projeto
- [ ] Adicionar testes unitários
- [ ] Documentar APIs

## ✅ Concluído

- [x] Scaffold inicial gerado ({{CREATED_AT}})
"""

_DOCS_TODAY_ACTIVITIES_MD = """\
# 📅 Atividades — {{PROJECT_TITLE}}

**Data**: {{CREATED_AT}}
**Projeto**: `{{PROJECT_NAME}}`

---

## ⏰ Atividades do Dia

### ✅ Scaffold Inicial Criado

- Projeto `{{PROJECT_NAME}}` inicializado via `uv run scripts/scaffold.py`
- Domínio: {{DOMAIN}} | Linguagem: {{LANGUAGE}}
- Estrutura de pastas criada
- Regras Copilot geradas

---

*Gerado por scaffold.py*
"""

_GITIGNORE = """\
# Segredos e credenciais
.secrets/
*.key
*.pem
*.crt
*.p12
*.pfx
*.jks
*.keystore
secrets/
credentials/
*.credentials
.env
.env.*
!.env.example

# Python
.venv/
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage

# Node.js
node_modules/
npm-debug.log*
.npm

# VS Code
.vscode/*
!.vscode/settings.json
!.vscode/mcp.json
!.vscode/extensions.json

# Claude Code
.claude/settings.local.json

# OS
.DS_Store
Thumbs.db
*.swp
*.swo

# Logs
*.log
logs/*
!logs/README.md
!scripts/logs/.gitkeep

# Infrastructure directories
tmp/*
!tmp/README.md
.memory/*
!.memory/README.md
.session-index/*
!.session-index/README.md
.session-time/*
!.session-time/README.md
"""

_SECRETS_README = """\
# 🔒 .secrets/ — Arquivos Sensíveis

**NUNCA commitar este diretório.**

Este diretório é ignorado pelo `.gitignore`.

## O que armazenar aqui

| Tipo | Exemplos |
|------|---------|
| Variáveis de ambiente | `.env`, `.env.production` |
| Chaves SSH | `id_rsa`, `*.pem` |
| Tokens de API | `api-tokens.txt` |
| Credenciais cloud | `aws-credentials` |
| Segredos Kubernetes | `kubeconfig` |

## Uso com MCP

Para servidores MCP que precisam de tokens:

```json
"env": {
  "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
}
```

Configure em `.secrets/.env` e carregue no shell antes de iniciar o VS Code.
"""

_SECRETS_SECURITY_MD = """\
# 🔒 Segurança do Diretório .secrets/

## ⚠️ ATENÇÃO: NUNCA COMMITAR ESTE DIRETÓRIO

Este diretório armazena credenciais, tokens e chaves sensíveis.

## 🛡️ Proteções Aplicadas

### 1. Permissões Restritivas
- **chmod 700** (somente proprietário pode ler/escrever/executar)
- Outros usuários não têm acesso
- Configurado automaticamente pelo scaffold

### 2. Exclusão do Git
- `.secrets/` está em `.gitignore` ✅
- Arquivos não são versionados
- Pre-commit hook valida (se ativado)

### 3. Padrões de Arquivos Sensíveis
**Nunca versionar**:
- `.env*` (qualquer variante)
- `*.key`, `*.pem`, `*.crt` (certificados/chaves)
- `*secret*`, `*password*`, `*token*` (padrões de nome)
- `.vault_pass` (Ansible Vault)

## 📝 Boas Práticas

### Armazenar Credenciais
```bash
# Variáveis de ambiente
cat > .secrets/.env << 'EOF'
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF

# Proteger arquivo
chmod 600 .secrets/.env
```

### Carregar no Shell
```bash
# Antes de abrir VS Code com MCP
source .secrets/.env
code .
```

### Referenciar em .vscode/mcp.json
```json
{
  "servers": {
    "github": {
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

## 🔍 Validação de Segurança

### Verificar Permissões
```bash
ls -la .secrets/
# Deve mostrar: drwx------ (700)
```

### Ativar Pre-Commit Hook (Opcional)
```bash
# Copiar do template
cp .git-hooks/pre-commit.secrets .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Testar
git add .secrets/.env  # Deve FALHAR
```

## 🚨 Checklist de Segurança

- [ ] `.secrets/` tem permissão 700
- [ ] Arquivos sensíveis têm permissão 600
- [ ] `.secrets/` está em `.gitignore`
- [ ] Variáveis carregadas antes do VS Code
- [ ] Credenciais NÃO estão em mcp.json (usar ${env:VAR})
- [ ] Pre-commit hook ativado (recomendado)

## 📚 Documentação Relacionada

- [Secrets Management Best Practices](../docs/SECURITY.md)
- [MCP Server Setup](../docs/README.md)
- [Ansible Vault Guide](../docs/ANSIBLE_VAULT_GUIDE.md) (se aplicável)

---

**Última verificação**: Automatizada via scaffold
**Permissões atuais**: `ls -ld .secrets/` para verificar
"""

_PRE_COMMIT_SECRETS_HOOK = r"""#!/usr/bin/env bash
# Pre-commit hook: Segurança — secrets, IPs internos e credenciais (Git Guardian rules)
# Instalação:
#   cp .git-hooks/pre-commit.secrets .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# MODO MANUAL (padrão): validações não rodam automaticamente a cada commit
# (economia de tokens). Para validar:
#   - PRE_COMMIT_VALIDATE=1 git commit ...
#   - bash .git-hooks/pre-commit.secrets --manual

set -euo pipefail

if [[ "${1:-}" != "--manual" && "${PRE_COMMIT_VALIDATE:-0}" != "1" ]]; then
    echo "⏭️  Pre-commit: validações em modo manual (PRE_COMMIT_VALIDATE=1 git commit, ou bash .git-hooks/pre-commit.secrets --manual)"
    exit 0
fi

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}🔍 Validando segurança (secrets + IPs + credenciais)...${NC}"

# ---------------------------------------------------------------------------
# 1. Bloquear commit de .secrets/
# ---------------------------------------------------------------------------
if git diff --cached --name-only | grep -q '^\.secrets/'; then
    echo -e "${RED}❌ BLOQUEADO: .secrets/ detectado${NC}"
    echo ""
    echo "Arquivos detectados:"
    git diff --cached --name-only | grep '^\.secrets/' | sed 's/^/  - /'
    echo ""
    echo "💡 Solução: git restore --staged .secrets/"
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Bloquear por nome de arquivo sensível
# ---------------------------------------------------------------------------
SENSITIVE_PATTERNS=(
    '\.env$'
    '\.env\.'
    '\.key$'
    '\.pem$'
    '\.p12$'
    '\.pfx$'
    '\.crt$'
    '\.cert$'
    '\.vault_pass'
    'kubeconfig'
    'credentials'
)

BLOCKED_FILES=()
for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    while IFS= read -r file; do
        if [[ "$file" =~ ^\.git-hooks/ ]]; then continue; fi
        [[ -n "$file" ]] && BLOCKED_FILES+=("$file")
    done < <(git diff --cached --name-only | grep -iE "$pattern" || true)
done

if [ ${#BLOCKED_FILES[@]} -gt 0 ]; then
    echo -e "${RED}❌ BLOQUEADO: Nomes de arquivos sensíveis detectados${NC}"
    printf '  - %s\n' "${BLOCKED_FILES[@]}"
    echo ""
    echo "💡 Mova para .secrets/ ou adicione ao .gitignore"
    exit 1
fi

# ---------------------------------------------------------------------------
# 3. Varredura de CONTEÚDO: IPs internos + credenciais (Git Guardian rules)
# ---------------------------------------------------------------------------
python3 - <<'PYEOF'
import re
import subprocess
import sys
from pathlib import Path

# Diretórios/arquivos que podem conter IPs/tokens como exemplo (não são segredos)
SCAN_EXCLUDES = {
    ".git-hooks", "docs/bugs", "docs/debates", "docs/implementations",
    "tests", ".memory", "CHANGELOG", "SECURITY.md",
}

# Extensões de texto a escanear (binários são ignorados)
TEXT_EXTENSIONS = {
    ".md", ".txt", ".yml", ".yaml", ".json", ".py", ".sh", ".env",
    ".conf", ".config", ".ini", ".toml", ".xml", ".html", ".js", ".ts",
    ".tf", ".hcl", ".j2", ".jinja", ".properties", ".cfg", ".sql",
    ".dockerfile", "", ".env.example",
}

# ---------------------------------------------------------------------------
# Padrões: IPs internos (RFC 1918 + loopback + link-local)
# ---------------------------------------------------------------------------
IP_PATTERNS = [
    (re.compile(r'\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),       "IP privado classe A (10.x.x.x)"),
    (re.compile(r'\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b'), "IP privado classe B (172.16-31.x.x)"),
    (re.compile(r'\b192\.168\.\d{1,3}\.\d{1,3}\b'),           "IP privado classe C (192.168.x.x)"),
    (re.compile(r'\b127\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),       "IP loopback (127.x.x.x)"),
    (re.compile(r'\b169\.254\.\d{1,3}\.\d{1,3}\b'),           "IP link-local (169.254.x.x)"),
]

# ---------------------------------------------------------------------------
# Padrões: credenciais hardcoded (Git Guardian rules)
# ---------------------------------------------------------------------------
CRED_PATTERNS = [
    # Chaves privadas PEM
    (re.compile(r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'), "Chave privada PEM"),
    # AWS
    (re.compile(r'\bAKIA[0-9A-Z]{16}\b'),                     "AWS Access Key ID"),
    (re.compile(r'(?i)aws.{0,20}(secret|key).{0,10}[=:]\s*[\'"]?[A-Za-z0-9/+]{40}'), "AWS Secret Key"),
    # GitHub tokens
    (re.compile(r'\bghp_[A-Za-z0-9]{36}\b'),                  "GitHub Personal Token (ghp_)"),
    (re.compile(r'\bgho_[A-Za-z0-9]{36}\b'),                  "GitHub OAuth Token (gho_)"),
    (re.compile(r'\bghs_[A-Za-z0-9]{36}\b'),                  "GitHub App Token (ghs_)"),
    (re.compile(r'\bghr_[A-Za-z0-9]{36}\b'),                  "GitHub Refresh Token (ghr_)"),
    # Credenciais em URLs (http://user:senha@host)
    (re.compile(r'[a-zA-Z]+://[^/@\s]+:[^/@\s]+@[^/\s]'),    "Credencial em URL (user:pass@host)"),
    # Variáveis com valor literal de senha/token
    (re.compile(r'(?i)(password|passwd|secret|api_key|apikey|auth_token|access_token)\s*[=:]\s*[\'"][^\'"\s]{8,}[\'"]'), "Senha/token literal em variável"),
    # Bearer tokens em código
    (re.compile(r'(?i)Bearer\s+[A-Za-z0-9\-._~+/]{20,}={0,2}(?!\s*(#|\/\/|<!--))'), "Bearer token hardcoded"),
    # Senhas base64 em YAML/JSON (padrão comum: password: <base64>)
    (re.compile(r'(?i)(password|secret)\s*:\s*[A-Za-z0-9+/]{16,}={0,2}\s*$', re.MULTILINE), "Valor base64 suspeito em campo sensível"),
]

def should_exclude(filepath: str) -> bool:
    p = Path(filepath)
    for excl in SCAN_EXCLUDES:
        if filepath.startswith(excl + "/") or filepath == excl:
            return True
    if p.suffix.lower() not in TEXT_EXTENSIONS:
        return True
    return False

def get_staged_content(filepath: str) -> str | None:
    try:
        r = subprocess.run(
            ["git", "show", f":{filepath}"],
            capture_output=True, text=True, errors="replace", timeout=10,
        )
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None

# Obter arquivos staged
r = subprocess.run(
    ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
    capture_output=True, text=True,
)
staged = [f for f in r.stdout.strip().split("\n") if f]

ip_violations: list[tuple[str, str, list[str]]] = []
cred_violations: list[tuple[str, str]] = []

for filepath in staged:
    if should_exclude(filepath):
        continue

    content = get_staged_content(filepath)
    if content is None:
        continue

    # Verificar IPs
    for pattern, label in IP_PATTERNS:
        found = list(dict.fromkeys(pattern.findall(content)))
        if found:
            ip_violations.append((filepath, label, found))

    # Verificar credenciais
    for pattern, label in CRED_PATTERNS:
        if pattern.search(content):
            cred_violations.append((filepath, label))

failed = False

if ip_violations:
    print("\n❌ BLOQUEADO: IPs internos detectados no conteúdo dos arquivos:")
    for filepath, label, ips in ip_violations:
        masked = [ip[:3] + ".***.***" for ip in ips]
        print(f"  {filepath} → {label}: {masked}")
    print()
    print("💡 Substitua os IPs por placeholders: <IP_DO_HOST>, 0.0.0.0, ou variável de ambiente")
    failed = True

if cred_violations:
    print("\n❌ BLOQUEADO: Credenciais hardcoded detectadas (Git Guardian rules):")
    for filepath, label in cred_violations:
        print(f"  {filepath} → {label}")
    print()
    print("💡 Mova credenciais para .secrets/*.json ou variáveis de ambiente")
    failed = True

sys.exit(1 if failed else 0)
PYEOF

# ---------------------------------------------------------------------------
# 4. Permissões de .secrets/
# ---------------------------------------------------------------------------
if [ -d .secrets ]; then
    PERMS=$(stat -c "%a" .secrets 2>/dev/null || stat -f "%A" .secrets 2>/dev/null || echo "000")
    if [ "$PERMS" != "700" ]; then
        echo -e "${YELLOW}⚠️  .secrets/ não tem permissão 700 — corrigindo...${NC}"
        chmod 700 .secrets
    fi
fi

echo -e "${GREEN}✅ Segurança OK — secrets, IPs e credenciais verificados${NC}"
exit 0
"""

# ---------------------------------------------------------------------------
# READMEs para sub-pastas de docs/ (IMP-61)
# ---------------------------------------------------------------------------

_DOCS_DEBATES_README = """\
# docs/debates/ — Debates Técnicos e de Produto

Armazena debates estruturados sobre decisões importantes do projeto.

## 🎯 Objetivo

Documentar o **processo de decisão** — não apenas o resultado, mas também:
- Alternativas consideradas
- Prós e contras de cada opção
- Contexto da decisão
- Participantes do debate

## 📝 Formato

Use o template de debate (agent `@template-architect` ou manual):

```markdown
# DEBATE: [Título da Questão]

**Data**: YYYY-MM-DD
**Participantes**: @user1, @user2, AI Agent
**Contexto**: [Por que este debate é necessário?]

## Questão Central
[Pergunta clara que precisa ser respondida]

## Alternativas

### Opção A: [Nome]
**Prós**: ...
**Contras**: ...

### Opção B: [Nome]
**Prós**: ...
**Contras**: ...

## Decisão
[Escolha + Justificativa]

## Ações
- [ ] Implementar X
- [ ] Documentar em decisions/
```

## 🔍 Quando usar

- Mudanças de arquitetura significativas
- Escolha entre tecnologias/frameworks
- Decisões que afetam múltiplos times
- Trade-offs complexos

## 📂 Nomenclatura

`DEBATE_[TOPICO]_YYYY-MM-DD.md`

Exemplos:
- `DEBATE_SPEC_DRIVEN_DEVELOPMENT_2026-04-05.md`
- `DEBATE_ESCOLHA_ORM_2026-03-15.md`

## 🔗 Ver também

- [decisions/](../decisions/) — Registro formal de decisões (ADRs)
- [retrospectives/](../retrospectives/) — Aprendizados pós-sprint
"""

_DOCS_DECISIONS_README = """\
# docs/decisions/ — Architecture Decision Records (ADRs)

Registro formal de decisões arquiteturais do projeto.

## 🎯 Objetivo

Documentar **decisões irreversíveis ou caras de reverter** de forma estruturada.

## 📝 Formato ADR

```markdown
# ADR-NNN: [Título da Decisão]

**Status**: Aceita | Proposta | Depreciada | Substituída por ADR-XXX
**Data**: YYYY-MM-DD
**Decisores**: [Quem tomou a decisão]

## Contexto
[Forças em jogo, restrições, requisitos]

## Decisão
[O que foi decidido]

## Consequências
**Positivas**:
- ...

**Negativas**:
- ...

**Riscos**:
- ...

## Alternativas Consideradas
1. [Opção descartada] — [Por que foi rejeitada]
2. ...
```

## 🔍 Quando criar ADR

- Escolha de banco de dados
- Arquitetura de microserviços vs monolito
- Padrões de autenticação
- Estratégia de deployment
- Frameworks principais

## 📂 Nomenclatura

`ADR-NNN-[titulo-kebab-case].md`

Exemplos:
- `ADR-001-escolha-postgresql.md`
- `ADR-002-arquitetura-event-driven.md`

## 🔗 Recursos

- [ADR GitHub](https://adr.github.io/)
- [decisions/](../decisions/) (esta pasta)
- [debates/](../debates/) — Discussões que antecederam a decisão
"""

_DOCS_GUIDES_README = r"""\
# docs/guides/ — Guias e Tutoriais

Documentação how-to e tutoriais passo-a-passo.

## 🎯 Objetivo

Ensinar como realizar tarefas específicas no projeto.

## 📝 Tipos de Guias

### 1. Guias de Setup
- Como configurar ambiente de desenvolvimento
- Como rodar testes localmente
- Como fazer deploy

### 2. Guias de Desenvolvimento
- Como adicionar uma nova feature
- Como escrever testes
- Como fazer code review

### 3. Guias de Troubleshooting
- Problemas comuns e soluções
- Como debugar erros específicos

### 4. Guias de Integração
- Como integrar com serviços externos
- Como usar APIs internas

## 📂 Estrutura sugerida

```
guides/
├── setup/
│   ├── local-development.md
│   └── ci-cd-setup.md
├── development/
│   ├── adding-features.md
│   └── testing-guide.md
└── troubleshooting/
    └── common-issues.md
```

## 📝 Template de Guia

```markdown
# [Nome da Tarefa]

**Objetivo**: [O que você vai aprender]
**Pré-requisitos**: [O que precisa antes]
**Tempo estimado**: X minutos

## Passo 1: [Ação]
[Instruções detalhadas]

\`\`\`bash
# Comandos exemplo
\`\`\`

## Passo 2: [Ação]
...

## Validação
Como verificar que funcionou:
- [ ] Check 1
- [ ] Check 2

## Troubleshooting
**Erro X**: Solução Y
```

## 🔗 Ver também

- [INDEX.md](../INDEX.md) — Índice geral da documentação
- [templates/](../templates/) — Templates reutilizáveis
"""

_DOCS_RETROSPECTIVES_README = """\
# docs/retrospectives/ — Retrospectivas e Lições Aprendidas

Documentação de aprendizados de sprints, incidentes e projetos.

## 🎯 Objetivo

Capturar **lições aprendidas** para melhorar continuamente.

## 📝 Tipos de Retrospectivas

### 1. Retrospectiva de Sprint
Aprendizados do ciclo de desenvolvimento (semanal/quinzenal)

### 2. Post-Mortem de Incidente
Análise de falhas em produção

### 3. Retrospectiva de Projeto
Review ao final de projeto/feature grande

## 📝 Template: Retrospectiva de Sprint

```markdown
# Retrospectiva Sprint NN — YYYY-MM-DD

**Período**: DD/MM a DD/MM
**Participantes**: [Time]

## ✅ O que funcionou bem
- ...

## ⚠️ O que pode melhorar
- ...

## 💡 Insights e Aprendizados
- ...

## 🎯 Ações para próxima sprint
- [ ] Ação 1
- [ ] Ação 2

## 📊 Métricas
- Velocity: X pontos
- Bugs encontrados: Y
- Deploy frequency: Z
```

## 📝 Template: Post-Mortem

```markdown
# Post-Mortem: [Descrição do Incidente]

**Data do incidente**: YYYY-MM-DD HH:MM
**Duração**: X horas
**Severidade**: Critical | High | Medium
**Impacto**: [Quantos usuários afetados]

## Timeline
- HH:MM - Detecção
- HH:MM - Resposta iniciada
- HH:MM - Causa identificada
- HH:MM - Mitigação aplicada
- HH:MM - Resolução completa

## Causa Raiz
[5 Whys ou análise detalhada]

## Ações Corretivas
- [ ] Curto prazo (hoje)
- [ ] Médio prazo (esta semana)
- [ ] Longo prazo (preventivo)

## Lições Aprendidas
1. ...
2. ...
```

## 📂 Nomenclatura

- Sprints: `RETRO_SPRINT_NN_YYYY-MM-DD.md`
- Post-mortems: `POSTMORTEM_[INCIDENTE]_YYYY-MM-DD.md`
- Projetos: `RETRO_[NOME_PROJETO]_YYYY-MM-DD.md`

## 🔗 Ver também

- [debates/](../debates/) — Decisões técnicas
- [SESSIONS/](../SESSIONS/) — Atividades diárias
"""

_DOCS_ARCHITECTURE_README = """\
# docs/architecture/ — Documentação de Arquitetura

Diagramas, visões e documentação estrutural do sistema.

## 🎯 Objetivo

Documentar a **estrutura e organização** do sistema.

## 📝 Conteúdo

### 1. Visões Arquiteturais (C4 Model)

```
architecture/
├── context/          # C4 Level 1: System Context
├── containers/       # C4 Level 2: Container Diagram
├── components/       # C4 Level 3: Component Diagram
└── code/            # C4 Level 4: Code (opcional)
```

### 2. Diagramas

- Arquitetura de alto nível
- Fluxo de dados
- Deployment topology
- Integrações externas

### 3. Documentação Estrutural

- Módulos e responsabilidades
- Padrões arquiteturais adotados
- Boundaries e interfaces

## 📝 Template: Documento de Arquitetura

```markdown
# Arquitetura: [Componente/Sistema]

**Última atualização**: YYYY-MM-DD
**Owner**: [Time/Pessoa]

## Visão Geral
[Descrição de alto nível]

## Componentes Principais
### [Nome do Componente]
- **Responsabilidade**: ...
- **Tecnologia**: ...
- **Dependências**: ...

## Decisões Arquiteturais
Ver ADRs relacionados:
- [ADR-001](../decisions/ADR-001-xxx.md)

## Diagramas
![Diagrama Context](./diagrams/context.png)

## Qualidade e Não-Funcionais
- Escalabilidade: ...
- Segurança: ...
- Performance: ...

## Riscos Arquiteturais
- [Risco] — [Mitigação]
```

## 🛠️ Ferramentas sugeridas

- **Mermaid** — Diagramas em Markdown
- **PlantUML** — UML extensivo
- **Draw.io** — Diagramas gerais
- **C4 Model** — Framework de visualização

## 📂 Estrutura sugerida

```
architecture/
├── README.md (este arquivo)
├── overview.md
├── context-diagram.md
├── api-design.md
├── data-model.md
└── diagrams/
    ├── context.mmd
    ├── containers.mmd
    └── deployment.png
```

## 🔗 Ver também

- [decisions/](../decisions/) — ADRs
- [debates/](../debates/) — Discussões arquiteturais
"""

_DOCS_TEMPLATES_README = """\
# docs/templates/ — Templates Reutilizáveis

Templates de documentos para uso no projeto.

## 🎯 Objetivo

Padronizar documentação com templates prontos.

## 📝 Templates Disponíveis

### Documentação Técnica
- `FEATURE_SPEC_TEMPLATE.md` — Especificação de feature
- `API_DESIGN_TEMPLATE.md` — Design de API
- `DATABASE_SCHEMA_TEMPLATE.md` — Schema de banco de dados

### Processos
- `BUG_REPORT_TEMPLATE.md` — Reporte de bugs detalhado
- `INCIDENT_REPORT_TEMPLATE.md` — Relatório de incidente
- `CHANGE_REQUEST_TEMPLATE.md` — Solicitação de mudança

### Debates e Decisões
- `DEBATE_TEMPLATE.md` — Estrutura de debate
- `ADR_TEMPLATE.md` — Architecture Decision Record

### Guides
- `GUIDE_TEMPLATE.md` — Tutorial passo-a-passo
- `SETUP_GUIDE_TEMPLATE.md` — Guia de configuração

## ✅ Boas Práticas

1. **Copie, não modifique** — Templates são base, crie cópias
2. **Mantenha atualizados** — Review trimestral
3. **Documente mudanças** — Se alterar template, documente por quê

## 🔗 Como usar

```bash
# Copiar template para novo documento
cp docs/templates/FEATURE_SPEC_TEMPLATE.md \
   docs/features/FEAT-123-new-feature.md
```

## 🔗 Ver também

- Todos os outros diretórios de docs/ usam estes templates
"""

_PROJECT_CREATION_SUMMARY = """\
# 📋 Resumo de Criação do Projeto

**Projeto**: `{{PROJECT_NAME}}`
**Título**: {{PROJECT_TITLE}}
**Criado em**: {{CREATED_AT}}
**Template**: Enterprise Scaffold Project Template v1.0.0

---

## 📊 Informações do Projeto

| Propriedade | Valor |
|-------------|-------|
| **Nome** | {{PROJECT_NAME}} |
| **Descrição** | {{PROJECT_DESCRIPTION}} |
| **Domínio** | {{DOMAIN}} |
| **Linguagem** | {{LANGUAGE}} |
| **Repositório** | {{GITHUB_REPO}} |

---

## 📁 Estrutura Criada

```
{{PROJECT_NAME}}/
├── .github/                    # GitHub config (workflows, agents, prompts)
│   ├── agents/                 # SpecKit agents (11 agents)
│   ├── prompts/                # Prompt templates (9 prompts)
│   ├── ISSUE_TEMPLATE/         # Issue forms (3 templates)
│   ├── copilot-instructions.md # Instruções projeto-específicas
│   ├── CODEOWNERS              # Code review assignments
│   └── dependabot.yml          # Dependências automatizadas
├── .secrets/                   # ⚠️  Credenciais (chmod 700, não versionado)
│   ├── README.md               # Guia de uso de secrets
│   └── SECURITY.md             # Práticas de segurança avançadas
├── .specify/                   # SpecKit memory & constitution
│   ├── memory/
│   │   └── constitution.md     # Princípios e práticas do projeto
│   └── templates/
│       └── agent-file-template.md
├── .vscode/                    # VS Code configuration
│   ├── settings.json           # Editor settings
│   ├── mcp.json                # MCP servers (memory, sequential-thinking)
│   ├── extensions.json         # Recommended extensions
│   ├── tasks.json              # Build tasks
│   └── launch.json             # Debug configurations
├── docs/                       # Documentação do projeto
│   ├── architecture/           # Diagramas e C4 Model
│   ├── debates/                # Debates técnicos
│   ├── decisions/              # ADRs (Architecture Decision Records)
│   ├── guides/                 # Tutoriais e how-tos
│   ├── retrospectives/         # Post-mortems e sprints
│   ├── templates/              # Templates reutilizáveis
│   ├── copilot/                # Regras Copilot (.copilot-* symlinks)
│   ├── SESSIONS/               # Diários de sessões de trabalho
│   │   └── YYYY-MM-DD/
│   ├── INDEX.md                # Índice principal
│   ├── TODO.md                 # Tarefas pendentes
│   └── TODAY_ACTIVITIES.md     # Atividades do dia
├── scripts/                    # Scripts utilitários
│   └── load-mcp.sh             # Ativação de MCP servers
├── CHANGELOG.md                # Histórico de mudanças
├── Makefile                    # Comandos de automação
├── objetivo.md                 # Objetivo do projeto
├── mcp-questions.md            # Perguntas de onboarding MCP
├── pyproject.toml              # Config Python (se aplicável)
├── README.md                   # Documentação pública
├── SECURITY.md                 # Política de segurança GitHub
└── .gitignore                  # Arquivos ignorados pelo Git
```

---

## 🎯 Profiles Aplicados

{profiles_section}

---

## 🔧 Git Inicializado

✅ **Repositório Git criado**
- Commit inicial: `chore: scaffold inicial do projeto {{PROJECT_NAME}}`
- Tag: `scaffold-v1.0.0` (marca versão do template)
- Branch: `master`{git_remote_section}

---

## 🚀 Próximos Passos

### 1. Revisar e Personalizar

```bash
# Revisar arquivos principais
cat README.md
cat objetivo.md
cat docs/INDEX.md
cat .specify/memory/constitution.md
```

### 2. Configurar Ambiente

```bash
# Instalar dependências (se aplicável)
make install-deps

# Configurar MCP servers
./scripts/load-mcp.sh
```

### 3. Configurar Secrets

```bash
# Criar variáveis de ambiente
cp .secrets/README.md .secrets/.env.example
# Editar com suas credenciais
vim .secrets/.env
```

### 4. Iniciar Desenvolvimento

```bash
# Ver comandos disponíveis
make help

# Iniciar dev server (se aplicável)
make dev

# Rodar testes (se implementados)
make test
```

### 5. GitHub (se aplicável)

```bash
# Push inicial para GitHub
git push -u origin master --tags

# Configurar branch protection rules no GitHub:
# - Settings → Branches → Add rule
# - Require pull request reviews
# - Require status checks
```

---

## 📚 Comandos Úteis

### Makefile Targets

```bash
make help           # Lista todos os comandos disponíveis
make init           # Inicialização completa
make install-deps   # Instalar dependências
make dev            # Iniciar desenvolvimento
make build          # Build para produção
make test           # Rodar testes
make lint           # Linting de código
make format         # Formatação de código
make clean          # Limpar arquivos gerados
```

### Git Workflow

```bash
# Criar nova feature
git checkout -b NNN-nome-da-feature

# Commit com arquivo de mensagem
./scripts/git-commit-with-file.sh /tmp/commit.txt

# Push e criar PR
git push -u origin NNN-nome-da-feature
```

### Documentação de Sessões

```bash
# Inicializar sessão e criar arquivos canônicos
python scripts/session-manager.py --json start
```

---

## 🔗 Links Úteis

### Documentação Interna

- [README.md](../README.md) — Documentação pública
- [docs/INDEX.md](INDEX.md) — Índice de documentação
- [docs/TODO.md](TODO.md) — Tarefas pendentes
- [.specify/memory/constitution.md](../.specify/memory/constitution.md) — Princípios do projeto

### SubPastas de Documentação

- [docs/architecture/](architecture/) — Diagramas e visões do sistema
- [docs/decisions/](decisions/) — ADRs (Architecture Decision Records)
- [docs/guides/](guides/) — Tutoriais e how-tos
- [docs/debates/](debates/) — Debates técnicos documentados
- [docs/retrospectives/](retrospectives/) — Post-mortems e lições aprendidas
- [docs/templates/](templates/) — Templates reutilizáveis

### Agentes & Automação

- [.github/agents/](../.github/agents/) — Agentes customizados (SpecKit)
- [.github/prompts/](../.github/prompts/) — Prompts de sessão

### Segurança

- [SECURITY.md](../SECURITY.md) — Política de segurança pública
- [.secrets/SECURITY.md](../.secrets/SECURITY.md) — Práticas avançadas de segurança
- [.git-hooks/pre-commit.secrets](../.git-hooks/pre-commit.secrets) — Hook para prevenir commits de secrets

---

## 🛡️ Recursos de Segurança

✅ **Proteção de Secrets Ativada**
- Diretório `.secrets/` com chmod 700 (acesso restrito)
- `.gitignore` configurado para ignorar credenciais
- Pre-commit hook disponível em `.git-hooks/pre-commit.secrets`

**Ativar hook de segurança:**
```bash
cp .git-hooks/pre-commit.secrets .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

✅ **GitHub Security Files**
- `SECURITY.md` — Política de segurança
- `CODEOWNERS` — Aprovações obrigatórias
- `dependabot.yml` — Atualizações automatizadas
- Workflows: `security-scan.yml`, `dependency-review.yml`

---

## 🤖 SpecKit & Agentes

### Agentes Disponíveis

| Agente | Uso |
|--------|-----|
| `@session-manager` | Inicialização e gestão de sessões |
| `@speckit.specify` | Criar especificações de features |
| `@speckit.plan` | Planejar implementação |
| `@speckit.tasks` | Gerar tarefas acionáveis |
| `@speckit.implement` | Executar implementação |
| `@speckit.analyze` | Análise de consistência |
| `@speckit.clarify` | Esclarecer requisitos |
| `@speckit.checklist` | Gerar checklists customizadas |
| `@speckit.constitution` | Gerenciar princípios do projeto |
| `@speckit.taskstoissues` | Converter tasks em GitHub issues |
| `@template-architect` | Análise e evolução do template |

### Prompts de Sessão

| Prompt | Quando usar |
|--------|-------------|
| `/session-start-first` | Primeira sessão do projeto |
| `/session-start` | Iniciar nova sessão |
| `/session-end` | Encerrar sessão |

---

## 📖 Convenções do Projeto

### Commits

```
<tipo>(<escopo>): <descrição>

[corpo opcional]

[rodapé opcional]
```

**Tipos**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branches

- Features: `NNN-nome-da-feature` (número opcional)
- Bugfixes: `fix-descricao-do-bug`
- Hotfixes: `hotfix-descricao`

### Documentação

- Markdown para toda documentação
- Diagramas em `docs/architecture/`
- ADRs em `docs/decisions/`
- Lições aprendidas em `docs/retrospectives/`

---

## 🎉 Projeto Pronto!

Seu projeto foi criado com sucesso usando o **Enterprise Scaffold Project Template v1.0.0**.

**Características principais:**
- ✅ Estrutura completa de diretórios
- ✅ SpecKit configurado (11 agentes + 9 prompts)
- ✅ Segurança avançada (secrets protegidos)
- ✅ Git inicializado (commit + tag)
- ✅ VS Code configurado (MCP, tasks, debug)
- ✅ Documentação organizada (6 sub-pastas)
- ✅ Makefile com comandos úteis

**Suporte e Dúvidas:**
- Consulte `docs/INDEX.md` para orientação
- Use `@session-manager` para iniciar primeira sessão
- Revise `CLAUDE.md` para regras e contexto do projeto

---

*Gerado automaticamente em {{CREATED_AT}}*
"""

# IMP-64: Templates _VSCODE_MCP_JSON e _VSCODE_SETTINGS_JSON removidos.
# Esses arquivos são agora gerados dinamicamente por vscode.py com
# customização por domínio e linguagem.

_MAKEFILE = """\
# Makefile — {{PROJECT_TITLE}}
# Gerado por scaffold.py em {{CREATED_AT}}

.PHONY: help init dev build test lint format clean

## Mostra esta ajuda
help:
\t@grep -E '^## ' Makefile | sed 's/## //'

## [DEPRECATED] — use: uv run scripts/scaffold.py
init:
\t@echo ""
\t@echo " ⚠️  Para criar/configurar o projeto, use diretamente:"
\t@echo "      uv run scripts/scaffold.py"
\t@echo "      python scripts/scaffold.py"
\t@echo ""

## Instala dependências
install-deps:
\t@echo "Instalando dependências..."

## Inicia servidor de desenvolvimento
dev:
\t@echo "Iniciando desenvolvimento..."

## Build de produção
build:
\t@echo "Buildando..."

## Executa testes
test:
\t@echo "Executando testes..."

## Lint do código
lint:
\t@echo "Linting..."

## Formata código
format:
\t@echo "Formatando..."

## Remove arquivos gerados
clean:
\t@rm -rf dist/ build/ __pycache__/ .pytest_cache/ *.egg-info/ .coverage htmlcov/
## Carrega variáveis MCP do .secrets/.env e orienta a abrir o VS Code
mcp:
	@bash scripts/load-mcp.sh"""

# ---------------------------------------------------------------------------
# Templates de segurança GitHub (BUG-06)
# ---------------------------------------------------------------------------

_SECURITY_MD_WITH_GITHUB = """\
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

Instead, please report them privately:

1. Go to the [Security tab]({{GITHUB_REPO}}/security) of this repository
2. Click "Report a vulnerability"
3. Provide detailed information about the vulnerability

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity (Critical: 24-48h, High: 1 week, Medium: 2 weeks, Low: 1 month)

## Security Best Practices

This project follows security best practices:

- ✅ Dependency scanning via Dependabot
- ✅ CodeQL analysis on every PR
- ✅ Secret scanning enabled
- ✅ Branch protection rules
- ✅ Required code review

## Security Contacts

For security-related questions, contact: [security contact info]
"""

_SECURITY_MD_WITHOUT_GITHUB = """
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

Instead, please report them privately through one of these channels:

1. **Email**: Send details to your project security contact
2. **Internal ticketing**: Create a confidential security ticket
3. **Direct contact**: Reach out to project maintainers directly

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity (Critical: 24-48h, High: 1 week, Medium: 2 weeks, Low: 1 month)

## Security Best Practices

This project follows security best practices:

- ✅ Regular security audits
- ✅ Dependency updates and scanning
- ✅ Code review for all changes
- ✅ Secure credential management
- ✅ Principle of least privilege

## Security Contacts

For security-related questions, contact: [security contact info]
"""

_SECURITY_MD_WITHOUT_GITHUB = """
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |

## Reporting a Vulnerability

**DO NOT** open public issues for security vulnerabilities.

Instead, please report them privately through one of these channels:

1. **Email**: Send details to your project security contact
2. **Internal ticketing**: Create a confidential security ticket
3. **Direct contact**: Reach out to project maintainers directly

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity (Critical: 24-48h, High: 1 week, Medium: 2 weeks, Low: 1 month)

## Security Best Practices

This project follows security best practices:

- ✅ Regular security audits
- ✅ Dependency updates and scanning
- ✅ Code review for all changes
- ✅ Secure credential management
- ✅ Principle of least privilege

## Security Contacts

For security-related questions, contact: [security contact info]
"""

_CODEOWNERS = """\
# Code Owners
#
# Lines starting with '#' are comments.
# Each line is a file pattern followed by one or more owners.
# Owners can be @username, @org/team-name, or email addresses.
#
# Docs: https://docs.github.com/articles/about-code-owners

# Default owners for everything in the repo
* @OWNER

# Security-related files require security team review
/.github/workflows/security-*.yml @OWNER
/.github/dependabot.yml @OWNER
/SECURITY.md @OWNER

# Infrastructure and deployment
/deploy/ @OWNER
/terraform/ @OWNER
/ansible/ @OWNER
/.github/workflows/ @OWNER

# CI/CD pipelines
/.github/workflows/*.yml @OWNER

# Documentation
/docs/ @OWNER
/*.md @OWNER
"""

_DEPENDABOT_YML = """\
# Dependabot configuration
# Docs: https://docs.github.com/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file

version: 2
updates:
  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    labels:
      - "dependencies"
      - "github-actions"
    reviewers:
      - "OWNER"
    commit-message:
      prefix: "ci"
      include: "scope"

  # Python (if applicable)
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    labels:
      - "dependencies"
      - "python"
    reviewers:
      - "OWNER"
    commit-message:
      prefix: "deps"
      include: "scope"
    groups:
      dev-dependencies:
        patterns:
          - "pytest*"
          - "black"
          - "ruff"
          - "mypy"

  # Node.js (if applicable)
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "09:00"
    labels:
      - "dependencies"
      - "npm"
    reviewers:
      - "OWNER"
    commit-message:
      prefix: "deps"
      include: "scope"
    groups:
      dev-dependencies:
        patterns:
          - "@types/*"
          - "eslint*"
          - "typescript"
"""

_SECURITY_SCAN_YML = """\
name: Security Scan

on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]
  schedule:
    - cron: '0 6 * * 1'  # Weekly on Mondays at 6 AM UTC

permissions:
  actions: read
  contents: read
  security-events: write

jobs:
  codeql:
    name: CodeQL Analysis
    runs-on: ubuntu-latest

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python', 'javascript' ]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: security-extended

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3

  secret-scan:
    name: Secret Scanning
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: TruffleHog OSS
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
          extra_args: --debug --only-verified
"""

_DEPENDENCY_REVIEW_YML = """\
name: Dependency Review

on:
  pull_request:
    branches: [ main, master, develop ]

permissions:
  contents: read
  pull-requests: write

jobs:
  dependency-review:
    name: Review Dependencies
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          warn-on-OpenSSF-scorecard-level: 3
          comment-summary-in-pr: always
"""

_CLAUDE_MD = """\
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão Geral do Projeto

**Projeto**: `{{PROJECT_NAME}}`
**Descrição**: {{PROJECT_DESCRIPTION}}
**Domínio**: {{DOMAIN}} | **Linguagem**: {{LANGUAGE}}
**Criado em**: {{CREATED_AT}}

## Comandos Frequentes

```bash
# Instalar dependências
make install-deps

# Rodar testes
make test

# Lint e formatação
make lint && make format

# Encerrar sessão (valida integridade do projeto)
make session-end

# Carregar MCP servers
make mcp

# Limpar arquivos gerados
make clean
```

## Ambiente

- Python 3.12+ gerenciado por `uv`
- Ambiente virtual em `.venv/`
- Dependências em `pyproject.toml`

## Estrutura do Projeto

```
{{PROJECT_NAME}}/
├── .claude/            # Claude Code: commands e skills
├── .github/            # CI/CD, agentes SpecKit
├── .secrets/           # Credenciais locais (não versionado, chmod 700)
├── .vscode/            # VS Code: settings, MCP, extensions
├── docs/               # Documentação (INDEX, TODO, SESSIONS)
├── scripts/            # Scripts de automação
└── src/                # Código-fonte
```

## Sessões de Trabalho

Documentar atividades em `docs/SESSIONS/YYYY-MM-DD/`:
- `SESSION_RECOVERY_YYYY-MM-DD.md` — contexto inicial
- `DAILY_ACTIVITIES_YYYY-MM-DD.md` — log incremental
- `FINAL_STATUS_YYYY-MM-DD.md` — estado ao encerrar

## Regras de Desenvolvimento

- Nunca commitar arquivos em `.secrets/`
- Seguir Conventional Commits: `feat`, `fix`, `docs`, `chore`, etc.
- Rodar `make lint` antes de cada commit
- Credenciais HTTP sempre via Python + requests (nunca curl com tokens)

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
"""

_CLAUDE_SETTINGS_JSON = """\
{
  "permissions": {
    "allow": [],
    "deny": []
  }
}
"""

_LOGS_README = """\
# Pasta logs/

## Propósito
Armazenamento de logs de execução:
- Logs de aplicação (runtime logs)
- Logs de scripts de automação
- Logs de testes e validações
- Outputs de diagnóstico

## Conteúdo Esperado
```
logs/
├── README.md
├── app-YYYY-MM-DD.log              # Logs da aplicação
├── scaffold-YYYY-MM-DD.log         # Logs do scaffold
├── tests-YYYY-MM-DD.log            # Logs de testes
└── session-*.log                   # Logs de sessão
```

## Rotation Policy
- Logs mantidos por 90 dias (rotação automática)
- Logs de erro mantidos indefinidamente
- Logs de debug deletados após 7 dias

## Git Status
Esta pasta está no `.gitignore` (conteúdo não versionado).
Apenas este README.md é commitado.

## Logging Configuration
- Python: configurado em `pyproject.toml` → `[tool.logging]`
- Scripts: usar `logging.basicConfig()` com arquivo em `logs/`
- Formato padrão: `YYYY-MM-DD HH:MM:SS [LEVEL] message`
"""

_TMP_README = """\
# Pasta tmp/

## Propósito
Armazenamento temporário para:
- Backups de upgrade (`backup-*`)
- Relatórios de atualização (`UPGRADE_REPORT_*`)
- Outputs temporários de testes
- Arquivos intermediários de processamento

## Conteúdo Esperado
```
tmp/
├── README.md
├── backup-sistema-deploy-YYYYMMDD-HHmmss/  # Backups automáticos
├── UPGRADE_REPORT_*.md                      # Relatórios de upgrade
└── *.tmp                                    # Arquivos temporários
```

## Lifecycle
- Backups: mantidos por 30 dias
- Reports: mantidos permanentemente (documentação)
- Arquivos .tmp: deletados após uso

## Git Status
Esta pasta está no `.gitignore` (conteúdo não versionado).
Apenas este README.md é commitado.

## Scripts Relacionados
- `scripts/scaffold.py --upgrade` (gera backups aqui)
- `scripts/cleanup-tmp.sh` (limpa arquivos antigos)
"""

_MEMORY_README = """\
# Pasta .memory/

## Propósito
Storage para MCP servers de memória:
- `memory` server: contexto de conversas
- `sequential-thinking` server: raciocínios salvos

## Estrutura
```
.memory/
├── README.md
├── *.json          # Memórias estruturadas
└── *.txt           # Memórias em texto livre
```

## Formato
- JSON: metadados + conteúdo estruturado
- TXT: raciocínios, notas, observações

## Indexação
MCP servers indexam automaticamente este diretório.
Busca disponível via interface de memória.

## Git Status
Esta pasta está no `.gitignore` (memórias são locais).
Apenas este README.md é commitado.

## MCP Configuration
Configurado em `.vscode/mcp.json`:
```json
{
  \"memory\": {
    \"command\": \"npx\",
    \"args\": [\"-y\", \"@modelcontextprotocol/server-memory\"]
  }
}
```
"""

_SESSION_INDEX_README = """\
# Pasta .session-index/

## Propósito
SQLite FTS5 database para busca em documentação de sessões.

## Estrutura
```
.session-index/
├── README.md
└── sessions.db     # SQLite database (FTS5)
```

## Database Schema
- Tabela `sessions_fts`: full-text search
- Índice BM25 ranking
- Campos: date, filename, content, metadata

## Uso
```bash
# Buscar em sessões
python scripts/session-search.py \"IMP-65\"

# Reconstruir índice
python scripts/session-index.py --rebuild
```

## Performance
- Queries: <0.01s (FTS5 otimizado)
- Tamanho típico: ~5MB/100 sessões

## Git Status
Database não é versionado (`.gitignore`).
Apenas README.md commitado.

## Sistema Relacionado
- IMP-51: Session Search System
- Scripts: `session-search.py`, `session-index.py`
"""

_SESSION_TIME_README = """\
# Pasta .session-time/

## Propósito
Time tracking de sessões de desenvolvimento.

## Estrutura
```
.session-time/
├── README.md
└── sessions.csv    # Registro de tempo
```

## Formato CSV
```csv
date,start,end,duration_minutes,pauses
2026-05-11,09:00,12:30,210,30
```

## Campos
- `date`: YYYY-MM-DD
- `start`: HH:MM
- `end`: HH:MM
- `duration_minutes`: tempo líquido
- `pauses`: tempo de pausas (café, almoço)

## Uso
```bash
# Registrar sessão
python scripts/session-time.py start
python scripts/session-time.py pause
python scripts/session-time.py resume
python scripts/session-time.py end

# Ver relatório
python scripts/session-time.py report --week
```

## Git Status
CSV não é versionado (dados pessoais).
Apenas README.md commitado.

## Sistema Relacionado
- Feature: Session Management System
- Script: `scripts/session-time.py`
"""

# ---------------------------------------------------------------------------
# Pastas a criar
# ---------------------------------------------------------------------------

# Diretórios base (presentes em todos os projetos, independente de AI)
DIRS_BASE = [
    "docs",
    ".session-docs",
    "docs/architecture",
    "docs/debates",
    "docs/decisions",
    "docs/guides",
    "docs/retrospectives",
    "docs/templates",
    ".github",
    ".github/agents",
    ".github/prompts",
    ".github/prompts/domain",
    ".git-hooks",
    ".secrets",
    ".vscode",
    "scripts/lib",
    "scripts/logs",
    "src",
    "logs",
    "tmp",
    ".memory",
    ".session-index",
    ".session-time",
    ".claude",
    ".claude/commands",
    ".claude/skills",
]

# Diretórios exclusivos do GitHub Copilot (gerenciados pelo CopilotPlugin)
DIRS_COPILOT = [
    "docs/copilot",
]

# Mantido para retrocompatibilidade (usado em testes e imports externos)
DIRS_TO_CREATE = DIRS_BASE + DIRS_COPILOT


# ---------------------------------------------------------------------------
# Arquivos a criar: (caminho relativo, conteúdo_template)
# ---------------------------------------------------------------------------

def get_claude_files() -> list[tuple[str, str]]:
    """
    Retorna os templates de arquivos exclusivos do Claude Code.

    Utilizado pelo ClaudePlugin para obter os templates centralizados
    sem duplicar as strings de conteúdo.

    :return: Lista de (caminho_relativo, conteúdo_template).
    :rtype: list[tuple[str, str]]
    """
    return [
        ("CLAUDE.md",             _CLAUDE_MD),
        (".claude/settings.json", _CLAUDE_SETTINGS_JSON),
    ]


# Arquivos base (presentes em todos os projetos, independente de AI)
FILES_BASE: list[tuple[str, str]] = [
    ("README.md",                  _README_MD),
    ("docs/INDEX.md",              _DOCS_INDEX_MD),
    ("docs/TODO.md",               _DOCS_TODO_MD),
    ("docs/TODAY_ACTIVITIES.md",   _DOCS_TODAY_ACTIVITIES_MD),
    ("docs/architecture/README.md", _DOCS_ARCHITECTURE_README),
    ("docs/debates/README.md",     _DOCS_DEBATES_README),
    ("docs/decisions/README.md",   _DOCS_DECISIONS_README),
    ("docs/guides/README.md",      _DOCS_GUIDES_README),
    ("docs/retrospectives/README.md", _DOCS_RETROSPECTIVES_README),
    ("docs/templates/README.md",   _DOCS_TEMPLATES_README),
    (".gitignore",                 _GITIGNORE),
    (".secrets/README.md",         _SECRETS_README),
    (".secrets/SECURITY.md",       _SECRETS_SECURITY_MD),
    (".git-hooks/pre-commit.secrets", _PRE_COMMIT_SECRETS_HOOK),
    # .vscode/mcp.json e settings.json são gerados dinamicamente por vscode.py (IMP-64)
    ("Makefile",                   _MAKEFILE),
    ("scripts/logs/.gitkeep",      ""),
    ("logs/README.md",             _LOGS_README),
    ("tmp/README.md",              _TMP_README),
    (".memory/README.md",          _MEMORY_README),
    (".session-index/README.md",   _SESSION_INDEX_README),
    (".session-time/README.md",    _SESSION_TIME_README),
]

# Mantido para retrocompatibilidade (inclui arquivos Claude)
FILES_TO_CREATE: list[tuple[str, str]] = FILES_BASE + get_claude_files()


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def create_structure(config: ProjectConfig) -> list[CreatedItem]:
    """
    Cria a estrutura de pastas e arquivos base do projeto em config.project_path.

    - Pastas já existentes → skipped (sem erro)
    - Arquivos já existentes → skipped (não sobrescreve)
    - Retorna lista de CreatedItem com status de cada operação

    A lista de diretórios e arquivos é montada dinamicamente:
    - DIRS_BASE e FILES_BASE para todos os projetos
    - Plugins ativos (via resolve_plugins) contribuem com seus próprios dirs/files
    """
    from .ai import resolve_plugins

    results: list[CreatedItem] = []
    base = config.project_path
    base.mkdir(parents=True, exist_ok=True)

    # Monta lista de diretórios e arquivos com contribuições dos plugins
    dirs = list(DIRS_BASE)
    all_files = list(FILES_BASE)

    for plugin in resolve_plugins(config.ai_assistant):
        dirs.extend(plugin.get_dirs())
        all_files.extend(plugin.get_files())

    # 1. Pastas
    for dir_rel in dirs:
        dir_path = base / dir_rel
        if dir_path.exists():
            results.append(CreatedItem(
                path=dir_path, kind="dir", status="skipped",
            ))
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                results.append(CreatedItem(
                    path=dir_path, kind="dir", status="created",
                ))
            except OSError as e:
                results.append(CreatedItem(
                    path=dir_path, kind="dir", status="error", message=str(e),
                ))

    # 2. Arquivos
    for file_rel, template in all_files:
        file_path = base / file_rel
        if file_path.exists():
            # EXCEÇÃO: Sempre sobrescrever hooks de segurança (garantir versão atualizada)
            # Ref: Fix BUG de hook pre-commit bloqueando .git-hooks/ (2026-04-29)
            if file_rel == ".git-hooks/pre-commit.secrets":
                content = _prepare_content(template, file_rel, config)
                file_path.write_text(content, encoding="utf-8")
                file_path.chmod(0o755)  # rwxr-xr-x
                results.append(CreatedItem(
                    path=file_path, kind="file", status="updated",
                    message="hook de segurança atualizado com versão mais recente"
                ))
                continue

            # NOVO: Tentar merge inteligente ao invés de skip incondicional
            # Fix: BUG-#1.1 (P0 sistêmico - arquivos críticos não mesclados)
            content = _prepare_content(template, file_rel, config)
            merge_result = file_merge.merge_or_skip(
                file_path=file_path,
                template_content=content,
                interactive=False  # Modo CI (não interativo por padrão)
            )
            results.append(merge_result)
            continue
        try:
            # Substitui {{PROJECT_*}} antes de escrever
            content = _prepare_content(template, file_rel, config)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            results.append(CreatedItem(
                path=file_path, kind="file", status="created",
            ))
        except OSError as e:
            results.append(CreatedItem(
                path=file_path, kind="file", status="error", message=str(e),
            ))

    # 3. [nome].code-workspace (nome dinâmico) - agora com MCP integrado
    ws_result = vscode.generate_workspace(config)
    results.append(ws_result)

    return results


def _prepare_content(template: str, file_rel: str, config: ProjectConfig) -> str:
    """Aplica placeholders e ajustes especiais (ex: README github section)."""
    if file_rel == "README.md":
        github_section = (
            f"**Repositório**: [{config.github_repo}]({config.github_repo})"
            if config.github_repo
            else ""
        )
        template = template.replace("{github_section}", github_section)
    return _apply_placeholders(template, config)


# ---------------------------------------------------------------------------
# SpecKit — inicialização via specify CLI e cópia de assets customizados
# ---------------------------------------------------------------------------

# Diretório de templates customizados do SpecKit (separado do projeto DEV)
_SPECKIT_TEMPLATES = _TEMPLATE_ROOT / "scaffold" / "templates" / "speckit"

# Mapeamento ai_assistant → integração(ões) do specify CLI
_AI_TO_SPECIFY: dict[str, list[str]] = {
    "claude":  ["claude"],
    "copilot": ["copilot"],
    "both":    ["claude", "copilot"],
    "none":    [],
}


def run_speckit_init(config: ProjectConfig) -> list[CreatedItem]:
    """
    Executa `specify init --here --force --integration <name>` no diretório do
    projeto para instalar os assets oficiais e versionados do SpecKit.

    Substitui a cópia manual de agents/prompts/specify do projeto DEV. Para
    cada integração mapeada ao ai_assistant do projeto, roda specify uma vez.

    Args:
        config: Configuração do projeto (usa project_path e ai_assistant)
    """
    results: list[CreatedItem] = []
    integrations = _AI_TO_SPECIFY.get(config.ai_assistant, [])

    if not integrations:
        log.info("ai_assistant=%s → specify init ignorado", config.ai_assistant)
        return results

    for integration in integrations:
        cmd = ["specify", "init", "--here", "--force", "--integration", integration]
        log.info("Executando: %s em %s", " ".join(cmd), config.project_path)
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(config.project_path),
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL,  # evita hanging quando stdin é um TTY interativo
            )
            if proc.returncode == 0:
                results.append(CreatedItem(
                    path=config.project_path / ".specify",
                    kind="dir",
                    status="created",
                    message=f"specify init --integration {integration}",
                ))
            else:
                output_diag = (proc.stderr or proc.stdout or "")[:400]
                log.error("specify init falhou (%s):\n%s", integration, output_diag)
                results.append(CreatedItem(
                    path=config.project_path / ".specify",
                    kind="dir",
                    status="error",
                    message=f"specify init --integration {integration}: {output_diag[:200]}",
                ))
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            log.error("Erro ao executar specify init: %s", exc)
            results.append(CreatedItem(
                path=config.project_path / ".specify",
                kind="dir",
                status="error",
                message=f"specify não encontrado ou timeout: {exc}",
            ))

    return results


def copy_speckit(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Compõe perfis de domínio do scaffold para o projeto gerado.

    Agents, prompts e .specify/ são gerados exclusivamente por run_speckit_init()
    via `specify init --here --force --integration <IA>`. Esta função NÃO copia
    nenhum asset do SpecKit — apenas os perfis de domínio do scaffold próprio.

    Perfis de domínio vão para .github/prompts/domain/ e são usados por TODAS as IAs:
      - Claude: session-start referencia .github/prompts/domain/ diretamente
      - Copilot: referenciados via .github/prompts/

    Compõe perfis (de scaffold/profiles/):
      - Perfil de domínio principal (DOMAIN_DEFAULT_PROFILES[cfg.domain])
      - Perfis extras selecionados (cfg.extra_profiles)
      - Sempre: SPECKIT_TRANSVERSAL_PROFILES (ex: devops-security)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes (com backup)
    """
    results: list[CreatedItem] = []
    errors: list[str] = []
    base = config.project_path

    # --- Perfis de domínio — usados por todas as IAs ---
    # 1) principal (pelo domínio)
    domain_profile = DOMAIN_DEFAULT_PROFILES.get(config.domain)
    if domain_profile:
        result = _copy_domain_profile(
            _TEMPLATE_ROOT, base, domain_profile, errors, force=force)
        results.append(result)

    # 2) extras selecionados pelo utilizador (D-21)
    for profile_name in config.extra_profiles:
        if profile_name != domain_profile:  # evita duplicata
            result = _copy_domain_profile(
                _TEMPLATE_ROOT, base, profile_name, errors, force=force)
            results.append(result)

    # 3) transversais — sempre copiados (D-20)
    for profile_name in SPECKIT_TRANSVERSAL_PROFILES:
        result = _copy_domain_profile(
            _TEMPLATE_ROOT, base, profile_name, errors, force=force)
        results.append(result)

    if errors:
        log.warning("⚠️  %d erro(s) ao copiar SpecKit: %s", len(errors), errors)

    return results


# ---------------------------------------------------------------------------
# Custom Agents — etapa independente do SpecKit, por assistente de IA
# ---------------------------------------------------------------------------

def copy_custom_agents(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia agents customizados do scaffold para o projeto gerado, conforme a IA selecionada.

    Esta etapa é independente do SpecKit:
      - Agents `speckit.*` são gerenciados pelo `specify init` e NÃO são copiados aqui.
      - Agents customizados (ex: session-manager, debug, devops-expert) foram criados
        pelo usuário e devem estar presentes em TODAS as IAs configuradas.

    Destinos por ai_assistant:
      - "claude" / "both"  → .github/agents/ (formato agent.md, acessível ao Claude)
                              Obs: .claude/commands/session-manager..md já existe via
                              copy_claude_config(); esta etapa adiciona a versão agent.
      - "copilot" / "both" → .github/agents/ (idem)
      - "none"             → ignorado.

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes (com backup)
    """
    results: list[CreatedItem] = []
    errors: list[str] = []
    base = config.project_path

    if config.ai_assistant == "none":
        log.info("⏭️  agents customizados ignorados (ai_assistant=none)")
        return results

    src_agents = _SPECKIT_TEMPLATES / "agents"
    if not src_agents.is_dir():
        log.warning("⚠️  scaffold/templates/speckit/agents/ não encontrado")
        return results

    for src_file in sorted(src_agents.glob("*.agent.md")):
        if src_file.name.startswith("speckit."):
            continue  # gerido pelo specify init
        dst_file = base / ".github" / "agents" / src_file.name
        result = _copy_file(src_file, dst_file, force=force)
        if result.status == "error":
            errors.append(str(src_file))
        results.append(result)

    if errors:
        log.warning("⚠️  %d erro(s) ao copiar agents customizados: %s", len(errors), errors)

    return results


# ---------------------------------------------------------------------------
# Objetivo.yaml Patching — adicionar campos ausentes durante upgrade
# ---------------------------------------------------------------------------

def _patch_objetivo_yaml(dst_objetivo: Path, src_template: Path) -> CreatedItem:
    """
    Patch objetivo.yaml existente com campos ausentes do template.

    Operação non-destructive:
    - Lê objetivo.yaml existente
    - Verifica se project.docstyle existe
    - Se não existir, adiciona após project.success_statement
    - Preserva formatação, comentários e todo conteúdo existente

    Args:
        dst_objetivo: Path para objetivo.yaml existente
        src_template: Path para template com campos padrão

    Returns:
        CreatedItem com status "updated" se modificou, "skipped" se já tinha

    Ref: BUG-001 Fix #1 — docstyle ausente em repositórios legados
    """
    try:
        # Ler arquivo existente
        existing_content = dst_objetivo.read_text(encoding="utf-8")

        # Verificar se project.docstyle já existe
        if "docstyle:" in existing_content:
            log.info("⏭️  objetivo.yaml já tem docstyle")
            return CreatedItem(
                path=dst_objetivo,
                kind="file",
                status="skipped",
                message="Campo docstyle já presente"
            )

        # Ler template para extrair valor default de docstyle
        template_content = src_template.read_text(encoding="utf-8")

        # Extrair linha do docstyle do template
        docstyle_line = None
        for line in template_content.split("\n"):
            if "docstyle:" in line:
                # Preservar indentação correta (2 espaços para campo project)
                docstyle_line = line
                break

        if not docstyle_line:
            log.warning("⚠️  Template não contém docstyle, pulando patch")
            return CreatedItem(
                path=dst_objetivo,
                kind="file",
                status="skipped",
                message="Template sem docstyle"
            )

        # Encontrar onde inserir: após success_statement ou problema/statement
        lines = existing_content.split("\n")
        insert_index = -1

        for i, line in enumerate(lines):
            # Procurar success_statement (campo que vem antes de docstyle)
            if "success_statement:" in line:
                # Encontrar próxima linha não-vazia após success_statement
                j = i + 1
                while j < len(lines) and (not lines[j].strip() or lines[j].strip().startswith("#")):
                    j += 1
                # Se próxima linha é stakeholders:, inserir antes
                if j < len(lines) and "stakeholders:" in lines[j]:
                    insert_index = j
                    break
                # Caso contrário, inserir após success_statement
                insert_index = i + 1
                break

        if insert_index == -1:
            log.warning("⚠️  Não encontrei onde inserir docstyle, pulando patch")
            return CreatedItem(
                path=dst_objetivo,
                kind="file",
                status="skipped",
                message="Ponto de inserção não encontrado"
            )

        # Inserir docstyle
        lines.insert(insert_index, docstyle_line)
        patched_content = "\n".join(lines)

        # Criar backup antes de modificar
        backup_path = dst_objetivo.with_suffix(".yaml.backup")
        dst_objetivo.rename(backup_path)

        # Escrever conteúdo modificado
        dst_objetivo.write_text(patched_content, encoding="utf-8")

        log.info("✅ objetivo.yaml: adicionado campo docstyle")
        return CreatedItem(
            path=dst_objetivo,
            kind="file",
            status="updated",
            message=f"Campo docstyle adicionado (backup: {backup_path.name})"
        )

    except Exception as exc:
        log.warning("⚠️  Erro ao fazer patch de objetivo.yaml: %s", exc)
        return CreatedItem(
            path=dst_objetivo,
            kind="file",
            status="error",
            message=str(exc)
        )


# ---------------------------------------------------------------------------
# Templates de documentação — setup inicial do projeto
# ---------------------------------------------------------------------------

def setup_project_docs(config: ProjectConfig, is_upgrade: bool = False) -> list[CreatedItem]:
    """
    Configura templates de documentação do projeto.

    Operações:
      1. objetivo-manifest-template.yaml → objetivo.yaml (raiz, com placeholders)
      2. mcp-questions-template.yaml → mcp-questions.yaml (raiz)
      2b. SESSION_DOCS_STYLE_GUIDE.md → docs/guides/SESSION_DOCS_STYLE_GUIDE.md
          (referenciado pelos rituais de sessão)
      3. .session-docs/README.md → guia para criação lazy dos artefatos de sessão

    Substituições em objetivo.yaml:
      - CHANGE_ME (project.name) → config.project_name
      - CHANGE_ME (summary) → config.description
      - CHANGE_ME (problem_statement) → config.description
      - Pasta do projeto atualizada

    Arquivos já existentes são saltados (idempotente).

    UPGRADE: Se objetivo.yaml existe, verifica e adiciona campos ausentes (ex: docstyle).
             Nenhuma pasta datada é criada automaticamente em `.session-docs`.

    Args:
        config: Configuração do projeto
        is_upgrade: True se executando durante scaffold upgrade

    Ref: BUG-09 (corrigido) — documentado em docs/lembrete.md
    Ref: BUG-001 Fix #1 — patch de docstyle durante upgrade
    Ref: BUG-22 — evitar criação automática de pastas de sessão datadas
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT
    src_templates = _TEMPLATE_ROOT / "scaffold" / "templates" / "docs"

    if not src_templates.is_dir():
        log.warning("⚠️  Diretório de origem não encontrado: %s",
                    src_templates)
        return results

    # 1. objetivo.yaml (raiz, com substituições)
    src_objetivo = src_templates / "objetivo-manifest-template.yaml"
    dst_objetivo = base / "objetivo.yaml"
    try:
        if dst_objetivo.exists():
            # BUG-001 Fix #1: Patch campos ausentes durante upgrade
            patch_result = _patch_objetivo_yaml(dst_objetivo, src_objetivo)
            results.append(patch_result)
        else:
            content = src_objetivo.read_text(encoding="utf-8")
            # Substituir placeholders
            content = content.replace(
                'name: "CHANGE_ME"', f'name: "{config.project_name}"')
            content = content.replace(
                'summary: "CHANGE_ME (1-2 linhas)"', f'summary: "{config.description}"')
            content = content.replace(
                'problem_statement: "CHANGE_ME (qual dor real será resolvida?)"', f'problem_statement: "{config.description}"')
            content = content.replace(
                'team_or_person: "CHANGE_ME"', f'team_or_person: "{config.project_name} team"')
            content = content.replace(
                '- "CHANGE_ME"', f'- "{config.project_name} owner"')

            dst_objetivo.write_text(content, encoding="utf-8")
            log.info("✅ criado: objetivo.yaml")
            results.append(CreatedItem(path=dst_objetivo,
                           kind="file", status="created"))
    except OSError as exc:
        log.warning("⚠️  erro ao criar objetivo.yaml: %s", exc)
        results.append(CreatedItem(path=dst_objetivo,
                       kind="file", status="error", message=str(exc)))

    # 2. mcp-questions.yaml (raiz, cópia direta)
    src_mcp = src_templates / "mcp-questions-template.yaml"
    dst_mcp = base / "mcp-questions.yaml"
    result = _copy_file(src_mcp, dst_mcp)
    results.append(result)

    # 2b. SESSION_DOCS_STYLE_GUIDE.md → docs/guides/
    # Referenciado pelos rituais de sessão para validar a documentação incremental.
    src_style_guide = src_root / "docs" / "guides" / "SESSION_DOCS_STYLE_GUIDE.md"
    dst_guides_dir = base / "docs" / "guides"
    dst_style_guide = dst_guides_dir / "SESSION_DOCS_STYLE_GUIDE.md"
    try:
        dst_guides_dir.mkdir(parents=True, exist_ok=True)
        result = _copy_file(src_style_guide, dst_style_guide)
        results.append(result)
    except OSError as exc:
        log.warning("⚠️  erro ao criar docs/guides/SESSION_DOCS_STYLE_GUIDE.md: %s", exc)
        results.append(CreatedItem(path=dst_style_guide,
                       kind="file", status="error", message=str(exc)))

    # 3. README em .session-docs para manter a pasta rastreável sem cristalizar data
    session_docs_readme = base / ".session-docs" / "README.md"
    results.append(_write_file(session_docs_readme, _SESSION_DOCS_README))

    return results


# ---------------------------------------------------------------------------
# Session Support Libraries — módulos compartilhados necessários para scripts
# ---------------------------------------------------------------------------

def copy_session_libs(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia módulos compartilhados necessários para scripts de sessão e memory.

    Módulos copiados:
      1. scripts/lib/__init__.py
      2. scripts/lib/search.py (usado por session-index, session-search, session-chat)
      3. scripts/lib/chat_capture.py (usado por session-chat)
      4. scripts/lib/memory.py (usado por memory scripts)
      5. scripts/lib/git_validators.py (usado por session-time-tracker, pre-commit hooks)
      6. scripts/lib/sanitize.py (usado por mem_save para detectar/sanitizar secrets)
      7. scripts/lib/session_context.py (usado por session-manager)
      8. scripts/lib/session_docs.py (usado por session-manager)
      9. scripts/lib/session_security.py (usado por session-manager)
      10. scripts/lib/git_session.py (usado por session-manager)
      11. scripts/lib/session_workflow.py (usado por session-manager)

    Esses módulos são dependências dos scripts de sessão e memory system.
    Sem eles, os scripts falham com ModuleNotFoundError.

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-14 — session scripts missing lib dependencies
    Ref: BUG-19 — git_validators.py deployment
    Ref: BUG-001 Fix #4 — sanitize.py missing for mem_save
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_lib = _TEMPLATE_ROOT / "scripts" / "lib"
    dst_lib = base / "scripts" / "lib"

    # Criar diretório scripts/lib/ se não existir
    dst_lib.mkdir(parents=True, exist_ok=True)

    libs_to_copy = [
        "__init__.py",
        "search.py",
        "chat_capture.py",
        "memory.py",
        "git_validators.py",
        "sanitize.py",
        "session_context.py",
        "session_docs.py",
        "session_security.py",
        "git_session.py",
        "session_workflow.py",
    ]

    for lib_name in libs_to_copy:
        src_file = src_lib / lib_name
        dst_file = dst_lib / lib_name
        result = _copy_file(src_file, dst_file, force=force)
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Session Scripts — cópia de scripts de rastreamento para novo projeto
# ---------------------------------------------------------------------------

def copy_session_scripts(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia scripts de rastreamento de sessão para o novo projeto.

    Scripts copiados:
      1. session-manager.py → scripts/session-manager.py
      2. session-index.py → scripts/session-index.py
      3. session-time-tracker.py → scripts/session-time-tracker.py
      4. session-search.py → scripts/session-search.py
      5. session-chat.py → scripts/session-chat.py
      6. session-validate.py → scripts/session-validate.py

    Esses scripts são necessários para:
      - Orquestrar rituais de sessão (session-manager.py)
      - Indexar documentação de sessões (session-index.py)
      - Rastrear tempo de trabalho (session-time-tracker.py)
      - Buscar em sessões indexadas (session-search.py)
      - Chat interativo com sessões (session-chat.py)
      - Validar estrutura de sessões (session-validate.py)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-11 — session-start-first incomplete initialization
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT / "scripts"

    scripts_to_copy = [
        "session-manager.py",
        "session-index.py",
        "session-time-tracker.py",
        "session-search.py",
        "session-chat.py",
        "session-validate.py",
    ]

    for script_name in scripts_to_copy:
        src_script = src_root / script_name
        dst_script = base / "scripts" / script_name
        result = _copy_file(src_script, dst_script, force=force)
        results.append(result)

    return results


def copy_memory_scripts(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia scripts do memory system para o novo projeto.

    Scripts copiados:
      1. create_memory_structure.py → scripts/create_memory_structure.py
      2. mem_context.py → scripts/mem_context.py
      3. mem_search.py → scripts/mem_search.py
      4. mem_save.py → scripts/mem_save.py
      5. test_memory_smoke.py → scripts/test_memory_smoke.py

    Esses scripts são necessários para:
      - Criar estrutura .memory/ (create_memory_structure.py)
      - Buscar memories por contexto (mem_context.py)
      - Buscar memories por query (mem_search.py)
      - Salvar novo memory (mem_save.py)
      - Testar funcionalidade do memory system (test_memory_smoke.py)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-12 — memory system not initialized
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT / "scripts"

    scripts_to_copy = [
        "create_memory_structure.py",
        "mem_context.py",
        "mem_search.py",
        "mem_save.py",
        "test_memory_smoke.py",
    ]

    for script_name in scripts_to_copy:
        src_script = src_root / script_name
        dst_script = base / "scripts" / script_name
        result = _copy_file(src_script, dst_script, force=force)
        results.append(result)

    return results


def copy_utility_scripts(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia scripts shell utilitários para o novo projeto.

    Scripts copiados:
      1. activate-mcp.sh → scripts/activate-mcp.sh
      2. git-commit-with-file.sh → scripts/git-commit-with-file.sh
      3. cleanup-tmp.sh → scripts/cleanup-tmp.sh
      4. validate-docs-links.sh → scripts/validate-docs-links.sh

    Esses scripts são necessários para:
      - Validar e ativar servidores MCP (activate-mcp.sh)
      - Git commits com arquivo de mensagem (git-commit-with-file.sh)
      - Limpar arquivos temporários (cleanup-tmp.sh)
      - Validar links em documentação (validate-docs-links.sh)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: Validação pós-scaffold - scripts shell essenciais
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT / "scripts"

    scripts_to_copy = [
        "activate-mcp.sh",
        "git-commit-with-file.sh",
        "cleanup-tmp.sh",
        "validate-docs-links.sh",
    ]

    for script_name in scripts_to_copy:
        src_script = src_root / script_name
        dst_script = base / "scripts" / script_name
        result = _copy_file(src_script, dst_script, force=force)
        # Garantir permissões executáveis (755)
        if result.status in ("created", "updated") and dst_script.exists():
            try:
                dst_script.chmod(0o755)
                log.debug("✅ Permissões executáveis aplicadas: %s", dst_script.name)
            except OSError as exc:
                log.warning("⚠️  Não foi possível aplicar chmod 755 em %s: %s", dst_script, exc)
        results.append(result)

    return results


def copy_copilot_instructions(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia arquivos de instruções customizadas do Copilot para o novo projeto.

    Arquivos copiados:
      1. copilot-instructions.md → .github/copilot-instructions.md
      2. .copilot-rules.md → .copilot-rules.md (raiz)

    Esses arquivos são necessários para:
      - Persistir instruções customizadas do Copilot (copilot-instructions.md)
      - Definir regras críticas P0/P1 do projeto (.copilot-rules.md)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: BUG-13 — copilot instructions not persisted
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT

    # Copiar copilot-instructions.md para .github/
    src_instructions = src_root / ".github" / "copilot-instructions.md"
    dst_instructions = base / ".github" / "copilot-instructions.md"
    result = _copy_file(src_instructions, dst_instructions, force=force)
    results.append(result)

    # Copiar .copilot-rules.md para raiz do projeto
    src_rules = src_root / ".copilot-rules.md"
    dst_rules = base / ".copilot-rules.md"
    result = _copy_file(src_rules, dst_rules, force=force)
    results.append(result)

    return results


def copy_claude_config(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia configuração do Claude Code para o novo projeto.

    Arquivos copiados:
      1. .claude/commands/*.md → .claude/commands/ (todos os slash commands)
      2. .claude/skills/*/SKILL.md → .claude/skills/*/ (todos os skills)

    Nota: .claude/settings.json e CLAUDE.md são gerados via FILES_TO_CREATE
    em create_structure() com placeholders substituídos automaticamente.
    settings.local.json (machine-specific) NÃO é copiado — fica em .gitignore.

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: IMP-XX — Claude Code integration
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_claude = _TEMPLATE_ROOT / ".claude"

    if not src_claude.is_dir():
        log.warning("⚠️  Diretório .claude/ não encontrado em %s", _TEMPLATE_ROOT)
        return results

    # 1. commands/ — copiar todos os .md (slash commands)
    src_commands = src_claude / "commands"
    if src_commands.is_dir():
        for src_file in sorted(src_commands.glob("*.md")):
            dst_file = base / ".claude" / "commands" / src_file.name
            result = _copy_file(src_file, dst_file, force=force)
            results.append(result)
    else:
        log.warning("⚠️  .claude/commands/ não encontrado em %s", _TEMPLATE_ROOT)

    # 2. skills/ — copiar cada subdiretório (skill_name/SKILL.md e arquivos extras)
    src_skills = src_claude / "skills"
    if src_skills.is_dir():
        for skill_dir in sorted(src_skills.iterdir()):
            if skill_dir.is_dir():
                for src_file in sorted(skill_dir.rglob("*")):
                    if src_file.is_file():
                        rel = src_file.relative_to(src_claude)
                        dst_file = base / ".claude" / rel
                        result = _copy_file(src_file, dst_file, force=force)
                        results.append(result)
    else:
        log.warning("⚠️  .claude/skills/ não encontrado em %s", _TEMPLATE_ROOT)

    return results


def copy_github_templates(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Copia templates de GitHub Best Practices para o novo projeto.

    Templates copiados (P1):
      1. CONTRIBUTING.md → raiz do projeto (com substituição de variáveis)
      2. PULL_REQUEST_TEMPLATE.md → .github/
      3. CODEOWNERS → .github/
      4. BRANCH_PROTECTION_SETUP.md → docs/

    Templates adicionais (P2):
      5. Issue templates → .github/ISSUE_TEMPLATE/ (bug, feature, docs, question)
      6. GitHub Actions workflows → .github/workflows/
      7. Git hooks → scripts/git-hooks/
      8. Badge guide → .github/BADGES.md
      9. Branch protection script → scripts/

    Variáveis substituídas:
      - {{ project_name }} → config.project_name
      - {{ current_date }} → config.created_at
      - {{ github_repo }} → config.github_repo (se configurado)

    Args:
        config: Configuração do projeto
        force: Se True, sobrescreve arquivos existentes após backup

    Ref: P1/P2 - GitHub Best Practices Integration
    """
    results: list[CreatedItem] = []
    base = config.project_path
    src_root = _TEMPLATE_ROOT / "scaffold" / "templates" / "base-configs" / "common"

    # Mapeamento de variáveis customizadas para templates GitHub
    github_owner_repo = config.github_repo if config.github_repo else "owner/repo"
    github_parts = github_owner_repo.split("/") if "/" in github_owner_repo else ["owner", "repo"]

    template_vars = {
        "{{ project_name }}": config.project_name,
        "{{ current_date }}": config.created_at.split("T")[0],  # YYYY-MM-DD apenas
        "{{ github_repo }}": github_parts[1] if len(github_parts) > 1 else "repo",
        "{{ github_owner }}": github_parts[0] if len(github_parts) > 0 else "owner",
    }

    # === P1 Templates ===

    # 1. CONTRIBUTING.md → raiz (com substituição de variáveis)
    src_contributing = src_root / "CONTRIBUTING.md"
    dst_contributing = base / "CONTRIBUTING.md"
    result = _copy_file_with_vars(src_contributing, dst_contributing, template_vars, force=force)
    results.append(result)

    # 2. PULL_REQUEST_TEMPLATE.md → .github/
    src_pr_template = src_root / "PULL_REQUEST_TEMPLATE.md"
    dst_pr_template = base / ".github" / "PULL_REQUEST_TEMPLATE.md"
    result = _copy_file(src_pr_template, dst_pr_template, force=force)
    results.append(result)

    # 3. CODEOWNERS → .github/
    src_codeowners = src_root / "CODEOWNERS"
    dst_codeowners = base / ".github" / "CODEOWNERS"
    result = _copy_file_with_vars(src_codeowners, dst_codeowners, template_vars, force=force)
    results.append(result)

    # 4. BRANCH_PROTECTION_SETUP.md → docs/
    src_guide = _TEMPLATE_ROOT / "docs" / "guides" / "BRANCH_PROTECTION_SETUP.md"
    dst_guide = base / "docs" / "BRANCH_PROTECTION_SETUP.md"
    result = _copy_file_with_vars(src_guide, dst_guide, template_vars, force=force)
    results.append(result)

    # === P2 Templates ===

    # 5. Issue templates → .github/ISSUE_TEMPLATE/ (.yml da base-configs + .md do template root)
    issue_templates_yml = ["bug_report.yml", "feature_request.yml", "documentation.yml", "question.yml", "config.yml"]
    for template_name in issue_templates_yml:
        src_issue = src_root / "ISSUE_TEMPLATE" / template_name
        dst_issue = base / ".github" / "ISSUE_TEMPLATE" / template_name
        result = _copy_file_with_vars(src_issue, dst_issue, template_vars, force=force)
        results.append(result)
    src_issue_md = _TEMPLATE_ROOT / ".github" / "ISSUE_TEMPLATE"
    if src_issue_md.is_dir():
        for src_file in sorted(src_issue_md.glob("*.md")):
            dst_file = base / ".github" / "ISSUE_TEMPLATE" / src_file.name
            result = _copy_file(src_file, dst_file, force=force)
            results.append(result)

    # 6. GitHub Actions workflows → .github/workflows/
    src_workflow = src_root / "workflows" / "git-validation.yml"
    dst_workflow = base / ".github" / "workflows" / "git-validation.yml"
    result = _copy_file_with_vars(src_workflow, dst_workflow, template_vars, force=force)
    results.append(result)

    # 7. Git hooks → scripts/git-hooks/
    src_hook = _TEMPLATE_ROOT / "scripts" / "git-hooks" / "commit-msg"
    dst_hook = base / "scripts" / "git-hooks" / "commit-msg"
    result = _copy_file(src_hook, dst_hook, force=force)
    # Garantir permissões executáveis
    if result.status in ("created", "updated") and dst_hook.exists():
        try:
            dst_hook.chmod(0o755)
            log.debug("✅ Permissões executáveis aplicadas: %s", dst_hook.name)
        except OSError as exc:
            log.warning("⚠️  Não foi possível aplicar chmod 755 em %s: %s", dst_hook, exc)
    results.append(result)

    # 8. Badge guide → .github/BADGES.md
    src_badges = src_root / "BADGES.md"
    dst_badges = base / ".github" / "BADGES.md"
    result = _copy_file_with_vars(src_badges, dst_badges, template_vars, force=force)
    results.append(result)

    # 9. Branch protection script → scripts/
    src_script = _TEMPLATE_ROOT / "scripts" / "setup-branch-protection.py"
    dst_script = base / "scripts" / "setup-branch-protection.py"
    result = _copy_file(src_script, dst_script, force=force)
    # Garantir permissões executáveis
    if result.status in ("created", "updated") and dst_script.exists():
        try:
            dst_script.chmod(0o755)
            log.debug("✅ Permissões executáveis aplicadas: %s", dst_script.name)
        except OSError as exc:
            log.warning("⚠️  Não foi possível aplicar chmod 755 em %s: %s", dst_script, exc)
    results.append(result)

    return results


def _copy_file_with_vars(
    src: Path,
    dst: Path,
    template_vars: dict[str, str],
    force: bool = False
) -> CreatedItem:
    """
    Copia arquivo aplicando substituição de variáveis.

    Args:
        src: Arquivo de origem
        dst: Arquivo de destino
        template_vars: Dicionário de variáveis a substituir
        force: Se True, sobrescreve arquivo existente

    Returns:
        CreatedItem com status da operação
    """
    if not src.exists():
        msg = f"origem não encontrada: {src}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    # Verificar se destino existe
    if dst.exists() and not force:
        msg = "já existe (use --force para sobrescrever)"
        log.info("⏭️  %s: %s", dst.name, msg)
        return CreatedItem(path=dst, kind="file", status="skipped", message=msg)

    try:
        # Criar diretório pai se necessário
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Ler conteúdo do template
        content = src.read_text(encoding="utf-8")

        # Aplicar substituições
        for var, value in template_vars.items():
            content = content.replace(var, value)

        # Escrever arquivo processado
        dst.write_text(content, encoding="utf-8")

        log.info("✅ %s (com substituição de variáveis)", dst.name)
        return CreatedItem(path=dst, kind="file", status="created")

    except (OSError, UnicodeDecodeError) as exc:
        msg = f"erro ao copiar: {exc}"
        log.error("❌ %s: %s", dst.name, msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)


def _copy_domain_profile(
    src_root: Path,
    base: Path,
    profile_name: str,
    errors: list[str],
    force: bool = False,
) -> CreatedItem:
    """Copia um perfil de domínio individual de scaffold/templates/speckit/prompts/domain/."""
    src_file = _SPECKIT_TEMPLATES / "prompts" / "domain" / f"{profile_name}.prompt.md"
    dst_file = base / ".github" / "prompts" / "domain" / f"{profile_name}.prompt.md"
    result = _copy_file(src_file, dst_file, force=force)
    if result.status == "error":
        errors.append(str(src_file))
    return result


def _copy_file(src: Path, dst: Path, force: bool = False) -> CreatedItem:
    """Copia src → dst com logging. Detecta drift e permite force com backup.

    Integração BUG-16: Usa sistema de merge inteligente quando disponível.

    Args:
        src: Arquivo de origem (upstream template)
        dst: Arquivo de destino (projeto local)
        force: Se True, sobrescreve arquivo existente após backup

    Returns:
        CreatedItem com status:
        - created: arquivo criado ou atualizado
        - merged: arquivo mergeado com sistema de merge inteligente (BUG-16)
        - skipped: arquivo existe e sem drift ou force=False
        - drift: arquivo existe com drift detectado (apenas se force=False)
        - error: erro ao copiar

    Nota: Se dst for um symlink, NUNCA sobrescreve (preserva symlink).
    """
    import hashlib

    if not src.exists():
        msg = f"origem não encontrada: {src}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    # PROTEÇÃO: Nunca sobrescrever symlinks (preservar configuração de shared files)
    if dst.is_symlink():
        log.info("🔗 skipped (symlink): %s → %s", dst.name, dst.resolve())
        return CreatedItem(
            path=dst,
            kind="symlink",
            status="skipped",
            message=f"Preservado symlink → {dst.resolve()}"
        )

    # Ler conteúdo do template
    try:
        template_content = src.read_text(encoding="utf-8")
    except Exception as exc:
        msg = f"Erro ao ler template {src}: {exc}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    # Calcular hash do arquivo upstream
    src_hash = hashlib.sha256(src.read_bytes()).hexdigest()[:8]

    if dst.exists():
        # BUG-16: Tentar merge inteligente primeiro (antes de force)
        # Verificar se há merger disponível para este tipo de arquivo
        merge_result = file_merge.merge_or_skip(dst, template_content, interactive=False)

        if merge_result.status == "merged" or merge_result.status == "created":
            # Merge bem-sucedido via sistema de merge inteligente
            log.info("🔀 merged via %s", merge_result.message or "intelligent merge system")
            return merge_result

        # Se chegou aqui, não há merger disponível ou merge foi skipped
        # Continuar com lógica antiga de drift detection

        # Calcular hash do arquivo local
        dst_hash = hashlib.sha256(dst.read_bytes()).hexdigest()[:8]

        # Detectar drift (Opção 3)
        if src_hash != dst_hash:
            if not force:
                log.warning(
                    "📊 drift detectado: %s (upstream: %s, local: %s)",
                    dst.name, src_hash, dst_hash
                )
                return CreatedItem(
                    path=dst,
                    kind="file",
                    status="drift",
                    message=f"Arquivo difere do upstream (upstream: {src_hash}, local: {dst_hash})"
                )
            else:
                # Opção 1: backup antes de sobrescrever
                backup_path = dst.with_suffix(dst.suffix + ".backup")
                shutil.copy2(dst, backup_path)
                log.info("📦 backup: %s → %s", dst.name, backup_path.name)
        else:
            # Arquivo idêntico ao upstream
            log.info("⏭️  skipped (idêntico ao upstream): %s", dst)
            return CreatedItem(path=dst, kind="file", status="skipped")

    # Criar ou sobrescrever arquivo
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(template_content, encoding="utf-8")
        action = "atualizado" if dst.exists() and force else "criado"
        log.info("✅ %s: %s → %s", action, src.name, dst)
        return CreatedItem(path=dst, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao copiar %s: %s", src, exc)
        return CreatedItem(path=dst, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# Constitution — geração do arquivo .specify/memory/constitution.md
# ---------------------------------------------------------------------------

def generate_constitution(config: ProjectConfig) -> CreatedItem:
    """
    Gera .specify/memory/constitution.md no projeto destino.

    Copia o constitution-template.md do template, resolve os placeholders
    padrão e adiciona metadados do projeto no cabeçalho.
    Se o arquivo já existir no destino, salta (idempotente).
    """
    src = _TEMPLATE_ROOT / ".specify" / "templates" / "constitution-template.md"
    dst = config.project_path / ".specify" / "memory" / "constitution.md"

    if dst.exists():
        log.info("⏭️  skipped (já existe): %s", dst)
        return CreatedItem(path=dst, kind="file", status="skipped")

    if not src.exists():
        msg = f"constitution-template.md não encontrado em {src}"
        log.warning("⚠️  %s", msg)
        return CreatedItem(path=dst, kind="file", status="error", message=msg)

    try:
        template_content = src.read_text(encoding="utf-8")

        # Substitui os marcadores de template do SpecKit
        content = template_content.replace(
            "[PROJECT_NAME]", config.project_title)
        content = content.replace(
            "[RATIFICATION_DATE]", config.created_at[:10])
        content = content.replace(
            "[LAST_AMENDED_DATE]", config.created_at[:10])
        content = content.replace("[CONSTITUTION_VERSION]", "1.0.0")

        # Cabeçalho com metadados do scaffold
        header = (
            f"<!-- Gerado por scaffold.py {SPECKIT_SYNC_DATE} | "
            f"Domínio: {config.domain} | Linguagem: {config.language} -->\n"
        )
        content = header + content

        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(content, encoding="utf-8")
        log.info("✅ constitution.md gerado: %s", dst)
        return CreatedItem(path=dst, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao gerar constitution.md: %s", exc)
        return CreatedItem(path=dst, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# MCP env vars required per domain (mirrors vscode._MCP_BY_DOMAIN "env" fields)
# ---------------------------------------------------------------------------

_MCP_ENV_VARS_BY_DOMAIN: dict[str, list[str]] = {
    "programming":    ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "infrastructure": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "analysis":       ["BRAVE_API_KEY"],
}


# ---------------------------------------------------------------------------
# load-mcp.sh — geração dinâmica por domínio
# ---------------------------------------------------------------------------

def generate_load_mcp(config: ProjectConfig) -> CreatedItem:
    """
    Gera scripts/load-mcp.sh com as variáveis de ambiente obrigatórias para o domínio.

    - Verifica .secrets/.env; orienta o usuário se ausente
    - Carrega as variáveis (set -a; source; set +a)
    - Valida variáveis obrigatórias pelo domínio
    - Verifica presença de npx e node
    - Imprime instrução para abrir o VS Code
    - Idempotente — skip se scripts/load-mcp.sh já existe
    """
    dest = config.project_path / "scripts" / "load-mcp.sh"
    if dest.exists():
        return CreatedItem(path=dest, kind="file", status="skipped", message="já existe")

    required_vars = _MCP_ENV_VARS_BY_DOMAIN.get(config.domain, [])

    # Bloco de exemplo para .secrets/.env
    example_lines = "\n".join(
        f"   {var}=your-value-here" for var in required_vars
    ) or "   (nenhuma variável requerida para este domínio)"

    # Bloco de validação de variáveis
    validation_lines = "\n".join(
        f'  [[ -z "${{{var}:-}}" ]] && MISSING+=("{var}")'
        for var in required_vars
    ) or "  # nenhuma variável requerida para este domínio"

    script = (
        "#!/usr/bin/env bash\n"
        "# load-mcp.sh — Carrega variáveis de ambiente para MCP Servers\n"
        f"# Domínio: {config.domain}\n"
        "# Gerado por scaffold.py — NÃO commitar este script com tokens reais\n"
        "#\n"
        "# Uso:\n"
        "#   bash scripts/load-mcp.sh\n"
        "#   make mcp\n"
        "set -euo pipefail\n"
        "\n"
        'SECRETS_ENV=".secrets/.env"\n'
        "\n"
        'if [[ ! -f "$SECRETS_ENV" ]]; then\n'
        '  echo "⚠️  .secrets/.env não encontrado."\n'
        '  echo "   Crie o arquivo com os tokens necessários:"\n'
        '  echo ""\n'
        '  echo "   # .secrets/.env"\n'
        f'  echo "{example_lines}"\n'
        '  echo ""\n'
        '  exit 1\n'
        "fi\n"
        "\n"
        "# Carrega sem poluir o histórico do shell\n"
        "set -a; source \"$SECRETS_ENV\"; set +a\n"
        "\n"
        "# Valida variáveis obrigatórias\n"
        "MISSING=()\n"
        + validation_lines + "\n"
        "\n"
        "if [[ ${#MISSING[@]} -gt 0 ]]; then\n"
        '  echo "❌ Variáveis obrigatórias ausentes em $SECRETS_ENV:"\n'
        "  printf '   %s\\n' \"${MISSING[@]}\"\n"
        "  exit 1\n"
        "fi\n"
        "\n"
        "# Verifica dependências de runtime\n"
        "for cmd in npx node; do\n"
        '  if ! command -v "$cmd" &>/dev/null; then\n'
        '    echo "❌ Dependência ausente: $cmd"\n'
        '    echo "   Instale o Node.js: https://nodejs.org/"\n'
        "    exit 1\n"
        "  fi\n"
        "done\n"
        "\n"
        'echo "✅ Ambiente MCP carregado com sucesso."\n'
        'echo ""\n'
        'echo "   Abra o VS Code com:"\n'
        'echo "   code ."\n'
    )

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(script, encoding="utf-8")
        # Torna executável: rwxr-xr-x (0o755)
        os.chmod(dest, 0o755)
        log.info("✅ load-mcp.sh gerado: %s", dest)
        return CreatedItem(path=dest, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao gerar load-mcp.sh: %s", exc)
        return CreatedItem(path=dest, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# Secrets Security Setup (IMP-60)
# ---------------------------------------------------------------------------

def setup_secrets_security(config: ProjectConfig) -> list[CreatedItem]:
    """
    Configura proteção avançada para .secrets/ directory.

    Implementa:
      - chmod 700 em .secrets/ (somente proprietário tem acesso)
      - .secrets/SECURITY.md já foi criado em FILES_TO_CREATE
      - .git-hooks/pre-commit.secrets template já foi criado
      - Valida que .secrets/ está no .gitignore

    Esta função é chamada APÓS create_structure(), garantindo que:
      1. .secrets/ já existe
      2. Arquivos de documentação já foram criados
      3. Aplicamos permissões restritivas

    Retorna lista de ações realizadas (permissões modificadas, validações).

    Ref: IMP-60 — documentado em docs/lembrete.md
    """
    results: list[CreatedItem] = []
    base = config.project_path
    secrets_dir = base / ".secrets"

    # 1. Verificar que .secrets/ existe
    if not secrets_dir.exists():
        msg = ".secrets/ não existe ainda — pulando setup de segurança"
        log.warning("⚠️  %s", msg)
        return results

    # 2. Aplicar chmod 700 (rwx------)
    try:
        current_perms = secrets_dir.stat().st_mode & 0o777
        if current_perms != 0o700:
            secrets_dir.chmod(0o700)
            log.info("🔒 .secrets/ protegido: chmod 700 aplicado")
            results.append(CreatedItem(
                path=secrets_dir,
                kind="dir",
                status="secured",
                message="chmod 700 aplicado"
            ))
        else:
            log.info("✅ .secrets/ já tem permissão 700")
            results.append(CreatedItem(
                path=secrets_dir,
                kind="dir",
                status="skipped",
                message="permissões já corretas (700)"
            ))
    except OSError as exc:
        log.warning("⚠️  erro ao aplicar chmod 700: %s", exc)
        results.append(CreatedItem(
            path=secrets_dir,
            kind="dir",
            status="error",
            message=f"chmod falhou: {exc}"
        ))

    # 3. Validar .gitignore contém .secrets/
    gitignore = base / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".secrets/" in content:
            log.info("✅ .gitignore contém .secrets/")
            results.append(CreatedItem(
                path=gitignore,
                kind="validation",
                status="ok",
                message=".secrets/ está ignorado no git"
            ))
        else:
            log.warning("⚠️  .secrets/ NÃO está em .gitignore!")
            results.append(CreatedItem(
                path=gitignore,
                kind="validation",
                status="warning",
                message=".secrets/ ausente no .gitignore"
            ))

    # 4. Ativar pre-commit hook automaticamente (BUG-#4 fix)
    hook_template = base / ".git-hooks" / "pre-commit.secrets"
    hook_target = base / ".git" / "hooks" / "pre-commit"

    if hook_template.exists():
        try:
            # Verificar se .git/hooks/ existe
            hooks_dir = base / ".git" / "hooks"
            if not hooks_dir.exists():
                log.warning(
                    "⚠️  .git/hooks/ não existe — pulando ativação de hook")
                results.append(CreatedItem(
                    path=hook_template,
                    kind="file",
                    status="available",
                    message="hook disponível (sem .git/hooks/ para instalar)"
                ))
            else:
                # Copiar hook template para .git/hooks/pre-commit
                shutil.copy2(hook_template, hook_target)
                hook_target.chmod(0o755)  # rwxr-xr-x

                log.info("✅ Pre-commit hook ativado automaticamente")
                results.append(CreatedItem(
                    path=hook_target,
                    kind="file",
                    status="activated",
                    message="pre-commit hook instalado em .git/hooks/"
                ))
        except Exception as e:
            log.warning("⚠️  Falha ao ativar pre-commit hook: %s", e)
            results.append(CreatedItem(
                path=hook_template,
                kind="file",
                status="available",
                message=f"hook disponível (ativação manual necessária): {e}"
            ))

    return results


# ---------------------------------------------------------------------------
# GitHub Security Files (BUG-06)
# ---------------------------------------------------------------------------

def generate_github_security_files(config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
    """
    Gera arquivos de segurança GitHub no projeto.

    Cria:
      - SECURITY.md (política de reporte de vulnerabilidades)
      - .github/CODEOWNERS (ownership de código) — apenas se github_repo configurado
      - .github/dependabot.yml (atualizações automáticas) — apenas se github_repo configurado
      - .github/workflows/security-scan.yml (CodeQL + secret scan) — apenas se github_repo configurado
      - .github/workflows/dependency-review.yml (análise de dependências em PRs) — apenas se github_repo configurado

    Se github_repo não estiver configurado, gerencia apenas SECURITY.md com versão genérica.

    OWNER placeholder é substituído pelo dono do repo GitHub (se disponível).

    Ref: BUG-06 — documentado em docs/lembrete.md
    """
    results: list[CreatedItem] = []
    base = config.project_path

    # Extrair owner do github_repo (ex: https://github.com/user/repo → user)
    owner = "OWNER"
    if config.github_repo:
        parts = config.github_repo.rstrip("/").split("/")
        if len(parts) >= 2:
            owner = f"@{parts[-2]}"

    # Arquivo 1: SECURITY.md (raiz do projeto)
    # Usa template com GitHub se repositório configurado, senão usa versão genérica
    security_md = base / "SECURITY.md"
    if config.github_repo:
        content = _apply_placeholders(_SECURITY_MD_WITH_GITHUB, config)
    else:
        content = _SECURITY_MD_WITHOUT_GITHUB
    results.append(_write_managed_file(security_md, content, force=force))

    # Arquivos 2-5: Apenas criar se houver repositório GitHub configurado
    if not config.github_repo:
        return results

    # Arquivo 2: .github/CODEOWNERS
    codeowners = base / ".github" / "CODEOWNERS"
    content = _CODEOWNERS.replace("@OWNER", owner)
    results.append(_write_managed_file(codeowners, content, force=force))

    # Arquivo 3: .github/dependabot.yml
    dependabot = base / ".github" / "dependabot.yml"
    content = _DEPENDABOT_YML.replace("OWNER", owner.lstrip("@"))
    results.append(_write_managed_file(dependabot, content, force=force))

    # Arquivo 4: .github/workflows/security-scan.yml
    security_scan = base / ".github" / "workflows" / "security-scan.yml"
    results.append(_write_managed_file(security_scan, _SECURITY_SCAN_YML, force=force))

    # Arquivo 5: .github/workflows/dependency-review.yml
    dependency_review = base / ".github" / "workflows" / "dependency-review.yml"
    results.append(_write_managed_file(dependency_review, _DEPENDENCY_REVIEW_YML, force=force))

    return results


def generate_project_creation_summary(config: ProjectConfig) -> CreatedItem:
    """
    Gera docs/PROJECT_CREATION_SUMMARY.md com resumo completo da criação.

    Contém:
      - Informações do projeto (nome, descrição, domínio, linguagem)
      - Estrutura de diretórios criada
      - Profiles aplicados
      - Status do Git (commit, tag, remote)
      - Próximos passos recomendados
      - Comandos úteis (Makefile, Git, Docs)
      - Links para documentação interna
      - Recursos de segurança
      - Agentes e prompts SpecKit disponíveis
      - Convenções do projeto

    Ref: IMP-63 — Feature documentada em docs/lembrete.md
    """
    summary_path = config.project_path / "docs" / "PROJECT_CREATION_SUMMARY.md"

    if summary_path.exists():
        log.info("⏭️  já existe: %s", summary_path.name)
        return CreatedItem(path=summary_path, kind="file", status="skipped")

    # Construir seção de profiles aplicados
    profiles = []
    # Adicionar profile padrão do domínio
    if config.domain in DOMAIN_DEFAULT_PROFILES:
        # DOMAIN_DEFAULT_PROFILES é dict[str, str], não list!
        profiles.append(DOMAIN_DEFAULT_PROFILES[config.domain])
    # Adicionar profiles transversais (aplicados sempre)
    profiles.extend(SPECKIT_TRANSVERSAL_PROFILES)
    # Adicionar profiles extras (se fornecidos)
    if config.extra_profiles:
        if isinstance(config.extra_profiles, str):
            # Se for string, fazer split por vírgula
            extra = [p.strip()
                     for p in config.extra_profiles.split(",") if p.strip()]
            profiles.extend(extra)
        elif isinstance(config.extra_profiles, list):
            profiles.extend(config.extra_profiles)

    # Remover duplicatas mantendo ordem
    seen = set()
    unique_profiles = []
    for p in profiles:
        if p not in seen:
            seen.add(p)
            unique_profiles.append(p)

    if unique_profiles:
        profiles_section = "**Profiles aplicados:**\n"
        for profile in unique_profiles:
            profiles_section += f"- ✅ `{profile}`\n"
    else:
        profiles_section = "*Nenhum profile específico aplicado.*\n"

    # Seção de remote Git (se configurado)
    git_remote_section = ""
    if config.github_repo:
        git_remote_section = f"\n- Remote: `origin` → {config.github_repo}"

    # Aplicar placeholders
    content = _apply_placeholders(_PROJECT_CREATION_SUMMARY, config)
    content = content.replace("{profiles_section}", profiles_section)
    content = content.replace("{git_remote_section}", git_remote_section)

    return _write_file(summary_path, content)


def _write_file(path: Path, content: str) -> CreatedItem:
    """Escreve arquivo com conteúdo, criando diretórios necessários."""
    try:
        if path.exists():
            log.info("⏭️  já existe: %s", path.name)
            return CreatedItem(path=path, kind="file", status="skipped")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log.info("✅ criado: %s", path.name)
        return CreatedItem(path=path, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao criar %s: %s", path.name, exc)
        return CreatedItem(path=path, kind="file", status="error", message=str(exc))


def _write_managed_file(path: Path, content: str, force: bool = False) -> CreatedItem:
    """Escreve arquivo gerenciado com detecção de drift e backup opcional."""
    import hashlib

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]

    if path.is_symlink():
        log.info("🔗 skipped (symlink): %s → %s", path.name, path.resolve())
        return CreatedItem(
            path=path,
            kind="symlink",
            status="skipped",
            message=f"Preservado symlink → {path.resolve()}",
        )

    file_exists = path.exists()
    if file_exists:
        try:
            current_content = path.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning("⚠️  erro ao ler %s: %s", path.name, exc)
            return CreatedItem(path=path, kind="file", status="error", message=str(exc))

        current_hash = hashlib.sha256(current_content.encode("utf-8")).hexdigest()[:8]
        if current_hash == content_hash:
            log.info("⏭️  skipped (idêntico ao upstream): %s", path)
            return CreatedItem(path=path, kind="file", status="skipped")

        if not force:
            log.warning(
                "📊 drift detectado: %s (upstream: %s, local: %s)",
                path.name,
                content_hash,
                current_hash,
            )
            return CreatedItem(
                path=path,
                kind="file",
                status="drift",
                message=f"Arquivo difere do upstream (upstream: {content_hash}, local: {current_hash})",
            )

        backup_path = path.with_suffix(path.suffix + ".backup")
        try:
            shutil.copy2(path, backup_path)
            log.info("📦 backup: %s → %s", path.name, backup_path.name)
        except OSError as exc:
            log.warning("⚠️  erro ao criar backup de %s: %s", path.name, exc)
            return CreatedItem(path=path, kind="file", status="error", message=str(exc))

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        action = "atualizado" if file_exists else "criado"
        log.info("✅ %s: %s", action, path)
        return CreatedItem(path=path, kind="file", status="created")
    except OSError as exc:
        log.warning("⚠️  erro ao escrever %s: %s", path.name, exc)
        return CreatedItem(path=path, kind="file", status="error", message=str(exc))


# ---------------------------------------------------------------------------
# Scaffold state — persiste e recupera configuração do projeto gerado
# ---------------------------------------------------------------------------

_STATE_FILENAME = ".scaffold-state.yaml"


def write_scaffold_state(
    config: ProjectConfig,
    profiles_applied: list[str] | None = None,
) -> CreatedItem:
    """
    Persiste o estado do projeto em <target_dir>/.scaffold-state.yaml.

    Chamado ao final de flow_new_project e de flow_compose_profiles para que
    o fluxo de upgrade saiba quais perfis foram aplicados e com qual config
    o projeto foi criado.

    O arquivo é SEMPRE sobrescrito (não é idempotente como os demais).

    IMP-65 Fase 1: Agora também armazena template_versions para tracking de drift.
    """
    from datetime import datetime, timezone

    state_path = config.project_path / _STATE_FILENAME

    # Carrega estado anterior (se existir) para preservar created_at e profiles
    existing_profiles: list[str] = []
    original_created_at: str = config.created_at
    if state_path.exists():
        try:
            import yaml
            with state_path.open(encoding="utf-8") as f:
                old = yaml.safe_load(f) or {}
            existing_profiles = old.get("profiles_applied", [])
            original_created_at = old.get("created_at", config.created_at)
        except Exception:
            pass

    # Merge: adiciona novos perfis sem duplicar
    merged_profiles = list(existing_profiles)
    for p in (profiles_applied or []):
        if p not in merged_profiles:
            merged_profiles.append(p)

    # IMP-65 Fase 1: Scan current template versions
    # BUG-03 FIX: Also collect template bases for merge tracking (IMP-65 Phase 3)
    template_versions = {}
    template_bases = {}
    template_dir = config.project_path / ".specify" / "templates"
    if template_dir.exists():
        try:
            from . import template_version
            templates = template_version.scan_templates(template_dir)
            template_versions = {
                name: info.version
                for name, info in templates.items()
            }

            # Collect base content for three-way merge support
            for name, info in templates.items():
                content = info.path.read_text(encoding="utf-8")
                template_bases[name] = {
                    "version": info.version,
                    "content": content,
                }
        except Exception as exc:
            log.warning("⚠️  Failed to scan template versions: %s", exc)

    state: dict = {
        "scaffold_version": "1.0.0",
        "created_at": original_created_at,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": {
            "name":         config.project_name,
            "title":        config.project_title,
            "description":  config.description,
            "domain":       config.domain,
            "language":     config.language,
            "github_repo":  config.github_repo or "",
            "ai_assistant": config.ai_assistant,
        },
        "paths": {
            "target_dir": str(config.target_dir),
            "shared_dir": str(config.shared_dir),
        },
        "profiles_applied": merged_profiles,
        "template_versions": template_versions,  # IMP-65 Fase 1
        "template_bases": template_bases,        # BUG-03 FIX: IMP-65 Phase 3
    }

    try:
        import yaml
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            yaml.dump(state, allow_unicode=True,
                      default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )
        log.info("✅ scaffold state gravado: %s", state_path)
        return CreatedItem(path=state_path, kind="file", status="created")
    except Exception as exc:
        log.warning("⚠️  erro ao gravar scaffold state: %s", exc)
        return CreatedItem(path=state_path, kind="file", status="error", message=str(exc))


def read_scaffold_state(target_dir: Path) -> dict | None:
    """
    Lê <target_dir>/.scaffold-state.yaml e retorna o dict com o estado.
    Retorna None se o arquivo não existe ou está corrompido.
    """
    state_path = target_dir / _STATE_FILENAME
    if not state_path.exists():
        return None
    try:
        import yaml
        with state_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else None
    except Exception as exc:
        log.warning("⚠️  erro ao ler scaffold state: %s", exc)
        return None


def config_from_state(state: dict, override_target: Path | None = None) -> ProjectConfig:
    """
    Reconstrói um ProjectConfig a partir do estado salvo.

    Args:
        state:           dict retornado por read_scaffold_state()
        override_target: se fornecido, sobrescreve paths.target_dir do state
                        No modo upgrade, override_target é o próprio projeto.
    """
    from datetime import datetime, timezone

    proj = state.get("project", {})
    paths = state.get("paths", {})
    project_name = proj.get("name", "unknown")

    # Correção IMP-47 + BUG-10: detectar se override_target é o próprio projeto
    if override_target:
        # Verificar se .scaffold-state.yaml existe em override_target
        # Se sim, override_target É O PROJETO (upgrade in-place)
        state_file = override_target / ".scaffold-state.yaml"

        if state_file.exists():
            # Upgrade in-place: override_target tem .scaffold-state.yaml
            # target_dir deve ser override_target (sem parent)
            # project_path será = target_dir (sem concatenação)
            target = override_target
        elif override_target.name == project_name:
            # override_target termina com project_name → é o projeto
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
        project_title=proj.get("title", proj.get("name", "Unknown")),
        description=proj.get("description", ""),
        domain=proj.get("domain", "programming"),
        language=proj.get("language", "python"),
        github_repo=proj.get("github_repo") or None,
        shared_dir=shared,
        target_dir=target,
        created_at=state.get("created_at", datetime.now(
            timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        extra_profiles=state.get("profiles_applied", []),
        ai_assistant=proj.get("ai_assistant", "both"),
    )
