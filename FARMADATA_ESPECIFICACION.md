# 💊 FarmaData — Especificación del Sistema
> Documento SDD (Spec Driven Development)  
> Metodología: ADIPD | Lenguaje: Python | BD: SQLite

---

## 1. DESCRIPCIÓN DEL PROYECTO

**FarmaData** es un sistema web para farmacias que permite:
1. Registrar y gestionar medicamentos (productos)
2. Registrar ventas al cliente
3. Ejecutar un pipeline ETL que analiza las ventas automáticamente
4. Mostrar un dashboard con métricas e indicadores clave

---

## 2. TECNOLOGÍAS A USAR

| Herramienta | Para qué sirve |
|---|---|
| Python 3.10+ | Lenguaje principal |
| Flask | Framework web (las pantallas/rutas) |
| SQLite | Base de datos (archivo local) |
| SQLAlchemy | Conectar Python con la BD |
| Pandas | Procesar y analizar datos (ETL) |
| Pytest | Pruebas unitarias |
| HTML + CSS + JS | Interfaz visual |

---

## 3. ESTRUCTURA DEL PROYECTO

```
farmadata/
│
├── app.py                  # Punto de entrada, inicia Flask
├── models.py               # Definición de tablas (BD)
├── routes.py               # Rutas/endpoints de la app
├── etl.py                  # Pipeline ETL (Extract-Transform-Load)
├── database.py             # Conexión a SQLite
│
├── templates/              # Pantallas HTML
│   ├── base.html
│   ├── index.html          # Dashboard principal
│   ├── productos.html      # Gestión de productos
│   ├── ventas.html         # Registrar ventas
│   └── alertas.html        # Stock bajo
│
├── static/                 # CSS y JS
│   ├── style.css
│   └── charts.js
│
├── tests/                  # Pruebas unitarias
│   ├── test_models.py
│   ├── test_etl.py
│   └── test_routes.py
│
├── requirements.txt        # Librerías necesarias
└── README.md
```

---

## 4. BASE DE DATOS

### Tabla: `productos`
| Campo | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK | Identificador único |
| nombre | TEXT | Nombre del medicamento |
| categoria | TEXT | Ej: Analgésico, Antibiótico |
| precio | REAL | Precio de venta |
| stock | INTEGER | Cantidad disponible |
| stock_minimo | INTEGER | Nivel mínimo antes de alerta (default: 10) |
| fecha_registro | DATETIME | Cuándo se registró |

### Tabla: `ventas`
| Campo | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK | Identificador único |
| producto_id | INTEGER FK | Referencia a productos |
| cantidad | INTEGER | Unidades vendidas |
| precio_unitario | REAL | Precio al momento de venta |
| precio_total | REAL | cantidad × precio_unitario |
| fecha | DATETIME | Fecha y hora de la venta |

### Tabla: `resumen_diario` *(generada por el ETL)*
| Campo | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK | Identificador único |
| fecha | DATE | Fecha del resumen |
| total_ventas | INTEGER | Número de ventas del día |
| total_ingresos | REAL | Suma de ingresos del día |
| producto_mas_vendido | TEXT | Nombre del producto top |
| fecha_generado | DATETIME | Cuándo se ejecutó el ETL |

---

## 5. FUNCIONALIDADES (Requisitos)

### RF-01: Gestión de Productos
- El sistema debe permitir **agregar** un producto nuevo
- El sistema debe permitir **listar** todos los productos
- El sistema debe permitir **editar** precio y stock de un producto
- El sistema debe permitir **eliminar** un producto (solo si no tiene ventas)

### RF-02: Registro de Ventas
- El sistema debe permitir **registrar una venta** seleccionando producto y cantidad
- Al registrar la venta, el **stock debe reducirse** automáticamente
- El sistema debe **rechazar la venta** si el stock es insuficiente
- El sistema debe **calcular el precio_total** automáticamente

### RF-03: Pipeline ETL
- El ETL debe **extraer** todas las ventas del día desde la tabla `ventas`
- El ETL debe **transformar** los datos: calcular total ventas, total ingresos y producto más vendido
- El ETL debe **cargar** el resultado en la tabla `resumen_diario`
- El ETL debe poder ejecutarse **manualmente** desde el dashboard con un botón
- Si ya existe un resumen para ese día, debe **actualizarlo**, no duplicarlo

