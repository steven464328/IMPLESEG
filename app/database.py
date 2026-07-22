"""
Configuración de la base de datos.

Por defecto usa SQLite (un solo archivo .db, cero configuración, ideal para
empezar). El día que el volumen de datos o el número de usuarios simultáneos
lo justifique, solo se cambia DATABASE_URL por una cadena de PostgreSQL y el
resto del código NO cambia (gracias a SQLModel/SQLAlchemy).
"""
import os
from sqlmodel import SQLModel, create_engine, Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'ej_sistemas.db')}"
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
