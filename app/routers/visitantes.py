from typing import Optional
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

@router.get("")
def listar_visitantes(session: Session = Depends(get_session)):
    query = text("SELECT * FROM registro_visitantes ORDER BY id DESC")
    result = session.execute(query).mappings().all()
    return [dict(r) for r in result]

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

@router.put("/{visitante_id}/salida")
def registrar_salida(visitante_id: int, session: Session = Depends(get_session)):
    try:
        query = text("""
            UPDATE registro_visitantes 
            SET hora_salida = CURRENT_TIMESTAMP, estado = 'SALIO'
            WHERE id = :id
        """)
        session.execute(query, {"id": visitante_id})
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))