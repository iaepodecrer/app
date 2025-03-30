#!/bin/bash
# run_dev_server.sh - Script para iniciar o servidor em modo de desenvolvimento

set -e

# Carregar variáveis de ambiente locais se existirem
if [ -f ".env.local" ]; then
    echo "Carregando configurações locais de .env.local..."
    export $(grep -v '^#' .env.local | xargs)
fi

# Ativar ambiente virtual
if [ -d "venv" ]; then
    echo "Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Verificar dependências
if ! pip list | grep -q "uvicorn"; then
    echo "Dependências não encontradas. Execute ./setup_dev_environment.sh primeiro."
    exit 1
fi

# Iniciar o servidor
echo "Iniciando servidor de desenvolvimento..."
python -m backend.start_server

# Capturar saída do servidor quando for encerrado
if [ $? -ne 0 ]; then
    echo "O servidor foi encerrado com erros. Verifique os logs para mais informações."
    exit 1
fi