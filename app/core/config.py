"""
Configuración central de IMPLESEG ERP.
"""

from pathlib import Path
import os

from dotenv import load_dotenv


# =========================================================
# RUTAS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent.parent

APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"
UPLOADS_DIR = BASE_DIR / "uploads"

for carpeta in [DATA_DIR, LOGS_DIR, UPLOADS_DIR]:
    carpeta.mkdir(parents=True, exist_ok=True)


# =========================================================
# .ENV
# =========================================================

ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# =========================================================
# APLICACIÓN
# =========================================================

APP_NAME = "IMPLESEG ERP"
APP_VERSION = "2.0.0"

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

TIMEZONE = "America/Bogota"

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        f"SECRET_KEY no está configurada. "
        f"Archivo esperado: {ENV_FILE}"
    )


# =========================================================
# POSTGRESQL
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL no está configurada. "
        f"Archivo esperado: {ENV_FILE}"
    )

if not DATABASE_URL.startswith(
    ("postgresql://", "postgresql+psycopg://")
):
    raise RuntimeError(
        "DATABASE_URL debe utilizar PostgreSQL."
    )


# =========================================================
# EMPRESA
# =========================================================

DEFAULT_COMPANY = "IMPLESEG"

COUNTRY = "Colombia"

LANGUAGE = "es"

CURRENCY = "COP"
