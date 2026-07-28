import csv
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from app.database import engine
from app.models import Equipo

def limpiar_valor(valor):
    if not valor or str(valor).strip() == "":
        return None
    return str(valor).strip()

def get_column_value(row, possible_names, default_value=None):
    row_keys_upper = {k.strip().upper(): k for k in row.keys() if k}
    for name in possible_names:
        upper_name = name.strip().upper()
        if upper_name in row_keys_upper:
            original_key = row_keys_upper[upper_name]
            return row.get(original_key)
    return default_value

def importar_equipos(ruta_csv):
    print(f"\n⏳ Leyendo archivo: {ruta_csv}...")
    try:
        with open(ruta_csv, mode='r', encoding='utf-8-sig') as file:
            # 🚨 TRUCO DE MAGIA: Detectar si Excel usó punto y coma o coma
            primera_linea = file.readline()
            delimitador = ';' if ';' in primera_linea else ','
            file.seek(0) # Regresar al inicio del archivo
            
            reader = csv.DictReader(file, delimiter=delimitador)
            print(f"📌 Separador detectado: '{delimitador}'")
            print(f"📌 Encabezados detectados: {reader.fieldnames}")
            
            exitosos = 0
            omitidos = 0
            
            with Session(engine) as session:
                for contador, row in enumerate(reader):
                    try:
                        nombre_raw = get_column_value(row, ['EQUIPO', 'NOMBRE EQUIPO', 'NOMBRE', 'HOSTNAME'])
                        nombre_equipo = limpiar_valor(nombre_raw)
                        
                        if not nombre_equipo:
                            nombre_equipo = f'TEMP-{contador}'
                        
                        existe = session.exec(select(Equipo).where(Equipo.equipo == nombre_equipo)).first()
                        if existe:
                            omitidos += 1
                            continue
                        
                        nuevo_equipo = Equipo(
                            empresa=limpiar_valor(get_column_value(row, ['EMPRESA', 'COMPAÑIA'], 'N/A')),
                            equipo=nombre_equipo,
                            codigo=limpiar_valor(get_column_value(row, ['CODIGO', 'COD', 'ID'])),
                            area=limpiar_valor(get_column_value(row, ['AREA', 'DEPARTAMENTO'])),
                            tipo_equipo=limpiar_valor(get_column_value(row, ['TIPO DE EQUIPO', 'TIPO'])),
                            cpu=limpiar_valor(get_column_value(row, ['CPU', 'PROCESADOR (RESUMEN)'])),
                            procesador=limpiar_valor(get_column_value(row, ['PROCESADOR', 'CPU DETALLE'])),
                            memoria=limpiar_valor(get_column_value(row, ['MEMORIA', 'RAM', 'MEMORIA RAM'])),
                            ip=limpiar_valor(get_column_value(row, ['IP', 'DIRECCION IP'])),
                            usuario_asignado=limpiar_valor(get_column_value(row, ['USUARIO ASIGNADO', 'USUARIO', 'RESPONSABLE'])),
                            estado_equipo=limpiar_valor(get_column_value(row, ['ESTADO', 'STATUS'])),
                        )
                        
                        session.add(nuevo_equipo)
                        session.commit()
                        exitosos += 1
                        
                    except IntegrityError:
                        session.rollback()
                        omitidos += 1
                    except Exception as e:
                        session.rollback()
                        print(f"⚠️ Error al procesar fila: {nombre_equipo}. Detalle: {e}")
                        
                print(f"\n✅ ¡Proceso terminado! Se importaron {exitosos} equipos nuevos. ({omitidos} omitidos o duplicados)")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ruta_csv}")

if __name__ == "__main__":
    print("===========================================")
    print("🚀 IMPORTADOR FLEXIBLE IMPLESEG")
    print("===========================================")
    print("1. Importar Hojas de Vida (Equipos)")
    opcion = input("\nElige una opción (1): ")
    
    if opcion == '1':
        ruta = input("Ingresa el nombre exacto del archivo CSV de equipos (ej. equipos.csv): ")
        importar_equipos(ruta)