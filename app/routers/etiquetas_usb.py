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

# --- ESQUEMAS DE DATOS (Pydantic) ---

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

# --- FUNCIONES AUXILIARES ---

def get_next_consecutivo(db: Session) -> int:
    max_consecutivo = db.exec(select(func.max(RegistroEtiqueta.consecutivo))).first()
    # Si no hay registros, empezamos en 20000000000 (como en tu app original)
    return (max_consecutivo or 20000000000) + 1

def generar_zpl_base(consecutivo: int, copias: int, fecha_str: str) -> str:
    """Genera el código ZPL para una etiqueta individual."""
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

# --- RUTAS DE LA API ---

@router.get("/", response_class=HTMLResponse)
async def vista_etiquetas(request: Request):
    """Renderiza la interfaz principal (HTML)"""
    return templates.TemplateResponse("recepcion_etiquetas.html", {"request": request})

@router.get("/api/estado")
async def obtener_estado(db: Session = Depends(get_session)):
    """Devuelve el consecutivo actual para mostrar en la interfaz."""
    siguiente = get_next_consecutivo(db)
    return {
        "consecutivo": siguiente,
        "impresora": "ZEBRA" # Mantenemos esto fijo por ahora ya que la impresión es web/descarga
    }

@router.get("/api/historial")
async def obtener_historial(db: Session = Depends(get_session)):
    """Devuelve el historial de registros."""
    # Para simplificar y no requerir las tablas antiguas de historial complejas,
    # usamos RegistroEtiqueta para generar un historial básico.
    registros = db.exec(select(RegistroEtiqueta).order_by(RegistroEtiqueta.consecutivo.desc()).limit(100)).all()
    
    historial = []
    for r in registros:
        historial.append({
            "fecha_hora": r.fecha_ingreso.isoformat(),
            "tipo_operacion": "IMPRESION" if r.impreso else "ASIGNACION",
            "desde_numero": r.consecutivo,
            "hasta_numero": r.consecutivo,
            "cantidad": 1,
            "copias": 1, # Asumimos 1 para el historial simple
            "usuario_nombre": r.nombre_completo,
            "usuario_cedula": r.cedula,
            "cliente_nombre": r.equipo_descripcion,
            "cliente_nit": ""
        })
    return historial

@router.post("/api/imprimir_nueva")
async def imprimir_nueva(datos: DatosNuevaEtiqueta, db: Session = Depends(get_session)):
    """Genera nuevas etiquetas (imprime o solo asigna)."""
    try:
        zpl_completo = ""
        primer_consecutivo = get_next_consecutivo(db)
        ultimo_consecutivo = primer_consecutivo + datos.cantidad - 1

        for i in range(datos.cantidad):
            consecutivo_actual = primer_consecutivo + i
            fecha_actual = datetime.now()
            
            # Formatear detalles del cliente para guardarlos (si se proporcionaron)
            cliente_info = datos.c_nombre
            if datos.c_nit: cliente_info += f" - NIT: {datos.c_nit}"
            if not cliente_info: cliente_info = "Sin detalles de cliente"

            nuevo_registro = RegistroEtiqueta(
                consecutivo=consecutivo_actual,
                cedula=datos.usuario_cedula,
                nombre_completo=datos.usuario_nombre,
                equipo_descripcion=cliente_info,
                fecha_ingreso=fecha_actual,
                impreso=not datos.solo_asignar
            )
            db.add(nuevo_registro)
            
            if not datos.solo_asignar:
                fecha_str = fecha_actual.strftime("%Y-%m-%d")
                zpl_completo += generar_zpl_base(consecutivo_actual, datos.copias, fecha_str)

        db.commit()

        return {
            "status": "ok", 
            "mensaje": f"Se procesaron {datos.cantidad} etiquetas (Desde {primer_consecutivo} hasta {ultimo_consecutivo})",
            "zpl": zpl_completo if not datos.solo_asignar else None
        }
    except Exception as e:
        db.rollback()
        print(f"Error en imprimir_nueva: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/imprimir_rango")
async def imprimir_rango(datos: DatosRangoEtiqueta, db: Session = Depends(get_session)):
    """Genera etiquetas hasta un número específico."""
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
            
            fecha_str = fecha_actual.strftime("%Y-%m-%d")
            zpl_completo += generar_zpl_base(consecutivo_actual, datos.copias, fecha_str)

        db.commit()

        return {
            "status": "ok", 
            "mensaje": f"Se imprimieron etiquetas hasta el número {datos.hasta_numero}",
            "zpl": zpl_completo
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/reimprimir")
async def reimprimir(datos: DatosReimpresion, db: Session = Depends(get_session)):
    """Reimprime un rango de etiquetas sin avanzar el consecutivo."""
    if datos.desde_numero > datos.hasta_numero:
         raise HTTPException(status_code=400, detail="El número 'desde' no puede ser mayor que 'hasta'")
    
    zpl_completo = ""
    cantidad = (datos.hasta_numero - datos.desde_numero) + 1
    fecha_str = datetime.now().strftime("%Y-%m-%d") # Usamos fecha actual para la reimpresión

    for i in range(cantidad):
        consecutivo_actual = datos.desde_numero + i
        zpl_completo += generar_zpl_base(consecutivo_actual, datos.copias, fecha_str)
        
    # NOTA: No guardamos nada en RegistroEtiqueta para no avanzar el consecutivo, 
    # pero devolvemos el ZPL para que se descargue e imprima.

    return {
        "status": "ok", 
        "mensaje": f"Se generó archivo para reimprimir desde {datos.desde_numero} hasta {datos.hasta_numero}",
        "zpl": zpl_completo
    }

@router.post("/api/configurar")
async def configurar(datos: DatosConfiguracion, db: Session = Depends(get_session)):
    """Actualiza la configuración (manual consecutivo)."""
    # Como simplificamos el modelo y no tenemos tabla de config, 
    # simularemos el cambio de consecutivo insertando un registro "falso" 
    # con el número anterior al deseado para que get_next_consecutivo lo tome.
    try:
        nuevo_valor_requerido = datos.nuevo_consecutivo
        
        # Verificamos si ese número ya existe para evitar errores de clave única
        existe = db.exec(select(RegistroEtiqueta).where(RegistroEtiqueta.consecutivo == nuevo_valor_requerido - 1)).first()
        
        if not existe:
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
        raise HTTPException(status_code=500, detail="Error ajustando configuración. Posible número duplicado.")
```eof

5.  Guarda el archivo en Visual Studio Code (`Ctrl + S`).

### Pasos finales de despliegue

**1. En Visual Studio Code terminal (Local):**
```bash
git add app/routers/etiquetas_usb.py
git commit -m "Restaurando rutas de API completas para etiquetas"
git push origin main