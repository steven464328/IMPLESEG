from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON

from app.models.base import BaseModel


class Baja(BaseModel, table=True):
    __tablename__ = "gh_bajas"

    codigo: str = Field(index=True, unique=True)
    
    # Campo datetime explícito para no romper TIMESTAMP en Postgres
    fecha: datetime = Field(default_factory=datetime.now)
    
    item_id: Optional[str] = None
    nombre: str
    categoria: Optional[str] = ""
    marca: Optional[str] = ""
    modelo: Optional[str] = ""
    serial: Optional[str] = ""
    cantidad: int = 1
    motivo: str
    disposicion: str
    entidad: Optional[str] = ""
    responsable_nombre: str
    responsable_cargo: Optional[str] = ""
    area: Optional[str] = ""
    observaciones: Optional[str] = ""
    firma: Optional[str] = ""
    status: str = "registrado"

    config: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    creado_en: datetime = Field(default_factory=datetime.now)