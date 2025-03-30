#!/bin/bash
# ci_regression_tests.sh - Script para executar testes de regressão

set -e

# Função para exibir mensagens formatadas
function log() {
    echo -e "\n\033[1;34m==>\033[0m \033[1m$1\033[0m"
}

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
export TEST_ENV="ci"
export LOG_LEVEL="INFO"

# Executar verificações de código
log "Executando verificações de estilo de código"
if command -v black &> /dev/null; then
    black --check .
fi

if command -v flake8 &> /dev/null; then
    flake8 .
fi

if command -v mypy &> /dev/null; then
    mypy .
fi

# Executar testes de unidade
log "Executando testes de unidade"
python -m pytest tests/ -v --cov=backend --cov=models

# Executar testes de integração
log "Executando testes de integração"
python -m pytest integration/ -v

# Executar testes de regressão se o script existir
if [ -f "run_regression_tests.py" ]; then
    log "Executando testes de regressão"
    python run_regression_tests.py
fi

log "Todos os testes foram concluídos com sucesso!"