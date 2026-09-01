import socket

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models import Impresora


router = APIRouter(
    prefix="/etiquetas/api/impresoras",
    tags=["Impresoras"],
)


class ImpresoraCrear(BaseModel):
    nombre: str
    modelo: str | None = None
    ip: str
    puerto: int = 9100
    ubicacion: str | None = None
    activa: bool = True
    predeterminada: bool = False


@router.get("")
def listar_impresoras(
    db: Session = Depends(get_session),
):
    return db.exec(
        select(Impresora)
        .order_by(Impresora.nombre)
    ).all()


@router.post("")
def crear_impresora(
    datos: ImpresoraCrear,
    db: Session = Depends(get_session),
):
    existente = db.exec(
        select(Impresora)
        .where(Impresora.nombre == datos.nombre)
    ).first()

    if existente:
        raise HTTPException(
            status_code=409,
            detail="Ya existe una impresora con ese nombre.",
        )

    if datos.puerto < 1 or datos.puerto > 65535:
        raise HTTPException(
            status_code=400,
            detail="El puerto debe estar entre 1 y 65535.",
        )

    impresora = Impresora(
        nombre=datos.nombre.strip(),
        modelo=datos.modelo.strip() if datos.modelo else None,
        ip=datos.ip.strip(),
        puerto=datos.puerto,
        ubicacion=datos.ubicacion.strip() if datos.ubicacion else None,
        activa=datos.activa,
        predeterminada=datos.predeterminada,
    )

    if datos.predeterminada:
        anteriores = db.exec(
            select(Impresora)
            .where(Impresora.predeterminada == True)
        ).all()

        for anterior in anteriores:
            anterior.predeterminada = False

    db.add(impresora)
    db.commit()
    db.refresh(impresora)

    return impresora


@router.post("/{impresora_id}/probar")
def probar_impresora(
    impresora_id: int,
    db: Session = Depends(get_session),
):
    impresora = db.get(Impresora, impresora_id)

    if not impresora:
        raise HTTPException(
            status_code=404,
            detail="Impresora no encontrada.",
        )

    try:
        with socket.create_connection(
            (impresora.ip, impresora.puerto),
            timeout=3,
        ):
            return {
                "status": "ok",
                "conectada": True,
                "mensaje": (
                    f"Impresora {impresora.nombre} "
                    f"disponible en "
                    f"{impresora.ip}:{impresora.puerto}"
                ),
            }

    except OSError as e:
        return {
            "status": "error",
            "conectada": False,
            "mensaje": (
                f"No fue posible conectar con "
                f"{impresora.ip}:{impresora.puerto}"
            ),
            "error": str(e),
        }


@router.delete("/{impresora_id}")
def eliminar_impresora(
    impresora_id: int,
    db: Session = Depends(get_session),
):
    impresora = db.get(Impresora, impresora_id)

    if not impresora:
        raise HTTPException(
            status_code=404,
            detail="Impresora no encontrada.",
        )

    db.delete(impresora)
    db.commit()

    return {
        "status": "ok",
        "mensaje": "Impresora eliminada correctamente.",
    }
