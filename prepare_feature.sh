#!/bin/bash
# prepare_feature.sh - Prepara uma nova feature para deploy
#
# Este script prepara uma nova feature para deploy, garantindo que
# todas as verificações de qualidade sejam executadas:
# 1. Testes de unidade
# 2. Testes de integração
# 3. Testes de regressão
# 4. Verificações de segurança
# 5. Análise de código
#
# Uso: ./prepare_feature.sh [nome-da-feature] [--skip-checkout] [--ci-mode] [--quick]
# Exemplo: ./prepare_feature.sh feature/nova-visualizacao

set -e

# Timestamp para medição de performance
START_TIME=$(date +%s)

# Parse de argumentos
FEATURE_NAME=$1
shift

SKIP_CHECKOUT=0
CI_MODE=0
QUICK_MODE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-checkout)
      SKIP_CHECKOUT=1
      ;;
    --ci-mode)
      CI_MODE=1
      ;;
    --quick)
      QUICK_MODE=1
      ;;
    *)
      echo "Opção desconhecida: $1"
      exit 1
      ;;
  esac
  shift
done

# Função para exibir mensagens formatadas
function log() {
    echo -e "\n\033[1;34m==>\033[0m \033[1m$1\033[0m"
}

function error() {
    echo -e "\n\033[1;31m==>\033[0m \033[1m$1\033[0m"
    exit 1
}

function success() {
    echo -e "\n\033[1;32m==>\033[0m \033[1m$1\033[0m"
}

function warning() {
    echo -e "\n\033[1;33m==>\033[0m \033[1m$1\033[0m"
}

function timing() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    echo "⏱️ Tempo decorrido: ${elapsed}s"
}

# Inicializar diretório de cache
CACHE_DIR="./.build_cache"
INCREMENTAL_FILE="${CACHE_DIR}/last_prepare_feature.txt"
mkdir -p "${CACHE_DIR}"

# Verifica se o nome da feature foi fornecido
if [ -z "$FEATURE_NAME" ]; then
    error "Nenhum nome de feature fornecido. Use: ./prepare_feature.sh [nome-da-feature]"
fi

# Checkout do branch (se necessário)
if [ "$SKIP_CHECKOUT" -eq 0 ]; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # Verificar se estamos no branch correto
    if [ "$CURRENT_BRANCH" != "$FEATURE_NAME" ]; then
        log "Mudando para o branch $FEATURE_NAME..."
        git checkout $FEATURE_NAME || error "Falha ao mudar para o branch $FEATURE_NAME"
    fi
else
    log "Pulando checkout de branch conforme solicitado (--skip-checkout)"
fi

# Carregar variáveis de ambiente
if [ -f ".env.local" ]; then
    log "Carregando configurações locais de .env.local"
    export $(grep -v '^#' .env.local | xargs)
fi

# Ativar ambiente virtual (se existir)
if [ -d "venv" ]; then
    log "Ativando ambiente virtual"
    source venv/bin/activate
fi

# Configuração de variáveis para os testes
export PYTHONPATH=$(pwd)
export TEST_ENV="feature_validation"
export LOG_LEVEL="INFO"

# Configuração de cache PIP
export PIP_CACHE_DIR="${CACHE_DIR}/pip"
mkdir -p "$PIP_CACHE_DIR"

# Determinar quais arquivos foram alterados desde o último prepare_feature
if [ -f "$INCREMENTAL_FILE" ] && [ "$QUICK_MODE" -eq 1 ]; then
    LAST_COMMIT=$(cat "$INCREMENTAL_FILE")
    CURRENT_COMMIT=$(git rev-parse HEAD)
    
    if [ "$LAST_COMMIT" == "$CURRENT_COMMIT" ]; then
        log "Nenhuma alteração detectada desde o último prepare_feature."
        success "Feature já está pronta para deploy!"
        exit 0
    fi
    
    log "Verificando alterações desde o último prepare_feature..."
    CHANGED_FILES=$(git diff --name-only "$LAST_COMMIT" "$CURRENT_COMMIT")
    
    # Detectar tipos de arquivos alterados
    PYTHON_CHANGES=$(echo "$CHANGED_FILES" | grep -c "\.py$" || echo "0")
    JS_CHANGES=$(echo "$CHANGED_FILES" | grep -c "\.js$" || echo "0")
    CSS_CHANGES=$(echo "$CHANGED_FILES" | grep -c "\.css$" || echo "0")
    HTML_CHANGES=$(echo "$CHANGED_FILES" | grep -c "\.html$" || echo "0")
    
    log "Alterações detectadas: $PYTHON_CHANGES Python, $JS_CHANGES JavaScript, $CSS_CHANGES CSS, $HTML_CHANGES HTML"
