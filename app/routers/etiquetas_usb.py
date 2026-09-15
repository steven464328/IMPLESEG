from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_session
from app.models import RegistroEtiqueta

router = APIRouter(prefix="/etiquetas", tags=["Control Etiquetas"])
templates = Jinja2Templates(directory="app/templates")


# ============================================================
# CONFIGURACION DE IMPRESION
# ============================================================

IMPRESORA_POR_DEFECTO = "ZDesigner ZT230-200dpi ZPL"
impresora_actual = IMPRESORA_POR_DEFECTO


# ============================================================
# MODELOS
# ============================================================

class DatosNuevaEtiqueta(BaseModel):
    cantidad: int
    copias: int
    solo_asignar: bool
    usuario_nombre: str
    usuario_cedula: str
    c_nombre: Optional[str] = ""
    c_nit: Optional[str] = ""
    c_contacto: Optional[str] = ""
    c_direccion: Optional[str] = ""


class DatosRangoEtiqueta(BaseModel):
    hasta_numero: int
    copias: int
    usuario_nombre: str
    usuario_cedula: str


class DatosReimpresion(BaseModel):
    desde_numero: int
    hasta_numero: int
    copias: int
    usuario_nombre: str
    usuario_cedula: str


class DatosConfiguracion(BaseModel):
    nuevo_consecutivo: int
    nombre_impresora: str


# ============================================================
# CONSECUTIVOS
# ============================================================

def get_next_consecutivo(db: Session) -> int:
    from sqlalchemy import text

    siguiente = db.exec(
        text(
            "SELECT last_value + 1 "
            "FROM etiquetas_consecutivo_seq"
        )
    ).one()[0]

    return int(siguiente)


def reservar_consecutivos(
    db: Session,
    cantidad: int
) -> list[int]:

    from sqlalchemy import text

    if cantidad <= 0:
        raise ValueError(
            "La cantidad debe ser mayor que cero."
        )

    # Bloqueo central para evitar que dos usuarios
    # reciban el mismo bloque de consecutivos.
    db.execute(
        text(
            "SELECT pg_advisory_xact_lock(874512)"
        )
    )

    resultado = db.execute(
        text(
            """
            SELECT nextval('etiquetas_consecutivo_seq')
            FROM generate_series(1, :cantidad)
            """
        ),
        {
            "cantidad": cantidad
        },
    )

    return [
        int(fila[0])
        for fila in resultado.fetchall()
    ]


# ============================================================
# ZPL
# ============================================================

def generar_etiqueta_individual(
    consecutivo: int
) -> str:
    """
    Geometría física para Zebra ZT230 200 dpi.

    Rollo:
    - Ancho total ZPL: 640 dots
    - Alto: 200 dots
    - Dos etiquetas por fila
    - Cada etiqueta: 320 x 200 dots

    Diseño de cada etiqueta:
    - IMPLESEG centrado
    - Código Code 128 más grande y centrado
    - Consecutivo más grande y centrado

    No se realiza impresión directa desde Ubuntu.
    Ubuntu genera el ZPL y el navegador lo entrega
    al agente de impresión de Windows.
    """

    consecutivo = str(consecutivo)

    ANCHO_ETIQUETA = 320
    ANCHO_TOTAL = 640
    ALTO_ETIQUETA = 200

    # Posiciones horizontales del código de barras.
    #
    # Con BY=3 el código ocupa más espacio horizontal.
    # Las posiciones están calculadas para centrarlo
    # dentro de cada área de 320 dots.
    X_BARCODE_IZQUIERDA = 40
    X_BARCODE_DERECHA = (
        ANCHO_ETIQUETA + X_BARCODE_IZQUIERDA
    )

    return f"""^XA
^PW{ANCHO_TOTAL}
^LL{ALTO_ETIQUETA}
^MD25
^PR3
^LH0,0
^LS0
^LT0
^MNY

^FO0,14
^A0N,38,38
^FB{ANCHO_ETIQUETA},1,0,C
^FDIMPLESEG^FS

^FO{X_BARCODE_IZQUIERDA},55
^BY3,2,55
^BCN,55,N,N,N
^FD{consecutivo}^FS

^FO0,132
^A0N,34,34
^FB{ANCHO_ETIQUETA},1,0,C
^FD{consecutivo}^FS


^FO{ANCHO_ETIQUETA},14
^A0N,38,38
^FB{ANCHO_ETIQUETA},1,0,C
^FDIMPLESEG^FS

^FO{X_BARCODE_DERECHA},55
^BY3,2,55
^BCN,55,N,N,N
^FD{consecutivo}^FS

^FO{ANCHO_ETIQUETA},132
^A0N,34,34
^FB{ANCHO_ETIQUETA},1,0,C
^FD{consecutivo}^FS

^XZ
"""


