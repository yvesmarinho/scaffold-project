#!/usr/bin/env bash
#
# Smoke tests para o script new-project
#
# Testa as funcionalidades básicas sem criar projetos reais
#

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NEW_PROJECT_SCRIPT="${SCRIPT_DIR}/../scripts/bin/new-project"

# Contadores
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Função auxiliar para testes que devem passar
test_command() {
    local test_name="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"

    TESTS_RUN=$((TESTS_RUN + 1))

    echo -n "  Testing: ${test_name}... "

    if eval "${command}" > /dev/null 2>&1; then
        actual_exit=$?
    else
        actual_exit=$?
    fi

    if [[ ${actual_exit} -eq ${expected_exit_code} ]]; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (exit ${actual_exit}, expected ${expected_exit_code})"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Função auxiliar para testes que devem falhar
test_command_fails() {
    local test_name="$1"
    local command="$2"

    TESTS_RUN=$((TESTS_RUN + 1))

    echo -n "  Testing: ${test_name}... "

    if eval "${command}" > /dev/null 2>&1; then
        echo -e "${RED}✗ FAIL${NC} (expected failure, got success)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    else
        echo -e "${GREEN}✓ PASS${NC} (correctly failed)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 Smoke Tests: new-project"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Teste 1: Script existe e é executável
echo "📋 Testes de Pré-requisitos"
test_command "Script exists" "[[ -f '${NEW_PROJECT_SCRIPT}' ]]"
test_command "Script is executable" "[[ -x '${NEW_PROJECT_SCRIPT}' ]]"
echo

# Teste 2: Python está disponível
echo "📋 Testes de Ambiente"
test_command "Python3 available" "command -v python3"
echo

# Teste 3: Help funciona
echo "📋 Testes de Interface"
test_command "--help flag" "'${NEW_PROJECT_SCRIPT}' --help"
test_command "-h flag" "'${NEW_PROJECT_SCRIPT}' -h"
echo

# Teste 4: Validação de nome (devem falhar)
echo "📋 Testes de Validação"
test_command_fails "Reject invalid name (uppercase)" "'${NEW_PROJECT_SCRIPT}' MyProject --ci"
test_command_fails "Reject invalid name (underscore)" "'${NEW_PROJECT_SCRIPT}' my_project --ci"
test_command_fails "Reject invalid name (space)" "'${NEW_PROJECT_SCRIPT}' 'my project' --ci"
echo

# Teste 5: Utilitários não-destrutivos
echo "📋 Testes de Utilitários"
test_command "--list-profiles returns success" "'${NEW_PROJECT_SCRIPT}' --list-profiles" 0
test_command "--validate returns success" "'${NEW_PROJECT_SCRIPT}' --validate" 0
echo

# Teste 6: Template directory detection
echo "📋 Testes de Configuração"
if [[ -f "${HOME}/Documentos/DevOps/Projetos/scaffold-project/scripts/scaffold.py" ]]; then
    test_command "Template directory exists" "true"
else
    echo -e "  ${YELLOW}⚠ SKIP${NC}: Template not in default location"
fi
echo

# Resumo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 Resumo"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Tests run:    ${TESTS_RUN}"
echo -e "  Tests passed: ${GREEN}${TESTS_PASSED}${NC}"
if [[ ${TESTS_FAILED} -gt 0 ]]; then
    echo -e "  Tests failed: ${RED}${TESTS_FAILED}${NC}"
else
    echo -e "  Tests failed: ${TESTS_FAILED}"
fi
echo

if [[ ${TESTS_FAILED} -eq 0 ]]; then
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed.${NC}"
    exit 1
fi
