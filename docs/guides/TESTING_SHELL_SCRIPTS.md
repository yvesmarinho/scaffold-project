# Testing Shell Scripts — new-project

## Problema Encontrado

O script `new-project` estava usando `python` hardcoded, mas muitos sistemas Linux modernos só têm `python3` disponível. Isso causava o erro:

```
/home/yves_marinho/.local/bin/new-project: linha 102: exec: python: não encontrado
```

## Correção Implementada

### 1. Detecção Automática de Python

Adicionada lógica de detecção que tenta `python3` primeiro, depois `python`:

```bash
# Detectar Python disponível (python3 ou python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Erro: Python não encontrado${NC}"
    exit 1
fi
```

### 2. Uso da Variável em Todas as Chamadas

Substituídas 4 ocorrências de `python` por `"${PYTHON_CMD}"`:
- `list_profiles()`
- `validate_profiles()`
- Modo interativo
- Construção do comando CI

## TDD para Scripts Shell

### Por que não tem TDD tradicional?

Scripts shell **não seguem TDD tradicional** como código Python/TypeScript porque:

1. **Natureza imperativa**: Shells são mais sobre orquestração de comandos
2. **Dependências externas**: Dependem de binários do sistema (python, git, etc.) que variam por ambiente
3. **Dificuldade de mockar**: Não há frameworks de mock maduros como no Python
4. **Execução no ambiente real**: Testes precisam rodar no sistema real, não em isolamento

### Abordagem Recomendada: Smoke Tests

Criamos **smoke tests** (`tests/test_new_project_script.sh`) que validam:

✅ **Pré-requisitos**
- Script existe
- Script é executável

✅ **Ambiente**
- Python3 disponível

✅ **Interface**
- Flags de ajuda funcionam (`--help`, `-h`)

✅ **Validação**
- Rejeita nomes inválidos (uppercase, underscore, espaço)

✅ **Utilitários**
- `--list-profiles` retorna sucesso
- `--validate` retorna sucesso

✅ **Configuração**
- Template directory existe

### Executar os Testes

```bash
cd /path/to/scaffold-project
./tests/test_new_project_script.sh
```

**Output esperado**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🧪 Smoke Tests: new-project
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Testes de Pré-requisitos
  Testing: Script exists... ✓ PASS
  Testing: Script is executable... ✓ PASS

[... todos os 11 testes ...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 Resumo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Tests run:    11
  Tests passed: 11
  Tests failed: 0

✅ All smoke tests passed!
```

## Lições Aprendidas

### 1. Nunca Assuma Binários

❌ **Errado**:
```bash
python script.py
```

✅ **Correto**:
```bash
# Detectar qual Python está disponível
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found"
    exit 1
fi

"${PYTHON_CMD}" script.py
```

### 2. Sempre Testar em Ambiente Limpo

Scripts devem ser testados em sistemas com diferentes configurações:
- Ubuntu (python3 only)
- macOS (pode ter python via brew)
- Alpine (configurações minimalistas)

### 3. Smoke Tests São Essenciais

Mesmo sem TDD completo, smoke tests **previnem regressões básicas**:
- ✅ Script funciona?
- ✅ Dependências disponíveis?
- ✅ Validações funcionam?
- ✅ Help está acessível?

### 4. Falhe Rápido com Mensagens Claras

Quando algo der errado, mostrar **exatamente** o problema e **como resolver**:

```bash
echo -e "${RED}❌ Erro: Python não encontrado${NC}"
echo -e "${YELLOW}💡 Instale Python 3.10+ para usar este comando${NC}"
echo -e "${YELLOW}   Ubuntu/Debian: sudo apt install python3${NC}"
echo -e "${YELLOW}   macOS: brew install python3${NC}"
```

## Ferramentas de Testing para Shell

### Frameworks Disponíveis

1. **bats-core** (Bash Automated Testing System)
   - Framework mais maduro para Bash
   - Similar a RSpec/Jest
   - https://github.com/bats-core/bats-core

2. **shunit2**
   - xUnit-style testing para shell
   - https://github.com/kward/shunit2

3. **shellspec**
   - BDD-style para shell scripts
   - https://shellspec.info/

### Por que Usamos Smoke Tests Simples?

Para este projeto, **smoke tests bash puros** são suficientes porque:

1. **Simplicidade**: Não requer dependências externas
2. **Portabilidade**: Funciona em qualquer sistema Unix-like
3. **Rápido**: Executam em < 2 segundos
4. **Suficiente**: Cobrem os casos críticos

## Integração com CI

Os smoke tests podem ser adicionados ao `.github/workflows/ci.yml`:

```yaml
- name: Test new-project script
  run: |
    chmod +x tests/test_new_project_script.sh
    ./tests/test_new_project_script.sh
```

## Referências

- [ShellCheck](https://www.shellcheck.net/) — Linter para shell scripts
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [BATS Core](https://github.com/bats-core/bats-core) — Framework de testes
- [Testing Bash Scripts](https://www.baeldung.com/linux/bash-script-testing) — Tutorial
