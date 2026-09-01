"""
Conexión PostgreSQL de IMPLESEG ERP.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import SQLModel, Session, create_engine


# =========================================================
# CARGAR .ENV DESDE LA RAÍZ DEL PROYECTO
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)


# =========================================================
# BASE DE DATOS
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
# MOTOR POSTGRESQL
# =========================================================

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


# =========================================================
# INICIALIZACIÓN
# =========================================================

def init_db():
    SQLModel.metadata.create_all(engine)


# =========================================================
# SESIONES
# =========================================================

def get_session():
    with Session(engine) as session:
        yield session
