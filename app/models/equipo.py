from typing import Optional
from datetime import datetime

from sqlmodel import Field

from app.models.base import BaseModel


class Equipo(BaseModel, table=True):
    """
    Hojas de Vida de Equipos.
    Modelo principal del ERP.
    """

    __tablename__ = "equipos"

    empresa_id: Optional[int] = Field(
        default=None,
        foreign_key="empresas.id",
        index=True
    )

    codigo: str = Field(index=True, unique=True)

    nombre_equipo: str = Field(index=True)

    tipo_equipo: Optional[str] = None

    marca: Optional[str] = None

    modelo: Optional[str] = None

    serial: Optional[str] = Field(default=None, index=True)

    activo_fijo: Optional[str] = None

    area: Optional[str] = Field(default=None, index=True)

    sede: Optional[str] = None

    usuario_asignado: Optional[str] = Field(default=None, index=True)

    cargo_usuario: Optional[str] = None

    correo_usuario: Optional[str] = None

    estado_equipo: str = "ACTIVO"

    sistema_operativo: Optional[str] = None

    version_so: Optional[str] = None

    office: Optional[str] = None

    licencia_office: Optional[str] = None

    antivirus: Optional[str] = None

    licencia_antivirus: Optional[str] = None

    procesador: Optional[str] = None

    memoria_ram: Optional[str] = None

    disco_duro: Optional[str] = None

    ip: Optional[str] = None

    mac: Optional[str] = None

    dominio: Optional[str] = None

    nombre_red: Optional[str] = None

    proveedor_mantenimiento: Optional[str] = None

    fecha_ultimo_mantenimiento: Optional[datetime] = None

    proximo_mantenimiento: Optional[datetime] = None

    observaciones: Optional[str] = None