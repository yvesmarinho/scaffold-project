"""
Test for BUG-01: Directory conflict validation.

Com a fix implementada:
- project_path detecta quando target_dir.name == project_name e usa target_dir diretamente
- Não há mais estrutura duplicada project/project/
- A validação apenas AVISA o usuário, não bloqueia a operação
"""

from pathlib import Path

from scripts.lib.ui import _validate_directory_conflict


def test_directory_conflict_warning_with_content(tmp_path):
    """Should warn (but allow) when project name matches existing dir with content."""
    project_name = "my-project"
    target_dir = tmp_path / "my-project"
    target_dir.mkdir()
    (target_dir / "existing-file.txt").write_text("content")

    is_valid, msg = _validate_directory_conflict(project_name, target_dir)

    assert is_valid, "Should allow creation (with warning)"
    assert "Aviso" in msg, "Should contain warning message"
    assert "já existe" in msg
    assert "NÃO serão sobrescritos" in msg


def test_directory_no_warning_nonexistent(tmp_path):
    """Should allow without warning when target dir doesn't exist yet."""
    project_name = "my-project"
    target_dir = tmp_path / "my-project"  # não existe ainda

    is_valid, msg = _validate_directory_conflict(project_name, target_dir)

    assert is_valid, "Should allow creation"
    assert msg == "", "No warning for nonexistent directory"


def test_directory_no_warning_empty_dir(tmp_path):
    """Should allow without warning when target dir exists but is empty."""
    project_name = "my-project"
    target_dir = tmp_path / "my-project"
    target_dir.mkdir()  # existe mas vazio

    is_valid, msg = _validate_directory_conflict(project_name, target_dir)

    assert is_valid, "Should allow creation"
    assert msg == "", "No warning for empty directory"


def test_directory_no_conflict_different_names():
    """Should pass validation when names differ (standard case)."""
    project_name = "my-project"
    target_dir = Path("/home/user/projects")

    is_valid, msg = _validate_directory_conflict(project_name, target_dir)

    assert is_valid, "Should allow"
    assert msg == "", "No warning when names differ"


def test_directory_warning_nested_path(tmp_path):
    """Should warn (but allow) regardless of full path depth."""
    project_name = "api-service"
    target_dir = tmp_path / "very" / "long" / "path" / "to" / "api-service"
    target_dir.mkdir(parents=True)
    (target_dir / "file.txt").write_text("data")

    is_valid, msg = _validate_directory_conflict(project_name, target_dir)

    assert is_valid, "Should allow with warning"
    assert "Aviso" in msg or "já existe" in msg


def test_directory_different_case_same_name():
    """Should handle case-sensitive comparison correctly (Linux)."""
    project_name = "my-project"
    target_dir = Path("/home/user/My-Project")

    is_valid, msg = _validate_directory_conflict(project_name, target_dir)

    # Linux is case-sensitive, so these are different names → no match
    assert is_valid
    assert msg == ""
