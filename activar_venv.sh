#!/bin/bash

# Script para activar el entorno virtual y ejecutar comandos Flask

if [ ! -d "venv" ]; then
    echo "❌ El entorno virtual no existe. Ejecuta primero: ./setup_venv.sh"
    exit 1
fi

echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Configurar FLASK_APP
export FLASK_APP=run.py

echo "✅ Entorno virtual activado"
echo ""
echo "Ahora puedes ejecutar comandos Flask como:"
echo "  flask db upgrade"
echo "  flask db migrate -m 'mensaje'"
echo "  python run.py"
echo ""
echo "Para desactivar el entorno virtual, ejecuta: deactivate"

# Si se pasaron argumentos, ejecutarlos
if [ $# -gt 0 ]; then
    echo ""
    echo "Ejecutando: $@"
    exec "$@"
else
    # Mantener el shell activo
    exec bash
fi

