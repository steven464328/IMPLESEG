from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class Permiso(BaseModel, table=True):
    __tablename__ = "permisos"

    codigo: str = Field(index=True, unique=True)

    nombre: str

    descripcion: Optional[str] = None