def generar_zpl(
    consecutivos: list[int],
    copias: int
) -> str:

    """
    Genera el trabajo ZPL completo.

    Cada consecutivo genera:
    - una etiqueta izquierda
    - una etiqueta derecha

    'copias' repite la fila completa.
    """

    if copias <= 0:
        raise ValueError(
            "Las copias deben ser mayores que cero."
        )

    return "".join(
        generar_etiqueta_individual(
            consecutivo
        )
        for consecutivo in consecutivos
        for _ in range(copias)
    )


# ============================================================
# IMPRESION
# ============================================================

def preparar_trabajo_impresion(
    zpl: str
) -> dict:
    """
    Ubuntu genera el ZPL y lo devuelve al navegador.

    El navegador entrega el ZPL al agente local
    de Windows, que es quien conversa con la impresora.
    """

    if not zpl:
        raise RuntimeError(
            "El trabajo ZPL está vacío."
        )

    return {
        "status": "ok",
        "metodo": "AGENTE_WINDOWS",
        "zpl": zpl,
    }


# ============================================================
# VISTA
# ============================================================

@router.get(
    "/",
    response_class=HTMLResponse
)
async def vista_etiquetas(
    request: Request
):
    return templates.TemplateResponse(
        "recepcion_etiquetas.html",
        {
            "request": request
        }
    )


# ============================================================
# ESTADO
# ============================================================

@router.get("/api/estado")
async def obtener_estado(
    db: Session = Depends(get_session)
):

    siguiente = get_next_consecutivo(
        db
    )

    return {
        "consecutivo": siguiente,
        "impresora": impresora_actual
    }


# ============================================================
# HISTORIAL
# ============================================================

@router.get("/api/historial")
async def obtener_historial(
    db: Session = Depends(get_session)
):

    registros = db.exec(
        select(RegistroEtiqueta)
        .order_by(
            RegistroEtiqueta.consecutivo.desc()
        )
        .limit(100)
    ).all()

    historial = []

    for r in registros:

        historial.append(
            {
                "fecha_hora": r.fecha.isoformat(),

                "tipo_operacion": (
                    "IMPRESION"
                    if r.impreso
                    else "ASIGNACION"
                ),

                "desde_numero": (
                    r.consecutivo
                ),

                "hasta_numero": (
                    r.consecutivo
                ),

                "cantidad": 1,
                "copias": 1,

                "usuario_nombre": (
                    r.nombre
                ),

                "usuario_cedula": (
                    r.cedula
                ),

                "cliente_nombre": (
                    r.cliente
                ),

                "cliente_nit": ""
            }
        )

    return historial


# ============================================================
# IMPRIMIR NUEVAS
# ============================================================

