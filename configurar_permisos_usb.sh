#!/bin/bash
# Script para configurar permisos USB para la impresora Xprinter XP-58IIT
# IDs detectados: Vendor ID: 1155 (0x0483), Product ID: 22339 (0x5743)

echo "=========================================="
echo "Configuración de Permisos USB"
echo "Impresora: Xprinter XP-58IIT"
echo "Vendor ID: 0x0483 (1155)"
echo "Product ID: 0x070b (1803)"
echo "=========================================="
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "Este script debe ejecutarse con sudo:"
    echo "  sudo ./configurar_permisos_usb.sh"
    exit 1
fi

# Crear el archivo de reglas udev
RULE_FILE="/etc/udev/rules.d/99-impresora-xprinter.rules"

echo "Creando regla udev en $RULE_FILE..."

cat > "$RULE_FILE" << EOF
# Regla para impresora térmica Xprinter XP-58IIT
# Vendor ID: 0x0483 (1155), Product ID: 0x070b (1803)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="070b", MODE="0666", GROUP="plugdev"
EOF

echo "✓ Regla creada"
echo ""

# Agregar el usuario actual al grupo plugdev si no está
CURRENT_USER=${SUDO_USER:-$USER}
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(logname 2>/dev/null || echo "")
fi

if [ -n "$CURRENT_USER" ]; then
    echo "Agregando usuario '$CURRENT_USER' al grupo 'plugdev'..."
    usermod -a -G plugdev "$CURRENT_USER"
    echo "✓ Usuario agregado al grupo"
    echo ""
fi

# Recargar reglas udev
echo "Recargando reglas udev..."
udevadm control --reload-rules
udevadm trigger
echo "✓ Reglas recargadas"
echo ""

echo "=========================================="
echo "Configuración completada"
echo "=========================================="
echo ""
echo "IMPORTANTE:"
echo "1. Si agregaste tu usuario al grupo plugdev, necesitas:"
echo "   - Cerrar sesión y volver a iniciar sesión, O"
echo "   - Ejecutar: newgrp plugdev"
echo ""
echo "2. Desconecta y vuelve a conectar la impresora USB"
echo ""
echo "3. Prueba la impresión desde la aplicación"
echo ""

