from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class Rol(BaseModel, table=True):
    __tablename__ = "roles"

    nombre: str = Field(index=True, unique=True)

    descripcion: Optional[str] = None

    es_administrador: bool = False