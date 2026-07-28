from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class Empresa(BaseModel, table=True):
    __tablename__ = "empresas"

    nombre: str = Field(index=True, unique=True)

    nit: Optional[str] = None

    direccion: Optional[str] = None

    telefono: Optional[str] = None

    correo: Optional[str] = None

    ciudad: Optional[str] = None

    pais: str = "Colombia"