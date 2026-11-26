"""
Flow: check-templates

Detectava drift de templates SpecKit entre o projeto e uma cópia "upstream"
mantida pelo scaffold (IMP-65 Fase 1).

Desde 26/11/2026 os templates SpecKit vêm só do instalador oficial
(``specify init``), e o scaffold não distribui mais uma cópia própria para
servir de upstream. A sincronização passa a ser feita pelo ``--upgrade``, que
reaplica o instalador. Este flow apenas informa isso.
"""

import argparse
import json
import logging

from ..ui import console

log = logging.getLogger(__name__)

SPECKIT_GERENCIADO_PELO_SPECIFY = (
    "Os templates SpecKit são gerenciados pelo instalador oficial (specify init). "
    "Para atualizá-los, use: scaffold.py --upgrade"
)


def flow_check_templates(args: argparse.Namespace) -> int:
    """
    Flow: informa que os templates SpecKit são sincronizados pelo ``--upgrade``.

    Args:
        args: Namespace com:
            - json_output: output JSON ao invés de texto

    Returns:
        2 (não há upstream de templates SpecKit no scaffold)
    """
    log.info(SPECKIT_GERENCIADO_PELO_SPECIFY)
    if getattr(args, "json_output", False):
        console.print(json.dumps({"error": SPECKIT_GERENCIADO_PELO_SPECIFY}, indent=2))
    else:
        console.print(
            f"\n[bold yellow]⚠️[/bold yellow]  {SPECKIT_GERENCIADO_PELO_SPECIFY}\n"
        )
    return 2
