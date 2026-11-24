# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------
NOME..: copilot.py
LANG..: Python3
TITULO: Plugin de integração do GitHub Copilot no scaffold
DATA..: 23/06/2026 10:00
MODIFICADO: 24/11/2026 15:00
VERSÃO: 0.1.0
HOST..: local
LOCAL.: scripts/lib/ai/plugins/
OBS...: Encapsula toda a lógica de setup do GitHub Copilot:
        - Diretório docs/copilot
        - Symlinks .copilot-*
        - Regras e instruções Copilot
        - Cópia de copilot-instructions

DEPEND: scripts/lib/links.py, scripts/lib/templates.py, scripts/lib/project.py

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


class CopilotPlugin(AIPlugin):
    """
    Plugin de integração do GitHub Copilot no scaffold.

    Cria symlinks .copilot-*, gera regras e instruções Copilot,
    e copia os arquivos de instrução do template para o projeto.
    """

    name = "copilot"
    label = "GitHub Copilot"

    def get_dirs(self) -> list[str]:
        """
        Retorna diretórios exclusivos do GitHub Copilot.

        :return: Lista com o diretório docs/copilot.
        :rtype: list[str]

        >>> CopilotPlugin().get_dirs()
        ['docs/copilot']
        """
        return ["docs/copilot"]

    def get_files(self) -> list[tuple[str, str]]:
        """
        Retorna arquivos de template do Copilot.

        Os arquivos Copilot são gerados dinamicamente (não são templates
        estáticos), portanto esta lista está vazia.

        :return: Lista vazia.
        :rtype: list[tuple[str, str]]

        >>> CopilotPlugin().get_files()
        []
        """
        return []

    def collect_config(self, defaults: dict) -> dict:
        """
        Coleta configuração do Copilot (modo interativo).

        Solicita ao usuário o diretório compartilhado (.copilot-shared).

        :param defaults: Defaults mesclados (CLI + JSON config).
        :type defaults: dict
        :return: Dict com chave "shared_dir".
        :rtype: dict
        """
        from rich.prompt import Prompt

        from ...config import get_default_shared_dir

        shared_dir_str = Prompt.ask(
            "  [cyan]Diretório compartilhado[/cyan] [dim](.copilot-shared)[/dim]",
            default=str(defaults.get("shared_dir") or get_default_shared_dir()),
        ).strip()
        return {"shared_dir": shared_dir_str}

    def get_config_defaults(self, overrides: dict) -> dict:
        """
        Retorna defaults de configuração do Copilot (modo CI).

        :param overrides: Overrides vindos do CLI.
        :type overrides: dict
        :return: Dict com chave "shared_dir".
        :rtype: dict
        """
        from ...config import get_default_shared_dir

        return {
            "shared_dir": str(overrides.get("shared_dir") or get_default_shared_dir())
        }

    def setup(self, config: ProjectConfig) -> list[CreatedItem]:
        """
        Executa setup completo do GitHub Copilot em projeto recém-criado.

        Configura symlinks, gera regras, gera instruções e copia
        os arquivos de instrução do template.

        :param config: Configuração do projeto.
        :type config: ProjectConfig
        :return: Lista de itens criados.
        :rtype: list[CreatedItem]
        """
        from ... import links, project, templates

        results: list[CreatedItem] = []
        results.extend(links.setup_symlinks(config))
        results.append(templates.generate_copilot_rules(config))
        results.append(templates.generate_copilot_instructions(config))
        results.extend(project.copy_copilot_instructions(config))
        return results

    def upgrade(self, config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
        """
        Re-aplica configuração do GitHub Copilot em projeto existente.

        :param config: Configuração do projeto.
        :type config: ProjectConfig
        :param force: Se True, sobrescreve arquivos existentes.
        :type force: bool
        :return: Lista de itens processados.
        :rtype: list[CreatedItem]
        """
        from ... import links, project, templates

        results: list[CreatedItem] = []
        results.extend(links.setup_symlinks(config))
        results.append(templates.generate_copilot_rules(config))
        results.append(templates.generate_copilot_instructions(config))
        results.extend(project.copy_copilot_instructions(config, force=force))
        return results
