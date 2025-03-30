#!/bin/bash
# setup_dev_environment.sh - Script para configurar ambiente de desenvolvimento

set -e  # Interrompe o script se algum comando falhar

echo "=== Configurando ambiente de desenvolvimento para CrossDebate ==="

# Detecção do sistema operacional
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="MacOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    OS="Windows"
else
    OS="Desconhecido"
fi

echo "Sistema operacional detectado: $OS"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
echo "Versão do Python encontrada: $PYTHON_VERSION"

# Verificar e criar ambiente virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    echo "Ambiente virtual criado com sucesso."
else
    echo "Ambiente virtual já existe."
fi

# Ativar o ambiente virtual
if [ "$OS" == "Windows" ]; then
    echo "Para ativar o ambiente virtual, execute: venv\\Scripts\\activate"
else
    echo "Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Instalar dependências
echo "Atualizando pip..."
pip install --upgrade pip

echo "Instalando dependências de desenvolvimento..."
pip install -r requirements-dev.txt

echo "Instalando dependências do projeto..."
pip install -r requirements.txt

# Instalar hooks do Git
if [ -f "instalar_hooks_git.sh" ]; then
    echo "Instalando hooks do Git..."
    bash instalar_hooks_git.sh
fi

# Verificar e criar arquivo de configuração local se não existir
if [ ! -f ".env.local" ]; then
    echo "Criando arquivo .env.local para configurações locais..."
    cat > .env.local << EOF
# Configurações locais do CrossDebate
ENVIRONMENT=development
LOG_LEVEL=DEBUG
PORT=8000
HOST=0.0.0.0
RELOAD=true

# Configurações do banco de dados
DB_TYPE=sqlite
DB_PATH=./data/crossdebate.db

# Caminhos para modelos
MODELS_DIR=./models
EOF
    echo "Arquivo .env.local criado com configurações padrão."
fi

echo "=== Configuração do ambiente de desenvolvimento concluída ==="
echo "Para iniciar o servidor de desenvolvimento, execute: python -m backend.start_server"
echo "Ou utilize: ./run_dev_server.sh"