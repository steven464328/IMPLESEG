"""
Gestión Humana > Inventario de herramientas y equipos.

Funciones:
- Listar inventario.
- Filtrar por texto y categoría.
- Mostrar únicamente elementos disponibles.
- Crear un nuevo ítem.
- Actualizar automáticamente si existe el mismo nombre + serial.
- Editar un ítem existente.
- Eliminar un ítem.

El código interno se genera automáticamente en el modelo
HerramientaInventario y no debe ser diligenciado desde el frontend.
"""

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.database import get_session
from app.models import HerramientaInventario


router = APIRouter(
    prefix="/api/gh/inventario",
    tags=["GH - Inventario"],
)


# ============================================================
# LISTAR INVENTARIO
# ============================================================

@router.get("", response_model=List[HerramientaInventario])
def listar(
    q: Optional[str] = None,
    categoria: Optional[str] = None,
    solo_disponibles: bool = False,
    session: Session = Depends(get_session),
):
    """
    Lista los elementos del inventario.

    Filtros disponibles:
    - q: búsqueda por nombre, marca, modelo, serial o descripción.
    - categoria: filtra por categoría.
    - solo_disponibles: muestra únicamente registros con stock > 0.
    """

    statement = select(HerramientaInventario)

    if categoria:
        statement = statement.where(
            HerramientaInventario.categoria == categoria
        )

    if solo_disponibles:
        statement = statement.where(
            HerramientaInventario.cantidad_stock > 0
        )

    items = session.exec(statement).all()

    if q:
        ql = q.strip().lower()

        items = [
            item
            for item in items
            if ql in (item.nombre or "").lower()
            or ql in (item.categoria or "").lower()
            or ql in (item.marca or "").lower()
            or ql in (item.modelo or "").lower()
            or ql in (item.serial or "").lower()
            or ql in (item.descripcion or "").lower()
            or ql in (item.codigo or "").lower()
        ]

    return items


# ============================================================
# FILTROS / METADATOS
# ============================================================

@router.get("/meta/filtros")
def filtros(
    session: Session = Depends(get_session),
):
    """
    Devuelve las categorías utilizadas actualmente
    en el inventario.
    """

    items = session.exec(
        select(HerramientaInventario)
    ).all()

    categorias = sorted(
        {
            item.categoria.strip()
            for item in items
            if item.categoria and item.categoria.strip()
        }
    )

    return {
        "categorias": categorias,
    }


# ============================================================
# CREAR O ACTUALIZAR POR NOMBRE + SERIAL
# ============================================================

@router.post("", response_model=HerramientaInventario)
def crear_o_actualizar(
    item: HerramientaInventario,
    session: Session = Depends(get_session),
):
    """
    Si existe un ítem con el mismo nombre + serial, lo actualiza.

    Si no existe, crea un nuevo registro.

    El código interno nunca se modifica desde esta operación.
    """

    nombre = item.nombre.strip() if item.nombre else ""

    if not nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre del ítem es obligatorio.",
        )

    if item.cantidad_stock < 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad de stock no puede ser negativa.",
        )

    item.nombre = nombre

    if item.categoria:
        item.categoria = item.categoria.strip() or None

    if item.marca:
        item.marca = item.marca.strip() or None

    if item.modelo:
        item.modelo = item.modelo.strip() or None

    if item.serial:
        item.serial = item.serial.strip() or None

    if item.descripcion:
        item.descripcion = item.descripcion.strip() or None

    if item.colaborador:
        item.colaborador = item.colaborador.strip() or None

    if item.tipo:
        item.tipo = item.tipo.strip() or None

    if item.estado:
        item.estado = item.estado.strip() or "Disponible"

    existente = session.exec(
        select(HerramientaInventario).where(
            HerramientaInventario.nombre == item.nombre,
            HerramientaInventario.serial == item.serial,
        )
    ).first()

    if existente:
        datos = item.model_dump(
            exclude_unset=True,
            exclude={
                "id",
                "codigo",
            },
        )

        for campo, valor in datos.items():
            setattr(existente, campo, valor)

        session.add(existente)
        session.commit()
        session.refresh(existente)

        return existente

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


# ============================================================
# ACTUALIZAR POR ID
# ============================================================

@router.put("/{item_id}", response_model=HerramientaInventario)
def actualizar(
    item_id: int,
    datos: HerramientaInventario,
    session: Session = Depends(get_session),
):
    """
    Actualiza un registro existente.

    El ID y el código interno quedan protegidos.
    """

    item = session.get(
        HerramientaInventario,
        item_id,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Ítem no encontrado.",
        )

    if datos.nombre:
        datos.nombre = datos.nombre.strip()

    if not datos.nombre:
        raise HTTPException(
            status_code=400,
            detail="El nombre del ítem es obligatorio.",
        )

    if datos.cantidad_stock < 0:
        raise HTTPException(
            status_code=400,
            detail="La cantidad de stock no puede ser negativa.",
        )

    campos = datos.model_dump(
        exclude_unset=True,
        exclude={
            "id",
            "codigo",
        },
    )

    for campo, valor in campos.items():

        if isinstance(valor, str):
            valor = valor.strip() or None

        setattr(item, campo, valor)

    session.add(item)
    session.commit()
    session.refresh(item)

    return item


# ============================================================
# ELIMINAR
# ============================================================

@router.delete("/{item_id}")
def eliminar(
    item_id: int,
    session: Session = Depends(get_session),
):
    """
    Elimina un ítem del inventario.
    """

    item = session.get(
        HerramientaInventario,
        item_id,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Ítem no encontrado.",
        )

    session.delete(item)
    session.commit()

    return {
        "ok": True,
        "mensaje": "Ítem eliminado correctamente.",
    }