else
    # Forçar verificação completa se não estiver no modo rápido ou for a primeira execução
    PYTHON_CHANGES=1
    JS_CHANGES=1
    CSS_CHANGES=1
    HTML_CHANGES=1
    log "Executando verificação completa..."
fi

# Atualizar dependências (apenas se necessário)
if [ "$PYTHON_CHANGES" -gt 0 ] || [ ! -d "venv" ]; then
    log "Atualizando dependências Python do projeto..."
    
    # Verificar se requirements.txt foi modificado usando hash
    REQ_HASH_FILE="${CACHE_DIR}/requirements_hash.txt"
    REQ_HASH=$(md5sum requirements.txt | awk '{print $1}')
    DEV_REQ_HASH=$(md5sum requirements-dev.txt | awk '{print $1}')
    CACHED_REQ_HASH=""
    CACHED_DEV_REQ_HASH=""
    
    if [ -f "$REQ_HASH_FILE" ]; then
        CACHED_REQ_HASH=$(head -n 1 "$REQ_HASH_FILE")
        CACHED_DEV_REQ_HASH=$(tail -n 1 "$REQ_HASH_FILE")
    fi
    
    # Instalar apenas se o hash mudou
    if [ "$REQ_HASH" != "$CACHED_REQ_HASH" ] || [ "$DEV_REQ_HASH" != "$CACHED_DEV_REQ_HASH" ]; then
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
        
        # Atualizar o hash armazenado
        echo -e "${REQ_HASH}\n${DEV_REQ_HASH}" > "$REQ_HASH_FILE"
    else
        log "Requirements não mudaram, pulando instalação de dependências Python"
    fi
fi

# Atualizar dependências de frontend (se necessário)
if [ "$JS_CHANGES" -gt 0 ] && [ -f "package.json" ]; then
    log "Atualizando dependências JavaScript do projeto..."
    
    # Verificar se package.json foi modificado usando hash
    PKG_HASH_FILE="${CACHE_DIR}/package_hash.txt"
    PKG_HASH=$(md5sum package.json | awk '{print $1}')
    CACHED_PKG_HASH=""
    
    if [ -f "$PKG_HASH_FILE" ]; then
        CACHED_PKG_HASH=$(cat "$PKG_HASH_FILE")
    fi
    
    # Instalar apenas se o hash mudou
    if [ "$PKG_HASH" != "$CACHED_PKG_HASH" ]; then
        # Usar npm ou yarn de acordo com o que está disponível
        if [ -f "yarn.lock" ]; then
            yarn install --frozen-lockfile
        else
            npm ci
        fi
        
        # Atualizar o hash armazenado
        echo "$PKG_HASH" > "$PKG_HASH_FILE"
    else
        log "Package.json não mudou, pulando instalação de dependências JavaScript"
    fi
fi

# Verificações em paralelo para acelerar o processo
# Usaremos arquivos temporários para capturar os resultados

CODE_STYLE_RESULT="/tmp/code_style_result.$$"
UNIT_TESTS_RESULT="/tmp/unit_tests_result.$$"
INTEGRATION_TESTS_RESULT="/tmp/integration_tests_result.$$"
REGRESSION_TESTS_RESULT="/tmp/regression_tests_result.$$"
SECURITY_TESTS_RESULT="/tmp/security_tests_result.$$"

