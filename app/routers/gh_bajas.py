"""
Gestión Humana > Baja de activos (formato F-GT-BAJA-01).
Al registrar una baja se descuenta definitivamente el stock del inventario y se almacena la firma.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Baja, HerramientaInventario
from app.routers.gh_utils import generar_codigo, fecha_actual_texto

router = APIRouter(prefix="/api/gh/bajas", tags=["GH - Bajas"])


class BajaPayload(BaseModel):
    itemId: Optional[str] = None
    nombre: str
    categoria: Optional[str] = ""
    marca: Optional[str] = ""
    modelo: Optional[str] = ""
    serial: Optional[str] = ""
    cantidad: int = 1
    motivo: str
    disposicion: str
    entidad: Optional[str] = ""
    responsNombre: str
    responsCargo: Optional[str] = ""
    area: Optional[str] = ""
    observaciones: Optional[str] = ""
    firma: Optional[str] = ""
    config: Dict[str, Any] = {}


@router.get("", response_model=List[Baja])
def listar(session: Session = Depends(get_session)):
    try:
        resultados = session.exec(select(Baja)).all()
        return sorted(resultados, key=lambda b: getattr(b, "id", 0) or 0, reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error consultando bajas: {str(e)}")


@router.get("/{baja_id}", response_model=Baja)
def obtener(baja_id: int, session: Session = Depends(get_session)):
    b = session.get(Baja, baja_id)
    if not b:
        raise HTTPException(status_code=404, detail="Baja no encontrada")
    return b


@router.post("", response_model=Baja)
def crear(payload: BajaPayload, session: Session = Depends(get_session)):
    try:
        codigo = generar_codigo("BAJA")

        if payload.itemId:
            try:
                item_id_int = int(payload.itemId)
                item = session.get(HerramientaInventario, item_id_int)
                if item:
                    item.cantidad_stock = max(0, (item.cantidad_stock or 0) - abs(payload.cantidad))
                    item.colaborador = ""
                    session.add(item)
            except ValueError:
                pass

        baja = Baja(
            codigo=codigo, 
            fecha=fecha_actual_texto(), 
            item_id=payload.itemId,
            nombre=payload.nombre, 
            categoria=payload.categoria or "", 
            marca=payload.marca or "",
            modelo=payload.modelo or "", 
            serial=payload.serial or "", 
            cantidad=payload.cantidad,
            motivo=payload.motivo, 
            disposicion=payload.disposicion, 
            entidad=payload.entidad or "",
            responsable_nombre=payload.responsNombre, 
            responsable_cargo=payload.responsCargo or "",
            area=payload.area or "", 
            observaciones=payload.observaciones or "", 
            firma=payload.firma or "",
            status="registrado", 
            config=payload.config or {},
        )
        session.add(baja)
        session.commit()
        session.refresh(baja)
        return baja
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al registrar la baja: {str(e)}")