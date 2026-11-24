"""
Testes para o hook pre-commit de validação do sistema de memória.

IMP-65 P1: Pre-commit hook que bloqueia commits de arquivos inválidos em .memory/

O hook valida:
1. Bloqueia commits de test-*.md em .memory/
2. Valida YAML frontmatter em arquivos .memory/*.md
3. Exit code 1 se violações detectadas

Referência: scripts/git-hooks/pre-commit
"""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _enable_hook_validation(monkeypatch):
    """Hook roda em modo manual por padrão; nos testes, força a validação."""
    monkeypatch.setenv("PRE_COMMIT_VALIDATE", "1")


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create .memory directory structure
    memory_dir = repo_path / ".memory" / "memories"
    memory_dir.mkdir(parents=True)

    # Copy pre-commit hook
    hook_src = Path(__file__).parent.parent / "scripts" / "git-hooks" / "pre-commit"
    hook_dst = repo_path / ".git" / "hooks" / "pre-commit"
    hook_dst.parent.mkdir(parents=True, exist_ok=True)
    hook_dst.write_text(hook_src.read_text())
    hook_dst.chmod(0o755)

    return repo_path


def test_hook_blocks_test_files(git_repo):
    """Verifica que o hook bloqueia commits de test-*.md em .memory/."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create test file with test pattern
    test_file = memory_dir / "__test-memory.md"
    test_file.write_text("Test content")

    # Try to stage and commit
    subprocess.run(["git", "add", str(test_file)], cwd=git_repo, check=True)

    # Commit should fail
    result = subprocess.run(
        ["git", "commit", "-m", "test: add test file"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Hook should block test file"
    assert "__test-memory.md" in result.stdout or "__test-memory.md" in result.stderr
    _msg = "Arquivos de teste em .memory/ não devem ser commitados"
    assert _msg in result.stdout or _msg in result.stderr


def test_hook_blocks_auto_generated_title(git_repo):
    """Verifica que o hook bloqueia __auto-generated-title.md."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create auto-generated-title file
    auto_file = memory_dir / "__auto-generated-title.md"
    auto_file.write_text("Auto-generated content")

    # Try to stage and commit
    subprocess.run(["git", "add", str(auto_file)], cwd=git_repo, check=True)

    # Commit should fail
    result = subprocess.run(
        ["git", "commit", "-m", "test: add auto-generated file"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Hook should block auto-generated file"
    assert (
        "__auto-generated-title.md" in result.stdout
        or "__auto-generated-title.md" in result.stderr
    )


def test_hook_blocks_search_test_files(git_repo):
    """Verifica que o hook bloqueia __search-test-*.md."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create search-test file
    search_file = memory_dir / "__search-test-results.md"
    search_file.write_text("Search test content")

    # Try to stage and commit
    subprocess.run(["git", "add", str(search_file)], cwd=git_repo, check=True)

    # Commit should fail
    result = subprocess.run(
        ["git", "commit", "-m", "test: add search test file"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Hook should block search test file"
    assert (
        "__search-test-results.md" in result.stdout
        or "__search-test-results.md" in result.stderr
    )


def test_hook_validates_frontmatter_invalid_category(git_repo):
    """Verifica que o hook rejeita categoria inválida em frontmatter."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create file with invalid category
    invalid_file = memory_dir / "test-invalid-category.md"
    invalid_file.write_text("""---
category: invalid_category
tags: [test]
---

# Test Memory

Content here.
""")

    # Try to stage and commit
    subprocess.run(["git", "add", str(invalid_file)], cwd=git_repo, check=True)

    # Commit should fail
    result = subprocess.run(
        ["git", "commit", "-m", "test: add invalid category"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Hook should reject invalid category"
    assert (
        "categoria inválida" in result.stdout or "categoria inválida" in result.stderr
    )


def test_hook_validates_frontmatter_missing_closing(git_repo):
    """Verifica que o hook rejeita frontmatter sem closing ---."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create file with malformed frontmatter (no closing ---, no --- in content)
    malformed_file = memory_dir / "test-malformed.md"
    malformed_file.write_text("""---
category: project
tags: [test]

Content without proper frontmatter closing.
""")

    # Try to stage and commit
    subprocess.run(["git", "add", str(malformed_file)], cwd=git_repo, check=True)

    # Commit should fail
    result = subprocess.run(
        ["git", "commit", "-m", "test: add malformed frontmatter"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0, "Hook should reject malformed frontmatter"
    _msg = "Frontmatter YAML inválido"
    assert _msg in result.stdout or _msg in result.stderr


def test_hook_allows_valid_memory_file(git_repo):
    """Verifica que o hook permite commit de arquivo válido."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create valid file
    valid_file = memory_dir / "valid-memory.md"
    valid_file.write_text("""---
category: project
tags: [test, valid]
---

# Valid Memory

This is valid content.
""")

    # Stage and commit should succeed
    subprocess.run(["git", "add", str(valid_file)], cwd=git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test: add valid memory"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Hook should allow valid file"


def test_hook_allows_file_without_frontmatter(git_repo):
    """Verifica que o hook permite arquivo sem frontmatter (opcional)."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create file without frontmatter
    no_frontmatter = memory_dir / "no-frontmatter.md"
    no_frontmatter.write_text("""# Memory Without Frontmatter

Content without frontmatter is valid.
""")

    # Stage and commit should succeed
    subprocess.run(["git", "add", str(no_frontmatter)], cwd=git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test: add file without frontmatter"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Hook should allow file without frontmatter"


def test_hook_skips_non_memory_files(git_repo):
    """Verifica que o hook ignora arquivos fora de .memory/."""
    # Create regular file
    regular_file = git_repo / "README.md"
    regular_file.write_text("# Test README")

    # Stage and commit should succeed without validation
    subprocess.run(["git", "add", str(regular_file)], cwd=git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "docs: add README"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Hook should skip non-memory files"
    # Hook atual valida tudo e reporta sucesso geral (mensagem em stderr)
    _msg = "TODAS AS VERIFICAÇÕES PASSARAM"
    assert _msg in result.stderr or _msg in result.stdout


def test_hook_allows_valid_categories(git_repo):
    """Verifica que o hook aceita todas as categorias válidas."""
    memory_dir = git_repo / ".memory" / "memories"
    valid_categories = ["project", "team", "sessions", "user"]

    for category in valid_categories:
        # Create file with valid category
        valid_file = memory_dir / f"test-{category}.md"
        valid_file.write_text(f"""---
category: {category}
tags: [test]
---

# Memory with {category} category

Content here.
""")

        # Stage and commit should succeed
        subprocess.run(["git", "add", str(valid_file)], cwd=git_repo, check=True)

        result = subprocess.run(
            ["git", "commit", "-m", f"test: add {category} memory"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Hook should allow category '{category}'"


def test_hook_error_messages_helpful(git_repo):
    """Verifica que mensagens de erro são úteis."""
    memory_dir = git_repo / ".memory" / "memories"

    # Create test file
    test_file = memory_dir / "__test-error-msg.md"
    test_file.write_text("Test content")

    # Try to commit
    subprocess.run(["git", "add", str(test_file)], cwd=git_repo, check=True)

    result = subprocess.run(
        ["git", "commit", "-m", "test: trigger error"],
        cwd=git_repo,
        capture_output=True,
        text=True,
    )

    output = result.stdout + result.stderr

    # Should mention helpful commands
    assert "make memory-cleanup" in output or "memory-cleanup" in output
    assert "conftest.py" in output or "test fixtures" in output.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
