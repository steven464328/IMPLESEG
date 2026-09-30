from typing import Optional
from uuid import uuid4

from sqlmodel import Field

from app.models.base import BaseModel


class HerramientaInventario(BaseModel, table=True):
    __tablename__ = "gh_inventario"

    # Código interno generado automáticamente.
    # El usuario NO necesita diligenciarlo desde la pantalla.
    codigo: str = Field(
        default_factory=lambda: f"GH-{uuid4().hex[:10].upper()}",
        index=True,
        unique=True,
    )

    # Datos principales del inventario
    nombre: str

    categoria: Optional[str] = None

    marca: Optional[str] = None

    modelo: Optional[str] = None

    serial: Optional[str] = None

    descripcion: Optional[str] = None

    # Se conserva 'tipo' y 'estado' para mantener compatibilidad
    # con lógica existente del módulo.
    tipo: Optional[str] = None

    estado: str = "Disponible"

    cantidad_stock: int = 0

    colaborador: Optional[str] = None