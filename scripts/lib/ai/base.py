# -*- coding: utf-8 -*-
"""
-------------------------------------------------------------------------
NOME..: base.py
LANG..: Python3
TITULO: Classe base abstrata para plugins de assistente de IA
DATA..: 23/06/2026 10:00
MODIFICADO: 24/11/2026 15:00
VERSÃO: 0.1.0
HOST..: local
LOCAL.: scripts/lib/ai/
OBS...: Cada plugin encapsula toda a lógica de setup/upgrade de um AI
        específico: diretórios a criar, arquivos a gerar, prompts
        interativos e operações de cópia.

        Para adicionar um novo AI:
        1. Crie scripts/lib/ai/plugins/meu_ai.py implementando AIPlugin
        2. Registre em scripts/lib/ai/__init__.py com register(MeuAIPlugin())
        Nenhum outro arquivo precisa ser alterado.

DEPEND: (nenhuma)

-------------------------------------------------------------------------
Modifications.....:
 Date          Rev    Author           Description
 23/06/2026    1      scaffold         Elaboração

-------------------------------------------------------------------------
STATUS: DEV
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import CreatedItem, ProjectConfig


class AIPlugin(ABC):
    """
    Plugin base para integração de assistente de IA no scaffold.

    Subclasses devem definir os atributos de classe `name` e `label`,
    e implementar pelo menos `setup()`.
    """

    #: Identificador único (ex: "claude", "copilot"). Usado como chave no registry.
    name: str = ""

    #: Nome legível para exibição nos menus e logs.
    label: str = ""

    # ------------------------------------------------------------------
    # Estrutura
    # ------------------------------------------------------------------

    def get_dirs(self) -> list[str]:
        """
        Retorna lista de diretórios relativos a criar quando este AI está ativo.

        :return: Lista de caminhos relativos (ex: ["docs/copilot"]).
        :rtype: list[str]

        >>> AIPlugin().get_dirs()
        []
        """
        return []

    def get_files(self) -> list[tuple[str, str]]:
        """
        Retorna lista de (caminho_relativo, conteúdo_template) de arquivos
        a criar quando este AI está ativo.

        Os templates aceitam os mesmos placeholders de project.py:
        {{PROJECT_NAME}}, {{PROJECT_TITLE}}, {{CREATED_AT}}, etc.

        :return: Lista de (path, template_string).
        :rtype: list[tuple[str, str]]

        >>> AIPlugin().get_files()
        []
        """
        return []

    # ------------------------------------------------------------------
    # Configuração interativa
    # ------------------------------------------------------------------

    def collect_config(self, defaults: dict) -> dict:
        """
        Modo interativo: exibe prompts específicos deste AI e retorna um dict
        com os valores coletados que serão mesclados na construção de ProjectConfig.

        Chaves retornadas comuns: "shared_dir".

        :param defaults: Defaults mesclados (CLI + JSON config).
        :type defaults: dict
        :return: Dict de configuração específica do plugin.
        :rtype: dict

        >>> AIPlugin().collect_config({})
        {}
        """
        return {}

    def get_config_defaults(self, overrides: dict) -> dict:
        """
        Modo CI/headless: retorna valores padrão sem prompts interativos.

        Mesmo contrato que collect_config(), sem exibir nada ao usuário.

        :param overrides: Overrides vindos do CLI / .scaffold-config.json.
        :type overrides: dict
        :return: Dict de configuração com valores padrão.
        :rtype: dict

        >>> AIPlugin().get_config_defaults({})
        {}
        """
        return {}

    # ------------------------------------------------------------------
    # Operações de setup / upgrade
    # ------------------------------------------------------------------

    @abstractmethod
    def setup(self, config: ProjectConfig) -> list[CreatedItem]:
        """
        Executa toda a configuração deste AI em um projeto recém-criado.

        Chamado por flows/new_project.py para cada plugin ativo.

        :param config: Configuração completa do projeto.
        :type config: ProjectConfig
        :return: Lista de itens criados/gerados.
        :rtype: list[CreatedItem]
        """
        ...

    def upgrade(self, config: ProjectConfig, force: bool = False) -> list[CreatedItem]:
        """
        Re-aplica a configuração deste AI a um projeto já existente (upgrade).

        Por padrão delega para setup(). Sobrescreva quando a lógica de upgrade
        difere da criação inicial (ex: precisar de --force nos arquivos).

        :param config: Configuração do projeto existente.
        :type config: ProjectConfig
        :param force: Se True, sobrescreve arquivos que já existem.
        :type force: bool
        :return: Lista de itens processados.
        :rtype: list[CreatedItem]
        """
        return self.setup(config)

    def __repr__(self) -> str:
        return f"<AIPlugin name={self.name!r} label={self.label!r}>"
