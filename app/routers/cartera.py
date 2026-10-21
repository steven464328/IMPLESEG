import os
import io
import pandas as pd
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, Response
from sqlmodel import Session
from app.database import get_session

router = APIRouter(prefix="/api/cartera", tags=["Cartera"])

# Configuración SMTP para Envío Corporativo
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sistemas@impleseg.com"
APP_PASSWORD = "uovb dzqb ewkl lvgj"

# Estado Global en Memoria para Consulta Inmediata sin Bloqueos de DB
DB_CARTERA_GLOBAL = []
MAPEO_VENDEDORES = {}
BITACORA_ENVIOS = []

@router.get("/init")
def init_cartera():
    return {"status": "ok", "total_registros": len(DB_CARTERA_GLOBAL)}

@router.get("/vendedores")
def obtener_mapeo_vendedores():
    resultado = [{"vendedor": k, "correo": v} for k, v in MAPEO_VENDEDORES.items()]
    return resultado

@router.post("/vendedores")
def guardar_mapeo_vendedor(payload: dict):
    vendedor = payload.get("vendedor", "").strip().upper()
    correo = payload.get("correo", "").strip().lower()
    if vendedor and correo:
        MAPEO_VENDEDORES[vendedor] = correo
        return {"status": "success", "vendedor": vendedor, "correo": correo}
    raise HTTPException(status_code=400, detail="Datos de vendedor o correo inválidos")

@router.post("/upload")
async def cargar_excel_siesa(file: UploadFile = File(...)):
    global DB_CARTERA_GLOBAL
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Formato no soportado. Debe ser un archivo Excel (.xlsx, .xls)")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Limpieza de nombres de columnas (Quitar espacios extra)
        df.columns = [str(c).strip() for c in df.columns]
        
        registros_procesados = []
        fecha_actual = datetime.now()

        for idx, row in df.iterrows():
            # Mapeo flexible de columnas SIESA
            cliente = str(row.get('Tercero / Razón Social', row.get('Razon Social', row.get('Cliente', row.get('TERCERO', 'CLIENTE VARIOS'))))).strip()
            nit = str(row.get('Nit / Cédula', row.get('Nit', row.get('NIT', row.get('Documento', 'N/A'))))).strip()
            factura = str(row.get('Docto. / Factura', row.get('Factura', row.get('DOCTO', row.get('Documento', f'FACT-{idx+1}'))))).strip()
            vendedor = str(row.get('Vendedor', row.get('VENDEDOR', row.get('Nombre Vendedor', 'SIN VENDEDOR')))).strip().upper()
            
            # Procesamiento de Fechas y Días de Mora
            fecha_venc_raw = row.get('Fecha Vencimiento', row.get('Vencimiento', row.get('FECHA_VENC', 'N/A')))
            dias_mora = 0
            fecha_venc_str = str(fecha_venc_raw).split('T')[0] if 'T' in str(fecha_venc_raw) else str(fecha_venc_raw)

            try:
                if isinstance(fecha_venc_raw, datetime):
                    dias_mora = (fecha_actual - fecha_venc_raw).days
                else:
                    dt = pd.to_datetime(fecha_venc_raw, errors='coerce')
                    if not pd.isna(dt):
                        dias_mora = (fecha_actual - dt).days
                        fecha_venc_str = dt.strftime('%Y-%m-%d')
            except Exception:
                dias_mora = 0

            # Procesamiento de Valores
            val_raw = row.get('Saldo Net. COP', row.get('Valor', row.get('Saldo', row.get('VALOR', 0))))
            try:
                if isinstance(val_raw, str):
                    val_clean = float(''.join(c for c in val_raw if c.isdigit() or c in ['.', '-']))
                else:
                    val_clean = float(val_raw)
            except Exception:
                val_clean = 0.0

            if val_clean > 0:
                registros_procesados.append({
                    "id": idx + 1,
                    "cliente": cliente,
                    "nit": nit,
                    "factura": factura,
                    "vendedor": vendedor,
                    "fecha_vencimiento": fecha_venc_str,
                    "dias_mora": max(0, dias_mora),
                    "valor": val_clean
                })

        DB_CARTERA_GLOBAL = registros_procesados
        return {
            "status": "success",
            "total_facturas": len(DB_CARTERA_GLOBAL),
            "saldo_total": sum(r["valor"] for r in DB_CARTERA_GLOBAL),
            "registros": DB_CARTERA_GLOBAL
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parseando archivo Excel SIESA: {str(e)}")

@router.get("/dashboard-metrics")
def obtener_metricas_dashboard():
    total_cartera = sum(r["valor"] for r in DB_CARTERA_GLOBAL)
    vencidos = [r for r in DB_CARTERA_GLOBAL if r["dias_mora"] > 0]
    total_vencido = sum(r["valor"] for r in vencidos)
    porcentaje_morosidad = (total_vencido / total_cartera * 100) if total_cartera > 0 else 0.0

    # Clasificación por edades de mora
    mora_0_30 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if 0 <= r["dias_mora"] <= 30)
    mora_31_60 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if 31 <= r["dias_mora"] <= 60)
    mora_61_90 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if 61 <= r["dias_mora"] <= 90)
    mora_mayor_90 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if r["dias_mora"] > 90)

    # Agrupación por Vendedores
    vendedores_dict = {}
    for r in DB_CARTERA_GLOBAL:
        v = r["vendedor"]
        vendedores_dict[v] = vendedores_dict.get(v, 0.0) + r["valor"]

    top_vendedores = sorted([{"vendedor": k, "total": v} for k, v in vendedores_dict.items()], key=lambda x: x["total"], reverse=True)

    return {
        "kpis": {
            "total_cartera": total_cartera,
            "total_vencido": total_vencido,
            "porcentaje_morosidad": round(porcentaje_morosidad, 2),
            "cantidad_facturas": len(DB_CARTERA_GLOBAL)
        },
        "edades_mora": {
            "mora_0_30": mora_0_30,
            "mora_31_60": mora_31_60,
            "mora_61_90": mora_61_90,
            "mora_mayor_90": mora_mayor_90
        },
        "top_vendedores": top_vendedores
    }

@router.get("/mis-datos")
def obtener_mis_datos(request: Request):
    # Retorna la lista global completa si es administración o si no se ha filtrado
    return DB_CARTERA_GLOBAL

@router.post("/notificar")
def ejecutar_envio_masivo():
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not DB_CARTERA_GLOBAL:
        raise HTTPException(status_code=400, detail="No hay cartera cargada para notificar")

    # Agrupar cartera por vendedor
    vendedores_cartera = {}
    for r in DB_CARTERA_GLOBAL:
        v = r["vendedor"]
        if v not in vendedores_cartera:
            vendedores_cartera[v] = []
        vendedores_cartera[v].append(r)

    correos_despachados = 0

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)

        for vendedor, facturas in vendedores_cartera.items():
            correo_destino = MAPEO_VENDEDORES.get(vendedor, SENDER_EMAIL)
            total_vendedor = sum(f["valor"] for f in facturas)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🚨 Reporte de Cartera Vencida - Vendedor: {vendedor}"
            msg["From"] = f"IMPLESEG ERP <{SENDER_EMAIL}>"
            msg["To"] = correo_destino

            filas_html = "".join([f"<tr><td>{f['cliente']}</td><td>{f['nit']}</td><td>{f['factura']}</td><td>{f['fecha_vencimiento']}</td><td>{f['dias_mora']} días</td><td>${f['valor']:,.2f}</td></tr>" for f in facturas])
            
            # Píxel de seguimiento de lectura
            pixel_id = f"{vendedor}_{int(datetime.now().timestamp())}"
            pixel_url = f"http://192.168.1.76:8000/api/cartera/tracking/pixel.png?id={pixel_id}"

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #0b1121; color: #ffffff; padding: 20px;">
                <h2 style="color: #f97316;">IMPLESEG ERP - Alerta de Cartera Vencida</h2>
                <p>Estimado(a) <b>{vendedor}</b>,</p>
                <p>A continuación se detalla la cartera en estado de mora bajo su gestión. Total vencido: <b style="color:#ef4444;">${total_vendedor:,.2f} COP</b>.</p>
                <table border="1" cellpadding="8" cellspacing="0" style="width:100%; border-color:#334155; border-collapse:collapse; color:#fff;">
                    <tr style="background-color:#1e293b; color:#10b981;">
                        <th>Cliente</th><th>NIT</th><th>Factura</th><th>Vencimiento</th><th>Días Mora</th><th>Valor</th>
                    </tr>
                    {filas_html}
                </table>
                <br>
                <img src="{pixel_url}" width="1" height="1" alt="" style="display:none;" />
                <p style="font-size:11px; color:#94a3b8;">Notificación generada automáticamente por IMPLESEG ERP.</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(html_body, "html"))
            server.sendmail(SENDER_EMAIL, correo_destino, msg.as_string())
            
            correos_despachados += 1
            BITACORA_ENVIOS.append({
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "vendedor": vendedor,
                "correo": correo_destino,
                "estado": "Entregado",
                "confirmacion": "Pendiente"
            })

        server.quit()
        return {"status": "success", "correos_enviados": correos_despachados}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error despachando correos SMTP: {str(e)}")

@router.get("/tracking/pixel.png")
def tracking_pixel(id: str):
    # Confirmación de lectura corporativa recibida
    for envio in BITACORA_ENVIOS:
        if envio["vendedor"] in id:
            envio["confirmacion"] = "Leído ✅"
    
    # Imagen transparente de 1x1 píxel en formato PNG
    pixel_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=pixel_bytes, media_type="image/png")

@router.get("/bitacora")
def obtener_bitacora():
    return BITACORA_ENVIOS