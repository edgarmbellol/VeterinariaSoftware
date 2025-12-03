#!/bin/bash

# ============================================================================
# Script de Instalación Automática - Sistema de Veterinaria
# ============================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║        🏥 SISTEMA DE GESTIÓN VETERINARIA - INSTALADOR         ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. VERIFICAR REQUISITOS
# ============================================================================

echo -e "${BLUE}[1/7]${NC} Verificando requisitos del sistema..."

# Verificar Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 no está instalado${NC}"
    echo "Por favor instala Python 3.8 o superior:"
    echo "  sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION encontrado"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ Error: pip3 no está instalado${NC}"
    echo "Por favor instala pip3:"
    echo "  sudo apt install python3-pip"
    exit 1
fi

echo -e "${GREEN}✓${NC} pip3 encontrado"

# Verificar git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Git no está instalado (opcional para actualizaciones)"
fi

# ============================================================================
# 2. CREAR Y ACTIVAR ENTORNO VIRTUAL
# ============================================================================

echo ""
echo -e "${BLUE}[2/7]${NC} Creando entorno virtual de Python..."

if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC} El entorno virtual ya existe. ¿Deseas recrearlo? (s/n)"
    read -r respuesta
    if [ "$respuesta" = "s" ]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓${NC} Entorno virtual recreado"
    else
        echo -e "${YELLOW}↷${NC} Usando entorno virtual existente"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Entorno virtual creado"
fi

# Activar entorno virtual
source venv/bin/activate
echo -e "${GREEN}✓${NC} Entorno virtual activado"

# ============================================================================
# 3. INSTALAR DEPENDENCIAS
# ============================================================================

echo ""
echo -e "${BLUE}[3/7]${NC} Instalando dependencias de Python..."

# Actualizar pip
pip install --upgrade pip > /dev/null 2>&1

# Instalar dependencias
if pip install -r requirements.txt > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Todas las dependencias instaladas correctamente"
else
    echo -e "${RED}❌ Error al instalar dependencias${NC}"
    echo "Intenta manualmente: pip install -r requirements.txt"
    exit 1
fi

# ============================================================================
# 4. CONFIGURAR VARIABLES DE ENTORNO
# ============================================================================

echo ""
echo -e "${BLUE}[4/7]${NC} Configurando variables de entorno..."

if [ -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC} El archivo .env ya existe. ¿Deseas recrearlo? (s/n)"
    read -r respuesta
    if [ "$respuesta" != "s" ]; then
        echo -e "${YELLOW}↷${NC} Usando archivo .env existente"
    else
        rm .env
    fi
fi

if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}📝 Configuración de API de Google Gemini${NC}"
    echo "Para el asistente IA necesitas una API Key de Google Gemini"
    echo "Obtén una gratis en: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "Ingresa tu API Key de Google Gemini (o presiona Enter para omitir): " api_key
    
    # Generar SECRET_KEY aleatoria
    secret_key=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    
    # Crear archivo .env
    cat > .env << EOF
# API Key de Google Gemini (para el asistente IA)
GOOGLE_API_KEY=${api_key:-tu_api_key_aqui}

# Configuración de Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=$secret_key

# Base de datos
DATABASE_URL=sqlite:///instance/veterinaria.db
EOF
    
    echo -e "${GREEN}✓${NC} Archivo .env creado"
    
    if [ -z "$api_key" ]; then
        echo -e "${YELLOW}⚠${NC} Recuerda configurar GOOGLE_API_KEY en el archivo .env"
    fi
fi

# ============================================================================
# 5. INICIALIZAR BASE DE DATOS
# ============================================================================

echo ""
echo -e "${BLUE}[5/7]${NC} Inicializando base de datos..."

# Crear directorio instance si no existe
mkdir -p instance

