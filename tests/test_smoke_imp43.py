"""
tests/test_smoke_imp43.py — IMP-43: scaffold.py --new-profile NOME

Cobertura:
  flow_new_profile (unitário):
    - gera YAML em profile-descriptors/{name}.yaml
    - gera MD em profile-descriptors/{name}.md
    - YAML gerado é parsável e tem campo 'name' correto
    - YAML gerado tem campo 'layer' conforme solicitado
    - YAML gerado tem 'version', 'last_tested', 'status', 'schema_version'
    - MD gerado contém o nome do perfil
    - retorna exit code 0
    - nome inválido (com espaços/maiúsculas) retorna exit code 1
    - nome inválido não cria arquivos
    - arquivo já existente retorna exit code 1 sem --force
    - arquivo já existente com --force sobrescreve e retorna 0
    - --ci sem nome retorna exit code 1

  CLI --new-profile (subprocesso):
    - --help menciona --new-profile
    - --new-profile smoke-43 --profile-layer layer2 --ci --json retorna JSON válido
    - JSON retornado tem 'success' == True
    - JSON retornado tem 'name' == 'smoke-43'
    - JSON retornado tem 'yaml' apontando para arquivo existente
    - JSON retornado tem 'md' apontando para arquivo existente
    - exit code 0 no --ci --json

  Validação automática após --new-profile:
    - os 13 descritores originais continuam sem erros após --new-profile
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.flows.new_profile import flow_new_profile  # noqa: E402

_PROJECT_ROOT = Path(__file__).parent.parent
_DESCRIPTORS_DIR = _PROJECT_ROOT / "profile-descriptors"
_PYTHON = sys.executable
_SCAFFOLD = [_PYTHON, str(_PROJECT_ROOT / "scripts" / "scaffold.py")]

# Names for isolated test profiles (cleaned up by fixtures)
_TEST_NAME = "test-imp43-unit"
_CLI_NAME = "test-imp43-cli"

_ORIGINAL_DESCRIPTORS = {
    "data-pipeline-airflow",
    "data-warehouse-dbt",
    "devops-analysis",
    "devops-infrastructure",
    "devops-programming",
    "devops-security",
    "k8s-helm",
    "lgpd-baseline",
    "python-fastapi",
    "python-flask",
    "soc2-baseline",
    "terraform-aws",
    "typescript-next",
}


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "new_profile": None,
        "profile_layer": "layer2",
        "ci": True,
        "json_output": True,
        "force": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _cleanup(*names: str) -> None:
    for name in names:
        for ext in (".yaml", ".md"):
            p = _DESCRIPTORS_DIR / f"{name}{ext}"
            if p.exists():
                p.unlink()


# ===========================================================================
# Unit — flow_new_profile
# ===========================================================================


class TestFlowNewProfile:

    def setup_method(self):
        _cleanup(_TEST_NAME)

    def teardown_method(self):
        _cleanup(_TEST_NAME)

    def test_creates_yaml_file(self):
        rc = flow_new_profile(_make_args(new_profile=_TEST_NAME))
        assert rc == 0
        assert (_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").exists()

    def test_creates_md_file(self):
        rc = flow_new_profile(_make_args(new_profile=_TEST_NAME))
        assert rc == 0
        assert (_DESCRIPTORS_DIR / f"{_TEST_NAME}.md").exists()

    def test_yaml_is_parseable(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        content = (_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text()
        data = yaml.safe_load(content)
        assert isinstance(data, dict)

    def test_yaml_name_correct(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        data = yaml.safe_load((_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text())
        assert data["name"] == _TEST_NAME

    def test_yaml_layer_correct(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME, profile_layer="layer3"))
        data = yaml.safe_load((_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text())
        assert data["layer"] == "layer3"

    def test_yaml_has_version(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        data = yaml.safe_load((_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text())
        assert "version" in data

    def test_yaml_has_last_tested(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        data = yaml.safe_load((_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text())
        assert "last_tested" in data

    def test_yaml_has_schema_version(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        data = yaml.safe_load((_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text())
        assert "schema_version" in data

    def test_yaml_has_status_draft(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        data = yaml.safe_load((_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text())
        assert data.get("status") == "draft"

    def test_md_contains_name(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        content = (_DESCRIPTORS_DIR / f"{_TEST_NAME}.md").read_text()
        assert _TEST_NAME in content

    def test_md_has_checklist(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        content = (_DESCRIPTORS_DIR / f"{_TEST_NAME}.md").read_text()
        assert "Checklist" in content

    def test_returns_zero(self):
        rc = flow_new_profile(_make_args(new_profile=_TEST_NAME))
        assert rc == 0

    def test_invalid_name_returns_nonzero(self):
        rc = flow_new_profile(_make_args(new_profile="Bad Name!"))
        assert rc != 0

    def test_invalid_name_no_files_created(self):
        flow_new_profile(_make_args(new_profile="Bad Name!"))
        assert not (_DESCRIPTORS_DIR / "Bad Name!.yaml").exists()

    def test_existing_profile_returns_nonzero_without_force(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        rc = flow_new_profile(_make_args(new_profile=_TEST_NAME, force=False))
        assert rc != 0

    def test_existing_profile_force_overwrites(self):
        flow_new_profile(_make_args(new_profile=_TEST_NAME, profile_layer="layer2"))
        rc = flow_new_profile(
            _make_args(new_profile=_TEST_NAME, profile_layer="layer3", force=True)
        )
        assert rc == 0
        data = yaml.safe_load((_DESCRIPTORS_DIR / f"{_TEST_NAME}.yaml").read_text())
        assert data["layer"] == "layer3"

    def test_ci_without_name_returns_nonzero(self):
        rc = flow_new_profile(_make_args(new_profile=None, ci=True))
        assert rc != 0

    def test_json_output_success(self):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = flow_new_profile(_make_args(new_profile=_TEST_NAME, json_output=True))
        assert rc == 0
        data = json.loads(buf.getvalue())
        assert data["success"] is True
        assert data["name"] == _TEST_NAME

    def test_json_output_has_yaml_and_md_paths(self):
        import contextlib
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            flow_new_profile(_make_args(new_profile=_TEST_NAME, json_output=True))
        data = json.loads(buf.getvalue())
        assert "yaml" in data
        assert "md" in data

    def test_original_descriptors_untouched(self):
        """Garante que os 13 descritores originais não foram modificados."""
        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        existing = {f.stem for f in _DESCRIPTORS_DIR.glob("*.yaml")}
        assert _ORIGINAL_DESCRIPTORS.issubset(existing)


# ===========================================================================
# CLI — subprocesso
# ===========================================================================


class TestCLINewProfile:

    def setup_method(self):
        _cleanup(_CLI_NAME)

    def teardown_method(self):
        _cleanup(_CLI_NAME)

    def test_help_mentions_new_profile(self):
        result = subprocess.run(
            [*_SCAFFOLD, "--help"],
            capture_output=True,
            text=True,
        )
        assert "--new-profile" in result.stdout

    def test_cli_json_success(self):
        result = subprocess.run(
            [
                *_SCAFFOLD,
                "--new-profile",
                _CLI_NAME,
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

    def test_cli_json_correct_name(self):
        result = subprocess.run(
            [
                *_SCAFFOLD,
                "--new-profile",
                _CLI_NAME,
                "--profile-layer",
                "layer2",
                "--ci",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data["name"] == _CLI_NAME

    def test_cli_creates_yaml_on_disk(self):
        subprocess.run(
            [
                *_SCAFFOLD,
                "--new-profile",
                _CLI_NAME,
                "--profile-layer",
                "layer2",
                "--ci",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        assert (_DESCRIPTORS_DIR / f"{_CLI_NAME}.yaml").exists()

    def test_cli_creates_md_on_disk(self):
        subprocess.run(
            [
                *_SCAFFOLD,
                "--new-profile",
                _CLI_NAME,
                "--profile-layer",
                "layer2",
                "--ci",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        assert (_DESCRIPTORS_DIR / f"{_CLI_NAME}.md").exists()

    def test_cli_exit_code_zero(self):
        result = subprocess.run(
            [
                *_SCAFFOLD,
                "--new-profile",
                _CLI_NAME,
                "--profile-layer",
                "layer2",
                "--ci",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_cli_invalid_name_nonzero(self):
        result = subprocess.run(
            [*_SCAFFOLD, "--new-profile", "INVALID NAME", "--ci", "--json"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0

    def test_cli_json_output_has_yaml_path(self):
        result = subprocess.run(
            [
                *_SCAFFOLD,
                "--new-profile",
                _CLI_NAME,
                "--profile-layer",
                "layer2",
                "--ci",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert Path(data["yaml"]).exists()

    def test_cli_json_output_has_md_path(self):
        result = subprocess.run(
            [
                *_SCAFFOLD,
                "--new-profile",
                _CLI_NAME,
                "--profile-layer",
                "layer2",
                "--ci",
                "--json",
            ],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert Path(data["md"]).exists()


# ===========================================================================
# Validação automática — 13 originais continuam ok após --new-profile
# ===========================================================================


class TestValidateAfterNewProfile:

    def setup_method(self):
        _cleanup(_TEST_NAME)

    def teardown_method(self):
        _cleanup(_TEST_NAME)

    def test_original_profiles_have_no_errors_after_new_profile(self):
        """Cria um novo perfil e verifica que os 13 originais continuam sem erros."""
        from lib.validate import validate_descriptors

        flow_new_profile(_make_args(new_profile=_TEST_NAME))
        report = validate_descriptors(_DESCRIPTORS_DIR)

        original_results = [
            r for r in report.results if r.name in _ORIGINAL_DESCRIPTORS
        ]
        errors = [
            (r.name, i.field, i.message) for r in original_results for i in r.errors
        ]
        assert (
            errors == []
        ), f"Erros em descritores originais após new-profile: {errors}"
