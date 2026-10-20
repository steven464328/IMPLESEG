import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlmodel import Session

from app.database import init_db, get_session
from app.routers import (
    dashboard, equipos, gh_inventario, gh_asignaciones,
    gh_bajas, recepcion, etiquetas_usb, dashboard_equipos,
    impresoras, hv_equipos, visitantes, usuarios
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="ERP IMPLESEG", version="3.0")

@app.on_event("startup")
def startup():
    init_db()
    # Creación segura de la tabla de usuarios sin tumbar el servidor
    try:
        db = next(get_session())
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                correo VARCHAR UNIQUE NOT NULL,
                password VARCHAR NOT NULL,
                rol VARCHAR NOT NULL,
                modulos TEXT NOT NULL,
                activo BOOLEAN DEFAULT TRUE
            );
        """))
        admin_check = db.execute(text("SELECT * FROM usuarios WHERE id = 1")).first()
        if not admin_check:
            db.execute(text("""
                INSERT INTO usuarios (correo, password, rol, modulos, activo) 
                VALUES ('admin@impleseg.com', 'impleseg2026', 'administrador', 'todos', TRUE)
            """))
        db.commit()
    except Exception as e:
        print(f"Advertencia: No se pudo verificar la tabla de usuarios en el inicio: {e}")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Incluir todos los routers
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
app.include_router(visitantes.router)
app.include_router(usuarios.router)

# ==============================================================================
# MOTOR DE SEGURIDAD (RBAC - INTERCEPTOR DE RUTAS)
# ==============================================================================
def verificar_acceso(request: Request, session: Session, modulo_requerido: str = None):
    correo = request.cookies.get("sesion_erp")
    if not correo:
        return RedirectResponse(url="/login")
    
    try:
        user = session.execute(text("SELECT * FROM usuarios WHERE correo = :c AND activo = TRUE"), {"c": correo}).mappings().first()
        if not user:
            return RedirectResponse(url="/logout")
            
        if user["rol"] == "administrador":
            return None
            
        if modulo_requerido:
            modulos = user["modulos"].split(",")
            if modulo_requerido not in modulos:
                return HTMLResponse(content=f"""
                    <div style="font-family:sans-serif; text-align:center; padding:100px 20px; background:#0f172a; color:#fff; height:100vh;">
                        <h1 style="color:#ef4444; font-size:45px;">🚫 ACCESO RESTRINGIDO</h1>
                        <p style="font-size:18px; color:#cbd5e1;">La cuenta <b>{correo}</b> no tiene privilegios para el módulo: <b>{modulo_requerido.upper()}</b>.</p>
                        <br><br>
                        <button onclick="window.history.back()" style="padding:15px 30px; background:#f97316; color:white; border:none; border-radius:8px; cursor:pointer;">← Volver atrás</button>
                    </div>
                """, status_code=403)
        return None
    except Exception:
        # Falla de conexión segura (Fallback al login)
        return RedirectResponse(url="/login")

# ==============================================================================
# LOGIN SEGURO
# ==============================================================================
@app.get("/login", response_class=HTMLResponse)
def login_page():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Acceso Corporativo · IMPLESEG ERP</title>
        <style>
            body { background: #070b14; color: #fff; font-family: system-ui, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: #121e2d; padding: 40px; border-radius: 12px; box-shadow: 0 15px 35px rgba(0,0,0,0.8); text-align: center; width: 340px; border-top: 4px solid #f97316; }
            input { width: 100%; padding: 14px; margin: 10px 0; border-radius: 6px; border: 1px solid #334155; background: #0b131e; color: white; box-sizing: border-box; outline:none; }
            input:focus { border-color: #f97316; }
            button { width: 100%; padding: 14px; background: #f97316; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; margin-top: 15px; font-size:16px;}
            button:hover { background: #ea580c; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2 style="color:#f97316; margin-top:0;">IMPLESEG ERP</h2>
            <p style="font-size:13px; color:#94a3b8; margin-bottom:20px;">Inicie sesión con su cuenta asignada</p>
            <form method="POST" action="/login">
                <input type="email" name="correo" placeholder="usuario@impleseg.com" required>
                <input type="password" name="password" placeholder="Contraseña de acceso" required>
                <button type="submit">Autenticar</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/login")
def procesar_login(correo: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    try:
        user = session.execute(text("SELECT * FROM usuarios WHERE correo = :c AND password = :p AND activo = TRUE"), {"c": correo, "p": password}).mappings().first()
        if user:
            url_destino = "/"
            if user["rol"] != "administrador":
                modulos = user["modulos"].split(",")
                if "visitantes" in modulos: url_destino = "/visitantes"
                elif "gestion_humana" in modulos: url_destino = "/gestion-humana"
                elif "hojas_vida" in modulos: url_destino = "/hojas_vida"

            response = RedirectResponse(url=url_destino, status_code=302)
            response.set_cookie(key="sesion_erp", value=correo, max_age=86400)
            response.set_cookie(key="rol_erp", value=user["rol"], max_age=86400)
            return response
    except Exception:
        pass
    return HTMLResponse("<script>alert('Credenciales incorrectas o usuario bloqueado.'); window.location.href='/login';</script>")

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("sesion_erp")
    response.delete_cookie("rol_erp")
    return response

# ==============================================================================
# PROTECCIÓN DE RUTAS DEL ERP
# ==============================================================================
@app.get("/")
def index(request: Request, session: Session = Depends(get_session)):
    fallo = verificar_acceso(request, session)
    if fallo: return fallo
    return FileResponse(os.path.join(BASE_DIR, "templates", "index.html"))

# RUTA PROFESIONAL PARA LA CONFIGURACIÓN DE SEGURIDAD
@app.get("/configuracion/seguridad")
def admin_usuarios_view(request: Request, session: Session = Depends(get_session)):
    # Solo un administrador puede acceder a esta ruta
    fallo = verificar_acceso(request, session, "ACCESO_RESTRINGIDO_SISTEMA_ROOT")
    if fallo: return fallo
    return FileResponse(os.path.join(BASE_DIR, "templates", "seguridad.html"))

# EL QUIOSCO QUEDA LIBRE PARA RECEPCIÓN, PERO EL PANEL INTERNO ESTÁ BLOQUEADO
@app.get("/visitantes")
def visitantes_view(request: Request):
    return FileResponse(os.path.join(BASE_DIR, "templates", "visitantes.html"))

@app.get("/gestion-humana")
def gestion_humana(request: Request, session: Session = Depends(get_session)):
    fallo = verificar_acceso(request, session, "gestion_humana")
    if fallo: return fallo
    return FileResponse(os.path.join(BASE_DIR, "templates", "gestion_humana.html"))

@app.get("/hojas_vida")
def hojas_vida(request: Request, session: Session = Depends(get_session)):
    fallo = verificar_acceso(request, session, "hojas_vida")
    if fallo: return fallo
    return FileResponse(os.path.join(BASE_DIR, "templates", "hojas_vida.html"))