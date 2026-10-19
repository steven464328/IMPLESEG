import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.database import init_db

from app.routers import (
    dashboard, equipos, gh_inventario, gh_asignaciones,
    gh_bajas, recepcion, etiquetas_usb, dashboard_equipos,
    impresoras, hv_equipos
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="ERP IMPLESEG", version="2.0.0")

@app.on_event("startup")
def startup():
    init_db()

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

app.include_router(dashboard.router)
app.include_router(equipos.router)
app.include_router(gh_inventario.router)
app.include_router(gh_asignaciones.router)
app.include_router(gh_bajas.router)
app.include_router(recepcion.router)
app.include_router(etiquetas_usb.router)
app.include_router(dashboard_equipos.router)
app.include_router(impresoras.router)
app.include_router(hv_equipos.router)

USUARIOS_PERMITIDOS = {
    "admin@impleseg.com": "admin123",
    "gerencia@impleseg.com": "impleseg2024",
    "sistemas@impleseg.com": "sistemas2024"
}

def verificar_sesion(request: Request):
    usuario = request.cookies.get("sesion_erp")
    return usuario in USUARIOS_PERMITIDOS

@app.get("/login", response_class=HTMLResponse)
def login_page():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Login · IMPLESEG ERP</title>
        <style>
            body { background: #0b1121; color: #fff; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); text-align: center; width: 320px; border-top: 4px solid #10b981; }
            input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #10b981; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 10px; }
            button:hover { background: #059669; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2 style="color:#10b981; margin-top:0;">IMPLESEG ERP</h2>
            <p style="font-size:13px; color:#94a3b8; margin-bottom:20px;">Acceso restringido a personal autorizado</p>
            <form method="POST" action="/login">
                <input type="email" name="correo" placeholder="Correo corporativo" required>
                <input type="password" name="password" placeholder="Contraseña" required>
                <button type="submit">Iniciar Sesión</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/login")
def procesar_login(correo: str = Form(...), password: str = Form(...)):
    if correo in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[correo] == password:
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="sesion_erp", value=correo, max_age=86400)
        return response
    return HTMLResponse(content="<script>alert('Credenciales incorrectas'); window.location.href='/login';</script>")

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("sesion_erp")
    return response

@app.get("/")
def index(request: Request):
    if not verificar_sesion(request):
        return RedirectResponse(url="/login")
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))

@app.get("/gestion-humana")
def gestion_humana(request: Request):
    if not verificar_sesion(request):
        return RedirectResponse(url="/login")
    return FileResponse(os.path.join(BASE_DIR, "templates", "gestion_humana.html"))

@app.get("/hojas_vida")
def hojas_vida(request: Request):
    if not verificar_sesion(request):
        return RedirectResponse(url="/login")
    return FileResponse(os.path.join(BASE_DIR, "templates", "hojas_vida.html"))