# cargar_datos_prueba.py
# Genera datos de prueba (30 medicamentos, 5 proveedores, 500 ventas
# históricas, resúmenes diarios y algunas compras) para que la demo en
# la nube no se vea vacía.
#
# CÓMO USARLO (con la misma variable de entorno ya activa en tu terminal):
#   python cargar_datos_prueba.py
#
# Si $env:DATABASE_URL no está definida, escribe en tu SQL Server local.

import os
import random
from datetime import datetime, timedelta, date

from database import SessionLocal
from models import Producto, Proveedor, Venta, Compra, ResumenDiario

random.seed(42)  # reproducible: siempre genera los mismos datos de prueba

# ---------------------------------------------------------
# 30 medicamentos con categorías (coinciden con las del dashboard)
# ---------------------------------------------------------
MEDICAMENTOS = [
    ("Paracetamol 500mg",        "Analgésico",       3.50),
    ("Ibuprofeno 400mg",         "Antiinflamatorio", 3.50),
    ("Aspirina 100mg",           "Analgésico",       1.80),
    ("Amoxicilina 500mg",        "Antibiótico",      8.00),
    ("Azitromicina 500mg",       "Antibiótico",      12.50),
    ("Ciprofloxacino 500mg",     "Antibiótico",      9.20),
    ("Metronidazol 500mg",       "Antibiótico",      6.50),
    ("Losartán 50mg",            "Cardiovascular",   6.00),
    ("Enalapril 10mg",           "Cardiovascular",   4.80),
    ("Amlodipino 5mg",           "Cardiovascular",   4.20),
    ("Simvastatina 20mg",        "Cardiovascular",   7.50),
    ("Clopidogrel 75mg",         "Cardiovascular",   15.00),
    ("Furosemida 40mg",          "Cardiovascular",   3.90),
    ("Metformina 850mg",         "Antidiabético",    6.00),
    ("Insulina NPH 100UI",       "Antidiabético",    45.00),
    ("Loratadina 10mg",          "Antialérgico",     4.20),
    ("Cetirizina 10mg",          "Antialérgico",     4.50),
    ("Diclofenaco 50mg",         "Antiinflamatorio", 3.20),
    ("Naproxeno 500mg",          "Antiinflamatorio", 5.50),
    ("Prednisona 20mg",          "Corticoide",       4.00),
    ("Dexametasona 4mg",         "Corticoide",       3.60),
    ("Omeprazol 20mg",           "Gastrointestinal", 5.50),
    ("Ranitidina 150mg",         "Gastrointestinal", 3.80),
    ("Salbutamol Inhalador",     "Respiratorio",     18.00),
    ("Bromuro de Ipratropio",    "Respiratorio",     22.00),
    ("Fluconazol 150mg",         "Otro",             7.00),
    ("Vitamina C 1000mg",        "Vitamina",         3.00),
    ("Vitamina D 1000UI",        "Vitamina",         3.50),
    ("Hierro 325mg",             "Vitamina",         4.00),
    ("Complejo B",               "Sistema Nervioso", 5.00),
]

PROVEEDORES = [
    ("Laboratorios Farma SAC",     "Juan Pérez",   "999-111-222", "juan@farmasac.com",   "Av. Industrial 123, Lima"),
    ("Distribuidora MedPlus",      "María García", "999-333-444", "maria@medplus.com",   "Jr. Comercio 456, Lima"),
    ("Genéricos del Perú SA",      "Ana Torres",   "999-777-888", "ana@genericosperu.com","Calle Real 321, Lima"),
    ("Importadora PharmaCorp",     "Carlos López", "999-555-666", "carlos@pharmcorp.com","Av. Argentina 789, Lima"),
    ("BioFarma Distribuciones",    "Luis Mendoza", "999-999-000", "luis@biofarma.com",   "Av. Grau 654, Lima"),
]

METODOS_PAGO = ["Efectivo", "Tarjeta", "Yape/Plin"]


