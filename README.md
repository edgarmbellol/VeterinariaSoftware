# Sistema de Ventas para Veterinaria

Sistema completo de gestión de ventas desarrollado con Flask y Tailwind CSS para el control de inventario y ventas de una veterinaria.

## Características

- ✅ **Gestión de Productos**: Crear, editar y administrar productos con código de barras
- ✅ **Control de Inventario**: Seguimiento de stock con alertas de stock mínimo
- ✅ **Sistema de Ventas**: Interfaz optimizada para pistola de código de barras
- ✅ **Múltiples Métodos de Pago**: Efectivo, Nequi y Daviplata
- ✅ **Dashboard Administrativo**: Estadísticas, reportes y análisis de ventas
- ✅ **Consultas Veterinarias**: Sistema completo de historias clínicas y consultas médicas
- ✅ **Interfaz Moderna**: Diseño atractivo con Tailwind CSS y Alpine.js

## Instalación

### Opción 1: Script Automatizado (Recomendado)

1. Clonar o descargar el proyecto

2. Instalar python3-venv si no está instalado:
```bash
sudo apt install python3-venv
# O para Python 3.12 específicamente:
sudo apt install python3.12-venv
```

3. Ejecutar el script de configuración:
```bash
./setup_venv.sh
```

Este script:
- Crea el entorno virtual
- Instala todas las dependencias
- Ejecuta las migraciones de base de datos automáticamente

### Opción 2: Configuración Manual

1. Clonar o descargar el proyecto

2. Crear un entorno virtual:
```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. Configurar Flask:
```bash
export FLASK_APP=run.py
```

5. Inicializar la base de datos (si es la primera vez):
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

6. Ejecutar la aplicación:
```bash
python run.py
```

La aplicación estará disponible en `http://localhost:5000`

### Uso del Entorno Virtual

**Para activar el entorno virtual:**
```bash
source venv/bin/activate
# O usar el script helper:
./activar_venv.sh
```

**Para desactivar el entorno virtual:**
```bash
deactivate
```

**Para ejecutar comandos Flask con el entorno activado:**
```bash
source venv/bin/activate
flask db upgrade  # Aplicar migraciones
flask db migrate -m "Descripción"  # Crear nueva migración
python run.py  # Ejecutar aplicación
```

## Uso de la Pistola de Código de Barras

La aplicación está optimizada para trabajar con pistolas de código de barras simples. Cuando escanees un código:

1. El código se captura automáticamente en el campo de búsqueda
2. El sistema busca el producto en la base de datos
3. Si existe, se agrega automáticamente a la venta
4. Si ya está en la venta, se incrementa la cantidad

**Nota**: La pistola funciona como un teclado, simplemente escanea y el código aparece donde está el cursor.

## Estructura del Proyecto

```
tiendas/
├── app/
│   ├── __init__.py          # Configuración de Flask
│   ├── models.py            # Modelos de base de datos
│   ├── routes/              # Blueprints de rutas
│   │   ├── productos.py
│   │   ├── ventas.py
│   │   └── admin.py
│   └── templates/           # Plantillas HTML
│       ├── base.html
│       ├── productos/
│       ├── ventas/
│       └── admin/
├── run.py                   # Punto de entrada
├── requirements.txt         # Dependencias
└── README.md
```

## Funcionalidades Principales

### Gestión de Productos
- Crear productos con código de barras único
- Editar información de productos
- Control de stock y stock mínimo
- Categorización de productos

### Sistema de Ventas
- Búsqueda rápida por código de barras
- Agregar múltiples productos
- Ajustar cantidades
- Selección de método de pago
- Cálculo automático de totales

### Dashboard Administrativo
- Estadísticas de ventas
- Ingresos y ganancias totales
- Ventas por método de pago
- Productos más vendidos
- Gráfico de ventas últimos 7 días
- Alertas de stock bajo

### Consultas Veterinarias
- Registro de animales con datos completos
- Historial de consultas médicas
- Búsqueda y filtrado de animales
- Relación entre consultas y ventas
- Vista completa de historias clínicas

## Tecnologías Utilizadas

- **Backend**: Flask 3.0
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: Tailwind CSS, Alpine.js
- **ORM**: SQLAlchemy
- **Migraciones**: Flask-Migrate

## Configuración

### Variables de Entorno

Puedes configurar las siguientes variables de entorno:

- `DATABASE_URL`: URL de conexión a la base de datos
- `SECRET_KEY`: Clave secreta para sesiones (cambiar en producción)

## Desarrollo

Para desarrollo, la aplicación usa SQLite por defecto. Para producción, se recomienda usar PostgreSQL o MySQL.

## Licencia

Este proyecto es de uso libre para fines comerciales y educativos.






