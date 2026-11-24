"""
Example test module demonstrating best practices for testing.

This file serves as a template for writing tests in projects generated
from this template. It demonstrates:
- Unit tests with proper structure
- Integration tests with external dependencies
- Use of fixtures from conftest.py
- Various assertion patterns
- Mocking strategies
- Performance testing

Copy and adapt sections as needed for your own tests.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# ---------------------------------------------------------------------------
# Unit Tests - Fast, isolated tests with no external dependencies
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExampleUnitTests:
    """Example unit tests demonstrating basic patterns."""

    def test_simple_assertion(self):
        """Most basic test - simple assertion."""
        result = 2 + 2
        assert result == 4

    def test_string_operations(self):
        """Testing string operations."""
        text = "Hello, World!"
        assert "Hello" in text
        assert text.startswith("Hello")
        assert text.endswith("!")
        assert len(text) == 13

    def test_list_operations(self):
        """Testing list operations."""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert 3 in items
        assert items[0] == 1
        assert items[-1] == 5

    def test_dictionary_operations(self):
        """Testing dictionary operations."""
        data = {"name": "test", "version": "1.0.0", "active": True}
        assert data["name"] == "test"
        assert "version" in data
        assert data.get("missing", "default") == "default"

    def test_with_pytest_raises(self):
        """Testing exception handling."""
        with pytest.raises(ValueError, match="invalid"):
            raise ValueError("invalid value")

    def test_with_pytest_warns(self):
        """Testing warning messages."""
        import warnings

        with pytest.warns(UserWarning):
            warnings.warn("example warning", UserWarning, stacklevel=2)


# ---------------------------------------------------------------------------
# Fixture Usage Examples
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFixtureUsage:
    """Examples of using fixtures from conftest.py."""

    def test_temp_file_fixture(self, temp_file):
        """Using temp_file fixture to create test files."""
        test_file = temp_file("test.txt", "Hello, World!")
        assert test_file.exists()
        assert test_file.read_text() == "Hello, World!"

    def test_mock_env_fixture(self, mock_env):
        """Using mock_env fixture to set environment variables."""
        import os

        mock_env({"TEST_VAR": "test_value", "DEBUG": "true"})
        assert os.getenv("TEST_VAR") == "test_value"
        assert os.getenv("DEBUG") == "true"

    def test_tmp_path_builtin(self, tmp_path):
        """Using pytest's built-in tmp_path fixture."""
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()
        test_file = test_dir / "file.txt"
        test_file.write_text("content")
        assert test_file.exists()


