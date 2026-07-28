"""
Modelos de base de datos - Sistema de Automatización EJ Soluciones
"""
from datetime import datetime
from typing import Optional, Dict, Any
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
    equipo: str = Field(index=True, unique=True)
    codigo: Optional[str] = Field(default=None, index=True)
    area: Optional[str] = Field(default=None, index=True)
    nombre_equipo: Optional[str] = None
    usuario_servidor: Optional[str] = None
    tipo_equipo: Optional[str] = Field(default=None, index=True)

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

    mac: Optional[str] = None
    ip: Optional[str] = Field(default=None, index=True)
    anydesk_id: Optional[str] = None
    dominio: Optional[str] = None

    diadema: Optional[str] = None
    teclado: Optional[str] = None
    mouse: Optional[str] = None
    base_refrigerante: Optional[str] = None

    usuario_asignado: Optional[str] = Field(default=None, index=True)

    sistema_operativo: Optional[str] = None
    antivirus: Optional[str] = None
    antivirus_vigencia: Optional[str] = None
    office: Optional[str] = None
    office_licencia: Optional[str] = None
    office_serial: Optional[str] = None
    office_funciones: Optional[str] = None
    programas_instalados: Optional[str] = None

    checklist_software: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    compra_numero: Optional[str] = None
    compra_factura: Optional[str] = None
    compra_fecha: Optional[str] = None
    compra_productos: Optional[str] = None
    compra_cantidad: Optional[str] = None
    compra_precio_unitario: Optional[str] = None
    compra_precio_total: Optional[str] = None
    compra_seriales: Optional[str] = None
    compra_usuarios_relacionados: Optional[str] = None

    estado_equipo: Optional[str] = Field(default=None, index=True)
    fecha_ultimo_mantenimiento: Optional[str] = None
    fecha_revision_drive: Optional[str] = None
    observacion_general: Optional[str] = None
    observacion_estado: Optional[str] = None
    observaciones_finales: Optional[str] = None

    extra_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    creado_en: datetime = Field(default_factory=datetime.utcnow)
    actualizado_en: datetime = Field(default_factory=datetime.utcnow)
    creado_por: Optional[str] = None
    actualizado_por: Optional[str] = None


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


class Visitante(SQLModel, table=True):
    __tablename__ = "recepcion_visitantes_v2" 

    id: Optional[int] = Field(default=None, primary_key=True)
    cedula: str = Field(index=True)
    nombre_completo: str
    empresa: Optional[str] = None
    correo: Optional[str] = None
    area_visita: str
    motivo_visita: str
    arl: str
    numero_emergencia: str
    persona_recibe: str
    
    fecha_ingreso: datetime = Field(default_factory=datetime.now)
    fecha_salida: Optional[datetime] = None

class RegistroEtiqueta(SQLModel, table=True):
    __tablename__ = "recepcion_etiquetas_usb"

    id: Optional[int] = Field(default=None, primary_key=True)
    consecutivo: int = Field(index=True, unique=True)
    cedula: str = Field(index=True)
    nombre_completo: str
    equipo_descripcion: str
    fecha_ingreso: datetime = Field(default_factory=datetime.now)
    fecha_salida: Optional[datetime] = None
    impreso: bool = Field(default=False)
```eof

5. Guarda el archivo (`Ctrl + S`).

### Sube y reinicia (Los pasos de siempre)

Ahora, en la **terminal de Visual Studio Code**, sube esta corrección:

```bash
git add .
git commit -m "Corregido error de sintaxis en models.py"
git push origin main