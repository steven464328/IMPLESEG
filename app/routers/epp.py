from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/epp", tags=["EPP y Dotación"])

class EntregaEPPModel(BaseModel):
    cedula: str
    nombre: str
    cargo: Optional[str] = ""
    area: Optional[str] = ""
    fecha_ingreso: Optional[str] = ""
    fecha_entrega: Optional[str] = ""
    cant_camisa: Optional[str] = ""
    talla_camisa: Optional[str] = ""
    cant_pantalon: Optional[str] = ""
    talla_pantalon: Optional[str] = ""
    cant_botas: Optional[str] = ""
    talla_botas: Optional[str] = ""
    cant_chaleco: Optional[str] = ""
    talla_chaleco: Optional[str] = ""
    gorra: Optional[str] = ""
    gafas: Optional[str] = ""
    prot_insercion: Optional[str] = ""
    copa: Optional[str] = ""
    otro: Optional[str] = ""
    cual: Optional[str] = ""
    firma_entrega: Optional[str] = ""
    firma_recibe: Optional[str] = ""

HISTORIAL_ENTREGAS_EPP = []

@router.post("/registrar")
async def registrar_entrega_epp(payload: EntregaEPPModel):
    try:
        data_dict = payload.dict()
        data_dict["id"] = len(HISTORIAL_ENTREGAS_EPP) + 1
        data_dict["fecha_registro"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        HISTORIAL_ENTREGAS_EPP.append(data_dict)
        return {
            "status": "success",
            "mensaje": f"Entrega registrada exitosamente para {payload.nombre}",
            "id_registro": data_dict["id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registrando entrega de EPP: {str(e)}")

@router.get("/historial")
def obtener_historial_epp():
    return HISTORIAL_ENTREGAS_EPP