"""
Configuración central del ERP IMPLESEG.

Toda la configuración del sistema debe obtenerse desde este archivo.
En el futuro leerá automáticamente un archivo .env.
"""

from pathlib import Path
import os

# ===========================
# RUTAS DEL PROYECTO
# ===========================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = BASE_DIR / "uploads"

# Crear carpetas si no existen
for carpeta in [DATA_DIR, LOGS_DIR, UPLOADS_DIR]:
    carpeta.mkdir(parents=True, exist_ok=True)

# ===========================
# CONFIGURACIÓN GENERAL
# ===========================

APP_NAME = "IMPLESEG ERP"
APP_VERSION = "2.0.0"

DEBUG = True

TIMEZONE = "America/Bogota"

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "CAMBIAR_ESTA_CLAVE_EN_PRODUCCION"
)

# ===========================
# BASE DE DATOS
# ===========================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'ej_sistemas.db'}"
)

# ===========================
# EMPRESA
# ===========================

DEFAULT_COMPANY = "IMPLESEG"

COUNTRY = "Colombia"

LANGUAGE = "es"

CURRENCY = "COP"