# Testing Guide

**Project**: Enterprise Scaffold Project Template
**Version**: 1.3.0
**Last Updated**: 2026-03-20

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Test Organization](#test-organization)
4. [Writing Tests](#writing-tests)
5. [Running Tests](#running-tests)
6. [Code Coverage](#code-coverage)
7. [Test Markers](#test-markers)
8. [Fixtures](#fixtures)
9. [Mocking](#mocking)
10. [Best Practices](#best-practices)
11. [CI/CD Integration](#cicd-integration)
12. [Troubleshooting](#troubleshooting)

---

## Overview

This template provides a comprehensive testing infrastructure using **pytest**, the most popular Python testing framework. The setup includes:

- ✅ **pytest** for test execution
- ✅ **pytest-cov** for code coverage
- ✅ **pytest-mock** for mocking support
- ✅ **Configuration files** (pytest.ini, .coveragerc)
- ✅ **Shared fixtures** in conftest.py
- ✅ **Example tests** demonstrating patterns
- ✅ **CI/CD integration** with GitHub Actions

### Testing Philosophy

- **Unit Tests**: Fast, isolated tests for individual components (≥80% coverage target)
- **Integration Tests**: Tests involving multiple components or external services
- **Smoke Tests**: Quick validation tests for critical functionality
- **Security Tests**: Validation of security measures and sensitive data handling

---

## Quick Start

### 1. Install Dependencies

```bash
# Install test dependencies
pip install -e ".[dev]"

# Or using requirements
pip install -r requirements-dev.txt
```

### 2. Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_example.py

# Run specific test class
pytest tests/test_example.py::TestExampleUnitTests

# Run specific test method
pytest tests/test_example.py::TestExampleUnitTests::test_simple_assertion
```

### 3. Check Coverage

```bash
# Run tests with coverage report
pytest --cov

# Generate HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# Coverage report in terminal with missing lines
pytest --cov --cov-report=term-missing
```

---

## Test Organization

### Directory Structure

```
tests/
├── __init__.py                 # Package marker
├── conftest.py                 # Shared fixtures and configuration
├── test_example.py             # Example tests (template)
├── unit/                       # Unit tests (fast, isolated)
│   ├── test_module1.py
│   └── test_module2.py
├── integration/                # Integration tests (external dependencies)
│   ├── test_api_integration.py
│   └── test_database_integration.py
├── fixtures/                   # Test data files
│   ├── sample_config.json
│   └── test_data.csv
├── helpers/                    # Test helper functions
│   └── assertions.py
└── snapshots/                  # Snapshot test baselines
    └── expected_output.txt
```

### Naming Conventions

- **Test files**: `test_*.py` or `*_test.py`
- **Test classes**: `Test*` (e.g., `TestUserAuth`)
- **Test functions**: `test_*` (e.g., `test_user_login_success`)
- **Fixtures**: Descriptive names (e.g., `mock_database`, `sample_user`)

---

## Writing Tests

### Basic Test Structure

```python
import pytest

class TestFeature:
    """Test suite for a specific feature."""

    def test_success_case(self):
        """Test the happy path."""
        result = function_to_test()
        assert result == expected_value

    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError):
            function_with_error()
```

### Assertion Patterns

```python
# Equality assertions
assert result == expected
assert result != unexpected

# Boolean assertions
assert condition
assert not condition
assert value is True
assert value is False

# Membership assertions
assert item in collection
assert item not in collection

# Type assertions
assert isinstance(obj, MyClass)
assert type(obj) == MyClass

# Comparison assertions
assert value > 10
assert value >= 10
assert value < 100
assert value <= 100

# String assertions
assert "substring" in text
assert text.startswith("prefix")
assert text.endswith("suffix")

# Exception assertions
with pytest.raises(ValueError, match="error message pattern"):
    function_that_raises()

# Warning assertions
with pytest.warns(UserWarning):
    function_that_warns()
```

### Parametrized Tests

Use parametrization to test multiple cases efficiently:

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
])
def test_double(input, expected):
    """Test doubling function with multiple inputs."""
    assert double(input) == expected
```

### Fixture-Based Tests

```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"id": 1, "name": "test"}

def test_with_fixture(sample_data):
    """Use fixture in test."""
    assert sample_data["id"] == 1
    assert sample_data["name"] == "test"
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with very verbose output (show full diffs)
pytest -vv

# Stop after first failure
pytest -x

# Stop after N failures
pytest --maxfail=3

# Run last failed tests
pytest --lf

# Run failed tests first, then all others
pytest --ff
```

### Selecting Tests

```bash
# Run specific file
pytest tests/test_module.py

# Run specific class
pytest tests/test_module.py::TestClass

# Run specific test
pytest tests/test_module.py::TestClass::test_method

# Run by marker
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m "not slow"    # Skip slow tests

# Run by keyword
pytest -k "test_user"   # Run tests matching "test_user"
pytest -k "not integration"  # Skip integration tests
```

### Parallel Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (auto-detect CPUs)
pytest -n auto

# Run tests on 4 workers
pytest -n 4
```

---

## Code Coverage

### Configuration

Coverage is configured in `pytest.ini`:

```ini
[pytest]
addopts =
    --cov=src
    --cov=scripts/lib
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### Coverage Commands

```bash
# Basic coverage report
pytest --cov

# Coverage with missing lines
pytest --cov --cov-report=term-missing

# HTML coverage report
pytest --cov --cov-report=html
open htmlcov/index.html

# XML coverage (for CI/CD)
pytest --cov --cov-report=xml

# Skip coverage for specific run
pytest --no-cov

# Coverage for specific module
pytest --cov=src.module --cov-report=term-missing
```

### Coverage Targets

- **Overall Project**: ≥80% coverage
- **Critical Modules**: ≥90% coverage
- **Utility Functions**: ≥95% coverage
- **CLI Tools**: ≥75% coverage

### Excluding from Coverage

In code:

```python
def debug_function():  # pragma: no cover
    """This function is excluded from coverage."""
    print("Debug info")
```

In `pytest.ini`:

```ini
[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    raise NotImplementedError
```

---

## Test Markers

### Built-in Markers

```python
@pytest.mark.unit           # Unit test (fast, isolated)
@pytest.mark.integration    # Integration test (external dependencies)
@pytest.mark.slow           # Slow test (> 1 second)
@pytest.mark.smoke          # Smoke test (quick validation)
@pytest.mark.security       # Security-related test

@pytest.mark.skip           # Skip test
@pytest.mark.skipif(condition, reason="...")  # Conditional skip
@pytest.mark.xfail          # Expected to fail

@pytest.mark.requires_docker    # Requires Docker
@pytest.mark.requires_ssh       # Requires SSH server
@pytest.mark.requires_network   # Requires network connectivity
```

### Using Markers

```python
import pytest

@pytest.mark.unit
def test_unit():
    """Fast unit test."""
    assert True

@pytest.mark.integration
@pytest.mark.requires_docker
def test_integration():
    """Integration test requiring Docker."""
    assert True

@pytest.mark.slow
def test_slow_operation():
    """Slow test marked explicitly."""
    import time
    time.sleep(2)
    assert True

@pytest.mark.skipif(sys.platform == "win32", reason="Not supported on Windows")
def test_unix_only():
    """Test that only runs on Unix systems."""
    assert True
```

### Running by Marker

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run all except slow tests
pytest -m "not slow"

# Run unit OR smoke tests
pytest -m "unit or smoke"

# Run tests requiring Docker
pytest -m requires_docker
```

---

## Fixtures

### Using Built-in Fixtures

```python
def test_temp_dir(tmp_path):
    """Use tmp_path for temporary directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")
    assert test_file.read_text() == "content"

def test_monkeypatch_env(monkeypatch):
    """Use monkeypatch to modify environment."""
    monkeypatch.setenv("API_KEY", "test_key")
    import os
    assert os.getenv("API_KEY") == "test_key"

def test_capture_output(capsys):
    """Capture stdout/stderr."""
    print("test output")
    captured = capsys.readouterr()
    assert "test output" in captured.out
```

### Custom Fixtures (from conftest.py)

```python
def test_temp_file(temp_file):
    """Use custom temp_file fixture."""
    file = temp_file("test.txt", "Hello, World!")
    assert file.exists()
    assert file.read_text() == "Hello, World!"

def test_mock_env(mock_env):
    """Use custom mock_env fixture."""
    mock_env({"DEBUG": "true", "API_URL": "http://test"})
    import os
    assert os.getenv("DEBUG") == "true"

def test_benchmark(benchmark_timer):
    """Use custom benchmark_timer fixture."""
    with benchmark_timer() as timer:
        result = sum(range(1000))
    assert timer.elapsed < 0.01
    assert result == 499500
```

### Fixture Scopes

```python
import pytest

@pytest.fixture(scope="function")  # Default: runs for each test
def function_fixture():
    return "function-scope"

@pytest.fixture(scope="class")  # Runs once per test class
def class_fixture():
    return "class-scope"

@pytest.fixture(scope="module")  # Runs once per module
def module_fixture():
    return "module-scope"

@pytest.fixture(scope="session")  # Runs once per test session
def session_fixture():
    return "session-scope"
```

---

## Mocking

### Using unittest.mock

```python
from unittest.mock import Mock, patch, MagicMock

def test_mock_function():
    """Mock a function call."""
    mock_func = Mock(return_value=42)
    result = mock_func("arg1", kwarg="value")

    assert result == 42
    mock_func.assert_called_once_with("arg1", kwarg="value")

def test_mock_side_effect():
    """Use side_effect for multiple returns."""
    mock_func = Mock(side_effect=[1, 2, 3])
    assert mock_func() == 1
    assert mock_func() == 2
    assert mock_func() == 3

def test_mock_exception():
    """Mock function that raises exception."""
    mock_func = Mock(side_effect=ValueError("error"))
    with pytest.raises(ValueError):
        mock_func()
```

### Patching

```python
def test_patch_function():
    """Patch a module function."""
    with patch('module.function', return_value=42) as mock:
        result = module.function()
        assert result == 42
        mock.assert_called_once()

def test_patch_decorator():
    """Use patch as decorator."""
    @patch('module.function', return_value=42)
    def inner(mock):
        result = module.function()
        assert result == 42

    inner()

def test_patch_object_method():
    """Patch object method."""
    obj = MyClass()
    with patch.object(obj, 'method', return_value='mocked'):
        assert obj.method() == 'mocked'
```

### Using pytest-mock

```python
def test_with_mocker(mocker):
    """Use pytest-mock's mocker fixture."""
    mock = mocker.patch('module.function', return_value=42)
    result = module.function()
    assert result == 42
    mock.assert_called_once()

def test_spy(mocker):
    """Use spy to monitor real function."""
    spy = mocker.spy(module, 'function')
    result = module.function()
    spy.assert_called_once()
```

---

## Best Practices

### 1. Test Isolation

```python
# ✅ Good: Tests are independent
def test_feature_a():
    data = create_test_data()
    assert process(data) == expected

def test_feature_b():
    data = create_test_data()
    assert validate(data) is True

# ❌ Bad: Tests depend on shared state
shared_data = None

def test_setup():
    global shared_data
    shared_data = create_test_data()

def test_use_shared():  # Fails if test_setup doesn't run first
    assert process(shared_data) == expected
```

### 2. Descriptive Test Names

```python
# ✅ Good: Clear what is being tested
def test_user_login_with_valid_credentials_returns_success():
    pass

def test_user_login_with_invalid_password_raises_auth_error():
    pass

# ❌ Bad: Unclear test purpose
def test_1():
    pass

def test_login():
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_create_user():
    # Arrange: Set up test data
    username = "testuser"
    email = "test@example.com"

    # Act: Perform the action
    user = create_user(username, email)

    # Assert: Verify the result
    assert user.username == username
    assert user.email == email
    assert user.is_active is True
```

### 4. Test One Thing

```python
# ✅ Good: Each test focuses on one aspect
def test_user_creation_sets_username():
    user = create_user("test")
    assert user.username == "test"

def test_user_creation_sets_default_active_status():
    user = create_user("test")
    assert user.is_active is True

# ❌ Bad: Testing multiple things
def test_user_creation():
    user = create_user("test")
    assert user.username == "test"
    assert user.is_active is True
    assert user.email is None
    assert user.created_at is not None
```

### 5. Use Fixtures for Setup

```python
# ✅ Good: Reusable fixture
@pytest.fixture
def sample_user():
    return User("test", "test@example.com")

def test_user_login(sample_user):
    assert sample_user.username == "test"

def test_user_email(sample_user):
    assert sample_user.email == "test@example.com"

# ❌ Bad: Duplicated setup
def test_user_login():
    user = User("test", "test@example.com")
    assert user.username == "test"

def test_user_email():
    user = User("test", "test@example.com")
    assert user.email == "test@example.com"
```

### 6. Mock External Dependencies

```python
# ✅ Good: Mock external API
@patch('requests.get')
def test_fetch_data(mock_get):
    mock_get.return_value.json.return_value = {"data": "test"}
    result = fetch_from_api()
    assert result == {"data": "test"}

# ❌ Bad: Calling real API (slow, unreliable)
def test_fetch_data():
    result = fetch_from_api()  # Makes real HTTP request
    assert "data" in result
```

### 7. Test Error Cases

```python
class TestUserValidation:
    def test_valid_user(self):
        """Test successful case."""
        user = create_user("valid")
        assert user is not None

    def test_empty_username_raises_error(self):
        """Test error case."""
        with pytest.raises(ValueError, match="Username cannot be empty"):
            create_user("")

    def test_invalid_email_raises_error(self):
        """Test validation error."""
        with pytest.raises(ValueError, match="Invalid email"):
            create_user("user", email="invalid")
```

---

## CI/CD Integration

### GitHub Actions

Tests run automatically via `.github/workflows/security-scan.yml`:

```yaml
jobs:
  pytest:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run tests with coverage
        run: |
          pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: pytest-check
      name: pytest-check
      entry: pytest
      language: system
      pass_filenames: false
      always_run: true
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'src'
# Solution: Install package in editable mode
pip install -e .
```

#### 2. Fixture Not Found

```bash
# Error: fixture 'my_fixture' not found
# Solution: Ensure fixture is in conftest.py or imported module
```

#### 3. Coverage Not Working

```bash
# Coverage shows 0%
# Solution: Check paths in pytest.ini match your package structure
[pytest]
addopts = --cov=src  # Update 'src' to your package name
```

#### 4. Tests Too Slow

```bash
# Run pytest-profiling to identify slow tests
pip install pytest-profiling
pytest --profile

# Use markers to skip slow tests in dev
pytest -m "not slow"
```

#### 5. Flaky Tests

```bash
# Install pytest-rerunfailures
pip install pytest-rerunfailures

# Rerun failed tests up to 3 times
pytest --reruns 3

# Mark specific test as flaky
@pytest.mark.flaky(reruns=3)
def test_flaky():
    pass
```

---

## Additional Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

### Example Tests
- [tests/test_example.py](../tests/test_example.py) - Comprehensive example tests
- [tests/conftest.py](../tests/conftest.py) - Shared fixtures

### Related Guides
- [README.md](../README.md) - Project overview
- [pyproject.toml](../pyproject.toml) - Test dependencies configuration
- [pytest.ini](../pytest.ini) - Pytest configuration

---

**Last Updated**: 2026-03-20
**Maintainer**: GitHub Copilot + Session Manager Agent
