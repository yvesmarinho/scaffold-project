# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------
NOME..: claude.py
LANG..: Python3
TITULO: Plugin de integração do Claude Code (Anthropic) no scaffold
DATA..: 23/06/2026 10:00
MODIFICADO: 24/11/2026 15:00
VERSÃO: 0.1.0
HOST..: local
LOCAL.: scripts/lib/ai/plugins/
OBS...: Encapsula toda a lógica de setup do Claude Code:
        - Arquivos de template (CLAUDE.md, .claude/settings.json)
        - Cópia de configuração Claude (commands, skills)

DEPEND: scripts/lib/project.py

-------------------------------------------------------------------------
Modifications.....:
 Date          Rev    Author           Description
 23/06/2026    1      scaffold         Elaboração

-------------------------------------------------------------------------
STATUS: DEV
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..base import AIPlugin

if TYPE_CHECKING:
    from ...config import CreatedItem, ProjectConfig


class ClaudePlugin(AIPlugin):
    """
    Plugin de integração do Claude Code (Anthropic) no scaffold.

    Cria CLAUDE.md, .claude/settings.json e copia commands/skills
    da pasta template para o projeto gerado.
    """

    name = "claude"
    label = "Claude Code (Anthropic)"

    def get_dirs(self) -> list[str]:
        """
        Retorna diretórios exclusivos do Claude Code.

        Nota: .claude/, .claude/commands e .claude/skills já estão em
        DIRS_BASE de project.py, portanto não precisam ser repetidos aqui.

        :return: Lista vazia (diretórios já declarados em DIRS_BASE).
        :rtype: list[str]

        >>> ClaudePlugin().get_dirs()
        []
        """
        return []

    def get_files(self) -> list[tuple[str, str]]:
        """
        Retorna os templates de arquivos exclusivos do Claude Code.

        Delega para project.get_claude_files() para manter os templates
        centralizados em project.py.

        :return: Lista de (caminho_relativo, conteúdo_template).
        :rtype: list[tuple[str, str]]
        """
        from ...project import get_claude_files

        return get_claude_files()

    def collect_config(self, defaults: dict) -> dict:
        """
        Coleta configuração específica do Claude Code (modo interativo).

        O Claude Code não requer prompts adicionais além dos padrão.

        :param defaults: Defaults mesclados (CLI + JSON config).
        :type defaults: dict
        :return: Dict vazio (sem prompts extras).
        :rtype: dict

        >>> ClaudePlugin().collect_config({})
        {}
        """
        return {}

    def get_config_defaults(self, overrides: dict) -> dict:
        """
        Retorna defaults de configuração do Claude Code (modo CI).

        :param overrides: Overrides vindos do CLI.
        :type overrides: dict
        :return: Dict vazio (sem defaults extras).
        :rtype: dict

        >>> ClaudePlugin().get_config_defaults({})
        {}
        """
        return {}

    def setup(self, config: ProjectConfig) -> list[CreatedItem]:
        """
        Executa setup completo do Claude Code em projeto recém-criado.

        Copia CLAUDE.md personalizado, settings.json e demais assets
        Claude (commands, skills) do template para o projeto.

        :param config: Configuração do projeto.
        :type config: ProjectConfig
        :return: Lista de itens criados.
        :rtype: list[CreatedItem]
        """
        from ...project import copy_claude_config

        return list(copy_claude_config(config))

    def upgrade(self, config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
        """
        Re-aplica configuração do Claude Code em projeto existente.

        :param config: Configuração do projeto.
        :type config: ProjectConfig
        :param force: Se True, sobrescreve arquivos existentes.
        :type force: bool
        :return: Lista de itens processados.
        :rtype: list[CreatedItem]
        """
        from ...project import copy_claude_config

        return list(copy_claude_config(config, force=force))
