#!/bin/bash
# deploy.sh - Script principal de deploy para CrossDebate
#
# Este script realiza o deploy de uma feature para um ambiente específico.
# Ele gerencia todo o ciclo de vida do processo de deployment:
# 1. Validação prévia da feature
# 2. Backup do ambiente atual
# 3. Deploy da nova versão
# 4. Migração de banco de dados (se aplicável)
# 5. Verificação pós-deploy
# 6. Possibilidade de rollback em caso de falha
#
# Uso: ./deploy.sh [branch/tag] [ambiente] [--skip-tests] [--skip-backup] [--force]
# Exemplo: ./deploy.sh feature/nova-visualizacao staging

set -e

# Configuração inicial
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${SCRIPT_DIR}/.build_cache"
START_TIME=$(date +%s)

# Análise de argumentos avançados
VERSION=$1
DEPLOY_ENV=$2
shift 2

SKIP_TESTS=0
SKIP_BACKUP=0
FORCE_DEPLOY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-tests)
      SKIP_TESTS=1
      ;;
    --skip-backup)
      SKIP_BACKUP=1
      ;;
    --force)
      FORCE_DEPLOY=1
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

function warning() {
    echo -e "\n\033[1;33m==>\033[0m \033[1m$1\033[0m"
}

function timing() {
    local current_time=$(date +%s)
    local elapsed=$((current_time - START_TIME))
    echo "⏱️ Tempo decorrido: ${elapsed}s"
}

# Função de cache de dependências
function setup_dependency_cache() {
    log "Configurando cache de dependências..."
    mkdir -p "${CACHE_DIR}/pip"
    mkdir -p "${CACHE_DIR}/npm"
    
    # Configurar pip para usar cache
    export PIP_CACHE_DIR="${CACHE_DIR}/pip"
    
    # Configurar npm para usar cache
    if command -v npm &> /dev/null; then
        npm config set cache "${CACHE_DIR}/npm"
    fi
    
    success "Cache de dependências configurado"
}

# Função de backup melhorada com opção de skip
function do_backup() {
    if [ "$SKIP_BACKUP" -eq 1 ]; then
        warning "Backup ignorado conforme solicitado (--skip-backup)"
        return 0
    fi
    
    log "Realizando backup do ambiente $DEPLOY_ENV..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_NAME="${PROJECT_NAME}_${DEPLOY_ENV}_${TIMESTAMP}"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    mkdir -p $BACKUP_DIR
    
    # Backup do código e banco em paralelo
    {
        # Backup do código
        if [ -d "$DEPLOY_PATH" ]; then
            log "Fazendo backup do código..."
            tar -czf "${BACKUP_PATH}_code.tar.gz" -C $(dirname $DEPLOY_PATH) $(basename $DEPLOY_PATH) || warning "Falha no backup do código"
        fi
    } &
    
    {
        # Backup do banco de dados
        case "$DB_TYPE" in
            "sqlite")
                if [ -f "$DB_PATH" ]; then
                    log "Fazendo backup do banco SQLite..."
                    cp "$DB_PATH" "${BACKUP_PATH}_db.sqlite" || warning "Falha no backup do banco de dados SQLite"
                fi
                ;;
            "postgresql")
                log "Fazendo backup do banco PostgreSQL..."
                export PGPASSWORD=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:([^@]*)@.*/\1/')
                pg_user=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:\/\/([^:]*):.*@.*/\1/')
                pg_host=$(echo $DB_CONNECTION_STRING | sed -E 's/.*@([^:]*):.*\/.*/\1/')
                pg_port=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:([0-9]+)\/.*/\1/')
                pg_db=$(echo $DB_CONNECTION_STRING | sed -E 's/.*\/([^?]*).*/\1/')
                
                pg_dump -h $pg_host -p $pg_port -U $pg_user -d $pg_db -f "${BACKUP_PATH}_db.sql" || warning "Falha no backup do banco de dados PostgreSQL"
                ;;
            *)
                warning "Tipo de banco de dados não suportado para backup: $DB_TYPE"
                ;;
        esac
    } &
    
    # Aguardar conclusão dos backups paralelos
    wait
    
    success "Backup concluído: ${BACKUP_PATH}"
    echo "BACKUP_PATH=${BACKUP_PATH}" > last_backup.env
}