### RF-04: Dashboard de Análisis
- Mostrar **total de ingresos del día**
- Mostrar **número de ventas del día**
- Mostrar **producto más vendido del día**
- Mostrar **gráfica de ventas de los últimos 7 días**
- Mostrar **top 5 productos más vendidos** (tabla)

### RF-05: Alertas de Stock
- Listar todos los productos cuyo `stock <= stock_minimo`
- Mostrar el stock actual y el stock mínimo de cada uno
- Mostrar alerta visual en el dashboard si hay productos con stock bajo

---

## 6. RUTAS / ENDPOINTS

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Dashboard principal |
| GET | `/productos` | Listar productos |
| POST | `/productos/agregar` | Agregar producto nuevo |
| POST | `/productos/editar/<id>` | Editar producto |
| POST | `/productos/eliminar/<id>` | Eliminar producto |
| GET | `/ventas` | Listar ventas |
| POST | `/ventas/registrar` | Registrar nueva venta |
| GET | `/alertas` | Ver productos con stock bajo |
| POST | `/etl/ejecutar` | Ejecutar pipeline ETL manualmente |
| GET | `/api/dashboard-data` | Retorna datos del dashboard en JSON |

---

## 7. PIPELINE ETL — Detalle

```
PASO 1 — EXTRACT
  → Leer todas las ventas de hoy desde la tabla `ventas`
  → Usar Pandas: pd.read_sql()

PASO 2 — TRANSFORM
  → Calcular total de ventas (count)
  → Calcular total de ingresos (sum de precio_total)
  → Identificar producto más vendido (groupby + sum de cantidad)

PASO 3 — LOAD
  → Verificar si ya existe resumen para hoy
  → Si existe: actualizar
  → Si no existe: insertar nuevo registro en `resumen_diario`
```

---

## 8. PRUEBAS UNITARIAS (mínimo requeridas)

### tests/test_models.py
- `test_crear_producto()` — verifica que se puede crear un producto
- `test_producto_stock_minimo()` — verifica que stock_minimo tiene valor por defecto

### tests/test_etl.py
- `test_etl_calcula_total_ingresos()` — verifica que el cálculo de ingresos es correcto
- `test_etl_identifica_producto_top()` — verifica que identifica bien el más vendido
- `test_etl_no_duplica_resumen()` — verifica que no inserta dos veces el mismo día
- `test_etl_sin_ventas()` — verifica que maneja correctamente un día sin ventas

### tests/test_routes.py
- `test_ruta_dashboard_200()` — verifica que el dashboard carga correctamente
- `test_agregar_producto()` — verifica que se puede agregar un producto vía POST
- `test_venta_reduce_stock()` — verifica que una venta reduce el stock
- `test_venta_stock_insuficiente()` — verifica que rechaza venta sin stock

> **Meta de cobertura: 95%**  
> Ejecutar con: `pytest --cov=. --cov-report=term-missing`

---

## 9. INSTALACIÓN Y EJECUCIÓN

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/farmadata.git
cd farmadata

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Inicializar la base de datos
python database.py

# 4. Ejecutar la aplicación
python app.py

# 5. Ejecutar pruebas
pytest --cov=. --cov-report=term-missing
```

---

## 10. DESPLIEGUE

- **Repositorio:** GitHub (rama `main`)
- **Plataforma:** Render.com (gratuito)
- **Base de datos en producción:** SQLite (archivo incluido en el repo)

---

## 11. GLOSARIO (para el informe)

| Término | Significado simple |
|---|---|
| ETL | Proceso de extraer, transformar y cargar datos |
| Pipeline | Flujo automático de pasos de procesamiento de datos |
| Stock | Cantidad disponible de un producto |
| Dashboard | Pantalla resumen con métricas e indicadores |
| Endpoint | URL que realiza una acción en el sistema |
| Cobertura de código | % del código que está siendo probado |
| SDD | Desarrollo guiado por especificaciones |

---

*Documento generado en Fase D — Diseño | Metodología ADIPD*
