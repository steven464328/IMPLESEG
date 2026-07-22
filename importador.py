import csv
import os
from datetime import datetime
from sqlmodel import Session
from app.database import engine
from app.models import Visitante, Equipo, HerramientaInventario

def limpiar_valor(valor):
    """Convierte celdas vacías del CSV a None para la base de datos."""
    if not valor or str(valor).strip() == "":
        return None
    return str(valor).strip()

def parsear_fecha(fecha_str):
    """Intenta convertir un texto a formato fecha de Python."""
    if not fecha_str or str(fecha_str).strip() == "":
        return None
    
    formatos = [
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", 
        "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S"
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(str(fecha_str).strip(), formato)
        except ValueError:
            continue
            
    print(f"⚠️ Advertencia: No se pudo reconocer el formato de fecha '{fecha_str}'. Se guardará la fecha actual.")
    return datetime.now()

def importar_visitantes(ruta_csv):
    """Importa el CSV de visitantes a la base de datos."""
    print(f"\n⏳ Leyendo archivo: {ruta_csv}...")
    
    try:
        with open(ruta_csv, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            contador = 0
            
            with Session(engine) as session:
                for row in reader:
                    # Mapea las columnas de tu CSV a los campos de la BD v2.
                    try:
                        nuevo_visitante = Visitante(
                            cedula=limpiar_valor(row.get('Cédula', row.get('CEDULA', '0'))),
                            nombre_completo=limpiar_valor(row.get('Nombre', row.get('NOMBRE', 'SIN NOMBRE'))),
                            empresa=limpiar_valor(row.get('Empresa', row.get('EMPRESA'))),
                            correo=limpiar_valor(row.get('Correo', row.get('CORREO'))),
                            area_visita=limpiar_valor(row.get('Área Visitada', row.get('AREA', 'N/A'))),
                            motivo_visita=limpiar_valor(row.get('Motivo', row.get('MOTIVO', 'N/A'))),
                            arl=limpiar_valor(row.get('ARL', 'N/A')),
                            numero_emergencia=limpiar_valor(row.get('Contacto Emergencia', row.get('EMERGENCIA', '0'))),
                            persona_recibe=limpiar_valor(row.get('Recibido Por', row.get('RECIBE', 'N/A'))),
                            # Fechas
                            fecha_ingreso=parsear_fecha(row.get('Fecha/Hora Ingreso', row.get('INGRESO'))),
                            # Manejo de la fecha de salida (si está vacía, sigue adentro)
                            fecha_salida=parsear_fecha(row.get('Fecha/Hora Salida', row.get('SALIDA'))) if limpiar_valor(row.get('Fecha/Hora Salida')) else None
                        )
                        session.add(nuevo_visitante)
                        contador += 1
                    except Exception as e:
                        print(f"❌ Error en fila: {row} -> {e}")
                
                session.commit()
                print(f"✅ ¡Éxito! Se importaron {contador} visitantes a la base de datos.")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ruta_csv}. Asegúrate de que el nombre esté bien escrito y termine en .csv")

def importar_equipos(ruta_csv):
    """Importa el CSV de Hojas de Vida a la base de datos."""
    print(f"\n⏳ Leyendo archivo: {ruta_csv}...")
    try:
        with open(ruta_csv, mode='r', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            contador = 0
            
            with Session(engine) as session:
                for row in reader:
                    try:
                        nuevo_equipo = Equipo(
                            empresa=limpiar_valor(row.get('EMPRESA', 'N/A')),
                            equipo=limpiar_valor(row.get('EQUIPO', f'TEMP-{contador}')),
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
                        contador += 1
                    except Exception as e:
                        print(f"❌ Error en fila: {row.get('EQUIPO')} -> {e}")
                        
                session.commit()
                print(f"✅ ¡Éxito! Se importaron {contador} equipos a la base de datos.")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo: {ruta_csv}")

if __name__ == "__main__":
    print("===========================================")
    print("🚀 IMPORTADOR DE DATOS IMPLESEG (CSV -> SQL)")
    print("===========================================")
    print("1. Importar Registro de Visitantes")
    print("2. Importar Hojas de Vida (Equipos)")
    print("3. Salir")
    
    opcion = input("\nElige una opción (1-3): ")
    
    if opcion == '1':
        ruta = input("Ingresa el nombre del archivo CSV de visitantes (Ej: Registro_Visitantes.csv): ")
        importar_visitantes(ruta)
    elif opcion == '2':
        ruta = input("Ingresa el nombre del archivo CSV de equipos (Ej: Hojas_Vida.csv): ")
        importar_equipos(ruta)
    else:
        print("Saliendo del importador...")