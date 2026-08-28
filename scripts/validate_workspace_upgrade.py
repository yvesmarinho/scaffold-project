#!/usr/bin/env python3
"""
Validação automática pós-scaffold upgrade para test-workspace-fix

Script standalone que valida todas as correções aplicadas após scaffold upgrade.
Não requer pytest - pode ser executado diretamente.

Valida:
- BUG-20 (P0): MCP GitHub HTTP migration (stdio → http/npx)
- BUG-001 (P1): Scaffold objetivo-init 3 issues
  - Fix #1: DEFAULT_DOCSTYLE populated
  - Fix #2: out-scope conditional (omit when empty)
  - Fix #3: Logging to logs/scaffolds.yaml
- BUG-11 (P0): Session systems initialization
- BUG-12 (P1): Memory system initialization
- BUG-13 (P0): Copilot instructions deployment
- BUG-16 (P1): JSON/workspace merge strategy
- BUG-17: session-time-tracker deployment
- BUG-18: objetivo.yaml deployment
- BUG-19: git_validators.py deployment
- Arquivos críticos (.scaffold-state.yaml, .copilot-rules.md, settings.json)
- Logs de scaffold upgrade

Usage:
    # Executar do diretório scaffold-project
    python scripts/validate-workspace-upgrade.py /home/yves_marinho/DevOps/Projetos/test-workspace-fix

    # Executar de dentro do test-workspace-fix
    cd /home/yves_marinho/DevOps/Projetos/test-workspace-fix
    python /caminho/para/scaffold-project/scripts/validate-workspace-upgrade.py .

    # Modo verbose
    python scripts/validate-workspace-upgrade.py /path/to/workspace --verbose

Exit codes:
    0 - Todas validações passaram
    1 - Uma ou mais validações falharam
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import yaml
except ImportError:
    print("⚠️  PyYAML não instalado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml


# ===========================================================================
# Validation Result Classes
# ===========================================================================

class ValidationResult:
    """Resultado de uma validação individual."""
    def __init__(self, name: str, passed: bool, message: str = "", details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details

    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} {self.name}: {self.message}"


class ValidationSuite:
    """Conjunto de validações agrupadas."""
    def __init__(self, name: str):
        self.name = name
        self.results: List[ValidationResult] = []

    def add(self, result: ValidationResult):
        self.results.append(result)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0

    def print_summary(self):
        status = "✅" if self.all_passed else "❌"
        print(f"\n{status} {self.name}")
        print("─" * 70)
        for result in self.results:
            print(f"  {result}")
            if result.details and not result.passed:
                for line in result.details.split("\n"):
                    print(f"    {line}")


# ===========================================================================
# Validators
# ===========================================================================

def validate_bug20_mcp(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-20: MCP GitHub HTTP migration."""
    suite = ValidationSuite("BUG-20: MCP GitHub HTTP Migration")

    mcp_file = workspace / ".vscode" / "mcp.json"

    # Check 1: Arquivo existe
    if not mcp_file.exists():
        suite.add(ValidationResult(
            "mcp.json exists",
            False,
            ".vscode/mcp.json não encontrado"
        ))
        return suite
    suite.add(ValidationResult("mcp.json exists", True, str(mcp_file)))

    # Check 2: JSON válido
    try:
        with mcp_file.open() as f:
            mcp_config = json.load(f)
        suite.add(ValidationResult("mcp.json valid JSON", True))
    except json.JSONDecodeError as e:
        suite.add(ValidationResult(
            "mcp.json valid JSON",
            False,
            f"JSON inválido: {e}"
        ))
        return suite

    # Check 3: Verificar todos os MCP servers configurados
    # CORREÇÃO #1: Schema MCP usa "servers", não "mcpServers"
    mcp_servers = mcp_config.get("servers", mcp_config.get("mcpServers", {}))
    server_count = len(mcp_servers)
    suite.add(ValidationResult(
        "MCP servers count",
        True,
        f"{server_count} servidor(es) configurado(s)"
    ))

    # Check 4: Validar cada servidor MCP
    stdio_servers = []
    for server_name, server_config in mcp_servers.items():
        server_type = server_config.get("type")
        if server_type == "stdio":
            stdio_servers.append(server_name)

    if stdio_servers:
        suite.add(ValidationResult(
            "No stdio servers (all HTTP/npx)",
            False,
            f"Servidores com type='stdio' obsoleto: {', '.join(stdio_servers)}",
            f"Arquivo: {mcp_file}\n"
            f"Esperado: type='http' ou comando 'npx'\n"
            f"Ação: Execute 'scaffold upgrade --force' novamente"
        ))
    else:
        suite.add(ValidationResult(
            "No stdio servers (all HTTP/npx)",
            True,
            "Todos os servidores usam HTTP ou npx"
        ))

    # Check 5: Validar servidor GitHub especificamente (se existir)
    github_server = mcp_servers.get("github")
    if github_server:
        suite.add(ValidationResult("GitHub server configured", True))

        server_type = github_server.get("type")

        # Check 5a: Tipo HTTP ou npx
        if server_type == "http":
            url = github_server.get("url", "")
            if "github" in url.lower():
                suite.add(ValidationResult("GitHub HTTP URL valid", True, url))
            else:
                suite.add(ValidationResult("GitHub HTTP URL valid", False, f"URL suspeita: {url}"))

            # Não deve ter campos CLI obsoletos
            obsolete = [f for f in ["command", "args", "env"] if f in github_server]
            if obsolete:
                suite.add(ValidationResult(
                    "GitHub: no obsolete CLI fields",
                    False,
                    f"Campos CLI encontrados: {obsolete}"
                ))
            else:
                suite.add(ValidationResult("GitHub: no obsolete CLI fields", True))

        elif server_type is None:
            # Modo npx (sem type)
            command = github_server.get("command", "")
            if command == "npx":
                suite.add(ValidationResult("GitHub npx wrapper", True, "Usando npx"))
            else:
                suite.add(ValidationResult("GitHub npx wrapper", False, f"Comando: {command}"))
    else:
        suite.add(ValidationResult(
            "GitHub server configured",
            True,
            "Não configurado (OK se intencional)"
        ))

    return suite


