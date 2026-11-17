"""
tests/conftest.py — Fixtures compartilhadas para os testes do scaffold.

IMP-16: Setup de pytest com fixtures de config para todos os combos
        domínio × linguagem.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Garante que scripts/ está no sys.path para importar lib/
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.config import ProjectConfig  # noqa: E402  (import after sys.path)

# ---------------------------------------------------------------------------
# Diretório de snapshots
# ---------------------------------------------------------------------------
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

# ---------------------------------------------------------------------------
# Opção CLI  --update-snapshots
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Regenera os arquivos de snapshot baseline (sobrescreve os existentes)",
    )


@pytest.fixture
def update_snapshots(request: pytest.FixtureRequest) -> bool:
    return request.config.getoption("--update-snapshots")


# ---------------------------------------------------------------------------
# Fixture factory: ProjectConfig
# ---------------------------------------------------------------------------


@pytest.fixture
def make_project_config(tmp_path: Path):
    """
    Factory fixture que constrói um ProjectConfig isolado em tmp_path.

    Uso:
        def test_foo(make_project_config):
            cfg = make_project_config("programming", "python")
    """

    def _factory(
        domain: str,
        language: str,
        project_name: str = "test-project",
        extra_profiles: list[str] | None = None,
    ) -> ProjectConfig:
        target = tmp_path / project_name
        target.mkdir(parents=True, exist_ok=True)
        return ProjectConfig(
            project_name=project_name,
            project_title="Test Project",
            description="A test project for smoke testing",
            domain=domain,
            language=language,
            github_repo=None,
            shared_dir=tmp_path / "shared",
            target_dir=target,
            created_at="2026-03-07T00:00:00",
            extra_profiles=extra_profiles or [],
        )

    return _factory


# ---------------------------------------------------------------------------
# Common Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_file(tmp_path: Path):
    """
    Factory fixture to create temporary files for testing.

    Usage:
        def test_foo(temp_file):
            test_file = temp_file("test.txt", "content")
    """
    def _factory(filename: str, content: str = "") -> Path:
        file_path = tmp_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
    return _factory


@pytest.fixture
def mock_env(monkeypatch):
    """
    Factory fixture to set environment variables.

    Usage:
        def test_foo(mock_env):
            mock_env({"KEY": "value", "DEBUG": "true"})
    """
    def _factory(env_vars: dict[str, str]):
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
    return _factory


@pytest.fixture
def capture_logs(caplog):
    """
    Fixture to capture and assert on log messages.

    Usage:
        def test_foo(capture_logs):
            with capture_logs("INFO") as logs:
                logger.info("test message")
            assert "test message" in logs
    """
    import logging
    from contextlib import contextmanager

    @contextmanager
    def _capture(level: str = "INFO"):
        caplog.set_level(getattr(logging, level))
        yield caplog.text

    return _capture


@pytest.fixture
def mock_subprocess(monkeypatch):
    """
    Mock subprocess.run calls for testing.

    Usage:
        def test_foo(mock_subprocess):
            mock_subprocess(stdout="output", stderr="", returncode=0)
    """


# ---------------------------------------------------------------------------
# Git Configuration for Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def configure_git_for_tests():
    """
    Configure Git user globally for all tests.

    This ensures scaffold tests that create Git commits don't fail
    due to missing user.email/user.name configuration.

    Runs once per test session automatically.
    """
    import subprocess

    # Configure Git user for tests
    subprocess.run(
        ["git", "config", "--global", "user.email", "test@example.com"],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "--global", "user.name", "Test User"],
        check=False,
        capture_output=True,
    )

    from unittest.mock import Mock
    import subprocess

    def _factory(stdout: str = "", stderr: str = "", returncode: int = 0):
        mock_result = Mock()
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        mock_result.returncode = returncode

        mock_run = Mock(return_value=mock_result)
        monkeypatch.setattr(subprocess, "run", mock_run)
        return mock_run

    return _factory


@pytest.fixture
def sample_config_file(temp_file):
    """
    Create a sample configuration file for testing.

    Returns:
        Path to the config file
    """
    config_content = """
    [project]
    name = "test-project"
    version = "1.0.0"

    [settings]
    debug = true
    """
    return temp_file("config.ini", config_content)


@pytest.fixture(scope="session", autouse=True)
def isolate_scaffold_logs_session(tmp_path_factory):
    """
    Fallback de SCAFFOLD_LOGS_DIR para fixtures de escopo module/class/session,
    que rodam antes do ``isolate_tests`` (escopo function) e escapariam dele.
    """
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("SCAFFOLD_LOGS_DIR", str(tmp_path_factory.mktemp("scaffold-logs")))
        yield


@pytest.fixture(autouse=True)
def isolate_tests(tmp_path, monkeypatch):
    """
    Auto-use fixture to isolate tests from system environment.

    - Sets temporary HOME/TMPDIR
    - Prevents accidental modifications to real files
    - Redireciona os logs de operação da ferramenta (SCAFFOLD_LOGS_DIR) para
      tmp_path — herdado também pelos testes que rodam scaffold.py em subprocesso
    """
    monkeypatch.setenv("SCAFFOLD_LOGS_DIR", str(tmp_path / "scaffold-logs"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("TMPDIR", str(tmp_path / "tmp"))
    (tmp_path / "home").mkdir(exist_ok=True)
    (tmp_path / "tmp").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Performance Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def benchmark_timer():
    """
    Simple benchmark timer for performance tests.

    Usage:
        def test_performance(benchmark_timer):
            with benchmark_timer() as timer:
                # code to benchmark
            assert timer.elapsed < 1.0  # seconds
    """
    import time
    from contextlib import contextmanager

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.elapsed = None

        def __enter__(self):
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, *args):
            self.end_time = time.perf_counter()
            self.elapsed = self.end_time - self.start_time

    @contextmanager
    def _timer():
        timer = Timer()
        with timer:
            yield timer

    return _timer


# ---------------------------------------------------------------------------
# Memory System Fixtures (IMP-65: Prevent .memory/ pollution by tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_memory_dir(tmp_path: Path):
    """
    Isolated memory directory for tests.

    Prevents test pollution of real .memory/ directory.
    All test memories are saved to temporary directory
    which is automatically cleaned up after test.

    Usage:
        def test_save_memory(temp_memory_dir):
            # Write to isolated memory
            (temp_memory_dir / "project" / "test.md").write_text("test")
    """
    memory_dir = tmp_path / ".memory" / "memories"
    memory_dir.mkdir(parents=True)

    # Setup test structure
    (memory_dir / "project").mkdir()
    (memory_dir / "team").mkdir()
    (memory_dir / "sessions").mkdir()

    yield memory_dir

    # Cleanup happens automatically via tmp_path fixture


@pytest.fixture
def isolated_memory(temp_memory_dir: Path, monkeypatch):
    """
    Monkey-patch memory functions to use isolated directory.

    Automatically patches MEMORY_DIR environment variable to point
    to temporary directory, ensuring tests never touch real .memory/.

    Usage:
        def test_something(isolated_memory):
            save_memory(...)  # Will use temp_memory_dir automatically
    """
    # Patch MEMORY_DIR constant in memory scripts
    monkeypatch.setenv("MEMORY_DIR", str(temp_memory_dir))
    yield temp_memory_dir
