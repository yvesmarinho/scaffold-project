<!-- Criado em: 26/11/2026 12:18 -->
<!-- Modificado em: 26/11/2026 12:18 -->

# BUG: `--upgrade --force` trocava as instruções do Copilot do projeto pelas do scaffold

- **Data**: 26/11/2026
- **Contexto**: registrado na fatia 5 do ADR-003 e corrigido na fatia 6.
- **Arquivos**: `scripts/lib/project.py` (`copy_copilot_instructions`), `scripts/lib/ai/plugins/copilot.py`.
- **Status**: ✅ corrigido

## Sintoma
Depois de `scaffold.py --upgrade --force` num projeto com Copilot, o `.github/copilot-instructions.md`
do projeto perdia o rodapé `Gerado por scaffold.py em ... — Projeto: <nome>`. Em seu lugar entrava o
`copilot-instructions.md` **do próprio scaffold-project**, com o bloco `<!-- SPECKIT START -->` e as
regras do repositório do scaffold.

## Causa
O plugin do Copilot rodava duas etapas em sequência:
1. `templates.generate_copilot_instructions`, que gera o arquivo do projeto;
2. `project.copy_copilot_instructions`, que copiava uma versão estática para o mesmo destino.

Na criação, a etapa 2 terminava como `skipped`, porque o arquivo já existia. No upgrade com `--force`,
ela fazia backup e sobrescrevia o arquivo gerado. Na origem, a versão estática era o arquivo do repo e,
desde a fatia 5, uma cópia dele em `scaffold/templates/copilot/`.

## Correção
- `copy_copilot_instructions` copia só o `.copilot-rules.md`.
- `scaffold/templates/copilot/copilot-instructions.md` foi removido.
- Teste: `tests/test_upgrade_reaplica_agents_github.py::test_upgrade_force_mantem_copilot_instructions_do_projeto`.

## Impacto
Projetos que já passaram por `--upgrade --force` estão com as instruções do scaffold. Para restaurar,
apague `.github/copilot-instructions.md` e rode `--upgrade` (sem `--force`); o arquivo do projeto é
gerado de novo.
