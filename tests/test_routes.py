# tests/test_routes.py
# Pruebas unitarias de las rutas (pantallas y acciones)

from models import Producto, Venta, Proveedor, Compra, Usuario
from werkzeug.security import generate_password_hash


# =====================
# PRUEBAS DE AUTENTICACIÓN
# =====================
def test_login_redirige_sin_sesion(client):
    """Verifica que sin sesión el dashboard redirige al login"""
    respuesta = client.get("/")
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_login_exitoso(client, db):
    """Verifica que el login funciona con credenciales correctas"""
    usuario = Usuario(
        nombre        = "Admin Prueba",
        username      = "admin_prueba",
        password_hash = generate_password_hash("admin123"),
        rol           = "admin"
    )
    db.add(usuario)
    db.commit()

    respuesta = client.post("/login", data={
        "username": "admin_prueba",
        "password": "admin123"
    })
    assert respuesta.status_code == 302


def test_login_fallido(client):
    """Verifica que el login falla con credenciales incorrectas"""
    respuesta = client.post("/login", data={
        "username": "noexiste",
        "password": "wrongpass"
    }, follow_redirects=True)
    assert respuesta.status_code == 200
    assert "incorrectos" in respuesta.data.decode("utf-8")


def test_logout(client_admin):
    """Verifica que el logout cierra la sesión correctamente"""
    respuesta = client_admin.get("/logout")
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


# =====================
# PRUEBAS DE DASHBOARD
# =====================
def test_dashboard_carga_con_admin(client_admin):
    """Verifica que el dashboard carga correctamente con sesión admin"""
    respuesta = client_admin.get("/")
    assert respuesta.status_code == 200
    assert "Dashboard" in respuesta.data.decode("utf-8")


def test_dashboard_carga_con_cajero(client_cajero):
    """Verifica que el dashboard carga correctamente con sesión cajero"""
    respuesta = client_cajero.get("/")
    assert respuesta.status_code == 200


# =====================
# PRUEBAS DE PRODUCTOS
# =====================
def test_productos_carga_correctamente(client_admin):
    """Verifica que la pantalla de productos carga correctamente"""
    respuesta = client_admin.get("/productos")
    assert respuesta.status_code == 200
    assert "Productos" in respuesta.data.decode("utf-8")


def test_agregar_producto(client_admin, db):
    """Verifica que se puede agregar un producto vía POST"""
    respuesta = client_admin.post("/productos/agregar", data={
        "nombre"    : "Producto Test Ruta",
        "categoria" : "Analgésico",
        "precio"    : "5.00",
        "stock"     : "50",
        "stock_minimo": "10"
    })
    assert respuesta.status_code == 302

    producto = db.query(Producto).filter_by(nombre="Producto Test Ruta").first()
    assert producto is not None
    assert producto.precio == 5.00


def test_buscador_productos(client_admin, db):
    """Verifica que el buscador filtra correctamente por nombre"""
    p1 = Producto(nombre="Vitamina Test", categoria="Vitamina", precio=3.0, stock=50)
    p2 = Producto(nombre="Antibiotico Test", categoria="Antibiótico", precio=8.0, stock=30)
    db.add_all([p1, p2])
    db.commit()

    respuesta = client_admin.get("/productos?buscar=Vitamina")
    contenido = respuesta.data.decode("utf-8")

    assert "Vitamina Test" in contenido
    assert "Antibiotico Test" not in contenido


# =====================
# PRUEBAS DE VENTAS
# =====================
def test_ventas_carga_correctamente(client_cajero):
    """Verifica que la pantalla de ventas carga correctamente"""
    respuesta = client_cajero.get("/ventas")
    assert respuesta.status_code == 200


def test_venta_reduce_stock(client_cajero, db):
    """Verifica que registrar una venta reduce el stock del producto"""
    producto = Producto(
        nombre="Med Stock Test", categoria="Analgésico",
        precio=5.00, stock=20
    )
    db.add(producto)
    db.commit()
    producto_id   = producto.id
    stock_inicial = producto.stock

    client_cajero.post("/ventas/registrar", data={
        "producto_id[]"   : [str(producto_id)],
        "cantidad[]"      : ["3"],
        "tipo_comprobante": "Boleta",
        "metodo_pago"     : "Efectivo",
        "cliente_nombre"  : "Test Cliente"
    })

    actualizado = db.query(Producto).filter_by(id=producto_id).first()
    assert actualizado.stock == stock_inicial - 3


def test_venta_stock_insuficiente(client_cajero, db):
    """Verifica que el sistema rechaza ventas cuando no hay stock suficiente"""
    producto = Producto(
        nombre="Med Sin Stock", categoria="Vitamina",
        precio=3.00, stock=2
    )
    db.add(producto)
    db.commit()
    producto_id = producto.id

    client_cajero.post("/ventas/registrar", data={
        "producto_id[]"   : [str(producto_id)],
        "cantidad[]"      : ["10"],
        "tipo_comprobante": "Boleta",
        "metodo_pago"     : "Efectivo"
    })

    actualizado = db.query(Producto).filter_by(id=producto_id).first()
    assert actualizado.stock == 2


def test_venta_genera_numero_comprobante(client_cajero, db):
    """Verifica que al registrar una venta se genera número de comprobante"""
    producto = Producto(
        nombre="Med Comprobante Test", categoria="Vitamina",
        precio=4.00, stock=30
    )
    db.add(producto)
    db.commit()
    producto_id = producto.id

    client_cajero.post("/ventas/registrar", data={
        "producto_id[]"   : [str(producto_id)],
        "cantidad[]"      : ["1"],
        "tipo_comprobante": "Boleta",
        "metodo_pago"     : "Yape/Plin"
    })

    venta = db.query(Venta).filter_by(producto_id=producto_id).first()
    assert venta is not None
    assert venta.numero_comprobante is not None
    assert "B001-" in venta.numero_comprobante


# =====================
# PRUEBAS DE ALERTAS
# =====================
def test_alertas_carga_correctamente(client_cajero):
    """Verifica que la pantalla de alertas carga correctamente"""
    respuesta = client_cajero.get("/alertas")
    assert respuesta.status_code == 200


def test_alertas_detecta_stock_bajo(client_admin, db):
    """Verifica que las alertas detectan productos con stock bajo"""
    producto = Producto(
        nombre="Med Stock Bajo Test", categoria="Analgésico",
        precio=2.50, stock=3, stock_minimo=10
    )
    db.add(producto)
    db.commit()

    respuesta = client_admin.get("/alertas")
    contenido = respuesta.data.decode("utf-8")
    assert "Med Stock Bajo Test" in contenido


# =====================
# PRUEBAS DE PROVEEDORES Y COMPRAS
# =====================
def test_proveedores_solo_admin(client_cajero):
    """Verifica que el cajero no puede acceder a proveedores"""
    respuesta = client_cajero.get("/proveedores")
    assert respuesta.status_code == 302


def test_agregar_proveedor(client_admin, db):
    """Verifica que se puede agregar un proveedor vía POST"""
    respuesta = client_admin.post("/proveedores/agregar", data={
        "nombre"   : "Proveedor Test SA",
        "contacto" : "Juan Test",
        "telefono" : "999-000-111",
        "email"    : "test@proveedor.com",
        "direccion": "Av. Test 123"
    })
    assert respuesta.status_code == 302

    proveedor = db.query(Proveedor).filter_by(nombre="Proveedor Test SA").first()
    assert proveedor is not None


def test_compra_aumenta_stock(client_admin, db):
    """Verifica que registrar una compra aumenta el stock del producto"""
    producto = Producto(
        nombre="Med Compra Test", categoria="Antibiótico",
        precio=8.00, stock=10
    )
    proveedor = Proveedor(nombre="Proveedor Stock Test")
    db.add_all([producto, proveedor])
    db.commit()
    producto_id  = producto.id
    stock_inicial = producto.stock

    client_admin.post("/compras/registrar", data={
        "proveedor_id" : str(proveedor.id),
        "producto_id"  : str(producto_id),
        "cantidad"     : "50",
        "precio_compra": "4.00"
    })

    actualizado = db.query(Producto).filter_by(id=producto_id).first()
    assert actualizado.stock == stock_inicial + 50

def test_eliminar_producto_sin_ventas(client_admin, db):
    """Verifica que se puede eliminar un producto sin ventas"""
    producto = Producto(
        nombre="Producto Eliminar Test", categoria="Vitamina",
        precio=3.00, stock=10
    )
    db.add(producto)
    db.commit()
    producto_id = producto.id

    respuesta = client_admin.post(f"/productos/eliminar/{producto_id}")
    assert respuesta.status_code == 302

    eliminado = db.query(Producto).filter_by(id=producto_id).first()
    assert eliminado is None


def test_eliminar_proveedor(client_admin, db):
    """Verifica que se puede eliminar un proveedor"""
    proveedor = Proveedor(nombre="Proveedor Eliminar Test")
    db.add(proveedor)
    db.commit()
    proveedor_id = proveedor.id

    respuesta = client_admin.post(f"/proveedores/eliminar/{proveedor_id}")
    assert respuesta.status_code == 302

    eliminado = db.query(Proveedor).filter_by(id=proveedor_id).first()
    assert eliminado is None


def test_etl_ejecutar_ruta(client_admin):
    """Verifica que la ruta del ETL ejecuta y redirige correctamente"""
    respuesta = client_admin.post("/etl/ejecutar")
    assert respuesta.status_code == 302


def test_comprobante_ver(client_cajero, db):
    """Verifica que se puede ver un comprobante existente"""
    producto = Producto(
        nombre="Med Comprobante Ver", categoria="Vitamina",
        precio=4.00, stock=30
    )
    db.add(producto)
    db.commit()

    venta = Venta(
        producto_id        = producto.id,
        cantidad            = 1,
        precio_unitario     = 4.00,
        precio_total        = 4.00,
        tipo_comprobante    = "Boleta",
        numero_comprobante  = "B001-TEST01",
        metodo_pago         = "Efectivo"
    )
    db.add(venta)
    db.commit()

    respuesta = client_cajero.get("/ventas/comprobante/B001-TEST01")
    assert respuesta.status_code == 200


def test_compras_carga_correctamente(client_admin):
    """Verifica que la pantalla de compras carga correctamente"""
    respuesta = client_admin.get("/compras")
    assert respuesta.status_code == 200


def test_proveedores_carga_correctamente(client_admin):
    """Verifica que la pantalla de proveedores carga correctamente"""
    respuesta = client_admin.get("/proveedores")
    assert respuesta.status_code == 200


def test_compras_solo_admin(client_cajero):
    """Verifica que el cajero no puede acceder a compras"""
    respuesta = client_cajero.get("/compras")
    assert respuesta.status_code == 302