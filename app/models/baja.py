from datetime import datetime

from sqlmodel import Field

from app.models.base import BaseModel


class Baja(BaseModel, table=True):
    __tablename__ = "gh_bajas"

    herramienta_id: int

    motivo: str

    fecha: datetime = Field(default_factory=datetime.utcnow)