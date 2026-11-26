"""
lib/publish.py — Publicação de release do template Enterprise.

Gera um tarball versionado (.tar.gz) e um manifesto JSON com a lista de
arquivos incluídos, contagem e tamanho. Usado pelo flow_publish() em
scaffold.py via flag --publish.

Arquivos incluídos no release (ADR-003 fatia 6):
  scripts/**  — o gerador, recursivo (menos scripts/tmp/)
  scaffold/** — perfis e templates de distribuição
  pyproject.toml, uv.lock, README.md — para instalar as dependências com uv
  O que é só do desenvolvimento do scaffold (tests, Makefile, pytest.ini,
  CHANGELOG, .github/, configs do repo) não entra.

Arquivos excluídos:
  __pycache__/, .venv/, .git/, node_modules/, .secrets/, dist/
  caches locais: .ruff_cache/, .mypy_cache/, .pytest_cache/, htmlcov/
  em repositório git: tudo que não é versionado (git ls-files); fora de repo
  (ex.: tarball extraído) ou sem git disponível, vale só o glob
  *.pyc, *.pyo
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import SCAFFOLD_VERSION

_LOCAL_TZ = ZoneInfo("America/Sao_Paulo")

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Padrões de inclusão (glob sobre project_root)
# ---------------------------------------------------------------------------

_INCLUDE_PATTERNS: list[str] = [
    # Gerador completo e as fontes de distribuição (ADR-003 fatia 6)
    "scripts/**/*",
    "scaffold/**/*",
    # Declaração de dependências (rich, pyyaml) para `uv run` no pacote extraído
    "pyproject.toml",
    "uv.lock",
    "README.md",
]

# Prefixos (relativos, posix) que nunca entram: rascunhos versionados
_EXCLUDE_PREFIXES: tuple[str, ...] = ("scripts/tmp/",)

# Nomes de diretório/arquivo a excluir (qualquer nível do path)
_EXCLUDE_NAMES: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        ".secrets",
        ".git",
        "dist",
        ".ruff_cache",
        ".mypy_cache",
        ".pytest_cache",
        "htmlcov",
    }
)

# Extensões de bytecode Python a excluir
_EXCLUDE_SUFFIXES: frozenset[str] = frozenset({".pyc", ".pyo", ".pyd"})


# ---------------------------------------------------------------------------
# Dataclass de resultado
# ---------------------------------------------------------------------------


@dataclass
class PublishResult:
    """Resultado de uma operação publish_template()."""

    tarball_path: Path
    manifest_path: Path
    file_count: int
    size_bytes: int
    version: str
    created_at: str
    included_files: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Coleta de arquivos
# ---------------------------------------------------------------------------


def _tracked_files(project_root: Path) -> set[str] | None:
    """
    Caminhos relativos (posix) versionados em ``project_root`` via ``git ls-files``.

    Retorna None quando ``project_root`` não é a raiz de um repositório git ou o
    git não está disponível — nesse caso o chamador mantém a seleção por glob.
    """
    git = shutil.which("git")
    if git is None:
        log.warning("git não encontrado no PATH; release filtrado só pelo glob")
        return None
    try:
        top = subprocess.run(  # noqa: S603 — argumentos fixos, sem entrada externa
            [git, "rev-parse", "--show-toplevel"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        if Path(top).resolve() != project_root.resolve():
            return None
        listed = subprocess.run(  # noqa: S603 — argumentos fixos, sem entrada externa
            [git, "ls-files", "-z"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        ).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        log.warning(
            "git indisponível para filtrar o release (%s); usando só o glob", exc
        )
        return None
    return {entry for entry in listed.split("\0") if entry}


def _collect_files(project_root: Path) -> list[Path]:
    """
    Percorre _INCLUDE_PATTERNS sob project_root e retorna lista ordenada
    de arquivos a incluir no tarball, excluindo nomes e extensões banidos.

    Retorna paths absolutos sem duplicatas (pelo caminho **relativo**: um
    symlink e o seu alvo são entradas distintas — o tar preserva o symlink e o
    alvo precisa estar no pacote para ele resolver; ADR-003 fatia 4).
    """
    seen: set[Path] = set()
    result: list[Path] = []
    # Em repo git, só entra o que é versionado (nada de rascunho local no release)
    tracked = _tracked_files(project_root)

    for pattern in _INCLUDE_PATTERNS:
        for path in sorted(project_root.glob(pattern)):
            if not path.is_file():
                continue

            rel = path.relative_to(project_root)
            if tracked is not None and rel.as_posix() not in tracked:
                continue
            if rel.as_posix().startswith(_EXCLUDE_PREFIXES):
                continue
            rel_parts = rel.parts

            # Exclui se qualquer componente do path está na lista negra
            if any(part in _EXCLUDE_NAMES for part in rel_parts):
                continue

            # Exclui extensões de bytecode
            if path.suffix in _EXCLUDE_SUFFIXES:
                continue

            if rel not in seen:
                seen.add(rel)
                result.append(path)

    return result


# ---------------------------------------------------------------------------
# Publicação
# ---------------------------------------------------------------------------


def publish_template(
    output_dir: Path,
    project_root: Path,
    version: str = SCAFFOLD_VERSION,
    now: datetime | None = None,
) -> PublishResult:
    """
    Cria um tarball de release do template e um manifesto JSON.

    Nomes gerados:
      enterprise-template-v{version}-{YYYYMMDD}.tar.gz
      release-manifest-v{version}-{YYYYMMDD}.json

    Idempotente por data: chamadas múltiplas no mesmo dia sobrescrevem o
    tarball anterior (comportamento intencional — "latest nightly build").

    Args:
        output_dir:   Diretório de saída (criado se não existir).
        project_root: Raiz do projeto template.
        version:      Versão do release (default: SCAFFOLD_VERSION).
        now:          Instante do release (timezone-aware); default agora.
                      created_at e a data dos nomes usam America/Sao_Paulo.

    Returns:
        PublishResult com metadados do release gerado.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if now is not None and now.tzinfo is None:
        raise ValueError("datetime sem timezone — use datetime.now(timezone.utc)")
    local = (now or datetime.now(UTC)).astimezone(_LOCAL_TZ)
    created_at = local.isoformat(timespec="seconds")
    date_slug = local.strftime("%Y%m%d")
    base_name = f"enterprise-template-v{version}-{date_slug}"

    tarball_path = output_dir / f"{base_name}.tar.gz"
    manifest_path = output_dir / f"release-manifest-v{version}-{date_slug}.json"

    files = _collect_files(project_root)
    included_files: list[str] = [str(f.relative_to(project_root)) for f in files]

    # Escreve tarball (sobrescreve se existir — idempotente por data)
    with tarfile.open(tarball_path, "w:gz") as tar:
        for file_path in files:
            arcname = str(file_path.relative_to(project_root))
            tar.add(str(file_path), arcname=arcname)

    size_bytes = tarball_path.stat().st_size

    # Escreve manifesto JSON
    manifest: dict = {
        "version": version,
        "created_at": created_at,
        "tarball": tarball_path.name,
        "file_count": len(files),
        "size_bytes": size_bytes,
        "files": included_files,
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return PublishResult(
        tarball_path=tarball_path,
        manifest_path=manifest_path,
        file_count=len(files),
        size_bytes=size_bytes,
        version=version,
        created_at=created_at,
        included_files=included_files,
    )
