# EJ Soluciones — Plataforma de Automatización de Procesos
### Módulo 1: Área de Sistemas · Hojas de Vida de Equipos

Sistema web modular, pensado para crecer: cada nueva área (Contabilidad,
Almacén, Recepción...) se agrega como un módulo independiente sin tocar lo
que ya funciona.

---

## 1. ¿Cómo funciona la arquitectura?

```
┌─────────────────────────────────────────────┐
│   UN equipo actúa como SERVIDOR              │
│   (ej: tu PC de sistemas, o el servidor EXSI)│
│                                               │
│   Aquí se instala Python + este proyecto     │
│   Aquí vive la base de datos (un solo lugar) │
└───────────────────┬───────────────────────────┘
                    │  red local (WiFi/cable)
        ┌───────────┼───────────┬────────────┐
        ▼           ▼           ▼            ▼
   IMPLE-001-A  IMPLE-002-A  IMPLE-003-A  Tu celular/portátil
   (solo abre  (solo abre   (solo abre    (solo abre
    el navegador) el navegador) el navegador)  el navegador)
```

**Ningún equipo cliente necesita instalar nada.** Solo abren el navegador y
entran a la dirección IP del servidor. Esto resuelve exactamente lo que
pediste: "instalar o mover en diferentes equipos que la requieran" — el
software vive en un solo lugar, y se puede migrar ese único lugar a otra
máquina simplemente copiando la carpeta.

---

## 2. Instalación (primera vez, en el equipo que hará de servidor)

### Requisitos
- Python 3.10 o superior instalado ([python.org](https://www.python.org/downloads/))
- Windows, con "Add Python to PATH" marcado durante la instalación

### Pasos

```bash
# 1. Entra a la carpeta del proyecto
cd ej_sistemas

# 2. Crea el entorno virtual (aísla las dependencias del resto del sistema)
python -m venv venv

# 3. Activa el entorno virtual
venv\Scripts\activate          # En Windows
source venv/bin/activate       # En Mac/Linux

# 4. Instala las dependencias
pip install -r requirements.txt

# 5. Ejecuta el servidor
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abre en el navegador: **http://localhost:8000**

Para que los demás equipos de la red accedan, usa la IP de este equipo:
**http://IP-DEL-SERVIDOR:8000** (ej: `http://192.168.1.149:8000`)

Para saber la IP del servidor en Windows: `ipconfig` (busca "Dirección IPv4").

---

## 3. Migrar tus datos actuales del Google Sheet

1. En tu Google Sheet, ve a la pestaña de datos → **Archivo → Descargar →
   Valores separados por comas (.csv)**
2. Guarda el archivo como `hojas_de_vida.csv` dentro de la carpeta `ej_sistemas`
3. Ejecuta:
   ```bash
   venv\Scripts\python importar_desde_sheets.py hojas_de_vida.csv
   ```
4. El script te dirá cuántos registros creó y actualizó. **Nada se pierde**:
   cualquier columna que no reconozca se guarda igual dentro del registro.

Puedes correr este importador las veces que quieras — si el código de equipo
ya existe, actualiza sus datos en vez de duplicarlo.

---

## 4. Mover el sistema a otro equipo

1. Copia toda la carpeta `ej_sistemas` (incluyendo la carpeta `data/`, ahí
   está tu base de datos con toda la información) al nuevo equipo.
2. Repite los pasos de instalación (crear venv, instalar dependencias).
3. Ejecuta el servidor. Toda la información migra con la carpeta.

> 💡 Recomendación: usa el mismo servidor donde ya tienes montado el ExSi /
> servidor de virtualización (IMPLE019 en tu inventario), ya que está encendido
> permanentemente y toda la red ya lo puede alcanzar.

---

## 5. ¿Qué incluye este primer módulo?

- **CRUD completo**: crear, consultar, modificar y eliminar hojas de vida
- **Búsqueda y filtros combinables**: por empresa, área, tipo de equipo,
  estado, usuario asignado, o búsqueda libre (IP, serial, marca, etc.)
- **Dashboard de analítica en tiempo real**:
  - Total de equipos y distribución por área/estado/tipo/marca/sistema operativo
  - Detección automática de equipos "en riesgo" (lentos, dañados, sin memoria...)
  - Equipos sin mantenimiento registrado (deuda técnica pendiente)
  - Valor estimado del parque de equipos (proyección financiera del activo)
- **Auditoría automática**: cada creación, modificación (campo por campo) y
  eliminación queda registrada con fecha y usuario — trazabilidad total
- **Exportación a CSV**: compatible con Excel/Sheets en cualquier momento
- **Arquitectura extensible sin migraciones**: el checklist de software
  instalado (Java, AnyDesk, 3CX, Office, GLPI, Wazuh...) vive en un campo
  flexible — agregar un programa nuevo al checklist no requiere tocar la
  base de datos

---

## 6. Próximos pasos sugeridos (roadmap de crecimiento)

Cuando quieras, seguimos con:
1. **Autenticación de usuarios** (login con roles: administrador / solo lectura)
2. **Alertas automáticas** (ej: aviso cuando vence una licencia de antivirus)
3. **Módulo de Contabilidad** (siguiente área, como módulo independiente)
4. **Migración a PostgreSQL** si el volumen de datos crece bastante
5. **Generación de PDF de la hoja de vida** individual de cada equipo, con
   el mismo estilo de tus reportes de visita técnica
6. **App para escanear código de equipo con el celular** y abrir su hoja de
   vida directamente

---

## Estructura del proyecto

```
ej_sistemas/
├── app/
│   ├── main.py              → Arranque de la aplicación
│   ├── models.py            → Estructura de datos (Equipo, Empresa, Historial)
│   ├── database.py          → Conexión a la base de datos
│   ├── routers/
│   │   ├── equipos.py       → CRUD y búsqueda
│   │   └── dashboard.py     → Analítica y proyecciones
│   ├── templates/index.html → Interfaz
│   └── static/               → Estilos y lógica del frontend
├── data/ej_sistemas.db      → Tu base de datos (se crea sola al arrancar)
├── importar_desde_sheets.py → Migrador desde Google Sheets
└── requirements.txt
```
