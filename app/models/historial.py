from datetime import datetime
from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class HistorialCambio(BaseModel, table=True):
    __tablename__ = "historial_cambios"

    equipo_id: int

    equipo_codigo: str

    accion: str

    campo: Optional[str] = None

    valor_anterior: Optional[str] = None

    valor_nuevo: Optional[str] = None

    usuario: Optional[str] = None

    fecha: datetime = Field(default_factory=datetime.utcnow)