# ---------------------------------------------------------------------------
# Mocking Examples
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestMockingExamples:
    """Examples of mocking for isolated testing."""

    def test_mock_function_call(self):
        """Mocking a function call."""
        mock_func = Mock(return_value=42)
        result = mock_func("test", param="value")

        assert result == 42
        mock_func.assert_called_once_with("test", param="value")

    def test_mock_with_side_effect(self):
        """Using side_effect for dynamic behavior."""
        mock_func = Mock(side_effect=[1, 2, 3])

        assert mock_func() == 1
        assert mock_func() == 2
        assert mock_func() == 3

    def test_patch_module_function(self):
        """Patching a module-level function."""
        with patch("builtins.open", MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "mocked"
            # Code that uses open() would get mocked data
            mock_open.assert_not_called()  # Not called yet in this test

    def test_mock_object_methods(self):
        """Mocking object methods."""
        mock_obj = MagicMock()
        mock_obj.method.return_value = "result"
        mock_obj.attribute = "value"

        assert mock_obj.method() == "result"
        assert mock_obj.attribute == "value"


# ---------------------------------------------------------------------------
# Parametrized Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParametrizedTests:
    """Examples of parametrized tests for multiple test cases."""

    @pytest.mark.parametrize(
        "input,expected",
        [
            (1, 2),
            (2, 4),
            (3, 6),
            (10, 20),
        ],
    )
    def test_double_function(self, input, expected):
        """Test function with multiple input/output pairs."""
        result = input * 2
        assert result == expected

    @pytest.mark.parametrize(
        "text,is_valid",
        [
            ("hello@example.com", True),
            ("invalid.email", False),
            ("@example.com", False),
            ("user@domain.co", True),
        ],
    )
    def test_email_validation(self, text, is_valid):
        """Test email validation with various inputs."""
        # Simple email validation
        has_at = "@" in text
        has_dot = "." in text
        result = has_at and has_dot and text.index("@") > 0
        assert result == is_valid


# ---------------------------------------------------------------------------
# Integration Tests - Tests requiring external services
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.requires_docker
class TestIntegrationExamples:
    """Example integration tests (marked to skip in certain environments)."""

    @pytest.mark.skip(reason="Example - requires actual Docker setup")
    def test_docker_container_interaction(self):
        """Example of testing Docker container interaction."""
        # This would test actual Docker operations
        pass

    @pytest.mark.skip(reason="Example - requires network")
    @pytest.mark.requires_network
    def test_api_call(self):
        """Example of testing external API calls."""
        # This would test actual API interactions
        pass


# ---------------------------------------------------------------------------
# Performance Tests
# ---------------------------------------------------------------------------


@pytest.mark.slow
class TestPerformanceExamples:
    """Example performance tests."""

    def test_operation_speed(self, benchmark_timer):
        """Test operation completes within time limit."""
        with benchmark_timer() as timer:
            # Simulate some work
            result = sum(range(10000))

        assert timer.elapsed < 0.1  # Should complete in < 100ms
        assert result == 49995000


# ---------------------------------------------------------------------------
# Security Tests
# ---------------------------------------------------------------------------


@pytest.mark.security
class TestSecurityExamples:
    """Example security-related tests."""

    def test_no_hardcoded_secrets(self, temp_file):
        """Ensure no secrets are hardcoded in config."""
        config = temp_file("config.ini", "[settings]\napi_key = ${API_KEY}\n")
        content = config.read_text()

        # Check for common secret patterns
        assert "password=" not in content.lower()
        assert "secret_key=" not in content.lower()
        assert "${" in content  # Using environment variables

    def test_secure_file_permissions(self, tmp_path):
        """Test that sensitive files have correct permissions."""
        secret_file = tmp_path / ".secrets" / "key.pem"
        secret_file.parent.mkdir(exist_ok=True)
        secret_file.write_text("secret")

        # On Unix systems, check permissions
        import stat

        secret_file.chmod(0o600)  # Owner read/write only
        mode = secret_file.stat().st_mode
        assert stat.S_IMODE(mode) == 0o600


# ---------------------------------------------------------------------------
# Smoke Tests - Quick validation tests
# ---------------------------------------------------------------------------


@pytest.mark.smoke
class TestSmokeExamples:
    """Example smoke tests for quick validation."""

    def test_imports_work(self):
        """Verify critical imports work."""
        import sys

        assert sys.version_info >= (3, 12)

    def test_config_file_exists(self, sample_config_file):
        """Verify config file is accessible."""
        assert sample_config_file.exists()
        content = sample_config_file.read_text()
        assert len(content) > 0


# ---------------------------------------------------------------------------
# Advanced Patterns
# ---------------------------------------------------------------------------


class TestAdvancedPatterns:
    """Advanced testing patterns."""

    @pytest.fixture
    def complex_fixture(self, tmp_path):
        """Example of a test-specific fixture."""

        class ComplexObject:
            def __init__(self, path):
                self.path = path
                self.data = {"initialized": True}

            def cleanup(self):
                self.data.clear()

        obj = ComplexObject(tmp_path)
        yield obj
        obj.cleanup()  # Teardown

    def test_with_complex_fixture(self, complex_fixture):
        """Using a custom complex fixture."""
        assert complex_fixture.data["initialized"] is True
        complex_fixture.data["test"] = "value"
        assert "test" in complex_fixture.data

    def test_context_manager(self):
        """Testing code that uses context managers."""
        from contextlib import contextmanager

        @contextmanager
        def managed_resource():
            resource = {"active": True}
            try:
                yield resource
            finally:
                resource["active"] = False

        with managed_resource() as resource:
            assert resource["active"] is True

        assert resource["active"] is False
