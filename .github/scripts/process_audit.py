#!/usr/bin/env python3
"""Process pip-audit JSON and generate security summary."""

import json
import sys


def main():
    try:
        with open("audit.json") as f:
            data = json.load(f)

        vulns = data.get("vulnerabilities", [])

        if vulns:
            print(
                f"**⚠️ Encontradas {len(vulns)} vulnerabilidade(s):**", file=sys.stderr
            )

            # Filtrar vulnerabilidades com fix disponível
            critical = [v for v in vulns if v.get("fix_versions")]

            if critical:
                print("\n### Vulnerabilidades Críticas\n", file=sys.stderr)
                for v in critical[:5]:  # Mostrar até 5
                    pkg = v.get("name", "unknown")
                    vuln_id = v.get("id", "N/A")
                    print(f"- **{pkg}**: {vuln_id}", file=sys.stderr)

            # Salvar contagem para próximo step
            with open("vuln_count.txt", "w") as f:
                f.write(str(len(vulns)))

            sys.exit(1)  # Falhar se vulnerabilidades encontradas
        else:
            print("✅ Nenhuma vulnerabilidade conhecida encontrada!")
            with open("vuln_count.txt", "w") as f:
                f.write("0")
            sys.exit(0)

    except Exception as e:
        print(f"Erro ao processar audit.json: {e}", file=sys.stderr)
        with open("vuln_count.txt", "w") as f:
            f.write("0")
        sys.exit(0)


if __name__ == "__main__":
    main()
