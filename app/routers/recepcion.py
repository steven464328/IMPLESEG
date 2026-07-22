from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
import csv
import io

from app.database import get_session
from app.models import Visitante

router = APIRouter(prefix="/recepcion", tags=["Recepción"])
templates = Jinja2Templates(directory="app/templates")

# Esquema "Blindado": Acepta campos tanto del diseño viejo como del nuevo
class IngresoVisitante(BaseModel):
    cedula: str
    nombre_completo: str
    empresa: Optional[str] = "N/A"
    arl: Optional[str] = "N/A"
    
    # Campos del diseño nuevo
    tipo_visitante: Optional[str] = "N/A"
    a_quien_visita: Optional[str] = "N/A"
    tarjeta_asignada: Optional[str] = "N/A"
    
    # Campos del diseño viejo
    correo: Optional[str] = "N/A"
    area_visita: Optional[str] = "N/A"
    motivo_visita: Optional[str] = "N/A"
    numero_emergencia: Optional[str] = "N/A"
    persona_recibe: Optional[str] = "N/A"

class SalidaVisitante(BaseModel):
    cedula: str

@router.get("/visitantes", response_class=HTMLResponse)
async def vista_recepcion(request: Request):
    """Renderiza la interfaz principal"""
    return templates.TemplateResponse("recepcion_visitantes.html", {"request": request})

@router.post("/api/ingreso")
async def registrar_ingreso(datos: IngresoVisitante, db: Session = Depends(get_session)):
    """Registra la entrada de un visitante."""
    try:
        # Validar si ya está adentro sin haber marcado salida
        visitante_activo = db.exec(
            select(Visitante).where(
                Visitante.cedula == datos.cedula,
                Visitante.fecha_salida == None
            )
        ).first()

        if visitante_activo:
            raise HTTPException(status_code=400, detail=f"La cédula {datos.cedula} ya está adentro. Registre la salida primero.")

        # Crear el objeto con los datos básicos
        nuevo_ingreso = Visitante(
            cedula=datos.cedula,
            nombre_completo=datos.nombre_completo.upper(),
            fecha_ingreso=datetime.now()
        )
        
        # Asignar los campos dinámicamente solo si existen en tu base de datos actual
        campos_opcionales = ['empresa', 'arl', 'tipo_visitante', 'a_quien_visita', 'tarjeta_asignada', 'correo', 'area_visita', 'motivo_visita', 'numero_emergencia', 'persona_recibe']
        
        for campo in campos_opcionales:
            if hasattr(nuevo_ingreso, campo):
                valor = getattr(datos, campo)
                setattr(nuevo_ingreso, campo, valor.upper() if valor else "N/A")

        db.add(nuevo_ingreso)
        db.commit()
        return {"status": "ok", "nombre": nuevo_ingreso.nombre_completo}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en ingreso: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor guardando el registro.")

@router.post("/api/salida")
async def registrar_salida(datos: SalidaVisitante, db: Session = Depends(get_session)):
    """Registra la salida verificando si existe."""
    visitante = db.exec(
        select(Visitante)
        .where(Visitante.cedula == datos.cedula, Visitante.fecha_salida == None)
        .order_by(Visitante.id.desc())
    ).first()

    if not visitante:
        raise HTTPException(status_code=404, detail="Cédula no encontrada o ya registró su salida.")

    visitante.fecha_salida = datetime.now()
    db.add(visitante)
    db.commit()
    
    return {
        "status": "ok", 
        "mensaje": f"Buen viaje, {visitante.nombre_completo}",
        "hora_salida": visitante.fecha_salida.strftime("%H:%M:%S")
    }

@router.get("/api/descargar_csv")
async def descargar_csv(db: Session = Depends(get_session)):
    """Exporta la tabla a CSV a prueba de fallos."""
    visitantes = db.exec(select(Visitante)).all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow(["Cédula", "Nombre", "Empresa", "ARL", "A Quien Visita/Recibe", "Fecha Ingreso", "Fecha Salida"])
    
    # Datos extraídos dinámicamente para que nunca falle
    for v in visitantes:
        fecha_ing = v.fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S") if getattr(v, 'fecha_ingreso', None) else "N/A"
        fecha_sal = v.fecha_salida.strftime("%Y-%m-%d %H:%M:%S") if getattr(v, 'fecha_salida', None) else "AÚN EN INSTALACIONES"
        
        # Busca el campo de quien recibe, sin importar si es de la versión vieja o nueva
        recibe = getattr(v, 'a_quien_visita', getattr(v, 'persona_recibe', 'N/A'))
        
        writer.writerow([
            v.cedula, 
            v.nombre_completo, 
            getattr(v, 'empresa', 'N/A'), 
            getattr(v, 'arl', 'N/A'), 
            recibe,
            fecha_ing, 
            fecha_sal
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Visitantes_{datetime.now().strftime('%Y%m%d')}.csv"}
    )