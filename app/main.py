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