# Verificar si la base de datos ya existe
if [ -f "instance/veterinaria.db" ]; then
    echo -e "${YELLOW}⚠${NC} La base de datos ya existe."
    echo "Opciones:"
    echo "  1) Mantener base de datos actual (recomendado)"
    echo "  2) Crear respaldo y nueva base de datos"
    echo "  3) Eliminar y crear nueva (¡se perderán todos los datos!)"
    read -p "Elige una opción (1/2/3): " opcion
    
    case $opcion in
        2)
            backup_name="instance/veterinaria_backup_$(date +%Y%m%d_%H%M%S).db"
            cp instance/veterinaria.db "$backup_name"
            echo -e "${GREEN}✓${NC} Respaldo creado: $backup_name"
            rm instance/veterinaria.db
            ;;
        3)
            rm instance/veterinaria.db
            echo -e "${YELLOW}⚠${NC} Base de datos eliminada"
            ;;
        *)
            echo -e "${YELLOW}↷${NC} Manteniendo base de datos actual"
            ;;
    esac
fi

# Crear/actualizar base de datos
if [ ! -f "instance/veterinaria.db" ]; then
    echo "Creando base de datos y tablas..."
    
    python3 << 'PYEOF'
from app import create_app, db
from app.models import Usuario, Categoria
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Crear todas las tablas
    db.create_all()
    
    # Verificar si ya existe el usuario admin
    admin_existe = Usuario.query.filter_by(username='admin').first()
    
    if not admin_existe:
        # Crear usuario administrador
        admin = Usuario(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            rol='administrador',
            activo=True
        )
        db.session.add(admin)
        
        # Crear categorías básicas
        categorias_basicas = [
            'Medicamentos',
            'Alimentos',
            'Accesorios',
            'Higiene',
            'Juguetes',
            'Antiparasitarios',
            'Vitaminas y Suplementos'
        ]
        
        for nombre_cat in categorias_basicas:
            categoria = Categoria(nombre=nombre_cat, activo=True)
            db.session.add(categoria)
        
        db.session.commit()
        print("✅ Base de datos creada exitosamente")
        print("✅ Usuario admin creado: admin / admin123")
        print("✅ Categorías básicas creadas")
    else:
        print("✅ Base de datos verificada")
PYEOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Base de datos inicializada correctamente"
    else
        echo -e "${RED}❌ Error al inicializar la base de datos${NC}"
        exit 1
    fi
else
    # Ejecutar migraciones si existen
    if [ -d "migrations" ]; then
        echo "Aplicando migraciones..."
        flask db upgrade > /dev/null 2>&1 || echo -e "${YELLOW}⚠${NC} No hay migraciones pendientes"
    fi
    echo -e "${GREEN}✓${NC} Base de datos verificada"
fi

# ============================================================================
# 6. CONFIGURAR IMPRESORA USB
# ============================================================================

echo ""
echo -e "${BLUE}[6/7]${NC} Configuración de impresora térmica USB..."

if [ -f "configurar_permisos_usb.sh" ]; then
    echo -e "${YELLOW}📝 Información sobre impresora térmica:${NC}"
    echo "  • Compatible con impresoras térmicas ESC/POS (58mm, 80mm)"
    echo "  • Se detecta automáticamente al conectarla por USB"
    echo "  • Requiere permisos especiales en Linux"
    echo ""
    echo "¿Deseas configurar los permisos USB ahora? (requiere sudo)"
    echo "Esto permitirá que el sistema imprima tickets sin problemas."
    read -p "(s/n): " respuesta
    
    if [ "$respuesta" = "s" ]; then
        echo ""
        echo "Detectando impresoras USB conectadas..."
        echo -e "${YELLOW}────────────────────────────────────────${NC}"
        lsusb | grep -i "print\|thermal\|escpos\|xprinter\|pos" || echo "No se detectaron impresoras conocidas"
        echo -e "${YELLOW}────────────────────────────────────────${NC}"
        echo ""
        
        chmod +x configurar_permisos_usb.sh
        
        if sudo ./configurar_permisos_usb.sh; then
            echo -e "${GREEN}✓${NC} Permisos USB configurados"
            echo -e "${YELLOW}⚠ IMPORTANTE:${NC} Debes cerrar sesión y volver a entrar"
            echo "  para que los permisos surtan efecto, o ejecuta:"
            echo "  sudo udevadm control --reload-rules && sudo udevadm trigger"
        else
            echo -e "${YELLOW}⚠${NC} No se pudieron configurar permisos automáticamente"
            echo "Puedes hacerlo manualmente más tarde: sudo ./configurar_permisos_usb.sh"
        fi
    else
        echo -e "${YELLOW}↷${NC} Configuración de impresora omitida"
        echo "Puedes configurarla más tarde ejecutando: sudo ./configurar_permisos_usb.sh"
    fi