# Função de rollback
function do_rollback() {
    warning "Iniciando procedimento de rollback..."
    
    if [ -f "last_backup.env" ]; then
        source last_backup.env
        
        if [ -z "$BACKUP_PATH" ]; then
            error "Caminho do backup não encontrado"
        fi
        
        log "Restaurando a partir do backup: $BACKUP_PATH"
        
        # Parar o serviço
        if [ -n "$SERVICE_NAME" ]; then
            log "Parando serviço: $SERVICE_NAME"
            sudo systemctl stop $SERVICE_NAME || warning "Falha ao parar o serviço"
        fi
        
        # Restaurações em paralelo para acelerar o processo
        {
            # Restaurar código
            if [ -f "${BACKUP_PATH}_code.tar.gz" ]; then
                log "Restaurando código..."
                rm -rf $DEPLOY_PATH
                mkdir -p $(dirname $DEPLOY_PATH)
                tar -xzf "${BACKUP_PATH}_code.tar.gz" -C $(dirname $DEPLOY_PATH) || error "Falha ao restaurar o código"
            fi
        } &
        
        {
            # Restaurar banco de dados
            case "$DB_TYPE" in
                "sqlite")
                    if [ -f "${BACKUP_PATH}_db.sqlite" ]; then
                        log "Restaurando banco SQLite..."
                        cp "${BACKUP_PATH}_db.sqlite" "$DB_PATH" || error "Falha ao restaurar o banco de dados SQLite"
                    fi
                    ;;
                "postgresql")
                    if [ -f "${BACKUP_PATH}_db.sql" ]; then
                        log "Restaurando banco PostgreSQL..."
                        export PGPASSWORD=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:([^@]*)@.*/\1/')
                        pg_user=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:\/\/([^:]*):.*@.*/\1/')
                        pg_host=$(echo $DB_CONNECTION_STRING | sed -E 's/.*@([^:]*):.*\/.*/\1/')
                        pg_port=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:([0-9]+)\/.*/\1/')
                        pg_db=$(echo $DB_CONNECTION_STRING | sed -E 's/.*\/([^?]*).*/\1/')
                        
                        psql -h $pg_host -p $pg_port -U $pg_user -d $pg_db -f "${BACKUP_PATH}_db.sql" || error "Falha ao restaurar o banco de dados PostgreSQL"
                    fi
                    ;;
                *)
                    warning "Tipo de banco de dados não suportado para restauração: $DB_TYPE"
                    ;;
            esac
        } &
        
        # Aguardar conclusão das restaurações paralelas
        wait
        
        # Iniciar o serviço
        if [ -n "$SERVICE_NAME" ]; then
            log "Iniciando serviço: $SERVICE_NAME"
            sudo systemctl start $SERVICE_NAME || warning "Falha ao iniciar o serviço"
        fi
        
        success "Rollback concluído com sucesso para a versão anterior"
    else
        error "Nenhum backup encontrado para rollback"
    fi
}

# Função de verificação de saúde do serviço aprimorada
function check_health() {
    log "Verificando saúde do serviço..."
    local max_attempts=10
    local wait_time=3
    local attempt=1
    
    # Verificação progressiva - aumenta o wait_time a cada tentativa
    while [ $attempt -le $max_attempts ]; do
        log "Tentativa $attempt de $max_attempts..."
        
        if curl -s "http://${SERVER_HOST}:${SERVER_PORT}/health" | grep -q "ok"; then
            success "Serviço está saudável!"
            return 0
        fi
        
        warning "Serviço ainda não está respondendo. Aguardando ${wait_time}s..."
        sleep $wait_time
        attempt=$((attempt + 1))
        # Aumentar o tempo de espera progressivamente
        wait_time=$((wait_time + 2))
    done
    
    error "Serviço não está saudável após $max_attempts tentativas"
    return 1
}

# Função para construir o ambiente virtual com cache
function build_venv_with_cache() {
    local env_path="$1"
    local req_file="$2"
    local req_hash_file="${CACHE_DIR}/requirements_hash.txt"
    
    # Calcular hash dos arquivos de requirements
    local req_hash=$(md5sum "$req_file" | awk '{print $1}')
    local cached_hash=""
    
    if [ -f "$req_hash_file" ]; then
        cached_hash=$(cat "$req_hash_file")
    fi
    
    # Se o hash é o mesmo e o ambiente virtual existe, pular a instalação
    if [ "$req_hash" == "$cached_hash" ] && [ -d "$env_path" ]; then
        log "Usando ambiente virtual em cache (requirements inalterados)"
        return 0
    fi
    
    # Caso contrário, criar/atualizar o ambiente virtual
    log "Criando/atualizando ambiente virtual..."
    
    # Criar o venv se não existir
    if [ ! -d "$env_path" ]; then
        python -m venv "$env_path"
    fi
    
    # Instalar dependências
    source "$env_path/bin/activate"
    pip install --upgrade pip
    pip install -r "$req_file"
    
    # Salvar o novo hash
    echo "$req_hash" > "$req_hash_file"
    
    success "Ambiente virtual atualizado!"
}

