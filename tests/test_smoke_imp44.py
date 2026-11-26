"""
tests/test_smoke_imp44.py — IMP-44: Subcomandos CLI (scaffold.py)

Cobertura:
  _translate_subcommand (unitário):
    - subcomando sem valor: 'validate' → ['--validate']
    - subcomando sem valor: 'check' → ['--check']
    - subcomando sem valor: 'list-profiles' → ['--list-profiles']
    - subcomando sem valor: 'upgrade' → ['--upgrade']
    - subcomando sem valor: 'publish' → ['--publish']
    - subcomando sem valor: 'new' → ['--new']
    - subcomando sem valor: 'infra' → ['--infra']
    - subcomando sem valor: 'dry-run' → ['--dry-run']
    - subcomando com valor: 'compose profiles' → ['--compose', 'profiles']
    - subcomando com valor: 'new-profile my-name' → ['--new-profile', 'my-name']
    - subcomando com valor: 'release 1.2.0' → ['--release', '1.2.0']
    - flags extras depois do subcomando são preservadas
    - argv vazio → retorna ([], False) sem erros
    - token desconhecido → retorna sem tradução (was_subcommand=False)

  _warn_legacy_flags (unitário):
    - --validate emite DeprecationWarning
    - --list-profiles emite DeprecationWarning
    - --new emite DeprecationWarning
    - subcomando 'validate' (sem --) NÃO emite DeprecationWarning

  CLI subcomandos (subprocesso):
    - scaffold.py list-profiles --json retorna lista de perfis válida
    - scaffold.py validate --json retorna JSON com valid=True
    - scaffold.py validate --json exit code 0
    - scaffold.py list-profiles --json exit code 0
    - scaffold.py check (exit code 0 ou 1, mas não crash)
    - scaffold.py dry-run --ci --name x --domain programming --language python --json
    - scaffold.py new-profile NAME --profile-layer layer2 --ci --json

  Compatibilidade legada (subprocesso):
    - --list-profiles --json ainda funciona (exit 0, JSON válido)
    - --validate --json ainda funciona (exit 0, JSON válido)
    - --list-profiles emite DeprecationWarning em stderr
    - --validate emite DeprecationWarning em stderr

  Dois caminhos produzem resultado idêntico:
    - 'list-profiles --json' == '--list-profiles --json' (output JSON)
    - 'validate --json' == '--validate --json' (output JSON)
"""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Re-import after path insert to get the module fresh
from scaffold import (  # noqa: E402
    _SUBCOMMAND_MAP,
    _SUBCOMMAND_VALUE,
    _translate_subcommand,
    _warn_legacy_flags,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_PYTHON = sys.executable
_SCAFFOLD = [_PYTHON, str(_PROJECT_ROOT / "scripts" / "scaffold.py")]
_DESCRIPTORS_DIR = _PROJECT_ROOT / "scaffold" / "profiles"
_TEST_PROFILE = "test-imp44-cli"


def _cleanup(*names: str) -> None:
    for name in names:
        for ext in (".yaml", ".md"):
            p = _DESCRIPTORS_DIR / f"{name}{ext}"
            if p.exists():
                p.unlink()


# ===========================================================================
# Unit — _translate_subcommand
# ===========================================================================


class TestTranslateSubcommand:
    @pytest.mark.parametrize(
        "subcmd,expected_flag",
        [
            ("validate", "--validate"),
            ("check", "--check"),
            ("list-profiles", "--list-profiles"),
            ("upgrade", "--upgrade"),
            ("publish", "--publish"),
            ("new", "--new"),
            ("infra", "--infra"),
            ("dry-run", "--dry-run"),
        ],
    )
    def test_simple_subcommand_translated(self, subcmd, expected_flag):
        result, was_sub = _translate_subcommand([subcmd])
        assert was_sub is True
        assert result[0] == expected_flag

    def test_compose_takes_value(self):
        result, was_sub = _translate_subcommand(["compose", "my-profiles"])
        assert was_sub is True
        assert result == ["--compose", "my-profiles"]

    def test_new_profile_takes_value(self):
        result, was_sub = _translate_subcommand(["new-profile", "my-name"])
        assert was_sub is True
        assert result == ["--new-profile", "my-name"]

    def test_release_takes_value(self):
        result, was_sub = _translate_subcommand(["release", "1.2.0"])
        assert was_sub is True
        assert result == ["--release", "1.2.0"]

    def test_extra_flags_preserved_simple(self):
        result, was_sub = _translate_subcommand(["validate", "--json"])
        assert was_sub is True
        assert "--validate" in result
        assert "--json" in result

    def test_extra_flags_preserved_with_value(self):
        result, was_sub = _translate_subcommand(
            ["new-profile", "my-name", "--profile-layer", "layer2"]
        )
        assert was_sub is True
        assert result == ["--new-profile", "my-name", "--profile-layer", "layer2"]

    def test_ci_flag_preserved(self):
        result, was_sub = _translate_subcommand(["list-profiles", "--json", "--ci"])
        assert was_sub is True
        assert "--list-profiles" in result
        assert "--json" in result
        assert "--ci" in result

    def test_empty_argv_returns_false(self):
        result, was_sub = _translate_subcommand([])
        assert was_sub is False
        assert result == []

    def test_unknown_token_returns_false(self):
        result, was_sub = _translate_subcommand(["--validate"])
        assert was_sub is False

    def test_unknown_word_returns_false(self):
        result, was_sub = _translate_subcommand(["frobnicate"])
        assert was_sub is False

    def test_dry_run_with_fields(self):
        argv = [
            "dry-run",
            "--ci",
            "--name",
            "foo",
            "--domain",
            "programming",
            "--language",
            "python",
            "--json",
        ]
        result, was_sub = _translate_subcommand(argv)
        assert was_sub is True
        assert "--dry-run" in result
        assert "--ci" in result
        assert "--name" in result

    def test_subcommand_map_complete(self):
        """Verify all required subcommands from IMP-44 spec are present."""
        required = {
            "new",
            "check",
            "list-profiles",
            "validate",
            "dry-run",
            "compose",
            "upgrade",
            "publish",
            "new-profile",
            "infra",
        }
        assert required.issubset(_SUBCOMMAND_MAP.keys())

    def test_value_subcommands_set(self):
        """Verify value-taking subcommands are registered."""
        assert "compose" in _SUBCOMMAND_VALUE
        assert "new-profile" in _SUBCOMMAND_VALUE
        assert "release" in _SUBCOMMAND_VALUE


# ===========================================================================
# Unit — _warn_legacy_flags
# ===========================================================================


class TestWarnLegacyFlags:
    def test_validate_flag_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_legacy_flags(["--validate"])
        assert any("--validate" in str(x.message) for x in w)
        assert any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_list_profiles_flag_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_legacy_flags(["--list-profiles"])
        assert any("--list-profiles" in str(x.message) for x in w)

    def test_new_flag_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_legacy_flags(["--new"])
        assert any("--new" in str(x.message) for x in w)

    def test_subcommand_without_dashes_no_warning(self):
        """'validate' (subcommand form) must NOT trigger a deprecation warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_legacy_flags(["validate"])  # no leading --
        assert not any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_no_flags_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_legacy_flags(["--ci", "--name", "foo"])
        assert not any(issubclass(x.category, DeprecationWarning) for x in w)

    def test_multiple_flags_warn_each(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_legacy_flags(["--validate", "--json", "--list-profiles"])
        messages = [
            str(x.message) for x in w if issubclass(x.category, DeprecationWarning)
        ]
        assert any("--validate" in m for m in messages)
        assert any("--list-profiles" in m for m in messages)

    def test_deprecation_message_contains_suggestion(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _warn_legacy_flags(["--validate"])
        depr = [x for x in w if issubclass(x.category, DeprecationWarning)]
        assert depr
        assert "scaffold.py validate" in str(depr[0].message)


# ===========================================================================
# CLI subcomandos (subprocesso)
# ===========================================================================


class TestCLISubcommands:
    def test_list_profiles_subcommand_returns_json(self):
        result = subprocess.run(
            [*_SCAFFOLD, "list-profiles", "--json"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_profiles_subcommand_exit_zero(self):
        result = subprocess.run(
            [*_SCAFFOLD, "list-profiles", "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_validate_subcommand_json_valid(self):
        result = subprocess.run(
            [*_SCAFFOLD, "validate", "--json"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data["valid"] is True

    def test_validate_subcommand_exit_zero(self):
        result = subprocess.run(
            [*_SCAFFOLD, "validate", "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_validate_subcommand_no_deprecation_warning(self):
        result = subprocess.run(
            [*_SCAFFOLD, "validate", "--json"],
            capture_output=True,
            text=True,
        )
        assert "DeprecationWarning" not in result.stderr

    def test_list_profiles_subcommand_no_deprecation_warning(self):
        result = subprocess.run(
            [*_SCAFFOLD, "list-profiles", "--json"],
            capture_output=True,
            text=True,
        )
        assert "DeprecationWarning" not in result.stderr

    def test_dry_run_subcommand_json(self):
        result = subprocess.run(
            [
                *_SCAFFOLD,
                "dry-run",
                "--ci",
                "--name",
                "imp44-dry",
                "--domain",
                "programming",
                "--language",
                "python",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data.get("dry_run") is True

    def test_check_subcommand_no_crash(self):
        result = subprocess.run(
            [*_SCAFFOLD, "check"],
            capture_output=True,
            text=True,
        )
        # exit code 0 (all links ok) or 1 (missing links) — both acceptable
        assert result.returncode in (0, 1)

    def test_new_profile_subcommand_json(self):
        _cleanup(_TEST_PROFILE)
        try:
            result = subprocess.run(
                [
                    *_SCAFFOLD,
                    "new-profile",
                    _TEST_PROFILE,
                    "--profile-layer",
                    "layer2",
                    "--ci",
                    "--json",
                ],
                capture_output=True,
                text=True,
            )
            data = json.loads(result.stdout)
            assert data["success"] is True
            assert data["name"] == _TEST_PROFILE
        finally:
            _cleanup(_TEST_PROFILE)


# ===========================================================================
# Compatibilidade legada (subprocesso)
# ===========================================================================


class TestLegacyFlagCompatibility:
    def test_legacy_list_profiles_json_still_works(self):
        result = subprocess.run(
            [*_SCAFFOLD, "--list-profiles", "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_legacy_validate_json_still_works(self):
        result = subprocess.run(
            [*_SCAFFOLD, "--validate", "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True

    def test_legacy_list_profiles_emits_deprecation(self):
        result = subprocess.run(
            [*_SCAFFOLD, "--list-profiles", "--json"],
            capture_output=True,
            text=True,
        )
        assert (
            "DeprecationWarning" in result.stderr
            or "deprecated" in result.stderr.lower()
        )

    def test_legacy_validate_emits_deprecation(self):
        result = subprocess.run(
            [*_SCAFFOLD, "--validate", "--json"],
            capture_output=True,
            text=True,
        )
        assert (
            "DeprecationWarning" in result.stderr
            or "deprecated" in result.stderr.lower()
        )


# ===========================================================================
# Equivalência: subcommand == legacy flag (output idêntico)
# ===========================================================================


class TestSubcommandEquivalence:
    def test_list_profiles_output_identical(self):
        sub = subprocess.run(
            [*_SCAFFOLD, "list-profiles", "--json"],
            capture_output=True,
            text=True,
        )
        leg = subprocess.run(
            [*_SCAFFOLD, "--list-profiles", "--json"],
            capture_output=True,
            text=True,
        )
        assert json.loads(sub.stdout) == json.loads(leg.stdout)

    def test_validate_output_identical(self):
        sub = subprocess.run(
            [*_SCAFFOLD, "validate", "--json"],
            capture_output=True,
            text=True,
        )
        leg = subprocess.run(
            [*_SCAFFOLD, "--validate", "--json"],
            capture_output=True,
            text=True,
        )
        assert json.loads(sub.stdout) == json.loads(leg.stdout)
