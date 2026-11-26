# -*- coding: utf-8 -*-  # noqa: UP009
"""
NOME: legacy_migrations.py
TITULO: Migrações de projetos gerados por versões antigas do scaffold
DATA: 26/11/2026 13:55
MODIFICADO: 26/11/2026 16:16
VERSÃO: 1.0.0
DEPEND: (stdlib)
STATUS: DEV

Usado pelo ``--upgrade``. Hoje cobre o ADR-005: os prompt files
(``.github/prompts/``) deixaram de ser gerados e viraram skills. Projetos
antigos ainda têm a pasta; ela vai inteira para backup
(``.github/prompts.bak-<AAAAMMDD-HHMMSS>``), decisão do dono do projeto em
26/11/2026. O conteúdo não é comparado, e nada é apagado.

Histórico:
    1.0.0 (26/11/2026): archive_legacy_prompts.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .config import CreatedItem, ProjectConfig

log = logging.getLogger(__name__)

_SP = ZoneInfo("America/Sao_Paulo")
LEGACY_PROMPTS_DIR = Path(".github") / "prompts"


def _destino_livre(origem: Path, carimbo: str) -> Path:
    """Primeiro ``prompts.bak-<carimbo>[-N]`` que ainda não existe."""
    base = origem.with_name(f"{origem.name}.bak-{carimbo}")
    destino, n = base, 0
    while destino.exists() or destino.is_symlink():
        n += 1
        destino = base.with_name(f"{base.name}-{n}")
    return destino


def archive_legacy_prompts(
    config: ProjectConfig, now: datetime | None = None
) -> CreatedItem:
    """
    Move ``.github/prompts/`` para ``.github/prompts.bak-<AAAAMMDD-HHMMSS>``.

    :param config: Configuração do projeto (usa ``project_path``).
    :type config: ProjectConfig
    :param now: Instante usado no nome do backup; default: agora em
        America/Sao_Paulo.
    :type now: datetime | None
    :return: ``updated`` (movido), ``skipped`` (sem a pasta) ou ``error``
        (falha de I/O; a pasta original fica onde estava).
    :rtype: CreatedItem

    :Example:

    >>> from pathlib import Path
    >>> LEGACY_PROMPTS_DIR.as_posix()
    '.github/prompts'
    """
    origem = config.project_path / LEGACY_PROMPTS_DIR
    if not origem.exists() and not origem.is_symlink():
        return CreatedItem(
            path=origem,
            kind="dir",
            status="skipped",
            message="sem .github/prompts/ legado (ADR-005)",
        )

    instante = now or datetime.now(_SP)
    destino = _destino_livre(origem, instante.strftime("%Y%m%d-%H%M%S"))
    try:
        shutil.move(str(origem), str(destino))
    except OSError as error:
        log.error("Falha ao mover %s para %s: %s", origem, destino, error)
        return CreatedItem(
            path=origem,
            kind="dir",
            status="error",
            message=f"não foi possível mover .github/prompts/: {error}",
        )
    log.info("Prompts legados movidos para %s", destino)
    return CreatedItem(
        path=destino,
        kind="dir",
        status="updated",
        message=(
            f"prompt files obsoletos (ADR-005) movidos para .github/{destino.name}/; "
            "as skills em .github/skills/ substituem. Apague o backup quando "
            "não precisar mais dele."
        ),
    )
