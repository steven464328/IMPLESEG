import csv
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError
from app.database import engine
from app.models import Visitante, Equipo

def limpiar_valor(valor):
    """Convierte celdas vacías del CSV a None para la base de datos."""
    if not valor or str(valor).strip() == "":
        return None
    return str(valor).strip()

def parsear_fecha(fecha_str):
    """Intenta convertir un texto a formato fecha."""
    if not fecha_str or str(fecha_str).strip() == "":
        return None
    formatos = ["%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"]
    for formato in formatos:
        try:
            return datetime.strptime(str(fecha_str).strip(), formato)
        except ValueError:
            continue
    return datetime.now()

def importar_visitantes(ruta_csv):
    print(f"\n⏳ Leyendo archivo: {ruta_csv}...")
    try:
        with open(ruta_csv, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            exitosos = 0
            errores = 0
            
            with Session(engine) as session:
                for row in reader:
                    try:
                        # Extraer datos con valores por defecto seguros para la v2
                        nuevo_visitante = Visitante(
                            cedula=limpiar_valor(row.get('Cédula', row.get('CEDULA', '000000'))),
                            nombre_completo=limpiar_valor(row.get('Nombre', row.get('NOMBRE', 'SIN NOMBRE'))),
                            empresa=limpiar_valor(row.get('Empresa', row.get('EMPRESA', 'N/A'))),
                            tipo_visitante="MIGRADO", # Campo nuevo en v2
                            a_quien_visita=limpiar_valor(row.get('Recibido Por', row.get('RECIBE', 'N/A'))),
                            arl=limpiar_valor(row.get('ARL', 'N/A')),
                            tarjeta_asignada="MIGRADA", # Campo nuevo en v2
                            fecha_ingreso=parsear_fecha(row.get('Fecha/Hora Ingreso', row.get('INGRESO'))),
                            fecha_salida=parsear_fecha(row.get('Fecha/Hora Salida', row.get('SALIDA'))) if limpiar_valor(row.get('Fecha/Hora Salida')) else None
                        )
                        
                        session.add(nuevo_visitante)
                        session.commit() # Guardar fila por fila
                        exitosos += 1
                        
                    except Exception as e:
                        session.rollback() # Si esta fila falla, deshacer y continuar
                        errores += 1
                        print(f"⚠️ Fila omitida (Cédula: {row.get('Cédula')}): Datos inválidos.")
                
                print(f"\n✅ ¡Proceso terminado! Se importaron {exitosos} visitantes exitosamente. ({errores} omitidos por errores)")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ruta_csv}")

def importar_equipos(ruta_csv):
    print(f"\n⏳ Leyendo archivo: {ruta_csv}...")
    try:
        with open(ruta_csv, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            exitosos = 0
            omitidos = 0
            
            with Session(engine) as session:
                for contador, row in enumerate(reader):
                    try:
                        nombre_equipo = limpiar_valor(row.get('EQUIPO', f'TEMP-{contador}'))
                        
                        # Verificar si el equipo ya existe para no duplicar
                        existe = session.exec(select(Equipo).where(Equipo.equipo == nombre_equipo)).first()
                        
                        if existe:
                            omitidos += 1
                            continue # Saltar esta fila y pasar a la siguiente
                        
                        nuevo_equipo = Equipo(
                            empresa=limpiar_valor(row.get('EMPRESA', 'N/A')),
                            equipo=nombre_equipo,
                            codigo=limpiar_valor(row.get('CODIGO')),
                            area=limpiar_valor(row.get('AREA')),
                            tipo_equipo=limpiar_valor(row.get('TIPO DE EQUIPO')),
                            cpu=limpiar_valor(row.get('CPU')),
                            procesador=limpiar_valor(row.get('PROCESADOR')),
                            memoria=limpiar_valor(row.get('MEMORIA')),
                            ip=limpiar_valor(row.get('IP')),
                            usuario_asignado=limpiar_valor(row.get('USUARIO ASIGNADO')),
                            estado_equipo=limpiar_valor(row.get('ESTADO')),
                        )
                        
                        session.add(nuevo_equipo)
                        session.commit() # Guardar fila por fila
                        exitosos += 1
                        
                    except IntegrityError:
                        session.rollback()
                        omitidos += 1
                    except Exception as e:
                        session.rollback()
                        print(f"⚠️ Error al procesar fila: {nombre_equipo}")
                        
                print(f"\n✅ ¡Proceso terminado! Se importaron {exitosos} equipos nuevos. ({omitidos} omitidos o duplicados)")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ruta_csv}")

if __name__ == "__main__":
    print("===========================================")
    print("🚀 IMPORTADOR BLINDADO IMPLESEG")
    print("===========================================")
    print("1. Importar Registro de Visitantes")
    print("2. Importar Hojas de Vida (Equipos)")
    print("3. Salir")
    
    opcion = input("\nElige una opción (1-3): ")
    
    if opcion == '1':
        ruta = input("Ingresa el nombre exacto del archivo CSV de visitantes: ")
        importar_visitantes(ruta)
    elif opcion == '2':
        ruta = input("Ingresa el nombre exacto del archivo CSV de equipos: ")
        importar_equipos(ruta)
    else:
        print("Saliendo...")