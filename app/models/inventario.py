from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class HerramientaInventario(BaseModel, table=True):
    __tablename__ = "gh_inventario"

    codigo: str = Field(index=True, unique=True)

    nombre: str

    marca: Optional[str] = None

    serial: Optional[str] = None

    tipo: Optional[str] = None

    estado: str = "Disponible"

    cantidad_stock: int = 0

    colaborador: Optional[str] = None