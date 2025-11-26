#!/bin/bash

# Script para configurar el entorno virtual y ejecutar la migración

echo "=========================================="
echo "Configuración del Entorno Virtual"
echo "=========================================="

# Verificar si python3-venv está instalado
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ Error: python3-venv no está instalado"
    echo ""
    echo "Por favor instala el paquete con:"
    echo "  sudo apt install python3-venv"
    echo ""
    echo "O si usas python3.12 específicamente:"
    echo "  sudo apt install python3.12-venv"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Error al crear el entorno virtual"
        exit 1
    fi
    echo "✅ Entorno virtual creado"
else
    echo "✅ Entorno virtual ya existe"
fi

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "📦 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Configurar FLASK_APP si no está configurado
if [ -z "$FLASK_APP" ]; then
    export FLASK_APP=run.py
fi

# Ejecutar migración
echo ""
echo "=========================================="
echo "Ejecutando Migración de Base de Datos"
echo "=========================================="
flask db upgrade

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Migración completada exitosamente!"
    echo ""
    echo "Para activar el entorno virtual en el futuro, ejecuta:"
    echo "  source venv/bin/activate"
    echo ""
    echo "Para ejecutar la aplicación:"
    echo "  python run.py"
else
    echo ""
    echo "❌ Error al ejecutar la migración"
    exit 1
fi

