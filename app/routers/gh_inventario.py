"""
Gestión Humana > Inventario de herramientas y equipos.
Mismo comportamiento que 'saveInventoryItem' / 'deleteInventoryItem' del
Apps Script original: si existe un ítem con el mismo nombre+serial, lo
actualiza; si no, crea uno nuevo con ID autoincremental.
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import HerramientaInventario

router = APIRouter(prefix="/api/gh/inventario", tags=["GH - Inventario"])


@router.get("", response_model=List[HerramientaInventario])
def listar(q: Optional[str] = None, categoria: Optional[str] = None,
           solo_disponibles: bool = False, session: Session = Depends(get_session)):
    statement = select(HerramientaInventario)
    if categoria:
        statement = statement.where(HerramientaInventario.categoria == categoria)
    if solo_disponibles:
        statement = statement.where(HerramientaInventario.cantidad_stock > 0)
    items = session.exec(statement).all()
    if q:
        ql = q.lower()
        items = [i for i in items if ql in (i.nombre or "").lower()
                 or ql in (i.marca or "").lower() or ql in (i.serial or "").lower()
                 or ql in (i.modelo or "").lower()]
    return items


@router.get("/meta/filtros")
def filtros(session: Session = Depends(get_session)):
    items = session.exec(select(HerramientaInventario)).all()
    categorias = sorted({i.categoria for i in items if i.categoria})
    return {"categorias": categorias}


@router.post("", response_model=HerramientaInventario)
def crear_o_actualizar(item: HerramientaInventario, session: Session = Depends(get_session)):
    existente = session.exec(
        select(HerramientaInventario).where(
            HerramientaInventario.nombre == item.nombre,
            HerramientaInventario.serial == item.serial,
        )
    ).first()

    if existente:
        datos = item.dict(exclude_unset=True, exclude={"id"})
        for k, v in datos.items():
            setattr(existente, k, v)
        session.add(existente)
        session.commit()
        session.refresh(existente)
        return existente

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{item_id}", response_model=HerramientaInventario)
def actualizar(item_id: int, datos: HerramientaInventario, session: Session = Depends(get_session)):
    item = session.get(HerramientaInventario, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    for k, v in datos.dict(exclude_unset=True, exclude={"id"}).items():
        setattr(item, k, v)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{item_id}")
def eliminar(item_id: int, session: Session = Depends(get_session)):
    item = session.get(HerramientaInventario, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    session.delete(item)
    session.commit()
    return {"ok": True}
