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

### 2. RUTA EXACTA: `app/main.py`
*(Doble clic en la carpeta `app`, luego clic en `main.py`. Borra todo y pega esto. Este archivo ya viene con el error de base de datos solucionado):*

```python:app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sqlite3
import pandas as pd

from app.routers import equipos, dashboard, gh_inventario, gh_asignaciones, gh_bajas, recepcion, etiquetas_usb

# --- Configuración base de datos y entorno ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "data", "ej_sistemas.db")

app = FastAPI(title="EJ Sistemas - Hojas de Vida", version="1.0.0")

# --- Rutas (API) ---
app.include_router(dashboard.router)
app.include_router(equipos.router)
app.include_router(gh_inventario.router)
app.include_router(gh_asignaciones.router)
app.include_router(gh_bajas.router)
app.include_router(recepcion.router)
app.include_router(etiquetas_usb.router)


# --- Frontend estático ---
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
def index():
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))

@app.get("/gestion-humana")
def gestion_humana():
    return FileResponse(os.path.join(BASE_DIR, "templates", "gestion_humana.html"))

@app.get("/api/dashboard/resumen")
def get_resumen():
    try:
        conn = sqlite3.connect(DB_FILE)
        
        total = pd.read_sql_query("SELECT COUNT(*) as t FROM equipos", conn).iloc[0]['t']
        riesgo = pd.read_sql_query("SELECT COUNT(*) as r FROM equipos WHERE antivirus IS NULL OR antivirus = '' OR office_licencia LIKE '%SIN LICENCIA%'", conn).iloc[0]['r']
        mantenimiento = pd.read_sql_query("SELECT COUNT(*) as m FROM equipos WHERE fecha_ultimo_mantenimiento IS NULL OR fecha_ultimo_mantenimiento = ''", conn).iloc[0]['m']
        
        df_areas = pd.read_sql_query("SELECT area as name, COUNT(*) as value FROM equipos WHERE area IS NOT NULL AND area != '' GROUP BY area ORDER BY value DESC", conn)
        df_estados = pd.read_sql_query("SELECT estado_equipo as name, COUNT(*) as value FROM equipos GROUP BY estado_equipo ORDER BY value DESC", conn)
        
        df_estados['name'] = df_estados['name'].fillna('SIN ESTADO')
        df_estados.loc[df_estados['name'] == '', 'name'] = 'SIN ESTADO'
        
        conn.close()
        
        return {
            "kpis": {
                "total": int(total),
                "riesgo": int(riesgo),
                "mantenimiento": int(mantenimiento),
                "valor_parque": 0
            },
            "graficos": {
                "areas": df_areas.to_dict('records'),
                "estados": df_estados.to_dict('records')
            }
        }
    except Exception as e:
        print(f"Error en dashboard: {e}")
        return {"error": str(e)}
```eof

### 3. RUTA EXACTA: `app/routers/etiquetas_usb.py`
*(Doble clic en la carpeta `app`, luego doble clic en `routers`, luego clic en `etiquetas_usb.py`. Borra todo y pega esto):*

