from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Cookie
from sqlalchemy import text
from sqlmodel import Session
from app.database import get_session
import pandas as pd
import io
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter(prefix="/api/cartera", tags=["Cartera SIESA"])

# Configuración SMTP Corporativa
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "sistemas@impleseg.com"
SMTP_PASS = "TU_CLAVE_DE_APLICACION_AQUI" 

def validar_admin(sesion_erp: Optional[str] = Cookie(None), rol_erp: Optional[str] = Cookie(None)):
    if not sesion_erp or rol_erp != "administrador":
        raise HTTPException(status_code=403, detail="Privilegios de Administrador requeridos.")
    return sesion_erp

def obtener_usuario_actual(sesion_erp: Optional[str] = Cookie(None)):
    if not sesion_erp:
        raise HTTPException(status_code=401, detail="No autenticado")
    return sesion_erp

@router.get("/init")
def inicializar_tablas(session: Session = Depends(get_session)):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS cartera_vendedores (
            id SERIAL PRIMARY KEY,
            vendedor VARCHAR UNIQUE NOT NULL,
            correo VARCHAR NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cartera_registros (
            id SERIAL PRIMARY KEY,
            cliente VARCHAR,
            nit VARCHAR,
            factura VARCHAR,
            fecha_vencimiento DATE,
            valor NUMERIC,
            vendedor VARCHAR
        );
    """))
    session.commit()
    return {"status": "ok"}

# ==========================================
# ADMINISTRACIÓN DE CORREOS (MAESTRO)
# ==========================================
@router.get("/vendedores")
def listar_vendedores(session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    query = text("SELECT * FROM cartera_vendedores ORDER BY vendedor")
    return [dict(r) for r in session.execute(query).mappings().all()]

@router.post("/vendedores")
def guardar_vendedor(payload: dict, session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    try:
        query = text("""
            INSERT INTO cartera_vendedores (vendedor, correo) 
            VALUES (:v, :c) ON CONFLICT (vendedor) DO UPDATE SET correo = :c
        """)
        session.execute(query, {"v": payload["vendedor"], "c": payload["correo"]})
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# PROCESAMIENTO DEL EXCEL DE SIESA
# ==========================================
@router.post("/upload")
async def subir_excel_siesa(file: UploadFile = File(...), session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        session.execute(text("TRUNCATE TABLE cartera_registros;"))
        hoy = datetime.datetime.now()
        insertados = 0
        
        for index, row in df.iterrows():
            fecha_vcto = pd.to_datetime(row.get('Fecha vcto.'), errors='coerce')
            if pd.isna(fecha_vcto) or fecha_vcto >= hoy:
                continue 
                
            valor = str(row.get('Total COP', '0')).replace(',', '').strip()
            try: valor_num = float(valor)
            except: valor_num = 0.0

            query = text("""
                INSERT INTO cartera_registros (cliente, nit, factura, fecha_vencimiento, valor, vendedor)
                VALUES (:cliente, :nit, :factura, :fecha_vencimiento, :valor, :vendedor)
            """)
            session.execute(query, {
                "cliente": str(row.get('Razón social sucursal', 'SIN NOMBRE')),
                "nit": str(row.get('Cliente', '0')),
                "factura": str(row.get('Nro. docto. cruce', 'N/A')),
                "fecha_vencimiento": fecha_vcto.strftime('%Y-%m-%d'),
                "valor": valor_num,
                "vendedor": str(row.get('Razón social vend. cliente', 'SIN VENDEDOR')).strip()
            })
            insertados += 1
            
        session.commit()
        return {"status": "ok", "registros_vencidos": insertados}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error procesando Excel: {str(e)}")

# ==========================================
# NOTIFICACIONES AUTOMATIZADAS
# ==========================================
@router.post("/notificar")
def enviar_notificaciones(session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    try:
        vendedores = session.execute(text("SELECT DISTINCT vendedor FROM cartera_registros")).fetchall()
        correos_maestro = {r.vendedor: r.correo for r in session.execute(text("SELECT vendedor, correo FROM cartera_vendedores")).fetchall()}
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        enviados = 0
        for v in vendedores:
            nombre_vendedor = v[0]
            correo_destino = correos_maestro.get(nombre_vendedor)
            if not correo_destino: continue
                
            facturas = session.execute(text("SELECT * FROM cartera_registros WHERE vendedor = :v"), {"v": nombre_vendedor}).mappings().all()
            
            filas_html = ""
            total_vencido = 0
            for f in facturas:
                filas_html += f"<tr><td>{f['cliente']}</td><td>{f['factura']}</td><td>{f['fecha_vencimiento']}</td><td>${f['valor']:,.2f}</td></tr>"
                total_vencido += float(f['valor'])
                
            html_correo = f"""
            <html><body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color:#f97316;">IMPLESEG - Reporte de Cartera Vencida</h2>
                <p>Estimado/a <b>{nombre_vendedor}</b>,</p>
                <p>A continuación se detalla su cartera de clientes con facturas vencidas. Saldo total en mora: <b>${total_vencido:,.2f}</b>.</p>
                <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse; width:100%; font-size:14px;">
                    <tr style="background-color:#1e293b; color:white;"><th>Cliente</th><th>Factura</th><th>Vencimiento</th><th>Valor (COP)</th></tr>
                    {filas_html}
                </table>
                <p style="margin-top:20px; font-size:12px; color:#666;">Este es un mensaje automático del ERP IMPLESEG. Por favor no responder a este correo.</p>
            </body></html>
            """
            
            msg = MIMEMultipart()
            msg['From'] = SMTP_USER
            msg['To'] = correo_destino
            msg['Subject'] = f"Alerta de Cartera Vencida - IMPLESEG"
            msg.attach(MIMEText(html_correo, 'html'))
            server.send_message(msg)
            enviados += 1
            
        server.quit()
        return {"status": "ok", "correos_enviados": enviados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# VISTA RESTRINGIDA PARA VENDEDORES
# ==========================================
@router.get("/mis-datos")
def obtener_mi_cartera(session: Session = Depends(get_session), usuario: str = Depends(obtener_usuario_actual)):
    vendedor_mapeado = session.execute(text("SELECT vendedor FROM cartera_vendedores WHERE correo = :c"), {"c": usuario}).first()
    if not vendedor_mapeado:
        return []
    
    query = text("SELECT * FROM cartera_registros WHERE vendedor = :v ORDER BY fecha_vencimiento ASC")
    return [dict(r) for r in session.execute(query, {"v": vendedor_mapeado[0]}).mappings().all()]