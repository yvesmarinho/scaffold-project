#!/bin/bash

# ==============================================================================
# Script de Inicialização de Novo Projeto
# ==============================================================================
# Este script configura um novo projeto a partir do template scaffold-project
#
# Uso: ./scripts/init-new-project.sh <nome-do-projeto>
# Exemplo: ./scripts/init-new-project.sh my-awesome-app
#
# O script irá:
# 1. Validar o nome do projeto
# 2. Configurar symlinks para arquivos compartilhados (.copilot-*)
# 3. Substituir placeholders pelo nome do projeto
# 4. Limpar histórico Git
# 5. Inicializar novo repositório Git
# 6. Executar make init para configurar estrutura
# ==============================================================================

set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
SHARED_DIR="$HOME/Documentos/DevOps/.copilot-shared"
REQUIRED_SHARED_FILES=(".copilot-rules.md" ".copilot-git-rules.md" ".copilot-strict-enforcement.md" ".copilot-strict-rules.md" ".copilot-file-rules.sh")

# ==============================================================================
# Funções Auxiliares
# ==============================================================================

print_header() {
    echo -e "\n${BLUE}===================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ==============================================================================
# Validações
# ==============================================================================

validate_project_name() {
    local project_name="$1"

    # Verifica se o nome foi fornecido
    if [[ -z "$project_name" ]]; then
        print_error "Nome do projeto não fornecido"
        echo ""
        echo "Uso: $0 <nome-do-projeto>"
        echo "Exemplo: $0 my-awesome-app"
        exit 1
    fi

    # Verifica formato (apenas letras minúsculas, números e hífens)
    if [[ ! "$project_name" =~ ^[a-z0-9-]+$ ]]; then
        print_error "Nome do projeto inválido"
        echo ""
        echo "O nome deve conter apenas:"
        echo "  - Letras minúsculas (a-z)"
        echo "  - Números (0-9)"
        echo "  - Hífens (-)"
        echo ""
        echo "Exemplos válidos: my-project, api-v2, data-processor-2024"
        exit 1
    fi

    print_success "Nome do projeto validado: $project_name"
}

check_shared_config_exists() {
    if [[ ! -d "$SHARED_DIR" ]]; then
        print_error "Diretório de configurações compartilhadas não encontrado"
        echo ""
        echo "Esperado em: $SHARED_DIR"
        echo ""
        echo "Execute primeiro:"
        echo "  make setup-shared-configs"
        exit 1
    fi

    print_success "Diretório compartilhado encontrado"
}

check_required_files() {
    local missing_files=()

    for file in "${REQUIRED_SHARED_FILES[@]}"; do
        if [[ ! -f "$SHARED_DIR/rules/$file" ]]; then
            missing_files+=("$file")
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        print_error "Arquivos compartilhados ausentes:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo "Execute primeiro: make setup-shared-configs"
        exit 1
    fi

    print_success "Todos os arquivos compartilhados encontrados"
}

# ==============================================================================
# Configuração de Symlinks
# ==============================================================================

setup_symlinks() {
    print_header "Configurando Symlinks para Arquivos Compartilhados"

    # Remove arquivos locais se existirem
    for file in "${REQUIRED_SHARED_FILES[@]}"; do
        if [[ -f "$file" && ! -L "$file" ]]; then
            print_info "Removendo arquivo local: $file"
            rm -f "$file"
        fi
    done

    # Cria symlinks
    for file in "${REQUIRED_SHARED_FILES[@]}"; do
        if [[ -L "$file" ]]; then
            print_info "Symlink já existe: $file"
        else
            # Calcula caminho relativo
            local relative_path=$(realpath --relative-to="." "$SHARED_DIR/rules/$file")
            ln -s "$relative_path" "$file"
            print_success "Symlink criado: $file -> $relative_path"
        fi
    done
}

# ==============================================================================
# Substituição de Placeholders
# ==============================================================================

replace_placeholders() {
    local project_name="$1"
    print_header "Substituindo Placeholders pelo Nome do Projeto"

    # Converte nome para diferentes formatos
    local project_name_upper=$(echo "$project_name" | tr '[:lower:]' '[:upper:]' | tr '-' '_')
    local project_name_title=$(echo "$project_name" | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')
    local project_name_snake=$(echo "$project_name" | tr '-' '_')

    print_info "Formatos:"
    echo "  - Original: $project_name"
    echo "  - Upper: $project_name_upper"
    echo "  - Title: $project_name_title"
    echo "  - Snake: $project_name_snake"
    echo ""

    # Lista de arquivos para substituição
    local files_to_update=(
        "README.md"
        "setup.py"
        "scaffold-project.code-workspace"
        ".env.example"
        "docker/Dockerfile"
        "docker-compose.yml"
        ".github/workflows/ci.yml"
        "Makefile"
    )

    for file in "${files_to_update[@]}"; do
        if [[ -f "$file" ]]; then
            print_info "Atualizando: $file"

            # Substitui placeholders
            sed -i "s/scaffold-project/$project_name/g" "$file"
            sed -i "s/SCAFFOLD_PROJECT/$project_name_upper/g" "$file"
            sed -i "s/Scaffold Project/$project_name_title/g" "$file"
            sed -i "s/scaffold_project/$project_name_snake/g" "$file"

            print_success "Atualizado: $file"
        fi
    done

    # Renomeia workspace file
    if [[ -f "scaffold-project.code-workspace" ]]; then
        mv "scaffold-project.code-workspace" "$project_name.code-workspace"
        print_success "Workspace renomeado: $project_name.code-workspace"
    fi
}

# ==============================================================================
# Limpeza de Arquivos Específicos do Template
# ==============================================================================

clean_template_files() {
    print_header "Limpando Arquivos Específicos do Template"

    # Remove documentação de sessões anteriores
    if [[ -d "docs/SESSIONS" ]]; then
        print_info "Removendo docs/SESSIONS"
        rm -rf "docs/SESSIONS"
        print_success "Sessões antigas removidas"
    fi

    # Remove arquivos de documentação do template
    local template_docs=(
        "docs/MAKEFILE.md"
        "docs/TEMPLATE_USAGE.md"
    )

    for doc in "${template_docs[@]}"; do
        if [[ -f "$doc" ]]; then
            print_info "Removendo: $doc"
            rm -f "$doc"
            print_success "Removido: $doc"
        fi
    done

    # Limpa arquivos de exemplo (se existirem)
    print_info "Limpando arquivos de exemplo..."
    find src -type f -name "example_*.py" -delete 2>/dev/null || true
    find tests -type f -name "test_example_*.py" -delete 2>/dev/null || true

    print_success "Arquivos do template limpos"
}

# ==============================================================================
# Inicialização Git
# ==============================================================================

reinitialize_git() {
    print_header "Reinicializando Repositório Git"

    # Remove histórico Git existente
    if [[ -d ".git" ]]; then
        print_warning "Removendo histórico Git do template..."
        rm -rf .git
        print_success "Histórico Git removido"
    fi

    # Inicializa novo repositório
    print_info "Inicializando novo repositório Git..."
    git init
    git add .
    git commit -m "feat: Initial commit from scaffold-project template

Created new project using enterprise default template
- Configured shared Copilot rules via symlinks
- Customized project structure
- Ready for development"

    print_success "Novo repositório Git inicializado"

    echo ""
    print_info "Para configurar remote:"
    echo "  git remote add origin <url-do-repositorio>"
    echo "  git branch -M main"
    echo "  git push -u origin main"
}

# ==============================================================================
# Finalização
# ==============================================================================

run_makefile_init() {
    print_header "Executando Inicialização do Makefile"

    if command -v make &> /dev/null; then
        print_info "Executando: make init"
        make init
        print_success "Makefile init executado"
    else
        print_warning "Make não encontrado, pulando inicialização"
    fi
}

print_next_steps() {
    local project_name="$1"

    print_header "🎉 Projeto Inicializado com Sucesso!"

    echo -e "${GREEN}Seu novo projeto '$project_name' está pronto!${NC}\n"

    echo "📋 Próximos Passos:"
    echo ""
    echo "1. Configure as variáveis de ambiente:"
    echo "   ${BLUE}code .env.example${NC}"
    echo "   ${BLUE}cp .env.example .env${NC}"
    echo ""
    echo "2. Escolha a linguagem principal:"
    echo "   ${BLUE}make setup-python${NC}  # Para Python"
    echo "   ${BLUE}make setup-node${NC}    # Para Node.js"
    echo ""
    echo "3. Configure o repositório remoto:"
    echo "   ${BLUE}git remote add origin <url>${NC}"
    echo "   ${BLUE}git push -u origin main${NC}"
    echo ""
    echo "4. Instale dependências:"
    echo "   ${BLUE}make install${NC}"
    echo ""
    echo "5. Execute testes:"
    echo "   ${BLUE}make test${NC}"
    echo ""
    echo "6. Veja todos os comandos disponíveis:"
    echo "   ${BLUE}make help${NC}"
    echo ""
    echo "📚 Documentação: ${BLUE}docs/INDEX.md${NC}"
    echo ""
}

# ==============================================================================
# Main
# ==============================================================================

main() {
    local project_name="${1:-}"

    print_header "🚀 Inicialização de Novo Projeto"

    # Validações
    validate_project_name "$project_name"
    check_shared_config_exists
    check_required_files

    # Confirmação
    echo ""
    echo -e "${YELLOW}Atenção: Este script irá:${NC}"
    echo "  1. Configurar symlinks para arquivos compartilhados"
    echo "  2. Substituir 'scaffold-project' por '$project_name' em todos os arquivos"
    echo "  3. Remover histórico Git e criar novo repositório"
    echo "  4. Limpar arquivos específicos do template"
    echo ""
    read -p "Deseja continuar? (s/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_warning "Operação cancelada"
        exit 0
    fi

    # Execução
    setup_symlinks
    replace_placeholders "$project_name"
    clean_template_files
    reinitialize_git
    run_makefile_init

    # Finalização
    print_next_steps "$project_name"
}

# Executa script
main "$@"
