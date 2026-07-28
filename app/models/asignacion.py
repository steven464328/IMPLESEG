from datetime import datetime
from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class Asignacion(BaseModel, table=True):
    __tablename__ = "gh_asignaciones"

    codigo: str = Field(index=True, unique=True)

    nombre: str

    cedula: str

    cargo: Optional[str] = None

    area: Optional[str] = None

    fecha: datetime = Field(default_factory=datetime.utcnow)

    status: str = "activo"