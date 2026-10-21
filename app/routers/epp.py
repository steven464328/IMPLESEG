import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session
from app.database import get_session

router = APIRouter(prefix="/epp", tags=["EPP"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_OUTPUT_DIR = os.path.join(BASE_DIR, "static", "epp_pdfs")
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

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
        filename = f"F-SGI-GS-03_{cedula}.html"
        filepath = os.path.join(PDF_OUTPUT_DIR, filename)

        # Rellenar filas vacías para completar la matriz del formato físico oficial
        filas_html = f"""
        <tr>
            <td style="text-align:center;">{fecha_ingreso or ''}</td>
            <td style="text-align:center;">{camisa_cant if camisa_cant != '0' else ''}</td>
            <td style="text-align:center;">{camisa_talla}</td>
            <td style="text-align:center;">{pantalon_cant if pantalon_cant != '0' else ''}</td>
            <td style="text-align:center;">{pantalon_talla}</td>
            <td style="text-align:center;">{botas_cant if botas_cant != '0' else ''}</td>
            <td style="text-align:center;">{botas_talla}</td>
            <td style="text-align:center;">{chaleco_cant if chaleco_cant != '0' else ''}</td>
            <td style="text-align:center;">{chaleco_talla}</td>
            <td style="text-align:center;">{gorra if gorra != '0' else ''}</td>
            <td style="text-align:center;">{gafas if gafas != '0' else ''}</td>
            <td style="text-align:center;">{prot_insercion if prot_insercion != '0' else ''}</td>
            <td style="text-align:center;">{prot_copa if prot_copa != '0' else ''}</td>
            <td style="text-align:center;">{'Sí' if otro_elem else ''}</td>
            <td style="text-align:center;">{otro_elem} {cantidad_detalle}</td>
            <td style="text-align:center; padding:2px;"><img src="{firma_entrega}" style="max-height:28px;"></td>
            <td style="text-align:center; padding:2px;"><img src="{firma_colaborador}" style="max-height:28px;"></td>
        </tr>
        """
        
        # Añadir filas de cuadrícula en blanco
        for _ in range(12):
            filas_html += "<tr>" + "<td>&nbsp;</td>" * 17 + "</tr>"

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>F-SGI-GS-03 - {cedula}</title>
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

    <!-- ENCABEZADO OFICIAL -->
    <table class="header-table">
        <tr>
            <td style="width: 20%; padding: 4px;">
                <img src="/static/img/logo.png" onerror="this.onerror=null; this.src='https://impleseg.com/wp-content/uploads/2021/04/logo-impleseg.png';" style="max-width: 130px; height: auto;">
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

    <!-- INFORMACIÓN DEL TRABAJADOR -->
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

    <!-- MATRIZ DE EPP Y DOTACIÓN -->
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

    <!-- PIE DE PÁGINA Y MARCO LEGAL -->
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
                <b>CLAUSULA DE CONFIDENCIALIDAD:</b> Esta información es propiedad intelectual de IMPLESEG S.A.S, Cualquier cambio, copia o reproducción, debe ser autorizada por el Líder de área y posteriormente aprobado por el representante del sistema de gestión integral. La información que se suministró en la presente planilla es veraz y me comprometo a cumplir con la información de notificación de riesgos y políticas de IMPLESEG S.A.S.
            </td>
        </tr>
    </table>

    <script>window.onload = function() {{ window.print(); }};</script>
</body>
</html>
        """

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        pdf_url = f"/static/epp_pdfs/{filename}"

        return JSONResponse({
            "status": "success",
            "message": f"Registro F-SGI-GS-03 generado para {nombre}",
            "pdf_url": pdf_url
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)