# ✅ Checklist de Teste - Scaffold Upgrade

**ATENÇÃO**: Teste a ser executado pelo usuário (@yves_marinho)

---

## 🎯 Comando Recomendado (Copie e Cole)

```bash
# Opção 1: Modo não-interativo (RECOMENDADO)
cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project && \
python scripts/scaffold.py --upgrade --force --json \
  --target-dir /home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix

# Validação
python scripts/validate-workspace-upgrade.py \
  /home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix
```

---

## 📋 Checklist

### Antes do Teste
- [x] BUG-20 fix aplicado manualmente (mcp.json corrigido)
- [x] .scaffold-state.yaml path corrigido
- [x] Pasta logs/ criada
- [x] Validação mostrando 17/23 PASS

### Durante o Teste
- [ ] Executar comando de scaffold upgrade
- [ ] Observar se há erros ou warnings
- [ ] Verificar se log foi criado em `logs/scaffold_*.log`

### Validação Pós-Teste
- [ ] Executar `validate-workspace-upgrade.py`
- [ ] Verificar resultado: espera-se **≥ 22/23 PASS**
- [ ] Confirmar BUG-20: 7/7 ✅
- [ ] Confirmar BUG-17: 2/2 ✅
- [ ] Confirmar BUG-19: 1/1 ✅
- [ ] Confirmar Arquivos Críticos: 6/6 ✅

### Reportar Resultado
- [ ] Se PASS ≥ 22/23: ✅ Teste bem-sucedido!
- [ ] Se PASS < 22/23: Reportar falhas encontradas

---

## 🚨 Problemas Conhecidos

**Path Incorreto**: NÃO use `/home/yves_marinho/DevOps/Projetos/...` (sem "Documentos")
**Correto**: `/home/yves_marinho/Documentos/DevOps/Projetos/test-workspace-fix`

**Prompt Interativo**: Se aparecer prompt pedindo escolha 1/2, responda `1`

---

**Documentação Completa**: [TESTE_SCAFFOLD_UPGRADE.md](TESTE_SCAFFOLD_UPGRADE.md)
