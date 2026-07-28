from typing import Optional

from sqlmodel import Field

from app.models.base import BaseModel


class Usuario(BaseModel, table=True):
    __tablename__ = "usuarios"

    username: str = Field(index=True, unique=True)

    nombre: str

    email: str = Field(index=True, unique=True)

    password_hash: str

    rol_id: Optional[int] = Field(default=None, foreign_key="roles.id")

    empresa_id: Optional[int] = Field(default=None, foreign_key="empresas.id")

    activo: bool = True