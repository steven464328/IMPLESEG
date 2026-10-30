from datetime import datetime, date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy import text, or_

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
# MODELOS PYDANTIC
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
    ruc: Optional[str] = ""
    ph: Optional[str] = ""
    tipo_documento: Optional[str] = ""
    numero_documento: Optional[str] = ""
    tipo_extintor: Optional[str] = ""
    capacidad: Optional[str] = ""
    fecha_vence_1ano: Optional[date] = None
    fecha_vence_5anos: Optional[date] = None

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
def get_next_consecutivo(db: Session) -> int:
    siguiente = db.exec(
        text("SELECT last_value + 1 FROM etiquetas_consecutivo_seq")
    ).one()[0]
    return int(siguiente)

def reservar_consecutivos(db: Session, cantidad: int) -> list[int]:
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero.")

    db.execute(text("SELECT pg_advisory_xact_lock(874512)"))
    resultado = db.execute(
        text("SELECT nextval('etiquetas_consecutivo_seq') FROM generate_series(1, :cantidad)"),
        {"cantidad": cantidad}
    )
    return [int(fila[0]) for fila in resultado.fetchall()]

# ============================================================
# ZPL INTACTO (MEDIDAS FISICAS PRESERVADAS)
# ============================================================
def generar_etiqueta_individual(consecutivo: int) -> str:
    consecutivo = str(consecutivo)
    ANCHO_TOTAL = 800
    ANCHO_ETIQUETA = 400
    ALTO_ETIQUETA = 200

    X_BARCODE_IZQUIERDA = 110
    X_BARCODE_DERECHA = ANCHO_ETIQUETA + X_BARCODE_IZQUIERDA

    X_TEXTO_IZQUIERDA = 35
    X_TEXTO_DERECHA = ANCHO_ETIQUETA + X_TEXTO_IZQUIERDA
    ANCHO_TEXTO = ANCHO_ETIQUETA

    Y_TITULO = 20
    Y_BARCODE = 65
    Y_NUMERO = 142

    FUENTE_TITULO = 42
    FUENTE_NUMERO = 40
    ALTURA_BARCODE = 60

    return f"""^XA
^PW{ANCHO_TOTAL}
^LL{ALTO_ETIQUETA}
^MD20
^PR3
^LH0,0
^LS0
^LT0
^MNY

^FO{X_TEXTO_IZQUIERDA},{Y_TITULO}
^A0N,{FUENTE_TITULO},{FUENTE_TITULO}
^FB{ANCHO_TEXTO},1,0,C
^FDIMPLESEG^FS

^FO{X_BARCODE_IZQUIERDA},{Y_BARCODE}
^BY2,2,{ALTURA_BARCODE}
^BCN,{ALTURA_BARCODE},N,N,N
^FD{consecutivo}^FS

^FO{X_TEXTO_IZQUIERDA},{Y_NUMERO}
^A0N,{FUENTE_NUMERO},{FUENTE_NUMERO}
^FB{ANCHO_TEXTO},1,0,C
^FD{consecutivo}^FS

^FO{X_TEXTO_DERECHA},{Y_TITULO}
^A0N,{FUENTE_TITULO},{FUENTE_TITULO}
^FB{ANCHO_TEXTO},1,0,C
^FDIMPLESEG^FS

^FO{X_BARCODE_DERECHA},{Y_BARCODE}
^BY2,2,{ALTURA_BARCODE}
^BCN,{ALTURA_BARCODE},N,N,N
^FD{consecutivo}^FS

^FO{X_TEXTO_DERECHA},{Y_NUMERO}
^A0N,{FUENTE_NUMERO},{FUENTE_NUMERO}
^FB{ANCHO_TEXTO},1,0,C
^FD{consecutivo}^FS

^XZ
"""

def generar_zpl(consecutivos: list[int], copias: int) -> str:
    if copias <= 0:
        raise ValueError("Las copias deben ser mayores que cero.")
    return "".join(
        generar_etiqueta_individual(consecutivo)
        for consecutivo in consecutivos
        for _ in range(copias)
    )

