"""
tests/test_smoke_imp30.py — IMP-30: Smoke tests para scaffold.py --publish.

Cobertura:
  _collect_files:
    - inclui scripts/scaffold.py
    - inclui pelo menos um profile descriptor YAML
    - inclui README.md
    - inclui Makefile
    - inclui pelo menos um arquivo em .github/prompts/
    - exclui arquivos __pycache__
    - exclui extensões .pyc

  publish_template:
    - cria o arquivo .tar.gz em output_dir
    - cria o arquivo de manifesto JSON
    - tarball é um arquivo gz válido
    - tarball contém scripts/scaffold.py
    - tarball contém pelo menos um profile descriptor
    - tarball contém README.md
    - manifesto tem chave 'version' correta
    - manifesto tem chave 'file_count' > 0
    - manifesto 'files' lista scripts/scaffold.py
    - manifesto 'size_bytes' > 0
    - PublishResult.file_count == len(included_files)
    - segunda chamada no mesmo dia sobrescreve o tarball (idempotente)

  CLI --publish:
    - --help menciona --publish
    - --publish --json retorna JSON válido
    - --publish --json tem chave 'success' == True
    - --publish --json tem chave 'tarball'
    - --publish --json tem chave 'file_count' > 0
    - --publish --json manifesto criado em disco
    - --publish --output-dir usa diretório especificado
"""

from __future__ import annotations

import json
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.publish import _collect_files, publish_template  # noqa: E402

_PROJECT_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _PROJECT_ROOT / "scripts"
_PYTHON = sys.executable


# ===========================================================================
# _collect_files
# ===========================================================================