```python:app/routers/etiquetas_usb.py
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pydantic import BaseModel
from sqlalchemy import func
from datetime import datetime

from app.database import get_session
from app.models import RegistroEtiqueta

router = APIRouter(prefix="/etiquetas", tags=["Control Etiquetas"])
templates = Jinja2Templates(directory="app/templates")

class IngresoEtiqueta(BaseModel):
    cedula: str
    nombre_completo: str
    equipo_descripcion: str

def get_next_consecutivo(db: Session) -> int:
    max_consecutivo = db.exec(select(func.max(RegistroEtiqueta.consecutivo))).first()
    return (max_consecutivo or 1000) + 1

@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas(request: Request):
    return templates.TemplateResponse("recepcion_etiquetas.html", {"request": request})

@router.get("/api/registros")
async def listar_registros(db: Session = Depends(get_session)):
    registros = db.exec(select(RegistroEtiqueta).order_by(RegistroEtiqueta.consecutivo.desc())).all()
    return [{
        "id": r.id, 
        "consecutivo": r.consecutivo, 
        "cedula": r.cedula, 
        "nombre": r.nombre_completo, 
        "equipo": r.equipo_descripcion, 
        "fecha": r.fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S")
    } for r in registros]

@router.post("/api/registrar")
async def registrar_y_generar(datos: IngresoEtiqueta, db: Session = Depends(get_session)):
    try:
        nuevo_consecutivo = get_next_consecutivo(db)
        
        nuevo_registro = RegistroEtiqueta(
            consecutivo=nuevo_consecutivo,
            cedula=datos.cedula,
            nombre_completo=datos.nombre_completo.upper(),
            equipo_descripcion=datos.equipo_descripcion.upper(),
            fecha_ingreso=datetime.now()
        )
        
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        fecha_str = nuevo_registro.fecha_ingreso.strftime("%Y-%m-%d")
        zpl_code = f"""^XA
^PW400
^LL200
^FO20,20^A0N,25,25^FDIMPLESEG S.A.S^FS
^FO20,50^A0N,20,20^FDControl de Ingreso^FS
^FO20,80^A0N,20,20^FDC.C: {nuevo_registro.cedula}^FS
^FO20,105^A0N,20,20^FDNom: {nuevo_registro.nombre_completo[:20]}^FS
^FO20,130^A0N,20,20^FDFecha: {fecha_str}^FS
^FO220,100^BQN,2,4^FDQA,{nuevo_registro.consecutivo}^FS
^FO220,160^A0N,25,25^FDN. {nuevo_registro.consecutivo}^FS
^XZ"""

        return {
            "status": "ok", 
            "mensaje": f"Registro guardado con consecutivo {nuevo_consecutivo}",
            "zpl": zpl_code
        }
    except Exception as e:
        print(f"Error registrando etiqueta: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor.")
```eof

### 4. RUTA EXACTA: `app/templates/recepcion_etiquetas.html`
*(Doble clic en la carpeta `app`, luego doble clic en `templates`, luego clic en `recepcion_etiquetas.html`. Borra todo y pega esto):*

