"""
Base de datos del ERP EJ Soluciones.

Compatible con:
- SQLite (desarrollo)
- PostgreSQL (producción)

No será necesario modificar el resto del proyecto al cambiar de motor.
"""

import os

from sqlmodel import SQLModel, Session, create_engine

# -----------------------------
# Directorios
# -----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

# -----------------------------
# Base de datos
# -----------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(DATA_DIR,'ej_sistemas.db')}"
)

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args
)

# -----------------------------
# Inicializar BD
# -----------------------------

def init_db():

    SQLModel.metadata.create_all(engine)

# -----------------------------
# Sesiones
# -----------------------------

def get_session():

    with Session(engine) as session:
        yield session