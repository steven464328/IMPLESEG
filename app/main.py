from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import dashboard_equipos
from app.database import init_db

from app.routers import (
    dashboard,
    equipos,
    gh_inventario,
    gh_asignaciones,
    gh_bajas,
    recepcion,
    etiquetas_usb,
)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="ERP EJ Soluciones",
    version="2.0.0",
)

@app.on_event("startup")
def startup():
    init_db()

app.include_router(dashboard.router)
app.include_router(equipos.router)
app.include_router(gh_inventario.router)
app.include_router(gh_asignaciones.router)
app.include_router(gh_bajas.router)
app.include_router(recepcion.router)
app.include_router(etiquetas_usb.router)
app.include_router(dashboard_equipos.router)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)

@app.get("/")
def index():
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))

@app.get("/gestion-humana")
def gestion_humana():
    return FileResponse(os.path.join(BASE_DIR, "templates", "gestion_humana.html"))