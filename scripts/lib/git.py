"""
lib/git.py — git init e git remote add.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from rich.console import Console

from .config import CreatedItem, ProjectConfig

console = Console()


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def is_git_repo(path: Path) -> bool:
    """Retorna True se path já contém um repositório git (.git/ existe)."""
    return (path / ".git").exists()


def init_repository(config: ProjectConfig) -> CreatedItem:
    """
    Executa git init no target_dir.
    Se config.github_repo fornecido, adiciona como remote 'origin'.

    - Não falha se .git/ já existe — reporta 'skipped'.
    - Não falha se git não está no PATH — aviso e retorna 'skipped'.
    - Usa subprocess com check=True e timeout=30s.
    """
    target = config.project_path

    if not shutil.which("git"):
        console.print("  [yellow]⚠️  git não encontrado no PATH — etapa Git ignorada.[/yellow]")
        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="skipped",
            message="git não encontrado no PATH",
        )

    if is_git_repo(target):
        # Repositório já existe — tenta apenas adicionar remote se necessário
        if config.github_repo:
            _ensure_remote(target, config.github_repo)
        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="skipped",
            message="repositório já existente",
        )

    try:
        subprocess.run(
            ["git", "init"],
            cwd=target,
            check=True,
            capture_output=True,
            timeout=30,
        )
    except subprocess.CalledProcessError as e:
        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="error",
            message=e.stderr.decode(errors="replace").strip(),
        )

    if config.github_repo:
        _ensure_remote(target, config.github_repo)

    return CreatedItem(
        path=target / ".git",
        kind="git",
        status="created",
        message=f"git init{' + remote origin' if config.github_repo else ''}",
    )


# ---------------------------------------------------------------------------
# Auxiliar interno
# ---------------------------------------------------------------------------

def create_initial_commit(config: ProjectConfig) -> CreatedItem:
    """
    Cria commit inicial no repositório com todos os arquivos do scaffold.

    - Adiciona todos os arquivos (git add -A)
    - Commit com mensagem padronizada
    - Retorna CreatedItem com status
    """
    target = config.project_path

    if not is_git_repo(target):
        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="skipped",
            message="repositório não inicializado",
        )

    try:
        # git add -A
        subprocess.run(
            ["git", "add", "-A"],
            cwd=target,
            check=True,
            capture_output=True,
            timeout=30,
        )

        # Commit inicial
        commit_msg = f"chore: scaffold inicial do projeto {config.project_name}\n\nGerado pelo Enterprise Scaffold Project Template v1.0.0"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=target,
            check=True,
            capture_output=True,
            timeout=30,
        )

        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="created",
            message="commit inicial criado",
        )
    except subprocess.CalledProcessError as e:
        # Se não há nada para commitar, não é erro
        stderr = e.stderr.decode(errors="replace").strip()
        if "nothing to commit" in stderr:
            return CreatedItem(
                path=target / ".git",
                kind="git",
                status="skipped",
                message="nada para commitar",
            )
        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="error",
            message=stderr,
        )


def tag_scaffold(config: ProjectConfig, version: str = "1.0.0") -> CreatedItem:
    """
    Cria tag anotada scaffold-v{version} no repositório.

    Args:
        config: Configuração do projeto
        version: Versão do scaffold (default: "1.0.0")

    Returns:
        CreatedItem com status da operação
    """
    target = config.project_path
    tag_name = f"scaffold-v{version}"

    if not is_git_repo(target):
        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="skipped",
            message="repositório não inicializado",
        )

    try:
        # Tag anotada com mensagem
        tag_msg = f"Projeto criado com Enterprise Scaffold Project Template v{version}"
        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", tag_msg],
            cwd=target,
            check=True,
            capture_output=True,
            timeout=10,
        )

        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="created",
            message=f"tag {tag_name} criada",
        )
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors="replace").strip()
        if "already exists" in stderr:
            return CreatedItem(
                path=target / ".git",
                kind="git",
                status="skipped",
                message=f"tag {tag_name} já existe",
            )
        return CreatedItem(
            path=target / ".git",
            kind="git",
            status="error",
            message=stderr,
        )


# ---------------------------------------------------------------------------
# Auxiliar interno
# ---------------------------------------------------------------------------

def _ensure_remote(target: Path, repo_url: str) -> None:
    """Adiciona remote 'origin' se não existir ainda. Silente em caso de erro."""
    try:
        result = subprocess.run(
            ["git", "remote"],
            cwd=target,
            check=True,
            capture_output=True,
            timeout=10,
        )
        existing = result.stdout.decode().split()
        if "origin" not in existing:
            subprocess.run(
                ["git", "remote", "add", "origin", repo_url],
                cwd=target,
                check=True,
                capture_output=True,
                timeout=10,
            )
    except subprocess.CalledProcessError:
        console.print(
            f"  [yellow]⚠️  Não foi possível adicionar remote origin: {repo_url}[/yellow]"
        )
