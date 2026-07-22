"""Utilidades compartidas para el módulo de Gestión Humana."""
import time
from datetime import datetime


def generar_codigo(prefijo: str) -> str:
    """Genera un código único con el mismo estilo del sistema original
    (ej: ASG-LXQP3F9, BAJA-LXQP4A2) basado en tiempo en base36."""
    base36 = ""
    n = int(time.time() * 1000)
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if n == 0:
        base36 = "0"
    while n > 0:
        n, rem = divmod(n, 36)
        base36 = digits[rem] + base36
    return f"{prefijo}-{base36}"


def fecha_actual_texto() -> str:
    """Formato dd/MM/yyyy HH:mm:ss, igual al usado en el Sheet original."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
