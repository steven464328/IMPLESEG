from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session

from app.database import get_session

router = APIRouter(prefix="/api/hv", tags=["Hojas de Vida"])

class HVPayload(BaseModel):
    id: Optional[int] = None
    tipo_activo: str
    empresa: Optional[str] = "IMPLESEG"
    codigo: str
    nombre_equipo: str
    area: Optional[str] = ""
    usuario_asignado: Optional[str] = ""
    marca: Optional[str] = ""
    modelo: Optional[str] = ""
    serial: Optional[str] = ""
    procesador: Optional[str] = ""
    memoria: Optional[str] = ""
    disco: Optional[str] = ""
    mac: Optional[str] = ""
    ip: Optional[str] = ""
    sistema_operativo: Optional[str] = ""
    licencia_office: Optional[str] = ""
    antivirus: Optional[str] = ""
    linea_numero: Optional[str] = ""
    plan_datos: Optional[str] = ""
    imei: Optional[str] = ""
    tipo_linea: Optional[str] = ""
    estado: Optional[str] = "Activo"
    fecha_compra: Optional[str] = ""
    precio: Optional[float] = 0.0
    mantenimiento_programado: Optional[str] = ""
    observaciones: Optional[str] = ""

@router.get("/equipos")
def listar_equipos(session: Session = Depends(get_session)):
    query = text("SELECT * FROM hv_equipos ORDER BY id DESC")
    result = session.execute(query).mappings().all()
    return [dict(r) for r in result]

@router.post("/equipos")
def crear_equipo(payload: HVPayload, session: Session = Depends(get_session)):
    try:
        # 1. Guardar en Hojas de Vida
        insert_query = text("""
            INSERT INTO hv_equipos (
                tipo_activo, empresa, codigo, nombre_equipo, area, usuario_asignado,
                marca, modelo, serial, procesador, memoria, disco, mac, ip,
                sistema_operativo, licencia_office, antivirus, linea_numero,
                plan_datos, imei, tipo_linea, estado, fecha_compra, precio,
                mantenimiento_programado, observaciones, creado_en
            ) VALUES (
                :tipo_activo, :empresa, :codigo, :nombre_equipo, :area, :usuario_asignado,
                :marca, :modelo, :serial, :procesador, :memoria, :disco, :mac, :ip,
                :sistema_operativo, :licencia_office, :antivirus, :linea_numero,
                :plan_datos, :imei, :tipo_linea, :estado, :fecha_compra, :precio,
                :mantenimiento_programado, :observaciones, CURRENT_TIMESTAMP
            ) RETURNING id;
        """)
        
        datos = payload.dict(exclude_none=True)
        res = session.execute(insert_query, datos)
        nuevo_id = res.scalar()
        session.commit()

        # 2. AUTO-SINCRONIZACIÓN CON GESTIÓN HUMANA
        try:
            nombre_inv = payload.nombre_equipo if payload.tipo_activo != "CELULAR" else f"CELULAR {payload.marca} - {payload.linea_numero}"
            serial_inv = payload.serial if payload.tipo_activo != "CELULAR" else payload.imei
            
            sync_query = text("""
                INSERT INTO gh_inventario (nombre, categoria, marca, modelo, serial, cantidad_stock, descripcion)
                VALUES (:nombre, :categoria, :marca, :modelo, :serial, 1, :descripcion)
            """)
            session.execute(sync_query, {
                "nombre": nombre_inv,
                "categoria": "Portátil/Laptop" if payload.tipo_activo in ["LAPTOP", "PC", "AIO"] else "Otro",
                "marca": payload.marca,
                "modelo": payload.modelo,
                "serial": serial_inv,
                "descripcion": f"Auto-Sync Hojas de Vida. Cód: {payload.codigo}"
            })
            session.commit()
        except Exception as e_sync:
            session.rollback()

        return {"id": nuevo_id, "status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))