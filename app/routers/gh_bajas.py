"""
Gestión Humana > Baja de activos (F-GT-BAJA-01).
Utiliza RAW SQL para garantizar compatibilidad absoluta con PostgreSQL.
"""
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session
from sqlalchemy import text

from app.database import get_session
from app.models import HerramientaInventario
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

@router.get("")
def listar(session: Session = Depends(get_session)):
    try:
        # RAW SQL: Lee la tabla directamente sin importar el esquema Pydantic
        query = text("SELECT * FROM gh_bajas ORDER BY id DESC")
        result = session.execute(query).mappings().all()
        bajas = []
        for r in result:
            row = dict(r)
            if isinstance(row.get("config"), str):
                try:
                    row["config"] = json.loads(row["config"])
                except:
                    row["config"] = {}
            bajas.append(row)
        return bajas
    except Exception as e:
        print(f"Error forzado leyendo bajas: {e}")
        return []

@router.post("")
def crear(payload: BajaPayload, session: Session = Depends(get_session)):
    try:
        codigo = generar_codigo("BAJA")
        fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Descuento en inventario
        if payload.itemId:
            try:
                item = session.get(HerramientaInventario, int(payload.itemId))
                if item:
                    item.cantidad_stock = max(0, (item.cantidad_stock or 0) - abs(payload.cantidad or 1))
                    item.colaborador = ""
                    session.add(item)
            except Exception:
                pass

        config_json = json.dumps(payload.config or {})

        # RAW SQL INSERT: Garantiza que PostgreSQL lo reciba correctamente
        insert_query = text("""
            INSERT INTO gh_bajas (
                codigo, fecha, item_id, nombre, categoria, marca, modelo, serial, 
                cantidad, motivo, disposicion, entidad, responsable_nombre, 
                responsable_cargo, area, observaciones, firma, status, config, creado_en
            ) VALUES (
                :codigo, :fecha, :item_id, :nombre, :categoria, :marca, :modelo, :serial,
                :cantidad, :motivo, :disposicion, :entidad, :responsable_nombre,
                :responsable_cargo, :area, :observaciones, :firma, :status, :config, CURRENT_TIMESTAMP
            ) RETURNING id;
        """)
        
        result = session.execute(insert_query, {
            "codigo": codigo, "fecha": fecha_str, "item_id": str(payload.itemId) if payload.itemId else None,
            "nombre": payload.nombre, "categoria": payload.categoria or "", "marca": payload.marca or "",
            "modelo": payload.modelo or "", "serial": payload.serial or "", "cantidad": payload.cantidad or 1,
            "motivo": payload.motivo or "", "disposicion": payload.disposicion or "", "entidad": payload.entidad or "",
            "responsable_nombre": payload.responsNombre or "", "responsable_cargo": payload.responsCargo or "",
            "area": payload.area or "", "observaciones": payload.observaciones or "", "firma": payload.firma or "",
            "status": "registrado", "config": config_json
        })
        
        new_id = result.scalar()
        session.commit()
        
        return {
            "id": new_id, "codigo": codigo, "fecha": fecha_str, "nombre": payload.nombre,
            "cantidad": payload.cantidad, "motivo": payload.motivo, "responsable_nombre": payload.responsNombre,
            "firma": payload.firma, "config": payload.config, "observaciones": payload.observaciones
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error crítico en base de datos: {str(e)}")