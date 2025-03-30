import os
import sys
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

import structlog
from loguru import logger as loguru_logger

# Definição de constantes
DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


class CorrelationIdFilter:
    """
    Filtro para adicionar um ID de correlação aos logs.
    Permite rastrear logs relacionados à mesma operação.
    """
    def __init__(self):
        self._correlation_id = {}

    def get_correlation_id(self) -> str:
        """Retorna o ID de correlação atual ou gera um novo."""
        thread_id = threading.get_ident()
        if thread_id not in self._correlation_id:
            self._correlation_id[thread_id] = str(uuid.uuid4())
        return self._correlation_id[thread_id]

    def set_correlation_id(self, correlation_id: str):
        """Define um ID de correlação para a thread atual."""
        self._correlation_id[threading.get_ident()] = correlation_id

    def clear_correlation_id(self):
        """Remove o ID de correlação da thread atual."""
        thread_id = threading.get_ident()
        if thread_id in self._correlation_id:
            del self._correlation_id[thread_id]

    def __call__(self, logger, method_name, event_dict):
        """Adiciona o ID de correlação ao contexto do log."""
        event_dict["correlation_id"] = self.get_correlation_id()
        return event_dict


class LoggingContextManager:
    """
    Gerenciador de contexto para adicionar informações temporárias ao contexto de log.
    """
    def __init__(self, **context):
        self.context = context
        self.temp_context = {}

    def __enter__(self):
        # Salva o contexto atual de cada thread
        self.temp_context = structlog.contextvars.get_contextvars()
        # Adiciona o novo contexto
        for key, value in self.context.items():
            structlog.contextvars.bind_contextvars(**{key: value})
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restaura o contexto anterior
        structlog.contextvars.clear_contextvars()
        for key, value in self.temp_context.items():
            structlog.contextvars.bind_contextvars(**{key: value})


class InterceptHandler(logging.Handler):
    """
    Handler para interceptar registros de logging padrão e redirecioná-los para loguru/structlog.
    """
    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        # Extrai informações do registro
        frame = sys._getframe(6)
        logger_context = {
            "file": os.path.basename(frame.f_code.co_filename),
            "function": frame.f_code.co_name,
            "line": frame.f_lineno,
        }
        
        # Adiciona exceção se existir
        if record.exc_info:
            logger_context["exception"] = record.exc_info
        
        # Passa para o estrutlog com contexto
        log = structlog.get_logger(record.name).bind(**logger_context)
        log.log(level, record.getMessage())


def add_app_context(logger, method_name, event_dict):
    """Adiciona informações do contexto da aplicação ao log."""
    event_dict["app_name"] = "crossdebate"
    event_dict["app_version"] = "1.0.0"  # Poderia vir de um arquivo de versão
    event_dict["environment"] = os.getenv("APP_ENV", "development")
    return event_dict


def configure_logging(
    log_level: str = DEFAULT_LOG_LEVEL,
    log_dir: str = "logs",
    json_logs: bool = True
):
    """
    Configura o sistema de logging estruturado para toda a aplicação.
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para armazenar os arquivos de log
        json_logs: Se True, os logs serão formatados em JSON
    """
    # Garantir que o diretório de logs exista
    os.makedirs(log_dir, exist_ok=True)
    
    # Importar threading aqui para evitar erro de importação circular
    global threading
    import threading
    
    # Configuração do structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        CorrelationIdFilter(),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    # Adicionar renderer baseado na configuração
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configurar nível de log
    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
    
    # Interceptar logs padrão do Python
    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=level,
        format="%(message)s",
    )
    
    # Suprimir mensagens de debug de algumas bibliotecas
    for logger_name in ["uvicorn", "uvicorn.error", "fastapi"]:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
        logging.getLogger(logger_name).propagate = False
    
    # Configurar loguru
    loguru_logger.configure(
        handlers=[
            {
                "sink": sys.stderr,
                "level": level,
                "format": "<level>{level}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
            },
            {
                "sink": os.path.join(log_dir, "app.log"),
                "level": level,
                "rotation": "10 MB",
                "retention": "1 week",
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
            },
            {
                "sink": os.path.join(log_dir, "error.log"),
                "level": "ERROR",
                "rotation": "10 MB",
                "retention": "1 month",
                "format": "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
            }
        ]
    )
    
    # Logar inicialização
    log = structlog.get_logger("logging_config")
    log.info("Structured logging configurado com sucesso", 
             log_level=log_level, 
             json_logs=json_logs)
    
    return log


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Obtém um logger estruturado com o nome especificado.
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger estruturado configurado
    """
    return structlog.get_logger(name)


def log_performance(
    logger,
    operation: str,
    duration: float,
    details: Optional[Dict[str, Any]] = None
):
    """
    Registra métricas de performance em um formato estruturado.
    
    Args:
        logger: Logger estruturado
        operation: Nome da operação sendo medida
        duration: Duração da operação em segundos
        details: Detalhes adicionais opcionais da operação
    """
    log_context = {
        "duration_seconds": duration,
        "operation": operation
    }
    
    if details:
        log_context.update(details)
    
    logger.info("Performance metric", **log_context)


def with_context(**context):
    """
    Decorator para adicionar contexto a todos os logs dentro de uma função.
    
    Args:
        **context: Pares chave-valor a serem adicionados ao contexto
    
    Returns:
        Decorator que adiciona contexto
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with LoggingContextManager(**context):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Aliases e utilitários para facilitar o uso
class Logger:
    """
    Wrapper para facilitar o uso do logger estruturado.
    """
    @staticmethod
    def get(name: str) -> structlog.stdlib.BoundLogger:
        """Obtém um logger estruturado."""
        return get_logger(name)
    
    @staticmethod
    def set_correlation_id(correlation_id: str = None):
        """Define o ID de correlação para a thread atual."""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        # Acessa o filtro CorrelationIdFilter nos processadores configurados
        for processor in structlog._config.processors:
            if isinstance(processor, CorrelationIdFilter):
                processor.set_correlation_id(correlation_id)
                break
        
        return correlation_id
    
    @staticmethod
    def clear_correlation_id():
        """Limpa o ID de correlação para a thread atual."""
        for processor in structlog._config.processors:
            if isinstance(processor, CorrelationIdFilter):
                processor.clear_correlation_id()
                break


# Importação de functools para o decorator
import functools

# Inicialização
if __name__ == "__main__":
    configure_logging()