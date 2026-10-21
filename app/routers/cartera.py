import os
import io
import pandas as pd
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, Response

router = APIRouter(prefix="/api/cartera", tags=["Cartera"])

# Configuración SMTP para Envío Corporativo
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "sistemas@impleseg.com"
APP_PASSWORD = "uovb dzqb ewkl lvgj"

# Estado Global en Memoria
DB_CARTERA_GLOBAL = []
MAPEO_VENDEDORES = {}
BITACORA_ENVIOS = []

@router.get("/init")
def init_cartera():
    return {"status": "ok", "total_registros": len(DB_CARTERA_GLOBAL)}

@router.get("/vendedores")
def obtener_mapeo_vendedores():
    return [{"vendedor": k, "correo": v} for k, v in MAPEO_VENDEDORES.items()]

@router.post("/vendedores")
def guardar_mapeo_vendedor(payload: dict):
    vendedor = str(payload.get("vendedor", "")).strip().upper()
    correo = str(payload.get("correo", "")).strip().lower()
    if vendedor and correo:
        MAPEO_VENDEDORES[vendedor] = correo
        return {"status": "success", "vendedor": vendedor, "correo": correo}
    raise HTTPException(status_code=400, detail="Datos de vendedor o correo inválidos")

@router.post("/upload")
async def cargar_excel_siesa(file: UploadFile = File(...)):
    global DB_CARTERA_GLOBAL
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Formato no soportado. Debe ser .xlsx o .xls")

    try:
        contents = await file.read()
        raw_df = pd.read_excel(io.BytesIO(contents))
        
        if raw_df.empty:
            raise HTTPException(status_code=400, detail="El archivo Excel está completamente vacío.")

        registros_procesados = []
        fecha_actual = datetime.now()

        for idx, row in raw_df.iterrows():
            row_dict = {str(k).strip().lower(): v for k, v in row.to_dict().items() if pd.notna(v)}
            
            cliente = str(row_dict.get('razón social sucursal', row_dict.get('cliente', 'CLIENTE VARIOS'))).strip()
            nit = str(row_dict.get('cliente', row_dict.get('auxiliar', 'N/A'))).strip()
            factura = str(row_dict.get('nro. docto. cruce', f'FACT-{idx+1}')).strip()
            vendedor = str(row_dict.get('razón social vend. cliente', 'SIN VENDEDOR')).strip().upper()
            
            val_raw = row_dict.get('total cop', 0)
            val_clean = 0.0
            try:
                if isinstance(val_raw, (int, float)):
                    val_clean = float(val_raw)
                else:
                    val_str = str(val_raw).replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
                    val_clean = float(val_str)
            except Exception:
                val_clean = 0.0

            fecha_venc_raw = row_dict.get('fecha vcto.', row_dict.get('fecha docto cruce', 'N/A'))
            dias_mora = 0
            fecha_venc_str = str(fecha_venc_raw)

            try:
                dt = pd.to_datetime(fecha_venc_raw, dayfirst=True, errors='coerce')
                if not pd.isna(dt):
                    dias_mora = (fecha_actual - dt).days
                    fecha_venc_str = dt.strftime('%Y-%m-%d')
            except Exception:
                dias_mora = 0

            registros_procesados.append({
                "id": idx + 1,
                "cliente": cliente,
                "nit": nit,
                "factura": factura,
                "vendedor": vendedor,
                "fecha_vencimiento": fecha_venc_str,
                "dias_mora": max(0, dias_mora),
                "valor": abs(val_clean)
            })

        DB_CARTERA_GLOBAL = registros_procesados
        
        return {
            "status": "success",
            "total_facturas": len(DB_CARTERA_GLOBAL),
            "saldo_total": sum(r["valor"] for r in DB_CARTERA_GLOBAL),
            "registros": DB_CARTERA_GLOBAL
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error leyendo SIESA: {str(e)}")

@router.get("/dashboard-metrics")
def obtener_metricas_dashboard():
    total_cartera = sum(r["valor"] for r in DB_CARTERA_GLOBAL)
    vencidos = [r for r in DB_CARTERA_GLOBAL if r["dias_mora"] > 0]
    total_vencido = sum(r["valor"] for r in vencidos)
    porcentaje_morosidad = (total_vencido / total_cartera * 100) if total_cartera > 0 else 0.0

    mora_0_30 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if 0 <= r["dias_mora"] <= 30)
    mora_31_60 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if 31 <= r["dias_mora"] <= 60)
    mora_61_90 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if 61 <= r["dias_mora"] <= 90)
    mora_mayor_90 = sum(r["valor"] for r in DB_CARTERA_GLOBAL if r["dias_mora"] > 90)

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
def obtener_mis_datos():
    return DB_CARTERA_GLOBAL

