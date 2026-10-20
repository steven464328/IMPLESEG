from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Cookie
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session
from app.database import get_session

router = APIRouter(prefix="/api/usuarios", tags=["Seguridad y Roles"])

class UsuarioPayload(BaseModel):
    correo: str
    password: str
    rol: str
    modulos: str
    activo: bool = True

def validar_admin(sesion_erp: Optional[str] = Cookie(None), rol_erp: Optional[str] = Cookie(None)):
    if not sesion_erp or rol_erp != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requieren privilegios de Administrador.")
    return sesion_erp

# =======================================================
# RUTA DE AUTO-REPARACIÓN DE BASE DE DATOS
# =======================================================
@router.get("/fix-db")
def reparar_base_datos(session: Session = Depends(get_session)):
    try:
        session.execute(text("DROP TABLE IF EXISTS usuarios CASCADE;"))
        session.execute(text("""
            CREATE TABLE usuarios (
                id SERIAL PRIMARY KEY,
                correo VARCHAR UNIQUE NOT NULL,
                password VARCHAR NOT NULL,
                rol VARCHAR NOT NULL,
                modulos TEXT NOT NULL,
                activo BOOLEAN DEFAULT TRUE
            );
        """))
        session.commit()
        return {"mensaje": "✅ Tabla de usuarios reconstruida con éxito. Ya puedes volver al panel y crear los usuarios."}
    except Exception as e:
        session.rollback()
        return {"error": f"Fallo al reparar: {str(e)}"}

# =======================================================

@router.get("")
def listar_usuarios(session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    try:
        query = text("SELECT id, correo, rol, modulos, activo FROM usuarios ORDER BY id ASC")
        return [dict(r) for r in session.execute(query).mappings().all()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def crear_usuario(payload: UsuarioPayload, session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    if not payload.correo.endswith("@impleseg.com"):
        raise HTTPException(status_code=400, detail="Solo se permiten correos corporativos (@impleseg.com)")
    try:
        query = text("""
            INSERT INTO usuarios (correo, password, rol, modulos, activo)
            VALUES (:correo, :password, :rol, :modulos, :activo)
        """)
        session.execute(query, payload.dict())
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Fallo en BD: {str(e)}")

@router.delete("/{user_id}")
def eliminar_usuario(user_id: int, session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    if user_id == 1:
        raise HTTPException(status_code=400, detail="El administrador principal no puede ser eliminado.")
    try:
        session.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": user_id})
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
@router.put("/{user_id}/estado")
def cambiar_estado(user_id: int, session: Session = Depends(get_session), admin: str = Depends(validar_admin)):
    if user_id == 1:
        raise HTTPException(status_code=400, detail="No puedes desactivar al administrador principal.")
    try:
        session.execute(text("UPDATE usuarios SET activo = NOT activo WHERE id = :id"), {"id": user_id})
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))