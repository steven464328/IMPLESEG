from typing import Optional
from datetime import datetime, date

from sqlmodel import Field

from app.models.base import BaseModel


class Equipo(BaseModel, table=True):
    """
    Hojas de Vida de Equipos.
    """

    __tablename__ = "equipos"

    empresa_id: Optional[int] = Field(
        default=None,
        foreign_key="empresas.id",
        index=True,
    )

    # =========================
    # IDENTIFICACIÓN
    # =========================

    codigo: str = Field(index=True, unique=True)

    nombre_equipo: str = Field(index=True)

    tipo_equipo: Optional[str] = Field(default=None)

    marca: Optional[str] = Field(default=None)

    modelo: Optional[str] = Field(default=None)

    serial: Optional[str] = Field(default=None, index=True)

    activo_fijo: Optional[str] = Field(default=None)

    hostname: Optional[str] = Field(default=None, index=True)

    area: Optional[str] = Field(default=None, index=True)

    sede: Optional[str] = Field(default=None)

    estado_equipo: str = Field(default="ACTIVO")

    criticidad: Optional[str] = Field(default="MEDIA")

    # =========================
    # USUARIO
    # =========================

    usuario_asignado: Optional[str] = Field(default=None, index=True)

    cargo_usuario: Optional[str] = Field(default=None)

    correo_usuario: Optional[str] = Field(default=None)

    # =========================
    # HARDWARE
    # =========================

    procesador: Optional[str] = Field(default=None)

    generacion_procesador: Optional[str] = Field(default=None)

    memoria_ram: Optional[str] = Field(default=None)

    ram_maxima: Optional[str] = Field(default=None)

    disco_duro: Optional[str] = Field(default=None)

    tipo_disco: Optional[str] = Field(default=None)

    tarjeta_grafica: Optional[str] = Field(default=None)

    monitor: Optional[str] = Field(default=None)

    # =========================
    # SOFTWARE
    # =========================

    sistema_operativo: Optional[str] = Field(default=None)

    version_so: Optional[str] = Field(default=None)

    office: Optional[str] = Field(default=None)

    licencia_office: Optional[str] = Field(default=None)

    antivirus: Optional[str] = Field(default=None)

    licencia_antivirus: Optional[str] = Field(default=None)

    fecha_vencimiento_antivirus: Optional[date] = Field(default=None)

    # =========================
    # RED
    # =========================

    ip: Optional[str] = Field(default=None)

    mac: Optional[str] = Field(default=None)

    dominio: Optional[str] = Field(default=None)

    nombre_red: Optional[str] = Field(default=None)

    # =========================
    # COMPRA
    # =========================

    proveedor: Optional[str] = Field(default=None)

    numero_factura: Optional[str] = Field(default=None)

    fecha_compra: Optional[date] = Field(default=None)

    garantia_meses: Optional[int] = Field(default=None)

    fecha_fin_garantia: Optional[date] = Field(default=None)

    valor_compra: Optional[float] = Field(default=None)

    # =========================
    # MANTENIMIENTOS
    # =========================

    proveedor_mantenimiento: Optional[str] = Field(default=None)

    fecha_ultimo_mantenimiento: Optional[datetime] = Field(default=None)

    proximo_mantenimiento: Optional[datetime] = Field(default=None)

    frecuencia_mantenimiento: Optional[int] = Field(default=6)

    # =========================
    # BAJA
    # =========================

    fecha_baja: Optional[date] = Field(default=None)

    motivo_baja: Optional[str] = Field(default=None)

    # =========================
    # OBSERVACIONES
    # =========================

    observaciones: Optional[str] = Field(default=None)