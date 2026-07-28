from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class BaseModel(SQLModel):
    """
    Modelo base para todas las tablas del ERP.
    Todos los modelos heredarán estos campos.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    fecha_creacion: datetime = Field(default_factory=datetime.utcnow)

    fecha_actualizacion: datetime = Field(default_factory=datetime.utcnow)

    activo: bool = Field(default=True)

    creado_por: Optional[str] = None

    actualizado_por: Optional[str] = None