def preparar_trabajo_impresion(zpl: str) -> dict:
    if not zpl:
        raise RuntimeError("El trabajo ZPL esta vacio.")
    return {
        "status": "ok",
        "metodo": "AGENTE_WINDOWS",
        "zpl": zpl,
    }

# ============================================================
# VISTAS Y ESTADO
# ============================================================
@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas(request: Request):
    return templates.TemplateResponse("recepcion_etiquetas.html", {"request": request})

@router.get("/api/estado")
async def obtener_estado(db: Session = Depends(get_session)):
    siguiente = get_next_consecutivo(db)
    return {
        "consecutivo": siguiente,
        "impresora": impresora_actual
    }

# ============================================================
# CLIENTES: AUTOCOMPLETAR Y CONSULTA
# ============================================================
@router.get("/api/clientes/buscar")
async def buscar_cliente(q: str = "", db: Session = Depends(get_session)):
    if not q or len(q.strip()) < 2:
        return []
    query = text("""
        SELECT nit, nombre, telefono, direccion 
        FROM etiquetas_clientes 
        WHERE nit ILIKE :q OR nombre ILIKE :q 
        LIMIT 10
    """)
    res = db.execute(query, {"q": f"%{q.strip()}%"}).mappings().all()
    return [dict(r) for r in res]

# ============================================================
# HISTORIAL GENERAL Y CONSULTA POR CLIENTE
# ============================================================
@router.get("/api/historial")
async def obtener_historial(
    db: Session = Depends(get_session),
    filtro_cliente: Optional[str] = None
):
    query = select(RegistroEtiqueta).order_by(RegistroEtiqueta.consecutivo.desc())
    if filtro_cliente and filtro_cliente.strip():
        term = f"%{filtro_cliente.strip()}%"
        query = query.where(
            or_(
                RegistroEtiqueta.cliente.ilike(term),
                RegistroEtiqueta.nit.ilike(term)
            )
        )
    registros = db.exec(query.limit(200)).all()

    historial = []
    for r in registros:
        doc_str = f"{r.tipo_documento} {r.numero_documento}".strip() if r.tipo_documento else "-"
        historial.append({
            "fecha_hora": r.fecha.isoformat(),
            "tipo_operacion": "IMPRESION" if r.impreso else "ASIGNACION",
            "desde_numero": r.consecutivo,
            "hasta_numero": r.consecutivo,
            "cantidad": 1,
            "copias": 1,
            "usuario_nombre": r.nombre,
            "usuario_cedula": r.cedula,
            "cliente_nombre": r.cliente,
            "cliente_nit": r.nit or "",
            "ruc": r.ruc or "",
            "ph": r.ph or "",
            "documento": doc_str,
            "tipo_extintor": r.tipo_extintor or "",
            "capacidad": r.capacidad or "",
            "vence_1ano": r.fecha_vence_1ano.isoformat() if r.fecha_vence_1ano else "",
            "vence_5anos": r.fecha_vence_5anos.isoformat() if r.fecha_vence_5anos else ""
        })
    return historial

