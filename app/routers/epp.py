import os
import re
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session
from sqlalchemy import text
from app.database import get_session

# Importaciones de Google Drive API
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    HAS_DRIVE = True
except ImportError:
    HAS_DRIVE = False

router = APIRouter(prefix="/epp", tags=["EPP"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_OUTPUT_DIR = os.path.join(BASE_DIR, "static", "epp_pdfs")
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

DRIVE_FOLDER_ID = "1VK0JzoDM0hSlbeQA-dGYBsgE4EUafzcY"
SERVICE_ACCOUNT_FILE = '/home/rtecnico/IMPLESEG/credentials.json'

def subir_a_google_drive(filepath, filename):
    if not HAS_DRIVE or not os.path.exists(SERVICE_ACCOUNT_FILE):
        print("⚠️ No se encontró credentials.json o librería googleapiclient.")
        return None
    try:
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        
        file_metadata = {
            'name': filename,
            'parents': [DRIVE_FOLDER_ID]
        }
        media = MediaFileUpload(filepath, mimetype='text/html')
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"✅ Archivo {filename} subido con éxito a Google Drive. ID: {file.get('id')}")
        return file.get('id')
    except Exception as e:
        print("❌ Error al subir a Google Drive:", str(e))
        return None

# ==============================================================================
# ENDPOINT 1: BUSCAR HISTORIAL POR CÉDULA
# ==============================================================================
@router.get("/buscar/{cedula}")
def buscar_usuario_epp(cedula: str, session: Session = Depends(get_session)):
    try:
        query = text("""
            SELECT * FROM epp_entregas 
            WHERE cedula = :c 
            ORDER BY id ASC
        """)
        registros = session.execute(query, {"c": cedula}).mappings().all()
        
        if not registros:
            return JSONResponse({"encontrado": False})
            
        ultimo = registros[-1]
        historial = []
        for r in registros:
            historial.append({
                "fecha": str(r.get("fecha_ingreso", "")),
                "camisa_cant": r.get("camisa_cant", ""),
                "camisa_talla": r.get("camisa_talla", ""),
                "pantalon_cant": r.get("pantalon_cant", ""),
                "pantalon_talla": r.get("pantalon_talla", ""),
                "botas_cant": r.get("botas_cant", ""),
                "botas_talla": r.get("botas_talla", ""),
                "chaleco_cant": r.get("chaleco_cant", ""),
                "chaleco_talla": r.get("chaleco_talla", ""),
                "gorra": r.get("gorra", ""),
                "gafas": r.get("gafas", ""),
                "prot_insercion": r.get("prot_insercion", ""),
                "prot_copa": r.get("prot_copa", ""),
                "otro_elem": r.get("otro_elem", ""),
                "cantidad_detalle": r.get("cantidad_detalle", ""),
                "firma_colaborador": r.get("firma_colaborador", ""),
                "firma_entrega": r.get("firma_entrega", "")
            })

        return JSONResponse({
            "encontrado": True,
            "colaborador": {
                "nombre": ultimo.get("nombre", ""),
                "cargo": ultimo.get("cargo", ""),
                "area": ultimo.get("area", ""),
                "fecha_ingreso": str(ultimo.get("fecha_ingreso", ""))
            },
            "historial": historial
        })
    except Exception as e:
        return JSONResponse({"encontrado": False, "error": str(e)})

# ==============================================================================
# ENDPOINT 2: GUARDAR NUEVA ENTREGA Y GENERAR ARCHIVO EPP
# ==============================================================================
@router.post("/guardar")
async def guardar_epp(
    request: Request,
    cedula: str = Form(...),
    nombre: str = Form(...),
    cargo: str = Form(""),
    area: str = Form(""),
    fecha_ingreso: str = Form(""),
    camisa_cant: str = Form(""),
    camisa_talla: str = Form(""),
    pantalon_cant: str = Form(""),
    pantalon_talla: str = Form(""),
    botas_cant: str = Form(""),
    botas_talla: str = Form(""),
    chaleco_cant: str = Form(""),
    chaleco_talla: str = Form(""),
    gorra: str = Form(""),
    gafas: str = Form(""),
    prot_insercion: str = Form(""),
    prot_copa: str = Form(""),
    otro_elem: str = Form(""),
    cantidad_detalle: str = Form(""),
    firma_colaborador: str = Form(""),
    firma_entrega: str = Form(""),
    session: Session = Depends(get_session)
):
    try:
        # 1. Asegurar tabla en base de datos
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS epp_entregas (
                id SERIAL PRIMARY KEY,
                cedula VARCHAR NOT NULL,
                nombre VARCHAR NOT NULL,
                cargo VARCHAR,
                area VARCHAR,
                fecha_ingreso VARCHAR,
                camisa_cant VARCHAR, camisa_talla VARCHAR,
                pantalon_cant VARCHAR, pantalon_talla VARCHAR,
                botas_cant VARCHAR, botas_talla VARCHAR,
                chaleco_cant VARCHAR, chaleco_talla VARCHAR,
                gorra VARCHAR, gafas VARCHAR,
                prot_insercion VARCHAR, prot_copa VARCHAR,
                otro_elem VARCHAR, cantidad_detalle VARCHAR,
                firma_colaborador TEXT, firma_entrega TEXT
            );
        """))
        session.commit()

        # 2. Registrar la nueva entrega
        session.execute(text("""
            INSERT INTO epp_entregas (
                cedula, nombre, cargo, area, fecha_ingreso,
                camisa_cant, camisa_talla, pantalon_cant, pantalon_talla,
                botas_cant, botas_talla, chaleco_cant, chaleco_talla,
                gorra, gafas, prot_insercion, prot_copa,
                otro_elem, cantidad_detalle, firma_colaborador, firma_entrega
            ) VALUES (
                :cedula, :nombre, :cargo, :area, :fecha_ingreso,
                :camisa_cant, :camisa_talla, :pantalon_cant, :pantalon_talla,
                :botas_cant, :botas_talla, :chaleco_cant, :chaleco_talla,
                :gorra, :gafas, :prot_insercion, :prot_copa,
                :otro_elem, :cantidad_detalle, :firma_colaborador, :firma_entrega
            )
        """), {
            "cedula": cedula, "nombre": nombre, "cargo": cargo, "area": area, "fecha_ingreso": fecha_ingreso,
            "camisa_cant": camisa_cant, "camisa_talla": camisa_talla,
            "pantalon_cant": pantalon_cant, "pantalon_talla": pantalon_talla,
            "botas_cant": botas_cant, "botas_talla": botas_talla,
            "chaleco_cant": chaleco_cant, "chaleco_talla": chaleco_talla,
            "gorra": gorra, "gafas": gafas, "prot_insercion": prot_insercion, "prot_copa": prot_copa,
            "otro_elem": otro_elem, "cantidad_detalle": cantidad_detalle,
            "firma_colaborador": firma_colaborador, "firma_entrega": firma_entrega
        })
        session.commit()

        # 3. Consultar todo el historial acumulado de entregas para este trabajador
        registros = session.execute(
            text("SELECT * FROM epp_entregas WHERE cedula = :c ORDER BY id ASC"),
            {"c": cedula}
        ).mappings().all()

        # Build HTML table rows for full history
        filas_html = ""
        for r in registros:
            filas_html += f"""
            <tr>
                <td style="text-align:center;">{r.get('fecha_ingreso') or ''}</td>
                <td style="text-align:center;">{r.get('camisa_cant') if r.get('camisa_cant') != '0' else ''}</td>
                <td style="text-align:center;">{r.get('camisa_talla') or ''}</td>
                <td style="text-align:center;">{r.get('pantalon_cant') if r.get('pantalon_cant') != '0' else ''}</td>
                <td style="text-align:center;">{r.get('pantalon_talla') or ''}</td>
                <td style="text-align:center;">{r.get('botas_cant') if r.get('botas_cant') != '0' else ''}</td>
                <td style="text-align:center;">{r.get('botas_talla') or ''}</td>
                <td style="text-align:center;">{r.get('chaleco_cant') if r.get('chaleco_cant') != '0' else ''}</td>
                <td style="text-align:center;">{r.get('chaleco_talla') or ''}</td>
                <td style="text-align:center;">{r.get('gorra') if r.get('gorra') != '0' else ''}</td>
                <td style="text-align:center;">{r.get('gafas') if r.get('gafas') != '0' else ''}</td>
                <td style="text-align:center;">{r.get('prot_insercion') if r.get('prot_insercion') != '0' else ''}</td>
                <td style="text-align:center;">{r.get('prot_copa') if r.get('prot_copa') != '0' else ''}</td>
                <td style="text-align:center;">{'Sí' if r.get('otro_elem') else ''}</td>
                <td style="text-align:center;">{r.get('otro_elem') or ''} {r.get('cantidad_detalle') or ''}</td>
                <td style="text-align:center; padding:2px;"><img src="{r.get('firma_entrega')}" style="max-height:25px;"></td>
                <td style="text-align:center; padding:2px;"><img src="{r.get('firma_colaborador')}" style="max-height:25px;"></td>
            </tr>
            """

        # Fill up grid empty lines
        filas_restantes = max(0, 12 - len(registros))
        for _ in range(filas_restantes):
            filas_html += "<tr>" + "<td>&nbsp;</td>" * 17 + "</tr>"

        # 4. Formatear el nombre exacto de la nomenclatura empresarial: EPP_CEDULA_NOMBRE.pdf
        nombre_limpio = re.sub(r'[^A-Za-z0-9_ ]+', '', nombre.upper()).strip()
        filename = f"EPP_{cedula}_{nombre_limpio}.html"
        filename_pdf = f"EPP_{cedula}_{nombre_limpio}.pdf"
        filepath = os.path.join(PDF_OUTPUT_DIR, filename)

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{filename_pdf}</title>
    <style>
        @page {{ size: letter portrait; margin: 8mm; }}
        body {{ font-family: Arial, sans-serif; font-size: 10px; color: #000; margin: 0; padding: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: -1px; }}
        td, th {{ border: 1px solid #000; padding: 3px 5px; box-sizing: border-box; }}
        .header-table td {{ text-align: center; font-weight: bold; }}
        .bg-green {{ background-color: #c5d99b; font-weight: bold; text-align: center; }}
        .vertical-text {{ writing-mode: vertical-lr; transform: rotate(180deg); text-align: center; white-space: nowrap; font-size: 8px; padding: 2px; height: 75px; width: 18px; }}
        .footer-legal {{ font-size: 7.5px; text-align: justify; line-height: 1.1; padding: 4px; }}
        .footer-signatures {{ text-align: center; font-weight: bold; font-size: 8.5px; }}
    </style>
</head>
<body>

    <!-- ENCABEZADO OFICIAL IMPLESEG -->
    <table class="header-table">
        <tr>
            <td style="width: 20%; padding: 4px; background: #ffffff;">
                <img src="https://impleseg.com/wp-content/uploads/2021/04/logo-impleseg.png" style="max-width: 130px; height: auto; display: block; margin: 0 auto;">
            </td>
            <td style="width: 55%; font-size: 11px;">
                IMPLESEG S.A.S<br>
                REGISTRO DE ENTREGA DE ELEMENTOS DE PROTECCIÓN PERSONAL (EPP) Y DOTACIÓN
            </td>
            <td style="width: 25%; padding: 0;">
                <table style="width:100%; height:100%; border:none;">
                    <tr><td style="border-top:none; border-left:none;">Código:</td><td style="border-top:none; border-right:none;">F-SGI-GS-03</td></tr>
                    <tr><td style="border-left:none;">Revisión:</td><td style="border-right:none;">03</td></tr>
                    <tr><td style="border-left:none;">Fecha:</td><td style="border-right:none;">30/9/2026</td></tr>
                    <tr><td style="border-bottom:none; border-left:none;">Página:</td><td style="border-bottom:none; border-right:none;">1 de 1</td></tr>
                </table>
            </td>
        </tr>
    </table>

    <!-- DATOS DEL TRABAJADOR -->
    <table>
        <tr>
            <td style="width: 10%;"><b>Nombre:</b></td>
            <td style="width: 30%;">{nombre}</td>
            <td style="width: 10%;"><b>Cédula:</b></td>
            <td style="width: 25%;">{cedula}</td>
            <td style="width: 10%;"><b>Fecha de ingreso:</b></td>
            <td style="width: 15%;">{fecha_ingreso}</td>
        </tr>
        <tr>
            <td><b>Cargo:</b></td>
            <td>{cargo}</td>
            <td><b>Área:</b></td>
            <td colspan="3">{area}</td>
        </tr>
    </table>

    <!-- MATRIZ HISTÓRICA COMPLETA DE EPP -->
    <table>
        <thead>
            <tr class="bg-green">
                <th rowspan="2" style="width:70px;">Fecha de Entrega</th>
                <th colspan="2">Camisa</th>
                <th colspan="2">Pantalón</th>
                <th colspan="2">Bota de Seguridad</th>
                <th colspan="2">Chaleco</th>
                <th rowspan="2" class="vertical-text">Gorra</th>
                <th rowspan="2" class="vertical-text">Gafas</th>
                <th colspan="2">Protección Auditiva</th>
                <th rowspan="2" class="vertical-text">¿Otro?</th>
                <th rowspan="2" style="width:80px;">¿Cuál?</th>
                <th rowspan="2" style="width:85px;">Firma Quien Entrega</th>
                <th rowspan="2" style="width:85px;">Firma Quien Recibe</th>
            </tr>
            <tr class="bg-green">
                <th class="vertical-text">Cantidad</th>
                <th class="vertical-text">Talla</th>
                <th class="vertical-text">Cantidad</th>
                <th class="vertical-text">Talla</th>
                <th class="vertical-text">Cantidad</th>
                <th class="vertical-text">Talla</th>
                <th class="vertical-text">Cantidad</th>
                <th class="vertical-text">Talla</th>
                <th class="vertical-text">Inserción</th>
                <th class="vertical-text">Copa</th>
            </tr>
        </thead>
        <tbody>
            {filas_html}
        </tbody>
    </table>

    <!-- MARCO LEGAL Y CONFIDENCIALIDAD -->
    <table>
        <tr>
            <td class="footer-legal">
                El trabajador manifiesta haber recibido capacitación sobre el uso correcto y los riesgos para los cuales esto(s) elemento(s) lo van a proteger, y se obliga a reportar de manera inmediata cualquier daño, pérdida o desgaste para proceder a su respectiva reposición, además se compromete a usarlo cuando esté en presencia del factor de riesgo, a darle un uso adecuado y a devolverle a la empresa los elementos desgastados o dañados, en caso de pérdida, daño intencional o la no devolución, el trabajador autoriza a la empresa para que descuente el valor correspondiente de los salarios y/o prestaciones sociales.<br>
                Utilizando los EPP, el trabajador cumple con sus deberes definidos en la Ley a través de la siguiente normatividad: Código Sustantivo del Trabajo; Art. 56 y Art. 58 numeral 7; Art. 88; Decreto 1295 de 1994 Art. 22.
            </td>
        </tr>
    </table>

    <table class="footer-signatures">
        <tr>
            <td style="width:33%;">Elaboró</td>
            <td style="width:33%;">Revisó</td>
            <td style="width:34%;">Gerente</td>
        </tr>
        <tr>
            <td>Coordinador SGI</td>
            <td>Coordinador SGI</td>
            <td>Aprobó</td>
        </tr>
        <tr>
            <td colspan="3" style="font-size: 6.5px; text-align: justify; font-weight: normal; padding: 2px 4px;">
                <b>CLAUSULA DE CONFIDENCIALIDAD:</b> Esta información es propiedad intelectual de IMPLESEG S.A.S, Cualquier cambio, copia o reproducción, debe ser autorizada por el Líder de área y posteriormente approved por el representante del sistema de gestión integral.
            </td>
        </tr>
    </table>

    <script>window.onload = function() {{ window.print(); }};</script>
</body>
</html>
        """

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Subir a Google Drive con el nombre normalizado
        subir_a_google_drive(filepath, filename_pdf)

        pdf_url = f"/static/epp_pdfs/{filename}"

        return JSONResponse({
            "status": "success",
            "message": f"Registro actualizado e historial generado para {nombre}",
            "pdf_url": pdf_url
        })
    except Exception as e:
        session.rollback()
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)