# --- PLANTILLA DE CORREO ELEGANTE, NOVEDOSA Y MODERNA ---
def generar_html_correo(vendedor: str, facturas: list, total_vendedor: float) -> str:
    filas_html = ""
    for f in facturas:
        color_mora = "#ef4444" if f['dias_mora'] > 30 else "#f59e0b"
        filas_html += f"""
        <tr style="border-bottom: 1px solid #1e293b;">
            <td style="padding: 12px; color: #ffffff; font-weight: 600;">{f['cliente']}</td>
            <td style="padding: 12px; color: #3b82f6; font-family: monospace; font-weight: bold;">{f['factura']}</td>
            <td style="padding: 12px; color: #cbd5e1;">{f['fecha_vencimiento']}</td>
            <td style="padding: 12px; text-align: center;">
                <span style="background-color: {color_mora}; color: #ffffff; padding: 4px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;">
                    {f['dias_mora']} días
                </span>
            </td>
            <td style="padding: 12px; text-align: right; color: #10b981; font-weight: bold;">${f['valor']:,.2f}</td>
        </tr>
        """

    pixel_id = f"{vendedor}_{int(datetime.now().timestamp())}"
    pixel_url = f"http://192.168.1.76:8000/api/cartera/tracking/pixel.png?id={pixel_id}"

    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
    </head>
    <body style="margin: 0; padding: 0; background-color: #070c18; font-family: 'Segoe UI', Arial, sans-serif; color: #e2e8f0;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #070c18; padding: 30px 10px;">
            <tr>
                <td align="center">
                    <table width="650" cellpadding="0" cellspacing="0" style="background: linear-gradient(145deg, #0f172a, #0b1120); border-radius: 16px; border: 1px solid #1e293b; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.6);">
                        
                        <!-- CABECERA DE IMPACTO -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #0f6c2f, #0a4f21); padding: 25px; text-align: center; border-bottom: 3px solid #f97316;">
                                <h1 style="color: #f97316; margin: 0; font-size: 26px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">IMPLESEG S.A.S</h1>
                                <p style="color: #86efac; margin: 5px 0 0 0; font-size: 12px; font-weight: bold; letter-spacing: 2px;">SISTEMA INTEGRADO EMPRESARIAL · GESTIÓN DE CARTERA</p>
                            </td>
                        </tr>

                        <!-- CONTENIDO -->
                        <tr>
                            <td style="padding: 30px;">
                                <h2 style="color: #ffffff; margin-top: 0; font-size: 20px;">🚨 Alerta de Cartera Vencida</h2>
                                <p style="color: #94a3b8; font-size: 14px; line-height: 1.6;">
                                    Estimado(a) <b style="color: #f97316;">{vendedor}</b>,<br>
                                    A continuación se detalla el estado actualizado de las facturas en mora asignadas a su gestión comercial:
                                </p>

                                <!-- TARJETA RESUMEN 3D -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin: 25px 0; background: #070d19; border-radius: 12px; border: 1px solid #1e293b; padding: 20px; text-align: center;">
                                    <tr>
                                        <td width="50%" style="border-right: 1px solid #1e293b;">
                                            <span style="font-size: 11px; color: #94a3b8; font-weight: bold; text-transform: uppercase;">SALDO TOTAL VENCIDO</span><br>
                                            <span style="font-size: 24px; color: #ef4444; font-weight: 800; font-family: monospace;">${total_vendedor:,.2f} COP</span>
                                        </td>
                                        <td width="50%">
                                            <span style="font-size: 11px; color: #94a3b8; font-weight: bold; text-transform: uppercase;">FACTURAS PENDIENTES</span><br>
                                            <span style="font-size: 24px; color: #3b82f6; font-weight: 800; font-family: monospace;">{len(facturas)}</span>
                                        </td>
                                    </tr>
                                </table>

                                <!-- TABLA DE FACTURAS -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse; font-size: 13px;">
                                    <thead>
                                        <tr style="background-color: #1e293b; color: #94a3b8; text-transform: uppercase; font-size: 11px;">
                                            <th style="padding: 10px; text-align: left;">Cliente</th>
                                            <th style="padding: 10px; text-align: left;">Factura</th>
                                            <th style="padding: 10px; text-align: left;">Vencimiento</th>
                                            <th style="padding: 10px; text-align: center;">Días Mora</th>
                                            <th style="padding: 10px; text-align: right;">Valor COP</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filas_html}
                                    </tbody>
                                </table>

                                <p style="color: #64748b; font-size: 12px; margin-top: 30px; text-align: center;">
                                    Por favor gestionar el cobro inmediato con sus clientes o reportar novedades al departamento de Contabilidad.
                                </p>
                            </td>
                        </tr>

                        <!-- PIE DE PÁGINA -->
                        <tr>
                            <td style="background-color: #070c18; padding: 15px; text-align: center; border-top: 1px solid #1e293b; font-size: 11px; color: #64748b;">
                                © IMPLESEG S.A.S · Notificación Automática Generada por ERP Corporativo.<br>
                                <img src="{pixel_url}" width="1" height="1" alt="" style="display:none;" />
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

