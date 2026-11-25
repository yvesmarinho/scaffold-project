"""
lib/base_templates.py — templates base dos projetos gerados (ADR-003, fatia 3).

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.

Os arquivos que antes eram strings em ``project.py`` vivem em
``scaffold/templates/base/*.tmpl``. Este módulo:

- carrega um template preservando os bytes (sem tradução de quebra de linha);
- renderiza o placeholder único ``{{NOME}}`` numa só passada (um valor que
  contenha outro placeholder não é expandido de novo).

Pastas com ponto (``.secrets/``, ``.memory/``) são evitadas no layout dos
templates porque o ``.gitignore`` do repositório pode ignorá-las e o publish
empacota só arquivos versionados.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from functools import cache
from pathlib import Path

BASE_TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent.parent / "scaffold" / "templates" / "base"
)

# Constante em project.py → template relativo a BASE_TEMPLATES_DIR
TEMPLATE_FILES: dict[str, str] = {
    "_README_MD": "README.md.tmpl",
    "_DOCS_INDEX_MD": "docs/INDEX.md.tmpl",
    "_DOCS_TODO_MD": "docs/TODO.md.tmpl",
    "_DOCS_TODAY_ACTIVITIES_MD": "docs/TODAY_ACTIVITIES.md.tmpl",
    "_DOCS_ARCHITECTURE_README": "docs/architecture/README.md.tmpl",
    "_DOCS_DEBATES_README": "docs/debates/README.md.tmpl",
    "_DOCS_DECISIONS_README": "docs/decisions/README.md.tmpl",
    "_DOCS_GUIDES_README": "docs/guides/README.md.tmpl",
    "_DOCS_RETROSPECTIVES_README": "docs/retrospectives/README.md.tmpl",
    "_DOCS_BUGS_README": "docs/bugs/README.md.tmpl",
    "_DOCS_IMPLEMENTATIONS_README": "docs/implementations/README.md.tmpl",
    "_DOCS_TEMPLATES_README": "docs/templates/README.md.tmpl",
    "_PROJECT_CREATION_SUMMARY": "docs/PROJECT_CREATION_SUMMARY.md.tmpl",
    "_GITIGNORE": "gitignore.tmpl",
    "_SECRETS_README": "secrets/README.md.tmpl",
    "_SECRETS_SECURITY_MD": "secrets/SECURITY.md.tmpl",
    "_PRE_COMMIT_SECRETS_HOOK": "git-hooks/pre-commit.secrets.tmpl",
    "_MAKEFILE": "Makefile.tmpl",
    "_LOGS_README": "logs/README.md.tmpl",
    "_TMP_README": "tmp/README.md.tmpl",
    "_MEMORY_README": "memory/README.md.tmpl",
    "_SESSION_TIME_README": "session-time/README.md.tmpl",
    "_SECURITY_MD_WITH_GITHUB": "SECURITY.with-github.md.tmpl",
    "_SECURITY_MD_WITHOUT_GITHUB": "SECURITY.without-github.md.tmpl",
    "_CODEOWNERS": "github/CODEOWNERS.tmpl",
    "_DEPENDABOT_YML": "github/dependabot.yml.tmpl",
    "_SECURITY_SCAN_YML": "github/workflows/security-scan.yml.tmpl",
    "_DEPENDENCY_REVIEW_YML": "github/workflows/dependency-review.yml.tmpl",
    "_CLAUDE_MD": "claude/CLAUDE.md.tmpl",
    "_CLAUDE_SETTINGS_JSON": "claude/settings.json.tmpl",
}

_NAME_RE = re.compile(
    r"^[A-Za-z0-9_-][A-Za-z0-9._-]*(?:/[A-Za-z0-9_-][A-Za-z0-9._-]*)*\.tmpl$"
)
_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_PLACEHOLDER_RE = re.compile(r"(?<!\$)\{\{([A-Z][A-Z0-9_]*)\}\}")


class InvalidTemplateNameError(ValueError):
    """Nome de template vazio, absoluto, com ``..`` ou fora do padrão ``*.tmpl``."""


class TemplateNotFoundError(FileNotFoundError):
    """Template base inexistente (ou diretório de templates indisponível)."""


@cache
def load_base_template(name: str) -> str:
    """
    Carrega ``scaffold/templates/base/<name>`` preservando os bytes.

    :param name: Caminho relativo terminado em ``.tmpl`` (ex.: ``docs/INDEX.md.tmpl``).
    :type name: str
    :return: Conteúdo do template, sem tradução de quebra de linha.
    :rtype: str
    :raises InvalidTemplateNameError: nome inválido ou tentativa de sair do diretório.
    :raises TemplateNotFoundError: arquivo ausente ou ilegível.

    :Example:

    >>> load_base_template("gitignore.tmpl").startswith("#")
    True
    """
    if not isinstance(name, str) or not _NAME_RE.match(name) or ".." in name.split("/"):
        raise InvalidTemplateNameError(f"nome de template inválido: {name!r}")
    path = BASE_TEMPLATES_DIR / name
    try:
        return path.read_bytes().decode("utf-8")
    except FileNotFoundError as error:
        raise TemplateNotFoundError(
            f"template base não encontrado: {name} ({path})"
        ) from error
    except (OSError, UnicodeDecodeError) as error:
        raise TemplateNotFoundError(
            f"template base ilegível: {name}: {error}"
        ) from error


def render(text: str, values: Mapping[str, str]) -> str:
    """
    Substitui ``{{CHAVE}}`` pelos valores, numa única passada.

    Chaves ausentes de ``values`` e expressões ``${{ ... }}`` (GitHub Actions)
    ficam intactas.

    :param text: Texto do template.
    :type text: str
    :param values: Mapa ``CHAVE`` (``[A-Z][A-Z0-9_]*``) → valor ``str``.
    :type values: Mapping[str, str]
    :return: Texto renderizado.
    :rtype: str
    :raises ValueError: chave fora do padrão ou valor que não é ``str``.

    :Example:

    >>> render("Olá {{NOME}} ${{ x }}", {"NOME": "Ana"})
    'Olá Ana ${{ x }}'
    """
    for key, value in values.items():
        if not isinstance(key, str) or not _KEY_RE.match(key):
            raise ValueError(f"chave de placeholder inválida: {key!r}")
        if not isinstance(value, str):
            raise ValueError(
                f"valor do placeholder {key} não é str: {type(value).__name__}"
            )

    def _sub(match: re.Match[str]) -> str:
        key = match.group(1)
        return values[key] if key in values else match.group(0)

    return _PLACEHOLDER_RE.sub(_sub, text)
