# 🏥 Sistema de Gestión Veterinaria

Sistema completo de punto de venta (POS) y gestión integral para clínicas veterinarias, desarrollado con Flask y Python.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación Rápida](#-instalación-rápida)
- [Instalación Manual](#-instalación-manual)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Módulos del Sistema](#-módulos-del-sistema)
- [Impresión de Tickets](#-impresión-de-tickets)
- [Asistente IA](#-asistente-ia)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## ✨ Características

### 🛒 Punto de Venta (POS)
- ✅ Interfaz intuitiva para ventas rápidas
- ✅ Búsqueda de productos por nombre, código de barras o categoría
- ✅ Gestión de inventario en tiempo real
- ✅ Impresión de tickets térmicos (58mm/80mm)
- ✅ Apertura automática de caja registradora
- ✅ Historial completo de ventas

### 🏥 Gestión Veterinaria
- ✅ Registro de pacientes (animales) y dueños
- ✅ Historial clínico completo
- ✅ Agenda de consultas
- ✅ Notas de evolución y tratamientos
- ✅ Seguimiento de vacunas y desparasitaciones

### 📦 Gestión de Inventario
- ✅ Control de productos y categorías
- ✅ Gestión de proveedores
- ✅ Registro de compras
- ✅ Alertas de stock bajo
- ✅ Códigos de barras
- ✅ Precios de compra y venta

### 🤖 Asistente IA Veterinario
- ✅ Asistente inteligente con Google Gemini
- ✅ Consultas sobre medicamentos y tratamientos
- ✅ Recomendaciones de productos
- ✅ Información sobre dosis y especies
- ✅ Búsqueda inteligente en inventario
- ✅ Contexto conversacional

### 👥 Gestión de Usuarios
- ✅ Sistema de roles (Administrador, Veterinario, Vendedor)
- ✅ Permisos granulares
- ✅ Registro de actividad
- ✅ Autenticación segura

### 🎨 Interfaz Moderna
- ✅ Diseño responsivo (móvil, tablet, desktop)
- ✅ Modo oscuro
- ✅ Íconos Font Awesome
- ✅ Alpine.js para interactividad
- ✅ Tailwind CSS para estilos

## 💻 Requisitos del Sistema

### Software Base
- **Python**: 3.8 o superior
- **pip**: Gestor de paquetes de Python
- **Sistema Operativo**: Linux (Ubuntu 20.04+), Windows 10+, macOS 10.14+

### Dependencias Principales
- Flask 2.3+
- SQLAlchemy (ORM)
- Flask-Login (autenticación)
- Flask-Migrate (migraciones de BD)
- python-escpos (impresión térmica)
- Google Generative AI (Gemini)

### Hardware Opcional
- **Impresora térmica**: Compatible con ESC/POS (58mm o 80mm)
- **Lector de códigos de barras**: USB o Bluetooth
- **Caja registradora**: Compatible con cable RJ11/RJ12

## 🚀 Instalación Rápida

### Opción 1: Script Automático (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/edgarmbellol/VeterinariaSoftware.git
cd VeterinariaSoftware

# 2. Ejecutar instalador automático
chmod +x instalar.sh
./instalar.sh

# 3. Iniciar el sistema
source venv/bin/activate
python run.py
```

¡Listo! El sistema estará disponible en `http://localhost:5000`

**Credenciales iniciales:**
- Usuario: `admin`
- Contraseña: `admin123`

## 📝 Instalación Manual

### 1. Clonar el Repositorio

```bash
git clone https://github.com/edgarmbellol/VeterinariaSoftware.git
cd VeterinariaSoftware
```

### 2. Crear Entorno Virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# API Key de Google Gemini (opcional, para asistente IA)
GOOGLE_API_KEY=tu_api_key_aqui

# Configuración de Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta_super_aleatoria

# Base de datos
DATABASE_URL=sqlite:///instance/veterinaria.db
```

**Obtener API Key de Gemini:** https://makersuite.google.com/app/apikey (Gratis)

### 5. Inicializar Base de Datos

```bash
# Crear directorio para BD
mkdir -p instance

# Inicializar BD con datos básicos
python3 << 'EOF'
from app import create_app, db
from app.models import Usuario, Categoria
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    db.create_all()
    
    # Crear admin
    admin = Usuario(
        username='admin',
        password_hash=generate_password_hash('admin123'),
        rol='administrador',
        activo=True
    )
    db.session.add(admin)
    
    # Crear categorías
    for cat in ['Medicamentos', 'Alimentos', 'Accesorios', 'Higiene']:
        db.session.add(Categoria(nombre=cat, activo=True))
    
    db.session.commit()
    print("✅ Base de datos creada")
EOF
```

### 6. Ejecutar el Sistema

```bash
python run.py
```

Acceder a: **http://localhost:5000**

## ⚙️ Configuración

### Configuración de Impresora USB (Linux)

Para usar la impresora térmica en Linux:

```bash
# 1. Conectar la impresora
# 2. Detectar IDs del dispositivo
lsusb

# 3. Configurar permisos
sudo ./configurar_permisos_usb.sh

# 4. Reiniciar servicios udev
sudo udevadm control --reload-rules
sudo udevadm trigger

# 5. Cerrar sesión y volver a entrar (importante)
```

### Configuración del Negocio

1. Iniciar sesión como administrador
2. Ir a **Admin → Configuración**
3. Configurar:
   - Nombre del negocio
   - Dirección y teléfono
   - Logo (para tickets)
   - Mensaje de pie de página
   - Información fiscal (RFC/NIT)

### Personalización del Sistema

#### Cambiar Puerto del Servidor

Editar `run.py`:

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)  # Puerto 8080
```

#### Cambiar Base de Datos a PostgreSQL

En `.env`:

```bash
DATABASE_URL=postgresql://usuario:password@localhost/veterinaria
```

Instalar driver:

```bash
pip install psycopg2-binary
```

## 📖 Uso

### Realizar una Venta

1. **Ventas → Nueva Venta**
2. Buscar productos por:
   - Nombre
   - Código de barras (escanear o escribir)
   - Categoría
3. Agregar productos al carrito
4. Especificar cantidad y descuentos
5. **Cobrar** → Imprimir ticket

### Registrar Consulta Veterinaria

1. **Consultas → Nueva Consulta**
2. Seleccionar o registrar animal
3. Registrar motivo y observaciones
4. Agregar diagnóstico y tratamiento
5. Asociar productos usados (opcional)
6. Guardar consulta

### Usar el Asistente IA

1. **Asistente IA** (menú lateral)
2. Hacer preguntas como:
   - "¿Qué medicamento tengo para garrapatas en perros?"
   - "¿Cuál es la dosis de amoxicilina para un gato de 3kg?"
   - "¿Tengo alimento para cachorros?"
3. El asistente busca en tu inventario y proporciona información

### Gestionar Productos

1. **Productos → Lista de Productos**
2. **Nuevo Producto**:
   - Nombre, descripción
   - Código de barras
   - Categoría
   - Precio de compra y venta
   - Stock inicial
   - Foto (opcional)
3. Guardar

### Imprimir Ticket

Los tickets se imprimen automáticamente al completar una venta. Incluyen:
- Logo del negocio
- Información fiscal
- Detalle de productos
- Total y forma de pago
- Código QR (opcional)
- Apertura automática de caja

## 🎯 Módulos del Sistema

### 1. Módulo de Ventas (`/ventas`)
- Nueva venta
- Historial de ventas
- Devoluciones
- Reporte de caja

### 2. Módulo de Productos (`/productos`)
- Lista de productos
- Crear/editar productos
- Categorías
- Búsqueda avanzada

### 3. Módulo de Consultas (`/consultas`)
- Lista de animales
- Historial clínico
- Nueva consulta
- Seguimiento

### 4. Módulo de Compras (`/compras`)
- Proveedores
- Registro de compras
- Productos por proveedor

### 5. Módulo de Administración (`/admin`)
- Dashboard
- Usuarios
- Configuración
- Reportes

### 6. Asistente IA (`/asistente_ia`)
- Chat inteligente
- Búsqueda de productos
- Información veterinaria

## 🖨️ Impresión de Tickets

### Impresoras Compatibles

El sistema es compatible con cualquier impresora térmica que soporte comandos ESC/POS:

- ✅ Xprinter (XP-58IIT, XP-80)
- ✅ Epson TM-T20, TM-T88
- ✅ Star Micronics
- ✅ Bixolon
- ✅ Genéricas ESC/POS

### Configuración de IDs

Si tu impresora no es detectada automáticamente:

1. Detectar IDs:
```bash
lsusb
# Ejemplo: Bus 001 Device 005: ID 0483:070b STMicroelectronics
#                                   ^^^^  ^^^^
#                                   |     Product ID
#                                   Vendor ID
```

2. Actualizar en `app/routes/ventas.py`:
```python
VENDOR_ID = 0x0483   # Tu Vendor ID
PRODUCT_ID = 0x070b  # Tu Product ID
```

### Scripts de Prueba

```bash
# Detectar impresora
python3 detectar_impresora.py

# Probar comandos de caja
python3 probar_cajon_monedero.py

# Probar múltiples comandos
python3 probar_comandos_automatico.py
```

## 🤖 Asistente IA

El sistema incluye un asistente IA veterinario potenciado por **Google Gemini**.

### Características

- 💬 Chat conversacional con contexto
- 🔍 Búsqueda inteligente en inventario
- 💊 Información sobre medicamentos y dosis
- 🐕 Recomendaciones por especie y tamaño
- 📊 Análisis de disponibilidad de productos

### Configuración

1. Obtener API Key gratis: https://makersuite.google.com/app/apikey
2. Agregar a `.env`:
```bash
GOOGLE_API_KEY=AIzaSy...
```

### Ejemplos de Uso

```
Usuario: "¿Qué antipulgas tengo para perros medianos?"
IA: "Tengo disponible:
     • Frontline Plus - $250 (3 pipetas)
     • Bravecto - $450 (1 tableta, protección 3 meses)
     ¿Cuál prefieres?"

Usuario: "¿Cuál es la dosis de amoxicilina para un gato de 4kg?"
IA: "Para un gato de 4kg:
     • Dosis: 50mg cada 12 horas por 7-10 días
     • Total: 200mg/día
     Tengo Amoxicilina 50mg tabletas en stock."
```

## 📁 Estructura del Proyecto

```
VeterinariaSoftware/
├── app/
│   ├── __init__.py              # Inicialización de Flask
│   ├── models.py                # Modelos de base de datos
│   ├── routes/
│   │   ├── admin.py             # Rutas de administración
│   │   ├── ventas.py            # Rutas de ventas y POS
│   │   ├── productos.py         # Gestión de productos
│   │   ├── consultas.py         # Consultas veterinarias
│   │   ├── compras.py           # Compras y proveedores
│   │   ├── asistente_ia.py      # Asistente IA
│   │   └── auth.py              # Autenticación
│   ├── templates/               # Plantillas HTML Jinja2
│   │   ├── base.html
│   │   ├── ventas/
│   │   ├── productos/
│   │   ├── consultas/
│   │   └── admin/
│   └── static/                  # CSS, JS, imágenes
│       ├── css/
│       ├── js/
│       └── uploads/
├── migrations/                   # Migraciones de BD
├── instance/                     # Base de datos SQLite
│   └── veterinaria.db
├── venv/                         # Entorno virtual
├── .env                          # Variables de entorno
├── .gitignore                    # Archivos ignorados por git
├── requirements.txt              # Dependencias Python
├── instalar.sh                   # Script de instalación
├── configurar_permisos_usb.sh   # Config de impresora
├── run.py                        # Punto de entrada
└── README.md                     # Este archivo
```

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con Werkzeug
- ✅ Protección CSRF en formularios
- ✅ Sesiones seguras con Flask-Login
- ✅ Validación de permisos por rol
- ✅ Variables sensibles en `.env` (no en git)

### Recomendaciones

1. **Cambiar contraseña del admin** inmediatamente
2. **No exponer** el sistema directamente a internet sin un proxy inverso (nginx)
3. **Usar HTTPS** en producción
4. **Realizar backups** regulares de la base de datos:
   ```bash
   cp instance/veterinaria.db backups/veterinaria_$(date +%Y%m%d).db
   ```

## 🐛 Solución de Problemas

### La impresora no imprime

1. Verificar conexión USB:
```bash
lsusb | grep -i print
```

2. Verificar permisos:
```bash
sudo ./configurar_permisos_usb.sh
```

3. Ver logs en la aplicación o ejecutar:
```bash
python3 detectar_impresora.py
```

### El asistente IA no responde

1. Verificar API Key en `.env`
2. Verificar conexión a internet
3. Ver logs de Flask para mensajes de error

### Error al iniciar: "Port already in use"

Cambiar puerto en `run.py` o matar el proceso:
```bash
# Ver qué usa el puerto 5000
lsof -i :5000

# Matar proceso
kill -9 <PID>
```

### Base de datos bloqueada

```bash
# Verificar conexiones
lsof instance/veterinaria.db

# Si persiste, recrear
mv instance/veterinaria.db instance/veterinaria_old.db
python run.py
```

## 📊 Backups y Migración

### Backup Manual

```bash
# Backup completo
cp -r instance/ backups/backup_$(date +%Y%m%d)/
```

### Backup Automático (Cron)

Agregar a crontab (`crontab -e`):

```bash
# Backup diario a las 2 AM
0 2 * * * cp /ruta/al/proyecto/instance/veterinaria.db /ruta/backups/veterinaria_$(date +\%Y\%m\%d).db
```

### Migrar a Otro Dispositivo

```bash
# En dispositivo origen
cp instance/veterinaria.db /ruta/de/backup/

# En dispositivo nuevo (después de instalar)
cp /ruta/de/backup/veterinaria.db instance/
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 👨‍💻 Autor

**Edgar Bellol**
- GitHub: [@edgarmbellol](https://github.com/edgarmbellol)

## 🙏 Agradecimientos

- [Flask](https://flask.palletsprojects.com/) - Framework web
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [python-escpos](https://github.com/python-escpos/python-escpos) - Impresión térmica
- [Google Gemini](https://deepmind.google/technologies/gemini/) - IA generativa
- [Alpine.js](https://alpinejs.dev/) - Framework JS reactivo
- [Tailwind CSS](https://tailwindcss.com/) - Framework CSS

---

<div align="center">

**⭐ Si este proyecto te fue útil, considera darle una estrella ⭐**

Made with ❤️ for veterinarians 🐾

</div>
