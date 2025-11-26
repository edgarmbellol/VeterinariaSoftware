#!/bin/bash

# Script alternativo que instala dependencias globalmente (solo para desarrollo)
# NOTA: Se recomienda usar setup_venv.sh con un entorno virtual

echo "=========================================="
echo "Instalación SIN Entorno Virtual"
echo "⚠️  ADVERTENCIA: Esto instalará paquetes globalmente"
echo "=========================================="

read -p "¿Continuar? (s/n): " respuesta
if [ "$respuesta" != "s" ] && [ "$respuesta" != "S" ]; then
    echo "Cancelado"
    exit 0
fi

echo "📦 Actualizando pip..."
python3 -m pip install --upgrade pip --user

echo "📦 Instalando dependencias..."
python3 -m pip install --user -r requirements.txt

# Configurar FLASK_APP
export FLASK_APP=run.py

echo ""
echo "=========================================="
echo "Ejecutando Migración de Base de Datos"
echo "=========================================="

# Intentar ejecutar la migración
python3 -m flask db upgrade

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Migración completada exitosamente!"
    echo ""
    echo "Para ejecutar la aplicación:"
    echo "  export FLASK_APP=run.py"
    echo "  python3 run.py"
else
    echo ""
    echo "❌ Error al ejecutar la migración"
    echo ""
    echo "Intenta ejecutar manualmente:"
    echo "  export FLASK_APP=run.py"
    echo "  python3 -m flask db upgrade"
    exit 1
fi