# Verificar argumentos
if [ $# -lt 0 ]; then
    error "Uso: ./deploy.sh [branch/tag] [ambiente] [--skip-tests] [--skip-backup] [--force]"
fi

# Inicializar cache
setup_dependency_cache

# Carregar configurações do ambiente
if [ -f "config/deploy_environments.sh" ]; then
    source config/deploy_environments.sh $DEPLOY_ENV
else
    error "Arquivo de configuração não encontrado: config/deploy_environments.sh"
fi

# Verificar metadados da feature (apenas se não for --force)
if [ "$FORCE_DEPLOY" -eq 0 ] && [ "$SKIP_TESTS" -eq 0 ]; then
    FEATURE_METADATA_FILE="feature_metadata.json"
    if [ -f "$FEATURE_METADATA_FILE" ]; then
        log "Metadados da feature encontrados. Verificando validação..."
        
        # Verificar se os testes foram aprovados
        if ! grep -q '"unit_tests": "passed"' "$FEATURE_METADATA_FILE" || \
           ! grep -q '"integration_tests": "passed"' "$FEATURE_METADATA_FILE" || \
           ! grep -q '"regression_tests": "passed"' "$FEATURE_METADATA_FILE"; then
            error "Esta feature não passou em todos os testes. Execute ./prepare_feature.sh $VERSION primeiro ou use --force."
        fi
        
        success "Validação de feature concluída!"
    else
        warning "Arquivo de metadados não encontrado. Recomenda-se executar './prepare_feature.sh $VERSION' antes do deploy."
        if [ "$FORCE_DEPLOY" -eq 0 ]; then
            read -p "Deseja continuar mesmo assim? (s/N): " continue_without_metadata
            if [[ "$continue_without_metadata" != "s" && "$continue_without_metadata" != "S" ]]; then
                error "Deploy cancelado pelo usuário."
            fi
        fi
    fi
else
    warning "Verificação de metadados ignorada devido às flags --skip-tests ou --force"
fi

log "Iniciando processo de deploy da versão '$VERSION' para o ambiente '$DEPLOY_ENV'"
timing

# Verificar se é deploy local ou remoto
if [ "$DEPLOY_ENV" == "development" ]; then
    # Deploy local
    log "Realizando deploy local..."
    
    # Checkout da versão
    log "Fazendo checkout da versão: $VERSION"
    git checkout $VERSION || error "Falha ao fazer checkout da versão $VERSION"
    
    # Fazer backup (se não for pulado)
    do_backup
    
    # Verificar modificações para build incremental
    CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)
    REBUILD_PYTHON=0
    REBUILD_JS=0
    
    if echo "$CHANGED_FILES" | grep -q "\.py$\|requirements"; then
        REBUILD_PYTHON=1
    fi
    
    if echo "$CHANGED_FILES" | grep -q "\.js$\|package.json"; then
        REBUILD_JS=1
    fi
    
    # Atualizar dependências Python incrementalmente
    if [ "$REBUILD_PYTHON" -eq 1 ]; then
        log "Atualizando dependências Python..."
        build_venv_with_cache "venv" "requirements.txt"
    else
        log "Pulando atualização de dependências Python (sem alterações)"
    fi
    
    # Atualizar dependências JavaScript incrementalmente
    if [ "$REBUILD_JS" -eq 1 ] && [ -f "package.json" ]; then
        log "Atualizando dependências JavaScript..."
        npm ci --prefer-offline || error "Falha ao instalar dependências JavaScript"
    elif [ -f "package.json" ]; then
        log "Pulando atualização de dependências JavaScript (sem alterações)"
    fi
    
    # Realizar migrações de banco de dados (se aplicável)
    log "Aplicando migrações de banco de dados (se existirem)..."
    if [ -f "manage.py" ]; then
        python manage.py migrate || warning "Falha ao aplicar migrações"
    fi
    
    # Reiniciar o servidor com monitoramento
    log "Reiniciando o servidor de desenvolvimento..."
    if pgrep -f "backend.start_server" > /dev/null; then
        pkill -f "backend.start_server" || true
    fi
    
    if [ -f "run_dev_server.sh" ]; then
        ./run_dev_server.sh &
    else
        nohup python -m backend.start_server > server.log 2>&1 &
    fi
    
    # Verificação de saúde
    sleep 3
    check_health
    
    success "Deploy local concluído com sucesso!"
    
