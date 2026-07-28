from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pydantic import BaseModel
from sqlalchemy import func
from datetime import datetime

from app.database import get_session
from app.models import RegistroEtiqueta

router = APIRouter(prefix="/etiquetas", tags=["Control Etiquetas"])
templates = Jinja2Templates(directory="app/templates")

# Esquema para recibir los datos del formulario web
class IngresoEtiqueta(BaseModel):
    cedula: str
    nombre_completo: str
    equipo_descripcion: str

def get_next_consecutivo(db: Session) -> int:
    """Calcula el siguiente número consecutivo buscando el máximo actual en la base de datos."""
    max_consecutivo = db.exec(select(func.max(RegistroEtiqueta.consecutivo))).first()
    return (max_consecutivo or 1000) + 1

@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas(request: Request):
    """Renderiza la interfaz web de control de etiquetas."""
    return templates.TemplateResponse("recepcion_etiquetas.html", {"request": request})

@router.get("/api/registros")
async def listar_registros(db: Session = Depends(get_session)):
    """Devuelve los registros para mostrarlos en la tabla web."""
    registros = db.exec(select(RegistroEtiqueta).order_by(RegistroEtiqueta.consecutivo.desc())).all()
    return [{
        "id": r.id, 
        "consecutivo": r.consecutivo, 
        "cedula": r.cedula, 
        "nombre": r.nombre_completo, 
        "equipo": r.equipo_descripcion, 
        "fecha": r.fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S")
    } for r in registros]

@router.post("/api/registrar")
async def registrar_y_generar(datos: IngresoEtiqueta, db: Session = Depends(get_session)):
    """Registra el ingreso, asigna consecutivo y devuelve datos para imprimir en ZPL."""
    try:
        nuevo_consecutivo = get_next_consecutivo(db)
        
        nuevo_registro = RegistroEtiqueta(
            consecutivo=nuevo_consecutivo,
            cedula=datos.cedula,
            nombre_completo=datos.nombre_completo.upper(),
            equipo_descripcion=datos.equipo_descripcion.upper()
        )
        
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        # Generar código ZPL básico (Para impresoras térmicas como Zebra)
        fecha_str = nuevo_registro.fecha_ingreso.strftime("%Y-%m-%d")
        
        # Este es el código crudo que entiende la impresora para dibujar la etiqueta
        zpl_code = f"""^XA
^PW400
^LL200
^FO20,20^A0N,25,25^FDIMPLESEG S.A.S^FS
^FO20,50^A0N,20,20^FDControl de Ingreso^FS
^FO20,80^A0N,20,20^FDC.C: {nuevo_registro.cedula}^FS
^FO20,105^A0N,20,20^FDNom: {nuevo_registro.nombre_completo[:20]}^FS
^FO20,130^A0N,20,20^FDFecha: {fecha_str}^FS
^FO220,100^BQN,2,4^FDQA,{nuevo_registro.consecutivo}^FS
^FO220,160^A0N,25,25^FDN. {nuevo_registro.consecutivo}^FS
^XZ"""

        return {
            "status": "ok", 
            "mensaje": f"Registro guardado exitosamente. Consecutivo asignado: {nuevo_consecutivo}",
            "zpl": zpl_code
        }
    except Exception as e:
        print(f"Error registrando etiqueta: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor.")