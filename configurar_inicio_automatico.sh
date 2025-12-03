#!/bin/bash

# ============================================================================
# Script para configurar inicio automático del Sistema de Veterinaria
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║     🚀 CONFIGURACIÓN DE INICIO AUTOMÁTICO - VETERINARIA       ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Obtener directorio actual y usuario
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CURRENT_USER=$(whoami)

echo -e "${BLUE}Configuración detectada:${NC}"
echo "  📁 Directorio: $SCRIPT_DIR"
echo "  👤 Usuario: $CURRENT_USER"
echo ""

# ============================================================================
# 1. CONFIGURAR SERVICIO SYSTEMD (Servidor Flask)
# ============================================================================

echo -e "${BLUE}[1/3]${NC} Configurando servicio systemd..."

# Crear archivo de servicio con rutas correctas
cat > /tmp/veterinaria.service << EOF
[Unit]
Description=Sistema de Gestión Veterinaria
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin"
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Copiar a systemd
if sudo cp /tmp/veterinaria.service /etc/systemd/system/; then
    echo -e "${GREEN}✓${NC} Archivo de servicio creado"
else
    echo -e "${RED}❌ Error al crear servicio${NC}"
    exit 1
fi

# Recargar systemd
sudo systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd recargado"

# Habilitar servicio
if sudo systemctl enable veterinaria.service; then
    echo -e "${GREEN}✓${NC} Servicio habilitado para inicio automático"
else
    echo -e "${RED}❌ Error al habilitar servicio${NC}"
    exit 1
fi

# Iniciar servicio
if sudo systemctl start veterinaria.service; then
    echo -e "${GREEN}✓${NC} Servicio iniciado"
else
    echo -e "${YELLOW}⚠${NC} El servicio no pudo iniciarse (verifica los logs)"
fi

# Verificar estado
sleep 2
if sudo systemctl is-active --quiet veterinaria.service; then
    echo -e "${GREEN}✓${NC} Servicio funcionando correctamente"
else
    echo -e "${YELLOW}⚠${NC} El servicio está instalado pero no está corriendo"
    echo "Para ver errores ejecuta: sudo systemctl status veterinaria.service"
fi

# ============================================================================
# 2. CONFIGURAR AUTOSTART DEL NAVEGADOR
# ============================================================================

echo ""
echo -e "${BLUE}[2/3]${NC} Configurando apertura automática del navegador..."

# Detectar entorno de escritorio
if [ "$XDG_CURRENT_DESKTOP" ]; then
    echo -e "${GREEN}✓${NC} Entorno detectado: $XDG_CURRENT_DESKTOP"
else
    echo -e "${YELLOW}⚠${NC} No se detectó entorno de escritorio"
fi

# Crear directorio autostart si no existe
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# Crear archivo .desktop para abrir navegador
cat > "$AUTOSTART_DIR/veterinaria-browser.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Veterinaria - Abrir Navegador
Comment=Abre el sistema de veterinaria en el navegador
Exec=bash -c 'sleep 5 && xdg-open http://localhost:5000'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

chmod +x "$AUTOSTART_DIR/veterinaria-browser.desktop"
echo -e "${GREEN}✓${NC} Navegador configurado para abrirse automáticamente"

# ============================================================================
# 3. CREAR SCRIPT DE ACCESO RÁPIDO
# ============================================================================

echo ""
echo -e "${BLUE}[3/3]${NC} Creando acceso rápido en el escritorio..."

# Crear icono de acceso directo en el escritorio
DESKTOP_DIR="$HOME/Escritorio"
if [ ! -d "$DESKTOP_DIR" ]; then
    DESKTOP_DIR="$HOME/Desktop"
fi

if [ -d "$DESKTOP_DIR" ]; then
    cat > "$DESKTOP_DIR/Veterinaria.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Sistema Veterinaria
Comment=Abrir Sistema de Gestión Veterinaria
Exec=xdg-open http://localhost:5000
Icon=applications-science
Terminal=false
Categories=Application;
EOF
    
    chmod +x "$DESKTOP_DIR/Veterinaria.desktop"
    echo -e "${GREEN}✓${NC} Acceso directo creado en el escritorio"
else
    echo -e "${YELLOW}⚠${NC} No se encontró el escritorio"
fi

# ============================================================================
# INFORMACIÓN FINAL
# ============================================================================

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║           ✅ ¡INICIO AUTOMÁTICO CONFIGURADO!                   ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}📋 ¿Qué se configuró?${NC}"
echo ""
echo "  1️⃣  ${GREEN}Servicio systemd:${NC}"
echo "     • El servidor Flask se inicia automáticamente al encender el PC"
echo "     • Se reinicia automáticamente si falla"
echo "     • Corre en segundo plano (background)"
echo ""
echo "  2️⃣  ${GREEN}Navegador automático:${NC}"
echo "     • El navegador se abre automáticamente en http://localhost:5000"
echo "     • Espera 5 segundos para que el servidor esté listo"
echo ""
echo "  3️⃣  ${GREEN}Acceso directo:${NC}"
echo "     • Icono en el escritorio para abrir el sistema rápidamente"
echo ""

echo -e "${BLUE}🔧 Comandos útiles:${NC}"
echo ""
echo "  Ver estado del servicio:"
echo "    ${YELLOW}sudo systemctl status veterinaria${NC}"
echo ""
echo "  Ver logs en tiempo real:"
echo "    ${YELLOW}sudo journalctl -u veterinaria -f${NC}"
echo ""
echo "  Detener el servicio:"
echo "    ${YELLOW}sudo systemctl stop veterinaria${NC}"
echo ""
echo "  Reiniciar el servicio:"
echo "    ${YELLOW}sudo systemctl restart veterinaria${NC}"
echo ""
echo "  Deshabilitar inicio automático:"
echo "    ${YELLOW}sudo systemctl disable veterinaria${NC}"
echo ""

echo -e "${BLUE}⚡ ¿Qué pasa ahora?${NC}"
echo ""
echo "  ${GREEN}✓${NC} El sistema YA está corriendo en http://localhost:5000"
echo "  ${GREEN}✓${NC} Cuando reinicies el PC, se iniciará automáticamente"
echo "  ${GREEN}✓${NC} El navegador se abrirá solo 5 segundos después del inicio"
echo ""

echo -e "${YELLOW}💡 Tip:${NC} Para probar sin reiniciar, abre: http://localhost:5000"
echo ""

# Preguntar si desea abrir ahora
read -p "¿Deseas abrir el sistema en el navegador ahora? (s/n): " respuesta
if [ "$respuesta" = "s" ]; then
    xdg-open http://localhost:5000 &
    echo -e "${GREEN}✓${NC} Abriendo navegador..."
fi

echo ""
echo -e "${GREEN}¡Listo! 🎉${NC}"
echo ""

