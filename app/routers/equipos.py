"""
Rutas del módulo Hojas de Vida - Área de Sistemas.
CRUD completo + búsqueda avanzada + analítica + auditoría automática.
"""

from typing import Optional, List
import io
import csv

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.models import Equipo, HistorialCambio
from app.database import get_session
from app.services.equipo_service import EquipoService
from app.schemas.equipo import EquipoCreate, EquipoUpdate

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
# LISTAR
# ---------------------------------------------------------------------------

@router.get("", response_model=List[Equipo])
def listar_equipos(

    q: Optional[str] = None,
    empresa_id: Optional[int] = None,
    area: Optional[str] = None,
    estado_equipo: Optional[str] = None,

    session: Session = Depends(get_session),

):

    return EquipoService.listar(

        session=session,
        q=q,
        empresa_id=empresa_id,
        area=area,
        estado=estado_equipo,

    )

@router.get("/{equipo_id}", response_model=Equipo)
def obtener_equipo(
    equipo_id: int,
    session: Session = Depends(get_session),
):

    equipo = EquipoService.obtener(session, equipo_id)

    if not equipo:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado",
        )

    return equipo

# ---------------------------------------------------------------------------
# CREAR
# ---------------------------------------------------------------------------
@router.post("", response_model=Equipo)
def crear_equipo(
    datos: EquipoCreate,
    session: Session = Depends(get_session),
):

    try:
        return EquipoService.crear(
            session,
            datos,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# ACTUALIZAR
# ---------------------------------------------------------------------------

@router.put("/{equipo_id}", response_model=Equipo)
def actualizar_equipo(
    equipo_id: int,
    datos: EquipoUpdate,
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

    try:
        return EquipoService.actualizar(
            session,
            equipo,
            datos,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

# ---------------------------------------------------------------------------
# ELIMINAR (borrado + registro en bitácora, no se pierde el rastro)
# ---------------------------------------------------------------------------
@router.delete("/{equipo_id}")
def eliminar_equipo(
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

    EquipoService.eliminar(
        session,
        equipo,
    )

    return {
        "mensaje": "Equipo eliminado correctamente"
    }

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
def valores_filtros(
    session: Session = Depends(get_session),
):

    def valores(campo):

        statement = select(
            getattr(Equipo, campo)
        ).distinct()

        return sorted(

            [
                v
                for v in session.exec(statement).all()
                if v
            ]

        )

    return {

        "areas": valores("area"),

        "estados_equipo": valores("estado_equipo"),

        "tipos_equipo": valores("tipo_equipo"),

    }

# ---------------------------------------------------------------------------
# DASHBOARD ERP
# ---------------------------------------------------------------------------

@router.get("/dashboard")
def dashboard(
    session: Session = Depends(get_session),
):

    return {

        "total_equipos": EquipoService.total_equipos(session),

        "equipos_activos": EquipoService.equipos_activos(session),

        "mantenimientos_pendientes": len(
            EquipoService.mantenimientos_pendientes(session)
        ),

        "antivirus_vencidos": len(
            EquipoService.antivirus_vencidos(session)
        ),

        "garantias_vencidas": len(
            EquipoService.garantia_vencida(session)
        ),

        "sin_mantenimiento": len(
            EquipoService.equipos_sin_mantenimiento(session)
        ),

    }


# ---------------------------------------------------------------------------
# ALERTAS ANTIVIRUS
# ---------------------------------------------------------------------------

@router.get("/alertas/antivirus")
def antivirus_vencidos(
    session: Session = Depends(get_session),
):
    return EquipoService.antivirus_vencidos(session)


# ---------------------------------------------------------------------------
# ALERTAS GARANTÍA
# ---------------------------------------------------------------------------

@router.get("/alertas/garantias")
def garantias_vencidas(
    session: Session = Depends(get_session),
):
    return EquipoService.garantia_vencida(session)


# ---------------------------------------------------------------------------
# MANTENIMIENTOS
# ---------------------------------------------------------------------------

@router.get("/mantenimientos")
def mantenimientos(
    session: Session = Depends(get_session),
):
    return EquipoService.mantenimientos_pendientes(session)


# ---------------------------------------------------------------------------
# SIN MANTENIMIENTO
# ---------------------------------------------------------------------------

@router.get("/sin-mantenimiento")
def sin_mantenimiento(
    session: Session = Depends(get_session),
):
    return EquipoService.equipos_sin_mantenimiento(session)


# ---------------------------------------------------------------------------
# CONSULTAR POR EMPRESA
# ---------------------------------------------------------------------------

@router.get("/empresa/{empresa_id}")
def equipos_empresa(
    empresa_id: int,
    session: Session = Depends(get_session),
):
    return EquipoService.equipos_por_empresa(
        session,
        empresa_id,
    )


# ---------------------------------------------------------------------------
# CONSULTAR POR USUARIO
# ---------------------------------------------------------------------------

@router.get("/usuario/{usuario}")
def equipos_usuario(
    usuario: str,
    session: Session = Depends(get_session),
):
    return EquipoService.equipos_por_usuario(
        session,
        usuario,
    )


# ---------------------------------------------------------------------------
# CONSULTAR POR ÁREA
# ---------------------------------------------------------------------------

@router.get("/area/{area}")
def equipos_area(
    area: str,
    session: Session = Depends(get_session),
):
    return EquipoService.equipos_por_area(
        session,
        area,
    )


# ---------------------------------------------------------------------------
# BUSCADOR GLOBAL ERP
# ---------------------------------------------------------------------------

@router.get("/buscar")
def buscar(
    texto: str,
    session: Session = Depends(get_session),
):
    return EquipoService.buscar(
        session,
        texto,
    )

# ---------------------------------------------------------------------------
# EXPORTAR A CSV
# ---------------------------------------------------------------------------

@router.get("/exportar/csv")
def exportar_csv(
    session: Session = Depends(get_session),
):

    equipos = session.exec(
        select(Equipo)
    ).all()

    output = io.StringIO()

    if equipos:

        campos = list(equipos[0].dict().keys())

        writer = csv.DictWriter(
            output,
            fieldnames=campos,
        )

        writer.writeheader()

        for equipo in equipos:
            writer.writerow(equipo.dict())

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=equipos.csv"
        },
    )