# ============================================================
# SISTEMA DE ALERTAS DE VENCIMIENTO
# ============================================================
@router.get("/api/alertas")
async def obtener_alertas(db: Session = Depends(get_session)):
    query = text("""
        SELECT 
            consecutivo, cliente, nit, telefono, 
            tipo_extintor, capacidad, 
            fecha_vence_1ano, fecha_vence_5anos,
            nombre as usuario_nombre
        FROM etiquetas
        WHERE fecha_vence_1ano IS NOT NULL OR fecha_vence_5anos IS NOT NULL
        ORDER BY fecha_vence_1ano ASC NULLS LAST
    """)
    filas = db.execute(query).mappings().all()

    hoy = date.today()
    alertas = []
    for f in filas:
        dias_1 = (f["fecha_vence_1ano"] - hoy).days if f["fecha_vence_1ano"] else None
        dias_5 = (f["fecha_vence_5anos"] - hoy).days if f["fecha_vence_5anos"] else None

        estado_1 = "VENCIDO" if (dias_1 is not None and dias_1 < 0) else ("PROXIMO" if (dias_1 is not None and dias_1 <= 30) else "VIGENTE")
        estado_5 = "VENCIDO" if (dias_5 is not None and dias_5 < 0) else ("PROXIMO" if (dias_5 is not None and dias_5 <= 30) else "VIGENTE")

        alertas.append({
            "consecutivo": f["consecutivo"],
            "cliente": f["cliente"],
            "nit": f["nit"] or "-",
            "telefono": f["telefono"] or "-",
            "tipo_extintor": f["tipo_extintor"] or "-",
            "capacidad": f["capacidad"] or "-",
            "fecha_1ano": str(f["fecha_vence_1ano"]) if f["fecha_vence_1ano"] else "-",
            "dias_1ano": dias_1,
            "estado_1ano": estado_1,
            "fecha_5anos": str(f["fecha_vence_5anos"]) if f["fecha_vence_5anos"] else "-",
            "dias_5anos": dias_5,
            "estado_5anos": estado_5,
        })
    return alertas

