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
    # 1. CIERRE AUTOMÁTICO (9:00 PM en adelante o días anteriores)
    query_cierre = text("""
        UPDATE registro_visitantes 
        SET estado = 'SALIDA AUTO', hora_salida = CURRENT_TIMESTAMP
        WHERE estado = 'DENTRO' 
        AND (EXTRACT(HOUR FROM CURRENT_TIMESTAMP) >= 21 OR DATE(hora_entrada) < CURRENT_DATE);
    """)
    session.execute(query_cierre)
    session.commit()

    # 2. Obtener la lista actualizada
    query = text("SELECT * FROM registro_visitantes ORDER BY id DESC")
    result = session.execute(query).mappings().all()
    return [dict(r) for r in result]

@router.get("/buscar/{cedula}")
def buscar_visitante(cedula: str, session: Session = Depends(get_session)):
    # AUTOCOMPLETADO: Busca si la cédula ya existe para traer sus datos
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
    # Función para que el admin le de salida a alguien desde el panel
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