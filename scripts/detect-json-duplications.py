#!/usr/bin/env python3
"""
Detector de duplicações em arquivos JSON.

Scan recursivo de duplicações em todos os arquivos JSON do projeto.
Útil para validação em CI/CD, pre-commit hooks e auditorias.

Usage:
    python scripts/detect-json-duplications.py .
    python scripts/detect-json-duplications.py .vscode/
    python scripts/detect-json-duplications.py .vscode/mcp.json
"""

import json
import logging
import sys
from collections import Counter
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)


def analyze_array_duplicates(arr, path="root"):
    """
    Analisa duplicações em um array.

    Args:
        arr: Array a ser analisado
        path: Caminho JSON para contexto

    Returns:
        Dict com informações sobre duplicações ou None se limpo
    """
    if not isinstance(arr, list):
        return None

    # Contar itens (objetos comparados por JSON)
    items = []
    for item in arr:
        key = (
            json.dumps(item, sort_keys=True) if isinstance(item, (dict, list)) else item
        )
        items.append(key)

    counts = Counter(items)
    duplicates = {k: v for k, v in counts.items() if v > 1}

    if duplicates:
        return {
            "path": path,
            "total": len(arr),
            "unique": len(counts),
            "duplicates": duplicates,
            "duplication_rate": (len(arr) - len(counts)) / len(arr) * 100,
        }

    return None


def scan_json_structure(data, path="root"):
    """
    Scan recursivo de duplicações em estrutura JSON.

    Args:
        data: Estrutura JSON (dict, list ou primitivo)
        path: Caminho atual para contexto

    Returns:
        Lista de issues encontrados
    """
    issues = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}"
            issues.extend(scan_json_structure(value, new_path))
    elif isinstance(data, list):
        # Analisar duplicações neste array
        result = analyze_array_duplicates(data, path)
        if result:
            issues.append(result)
        # Scan recursivo em itens
        for i, item in enumerate(data):
            issues.extend(scan_json_structure(item, f"{path}[{i}]"))

    return issues


def scan_file(file_path: Path):
    """
    Scan de duplicações em um arquivo JSON.

    Args:
        file_path: Caminho do arquivo JSON

    Returns:
        True se encontrou duplicações, False se limpo
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        issues = scan_json_structure(data, file_path.name)

        if issues:
            log.warning(f"⚠️  {file_path}")
            for issue in issues:
                log.warning(f"   Array: {issue['path']}")
                log.warning(f"   Items: {issue['total']} ({issue['unique']} únicos)")
                log.warning(f"   Taxa: {issue['duplication_rate']:.1f}%")
                for item, count in issue["duplicates"].items():
                    preview = item[:50] + "..." if len(item) > 50 else item
                    log.warning(f"   - {count}x: {preview}")
            return True
        else:
            log.info(f"✅ {file_path}")
            return False

    except json.JSONDecodeError as e:
        log.error(f"❌ {file_path}: Erro JSON - {e}")
        return False
    except Exception as e:
        log.error(f"❌ {file_path}: {e}")
        return False


def main():
    """Main: scan de arquivos JSON."""
    # Argumento: arquivo/pasta/projeto
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

    # Listar JSONs
    if root.is_file():
        # Scan de arquivo único
        files = [root]
    else:
        # Scan recursivo de pasta
        files = list(root.rglob("*.json"))
        # Filtrar .git e node_modules
        files = [
            f for f in files if ".git" not in f.parts and "node_modules" not in f.parts
        ]

    log.info(f"🔍 Scanning {len(files)} JSON files...\n")

    issues_count = 0
    for file in sorted(files):
        if scan_file(file):
            issues_count += 1

    log.info(f"\n{'='*60}")
    if issues_count > 0:
        log.warning(f"⚠️  {issues_count} file(s) com duplicações")
        log.warning("Execute: python scripts/fix-json-duplications.py .")
        sys.exit(1)
    else:
        log.info(f"✅ Todos os {len(files)} arquivos estão limpos")
        sys.exit(0)


if __name__ == "__main__":
    main()
