"""
lib/config.py — ProjectConfig dataclass, constantes e paths.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Versão do scaffold e data de sincronização do SpecKit
# ---------------------------------------------------------------------------
SCAFFOLD_VERSION = "1.7.1"

# Data da última atualização dos assets SpecKit neste template.
# Atualizar manualmente sempre que agents/prompts forem modificados.
SPECKIT_SYNC_DATE = "2026-03-05"

# ---------------------------------------------------------------------------
# Caminhos padrão
# ---------------------------------------------------------------------------
DEFAULT_SHARED_DIR = Path.home() / "Documentos" / "DevOps" / ".copilot-shared"
DEFAULT_TARGET_DIR = Path.home()

# ---------------------------------------------------------------------------
# Arquivo de configuração customizável
# ---------------------------------------------------------------------------
CONFIG_FILE = Path(__file__).parent.parent.parent / ".scaffold-config.json"


def load_user_config() -> dict[str, Any]:
    """
    Carrega configurações customizadas do arquivo .scaffold-config.json.

    Retorna dict vazio se arquivo não existir ou houver erro de parse.
    Os valores do JSON sobrescrevem os defaults hardcoded.
    """
    if not CONFIG_FILE.exists():
        logger.debug("Config file not found: %s", CONFIG_FILE)
        return {}

    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            config_data = json.load(f)
            logger.debug("Loaded config from: %s", CONFIG_FILE)
            return config_data
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON in config file %s: %s", CONFIG_FILE, exc)
        return {}
    except Exception as exc:
        logger.warning("Error reading config file %s: %s", CONFIG_FILE, exc)
        return {}


def get_default_target_dir() -> Path:
    """Retorna o diretório padrão onde novos projetos serão criados."""
    config = load_user_config()
    target_dir_str = config.get("defaults", {}).get("target_dir")

    if target_dir_str:
        # Expandir ~ para home directory
        expanded = os.path.expanduser(target_dir_str)
        return Path(expanded)

    return DEFAULT_TARGET_DIR


def get_default_shared_dir() -> Path:
    """Retorna o diretório de arquivos compartilhados (.copilot-shared)."""
    config = load_user_config()
    shared_dir_str = config.get("defaults", {}).get("shared_dir")

    if shared_dir_str:
        expanded = os.path.expanduser(shared_dir_str)
        return Path(expanded)

    return DEFAULT_SHARED_DIR


# Pós-IMP-13: apenas um arquivo copilot ativo (consolidado de 5 → 1)
SHARED_COPILOT_FILES: list[str] = [
    ".copilot-rules.md",
]

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------
DomainType = Literal["programming", "infrastructure", "analysis"]
LanguageType = Literal["python", "typescript", "go", "other"]
ExtraProfilesMode = Literal["domain-only", "all", "custom"]
AiAssistantType = Literal["claude", "copilot", "both", "none"]

# Mantido para retrocompatibilidade. Após a refatoração para plugins,
# os valores válidos são gerados dinamicamente por ai.get_valid_values().
VALID_AI_ASSISTANTS: list[str] = ["claude", "copilot", "both", "none"]

# ---------------------------------------------------------------------------
# Perfis de domínio
# ---------------------------------------------------------------------------

# Perfil principal por domínio (copiado sempre)
DOMAIN_DEFAULT_PROFILES: dict[str, str] = {
    "programming":    "devops-programming",
    "infrastructure": "devops-infrastructure",
    "analysis":       "devops-analysis",
}

# Todos os perfis selecionáveis (excluindo o transversal de segurança)
ALL_SELECTABLE_PROFILES: list[str] = [
    "devops-programming",
    "devops-infrastructure",
    "devops-analysis",
]

# Perfil transversal — copiado silenciosamente em todos os projetos (D-20)
SPECKIT_TRANSVERSAL_PROFILES: list[str] = ["devops-security"]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ProjectConfig:
    """Configuração completa de um projeto scaffold."""

    project_name: str                   # slug kebab-case, ex: my-api-v2
    project_title: str                  # legível, ex: My API v2
    description: str                    # 1 frase
    domain: DomainType                  # programming | infrastructure | analysis
    language: LanguageType              # python | typescript | go | other
    github_repo: str | None             # URL GitHub ou None
    shared_dir: Path                    # caminho para .copilot-shared
    target_dir: Path                    # diretório PAI onde criar a pasta do projeto
    created_at: str                     # ISO8601 timestamp
    # perfis extras além do domínio (D-21)
    extra_profiles: list[str] = field(default_factory=list)
    # assistente(s) de IA ativo(s): claude | copilot | both | none
    ai_assistant: AiAssistantType = "both"

    @property
    def project_path(self) -> Path:
        """
        Retorna o caminho completo do projeto.

        Lógica de detecção:
        1. Se target_dir tem .scaffold-state.yaml → upgrade in-place, retorna target_dir
        2. Se target_dir.name == project_name → evita duplicação, retorna target_dir
        3. Caso contrário → retorna target_dir / project_name (modo normal)
        """
        # Upgrade in-place: se .scaffold-state.yaml existe em target_dir, é o projeto
        state_file = self.target_dir / ".scaffold-state.yaml"
        if state_file.exists():
            return self.target_dir.resolve()

        # Evita duplicação: se target_dir.name == project_name, não concatena novamente
        if self.target_dir.resolve().name == self.project_name:
            return self.target_dir.resolve()

        # Modo normal: target_dir é o pai, concatena com project_name
        return self.target_dir / self.project_name


@dataclass
class CreatedItem:
    """Resultado de uma operação de criação (pasta, arquivo, symlink, git)."""

    path: Path
    kind: Literal["dir", "file", "symlink", "git"]
    status: Literal["created", "skipped", "error"]
    message: str = ""


@dataclass
class LinkStatus:
    """Resultado da verificação de um symlink .copilot-*."""

    name: str
    target: Path | None
    status: Literal["ok", "broken", "missing"]


# ---------------------------------------------------------------------------
# Domínios válidos e linguagens válidas
# ---------------------------------------------------------------------------
VALID_DOMAINS: list[str] = ["programming", "infrastructure", "analysis"]
VALID_LANGUAGES: list[str] = ["python", "typescript", "go", "other"]
