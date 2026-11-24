"""
tests/helpers/fake_project.py — Utilitários para testes de integração de templates.

Copia um template físico (.github/templates/<perfil>/) para um tmpdir,
expande os placeholders {curly-brace} e devolve um FakeProject com
helpers de asserção.

Uso nos testes:
    from tests.helpers.fake_project import expand_template, TEMPLATES_DIR

    def test_makefile_exists(tmp_path):
        proj = expand_template("python-fastapi", tmp_path)
        assert proj.file("Makefile").exists()
        proj.assert_no_placeholders()
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths base
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = _REPO_ROOT / ".github" / "templates"

# ---------------------------------------------------------------------------
# Valores fixos usados na expansão (não importa serem "reais")
# ---------------------------------------------------------------------------

_DEFAULT_VARS: dict[str, str] = {
    "project_name": "fake-project",
    "project_title": "Fake Project",
    "description": "Integration test fake project",
    "author": "Test Author",
    "year": "2026",
    "domain": "programming",
    "language": "python",
    "github_repo": "https://github.com/org/fake-project",
    "python_version": "3.12",
    "node_version": "22",
    "chart_version": "0.1.0",
    "app_version": "0.1.0",
    "namespace": "default",
    "registry": "ghcr.io/org",
}

# Extensões de arquivo que serão tratadas como texto (conteúdo expandido)
_TEXT_SUFFIXES: frozenset[str] = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".json",
        ".toml",
        ".yml",
        ".yaml",
        ".md",
        ".txt",
        ".sh",
        ".env",
        ".env.example",
        ".gitignore",
        ".dockerignore",
        ".sql",
        ".tf",
        ".tfvars",
        ".hcl",
        ".cfg",
        ".ini",
        ".conf",
        ".html",
        ".css",
        ".scss",
        "",  # Makefile, Dockerfile, etc.
    }
)

# Nomes canônicos usados nos templates — só estes são expandidos/verificados.
# Padrões como {children} (JSX), {req} (f-string) ou {high} (format-string de
# CI) NÃO são placeholders de template e não devem disparar asserções.
_KNOWN_PLACEHOLDER_NAMES: frozenset[str] = frozenset(
    {
        "project_name",
        "project_title",
        "description",
        "author",
        "year",
        "domain",
        "language",
        "github_repo",
        "python_version",
        "node_version",
        "chart_version",
        "app_version",
        "namespace",
        "registry",
    }
)
_PLACEHOLDER_RE = re.compile(
    r"\{(" + "|".join(re.escape(k) for k in _KNOWN_PLACEHOLDER_NAMES) + r")\}"
)

# Binários: não tentar decodificar
_BINARY_SUFFIXES: frozenset[str] = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".ico",
        ".svg",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".zip",
        ".tar",
        ".gz",
        ".jar",
        ".db",
        ".pdf",
        ".pyc",
        ".pyo",
    }
)


# ---------------------------------------------------------------------------
# FakeProject — resultado da expansão
# ---------------------------------------------------------------------------


@dataclass
class FakeProject:
    """Representa um template expandido num diretório temporário."""

    root: Path
    """Raiz do projeto expandido (dentro de tmp_path)."""

    profile: str
    """Nome do perfil que foi expandido."""

    vars: dict[str, str] = field(default_factory=dict)
    """Variáveis usadas na expansão."""

    # ------------------------------------------------------------------
    # Helpers de path
    # ------------------------------------------------------------------

    def file(self, *parts: str) -> Path:
        """Retorna o Path de um arquivo relativo à raiz do projeto."""
        return self.root.joinpath(*parts)

    def exists(self, *parts: str) -> bool:
        """Verifica se um arquivo/pasta existe."""
        return self.file(*parts).exists()

    def read(self, *parts: str) -> str:
        """Lê o conteúdo de um arquivo de texto."""
        return self.file(*parts).read_text(encoding="utf-8")

    def text_files(self) -> Iterator[Path]:
        """Itera sobre todos os arquivos de texto no projeto."""
        for f in sorted(self.root.rglob("*")):
            if f.is_file() and f.suffix not in _BINARY_SUFFIXES:
                yield f

    # ------------------------------------------------------------------
    # Asserções prontas
    # ------------------------------------------------------------------

    def assert_no_placeholders(self) -> None:
        """Falha se qualquer arquivo de texto ainda contiver {placeholder}."""
        violations: list[str] = []
        for f in self.text_files():
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                matches = _PLACEHOLDER_RE.findall(content)
                if matches:
                    rel = f.relative_to(self.root)
                    violations.append(f"{rel}: {matches[:5]}")
            except OSError as exc:
                # arquivo ilegível não pode esconder violação: registra no relatório
                violations.append(f"{f.relative_to(self.root)}: ilegível ({exc})")
        assert not violations, (
            f"Placeholders não substituídos encontrados em [{self.profile}]:\n"
            + "\n".join(f"  {v}" for v in violations)
        )

    def assert_file_exists(self, *rel_parts: str) -> None:
        """Falha se o arquivo não existir."""
        p = self.file(*rel_parts)
        rel = Path(*rel_parts)
        assert p.exists(), (
            f"[{self.profile}] Arquivo obrigatório ausente: {rel}\n"
            f"  (procurado em: {p})"
        )

    def assert_file_contains(
        self, rel: str, pattern: str, *, regex: bool = False
    ) -> None:
        """Falha se o arquivo não contiver o padrão (string ou regex)."""
        p = self.file(rel)
        assert p.exists(), f"[{self.profile}] Arquivo {rel} não encontrado"
        content = p.read_text(encoding="utf-8", errors="replace")
        if regex:
            assert re.search(
                pattern, content
            ), f"[{self.profile}] {rel} não contém o padrão `{pattern}`"
        else:
            assert pattern in content, f"[{self.profile}] {rel} não contém `{pattern}`"

    def assert_gitignore_covers(self, *patterns: str) -> None:
        """.gitignore deve conter cada um dos padrões informados."""
        gi = self.file(".gitignore")
        assert gi.exists(), f"[{self.profile}] .gitignore ausente"
        content = gi.read_text(encoding="utf-8")
        for pat in patterns:
            assert pat in content, f"[{self.profile}] .gitignore não cobre `{pat}`"


# ---------------------------------------------------------------------------
# expand_template — função principal
# ---------------------------------------------------------------------------


def expand_template(
    profile: str,
    dest: Path,
    *,
    vars: dict[str, str] | None = None,
) -> FakeProject:
    """
    Copia `.github/templates/<profile>/` para `dest/`, expandindo placeholders.

    Args:
        profile: Nome do perfil (ex: "python-fastapi", "typescript-next").
        dest: Diretório de destino (normalmente `tmp_path` do pytest).
        vars: Substituições adicionais/override (mescla com _DEFAULT_VARS).

    Returns:
        FakeProject com root=dest e métodos de asserção.

    Raises:
        FileNotFoundError: Se o template não existir em TEMPLATES_DIR.
    """
    template_src = TEMPLATES_DIR / profile
    if not template_src.is_dir():
        raise FileNotFoundError(
            f"Template '{profile}' não encontrado em {TEMPLATES_DIR}"
        )

    effective_vars = {**_DEFAULT_VARS, **(vars or {})}

    # Copia toda a árvore para dest
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(template_src, dest, dirs_exist_ok=False)

    # Expande placeholders em todos os arquivos de texto
    _expand_dir(dest, effective_vars)

    return FakeProject(root=dest, profile=profile, vars=effective_vars)


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _expand_dir(root: Path, vars: dict[str, str]) -> None:
    """Substitui {placeholder} em todos os arquivos de texto dentro de root."""
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix in _BINARY_SUFFIXES:
            continue
        try:
            original = f.read_text(encoding="utf-8", errors="replace")
            expanded = _apply_vars(original, vars)
            if expanded != original:
                f.write_text(expanded, encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            pass


def _apply_vars(text: str, vars: dict[str, str]) -> str:
    """Substitui todos os {key} por vars[key] no texto."""
    for key, value in vars.items():
        text = text.replace(f"{{{key}}}", value)
    return text
