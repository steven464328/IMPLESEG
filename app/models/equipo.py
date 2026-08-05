from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class Equipo(SQLModel, table=True):
    """
    Modelo principal de Hojas de Vida de Equipos.
    Compatible con la estructura actual de la tabla 'equipos'
    en la base de datos SQLite.
    """

    __tablename__ = "equipos"

    # ==========================================================
    # CLAVE PRIMARIA
    # ==========================================================

    id: Optional[int] = Field(default=None, primary_key=True)

    # ==========================================================
    # IDENTIFICACIÓN
    # ==========================================================

    empresa: str = Field(index=True)
    equipo: str = Field(index=True)
    codigo: Optional[str] = Field(default=None, index=True)

    nombre_equipo: Optional[str] = None
    tipo_equipo: Optional[str] = Field(default=None, index=True)

    area: Optional[str] = Field(default=None, index=True)

    usuario_servidor: Optional[str] = None
    usuario_asignado: Optional[str] = Field(default=None, index=True)

    estado_equipo: Optional[str] = Field(default=None, index=True)

    # ==========================================================
    # HARDWARE
    # ==========================================================

    marca: Optional[str] = None
    modelo_equipo: Optional[str] = None
    serial: Optional[str] = Field(default=None, index=True)

    cpu: Optional[str] = None
    procesador: Optional[str] = None
    memoria: Optional[str] = None
    modelo_ram: Optional[str] = None
    mainboard: Optional[str] = None

    tipo_disco: Optional[str] = None
    tamano_disco: Optional[str] = None

    pantalla_auxiliar: Optional[str] = None

    teclado: Optional[str] = None
    mouse: Optional[str] = None
    diadema: Optional[str] = None
    base_refrigerante: Optional[str] = None

    # ==========================================================
    # RED
    # ==========================================================

    ip: Optional[str] = Field(default=None, index=True)
    mac: Optional[str] = None
    dominio: Optional[str] = None
    anydesk_id: Optional[str] = None

    # ==========================================================
    # SOFTWARE
    # ==========================================================

    sistema_operativo: Optional[str] = None

    antivirus: Optional[str] = None
    antivirus_vigencia: Optional[str] = None

    office: Optional[str] = None
    office_licencia: Optional[str] = None
    office_serial: Optional[str] = None
    office_funciones: Optional[str] = None

    programas_instalados: Optional[str] = None

    checklist_software: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON),
    )

    # ==========================================================
    # COMPRA
    # ==========================================================

    compra_numero: Optional[str] = None
    compra_factura: Optional[str] = None
    compra_fecha: Optional[str] = None

    compra_productos: Optional[str] = None
    compra_cantidad: Optional[str] = None

    compra_precio_unitario: Optional[str] = None
    compra_precio_total: Optional[str] = None

    compra_seriales: Optional[str] = None
    compra_usuarios_relacionados: Optional[str] = None

    # ==========================================================
    # MANTENIMIENTO
    # ==========================================================

    fecha_ultimo_mantenimiento: Optional[str] = None
    fecha_revision_drive: Optional[str] = None

    # ==========================================================
    # OBSERVACIONES
    # ==========================================================

    observacion_general: Optional[str] = None
    observacion_estado: Optional[str] = None
    observaciones_finales: Optional[str] = None

    # ==========================================================
    # DATOS EXTRA
    # ==========================================================

    extra_data: Optional[Any] = Field(
        default=None,
        sa_column=Column(JSON),
    )

    # ==========================================================
    # AUDITORÍA
    # ==========================================================

    creado_en: datetime
    actualizado_en: datetime

    creado_por: Optional[str] = None
    actualizado_por: Optional[str] = None