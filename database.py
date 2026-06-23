# database.py
# Conexión a SQL Server

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Datos de conexión a SQL Server
SERVIDOR   = r"DESKTOP-QELTJMP\MSSQLSERVER2022"
USUARIO    = "sa"
CONTRASENA = "121002"
BASE_DATOS = "farmadata"

# Cadena de conexión para SQL Server
DATABASE_URL = (
    f"mssql+pyodbc://{USUARIO}:{CONTRASENA}@{SERVIDOR}/{BASE_DATOS}"
    f"?driver=ODBC+Driver+17+for+SQL+Server"
)

# Creamos el motor de conexión
engine = create_engine(DATABASE_URL, fast_executemany=True)

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
        