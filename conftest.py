import sys
import os
from pathlib import Path

# Add the project root directory to Python's module search path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Adiciona também os subdiretórios principais ao path
for subdir in ["backend", "models"]:
    subdir_path = project_root / subdir
    if subdir_path.exists():
        sys.path.insert(0, str(subdir_path))

# Configuração de variáveis de ambiente para desenvolvimento
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("LOG_LEVEL", "DEBUG")