<!-- Criado em: 25/11/2026 15:20 -->
<!-- Modificado em: 25/11/2026 15:20 -->

# BUG: `.copilot-rules.md` copiado sem `.copilot-shared` ainda cita `.github/prompts`

- **Data**: 25/11/2026
- **PR**: #70 (Copilot P0)
- **Status**: ✅ corrigido em `a7e91be`

## Sintoma
O check `Tests` falhou no PR #70 em `test_nenhuma_referencia_a_prompts_nos_arquivos_de_ia`, com
`['.copilot-rules.md']`. O mesmo teste passava localmente. Como o `CLI Smoke Tests` depende de `Tests`,
ele foi pulado, e o PR ficou bloqueado para merge.

## Causa
- Quando o `.copilot-shared` existe, como na máquina do usuário, o projeto gerado recebe `.copilot-rules.md`
  como **symlink** para o arquivo externo, e o teste ignorava symlinks.
- Sem ele, como no CI, o scaffold **copia o `.copilot-rules.md` do próprio repositório**. É o
  acoplamento descrito no ADR-003. A linha "Domain Profiles" desse arquivo ainda apontava para
  `.github/prompts/domain/*.prompt.md`.

## Correção
- A linha 9 do `.copilot-rules.md` passou a apontar para `.github/skills/<perfil>/SKILL.md`.
- `tests/test_copilot_p0.py` agora gera os projetos com `--shared-dir` vazio, reproduzindo o CI em qualquer
  máquina. A exceção para symlink foi removida.

## Lição
Teste e2e que dependem de diretório externo do usuário mudam de comportamento entre a máquina local e o CI.
Fixar o ambiente no próprio teste (`--shared-dir`) evita o falso verde local.