class TestCollectFiles:

    def test_includes_scaffold_py(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        rel = [str(f.relative_to(_PROJECT_ROOT)) for f in files]
        assert (
            "scripts/scaffold.py" in rel
        ), f"scaffold.py ausente; encontrado: {rel[:10]}"

    def test_includes_at_least_one_profile_descriptor(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        rel = [str(f.relative_to(_PROJECT_ROOT)) for f in files]
        descriptors = [
            r for r in rel if r.startswith("scaffold/profiles/") and r.endswith(".yaml")
        ]
        assert len(descriptors) >= 1, "Nenhum profile descriptor encontrado"

    def test_includes_readme(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        rel = [str(f.relative_to(_PROJECT_ROOT)) for f in files]
        assert "README.md" in rel

    def test_includes_makefile(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        rel = [str(f.relative_to(_PROJECT_ROOT)) for f in files]
        assert "Makefile" in rel

    def test_includes_at_least_one_prompt(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        rel = [str(f.relative_to(_PROJECT_ROOT)) for f in files]
        prompts = [r for r in rel if r.startswith(".github/prompts/")]
        assert len(prompts) >= 1, "Nenhum prompt encontrado"

    def test_excludes_pycache_files(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        rel = [str(f.relative_to(_PROJECT_ROOT)) for f in files]
        pycache = [r for r in rel if "__pycache__" in r]
        assert pycache == [], f"__pycache__ não deveria estar incluído: {pycache}"

    def test_excludes_pyc_extension(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        pyc = [f for f in files if f.suffix in (".pyc", ".pyo")]
        assert pyc == [], f"Arquivos .pyc não deveriam ser incluídos: {pyc}"

    def test_returns_only_files(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        non_files = [f for f in files if not f.is_file()]
        assert non_files == [], f"Todos os itens devem ser arquivos: {non_files}"

    def test_no_duplicates(self) -> None:
        # Pelo caminho relativo: symlink (scripts/x) e alvo (scaffold/templates/
        # runtime/scripts/x) são entradas distintas desde a fatia 4 do ADR-003.
        files = _collect_files(_PROJECT_ROOT)
        rels = [f.relative_to(_PROJECT_ROOT) for f in files]
        assert len(rels) == len(set(rels)), "Lista contém arquivos duplicados"

    def test_symlinks_tem_alvo_no_pacote(self) -> None:
        files = _collect_files(_PROJECT_ROOT)
        included = {f.resolve() for f in files if not f.is_symlink()}
        dangling = [
            str(f.relative_to(_PROJECT_ROOT))
            for f in files
            if f.is_symlink() and f.resolve() not in included
        ]
        assert dangling == [], "symlinks sem alvo no tarball"


# ===========================================================================
# publish_template
# ===========================================================================


class TestPublishTemplate:

    def test_creates_tarball(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        assert (
            result.tarball_path.exists()
        ), f"Tarball não criado: {result.tarball_path}"

    def test_creates_manifest(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        assert (
            result.manifest_path.exists()
        ), f"Manifesto não criado: {result.manifest_path}"

    def test_tarball_is_valid_gz(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        assert tarfile.is_tarfile(
            result.tarball_path
        ), "O tarball não é um arquivo tar válido"

    def test_tarball_contains_scaffold_py(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        with tarfile.open(result.tarball_path, "r:gz") as tar:
            names = tar.getnames()
        assert (
            "scripts/scaffold.py" in names
        ), f"scaffold.py ausente no tarball; nomes: {names[:10]}"

    def test_tarball_contains_readme(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        with tarfile.open(result.tarball_path, "r:gz") as tar:
            names = tar.getnames()
        assert "README.md" in names

    def test_tarball_contains_profile_descriptor(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        with tarfile.open(result.tarball_path, "r:gz") as tar:
            names = tar.getnames()
        descriptors = [
            n
            for n in names
            if n.startswith("scaffold/profiles/") and n.endswith(".yaml")
        ]
        assert len(descriptors) >= 1, "Nenhum profile descriptor no tarball"

    def test_manifest_version_correct(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        data = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert data["version"] == result.version

    def test_manifest_file_count_positive(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        data = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert data["file_count"] > 0

    def test_manifest_lists_scaffold_py(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        data = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert "scripts/scaffold.py" in data["files"]

    def test_manifest_size_bytes_positive(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        data = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert data["size_bytes"] > 0

    def test_result_file_count_matches_included_files(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        assert result.file_count == len(result.included_files)

    def test_result_size_bytes_positive(self, tmp_path: Path) -> None:
        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        assert result.size_bytes > 0

    def test_second_call_overwrites_tarball(self, tmp_path: Path) -> None:
        """Segunda chamada no mesmo dia sobrescreve o tarball anterior."""
        result1 = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        # Corrompe o tarball: se a 2ª chamada não sobrescrever, ele continua inválido
        # (comparar mtime não serve — pode ser igual em sistemas rápidos).
        result1.tarball_path.write_bytes(b"corrompido")

        result2 = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)

        # Ambos apontam para o mesmo arquivo (mesmo nome por data)
        assert result1.tarball_path == result2.tarball_path
        assert tarfile.is_tarfile(result2.tarball_path), "tarball não foi sobrescrito"

    def test_output_dir_is_created_if_missing(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "sub" / "releases"
        assert not output_dir.exists()
        result = publish_template(output_dir=output_dir, project_root=_PROJECT_ROOT)
        assert output_dir.exists()
        assert result.tarball_path.exists()

    def test_publish_result_has_correct_version(self, tmp_path: Path) -> None:
        from lib.config import SCAFFOLD_VERSION

        result = publish_template(output_dir=tmp_path, project_root=_PROJECT_ROOT)
        assert result.version == SCAFFOLD_VERSION


# ===========================================================================
# CLI --publish
# ===========================================================================


class TestPublishCLI:

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [_PYTHON, str(_SCRIPTS_DIR / "scaffold.py"), *args],
            capture_output=True,
            text=True,
        )

    def test_help_mentions_publish(self) -> None:
        proc = self._run("--help")
        assert (
            "--publish" in proc.stdout
        ), f"--publish ausente no --help; stdout: {proc.stdout[:300]}"

    def test_help_mentions_output_dir(self) -> None:
        proc = self._run("--help")
        assert "--output-dir" in proc.stdout

    def test_publish_json_returns_zero(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        assert proc.returncode == 0, f"rc={proc.returncode}; stderr={proc.stderr[:200]}"

    def test_publish_json_is_valid_json(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        data = json.loads(proc.stdout)
        assert isinstance(data, dict)

    def test_publish_json_has_success_true(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        data = json.loads(proc.stdout)
        assert data.get("success") is True

    def test_publish_json_has_tarball_key(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        data = json.loads(proc.stdout)
        assert "tarball" in data

    def test_publish_json_file_count_positive(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        data = json.loads(proc.stdout)
        assert data.get("file_count", 0) > 0

    def test_publish_json_tarball_file_exists(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        data = json.loads(proc.stdout)
        assert Path(data["tarball"]).exists(), f"Tarball não existe: {data['tarball']}"

    def test_publish_json_manifest_file_exists(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        data = json.loads(proc.stdout)
        assert Path(
            data["manifest"]
        ).exists(), f"Manifesto não existe: {data['manifest']}"

    def test_publish_json_created_at_is_iso(self, tmp_path: Path) -> None:
        proc = self._run("--publish", "--json", "--output-dir", str(tmp_path))
        data = json.loads(proc.stdout)
        created_at = data.get("created_at", "")
        # America/Sao_Paulo com offset (ISO 8601), não mais UTC com "Z"
        assert (
            datetime.fromisoformat(created_at).utcoffset() is not None
        ), f"created_at inválido: {created_at}"

    def test_publish_output_dir_flag(self, tmp_path: Path) -> None:
        custom_dir = tmp_path / "my-releases"
        proc = self._run("--publish", "--json", "--output-dir", str(custom_dir))
        assert proc.returncode == 0
        data = json.loads(proc.stdout)
        # Tarball deve estar no diretório especificado
        assert str(custom_dir) in data["tarball"]
