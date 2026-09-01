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
        text("SELECT last_value + 1 FROM etiquetas_consecutivo_seq")
    ).one()[0]

    return int(siguiente)


def reservar_consecutivos(db: Session, cantidad: int) -> list[int]:
    from sqlalchemy import text

    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    # Evita que dos usuarios reciban el mismo bloque.
    db.execute(
        text("SELECT pg_advisory_xact_lock(874512)")
    )

    resultado = db.execute(
        text("""
            SELECT nextval('etiquetas_consecutivo_seq')
            FROM generate_series(1, :cantidad)
        """),
        {"cantidad": cantidad},
    )

    return [int(fila[0]) for fila in resultado.fetchall()]


# ============================================================
# ZPL
# ============================================================


def generar_etiqueta_individual(consecutivo: int) -> str:
    """
    Genera UNA fila física del rollo con DOS etiquetas TUFFMARK VOID.

    Especificación física:
        - 50 x 25 mm cada etiqueta.
        - Ancho total de paso: 102 mm.
        - 2 columnas al ancho.
        - Zebra ZT230, 200 dpi.
        - Orientación 0 grados.
        - Margen interno aproximado: 2 mm.
        - Mismo consecutivo en ambas etiquetas.

    A 200 dpi:
        50 mm ~= 400 dots
        25 mm ~= 200 dots
        102 mm ~= 816 dots

    El origen de impresión se desplaza 3.5 mm hacia la izquierda
    mediante ^LS-28 para compensar el offset físico de la impresora.
    """

    consecutivo = str(consecutivo)

    ANCHO_ETIQUETA = 400
    ALTO_ETIQUETA = 200
    GAP = 16
    ANCHO_PASO = 816

    X_IZQUIERDA = 0
    X_DERECHA = ANCHO_ETIQUETA + GAP

    OFFSET_X = -28

    MARGEN = 16
    ANCHO_CONTENIDO = ANCHO_ETIQUETA - (MARGEN * 2)

    Y_IMPLESEG = 4
    Y_BARRAS = 52
    Y_NUMERO = 153

    FUENTE_IMPLESEG = 48
    FUENTE_NUMERO = 34

    ALTURA_BARRAS = 74
    X_BARRAS_IZQUIERDA = 42
    X_BARRAS_DERECHA = X_BARRAS_IZQUIERDA + X_DERECHA

    zpl = (
        f"^XA\n"
        f"^PW{ANCHO_PASO}\n"
        f"^LL{ALTO_ETIQUETA}\n"
        "^LH0,0\n"
        f"^LS{OFFSET_X}\n"
        "^LT0\n"
        "^MNY\n"
        "^MD25\n"
        "^PR3\n"
        "\n"
        f"^FO{X_IZQUIERDA + MARGEN},{Y_IMPLESEG}\n"
        f"^A0N,{FUENTE_IMPLESEG},{FUENTE_IMPLESEG}\n"
        f"^FB{ANCHO_CONTENIDO},1,0,C\n"
        "^FDIMPLESEG^FS\n"
        "\n"
        f"^FO{X_BARRAS_IZQUIERDA},{Y_BARRAS}\n"
        f"^BY2,2,{ALTURA_BARRAS}\n"
        f"^BCN,{ALTURA_BARRAS},N,N,N\n"
        f"^FD{consecutivo}^FS\n"
        "\n"
        f"^FO{X_IZQUIERDA + MARGEN},{Y_NUMERO}\n"
        f"^A0N,{FUENTE_NUMERO},{FUENTE_NUMERO}\n"
        f"^FB{ANCHO_CONTENIDO},1,0,C\n"
        f"^FD{consecutivo}^FS\n"
        "\n"
        f"^FO{X_DERECHA + MARGEN},{Y_IMPLESEG}\n"
        f"^A0N,{FUENTE_IMPLESEG},{FUENTE_IMPLESEG}\n"
        f"^FB{ANCHO_CONTENIDO},1,0,C\n"
        "^FDIMPLESEG^FS\n"
        "\n"
        f"^FO{X_BARRAS_DERECHA},{Y_BARRAS}\n"
        f"^BY2,2,{ALTURA_BARRAS}\n"
        f"^BCN,{ALTURA_BARRAS},N,N,N\n"
        f"^FD{consecutivo}^FS\n"
        "\n"
        f"^FO{X_DERECHA + MARGEN},{Y_NUMERO}\n"
        f"^A0N,{FUENTE_NUMERO},{FUENTE_NUMERO}\n"
        f"^FB{ANCHO_CONTENIDO},1,0,C\n"
        f"^FD{consecutivo}^FS\n"
        "\n"
        "^XZ\n"
    )

    return zpl


