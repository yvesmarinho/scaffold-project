# 📘 Makefile Documentation

Complete guide for using the Makefile to automate project setup, development, and deployment tasks.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Available Commands](#available-commands)
- [Detailed Command Reference](#detailed-command-reference)
- [Workflow Examples](#workflow-examples)
- [Customization](#customization)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Makefile automates common development tasks and provides a consistent interface for project management across different environments. It handles:

- Complete project structure initialization
- Language-specific setup (Python, Node.js/TypeScript, etc.)
- Development environment configuration
- Build and deployment automation
- Testing and code quality checks
- Docker container management

### Benefits

- **Consistency**: Same commands work across all developer machines
- **Efficiency**: Automate repetitive tasks with simple commands
- **Documentation**: Self-documenting with built-in help
- **Simplicity**: Complex operations reduced to single commands

## 🔧 Prerequisites

Before using the Makefile, ensure you have:

- **Make**: Pre-installed on most Unix-based systems (Linux, macOS)
- **Git**: For version control
- **Docker** (optional): For containerized development
- **Language-specific tools**:
  - Python: `python3`, `pip`
  - Node.js: `node`, `npm`
  - Java: `java`, `maven` or `gradle`

### Installing Make

**Linux:**
```bash
sudo apt-get install build-essential  # Debian/Ubuntu
sudo yum groupinstall "Development Tools"  # CentOS/RHEL
```

**macOS:**
```bash
xcode-select --install
```

**Windows:**
- Use WSL (Windows Subsystem for Linux)
- Or install via Chocolatey: `choco install make`

## 🚀 Quick Start

### 1. Initialize a New Project

```bash
# Create complete project structure
make init
```

This command will:
- Create all necessary directories
- Generate configuration files
- Set up GitHub workflows
- Create Docker configurations
- Generate README files for each directory

### 2. Choose Your Language Stack

**For Python projects:**
```bash
make setup-python
```

**For Node.js/TypeScript projects:**
```bash
make setup-node
```

### 3. Install Dependencies

```bash
make install-deps
```

### 4. Start Development

```bash
make dev
```

## 📚 Available Commands

View all available commands:
```bash
make help
```

### Command Categories

#### 🏗️ Structure & Initialization
- `make init` - Complete project initialization
- `make structure` - Create directory structure only
- `make dirs` - Create base directories
- `make src` - Create source code directories
- `make tests` - Create test directories
- `make docs` - Create documentation directories

#### ⚙️ Project Setup
- `make setup-python` - Configure Python project
- `make setup-node` - Configure Node.js project
- `make install-deps` - Install dependencies

#### 💻 Development
- `make dev` - Start development server
- `make build` - Build the project
- `make test` - Run all tests
- `make lint` - Run code linting
- `make format` - Format code

#### 🐳 Docker Operations
- `make docker-build` - Build Docker image
- `make docker-up` - Start containers
- `make docker-down` - Stop containers

#### 🧹 Maintenance
- `make clean` - Remove generated files
- `make status` - Show project status

## 📖 Detailed Command Reference

### `make init`

**Purpose**: Complete project initialization for new projects

**What it does**:
1. Creates complete directory structure
2. Generates all base configuration files
3. Sets up version control templates
4. Creates Docker configurations
5. Initializes documentation structure

**Usage**:
```bash
make init
```

**Output**:
```
🚀 Initializing Enterprise Project Structure...
📁 Creating base directories...
📁 Creating GitHub structure...
📁 Creating Speckit structure...
...
✅ Project structure created successfully!

Next steps:
  1. Run 'make setup-python' or 'make setup-node' to configure your language
  2. Run 'make install-deps' to install dependencies
  3. Run 'make dev' to start development
```

---

### `make structure`

**Purpose**: Create only the directory structure without configuration files

**What it does**:
- Creates all directories defined in the project structure
- Does not create configuration files
- Useful for rebuilding directory structure

**Usage**:
```bash
make structure
```

**Directories created**:
```
.github/workflows/
.github/ISSUE_TEMPLATE/
.specify/specs/
docs/architecture/
docs/api/
docs/guides/
src/core/models/
src/core/interfaces/
src/core/services/
src/data/repositories/
src/data/factories/
src/data/migrations/
src/presentation/views/
src/presentation/presenters/
src/presentation/viewmodels/
src/infrastructure/config/
src/infrastructure/logging/
src/infrastructure/security/
src/shared/constants/
src/shared/helpers/
src/shared/validators/
tests/unit/
tests/integration/
tests/e2e/
scripts/setup/
scripts/build/
scripts/deploy/
config/
docker/
```

---

### `make setup-python`

**Purpose**: Configure project for Python development

**What it does**:
1. Creates `requirements.txt` with essential dependencies
2. Creates `requirements-dev.txt` for development dependencies
3. Creates `setup.py` for package configuration

**Usage**:
```bash
make setup-python
```

**Generated files**:
- `requirements.txt`: Production dependencies
  ```
  fastapi>=0.104.0
  uvicorn>=0.24.0
  pydantic>=2.5.0
  pytest>=7.4.0
  pytest-cov>=4.1.0
  black>=23.11.0
  flake8>=6.1.0
  mypy>=1.7.0
  ```

- `requirements-dev.txt`: Development dependencies
  ```
  -r requirements.txt
  ipython>=8.17.0
  ipdb>=0.13.13
  ```

- `setup.py`: Package configuration

**After running**:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install-deps
```

---

### `make setup-node`

**Purpose**: Configure project for Node.js/TypeScript development

**What it does**:
1. Creates `package.json` with scripts and metadata
2. Creates `tsconfig.json` for TypeScript configuration

**Usage**:
```bash
make setup-node
```

**Generated files**:
- `package.json`: Project metadata and scripts
  ```json
  {
    "name": "scaffold-project",
    "version": "1.0.0",
    "scripts": {
      "dev": "nodemon src/index.ts",
      "build": "tsc",
      "start": "node dist/index.js",
      "test": "jest",
      "lint": "eslint src/**/*.ts",
      "format": "prettier --write \"src/**/*.ts\""
    }
  }
  ```

- `tsconfig.json`: TypeScript compiler configuration

**After running**:
```bash
# Install dependencies
npm install express typescript @types/node nodemon ts-node

# Or use the make command
make install-deps
```

---

### `make install-deps`

**Purpose**: Install project dependencies based on detected configuration

**What it does**:
- Detects project type (Python or Node.js)
- Installs dependencies using appropriate package manager
- Works for both Python (`pip`) and Node.js (`npm`)

**Usage**:
```bash
make install-deps
```

**Behavior**:
- If `package.json` exists: runs `npm install`
- If `requirements.txt` exists: runs `pip install -r requirements.txt`
- If both exist: installs both

---

### `make dev`

**Purpose**: Start the development server

**What it does**:
- Detects project type
- Starts appropriate development server with hot-reload

**Usage**:
```bash
make dev
```

**Behavior**:
- **Node.js projects**: Runs `npm run dev` (typically nodemon)
- **Python projects**: Runs `uvicorn main:app --reload`

**Example output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

---

### `make build`

**Purpose**: Build the project for production

**What it does**:
- Compiles source code
- Generates production-ready artifacts

**Usage**:
```bash
make build
```

**Behavior**:
- **Node.js/TypeScript**: Runs `npm run build` (TypeScript compilation)
- **Python**: Runs `python setup.py build`

**Output location**:
- Node.js: `dist/` directory
- Python: `build/` directory

---

### `make test`

**Purpose**: Run all test suites

**What it does**:
- Executes unit, integration, and E2E tests
- Generates test reports

**Usage**:
```bash
# Run all tests
make test

# Run specific test suites (manual commands)
npm run test:unit        # Unit tests only
npm run test:integration # Integration tests
npm run test:e2e        # E2E tests
pytest tests/unit/      # Python unit tests
```

**Example output**:
```
PASS tests/unit/services/user.test.ts
PASS tests/integration/api/auth.test.ts
Test Suites: 2 passed, 2 total
Tests:       15 passed, 15 total
```

---

### `make lint`

**Purpose**: Check code quality and style

**What it does**:
- Runs language-specific linters
- Checks for code quality issues
- Reports style violations

**Usage**:
```bash
make lint
```

**Behavior**:
- **Node.js**: Runs `eslint src/**/*.ts`
- **Python**: Runs `flake8 src/`

**Example output**:
```
src/services/user.ts
  10:5  error  'userData' is assigned a value but never used  @typescript-eslint/no-unused-vars

✖ 1 problem (1 error, 0 warnings)
```

---

### `make format`

**Purpose**: Automatically format code

**What it does**:
- Applies consistent code formatting
- Fixes style issues automatically

**Usage**:
```bash
make format
```

**Behavior**:
- **Node.js**: Runs `prettier --write "src/**/*.ts"`
- **Python**: Runs `black src/`

**Example output**:
```
src/services/user.ts 200ms
src/models/user.ts 150ms
✨ 2 files formatted
```

---

### `make docker-build`

**Purpose**: Build Docker image

**What it does**:
- Builds Docker image from Dockerfile
- Tags image as `scaffold-project:latest`

**Usage**:
```bash
make docker-build
```

**Equivalent to**:
```bash
docker build -f docker/Dockerfile -t scaffold-project:latest .
```

---

### `make docker-up`

**Purpose**: Start Docker containers

**What it does**:
- Starts all services defined in docker-compose.yml
- Runs containers in detached mode

**Usage**:
```bash
make docker-up
```

**Equivalent to**:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

---

### `make docker-down`

**Purpose**: Stop Docker containers

**What it does**:
- Stops all running containers
- Removes containers and networks

**Usage**:
```bash
make docker-down
```

**Equivalent to**:
```bash
docker-compose -f docker/docker-compose.yml down
```

---

### `make clean`

**Purpose**: Remove generated files and build artifacts

**What it does**:
- Removes build directories
- Cleans Python cache files
- Removes test coverage reports
- Deletes node_modules (if needed)

**Usage**:
```bash
make clean
```

**Files/directories removed**:
- `dist/`
- `build/`
- `*.egg-info/`
- `__pycache__/`
- `.pytest_cache/`
- `coverage/`
- `*.pyc` files

---

### `make status`

**Purpose**: Display project status and structure

**What it does**:
- Shows directory structure
- Lists configuration files
- Displays project overview

**Usage**:
```bash
make status
```

**Example output**:
```
╔════════════════════════════════════════════════════════════╗
║  Project Status                                            ║
╚════════════════════════════════════════════════════════════╝

Directory Structure:
.
├── src/
│   ├── core/
│   ├── data/
│   └── presentation/
├── tests/
├── docs/
└── config/

Configuration Files:
package.json
Makefile
README.md
docker-compose.yml
```

---

## 🔄 Workflow Examples

### Starting a New Python Project

```bash
# 1. Initialize structure
make init

# 2. Setup Python
make setup-python

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate

# 4. Install dependencies
make install-deps

# 5. Start development
make dev
```

### Starting a New Node.js Project

```bash
# 1. Initialize structure
make init

# 2. Setup Node.js
make setup-node

# 3. Install dependencies
make install-deps

# 4. Start development
make dev
```

### Daily Development Workflow

```bash
# 1. Pull latest changes
git pull

# 2. Install any new dependencies
make install-deps

# 3. Run tests
make test

# 4. Check code quality
make lint

# 5. Format code
make format

# 6. Start development server
make dev
```

### Pre-Deployment Workflow

```bash
# 1. Run all tests
make test

# 2. Check code quality
make lint

# 3. Build for production
make build

# 4. Build Docker image
make docker-build

# 5. Test Docker container
make docker-up
# ... test application ...
make docker-down
```

### Docker Development Workflow

```bash
# 1. Build image
make docker-build

# 2. Start containers
make docker-up

# 3. View logs
docker-compose -f docker/docker-compose.yml logs -f

# 4. Stop when done
make docker-down
```

## 🛠️ Customization

### Adding Custom Commands

Add new targets to the Makefile:

```makefile
## my-command: Description of what it does
my-command:
	@echo "$(BLUE)Running my command...$(NC)"
	# Your commands here
	@echo "$(GREEN)✅ Done$(NC)"
```

### Modifying Existing Commands

Edit the Makefile to change behavior:

```makefile
## dev: Start development server with custom port
dev:
	@if [ -f package.json ]; then \
		PORT=8080 npm run dev; \
	fi
```

### Adding Language Support

Add new language setup:

```makefile
## setup-java: Setup Java project structure
setup-java:
	@echo "$(BLUE)☕ Setting up Java project...$(NC)"
	# Create pom.xml or build.gradle
	# Setup source directories
	@echo "$(GREEN)✅ Java project setup complete$(NC)"
```

## 🐛 Troubleshooting

### Command Not Found

**Problem**: `make: command not found`

**Solution**:
```bash
# Install make
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install
```

---

### Permission Denied

**Problem**: `make: permission denied`

**Solution**:
```bash
# Make the Makefile executable
chmod +x Makefile

# Or run with sudo (not recommended)
sudo make init
```

---

### Directory Already Exists

**Problem**: Some directories already exist

**Solution**:
The Makefile safely handles existing directories. It won't overwrite existing files unless explicitly designed to do so.

---

### Python/Node Not Found

**Problem**: `python: command not found` or `node: command not found`

**Solution**:
```bash
# Install Python
sudo apt-get install python3 python3-pip  # Ubuntu/Debian
brew install python3  # macOS

# Install Node.js
sudo apt-get install nodejs npm  # Ubuntu/Debian
brew install node  # macOS
```

---

### Make Target Failed

**Problem**: A make command fails

**Solution**:
```bash
# Run with verbose output
make -d target-name

# Check for missing prerequisites
make --trace target-name
```

---

## 📚 Additional Resources

- [GNU Make Manual](https://www.gnu.org/software/make/manual/)
- [Makefile Tutorial](https://makefiletutorial.com/)
- [Project README](../README.md)
- [Architecture Documentation](architecture/README.md)

## 🤝 Contributing to Makefile

To add new commands or improve existing ones:

1. Follow the existing pattern
2. Add descriptive comments with `##`
3. Use colored output for better UX
4. Test thoroughly before committing
5. Update this documentation

## 📝 Makefile Syntax Quick Reference

```makefile
# Target: prerequisites
target: prerequisite1 prerequisite2
	command1
	command2

# Variables
VAR = value
$(VAR)  # Use variable

# Phony targets (not files)
.PHONY: target-name

# Conditional execution
@if [ condition ]; then \
	command; \
fi

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
NC := \033[0m  # No Color

# Suppress command echo
@command  # Doesn't print command, only output
```

---

**Last Updated**: January 27, 2026  
**Version**: 1.0.0  
**Maintainer**: Vya-Jobs Team
