#!/bin/bash
# check_system_requirements.sh - Verifica requisitos do sistema para CrossDebate

set -e

echo "=== Verificando requisitos do sistema para CrossDebate ==="

# Função para verificar versão do Python
check_python() {
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version | awk '{print $2}')
        echo "Python encontrado: $python_version"
        
        # Verificar se é pelo menos 3.8
        if python3 -c 'import sys; sys.exit(0) if sys.version_info >= (3, 8) else sys.exit(1)'; then
            echo "✅ Versão do Python atende aos requisitos"
        else
            echo "❌ Versão do Python não atende aos requisitos (3.8+)"
            return 1
        fi
    else
        echo "❌ Python 3 não encontrado"
        return 1
    fi
    return 0
}

# Função para verificar memória disponível
check_memory() {
    if [ "$(uname)" == "Linux" ]; then
        # Verificação para Linux
        total_mem=$(free -m | awk '/^Mem:/{print $2}')
        echo "Memória total: ${total_mem}MB"
        if [ $total_mem -ge 8000 ]; then
            echo "✅ Memória suficiente para execução (mínimo 8GB)"
        else
            echo "⚠️ Memória disponível abaixo do recomendado (8GB)"
            if [ $total_mem -lt 4000 ]; then
                echo "❌ Memória insuficiente para modelos grandes"
                return 1
            fi
        fi
    elif [ "$(uname)" == "Darwin" ]; then
        # Verificação para macOS
        total_mem=$(sysctl -n hw.memsize | awk '{print $0 / 1024 / 1024}')
        total_mem=${total_mem%.*}
        echo "Memória total: ${total_mem}MB"
        if [ $total_mem -ge 8000 ]; then
            echo "✅ Memória suficiente para execução (mínimo 8GB)"
        else
            echo "⚠️ Memória disponível abaixo do recomendado (8GB)"
            if [ $total_mem -lt 4000 ]; then
                echo "❌ Memória insuficiente para modelos grandes"
                return 1
            fi
        fi
    else
        echo "⚠️ Sistema operacional não reconhecido, não foi possível verificar memória"
    fi
    return 0
}

# Função para verificar espaço em disco
check_disk_space() {
    # Verificar espaço no diretório atual
    if [ "$(uname)" == "Linux" ] || [ "$(uname)" == "Darwin" ]; then
        available_space=$(df -m . | awk 'NR==2 {print $4}')
        echo "Espaço disponível: ${available_space}MB"
        if [ $available_space -ge 10000 ]; then
            echo "✅ Espaço em disco suficiente (mínimo 10GB)"
        else
            echo "⚠️ Espaço em disco abaixo do recomendado (10GB)"
            if [ $available_space -lt 5000 ]; then
                echo "❌ Espaço em disco insuficiente para modelos"
                return 1
            fi
        fi
    else
        echo "⚠️ Sistema operacional não reconhecido, não foi possível verificar espaço em disco"
    fi
    return 0
}

# Função para verificar dependências opcionais
check_optional_dependencies() {
    echo "Verificando dependências opcionais..."
    
    # Verificar ferramentas de desenvolvimento
    for cmd in git npm node; do
        if command -v $cmd &> /dev/null; then
            echo "✅ $cmd encontrado: $(command -v $cmd)"
        else
            echo "⚠️ $cmd não encontrado (opcional)"
        fi
    done
    
    # Verificar suporte a GPU (apenas Linux)
    if [ "$(uname)" == "Linux" ]; then
        if command -v nvidia-smi &> /dev/null; then
            echo "✅ NVIDIA GPU encontrada"
            nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
        else
            echo "⚠️ GPU NVIDIA não detectada"
        fi
    fi
}

# Executar verificações
echo "Executando verificações..."
python_ok=true
mem_ok=true
disk_ok=true

check_python || python_ok=false
check_memory || mem_ok=false
check_disk_space || disk_ok=false
check_optional_dependencies

# Resumo
echo ""
echo "=== Resumo da verificação de requisitos ==="
if $python_ok && $mem_ok && $disk_ok; then
    echo "✅ Todos os requisitos essenciais foram atendidos!"
    echo "Você pode prosseguir com a configuração do ambiente usando ./setup_dev_environment.sh"
else
    echo "❌ Alguns requisitos não foram atendidos. Revise as mensagens acima."
fi

exit 0