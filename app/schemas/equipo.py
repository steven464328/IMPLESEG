from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class EquipoBase(SQLModel):

    empresa_id: Optional[int] = None

    codigo: str

    nombre_equipo: str

    tipo_equipo: Optional[str] = None

    marca: Optional[str] = None

    modelo: Optional[str] = None

    serial: Optional[str] = None

    activo_fijo: Optional[str] = None

    area: Optional[str] = None

    sede: Optional[str] = None

    usuario_asignado: Optional[str] = None

    cargo_usuario: Optional[str] = None

    correo_usuario: Optional[str] = None

    estado_equipo: Optional[str] = "ACTIVO"

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

    area: Optional[str] = None

    sede: Optional[str] = None

    usuario_asignado: Optional[str] = None

    cargo_usuario: Optional[str] = None

    correo_usuario: Optional[str] = None

    estado_equipo: Optional[str] = None

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