else
    # Deploy remoto
    log "Realizando deploy remoto para $DEPLOY_ENV..."
    
    # Verificar SSH
    log "Verificando conexão SSH com $SERVER_HOST..."
    ssh -q $DEPLOY_USER@$SERVER_HOST exit || error "Não foi possível conectar via SSH. Verifique as credenciais e a rede."
    
    # Verificar diretório de deploy
    log "Verificando diretório de deploy..."
    ssh $DEPLOY_USER@$SERVER_HOST "mkdir -p $DEPLOY_PATH"
    
    # Fazer backup remoto (se não for pulado)
    if [ "$SKIP_BACKUP" -eq 0 ]; then
        log "Iniciando backup remoto..."
        ssh $DEPLOY_USER@$SERVER_HOST "mkdir -p $BACKUP_DIR"
        
        # Executar script de backup remoto para acelerar processo
        cat > /tmp/remote_backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="$1"
DEPLOY_PATH="$2"
PROJECT_NAME="$3"
DEPLOY_ENV="$4"
DB_TYPE="$5"
DB_PATH="$6"
DB_CONNECTION_STRING="${7:-}"

# Backup em paralelo do código e banco
{
    # Backup do código
    if [ -d "$DEPLOY_PATH" ]; then
        echo "Backup do código remoto..."
        tar -czf "${BACKUP_DIR}/${PROJECT_NAME}_${DEPLOY_ENV}_$(date +%Y%m%d_%H%M%S)_code.tar.gz" -C $(dirname $DEPLOY_PATH) $(basename $DEPLOY_PATH)
    fi
} &

{
    # Backup do banco
    echo "Backup do banco de dados remoto..."
    case "$DB_TYPE" in
        "sqlite")
            if [ -f "$DB_PATH" ]; then
                cp "$DB_PATH" "${BACKUP_DIR}/${PROJECT_NAME}_${DEPLOY_ENV}_$(date +%Y%m%d_%H%M%S)_db.sqlite"
            fi
            ;;
        "postgresql")
            if [ -n "$DB_CONNECTION_STRING" ]; then
                export PGPASSWORD=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:([^@]*)@.*/\1/')
                pg_user=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:\/\/([^:]*):.*@.*/\1/')
                pg_host=$(echo $DB_CONNECTION_STRING | sed -E 's/.*@([^:]*):.*\/.*/\1/')
                pg_port=$(echo $DB_CONNECTION_STRING | sed -E 's/.*:([0-9]+)\/.*/\1/')
                pg_db=$(echo $DB_CONNECTION_STRING | sed -E 's/.*\/([^?]*).*/\1/')
                
                pg_dump -h $pg_host -p $pg_port -U $pg_user -d $pg_db -f "${BACKUP_DIR}/${PROJECT_NAME}_${DEPLOY_ENV}_$(date +%Y%m%d_%H%M%S)_db.sql"
            fi
            ;;
    esac
} &

wait
echo "Backup concluído!"
EOF

        # Enviar e executar script de backup remoto
        scp /tmp/remote_backup.sh $DEPLOY_USER@$SERVER_HOST:/tmp/
        ssh $DEPLOY_USER@$SERVER_HOST "chmod +x /tmp/remote_backup.sh && /tmp/remote_backup.sh '$BACKUP_DIR' '$DEPLOY_PATH' '$PROJECT_NAME' '$DEPLOY_ENV' '$DB_TYPE' '$DB_PATH' '$DB_CONNECTION_STRING'"
    else
        warning "Backup remoto ignorado conforme solicitado (--skip-backup)"
    fi
    
    # Parar o serviço
    if [ -n "$SERVICE_NAME" ]; then
        log "Parando o serviço remoto: $SERVICE_NAME"
        ssh $DEPLOY_USER@$SERVER_HOST "sudo systemctl stop $SERVICE_NAME" || warning "Falha ao parar o serviço remoto"
    fi
    
    # Deploy do código (clone do repositório)
    log "Fazendo deploy do código para $VERSION..."
    ssh $DEPLOY_USER@$SERVER_HOST "if [ -d \"$DEPLOY_PATH/.git\" ]; then cd $DEPLOY_PATH && git fetch && git checkout $VERSION; else git clone --branch $VERSION $REPO_URL $DEPLOY_PATH; fi" || error "Falha ao fazer deploy do código"
    
    # Deploy do cache de dependências para o servidor remoto
    log "Enviando cache de dependências para o servidor remoto..."
    ssh $DEPLOY_USER@$SERVER_HOST "mkdir -p ${DEPLOY_PATH}/.build_cache/pip"
    scp -r "${CACHE_DIR}/pip" $DEPLOY_USER@$SERVER_HOST:"${DEPLOY_PATH}/.build_cache/"
    
    # Criar script remoto para configurar ambiente com cache
    cat > /tmp/remote_setup.sh << 'EOF'