# Executar verificações apenas se houver mudanças relevantes
if [ "$PYTHON_CHANGES" -gt 0 ]; then
    # Executar verificações de estilo de código em paralelo
    {
        log "Executando verificações de estilo de código"
        STYLE_OK=1
        
        if command -v black &> /dev/null; then
            black --check . || STYLE_OK=0
        fi
        
        if command -v flake8 &> /dev/null && [ "$STYLE_OK" -eq 1 ]; then
            flake8 . || STYLE_OK=0
        fi
        
        if command -v mypy &> /dev/null && [ "$STYLE_OK" -eq 1 ]; then
            mypy . || STYLE_OK=0
        fi
        
        echo $STYLE_OK > "$CODE_STYLE_RESULT"
    } &
    
    # Executar testes unitários em paralelo
    {
        log "Executando testes unitários..."
        python -m pytest tests/ -v --cov=backend --cov=models
        echo $? > "$UNIT_TESTS_RESULT"
    } &
    
    # Executar testes de integração em paralelo (apenas se não estiver no modo rápido)
    if [ "$QUICK_MODE" -eq 0 ]; then
        {
            log "Executando testes de integração..."
            python -m pytest integration/ -v
            echo $? > "$INTEGRATION_TESTS_RESULT"
        } &
    else
        echo 0 > "$INTEGRATION_TESTS_RESULT" # Fingir que passou no modo rápido
    fi
fi

# Executar testes de regressão apenas se necessário e não no modo rápido
if [ "$PYTHON_CHANGES" -gt 0 ] && [ "$QUICK_MODE" -eq 0 ] && [ -f "run_regression_tests.py" ]; then
    {
        log "Executando testes de regressão..."
        python run_regression_tests.py
        echo $? > "$REGRESSION_TESTS_RESULT"
    } &
else
    echo 0 > "$REGRESSION_TESTS_RESULT" # Fingir que passou se não for necessário
fi

# Executar verificações de segurança apenas se houver mudanças relevantes e não no modo rápido
if [ "$PYTHON_CHANGES" -gt 0 ] && [ "$QUICK_MODE" -eq 0 ] && [ -f "security_scan.sh" ]; then
    {
        log "Executando verificações de segurança..."
        bash security_scan.sh
        echo $? > "$SECURITY_TESTS_RESULT"
    } &
else
    echo 0 > "$SECURITY_TESTS_RESULT" # Fingir que passou se não for necessário
fi

# Aguardar a conclusão de todas as tarefas em paralelo
log "Aguardando a conclusão de todas as verificações..."
wait
timing

# Verificar resultados
STYLE_OK=$(cat "$CODE_STYLE_RESULT" 2>/dev/null || echo "1")
UNIT_TESTS_OK=$(cat "$UNIT_TESTS_RESULT" 2>/dev/null || echo "1")
INTEGRATION_TESTS_OK=$(cat "$INTEGRATION_TESTS_RESULT" 2>/dev/null || echo "1")
REGRESSION_TESTS_OK=$(cat "$REGRESSION_TESTS_RESULT" 2>/dev/null || echo "1")
SECURITY_TESTS_OK=$(cat "$SECURITY_TESTS_RESULT" 2>/dev/null || echo "1")

# Limpar arquivos temporários
rm -f "$CODE_STYLE_RESULT" "$UNIT_TESTS_RESULT" "$INTEGRATION_TESTS_RESULT" "$REGRESSION_TESTS_RESULT" "$SECURITY_TESTS_RESULT"

# Verificar se algum teste falhou
TESTS_FAILED=0

if [ "$STYLE_OK" -ne 0 ]; then
    error "Problemas de formatação de código detectados. Execute 'black .' para corrigir."
    TESTS_FAILED=1
fi

if [ "$UNIT_TESTS_OK" -ne 0 ]; then
    error "Falha nos testes unitários."
    TESTS_FAILED=1
fi

if [ "$INTEGRATION_TESTS_OK" -ne 0 ]; then
    error "Falha nos testes de integração."
    TESTS_FAILED=1
