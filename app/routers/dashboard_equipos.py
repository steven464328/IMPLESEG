"""
Dashboard del módulo Hojas de Vida.
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.services.dashboard_equipo_service import DashboardEquipoService

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard Equipos"],
)


@router.get("/equipos")
def dashboard_equipos(
    session: Session = Depends(get_session),
):
    """
    Resumen general del módulo Hojas de Vida.
    """

    return DashboardEquipoService.resumen(session)