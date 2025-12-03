#!/usr/bin/env python3
"""
Script simple para probar el comando más común para abrir cajón monedero
Según documentación: 1B 70 00 19 FA (ESC p 0 25 250)
"""

from escpos.printer import Usb
import time

print("="*60)
print("PRUEBA RÁPIDA - COMANDO CAJÓN MONEDERO")
print("="*60)
print("\nEste script probará el comando más común:")
print("1B 70 00 19 FA (ESC p 0 25 250)")
print("\nAsegúrate de que la impresora esté conectada y encendida.\n")

input("Presiona Enter para comenzar...")

try:
    # Detectar impresora
    print("\nDetectando impresora...")
    printer = Usb(0x0483, 0x070b, timeout=0)
    print("✓ Impresora detectada\n")
    
    # Probar el comando más común según documentación
    print("Enviando comando: ESC p 0 25 250 (1B 70 00 19 FA)...")
    printer._raw(b'\x1B\x70\x00\x19\xFA')
    print("✓ Comando enviado")
    
    time.sleep(0.5)
    
    # También probar con cashdraw
    print("\nEnviando comando: cashdraw(pin=2)...")
    printer.cashdraw(2)
    print("✓ Comando enviado")
    
    time.sleep(0.5)
    
    print("\nEnviando comando: cashdraw(pin=5)...")
    printer.cashdraw(5)
    print("✓ Comando enviado")
    
    printer.close()
    
    print("\n" + "="*60)
    print("¿Se abrió el cajón con alguno de estos comandos?")
    print("="*60)
    print("\nSi no se abrió, ejecuta el script completo:")
    print("  python3 probar_cajon_monedero.py")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    print("\nVerifica que:")
    print("1. La impresora esté conectada por USB")
    print("2. Tengas permisos USB configurados")
    print("3. La impresora esté encendida")

