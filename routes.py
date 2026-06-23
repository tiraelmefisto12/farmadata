# routes.py
# Aquí definimos todas las pantallas y acciones de la app

from flask import render_template, request, redirect, url_for, jsonify, flash, session
from functools import wraps
from werkzeug.security import check_password_hash
from app import app
from database import SessionLocal
from models import Producto, Venta, ResumenDiario, Proveedor, Compra, Usuario
from etl import ejecutar_etl
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract


# =====================
# AUTENTICACIÓN
# =====================
def login_required(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorado

def admin_required(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        if session.get("rol") != "admin":
            flash("No tienes permiso para acceder a esa sección.")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorado

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = SessionLocal()
        usuario = db.query(Usuario).filter(
            Usuario.username == username,
            Usuario.activo == True
        ).first()
        db.close()

        if usuario and check_password_hash(usuario.password_hash, password):
            session["usuario_id"] = usuario.id
            session["nombre"]     = usuario.nombre
            session["rol"]        = usuario.rol
            return redirect(url_for("dashboard"))

        flash("Usuario o contraseña incorrectos.")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =====================
# DASHBOARD PRINCIPAL
# =====================
@app.route("/")
@login_required
def dashboard():
    db = SessionLocal()
    hoy = date.today()

    resumen  = db.query(ResumenDiario).filter(ResumenDiario.fecha == hoy).first()
    alertas  = db.query(Producto).filter(Producto.stock <= Producto.stock_minimo).count()
    total_productos = db.query(Producto).count()

    inicio_semana = hoy - timedelta(days=7)
    ingresos_semana = db.query(func.sum(Venta.precio_total)).filter(
        Venta.fecha >= inicio_semana
    ).scalar() or 0

    ultimos = db.query(ResumenDiario).order_by(ResumenDiario.fecha.desc()).limit(7).all()
    ultimos.reverse()

    cat_data = db.query(
        Producto.categoria,
        func.sum(Venta.precio_total)
    ).join(Venta, Producto.id == Venta.producto_id).group_by(Producto.categoria).all()

    top_data = db.query(
        Producto.nombre,
        func.sum(Venta.cantidad)
    ).join(Venta, Producto.id == Venta.producto_id).group_by(
        Producto.nombre
    ).order_by(func.sum(Venta.cantidad).desc()).limit(5).all()

    hora_col = extract('hour', Venta.fecha)
    horas_data = db.query(
        hora_col.label('hora'),
        func.count(Venta.id)
    ).group_by(hora_col).order_by(hora_col).all()

    db.close()

    return render_template("index.html",
        resumen          = resumen,
        alertas          = alertas,
        total_productos  = total_productos,
        ingresos_semana  = round(float(ingresos_semana), 2),
        fechas           = [str(r.fecha) for r in ultimos],
        ingresos         = [float(r.total_ingresos) for r in ultimos],
        categorias       = [c[0] for c in cat_data],
        cat_ingresos     = [float(c[1]) for c in cat_data],
        top_nombres      = [t[0] for t in top_data],
        top_cantidades   = [int(t[1]) for t in top_data],
        horas            = [f"{int(h[0])}:00" for h in horas_data],
        horas_ventas     = [int(h[1]) for h in horas_data],
    )


# =====================
# PRODUCTOS
# =====================
@app.route("/productos")
@login_required
def productos():
    db = SessionLocal()
    busqueda = request.args.get("buscar", "")
    hoy = date.today()
    alerta_dias = 30

    if busqueda:
        lista = db.query(Producto).filter(
            Producto.nombre.ilike(f"%{busqueda}%")
        ).order_by(Producto.nombre).all()
    else:
        lista = db.query(Producto).order_by(Producto.nombre).all()

    db.close()
    return render_template("productos.html",
        productos    = lista,
        busqueda     = busqueda,
        hoy          = hoy,
        alerta_dias  = alerta_dias
    )

@app.route("/productos/agregar", methods=["POST"])
@login_required
def agregar_producto():
    db = SessionLocal()
    fecha_venc = request.form.get("fecha_vencimiento")

    nuevo = Producto(
        nombre            = request.form["nombre"],
        categoria         = request.form["categoria"],
        precio            = float(request.form["precio"]),
        stock             = int(request.form["stock"]),
        stock_minimo      = int(request.form.get("stock_minimo", 10)),
        fecha_vencimiento = fecha_venc if fecha_venc else None
    )
    db.add(nuevo)
    db.commit()
    db.close()
    return redirect(url_for("productos"))

@app.route("/productos/eliminar/<int:id>", methods=["POST"])
@admin_required
def eliminar_producto(id):
    db = SessionLocal()
    producto = db.query(Producto).filter(Producto.id == id).first()
    if producto:
        if len(producto.ventas) == 0:
            db.delete(producto)
            db.commit()
    db.close()
    return redirect(url_for("productos"))


# =====================
# VENTAS (con carrito de varios productos)
# =====================
@app.route("/ventas")
@login_required
def ventas():
    db = SessionLocal()
    lista     = db.query(Venta).join(Producto).order_by(Venta.fecha.desc()).limit(50).all()
    for v in lista:
        _ = v.producto.nombre
    productos = db.query(Producto).filter(Producto.stock > 0).all()
    db.close()
    return render_template("ventas.html", ventas=lista, productos=productos)

@app.route("/ventas/registrar", methods=["POST"])
@login_required
def registrar_venta():
    db = SessionLocal()

    producto_ids     = request.form.getlist("producto_id[]")
    cantidades       = request.form.getlist("cantidad[]")
    tipo_comprobante = request.form["tipo_comprobante"]
    metodo_pago      = request.form["metodo_pago"]
    cliente_dni      = request.form.get("cliente_dni", "").strip() or None
    cliente_nombre   = request.form.get("cliente_nombre", "").strip() or None

    if not producto_ids:
        db.close()
        return redirect(url_for("ventas"))

    # Validar stock de TODOS los productos antes de registrar cualquiera
    items = []
    for pid, cant in zip(producto_ids, cantidades):
        producto = db.query(Producto).filter(Producto.id == int(pid)).first()
        cantidad = int(cant)
        if not producto or producto.stock < cantidad:
            db.close()
            flash(f"Stock insuficiente para {producto.nombre if producto else 'un producto'}.")
            return redirect(url_for("ventas"))
        items.append((producto, cantidad))

    # Generar número de comprobante UNA sola vez para todo el carrito
    prefijo = "B001-" if tipo_comprobante == "Boleta" else "F001-"
    cantidad_emitidos = db.query(Venta.numero_comprobante).filter(
        Venta.tipo_comprobante == tipo_comprobante
    ).distinct().count()
    numero_comprobante = f"{prefijo}{cantidad_emitidos + 1:06d}"

    for producto, cantidad in items:
        venta = Venta(
            producto_id        = producto.id,
            cantidad            = cantidad,
            precio_unitario     = producto.precio,
            precio_total        = producto.precio * cantidad,
            tipo_comprobante    = tipo_comprobante,
            numero_comprobante  = numero_comprobante,
            metodo_pago         = metodo_pago,
            cliente_dni         = cliente_dni,
            cliente_nombre      = cliente_nombre
        )
        producto.stock -= cantidad
        db.add(venta)

    db.commit()
    db.close()

    ejecutar_etl()

    return redirect(url_for("ver_comprobante", numero=numero_comprobante))

@app.route("/ventas/comprobante/<numero>")
@login_required
def ver_comprobante(numero):
    db = SessionLocal()
    items = db.query(Venta).filter(Venta.numero_comprobante == numero).all()
    for v in items:
        _ = v.producto.nombre
    db.close()

    if not items:
        return redirect(url_for("ventas"))

    primero = items[0]
    total = sum(v.precio_total for v in items)

    return render_template("comprobante.html", items=items, venta=primero, total=total)


# =====================
# ALERTAS
# =====================
@app.route("/alertas")
@login_required
def alertas():
    db = SessionLocal()
    hoy = date.today()
    limite_vencimiento = hoy + timedelta(days=30)

    lista = db.query(Producto).filter(
        Producto.stock <= Producto.stock_minimo
    ).all()

    por_vencer = db.query(Producto).filter(
        Producto.fecha_vencimiento <= limite_vencimiento
    ).order_by(Producto.fecha_vencimiento).all()

    db.close()
    return render_template("alertas.html",
        alertas    = lista,
        por_vencer = por_vencer,
        hoy        = hoy
    )


# =====================
# API DATOS DASHBOARD (para las gráficas)
# =====================
@app.route("/api/dashboard-data")
@login_required
def dashboard_data():
    db = SessionLocal()
    ultimos = db.query(ResumenDiario).order_by(ResumenDiario.fecha.desc()).limit(7).all()
    ultimos.reverse()
    db.close()

    datos = {
        "fechas":   [str(r.fecha) for r in ultimos],
        "ingresos": [r.total_ingresos for r in ultimos],
        "ventas":   [r.total_ventas for r in ultimos]
    }
    return jsonify(datos)


# =====================
# PROVEEDORES
# =====================
@app.route("/proveedores")
@admin_required
def proveedores():
    db = SessionLocal()
    lista = db.query(Proveedor).order_by(Proveedor.nombre).all()
    db.close()
    return render_template("proveedores.html", proveedores=lista)

@app.route("/proveedores/agregar", methods=["POST"])
@admin_required
def agregar_proveedor():
    db = SessionLocal()
    nuevo = Proveedor(
        nombre    = request.form["nombre"],
        contacto  = request.form.get("contacto"),
        telefono  = request.form.get("telefono"),
        email     = request.form.get("email"),
        direccion = request.form.get("direccion")
    )
    db.add(nuevo)
    db.commit()
    db.close()
    return redirect(url_for("proveedores"))

@app.route("/proveedores/eliminar/<int:id>", methods=["POST"])
@admin_required
def eliminar_proveedor(id):
    db = SessionLocal()
    proveedor = db.query(Proveedor).filter(Proveedor.id == id).first()
    if proveedor:
        db.delete(proveedor)
        db.commit()
    db.close()
    return redirect(url_for("proveedores"))


# =====================
# COMPRAS
# =====================
@app.route("/compras")
@admin_required
def compras():
    db = SessionLocal()
    lista       = db.query(Compra).order_by(Compra.fecha.desc()).limit(50).all()
    for c in lista:
        _ = c.proveedor.nombre
        _ = c.producto.nombre
    proveedores = db.query(Proveedor).order_by(Proveedor.nombre).all()
    productos   = db.query(Producto).order_by(Producto.nombre).all()
    db.close()
    return render_template("compras.html",
        compras     = lista,
        proveedores = proveedores,
        productos   = productos
    )

@app.route("/compras/registrar", methods=["POST"])
@admin_required
def registrar_compra():
    db = SessionLocal()
    proveedor_id  = int(request.form["proveedor_id"])
    producto_id   = int(request.form["producto_id"])
    cantidad      = int(request.form["cantidad"])
    precio_compra = float(request.form["precio_compra"])

    compra = Compra(
        proveedor_id  = proveedor_id,
        producto_id   = producto_id,
        cantidad      = cantidad,
        precio_compra = precio_compra,
        precio_total  = round(precio_compra * cantidad, 2)
    )
    db.add(compra)

    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        producto.stock += cantidad

    db.commit()
    db.close()
    return redirect(url_for("compras"))


# =====================
# ETL
# =====================
@app.route("/etl/ejecutar", methods=["POST"])
@admin_required
def ejecutar_etl_ruta():
    ejecutar_etl()
    return redirect(url_for("dashboard"))