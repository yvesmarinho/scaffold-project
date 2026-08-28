#!/usr/bin/env bash
# Test script to validate BUG-01 fix

set -euo pipefail

TEST_DIR="/tmp/test-bug01-fix-$$"
PROJECT_NAME="speckup-sync"

echo "🧪 Testando fix do BUG-01..."
echo "   Criando projeto com target_dir.name == project_name"
echo ""

# Cleanup
trap "rm -rf '$TEST_DIR'" EXIT

# Criar diretório de teste
mkdir -p "$TEST_DIR/$PROJECT_NAME"

cd /home/yves_marinho/Documentos/DevOps/Projetos/scaffold-project

# Executar scaffold em modo CI
python3 scripts/scaffold.py new --ci \
    --name "$PROJECT_NAME" \
    --title "Test Project" \
    --domain programming \
    --language python \
    --target-dir "$TEST_DIR/$PROJECT_NAME"

# Verificar estrutura criada
echo ""
echo "📁 Estrutura criada:"
ls -la "$TEST_DIR/$PROJECT_NAME/" | head -20

# Verificar se arquivo foi criado no lugar correto (sem duplicação)
if [[ -f "$TEST_DIR/$PROJECT_NAME/README.md" ]]; then
    echo ""
    echo "✅ SUCESSO: Arquivo criado em $TEST_DIR/$PROJECT_NAME/README.md"
    echo "   (sem duplicação de diretório)"
    exit 0
else
    echo ""
    echo "❌ FALHA: README.md não encontrado em $TEST_DIR/$PROJECT_NAME/"
    if [[ -f "$TEST_DIR/$PROJECT_NAME/$PROJECT_NAME/README.md" ]]; then
        echo "   Encontrado em $TEST_DIR/$PROJECT_NAME/$PROJECT_NAME/README.md"
        echo "   (estrutura duplicada detectada)"
    fi
    exit 1
fi
