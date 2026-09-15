from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_session
from app.models import RegistroEtiqueta


router = APIRouter(
    prefix="/etiquetas",
    tags=["Control Etiquetas"]
)

templates = Jinja2Templates(
    directory="app/templates"
)


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


class DatosConfirmarImpresion(BaseModel):
    desde_numero: int
    hasta_numero: int


# ============================================================
# CONSECUTIVOS
# ============================================================

def get_next_consecutivo(
    db: Session
) -> int:

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
        }
    )

    return [
        int(fila[0])
        for fila in resultado.fetchall()
    ]


# ============================================================
# ZPL
# ============================================================

# ----------------------------------------------------------
# CALIBRACION FISICA DEL ROLLO DE ETIQUETAS
# ----------------------------------------------------------
# Etiqueta física: TUFFMARK VOID 50mm x 25mm (par de etiquetas
# por fila en el rollo, cada una de 50mm x 25mm).
#
# La ZT230 se vende como "200dpi" pero su resolución real es
# 203 dpi -> 203/25.4 = 7.9921 dots/mm.
#   50 mm x 7.9921 = 399.6 -> 400 dots de ancho por etiqueta
#   25 mm x 7.9921 = 199.8 -> 200 dots de alto por etiqueta
#
# Si en el futuro cambia el rollo (otro proveedor u otro
# tamaño), solo hay que recalcular estos 3 valores con la
# misma fórmula (mm x 7.9921, redondeado al entero más cercano).
#
# ANCHO_ETIQUETA: ancho de UNA sola etiqueta física (dots)
# ALTO_ETIQUETA : alto de UNA sola etiqueta física (dots)
# MARGEN        : margen de seguridad interno para que el
#                 texto/código nunca toque el borde o la
#                 línea de troquelado entre las dos etiquetas
# ----------------------------------------------------------
ANCHO_ETIQUETA = 400   # 50 mm a 203dpi (TUFFMARK VOID 50x25mm)
ALTO_ETIQUETA = 200    # 25 mm a 203dpi (TUFFMARK VOID 50x25mm)
MARGEN = 24            # ~3 mm de margen interno de seguridad

# Módulo del código de barras (grosor de barra angosta, en dots).
# Coincide con ^BY en generar_etiqueta_individual.
MODULO_BARRAS = 2

# Factores empíricos de ancho por caracter de la fuente escalable
# de Zebra (Font 0), como fracción de la altura de fuente.
# Las letras (IMPLESEG) son un poco más anchas que los dígitos.
#
# CALIBRADO (2026-09-15) con una impresión real: se midió en
# píxeles el ancho que la impresora realmente dibujó para
# "IMPLESEG" (^A0N,42,42) y para un consecutivo de 8 dígitos
# (^A0N,40,40) en la etiqueta física, y se despejó el factor.
# Los valores anteriores (0.62 / 0.55) sobrestimaban el ancho
# real, por eso el título y el número quedaban recostados a la
# izquierda en vez de centrados.
FACTOR_ANCHO_LETRAS = 0.47
FACTOR_ANCHO_DIGITOS = 0.43


def ancho_texto_dots(texto: str, alto_fuente: int, factor: float) -> int:
    """Ancho aproximado (en dots) de un texto en Font 0 de Zebra."""
    return round(len(texto) * alto_fuente * factor)


def ancho_barcode_code128_dots(datos: str, modulo: int) -> int:
    """
    Ancho aproximado (en dots) de un código Code 128 en modo
    automático (^BCN,...,N).

    CORRECCION (2026-09-15): se había asumido que, para datos
    numéricos de longitud par, el firmware comprime en el
    subconjunto C (2 dígitos por codeword). Una impresión real
    mostró que esta ZT230 en realidad NO comprime: usa el
    subconjunto B (1 caracter por codeword), que es más ancho.
    Con el supuesto de subconjunto C el ancho salía subestimado,
    así que el código quedaba corrido hacia la derecha, con un
    hueco grande a la izquierda dentro de la etiqueta.

    total_modulos = inicio(11) + datos(11 c/u) + check(11) + parada(13)
    """
    total_modulos = 11 + (11 * len(datos)) + 11 + 13

    return total_modulos * modulo


