from app.database import engine
from sqlalchemy import text

with engine.begin() as conn:

    conn.execute(text("""
        ALTER TABLE impresoras
        ADD COLUMN IF NOT EXISTS tipo_conexion VARCHAR(10)
        NOT NULL DEFAULT 'RED'
    """))

    conn.execute(text("""
        ALTER TABLE impresoras
        ADD COLUMN IF NOT EXISTS nombre_windows VARCHAR(255)
    """))

    conn.execute(text("""
        ALTER TABLE impresoras
        ALTER COLUMN ip DROP NOT NULL
    """))

print("OK: tabla impresoras preparada para USB + RED")