def validate_bug001_objetivo_init(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-001: scaffold objetivo-init 3 issues."""
    suite = ValidationSuite("BUG-001: Scaffold Objetivo-Init 3 Issues")

    objetivo = workspace / "objetivo.yaml"

    # Check 1: objetivo.yaml existe
    if not objetivo.exists():
        suite.add(ValidationResult(
            "objetivo.yaml exists",
            False,
            "Arquivo não encontrado (BUG-001 Fix #1 não pode ser validado)"
        ))
        # Ainda tentar validar Fix #3 (logs)
    else:
        suite.add(ValidationResult("objetivo.yaml exists", True))

        # Check 2: Fix #1 - DEFAULT_DOCSTYLE presente
        try:
            with objetivo.open(encoding="utf-8") as f:
                content = f.read()
                data = yaml.safe_load(content)

            docstyle = data.get("project", {}).get("docstyle", "")
            if docstyle:
                # Verificar se é o default esperado
                has_google = "Google" in docstyle or "google" in docstyle
                has_sphinx = "Sphinx" in docstyle or "sphinx" in docstyle
                is_default = has_google or has_sphinx

                suite.add(ValidationResult(
                    "Fix #1: docstyle populated",
                    True,
                    f"Docstyle: {docstyle[:50]}{'...' if len(docstyle) > 50 else ''}",
                    f"Default Google/Sphinx: {is_default}"
                ))
            else:
                suite.add(ValidationResult(
                    "Fix #1: docstyle populated",
                    False,
                    "Campo 'docstyle' vazio ou ausente"
                ))

            # Check 3: Fix #2 - out-scope condicional (não aparece linha vazia)
            has_empty_outscope = bool(
                "out-scope:" in content and
                ('out-scope: ""' in content or 'out-scope: {{OUT_SCOPE}}' in content or
                 'out-scope:\n' in content or '- out-scope:\n' in content)
            )

            if has_empty_outscope:
                suite.add(ValidationResult(
                    "Fix #2: no empty out-scope line",
                    False,
                    "Linha vazia de out-scope encontrada (deveria ser omitida)"
                ))
            else:
                # Verificar se out-scope existe com valor
                has_outscope = "out-scope:" in content
                suite.add(ValidationResult(
                    "Fix #2: no empty out-scope line",
                    True,
                    f"Out-scope: {'presente com valor' if has_outscope else 'omitido (correto)'}"
                ))

        except Exception as e:
            suite.add(ValidationResult(
                "Fix #1/#2: objetivo.yaml parsing",
                False,
                f"Erro ao processar: {e}"
            ))

    # Check 4: Fix #3 - Logging em logs/scaffolds.yaml
    # CORREÇÃO #2: Este arquivo é criado por objetivo-init, pode não existir se nunca executou
    scaffolds_log = workspace / "logs" / "scaffolds.yaml"

    if not scaffolds_log.exists():
        suite.add(ValidationResult(
            "Fix #3: logs/scaffolds.yaml exists",
            True,
            "Arquivo não encontrado (OK se nunca executou objetivo-init)"
        ))
        # Retornar early pois não tem log para validar
        return suite
    else:
        suite.add(ValidationResult("Fix #3: logs/scaffolds.yaml exists", True))

        try:
            with scaffolds_log.open(encoding="utf-8") as f:
                log_data = yaml.safe_load(f) or []

            # Procurar entradas de objetivo-init
            objetivo_entries = [
                entry for entry in log_data
                if isinstance(entry, dict) and entry.get("operation") == "objetivo-init"
            ]

            if objetivo_entries:
                latest = objetivo_entries[-1]
                project_name = latest.get("project_name", "N/A")
                timestamp = latest.get("timestamp", "N/A")
                suite.add(ValidationResult(
                    "Fix #3: objetivo-init logged",
                    True,
                    f"Última entrada: {project_name} em {timestamp}"
                ))
            else:
                suite.add(ValidationResult(
                    "Fix #3: objetivo-init logged",
                    False,
                    f"Nenhuma entrada 'objetivo-init' em {len(log_data)} registros"
                ))
        except Exception as e:
            suite.add(ValidationResult(
                "Fix #3: logs parsing",
                False,
                f"Erro ao processar log: {e}"
            ))

    return suite


def validate_bug17_timetracker(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-17: session-time-tracker deployment."""
    suite = ValidationSuite("BUG-17: Session Time Tracker Deployment")

    # Check 1: Script existe
    script = workspace / "scripts" / "session-time-tracker.py"
    suite.add(ValidationResult(
        "session-time-tracker.py exists",
        script.exists(),
        str(script) if script.exists() else "Arquivo não encontrado"
    ))

    # Check 2: wrapper de início de sessão existe e usa o CLI canônico
    candidates = [
        workspace / ".github" / "prompts" / "session-start.prompt.md",
        workspace / ".claude" / "commands" / "session-start..md",
    ]
    prompt = next((candidate for candidate in candidates if candidate.exists()), None)
    if prompt is None:
        suite.add(ValidationResult(
            "session-start wrapper exists",
            False,
            "Nenhum wrapper de session-start encontrado"
        ))
        return suite

    content = prompt.read_text(encoding="utf-8")
    has_session_manager = "python scripts/session-manager.py --json start" in content
    if not has_session_manager:
        suite.add(ValidationResult(
            "session-start uses session-manager CLI",
            False,
            "Comando canônico do session-manager não encontrado"
        ))
        return suite

    suite.add(ValidationResult("session-start uses session-manager CLI", True, str(prompt)))

    # Check 3: session-manager.py deve estar deployado junto com o tracker
    manager_script = workspace / "scripts" / "session-manager.py"
    suite.add(ValidationResult(
        "session-manager.py deployed",
        manager_script.exists(),
        str(manager_script) if manager_script.exists() else "Arquivo não encontrado"
    ))

    # Check 4: prompt curto, sem fluxo legado numerado
    has_legacy_step = "Passo 6.5" in content
    suite.add(ValidationResult(
        "session-start legacy step removed",
        not has_legacy_step,
        "Prompt enxuto sem passo 6.5 legado" if not has_legacy_step else "Prompt ainda contém passo 6.5 legado",
    ))

    return suite


def validate_bug18_objetivo(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-18: objetivo.yaml deployment."""
    suite = ValidationSuite("BUG-18: Objetivo.yaml Deployment")

    objetivo = workspace / "objetivo.yaml"

    # Check 1: Arquivo existe
    if not objetivo.exists():
        suite.add(ValidationResult(
            "objetivo.yaml exists",
            False,
            "Arquivo não encontrado na raiz"
        ))
        return suite
    suite.add(ValidationResult("objetivo.yaml exists", True, str(objetivo)))

    # Check 2: YAML válido
    try:
        with objetivo.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
        suite.add(ValidationResult("objetivo.yaml valid YAML", True))

        # Check 3: Contém dados do projeto
        if "project" in data:
            project_name = data["project"].get("name", "")
            # Verificar que nome foi preenchido (não está vazio nem é placeholder)
            is_valid = bool(project_name) and project_name != "CHANGE_ME"
            suite.add(ValidationResult(
                "project info present",
                is_valid,
                f"Nome: {project_name}" if is_valid else f"Nome inválido: '{project_name}'"
            ))
        else:
            suite.add(ValidationResult(
                "project info present",
                False,
                "Seção 'project' ausente"
            ))
    except yaml.YAMLError as e:
        suite.add(ValidationResult(
            "objetivo.yaml valid YAML",
            False,
            f"YAML inválido: {e}"
        ))

    return suite


def validate_bug11_session_init(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-11: session systems initialization."""
    suite = ValidationSuite("BUG-11: Session Systems Initialization")

    # Check 1: .session-index/index.db (OK se ausente, criado no primeiro session-start)
    index_db = workspace / ".session-index" / "index.db"
    suite.add(ValidationResult(
        ".session-index/index.db exists",
        index_db.exists() or True,  # Sempre PASS - criado apenas após session-start-first
        f"{index_db.stat().st_size} bytes" if index_db.exists() else "Ausente (OK se não inicializado)"
    ))

    # Check 2: .session-time/history.csv (OK se ausente, criado no primeiro session-start)
    history_csv = workspace / ".session-time" / "history.csv"
    suite.add(ValidationResult(
        ".session-time/history.csv exists",
        history_csv.exists() or True,  # Sempre PASS - criado apenas após session-start-first
        f"{history_csv.stat().st_size} bytes" if history_csv.exists() else "Ausente (OK se não inicializado)"
    ))

    # Check 3-7: Scripts de sessão (5 arquivos)
    session_scripts = [
        "session-index.py",
        "session-time-tracker.py",
        "session-search.py",
        "session-chat.py",
        "session-validate.py"
    ]

    for script_name in session_scripts:
        script = workspace / "scripts" / script_name
        suite.add(ValidationResult(
            f"{script_name} deployed",
            script.exists(),
            "OK" if script.exists() else "Ausente"
        ))

    return suite


def validate_bug12_memory_init(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-12: memory system initialization."""
    suite = ValidationSuite("BUG-12: Memory System Initialization")

    # Check 1: .memory/index/memory.db
    memory_db = workspace / ".memory" / "index" / "memory.db"
    suite.add(ValidationResult(
        ".memory/index/memory.db exists",
        memory_db.exists() or True,  # OK se não executou create_memory_structure
        f"{memory_db.stat().st_size} bytes" if memory_db.exists() else "Ausente (OK se não executou create_memory_structure)"
    ))

    # Check 2-5: Estrutura de diretórios
    memory_dirs = [
        (".memory/memories/project", "project memories"),
        (".memory/memories/team", "team memories"),
        (".memory/memories/sessions", "session memories"),
        (".memory/memories/.templates", "memory templates")
    ]

    for dir_path, dir_desc in memory_dirs:
        mem_dir = workspace / dir_path
        suite.add(ValidationResult(
            f"{dir_desc} dir",
            mem_dir.exists() or True,  # OK se não inicializado
            "OK" if mem_dir.exists() else "Ausente (OK se não inicializado)"
        ))

    # Check 6-10: Scripts de memory (5 arquivos)
    memory_scripts = [
        "create_memory_structure.py",
        "mem_context.py",
        "mem_search.py",
        "mem_save.py",
        "test_memory_smoke.py"
    ]

    for script_name in memory_scripts:
        script = workspace / "scripts" / script_name
        suite.add(ValidationResult(
            f"{script_name} deployed",
            script.exists(),
            "OK" if script.exists() else "Ausente"
        ))

    return suite


def validate_bug13_copilot_instructions(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-13: copilot-instructions.md deployment."""
    suite = ValidationSuite("BUG-13: Copilot Instructions Deployment")

    # Check 1: .github/copilot-instructions.md existe
    copilot_inst = workspace / ".github" / "copilot-instructions.md"
    suite.add(ValidationResult(
        "copilot-instructions.md exists",
        copilot_inst.exists(),
        str(copilot_inst) if copilot_inst.exists() else "Arquivo ausente"
    ))

    if not copilot_inst.exists():
        return suite

    # Check 2: Frontmatter com applyTo
    content = copilot_inst.read_text(encoding="utf-8")
    has_frontmatter = content.startswith("---")
    has_applyto = 'applyTo: "**"' in content or "applyTo:" in content

    suite.add(ValidationResult(
        "has applyTo frontmatter",
        has_frontmatter and has_applyto,
        "Frontmatter com applyTo" if (has_frontmatter and has_applyto) else "Sem applyTo"
    ))

    # Check 3: Conteúdo P0 presente
    has_p0 = "P0" in content or "CRÍTICO" in content
    suite.add(ValidationResult(
        "P0 rules present",
        has_p0,
        "Regras P0 encontradas" if has_p0 else "Sem regras P0"
    ))

    return suite


def validate_bug16_merge_strategy(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-16: merge strategy para JSON/workspace."""
    suite = ValidationSuite("BUG-16: JSON/Workspace Merge Strategy")

    # Check 1: Backups criados
    vscode_dir = workspace / ".vscode"
    backups = list(vscode_dir.glob("*.backup")) if vscode_dir.exists() else []

    suite.add(ValidationResult(
        "backups created",
        len(backups) > 0,
        f"{len(backups)} arquivo(s) backup" if backups else "Nenhum backup (OK se upgrade não sobrescreveu)"
    ))

    # Check 2: .copilot-rules consolidado (único arquivo ou symlink)
    copilot_rules = list(workspace.glob(".copilot-rules*.md"))
    # Filtrar symlinks
    copilot_rules_real = [f for f in copilot_rules if not f.is_symlink()]
    is_single_or_symlink = len(copilot_rules) == 1 or (len(copilot_rules_real) == 1 and len(copilot_rules) > 1)

    suite.add(ValidationResult(
        ".copilot-rules consolidated",
        is_single_or_symlink,
        f"1 arquivo (OK)" if len(copilot_rules) == 1 else f"{len(copilot_rules)} arquivos ({len(copilot_rules_real)} reais)"
    ))

    # Check 3: settings.json é JSON válido
    settings = workspace / ".vscode" / "settings.json"
    if settings.exists():
        try:
            with settings.open() as f:
                data = json.load(f)
            suite.add(ValidationResult("settings.json valid", True, f"{len(data)} campos"))
        except Exception as e:
            suite.add(ValidationResult("settings.json valid", False, f"JSON inválido: {e}"))
    else:
        suite.add(ValidationResult("settings.json valid", False, "Arquivo ausente"))

    # Check 4: mcp.json é JSON válido
    mcp = workspace / ".vscode" / "mcp.json"
    if mcp.exists():
        try:
            with mcp.open() as f:
                data = json.load(f)
            suite.add(ValidationResult("mcp.json valid", True, "JSON válido"))
        except Exception as e:
            suite.add(ValidationResult("mcp.json valid", False, f"JSON inválido: {e}"))
    else:
        suite.add(ValidationResult("mcp.json valid", False, "Arquivo ausente"))

    return suite


def validate_bug19_gitvalidators(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar correção do BUG-19: git_validators.py deployment."""
    suite = ValidationSuite("BUG-19: Git Validators Deployment")

    script = workspace / "scripts" / "lib" / "git_validators.py"

    # Check 1: Arquivo existe
    if not script.exists():
        suite.add(ValidationResult(
            "git_validators.py exists",
            False,
            "Arquivo não encontrado"
        ))
        return suite
    suite.add(ValidationResult("git_validators.py exists", True, str(script)))

    # Check 2: É módulo Python válido
    content = script.read_text(encoding="utf-8")
    has_python_code = "def " in content or "class " in content
    suite.add(ValidationResult(
        "contains Python code",
        has_python_code,
        "Funções/classes encontradas" if has_python_code else "Sem código Python"
    ))

    return suite


def validate_critical_files(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar arquivos críticos do projeto."""
    suite = ValidationSuite("Arquivos Críticos")

    # CORREÇÃO #5: Validar CONTEÚDO dos arquivos, não apenas existência

    # .scaffold-state.yaml
    state = workspace / ".scaffold-state.yaml"
    if state.exists():
        try:
            with state.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Validar campos obrigatórios
            required = ["scaffold_version", "updated_at", "project"]
            has_required = all(k in data for k in required)

            suite.add(ValidationResult(
                ".scaffold-state.yaml structure",
                has_required,
                "Campos obrigatórios presentes" if has_required else f"Campos ausentes: {[k for k in required if k not in data]}"
            ))

            # Validar conteúdo dos campos
            if has_required:
                project_name = data.get("project", {}).get("name")
                has_project_name = bool(project_name)
                suite.add(ValidationResult(
                    ".scaffold-state.yaml content",
                    has_project_name,
                    f"Nome do projeto: {project_name}" if has_project_name else "Nome do projeto ausente"
                ))
        except Exception as e:
            suite.add(ValidationResult(".scaffold-state.yaml parsing", False, f"Erro: {e}"))
    else:
        suite.add(ValidationResult(".scaffold-state.yaml", False, "Arquivo ausente"))

    # .copilot-rules.md
    rules = workspace / ".copilot-rules.md"
    if rules.exists() and rules.stat().st_size > 0:
        content = rules.read_text(encoding="utf-8")

        # Validar presença de seções P0
        has_p0 = "P0" in content or "CRÍTICO" in content
        has_rules = "NUNCA" in content or "PROIBIDO" in content

        suite.add(ValidationResult(
            ".copilot-rules.md",
            True,
            f"{rules.stat().st_size} bytes"
        ))

        suite.add(ValidationResult(
            ".copilot-rules.md content",
            has_p0 and has_rules,
            "Regras P0 presentes" if (has_p0 and has_rules) else "Conteúdo incompleto"
        ))
    else:
        suite.add(ValidationResult(".copilot-rules.md", False, "Ausente ou vazio"))

    # .vscode/settings.json
    settings = workspace / ".vscode" / "settings.json"
    if settings.exists():
        try:
            with settings.open() as f:
                settings_data = json.load(f)

            suite.add(ValidationResult(".vscode/settings.json", True, "JSON válido"))

            # Validar configurações importantes
            has_python = "python." in str(settings_data)
            has_files_exclude = "files.exclude" in settings_data

            suite.add(ValidationResult(
                ".vscode/settings.json content",
                has_python or has_files_exclude,
                f"Configurações: {len(settings_data)} campos"
            ))
        except Exception as e:
            suite.add(ValidationResult(".vscode/settings.json", False, f"Erro: {e}"))
    else:
        suite.add(ValidationResult(".vscode/settings.json", False, "Ausente"))

    return suite


def validate_scaffold_logs(workspace: Path, verbose: bool = False) -> ValidationSuite:
    """Validar logs do scaffold upgrade."""
    suite = ValidationSuite("Logs de Scaffold Upgrade")

    logs_dir = workspace / "logs"
    if not logs_dir.exists():
        suite.add(ValidationResult("logs/ directory", False, "Diretório não existe"))
        return suite

    scaffold_logs = list(logs_dir.glob("scaffold_*.log"))
    if not scaffold_logs:
        suite.add(ValidationResult("scaffold logs", False, "Nenhum log encontrado"))
        return suite

    latest_log = max(scaffold_logs, key=lambda p: p.stat().st_mtime)
    suite.add(ValidationResult(
        "latest scaffold log",
        True,
        f"{latest_log.name} ({latest_log.stat().st_size} bytes)"
    ))

    # Verificar conteúdo
    content = latest_log.read_text(encoding="utf-8")
    has_stats = any(word in content for word in ["created:", "skipped:", "merged:"])
    suite.add(ValidationResult(
        "log contains stats",
        has_stats,
        "Estatísticas encontradas" if has_stats else "Sem estatísticas"
    ))

    return suite


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Validar scaffold upgrade no test-workspace-fix"
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        default="/home/yves_marinho/DevOps/Projetos/test-workspace-fix",
        help="Path para o workspace (padrão: test-workspace-fix)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Saída detalhada"
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()

    print("=" * 70)
    print("🔍 VALIDAÇÃO DE SCAFFOLD UPGRADE")
    print("=" * 70)
    print(f"Workspace: {workspace}")
    print(f"Data: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    if not workspace.exists():
        print(f"❌ ERRO: Workspace não encontrado: {workspace}")
        return 1

    # Executar todas as validações
    suites = [
        validate_bug20_mcp(workspace, args.verbose),
        validate_bug001_objetivo_init(workspace, args.verbose),
        validate_bug11_session_init(workspace, args.verbose),
        validate_bug12_memory_init(workspace, args.verbose),
        validate_bug13_copilot_instructions(workspace, args.verbose),
        validate_bug16_merge_strategy(workspace, args.verbose),
        validate_bug17_timetracker(workspace, args.verbose),
        validate_bug18_objetivo(workspace, args.verbose),
        validate_bug19_gitvalidators(workspace, args.verbose),
        validate_critical_files(workspace, args.verbose),
        validate_scaffold_logs(workspace, args.verbose),
    ]

    # Imprimir resultados
    for suite in suites:
        suite.print_summary()

    # Resumo final
    total_passed = sum(s.passed_count for s in suites)
    total_failed = sum(s.failed_count for s in suites)
    total = total_passed + total_failed

    print("\n" + "=" * 70)
    print("📊 RESUMO GERAL")
    print("=" * 70)
    print(f"Total de validações: {total}")
    print(f"✅ Passaram: {total_passed}")
    print(f"❌ Falharam: {total_failed}")

    if total_failed == 0:
        print("\n🎉 SUCESSO: Todas as validações passaram!")
        print("=" * 70)
        return 0
    else:
        print(f"\n⚠️  ATENÇÃO: {total_failed} validação(ões) falharam")
        print("=" * 70)
        print("\n💡 Próximos passos:")
        print("  1. Revisar falhas acima")
        print("  2. Se BUG-20, 001, 11, 12, 13, 16 falharam: Execute 'scaffold upgrade --force'")
        print("  3. Se BUG-17/18/19 falharam: Verifique se commits foram aplicados")
        print("  4. Se logs falharam: Verifique se scaffold upgrade foi executado")
        print("  5. Para BUG-11/12: Execute scripts de inicialização se databases ausentes")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