def centrar_x(x_base: int, ancho_bloque: int, ancho_contenido: int) -> int:
    """
    Calcula el X inicial (^FO) para que 'ancho_contenido' quede
    centrado dentro de una etiqueta que arranca en x_base y mide
    ancho_bloque dots útiles (ya descontado el margen).
    Si el contenido es más ancho que el bloque, no se recorta
    hacia afuera: se ancla al margen izquierdo del bloque.
    """
    desplazamiento = max(0, (ancho_bloque - ancho_contenido) // 2)
    return x_base + MARGEN + desplazamiento


def generar_etiqueta_individual(
    consecutivo: int
) -> str:
    """
    FORMATO FISICO PARA ZEBRA ZT230 200 DPI

    - Ancho total: 2 x ANCHO_ETIQUETA (dos etiquetas físicas
      una junto a la otra, separadas por la línea de
      troquelado del rollo)
    - Alto: ALTO_ETIQUETA
    - Cada etiqueta contiene: IMPLESEG, código de barras
      Code 128 y el consecutivo, TODO CENTRADO.

    CORRECCION (2026-09-15):
    Primero se intentó centrar con ^FB (Field Block), pero el
    firmware de esta ZT230 no lo respeta para estos campos y el
    contenido queda pegado al borde izquierdo. Por eso se volvió
    a posicionar cada campo con ^FO explícito (como el código
    original), pero calculando el ancho real de cada texto y del
    código de barras (ancho_texto_dots / ancho_barcode_code128_dots)
    en vez de usar números fijos "a ojo". Así el centrado es
    matemático y se ajusta solo si cambia la cantidad de dígitos
    del consecutivo, en vez de depender de una calibración manual
    que solo servía para una longitud de número puntual.
    """

    consecutivo = str(consecutivo)

    ancho_total = ANCHO_ETIQUETA * 2
    ancho_bloque = ANCHO_ETIQUETA - (MARGEN * 2)

    ancho_titulo = ancho_texto_dots("IMPLESEG", 42, FACTOR_ANCHO_LETRAS)
    ancho_numero = ancho_texto_dots(consecutivo, 40, FACTOR_ANCHO_DIGITOS)
    ancho_barras = ancho_barcode_code128_dots(consecutivo, MODULO_BARRAS)

    partes = ["^XA",
              f"^PW{ancho_total}",
              f"^LL{ALTO_ETIQUETA}",
              "^MD20",
              "^PR3",
              "^LH0,0",
              "^LS0",
              "^LT0",
              "^MNY",
              ""]

    for x_base in (0, ANCHO_ETIQUETA):

        x_titulo = centrar_x(x_base, ancho_bloque, ancho_titulo)
        x_barras = centrar_x(x_base, ancho_bloque, ancho_barras)
        x_numero = centrar_x(x_base, ancho_bloque, ancho_numero)

        # Título "IMPLESEG"
        partes.append(
            f"^FO{x_titulo},10\n"
            f"^A0N,42,42\n"
            f"^FDIMPLESEG^FS"
        )

        # Código de barras Code 128
        partes.append(
            f"^FO{x_barras},55\n"
            f"^BY{MODULO_BARRAS},2,60\n"
            f"^BCN,60,N,N,N\n"
            f"^FD{consecutivo}^FS"
        )

        # Consecutivo legible debajo del código de barras
        partes.append(
            f"^FO{x_numero},132\n"
            f"^A0N,40,40\n"
            f"^FD{consecutivo}^FS"
        )

    partes.append("^XZ\n")

    return "\n".join(partes)


def generar_zpl(
    consecutivos: list[int],
    copias: int
) -> str:

    """
    Genera todo el trabajo ZPL.

    Un consecutivo genera una fila fisica:
    - etiqueta izquierda
    - etiqueta derecha

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
    Ubuntu genera el ZPL.

    El navegador entrega el ZPL al agente
    local de Windows, que realiza la impresion.
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

@router.get(
    "/api/estado"
)
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

@router.get(
    "/api/historial"
)
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

    for registro in registros:

        historial.append(
            {
                "fecha_hora": (
                    registro.fecha.isoformat()
                ),

                "tipo_operacion": (
                    "IMPRESION"
                    if registro.impreso
                    else "ASIGNACION"
                ),

                "desde_numero": (
                    registro.consecutivo
                ),

                "hasta_numero": (
                    registro.consecutivo
                ),

                "cantidad": 1,

                "copias": 1,

                "usuario_nombre": (
                    registro.nombre
                ),

                "usuario_cedula": (
                    registro.cedula
                ),

                "cliente_nombre": (
                    registro.cliente
                ),

                "cliente_nit": ""
            }
        )

    return historial


# ============================================================
# IMPRIMIR NUEVAS
# ============================================================

@router.post(
    "/api/imprimir_nueva"
)
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

        numeros = reservar_consecutivos(
            db,
            datos.cantidad
        )

        primer_consecutivo = numeros[0]

        ultimo_consecutivo = numeros[-1]

        # ----------------------------------------------------
        # CLIENTE
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # REGISTRO
        # ----------------------------------------------------

        for consecutivo_actual in numeros:

            nuevo_registro = RegistroEtiqueta(
                consecutivo=(
                    consecutivo_actual
                ),

                cedula=(
                    datos.usuario_cedula
                ),

                nombre=(
                    datos.usuario_nombre
                ),

                cliente=cliente_info,

                fecha=datetime.now(),

                impreso=False,
            )

            db.add(
                nuevo_registro
            )

        # ----------------------------------------------------
        # SOLO ASIGNAR
        # ----------------------------------------------------

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

                "desde": (
                    primer_consecutivo
                ),

                "hasta": (
                    ultimo_consecutivo
                ),

                "cantidad": (
                    datos.cantidad
                ),

                "copias": (
                    datos.copias
                ),

                "impreso": False,

                "job_id": None,

                "zpl": None
            }

        # ----------------------------------------------------
        # GENERAR ZPL
        # ----------------------------------------------------

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
                f"Se imprimieron "
                f"{datos.cantidad} consecutivos "
                f"con {datos.copias} copia(s) "
                f"cada uno."
            ),

            "desde": (
                primer_consecutivo
            ),

            "hasta": (
                ultimo_consecutivo
            ),

            "cantidad": (
                datos.cantidad
            ),

            "copias": (
                datos.copias
            ),

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

@router.post(
    "/api/imprimir_rango"
)
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
                    "El número 'hasta' debe "
                    "ser mayor o igual al "
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

        # ----------------------------------------------------
        # REGISTRO
        # ----------------------------------------------------

        for consecutivo_actual in numeros:

            nuevo_registro = RegistroEtiqueta(
                consecutivo=(
                    consecutivo_actual
                ),

                cedula=(
                    datos.usuario_cedula
                ),

                nombre=(
                    datos.usuario_nombre
                ),

                cliente=(
                    "Impresión por Rango"
                ),

                fecha=datetime.now(),

                impreso=False,
            )

            db.add(
                nuevo_registro
            )

        # ----------------------------------------------------
        # ZPL
        # ----------------------------------------------------

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

            "desde": (
                numeros[0]
            ),

            "hasta": (
                numeros[-1]
            ),

            "cantidad": (
                len(numeros)
            ),

            "copias": (
                datos.copias
            ),

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
# CONFIRMAR IMPRESION
# ============================================================

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

@router.post(
    "/api/reimprimir"
)
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

            "cantidad": (
                len(numeros)
            ),

            "copias": (
                datos.copias
            ),

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

@router.post(
    "/api/configurar"
)
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