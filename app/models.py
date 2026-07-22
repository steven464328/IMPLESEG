"""
Modelos de base de datos - Sistema de Automatización EJ Soluciones
Módulo: Área de Sistemas > Hojas de Vida de Equipos
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Column, JSON


class Empresa(SQLModel, table=True):
    __tablename__ = "empresas"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
    nit: Optional[str] = None
    contacto_principal: Optional[str] = None
    correo_contacto: Optional[str] = None
    telefono_contacto: Optional[str] = None
    direccion: Optional[str] = None
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class Equipo(SQLModel, table=True):
    __tablename__ = "equipos"

    id: Optional[int] = Field(default=None, primary_key=True)
    empresa: str = Field(index=True)
    equipo: str = Field(index=True, unique=True)          # Ej: IMPLE001
    codigo: Optional[str] = Field(default=None, index=True)  # Ej: AIO001
    area: Optional[str] = Field(default=None, index=True)
    nombre_equipo: Optional[str] = None
    usuario_servidor: Optional[str] = None
    tipo_equipo: Optional[str] = Field(default=None, index=True)

    # --- Hardware ---
    cpu: Optional[str] = None
    procesador: Optional[str] = None
    memoria: Optional[str] = None
    modelo_ram: Optional[str] = None
    mainboard: Optional[str] = None
    tipo_disco: Optional[str] = None
    tamano_disco: Optional[str] = None
    marca: Optional[str] = None
    modelo_equipo: Optional[str] = None
    serial: Optional[str] = None
    pantalla_auxiliar: Optional[str] = None

    # --- Red / acceso remoto ---
    mac: Optional[str] = None
    ip: Optional[str] = Field(default=None, index=True)
    anydesk_id: Optional[str] = None
    dominio: Optional[str] = None

    # --- Periféricos ---
    diadema: Optional[str] = None
    teclado: Optional[str] = None
    mouse: Optional[str] = None
    base_refrigerante: Optional[str] = None

    # --- Asignación ---
    usuario_asignado: Optional[str] = Field(default=None, index=True)

    # --- Software base ---
    sistema_operativo: Optional[str] = None
    antivirus: Optional[str] = None
    antivirus_vigencia: Optional[str] = None
    office: Optional[str] = None
    office_licencia: Optional[str] = None
    office_serial: Optional[str] = None
    office_funciones: Optional[str] = None
    programas_instalados: Optional[str] = None

    # --- Checklist de software instalado ---
    checklist_software: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # --- Compra / activo fijo ---
    compra_numero: Optional[str] = None
    compra_factura: Optional[str] = None
    compra_fecha: Optional[str] = None
    compra_productos: Optional[str] = None
    compra_cantidad: Optional[str] = None
    compra_precio_unitario: Optional[str] = None
    compra_precio_total: Optional[str] = None
    compra_seriales: Optional[str] = None
    compra_usuarios_relacionados: Optional[str] = None

    # --- Estado y mantenimiento ---
    estado_equipo: Optional[str] = Field(default=None, index=True)
    fecha_ultimo_mantenimiento: Optional[str] = None
    fecha_revision_drive: Optional[str] = None
    observacion_general: Optional[str] = None
    observacion_estado: Optional[str] = None
    observaciones_finales: Optional[str] = None

    # --- Bolsa de campos futuros ---
    extra_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # --- Auditoría ---
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = None
    actualizado_por: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# MÓDULO 2: GESTIÓN HUMANA
# ═══════════════════════════════════════════════════════════════

class HerramientaInventario(SQLModel, table=True):
    __tablename__ = "gh_inventario"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    categoria: Optional[str] = Field(default=None, index=True)
    marca: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = Field(default=None, index=True)
    descripcion: Optional[str] = None
    cantidad_stock: int = Field(default=0)
    colaborador: Optional[str] = None
    disponible: Optional[str] = None

    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)


class Asignacion(SQLModel, table=True):
    __tablename__ = "gh_asignaciones"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)

    nombre: str
    cedula: str = Field(index=True)
    cargo: Optional[str] = None
    area: Optional[str] = Field(default=None, index=True)
    fecha: str

    items: list = Field(default_factory=list, sa_column=Column(JSON))
    firma_recibe: Optional[str] = None
    firma_entrega: Optional[str] = None

    status: str = Field(default="activo", index=True)

    fecha_dev: Optional[str] = None
    items_dev: list = Field(default_factory=list, sa_column=Column(JSON))
    firma_recibe_dev: Optional[str] = None
    firma_entrega_dev: Optional[str] = None

    historial: list = Field(default_factory=list, sa_column=Column(JSON))
    doc_url: Optional[str] = None

    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)


class Baja(SQLModel, table=True):
    __tablename__ = "gh_bajas"

    id: Optional[int] = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)

    fecha: str
    item_id: Optional[str] = None
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = None
    cantidad: int = Field(default=1)

    motivo: Optional[str] = None
    disposicion: Optional[str] = None
    entidad: Optional[str] = None

    responsable_nombre: Optional[str] = None
    responsable_cargo: Optional[str] = None
    area: Optional[str] = None
    observaciones: Optional[str] = None
    firma: Optional[str] = None
    status: str = Field(default="registrado")

    config: dict = Field(default_factory=dict, sa_column=Column(JSON))
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class HistorialCambio(SQLModel, table=True):
    __tablename__ = "historial_cambios"

    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: int
    equipo_codigo: Optional[str] = None
    accion: str
    campo: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    usuario: Optional[str] = None
    fecha: datetime = Field(default_factory=datetime.utcnow)


# ... existing code ...
class HistorialCambio(SQLModel, table=True):
    __tablename__ = "historial_cambios"

    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: int
    equipo_codigo: Optional[str] = None
    accion: str
    campo: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    usuario: Optional[str] = None
    fecha: datetime = Field(default_factory=datetime.utcnow)

# ═══════════════════════════════════════════════════════════════
# MÓDULO 3: RECEPCIÓN
# Control de acceso de visitantes (Ingreso y Salida)
# ═══════════════════════════════════════════════════════════════

class Visitante(SQLModel, table=True):
    """Registro de entradas y salidas de visitantes."""
    __tablename__ = "recepcion_visitantes"

    id: Optional[int] = Field(default=None, primary_key=True)
    cedula: str = Field(index=True)
    nombre_completo: str
    empresa: Optional[str] = None
    tipo_visitante: str  # PROVEEDOR, VISITANTE, CONTRATISTA, CLIENTE
    a_quien_visita: str
    arl: str  # SI / NO
    tarjeta_asignada: Optional[str] = None
    
    fecha_ingreso: datetime = Field(default_factory=datetime.now)
    fecha_salida: Optional[datetime] = None  # Se llena cuando marcan salida