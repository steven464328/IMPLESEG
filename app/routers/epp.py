import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
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
    camisa_cant: str = Form("0"),
    camisa_talla: str = Form(""),
    pantalon_cant: str = Form("0"),
    pantalon_talla: str = Form(""),
    botas_cant: str = Form("0"),
    botas_talla: str = Form(""),
    chaleco_cant: str = Form("0"),
    chaleco_talla: str = Form(""),
    gorra: str = Form("0"),
    gafas: str = Form("0"),
    prot_insercion: str = Form("0"),
    prot_copa: str = Form("0"),
    otro_elem: str = Form(""),
    cantidad_detalle: str = Form(""),
    firma_colaborador: str = Form(...),
    firma_entrega: str = Form(...),
    session: Session = Depends(get_session)
):
    try:
        filename = f"F-SGI-GS-03_{cedula}.html"
        filepath = os.path.join(PDF_OUTPUT_DIR, filename)

        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>F-SGI-GS-03 {cedula}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 30px; color: #000; background: #fff; }}
                h2 {{ text-align: center; margin-bottom: 5px; color: #000; }}
                .subtitle {{ text-align: center; font-size: 12px; color: #555; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; }}
                th, td {{ border: 1px solid #000; padding: 6px 10px; font-size: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .signatures {{ display: flex; justify-content: space-between; margin-top: 30px; }}
                .sig-box {{ text-align: center; width: 45%; }}
                .sig-box img {{ max-width: 100%; height: 80px; border-bottom: 1px solid #000; }}
            </style>
        </head>
        <body>
            <h2>IMPLESEG S.A.S.</h2>
            <div class="subtitle">FORMATO OFICIAL F-SGI-GS-03 (REV. 03) - REGISTRO DE ENTREGA DE EPP Y DOTACIÓN</div>
            
            <table>
                <tr><th colspan="4">1. INFORMACIÓN DEL TRABAJADOR</th></tr>
                <tr><td><b>Cédula:</b> {cedula}</td><td><b>Nombre:</b> {nombre}</td><td><b>Cargo:</b> {cargo}</td><td><b>Área:</b> {area}</td></tr>
            </table>

            <table>
                <tr><th colspan="4">2. ELEMENTOS ENTREGADOS</th></tr>
                <tr><th>Elemento</th><th>Cantidad</th><th>Talla / Detalle</th></tr>
                <tr><td>Camisa</td><td>{camisa_cant}</td><td>{camisa_talla}</td></tr>
                <tr><td>Pantalón</td><td>{pantalon_cant}</td><td>{pantalon_talla}</td></tr>
                <tr><td>Botas de Seguridad</td><td>{botas_cant}</td><td>{botas_talla}</td></tr>
                <tr><td>Chaleco</td><td>{chaleco_cant}</td><td>{chaleco_talla}</td></tr>
                <tr><td>Gorra</td><td>{gorra}</td><td>-</td></tr>
                <tr><td>Gafas de Seguridad</td><td>{gafas}</td><td>-</td></tr>
                <tr><td>Prot. Inserción</td><td>{prot_insercion}</td><td>-</td></tr>
                <tr><td>Prot. Copa</td><td>{prot_copa}</td><td>-</td></tr>
                <tr><td>{otro_elem or 'Otro'}</td><td>-</td><td>{cantidad_detalle}</td></tr>
            </table>

            <div class="signatures">
                <div class="sig-box">
                    <img src="{firma_colaborador}">
                    <p><b>Firma Colaborador</b><br>{nombre}<br>C.C. {cedula}</p>
                </div>
                <div class="sig-box">
                    <img src="{firma_entrega}">
                    <p><b>Firma Quien Entrega</b><br>HSE / Gestión Humana</p>
                </div>
            </div>

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