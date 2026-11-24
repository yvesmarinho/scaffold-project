# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------
NOME..: __init__.py
LANG..: Python3
TITULO: API pública do pacote de plugins de IA
DATA..: 23/06/2026 10:00
MODIFICADO: 24/11/2026 15:00
VERSÃO: 0.1.0
HOST..: local
LOCAL.: scripts/lib/ai/
OBS...: Registra os plugins na ordem desejada de exibição no menu
        (claude primeiro, copilot segundo). Para adicionar novo AI:
        1. Crie scripts/lib/ai/plugins/meu_ai.py
        2. Importe e registre abaixo com register(MeuAIPlugin())

DEPEND: (nenhuma)

-------------------------------------------------------------------------
Modifications.....:
 Date          Rev    Author           Description
 23/06/2026    1      scaffold         Elaboração

-------------------------------------------------------------------------
STATUS: DEV
"""

from .plugins.claude import ClaudePlugin
from .plugins.copilot import CopilotPlugin
from .registry import (
    REGISTRY,
    get_plugin_menu_options,
    get_valid_values,
    register,
    resolve_plugins,
)

# Registrar na ordem desejada no menu (claude primeiro, copilot segundo)
register(ClaudePlugin())
register(CopilotPlugin())

__all__ = [
    "REGISTRY",
    "register",
    "resolve_plugins",
    "get_plugin_menu_options",
    "get_valid_values",
    "ClaudePlugin",
    "CopilotPlugin",
]
