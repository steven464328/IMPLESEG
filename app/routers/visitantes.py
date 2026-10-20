from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session
from app.database import get_session

router = APIRouter(prefix="/api/visitantes", tags=["Visitantes"])

class VisitantePayload(BaseModel):
    id: Optional[int] = None
    nombre: str
    cedula: str
    empresa: Optional[str] = ""
    correo: Optional[str] = ""
    area: Optional[str] = ""
    motivo: Optional[str] = ""
    persona_recibe: Optional[str] = ""
    arl: Optional[str] = ""
    contacto: Optional[str] = ""

# Payload exacto para la importación desde Excel
class VisitanteImportPayload(BaseModel):
    nombre: str
    cedula: str
    empresa: str
    correo: str
    area: str
    motivo: str
    persona_recibe: str
    arl: str
    contacto: str
    hora_entrada: str
    hora_salida: Optional[str] = ""

@router.get("")
def listar_visitantes(session: Session = Depends(get_session)):
    query = text("SELECT * FROM registro_visitantes ORDER BY id DESC")
    result = session.execute(query).mappings().all()
    return [dict(r) for r in result]

@router.get("/buscar/{cedula}")
def buscar_visitante(cedula: str, session: Session = Depends(get_session)):
    query = text("""
        SELECT nombre, empresa, correo, arl, contacto 
        FROM registro_visitantes 
        WHERE cedula = :cedula 
        ORDER BY id DESC LIMIT 1
    """)
    res = session.execute(query, {"cedula": cedula}).mappings().first()
    if res:
        return dict(res)
    raise HTTPException(status_code=404, detail="Visitante nuevo")

@router.post("")
def registrar_ingreso(payload: VisitantePayload, session: Session = Depends(get_session)):
    try:
        query = text("""
            INSERT INTO registro_visitantes (
                nombre, cedula, empresa, correo, area, motivo,
                persona_recibe, arl, contacto, hora_entrada, estado
            ) VALUES (
                :nombre, :cedula, :empresa, :correo, :area, :motivo,
                :persona_recibe, :arl, :contacto, CURRENT_TIMESTAMP, 'DENTRO'
            ) RETURNING id;
        """)
        res = session.execute(query, payload.dict(exclude={"id"}))
        nuevo_id = res.scalar()
        session.commit()
        return {"id": nuevo_id, "status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/salida-cedula/{cedula}")
def registrar_salida_cedula(cedula: str, session: Session = Depends(get_session)):
    try:
        query = text("""
            UPDATE registro_visitantes 
            SET hora_salida = CURRENT_TIMESTAMP, estado = 'SALIO'
            WHERE id = (
                SELECT id FROM registro_visitantes 
                WHERE cedula = :cedula AND estado = 'DENTRO' 
                ORDER BY id DESC LIMIT 1
            )
            RETURNING id;
        """)
        res = session.execute(query, {"cedula": cedula})
        row = res.fetchone()
        session.commit()
        if not row:
            raise HTTPException(status_code=404, detail="No activo")
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{visitante_id}/salida-manual")
def registrar_salida_manual(visitante_id: int, session: Session = Depends(get_session)):
    try:
        query = text("""
            UPDATE registro_visitantes 
            SET hora_salida = CURRENT_TIMESTAMP, estado = 'SALIO (MANUAL)'
            WHERE id = :id
        """)
        session.execute(query, {"id": visitante_id})
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/importar")
def importar_historico(visitantes: List[VisitanteImportPayload], session: Session = Depends(get_session)):
    try:
        for v in visitantes:
            # Identificar estado basado en si tiene hora de salida en el Excel
            estado = "SALIO" if v.hora_salida and v.hora_salida.strip() != "" else "DENTRO"
            
            # Castear con cuidado las fechas ya arregladas desde el JavaScript
            query = text("""
                INSERT INTO registro_visitantes (
                    nombre, cedula, empresa, correo, area, motivo,
                    persona_recibe, arl, contacto, hora_entrada, hora_salida, estado
                ) VALUES (
                    :nombre, :cedula, :empresa, :correo, :area, :motivo,
                    :persona_recibe, :arl, :contacto, 
                    CAST(:hora_entrada AS TIMESTAMP), 
                    CASE WHEN :hora_salida = '' THEN NULL ELSE CAST(:hora_salida AS TIMESTAMP) END, 
                    :estado
                )
            """)
            session.execute(query, {
                "nombre": v.nombre,
                "cedula": v.cedula,
                "empresa": v.empresa,
                "correo": v.correo,
                "area": v.area,
                "motivo": v.motivo,
                "persona_recibe": v.persona_recibe,
                "arl": v.arl,
                "contacto": v.contacto,
                "hora_entrada": v.hora_entrada,
                "hora_salida": v.hora_salida,
                "estado": estado
            })
        session.commit()
        return {"status": "ok", "importados": len(visitantes)}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))