```html:app/templates/recepcion_etiquetas.html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IMPLESEG - Control de Etiquetas Web</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        body {
            background-color: #0b1120;
            background-image: radial-gradient(circle at 50% 100%, #172554 0%, #0b1120 70%);
            min-height: 100vh;
            color: white;
            font-family: 'Segoe UI', system-ui, sans-serif;
            overflow-x: hidden;
        }
        .glass-panel {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        .input-field {
            width: 100%; background: #1e293b; color: white;
            border: 1px solid #334155; padding: 1rem; border-radius: 0.5rem;
            transition: all 0.3s ease;
        }
        .input-field:focus { outline: none; background: #0f172a; border-color: #38bdf8; box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2); }
        table { border-collapse: separate; border-spacing: 0; width: 100%; }
        th { background-color: #0f172a; color: #38bdf8; padding: 12px; text-align: left; border-bottom: 2px solid #334155; position: sticky; top: 0; }
        td { padding: 12px; border-bottom: 1px solid #334155; font-size: 0.875rem; }
        tbody tr:hover { background-color: #1e293b; }
    </style>
</head>
<body class="p-6 h-screen flex flex-col relative">

    <div class="w-full flex justify-between items-center mb-6 relative z-10 border-b border-gray-800 pb-4">
        <div class="flex items-center gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-sky-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-900/50">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path></svg>
            </div>
            <div>
                <h1 class="text-3xl font-black tracking-widest text-white">IMPLESEG</h1>
                <p class="text-sky-400 font-bold tracking-widest text-xs mt-1 uppercase">Control de Etiquetas USB</p>
            </div>
        </div>
        <button onclick="window.location.href='/'" class="bg-gray-800 hover:bg-gray-700 text-gray-300 px-4 py-2 rounded font-bold text-xs tracking-widest uppercase border border-gray-600 transition flex items-center gap-2">
            ← Volver al Menú Principal
        </button>
    </div>

    <div class="flex-grow flex gap-6 overflow-hidden relative z-10">
        <div class="w-1/3 glass-panel rounded-2xl p-8 border-t-4 border-t-sky-500 flex flex-col gap-4">
            <h2 class="text-xl font-bold text-sky-400 uppercase tracking-widest mb-4">Nuevo Ingreso</h2>
            <form id="form-etiqueta" onsubmit="registrarIngreso(event)" class="flex flex-col gap-4">
                <div>
                    <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Cédula *</label>
                    <input type="number" id="cedula" required placeholder="Ej. 10234567" class="input-field">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Nombre Completo *</label>
                    <input type="text" id="nombre" required placeholder="Nombre de la persona" class="input-field">
                </div>
                <div>
                    <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Equipo / Objeto *</label>
                    <input type="text" id="equipo" required placeholder="Ej. Laptop HP Plata" class="input-field">
                </div>
                <button type="submit" id="btn-registrar" class="mt-4 w-full bg-sky-600 hover:bg-sky-500 text-white font-black tracking-widest text-sm py-4 rounded-xl shadow-[0_0_20px_rgba(2,132,199,0.4)] transition-all uppercase">
                    Registrar y Generar Etiqueta
                </button>
            </form>
            
            <div id="zpl-container" class="mt-6 hidden flex-col gap-2 p-4 bg-gray-900 rounded-xl border border-gray-700">
                <p class="text-xs text-green-400 font-bold uppercase tracking-wider flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    Código ZPL Generado
                </p>
                <textarea id="zpl-code" class="w-full h-32 bg-black text-green-500 p-2 text-xs font-mono rounded border border-gray-800 focus:outline-none" readonly></textarea>
                <p class="text-xs text-gray-500 mt-2">Copia este código y envíalo a tu impresora Zebra.</p>
            </div>
        </div>

        <div class="w-2/3 glass-panel rounded-2xl p-8 flex flex-col overflow-hidden">
            <h2 class="text-xl font-bold text-gray-300 uppercase tracking-widest mb-4">Historial de Registros</h2>
            <div class="overflow-y-auto flex-grow rounded-xl border border-gray-700 bg-gray-800/50">
                <table class="w-full">
                    <thead>
                        <tr>
                            <th># Cons.</th>
                            <th>Fecha de Ingreso</th>
                            <th>Cédula</th>
                            <th>Nombre</th>
                            <th>Equipo Registrado</th>
                        </tr>
                    </thead>
                    <tbody id="tabla-registros">
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        async function cargarRegistros() {
            try {
                const res = await fetch('/etiquetas/api/registros');
                const data = await res.json();
                const tbody = document.getElementById('tabla-registros');
                tbody.innerHTML = '';
                
                data.forEach(reg => {
                    tbody.innerHTML += `
                        <tr>
                            <td class="font-black text-sky-400 text-lg">${reg.consecutivo}</td>
                            <td class="text-gray-400">${reg.fecha}</td>
                            <td class="font-medium">${reg.cedula}</td>
                            <td class="font-bold">${reg.nombre}</td>
                            <td class="text-sky-200">${reg.equipo}</td>
                        </tr>
                    `;
                });
            } catch (error) {
                console.error("Error cargando registros", error);
            }
        }

        async function registrarIngreso(e) {
            e.preventDefault();
            const btn = document.getElementById('btn-registrar');
            btn.innerHTML = "Procesando..."; btn.disabled = true;
            
            const datos = {
                cedula: document.getElementById('cedula').value.trim(),
                nombre_completo: document.getElementById('nombre').value.trim(),
                equipo_descripcion: document.getElementById('equipo').value.trim()
            };

            try {
                const res = await fetch('/etiquetas/api/registrar', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datos)
                });
                const data = await res.json();

                if (res.ok) {
                    Swal.fire({
                        title: '¡Registro Exitoso!',
                        text: data.mensaje,
                        icon: 'success',
                        background: '#1e293b', color: 'white', confirmButtonColor: '#0284c7'
                    });
                    
                    document.getElementById('zpl-container').classList.remove('hidden');
                    document.getElementById('zpl-code').value = data.zpl;
                    
                    document.getElementById('form-etiqueta').reset();
                    cargarRegistros();
                } else {
                    Swal.fire({title: 'Error', text: 'No se pudo guardar.', icon: 'error', background: '#1e293b', color: 'white'});
                }
            } catch (error) {
                console.error(error);
                Swal.fire({title: 'Error', text: 'Problema de conexión con el servidor.', icon: 'error', background: '#1e293b', color: 'white'});
            } finally {
                btn.innerHTML = "Registrar y Generar Etiqueta"; btn.disabled = false;
            }
        }

        cargarRegistros();
    </script>
</body>
</html>
```eof

