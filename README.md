# 🚀 Enterprise Scaffold Project Template

A production-ready, scalable project template designed to accelerate development of enterprise applications across multiple programming languages, incorporating industry best practices, design patterns, and modern development tools.

> **🎯 Ready to Use**: This is a complete template. Clone, run the initialization script, and start coding in minutes!

---

> **⚠️ CI/CD Temporariamente Desabilitado**
> Os workflows GitHub Actions foram temporariamente removidos durante o desenvolvimento ativo do template.
> **Status:** 🔴 Workflows desabilitados desde 2026-03-31
> **Motivo:** Foco no desenvolvimento core (scaffold.py, MCP, documentação)
> **Restauração:** Q2 2026 após conclusão do core
> **Exceção:** ✅ `.github/workflows/scaffold-tests.yml` está **ativo** (testes automatizados do scaffold)
> **Guia completo:** [WORKFLOWS_REMOVED_TEMPORARILY.md](WORKFLOWS_REMOVED_TEMPORARILY.md) | [CI-CD-RESTORATION-GUIDE.md](docs/CI-CD-RESTORATION-GUIDE.md)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Project Structure](#project-structure)
- [Supported Languages](#supported-languages)
- [Architecture Patterns](#architecture-patterns)
- [Template Usage](#template-usage)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [CI/CD Integration](#cicd-integration)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This template provides a comprehensive starting point for enterprise projects, eliminating the repetitive setup tasks and ensuring consistency across projects. It implements proven architectural patterns and incorporates modern development practices to help teams deliver high-quality software faster.

### Key Objectives

- **Rapid Project Initialization**: Get new projects up and running in minutes
- **Best Practices Built-in**: Folder structures, naming conventions, and code organization following industry standards
- **Multi-Language Support**: Flexible architecture supporting multiple programming languages
- **Scalability**: Designed to grow from MVP to enterprise-scale applications
- **Maintainability**: Clean architecture with clear separation of concerns
- **Developer Experience**: Integrated tooling and automation for smooth development workflow

## 🚀 Quick Start

### Option 1: Global Command (Recommended)

Install the `new-project` command globally for maximum convenience:

```bash
# Install (one time)
cp scripts/bin/new-project ~/.local/bin/new-project
chmod +x ~/.local/bin/new-project

# Use from anywhere
new-project my-api
new-project my-api --compose python-fastapi
new-project --help
```

📖 **Full guide**: [docs/NEW_PROJECT_COMMAND.md](docs/NEW_PROJECT_COMMAND.md)

### Option 2: Direct Scaffold Usage

```bash
# Interactive mode
python scripts/scaffold.py new

# CI mode (non-interactive)
python scripts/scaffold.py new --ci --name my-api --domain programming --language python
```

📖 **Detailed guide**: [QUICKSTART.md](QUICKSTART.md)

### Option 3: Adopt a Legacy Project

Para projetos **já existentes** (criados fora do scaffold, sem `.scaffold-state.yaml`):

```bash
# Detecta linguagem/domínio, confirma e aplica o template sem sobrescrever nada
python scripts/scaffold.py adopt --target-dir /caminho/do/projeto

# Não-interativo, com overrides
python scripts/scaffold.py adopt --ci --target-dir . --language python --ai claude
```

O `adopt` detecta linguagem (`pyproject.toml`, `package.json`, `go.mod`, ...) e domínio (marcadores IaC como `*.tf`/`Chart.yaml` → `infrastructure`), grava o `.scaffold-state.yaml` e delega ao pipeline idempotente do `upgrade` — arquivos existentes são **preservados** (use `--force` para sobrescrever com backup). Depois da adoção, use `scaffold.py upgrade` normalmente.

---

## 🧙 Objetivo.yaml v2.0 — Human-Readable Project Definition

Define your project goals and scope in a **human-readable format** using the new `objetivo.yaml` v2.0 specification.

### What is objetivo.yaml v2.0?

A **Markdown Híbrido** format (YAML frontmatter + numbered emoji sections) that combines:
- ✅ Machine-readable metadata (project name, type, domain, language)
- ✅ Human-readable descriptions (what, why, scope)
- ✅ Progressive disclosure (P0 required → P1 recommended → P2 optional)

### Quick Example

```yaml
---
version: "2.0"
project:
  name: "user-auth-api"
  title: "User Authentication API"
  type: "backend-api"
  domain: "programming"
  language: "python"
---

## 1️⃣ O que este projeto faz?

RESTful API for user authentication with JWT tokens and OAuth2 integration.

## 2️⃣ Qual problema resolve?

Current basic auth is insecure, 20% of accounts compromised monthly.

## 3️⃣ Escopo do Projeto

### ✅ Incluído
- JWT authentication (P0)
- OAuth2 Google/GitHub (P1)
- 2FA via SMS (P2)

### ❌ Excluído
- Social login (Facebook, Twitter)
- Biometric authentication
```

### Create objetivo.yaml with Interactive Wizard

```bash
# Interactive wizard (5-10 min)
scaffold.py objetivo-init

# Non-interactive (CI/CD)
scaffold.py objetivo-init --from-file answers.json

# Just copy template
scaffold.py objetivo-init --template-only
```

### Create objetivo.yaml with the `objetivo-init` Agent

Alternativa ao wizard CLI: o agent [`objetivo-init`](.github/agents/objetivo-init.agent.md) conduz uma entrevista guiada (agnóstica de linguagem) a partir do template canônico [`docs/templates/objetivo-init-minimal.yaml`](docs/templates/objetivo-init-minimal.yaml), com sugestão contextual em cada pergunta, e persiste o resultado em `objetivo-init.yaml` na raiz do projeto (mesmo destino do wizard). Projetos gerados pelo scaffold recebem o agent automaticamente em `.github/agents/`.

### Validate and Generate Technical Spec

```bash
# Validate objetivo.yaml
scaffold.py objetivo-validate

# Generate technical YAML spec
scaffold.py objetivo-generate
# Output: objetivo-spec.yaml (profiles, features, personas auto-detected)

# Use spec to create project
scaffold.py new --config objetivo-spec.yaml
```

### Migrate from v1.0 to v2.0

```bash
# Migrate old formato (pure YAML) → new format (Markdown Híbrido)
scaffold.py objetivo-migrate --file objetivo.yaml

# Preview before overwrite
scaffold.py objetivo-migrate --file objetivo.yaml --no-auto
```

📖 **Complete guide**: [docs/guides/OBJETIVO_WIZARD_GUIDE.md](docs/guides/OBJETIVO_WIZARD_GUIDE.md)
📋 **Specification**: [specs/066-objetivo-yaml-v2/spec.md](specs/066-objetivo-yaml-v2/spec.md)
🔀 **v1.0 vs v2.0 comparison**: [docs/debates/COMPARACAO-OBJETIVO-V1-V2.md](docs/debates/COMPARACAO-OBJETIVO-V1-V2.md)

---

## ✨ Features

### 🏗️ Architecture & Design Patterns

- **MVP (Model-View-Presenter) Pattern**: Clean separation between business logic and presentation
- **Factory Pattern**: Flexible object creation with dependency injection support
- **Repository Pattern**: Abstract data access layer for easy database switching
- **Service Layer Pattern**: Business logic encapsulation
- **Dependency Injection**: Loose coupling and testable code

### 🛠️ Development Tools

- **Global Command**: `new-project` wrapper for convenient project creation
- **Speckit Integration**: Automated specification and documentation generation
- **Session Documentation System**: Structured session tracking with incremental documentation (IMP-48, IMP-49, IMP-50)
- **Full-Text Search**: SQLite FTS5-based search across all documentation (sessions, docs, specs) with scope filtering (IMP-51, IMP-57)
- **Migration Toolkit**: Legacy session docs → canonical format converter with validation (IMP-50)
- **Memory Assessment**: Data-driven framework for evaluating active memory needs (IMP-58)
- **CI/CD Ready**: Pre-configured GitHub Actions workflows (temporarily disabled, restoration guide available)
- **Code Quality**: ESLint, Prettier, and language-specific linters
- **Testing Framework**: Unit, integration, and E2E testing setup
- **Docker Support**: Containerization for consistent environments
- **Environment Management**: Multi-environment configuration (dev, staging, production)

### 📁 Standardized Structure

- Consistent folder organization across all projects
- Clear separation of concerns
- Modular and extensible architecture
- Easy navigation and onboarding

## 📂 Project Structure

### Template Structure (Before Initialization)

```
scaffold-project/                 # Template repository
├── .copilot-rules.md           # Copilot rules (symlink to shared)
├── .copilot-git-rules.md       # Git rules (symlink to shared)
├── .copilot-strict-enforcement.md
├── .copilot-strict-rules.md
├── .copilot-file-rules.sh
├── .git/                       # Template git history
├── .gitignore
├── .secrets/                   # Secrets directory template
│   └── README.md
├── .specify/                   # Speckit configuration
├── .vscode/                    # VS Code settings
├── docs/                       # Template documentation
│   ├── INDEX.md
│   ├── TODO.md
│   ├── TODAY_ACTIVITIES.md
│   ├── TEMPLATE_USAGE.md
│   └── MAKEFILE.md
├── setup/                      # Setup & installation scripts (legacy)
│   ├── README.md               # Setup scripts documentation
│   ├── init-new-project.sh     # [DEPRECATED] Use scaffold.py
│   ├── setup-project-links.sh  # [DEPRECATED] Use scaffold.py
│   └── check-project-links.sh  # [DEPRECATED] Use scaffold.py
├── scripts/                    # Active scripts
│   ├── scaffold.py             # ✨ Main scaffolding tool
│   ├── manage.py               # Project management
│   └── lib/                    # Python libraries
├── Makefile                    # 40+ automation commands
├── README.md                   # This file
└── scaffold-project.code-workspace
```

### After Initialization (`uv run scripts/scaffold.py`)

Após executar `uv run scripts/scaffold.py --new`, o novo projeto terá:

```
my-awesome-project/             # Your new project
├── .copilot-rules.md          # Symlink para shared configs
├── .copilot-rules-[nome].md   # Regras específicas geradas pelo scaffold
├── .github/
│   └── prompts/               # Symlink para shared prompts
├── .git/                      # Fresh Git repository
├── .gitignore
├── .secrets/                  # Secrets directory (git-ignored)
│   └── README.md
├── .vscode/
│   ├── mcp.json               # MCP servers por domínio
│   ├── settings.json          # Settings por linguagem
│   └── extensions.json        # Extensões por domínio+linguagem
├── docs/
│   ├── INDEX.md
│   ├── TODO.md
│   └── SESSIONS/
├── src/
├── tests/
├── Makefile
└── README.md
```

```
my-awesome-project/             # Your new project
├── .copilot-rules.md          # Symlinked to shared configs
├── .copilot-git-rules.md      # Symlinked to shared configs
├── .copilot-strict-enforcement.md  # Symlinked
├── .copilot-strict-rules.md   # Symlinked
├── .copilot-file-rules.sh     # Symlinked
├── .git/                      # Fresh Git repository
├── .github/                   # Generated by make
│   ├── agents/
│   ├── prompts/
│   ├── scripts/
│   ├── templates/
│   ├── workflows/
│   │   └── ci.yml            # CI/CD pipeline
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
├── .gitignore                 # Git ignore rules
├── .editorconfig              # Generated by make
├── .env.example               # Generated by make
├── .secrets/                  # Secrets directory (git-ignored)
│   └── README.md
├── .specify/                  # Speckit integration
│   ├── config.json
│   └── specs/
├── .vscode/                   # VS Code configuration
│   ├── settings.json
│   ├── tasks.json
│   └── launch.json
├── config/                    # Environment configs
│   ├── development.json
│   ├── staging.json
│   └── production.json
├── docs/                      # Project documentation
│   ├── INDEX.md
│   ├── TODO.md
│   ├── TODAY_ACTIVITIES.md
│   ├── architecture/
│   ├── api/
│   └── guides/
├── docker/                    # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── scripts/                   # Utility scripts
│   ├── setup/
│   ├── build/
│   └── deploy/
├── src/                       # Source code (generated by make)
│   ├── core/                 # Core business logic
│   │   ├── models/
│   │   ├── interfaces/
│   │   └── services/
│   ├── data/                 # Data access layer
│   │   ├── repositories/
│   │   ├── factories/
│   │   └── migrations/
│   ├── presentation/         # Presentation layer (MVP)
│   │   ├── views/
│   │   ├── presenters/
│   │   └── viewmodels/
│   ├── infrastructure/       # Infrastructure concerns
│   │   ├── config/
│   │   ├── logging/
│   │   └── security/
│   └── shared/               # Shared utilities
│       ├── constants/
│       ├── helpers/
│       └── validators/
├── tests/                    # Test suites (generated by make)
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── requirements.txt          # Python dependencies (if Python)
├── requirements-dev.txt      # Python dev dependencies
├── setup.py                  # Python package setup
├── package.json              # Node.js dependencies (if Node)
├── Makefile                  # Project automation
├── README.md                 # Project documentation
└── my-awesome-project.code-workspace  # VS Code workspace

```

> **Note**: The `src/`, `tests/`, and `config/` directories are created by `make init` or `make structure`. The template itself only contains the essential files and scripts.

## 🌐 Supported Languages

This template is designed to work with multiple programming languages. Choose your stack based on project requirements:

### Primary Languages

- **Python** 🐍
  - Django/FastAPI for web applications
  - Data science and ML projects
  - Automation and scripting

- **TypeScript/JavaScript** 📘
  - Node.js backend services
  - React/Vue/Angular frontends
  - Full-stack applications

- **Java** ☕
  - Spring Boot enterprise applications
  - Microservices architecture
  - Android development

- **C#/.NET** 🔷
  - ASP.NET Core web applications
  - Desktop applications
  - Azure cloud services

- **Go** 🔵
  - High-performance microservices
  - CLI tools
  - Cloud-native applications

### Language-Specific Adaptations

Each language implementation maintains the same architectural patterns while respecting language-specific conventions and best practices.

## 🏛️ Architecture Patterns

### MVP (Model-View-Presenter) Pattern

The MVP pattern ensures clean separation of concerns:

```
┌─────────────┐         ┌──────────────┐         ┌─────────┐
│    View     │────────▶│  Presenter   │────────▶│  Model  │
│  (UI Layer) │◀────────│  (Logic)     │◀────────│ (Data)  │
└─────────────┘         └──────────────┘         └─────────┘
```

**Benefits:**
- Testable business logic (Presenter can be tested without UI)
- Flexible UI changes without affecting business logic
- Clear data flow and responsibility separation

### Factory Pattern Implementation

```python
# Example Factory Pattern
class ServiceFactory:
    """Factory for creating service instances with proper dependencies"""

    @staticmethod
    def create_user_service(config):
        repository = RepositoryFactory.create_user_repository(config)
        validator = ValidatorFactory.create_user_validator()
        return UserService(repository, validator)
```

### Repository Pattern

```python
# Abstract repository interface
class IUserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: str) -> User:
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        pass
```

## 🚀 Quick Start

### Inicializar novo projeto (Recomendado)

```bash
# 1. Clone este template
git clone https://github.com/yvesmarinho/scaffold-project.git meu-projeto
cd meu-projeto

# 2. Executar o scaffold (interativo)
uv run scripts/scaffold.py

# 3. Ou modo não-interativo (CI/CD)
uv run scripts/scaffold.py --new \
  --name meu-projeto \
  --domain programming \
  --language python \
  --repo https://github.com/org/meu-projeto

# 4. Verificar links e estrutura
uv run scripts/scaffold.py --check
```

### Option 2: Using Makefile

```bash
git clone <template-url> my-new-project
cd my-new-project
make init-new-project NAME=my-new-project
```

### Option 3: Manual Setup

See [docs/TEMPLATE_USAGE.md](docs/TEMPLATE_USAGE.md) for complete manual setup instructions.

## 📚 Template Usage

This project is designed to be used as a template. See the comprehensive guide:

👉 **[Complete Template Usage Guide](docs/TEMPLATE_USAGE.md)**

Key features:
- ✅ Automatic project initialization
- ✅ Shared configuration management via symlinks
- ✅ Placeholder replacement
- ✅ Git reinitialization
- ✅ Clean template-specific files
- ✅ Ready-to-use structure

### What Happens During Initialization?

1. **Validates** project name (lowercase, hyphens allowed)
2. **Configures symlinks** to shared Copilot rules
3. **Replaces placeholders** (scaffold-project → your-project)
4. **Cleans** template-specific files
5. **Reinitializes** Git with clean history
6. **Runs** `make init` to create structure

### Shared Configuration Management

The template uses **symlinks** to maintain shared configurations:

```bash
# Setup shared configs (first time only)
make setup-shared-configs

# Verify symlinks in your project
make check-project-links
```

Benefits:
- ✅ Single source of truth for Copilot rules
- ✅ Consistent configuration across all projects
- ✅ 90% space reduction (400KB → 82KB for 5 projects)
- ✅ Update once, applies to all projects

## 🚀 Getting Started (After Initialization)

### Prerequisites

- Git
- Docker & Docker Compose (recommended)
- Language-specific runtime (Node.js, Python, Java, etc.)
- Speckit CLI (for specification management)

### Quick Start

1. **Clone the template**
   ```bash
   git clone <repository-url> my-new-project
   cd my-new-project
   ```

2. **Initialize the project**
   ```bash
   ./scripts/setup/init.sh
   ```

3. **Choose your language stack**
   ```bash
   ./scripts/setup/setup-language.sh --lang python
   # or
   ./scripts/setup/setup-language.sh --lang typescript
   ```

4. **Install dependencies**
   ```bash
   # Python
   pip install -r requirements.txt

   # Node.js
   npm install

   # Using Docker
   docker-compose up -d
   ```

5. **Start development**
   ```bash
   # Development server
   npm run dev  # or equivalent for your language
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Application
APP_NAME=my-project
APP_ENV=development
APP_PORT=3000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp_db
DB_USER=myapp_user
DB_PASSWORD=secure_password

# Authentication
JWT_SECRET=your-secret-key
JWT_EXPIRATION=3600

# External Services
API_KEY=your-api-key
```

### Speckit Configuration

Configure Speckit in `.specify/config.json`:

```json
{
  "version": "2.0",
  "organization": "your-org",
  "project": "your-project",
  "specs": {
    "outputPath": "docs/api",
    "format": "openapi-3.0"
  }
}
```

### Secrets Management

The `.secrets/` directory is automatically created and git-ignored for storing sensitive files:

```bash
.secrets/
├── README.md           # Instructions
├── certificates/       # SSL/TLS certificates
├── keys/              # Private keys
└── tokens/            # API tokens and credentials
```

**Supported file types (auto-ignored)**:
- Certificate files: `*.crt`, `*.pem`, `*.p12`
- Private keys: `*.key`
- Environment secrets: Keep in `.env` (also git-ignored)

**Best Practices**:
- Never commit secrets to version control
- Use environment variables for runtime secrets
- Rotate credentials regularly
- Use secret management tools (Vault, AWS Secrets Manager) in production
- Document required secrets in `.env.example`

## 💻 Development Workflow

### Branch Strategy

- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: New features
- `bugfix/*`: Bug fixes
- `hotfix/*`: Production hotfixes

### Code Standards

1. **Naming Conventions**
   - Classes: PascalCase
   - Functions/Methods: camelCase or snake_case (language-dependent)
   - Constants: UPPER_SNAKE_CASE
   - Files: kebab-case or snake_case

2. **Code Reviews**
   - All changes require PR review
   - Minimum 1 approval required
   - CI must pass before merge

3. **Commit Messages**
   ```
   type(scope): subject

   body

   footer
   ```
   Types: feat, fix, docs, style, refactor, test, chore

### Development Commands

```bash
# Run tests
npm test                    # or language equivalent

# Run linter
npm run lint                # or language equivalent

# Format code
npm run format              # or language equivalent

# Build project
npm run build               # or language equivalent

# Generate documentation
npm run docs:generate       # or language equivalent
```

### Configuration Validation

The project supports automated validation of YAML and JSON configuration files using industry-standard tools.

#### YAML Validation with yamllint

**Installation**:
```bash
# Using uv (recommended for Python projects)
uv add --dev yamllint

# Or using pip
pip install yamllint

# Verify installation
yamllint --version
```

**Usage**:
```bash
# Validate specific directories
yamllint .github/workflows/
yamllint profile-descriptors/

# Validate with custom config
yamllint -c .yamllint.yml .

# Check all YAML files in project
find . -name "*.yml" -o -name "*.yaml" | xargs yamllint

# Integration with make
make lint-yaml
```

**Configuration**: Create `.yamllint.yml` in project root:
```yaml
extends: default
rules:
  line-length:
    max: 120
  indentation:
    spaces: 2
  comments:
    min-spaces-from-content: 1
```

#### JSON Schema Validation

**Installation**:
```bash
# Using uv (recommended for Python projects)
uv add --dev jsonschema

# Or using pip
pip install jsonschema

# Or using npm (for Node.js projects)
npm install --save-dev ajv-cli
```

**Usage with Python**:
```bash
# Validate JSON against schema
python -m jsonschema -i config.json schema.json

# Validate VS Code settings
python -m jsonschema -i .vscode/mcp.json schemas/mcp-schema.json

# Check .scaffold-state.yaml format
python -m jsonschema -i .scaffold-state.yaml schemas/scaffold-state-schema.json
```

**Usage with Node.js (ajv-cli)**:
```bash
# Validate JSON
npx ajv validate -s schema.json -d config.json

# Validate multiple files
npx ajv validate -s schema.json -d "config/*.json"
```

**Example Python validation script**:
```python
import json
from jsonschema import validate, ValidationError

# Load schema
with open('schema.json') as f:
    schema = json.load(f)

# Load and validate data
with open('config.json') as f:
    data = json.load(f)
    try:
        validate(instance=data, schema=schema)
        print("✅ Valid configuration")
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
```

#### Makefile Integration

Add these targets to your `Makefile`:
```makefile
.PHONY: lint-yaml lint-json lint-config

## Validate YAML files
lint-yaml:
	@echo "🔍 Validating YAML configuratio files..."
	@yamllint .github/workflows/ profile-descriptors/ .scaffold-state.yaml

## Validate JSON files
lint-json:
	@echo "🔍 Validating JSON configuration files..."
	@find . -name "*.json" -not -path "*/node_modules/*" -not -path "*/.venv/*" \
	  -exec echo "Checking: {}" \; -exec python -m json.tool {} /dev/null \;

## Validate all configuration files
lint-config: lint-yaml lint-json
	@echo "✅ All configuration files validated"
```

**Usage**:
```bash
# Validate all configuration
make lint-config

# Validate only YAML
make lint-yaml

# Validate only JSON
make lint-json

# Integrate with CI
make lint lint-config
```

#### Pre-commit Hooks

Automate validation with pre-commit hooks in `.git/hooks/pre-commit`:
```bash
#!/bin/bash
make lint-yaml || exit 1
make lint-json || exit 1
```

### Temporary Files Management

The project includes a dedicated `tmp/` directory for temporary files:

**Purpose**:
- Store temporary files during script execution
- Avoid cluttering system `/tmp/` with project-specific files
- Automatic cleanup on session end

**Usage in scripts**:
```bash
# Instead of
temp_file="/tmp/myfile.txt"

# Use
temp_file="./tmp/myfile.txt"
```

**Cleanup**:
```bash
# Manual cleanup (with dry run)
./scripts/cleanup-tmp.sh --dry-run

# Clean all temporary files
./scripts/cleanup-tmp.sh --verbose
```

**Note**: The `tmp/` directory is automatically cleaned at session end. Files are ignored by git (except `tmp/README.md`).

## 🧪 Testing Strategy

### Test Pyramid

```
        ╱╲
       ╱E2E╲         ← Few, critical user journeys
      ╱──────╲
     ╱  Inte- ╲      ← Medium, component integration
    ╱  gration ╲
   ╱────────────╲
  ╱     Unit     ╲   ← Many, fast, isolated tests
 ╱────────────────╲
```

### Test Organization

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **E2E Tests**: Test complete user workflows

### Running Tests

```bash
# All tests
npm test

# Unit tests only
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Coverage report
npm run test:coverage
```

## 🔄 CI/CD Integration

### GitHub Actions Workflows

1. **Continuous Integration** (`.github/workflows/ci.yml`)
   - Run on every push and PR
   - Linting and code quality checks
   - Unit and integration tests
   - Build verification

2. **Continuous Deployment** (`.github/workflows/cd.yml`)
   - Deploy to staging on merge to develop
   - Deploy to production on merge to main
   - Automated rollback on failure

3. **Security Scanning** (`.github/workflows/security.yml`)
   - Dependency vulnerability scanning
   - Code security analysis
   - Container image scanning

### Deployment

```bash
# Manual deployment
./scripts/deploy/deploy.sh --env production

# Rollback
./scripts/deploy/rollback.sh --env production --version v1.2.3
```

## 📚 Additional Resources

### Documentation

- [Architecture Decisions](docs/architecture/README.md)
- [API Documentation](docs/api/README.md)
- [Development Guide](docs/guides/development.md)
- [Deployment Guide](docs/guides/deployment.md)
- [JSON Merge Strategy](docs/guides/json-merge-strategy.md) - Estratégia universal de merge JSON
- [JSON Merge Examples](docs/guides/json-merge-examples.md) - Exemplos práticos por tipo de arquivo

### Git & GitHub Workflows

**✨ NOVO**: Templates de GitHub (P1 + P2) são copiados automaticamente ao criar novo projeto via scaffold!

- [GitHub Best Practices](docs/guides/GitHub_Melhores_praticas_de_atualizacao_repositprios.md) - Documento base de boas práticas
- [Branch Protection Setup](docs/guides/BRANCH_PROTECTION_SETUP.md) - Guia de configuração de proteção de branches
- [GitHub Best Practices Integration](docs/guides/GITHUB_BEST_PRACTICES_INTEGRATION.md) - Como as práticas foram integradas no template

**Templates P1** (copiados automaticamente):
- [CONTRIBUTING.md](.github/templates/common/CONTRIBUTING.md) - Guia de contribuição
- [PULL_REQUEST_TEMPLATE.md](.github/templates/common/PULL_REQUEST_TEMPLATE.md) - Template de PR
- [CODEOWNERS](.github/templates/common/CODEOWNERS) - Definição de responsáveis

**Templates P2** (copiados automaticamente):
- Issue Templates: [bug_report](.github/templates/common/ISSUE_TEMPLATE/bug_report.yml), [feature_request](.github/templates/common/ISSUE_TEMPLATE/feature_request.yml), [documentation](.github/templates/common/ISSUE_TEMPLATE/documentation.yml), [question](.github/templates/common/ISSUE_TEMPLATE/question.yml)
- [GitHub Actions Workflow](.github/templates/common/workflows/git-validation.yml) - Validação automática de branches/commits/PRs
- [Pre-commit Hook](scripts/git-hooks/commit-msg) - Validação local de commits
- [Branch Protection Script](scripts/setup-branch-protection.py) - Automação via GitHub API
- [Badges Guide](.github/templates/common/BADGES.md) - Guia completo de badges

**Implementação**:
- `scripts/lib/project.py`: Função `copy_github_templates()` (P1 + P2 integrados)
- Processamento automático de variáveis `{{ project_name }}`, `{{ current_date }}`, `{{ github_repo }}`
- Template README atualizado com badges de conformidade
- Permissões executáveis aplicadas automaticamente (git hooks, scripts)

### Tools & Extensions

- **Speckit**: Specification management and documentation
- **Prettier**: Code formatting
- **ESLint/Pylint**: Code linting
- **Husky**: Git hooks for pre-commit checks
- **Commitlint**: Commit message validation
- **git_validators**: Validação automática de branches e commits (Python)
- **setup-branch-protection.py**: Automação de proteção de branches via API

## 📅 Version History

### v1.3.0 (2026-03-01)
- ✅ `scripts/scaffold.py` implementado — PEP 723, `uv run`, 9 módulos em `scripts/lib/`
- ✅ `make init` → redirect-only para `scaffold.py` (D-21: zero duplicidade)
- ✅ Domain Profiles: `devops-programming`, `devops-infrastructure`, `devops-analysis`
- ✅ Rituais de sessão: `session-start`, `session-start-first`, `session-end`
- ✅ Geração automática `.vscode/mcp.json`, `settings.json`, `extensions.json` por domínio+linguagem
- ✅ `.copilot-rules.md` atualizado (v2026-03-01)

### v1.2.0 (2026-02-28)
- ✅ IMP-13: 5 arquivos `.copilot-*` (1910 linhas) → 1 arquivo `.copilot-rules.md` (193 linhas, 7 seções)
- ✅ `docs/PROJECT-KNOWLEDGE-MAP.md` criado (mapa de funcionalidades v1.1)
- ✅ `scripts/scaffold.py` especificado (SPEC, USER-STORIES, DEBATE)

### v1.1.0 (2026-02-27)
- ✅ MCP configurado (`memory`, `sequential-thinking`, `filesystem`, `github`)
- ✅ Arquitetura Domain Profiles definida (estratégia 3 camadas, 19 decisões D-01–D-19)
- ✅ `docs/copilot/` — Strategy + Decisions documentados
- ✅ `scripts/manage.py` adicionado (TUI Python inicial)

### v1.0.0 (2026-01-27)
- ✅ Estrutura inicial do projeto template
- ✅ Makefile (40+ comandos)
- ✅ Documentação completa (README, INDEX, MAKEFILE.md)
- ✅ `.secrets/` implementado e protegido
- ✅ Suporte multi-linguagem (Python, TypeScript, Go)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📧 Email: support@your-org.com
- 💬 Slack: #project-support
- 📖 Wiki: [Project Wiki](https://wiki.your-org.com)
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/your-project/issues)

## 🎯 Roadmap

- [ ] Additional language templates (Rust, Kotlin)
- [ ] Kubernetes deployment configurations
- [ ] GraphQL API template
- [ ] Microservices architecture template
- [ ] Advanced monitoring and observability setup
- [ ] AI/ML pipeline integration
- [ ] Mobile app templates (React Native, Flutter)

---

**Made with ❤️ by the Vya-Jobs Team**