# --- ENVÍO INDIVIDUAL DE UN VENDEDOR ESPECÍFICO ---
@router.post("/notificar-individual")
def ejecutar_envio_individual(payload: dict):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    vendedor = payload.get("vendedor", "").strip().upper()
    correo_destino = payload.get("correo", "").strip().lower()

    if not vendedor or not correo_destino:
        raise HTTPException(status_code=400, detail="Vendedor y correo son requeridos.")

    facturas_vendedor = [f for f in DB_CARTERA_GLOBAL if f["vendedor"] == vendedor]

    if not facturas_vendedor:
        raise HTTPException(status_code=400, detail=f"No hay facturas registradas para el vendedor {vendedor}.")

    total_vendedor = sum(f["valor"] for f in facturas_vendedor)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 IMPLESEG ERP: Notificación de Cartera Vencida - {vendedor}"
        msg["From"] = f"IMPLESEG S.A.S <{SENDER_EMAIL}>"
        msg["To"] = correo_destino

        html_body = generar_html_correo(vendedor, facturas_vendedor, total_vendedor)
        msg.attach(MIMEText(html_body, "html"))

        server.sendmail(SENDER_EMAIL, correo_destino, msg.as_string())
        server.quit()

        BITACORA_ENVIOS.append({
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "vendedor": vendedor,
            "correo": correo_destino,
            "estado": "Entregado",
            "confirmacion": "Pendiente"
        })

        return {"status": "success", "mensaje": f"Notificación enviada a {vendedor} (<{correo_destino}>)"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando correo SMTP: {str(e)}")

# --- ENVÍO MASIVO DE TODOS LOS VENDEDORES ---
@router.post("/notificar")
def ejecutar_envio_masivo():
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    if not DB_CARTERA_GLOBAL:
        raise HTTPException(status_code=400, detail="No hay datos de cartera cargados para notificar")

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
            msg["Subject"] = f"🚨 IMPLESEG ERP: Notificación de Cartera Vencida - {vendedor}"
            msg["From"] = f"IMPLESEG S.A.S <{SENDER_EMAIL}>"
            msg["To"] = correo_destino

            html_body = generar_html_correo(vendedor, facturas, total_vendedor)
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
        raise HTTPException(status_code=500, detail=f"Error despachando correos: {str(e)}")

@router.get("/tracking/pixel.png")
def tracking_pixel(id: str):
    for envio in BITACORA_ENVIOS:
        if envio["vendedor"] in id:
            envio["confirmacion"] = "Leído ✅"
    
    pixel_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=pixel_bytes, media_type="image/png")

@router.get("/bitacora")
def obtener_bitacora():
    return BITACORA_ENVIOS