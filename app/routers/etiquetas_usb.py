from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_session
from app.models import EtiquetaConfig, EtiquetaHistorial

router = APIRouter(prefix="/etiquetas", tags=["Control Etiquetas v2"])
templates = Jinja2Templates(directory="app/templates")

# --- ESQUEMAS DE DATOS PARA LAS PETICIONES ---
class OperacionNueva(BaseModel):
    cantidad: int
    copias: int
    solo_asignar: bool
    usuario_nombre: str
    usuario_cedula: str
    # Datos cliente
    c_nombre: Optional[str] = ""
    c_nit: Optional[str] = ""
    c_contacto: Optional[str] = ""
    c_direccion: Optional[str] = ""

class OperacionRango(BaseModel):
    hasta_numero: int
    copias: int
    usuario_nombre: str
    usuario_cedula: str

class OperacionReimprimir(BaseModel):
    desde_numero: int
    hasta_numero: int
    copias: int
    usuario_nombre: str
    usuario_cedula: str

class ConfiguracionUpdate(BaseModel):
    nuevo_consecutivo: int
    nombre_impresora: str

# --- FUNCIONES AUXILIARES ---
def obtener_config(db: Session) -> EtiquetaConfig:
    config = db.exec(select(EtiquetaConfig).where(EtiquetaConfig.id == 1)).first()
    if not config:
        config = EtiquetaConfig(id=1, consecutivo_actual=20000000000, impresora_nombre="ZEBRA")
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def generar_zpl_bloque(desde: int, hasta: int, copias: int, cliente: str = "IMPLESEG S.A.S") -> str:
    zpl_total = ""
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    nombre_cliente = cliente[:25] if cliente else "IMPLESEG S.A.S"
    
    for num in range(desde, hasta + 1):
        zpl = f"""^XA
^PW400
^LL200
^FO20,20^A0N,25,25^FD{nombre_cliente}^FS
^FO20,50^A0N,20,20^FDControl y Trazabilidad^FS
^FO20,80^A0N,20,20^FDFecha: {fecha_actual}^FS
^FO20,110^A0N,20,20^FDN. {num}^FS
^FO220,70^BQN,2,5^FDQA,{num}^FS
^PQ{copias}
^XZ\n"""
        zpl_total += zpl
    return zpl_total

# --- ENDPOINTS FRONTEND ---
@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas_v2(request: Request):
    return templates.TemplateResponse("recepcion_etiquetas.html", {"request": request})

@router.get("/api/estado")
async def obtener_estado_actual(db: Session = Depends(get_session)):
    config = obtener_config(db)
    return {"consecutivo": config.consecutivo_actual, "impresora": config.impresora_nombre}

@router.get("/api/historial")
async def obtener_historial(db: Session = Depends(get_session)):
    historial = db.exec(select(EtiquetaHistorial).order_by(EtiquetaHistorial.id.desc()).limit(500)).all()
    return historial

# --- ENDPOINTS OPERACIONES ---
@router.post("/api/imprimir_nueva")
async def imprimir_nueva(datos: OperacionNueva, db: Session = Depends(get_session)):
    config = obtener_config(db)
    
    desde = config.consecutivo_actual
    hasta = desde + datos.cantidad - 1
    
    # 1. Guardar Historial
    tipo_op = "ASIGNACION" if datos.solo_asignar else "IMPRESION"
    nuevo_historial = EtiquetaHistorial(
        tipo_operacion=tipo_op, desde_numero=desde, hasta_numero=hasta,
        cantidad=datos.cantidad, copias=0 if datos.solo_asignar else datos.copias,
        usuario_nombre=datos.usuario_nombre, usuario_cedula=datos.usuario_cedula,
        cliente_nombre=datos.c_nombre, cliente_nit=datos.c_nit,
        cliente_contacto=datos.c_contacto, cliente_direccion=datos.c_direccion
    )
    db.add(nuevo_historial)
    
    # 2. Avanzar Consecutivo
    config.consecutivo_actual = hasta + 1
    db.add(config)
    db.commit()
    
    # 3. Generar ZPL si aplica
    zpl_code = ""
    if not datos.solo_asignar:
        cliente_print = datos.c_nombre if datos.c_nombre else "IMPLESEG S.A.S"
        zpl_code = generar_zpl_bloque(desde, hasta, datos.copias, cliente_print)
        
    return {"status": "ok", "zpl": zpl_code, "nuevo_consecutivo": config.consecutivo_actual}

@router.post("/api/imprimir_rango")
async def imprimir_rango(datos: OperacionRango, db: Session = Depends(get_session)):
    config = obtener_config(db)
    
    desde = config.consecutivo_actual
    hasta = datos.hasta_numero
    
    if hasta < desde:
        raise HTTPException(status_code=400, detail="El número 'hasta' debe ser mayor o igual al consecutivo actual.")
        
    cantidad = (hasta - desde) + 1
    
    historial = EtiquetaHistorial(
        tipo_operacion="IMPRESION", desde_numero=desde, hasta_numero=hasta,
        cantidad=cantidad, copias=datos.copias,
        usuario_nombre=datos.usuario_nombre, usuario_cedula=datos.usuario_cedula
    )
    db.add(historial)
    
    config.consecutivo_actual = hasta + 1
    db.add(config)
    db.commit()
    
    zpl_code = generar_zpl_bloque(desde, hasta, datos.copias)
    return {"status": "ok", "zpl": zpl_code, "nuevo_consecutivo": config.consecutivo_actual}

@router.post("/api/reimprimir")
async def reimprimir(datos: OperacionReimprimir, db: Session = Depends(get_session)):
    if datos.hasta_numero < datos.desde_numero:
        raise HTTPException(status_code=400, detail="El rango de reimpresión es inválido.")
        
    cantidad = (datos.hasta_numero - datos.desde_numero) + 1
    
    historial = EtiquetaHistorial(
        tipo_operacion="REIMPRESION", desde_numero=datos.desde_numero, hasta_numero=datos.hasta_numero,
        cantidad=cantidad, copias=datos.copias,
        usuario_nombre=datos.usuario_nombre, usuario_cedula=datos.usuario_cedula
    )
    db.add(historial)
    db.commit() # ¡Ojo! Aquí NO avanzamos el consecutivo de Config.
    
    zpl_code = generar_zpl_bloque(datos.desde_numero, datos.hasta_numero, datos.copias)
    return {"status": "ok", "zpl": zpl_code}

@router.post("/api/configurar")
async def guardar_configuracion(datos: ConfiguracionUpdate, db: Session = Depends(get_session)):
    config = obtener_config(db)
    config.consecutivo_actual = datos.nuevo_consecutivo
    config.impresora_nombre = datos.nombre_impresora.strip().upper()
    db.add(config)
    db.commit()
    return {"status": "ok"}