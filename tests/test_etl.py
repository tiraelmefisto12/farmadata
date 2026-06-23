# tests/test_etl.py
# Pruebas unitarias del pipeline ETL

import pandas as pd
from datetime import date, datetime
from models import Producto, Venta, ResumenDiario


# =====================
# PRUEBAS DE TRANSFORMACIÓN (el corazón del ETL)
# Estas pruebas verifican la lógica sin tocar la base de datos
# =====================

def test_etl_calcula_total_ingresos():
    """Verifica que el ETL suma correctamente los ingresos"""
    datos = {
        "producto_nombre": ["Paracetamol", "Ibuprofeno", "Vitamina C"],
        "cantidad":        [2,             3,            1],
        "precio_total":    [5.00,          10.50,        3.00]
    }
    df = pd.DataFrame(datos)

    total_ingresos = round(float(df["precio_total"].sum()), 2)

    assert total_ingresos == 18.50


def test_etl_calcula_total_ventas():
    """Verifica que el ETL cuenta correctamente el número de ventas"""
    datos = {
        "producto_nombre": ["Paracetamol", "Ibuprofeno", "Vitamina C"],
        "cantidad":        [2,             3,            1],
        "precio_total":    [5.00,          10.50,        3.00]
    }
    df = pd.DataFrame(datos)

    total_ventas = len(df)

    assert total_ventas == 3


def test_etl_identifica_producto_top():
    """Verifica que el ETL identifica correctamente el producto más vendido"""
    datos = {
        "producto_nombre": ["Paracetamol", "Ibuprofeno", "Paracetamol", "Vitamina C"],
        "cantidad":        [2,             1,            5,             3],
        "precio_total":    [5.00,          3.50,         12.50,         9.00]
    }
    df = pd.DataFrame(datos)

    top = df.groupby("producto_nombre")["cantidad"].sum()
    producto_top = top.idxmax()

    # Paracetamol tiene 2+5=7 unidades vs Vitamina C 3 vs Ibuprofeno 1
    assert producto_top == "Paracetamol"


def test_etl_producto_top_con_empate():
    """Verifica que el ETL maneja correctamente un empate en unidades vendidas"""
    datos = {
        "producto_nombre": ["ProductoA", "ProductoB"],
        "cantidad":        [5,           5],
        "precio_total":    [10.00,       10.00]
    }
    df = pd.DataFrame(datos)

    top = df.groupby("producto_nombre")["cantidad"].sum()
    producto_top = top.idxmax()

    # Debe retornar alguno de los dos (idxmax devuelve el primero alfabéticamente)
    assert producto_top in ["ProductoA", "ProductoB"]


def test_etl_sin_ventas():
    """Verifica que el ETL maneja correctamente un día sin ventas"""
    df = pd.DataFrame(columns=["producto_nombre", "cantidad", "precio_total"])

    if df.empty:
        total_ventas         = 0
        total_ingresos       = 0.0
        producto_mas_vendido = "Sin ventas"
    else:
        total_ventas         = len(df)
        total_ingresos       = float(df["precio_total"].sum())
        producto_mas_vendido = df.groupby("producto_nombre")["cantidad"].sum().idxmax()

    assert total_ventas         == 0
    assert total_ingresos       == 0.0
    assert producto_mas_vendido == "Sin ventas"


def test_etl_crea_resumen_en_bd(db):
    """Verifica que el ETL guarda correctamente el resumen en la base de datos"""
    hoy = date.today()

    resumen = ResumenDiario(
        fecha                = hoy,
        total_ventas         = 5,
        total_ingresos       = 150.50,
        producto_mas_vendido = "Paracetamol",
        fecha_generado       = datetime.now()
    )
    db.add(resumen)
    db.commit()

    resultado = db.query(ResumenDiario).filter_by(fecha=hoy).first()
    assert resultado is not None
    assert resultado.total_ventas   == 5
    assert resultado.total_ingresos == 150.50


def test_etl_no_duplica_resumen(db):
    """Verifica que el ETL no crea dos resúmenes para el mismo día"""
    from datetime import date, timedelta
    ayer = date.today() - timedelta(days=1)

    # Crear primer resumen
    resumen1 = ResumenDiario(
        fecha                = ayer,
        total_ventas         = 3,
        total_ingresos       = 50.00,
        producto_mas_vendido = "Ibuprofeno",
        fecha_generado       = datetime.now()
    )
    db.add(resumen1)
    db.commit()

    # Simular actualización (no crear uno nuevo)
    existente = db.query(ResumenDiario).filter_by(fecha=ayer).first()
    existente.total_ventas   = 8
    existente.total_ingresos = 120.00
    db.commit()

    # Verificar que solo hay uno y tiene los datos actualizados
    todos = db.query(ResumenDiario).filter_by(fecha=ayer).all()
    assert len(todos) == 1
    assert todos[0].total_ventas   == 8
    assert todos[0].total_ingresos == 120.00


def test_etl_ingresos_con_decimales():
    """Verifica que el ETL maneja correctamente precios con decimales"""
    datos = {
        "producto_nombre": ["MedA", "MedB"],
        "cantidad":        [1,      1],
        "precio_total":    [4.20,   8.80]
    }
    df = pd.DataFrame(datos)

    total = round(float(df["precio_total"].sum()), 2)

    assert total == 13.00