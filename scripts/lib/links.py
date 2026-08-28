"""
lib/links.py — Setup e verificação de symlinks .copilot-*.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console

from .config import SHARED_COPILOT_FILES, CreatedItem, LinkStatus, ProjectConfig

console = Console()


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def setup_symlinks(config: ProjectConfig) -> list[CreatedItem]:
    """
    Cria symlinks relativos dos arquivos .copilot-* do shared_dir para target_dir.

    Regras:
    - shared_dir não existe           → aviso, skip todos
    - arquivo ausente no shared_dir   → aviso, skip esse arquivo
    - symlink ok existente            → skipped
    - symlink quebrado                → recria
    - não existe                      → cria symlink relativo
    """
    results: list[CreatedItem] = []
    target = config.project_path
    shared = config.shared_dir

    if not shared.exists():
        console.print(
            f"  [yellow]⚠️  Diretório compartilhado não encontrado: {shared}[/yellow]\n"
            "     Symlinks .copilot-* não criados."
        )
        for name in SHARED_COPILOT_FILES:
            results.append(CreatedItem(
                path=target / name,
                kind="symlink",
                status="skipped",
                message=f"shared_dir não existe: {shared}",
            ))
        return results

    for name in SHARED_COPILOT_FILES:
        # Os arquivos compartilhados estão em shared_dir/rules/
        src = shared / "rules" / name
        dst = target / name

        if not src.exists():
            console.print(
                f"  [yellow]⚠️  Arquivo ausente em shared: {src}[/yellow]")
            results.append(CreatedItem(
                path=dst, kind="symlink", status="skipped",
                message=f"arquivo ausente em shared: {src}",
            ))
            continue

        # Calcula symlink relativo (portabilidade)
        try:
            rel_target = os.path.relpath(src, start=target)
        except ValueError:
            # No Windows, relpath pode falhar entre drives — usa absoluto como fallback
            rel_target = str(src)

        if dst.is_symlink():
            if dst.exists():
                # Symlink ok — verifica se aponta para o lugar certo
                current = os.readlink(dst)
                if current == rel_target:
                    results.append(CreatedItem(
                        path=dst, kind="symlink", status="skipped",
                        message="symlink ok",
                    ))
                    continue
            # Symlink quebrado ou apontando para lugar errado → recria
            dst.unlink()

        try:
            dst.symlink_to(rel_target)
            results.append(CreatedItem(
                path=dst, kind="symlink", status="created",
                message=f"→ {rel_target}",
            ))
        except OSError as e:
            results.append(CreatedItem(
                path=dst, kind="symlink", status="error", message=str(e),
            ))

    return results


def check_symlinks(target_dir: Path, shared_dir: Path) -> list[LinkStatus]:
    """
    Verifica status de cada symlink .copilot-* em target_dir.

    Retorna lista de LinkStatus:
    - 'ok'      → symlink existe e aponta para arquivo real
    - 'broken'  → symlink existe mas target não existe
    - 'missing' → symlink não existe no target_dir
    """
    results: list[LinkStatus] = []

    for name in SHARED_COPILOT_FILES:
        dst = target_dir / name

        if not dst.exists() and not dst.is_symlink():
            results.append(LinkStatus(
                name=name, target=None, status="missing"))
            continue

        if dst.is_symlink():
            resolved = dst.resolve()
            if resolved.exists():
                results.append(LinkStatus(
                    name=name, target=resolved, status="ok"))
            else:
                raw = Path(os.readlink(dst))
                results.append(LinkStatus(
                    name=name, target=raw, status="broken"))
        else:
            # Arquivo real (não é symlink) — reporta como ok
            results.append(LinkStatus(name=name, target=dst, status="ok"))

    return results
