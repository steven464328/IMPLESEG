from typing import List, Optional
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

        # Sincronización con Gestión Humana
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
                "descripcion": f"Auto-Sync HV. Cód: {payload.codigo}"
            })
            session.commit()
        except Exception:
            session.rollback() # Ignora fallo de sync si ya guardó HV

        return {"id": nuevo_id, "status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/equipos/{equipo_id}")
def editar_equipo(equipo_id: int, payload: HVPayload, session: Session = Depends(get_session)):
    try:
        update_query = text("""
            UPDATE hv_equipos SET 
                codigo=:codigo, nombre_equipo=:nombre_equipo, area=:area, usuario_asignado=:usuario_asignado,
                marca=:marca, modelo=:modelo, serial=:serial, procesador=:procesador, memoria=:memoria, 
                disco=:disco, mac=:mac, ip=:ip, sistema_operativo=:sistema_operativo, 
                licencia_office=:licencia_office, antivirus=:antivirus, linea_numero=:linea_numero, 
                plan_datos=:plan_datos, imei=:imei, tipo_linea=:tipo_linea, estado=:estado, 
                mantenimiento_programado=:mantenimiento_programado, observaciones=:observaciones
            WHERE id = :id
        """)
        datos = payload.dict(exclude_none=True)
        datos["id"] = equipo_id
        session.execute(update_query, datos)
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/equipos/{equipo_id}")
def eliminar_equipo(equipo_id: int, session: Session = Depends(get_session)):
    try:
        session.execute(text("DELETE FROM hv_equipos WHERE id = :id"), {"id": equipo_id})
        session.commit()
        return {"status": "ok"}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))