# etl.py
# Pipeline ETL - Extract, Transform, Load
# Este archivo procesa las ventas y genera el resumen diario

import pandas as pd
from sqlalchemy import text
from database import engine, SessionLocal
from models import ResumenDiario
from datetime import date, datetime

def ejecutar_etl():
    """
    Pipeline ETL completo:
    1. EXTRACT  - Extrae las ventas de hoy desde la base de datos
    2. TRANSFORM - Calcula totales y producto más vendido
    3. LOAD     - Guarda el resumen en la tabla resumen_diario
    """

    print("🔄 Iniciando pipeline ETL...")
    hoy = date.today()

    # =====================
    # PASO 1: EXTRACT
    # Leemos las ventas de hoy con Pandas
    # =====================
    print("📤 EXTRACT: Leyendo ventas de hoy...")

    query = text("""
    SELECT v.id, v.cantidad, v.precio_total, p.nombre as producto_nombre
    FROM ventas v
    JOIN productos p ON v.producto_id = p.id
    WHERE CAST(v.fecha AS DATE) = :hoy
""")

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"hoy": str(hoy)})

    print(f"   → {len(df)} ventas encontradas para hoy")

    # =====================
    # PASO 2: TRANSFORM
    # Calculamos las métricas con Pandas
    # =====================
    print("⚙️  TRANSFORM: Calculando métricas...")

    if df.empty:
        # Si no hay ventas hoy
        total_ventas         = 0
        total_ingresos       = 0.0
        producto_mas_vendido = "Sin ventas"
        print("   → No hay ventas hoy")
    else:
        # Total de ventas (número de transacciones)
        total_ventas = len(df)

        # Total de ingresos (suma de todos los precios_total)
        total_ingresos = round(float(df["precio_total"].sum()), 2)

        # Producto más vendido (el que más cantidad acumuló)
        top = df.groupby("producto_nombre")["cantidad"].sum()
        producto_mas_vendido = top.idxmax()

        print(f"   → Total ventas: {total_ventas}")
        print(f"   → Total ingresos: S/. {total_ingresos}")
        print(f"   → Producto top: {producto_mas_vendido}")

    # =====================
    # PASO 3: LOAD
    # Guardamos o actualizamos el resumen en la BD
    # =====================
    print("📥 LOAD: Guardando resumen en base de datos...")

    db = SessionLocal()

    # Verificar si ya existe resumen para hoy
    resumen = db.query(ResumenDiario).filter(ResumenDiario.fecha == hoy).first()

    if resumen:
        # Actualizar el existente
        resumen.total_ventas         = total_ventas
        resumen.total_ingresos       = total_ingresos
        resumen.producto_mas_vendido = producto_mas_vendido
        resumen.fecha_generado       = datetime.now()
        print("   → Resumen actualizado")
    else:
        # Crear uno nuevo
        nuevo_resumen = ResumenDiario(
            fecha                = hoy,
            total_ventas         = total_ventas,
            total_ingresos       = total_ingresos,
            producto_mas_vendido = producto_mas_vendido,
            fecha_generado       = datetime.now()
        )
        db.add(nuevo_resumen)
        print("   → Resumen creado")

    db.commit()
    db.close()
    print("✅ ETL completado exitosamente!")
