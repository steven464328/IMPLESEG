from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlmodel import Session, select

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
    db.execute(text("SELECT pg_advisory_xact_lock(874512)"))

    resultado = db.execute(
        text("""
            SELECT nextval('etiquetas_consecutivo_seq')
            FROM generate_series(1, :cantidad)
        """),
        {"cantidad": cantidad},
    )

    return [int(fila[0]) for fila in resultado.fetchall()]


# ============================================================
# ZPL (GEOMETRÍA Y CENTRADO SIMÉTRICO PERFECTO)
# ============================================================


def generar_etiqueta_individual(consecutivo: int) -> str:
    """Genera UNA fila física con DOS etiquetas TUFFMARK VOID de 50 x 25 mm.

    IMPRESORA:
        Zebra ZT230 - 200 dpi

    CORRECCIÓN DE SIMETRÍA:
        - Se incorpora GAP_INTERMEDIO (16 dots = 2 mm) entre ambas columnas
          para que la etiqueta derecha interprete el desplazamiento real del rollo.
        - Se sincroniza el centrado dinámico del código de barras en ambas etiquetas.
    """

    consecutivo_str = str(consecutivo)

    # ============================================================
    # GEOMETRÍA DE ROLLO (Dots a 200 dpi)
    # ============================================================
    ANCHO_ETIQUETA = 400
    GAP_INTERMEDIO = 16  # Espacio físico de 2 mm entre columna 1 y columna 2

    X_IZQUIERDA = 0
    X_DERECHA = ANCHO_ETIQUETA + GAP_INTERMEDIO  # Inicio real de la etiqueta derecha

    MARGEN_TEXTO = 16
    ANCHO_TEXTO = ANCHO_ETIQUETA - (2 * MARGEN_TEXTO)

    # ============================================================
    # POSICIONES VERTICALES (Y)
    # ============================================================
    Y_IMPLESEG = 10
    Y_BARRAS = 60
    Y_NUMERO = 145

    # ============================================================
    # TIPOGRAFÍA Y BARRAS
    # ============================================================
    FUENTE_IMPLESEG = 44
    FUENTE_NUMERO = 28
    ALTURA_BARRAS = 65

    # ============================================================
    # CÁLCULO DINÁMICO DE CENTRADO SIMÉTRICO
    # ============================================================
    # Code 128 con ^BY2 ocupa aprox 22 dots por dígito + 80 dots de cabeceras/controles.
    ancho_estimado_barcode = (len(consecutivo_str) * 22) + 80
    
    # Offset idéntico calculado para ambas etiquetas
    offset_centrado = max(10, int((ANCHO_ETIQUETA - ancho_estimado_barcode) / 2))

    X_BARRAS_IZQUIERDA = X_IZQUIERDA + offset_centrado
    X_BARRAS_DERECHA = X_DERECHA + offset_centrado

    zpl = f"""^XA
^PW820
^LL200
^LH0,0
^LS0
^LT0
^MNY
^MD25
^PR3

^FO{X_IZQUIERDA + MARGEN_TEXTO},{Y_IMPLESEG}
^A0N,{FUENTE_IMPLESEG},{FUENTE_IMPLESEG}
^FB{ANCHO_TEXTO},1,0,C
^FDIMPLESEG^FS

^FO{X_BARRAS_IZQUIERDA},{Y_BARRAS}
^BY2,2,{ALTURA_BARRAS}
^BCN,{ALTURA_BARRAS},N,N,N
^FD{consecutivo_str}^FS

^FO{X_IZQUIERDA + MARGEN_TEXTO},{Y_NUMERO}
^A0N,{FUENTE_NUMERO},{FUENTE_NUMERO}
^FB{ANCHO_TEXTO},1,0,C
^FD{consecutivo_str}^FS

^FO{X_DERECHA + MARGEN_TEXTO},{Y_IMPLESEG}
^A0N,{FUENTE_IMPLESEG},{FUENTE_IMPLESEG}
^FB{ANCHO_TEXTO},1,0,C
^FDIMPLESEG^FS

^FO{X_BARRAS_DERECHA},{Y_BARRAS}
^BY2,2,{ALTURA_BARRAS}
^BCN,{ALTURA_BARRAS},N,N,N
^FD{consecutivo_str}^FS

^FO{X_DERECHA + MARGEN_TEXTO},{Y_NUMERO}
^A0N,{FUENTE_NUMERO},{FUENTE_NUMERO}
^FB{ANCHO_TEXTO},1,0,C
^FD{consecutivo_str}^FS

^XZ
"""
    return zpl


