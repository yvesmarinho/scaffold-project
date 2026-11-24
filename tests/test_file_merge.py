"""
Testes para sistema de merge inteligente de arquivos.

Bug fix: BUG-#1.1 (P0 CRITICAL - Sistema de merge ausente)
Tests: Sprint 1 - Security Critical

Cenários testados:
1. GitignoreMerger: .gitignore pré-existente recebe .secrets/
2. MakefileMerger: Makefile customizado preserva targets + adiciona essenciais
3. ReadmeMerger: README customizado preserva intro + adiciona seções
4. merge_or_skip: Arquivos sem merger são pulados (comportamento seguro)
"""

import tempfile
from pathlib import Path

import pytest

from scripts.lib.file_merge import (
    GitignoreMerger,
    MakefileMerger,
    ReadmeMerger,
    get_registered_mergers,
    merge_or_skip,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_dir():
    """Diretório temporário para testes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# =============================================================================
# GitignoreMerger Tests
# =============================================================================


def test_gitignore_merge_adds_security_patterns(temp_dir):
    """
    Cenário: .gitignore do GitHub existe mas não tem .secrets/
    Expectativa: .secrets/ e outros padrões críticos são adicionados
    Bug fix: BUG-#1 (P0 - .gitignore não atualizado, risco de vazamento)
    """
    # Arrange: Simular .gitignore do GitHub (Python padrão)
    gitignore = temp_dir / ".gitignore"
    gitignore.write_text("""# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
dist/
build/
*.egg-info/
""")

    template_content = """# Template gitignore (não usado diretamente pelo merger)
.secrets/
*.key
"""

    # Act: Executar merge
    merger = GitignoreMerger()
    result = merger.merge(gitignore, template_content, interactive=False)

    # Assert: Verificar que padrões críticos foram adicionados
    assert result.status == "created"  # Merge bem-sucedido
    assert ".secrets/" in gitignore.read_text()
    assert "*.key" in gitignore.read_text()
    assert "__pycache__/" in gitignore.read_text()  # Conteúdo original preservado
    assert "Enterprise Template Security" in gitignore.read_text()  # Header adicionado


def test_gitignore_merge_skips_if_all_patterns_present(temp_dir):
    """
    Cenário: .gitignore já tem todos os padrões críticos
    Expectativa: Skip (não modificar arquivo)
    """
    # Arrange: .gitignore já completo
    gitignore = temp_dir / ".gitignore"
    complete_content = """# Security
.secrets/
*.key
*.pem
.env
.vault_pass
*.crt
*secret*
*password*
*token*

# Python
__pycache__/
"""
    gitignore.write_text(complete_content)

    template_content = ".secrets/\n*.key\n"

    # Act
    merger = GitignoreMerger()
    result = merger.merge(gitignore, template_content, interactive=False)

    # Assert: Arquivo não foi modificado
    assert result.status == "skipped"
    assert gitignore.read_text() == complete_content  # Nenhuma mudança


def test_gitignore_merge_on_empty_file(temp_dir):
    """
    Cenário: .gitignore existe mas está vazio
    Expectativa: Todos padrões críticos são adicionados
    """
    # Arrange
    gitignore = temp_dir / ".gitignore"
    gitignore.write_text("")

    template_content = ".secrets/\n*.key\n"

    # Act
    merger = GitignoreMerger()
    result = merger.merge(gitignore, template_content, interactive=False)

    # Assert
    assert result.status == "created"
    content = gitignore.read_text()
    assert ".secrets/" in content
    assert "*.key" in content
    assert "*.pem" in content  # Todos os CRITICAL_PATTERNS


# =============================================================================
# MakefileMerger Tests
# =============================================================================


def test_makefile_merge_adds_essential_targets(temp_dir):
    """
    Cenário: Makefile customizado sem targets do template
    Expectativa: Targets essenciais adicionados, customizados preservados
    Bug fix: BUG-#1.1 (P0 sistêmico - Makefile não mesclado)
    """
    # Arrange: Makefile customizado
    makefile = temp_dir / "Makefile"
    makefile.write_text("""deploy:
\t./scripts/deploy.sh

custom-task:
\techo "Custom task"
""")

    template_content = """help:
\t@echo "Available targets:"
\t@echo "  make test    - Run tests"

test:
\tpytest tests/

lint:
\truff check .
"""

    # Act
    merger = MakefileMerger()
    result = merger.merge(makefile, template_content, interactive=False)

    # Assert
    assert result.status == "created"
    content = makefile.read_text()
    assert "help:" in content  # Target do template adicionado
    assert "test:" in content  # Target do template adicionado
    assert "lint:" in content  # Target do template adicionado
    assert "deploy:" in content  # Target customizado preservado
    assert "custom-task:" in content  # Target customizado preservado


def test_makefile_merge_skips_if_all_targets_present(temp_dir):
    """
    Cenário: Makefile já tem todos os targets essenciais
    Expectativa: Skip (não modificar)
    """
    # Arrange: Makefile completo
    makefile = temp_dir / "Makefile"
    complete_content = """help:
\t@echo "Help"

test:
\tpytest

lint:
\truff check .

format:
\tblack .

clean:
\trm -rf build/

install-deps:
\tpip install -r requirements.txt
"""
    makefile.write_text(complete_content)

    template_content = "help:\n\t@echo 'template help'\n"

    # Act
    merger = MakefileMerger()
    result = merger.merge(makefile, template_content, interactive=False)

    # Assert
    assert result.status == "skipped"
    assert makefile.read_text() == complete_content


# =============================================================================
# ReadmeMerger Tests
# =============================================================================


def test_readme_merge_adds_template_sections(temp_dir):
    """
    Cenário: README do GitHub com introdução customizada
    Expectativa: Seções do template adicionadas, intro preservada
    Bug fix: BUG-#1.1 (P0 sistêmico - README não mesclado)
    """
    # Arrange: README do GitHub
    readme = temp_dir / "README.md"
    readme.write_text("""# My Custom Project

This is my awesome project that does amazing things.

## Custom Section

Some custom content here.
""")

    template_content = """# {{PROJECT_NAME}}

Template intro (não usado)

## Project Status

🟢 Active development

## Stack

- Python 3.12+
- pytest

## Features

- Feature 1
- Feature 2
"""

    # Act
    merger = ReadmeMerger()
    result = merger.merge(readme, template_content, interactive=False)

    # Assert
    assert result.status == "created"
    content = readme.read_text()
    assert "My Custom Project" in content  # Título preservado
    assert "awesome project" in content  # Intro preservada
    assert "## Project Status" in content  # Seção template adicionada
    assert "## Stack" in content  # Seção template adicionada
    assert "## Features" in content  # Seção template adicionada
    assert "## Custom Section" in content  # Seção customizada preservada


def test_readme_merge_skips_if_all_sections_present(temp_dir):
    """
    Cenário: README já tem todas as seções essenciais
    Expectativa: Skip (não modificar)
    """
    # Arrange: README completo
    readme = temp_dir / "README.md"
    complete_content = """# My Project

Intro text

## Project Status
Active

## Stack
Python

## Features
- Feature 1

## Installation
pip install

## Usage
python main.py
"""
    readme.write_text(complete_content)

    template_content = "## Project Status\nTemplate status\n"

    # Act
    merger = ReadmeMerger()
    result = merger.merge(readme, template_content, interactive=False)

    # Assert
    assert result.status == "skipped"
    assert readme.read_text() == complete_content


def test_readme_merge_preserves_intro_without_sections(temp_dir):
    """
    Cenário: README só tem introdução, sem seções ##
    Expectativa: Intro preservada, seções template adicionadas
    """
    # Arrange
    readme = temp_dir / "README.md"
    readme.write_text("""# Simple Project

Just a simple intro paragraph.
No sections yet.
""")

    template_content = """# Template

## Project Status
Active

## Stack
Python
"""

    # Act
    merger = ReadmeMerger()
    result = merger.merge(readme, template_content, interactive=False)

    # Assert
    assert result.status == "created"
    content = readme.read_text()
    assert "Simple Project" in content
    assert "simple intro" in content
    assert "## Project Status" in content
    assert "## Stack" in content


# =============================================================================
# merge_or_skip Function Tests
# =============================================================================


def test_merge_or_skip_uses_gitignore_merger(temp_dir):
    """
    Cenário: Arquivo .gitignore existente
    Expectativa: GitignoreMerger é usado automaticamente
    """
    # Arrange
    gitignore = temp_dir / ".gitignore"
    gitignore.write_text("__pycache__/\n")

    template_content = ".secrets/\n*.key\n"

    # Act
    result = merge_or_skip(gitignore, template_content, interactive=False)

    # Assert
    assert result.status in ["created", "skipped"]
    assert ".secrets/" in gitignore.read_text()  # Merge executado


def test_merge_or_skip_skips_unsupported_files(temp_dir):
    """
    Cenário: Arquivo sem merger disponível (ex: custom.txt)
    Expectativa: Skip seguro (não tenta merge)
    """
    # Arrange
    custom_file = temp_dir / "custom.txt"
    custom_file.write_text("User content\n")

    template_content = "Template content\n"

    # Act
    result = merge_or_skip(custom_file, template_content, interactive=False)

    # Assert
    assert result.status == "skipped"
    assert result.message == "File exists, no merger available"
    assert custom_file.read_text() == "User content\n"  # Não modificado


def test_merge_or_skip_uses_makefile_merger(temp_dir):
    """
    Cenário: Makefile existente
    Expectativa: MakefileMerger é usado automaticamente
    """
    # Arrange
    makefile = temp_dir / "Makefile"
    makefile.write_text("deploy:\n\t./deploy.sh\n")

    template_content = "help:\n\t@echo 'Help'\n\ntest:\n\tpytest\n"

    # Act
    result = merge_or_skip(makefile, template_content, interactive=False)

    # Assert
    assert result.status in ["created", "skipped"]
    content = makefile.read_text()
    assert "deploy:" in content  # Preservado
    if result.status == "created":
        assert "help:" in content  # Adicionado


def test_merge_or_skip_uses_readme_merger(temp_dir):
    """
    Cenário: README.md existente
    Expectativa: ReadmeMerger é usado automaticamente
    """
    # Arrange
    readme = temp_dir / "README.md"
    readme.write_text("# My Project\n\nIntro\n")

    template_content = "# Template\n\n## Project Status\nActive\n"

    # Act
    result = merge_or_skip(readme, template_content, interactive=False)

    # Assert
    assert result.status in ["created", "skipped"]
    content = readme.read_text()
    assert "My Project" in content  # Preservado


# =============================================================================
# Registry Tests
# =============================================================================


def test_get_registered_mergers():
    """
    Cenário: Consultar mergers registrados
    Expectativa: 13 mergers no sistema (3 essenciais + 10 específicos)
    """
    # Act
    mergers = get_registered_mergers()

    # Assert - Mergers essenciais
    assert "GitignoreMerger" in mergers
    assert "MakefileMerger" in mergers
    assert "ReadmeMerger" in mergers

    # Mergers específicos
    assert "WorkspaceMerger" in mergers
    assert "JSONMerger" in mergers
    assert "CopilotAgentMerger" in mergers
    assert "CopilotPromptMerger" in mergers
    assert "CopilotRulesMerger" in mergers
    assert "GitHubWorkflowMerger" in mergers
    assert "PyprojectMerger" in mergers
    assert "PreCommitMerger" in mergers
    assert "VSCodeConfigMerger" in mergers
    assert "IssueTemplateMerger" in mergers

    assert len(mergers) == 13


# =============================================================================
# Integration Tests (Cenário Completo)
# =============================================================================


def test_full_github_repo_scaffold_scenario(temp_dir):
    """
    Cenário COMPLETO: Simula clone de repo GitHub + scaffold

    1. Repo tem .gitignore, README.md do GitHub
    2. Scaffold executa merge em ambos
    3. Verifica resultado final

    Este é o cenário REAL que causou o BUG-#1.
    """
    # Arrange: Simular repo GitHub recém-clonado
    gitignore = temp_dir / ".gitignore"
    gitignore.write_text("""# Python
__pycache__/
*.pyc
*.pyo
""")

    readme = temp_dir / "README.md"
    readme.write_text("""# knowledge-harvester-library

A library for harvesting knowledge from various sources.
""")

    # Templates (simplificados)
    gitignore_template = ".secrets/\n*.key\n"
    readme_template = """# Project

## Project Status
Active

## Stack
Python
"""

    # Act: Executar merge em ambos os arquivos
    gitignore_result = merge_or_skip(gitignore, gitignore_template, interactive=False)
    readme_result = merge_or_skip(readme, readme_template, interactive=False)

    # Assert: Verificar merge bem-sucedido
    # .gitignore
    assert gitignore_result.status == "created"
    gitignore_content = gitignore.read_text()
    assert ".secrets/" in gitignore_content  # 🔒 CRÍTICO: Segurança
    assert "__pycache__/" in gitignore_content  # Preservado

    # README.md
    assert readme_result.status == "created"
    readme_content = readme.read_text()
    assert "knowledge-harvester-library" in readme_content  # Preservado
    assert "harvesting knowledge" in readme_content  # Preservado
    assert "## Project Status" in readme_content  # Adicionado
    assert "## Stack" in readme_content  # Adicionado


def test_empty_project_scaffold_scenario(temp_dir):
    """
    Cenário: Projeto vazio (sem arquivos pré-existentes)
    Expectativa: merge_or_skip não é chamado (arquivos criados normalmente)

    Este cenário já funcionava antes do fix.
    """
    # Arrange: Diretório vazio (sem .gitignore nem README)
    gitignore = temp_dir / ".gitignore"
    readme = temp_dir / "README.md"

    # Assert: Arquivos não existem
    assert not gitignore.exists()
    assert not readme.exists()

    # Neste cenário, create_structure() cria arquivos diretamente
    # (não passa por merge_or_skip)
    # Este teste documenta o comportamento baseline.