@router.post("/api/imprimir_nueva")
async def imprimir_nueva(
    datos: DatosNuevaEtiqueta,
    db: Session = Depends(get_session)
):

    try:

        if datos.cantidad <= 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "La cantidad debe ser "
                    "mayor que cero."
                )
            )

        if datos.copias <= 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Las copias deben ser "
                    "mayores que cero."
                )
            )

        # --------------------------------------------------------
        # RESERVAR CONSECUTIVOS
        # --------------------------------------------------------

        numeros = reservar_consecutivos(
            db,
            datos.cantidad
        )

        primer_consecutivo = numeros[0]
        ultimo_consecutivo = numeros[-1]

        # --------------------------------------------------------
        # INFORMACION CLIENTE
        # --------------------------------------------------------

        cliente_info = (
            datos.c_nombre or ""
        )

        if datos.c_nit:

            cliente_info += (
                f" - NIT: {datos.c_nit}"
            )

        if not cliente_info:

            cliente_info = (
                "Sin detalles de cliente"
            )

        # --------------------------------------------------------
        # REGISTRAR CONSECUTIVOS
        # --------------------------------------------------------

        for consecutivo_actual in numeros:

            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre=datos.usuario_nombre,
                cliente=cliente_info,
                fecha=datetime.now(),
                impreso=False,
            )

            db.add(
                nuevo_registro
            )

        # --------------------------------------------------------
        # SOLO ASIGNAR
        # --------------------------------------------------------

        if datos.solo_asignar:

            db.commit()

            return {
                "status": "ok",

                "mensaje": (
                    f"Se asignaron "
                    f"{datos.cantidad} etiquetas "
                    f"(Desde "
                    f"{primer_consecutivo} "
                    f"hasta "
                    f"{ultimo_consecutivo})"
                ),

                "desde": primer_consecutivo,
                "hasta": ultimo_consecutivo,
                "cantidad": datos.cantidad,
                "copias": datos.copias,

                "impreso": False,

                "job_id": None,
                "zpl": None
            }

        # --------------------------------------------------------
        # GENERAR ZPL
        # --------------------------------------------------------

        zpl_completo = generar_zpl(
            numeros,
            datos.copias
        )

        # --------------------------------------------------------
        # PREPARAR IMPRESION
        # --------------------------------------------------------

        preparar_trabajo_impresion(
            zpl_completo
        )

        db.commit()

        return {
            "status": "ok",

            "mensaje": (
                f"Se imprimieron "
                f"{datos.cantidad} consecutivos "
                f"con {datos.copias} copia(s) "
                f"cada uno."
            ),

            "desde": primer_consecutivo,
            "hasta": ultimo_consecutivo,
            "cantidad": datos.cantidad,
            "copias": datos.copias,

            "impreso": False,

            "impresora": (
                IMPRESORA_POR_DEFECTO
            ),

            "job_id": None,

            "zpl": zpl_completo
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# IMPRIMIR RANGO
# ============================================================

@router.post("/api/imprimir_rango")
async def imprimir_rango(
    datos: DatosRangoEtiqueta,
    db: Session = Depends(get_session)
):

    try:

        if datos.copias <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Las copias deben ser "
                    "mayores que cero."
                )
            )

        siguiente = get_next_consecutivo(
            db
        )

        if datos.hasta_numero < siguiente:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El número 'hasta' debe ser "
                    "mayor o igual al "
                    f"consecutivo actual "
                    f"({siguiente})."
                )
            )

        cantidad = (
            datos.hasta_numero
            - siguiente
            + 1
        )

        numeros = reservar_consecutivos(
            db,
            cantidad
        )

        # --------------------------------------------------------
        # REGISTRAR
        # --------------------------------------------------------

        for consecutivo_actual in numeros:

            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre=datos.usuario_nombre,
                cliente="Impresión por Rango",
                fecha=datetime.now(),
                impreso=False,
            )

            db.add(
                nuevo_registro
            )

        # --------------------------------------------------------
        # GENERAR ZPL
        # --------------------------------------------------------

        zpl_completo = generar_zpl(
            numeros,
            datos.copias
        )

        preparar_trabajo_impresion(
            zpl_completo
        )

        db.commit()

        return {
            "status": "ok",

            "mensaje": (
                "Se imprimieron etiquetas "
                "hasta el número "
                f"{datos.hasta_numero}"
            ),

            "desde": numeros[0],
            "hasta": numeros[-1],
            "cantidad": len(numeros),
            "copias": datos.copias,

            "impresora": (
                IMPRESORA_POR_DEFECTO
            ),

            "job_id": None,
            "zpl": zpl_completo
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# CONFIRMAR IMPRESION DESDE EL AGENTE WINDOWS
# ============================================================

class DatosConfirmarImpresion(BaseModel):
    desde_numero: int
    hasta_numero: int


@router.post(
    "/api/marcar_impresion"
)
async def marcar_impresion(
    datos: DatosConfirmarImpresion,
    db: Session = Depends(get_session)
):

    if (
        datos.desde_numero
        > datos.hasta_numero
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "El número desde no puede "
                "ser mayor que hasta."
            )
        )

    try:

        registros = db.exec(
            select(
                RegistroEtiqueta
            ).where(
                RegistroEtiqueta.consecutivo
                >= datos.desde_numero,

                RegistroEtiqueta.consecutivo
                <= datos.hasta_numero,
            )
        ).all()

        for registro in registros:

            registro.impreso = True

            db.add(
                registro
            )

        db.commit()

        return {
            "status": "ok",

            "mensaje": (
                "Impresión confirmada "
                "por el agente local."
            ),

            "desde": (
                datos.desde_numero
            ),

            "hasta": (
                datos.hasta_numero
            ),

            "cantidad_actualizada": (
                len(registros)
            ),
        }

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# REIMPRESION
# ============================================================

