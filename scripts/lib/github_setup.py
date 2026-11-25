"""
lib/github_setup.py — publica main/dev no GitHub e protege a main (spec 067).

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.

Modelo de branches dos projetos gerados (ADR-004):
- ``main``: só recebe merge de ``dev`` (ou ``release/faseN``) por PR com CI verde;
- ``dev``: branch default, destino dos PRs de feature;
- ``release/faseN``: fases do projeto.

Esta etapa é opcional e tolerante a falhas: sem ``--repo`` GitHub, sem ``gh``
autenticado, com repositório remoto inexistente ou falha de rede, devolve
``CreatedItem(status="skipped")`` com o motivo — nunca derruba a geração.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .config import CreatedItem, ProjectConfig

_GIT = shutil.which("git") or "git"
_TIMEOUT_S = 60

# Workflow → nome do job agregador exigido na proteção da main.
_CHECKS_BY_WORKFLOW: tuple[tuple[str, str], ...] = (
    ("git-validation.yml", "Validation Summary"),
    ("ci.yml", "ci"),
)

_SLUG_RE = re.compile(
    r"^(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"(?P<owner>[A-Za-z0-9][A-Za-z0-9-]*)/(?P<repo>[A-Za-z0-9._-]+?)(?:\.git)?/?$"
)

Runner = Callable[..., subprocess.CompletedProcess]


class InvalidGithubRepoError(ValueError):
    """URL de repositório ausente ou que não aponta para ``owner/repo`` no GitHub."""


class GithubSetupError(RuntimeError):
    """Uma etapa da configuração remota falhou (gh, push, default branch, proteção)."""


# ---------------------------------------------------------------------------
# Funções puras
# ---------------------------------------------------------------------------


def parse_github_slug(url: str) -> str:
    """
    Extrai ``owner/repo`` de uma URL GitHub (https, ssh ou scp-like).

    :param url: URL do repositório.
    :type url: str
    :return: Slug ``owner/repo``.
    :rtype: str
    :raises InvalidGithubRepoError: URL vazia, não-GitHub ou fora do formato.

    :Example:

    >>> parse_github_slug("git@github.com:org/repo.git")
    'org/repo'
    """
    if not isinstance(url, str) or not url.strip():
        raise InvalidGithubRepoError("URL do repositório vazia")
    match = _SLUG_RE.match(url.strip())
    if not match:
        raise InvalidGithubRepoError(
            f"URL não é um repositório GitHub owner/repo: {url}"
        )
    return f"{match['owner']}/{match['repo']}"


def required_checks_for(project_path: Path) -> list[str]:
    """
    Lista os checks obrigatórios conforme os workflows presentes no projeto.

    :param project_path: Raiz do projeto gerado.
    :type project_path: Path
    :return: Nomes dos jobs a exigir, na ordem de ``_CHECKS_BY_WORKFLOW``.
    :rtype: list[str]
    """
    workflows = project_path / ".github" / "workflows"
    return [
        check for name, check in _CHECKS_BY_WORKFLOW if (workflows / name).is_file()
    ]


def build_protection_payload(checks: list[str], *, strict: bool) -> dict[str, Any]:
    """
    Monta o corpo de ``PUT /repos/{slug}/branches/main/protection``.

    Sem checks, ``required_status_checks`` fica ``None``: exigir um check que
    nenhum workflow produz trava o merge para sempre.

    :param checks: Nomes dos checks obrigatórios (não vazios, sem repetição).
    :type checks: list[str]
    :param strict: Exige branch atualizada com a base antes do merge.
    :type strict: bool
    :return: Payload da API de branch protection.
    :rtype: dict[str, Any]
    :raises ValueError: check vazio ou duplicado.

    :Example:

    >>> build_protection_payload([], strict=True)["required_status_checks"] is None
    True
    """
    if any(not c or not c.strip() for c in checks):
        raise ValueError("nome de check vazio")
    if len(set(checks)) != len(checks):
        raise ValueError(f"checks duplicados: {checks}")
    return {
        "required_status_checks": (
            {"strict": strict, "contexts": list(checks)} if checks else None
        ),
        "enforce_admins": False,
        "required_pull_request_reviews": {"required_approving_review_count": 0},
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }


# ---------------------------------------------------------------------------
# Execução (fronteira com gh/git)
# ---------------------------------------------------------------------------


def _run(
    cmd: list[str], cwd: Path, input_text: str | None = None
) -> subprocess.CompletedProcess:
    """Runner padrão: subprocess com timeout, sem levantar em returncode != 0."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        capture_output=True,
        text=True,
        timeout=_TIMEOUT_S,
        check=False,
    )


def _step(
    runner: Runner, label: str, cmd: list[str], cwd: Path, input_text: str | None = None
) -> None:
    """Executa uma etapa; converte returncode != 0, timeout e OSError em GithubSetupError."""
    try:
        result = runner(cmd, cwd, input_text)
    except (subprocess.TimeoutExpired, OSError) as error:
        raise GithubSetupError(f"{label}: {error}") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise GithubSetupError(f"{label}: {detail or f'código {result.returncode}'}")


def _skipped(path: Path, message: str) -> CreatedItem:
    return CreatedItem(
        path=path / ".git", kind="git", status="skipped", message=message
    )


def configure_github_branches(
    config: ProjectConfig, runner: Runner | None = None
) -> CreatedItem:
    """
    Publica main/dev/tags, define ``dev`` como default e protege ``main``.

    :param config: Configuração do projeto (usa ``github_repo`` e ``project_path``).
    :type config: ProjectConfig
    :param runner: Executor de comandos (injeção para testes); default subprocess.
    :type runner: Runner | None
    :return: ``created`` se todas as etapas passaram; ``skipped`` com o motivo
        caso contrário.
    :rtype: CreatedItem
    """
    run = runner or _run
    path = config.project_path

    if not config.github_repo:
        return _skipped(path, "GitHub: sem --repo, branches só locais")
    try:
        slug = parse_github_slug(config.github_repo)
    except InvalidGithubRepoError as error:
        return _skipped(path, f"GitHub: {error}")

    gh = shutil.which("gh")
    if not gh:
        return _skipped(
            path,
            "GitHub: gh não encontrado no PATH — veja docs/BRANCH_PROTECTION_SETUP.md",
        )

    payload = json.dumps(
        build_protection_payload(required_checks_for(path), strict=True)
    )
    steps: list[tuple[str, list[str], str | None]] = [
        ("gh auth status", [gh, "auth", "status"], None),
        ("gh repo view", [gh, "repo", "view", slug, "--json", "name"], None),
        ("git push", [_GIT, "push", "-u", "origin", "main", "dev", "--tags"], None),
        (
            "default branch dev",
            [gh, "repo", "edit", slug, "--default-branch", "dev"],
            None,
        ),
        (
            "proteção da main",
            [
                gh,
                "api",
                "-X",
                "PUT",
                f"repos/{slug}/branches/main/protection",
                "--input",
                "-",
            ],
            payload,
        ),
    ]
    for label, cmd, input_text in steps:
        try:
            _step(run, label, cmd, path, input_text)
        except GithubSetupError as error:
            return _skipped(path, f"GitHub: etapa interrompida — {error}")

    return CreatedItem(
        path=path / ".git",
        kind="git",
        status="created",
        message=f"GitHub {slug}: main/dev publicadas, default=dev, main protegida",
    )
