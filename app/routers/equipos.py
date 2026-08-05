"""
Rutas del módulo Hojas de Vida.
"""

from typing import List, Optional
import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.database import get_session
from app.models import Equipo, HistorialCambio
from app.schemas.equipo import EquipoCreate, EquipoUpdate
from app.services.equipo_service import EquipoService

router = APIRouter(
    prefix="/api/equipos",
    tags=["Equipos"],
)

# ==========================================================
# AUDITORÍA
# ==========================================================

def registrar_historial(
    session: Session,
    equipo_id: int,
    codigo: str,
    accion: str,
    campo: str = None,
    anterior: str = None,
    nuevo: str = None,
    usuario: str = None,
):

    registro = HistorialCambio(
        equipo_id=equipo_id,
        equipo_codigo=codigo,
        accion=accion,
        campo=campo,
        valor_anterior=anterior,
        valor_nuevo=nuevo,
        usuario=usuario,
    )

    session.add(registro)


# ==========================================================
# LISTAR
# ==========================================================

@router.get("", response_model=List[Equipo])
def listar_equipos(

    q: Optional[str] = None,
    empresa: Optional[str] = None,
    tipo_equipo: Optional[str] = None,
    area: Optional[str] = None,
    estado_equipo: Optional[str] = None,

    session: Session = Depends(get_session),

):

    return EquipoService.listar(

        session=session,
        q=q,
        empresa=empresa,
        tipo_equipo=tipo_equipo,
        area=area,
        estado=estado_equipo,

    )


# ==========================================================
# OBTENER
# ==========================================================

@router.get("/{equipo_id}", response_model=Equipo)
def obtener_equipo(

    equipo_id: int,
    session: Session = Depends(get_session),

):

    equipo = EquipoService.obtener(
        session,
        equipo_id,
    )

    if not equipo:

        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado",
        )

    return equipo


# ==========================================================
# CREAR
# ==========================================================

@router.post("", response_model=Equipo)
def crear_equipo(

    datos: EquipoCreate,
    session: Session = Depends(get_session),

):

    try:

        equipo = EquipoService.crear(
            session,
            datos,
        )

        registrar_historial(
            session=session,
            equipo_id=equipo.id,
            codigo=equipo.codigo,
            accion="CREAR",
        )

        session.commit()

        return equipo

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
"""
Rutas del módulo Hojas de Vida.
"""

from typing import List, Optional
import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.database import get_session
from app.models import Equipo, HistorialCambio
from app.schemas.equipo import EquipoCreate, EquipoUpdate
from app.services.equipo_service import EquipoService

router = APIRouter(
    prefix="/api/equipos",
    tags=["Equipos"],
)

# ==========================================================
# AUDITORÍA
# ==========================================================

def registrar_historial(
    session: Session,
    equipo_id: int,
    codigo: str,
    accion: str,
    campo: str = None,
    anterior: str = None,
    nuevo: str = None,
    usuario: str = None,
):

    registro = HistorialCambio(
        equipo_id=equipo_id,
        equipo_codigo=codigo,
        accion=accion,
        campo=campo,
        valor_anterior=anterior,
        valor_nuevo=nuevo,
        usuario=usuario,
    )

    session.add(registro)


# ==========================================================
# LISTAR
# ==========================================================

@router.get("", response_model=List[Equipo])
def listar_equipos(

    q: Optional[str] = None,
    empresa: Optional[str] = None,
    tipo_equipo: Optional[str] = None,
    area: Optional[str] = None,
    estado_equipo: Optional[str] = None,

    session: Session = Depends(get_session),

):

    return EquipoService.listar(

        session=session,
        q=q,
        empresa=empresa,
        tipo_equipo=tipo_equipo,
        area=area,
        estado=estado_equipo,

    )


# ==========================================================
# OBTENER
# ==========================================================

@router.get("/{equipo_id}", response_model=Equipo)
def obtener_equipo(

    equipo_id: int,
    session: Session = Depends(get_session),

):

    equipo = EquipoService.obtener(
        session,
        equipo_id,
    )

    if not equipo:

        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado",
        )

    return equipo


# ==========================================================
# CREAR
# ==========================================================

@router.post("", response_model=Equipo)
def crear_equipo(

    datos: EquipoCreate,
    session: Session = Depends(get_session),

):

    try:

        equipo = EquipoService.crear(
            session,
            datos,
        )

        registrar_historial(
            session=session,
            equipo_id=equipo.id,
            codigo=equipo.codigo,
            accion="CREAR",
        )

        session.commit()

        return equipo

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )