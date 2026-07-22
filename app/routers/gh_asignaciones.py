"""
Gestión Humana > Asignaciones de herramientas (formato F-SGI-GH-12).

Esta es la lógica más delicada del sistema original, portada 1:1:
- Al CREAR una asignación: se descuenta el stock de cada ítem vinculado al
  inventario y se marca el colaborador en ese ítem.
- Al EDITAR: se detectan automáticamente los ítems retirados (se les
  devuelve el stock) y los nuevos ítems agregados (se les descuenta), y
  cada cambio queda anotado en el historial del acta con su propia firma.
- Al RECIBIR (recepción/devolución): se reintegra el stock de todos los
  ítems devueltos y el acta pasa a estado 'devuelto'.
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Asignacion, HerramientaInventario
from app.routers.gh_utils import generar_codigo, fecha_actual_texto

router = APIRouter(prefix="/api/gh/asignaciones", tags=["GH - Asignaciones"])


# ---------------------------------------------------------------------------
# Esquemas de entrada
# ---------------------------------------------------------------------------
class ItemAsignado(BaseModel):
    herramienta: str
    marca: Optional[str] = ""
    serialOriginal: Optional[str] = ""
    cantidad: int = 1
    estado: Optional[str] = "Bueno"
    observaciones: Optional[str] = ""
    fecha: Optional[str] = ""


class CrearAsignacionPayload(BaseModel):
    nombre: str
    cedula: str
    cargo: Optional[str] = ""
    area: Optional[str] = ""
    items: List[ItemAsignado]
    firmaRecibe: Optional[str] = ""
    firmaEntrega: Optional[str] = ""
    docUrl: Optional[str] = ""


class NuevoHistorial(BaseModel):
    herramienta: str
    nota: str
    firmaR: Optional[str] = ""
    firmaE: Optional[str] = ""


class ActualizarAsignacionPayload(BaseModel):
    nombre: str
    cedula: str
    cargo: Optional[str] = ""
    area: Optional[str] = ""
    items: List[ItemAsignado]
    nuevosHistoriales: List[NuevoHistorial] = []
    firmaR_base: Optional[str] = None
    firmaE_base: Optional[str] = None


class RecepcionPayload(BaseModel):
    items: List[dict]
    firmaRecibe: str
    firmaEntrega: Optional[str] = ""


# ---------------------------------------------------------------------------
# Utilidad: ajustar stock buscando por nombre (+serial si se tiene)
# ---------------------------------------------------------------------------
def _buscar_item_inventario(session: Session, nombre: str, serial: str = ""):
    statement = select(HerramientaInventario).where(HerramientaInventario.nombre == nombre)
    candidatos = session.exec(statement).all()
    if not candidatos:
        return None
    if serial:
        for c in candidatos:
            if (c.serial or "") == serial:
                return c
    return candidatos[0]


def _ajustar_stock(session: Session, herramienta: str, serial: str, delta: int, colaborador: Optional[str]):
    item = _buscar_item_inventario(session, herramienta, serial)
    if not item:
        return
    item.cantidad_stock = max(0, (item.cantidad_stock or 0) + delta)
    item.colaborador = colaborador or ""
    session.add(item)


# ---------------------------------------------------------------------------
# LISTAR / CONSULTAR
# ---------------------------------------------------------------------------
@router.get("", response_model=List[Asignacion])
def listar(status: Optional[str] = None, q: Optional[str] = None,
           session: Session = Depends(get_session)):
    statement = select(Asignacion)
    if status:
        statement = statement.where(Asignacion.status == status)
    resultados = session.exec(statement).all()
    if q:
        ql = q.lower()
        resultados = [a for a in resultados if ql in (a.nombre or "").lower()
                      or ql in (a.cedula or "") or ql in (a.area or "").lower()
                      or ql in (a.codigo or "").lower()]
    return sorted(resultados, key=lambda a: a.id, reverse=True)


@router.get("/{asignacion_id}", response_model=Asignacion)
def obtener(asignacion_id: int, session: Session = Depends(get_session)):
    a = session.get(Asignacion, asignacion_id)
    if not a:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return a


# ---------------------------------------------------------------------------
# CREAR (equivalente a saveAsignacion)
# ---------------------------------------------------------------------------
@router.post("", response_model=Asignacion)
def crear(payload: CrearAsignacionPayload, session: Session = Depends(get_session)):
    codigo = generar_codigo("ASG")
    items_dict = [it.dict() for it in payload.items]

    for it in items_dict:
        if it.get("herramienta"):
            _ajustar_stock(session, it["herramienta"], it.get("serialOriginal", ""),
                           -abs(int(it.get("cantidad") or 1)), payload.nombre)

    asignacion = Asignacion(
        codigo=codigo, nombre=payload.nombre, cedula=payload.cedula, cargo=payload.cargo,
        area=payload.area, fecha=fecha_actual_texto(), items=items_dict,
        firma_recibe=payload.firmaRecibe or "", firma_entrega=payload.firmaEntrega or "",
        status="activo", doc_url=payload.docUrl or "",
    )
    session.add(asignacion)
    session.commit()
    session.refresh(asignacion)
    return asignacion


# ---------------------------------------------------------------------------
# ACTUALIZAR (equivalente a updateAsignacion — el más complejo)
# ---------------------------------------------------------------------------
@router.put("/{asignacion_id}", response_model=Asignacion)
def actualizar(asignacion_id: int, payload: ActualizarAsignacionPayload,
               session: Session = Depends(get_session)):
    a = session.get(Asignacion, asignacion_id)
    if not a:
        raise HTTPException(status_code=404, detail="Acta no encontrada")

    items_anteriores = a.items or []
    items_nuevos = [it.dict() for it in payload.items]

    nombres_anteriores = {it["herramienta"] for it in items_anteriores}
    nombres_nuevos = {it["herramienta"] for it in items_nuevos}

    # Ítems retirados -> reintegrar stock, liberar colaborador
    for it in items_anteriores:
        if it["herramienta"] not in nombres_nuevos:
            _ajustar_stock(session, it["herramienta"], it.get("serialOriginal", ""),
                           abs(int(it.get("cantidad") or 1)), None)

    # Ítems nuevos -> descontar stock, asignar colaborador
    for it in items_nuevos:
        if it["herramienta"] not in nombres_anteriores:
            _ajustar_stock(session, it["herramienta"], it.get("serialOriginal", ""),
                           -abs(int(it.get("cantidad") or 1)), payload.nombre)

    # Anotar historial
    historial = a.historial or []
    fecha_mod = fecha_actual_texto()
    for nh in payload.nuevosHistoriales:
        if nh.nota:
            historial.append({
                "fecha": fecha_mod, "herramienta": nh.herramienta, "nota": nh.nota,
                "firmaR": nh.firmaR or "", "firmaE": nh.firmaE or "",
            })

    a.nombre = payload.nombre
    a.cedula = payload.cedula
    a.cargo = payload.cargo
    a.area = payload.area
    a.items = items_nuevos
    a.historial = historial
    a.actualizado_en = datetime.utcnow()

    if payload.firmaR_base is not None:
        a.firma_recibe = payload.firmaR_base
    if payload.firmaE_base is not None:
        a.firma_entrega = payload.firmaE_base

    session.add(a)
    session.commit()
    session.refresh(a)
    return a


# ---------------------------------------------------------------------------
# RECEPCIÓN / DEVOLUCIÓN (equivalente a saveRecepcion)
# ---------------------------------------------------------------------------
@router.post("/{asignacion_id}/recepcion", response_model=Asignacion)
def recibir(asignacion_id: int, payload: RecepcionPayload, session: Session = Depends(get_session)):
    a = session.get(Asignacion, asignacion_id)
    if not a:
        raise HTTPException(status_code=404, detail="Acta no encontrada")

    for it in payload.items:
        _ajustar_stock(session, it.get("herramienta", ""), it.get("serialOriginal", ""),
                       abs(int(it.get("cantidad") or 1)), None)

    a.status = "devuelto"
    a.fecha_dev = datetime.now().strftime("%d/%m/%Y")
    a.items_dev = payload.items
    a.firma_recibe_dev = payload.firmaRecibe
    a.firma_entrega_dev = payload.firmaEntrega or ""
    a.actualizado_en = datetime.utcnow()

    session.add(a)
    session.commit()
    session.refresh(a)
    return a


# ---------------------------------------------------------------------------
# Listar pendientes de recepción (equivalente al filtro de vRec())
# ---------------------------------------------------------------------------
@router.get("/pendientes/recepcion", response_model=List[Asignacion])
def pendientes_recepcion(q: Optional[str] = None, session: Session = Depends(get_session)):
    statement = select(Asignacion).where(Asignacion.status != "devuelto")
    resultados = session.exec(statement).all()
    if q:
        ql = q.lower()
        resultados = [a for a in resultados if ql in (a.nombre or "").lower() or ql in (a.cedula or "")]
    return resultados