def generar_zpl(consecutivos: list[int], copias: int) -> str:
    """
    Genera el trabajo ZPL completo.

    Cada consecutivo genera una fila física con dos stickers
    (izquierda y derecha). 'copias' repite esa fila completa.
    """

    if copias <= 0:
        raise ValueError("Las copias deben ser mayores que cero.")

    return "".join(
        generar_etiqueta_individual(consecutivo)
        for consecutivo in consecutivos
        for _ in range(copias)
    )


# ============================================================
# IMPRESION
# ============================================================

def preparar_trabajo_impresion(zpl: str) -> dict:
    """
    Ubuntu genera el ZPL y lo devuelve al navegador.

    El navegador lo entrega al agente local de Windows, que es quien
    conversa con la impresora USB o compartida.
    """
    if not zpl:
        raise RuntimeError("El trabajo ZPL está vacío.")

    return {
        "status": "ok",
        "metodo": "AGENTE_WINDOWS",
        "zpl": zpl,
    }


# ============================================================
# VISTA
# ============================================================

@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas(request: Request):
    return templates.TemplateResponse(
        "recepcion_etiquetas.html",
        {"request": request}
    )


# ============================================================
# ESTADO
# ============================================================

@router.get("/api/estado")
async def obtener_estado(db: Session = Depends(get_session)):
    siguiente = get_next_consecutivo(db)

    return {
        "consecutivo": siguiente,
        "impresora": impresora_actual
    }


# ============================================================
# HISTORIAL
# ============================================================

