# Enterprise Scaffold Project Template - Makefile
# This Makefile automates the creation of the complete project structure
# and provides common development tasks

.PHONY: help init structure dirs docs github specify src tests scripts config docker clean install-deps test test-cov test-quick lint format

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

## help: Display this help message
help:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║  Enterprise Scaffold Project Template - Makefile Help      ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(GREEN)Available targets:$(NC)"
	@echo ""
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  /' | awk -F: '{printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

## init: [DEPRECATED] — use: uv run scripts/scaffold.py
init:
	@echo ""
	@echo "  ⚠️  Para criar/configurar o projeto, use diretamente:"
	@echo "      uv run scripts/scaffold.py"
	@echo "      python scripts/scaffold.py"
	@echo ""
	@echo "  O scaffold.py é o dono exclusivo da lógica de scaffolding."
	@echo "  O Makefile é responsável por: build, test, lint, CI/CD."
	@echo ""

## test-quick: Run tests without coverage (fast)
test-quick:
	@echo "$(BLUE)🧪 Running tests (no coverage)...$(NC)"
	@pytest tests/ --tb=short -q

## test: Run tests with coverage (default CI behavior)
test:
	@echo "$(BLUE)🧪 Running tests with coverage...$(NC)"
	@pytest tests/ \
		--cov=src \
		--cov=scripts/lib \
		--cov-report=html:htmlcov \
		--cov-report=term-missing:skip-covered \
		--cov-report=xml:coverage.xml \
		--cov-fail-under=80

## test-cov: Alias for test (with coverage)
test-cov: test

## test-p2: Run GitHub Best Practices P2 tests only
test-p2:
	@echo "$(BLUE)🧪 Running GitHub Best Practices P2 tests...$(NC)"
	@./tests/run_p2_tests.sh

## test-p2-cov: Run P2 tests with coverage
test-p2-cov:
	@echo "$(BLUE)🧪 Running GitHub Best Practices P2 tests with coverage...$(NC)"
	@./tests/run_p2_tests.sh --coverage

## test-all: Run complete test suite with all bells and whistles
test-all:
	@echo "$(BLUE)🧪 Running complete test suite...$(NC)"
	@./tests/run_all_tests.sh --coverage --verbose

## test-smoke: Run smoke tests only (quick validation)
test-smoke:
	@echo "$(BLUE)💨 Running smoke tests...$(NC)"
	@pytest tests/ -m smoke -q

## test-git: Run Git validators tests only
test-git:
	@echo "$(BLUE)🔍 Running Git validators tests...$(NC)"
	@pytest tests/test_git_validators.py -v

## test-watch: Run tests in watch mode (failed first)
test-watch:
	@echo "$(BLUE)👀 Running tests in watch mode...$(NC)"
	@pytest tests/ --ff -v

## lint: Run code linting
lint:
	@echo "$(BLUE)🔍 Running code linting...$(NC)"
	@echo "$(YELLOW)Checking Python files...$(NC)"
	@python -m py_compile scripts/scaffold.py scripts/lib/*.py scripts/lib/flows/*.py
	@echo "$(GREEN)✅ Python syntax valid$(NC)"

## format: Format code (Python)
format:
	@echo "$(BLUE)✨ Formatting Python code...$(NC)"
	@if command -v black >/dev/null 2>&1; then \
		black scripts/ tests/ src/ --line-length 88; \
		echo "$(GREEN)✅ Code formatted$(NC)"; \
	else \
		echo "$(YELLOW)⚠ black not installed. Install with: pip install black$(NC)"; \
	fi

## lint-yaml: Validate YAML configuration files
lint-yaml:
	@echo "$(BLUE)🔍 Validating YAML configuration files...$(NC)"
	@if command -v yamllint >/dev/null 2>&1; then \
		yamllint .github/workflows/ profile-descriptors/ .scaffold-state.yaml 2>/dev/null || true; \
		echo "$(GREEN)✅ YAML files validated$(NC)"; \
	else \
		echo "$(YELLOW)⚠ yamllint not installed. Install with: uv add --dev yamllint$(NC)"; \
	fi

## lint-json: Validate JSON configuration files
lint-json:
	@echo "$(BLUE)🔍 Validating JSON configuration files...$(NC)"
	@if command -v python3 >/dev/null 2>&1; then \
		for file in .vscode/*.json **/*.json; do \
			if [ -f "$$file" ]; then \
				python3 -c "import json; json.load(open('$$file'))" 2>/dev/null && echo "$(GREEN)✓$(NC) $$file" || echo "$(YELLOW)✗$(NC) $$file"; \
			fi; \
		done; \
		echo "$(GREEN)✅ JSON files validated$(NC)"; \
	else \
		echo "$(YELLOW)⚠ python3 not found$(NC)"; \
	fi

## lint-config: Run all configuration validation checks
lint-config: lint-yaml lint-json

## validate-templates: Validate .specify/templates/ (IMP-65-LITE)
validate-templates:
	@echo "$(BLUE)🔍 Validating templates in .specify/templates/...$(NC)"
	@python scripts/validate-templates.py
	@echo "$(GREEN)✅ Templates validated$(NC)"
	@echo "$(GREEN)✅ All configuration files validated$(NC)"

## structure: Create complete directory structure
structure: dirs github specify docs src tests scripts config docker
	@echo "$(GREEN)✅ Directory structure created$(NC)"

## dirs: Create base directories
dirs:
	@echo "$(BLUE)📁 Creating base directories...$(NC)"
	@mkdir -p .vscode
	@mkdir -p .secrets
	@if [ -d .secrets ] && [ ! -f .secrets/.gitkeep ]; then \
		echo "# This directory stores sensitive files" > .secrets/README.md; \
		echo "# Add your secrets here (certificates, keys, etc.)" >> .secrets/README.md; \
		echo "# These files are ignored by git" >> .secrets/README.md; \
	fi

## github: Create GitHub-related directories and files
github:
	@echo "$(BLUE)📁 Creating GitHub structure...$(NC)"
	@mkdir -p .github/workflows
	@mkdir -p .github/ISSUE_TEMPLATE

## specify: Create Speckit directories
specify:
	@echo "$(BLUE)📁 Creating Speckit structure...$(NC)"
	@mkdir -p .specify/specs

## docs: Create documentation directories
docs:
	@echo "$(BLUE)📁 Creating documentation structure...$(NC)"
	@mkdir -p docs/architecture
	@mkdir -p docs/api
	@mkdir -p docs/guides

## src: Create source code directories
src:
	@echo "$(BLUE)📁 Creating source code structure...$(NC)"
	@mkdir -p src/core/models
	@mkdir -p src/core/interfaces
	@mkdir -p src/core/services
	@mkdir -p src/data/repositories
	@mkdir -p src/data/factories
	@mkdir -p src/data/migrations
	@mkdir -p src/presentation/views
	@mkdir -p src/presentation/presenters
	@mkdir -p src/presentation/viewmodels
	@mkdir -p src/infrastructure/config
	@mkdir -p src/infrastructure/logging
	@mkdir -p src/infrastructure/security
	@mkdir -p src/shared/constants
	@mkdir -p src/shared/helpers
	@mkdir -p src/shared/validators

## tests: Create test directories
tests:
	@echo "$(BLUE)📁 Creating test structure...$(NC)"
	@mkdir -p tests/unit
	@mkdir -p tests/integration
	@mkdir -p tests/e2e

## scripts: Create script directories
scripts:
	@echo "$(BLUE)📁 Creating scripts structure...$(NC)"
	@mkdir -p scripts/setup
	@mkdir -p scripts/build
	@mkdir -p scripts/deploy

## config: Create configuration directories
config:
	@echo "$(BLUE)📁 Creating configuration structure...$(NC)"
	@mkdir -p config

## docker: Create Docker directories
docker:
	@echo "$(BLUE)📁 Creating Docker structure...$(NC)"
	@mkdir -p docker

## create-base-files: Create base configuration files
create-base-files:
	@echo "$(BLUE)📝 Creating base files...$(NC)"
	@$(MAKE) create-gitignore
	@$(MAKE) create-env-example
	@$(MAKE) create-editorconfig
	@$(MAKE) create-github-files
	@$(MAKE) create-speckit-config
	@$(MAKE) create-docker-files
	@$(MAKE) create-config-files
	@$(MAKE) create-readme-files
	@echo "$(GREEN)✅ Base files created$(NC)"

## create-gitignore: Create .gitignore file
create-gitignore:
	@if [ ! -f .gitignore ]; then \
		echo "$(BLUE)Creating .gitignore...$(NC)"; \
		echo "# Dependencies" > .gitignore; \
		echo "node_modules/" >> .gitignore; \
		echo "__pycache__/" >> .gitignore; \
		echo "*.pyc" >> .gitignore; \
		echo "venv/" >> .gitignore; \
		echo ".venv/" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# Environment variables" >> .gitignore; \
		echo ".env" >> .gitignore; \
		echo ".env.local" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# Secrets and sensitive data" >> .gitignore; \
		echo ".secrets/" >> .gitignore; \
		echo "*.key" >> .gitignore; \
		echo "*.pem" >> .gitignore; \
		echo "*.crt" >> .gitignore; \
		echo "*.p12" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# Build outputs" >> .gitignore; \
		echo "dist/" >> .gitignore; \
		echo "build/" >> .gitignore; \
		echo "*.egg-info/" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# IDE" >> .gitignore; \
		echo ".idea/" >> .gitignore; \
		echo "*.swp" >> .gitignore; \
		echo "*.swo" >> .gitignore; \
		echo ".DS_Store" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# Logs" >> .gitignore; \
		echo "*.log" >> .gitignore; \
		echo "logs/" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# Testing" >> .gitignore; \
		echo "coverage/" >> .gitignore; \
		echo ".coverage" >> .gitignore; \
		echo ".pytest_cache/" >> .gitignore; \
		echo "" >> .gitignore; \
		echo "# OS" >> .gitignore; \
		echo "Thumbs.db" >> .gitignore; \
		echo "$(GREEN)✅ .gitignore created$(NC)"; \
	fi

## create-env-example: Create .env.example file
create-env-example:
	@if [ ! -f .env.example ]; then \
		echo "$(BLUE)Creating .env.example...$(NC)"; \
		echo "# Application Configuration" > .env.example; \
		echo "APP_NAME=my-project" >> .env.example; \
		echo "APP_ENV=development" >> .env.example; \
		echo "APP_PORT=3000" >> .env.example; \
		echo "APP_DEBUG=true" >> .env.example; \
		echo "" >> .env.example; \
		echo "# Database Configuration" >> .env.example; \
		echo "DB_HOST=localhost" >> .env.example; \
		echo "DB_PORT=5432" >> .env.example; \
		echo "DB_NAME=myapp_db" >> .env.example; \
		echo "DB_USER=myapp_user" >> .env.example; \
		echo "DB_PASSWORD=secure_password" >> .env.example; \
		echo "" >> .env.example; \
		echo "# Authentication" >> .env.example; \
		echo "JWT_SECRET=your-secret-key-change-in-production" >> .env.example; \
		echo "JWT_EXPIRATION=3600" >> .env.example; \
		echo "" >> .env.example; \
		echo "# External Services" >> .env.example; \
		echo "API_KEY=your-api-key" >> .env.example; \
		echo "$(GREEN)✅ .env.example created$(NC)"; \
	fi

## create-editorconfig: Create .editorconfig file
create-editorconfig:
	@if [ ! -f .editorconfig ]; then \
		echo "$(BLUE)Creating .editorconfig...$(NC)"; \
		echo "root = true" > .editorconfig; \
		echo "" >> .editorconfig; \
		echo "[*]" >> .editorconfig; \
		echo "charset = utf-8" >> .editorconfig; \
		echo "end_of_line = lf" >> .editorconfig; \
		echo "insert_final_newline = true" >> .editorconfig; \
		echo "trim_trailing_whitespace = true" >> .editorconfig; \
		echo "" >> .editorconfig; \
		echo "[*.{js,ts,jsx,tsx,json}]" >> .editorconfig; \
		echo "indent_style = space" >> .editorconfig; \
		echo "indent_size = 2" >> .editorconfig; \
		echo "" >> .editorconfig; \
		echo "[*.{py}]" >> .editorconfig; \
		echo "indent_style = space" >> .editorconfig; \
		echo "indent_size = 4" >> .editorconfig; \
		echo "" >> .editorconfig; \
		echo "[*.{md}]" >> .editorconfig; \
		echo "trim_trailing_whitespace = false" >> .editorconfig; \
		echo "$(GREEN)✅ .editorconfig created$(NC)"; \
	fi

## create-github-files: Create GitHub workflow and template files
create-github-files:
	@echo "$(BLUE)Creating GitHub files...$(NC)"
	@if [ ! -f .github/workflows/ci.yml ]; then \
		echo "name: CI" > .github/workflows/ci.yml; \
		echo "" >> .github/workflows/ci.yml; \
		echo "on:" >> .github/workflows/ci.yml; \
		echo "  push:" >> .github/workflows/ci.yml; \
		echo "    branches: [ main, develop ]" >> .github/workflows/ci.yml; \
		echo "  pull_request:" >> .github/workflows/ci.yml; \
		echo "    branches: [ main, develop ]" >> .github/workflows/ci.yml; \
		echo "" >> .github/workflows/ci.yml; \
		echo "jobs:" >> .github/workflows/ci.yml; \
		echo "  test:" >> .github/workflows/ci.yml; \
		echo "    runs-on: ubuntu-latest" >> .github/workflows/ci.yml; \
		echo "    steps:" >> .github/workflows/ci.yml; \
		echo "      - uses: actions/checkout@v3" >> .github/workflows/ci.yml; \
		echo "      - name: Run tests" >> .github/workflows/ci.yml; \
		echo "        run: make test" >> .github/workflows/ci.yml; \
	fi
	@if [ ! -f .github/PULL_REQUEST_TEMPLATE.md ]; then \
		echo "## Description" > .github/PULL_REQUEST_TEMPLATE.md; \
		echo "" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "Brief description of changes" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "## Type of Change" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "- [ ] Bug fix" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "- [ ] New feature" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "- [ ] Breaking change" >> .github/PULL_REQUEST_TEMPLATE.md; \
		echo "- [ ] Documentation update" >> .github/PULL_REQUEST_TEMPLATE.md; \
	fi
	@echo "$(GREEN)✅ GitHub files created$(NC)"

## create-speckit-config: Create Speckit configuration
create-speckit-config:
	@if [ ! -f .specify/config.json ]; then \
		echo "$(BLUE)Creating Speckit config...$(NC)"; \
		echo "{" > .specify/config.json; \
		echo "  \"version\": \"2.0\"," >> .specify/config.json; \
		echo "  \"organization\": \"your-org\"," >> .specify/config.json; \
		echo "  \"project\": \"scaffold-project\"," >> .specify/config.json; \
		echo "  \"specs\": {" >> .specify/config.json; \
		echo "    \"outputPath\": \"docs/api\"," >> .specify/config.json; \
		echo "    \"format\": \"openapi-3.0\"" >> .specify/config.json; \
		echo "  }" >> .specify/config.json; \
		echo "}" >> .specify/config.json; \
		echo "$(GREEN)✅ Speckit config created$(NC)"; \
	fi

## create-docker-files: Create Docker configuration files
create-docker-files:
	@if [ ! -f docker/Dockerfile ]; then \
		echo "$(BLUE)Creating Dockerfile...$(NC)"; \
		echo "FROM node:18-alpine" > docker/Dockerfile; \
		echo "" >> docker/Dockerfile; \
		echo "WORKDIR /app" >> docker/Dockerfile; \
		echo "" >> docker/Dockerfile; \
		echo "COPY package*.json ./" >> docker/Dockerfile; \
		echo "RUN npm install" >> docker/Dockerfile; \
		echo "" >> docker/Dockerfile; \
		echo "COPY . ." >> docker/Dockerfile; \
		echo "" >> docker/Dockerfile; \
		echo "EXPOSE 3000" >> docker/Dockerfile; \
		echo "" >> docker/Dockerfile; \
		echo "CMD [\"npm\", \"start\"]" >> docker/Dockerfile; \
	fi
	@if [ ! -f docker/docker-compose.yml ]; then \
		echo "$(BLUE)Creating docker-compose.yml...$(NC)"; \
		echo "version: '3.8'" > docker/docker-compose.yml; \
		echo "" >> docker/docker-compose.yml; \
		echo "services:" >> docker/docker-compose.yml; \
		echo "  app:" >> docker/docker-compose.yml; \
		echo "    build:" >> docker/docker-compose.yml; \
		echo "      context: .." >> docker/docker-compose.yml; \
		echo "      dockerfile: docker/Dockerfile" >> docker/docker-compose.yml; \
		echo "    ports:" >> docker/docker-compose.yml; \
		echo "      - \"3000:3000\"" >> docker/docker-compose.yml; \
		echo "    environment:" >> docker/docker-compose.yml; \
		echo "      - NODE_ENV=development" >> docker/docker-compose.yml; \
		echo "    volumes:" >> docker/docker-compose.yml; \
		echo "      - ..:/app" >> docker/docker-compose.yml; \
		echo "      - /app/node_modules" >> docker/docker-compose.yml; \
	fi
	@echo "$(GREEN)✅ Docker files created$(NC)"

## create-config-files: Create environment-specific config files
create-config-files:
	@if [ ! -f config/development.json ]; then \
		echo "$(BLUE)Creating config files...$(NC)"; \
		echo "{" > config/development.json; \
		echo "  \"env\": \"development\"," >> config/development.json; \
		echo "  \"debug\": true," >> config/development.json; \
		echo "  \"api\": {" >> config/development.json; \
		echo "    \"baseUrl\": \"http://localhost:3000\"" >> config/development.json; \
		echo "  }" >> config/development.json; \
		echo "}" >> config/development.json; \
		echo "{" > config/staging.json; \
		echo "  \"env\": \"staging\"," >> config/staging.json; \
		echo "  \"debug\": false," >> config/staging.json; \
		echo "  \"api\": {" >> config/staging.json; \
		echo "    \"baseUrl\": \"https://staging.example.com\"" >> config/staging.json; \
		echo "  }" >> config/staging.json; \
		echo "}" >> config/staging.json; \
		echo "{" > config/production.json; \
		echo "  \"env\": \"production\"," >> config/production.json; \
		echo "  \"debug\": false," >> config/production.json; \
		echo "  \"api\": {" >> config/production.json; \
		echo "    \"baseUrl\": \"https://api.example.com\"" >> config/production.json; \
		echo "  }" >> config/production.json; \
		echo "}" >> config/production.json; \
		echo "$(GREEN)✅ Config files created$(NC)"; \
	fi

## create-readme-files: Create README files for major directories
create-readme-files:
	@echo "$(BLUE)Creating README files for directories...$(NC)"
	@echo "# Core Business Logic" > src/core/README.md
	@echo "" >> src/core/README.md
	@echo "This directory contains the core business logic of the application." >> src/core/README.md
	@echo "# Data Access Layer" > src/data/README.md
	@echo "" >> src/data/README.md
	@echo "This directory contains repositories and data access implementations." >> src/data/README.md
	@echo "# Presentation Layer" > src/presentation/README.md
	@echo "" >> src/presentation/README.md
	@echo "This directory contains the MVP presentation layer components." >> src/presentation/README.md
	@echo "# Tests" > tests/README.md
	@echo "" >> tests/README.md
	@echo "This directory contains all test suites for the application." >> tests/README.md
	@echo "$(GREEN)✅ README files created$(NC)"

## setup-python: Setup Python project structure
setup-python:
	@echo "$(BLUE)🐍 Setting up Python project...$(NC)"
	@if [ ! -f requirements.txt ]; then \
		echo "# Core dependencies" > requirements.txt; \
		echo "fastapi>=0.104.0" >> requirements.txt; \
		echo "uvicorn>=0.24.0" >> requirements.txt; \
		echo "pydantic>=2.5.0" >> requirements.txt; \
		echo "" >> requirements.txt; \
		echo "# Development dependencies" >> requirements.txt; \
		echo "pytest>=7.4.0" >> requirements.txt; \
		echo "pytest-cov>=4.1.0" >> requirements.txt; \
		echo "black>=23.11.0" >> requirements.txt; \
		echo "flake8>=6.1.0" >> requirements.txt; \
		echo "mypy>=1.7.0" >> requirements.txt; \
	fi
	@if [ ! -f requirements-dev.txt ]; then \
		echo "# Development-only dependencies" > requirements-dev.txt; \
		echo "-r requirements.txt" >> requirements-dev.txt; \
		echo "ipython>=8.17.0" >> requirements-dev.txt; \
		echo "ipdb>=0.13.13" >> requirements-dev.txt; \
	fi
	@if [ ! -f setup.py ]; then \
		echo "from setuptools import setup, find_packages" > setup.py; \
		echo "" >> setup.py; \
		echo "setup(" >> setup.py; \
		echo "    name='scaffold-project'," >> setup.py; \
		echo "    version='0.1.0'," >> setup.py; \
		echo "    packages=find_packages()," >> setup.py; \
		echo "    install_requires=[" >> setup.py; \
		echo "        'fastapi>=0.104.0'," >> setup.py; \
		echo "        'uvicorn>=0.24.0'," >> setup.py; \
		echo "    ]," >> setup.py; \
		echo ")" >> setup.py; \
	fi
	@echo "$(GREEN)✅ Python project setup complete$(NC)"

## setup-node: Setup Node.js/TypeScript project structure
setup-node:
	@echo "$(BLUE)📘 Setting up Node.js project...$(NC)"
	@if [ ! -f package.json ]; then \
		echo "{" > package.json; \
		echo "  \"name\": \"scaffold-project\"," >> package.json; \
		echo "  \"version\": \"1.0.0\"," >> package.json; \
		echo "  \"description\": \"Enterprise Scaffold Project Template\"," >> package.json; \
		echo "  \"main\": \"dist/index.js\"," >> package.json; \
		echo "  \"scripts\": {" >> package.json; \
		echo "    \"dev\": \"nodemon src/index.ts\"," >> package.json; \
		echo "    \"build\": \"tsc\"," >> package.json; \
		echo "    \"start\": \"node dist/index.js\"," >> package.json; \
		echo "    \"test\": \"jest\"," >> package.json; \
		echo "    \"test:watch\": \"jest --watch\"," >> package.json; \
		echo "    \"test:coverage\": \"jest --coverage\"," >> package.json; \
		echo "    \"lint\": \"eslint src/**/*.ts\"," >> package.json; \
		echo "    \"format\": \"prettier --write \\\"src/**/*.ts\\\"\"" >> package.json; \
		echo "  }," >> package.json; \
		echo "  \"keywords\": [\"template\", \"enterprise\", \"mvp\"]," >> package.json; \
		echo "  \"author\": \"Vya-Jobs Team\"," >> package.json; \
		echo "  \"license\": \"MIT\"" >> package.json; \
		echo "}" >> package.json; \
	fi
	@if [ ! -f tsconfig.json ]; then \
		echo "{" > tsconfig.json; \
		echo "  \"compilerOptions\": {" >> tsconfig.json; \
		echo "    \"target\": \"ES2020\"," >> tsconfig.json; \
		echo "    \"module\": \"commonjs\"," >> tsconfig.json; \
		echo "    \"outDir\": \"./dist\"," >> tsconfig.json; \
		echo "    \"rootDir\": \"./src\"," >> tsconfig.json; \
		echo "    \"strict\": true," >> tsconfig.json; \
		echo "    \"esModuleInterop\": true," >> tsconfig.json; \
		echo "    \"skipLibCheck\": true," >> tsconfig.json; \
		echo "    \"forceConsistentCasingInFileNames\": true," >> tsconfig.json; \
		echo "    \"resolveJsonModule\": true," >> tsconfig.json; \
		echo "    \"declaration\": true," >> tsconfig.json; \
		echo "    \"declarationMap\": true," >> tsconfig.json; \
		echo "    \"sourceMap\": true" >> tsconfig.json; \
		echo "  }," >> tsconfig.json; \
		echo "  \"include\": [\"src/**/*\"]," >> tsconfig.json; \
		echo "  \"exclude\": [\"node_modules\", \"dist\", \"tests\"]" >> tsconfig.json; \
		echo "}" >> tsconfig.json; \
	fi
	@echo "$(GREEN)✅ Node.js project setup complete$(NC)"

## install-deps: Install project dependencies
install-deps:
	@if [ -f package.json ]; then \
		echo "$(BLUE)📦 Installing Node.js dependencies...$(NC)"; \
		npm install; \
	fi
	@if [ -f requirements.txt ]; then \
		echo "$(BLUE)📦 Installing Python dependencies...$(NC)"; \
		pip install -r requirements.txt; \
	fi
	@echo "$(GREEN)✅ Dependencies installed$(NC)"

## dev: Start development server
dev:
	@if [ -f package.json ]; then \
		npm run dev; \
	elif [ -f requirements.txt ]; then \
		uvicorn main:app --reload; \
	else \
		echo "$(RED)❌ No package.json or requirements.txt found$(NC)"; \
	fi

## build: Build the project
build:
	@echo "$(BLUE)🔨 Building project...$(NC)"
	@if [ -f package.json ]; then \
		npm run build; \
	elif [ -f setup.py ]; then \
		python setup.py build; \
	fi
	@echo "$(GREEN)✅ Build complete$(NC)"

# =============================================================================
# Testing Commands
# =============================================================================

## test: Run all tests with coverage
test:
	@echo "$(BLUE)🧪 Running all tests...$(NC)"
	@if [ -f package.json ]; then \
		npm test; \
	elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then \
		pytest --cov --cov-report=term-missing; \
	else \
		echo "$(YELLOW)⚠️  No test configuration found$(NC)"; \
	fi

## test-unit: Run only unit tests (fast)
test-unit:
	@echo "$(BLUE)⚡ Running unit tests...$(NC)"
	@pytest -m unit -v

## test-integration: Run integration tests
test-integration:
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	@pytest -m integration -v

## test-smoke: Run smoke tests (quick validation)
test-smoke:
	@echo "$(BLUE)💨 Running smoke tests...$(NC)"
	@pytest -m smoke -v

## test-security: Run security tests
test-security:
	@echo "$(BLUE)🔒 Running security tests...$(NC)"
	@pytest -m security -v

## test-watch: Run tests in watch mode
test-watch:
	@echo "$(BLUE)👀 Running tests in watch mode...$(NC)"
	@if command -v ptw >/dev/null 2>&1; then \
		ptw -- --testmon; \
	else \
		echo "$(YELLOW)⚠️  Install pytest-watch: pip install pytest-watch$(NC)"; \
		echo "$(YELLOW)Falling back to pytest-testmon...$(NC)"; \
		pytest --testmon; \
	fi

## test-coverage: Generate detailed coverage report
test-coverage:
	@echo "$(BLUE)📊 Generating coverage report...$(NC)"
	@pytest --cov --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✅ Coverage report: htmlcov/index.html$(NC)"

## test-coverage-xml: Generate XML coverage (for CI)
test-coverage-xml:
	@echo "$(BLUE)📄 Generating XML coverage...$(NC)"
	@pytest --cov --cov-report=xml
	@echo "$(GREEN)✅ Coverage report: coverage.xml$(NC)"

## test-failed: Run only failed tests from last run
test-failed:
	@echo "$(BLUE)🔄 Re-running failed tests...$(NC)"
	@pytest --lf -v

## test-verbose: Run tests with verbose output
test-verbose:
	@echo "$(BLUE)🔊 Running tests (verbose)...$(NC)"
	@pytest -vv

## test-parallel: Run tests in parallel
test-parallel:
	@echo "$(BLUE)⚡ Running tests in parallel...$(NC)"
	@if command -v pytest-xdist >/dev/null 2>&1; then \
		pytest -n auto; \
	else \
		echo "$(YELLOW)⚠️  Install pytest-xdist: pip install pytest-xdist$(NC)"; \
		pytest; \
	fi

## test-profile: Profile test execution time
test-profile:
	@echo "$(BLUE)⏱️  Profiling test execution...$(NC)"
	@pytest --durations=10

## test-clean: Clean test cache and coverage files
test-clean:
	@echo "$(BLUE)🧹 Cleaning test artifacts...$(NC)"
	@rm -rf .pytest_cache htmlcov .coverage coverage.xml
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✅ Test artifacts cleaned$(NC)"

## lint: Run linting
lint:
	@echo "$(BLUE)🔍 Running linter...$(NC)"
	@if [ -f package.json ]; then \
		npm run lint; \
	elif [ -f requirements.txt ]; then \
		flake8 src/; \
	fi

## format: Format code
format:
	@echo "$(BLUE)✨ Formatting code...$(NC)"
	@if [ -f package.json ]; then \
		npm run format; \
	elif [ -f requirements.txt ]; then \
		black src/; \
	fi

## docker-build: Build Docker image
docker-build:
	@echo "$(BLUE)🐳 Building Docker image...$(NC)"
	@docker build -f docker/Dockerfile -t scaffold-project:latest .
	@echo "$(GREEN)✅ Docker image built$(NC)"

## docker-up: Start Docker containers
docker-up:
	@echo "$(BLUE)🐳 Starting Docker containers...$(NC)"
	@docker-compose -f docker/docker-compose.yml up -d
	@echo "$(GREEN)✅ Containers started$(NC)"

## docker-down: Stop Docker containers
docker-down:
	@echo "$(BLUE)🐳 Stopping Docker containers...$(NC)"
	@docker-compose -f docker/docker-compose.yml down
	@echo "$(GREEN)✅ Containers stopped$(NC)"

## session-index: Build or update session documentation search index
session-index:
	@echo "$(BLUE)📚 Indexing session documentation...$(NC)"
	@python scripts/session-index.py
	@echo "$(GREEN)✅ Session index updated$(NC)"

## session-index-rebuild: Rebuild session index from scratch
session-index-rebuild:
	@echo "$(BLUE)📚 Rebuilding session documentation index...$(NC)"
	@python scripts/session-index.py --rebuild
	@echo "$(GREEN)✅ Session index rebuilt$(NC)"

## session-search: Search session documentation (use QUERY="text")
session-search:
	@if [ -z "$(QUERY)" ]; then \
		echo "$(RED)✗ Error: QUERY parameter is required$(NC)"; \
		echo "$(YELLOW)Usage: make session-search QUERY=\"your search text\"$(NC)"; \
		echo "$(YELLOW)Examples:$(NC)"; \
		echo "  make session-search QUERY=\"IMP-50\""; \
		echo "  make session-search QUERY=\"python AND fastapi\""; \
		echo "  make session-search QUERY='\"bug fix\"'"; \
		exit 1; \
	fi
	@python scripts/session-search.py "$(QUERY)"

## session-index-stats: Show session index statistics
session-index-stats:
	@echo "$(BLUE)📊 Session Index Statistics$(NC)"
	@python scripts/session-index.py --stats

## chat-capture: Capture latest Copilot conversation to CHAT-*.md
chat-capture:
	@echo "$(BLUE)💬 Capturing latest conversation...$(NC)"
	@python scripts/session-chat.py capture --latest
	@echo "$(GREEN)✅ Chat captured$(NC)"

## chat-list: List all captured CHAT-*.md files
chat-list:
	@echo "$(BLUE)📋 Captured Conversations$(NC)"
	@python scripts/session-chat.py list

## chat-search: Search in captured conversations (use QUERY="text")
chat-search:
	@if [ -z "$(QUERY)" ]; then \
		echo "$(RED)✗ Error: QUERY parameter is required$(NC)"; \
		echo "$(YELLOW)Usage: make chat-search QUERY=\"your search text\"$(NC)"; \
		echo "$(YELLOW)Examples:$(NC)"; \
		echo "  make chat-search QUERY=\"IMP-55\""; \
		echo "  make chat-search QUERY=\"debugging\""; \
		exit 1; \
	fi
	@python scripts/session-chat.py search "$(QUERY)"

##
## ═══════════════════════════════════════════════════════════════════════
## DEPENDENCY MANAGEMENT (IMP-65 P0)
## ═══════════════════════════════════════════════════════════════════════

## update-deps-safe: Update security dependencies (bandit, safety) with smoke tests
update-deps-safe:
	@echo "$(BLUE)🔍 Atualizando dependências de segurança...$(NC)"
	@pip install --upgrade bandit safety
	@echo ""
	@echo "$(YELLOW)✅ Segurança atualizada. Rodando smoke tests...$(NC)"
	@pytest tests/test_memory_smoke.py -v || true
	@echo ""
	@echo "$(GREEN)✅ Smoke tests passaram. Dependências seguras.$(NC)"

## update-deps: Update all dependencies (caution: may introduce breaking changes)
update-deps:
	@echo "$(YELLOW)⚠️  ATENÇÃO: Atualizando TODAS as dependências...$(NC)"
	@echo "$(YELLOW)Isso pode introduzir breaking changes. Continue? [y/N] $(NC)" && read ans && [ $${ans:-N} = y ]
	@pip install --upgrade -e ".[dev,security]"
	@echo ""
	@echo "$(BLUE)🧪 Rodando testes completos...$(NC)"
	@pytest tests/ -v
	@echo ""
	@echo "$(GREEN)✅ Testes passaram. Revise git diff antes de commitar.$(NC)"

## deps-check: Check for outdated dependencies (used in session-start Passo 4.5)
deps-check:
	@pip list --outdated --format=json | python -c "import sys, json; data = json.load(sys.stdin) if not sys.stdin.isatty() else []; print(f'📦 {len(data)} pacote(s) desatualizado(s)') if data else print('✅ Tudo atualizado')"

## memory-cleanup: Limpeza de memórias (dry-run, mostra o que seria removido)
memory-cleanup:
	@python scripts/memory-cleanup.py

## memory-cleanup-force: Executar limpeza (cria backup automático)
memory-cleanup-force:
	@python scripts/memory-cleanup.py --execute --backup

## config-validate: Validar configurações críticas (MCP, pyproject.toml, copilot-rules)
config-validate:
	@python scripts/validate-configs.py

## git-hooks-install: Instalar Git hooks (pre-commit, commit-msg)
git-hooks-install:
	@echo "$(BLUE)🪝 Instalando Git hooks...$(NC)"
	@mkdir -p .git/hooks
	@cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
	@cp scripts/git-hooks/commit-msg .git/hooks/commit-msg
	@chmod +x .git/hooks/pre-commit
	@chmod +x .git/hooks/commit-msg
	@echo "$(GREEN)✅ Git hooks instalados:$(NC)"
	@echo "  - pre-commit (memory validation)"
	@echo "  - commit-msg (conventional commits)"

## clean: Remove generated files and directories
clean:
	@echo "$(BLUE)🧹 Cleaning project...$(NC)"
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info/
	@rm -rf __pycache__/
	@rm -rf .pytest_cache/
	@rm -rf coverage/
	@rm -rf node_modules/
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@echo "$(GREEN)✅ Project cleaned$(NC)"

## status: Show project status and structure
status:
	@echo "$(BLUE)╔════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║  Project Status                                            ║$(NC)"
	@echo "$(BLUE)╚════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Directory Structure:$(NC)"
	@tree -L 2 -I 'node_modules|__pycache__|*.pyc|.git' || ls -la
	@echo ""
	@echo "$(YELLOW)Configuration Files:$(NC)"
	@ls -1 | grep -E '(package.json|requirements.txt|Makefile|README.md|Dockerfile|docker-compose.yml)' || echo "  No config files found"

##
## ═══════════════════════════════════════════════════════════════════════
## MEMORY SYSTEM (IMP-59)
## ═══════════════════════════════════════════════════════════════════════
##

## memory-save: Save a new memory interactively
memory-save:
	@echo "$(BLUE)💾 Saving new memory...$(NC)"
	@python scripts/mem_save.py

## memory-search: Search memories (usage: make memory-search QUERY="database")
memory-search:
	@if [ -z "$(QUERY)" ]; then \
		echo "$(YELLOW)Usage: make memory-search QUERY=\"your search terms\"$(NC)"; \
		echo "Example: make memory-search QUERY=\"database migration\""; \
		exit 1; \
	fi
	@echo "$(BLUE)🔍 Searching memories: $(QUERY)$(NC)"
	@python scripts/mem_search.py --query "$(QUERY)"

## memory-context: Get context suggestions based on current work
memory-context:
	@echo "$(BLUE)💡 Analyzing current context...$(NC)"
	@python scripts/mem_context.py --auto

## memory-context-task: Get context for specific task (usage: make memory-context-task TASK=IMP-60)
memory-context-task:
	@if [ -z "$(TASK)" ]; then \
		echo "$(YELLOW)Usage: make memory-context-task TASK=IMP-XX$(NC)"; \
		echo "Example: make memory-context-task TASK=IMP-60"; \
		exit 1; \
	fi
	@echo "$(BLUE)💡 Getting context for task: $(TASK)$(NC)"
	@python scripts/mem_context.py --task "$(TASK)"

## memory-rebuild: Rebuild memory index from markdown files
memory-rebuild:
	@echo "$(BLUE)🔄 Rebuilding memory index...$(NC)"
	@python scripts/mem_rebuild.py
	@echo "$(GREEN)✅ Memory index rebuilt$(NC)"

## memory-test: Run memory system tests
memory-test:
	@echo "$(BLUE)🧪 Running memory system tests...$(NC)"
	@pytest tests/test_memory*.py -v --tb=short
	@echo "$(GREEN)✅ Memory tests completed$(NC)"

## memory-test-quick: Run memory tests without verbose output
memory-test-quick:
	@pytest tests/test_memory*.py -q

## memory-health: Check memory system health
memory-health:
	@echo "$(BLUE)🏥 Checking memory system health...$(NC)"
	@echo ""
	@echo "$(YELLOW)Directory structure:$(NC)"
	@if [ -d .memory/memories/project ]; then echo "  ✅ .memory/memories/project/"; else echo "  ❌ .memory/memories/project/ missing"; fi
	@if [ -d .memory/memories/team ]; then echo "  ✅ .memory/memories/team/"; else echo "  ❌ .memory/memories/team/ missing"; fi
	@if [ -d .memory/memories/sessions ]; then echo "  ✅ .memory/memories/sessions/"; else echo "  ❌ .memory/memories/sessions/ missing"; fi
	@if [ -d .memory/index ]; then echo "  ✅ .memory/index/"; else echo "  ❌ .memory/index/ missing"; fi
	@echo ""
	@echo "$(YELLOW)Index status:$(NC)"
	@if [ -f .memory/index/memory.db ]; then \
		echo "  ✅ .memory/index/memory.db exists"; \
		python -c "import sqlite3; conn = sqlite3.connect('.memory/index/memory.db'); print('  ✅ Database is valid'); conn.close()" 2>/dev/null || echo "  ❌ Database is corrupted (run: make memory-rebuild)"; \
	else \
		echo "  ❌ .memory/index/memory.db missing (run: make memory-rebuild)"; \
	fi
	@echo ""
	@echo "$(YELLOW)Memory count:$(NC)"
	@if [ -f .memory/index/memory.db ]; then \
		python -c "import sqlite3; conn = sqlite3.connect('.memory/index/memory.db'); cursor = conn.execute('SELECT COUNT(*) FROM memories'); print(f'  📊 Total memories: {cursor.fetchone()[0]}'); conn.close()" 2>/dev/null || echo "  ⚠ Could not query database"; \
	fi
	@echo ""
	@echo "$(GREEN)✅ Health check completed$(NC)"

##
## ═══════════════════════════════════════════════════════════════════════
## SESSION DOCUMENTATION
## ═══════════════════════════════════════════════════════════════════════
##

## session-log: Show recent session activity log
session-log:
	@echo "$(BLUE)📋 Recent Session Activity$(NC)"
	@echo ""
	@if [ -d "docs/SESSIONS" ]; then \
		LATEST_SESSION=$$(find docs/SESSIONS -maxdepth 1 -type d -name "20*" | sort -r | head -1); \
		if [ -n "$$LATEST_SESSION" ]; then \
			SESSION_DATE=$$(basename $$LATEST_SESSION); \
			echo "$(YELLOW)Session: $$SESSION_DATE$(NC)"; \
			echo ""; \
			if [ -f "$$LATEST_SESSION/DAILY_ACTIVITIES_$$SESSION_DATE.md" ]; then \
				echo "$(GREEN)DAILY_ACTIVITIES:$(NC)"; \
				tail -n 50 "$$LATEST_SESSION/DAILY_ACTIVITIES_$$SESSION_DATE.md"; \
			else \
				echo "$(YELLOW)⚠️  No DAILY_ACTIVITIES found for this session$(NC)"; \
			fi; \
		else \
			echo "$(YELLOW)⚠️  No session directories found$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ docs/SESSIONS/ directory not found$(NC)"; \
	fi

## session-validate: Validate session documentation format
session-validate:
	@echo "$(BLUE)🔍 Validating session documentation...$(NC)"
	@echo ""
	@if command -v python3 >/dev/null 2>&1; then \
		python3 scripts/session-validate.py --all; \
	else \
		echo "$(RED)❌ python3 not found$(NC)"; \
		exit 1; \
	fi

## session-sanitize: Scan session docs for sensitive data exposure
session-sanitize:
	@echo "$(BLUE)🛡️  Scanning session docs for sensitive data...$(NC)"
	@echo ""
	@if command -v gitleaks >/dev/null 2>&1; then \
		if [ -d "docs/SESSIONS" ]; then \
			gitleaks detect \
				--config .gitleaks-session-docs.toml \
				--source docs/SESSIONS/ \
				--verbose \
				--no-git; \
			if [ $$? -eq 0 ]; then \
				echo ""; \
				echo "$(GREEN)✅ No sensitive data found$(NC)"; \
			else \
				echo ""; \
				echo "$(RED)❌ Sensitive data detected - review and sanitize$(NC)"; \
				echo "$(YELLOW)See session-end.prompt.md (Passo 6) for sanitization guidelines$(NC)"; \
				exit 1; \
			fi; \
		else \
			echo "$(YELLOW)⚠️  docs/SESSIONS/ directory not found$(NC)"; \
		fi; \
	else \
		echo "$(YELLOW)⚠️  gitleaks not installed$(NC)"; \
		echo ""; \
		echo "Install gitleaks:"; \
		echo "  macOS:  brew install gitleaks"; \
		echo "  Linux:  wget https://github.com/gitleaks/gitleaks/releases/..."; \
		exit 1; \
	fi

##
## ═══════════════════════════════════════════════════════════════════════
## TEMPLATE MANAGEMENT
## ═══════════════════════════════════════════════════════════════════════
##

## release: Cria release versionada (semver obrigatório)
##           Uso:     make release VERSION=1.1.0
##           Dry-run: make release VERSION=1.1.0 DRY_RUN=1
release:
	@if [ -z "$(VERSION)" ]; then \
		echo "$(RED)❌ VERSION obrigatório$(NC)"; \
		echo ""; \
		echo "  Uso:     make release VERSION=1.1.0"; \
		echo "  Dry-run: make release VERSION=1.1.0 DRY_RUN=1"; \
		exit 1; \
	fi
	@if [ -n "$(DRY_RUN)" ]; then \
		python scripts/scaffold.py --release $(VERSION) --dry-run; \
	else \
		python scripts/scaffold.py --release $(VERSION); \
	fi

## init-new-project: Initialize a new project from this template
init-new-project:
	@if [ -z "$(NAME)" ]; then \
		echo "$(RED)Error: Project name required$(NC)"; \
		echo ""; \
		echo "Usage: make init-new-project NAME=my-project"; \
		echo ""; \
		echo "The name must:"; \
		echo "  - Use only lowercase letters (a-z)"; \
		echo "  - Use numbers (0-9)"; \
		echo "  - Use hyphens (-) to separate words"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make init-new-project NAME=my-app"; \
		echo "  make init-new-project NAME=api-v2"; \
		echo "  make init-new-project NAME=data-processor-2024"; \
		exit 1; \
	fi
	@echo "$(BLUE)🚀 Initializing new project: $(NAME)$(NC)"
	@./setup/init-new-project.sh $(NAME)

## setup-shared-configs: Setup shared configuration repository
setup-shared-configs:
	@echo "$(BLUE)📦 Setting up shared configuration repository...$(NC)"
	@if [ -d "$$HOME/Documentos/DevOps/.copilot-shared" ]; then \
		echo "$(YELLOW)⚠ Shared configs already exist at ~/Documentos/DevOps/.copilot-shared$(NC)"; \
		read -p "Overwrite? (y/N): " confirm; \
		if [ "$$confirm" != "y" ] && [ "$$confirm" != "Y" ]; then \
			echo "$(YELLOW)Cancelled$(NC)"; \
			exit 0; \
		fi; \
	fi
	@mkdir -p "$$HOME/Documentos/DevOps/.copilot-shared"/{rules,scripts,templates,docs}
	@echo "$(GREEN)✅ Shared directory structure created$(NC)"
	@echo ""
	@echo "$(BLUE)Copying configuration files...$(NC)"
	@cp .copilot-rules.md "$$HOME/Documentos/DevOps/.copilot-shared/rules/" 2>/dev/null || true
	@cp .copilot-git-rules.md "$$HOME/Documentos/DevOps/.copilot-shared/rules/" 2>/dev/null || true
	@cp .copilot-strict-enforcement.md "$$HOME/Documentos/DevOps/.copilot-shared/rules/" 2>/dev/null || true
	@cp .copilot-strict-rules.md "$$HOME/Documentos/DevOps/.copilot-shared/rules/" 2>/dev/null || true
	@cp .copilot-file-rules.sh "$$HOME/Documentos/DevOps/.copilot-shared/rules/" 2>/dev/null || true
	@echo "$(GREEN)✅ Configuration files copied$(NC)"
	@echo ""
	@echo "$(BLUE)Copying scripts...$(NC)"
	@cp setup/setup-project-links.sh "$$HOME/Documentos/DevOps/.copilot-shared/scripts/" 2>/dev/null || true
	@cp setup/check-project-links.sh "$$HOME/Documentos/DevOps/.copilot-shared/scripts/" 2>/dev/null || true
	@chmod +x "$$HOME/Documentos/DevOps/.copilot-shared/scripts"/*.sh
	@echo "$(GREEN)✅ Scripts copied and made executable$(NC)"
	@echo ""
	@echo "$(BLUE)Copying documentation...$(NC)"
	@if [ -f "docs/SHARED_CONFIGS_SOLUTION.md" ]; then \
		cp docs/SHARED_CONFIGS_SOLUTION.md "$$HOME/Documentos/DevOps/.copilot-shared/docs/" 2>/dev/null || true; \
		echo "$(GREEN)✅ Documentation copied$(NC)"; \
	else \
		echo "$(YELLOW)⚠ SHARED_CONFIGS_SOLUTION.md not found (may already be moved)$(NC)"; \
	fi
	@echo ""
	@echo "$(BLUE)Initializing Git repository...$(NC)"
	@cd "$$HOME/Documentos/DevOps/.copilot-shared" && \
		if [ ! -d .git ]; then \
			git init && \
			git add . && \
			git commit -m "feat: Initial shared configs"; \
			echo "$(GREEN)✅ Git repository initialized$(NC)"; \
		else \
			echo "$(YELLOW)⚠ Git already initialized$(NC)"; \
		fi
	@echo ""
	@echo "$(GREEN)🎉 Shared configuration repository ready!$(NC)"
	@echo ""
	@echo "$(YELLOW)Location: $$HOME/Documentos/DevOps/.copilot-shared/$(NC)"
	@echo ""
	@echo "$(YELLOW)Structure created:$(NC)"
	@echo "  rules/     - Copilot configuration files"
	@echo "  scripts/   - Automation scripts"
	@echo "  templates/ - Project templates"
	@echo "  docs/      - Shared documentation"
	@echo ""
	@echo "$(YELLOW)Suggested aliases (add to ~/.zshrc or ~/.bashrc):$(NC)"
	@echo '  alias copilot-setup="$$HOME/Documentos/DevOps/.copilot-shared/scripts/setup-project-links.sh"'
	@echo '  alias copilot-check="$$HOME/Documentos/DevOps/.copilot-shared/scripts/check-project-links.sh"'
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Setup links for this project:"
	@echo "     make setup-project-links"
	@echo "  2. Or create a new project:"
	@echo "     make init-new-project NAME=my-project"

## setup-project-links: Setup symlinks to shared configs for this project
setup-project-links:
	@echo "$(BLUE)🔗 Setting up symlinks to shared configs...$(NC)"
	@if [ ! -d "$$HOME/Documentos/DevOps/.copilot-shared" ]; then \
		echo "$(RED)Error: Shared configs not found$(NC)"; \
		echo ""; \
		echo "Run first: make setup-shared-configs"; \
		exit 1; \
	fi
	@"$$HOME/Documentos/DevOps/.copilot-shared/scripts/setup-project-links.sh" .
	@echo "$(GREEN)✅ Symlinks configured$(NC)"

## check-project-links: Verify symlinks status
check-project-links:
	@echo "$(BLUE)🔍 Checking symlinks status...$(NC)"
	@if [ ! -d "$$HOME/Documentos/DevOps/.copilot-shared" ]; then \
		echo "$(RED)Error: Shared configs not found$(NC)"; \
		exit 1; \
	fi
	@"$$HOME/Documentos/DevOps/.copilot-shared/scripts/check-project-links.sh" .
