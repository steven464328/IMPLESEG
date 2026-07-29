from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import func
from datetime import datetime

from app.database import get_session
from app.models import RegistroEtiqueta

router = APIRouter(prefix="/etiquetas", tags=["Control Etiquetas"])
templates = Jinja2Templates(directory="app/templates")

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

def get_next_consecutivo(db: Session) -> int:
    ultimo_registro = db.exec(
        select(RegistroEtiqueta)
        .order_by(RegistroEtiqueta.fecha.desc())
    ).first()

    return (
        ultimo_registro.consecutivo + 1
        if ultimo_registro
        else 20000000000
    )

def generar_zpl_base(consecutivo: int, copias: int, fecha_str: str) -> str:
    return f"""^XA
^PQ{copias}
^PW400
^LL200
^FO20,20^A0N,25,25^FDIMPLESEG S.A.S^FS
^FO20,50^A0N,20,20^FDControl de Ingreso^FS
^FO20,130^A0N,20,20^FDFecha: {fecha_str}^FS
^FO220,100^BQN,2,4^FDQA,{consecutivo}^FS
^FO220,160^A0N,25,25^FDN. {consecutivo}^FS
^XZ
"""

@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas(request: Request):
    return templates.TemplateResponse("recepcion_etiquetas.html", {"request": request})

@router.get("/api/estado")
async def obtener_estado(db: Session = Depends(get_session)):
    siguiente = get_next_consecutivo(db)
    return {"consecutivo": siguiente, "impresora": "ZEBRA"}

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

@router.post("/api/imprimir_nueva")
async def imprimir_nueva(datos: DatosNuevaEtiqueta, db: Session = Depends(get_session)):
    try:
        zpl_completo = ""
        primer_consecutivo = get_next_consecutivo(db)
        ultimo_consecutivo = primer_consecutivo + datos.cantidad - 1

        for i in range(datos.cantidad):
            consecutivo_actual = primer_consecutivo + i
            fecha_actual = datetime.now()
            cliente_info = datos.c_nombre
            if datos.c_nit: cliente_info += f" - NIT: {datos.c_nit}"
            if not cliente_info: cliente_info = "Sin detalles de cliente"

            nuevo_registro = RegistroEtiqueta(

    consecutivo=consecutivo_actual,

    cedula=datos.usuario_cedula,

    nombre=datos.usuario_nombre,

    cliente=cliente_info,

    fecha=fecha_actual,

    impreso=not datos.solo_asignar,

)

            db.add(nuevo_registro)
            if not datos.solo_asignar:
                zpl_completo += generar_zpl_base(consecutivo_actual, datos.copias, fecha_actual.strftime("%Y-%m-%d"))

        db.commit()
        return {"status": "ok", "mensaje": f"Se procesaron {datos.cantidad} etiquetas (Desde {primer_consecutivo} hasta {ultimo_consecutivo})", "zpl": zpl_completo if not datos.solo_asignar else None}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/imprimir_rango")
async def imprimir_rango(datos: DatosRangoEtiqueta, db: Session = Depends(get_session)):
    try:
        primer_consecutivo = get_next_consecutivo(db)
        if datos.hasta_numero < primer_consecutivo:
            raise HTTPException(status_code=400, detail=f"El número 'hasta' debe ser mayor o igual al consecutivo actual ({primer_consecutivo})")

        cantidad = (datos.hasta_numero - primer_consecutivo) + 1
        zpl_completo = ""

        for i in range(cantidad):
            consecutivo_actual = primer_consecutivo + i
            fecha_actual = datetime.now()
            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre_completo=datos.usuario_nombre,
                equipo_descripcion="Impresión por Rango",
                fecha_ingreso=fecha_actual,
                impreso=True
            )
            db.add(nuevo_registro)
            zpl_completo += generar_zpl_base(consecutivo_actual, datos.copias, fecha_actual.strftime("%Y-%m-%d"))

        db.commit()
        return {"status": "ok", "mensaje": f"Se imprimieron etiquetas hasta el número {datos.hasta_numero}", "zpl": zpl_completo}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/reimprimir")
async def reimprimir(datos: DatosReimpresion, db: Session = Depends(get_session)):
    if datos.desde_numero > datos.hasta_numero:
         raise HTTPException(status_code=400, detail="El número 'desde' no puede ser mayor que 'hasta'")
    zpl_completo = ""
    cantidad = (datos.hasta_numero - datos.desde_numero) + 1
    fecha_str = datetime.now().strftime("%Y-%m-%d")
    for i in range(cantidad):
        consecutivo_actual = datos.desde_numero + i
        zpl_completo += generar_zpl_base(consecutivo_actual, datos.copias, fecha_str)
    return {"status": "ok", "mensaje": f"Se generó archivo para reimprimir desde {datos.desde_numero} hasta {datos.hasta_numero}", "zpl": zpl_completo}

@router.post("/api/configurar")
async def configurar(datos: DatosConfiguracion, db: Session = Depends(get_session)):
    try:
        nuevo_valor_requerido = datos.nuevo_consecutivo
        registro_ajuste = RegistroEtiqueta(
            consecutivo=nuevo_valor_requerido - 1,
            cedula="000000",
            nombre_completo="SISTEMA",
            equipo_descripcion="Ajuste Manual de Consecutivo",
            fecha_ingreso=datetime.now(),
            impreso=False
        )
        db.add(registro_ajuste)
        db.commit()
        return {"status": "ok", "mensaje": f"Consecutivo ajustado a {nuevo_valor_requerido}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error ajustando configuración.")