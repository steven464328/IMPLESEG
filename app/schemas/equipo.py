from datetime import datetime, date
from typing import Optional

from sqlmodel import SQLModel


class EquipoBase(SQLModel):

    # =====================
    # EMPRESA
    # =====================

    empresa_id: Optional[int] = None

    # =====================
    # IDENTIFICACIÓN
    # =====================

    codigo: str
    nombre_equipo: str

    tipo_equipo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = None
    activo_fijo: Optional[str] = None
    hostname: Optional[str] = None

    area: Optional[str] = None
    sede: Optional[str] = None

    estado_equipo: str = "ACTIVO"
    criticidad: Optional[str] = "MEDIA"

    # =====================
    # USUARIO
    # =====================

    usuario_asignado: Optional[str] = None
    cargo_usuario: Optional[str] = None
    correo_usuario: Optional[str] = None

    # =====================
    # HARDWARE
    # =====================

    procesador: Optional[str] = None
    generacion_procesador: Optional[str] = None

    memoria_ram: Optional[str] = None
    ram_maxima: Optional[str] = None

    disco_duro: Optional[str] = None
    tipo_disco: Optional[str] = None

    tarjeta_grafica: Optional[str] = None
    monitor: Optional[str] = None

    # =====================
    # SOFTWARE
    # =====================

    sistema_operativo: Optional[str] = None
    version_so: Optional[str] = None

    office: Optional[str] = None
    licencia_office: Optional[str] = None

    antivirus: Optional[str] = None
    licencia_antivirus: Optional[str] = None
    fecha_vencimiento_antivirus: Optional[date] = None

    # =====================
    # RED
    # =====================

    ip: Optional[str] = None
    mac: Optional[str] = None
    dominio: Optional[str] = None
    nombre_red: Optional[str] = None

    # =====================
    # COMPRA
    # =====================

    proveedor: Optional[str] = None
    numero_factura: Optional[str] = None

    fecha_compra: Optional[date] = None

    garantia_meses: Optional[int] = None

    fecha_fin_garantia: Optional[date] = None

    valor_compra: Optional[float] = None

    # =====================
    # MANTENIMIENTO
    # =====================

    proveedor_mantenimiento: Optional[str] = None

    fecha_ultimo_mantenimiento: Optional[datetime] = None

    proximo_mantenimiento: Optional[datetime] = None

    frecuencia_mantenimiento: Optional[int] = 6

    # =====================
    # BAJA
    # =====================

    fecha_baja: Optional[date] = None

    motivo_baja: Optional[str] = None

    # =====================
    # OBSERVACIONES
    # =====================

    observaciones: Optional[str] = None


class EquipoCreate(EquipoBase):
    pass


class EquipoUpdate(SQLModel):

    empresa_id: Optional[int] = None

    codigo: Optional[str] = None
    nombre_equipo: Optional[str] = None

    tipo_equipo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = None
    activo_fijo: Optional[str] = None
    hostname: Optional[str] = None

    area: Optional[str] = None
    sede: Optional[str] = None

    estado_equipo: Optional[str] = None
    criticidad: Optional[str] = None

    usuario_asignado: Optional[str] = None
    cargo_usuario: Optional[str] = None
    correo_usuario: Optional[str] = None

    procesador: Optional[str] = None
    generacion_procesador: Optional[str] = None

    memoria_ram: Optional[str] = None
    ram_maxima: Optional[str] = None

    disco_duro: Optional[str] = None
    tipo_disco: Optional[str] = None

    tarjeta_grafica: Optional[str] = None
    monitor: Optional[str] = None

    sistema_operativo: Optional[str] = None
    version_so: Optional[str] = None

    office: Optional[str] = None
    licencia_office: Optional[str] = None

    antivirus: Optional[str] = None
    licencia_antivirus: Optional[str] = None
    fecha_vencimiento_antivirus: Optional[date] = None

    ip: Optional[str] = None
    mac: Optional[str] = None
    dominio: Optional[str] = None
    nombre_red: Optional[str] = None

    proveedor: Optional[str] = None
    numero_factura: Optional[str] = None

    fecha_compra: Optional[date] = None
    garantia_meses: Optional[int] = None
    fecha_fin_garantia: Optional[date] = None
    valor_compra: Optional[float] = None

    proveedor_mantenimiento: Optional[str] = None
    fecha_ultimo_mantenimiento: Optional[datetime] = None
    proximo_mantenimiento: Optional[datetime] = None
    frecuencia_mantenimiento: Optional[int] = None

    fecha_baja: Optional[date] = None
    motivo_baja: Optional[str] = None

    observaciones: Optional[str] = None