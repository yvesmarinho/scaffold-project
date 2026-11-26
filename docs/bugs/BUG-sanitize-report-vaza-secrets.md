<!-- Criado em: 26/11/2026 10:58 -->
<!-- Modificado em: 26/11/2026 10:59 -->

# BUG: relatório de segurança do mem_save gravava secrets no log

- **Data**: 26/11/2026
- **Contexto**: achado durante a ADR-003 fatia 4 (já existia antes dela).
- **Arquivo**: `scaffold/templates/runtime/scripts/lib/sanitize.py` (`get_security_report`).
- **Status**: ✅ corrigido

## Sintoma
Ao salvar uma memória com conteúdo sensível, o `mem_save.py` chamava `get_security_report` e mandava o
resultado para `log.warning`. O relatório mostrava até 3 exemplos por tipo detectado:
- valores com mais de 20 caracteres apareciam cortados nos 20 primeiros;
- valores com 20 caracteres ou menos apareciam **inteiros**: senhas curtas, emails e IPs.

Ou seja, a ferramenta que existe para impedir que secrets sejam gravados acabava gravando-os no log.

## Causa
O relatório foi pensado como uma ajuda para localizar o problema e montava uma prévia de cada valor com
`value[:20]`. Não havia nenhum mascaramento.

## Correção
- O relatório agora lista **só o tipo e a contagem** (`password: 2 found`), sem exemplos nem prefixos.
- Testes novos em `tests/test_memory_security.py`:
  - senha curta não aparece;
  - nenhum trecho de 6 caracteres de um token longo aparece;
  - email e IP não aparecem;
  - tipo e contagem continuam presentes;
  - texto limpo continua com a mensagem de OK.

## Impacto e ação recomendada
- Projetos gerados antes da correção têm a versão antiga em `scripts/lib/sanitize.py`. O upgrade só a
  substitui com `--force`. Sem a flag, o arquivo existente com conteúdo diferente fica como `skipped`.
- Se algum log de projeto gerado contém o relatório antigo, considere comprometidos os secrets que
  aparecem ali e rotacione as credenciais.