else
    echo -e "${YELLOW}⚠${NC} Script configurar_permisos_usb.sh no encontrado"
fi

# ============================================================================
# 7. VERIFICAR INSTALACIÓN
# ============================================================================

echo ""
echo -e "${BLUE}[7/7]${NC} Verificando instalación..."

# Verificar que Flask está instalado
if python3 -c "import flask" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Flask instalado correctamente"
else
    echo -e "${RED}❌ Flask no está instalado${NC}"
    exit 1
fi

# Verificar que la app se puede importar
if python3 -c "from app import create_app; app = create_app()" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Aplicación verificada correctamente"
else
    echo -e "${RED}❌ Error al verificar la aplicación${NC}"
    exit 1
fi

# ============================================================================
# FINALIZACIÓN
# ============================================================================

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║              ✅ ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!          ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}📋 Información de acceso:${NC}"
echo "  • Usuario: admin"
echo "  • Contraseña: admin123"
echo "  • URL: http://localhost:5000"
echo ""

echo -e "${BLUE}🚀 Para iniciar el sistema:${NC}"
echo "  1. Activa el entorno virtual:"
echo "     ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo "  2. Ejecuta el servidor:"
echo "     ${YELLOW}python run.py${NC}"
echo ""
echo "  3. Abre tu navegador en:"
echo "     ${YELLOW}http://localhost:5000${NC}"
echo ""

echo -e "${BLUE}📝 Notas importantes:${NC}"
echo "  • Cambia la contraseña del admin al primer ingreso"
if [ -z "$api_key" ] || [ "$api_key" = "tu_api_key_aqui" ]; then
    echo "  • Configura GOOGLE_API_KEY en .env para usar el asistente IA"
fi
echo "  • Revisa el README.md para más información"
echo "  • Los respaldos de la BD se guardan en instance/"
echo ""

echo -e "${GREEN}¡Gracias por usar el Sistema de Gestión Veterinaria! 🏥🐾${NC}"
echo ""

# ============================================================================
# PREGUNTAR POR INICIO AUTOMÁTICO
# ============================================================================

echo -e "${BLUE}🚀 ¿Deseas configurar el INICIO AUTOMÁTICO?${NC}"
echo ""
echo "Esto hará que el sistema se inicie automáticamente al encender el PC"
echo "y que el navegador se abra solo en http://localhost:5000"
echo ""
read -p "¿Configurar inicio automático ahora? (s/n): " config_autostart

if [ "$config_autostart" = "s" ]; then
    echo ""
    echo -e "${BLUE}Configurando inicio automático...${NC}"
    
    if [ -f "configurar_inicio_automatico.sh" ]; then
        chmod +x configurar_inicio_automatico.sh
        
        if sudo ./configurar_inicio_automatico.sh; then
            echo -e "${GREEN}✓${NC} Inicio automático configurado exitosamente"
        else
            echo -e "${YELLOW}⚠${NC} Hubo un problema al configurar el inicio automático"
            echo "Puedes intentarlo manualmente más tarde:"
            echo "  sudo ./configurar_inicio_automatico.sh"
        fi
    else
        echo -e "${RED}❌ No se encontró el script configurar_inicio_automatico.sh${NC}"
    fi
else
    echo -e "${YELLOW}↷${NC} Inicio automático omitido"
    echo ""
    echo "Puedes configurarlo más tarde ejecutando:"
    echo "  ${YELLOW}sudo ./configurar_inicio_automatico.sh${NC}"
fi

echo ""