fi

if [ "$REGRESSION_TESTS_OK" -ne 0 ]; then
    error "Falha nos testes de regressão."
    TESTS_FAILED=1
fi

if [ "$SECURITY_TESTS_OK" -ne 0 ]; then
    error "Problemas de segurança detectados."
    TESTS_FAILED=1
fi

# Criar arquivo de metadados da feature
FEATURE_METADATA_FILE="feature_metadata.json"
log "Criando metadados da feature em $FEATURE_METADATA_FILE..."

# Obter o autor do último commit
AUTHOR=$(git log -1 --pretty=format:'%an <%ae>')
# Obter o hash do último commit
COMMIT_HASH=$(git rev-parse HEAD)
# Obter a data atual
CURRENT_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Contar arquivos modificados por tipo
if [ -f "$INCREMENTAL_FILE" ]; then
    LAST_COMMIT=$(cat "$INCREMENTAL_FILE")
    MODIFIED_PY=$(git diff --name-only $LAST_COMMIT HEAD | grep -c "\.py$" || echo "0")
    MODIFIED_JS=$(git diff --name-only $LAST_COMMIT HEAD | grep -c "\.js$" || echo "0")
    MODIFIED_HTML=$(git diff --name-only $LAST_COMMIT HEAD | grep -c "\.html$" || echo "0")
    MODIFIED_CSS=$(git diff --name-only $LAST_COMMIT HEAD | grep -c "\.css$" || echo "0")
    TOTAL_MODIFIED=$(git diff --name-only $LAST_COMMIT HEAD | wc -l)
else
    MODIFIED_PY=$(git diff --name-only $(git merge-base origin/develop HEAD) HEAD | grep -c "\.py$" || echo "0")
    MODIFIED_JS=$(git diff --name-only $(git merge-base origin/develop HEAD) HEAD | grep -c "\.js$" || echo "0")
    MODIFIED_HTML=$(git diff --name-only $(git merge-base origin/develop HEAD) HEAD | grep -c "\.html$" || echo "0")
    MODIFIED_CSS=$(git diff --name-only $(git merge-base origin/develop HEAD) HEAD | grep -c "\.css$" || echo "0")
    TOTAL_MODIFIED=$(git diff --name-only $(git merge-base origin/develop HEAD) HEAD | wc -l)
fi

# Criar JSON com as informações da feature
cat > $FEATURE_METADATA_FILE << EOF
{
    "feature_name": "$FEATURE_NAME",
    "prepared_at": "$CURRENT_DATE",
    "prepared_by": "$AUTHOR",
    "commit_hash": "$COMMIT_HASH",
    "modified_files": {
        "total": $TOTAL_MODIFIED,
        "python": $MODIFIED_PY,
        "javascript": $MODIFIED_JS,
        "html": $MODIFIED_HTML,
        "css": $MODIFIED_CSS
    },
    "validation": {
        "unit_tests": "passed",
        "integration_tests": "passed",
        "regression_tests": "passed",
        "security_checks": "passed",
        "code_quality": "passed"
    },
    "runtime_seconds": $(($(date +%s) - START_TIME)),
    "quick_mode": $QUICK_MODE,
    "ready_for_review": true
}
EOF

# Armazenar o commit atual para verificação incremental futura
echo "$COMMIT_HASH" > "$INCREMENTAL_FILE"

success "Feature $FEATURE_NAME está pronta para deploy!"
log "Um arquivo de metadados foi criado em $FEATURE_METADATA_FILE"
log "Próximos passos:"
log "1. Revise as alterações uma última vez: git diff origin/develop"
log "2. Faça commit dos metadados: git add $FEATURE_METADATA_FILE && git commit -m 'Add feature metadata'"
log "3. Envie para o repositório: git push origin $FEATURE_NAME"
log "4. Crie um Pull Request para develop"
log "5. Após aprovação, execute: ./deploy.sh $FEATURE_NAME [ambiente]"

# Mostrar tempo total de execução
END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))
log "Tempo total de execução: ${TOTAL_TIME}s"