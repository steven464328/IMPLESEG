import os
import base64
from fastapi import APIRouter, Request, Form, Depends, HTTPException
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
        filename = f"F-SGI-GS-03_{cedula}.pdf"
        filepath = os.path.join(PDF_OUTPUT_DIR, filename)

        # HIC PDF GENERATUR ET ENREGISTRATUR IN FILEPATH
        # (Exemplo: scribere base64 vel generare cum reportlab/fpdf)
        
        pdf_url = f"/static/epp_pdfs/{filename}"

        return JSONResponse({
            "status": "success",
            "message": "Registro F-SGI-GS-03 generado correctamente",
            "pdf_url": pdf_url
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)