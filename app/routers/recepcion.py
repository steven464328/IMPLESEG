from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from pydantic import BaseModel

from app.database import get_session
from app.models import Visitante

router = APIRouter(prefix="/recepcion", tags=["Recepción"])
templates = Jinja2Templates(directory="app/templates")

# Esquemas para recibir datos desde el frontend (AJAX)
class IngresoVisitante(BaseModel):
    cedula: str
    nombre_completo: str
    empresa: str
    tipo_visitante: str
    a_quien_visita: str
    arl: str
    tarjeta_asignada: str

class SalidaVisitante(BaseModel):
    cedula: str

@router.get("/visitantes", response_class=HTMLResponse)
async def vista_recepcion(request: Request):
    """Renderiza la interfaz principal (Botones Ingreso/Salida)"""
    return templates.TemplateResponse("recepcion_visitantes.html", {"request": request})

@router.post("/api/ingreso")
async def registrar_ingreso(datos: IngresoVisitante, db: Session = Depends(get_session)):
    """API para registrar la entrada de un visitante."""
    
    # Validar si ya está adentro sin haber marcado salida
    visitante_activo = db.exec(
        select(Visitante).where(
            Visitante.cedula == datos.cedula,
            Visitante.fecha_salida == None
        )
    ).first()

    if visitante_activo:
        raise HTTPException(status_code=400, detail="Este visitante ya tiene un ingreso activo. Debe marcar salida primero.")

    nuevo_ingreso = Visitante(
        cedula=datos.cedula,
        nombre_completo=datos.nombre_completo.upper(),
        empresa=datos.empresa.upper(),
        tipo_visitante=datos.tipo_visitante,
        a_quien_visita=datos.a_quien_visita.upper(),
        arl=datos.arl,
        tarjeta_asignada=datos.tarjeta_asignada,
        fecha_ingreso=datetime.now()
    )
    
    db.add(nuevo_ingreso)
    db.commit()
    db.refresh(nuevo_ingreso)
    return {"status": "ok", "mensaje": "Ingreso registrado correctamente"}

@router.post("/api/salida")
async def registrar_salida(datos: SalidaVisitante, db: Session = Depends(get_session)):
    """API para registrar la salida usando solo la cédula."""
    
    # Buscar el último registro de esta cédula que no tenga salida
    visitante = db.exec(
        select(Visitante)
        .where(Visitante.cedula == datos.cedula, Visitante.fecha_salida == None)
        .order_by(Visitante.id.desc())
    ).first()

    if not visitante:
        raise HTTPException(status_code=404, detail="No se encontró un ingreso activo para esta cédula.")

    visitante.fecha_salida = datetime.now()
    db.add(visitante)
    db.commit()
    
    return {
        "status": "ok", 
        "mensaje": f"Salida registrada exitosamente para {visitante.nombre_completo}",
        "hora_salida": visitante.fecha_salida.strftime("%Y-%m-%d %H:%M:%S")
    }