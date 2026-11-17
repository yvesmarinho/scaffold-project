# Copilot Rules — Test Project

> Arquivo gerado automaticamente por `scripts/scaffold.py` em {{CREATED_AT}}
> Regras genéricas compartilhadas: ver `.copilot-rules.md` (symlink para shared)

---

## 🎯 Identidade do Projeto

| Campo | Valor |
|-------|-------|
| **Nome** | `test-project` |
| **Título** | Test Project |
| **Descrição** | A test project for smoke testing |
| **Domínio** | infrastructure |
| **Linguagem principal** | python |
| **Repositório** | (não informado) |
| **Criado em** | {{CREATED_AT}} |

---

## 🎭 Perfis de Domínio Ativos

| Perfil | Arquivo | Tipo |
|--------|---------|------|
| **Principal** | `.github/prompts/domain/devops-infrastructure.prompt.md` | Domínio padrão |
| **Segurança** | `.github/prompts/domain/devops-security.prompt.md` | Transversal |


Para declarar o modo ativo no início de cada sessão:

```
Modo: INFRASTRUCTURE. Projeto: test-project. Perfil: devops-infrastructure.
```

Ritual canônico: `python scripts/session-manager.py --json start`

---

## 📁 Estrutura de Pastas

```
test-project/
├── terraform/             # IaC Terraform (se aplicável)
│   ├── modules/
│   ├── environments/
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── variables.tf
├── ansible/               # Playbooks Ansible (se aplicável)
│   ├── roles/
│   └── playbooks/
├── docker/                # Dockerfiles e compose
│   ├── Dockerfile
│   └── docker-compose.yml
├── k8s/                   # Manifests Kubernetes (se aplicável)
│   ├── base/
│   └── overlays/
├── scripts/               # Scripts de automação de infra
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── RUNBOOK.md         # Procedures operacionais
└── .vscode/
```

---

## 🔧 Regras Específicas — Domínio `infrastructure`

> Pré-preenchidas com base no domínio. Edite e acrescente conforme o projeto evoluir.

- **P0**: IaC declarativo — nunca modificar estado de infraestrutura fora do código versionado
- **P0**: Toda operação destrutiva (`destroy`, `delete`, `drop`) requer confirmação explícita do usuário
- **P0**: Scripts de infra devem ser idempotentes — executar N vezes = mesmo resultado
- **P1**: Secrets nunca em código IaC — usar Vault, SSM Parameter Store ou `.secrets/`
- **P1**: Nenhuma alteração em produção sem `plan`/`dry-run` revisado primeiro

---

## 💻 Convenções de Linguagem — `python`

| Aspecto | Convenção |
|---------|-----------|
| Estilo | PEP 8 — formatado com `ruff format` ou `black` |
| Nomenclatura | `snake_case` para funções/variáveis, `PascalCase` para classes |
| Type hints | Obrigatório em funções públicas (`from __future__ import annotations`) |
| Imports | `isort` ou `ruff --select I` — agrupamento stdlib/third-party/interno |
| Linter | `ruff check` ou `flake8` |
| Testes | `pytest` — cobertura mínima 80% — rodar com `uv run pytest` |
| Gerenciador | **`uv`** (➕ preferêncial) — `uv venv`, `uv add`, `uv run`, `uv sync` |
| Virtual env | `.venv/` na raiz (gitignored) — criado com `uv venv` |
| Dependências | `pyproject.toml` (PEP 621) — lock em `uv.lock` (commitar) |
| Scripts | Executar via `uv run <script>` — não ativar `.venv` manualmente |

---

## 🔐 Segurança

- Credenciais, tokens e chaves: **NUNCA** em arquivos versionados
- Usar `.secrets/.env` + `${env:VAR_NAME}` em `mcp.json`
- `.secrets/` está no `.gitignore` ✅
- Scan obrigatório a cada início de sessão: `.env*`, `*.key`, `*.pem`, `*.crt`, `*secret*`, `*password*`, `*token*`

---

## 📋 Decisões Técnicas do Projeto

> Registre aqui decisões arquiteturais e técnicas tomadas ao longo do projeto.

| Data | Decisão | Resultado |
|------|---------|-----------|
| {{CREATED_AT}} | Scaffold inicial criado | Domínio: infrastructure, Linguagem: python |

---

## 🔗 Referências

- [README.md](README.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/TODO.md](docs/TODO.md)
- [.copilot-rules.md](.copilot-rules.md) ← regras genéricas compartilhadas
- [.github/prompts/domain/devops-infrastructure.prompt.md](.github/prompts/domain/devops-infrastructure.prompt.md)

---

*Gerado por scripts/scaffold.py v1.7.1 | {{CREATED_AT}}*
