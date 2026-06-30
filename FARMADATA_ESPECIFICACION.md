# 💊 FarmaData — Especificación del Sistema
> Documento SDD (Spec Driven Development) — Configuración Manual  
> Metodología: ADIPD | Lenguaje: Python | BD: **SQL Server**

---

## 0. CONTROL DE VERSIONES DEL DOCUMENTO

Este proyecto sigue **Spec Driven Development (SDD)** con configuración manual:
las especificaciones se definen primero en este documento `.MD`, y luego se
implementa el código siguiendo exactamente lo definido aquí. Cada cambio al
sistema se refleja primero como una actualización de este documento.

| Versión | Cambios |
|---|---|
| v1.0 | Especificación inicial: productos, ventas, ETL, dashboard básico, alertas de stock. BD: SQLite |
| v2.0 | **Migración de BD a SQL Server** (gestión de datos vía SSMS). Se agregan: modo oscuro, 4 gráficas estadísticas, fechas de vencimiento, módulo de proveedores y compras, buscador de productos |

---

## 1. DESCRIPCIÓN DEL PROYECTO

**FarmaData** es un sistema web para farmacias que permite:
1. Registrar y gestionar medicamentos (productos), incluyendo control de vencimiento
2. Registrar ventas al cliente
3. Registrar compras a proveedores (reabastecimiento de stock)
4. Ejecutar un pipeline ETL que analiza las ventas automáticamente
5. Mostrar un dashboard con métricas y múltiples gráficas estadísticas
6. Operar en modo claro u oscuro según preferencia del usuario

---

## 2. TECNOLOGÍAS A USAR

| Herramienta | Para qué sirve |
|---|---|
| Python 3.14 | Lenguaje principal |
| Flask | Framework web (las pantallas/rutas) |
| **SQL Server** (SSMS) | Base de datos — tablas y carga de datos gestionadas manualmente en SSMS |
| SQLAlchemy + pyodbc | Conectar Python con SQL Server |
| Pandas | Procesar y analizar datos (ETL) |
| Chart.js | Gráficas interactivas del dashboard |
| Pytest + pytest-cov | Pruebas unitarias y cobertura de código |
| HTML + CSS + JS (Jinja2) | Interfaz visual con soporte de modo oscuro |

> 📌 **Decisión de diseño:** las tablas, relaciones y carga masiva de datos
> (500+ registros) se gestionan directamente en **SQL Server Management
> Studio (SSMS)** con sentencias SQL puras. Python/Flask únicamente **consume**
> esos datos — no crea ni modifica el esquema automáticamente
> (`Base.metadata.create_all` queda deshabilitado intencionalmente).

---

## 3. ESTRUCTURA DEL PROYECTO

```
farmadata/
│
├── app.py                  # Punto de entrada, inicia Flask
├── models.py                # Definición de tablas (mapeo BD)
├── routes.py                 # Rutas/endpoints de la app
├── etl.py                    # Pipeline ETL (Extract-Transform-Load)
├── database.py                # Conexión a SQL Server
├── datos_prueba.py             # Script generador de datos de prueba (histórico)
│
├── templates/                 # Pantallas HTML
│   ├── base.html               # Plantilla base + navbar + modo oscuro
│   ├── index.html               # Dashboard con 4 gráficas
│   ├── productos.html            # Gestión de productos + buscador + vencimientos
│   ├── ventas.html                # Registrar ventas
│   ├── alertas.html                # Stock bajo + productos por vencer
│   ├── proveedores.html             # Gestión de proveedores
│   └── compras.html                  # Registro de compras / reabastecimiento
│
├── static/                    # CSS y JS adicionales
│
├── tests/                      # Pruebas unitarias
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_etl.py
│   └── test_routes.py
│
├── requirements.txt             # Librerías necesarias
└── FARMADATA_ESPECIFICACION.md   # Este documento (spec SDD)
```

---

## 4. BASE DE DATOS (SQL Server)

> Todas las tablas se crean y pueblan manualmente desde **SSMS**, no desde
> Python. Ver Sección 8 para los scripts SQL exactos usados.

### Tabla: `productos`
| Campo | Tipo SQL Server | Descripción |
|---|---|---|
| id | INT IDENTITY PK | Identificador único |
| nombre | NVARCHAR(100) | Nombre del medicamento |
| categoria | NVARCHAR(50) | Ej: Analgésico, Antibiótico |
| precio | DECIMAL(10,2) | Precio de venta |
| stock | INT | Cantidad disponible |
| stock_minimo | INT | Nivel mínimo antes de alerta (default: 10) |
| fecha_registro | DATETIME | Cuándo se registró (default: GETDATE()) |
| **fecha_vencimiento** | **DATE** | **Fecha de caducidad del medicamento (nullable)** |

### Tabla: `ventas`
| Campo | Tipo SQL Server | Descripción |
|---|---|---|
| id | INT IDENTITY PK | Identificador único |
| producto_id | INT FK → productos.id | Referencia a productos |
| cantidad | INT | Unidades vendidas |
| precio_unitario | DECIMAL(10,2) | Precio al momento de venta |
| precio_total | DECIMAL(10,2) | cantidad × precio_unitario |
| fecha | DATETIME | Fecha y hora de la venta (default: GETDATE()) |

