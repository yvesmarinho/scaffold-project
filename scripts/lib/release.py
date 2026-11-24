"""
scripts/lib/release.py — Processo de release automático do template.

Uso (via scaffold.py ou make):
    python scripts/scaffold.py --release VERSION=x.y.z
    make release VERSION=x.y.z

Etapas executadas em ordem:
    1. Valida que VERSION segue semver (X.Y.Z ou X.Y.Z-suffix)
    2. Verifica que há conteúdo em [Unreleased] no CHANGELOG.md
    3. Fecha seção [Unreleased] → [X.Y.Z] — YYYY-MM-DD no CHANGELOG.md
    4. Bumpa SCAFFOLD_VERSION em scripts/lib/config.py
    5. Executa publish_template() gerando o tarball em dist/
    6. Cria git tag vX.Y.Z anotada com o conteúdo daquela versão no CHANGELOG
    7. Retorna ReleaseResult com status e artefatos gerados
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# Caminho absoluto do git (S607/B607); "git" como fallback fora do PATH.
_GIT = shutil.which("git") or "git"

# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------

_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[a-zA-Z0-9.-]+))?$"
)

_UNRELEASED_HEADER_RE = re.compile(r"^## \[Unreleased\]", re.MULTILINE)
_VERSIONED_HEADER_RE = re.compile(r"^## \[\d+\.\d+\.\d+", re.MULTILINE)


# --------------------------------------------------------------------------
# Dataclasses de resultado
# --------------------------------------------------------------------------


@dataclass
class ReleaseResult:
    version: str
    success: bool
    steps_done: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    tarball: Path | None = None
    tag_created: bool = False

    @property
    def ok(self) -> bool:
        return self.success and not self.errors


# --------------------------------------------------------------------------
# Validação de versão
# --------------------------------------------------------------------------


def validate_semver(version: str) -> bool:
    """Retorna True se version é semver válido (X.Y.Z ou X.Y.Z-suffix)."""
    return bool(_SEMVER_RE.match(version.lstrip("v")))


def _canonical(version: str) -> str:
    """Remove prefixo 'v' se presente."""
    return version.lstrip("v")


# --------------------------------------------------------------------------
# CHANGELOG.md
# --------------------------------------------------------------------------


def close_unreleased(changelog_path: Path, version: str, release_date: str) -> str:
    """
    Substitui '## [Unreleased]' por:
        ## [Unreleased]
        (seção vazia preservada para o próximo ciclo)

        ## [X.Y.Z] — YYYY-MM-DD

    Retorna o conteúdo do bloco da versão fechada (para usar como mensagem da tag git).
    Lança ValueError se não houver seção [Unreleased] ou se estiver vazia.
    """
    text = changelog_path.read_text(encoding="utf-8")

    match_unreleased = _UNRELEASED_HEADER_RE.search(text)
    if not match_unreleased:
        raise ValueError("CHANGELOG.md não tem seção '## [Unreleased]'")

    # Encontrar o fim do bloco [Unreleased]: até o próximo ## ou fim do arquivo
    start = match_unreleased.end()
    next_section = _VERSIONED_HEADER_RE.search(text, start)
    if next_section:
        block_body = text[start : next_section.start()]
    else:
        block_body = text[start:]

    # Verificar que há conteúdo real (não apenas linhas em branco)
    if not block_body.strip():
        raise ValueError(
            "Seção [Unreleased] está vazia — não há o que fechar como release."
        )

    tag_body = block_body.rstrip()

    # Montar novo conteúdo do CHANGELOG
    new_version_header = f"## [{version}] — {release_date}"

    if next_section:
        new_text = (
            text[: match_unreleased.start()]
            + "## [Unreleased]\n\n---\n\n"
            + new_version_header
            + block_body
            + text[next_section.start() :]
        )
    else:
        new_text = (
            text[: match_unreleased.start()]
            + "## [Unreleased]\n\n---\n\n"
            + new_version_header
            + block_body
        )

    changelog_path.write_text(new_text, encoding="utf-8")
    return tag_body.strip()


# --------------------------------------------------------------------------
# Bump de SCAFFOLD_VERSION em config.py
# --------------------------------------------------------------------------


def bump_scaffold_version(config_path: Path, new_version: str) -> str:
    """
    Substitui SCAFFOLD_VERSION = "X.Y.Z" in config.py pelo novo valor.
    Retorna a versão anterior.
    Lança ValueError se o campo não for encontrado.
    """
    text = config_path.read_text(encoding="utf-8")
    pattern = re.compile(r'(SCAFFOLD_VERSION\s*=\s*")[^"]*(")')
    match = pattern.search(text)
    if not match:
        raise ValueError(f"SCAFFOLD_VERSION não encontrado em {config_path}")
    old_version = text[match.start() : match.end()].split('"')[1]
    new_text = pattern.sub(rf"\g<1>{new_version}\g<2>", text)
    config_path.write_text(new_text, encoding="utf-8")
    return old_version


# --------------------------------------------------------------------------
# Git tag
# --------------------------------------------------------------------------


def create_git_tag(version: str, tag_message: str, project_root: Path) -> None:
    """
    Cria uma tag git anotada vX.Y.Z com tag_message como anotação.
    Lança subprocess.CalledProcessError em caso de falha.
    """
    tag_name = f"v{version}"
    subprocess.run(
        [_GIT, "tag", "-a", tag_name, "-m", tag_message],
        cwd=str(project_root),
        check=True,
        capture_output=True,
        text=True,
    )


def git_tag_exists(version: str, project_root: Path) -> bool:
    """Retorna True se a tag vX.Y.Z já existe."""
    tag_name = f"v{version}"
    result = subprocess.run(
        [_GIT, "tag", "-l", tag_name],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


# --------------------------------------------------------------------------
# Orquestrador principal
# --------------------------------------------------------------------------


def run_release(
    version: str,
    project_root: Path,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> ReleaseResult:
    """
    Executa o processo completo de release.

    Args:
        version:      versão semver (com ou sem prefixo 'v'), ex: "1.1.0"
        project_root: raiz do repositório do template
        output_dir:   diretório de saída do tarball (default: project_root/dist)
        dry_run:      se True, valida tudo mas não grava nenhum arquivo/tag

    Returns:
        ReleaseResult com status e artefatos gerados.
    """
    version = _canonical(version)
    result = ReleaseResult(version=version, success=False)

    if output_dir is None:
        output_dir = project_root / "dist"

    # ------------------------------------------------------------------
    # Etapa 1 — Validar semver
    # ------------------------------------------------------------------
    if not validate_semver(version):
        result.errors.append(
            f"Versão inválida: '{version}' não segue semver (esperado X.Y.Z ou X.Y.Z-suffix)"
        )
        return result
    result.steps_done.append(f"semver válido: {version}")

    # ------------------------------------------------------------------
    # Etapa 2 — Verificar tag duplicada
    # ------------------------------------------------------------------
    if git_tag_exists(version, project_root):
        result.errors.append(
            f"Tag v{version} já existe no repositório git — escolha outra versão."
        )
        return result
    result.steps_done.append(f"tag v{version} não existe — OK")

    # ------------------------------------------------------------------
    # Etapa 3 — Fechar [Unreleased] no CHANGELOG.md
    # ------------------------------------------------------------------
    changelog_path = project_root / "CHANGELOG.md"
    if not changelog_path.exists():
        result.errors.append("CHANGELOG.md não encontrado na raiz do projeto")
        return result

    release_date = date.today().isoformat()

    if dry_run:
        # Apenas verificar a estrutura sem gravar
        text = changelog_path.read_text(encoding="utf-8")
        if not _UNRELEASED_HEADER_RE.search(text):
            result.errors.append("CHANGELOG.md não tem seção '## [Unreleased]'")
            return result
        m = _UNRELEASED_HEADER_RE.search(text)
        start = m.end()
        nxt = _VERSIONED_HEADER_RE.search(text, start)
        block_body = text[start : nxt.start()] if nxt else text[start:]
        if not block_body.strip():
            result.errors.append(
                "Seção [Unreleased] está vazia — não há o que fechar como release."
            )
            return result
        tag_body = block_body.strip()
        result.steps_done.append(
            f"[dry-run] CHANGELOG.md: seção [{version}] seria criada em {release_date}"
        )
    else:
        try:
            tag_body = close_unreleased(changelog_path, version, release_date)
        except ValueError as exc:
            result.errors.append(f"CHANGELOG.md: {exc}")
            return result
        result.steps_done.append(
            f"CHANGELOG.md: seção [{version}] criada em {release_date}"
        )

    # ------------------------------------------------------------------
    # Etapa 4 — Bump SCAFFOLD_VERSION em config.py
    # ------------------------------------------------------------------
    config_path = project_root / "scripts" / "lib" / "config.py"
    if not config_path.exists():
        result.errors.append("scripts/lib/config.py não encontrado")
        return result

    try:
        if dry_run:
            # Apenas verificar sem gravar
            text = config_path.read_text(encoding="utf-8")
            pattern = re.compile(r'(SCAFFOLD_VERSION\s*=\s*")[^"]*(")')
            if not pattern.search(text):
                raise ValueError("SCAFFOLD_VERSION não encontrado")
            old_ver = pattern.search(text).group(0).split('"')[1]
            result.steps_done.append(
                f"[dry-run] config.py: SCAFFOLD_VERSION '{old_ver}' → '{version}'"
            )
        else:
            old_ver = bump_scaffold_version(config_path, version)
            result.steps_done.append(
                f"config.py: SCAFFOLD_VERSION '{old_ver}' → '{version}'"
            )
    except ValueError as exc:
        result.errors.append(f"config.py: {exc}")
        return result

    # ------------------------------------------------------------------
    # Etapa 5 — Gerar tarball (publish)
    # ------------------------------------------------------------------
    if dry_run:
        tarball_path = (
            output_dir
            / f"enterprise-template-v{version}-{release_date.replace('-','')}.tar.gz"
        )
        result.steps_done.append(
            f"[dry-run] publish: tarball seria gerado em {tarball_path}"
        )
        result.tarball = tarball_path
    else:
        try:
            from scripts.lib.publish import publish_template  # type: ignore
        except ImportError:
            import sys

            sys.path.insert(0, str(project_root / "scripts"))
            from lib.publish import publish_template  # type: ignore

        output_dir.mkdir(parents=True, exist_ok=True)
        publish_result = publish_template(output_dir, project_root, version=version)
        result.tarball = publish_result.tarball_path
        result.steps_done.append(f"publish: tarball gerado em {result.tarball}")

    # ------------------------------------------------------------------
    # Etapa 6 — git tag vX.Y.Z
    # ------------------------------------------------------------------
    tag_annotation = f"Release v{version} — {release_date}\n\n{tag_body}"

    if dry_run:
        result.steps_done.append(
            f"[dry-run] git tag: v{version} seria criada com anotação de {len(tag_annotation)} chars"
        )
    else:
        try:
            create_git_tag(version, tag_annotation, project_root)
            result.tag_created = True
            result.steps_done.append(f"git tag: v{version} criada")
        except subprocess.CalledProcessError as exc:
            result.errors.append(f"git tag falhou: {exc.stderr.strip()}")
            return result

    result.success = True
    return result