# ============================================================
# IMPRIMIR NUEVAS CON TODOS LOS CAMPOS
# ============================================================
@router.post("/api/imprimir_nueva")
async def imprimir_nueva(datos: DatosNuevaEtiqueta, db: Session = Depends(get_session)):
    try:
        if datos.cantidad <= 0 or datos.copias <= 0:
            raise HTTPException(status_code=400, detail="Cantidad y copias deben ser mayores que cero.")

        # Guardar / Actualizar cliente si se proporcionó NIT
        if datos.c_nit and datos.c_nit.strip():
            db.execute(text("""
                INSERT INTO etiquetas_clientes (nit, nombre, telefono, direccion)
                VALUES (:nit, :nombre, :tel, :dir)
                ON CONFLICT (nit) DO UPDATE SET
                    nombre = EXCLUDED.nombre,
                    telefono = EXCLUDED.telefono,
                    direccion = EXCLUDED.direccion;
            """), {
                "nit": datos.c_nit.strip(),
                "nombre": datos.c_nombre.strip() or "Sin nombre",
                "tel": datos.c_contacto or "",
                "dir": datos.c_direccion or ""
            })

        numeros = reservar_consecutivos(db, datos.cantidad)
        cliente_nombre = datos.c_nombre.strip() or "Sin cliente"

        for consecutivo_actual in numeros:
            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre=datos.usuario_nombre,
                cliente=cliente_nombre,
                nit=datos.c_nit or "",
                telefono=datos.c_contacto or "",
                direccion=datos.c_direccion or "",
                ruc=datos.ruc or "",
                ph=datos.ph or "",
                tipo_documento=datos.tipo_documento or "",
                numero_documento=datos.numero_documento or "",
                tipo_extintor=datos.tipo_extintor or "",
                capacidad=datos.capacidad or "",
                fecha_vence_1ano=datos.fecha_vence_1ano,
                fecha_vence_5anos=datos.fecha_vence_5anos,
                fecha=datetime.now(),
                impreso=False,
            )
            db.add(nuevo_registro)

        if datos.solo_asignar:
            db.commit()
            return {
                "status": "ok",
                "mensaje": f"Se asignaron {datos.cantidad} etiquetas (Desde {numeros[0]} hasta {numeros[-1]})",
                "desde": numeros[0],
                "hasta": numeros[-1],
                "cantidad": datos.cantidad,
                "copias": datos.copias,
                "impreso": False,
                "zpl": None
            }

        zpl_completo = generar_zpl(numeros, datos.copias)
        preparar_trabajo_impresion(zpl_completo)
        db.commit()

        return {
            "status": "ok",
            "mensaje": f"Se imprimieron {datos.cantidad} consecutivos con {datos.copias} copia(s).",
            "desde": numeros[0],
            "hasta": numeros[-1],
            "cantidad": datos.cantidad,
            "copias": datos.copias,
            "impreso": False,
            "impresora": IMPRESORA_POR_DEFECTO,
            "zpl": zpl_completo
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# RANGOS, REIMPRESION Y CONFIGURACION (SE MANTIENEN EXACTOS)
# ============================================================
@router.post("/api/imprimir_rango")
async def imprimir_rango(datos: DatosRangoEtiqueta, db: Session = Depends(get_session)):
    try:
        if datos.copias <= 0:
            raise HTTPException(status_code=400, detail="Las copias deben ser mayores que cero.")

        siguiente = get_next_consecutivo(db)
        if datos.hasta_numero < siguiente:
            raise HTTPException(status_code=400, detail=f"El número 'hasta' debe ser >= al actual ({siguiente})")

        cantidad = datos.hasta_numero - siguiente + 1
        numeros = reservar_consecutivos(db, cantidad)

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

        zpl_completo = generar_zpl(numeros, datos.copias)
        preparar_trabajo_impresion(zpl_completo)
        db.commit()

        return {
            "status": "ok",
            "mensaje": f"Se imprimieron etiquetas hasta el número {datos.hasta_numero}",
            "desde": numeros[0],
            "hasta": numeros[-1],
            "cantidad": len(numeros),
            "copias": datos.copias,
            "impresora": IMPRESORA_POR_DEFECTO,
            "zpl": zpl_completo
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/marcar_impresion")
async def marcar_impresion(datos: DatosConfirmarImpresion, db: Session = Depends(get_session)):
    if datos.desde_numero > datos.hasta_numero:
        raise HTTPException(status_code=400, detail="El número desde no puede ser mayor que hasta.")
    try:
        registros = db.exec(
            select(RegistroEtiqueta).where(
                RegistroEtiqueta.consecutivo >= datos.desde_numero,
                RegistroEtiqueta.consecutivo <= datos.hasta_numero,
            )
        ).all()
        for r in registros:
            r.impreso = True
            db.add(r)
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

@router.post("/api/reimprimir")
async def reimprimir(datos: DatosReimpresion, db: Session = Depends(get_session)):
    if datos.desde_numero > datos.hasta_numero or datos.copias <= 0:
        raise HTTPException(status_code=400, detail="Rango o copias inválidas.")
    numeros = list(range(datos.desde_numero, datos.hasta_numero + 1))
    try:
        zpl_completo = generar_zpl(numeros, datos.copias)
        preparar_trabajo_impresion(zpl_completo)
        return {
            "status": "ok",
            "mensaje": f"Se reimprimieron etiquetas desde {datos.desde_numero} hasta {datos.hasta_numero}",
            "desde": datos.desde_numero,
            "hasta": datos.hasta_numero,
            "cantidad": len(numeros),
            "copias": datos.copias,
            "impresora": IMPRESORA_POR_DEFECTO,
            "zpl": zpl_completo
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/configurar")
async def configurar(datos: DatosConfiguracion, db: Session = Depends(get_session)):
    global impresora_actual
    try:
        if datos.nuevo_consecutivo <= 0:
            raise HTTPException(status_code=400, detail="El consecutivo debe ser mayor que cero.")
        db.execute(
            text("SELECT setval('etiquetas_consecutivo_seq', :valor, true)"),
            {"valor": datos.nuevo_consecutivo - 1}
        )
        if datos.nombre_impresora:
            impresora_actual = datos.nombre_impresora.strip()
        db.commit()
        return {
            "status": "ok",
            "mensaje": f"Configuración guardada. Siguiente: {datos.nuevo_consecutivo}.",
            "consecutivo": datos.nuevo_consecutivo,
            "impresora": impresora_actual,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))