from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime
from pydantic import BaseModel
import csv
import io

from app.database import get_session
from app.models import Visitante

router = APIRouter(prefix="/recepcion", tags=["Recepción"])
templates = Jinja2Templates(directory="app/templates")

# Esquemas para recibir datos desde el frontend
class IngresoVisitante(BaseModel):
    nombre_completo: str
    cedula: str
    empresa: str
    correo: str
    area_visita: str
    motivo_visita: str
    arl: str
    numero_emergencia: str
    persona_recibe: str

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
            raise HTTPException(status_code=400, detail=f"{visitante_activo.nombre_completo} ya tiene un ingreso activo. Debe marcar salida primero.")

        nuevo_ingreso = Visitante(
            cedula=datos.cedula,
            nombre_completo=datos.nombre_completo.upper(),
            empresa=datos.empresa.upper() if datos.empresa else "N/A",
            correo=datos.correo.lower() if datos.correo else "N/A",
            area_visita=datos.area_visita.upper(),
            motivo_visita=datos.motivo_visita.upper(),
            arl=datos.arl.upper(),
            numero_emergencia=datos.numero_emergencia,
            persona_recibe=datos.persona_recibe.upper(),
            fecha_ingreso=datetime.now()
        )
        
        db.add(nuevo_ingreso)
        db.commit()
        return {"status": "ok", "nombre": nuevo_ingreso.nombre_completo}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en ingreso: {e}")
        raise HTTPException(status_code=500, detail="Error interno en el servidor. Verifica los datos.")

@router.post("/api/salida")
async def registrar_salida(datos: SalidaVisitante, db: Session = Depends(get_session)):
    """Registra la salida verificando si existe."""
    
    visitante = db.exec(
        select(Visitante)
        .where(Visitante.cedula == datos.cedula, Visitante.fecha_salida == None)
        .order_by(Visitante.id.desc())
    ).first()

    if not visitante:
        raise HTTPException(status_code=404, detail="No se encontró un ingreso activo para esta cédula. Verifique el número ingresado.")

    visitante.fecha_salida = datetime.now()
    db.add(visitante)
    db.commit()
    
    return {
        "status": "ok", 
        "nombre": visitante.nombre_completo,
        "hora_salida": visitante.fecha_salida.strftime("%H:%M:%S")
    }

@router.get("/api/descargar_csv")
async def descargar_csv(db: Session = Depends(get_session)):
    """Exporta toda la tabla de visitantes a formato CSV (Excel)."""
    visitantes = db.exec(select(Visitante)).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow(["ID", "Cédula", "Nombre", "Empresa", "Correo", "Área Visitada", "Motivo", "ARL", "Contacto Emergencia", "Recibido Por", "Fecha/Hora Ingreso", "Fecha/Hora Salida"])
    
    # Escribir datos
    for v in visitantes:
        fecha_salida_str = v.fecha_salida.strftime("%Y-%m-%d %H:%M:%S") if v.fecha_salida else "AÚN EN INSTALACIONES"
        writer.writerow([
            v.id, v.cedula, v.nombre_completo, v.empresa, v.correo, v.area_visita, 
            v.motivo_visita, v.arl, v.numero_emergencia, v.persona_recibe, 
            v.fecha_ingreso.strftime("%Y-%m-%d %H:%M:%S"), fecha_salida_str
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=Registro_Visitantes_{datetime.now().strftime('%Y%m%d')}.csv"}
    )