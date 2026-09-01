from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class Impresora(BaseModel, table=True):
    __tablename__ = "impresoras"

    nombre: str = Field(index=True, unique=True)

    modelo: Optional[str] = None

    tipo_conexion: str = Field(default="RED")

    nombre_windows: Optional[str] = None

    host_windows: Optional[str] = None

    ip: Optional[str] = None

    puerto: int = Field(default=9100)

    ubicacion: Optional[str] = None

    activa: bool = Field(default=True)

    predeterminada: bool = Field(default=False)
