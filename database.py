# database.py
# Conexión a la base de datos
# - En LOCAL (tu máquina): sigue usando SQL Server, tal como siempre.
# - En la NUBE (Render/Supabase): usa PostgreSQL automáticamente si existe
#   la variable de entorno DATABASE_URL. No tienes que tocar nada más.

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ---------------------------------------------------------
# Configuración LOCAL (SQL Server) - se usa si NO hay DATABASE_URL
# ---------------------------------------------------------
SERVIDOR   = r"DESKTOP-QELTJMP\MSSQLSERVER2022"
USUARIO    = "sa"
CONTRASENA = "121002"
BASE_DATOS = "farmadata"

LOCAL_DATABASE_URL = (
    f"mssql+pyodbc://{USUARIO}:{CONTRASENA}@{SERVIDOR}/{BASE_DATOS}"
    f"?driver=ODBC+Driver+17+for+SQL+Server"
)

# ---------------------------------------------------------
# Si existe la variable de entorno DATABASE_URL (la pone Render
# automáticamente cuando la configuras), se usa esa (PostgreSQL en la nube).
# Si no existe, usamos la conexión local de SQL Server de siempre.
# ---------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", LOCAL_DATABASE_URL)

# Supabase a veces entrega la URL como "postgres://" en vez de
# "postgresql://" - SQLAlchemy necesita el segundo formato.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# fast_executemany solo aplica al driver de SQL Server (pyodbc);
# si estamos en PostgreSQL, se ignora ese parámetro.
if DATABASE_URL.startswith("mssql"):
    engine = create_engine(DATABASE_URL, fast_executemany=True)
else:
    engine = create_engine(DATABASE_URL)

# Creamos la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
class Base(DeclarativeBase):
    pass

def get_db():
    """Función para obtener una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()