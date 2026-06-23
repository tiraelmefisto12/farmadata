# models.py
# Aquí definimos las tablas de nuestra base de datos

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# =====================
# TABLA: productos
# =====================
class Producto(Base):
    __tablename__ = "productos"

    id              = Column(Integer, primary_key=True, index=True)
    nombre          = Column(String, nullable=False)
    categoria       = Column(String, nullable=False)
    precio          = Column(Float, nullable=False)
    stock           = Column(Integer, nullable=False)
    stock_minimo    = Column(Integer, default=10)
    fecha_registro  = Column(DateTime, default=datetime.now)
    fecha_vencimiento = Column(Date, nullable=True)


    # Relación: un producto puede tener muchas ventas
    ventas = relationship("Venta", back_populates="producto")

# =====================
# TABLA: ventas
# =====================
class Venta(Base):
    __tablename__ = "ventas"

    id                  = Column(Integer, primary_key=True, index=True)
    producto_id         = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad            = Column(Integer, nullable=False)
    precio_unitario     = Column(Float, nullable=False)
    precio_total        = Column(Float, nullable=False)
    fecha               = Column(DateTime, default=datetime.now)

    tipo_comprobante    = Column(String, nullable=True)
    numero_comprobante  = Column(String, nullable=True)
    metodo_pago         = Column(String, nullable=True)
    cliente_dni         = Column(String, nullable=True)
    cliente_nombre      = Column(String, nullable=True)

    producto = relationship("Producto", back_populates="ventas")

# =====================
# TABLA: resumen_diario (generada por el ETL)
# =====================
class ResumenDiario(Base):
    __tablename__ = "resumen_diario"

    id                   = Column(Integer, primary_key=True, index=True)
    fecha                = Column(Date, nullable=False, unique=True)
    total_ventas         = Column(Integer, default=0)
    total_ingresos       = Column(Float, default=0.0)
    producto_mas_vendido = Column(String, default="Sin ventas")
    fecha_generado       = Column(DateTime, default=datetime.now)

# =====================
# TABLA: proveedores
# =====================
class Proveedor(Base):
    __tablename__ = "proveedores"

    id             = Column(Integer, primary_key=True, index=True)
    nombre         = Column(String, nullable=False)
    contacto       = Column(String)
    telefono       = Column(String)
    email          = Column(String)
    direccion      = Column(String)
    fecha_registro = Column(DateTime, default=datetime.now)

    compras = relationship("Compra", back_populates="proveedor")

# =====================
# TABLA: compras
# =====================
class Compra(Base):
    __tablename__ = "compras"

    id            = Column(Integer, primary_key=True, index=True)
    proveedor_id  = Column(Integer, ForeignKey("proveedores.id"), nullable=False)
    producto_id   = Column(Integer, ForeignKey("productos.id"),   nullable=False)
    cantidad      = Column(Integer, nullable=False)
    precio_compra = Column(Float, nullable=False)
    precio_total  = Column(Float, nullable=False)
    fecha         = Column(DateTime, default=datetime.now)

    proveedor = relationship("Proveedor", back_populates="compras")
    producto  = relationship("Producto")
    

# =====================
# TABLA: usuarios
# =====================
class Usuario(Base):
    __tablename__ = "usuarios"

    id             = Column(Integer, primary_key=True, index=True)
    nombre         = Column(String, nullable=False)
    username       = Column(String, nullable=False, unique=True)
    password_hash  = Column(String, nullable=False)
    rol            = Column(String, nullable=False)  # 'admin' o 'cajero'
    activo         = Column(Boolean, default=True)
    fecha_registro = Column(DateTime, default=datetime.now)