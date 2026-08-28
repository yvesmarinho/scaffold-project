#!/usr/bin/env bash
# /// script
# description = "Run complete test suite for Enterprise Scaffold Project Template"
# ///
#
# tests/run_all_tests.sh
#
# Executa TODA a bateria de testes do projeto
#
# Uso:
#   ./tests/run_all_tests.sh                      # Rodar todos testes
#   ./tests/run_all_tests.sh --verbose            # Modo verbose
#   ./tests/run_all_tests.sh --coverage           # Com coverage
#   ./tests/run_all_tests.sh --parallel           # Execução paralela
#   ./tests/run_all_tests.sh --markers=smoke      # Apenas smoke tests
#   ./tests/run_all_tests.sh --failed-first       # Rodar falhas primeiro

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse argumentos
VERBOSE=false
COVERAGE=false
PARALLEL=false
FAILED_FIRST=false
MARKERS=""
EXTRA_ARGS=""

for arg in "$@"; do
    case $arg in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --parallel|-n)
            PARALLEL=true
            shift
            ;;
        --failed-first|--ff)
            FAILED_FIRST=true
            shift
            ;;
        --markers=*)
            MARKERS="${arg#*=}"
            shift
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $arg"
            ;;
    esac
done

echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Enterprise Scaffold Project Template - Complete Test Suite   ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

cd "$PROJECT_ROOT"

# Listar categorias de testes
echo -e "${BLUE}📋 Categorias de Testes Disponíveis:${NC}"
echo ""
echo -e "  ${YELLOW}Core Features:${NC}"
echo "    - test_git_validators.py            (Git branch/commit validation)"
echo "    - test_github_best_practices_p2.py  (GitHub templates P1+P2)"
echo "    - test_scaffold_*.py                (Scaffold system)"
echo ""
echo -e "  ${YELLOW}Integration:${NC}"
echo "    - test_integration_*.py             (Integration tests)"
echo "    - test_session_*.py                 (Session management)"
echo ""
echo -e "  ${YELLOW}Smoke Tests:${NC}"
echo "    - test_smoke_*.py                   (Quick validation tests)"
echo ""
echo -e "  ${YELLOW}Objetivo & Spec:${NC}"
echo "    - test_objetivo_*.py                (Objetivo YAML v2)"
echo "    - test_spec_*.py                    (Spec validation)"
echo ""
echo -e "  ${YELLOW}Mergers:${NC}"
echo "    - test_*_merger.py                  (File merge strategies)"
echo ""
echo -e "  ${YELLOW}Memory & Session:${NC}"
echo "    - test_memory_*.py                  (Memory management)"
echo "    - test_session_*.py                 (Session tracking)"
echo ""

# Construir comando pytest
PYTEST_CMD="pytest tests/"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
else
    PYTEST_CMD="$PYTEST_CMD -q"
fi

if [ "$COVERAGE" = true ]; then
    # Verificar se pytest-cov está instalado
    if python -c "import pytest_cov" 2>/dev/null; then
        PYTEST_CMD="$PYTEST_CMD --cov=scripts/lib --cov=scripts/lib/flows --cov-report=term-missing --cov-report=html"
    else
        echo -e "${YELLOW}⚠️  pytest-cov não instalado. Rodando sem coverage.${NC}"
        echo -e "${YELLOW}   Instale com: pip install pytest-cov${NC}"
        echo ""
        COVERAGE=false
    fi
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

if [ "$FAILED_FIRST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --ff"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
fi

if [ -n "$EXTRA_ARGS" ]; then
    PYTEST_CMD="$PYTEST_CMD $EXTRA_ARGS"
fi

echo -e "${YELLOW}Comando: $PYTEST_CMD${NC}"
echo ""
echo -e "${BLUE}🏃 Executando testes...${NC}"
echo ""

# Capturar tempo de início
START_TIME=$(date +%s)

# Executar testes
if eval "$PYTEST_CMD"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    ✅ ALL TESTS PASSED                         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}⏱️  Duration: ${DURATION}s${NC}"

    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${BLUE}📊 Coverage Reports:${NC}"
        echo "  - Terminal: (exibido acima)"
        echo "  - HTML: htmlcov/index.html"
        echo ""
        echo -e "${YELLOW}Para visualizar coverage HTML:${NC}"
        echo "  python -m http.server 8000 --directory htmlcov"
        echo "  Acesse: http://localhost:8000"
    fi

    exit 0
else
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                    ❌ TESTS FAILED                             ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}⏱️  Duration: ${DURATION}s${NC}"
    echo ""
    echo -e "${YELLOW}💡 Dicas para debugging:${NC}"
    echo "  - Rodar apenas testes falhados: ./tests/run_all_tests.sh --failed-first"
    echo "  - Modo verbose: ./tests/run_all_tests.sh --verbose"
    echo "  - Rodar teste específico: pytest tests/test_name.py::test_function -v"
    echo ""
    exit 1
fi
