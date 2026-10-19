"""
Gestión Humana > Baja de activos (F-GT-BAJA-01).
Soporte completo para fechas nativas en PostgreSQL.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Baja, HerramientaInventario
from app.routers.gh_utils import generar_codigo

router = APIRouter(prefix="/api/gh/bajas", tags=["GH - Bajas"])

class BajaPayload(BaseModel):
    itemId: Optional[str] = None
    nombre: str
    categoria: Optional[str] = ""
    marca: Optional[str] = ""
    modelo: Optional[str] = ""
    serial: Optional[str] = ""
    cantidad: int = 1
    motivo: Optional[str] = "Fin de vida útil"
    disposicion: Optional[str] = "Chatarrización"
    entidad: Optional[str] = ""
    responsNombre: str
    responsCargo: Optional[str] = ""
    area: Optional[str] = ""
    observaciones: Optional[str] = ""
    firma: Optional[str] = ""
    config: Optional[Dict[str, Any]] = {}

@router.get("", response_model=List[Baja])
def listar(session: Session = Depends(get_session)):
    try:
        resultados = session.exec(select(Baja).order_by(Baja.id.desc())).all()
        return resultados
    except Exception:
        return []

@router.post("", response_model=Baja)
def crear(payload: BajaPayload, session: Session = Depends(get_session)):
    try:
        codigo = generar_codigo("BAJA")

        if payload.itemId:
            try:
                item_id_int = int(payload.itemId)
                item = session.get(HerramientaInventario, item_id_int)
                if item:
                    item.cantidad_stock = max(0, (item.cantidad_stock or 0) - abs(payload.cantidad or 1))
                    item.colaborador = ""
                    session.add(item)
            except Exception:
                pass

        baja = Baja(
            codigo=codigo,
            fecha=datetime.now(),  # <--- Inyección directa compatible con PostgreSQL
            item_id=str(payload.itemId) if payload.itemId else None,
            nombre=payload.nombre,
            categoria=payload.categoria or "",
            marca=payload.marca or "",
            modelo=payload.modelo or "",
            serial=payload.serial or "",
            cantidad=payload.cantidad or 1,
            motivo=payload.motivo or "Baja de activo",
            disposicion=payload.disposicion or "Chatarrización",
            entidad=payload.entidad or "",
            responsable_nombre=payload.responsNombre or "",
            responsable_cargo=payload.responsCargo or "",
            area=payload.area or "",
            observaciones=payload.observaciones or "",
            firma=payload.firma or "",
            status="registrado",
            config=payload.config or {},
            creado_en=datetime.now()
        )
        session.add(baja)
        session.commit()
        session.refresh(baja)
        return baja
    except Exception as e:
        session.rollback()
        # Devuelve el error exacto a la pantalla si PostgreSQL lo vuelve a rechazar
        raise HTTPException(status_code=500, detail=str(e))