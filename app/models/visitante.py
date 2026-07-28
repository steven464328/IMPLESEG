from datetime import datetime
from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class Visitante(BaseModel, table=True):
    __tablename__ = "visitantes"

    cedula: str

    nombre: str

    empresa: Optional[str] = None

    ingreso: datetime = Field(default_factory=datetime.utcnow)

    salida: Optional[datetime] = None