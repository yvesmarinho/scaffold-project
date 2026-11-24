"""
tests/test_smoke_imp35.py — IMP-35: Testes de smoke para o processo de release automático.

Cobertura:
  Validação semver:
    - validate_semver("1.0.0") aceita
    - validate_semver("2.10.3") aceita
    - validate_semver("0.0.1") aceita
    - validate_semver("1.0.0-alpha") aceita (pre-release)
    - validate_semver("v1.0.0") aceita (prefixo v removido)
    - validate_semver("bad") rejeita
    - validate_semver("1.0") rejeita (falta patch)
    - validate_semver("1.0.0.0") rejeita (quatro segmentos)

  close_unreleased():
    - Fecha seção [Unreleased] corretamente → [X.Y.Z] — DATE
    - Adiciona nova seção [Unreleased] vazia acima
    - Retorna o conteúdo do bloco da versão
    - Lança ValueError se [Unreleased] não existe
    - Lança ValueError se [Unreleased] está vazia

  bump_scaffold_version():
    - Atualiza corretamente SCAFFOLD_VERSION em config.py simulado
    - Retorna a versão anterior
    - Lança ValueError se SCAFFOLD_VERSION não existe no arquivo

  run_release() dry-run:
    - dry_run=True retorna ReleaseResult com success=True
    - dry_run=True não grava arquivos
    - dry_run=True tem todos os steps esperados
    - dry_run=False com semver inválido retorna success=False com erro

  CLI --release --dry-run:
    - scaffold.py --release 9.9.9 --dry-run retorna exit 0
    - scaffold.py --release 9.9.9 --dry-run --json tem success=True
    - scaffold.py --release sem VERSION retorna exit 1
    - scaffold.py --release INVALID_VERSION --dry-run retorna exit 1
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.release import (  # noqa: E402
    bump_scaffold_version,
    close_unreleased,
    run_release,
    validate_semver,
)

_PROJECT_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
_PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tmp_file(suffix: str) -> Path:
    """Arquivo temporário criado de forma segura (substitui tempfile.mktemp)."""
    fd, nome = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    return Path(nome)


def _mock_changelog(lines: str) -> Path:
    """Cria um CHANGELOG.md temporário com o conteúdo dado."""
    tmp = _tmp_file(".md")
    tmp.write_text(lines, encoding="utf-8")
    return tmp


def _mock_config_py(version: str = "1.0.0") -> Path:
    """Cria um config.py temporário com SCAFFOLD_VERSION definido."""
    tmp = _tmp_file(".py")
    tmp.write_text(
        textwrap.dedent(f"""\
            # scripts/lib/config.py
            SCAFFOLD_VERSION = "{version}"
            SOME_OTHER_VAR = "value"
        """),
        encoding="utf-8",
    )
    return Path(tmp)


# ---------------------------------------------------------------------------
# Validação semver
# ---------------------------------------------------------------------------


class TestValidateSemver:
    def test_tres_segmentos_simples(self):
        assert validate_semver("1.0.0") is True

    def test_numeros_maiores(self):
        assert validate_semver("2.10.3") is True

    def test_patch_zero(self):
        assert validate_semver("0.0.1") is True

    def test_prerelease(self):
        assert validate_semver("1.0.0-alpha") is True

    def test_prefixo_v_aceito(self):
        assert validate_semver("v1.0.0") is True

    def test_string_invalida(self):
        assert validate_semver("bad") is False

    def test_dois_segmentos(self):
        assert validate_semver("1.0") is False

    def test_quatro_segmentos(self):
        assert validate_semver("1.0.0.0") is False

    def test_com_espacos(self):
        assert validate_semver("1.0.0 ") is False


# ---------------------------------------------------------------------------
# close_unreleased()
# ---------------------------------------------------------------------------


class TestCloseUnreleased:
    _CHANGELOG_OK = textwrap.dedent("""\
        # Changelog

        ## [Unreleased]

        ### Added
        - Feature X implementada

        ## [1.0.0] — 2026-01-01

        ### Added
        - Release inicial
    """)

    _CHANGELOG_EMPTY_UNRELEASED = textwrap.dedent("""\
        # Changelog

        ## [Unreleased]

        ## [1.0.0] — 2026-01-01

        ### Added
        - Release inicial
    """)

    _CHANGELOG_NO_UNRELEASED = textwrap.dedent("""\
        # Changelog

        ## [1.0.0] — 2026-01-01

        ### Added
        - Release inicial
    """)

    def test_fecha_secao_corretamente(self):
        cl = _mock_changelog(self._CHANGELOG_OK)
        try:
            close_unreleased(cl, "1.1.0", "2026-03-14")
            text = cl.read_text(encoding="utf-8")
            assert "## [1.1.0] — 2026-03-14" in text
        finally:
            cl.unlink(missing_ok=True)

    def test_adiciona_unreleased_vazio_acima(self):
        cl = _mock_changelog(self._CHANGELOG_OK)
        try:
            close_unreleased(cl, "1.1.0", "2026-03-14")
            text = cl.read_text(encoding="utf-8")
            # [Unreleased] deve preceder [1.1.0]
            idx_unreleased = text.index("## [Unreleased]")
            idx_new_version = text.index("## [1.1.0]")
            assert idx_unreleased < idx_new_version
        finally:
            cl.unlink(missing_ok=True)

    def test_retorna_conteudo_bloco(self):
        cl = _mock_changelog(self._CHANGELOG_OK)
        try:
            block = close_unreleased(cl, "1.1.0", "2026-03-14")
            assert "Feature X implementada" in block
        finally:
            cl.unlink(missing_ok=True)

    def test_levanta_se_sem_unreleased(self):
        cl = _mock_changelog(self._CHANGELOG_NO_UNRELEASED)
        try:
            with pytest.raises(ValueError, match="Unreleased"):
                close_unreleased(cl, "1.1.0", "2026-03-14")
        finally:
            cl.unlink(missing_ok=True)

    def test_levanta_se_unreleased_vazia(self):
        cl = _mock_changelog(self._CHANGELOG_EMPTY_UNRELEASED)
        try:
            with pytest.raises(ValueError, match="vazi"):
                close_unreleased(cl, "1.1.0", "2026-03-14")
        finally:
            cl.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# bump_scaffold_version()
# ---------------------------------------------------------------------------


class TestBumpScaffoldVersion:
    def test_atualiza_versao_corretamente(self):
        cfg = _mock_config_py("1.0.0")
        try:
            bump_scaffold_version(cfg, "1.1.0")
            text = cfg.read_text(encoding="utf-8")
            assert 'SCAFFOLD_VERSION = "1.1.0"' in text
        finally:
            cfg.unlink(missing_ok=True)

    def test_retorna_versao_anterior(self):
        cfg = _mock_config_py("1.0.0")
        try:
            old = bump_scaffold_version(cfg, "2.0.0")
            assert old == "1.0.0"
        finally:
            cfg.unlink(missing_ok=True)

    def test_nao_toca_outras_variaveis(self):
        cfg = _mock_config_py("1.0.0")
        try:
            bump_scaffold_version(cfg, "2.0.0")
            text = cfg.read_text(encoding="utf-8")
            assert 'SOME_OTHER_VAR = "value"' in text
        finally:
            cfg.unlink(missing_ok=True)

    def test_levanta_se_campo_ausente(self):
        tmp = _tmp_file(".py")
        tmp.write_text("# sem scaffold\nSOME_VAR = 1\n", encoding="utf-8")
        try:
            with pytest.raises(ValueError, match="SCAFFOLD_VERSION"):
                bump_scaffold_version(tmp, "1.0.0")
        finally:
            tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# run_release() — dry-run (sem git, sem escrita real)
# ---------------------------------------------------------------------------


class TestRunReleaseDryRun:
    """Testes que usam dry_run=True para não tocar em arquivos reais."""

    def _make_fake_root(self, version: str = "1.0.0") -> Path:
        """Cria um diretório temporário com CHANGELOG.md e config.py mínimos."""
        root = Path(tempfile.mkdtemp())
        # CHANGELOG
        (root / "CHANGELOG.md").write_text(
            textwrap.dedent("""\
                # Changelog

                ## [Unreleased]

                ### Added
                - Feature fake para dry-run

                ## [1.0.0] — 2026-01-01

                ### Added
                - Release inicial
            """),
            encoding="utf-8",
        )
        # config.py
        scripts_lib = root / "scripts" / "lib"
        scripts_lib.mkdir(parents=True)
        (scripts_lib / "config.py").write_text(
            f'SCAFFOLD_VERSION = "{version}"\n',
            encoding="utf-8",
        )
        # git init mínimo para git_tag_exists não falhar
        subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=str(root),
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=str(root),
            check=True,
        )
        return root

    def test_dry_run_success_true(self):
        root = self._make_fake_root()
        result = run_release("1.1.0", project_root=root, dry_run=True)
        assert result.success is True

    def test_dry_run_nao_modifica_changelog(self):
        root = self._make_fake_root()
        original = (root / "CHANGELOG.md").read_text()
        run_release("1.1.0", project_root=root, dry_run=True)
        assert (root / "CHANGELOG.md").read_text() == original

    def test_dry_run_nao_modifica_config(self):
        root = self._make_fake_root("1.0.0")
        original = (root / "scripts" / "lib" / "config.py").read_text()
        run_release("1.1.0", project_root=root, dry_run=True)
        assert (root / "scripts" / "lib" / "config.py").read_text() == original

    def test_dry_run_steps_presentes(self):
        root = self._make_fake_root()
        result = run_release("1.1.0", project_root=root, dry_run=True)
        joined = " ".join(result.steps_done)
        assert "semver" in joined
        assert "1.1.0" in joined

    def test_semver_invalido_retorna_failure(self):
        root = self._make_fake_root()
        result = run_release("nao_semver", project_root=root, dry_run=True)
        assert result.success is False
        assert result.errors


# ---------------------------------------------------------------------------
# CLI --release --dry-run
# ---------------------------------------------------------------------------


class TestCLIRelease:
    def _run_scaffold(self, *extra_args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [_PYTHON, str(_SCRIPTS_DIR / "scaffold.py"), *extra_args],
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

    def test_release_dry_run_exit_zero(self):
        """--release VERSION --dry-run deve terminar com 0."""
        proc = self._run_scaffold("--release", "9.9.9", "--dry-run")
        assert proc.returncode == 0, f"stderr: {proc.stderr}"

    def test_release_dry_run_json_success(self):
        """--release VERSION --dry-run --json deve ter success=true."""
        proc = self._run_scaffold("--release", "9.9.9", "--dry-run", "--json")
        assert proc.returncode == 0, f"stderr: {proc.stderr}"
        data = json.loads(proc.stdout)
        assert data["success"] is True
        assert data["dry_run"] is True
        assert data["version"] == "9.9.9"

    def test_release_sem_version_exit_one(self):
        """--release sem argumento deve falhar (argparse error)."""
        proc = self._run_scaffold("--release")
        assert proc.returncode != 0

    def test_release_version_invalida_dry_run_exit_one(self):
        """--release com versão inválida deve retornar exit != 0."""
        proc = self._run_scaffold("--release", "nao_semver", "--dry-run", "--json")
        assert proc.returncode == 1
        data = json.loads(proc.stdout)
        assert data["success"] is False