def generar_zpl(consecutivos: list[int], copias: int) -> str:
    """Genera el trabajo ZPL completo.

    Cada consecutivo genera una fila física con dos stickers (izquierda y
    derecha). 'copias' repite esa fila completa.
    """

    if copias <= 0:
        raise ValueError("Las copias deben ser mayores que cero.")

    return "".join(
        generar_etiqueta_individual(consecutivo)
        for consecutivo in consecutivos
        for _ in range(copias)
    )


# ============================================================
# IMPRESION DIRECTA WINDOWS
# ============================================================


def imprimir_raw_windows(zpl: str, nombre_impresora: str) -> int:
    """Envía ZPL directamente a una impresora instalada en Windows.

    Requiere pywin32.
    """

    try:
        import win32print
    except ImportError as e:
        raise RuntimeError(
            "pywin32 no está instalado en el entorno del servidor."
        ) from e

    try:
        handle = win32print.OpenPrinter(nombre_impresora)

        try:
            job_id = win32print.StartDocPrinter(
                handle, 1, ("IMPLES EG - Etiquetas", None, "RAW")
            )

            try:
                win32print.StartPagePrinter(handle)

                try:
                    datos = zpl.encode("ascii")
                    escrito = win32print.WritePrinter(handle, datos)

                    if escrito != len(datos):
                        raise RuntimeError(
                            f"Windows escribió {escrito} bytes de {len(datos)} enviados."
                        )

                finally:
                    win32print.EndPagePrinter(handle)

            finally:
                win32print.EndDocPrinter(handle)

            return job_id

        finally:
            win32print.ClosePrinter(handle)

    except Exception as e:
        raise RuntimeError(
            f"No fue posible imprimir en '{nombre_impresora}': {e}"
        ) from e


# ============================================================
# VISTA
# ============================================================


@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas(request: Request):
    return templates.TemplateResponse(
        "recepcion_etiquetas.html", {"request": request}
    )


# ============================================================
# ESTADO
# ============================================================


@router.get("/api/estado")
async def obtener_estado(db: Session = Depends(get_session)):
    siguiente = get_next_consecutivo(db)

    return {"consecutivo": siguiente, "impresora": impresora_actual}


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
                "IMPRESION" if r.impreso else "ASIGNACION"
            ),
            "desde_numero": r.consecutivo,
            "hasta_numero": r.consecutivo,
            "cantidad": 1,
            "copias": 1,
            "usuario_nombre": r.nombre,
            "usuario_cedula": r.cedula,
            "cliente_nombre": r.cliente,
            "cliente_nit": "",
        })

    return historial


# ============================================================
# IMPRIMIR NUEVAS
# ============================================================


@router.post("/api/imprimir_nueva")
async def imprimir_nueva(
    datos: DatosNuevaEtiqueta, db: Session = Depends(get_session)
):
    try:

        if datos.cantidad <= 0:
            raise HTTPException(
                status_code=400,
                detail="La cantidad debe ser mayor que cero.",
            )

        if datos.copias <= 0:
            raise HTTPException(
                status_code=400, detail="Las copias deben ser mayores que cero."
            )

        # Reservar consecutivos de forma segura.
        numeros = reservar_consecutivos(db, datos.cantidad)

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
                impreso=not datos.solo_asignar,
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
                "zpl": None,
            }

        # --------------------------------------------------------
        # GENERAR ZPL
        # --------------------------------------------------------

        zpl_completo = generar_zpl(numeros, datos.copias)

        # --------------------------------------------------------
        # IMPRIMIR DIRECTAMENTE
        # --------------------------------------------------------

        job_id = imprimir_raw_windows(zpl_completo, IMPRESORA_POR_DEFECTO)

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
            "impreso": True,
            "impresora": IMPRESORA_POR_DEFECTO,
            "job_id": job_id,
            "zpl": None,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()

        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# IMPRIMIR RANGO