### Tabla: `resumen_diario` *(generada por el ETL)*
| Campo | Tipo SQL Server | Descripción |
|---|---|---|
| id | INT IDENTITY PK | Identificador único |
| fecha | DATE UNIQUE | Fecha del resumen |
| total_ventas | INT | Número de ventas del día |
| total_ingresos | DECIMAL(10,2) | Suma de ingresos del día |
| producto_mas_vendido | NVARCHAR(100) | Nombre del producto top |
| fecha_generado | DATETIME | Cuándo se ejecutó el ETL |

### Tabla: `proveedores` *(nueva en v2.0)*
| Campo | Tipo SQL Server | Descripción |
|---|---|---|
| id | INT IDENTITY PK | Identificador único |
| nombre | NVARCHAR(100) | Nombre de la empresa proveedora |
| contacto | NVARCHAR(100) | Persona de contacto |
| telefono | NVARCHAR(20) | Teléfono |
| email | NVARCHAR(100) | Correo electrónico |
| direccion | NVARCHAR(200) | Dirección física |
| fecha_registro | DATETIME | Cuándo se registró |

### Tabla: `compras` *(nueva en v2.0)*
| Campo | Tipo SQL Server | Descripción |
|---|---|---|
| id | INT IDENTITY PK | Identificador único |
| proveedor_id | INT FK → proveedores.id | Proveedor que vendió el lote |
| producto_id | INT FK → productos.id | Producto comprado |
| cantidad | INT | Unidades compradas |
| precio_compra | DECIMAL(10,2) | Precio unitario de compra |
| precio_total | DECIMAL(10,2) | cantidad × precio_compra |
| fecha | DATETIME | Fecha de la compra |

### 4.1 — Diagrama de relaciones

```
proveedores ──┐
              ├──< compras >──┐
              │                ├── productos ──< ventas
              │                │
              └────────────────┘

resumen_diario  (tabla derivada, generada por el pipeline ETL a partir de ventas)
```

---

## 5. FUNCIONALIDADES (Requisitos)

### RF-01: Gestión de Productos
- Agregar, listar y eliminar productos (solo si no tienen ventas asociadas)
- **Buscador de productos por nombre** (filtro `ILIKE`)
- **Registrar fecha de vencimiento** al crear un producto
- Mostrar estado visual: ✅ OK / ⚠️ por vencer (≤30 días) / 🚨 vencido / 📦 stock bajo

### RF-02: Registro de Ventas
- Registrar una venta seleccionando producto y cantidad
- El stock se reduce automáticamente al vender
- Rechazar la venta si el stock es insuficiente
- Calcular `precio_total` automáticamente

### RF-03: Pipeline ETL
- **Extract:** leer todas las ventas del día desde `ventas` (vía Pandas + SQL Server)
- **Transform:** calcular total de ventas, total de ingresos y producto más vendido
- **Load:** insertar o actualizar el registro correspondiente en `resumen_diario`
- Ejecutable manualmente desde un botón en el dashboard
- Compatible con sintaxis SQL Server (`CAST(fecha AS DATE)` en vez de `DATE()`)

### RF-04: Dashboard de Análisis *(ampliado en v2.0)*
- 6 métricas: ventas hoy, ingresos hoy, producto top hoy, alertas de stock,
  total de productos registrados, ingresos de la semana
- **Gráfica de barras** — ingresos últimos 7 días
- **Gráfica de dona** — ventas agrupadas por categoría de medicamento
- **Gráfica de barras horizontales** — top 5 productos más vendidos (histórico)
- **Gráfica de línea** — distribución de ventas por hora del día

### RF-05: Alertas
- Listar productos con `stock <= stock_minimo`
- **Listar productos cuya fecha de vencimiento esté a ≤30 días o ya vencidos**
- Distinguir visualmente "vencido" de "por vencer"

### RF-06: Proveedores *(nuevo en v2.0)*
- Registrar proveedor (nombre, contacto, teléfono, email, dirección)
- Listar todos los proveedores
- Eliminar proveedor

### RF-07: Compras / Reabastecimiento *(nuevo en v2.0)*
- Registrar una compra a un proveedor, indicando producto, cantidad y precio de compra
- **El stock del producto aumenta automáticamente** al registrar la compra
- Historial de las últimas 50 compras con proveedor y producto

### RF-08: Interfaz — Modo Oscuro *(nuevo en v2.0)*
- Botón en el navbar para alternar modo claro/oscuro
- Preferencia persistente entre sesiones (localStorage)
- Todas las pantallas y gráficas se adaptan a ambos modos

---

