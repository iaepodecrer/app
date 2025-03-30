#!/bin/bash
# ci_build.sh - Script de build para CI/CD do CrossDebate
#
# Este script automatiza o processo de build e deploy em ambientes de CI/CD,
# integrando os scripts de prepare_feature.sh e deploy.sh em um único fluxo.
#
# Uso: ./ci_build.sh [branch] [ambiente] [--skip-tests] [--skip-backup] [--force]
# Exemplo: ./ci_build.sh feature/nova-visualizacao staging

set -e

# Timestamp para medição de performance
START_TIME=$(date +%s)

# Parse de argumentos
if [ $# -lt 2 ]; then
    echo "Uso: ./ci_build.sh [branch] [ambiente] [--skip-tests] [--skip-backup] [--force]"
    exit 1
fi

BRANCH=$1
ENVIRONMENT=$2
shift 2

# Opções adicionais para passar para os scripts
PREPARE_OPTS="--ci-mode --skip-checkout"
DEPLOY_OPTS=""

# Parse de opções extras
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-tests)
      PREPARE_OPTS="$PREPARE_OPTS --quick"
      DEPLOY_OPTS="$DEPLOY_OPTS --skip-tests"
      ;;
    --skip-backup)
      DEPLOY_OPTS="$DEPLOY_OPTS --skip-backup"
      ;;
    --force)
      DEPLOY_OPTS="$DEPLOY_OPTS --force"
      ;;
    *)
      echo "Opção desconhecida: $1"
      exit 1
      ;;
  esac
  shift
done

# Funções de Utilidade
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

function timing() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    echo "⏱️ Tempo decorrido: ${elapsed}s"
}

# Iniciar o processo de build
log "Iniciando processo de build para branch '$BRANCH' no ambiente '$ENVIRONMENT'"
timing

# Checkout do branch
log "Fazendo checkout do branch $BRANCH..."
git fetch origin
git checkout $BRANCH || error "Falha ao fazer checkout do branch $BRANCH"
git pull origin $BRANCH || error "Falha ao atualizar o branch $BRANCH"

# Configurar cache para acelerar o build
CACHE_DIR="./.build_cache"
mkdir -p "$CACHE_DIR/pip"
mkdir -p "$CACHE_DIR/npm"
export PIP_CACHE_DIR="$CACHE_DIR/pip"

if command -v npm &> /dev/null; then
    npm config set cache "$CACHE_DIR/npm"
fi

# Etapa 1: Preparar a feature
log "Preparando a feature..."
./prepare_feature.sh $BRANCH $PREPARE_OPTS
PREPARE_EXIT_CODE=$?

if [ $PREPARE_EXIT_CODE -ne 0 ]; then
    error "Falha na preparação da feature. Abortando build."
fi

log "Preparação de feature concluída com sucesso!"
timing

# Etapa 2: Realizar o deploy
log "Iniciando deploy para o ambiente '$ENVIRONMENT'..."
./deploy.sh $BRANCH $ENVIRONMENT $DEPLOY_OPTS
DEPLOY_EXIT_CODE=$?

if [ $DEPLOY_EXIT_CODE -ne 0 ]; then
    error "Falha no deploy para o ambiente '$ENVIRONMENT'."
fi

log "Deploy para o ambiente '$ENVIRONMENT' concluído com sucesso!"

# Etapa 3: Registrar informações do build completo
BUILD_LOG_FILE="build_history.log"
END_TIME=$(date +%s)
BUILD_DURATION=$((END_TIME - START_TIME))

echo "[$(date)] - Build e deploy de '$BRANCH' para '$ENVIRONMENT' - Duração: ${BUILD_DURATION}s" >> $BUILD_LOG_FILE

# Verificar estado atual da aplicação
if [ "$ENVIRONMENT" != "development" ]; then
    log "Verificando estado da aplicação..."
    
    # Carregar configuração do ambiente
    source config/deploy_environments.sh $ENVIRONMENT
    
    # Verificar se o serviço está respondendo
    if curl -s "http://${SERVER_HOST}:${SERVER_PORT}/health" | grep -q "ok"; then
        success "Serviço está saudável no ambiente $ENVIRONMENT!"
    else
        error "Serviço não está respondendo corretamente no ambiente $ENVIRONMENT!"
    fi
fi

success "Processo de build e deploy concluído com sucesso em ${BUILD_DURATION}s!"
timing

# Exibir um resumo do build
log "Resumo do Build:"
echo "- Branch: $BRANCH"
echo "- Ambiente: $ENVIRONMENT"
echo "- Duração total: ${BUILD_DURATION}s"
echo "- Status: SUCESSO"

exit 0