@router.post("/api/reimprimir")
async def reimprimir(
    datos: DatosReimpresion,
    db: Session = Depends(get_session)
):

    if (
        datos.desde_numero
        > datos.hasta_numero
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "El número desde no puede "
                "ser mayor que hasta."
            )
        )

    if datos.copias <= 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Las copias deben ser "
                "mayores que cero."
            )
        )

    numeros = list(
        range(
            datos.desde_numero,
            datos.hasta_numero + 1
        )
    )

    try:

        zpl_completo = generar_zpl(
            numeros,
            datos.copias
        )

        preparar_trabajo_impresion(
            zpl_completo
        )

        return {
            "status": "ok",

            "mensaje": (
                "Se reimprimieron etiquetas "
                "desde "
                f"{datos.desde_numero} "
                "hasta "
                f"{datos.hasta_numero}"
            ),

            "desde": (
                datos.desde_numero
            ),

            "hasta": (
                datos.hasta_numero
            ),

            "cantidad": len(numeros),
            "copias": datos.copias,

            "impresora": (
                IMPRESORA_POR_DEFECTO
            ),

            "job_id": None,

            "zpl": zpl_completo
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# CONFIGURAR CONSECUTIVO
# ============================================================

@router.post("/api/configurar")
async def configurar(
    datos: DatosConfiguracion,
    db: Session = Depends(get_session)
):

    global impresora_actual

    from sqlalchemy import text

    try:

        if datos.nuevo_consecutivo <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El consecutivo debe "
                    "ser mayor que cero."
                )
            )

        actual = get_next_consecutivo(
            db
        )

        if datos.nuevo_consecutivo == actual:

            raise HTTPException(
                status_code=400,
                detail=(
                    "El nuevo consecutivo "
                    "ya es el actual."
                )
            )

        # Si el siguiente número deseado es N,
        # PostgreSQL debe quedar con last_value = N-1.
        db.execute(
            text(
                "SELECT setval("
                "'etiquetas_consecutivo_seq', "
                ":valor, "
                "true)"
            ),
            {
                "valor": (
                    datos.nuevo_consecutivo
                    - 1
                )
            }
        )

        if datos.nombre_impresora:

            impresora_actual = (
                datos.nombre_impresora.strip()
            )

        db.commit()

        return {
            "status": "ok",

            "mensaje": (
                "Configuración guardada. "
                "Siguiente consecutivo: "
                f"{datos.nuevo_consecutivo}."
            ),

            "consecutivo": (
                datos.nuevo_consecutivo
            ),

            "impresora": (
                impresora_actual
            ),
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )