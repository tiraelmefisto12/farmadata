# tests/test_models.py
# Pruebas unitarias de los modelos (tablas de la base de datos)

from datetime import date, datetime
from models import Producto, Venta, ResumenDiario, Proveedor, Compra, Usuario


# =====================
# PRUEBAS DE PRODUCTO
# =====================
def test_crear_producto(db):
    """Verifica que se puede crear un producto correctamente"""
    producto = Producto(
        nombre    = "Paracetamol Test",
        categoria = "Analgésico",
        precio    = 2.50,
        stock     = 100
    )
    db.add(producto)
    db.commit()

    resultado = db.query(Producto).filter_by(nombre="Paracetamol Test").first()
    assert resultado is not None
    assert resultado.precio == 2.50
    assert resultado.stock == 100


def test_producto_stock_minimo_default(db):
    """Verifica que el stock mínimo tiene valor por defecto de 10"""
    producto = Producto(
        nombre    = "Ibuprofeno Test",
        categoria = "Antiinflamatorio",
        precio    = 3.50,
        stock     = 50
    )
    db.add(producto)
    db.commit()

    resultado = db.query(Producto).filter_by(nombre="Ibuprofeno Test").first()
    assert resultado.stock_minimo == 10


def test_producto_fecha_vencimiento_nullable(db):
    """Verifica que la fecha de vencimiento puede ser nula"""
    producto = Producto(
        nombre            = "Aspirina Test",
        categoria         = "Analgésico",
        precio            = 1.80,
        stock             = 200,
        fecha_vencimiento = None
    )
    db.add(producto)
    db.commit()

    resultado = db.query(Producto).filter_by(nombre="Aspirina Test").first()
    assert resultado.fecha_vencimiento is None


def test_producto_con_fecha_vencimiento(db):
    """Verifica que se puede registrar una fecha de vencimiento"""
    fecha = date(2027, 12, 31)
    producto = Producto(
        nombre            = "Vitamina C Test",
        categoria         = "Vitamina",
        precio            = 3.00,
        stock             = 150,
        fecha_vencimiento = fecha
    )
    db.add(producto)
    db.commit()

    resultado = db.query(Producto).filter_by(nombre="Vitamina C Test").first()
    assert resultado.fecha_vencimiento == fecha


# =====================
# PRUEBAS DE VENTA
# =====================
def test_crear_venta(db):
    """Verifica que se puede crear una venta correctamente"""
    producto = Producto(
        nombre="Omeprazol Test", categoria="Gastrointestinal",
        precio=5.50, stock=75
    )
    db.add(producto)
    db.commit()

    venta = Venta(
        producto_id     = producto.id,
        cantidad        = 2,
        precio_unitario = producto.precio,
        precio_total    = producto.precio * 2
    )
    db.add(venta)
    db.commit()

    resultado = db.query(Venta).filter_by(producto_id=producto.id).first()
    assert resultado is not None
    assert resultado.precio_total == 11.0


def test_venta_precio_total_calculado(db):
    """Verifica que el precio total es cantidad × precio unitario"""
    producto = Producto(
        nombre="Loratadina Test", categoria="Antialérgico",
        precio=4.20, stock=90
    )
    db.add(producto)
    db.commit()

    cantidad = 3
    venta = Venta(
        producto_id     = producto.id,
        cantidad        = cantidad,
        precio_unitario = producto.precio,
        precio_total    = producto.precio * cantidad
    )
    db.add(venta)
    db.commit()

    assert venta.precio_total == 4.20 * 3


# =====================
# PRUEBAS DE PROVEEDOR
# =====================
def test_crear_proveedor(db):
    """Verifica que se puede crear un proveedor correctamente"""
    proveedor = Proveedor(
        nombre    = "Laboratorio Test SAC",
        contacto  = "Juan Test",
        telefono  = "999-000-111",
        email     = "test@lab.com",
        direccion = "Av. Test 123"
    )
    db.add(proveedor)
    db.commit()

    resultado = db.query(Proveedor).filter_by(nombre="Laboratorio Test SAC").first()
    assert resultado is not None
    assert resultado.email == "test@lab.com"


def test_proveedor_campos_opcionales(db):
    """Verifica que los campos opcionales del proveedor pueden ser nulos"""
    proveedor = Proveedor(nombre="Proveedor Mínimo")
    db.add(proveedor)
    db.commit()

    resultado = db.query(Proveedor).filter_by(nombre="Proveedor Mínimo").first()
    assert resultado is not None
    assert resultado.contacto is None
    assert resultado.telefono is None


# =====================
# PRUEBAS DE USUARIO
# =====================
def test_crear_usuario(db):
    """Verifica que se puede crear un usuario con rol"""
    usuario = Usuario(
        nombre        = "Admin Test",
        username      = "admin_test",
        password_hash = "hash_simulado",
        rol           = "admin"
    )
    db.add(usuario)
    db.commit()

    resultado = db.query(Usuario).filter_by(username="admin_test").first()
    assert resultado is not None
    assert resultado.rol == "admin"
    assert resultado.activo == True


def test_usuario_cajero(db):
    """Verifica que se puede crear un usuario con rol cajero"""
    usuario = Usuario(
        nombre        = "Cajero Test",
        username      = "cajero_test",
        password_hash = "hash_simulado",
        rol           = "cajero"
    )
    db.add(usuario)
    db.commit()

    resultado = db.query(Usuario).filter_by(username="cajero_test").first()
    assert resultado.rol == "cajero"