## 6. RUTAS / ENDPOINTS

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Dashboard principal (6 métricas + 4 gráficas) |
| GET | `/productos` | Listar productos (admite `?buscar=` para filtrar) |
| POST | `/productos/agregar` | Agregar producto nuevo (incluye fecha_vencimiento) |
| POST | `/productos/eliminar/<id>` | Eliminar producto |
| GET | `/ventas` | Listar últimas 50 ventas |
| POST | `/ventas/registrar` | Registrar nueva venta |
| GET | `/alertas` | Stock bajo + productos por vencer |
| GET | `/proveedores` | Listar proveedores |
| POST | `/proveedores/agregar` | Agregar proveedor |
| POST | `/proveedores/eliminar/<id>` | Eliminar proveedor |
| GET | `/compras` | Listar últimas 50 compras |
| POST | `/compras/registrar` | Registrar compra (aumenta stock) |
| POST | `/etl/ejecutar` | Ejecutar pipeline ETL manualmente |
| GET | `/api/dashboard-data` | Retorna datos del dashboard en JSON |

---

## 7. PIPELINE ETL — Detalle

```
PASO 1 — EXTRACT
  → Leer ventas de hoy uniendo `ventas` + `productos`
  → Usar Pandas: pd.read_sql() con sintaxis T-SQL (CAST AS DATE)

PASO 2 — TRANSFORM
  → Calcular total de ventas (count)
  → Calcular total de ingresos (sum de precio_total)
  → Identificar producto más vendido (groupby + sum de cantidad)

PASO 3 — LOAD
  → Verificar si ya existe resumen para hoy en `resumen_diario`
  → Si existe: actualizar (UPDATE)
  → Si no existe: insertar nuevo registro (INSERT)
```

---

## 8. CARGA DE DATOS (gestión directa en SSMS)

Para cumplir con el requisito de **"trabajar con una cantidad considerable de
datos"**, la carga de datos de prueba se realiza directamente con SQL en SSMS:

| Acción | Cantidad | Método |
|---|---|---|
| Productos | 30 medicamentos variados | `INSERT` manual con datos reales de farmacia |
| Ventas históricas | 500 ventas en los últimos 30 días | Script T-SQL con `WHILE` + `RAND()` |
| Ventas del día | 20 ventas adicionales | Script T-SQL con `GETDATE()` |
| Proveedores | 5 empresas distribuidoras | `INSERT` manual |
| Fechas de vencimiento | 30 productos actualizados | `UPDATE` con `DATEADD` + `RAND` |

Esto demuestra manejo de **datos a escala** y consultas SQL avanzadas
(bucles `WHILE`, funciones de fecha, agregaciones `GROUP BY`, `JOIN`s).

---

## 9. PRUEBAS UNITARIAS (mínimo requeridas)

### tests/test_models.py
- `test_crear_producto()` — verifica que se puede crear un producto
- `test_producto_stock_minimo()` — verifica valor por defecto de stock_minimo
- `test_producto_fecha_vencimiento_nullable()` — verifica que el campo acepta nulo

### tests/test_etl.py
- `test_etl_calcula_total_ingresos()` — verifica cálculo correcto de ingresos
- `test_etl_identifica_producto_top()` — verifica que identifica bien el más vendido
- `test_etl_no_duplica_resumen()` — verifica que no inserta dos veces el mismo día
- `test_etl_sin_ventas()` — verifica manejo correcto de un día sin ventas

### tests/test_routes.py
- `test_ruta_dashboard_200()` — verifica que el dashboard carga correctamente
- `test_agregar_producto()` — verifica que se puede agregar un producto vía POST
- `test_venta_reduce_stock()` — verifica que una venta reduce el stock
- `test_venta_stock_insuficiente()` — verifica que rechaza venta sin stock
- `test_compra_aumenta_stock()` — verifica que una compra aumenta el stock
- `test_buscador_productos()` — verifica que el filtro de búsqueda funciona
- `test_alertas_vencimiento()` — verifica que detecta productos por vencer

> **Meta de cobertura: 95%**  
> Ejecutar con: `pytest --cov=. --cov-report=term-missing`

---

## 10. INSTALACIÓN Y EJECUCIÓN

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/farmadata.git
cd farmadata

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear la base de datos y tablas en SSMS (ver scripts en /sql)

# 5. Configurar conexión en database.py (servidor, usuario, contraseña)

# 6. Ejecutar la aplicación
python app.py

# 7. Ejecutar pruebas
pytest --cov=. --cov-report=term-missing
```

---

## 11. DESPLIEGUE

- **Repositorio:** GitHub (rama `main`)
- **Plataforma:** Render.com (gratuito)
- **Base de datos en producción:** SQL Server

---

## 12. GLOSARIO (para el informe)

| Término | Significado simple |
|---|---|
| ETL | Proceso de extraer, transformar y cargar datos |
| Pipeline | Flujo automático de pasos de procesamiento de datos |
| Stock | Cantidad disponible de un producto |
| Dashboard | Pantalla resumen con métricas e indicadores |
| Endpoint | URL que realiza una acción en el sistema |
| Cobertura de código | % del código que está siendo probado |
| SDD | Desarrollo guiado por especificaciones (este documento es la "spec") |
| SSMS | SQL Server Management Studio — herramienta para administrar SQL Server |
| ILIKE / LIKE | Operador SQL para búsquedas de texto parcial |

---

*Documento v2.0 — actualizado en Fase D (Diseño, revisión iterativa) | Metodología ADIPD + SDD manual*