#!/bin/bash
DEPLOY_PATH="$1"
VENV_DIR="${DEPLOY_PATH}/venv"
REQ_FILE="${DEPLOY_PATH}/requirements.txt"
CACHE_DIR="${DEPLOY_PATH}/.build_cache"
REQ_HASH_FILE="${CACHE_DIR}/requirements_hash.txt"

# Configurar cache pip
export PIP_CACHE_DIR="${CACHE_DIR}/pip"

# Calcular hash dos requirements
mkdir -p "${CACHE_DIR}"
REQ_HASH=$(md5sum "$REQ_FILE" | awk '{print $1}')
CACHED_HASH=""

if [ -f "$REQ_HASH_FILE" ]; then
    CACHED_HASH=$(cat "$REQ_HASH_FILE")
fi

# Verificar se podemos usar cache
if [ "$REQ_HASH" == "$CACHED_HASH" ] && [ -d "$VENV_DIR" ]; then
    echo "Usando ambiente virtual em cache (requirements inalterados)"
else
    echo "Criando/atualizando ambiente virtual..."
    
    # Criar venv se não existir
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi
    
    # Instalar dependências
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip
    pip install -r "$REQ_FILE"
    
    # Salvar hash
    echo "$REQ_HASH" > "$REQ_HASH_FILE"
fi

# Aplicar migrações se existirem
source "${VENV_DIR}/bin/activate"
if [ -f "${DEPLOY_PATH}/manage.py" ]; then
    echo "Aplicando migrações de banco de dados..."
    python "${DEPLOY_PATH}/manage.py" migrate
fi

echo "Configuração do ambiente concluída!"
EOF

    # Enviar e executar script de configuração remota
    scp /tmp/remote_setup.sh $DEPLOY_USER@$SERVER_HOST:/tmp/
    ssh $DEPLOY_USER@$SERVER_HOST "chmod +x /tmp/remote_setup.sh && /tmp/remote_setup.sh '$DEPLOY_PATH'"
    
    # Criar/atualizar arquivo de serviço systemd
    if [ -n "$SERVICE_NAME" ]; then
        log "Configurando serviço systemd: $SERVICE_NAME"
        
        # Criar arquivo de serviço temporário
        cat > /tmp/${SERVICE_NAME}.service << EOF
[Unit]
Description=CrossDebate Server (${DEPLOY_ENV})
After=network.target

[Service]
User=${DEPLOY_USER}
Group=${DEPLOY_USER}
WorkingDirectory=${DEPLOY_PATH}
Environment="PATH=${DEPLOY_PATH}/venv/bin"
ExecStart=${DEPLOY_PATH}/venv/bin/python -m backend.start_server
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

        # Copiar para o servidor
        scp /tmp/${SERVICE_NAME}.service $DEPLOY_USER@$SERVER_HOST:/tmp/
        ssh $DEPLOY_USER@$SERVER_HOST "sudo mv /tmp/${SERVICE_NAME}.service /etc/systemd/system/ && sudo systemctl daemon-reload" || error "Falha ao configurar serviço systemd"
        
        # Iniciar o serviço
        log "Iniciando serviço: $SERVICE_NAME"
        ssh $DEPLOY_USER@$SERVER_HOST "sudo systemctl start $SERVICE_NAME && sudo systemctl enable $SERVICE_NAME" || error "Falha ao iniciar o serviço"
    fi
    
    # Verificar saúde do serviço
    log "Verificando saúde do serviço remoto..."
    sleep 5
    if curl -s "http://${SERVER_HOST}:${SERVER_PORT}/health" | grep -q "ok"; then
        success "Serviço remoto está saudável!"
    else
        warning "Serviço remoto pode não estar funcionando corretamente. Verifique os logs."
        read -p "Deseja fazer rollback? (s/N): " do_rollback_choice
        if [[ "$do_rollback_choice" == "s" || "$do_rollback_choice" == "S" ]]; then
            do_rollback
        fi
    fi
    
    success "Deploy concluído para $DEPLOY_ENV!"
fi

# Registro do deploy
log "Registrando informações do deploy..."
DEPLOY_LOG_FILE="deploy_history.log"
END_TIME=$(date +%s)
DEPLOY_DURATION=$((END_TIME - START_TIME))
echo "[$(date)] - Deploy da versão '$VERSION' para '$DEPLOY_ENV' por '$(whoami)' - Duração: ${DEPLOY_DURATION}s" >> $DEPLOY_LOG_FILE

success "Processo de deploy concluído com sucesso! (${DEPLOY_DURATION}s)"
timing