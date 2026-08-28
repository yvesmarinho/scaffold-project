"""
lib/vscode.py — Geração de arquivos VS Code personalizados por domínio/linguagem.

Parte do scripts/scaffold.py — Enterprise Scaffold Project Template.

Gera:
  .vscode/settings.json   — configurações do editor por linguagem
  .vscode/mcp.json        — servidores MCP pré-selecionados por domínio
  .vscode/extensions.json — extensões recomendadas (BASE + DOMAIN + LANGUAGE)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import CreatedItem, DomainType, LanguageType, ProjectConfig
from . import file_merge

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extensões — 3 camadas: BASE + DOMAIN + LANGUAGE
# ---------------------------------------------------------------------------

BASE_EXTENSIONS: list[str] = [
    "github.copilot",
    "github.copilot-chat",
    "eamodio.gitlens",
    "mhutchie.git-graph",
    "usernamehw.errorlens",
    "EditorConfig.EditorConfig",
    "streetsidesoftware.code-spell-checker",
    "yzhang.markdown-all-in-one",
    "christian-kohler.path-intellisense",
    "donjayamanne.githistory",
    "ms-vscode.live-server",
]

DOMAIN_EXTENSIONS: dict[str, list[str]] = {
    "programming": [],  # linguagem define os extras
    "infrastructure": [
        "ms-azuretools.vscode-docker",
        "p1c2u.docker-compose",
        "exiasr.hadolint",
        "ms-vscode-remote.remote-containers",
        "ms-vscode-remote.remote-ssh",
        "HashiCorp.terraform",
        "redhat.vscode-yaml",
        "ms-kubernetes-tools.vscode-kubernetes-tools",
        "tim-koehler.helm-intellisense",
        "redhat.ansible",
        "signageos.signageos-vscode-sops",
    ],
    "analysis": [
        "ms-toolsai.jupyter",
        "ms-toolsai.vscode-jupyter-slideshow",
        "ms-toolsai.jupyter-keymap",
        "mechatroner.rainbow-csv",
        "GrapeCity.gc-excelviewer",
    ],
}

LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "python": [
        "ms-python.python",
        "ms-python.pylance",
        "astral-sh.uv",
        "ms-python.black-formatter",
        "ms-python.flake8",
        "ms-python.mypy-type-checker",
        "ms-python.debugpy",
        "njpwerner.autodocstring",
        "ms-python.isort",
        "KevinRose.vsc-python-indent",
    ],
    "typescript": [
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode",
        "ms-vscode.vscode-typescript-next",
        "orta.vscode-jest",
        "bradlc.vscode-tailwindcss",
        "ms-vscode.js-debug",
    ],
    "go": [
        "golang.go",
    ],
    "other": [],
}

# ---------------------------------------------------------------------------
# Settings globais (aplicados a todos os projetos)
# ---------------------------------------------------------------------------

_SETTINGS_GLOBAL: dict = {
    # Idioma e regionalização
    "locale.language": "pt-br",

    # GitHub Copilot e MCP
    "chat.mcp.autostart": True,
    "github.copilot.chat.enableMcp": True,
    "chat.promptFilesRecommendations": {
        "speckit.constitution": True,
        "speckit.specify": True,
        "speckit.plan": True,
        "speckit.tasks": True,
        "speckit.implement": True,
    },
    "chat.tools.terminal.autoApprove": {
        ".specify/scripts/bash/": True,
        ".specify/scripts/powershell/": True,
    },

    # Configurações gerais do editor
    "editor.tabSize": 4,
    "editor.insertSpaces": True,
    "editor.trimAutoWhitespace": True,
    "files.encoding": "utf8",
    "files.eol": "\n",
    "files.trimTrailingWhitespace": True,
    "files.insertFinalNewline": True,
}

# ---------------------------------------------------------------------------
# Settings por linguagem
# ---------------------------------------------------------------------------

_SETTINGS_BY_LANGUAGE: dict[str, dict] = {
    "python": {
        "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
        "python-envs.pythonProjects": [
            {
                "path": ".",
                "envManager": "astral-sh.uv:uv",
                "packageManager": "astral-sh.uv:uv",
            }
        ],
        "flake8.path": ["${workspaceFolder}/.venv/bin/flake8"],
        "flake8.args": [],
        "editor.defaultFormatter": "ms-python.black-formatter",
        "editor.formatOnSave": True,
        "python.linting.enabled": True,
        "python.linting.flake8Enabled": True,
        "python.linting.mypyEnabled": True,
        "python.analysis.typeCheckingMode": "basic",
        "editor.rulers": [88],
        "isort.args": ["--profile", "black"],
    },
    "typescript": {
        "editor.defaultFormatter": "esbenp.prettier-vscode",
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {"source.fixAll.eslint": True},
        "typescript.preferences.importModuleSpecifier": "relative",
        "editor.rulers": [100],
    },
    "go": {
        "go.useLanguageServer": True,
        "editor.formatOnSave": True,
        "editor.rulers": [120],
    },
    "other": {
        "editor.formatOnSave": True,
        "editor.rulers": [120],
    },
}

_SETTINGS_BY_DOMAIN: dict[str, dict] = {
    "infrastructure": {
        "editor.defaultFormatter": "redhat.vscode-yaml",
        "editor.formatOnSave": True,
        "yaml.schemas": {
            "https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json": "docker-compose*.yml",
        },
        "docker.showStartPage": False,
        "editor.rulers": [120],
    },
    "programming": {},
    "analysis": {
        "editor.formatOnSave": True,
        "editor.rulers": [100],
    },
}

# ---------------------------------------------------------------------------
# Servidores MCP por domínio
# ---------------------------------------------------------------------------

_ALL_MCP_SERVERS: dict[str, dict] = {
    "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"],
    },
    "sequential-thinking": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
    },
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
    },
    # Servidor GitHub via GitHub Copilot (HTTP — requer assinatura Copilot)
    "github": {
        "type": "http",
        "url": "https://api.githubcopilot.com/mcp/",
    },
    # Servidor GitHub via Docker oficial (stdio — requer Docker + PAT)
    # Usa ${input:github-token} resolvido pelo VS Code via seção "inputs"
    "io.github.github/github-mcp-server": {
        "type": "stdio",
        "command": "docker",
        "args": [
            "run", "-i", "--rm",
            "-e", "GITHUB_PERSONAL_ACCESS_TOKEN=${input:github-token}",
            "ghcr.io/github/github-mcp-server:1.4.0",
        ],
    },
    "sqlite": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", ".data/db.sqlite"],
    },
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
            "BRAVE_API_KEY": "${env:BRAVE_API_KEY}",
        },
    },
}

_MCP_BY_DOMAIN: dict[str, list[str]] = {
    "programming":    ["memory", "sequential-thinking", "filesystem", "github"],
    "infrastructure": ["memory", "sequential-thinking", "filesystem", "github", "sqlite"],
    "analysis":       ["memory", "sequential-thinking", "filesystem", "sqlite", "brave-search"],
}

# Padrões que identificam servidores GitHub não-oficiais (via npx args)
# ATENÇÃO: NÃO incluir "github-mcp-server" sem prefixo — matchearia falsamente
# a imagem Docker oficial "ghcr.io/github/github-mcp-server:*"
_UNOFFICIAL_GITHUB_ARG_PATTERNS: list[str] = [
    "@modelcontextprotocol/server-github",
    "mcp-server-github",
]

# Prefixo da imagem Docker oficial do GitHub MCP — não deve ser removida
_OFFICIAL_GITHUB_DOCKER_IMAGE = "ghcr.io/github/github-mcp-server"


# ---------------------------------------------------------------------------
# Normalização do servidor GitHub MCP
# ---------------------------------------------------------------------------

def normalize_github_mcp(servers: dict) -> tuple[dict, list[str]]:
    """
    Garante que o servidor GitHub MCP no mcp.json seja o oficial (HTTP).

    Critérios de substituição/remoção:
    - Entrada "github" com configuração diferente da oficial → substituída
    - Entrada com outro nome cujos args contenham padrões não-oficiais do
      GitHub MCP (ex: @modelcontextprotocol/server-github) → removida
    - Entrada com outro nome cuja URL aponte para github mas não seja a
      URL oficial → removida

    Args:
        servers: Dicionário ``servers`` do mcp.json.

    Returns:
        Tupla ``(servers_normalizados, lista_de_mudanças)``.

    Exemplos:
        >>> official = {"type": "http", "url": "https://api.githubcopilot.com/mcp/"}
        >>> old = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
        >>> result, changes = normalize_github_mcp({"memory": {}, "github": old})
        >>> result["github"] == official
        True
        >>> len(changes) == 1
        True

        >>> result2, changes2 = normalize_github_mcp({"github": official})
        >>> len(changes2) == 0
        True
    """
    official = _ALL_MCP_SERVERS["github"]
    normalized: dict = {}
    changes: list[str] = []

    for name, cfg in servers.items():
        if name == "github":
            if cfg != official:
                changes.append(
                    f"servers.github: substituído por servidor oficial "
                    f"(type=http, url={official['url']})"
                )
                normalized[name] = official
            else:
                normalized[name] = cfg
            continue

        # Detectar entradas não-github que são, na verdade, github não-oficial
        args: list[str] = cfg.get("args", [])
        url: str = cfg.get("url", "")
        official_url: str = official.get("url", "")

        is_unofficial_github = any(
            pattern in arg
            for pattern in _UNOFFICIAL_GITHUB_ARG_PATTERNS
            for arg in args
            # Excluir imagem Docker oficial: ghcr.io/github/github-mcp-server
            if _OFFICIAL_GITHUB_DOCKER_IMAGE not in arg
        ) or (
            "github" in url.lower()
            and url != official_url
        )

        if is_unofficial_github:
            changes.append(
                f"servers.{name}: removido (servidor GitHub não-oficial detectado)"
            )
        else:
            normalized[name] = cfg

    return normalized, changes


def _apply_github_normalization(mcp_path: Path) -> None:
    """
    Lê mcp.json, normaliza servidor GitHub e salva se houve mudanças.

    Args:
        mcp_path: Caminho para o arquivo .vscode/mcp.json.
    """
    try:
        data: dict = json.loads(mcp_path.read_text(encoding="utf-8"))
        servers: dict = data.get("servers", {})
        normalized, changes = normalize_github_mcp(servers)

        if not changes:
            return

        for change in changes:
            log.warning("🔄 MCP normalize: %s", change)

        data["servers"] = normalized
        mcp_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        log.info("✅ mcp.json normalizado (%d mudança(s))", len(changes))

    except Exception as exc:
        log.warning("⚠️  Falha ao normalizar mcp.json: %s", exc)


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------

def generate_settings(config: ProjectConfig) -> CreatedItem:
    """
    Gera `.vscode/settings.json` personalizado pela linguagem e domínio.

    Se arquivo existe, usa merge inteligente (BUG-16 fix).

    Camadas aplicadas em ordem (últimas sobrescrevem primeiras):
      1. _SETTINGS_GLOBAL      → configs universais (locale, encoding, etc.)
      2. _SETTINGS_BY_DOMAIN   → por domínio (infrastructure, programming, analysis)
      3. _SETTINGS_BY_LANGUAGE → por linguagem (python, typescript, go, other)
    """
    dest = config.project_path / ".vscode" / "settings.json"

    # Gerar conteúdo do template
    settings: dict = {}
    # Camada 1: Global (base)
    settings.update(_SETTINGS_GLOBAL)
    # Camada 2: Domínio
    settings.update(_SETTINGS_BY_DOMAIN.get(config.domain, {}))
    # Camada 3: Linguagem (mais específicos sobrescrevem)
    settings.update(_SETTINGS_BY_LANGUAGE.get(config.language, {}))

    if dest.exists():
        # FIX BUG P0: Usar merge_or_skip ao invés de skip incondicional
        template_content = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"
        return file_merge.merge_or_skip(dest, template_content, interactive=False)

    return _write_json(dest, settings)


def generate_mcp(config: ProjectConfig) -> CreatedItem:
    """
    Gera `.vscode/mcp.json` com servidores pré-selecionados pelo domínio.

    Se arquivo existe, usa merge inteligente (BUG-16 fix) seguido de
    normalização do servidor GitHub para garantir que seja o oficial HTTP.

    Preserva a seção ``inputs`` de arquivos existentes (necessária para
    servidores que usam ${input:*} — ex: github-mcp-server via Docker + PAT).
    """
    dest = config.project_path / ".vscode" / "mcp.json"

    server_names = _MCP_BY_DOMAIN.get(
        config.domain, ["memory", "sequential-thinking", "filesystem", "github"])
    servers = {name: _ALL_MCP_SERVERS[name]
               for name in server_names if name in _ALL_MCP_SERVERS}

    payload: dict = {"servers": servers}

    if dest.exists():
        # Preservar seção "inputs" existente antes do merge
        try:
            existing = json.loads(dest.read_text(encoding="utf-8"))
            if "inputs" in existing:
                payload["inputs"] = existing["inputs"]
        except Exception:
            pass
        # FIX BUG P0: Usar merge_or_skip ao invés de skip incondicional
        template_content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        result = file_merge.merge_or_skip(dest, template_content, interactive=False)
        # Garantir servidor GitHub oficial após merge (cobre casos não tratados pelo BUG-20)
        _apply_github_normalization(dest)
        return result

    return _write_json(dest, payload)


def generate_extensions(config: ProjectConfig) -> CreatedItem:
    """
    Gera `.vscode/extensions.json` com extensões recomendadas.

    Combina em 3 camadas:
      1. BASE_EXTENSIONS      → sempre incluídas
      2. DOMAIN_EXTENSIONS    → por domínio
      3. LANGUAGE_EXTENSIONS  → por linguagem

    Lista final deduplicada e ordenada. Se arquivo existe, usa merge inteligente (BUG-16 fix).
    """
    dest = config.project_path / ".vscode" / "extensions.json"

    combined: list[str] = list(BASE_EXTENSIONS)  # cópia
    combined.extend(DOMAIN_EXTENSIONS.get(config.domain, []))
    combined.extend(LANGUAGE_EXTENSIONS.get(config.language, []))

    # Deduplica preservando ordem de inserção
    seen: set[str] = set()
    unique: list[str] = []
    for ext in combined:
        if ext not in seen:
            seen.add(ext)
            unique.append(ext)

    payload = {"recommendations": sorted(unique)}

    if dest.exists():
        # FIX BUG P0: Usar merge_or_skip ao invés de skip incondicional
        template_content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        return file_merge.merge_or_skip(dest, template_content, interactive=False)

    return _write_json(dest, payload)


# ---------------------------------------------------------------------------
# Auxiliar interno
# ---------------------------------------------------------------------------

def generate_tasks(config: ProjectConfig) -> CreatedItem:
    """
    Gera `.vscode/tasks.json` com os targets padrão do Makefile como tasks VS Code.

    Tasks: install-deps, dev, build, test (isDefault), lint, format, clean.
    Se arquivo existe, usa merge inteligente via VSCodeConfigMerger (BUG-16 fix).
    """
    dest = config.project_path / ".vscode" / "tasks.json"

    tasks = [
        {
            "label": "make: install-deps",
            "type": "shell",
            "command": "make install-deps",
            "group": "build",
            "problemMatcher": [],
        },
        {
            "label": "make: dev",
            "type": "shell",
            "command": "make dev",
            "group": {"kind": "build", "isDefault": True},
            "problemMatcher": [],
        },
        {
            "label": "make: build",
            "type": "shell",
            "command": "make build",
            "group": "build",
            "problemMatcher": [],
        },
        {
            "label": "make: test",
            "type": "shell",
            "command": "make test",
            "group": {"kind": "test", "isDefault": True},
            "problemMatcher": [],
        },
        {
            "label": "make: lint",
            "type": "shell",
            "command": "make lint",
            "group": "test",
            "problemMatcher": [],
        },
        {
            "label": "make: format",
            "type": "shell",
            "command": "make format",
            "group": "build",
            "problemMatcher": [],
        },
        {
            "label": "make: clean",
            "type": "shell",
            "command": "make clean",
            "group": "build",
            "problemMatcher": [],
        },
    ]

    payload = {"version": "2.0.0", "tasks": tasks}

    if dest.exists():
        # FIX BUG P0: Usar merge_or_skip (VSCodeConfigMerger) ao invés de skip incondicional
        template_content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        return file_merge.merge_or_skip(dest, template_content, interactive=False)

    return _write_json(dest, payload)


def generate_launch(config: ProjectConfig) -> CreatedItem:
    """
    Gera `.vscode/launch.json` com configurações de debug por linguagem.

    Python: debugpy (módulo atual + pytest)
    TypeScript: js-debug (arquivo atual + jest)
    Go: dlv (teste + execução direta)
    other: generic shell run

    Se arquivo existe, usa merge inteligente via VSCodeConfigMerger (BUG-16 fix).
    """
    dest = config.project_path / ".vscode" / "launch.json"

    configurations: list[dict] = _LAUNCH_BY_LANGUAGE.get(
        config.language, _LAUNCH_BY_LANGUAGE["other"]
    )

    payload = {"version": "0.2.0", "configurations": configurations}

    if dest.exists():
        # FIX BUG P0: Usar merge_or_skip (VSCodeConfigMerger) ao invés de skip incondicional
        template_content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        return file_merge.merge_or_skip(dest, template_content, interactive=False)

    return _write_json(dest, payload)


# ---------------------------------------------------------------------------
# Launch configurations per language
# ---------------------------------------------------------------------------

_LAUNCH_BY_LANGUAGE: dict[str, list[dict]] = {
    "python": [
        {
            "name": "Python: módulo atual",
            "type": "debugpy",
            "request": "launch",
            "module": "${fileBasenameNoExtension}",
            "justMyCode": True,
        },
        {
            "name": "Python: pytest",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["${workspaceFolder}/tests", "-v"],
            "justMyCode": False,
        },
    ],
    "typescript": [
        {
            "name": "TypeScript: arquivo atual",
            "type": "node",
            "request": "launch",
            "program": "${file}",
            "runtimeArgs": ["-r", "ts-node/register"],
            "sourceMaps": True,
            "outFiles": ["${workspaceFolder}/dist/**/*.js"],
        },
        {
            "name": "TypeScript: Jest",
            "type": "node",
            "request": "launch",
            "runtimeExecutable": "npx",
            "runtimeArgs": ["jest", "--runInBand", "--no-coverage"],
            "sourceMaps": True,
            "console": "integratedTerminal",
        },
    ],
    "go": [
        {
            "name": "Go: arquivo atual",
            "type": "go",
            "request": "launch",
            "mode": "debug",
            "program": "${file}",
        },
        {
            "name": "Go: testes do pacote",
            "type": "go",
            "request": "launch",
            "mode": "test",
            "program": "${workspaceFolder}",
            "args": ["-v", "-run", "Test"],
        },
    ],
    "other": [
        {
            "name": "Shell: script atual",
            "type": "node",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
        },
    ],
}


def generate_workspace(config: ProjectConfig) -> CreatedItem:
    """
    Gera `[project-name].code-workspace` com configurações MCP integradas.

    Inclui:
    - Folders (path atual)
    - Settings básicos (formatOnSave, rulers, etc)
    - Tasks do Makefile
    - Launch configurations vazias
    - **MCP servers** (dinamicamente por domínio) ⭐ FIX BUG

    Não sobrescreve se já existe.
    """
    dest = config.project_path / f"{config.project_name}.code-workspace"
    if dest.exists():
        return CreatedItem(path=dest, kind="file", status="skipped", message="já existe")

    # Get MCP servers for this domain
    server_names = _MCP_BY_DOMAIN.get(
        config.domain, ["memory", "sequential-thinking", "filesystem", "github"])
    mcp_servers = {name: _ALL_MCP_SERVERS[name]
                   for name in server_names if name in _ALL_MCP_SERVERS}

    # Get settings for this language/domain
    settings: dict = {}
    settings.update(_SETTINGS_BY_DOMAIN.get(config.domain, {}))
    settings.update(_SETTINGS_BY_LANGUAGE.get(config.language, {}))

    # Add base settings
    settings.update({
        "editor.formatOnSave": True,
        "editor.rulers": [88, 120],
        "files.trimTrailingWhitespace": True,
        "files.insertFinalNewline": True,
    })

    workspace_config = {
        "folders": [{"path": "."}],
        "settings": settings,
        "mcp": {
            "servers": mcp_servers
        },
        "tasks": {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "make: install-deps",
                    "type": "shell",
                    "command": "make install-deps",
                    "group": "build",
                    "problemMatcher": []
                },
                {
                    "label": "make: dev",
                    "type": "shell",
                    "command": "make dev",
                    "group": {"kind": "build", "isDefault": True},
                    "problemMatcher": []
                },
                {
                    "label": "make: build",
                    "type": "shell",
                    "command": "make build",
                    "group": "build",
                    "problemMatcher": []
                },
                {
                    "label": "make: test",
                    "type": "shell",
                    "command": "make test",
                    "group": {"kind": "test", "isDefault": True},
                    "problemMatcher": []
                },
                {
                    "label": "make: lint",
                    "type": "shell",
                    "command": "make lint",
                    "group": "test",
                    "problemMatcher": []
                },
                {
                    "label": "make: format",
                    "type": "shell",
                    "command": "make format",
                    "group": "build",
                    "problemMatcher": []
                },
                {
                    "label": "make: clean",
                    "type": "shell",
                    "command": "make clean",
                    "group": "build",
                    "problemMatcher": []
                }
            ]
        },
        "launch": {
            "version": "0.2.0",
            "configurations": []
        }
    }

    return _write_json(dest, workspace_config)


# ---------------------------------------------------------------------------
# Auxiliar interno
# ---------------------------------------------------------------------------

def _write_json(dest: Path, data: dict) -> CreatedItem:
    """Serializa dict como JSON formatado e grava em dest."""
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(
            data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return CreatedItem(path=dest, kind="file", status="created")
    except OSError as e:
        return CreatedItem(path=dest, kind="file", status="error", message=str(e))
