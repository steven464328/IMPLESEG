"""
Rutas del módulo Hojas de Vida - Área de Sistemas.
CRUD completo + búsqueda avanzada + analítica + auditoría automática.
"""
from datetime import datetime, date
from typing import Optional, List
import io
import csv

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, or_, func

from app.database import get_session
from app.models import Equipo, Empresa, HistorialCambio

router = APIRouter(prefix="/api/equipos", tags=["Equipos"])


# ---------------------------------------------------------------------------
# Utilidad interna: registra en la bitácora cada cambio (auditoría automática)
# ---------------------------------------------------------------------------
def _registrar_historial(session: Session, equipo_id: int, codigo: str, accion: str,
                          campo: str = None, anterior: str = None, nuevo: str = None,
                          usuario: str = None):
    registro = HistorialCambio(
        equipo_id=equipo_id, equipo_codigo=codigo, accion=accion,
        campo=campo, valor_anterior=anterior, valor_nuevo=nuevo, usuario=usuario,
    )
    session.add(registro)


# ---------------------------------------------------------------------------
# LISTAR / BUSCAR (con filtros combinables — lógica de consulta robusta)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[Equipo])
def listar_equipos(
    q: Optional[str] = Query(None, description="Búsqueda libre en varios campos"),
    empresa: Optional[str] = None,
    area: Optional[str] = None,
    tipo_equipo: Optional[str] = None,
    estado_equipo: Optional[str] = None,
    usuario_asignado: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
    session: Session = Depends(get_session),
):
    statement = select(Equipo)

    if empresa:
        statement = statement.where(Equipo.empresa == empresa)
    if area:
        statement = statement.where(Equipo.area == area)
    if tipo_equipo:
        statement = statement.where(Equipo.tipo_equipo == tipo_equipo)
    if estado_equipo:
        statement = statement.where(Equipo.estado_equipo == estado_equipo)
    if usuario_asignado:
        statement = statement.where(Equipo.usuario_asignado.ilike(f"%{usuario_asignado}%"))

    if q:
        like = f"%{q}%"
        statement = statement.where(
            or_(
                Equipo.equipo.ilike(like),
                Equipo.codigo.ilike(like),
                Equipo.nombre_equipo.ilike(like),
                Equipo.usuario_asignado.ilike(like),
                Equipo.serial.ilike(like),
                Equipo.ip.ilike(like),
                Equipo.marca.ilike(like),
                Equipo.area.ilike(like),
            )
        )

    statement = statement.offset(offset).limit(limit)
    return session.exec(statement).all()


# ---------------------------------------------------------------------------
# OBTENER UNO
# ---------------------------------------------------------------------------
@router.get("/{equipo_id}", response_model=Equipo)
def obtener_equipo(equipo_id: int, session: Session = Depends(get_session)):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo


# ---------------------------------------------------------------------------
# CREAR
# ---------------------------------------------------------------------------
@router.post("", response_model=Equipo)
def crear_equipo(equipo: Equipo, usuario: Optional[str] = Query(None), session: Session = Depends(get_session)):
    existente = session.exec(select(Equipo).where(Equipo.equipo == equipo.equipo)).first()
    if existente:
        raise HTTPException(status_code=409, detail=f"Ya existe un equipo con código '{equipo.equipo}'")

    equipo.creado_en = datetime.utcnow()
    equipo.actualizado_en = datetime.utcnow()
    equipo.creado_por = usuario
    equipo.actualizado_por = usuario

    session.add(equipo)
    session.commit()
    session.refresh(equipo)

    _registrar_historial(session, equipo.id, equipo.equipo, "CREACION", usuario=usuario)
    session.commit()
    return equipo


# ---------------------------------------------------------------------------
# ACTUALIZAR (registra diffs campo a campo en la bitácora)
# ---------------------------------------------------------------------------
@router.put("/{equipo_id}", response_model=Equipo)
def actualizar_equipo(equipo_id: int, datos: Equipo, usuario: Optional[str] = Query(None),
                       session: Session = Depends(get_session)):
    equipo_db = session.get(Equipo, equipo_id)
    if not equipo_db:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    nuevos = datos.dict(exclude_unset=True, exclude={"id", "creado_en", "creado_por"})
    for campo, valor_nuevo in nuevos.items():
        valor_anterior = getattr(equipo_db, campo)
        if valor_anterior != valor_nuevo:
            _registrar_historial(
                session, equipo_id, equipo_db.equipo, "MODIFICACION",
                campo=campo, anterior=str(valor_anterior), nuevo=str(valor_nuevo), usuario=usuario,
            )
        setattr(equipo_db, campo, valor_nuevo)

    equipo_db.actualizado_en = datetime.utcnow()
    equipo_db.actualizado_por = usuario

    session.add(equipo_db)
    session.commit()
    session.refresh(equipo_db)
    return equipo_db


# ---------------------------------------------------------------------------
# ELIMINAR (borrado + registro en bitácora, no se pierde el rastro)
# ---------------------------------------------------------------------------
@router.delete("/{equipo_id}")
def eliminar_equipo(equipo_id: int, usuario: Optional[str] = Query(None), session: Session = Depends(get_session)):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    _registrar_historial(session, equipo_id, equipo.equipo, "ELIMINACION", usuario=usuario)
    session.delete(equipo)
    session.commit()
    return {"ok": True, "mensaje": f"Equipo '{equipo.equipo}' eliminado correctamente"}


# ---------------------------------------------------------------------------
# HISTORIAL / AUDITORÍA de un equipo puntual
# ---------------------------------------------------------------------------
@router.get("/{equipo_id}/historial", response_model=List[HistorialCambio])
def historial_equipo(equipo_id: int, session: Session = Depends(get_session)):
    statement = select(HistorialCambio).where(HistorialCambio.equipo_id == equipo_id).order_by(HistorialCambio.fecha.desc())
    return session.exec(statement).all()


# ---------------------------------------------------------------------------
# VALORES ÚNICOS PARA FILTROS DINÁMICOS (poblar selects del frontend)
# ---------------------------------------------------------------------------
@router.get("/meta/filtros")
def valores_filtros(session: Session = Depends(get_session)):
    def valores(campo):
        statement = select(getattr(Equipo, campo)).distinct()
        return sorted([v for v in session.exec(statement).all() if v])

    return {
        "empresas": valores("empresa"),
        "areas": valores("area"),
        "tipos_equipo": valores("tipo_equipo"),
        "estados_equipo": valores("estado_equipo"),
    }


# ---------------------------------------------------------------------------
# EXPORTAR A CSV (compatible con Excel / Google Sheets)
# ---------------------------------------------------------------------------
@router.get("/exportar/csv")
def exportar_csv(session: Session = Depends(get_session)):
    equipos = session.exec(select(Equipo)).all()
    output = io.StringIO()
    if equipos:
        campos = [c for c in equipos[0].dict().keys() if c not in ("checklist_software", "extra_data")]
        writer = csv.DictWriter(output, fieldnames=campos)
        writer.writeheader()
        for e in equipos:
            fila = {k: v for k, v in e.dict().items() if k in campos}
            writer.writerow(fila)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=hojas_de_vida_export.csv"},
    )
