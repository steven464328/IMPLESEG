"""
Dashboard analítico del módulo Hojas de Vida.
"""

from collections import Counter
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Equipo

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)

PALABRAS_CLAVE_RIESGO = [
    "LENTO",
    "DAÑADO",
    "FALLA",
    "SIN MEMORIAS",
    "CHATARR",
]


# ==========================================================
# UTILIDADES
# ==========================================================

def _parsear_precio(valor: Optional[str]) -> float:

    if not valor:
        return 0.0

    s = "".join(
        ch
        for ch in str(valor).strip()
        if ch.isdigit() or ch in ".,"
    )

    if not s:
        return 0.0

    if "," in s and "." in s:

        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")

        else:
            s = s.replace(",", "")

    elif "," in s:

        partes = s.split(",")

        if len(partes[-1]) == 2:
            s = s.replace(",", ".")

        else:
            s = s.replace(",", "")

    elif "." in s:

        partes = s.split(".")

        if len(partes[-1]) != 2:
            s = s.replace(".", "")

    try:
        valor_final = float(s)

    except ValueError:
        return 0.0

    if valor_final > 200_000_000:
        return 0.0

    return valor_final


# ==========================================================
# DASHBOARD
# ==========================================================

@router.get("/resumen")
def resumen_general(

    empresa: Optional[str] = None,
    session: Session = Depends(get_session),

):

    statement = select(Equipo)

    if empresa:
        statement = statement.where(
            Equipo.empresa == empresa
        )

    equipos = session.exec(statement).all()

    total = len(equipos)

    por_area = Counter(
        e.area or "SIN ÁREA"
        for e in equipos
    )

    por_estado = Counter(
        e.estado_equipo or "SIN ESTADO"
        for e in equipos
    )

    por_tipo = Counter(
        e.tipo_equipo or "SIN TIPO"
        for e in equipos
    )

    por_empresa = Counter(
        e.empresa or "SIN EMPRESA"
        for e in equipos
    )

    por_marca = Counter(
        e.marca or "SIN MARCA"
        for e in equipos
    )

    por_so = Counter(
        e.sistema_operativo or "SIN SO"
        for e in equipos
    )

    # ------------------------------------------------------

    equipos_en_riesgo = []

    for equipo in equipos:

        texto = (
            f"{equipo.estado_equipo or ''} "
            f"{equipo.observacion_estado or ''} "
            f"{equipo.observacion_general or ''}"
        ).upper()

        if any(
            palabra in texto
            for palabra in PALABRAS_CLAVE_RIESGO
        ):

            equipos_en_riesgo.append({

                "id": equipo.id,
                "equipo": equipo.equipo,
                "usuario_asignado": equipo.usuario_asignado,
                "area": equipo.area,
                "estado_equipo": equipo.estado_equipo,
                "motivo": equipo.observacion_estado
                          or equipo.observacion_general,

            })

    # ------------------------------------------------------

    sin_mantenimiento = [

        {

            "id": equipo.id,
            "equipo": equipo.equipo,
            "area": equipo.area,
            "usuario_asignado": equipo.usuario_asignado,

        }

        for equipo in equipos

        if not equipo.fecha_ultimo_mantenimiento

    ]

    valor_total = sum(

        _parsear_precio(
            equipo.compra_precio_total
        )

        for equipo in equipos

    )

    return {

        "total_equipos": total,

        "por_area":
            dict(por_area.most_common()),

        "por_estado":
            dict(por_estado.most_common()),

        "por_tipo_equipo":
            dict(por_tipo.most_common()),

        "por_empresa":
            dict(por_empresa.most_common()),

        "por_marca":
            dict(por_marca.most_common(10)),

        "por_sistema_operativo":
            dict(por_so.most_common()),

        "equipos_en_riesgo":
            equipos_en_riesgo,

        "total_en_riesgo":
            len(equipos_en_riesgo),

        "equipos_sin_mantenimiento_registrado":
            len(sin_mantenimiento),

        "detalle_sin_mantenimiento":
            sin_mantenimiento[:25],

        "valor_estimado_parque_equipos":
            round(valor_total, 2),

        "generado_en":
            datetime.utcnow().isoformat(),

    }