@router.get("/api/historial")
async def obtener_historial(db: Session = Depends(get_session)):

    registros = db.exec(
        select(RegistroEtiqueta)
        .order_by(RegistroEtiqueta.consecutivo.desc())
        .limit(100)
    ).all()

    historial = []

    for r in registros:
        historial.append({
            "fecha_hora": r.fecha.isoformat(),
            "tipo_operacion": (
                "IMPRESION"
                if r.impreso
                else "ASIGNACION"
            ),
            "desde_numero": r.consecutivo,
            "hasta_numero": r.consecutivo,
            "cantidad": 1,
            "copias": 1,
            "usuario_nombre": r.nombre,
            "usuario_cedula": r.cedula,
            "cliente_nombre": r.cliente,
            "cliente_nit": ""
        })

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
                detail="La cantidad debe ser mayor que cero."
            )

        if datos.copias <= 0:
            raise HTTPException(
                status_code=400,
                detail="Las copias deben ser mayores que cero."
            )

        # Reservar consecutivos de forma segura.
        numeros = reservar_consecutivos(
            db,
            datos.cantidad
        )

        primer_consecutivo = numeros[0]
        ultimo_consecutivo = numeros[-1]

        cliente_info = datos.c_nombre or ""

        if datos.c_nit:
            cliente_info += f" - NIT: {datos.c_nit}"

        if not cliente_info:
            cliente_info = "Sin detalles de cliente"

        # Registrar cada consecutivo.
        for consecutivo_actual in numeros:

            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre=datos.usuario_nombre,
                cliente=cliente_info,
                fecha=datetime.now(),
                impreso=False,
            )

            db.add(nuevo_registro)

        # --------------------------------------------------------
        # SOLO ASIGNAR
        # --------------------------------------------------------

        if datos.solo_asignar:
            db.commit()

            return {
                "status": "ok",
                "mensaje": (
                    f"Se asignaron {datos.cantidad} etiquetas "
                    f"(Desde {primer_consecutivo} "
                    f"hasta {ultimo_consecutivo})"
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
        # IMPRIMIR DIRECTAMENTE
        # --------------------------------------------------------

        preparar_trabajo_impresion(zpl_completo)

        db.commit()

        return {
            "status": "ok",
            "mensaje": (
                f"Se imprimieron {datos.cantidad} consecutivos "
                f"con {datos.copias} copia(s) cada uno."
            ),
            "desde": primer_consecutivo,
            "hasta": ultimo_consecutivo,
            "cantidad": datos.cantidad,
            "copias": datos.copias,
            "impreso": False,
            "impresora": IMPRESORA_POR_DEFECTO,
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

        siguiente = get_next_consecutivo(db)

        if datos.hasta_numero < siguiente:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"El número 'hasta' debe ser mayor o igual "
                    f"al consecutivo actual ({siguiente})"
                )
            )

        cantidad = (
            datos.hasta_numero - siguiente
        ) + 1

        numeros = reservar_consecutivos(
            db,
            cantidad
        )

        for consecutivo_actual in numeros:

            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre=datos.usuario_nombre,
                cliente="Impresión por Rango",
                fecha=datetime.now(),
                impreso=False,
            )

            db.add(nuevo_registro)

        zpl_completo = generar_zpl(
            numeros,
            datos.copias
        )

        preparar_trabajo_impresion(zpl_completo)

        db.commit()

        return {
            "status": "ok",
            "mensaje": (
                f"Se imprimieron etiquetas hasta "
                f"el número {datos.hasta_numero}"
            ),
            "desde": numeros[0],
            "hasta": numeros[-1],
            "cantidad": len(numeros),
            "copias": datos.copias,
            "impresora": IMPRESORA_POR_DEFECTO,
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


@router.post("/api/marcar_impresion")
async def marcar_impresion(
    datos: DatosConfirmarImpresion,
    db: Session = Depends(get_session)
):
    if datos.desde_numero > datos.hasta_numero:
        raise HTTPException(
            status_code=400,
            detail="El número desde no puede ser mayor que hasta."
        )

    try:
        registros = db.exec(
            select(RegistroEtiqueta).where(
                RegistroEtiqueta.consecutivo >= datos.desde_numero,
                RegistroEtiqueta.consecutivo <= datos.hasta_numero,
            )
        ).all()

        for registro in registros:
            registro.impreso = True
            db.add(registro)

        db.commit()

        return {
            "status": "ok",
            "mensaje": "Impresión confirmada por el agente local.",
            "desde": datos.desde_numero,
            "hasta": datos.hasta_numero,
            "cantidad_actualizada": len(registros),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# REIMPRESION
# ============================================================

@router.post("/api/reimprimir")
async def reimprimir(
    datos: DatosReimpresion,
    db: Session = Depends(get_session)
):

    if datos.desde_numero > datos.hasta_numero:
        raise HTTPException(
            status_code=400,
            detail=(
                "El número 'desde' no puede ser mayor "
                "que 'hasta'"
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

        preparar_trabajo_impresion(zpl_completo)

        return {
            "status": "ok",
            "mensaje": (
                f"Se reimprimieron etiquetas desde "
                f"{datos.desde_numero} hasta "
                f"{datos.hasta_numero}"
            ),
            "desde": datos.desde_numero,
            "hasta": datos.hasta_numero,
            "cantidad": len(numeros),
            "copias": datos.copias,
            "impresora": IMPRESORA_POR_DEFECTO,
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
                detail="El consecutivo debe ser mayor que cero."
            )

        actual = get_next_consecutivo(db)

        if datos.nuevo_consecutivo == actual:
            raise HTTPException(
                status_code=400,
                detail="El nuevo consecutivo ya es el actual."
            )

        # Si el siguiente número deseado es N, PostgreSQL debe quedar
        # con last_value=N-1 para que el próximo nextval() entregue N.
        db.execute(
            text("SELECT setval('etiquetas_consecutivo_seq', :valor, true)"),
            {"valor": datos.nuevo_consecutivo - 1}
        )

        db.add(RegistroEtiqueta(
            consecutivo=datos.nuevo_consecutivo - 1,
            cedula="SISTEMA",
            nombre="SISTEMA",
            cliente=(
                f"Ajuste Manual de Consecutivo: "
                f"{actual} -> {datos.nuevo_consecutivo}"
            ),
            fecha=datetime.now(),
            impreso=False,
        ))

        if datos.nombre_impresora:
            impresora_actual = datos.nombre_impresora.strip()

        db.commit()

        return {
            "status": "ok",
            "mensaje": (
                f"Configuración guardada. Siguiente consecutivo: "
                f"{datos.nuevo_consecutivo}."
            ),
            "consecutivo": datos.nuevo_consecutivo,
            "impresora": impresora_actual,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

