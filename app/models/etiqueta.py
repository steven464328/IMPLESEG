from datetime import datetime, date
from typing import Optional
from sqlmodel import Field
from sqlalchemy import BigInteger
from app.models.base import BaseModel

class RegistroEtiqueta(BaseModel, table=True):
    __tablename__ = "etiquetas"

    consecutivo: int = Field(sa_type=BigInteger, index=True, unique=True)
    cedula: str
    nombre: str
    cliente: str = Field(default="")
    impreso: bool = Field(default=False)
    fecha: datetime = Field(default_factory=datetime.utcnow)

    # Nuevos campos de trazabilidad
    nit: Optional[str] = Field(default="", index=True)
    telefono: Optional[str] = Field(default="")
    direccion: Optional[str] = Field(default="")
    ruc: Optional[str] = Field(default="")
    ph: Optional[str] = Field(default="")
    tipo_documento: Optional[str] = Field(default="")
    numero_documento: Optional[str] = Field(default="")
    tipo_extintor: Optional[str] = Field(default="")
    capacidad: Optional[str] = Field(default="")
    fecha_vence_1ano: Optional[date] = Field(default=None)
    fecha_vence_5anos: Optional[date] = Field(default=None)