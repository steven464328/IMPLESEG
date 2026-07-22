"""
Modelos de base de datos - Sistema de Automatización EJ Soluciones
Módulo: Área de Sistemas > Hojas de Vida de Equipos

Diseño: se usan campos JSON ("checklist_software" y "extra_data") para que el
sistema pueda CRECER sin necesidad de migraciones de base de datos cada vez que
aparece un programa nuevo, un campo nuevo, o una particularidad de un cliente.
Esto es clave para que la plataforma escale a nuevas áreas y nuevos requisitos
sin romper lo ya construido.
"""
from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON


class Empresa(SQLModel, table=True):
    """Catálogo de empresas cliente (multi-tenant lógico dentro de la misma base)."""
    __tablename__ = "empresas"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
    nit: Optional[str] = None
    contacto_principal: Optional[str] = None
    correo_contacto: Optional[str] = None
    telefono_contacto: Optional[str] = None
    direccion: Optional[str] = None
    activo: bool = Field(default=True)
    creado_en: datetime = Field(default_factory=datetime.utcnow)


class Equipo(SQLModel, table=True):
    """
    Hoja de vida de un equipo de cómputo.
    Mapea 1:1 con las columnas reales de la hoja 'HOJAS DE VIDA IMPLESEG'.
    """
    __tablename__ = "equipos"

    id: int | None = Field(default=None, primary_key=True)
    empresa: str = Field(index=True)
    equipo: str = Field(index=True, unique=True)          # Ej: IMPLE001
    codigo: Optional[str] = Field(default=None, index=True)  # Ej: AIO001
    area: Optional[str] = Field(default=None, index=True)
    nombre_equipo: Optional[str] = None
    usuario_servidor: Optional[str] = None
    tipo_equipo: Optional[str] = Field(default=None, index=True)  # AIO/DESKTOP/LAPTOP/SERVIDOR

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
    antivirus_vigencia: Optional[str] = None   # Ej: "27/12/2025 BUSINESS SECURITY"
    office: Optional[str] = None
    office_licencia: Optional[str] = None
    office_serial: Optional[str] = None
    office_funciones: Optional[str] = None
    programas_instalados: Optional[str] = None

    # --- Checklist de software instalado (EXTENSIBLE sin migraciones) ---
    # Ej: {"JAVA": "INSTALADO", "ANYDESK": "INSTALADO", "3CX": "BLANCO", ...}
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
    estado_equipo: Optional[str] = Field(default=None, index=True)  # FUNCIONAL / LENTO / DONADO / CHATARRIZADO...
    fecha_ultimo_mantenimiento: Optional[str] = None
    fecha_revision_drive: Optional[str] = None
    observacion_general: Optional[str] = None
    observacion_estado: Optional[str] = None
    observaciones_finales: Optional[str] = None

    # --- Bolsa de campos futuros (cualquier columna nueva que aparezca) ---
    extra_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # --- Auditoría (trazabilidad de cambios, clave para "robustez") ---
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = None
    actualizado_por: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# MÓDULO 2: GESTIÓN HUMANA
# Asignación, recepción y baja de herramientas/equipos a colaboradores.
# Migrado 1:1 desde el Apps Script F-SGI-GH-12 (mismas columnas,
# mismos formatos de PDF, mismas firmas) para no perder continuidad
# con los registros y actas que ya existen.
# ═══════════════════════════════════════════════════════════════

class HerramientaInventario(SQLModel, table=True):
    """Inventario de herramientas/equipos de Gestión Humana (independiente
    del inventario técnico de Sistemas, aunque comparte la misma plataforma)."""
    __tablename__ = "gh_inventario"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    categoria: Optional[str] = Field(default=None, index=True)
    marca: Optional[str] = None
    modelo: Optional[str] = None
    serial: Optional[str] = Field(default=None, index=True)
    descripcion: Optional[str] = None
    cantidad_stock: int = Field(default=0)
    colaborador: Optional[str] = None  # colaborador actualmente asignado (si aplica)
    disponible: Optional[str] = None

    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)


class Asignacion(SQLModel, table=True):
    """Acta de asignación de herramientas a un colaborador (formato F-SGI-GH-12)."""
    __tablename__ = "gh_asignaciones"

    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)  # Ej: ASG-LXXXXX (se conserva el formato original)

    nombre: str
    cedula: str = Field(index=True)
    cargo: Optional[str] = None
    area: Optional[str] = Field(default=None, index=True)
    fecha: str  # se conserva como texto con formato dd/MM/yyyy HH:mm:ss, igual que el Sheet original

    items: list = Field(default_factory=list, sa_column=Column(JSON))
    firma_recibe: Optional[str] = None   # base64 (dataURL) de la firma del colaborador
    firma_entrega: Optional[str] = None  # base64 (dataURL) de la firma de la empresa

    status: str = Field(default="activo", index=True)  # activo | devuelto

    fecha_dev: Optional[str] = None
    items_dev: list = Field(default_factory=list, sa_column=Column(JSON))
    firma_recibe_dev: Optional[str] = None
    firma_entrega_dev: Optional[str] = None

    historial: list = Field(default_factory=list, sa_column=Column(JSON))
    doc_url: Optional[str] = None  # link al acta física escaneada (si se subió una)

    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)


class Baja(SQLModel, table=True):
    """Acta de baja de activos (formato F-GT-BAJA-01)."""
    __tablename__ = "gh_bajas"

    id: int | None = Field(default=None, primary_key=True)
    codigo: str = Field(index=True, unique=True)  # Ej: BAJA-LXXXXX

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

    # Especificaciones técnicas + software instalado (todo lo variable del acta)
    config: dict = Field(default_factory=dict, sa_column=Column(JSON))

    creado_en: datetime = Field(default_factory=datetime.utcnow)


class HistorialCambio(SQLModel, table=True):
    """
    Bitácora de auditoría: cada creación/edición/eliminación queda registrada.
    Esto da trazabilidad total (quién cambió qué y cuándo) - fundamental en un
    sistema que va a manejar activos de varias empresas cliente.
    """
    __tablename__ = "historial_cambios"

    id: int | None = Field(default=None, primary_key=True)
    equipo_id: int
    equipo_codigo: Optional[str] = None
    accion: str  # CREACION / MODIFICACION / ELIMINACION
    campo: Optional[str] = None
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    usuario: Optional[str] = None
    fecha: datetime = Field(default_factory=datetime.utcnow)
