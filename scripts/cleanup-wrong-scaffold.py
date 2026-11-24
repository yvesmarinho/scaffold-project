#!/usr/bin/env python3
"""
Limpa arquivos criados pelo scaffold no diretório errado.
Usa .scaffold-state.yaml como referência do que foi criado.
"""

import logging
import shutil
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Diretórios e arquivos típicos criados pelo scaffold
SCAFFOLD_DIRS = [
    "docs",
    "docs/SESSIONS",
    "docs/copilot",
    ".github",
    ".github/agents",
    ".github/prompts",
    ".github/prompts/domain",
    ".github/ISSUE_TEMPLATE",
    ".secrets",
    ".vscode",
    ".specify",
    ".specify/memory",
    ".specify/templates",
    "scripts",
    "scripts/lib",
    "scripts/logs",
    "src",
]

SCAFFOLD_FILES = [
    "README.md",
    "docs/INDEX.md",
    "docs/TODO.md",
    "docs/TODAY_ACTIVITIES.md",
    ".gitignore",
    ".copilot-rules.md",
    ".github/copilot-instructions.md",
    ".secrets/README.md",
    ".vscode/settings.json",
    ".vscode/mcp.json",
    ".vscode/extensions.json",
    ".vscode/tasks.json",
    ".vscode/launch.json",
    "Makefile",
    "scripts/load-mcp.sh",
    "scripts/logs/.gitkeep",
    ".scaffold-state.yaml",
    ".git",  # diretório git
]


def cleanup_scaffold_files(target_dir: Path, project_name: str, dry_run: bool = False):
    """Remove arquivos e pastas criados pelo scaffold."""

    print(f"\n{'🔍 DRY RUN' if dry_run else '🗑️  LIMPEZA'}: {target_dir}")
    print(f"Projeto: {project_name}\n")

    # Verifica se existe .scaffold-state.yaml
    state_file = target_dir / ".scaffold-state.yaml"
    if state_file.exists():
        print(f"✅ Encontrado: {state_file}")
        try:
            with open(state_file) as f:
                state = yaml.safe_load(f)
                print(f"   - Projeto: {state.get('project', {}).get('name', 'N/A')}")
                print(f"   - Criado em: {state.get('created_at', 'N/A')}")
        except Exception as e:
            log.warning(f"Erro ao ler state file: {e}")
    else:
        print(f"⚠️  Arquivo .scaffold-state.yaml não encontrado em {target_dir}")
        response = input("\nContinuar mesmo assim? [y/N]: ")
        if response.lower() != "y":
            print("❌ Operação cancelada.")
            return

    print("\n" + "=" * 60)

    # 1. Remove arquivos
    print("\n📄 Arquivos a remover:")
    removed_files = 0
    for file_rel in SCAFFOLD_FILES:
        file_path = target_dir / file_rel
        if file_path.exists():
            print(f"   • {file_rel}")
            if not dry_run:
                try:
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                    removed_files += 1
                except Exception as e:
                    log.error(f"Erro ao remover {file_path}: {e}")

    # 2. Remove workspace file se existir
    workspace_file = target_dir / f"{project_name}.code-workspace"
    if workspace_file.exists():
        print(f"   • {workspace_file.name}")
        if not dry_run:
            try:
                workspace_file.unlink()
                removed_files += 1
            except Exception as e:
                log.error(f"Erro ao remover {workspace_file}: {e}")

    # 3. Remove diretórios (ordem reversa para remover filhos antes dos pais)
    print("\n📁 Diretórios a remover:")
    removed_dirs = 0
    for dir_rel in reversed(SCAFFOLD_DIRS):
        dir_path = target_dir / dir_rel
        if dir_path.exists() and dir_path.is_dir():
            try:
                # Só remove se estiver vazio ou se não for dry_run
                contents = list(dir_path.iterdir())
                if not contents or not dry_run:
                    print(f"   • {dir_rel}" + (" (vazio)" if not contents else ""))
                    if not dry_run:
                        shutil.rmtree(dir_path)
                        removed_dirs += 1
                else:
                    print(f"   ⚠️  {dir_rel} (não vazio - não removido em dry-run)")
            except Exception as e:
                log.error(f"Erro ao remover {dir_path}: {e}")

    print("\n" + "=" * 60)

    if dry_run:
        print("\n✅ DRY RUN completo (nenhum arquivo foi removido)")
        print("\n   Execute novamente com --execute para remover os arquivos.")
    else:
        print("\n✅ Limpeza completa!")
        print(f"   • {removed_files} arquivos removidos")
        print(f"   • {removed_dirs} diretórios removidos")


if __name__ == "__main__":
    import sys

    # Argumentos
    target_dir = Path("/home/yves_marinho/Documentos/DevOps/Vya-Jobs")
    project_name = "enterprise-python-docker"

    # Verifica se deve executar ou apenas simular
    dry_run = "--execute" not in sys.argv

    if dry_run:
        print("\n" + "=" * 60)
        print("🔍 MODO DRY-RUN (simulação)")
        print("=" * 60)
        print("\nNenhum arquivo será removido. Para executar de verdade, use:")
        print(f"\n   python3 {Path(__file__).name} --execute\n")

    cleanup_scaffold_files(target_dir, project_name, dry_run=dry_run)

    print("\n")
