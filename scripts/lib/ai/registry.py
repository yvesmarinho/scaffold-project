# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------
NOME..: registry.py
LANG..: Python3
TITULO: Registro central de plugins de IA
DATA..: 23/06/2026 10:00
MODIFICADO: 24/11/2026 15:00
VERSÃO: 0.1.0
HOST..: local
LOCAL.: scripts/lib/ai/
OBS...: O registro é um dict ordenado: a ordem de inserção define a
        ordem de exibição no menu interativo.

        Para adicionar um novo AI ao scaffold:
        1. Implemente AIPlugin em scripts/lib/ai/plugins/seu_ai.py
        2. Importe e registre em scripts/lib/ai/__init__.py:
               from .plugins.seu_ai import SeuAIPlugin
               register(SeuAIPlugin())
        Nenhum outro arquivo precisa ser modificado.

DEPEND: (nenhuma)

-------------------------------------------------------------------------
Modifications.....:
 Date          Rev    Author           Description
 23/06/2026    1      scaffold         Elaboração

-------------------------------------------------------------------------
STATUS: DEV
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import AIPlugin

# Dict ordenado: name → plugin instance
REGISTRY: dict[str, AIPlugin] = {}


def register(plugin: AIPlugin) -> None:
    """
    Registra um plugin de IA.

    :param plugin: Instância do plugin a registrar.
    :type plugin: AIPlugin
    :raises ValueError: Se `plugin.name` estiver vazio ou já registrado.

    >>> class P:
    ...     name = "x"; label = "X"
    ...     def setup(self, c): return []
    >>> # register(P())  # funcionaria se AIPlugin fosse importado
    """
    if not plugin.name:
        raise ValueError("AIPlugin.name não pode ser vazio")
    if plugin.name in REGISTRY:
        raise ValueError(f"Plugin '{plugin.name}' já registrado")
    REGISTRY[plugin.name] = plugin


def resolve_plugins(ai_assistant: str) -> list[AIPlugin]:
    """
    Retorna a lista de plugins ativos para o valor de ai_assistant.

    "both"     → todos os plugins registrados (na ordem de registro)
    "none"     → lista vazia
    "<nome>"   → [REGISTRY[nome]] se existir, [] caso contrário

    :param ai_assistant: Valor configurado (claude, copilot, both, none, ...).
    :type ai_assistant: str
    :return: Lista de plugins ativos.
    :rtype: list[AIPlugin]

    >>> resolve_plugins("none")
    []
    >>> resolve_plugins("inexistente")
    []
    """
    if ai_assistant == "both":
        return list(REGISTRY.values())
    if ai_assistant == "none":
        return []
    plugin = REGISTRY.get(ai_assistant)
    return [plugin] if plugin else []


def get_plugin_menu_options() -> list[tuple[str, str]]:
    """
    Retorna as opções para o menu interativo de seleção de AI, na ordem:
    [("both", "<label1> + <label2> + ..."), ("<name1>", "<label1>"), ..., ("none", "Nenhum")]

    :return: Lista de (valor, descrição) para exibição no menu.
    :rtype: list[tuple[str, str]]

    >>> opts = get_plugin_menu_options()
    >>> opts[0][0]   # sempre "both" como primeiro
    'both'
    >>> opts[-1][0]  # sempre "none" como último
    'none'
    """
    all_labels = " + ".join(p.label for p in REGISTRY.values())
    return [
        ("both", all_labels or "Todos"),
        *[(p.name, p.label) for p in REGISTRY.values()],
        ("none", "Nenhum"),
    ]


def get_valid_values() -> list[str]:
    """
    Retorna todos os valores válidos para ai_assistant, incluindo os plugins registrados.

    :return: Lista de strings válidas.
    :rtype: list[str]

    >>> get_valid_values()
    ['both', 'none']
    """
    return ["both", *REGISTRY.keys(), "none"]
