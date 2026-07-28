from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Equipo(SQLModel, table=True):
    __tablename__ = "equipos"
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa: Optional[str] = None
    equipo: str = Field(index=True)
    codigo: Optional[str] = None
    area: Optional[str] = None
    tipo_equipo: Optional[str] = None
    cpu: Optional[str] = None
    procesador: Optional[str] = None
    memoria: Optional[str] = None
    ip: Optional[str] = None
    usuario_asignado: Optional[str] = None
    estado_equipo: Optional[str] = None
    disco_duro: Optional[str] = None
    office: Optional[str] = None
    licencia: Optional[str] = None
    serial_correo: Optional[str] = None
    antivirus: Optional[str] = None
    fecha_ultimo_mantenimiento: Optional[str] = None
    proveedor_mantenimiento: Optional[str] = None

class Visitante(SQLModel, table=True):
    __tablename__ = "recepcion_visitantes"
    id: Optional[int] = Field(default=None, primary_key=True)
    cedula: str = Field(index=True)
    nombre_completo: str
    fecha_ingreso: datetime = Field(default_factory=datetime.now)
    fecha_salida: Optional[datetime] = None
    empresa: Optional[str] = Field(default="N/A")
    arl: Optional[str] = Field(default="N/A")
    tipo_visitante: Optional[str] = Field(default="N/A")
    a_quien_visita: Optional[str] = Field(default="N/A")
    tarjeta_asignada: Optional[str] = Field(default="N/A")
    correo: Optional[str] = Field(default="N/A")
    area_visita: Optional[str] = Field(default="N/A")
    motivo_visita: Optional[str] = Field(default="N/A")
    numero_emergencia: Optional[str] = Field(default="N/A")
    persona_recibe: Optional[str] = Field(default="N/A")

class RegistroEtiqueta(SQLModel, table=True):
    """Guarda cada etiqueta impresa o asignada para llevar el consecutivo"""
    __tablename__ = "recepcion_etiquetas_historial"
    id: Optional[int] = Field(default=None, primary_key=True)
    consecutivo: int = Field(index=True, unique=True)
    cedula: str
    nombre_completo: str
    equipo_descripcion: Optional[str] = None
    fecha_ingreso: datetime = Field(default_factory=datetime.now)
    impreso: bool = Field(default=True)