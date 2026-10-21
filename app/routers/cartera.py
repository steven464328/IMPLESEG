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
            
            # 1. Cliente
            cliente = str(row_dict.get('razón social sucursal', row_dict.get('cliente', 'CLIENTE VARIOS'))).strip()
            
            # 2. NIT (En SIESA la columna 'cliente' trae el NIT)
            nit = str(row_dict.get('cliente', row_dict.get('auxiliar', 'N/A'))).strip()
            
            # 3. Factura
            factura = str(row_dict.get('nro. docto. cruce', f'FACT-{idx+1}')).strip()
            
            # 4. Vendedor
            vendedor = str(row_dict.get('razón social vend. cliente', 'SIN VENDEDOR')).strip().upper()
            
            # 5. Valor COP (Limpieza de puntos de miles y comas decimales)
            val_raw = row_dict.get('total cop', 0)
            val_clean = 0.0
            try:
                if isinstance(val_raw, (int, float)):
                    val_clean = float(val_raw)
                else:
                    # Formato COP: 2.244.697,00 -> 2244697.00
                    val_str = str(val_raw).replace('$', '').replace(' ', '').replace('.', '').replace(',', '.')
                    val_clean = float(val_str)
            except Exception:
                val_clean = 0.0

            # 6. Fecha Vencimiento y Cálculo de Días de Mora
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
            msg["Subject"] = f"🚨 Reporte de Cartera Vencida - Vendedor: {vendedor}"
            msg["From"] = f"IMPLESEG ERP <{SENDER_EMAIL}>"
            msg["To"] = correo_destino

            filas_html = "".join([f"<tr><td>{f['cliente']}</td><td>{f['nit']}</td><td>{f['factura']}</td><td>{f['fecha_vencimiento']}</td><td>{f['dias_mora']} días</td><td>${f['valor']:,.2f}</td></tr>" for f in facturas])
            
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