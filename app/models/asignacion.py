from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON

from app.models.base import BaseModel


class Asignacion(BaseModel, table=True):
    __tablename__ = "gh_asignaciones"

    codigo: str = Field(index=True, unique=True)
    nombre: str
    cedula: str
    cargo: Optional[str] = None
    area: Optional[str] = None
    
    # Campo tipo datetime compatible con TIMESTAMP de PostgreSQL
    fecha: datetime = Field(default_factory=datetime.now)
    status: str = "activo"

    doc_url: Optional[str] = ""
    firma_recibe: Optional[str] = ""
    firma_entrega: Optional[str] = ""

    items: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    historial: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))

    fecha_dev: Optional[str] = None
    items_dev: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON))
    firma_recibe_dev: Optional[str] = ""
    firma_entrega_dev: Optional[str] = ""

    actualizado_en: datetime = Field(default_factory=datetime.now)