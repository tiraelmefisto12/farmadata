# crear_tablas_nube.py
# Ejecuta este script UNA SOLA VEZ para crear las 6 tablas y los usuarios
# iniciales (admin/cajero) en tu base de datos de Supabase.
#
# CÓMO USARLO:
# 1. Copia este archivo a la raíz de tu proyecto (junto a app.py, models.py).
# 2. En la terminal, define temporalmente la variable de entorno con tu
#    connection string de Supabase (reemplaza con la tuya real):
#
#    Windows (PowerShell):
#      $env:DATABASE_URL="postgresql://postgres:TU_PASSWORD@db.xxxx.supabase.co:5432/postgres"
#
# 3. Luego corre:
#      python crear_tablas_nube.py
#
# Esto crea las tablas vacías + 2 usuarios de prueba (admin/cajero).
# Después puedes cargar tus datos de prueba (medicamentos, ventas históricas)
# con tu script original, apuntando también a esta misma variable de entorno.

import os
from werkzeug.security import generate_password_hash
from database import Base, engine, SessionLocal
from models import Producto, Venta, ResumenDiario, Proveedor, Compra, Usuario

def main():
    if "DATABASE_URL" not in os.environ:
        print("⚠️  ADVERTENCIA: no encontré la variable DATABASE_URL.")
        print("   Esto va a crear las tablas en tu SQL Server LOCAL, no en la nube.")
        respuesta = input("   ¿Seguro que quieres continuar? (s/n): ")
        if respuesta.lower() != "s":
            print("Cancelado.")
            return

    print("Creando las 6 tablas en la base de datos...")
    Base.metadata.create_all(engine)
    print("✅ Tablas creadas: productos, ventas, resumen_diario, proveedores, compras, usuarios")

    db = SessionLocal()

    # Evita duplicar usuarios si el script se corre más de una vez
    existe_admin = db.query(Usuario).filter(Usuario.username == "admin").first()
    if not existe_admin:
        admin = Usuario(
            nombre        = "Administrador",
            username      = "admin",
            password_hash = generate_password_hash("admin123"),
            rol           = "admin",
            activo        = True
        )
        cajero = Usuario(
            nombre        = "Cajero Principal",
            username      = "cajero",
            password_hash = generate_password_hash("cajero123"),
            rol           = "cajero",
            activo        = True
        )
        db.add(admin)
        db.add(cajero)
        db.commit()
        print("✅ Usuarios creados: admin/admin123 y cajero/cajero123")
        print("   ⚠️ Cambia estas contraseñas después de la demo si el sistema queda público.")
    else:
        print("ℹ️  Los usuarios admin/cajero ya existían, no se duplicaron.")

    db.close()
    print("🎉 Listo. Tu base de datos en la nube está lista para usarse.")

if __name__ == "__main__":
    main()