# ============================================================


@router.post("/api/imprimir_rango")
async def imprimir_rango(
    datos: DatosRangoEtiqueta, db: Session = Depends(get_session)
):
    try:

        siguiente = get_next_consecutivo(db)

        if datos.hasta_numero < siguiente:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"El número 'hasta' debe ser mayor o igual "
                    f"al consecutivo actual ({siguiente})"
                ),
            )

        cantidad = (datos.hasta_numero - siguiente) + 1

        numeros = reservar_consecutivos(db, cantidad)

        for consecutivo_actual in numeros:

            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre=datos.usuario_nombre,
                cliente="Impresión por Rango",
                fecha=datetime.now(),
                impreso=True,
            )

            db.add(nuevo_registro)

        zpl_completo = generar_zpl(numeros, datos.copias)

        job_id = imprimir_raw_windows(zpl_completo, IMPRESORA_POR_DEFECTO)

        db.commit()

        return {
            "status": "ok",
            "mensaje": (
                f"Se imprimieron etiquetas hasta el número {datos.hasta_numero}"
            ),
            "desde": numeros[0],
            "hasta": numeros[-1],
            "cantidad": len(numeros),
            "copias": datos.copias,
            "impresora": IMPRESORA_POR_DEFECTO,
            "job_id": job_id,
            "zpl": None,
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()

        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# REIMPRESION
# ============================================================


@router.post("/api/reimprimir")
async def reimprimir(
    datos: DatosReimpresion, db: Session = Depends(get_session)
):

    if datos.desde_numero > datos.hasta_numero:
        raise HTTPException(
            status_code=400,
            detail="El número 'desde' no puede ser mayor que 'hasta'",
        )

    numeros = list(range(datos.desde_numero, datos.hasta_numero + 1))

    try:

        zpl_completo = generar_zpl(numeros, datos.copias)

        job_id = imprimir_raw_windows(zpl_completo, IMPRESORA_POR_DEFECTO)

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
            "job_id": job_id,
        }

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# CONFIGURAR CONSECUTIVO
# ============================================================


@router.post("/api/configurar")
async def configurar(
    datos: DatosConfiguracion, db: Session = Depends(get_session)
):
    global impresora_actual
    from sqlalchemy import text

    try:
        if datos.nuevo_consecutivo <= 0:
            raise HTTPException(
                status_code=400,
                detail="El consecutivo debe ser un número entero mayor que cero.",
            )

        actual = get_next_consecutivo(db)

        if datos.nuevo_consecutivo == actual:
            raise HTTPException(
                status_code=400, detail="El nuevo consecutivo ya es el actual."
            )

        # Si el siguiente número deseado es N, PostgreSQL debe quedar
        # con last_value=N-1 para que el próximo nextval() entregue N.
        db.execute(
            text("SELECT setval('etiquetas_consecutivo_seq', :valor, true)"),
            {"valor": datos.nuevo_consecutivo - 1},
        )

        # IMPORTANTE:
        # No se registra el cambio manual en RegistroEtiqueta.
        #
        # RegistroEtiqueta.consecutivo es único y el número seleccionado
        # puede existir previamente porque manejamos varios consecutivos.
        # Insertarlo aquí provocaba UniqueViolation y hacía rollback
        # del cambio de secuencia.
        #
        # El cambio manual afecta únicamente la secuencia PostgreSQL.
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