def main():
    origen = "SUPABASE (nube)" if "DATABASE_URL" in os.environ else "SQL SERVER LOCAL"
    print(f"⚠️  Vas a cargar datos de prueba en: {origen}")

    db = SessionLocal()

    # -----------------------------------------------------
    # 1. PRODUCTOS
    # -----------------------------------------------------
    if db.query(Producto).count() > 0:
        print("ℹ️  Ya hay productos cargados, no se duplican.")
        productos_bd = db.query(Producto).all()
    else:
        print("📦 Creando 30 productos...")
        productos_bd = []
        hoy = date.today()
        for nombre, categoria, precio in MEDICAMENTOS:
            # Mezcla de vencimientos: vigentes, por vencer y vencidos (para
            # que se vea bien la pantalla de Alertas)
            r = random.random()
            if r < 0.10:
                venc = hoy - timedelta(days=random.randint(1, 20))       # vencido
            elif r < 0.25:
                venc = hoy + timedelta(days=random.randint(1, 29))       # por vencer
            else:
                venc = hoy + timedelta(days=random.randint(60, 700))     # vigente

            p = Producto(
                nombre=nombre,
                categoria=categoria,
                precio=precio,
                stock=random.randint(0, 150),
                stock_minimo=random.choice([5, 10, 15, 20]),
                fecha_vencimiento=venc
            )
            db.add(p)
            productos_bd.append(p)
        db.commit()
        for p in productos_bd:
            db.refresh(p)
        print(f"✅ {len(productos_bd)} productos creados.")

    # -----------------------------------------------------
    # 2. PROVEEDORES
    # -----------------------------------------------------
    if db.query(Proveedor).count() > 0:
        print("ℹ️  Ya hay proveedores cargados, no se duplican.")
        proveedores_bd = db.query(Proveedor).all()
    else:
        print("🏢 Creando 5 proveedores...")
        proveedores_bd = []
        for nombre, contacto, telefono, email, direccion in PROVEEDORES:
            prov = Proveedor(nombre=nombre, contacto=contacto, telefono=telefono,
                              email=email, direccion=direccion)
            db.add(prov)
            proveedores_bd.append(prov)
        db.commit()
        for pr in proveedores_bd:
            db.refresh(pr)
        print(f"✅ {len(proveedores_bd)} proveedores creados.")

    # -----------------------------------------------------
    # 3. VENTAS HISTÓRICAS (500, distribuidas en los últimos 14 días)
    # -----------------------------------------------------
    if db.query(Venta).count() > 0:
        print("ℹ️  Ya hay ventas cargadas, no se duplican.")
    else:
        print("🧾 Generando 500 ventas históricas...")
        contador_boleta = 0
        contador_factura = 0
        dias_atras = 14

        for i in range(500):
            producto = random.choice(productos_bd)
            cantidad = random.randint(1, 5)
            dia_offset = random.randint(0, dias_atras)
            hora = random.randint(7, 21)
            minuto = random.randint(0, 59)
            fecha_venta = datetime.now() - timedelta(days=dia_offset)
            fecha_venta = fecha_venta.replace(hour=hora, minute=minuto, second=0, microsecond=0)

            tipo = "Boleta" if random.random() < 0.85 else "Factura"
            if tipo == "Boleta":
                contador_boleta += 1
                numero = f"B001-{contador_boleta:06d}"
            else:
                contador_factura += 1
                numero = f"F001-{contador_factura:06d}"

            venta = Venta(
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                precio_total=round(producto.precio * cantidad, 2),
                fecha=fecha_venta,
                tipo_comprobante=tipo,
                numero_comprobante=numero,
                metodo_pago=random.choice(METODOS_PAGO),
                cliente_dni=None,
                cliente_nombre=None
            )
            db.add(venta)

        db.commit()
        print("✅ 500 ventas creadas.")

        # -----------------------------------------------------
        # 4. RESUMEN DIARIO (para que el gráfico "Ingresos últimos 7 días" no
        #    salga vacío, ya que normalmente solo lo llena el ETL por venta)
        # -----------------------------------------------------
        print("📊 Generando resumen_diario para los últimos 14 días...")
        for offset in range(dias_atras + 1):
            dia = date.today() - timedelta(days=offset)
            ventas_del_dia = db.query(Venta).filter(
                Venta.fecha >= datetime.combine(dia, datetime.min.time()),
                Venta.fecha < datetime.combine(dia + timedelta(days=1), datetime.min.time())
            ).all()

            if not ventas_del_dia:
                continue

            total_ventas = len(ventas_del_dia)
            total_ingresos = round(sum(v.precio_total for v in ventas_del_dia), 2)

            conteo_productos = {}
            for v in ventas_del_dia:
                conteo_productos[v.producto_id] = conteo_productos.get(v.producto_id, 0) + v.cantidad
            id_top = max(conteo_productos, key=conteo_productos.get)
            producto_top = db.query(Producto).filter(Producto.id == id_top).first()

            resumen = ResumenDiario(
                fecha=dia,
                total_ventas=total_ventas,
                total_ingresos=total_ingresos,
                producto_mas_vendido=producto_top.nombre if producto_top else "Sin ventas",
                fecha_generado=datetime.now()
            )
            db.add(resumen)

        db.commit()
        print("✅ Resúmenes diarios generados.")

    # -----------------------------------------------------
    # 5. COMPRAS (15 registros, para la pantalla de Compras)
    # -----------------------------------------------------
    if db.query(Compra).count() > 0:
        print("ℹ️  Ya hay compras cargadas, no se duplican.")
    else:
        print("🛒 Generando 15 compras de reabastecimiento...")
        for i in range(15):
            proveedor = random.choice(proveedores_bd)
            producto = random.choice(productos_bd)
            cantidad = random.randint(20, 100)
            precio_compra = round(producto.precio * 0.55, 2)  # margen simulado

            compra = Compra(
                proveedor_id=proveedor.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_compra=precio_compra,
                precio_total=round(precio_compra * cantidad, 2),
                fecha=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            db.add(compra)
        db.commit()
        print("✅ 15 compras creadas.")

    db.close()
    print("🎉 Datos de prueba cargados con éxito.")


if __name__ == "__main__":
    main()
