"""
Migración de datos: Google Sheet 'HOJAS DE VIDA IMPLESEG' -> Base de datos local.

CÓMO USARLO:
1. Abre tu Google Sheet -> Archivo -> Descargar -> Valores separados por comas (.csv)
   (asegúrate de estar en la pestaña correcta antes de descargar)
2. Guarda ese archivo como 'hojas_de_vida.csv' en esta misma carpeta.
3. Ejecuta:  venv/bin/python importar_desde_sheets.py

El script es tolerante: si una columna del CSV no coincide exactamente con el
nombre técnico del sistema, la busca por similitud; y todo lo que no logre
mapear lo guarda igual dentro de 'extra_data' para que no se pierda ningún dato.
"""
import csv
import sys
import unicodedata
from sqlmodel import Session, select

sys.path.insert(0, ".")
from app.database import engine, init_db
from app.models import Equipo

# Mapeo columna_del_sheet -> campo_del_sistema
MAPEO = {
    "EMPRESA": "empresa",
    "EQUIPO": "equipo",
    "CODIGO": "codigo",
    "AREA": "area",
    "NOMBRE EQUIPO": "nombre_equipo",
    "USUARIO SERVIDOR": "usuario_servidor",
    "CPU": "cpu",
    "PROCESADOR": "procesador",
    "MEMORIA": "memoria",
    "MODELO": "modelo_ram",
    "MAINBOARD": "mainboard",
    "HDD/SSD": "tipo_disco",
    "TAMAÑO DISCO": "tamano_disco",
    "MAC": "mac",
    "IP": "ip",
    "ANYDESK": "anydesk_id",
    "DIADEMA": "diadema",
    "TECLADO": "teclado",
    "MOUSE": "mouse",
    "BASE REFRIGERANTE": "base_refrigerante",
    "USUARIO ASIGNADO": "usuario_asignado",
    "TIPO DESKTOP/LAPTOP": "tipo_equipo",
    "ANTIVIRUS": "antivirus",
    "MARCA": "marca",
    "SERIAL NUMBER / SERVICE TAG": "serial",
    "SISTEMA OPERATIVO": "sistema_operativo",
    "OFICCE": "office",
    "LICENCIA": "office_licencia",
    "SERIAL / CORREO": "office_serial",
    "OFFICE FUNCIONES": "office_funciones",
    "ESTADO DEL EQUIPO": "estado_equipo",
    "MANTENIMIENTO": "fecha_ultimo_mantenimiento",
    "OBSERVACION": "observacion_estado",
    "OBERVACIONES": "observaciones_finales",
    "REVISION DRIVE": "fecha_revision_drive",
    "PROGRAMAS": "programas_instalados",
    "NUMERO": "compra_numero",
    "FACTURA": "compra_factura",
    "FECHA": "compra_fecha",
    "PRODUCTOS": "compra_productos",
    "PRECIO": "compra_precio_unitario",
    "PRECIO TOTAL": "compra_precio_total",
    "SERIALES": "compra_seriales",
    "USUARIOS": "compra_usuarios_relacionados",
}

CAMPOS_CHECKLIST = [
    "DOMINIO", "JAVA", "ANYDESK INSTALADO", "ADOBE READER", "7ZIP INSTALADO",
    "TELEFONIA 3CX", "ANTIVIRUS INSTALADO", "CLIENTE IMPRESORA SIESA", "IMPRESORAS",
    "ESCANER", "OFFICE", "ZOFTKRATES", "SIESA", "DRIVE", "GLPI", "WAZUH",
    "HOJA DE VIDA", "ETIQUETA", "CHAT GOOGLE", "MEET", "FIREFOX", "ZOOM", "TEAMS",
]


def normalizar(texto):
    texto = texto.strip().upper()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return texto


def importar(ruta_csv="hojas_de_vida.csv"):
    init_db()
    creados, actualizados, saltados = 0, 0, 0

    with open(ruta_csv, newline="", encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        encabezados_normalizados = {normalizar(h): h for h in lector.fieldnames}

        with Session(engine) as session:
            for fila in lector:
                fila_norm = {normalizar(k): v for k, v in fila.items()}
                codigo_equipo = fila_norm.get("EQUIPO", "").strip()
                if not codigo_equipo:
                    saltados += 1
                    continue

                datos = {}
                extra = {}
                checklist = {}

                for col_sheet, campo_sistema in MAPEO.items():
                    valor = fila_norm.get(normalizar(col_sheet), "").strip()
                    if valor:
                        datos[campo_sistema] = valor

                for col in CAMPOS_CHECKLIST:
                    valor = fila_norm.get(normalizar(col), "").strip()
                    if valor:
                        checklist[col] = valor

                # Todo lo no mapeado se guarda también, nada se pierde
                columnas_usadas = {normalizar(c) for c in MAPEO} | {normalizar(c) for c in CAMPOS_CHECKLIST}
                for col_original, valor in fila.items():
                    if normalizar(col_original) not in columnas_usadas and valor and valor.strip():
                        extra[col_original] = valor.strip()

                datos["checklist_software"] = checklist
                datos["extra_data"] = extra

                existente = session.exec(select(Equipo).where(Equipo.equipo == codigo_equipo)).first()
                if existente:
                    for k, v in datos.items():
                        setattr(existente, k, v)
                    session.add(existente)
                    actualizados += 1
                else:
                    session.add(Equipo(**datos))
                    creados += 1

            session.commit()

    print(f"✔ Importación completa.")
    print(f"  Nuevos registros creados:      {creados}")
    print(f"  Registros existentes actualizados: {actualizados}")
    print(f"  Filas saltadas (sin código de equipo): {saltados}")


if __name__ == "__main__":
    ruta = sys.argv[1] if len(sys.argv) > 1 else "hojas_de_vida.csv"
    importar(ruta)
