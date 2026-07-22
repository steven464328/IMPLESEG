"""
Módulo de analítica: convierte los datos crudos de las hojas de vida en
indicadores accionables para el área de sistemas.
"""
from collections import Counter
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.database import get_session
from app.models import Equipo

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

PALABRAS_CLAVE_RIESGO = ["LENTO", "DAÑADO", "FALLA", "SIN MEMORIAS", "CHATARR"]


def _parsear_precio(valor: Optional[str]) -> float:
    """Convierte texto de precio (formato colombiano, con puntos de miles y/o
    comas decimales) a número. Si el resultado es absurdamente alto para un
    solo equipo, se descarta como dato mal diligenciado en vez de inflar el total."""
    if not valor:
        return 0.0
    s = "".join(ch for ch in str(valor).strip() if ch.isdigit() or ch in ".,")
    if not s:
        return 0.0

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        partes = s.split(",")
        s = s.replace(",", ".") if len(partes[-1]) == 2 else s.replace(",", "")
    elif "." in s:
        partes = s.split(".")
        if len(partes[-1]) != 2:
            s = s.replace(".", "")

    try:
        val = float(s)
    except ValueError:
        return 0.0

    # Un solo equipo no debería costar más de ~200 millones COP: si supera
    # eso, es texto mal interpretado (seriales, fechas, etc.), se descarta.
    return val if 0 <= val <= 200_000_000 else 0.0


@router.get("/resumen")
def resumen_general(empresa: Optional[str] = None, session: Session = Depends(get_session)):
    statement = select(Equipo)
    if empresa:
        statement = statement.where(Equipo.empresa == empresa)
    equipos = session.exec(statement).all()

    total = len(equipos)
    por_area = Counter(e.area or "SIN ÁREA" for e in equipos)
    por_estado = Counter(e.estado_equipo or "SIN ESTADO" for e in equipos)
    por_tipo = Counter(e.tipo_equipo or "SIN TIPO" for e in equipos)
    por_empresa = Counter(e.empresa or "SIN EMPRESA" for e in equipos)
    por_marca = Counter(e.marca or "SIN MARCA" for e in equipos)
    por_so = Counter(e.sistema_operativo or "SIN SO" for e in equipos)

    # --- Detección de riesgo: equipos que requieren atención pronto ---
    en_riesgo = []
    for e in equipos:
        texto_riesgo = f"{e.estado_equipo or ''} {e.observacion_estado or ''} {e.observacion_general or ''}".upper()
        if any(palabra in texto_riesgo for palabra in PALABRAS_CLAVE_RIESGO):
            en_riesgo.append({
                "id": e.id, "equipo": e.equipo, "usuario_asignado": e.usuario_asignado,
                "area": e.area, "estado_equipo": e.estado_equipo,
                "motivo": e.observacion_estado or e.observacion_general,
            })

    # --- Equipos sin mantenimiento registrado (posible deuda técnica) ---
    sin_mantenimiento = [
        {"id": e.id, "equipo": e.equipo, "area": e.area, "usuario_asignado": e.usuario_asignado}
        for e in equipos if not e.fecha_ultimo_mantenimiento
    ]

    # --- Proyección financiera del parque de equipos ---
    valor_total_activos = sum(_parsear_precio(e.compra_precio_total) for e in equipos)

    return {
        "total_equipos": total,
        "por_area": dict(por_area.most_common()),
        "por_estado": dict(por_estado.most_common()),
        "por_tipo_equipo": dict(por_tipo.most_common()),
        "por_empresa": dict(por_empresa.most_common()),
        "por_marca": dict(por_marca.most_common(10)),
        "por_sistema_operativo": dict(por_so.most_common()),
        "equipos_en_riesgo": en_riesgo,
        "total_en_riesgo": len(en_riesgo),
        "equipos_sin_mantenimiento_registrado": len(sin_mantenimiento),
        "detalle_sin_mantenimiento": sin_mantenimiento[:25],
        "valor_estimado_parque_equipos": round(valor_total_activos, 2),
        "generado_en": datetime.utcnow().isoformat(),
    }
