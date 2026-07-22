"""
EJ Soluciones - Plataforma de Automatización de Procesos
Módulo 1: Área de Sistemas > Hojas de Vida de Equipos

Punto de entrada de la aplicación. Diseñado para que cada nueva área
(Contabilidad, Almacén, Recepción, etc.) se agregue como un nuevo router,
sin tocar el código ya existente.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.database import init_db
from app.routers import equipos, dashboard, gh_inventario, gh_asignaciones, gh_bajas
from app.routers import equipos, dashboard, gh_inventario, gh_asignaciones, gh_bajas, recepcion # <--- AÑADIR 'recepcion'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="EJ Soluciones - Plataforma de Automatización",
    description="Sistema modular de gestión para EJ Soluciones y sus clientes",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# --- Routers de cada módulo/área ---
app.include_router(equipos.router)
app.include_router(dashboard.router)
app.include_router(gh_inventario.router)
app.include_router(gh_asignaciones.router)
app.include_router(gh_bajas.router)
app.include_router(recepcion.router)

# --- Frontend estático ---
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))


@app.get("/gestion-humana")
def gestion_humana():
    return FileResponse(os.path.join(BASE_DIR, "templates", "gestion_humana.html"))


@app.get("/api/health")
def health():
    return {"status": "ok", "sistema": "EJ Soluciones - Plataforma de Automatización"}
