from datetime import datetime

from sqlmodel import Field

from app.models.base import BaseModel


class RegistroEtiqueta(BaseModel, table=True):
    __tablename__ = "etiquetas"

    consecutivo: int = Field(index=True, unique=True)

    cedula: str

    nombre: str

    cliente: str = Field(default="")

    impreso: bool = Field(default=False)

    fecha: datetime = Field(default_factory=datetime.utcnow)