### 5. RUTA EXACTA: `app/templates/index.html`
*(Doble clic en la carpeta `app`, luego doble clic en `templates`, luego clic en `index.html`. Borra todo y pega esto. Aquí va el menú con el botón añadido):*

```html:app/templates/index.html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EJ Soluciones - Hojas de Vida</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/style.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="app-shell">
        <aside class="sidebar">
            <div class="brand">
                <div class="logo">EJ</div>
                <div class="brand-text">
                    <h1>EJ Soluciones</h1>
                    <p>Soporte Tecnológico</p>
                </div>
            </div>

            <nav class="sidebar-nav">
                <h3 class="nav-header">ÁREAS</h3>
                <button class="nav-item active">
                    <span class="dot dot-live"></span> Sistemas · Hojas de Vida
                </button>
                <button class="nav-item" onclick="window.location.href='/gestion-humana'">
                    <span class="dot dot-live"></span> Gestión Humana
                </button>
                <button class="nav-item is-locked" disabled>
                    <span class="dot"></span> Contabilidad <em>próximamente</em>
                </button>
                <button class="nav-item is-locked" disabled>
                    <span class="dot"></span> Almacén <em>próximamente</em>
                </button>
                <button class="nav-item" onclick="window.location.href='/recepcion/visitantes'">
                    <span class="dot dot-live"></span> Recepción
                </button>
                
                <!-- BOTÓN NUEVO DE ETIQUETAS AQUÍ -->
                <button class="nav-item" onclick="window.location.href='/etiquetas/'">
                    <span class="dot dot-live" style="background-color: #38bdf8; box-shadow: 0 0 10px #38bdf8;"></span> Etiquetas USB
                </button>
                <!-- FIN BOTÓN NUEVO -->

                <button class="nav-item nav-add" disabled title="Cada área nueva se integra aquí sin afectar las demás">
                    + Agregar área
                </button>
                <button class="nav-item nav-add" disabled>
                    + Agregar área
                </button>
            </nav>
        </aside>

        <main class="main-content">
            <header class="top-header">
                <div class="header-titles">
                    <h2>Hojas de Vida de Equipos</h2>
                    <p>Inventario técnico, asignación y trazabilidad — Área de Sistemas</p>
                </div>
                <div class="header-actions">
                    <button class="btn btn-secondary" onclick="exportarCSV()">Exportar CSV</button>
                    <button class="btn btn-primary" onclick="abrirModalNuevo()">+ Nueva hoja de vida</button>
                </div>
            </header>

            <div class="dashboard-grid">
                <div class="kpi-card">
                    <p class="kpi-title">EQUIPOS REGISTRADOS</p>
                    <h3 class="kpi-value" id="kpi-total">0</h3>
                </div>
                <div class="kpi-card warning">
                    <p class="kpi-title">EN RIESGO / REQUIEREN ATENCIÓN</p>
                    <h3 class="kpi-value" id="kpi-riesgo">0</h3>
                </div>
                <div class="kpi-card info">
                    <p class="kpi-title">SIN MANTENIMIENTO REGISTRADO</p>
                    <h3 class="kpi-value" id="kpi-mantenimiento">0</h3>
                </div>
                <div class="kpi-card success">
                    <p class="kpi-title">VALOR ESTIMADO DEL PARQUE</p>
                    <h3 class="kpi-value">$ 0</h3>
                </div>

                <div class="chart-card chart-large">
                    <div class="chart-header">
                        <h3>Distribución por área</h3>
                    </div>
                    <div class="chart-body" id="chart-areas-container">
                    </div>
                </div>

                <div class="chart-card chart-medium">
                    <div class="chart-header">
                        <h3>Estado de los equipos</h3>
                    </div>
                    <div class="chart-body" id="chart-estados-container">
                    </div>
                </div>
            </div>

            <div class="table-container mt-6">
                <div class="table-toolbar">
                    <div class="search-box">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input type="text" id="buscadorGlobal" placeholder="Buscar por equipo, serial, usuario o IP..." onkeyup="filtrarTabla()">
                    </div>
                    <div class="filters">
                        <select id="filtroArea" onchange="filtrarTabla()">
                            <option value="">Todas las áreas</option>
                        </select>
                        <select id="filtroTipo" onchange="filtrarTabla()">
                            <option value="">Todos los tipos</option>
                        </select>
                    </div>
                </div>

                <table id="tablaEquipos">
                    <thead>
                        <tr>
                            <th>Equipo</th>
                            <th>Área</th>
                            <th>Usuario Asignado</th>
                            <th>Tipo</th>
                            <th>IP / Dominio</th>
                            <th>Estado</th>
                            <th class="text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody id="tablaBody">
                        <tr><td colspan="7" class="loading-state">Cargando inventario...</td></tr>
                    </tbody>
                </table>
            </div>
        </main>
    </div>

    <!-- Modales Formulario y Ficha Técnica -->
    <div id="modalFormulario" class="modal-overlay">
        <div class="modal-content modal-large">
            <div class="modal-header">
                <h3 id="modalTitulo">Nueva Hoja de Vida</h3>
                <button class="close-btn" onclick="cerrarModal('modalFormulario')">&times;</button>
            </div>
            <div class="modal-body">
                <form id="formEquipo" class="form-grid">
                    <input type="hidden" id="equipoId">
                    <div class="form-section">
                        <h4>1. Identificación del Equipo</h4>
                        <div class="form-row form-cols-2">
                            <div class="form-group"><label>Empresa*</label><input type="text" id="f_empresa" required></div>
                            <div class="form-group"><label>Nombre del Equipo*</label><input type="text" id="f_equipo" required></div>
                            <div class="form-group"><label>Código de Inventario</label><input type="text" id="f_codigo"></div>
                            <div class="form-group"><label>Área o Departamento</label><input type="text" id="f_area"></div>
                            <div class="form-group"><label>Usuario Servidor</label><input type="text" id="f_usuario_servidor"></div>
                            <div class="form-group">
                                <label>Tipo de Equipo</label>
                                <select id="f_tipo_equipo">
                                    <option value="">Seleccione...</option>
                                    <option value="PORTATIL">Portátil</option>
                                    <option value="ESCRITORIO">Escritorio</option>
                                    <option value="ALL IN ONE">All in One</option>
                                    <option value="SERVIDOR">Servidor</option>
                                    <option value="OTRO">Otro</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="form-section">
                        <h4>2. Especificaciones de Hardware</h4>
                        <div class="form-row form-cols-3">
                            <div class="form-group"><label>Marca</label><input type="text" id="f_marca"></div>
                            <div class="form-group"><label>Modelo</label><input type="text" id="f_modelo_equipo"></div>
                            <div class="form-group"><label>Serial</label><input type="text" id="f_serial"></div>
                            <div class="form-group"><label>CPU (Resumen)</label><input type="text" id="f_cpu"></div>
                            <div class="form-group"><label>Procesador (Detalle)</label><input type="text" id="f_procesador"></div>
                            <div class="form-group"><label>Memoria RAM</label><input type="text" id="f_memoria"></div>
                            <div class="form-group">
                                <label>Tipo de Disco</label>
                                <select id="f_tipo_disco">
                                    <option value="">Seleccione...</option>
                                    <option value="SSD">SSD</option>
                                    <option value="HDD">HDD</option>
                                    <option value="NVMe">NVMe</option>
                                </select>
                            </div>
                            <div class="form-group"><label>Tamaño Disco</label><input type="text" id="f_tamano_disco"></div>
                            <div class="form-group"><label>Mainboard</label><input type="text" id="f_mainboard"></div>
                        </div>
                    </div>
                    <div class="form-section">
                        <h4>3. Red y Conectividad</h4>
                        <div class="form-row form-cols-2">
                            <div class="form-group"><label>Dirección IP</label><input type="text" id="f_ip"></div>
                            <div class="form-group"><label>Dirección MAC</label><input type="text" id="f_mac"></div>
                            <div class="form-group"><label>ID AnyDesk</label><input type="text" id="f_anydesk_id"></div>
                            <div class="form-group"><label>Dominio</label><input type="text" id="f_dominio"></div>
                        </div>
                    </div>
                    <div class="form-section">
                        <h4>4. Asignación y Periféricos</h4>
                        <div class="form-row form-cols-2">
                            <div class="form-group" style="grid-column: 1 / -1;">
                                <label>Usuario Asignado</label><input type="text" id="f_usuario_asignado" style="font-weight: 600; color: #38bdf8;">
                            </div>
                            <div class="form-group"><label>Diadema</label><input type="text" id="f_diadema"></div>
                            <div class="form-group"><label>Teclado</label><input type="text" id="f_teclado"></div>
                            <div class="form-group"><label>Mouse</label><input type="text" id="f_mouse"></div>
                            <div class="form-group"><label>Base Refrigerante</label><input type="text" id="f_base_refrigerante"></div>
                            <div class="form-group"><label>Pantalla Auxiliar</label><input type="text" id="f_pantalla_auxiliar"></div>
                        </div>
                    </div>
                    <div class="form-section">
                        <h4>5. Software y Licenciamiento</h4>
                        <div class="form-row form-cols-2">
                            <div class="form-group"><label>Sistema Operativo</label><input type="text" id="f_sistema_operativo"></div>
                            <div class="form-group"><label>Programas</label><input type="text" id="f_programas_instalados"></div>
                            <div class="form-group"><label>Antivirus</label><input type="text" id="f_antivirus"></div>
                            <div class="form-group"><label>Vencimiento Antivirus</label><input type="text" id="f_antivirus_vigencia"></div>
                            <div class="form-group"><label>Office</label><input type="text" id="f_office"></div>
                            <div class="form-group"><label>Licencia Office</label><input type="text" id="f_office_licencia"></div>
                            <div class="form-group"><label>Serial Office</label><input type="text" id="f_office_serial"></div>
                        </div>
                    </div>
                    <div class="form-section">
                        <h4>6. Mantenimiento y Estado</h4>
                        <div class="form-row form-cols-2">
                            <div class="form-group">
                                <label>Estado del Equipo</label>
                                <select id="f_estado_equipo">
                                    <option value="">Seleccione...</option>
                                    <option value="ACTIVO">Activo / Operativo</option>
                                    <option value="MANTENIMIENTO">En Mantenimiento</option>
                                    <option value="DADO DE BAJA">Dado de Baja</option>
                                    <option value="BODEGA">En Bodega / Disponible</option>
                                </select>
                            </div>
                            <div class="form-group"><label>Último Mantenimiento</label><input type="text" id="f_fecha_ultimo_mantenimiento"></div>
                            <div class="form-group" style="grid-column: 1 / -1;">
                                <label>Observaciones Finales</label><textarea id="f_observaciones_finales" rows="3"></textarea>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="cerrarModal('modalFormulario')">Cancelar</button>
                <button class="btn btn-primary" onclick="guardarEquipo()">Guardar Equipo</button>
            </div>
        </div>
    </div>

    <!-- Script principal de la aplicación -->
    <script src="/static/app.js"></script>
</body>
</html>
```eof

---

### COMANDOS FINALES 

#### A. EN LA TERMINAL DE TU COMPUTADOR (Visual Studio Code):
Ejecuta esto uno por uno:
```bash
git add .