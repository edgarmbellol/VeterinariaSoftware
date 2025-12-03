#!/bin/bash

# ============================================================================
# Script para desactivar inicio automático del Sistema de Veterinaria
# ============================================================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     🛑 DESACTIVAR INICIO AUTOMÁTICO - VETERINARIA             ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

echo -e "${YELLOW}⚠ Este script desactivará:${NC}"
echo "  • Servicio systemd (servidor Flask)"
echo "  • Apertura automática del navegador"
echo "  • Acceso directo del escritorio"
echo ""

read -p "¿Deseas continuar? (s/n): " respuesta
if [ "$respuesta" != "s" ]; then
    echo "Operación cancelada"
    exit 0
fi

echo ""

# Detener y deshabilitar servicio
echo -e "${BLUE}[1/3]${NC} Desactivando servicio systemd..."

if sudo systemctl stop veterinaria.service 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Servicio detenido"
else
    echo -e "${YELLOW}⚠${NC} El servicio no estaba corriendo"
fi

if sudo systemctl disable veterinaria.service 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Servicio deshabilitado"
else
    echo -e "${YELLOW}⚠${NC} El servicio no estaba habilitado"
fi

if sudo rm -f /etc/systemd/system/veterinaria.service 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Archivo de servicio eliminado"
    sudo systemctl daemon-reload
fi

# Eliminar autostart del navegador
echo ""
echo -e "${BLUE}[2/3]${NC} Eliminando apertura automática del navegador..."

if rm -f "$HOME/.config/autostart/veterinaria-browser.desktop" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Autostart del navegador eliminado"
else
    echo -e "${YELLOW}⚠${NC} No se encontró configuración de autostart"
fi

# Eliminar acceso directo
echo ""
echo -e "${BLUE}[3/3]${NC} Eliminando acceso directo del escritorio..."

DESKTOP_DIR="$HOME/Escritorio"
if [ ! -d "$DESKTOP_DIR" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi

if rm -f "$DESKTOP_DIR/Veterinaria.desktop" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Acceso directo eliminado"
else
    echo -e "${YELLOW}⚠${NC} No se encontró acceso directo"
fi

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║        ✅ INICIO AUTOMÁTICO DESACTIVADO CORRECTAMENTE          ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${BLUE}📋 Estado actual:${NC}"
echo "  • El servidor NO se iniciará automáticamente al encender el PC"
echo "  • El navegador NO se abrirá automáticamente"
echo "  • Puedes iniciar manualmente con: python run.py"
echo ""

echo -e "${YELLOW}💡 Para volver a activar el inicio automático:${NC}"
echo "   ./configurar_inicio_automatico.sh"
echo ""

