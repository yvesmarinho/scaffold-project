<!--
Criado em: 09/11/2026 15:48
Modificado em: 09/11/2026 15:48
-->

# BUG — hook ansible-lint do pre-commit quebrado

**Status**: ✅ Corrigido em 09/11/2026 (branch `fix/ansible-lint-precommit`)

## Sintoma

`pre-commit run ansible-lint --all-files` falhava antes de analisar qualquer arquivo:

```
ModuleNotFoundError: No module named 'ansible.parsing.yaml.constructor'
```

## Causa

1. O hook estava fixado em `ansible-lint v6.22.1`, que importa um módulo removido do
   `ansible-core` 2.19+. O ambiente do pre-commit instala o ansible-core mais recente, por
   isso o import falhava.
2. O filtro `files: \.(yaml|yml)$` mandava **todo** YAML do repositório (workflows, perfis,
   configurações) para o ansible-lint, embora só 4 arquivos sejam playbooks.

## Correção

- `rev: v26.10.1`. A v26.11.0 tinha saído havia só 4 dias, por isso ficou de fora.
- `files: ^scaffold/templates/project/ansible/.*\.ya?ml$` + `args` apontando para a pasta.
- `language_version: python3.12`, porque a v26 pede `python3.14` por padrão e a máquina não tem.

## Verificação

- `pre-commit run ansible-lint --all-files` → **Passed**
- `ansible-lint scaffold/templates/project/ansible/` → 0 falhas, 0 avisos, perfil `production`
