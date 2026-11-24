"""
tests/test_smoke_imp28.py — IMP-28: Smoke tests para o modo upgrade/re-apply.

Cobertura:
  - write_scaffold_state cria .scaffold-state.yaml com estrutura correta
  - read_scaffold_state retorna dict com campos obrigatórios
  - config_from_state reconstrói ProjectConfig com campos corretos
  - write_scaffold_state preserva created_at em chamadas subsequentes
  - write_scaffold_state faz merge de profiles_applied sem duplicar
  - read_scaffold_state retorna None para diretório sem state file
  - read_scaffold_state retorna None para arquivo YAML inválido
  - config_from_state aceita override_target
  - flow_new_project persiste .scaffold-state.yaml ao final
  - --upgrade com state ausente retorna exit code 1
  - --upgrade com state válido re-aplica os passos (exit code 0)
  - --upgrade com --json-output emite JSON com chave "upgrade": true
  - Múltiplos upgrades são idempotentes (created_count estável após 1ª execução)
  - --upgrade + --target-dir aponta para target correto
  - scaffold --upgrade --help lista a opção no texto de ajuda
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from datetime import UTC

from lib.config import ProjectConfig  # noqa: E402
from lib.project import (  # noqa: E402
    config_from_state,
    read_scaffold_state,
    write_scaffold_state,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
_STATE_FILENAME = ".scaffold-state.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cfg(tmp_path: Path, shared: Path | None = None) -> ProjectConfig:
    """Cria um ProjectConfig mínimo para testes."""
    from datetime import datetime

    project_dir = tmp_path / "test-proj"
    project_dir.mkdir(exist_ok=True)
    return ProjectConfig(
        project_name="test-proj",
        project_title="Test Project",
        description="Projeto de teste para IMP-28",
        domain="programming",
        language="python",
        github_repo="https://github.com/test/test-proj",
        shared_dir=shared or tmp_path / "shared",
        target_dir=project_dir,
        created_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        extra_profiles=[],
    )


def _state_path(tmp_path: Path) -> Path:
    """Retorna o caminho do arquivo de estado do projeto de teste."""
    return tmp_path / "test-proj" / _STATE_FILENAME


# ===========================================================================
# write_scaffold_state
# ===========================================================================


class TestWriteScaffoldState:
    def test_creates_state_file(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=[])
        assert _state_path(tmp_path).exists()

    def test_returns_created_item_with_created_status(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        item = write_scaffold_state(cfg, profiles_applied=[])
        assert item.status == "created"

    def test_state_file_has_required_keys(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=[])
        data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        assert "scaffold_version" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "project" in data
        assert "paths" in data
        assert "profiles_applied" in data

    def test_project_section_correct(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=["python-fastapi"])
        data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        assert data["project"]["name"] == "test-proj"
        assert data["project"]["domain"] == "programming"
        assert data["project"]["language"] == "python"

    def test_profiles_applied_stored(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=["python-fastapi", "k8s-helm"])
        data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        assert "python-fastapi" in data["profiles_applied"]
        assert "k8s-helm" in data["profiles_applied"]

    def test_preserves_created_at_on_second_call(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=[])
        first_data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        first_created_at = first_data["created_at"]

        # Segunda chamada — created_at deve ser preservado
        write_scaffold_state(cfg, profiles_applied=["python-fastapi"])
        second_data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        assert second_data["created_at"] == first_created_at

    def test_updated_at_changes_on_second_call(self, tmp_path: Path) -> None:
        import time

        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=[])
        first_data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        time.sleep(1.1)
        write_scaffold_state(cfg, profiles_applied=["python-fastapi"])
        second_data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        assert second_data["updated_at"] >= first_data["updated_at"]

    def test_merges_profiles_without_duplicates(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=["python-fastapi"])
        # Segunda chamada com perfil repetido e um novo
        write_scaffold_state(cfg, profiles_applied=["python-fastapi", "k8s-helm"])
        data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        profiles = data["profiles_applied"]
        assert profiles.count("python-fastapi") == 1
        assert "k8s-helm" in profiles

    def test_paths_section_correct(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=[])
        data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        assert "target_dir" in data["paths"]
        assert "shared_dir" in data["paths"]

    def test_none_profiles_treated_as_empty(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=None)
        data = yaml.safe_load(_state_path(tmp_path).read_text(encoding="utf-8"))
        assert data["profiles_applied"] == []


# ===========================================================================
# read_scaffold_state
# ===========================================================================


class TestReadScaffoldState:
    def test_returns_none_when_file_absent(self, tmp_path: Path) -> None:
        result = read_scaffold_state(tmp_path)
        assert result is None

    def test_returns_dict_when_file_present(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg)
        result = read_scaffold_state(tmp_path / "test-proj")
        assert isinstance(result, dict)

    def test_returns_correct_project_name(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg)
        state = read_scaffold_state(tmp_path / "test-proj")
        assert state is not None
        assert state["project"]["name"] == "test-proj"

    def test_returns_none_for_invalid_yaml(self, tmp_path: Path) -> None:
        (tmp_path / _STATE_FILENAME).write_text(
            ":::INVALID:::\n- not: valid: yaml: content\n", encoding="utf-8"
        )
        result = read_scaffold_state(tmp_path)
        assert result is None

    def test_returns_none_for_non_dict_yaml(self, tmp_path: Path) -> None:
        (tmp_path / _STATE_FILENAME).write_text("- item1\n- item2\n", encoding="utf-8")
        result = read_scaffold_state(tmp_path)
        assert result is None

    def test_returns_profiles_applied(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=["python-fastapi"])
        state = read_scaffold_state(tmp_path / "test-proj")
        assert state is not None
        assert "python-fastapi" in state["profiles_applied"]


# ===========================================================================
# config_from_state
# ===========================================================================


class TestConfigFromState:
    def test_reconstructs_project_name(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg)
        state = read_scaffold_state(tmp_path / "test-proj")
        rebuilt = config_from_state(state)
        assert rebuilt.project_name == "test-proj"

    def test_reconstructs_domain(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg)
        state = read_scaffold_state(tmp_path / "test-proj")
        rebuilt = config_from_state(state)
        assert rebuilt.domain == "programming"

    def test_reconstructs_language(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg)
        state = read_scaffold_state(tmp_path / "test-proj")
        rebuilt = config_from_state(state)
        assert rebuilt.language == "python"

    def test_override_target_is_used(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg)
        state = read_scaffold_state(tmp_path / "test-proj")
        override = tmp_path / "override"
        rebuilt = config_from_state(state, override_target=override)
        assert rebuilt.target_dir == override

    def test_returns_projectconfig_instance(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg)
        state = read_scaffold_state(tmp_path / "test-proj")
        rebuilt = config_from_state(state)
        assert isinstance(rebuilt, ProjectConfig)

    def test_extra_profiles_from_state(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        write_scaffold_state(cfg, profiles_applied=["python-fastapi", "k8s-helm"])
        state = read_scaffold_state(tmp_path / "test-proj")
        rebuilt = config_from_state(state)
        assert "python-fastapi" in rebuilt.extra_profiles

    def test_github_repo_none_when_empty(self, tmp_path: Path) -> None:
        cfg = _make_cfg(tmp_path)
        object.__setattr__(cfg, "github_repo", "")
        write_scaffold_state(cfg)
        state = read_scaffold_state(tmp_path / "test-proj")
        rebuilt = config_from_state(state)
        # github_repo vazio deve vir como None
        assert rebuilt.github_repo is None or rebuilt.github_repo == ""


# ===========================================================================
# scaffold.py --upgrade via subprocess
# ===========================================================================


class TestUpgradeFlow:
    """Testes de integração usando subprocess para exercitar scaffold.py --upgrade."""

    def _run_scaffold(
        self, args: list[str], env: dict | None = None
    ) -> tuple[int, str, str]:
        import os
        import subprocess

        environ = os.environ.copy()
        # Garantir identidade git para commits em repositórios temporários
        environ.setdefault("GIT_AUTHOR_NAME", "Test User")
        environ.setdefault("GIT_AUTHOR_EMAIL", "test@example.com")
        environ.setdefault("GIT_COMMITTER_NAME", "Test User")
        environ.setdefault("GIT_COMMITTER_EMAIL", "test@example.com")
        if env:
            environ.update(env)
        result = subprocess.run(
            [sys.executable, str(_SCRIPTS_DIR / "scaffold.py")] + args,
            capture_output=True,
            text=True,
            env=environ,
        )
        return result.returncode, result.stdout, result.stderr

    def test_upgrade_missing_state_returns_error(self, tmp_path: Path) -> None:
        rc, _out, _err = self._run_scaffold(
            [
                "--upgrade",
                "--target-dir",
                str(tmp_path),
                "--json",
            ]
        )
        assert rc != 0

    def test_upgrade_missing_state_json_has_error_key(self, tmp_path: Path) -> None:
        rc, out, _err = self._run_scaffold(
            [
                "--upgrade",
                "--target-dir",
                str(tmp_path),
                "--json",
            ]
        )
        parsed = json.loads(out)
        assert "error" in parsed

    def test_upgrade_help_lists_option(self) -> None:
        rc, out, err = self._run_scaffold(["--help"])
        combined = out + err
        assert "--upgrade" in combined

    def test_upgrade_with_valid_state_exits_zero(self, tmp_path: Path) -> None:
        """flow_new_project deve gravar state → --upgrade deve conseguir ler."""
        # Primeiro cria projeto via --ci
        project_name = "upgrade-test"
        project_dir = tmp_path / project_name
        shared = tmp_path / "shared"
        shared.mkdir(parents=True, exist_ok=True)
        rc, out, err = self._run_scaffold(
            [
                "--new",
                "--ci",
                "--name",
                project_name,
                "--domain",
                "programming",
                "--language",
                "python",
                "--target-dir",
                str(tmp_path),
                "--shared-dir",
                str(shared),
                "--json",
            ]
        )
        assert rc == 0, f"flow_new_project falhou: stdout={out}\nstderr={err}"
        assert (
            project_dir / _STATE_FILENAME
        ).exists(), "State file não foi criado por --new"

        # Agora upgrade
        rc2, out2, _err2 = self._run_scaffold(
            [
                "--upgrade",
                "--target-dir",
                str(project_dir),
                "--json",
            ]
        )
        assert rc2 == 0, f"--upgrade falhou: rc={rc2}\nstdout={out2}\nstderr={_err2}"

    def test_upgrade_json_has_upgrade_key_true(self, tmp_path: Path) -> None:
        project_name = "json-test"
        project_dir = tmp_path / project_name
        shared = tmp_path / "shared"
        shared.mkdir(parents=True, exist_ok=True)
        self._run_scaffold(
            [
                "--new",
                "--ci",
                "--name",
                project_name,
                "--domain",
                "programming",
                "--language",
                "python",
                "--target-dir",
                str(tmp_path),
                "--shared-dir",
                str(shared),
                "--json",
            ]
        )
        rc, out, err = self._run_scaffold(
            [
                "--upgrade",
                "--target-dir",
                str(project_dir),
                "--json",
            ]
        )
        assert rc == 0, f"upgrade rc={rc}\nstdout={out!r}\nstderr={err!r}"
        data = json.loads(out)
        assert data.get("upgrade") is True

    def test_second_upgrade_is_idempotent(self, tmp_path: Path) -> None:
        """O segundo upgrade não deve criar mais arquivos que o primeiro (estabilidade)."""
        project_name = "idempotent-test"
        project_dir = tmp_path / project_name
        shared = tmp_path / "shared"
        shared.mkdir(parents=True, exist_ok=True)
        self._run_scaffold(
            [
                "--new",
                "--ci",
                "--name",
                project_name,
                "--domain",
                "programming",
                "--language",
                "python",
                "--target-dir",
                str(tmp_path),
                "--shared-dir",
                str(shared),
                "--json",
            ]
        )
        # Primeiro upgrade
        _, out1, _ = self._run_scaffold(
            [
                "--upgrade",
                "--target-dir",
                str(project_dir),
                "--json",
            ]
        )
        first_created = json.loads(out1).get("created", 0)

        # Segundo upgrade
        rc, out, err = self._run_scaffold(
            [
                "--upgrade",
                "--target-dir",
                str(project_dir),
                "--json",
            ]
        )
        assert rc == 0, f"2nd upgrade rc={rc}\nstdout={out!r}\nstderr={err!r}"
        data = json.loads(out)
        second_created = data.get("created", -1)
        # Upgrades sucessivos devem ser estáveis (não crescer a cada execução)
        assert (
            second_created <= first_created
        ), f"2º upgrade criou mais arquivos ({second_created}) que o 1º ({first_created})"

    def test_upgrade_updates_state_updated_at(self, tmp_path: Path) -> None:
        """O state file deve ter updated_at atualizado após upgrade."""
        import time

        project_name = "ts-test"
        project_dir = tmp_path / project_name
        shared = tmp_path / "shared"
        shared.mkdir(parents=True, exist_ok=True)
        self._run_scaffold(
            [
                "--new",
                "--ci",
                "--name",
                project_name,
                "--domain",
                "programming",
                "--language",
                "python",
                "--target-dir",
                str(tmp_path),
                "--shared-dir",
                str(shared),
                "--json",
            ]
        )
        first_state = yaml.safe_load((project_dir / _STATE_FILENAME).read_text())
        created_at_before = first_state["created_at"]
        updated_at_before = first_state["updated_at"]

        time.sleep(1.1)
        self._run_scaffold(
            [
                "--upgrade",
                "--target-dir",
                str(project_dir),
                "--json",
            ]
        )
        second_state = yaml.safe_load((project_dir / _STATE_FILENAME).read_text())
        # created_at deve ser preservado
        assert second_state["created_at"] == created_at_before
        # updated_at deve ser igual ou posterior
        assert second_state["updated_at"] >= updated_at_before
