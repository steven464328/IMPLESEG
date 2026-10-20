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

app = FastAPI(title="ERP IMPLESEG SEGURO", version="3.0")

@app.on_event("startup")
def startup():
    init_db()

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
    
    # Bypass Maestro: Si eres tú, entras a todo sin preguntar
    if correo == "sistemas@impleseg.com":
        return None

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
        return RedirectResponse(url="/login")

# ==============================================================================
# LOGIN SEGURO CON BYPASS MAESTRO INFALIBLE
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
    if not correo.endswith("@impleseg.com"):
        return HTMLResponse("<script>alert('ALERTA: Solo se admiten correos corporativos autorizados (@impleseg.com)'); window.location.href='/login';</script>")
    
    # 1. MODO DIOS: INGRESO ABSOLUTO GARANTIZADO (Evita cualquier bloqueo de PostgreSQL)
    if correo == "sistemas@impleseg.com" and password == "Ejs0luciones$":
        try:
            # Intentamos inyectarlo en la base de datos para que quede registrado
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    correo VARCHAR UNIQUE NOT NULL,
                    password VARCHAR NOT NULL,
                    rol VARCHAR NOT NULL,
                    modulos TEXT NOT NULL,
                    activo BOOLEAN DEFAULT TRUE
                );
            """))
            session.commit()
            
            admin_exist = session.execute(text("SELECT * FROM usuarios WHERE correo = :c"), {"c": correo}).first()
            if not admin_exist:
                session.execute(text("""
                    INSERT INTO usuarios (correo, password, rol, modulos, activo) 
                    VALUES (:c, :p, 'administrador', 'todos', TRUE)
                """), {"c": correo, "p": password})
                session.commit()
        except Exception as e:
            # SI LA BASE DE DATOS FALLA, IGNORAMOS EL ERROR (Rollback limpia el bloqueo)
            session.rollback()
            print("Error forzando DB (Ignorado por Bypass Maestro):", e)
        
        # SIN IMPORTAR SI LA BD FALLÓ, TE DEJA ENTRAR
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(key="sesion_erp", value=correo, max_age=86400)
        response.set_cookie(key="rol_erp", value="administrador", max_age=86400)
        return response

    # 2. PROCESO NORMAL PARA LOS DEMÁS USUARIOS
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
    except Exception as e:
        session.rollback()
        print("Error durante autenticación:", e)
        
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

@app.get("/configuracion/seguridad")
def admin_usuarios_view(request: Request, session: Session = Depends(get_session)):
    fallo = verificar_acceso(request, session, "ACCESO_RESTRINGIDO_SISTEMA_ROOT")
    if fallo: return fallo
    return FileResponse(os.path.join(BASE_DIR, "templates", "seguridad.html"))

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