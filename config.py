import os
from pathlib import Path

# Definições de caminhos
DB_DIR = Path("databases")
MAIN_DB = DB_DIR / "main.sqlite"
TEMPLATES_DIR = Path("templates")

# URLs Externos
OPENDOTA_API_URL = "https://api.opendota.com/api"

# Garante que os diretórios necessários existem na raiz do projeto
DB_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)