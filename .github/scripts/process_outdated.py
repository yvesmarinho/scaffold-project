#!/usr/bin/env python3
"""Process outdated packages JSON and generate markdown table."""

import json
import sys


def main():
    try:
        with open("outdated.json") as f:
            data = json.load(f)

        count = len(data)

        # Primeira linha: contagem
        print(count)

        # Linhas seguintes: tabela markdown
        if count > 0:
            for pkg in data:
                name = pkg.get("name", "N/A")
                version = pkg.get("version", "N/A")
                latest = pkg.get("latest_version", "N/A")
                print(f"| {name} | {version} | {latest} |")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("0")


if __name__ == "__main__":
    main()
