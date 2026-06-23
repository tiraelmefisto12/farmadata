# app.py
# Punto de entrada principal - aquí arranca la aplicación

from flask import Flask
from database import engine, Base

# Importamos los modelos para que se creen las tablas
import models

# Creamos la aplicación Flask
app = Flask(__name__)
app.secret_key = "farmadata_clave_secreta_2026"

# Creamos todas las tablas en la base de datos si no existen
#Base.metadata.create_all(bind=engine)

# Importamos las rutas (pantallas) de la app
from routes import *

if __name__ == "__main__":
    print("🚀 FarmaData iniciando...")
    print("📊 Abre tu navegador en: http://127.0.0.1:5000")
    app.run(debug=True)
