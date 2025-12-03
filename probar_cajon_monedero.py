#!/usr/bin/env python3
"""
Script para probar diferentes comandos y encontrar cuál abre el cajón monedero.
Ejecuta este script y prueba cada comando presionando Enter.
"""

import sys
import time

def probar_comando(printer, nombre, comando_func):
    """Prueba un comando y espera confirmación del usuario"""
    print(f"\n{'='*60}")
    print(f"Probando: {nombre}")
    print(f"{'='*60}")
    input("Presiona Enter para enviar el comando...")
    
    try:
        comando_func(printer)
        print("✓ Comando enviado correctamente")
        respuesta = input("¿Se abrió el cajón? (s/n): ").lower().strip()
        if respuesta == 's' or respuesta == 'si' or respuesta == 'y' or respuesta == 'yes':
            return True
    except Exception as e:
        print(f"✗ Error al enviar comando: {str(e)}")
    
    return False

def main():
    print("="*60)
    print("SCRIPT DE PRUEBA - CAJÓN MONEDERO")
    print("="*60)
    print("\nEste script probará diferentes comandos para abrir el cajón.")
    print("Después de cada comando, indica si el cajón se abrió o no.")
    print("\nAsegúrate de que la impresora esté conectada y encendida.")
    print("\nPresiona Ctrl+C para salir en cualquier momento.\n")
    
    input("Presiona Enter para comenzar...")
    
    try:
        from escpos.printer import Usb
        import usb.core
    except ImportError:
        print("ERROR: python-escpos no está instalado.")
        print("Ejecuta: pip install python-escpos pyusb")
        sys.exit(1)
    
    # Detectar impresora
    print("\nDetectando impresora...")
    printer = None
    
    # IDs conocidos de la impresora
    impresoras = [
        (0x0483, 0x070b),  # Xprinter XP-58IIT detectada
        (1155, 1803),       # En decimal
        (0x0483, 0x5743),  # Otra variante
    ]
    
    for vendor_id, product_id in impresoras:
        try:
            printer = Usb(vendor_id, product_id, timeout=0)
            print(f"✓ Impresora detectada: Vendor ID: 0x{vendor_id:04x}, Product ID: 0x{product_id:04x}")
            break
        except Exception as e:
            continue
    
    if not printer:
        print("✗ No se pudo detectar la impresora.")
        print("Verifica que esté conectada y que tengas permisos USB.")
        sys.exit(1)
    
    # Lista de comandos a probar
    comandos = []
    
    # Método 1: cashdraw() con diferentes pins
    comandos.append(("cashdraw(pin=2)", lambda p: p.cashdraw(2)))
    comandos.append(("cashdraw(pin=1)", lambda p: p.cashdraw(1)))
    comandos.append(("cashdraw(pin=0)", lambda p: p.cashdraw(0)))
    comandos.append(("cashdraw(pin=5)", lambda p: p.cashdraw(5)))
    
    # Método 2: Comandos directos ESC/POS (3bumen 405xd puede necesitar tiempos específicos)
    # Comandos comunes
    comandos.append(("ESC p 0 25 25", lambda p: p._raw(b'\x1B\x70\x00\x19\x19')))
    comandos.append(("ESC p 1 25 25", lambda p: p._raw(b'\x1B\x70\x01\x19\x19')))
    comandos.append(("ESC p 0 50 50", lambda p: p._raw(b'\x1B\x70\x00\x32\x32')))
    comandos.append(("ESC p 1 50 50", lambda p: p._raw(b'\x1B\x70\x01\x32\x32')))
    comandos.append(("ESC p 0 100 100", lambda p: p._raw(b'\x1B\x70\x00\x64\x64')))
    comandos.append(("ESC p 1 100 100", lambda p: p._raw(b'\x1B\x70\x01\x64\x64')))
    comandos.append(("ESC p 0 200 200", lambda p: p._raw(b'\x1B\x70\x00\xC8\xC8')))
    comandos.append(("ESC p 1 200 200", lambda p: p._raw(b'\x1B\x70\x01\xC8\xC8')))
    
    # Comandos específicos para 3bumen (puede necesitar pulso más largo)
    comandos.append(("ESC p 0 25 250 (3bumen)", lambda p: p._raw(b'\x1B\x70\x00\x19\xFA')))
    comandos.append(("ESC p 1 25 250 (3bumen)", lambda p: p._raw(b'\x1B\x70\x01\x19\xFA')))
    comandos.append(("ESC p 0 50 250 (3bumen)", lambda p: p._raw(b'\x1B\x70\x00\x32\xFA')))
    comandos.append(("ESC p 1 50 250 (3bumen)", lambda p: p._raw(b'\x1B\x70\x01\x32\xFA')))
    comandos.append(("ESC p 0 100 250 (3bumen)", lambda p: p._raw(b'\x1B\x70\x00\x64\xFA')))
    comandos.append(("ESC p 1 100 250 (3bumen)", lambda p: p._raw(b'\x1B\x70\x01\x64\xFA')))
    
    # Método 3: Comandos alternativos
    comandos.append(("DLE DC4 (0x10 0x14)", lambda p: p._raw(b'\x10\x14\x01\x01\x0A')))
    comandos.append(("ESC p básico", lambda p: p._raw(b'\x1B\x70')))
    comandos.append(("ESC p 0 0 0", lambda p: p._raw(b'\x1B\x70\x00\x00\x00')))
    comandos.append(("ESC p 1 0 0", lambda p: p._raw(b'\x1B\x70\x01\x00\x00')))
    
    # Método 4: Comandos con diferentes tiempos (más variaciones)
    for tiempo in [10, 20, 30, 40, 60, 80, 120, 150, 200, 250]:
        comandos.append((f"ESC p 0 {tiempo} {tiempo}", 
                        lambda p, t=tiempo: p._raw(bytes([0x1B, 0x70, 0x00, t, t]))))
        comandos.append((f"ESC p 1 {tiempo} {tiempo}", 
                        lambda p, t=tiempo: p._raw(bytes([0x1B, 0x70, 0x01, t, t]))))
    
    # Método 5: Comandos con tiempos asimétricos (común en algunos cajones)
    tiempos_asimetricos = [
        (25, 250), (50, 250), (100, 250), (25, 200), (50, 200), (100, 200)
    ]
    for t1, t2 in tiempos_asimetricos:
        comandos.append((f"ESC p 0 {t1} {t2} (asimétrico)", 
                        lambda p, t1=t1, t2=t2: p._raw(bytes([0x1B, 0x70, 0x00, t1, t2]))))
        comandos.append((f"ESC p 1 {t1} {t2} (asimétrico)", 
                        lambda p, t1=t1, t2=t2: p._raw(bytes([0x1B, 0x70, 0x01, t1, t2]))))
    
    print(f"\nSe probarán {len(comandos)} comandos diferentes.")
    print("Después de cada prueba, indica si el cajón se abrió.\n")
    
    input("Presiona Enter para comenzar las pruebas...")
    
    comandos_exitosos = []
    
    for i, (nombre, comando_func) in enumerate(comandos, 1):
        print(f"\n[{i}/{len(comandos)}]")
        if probar_comando(printer, nombre, comando_func):
            comandos_exitosos.append(nombre)
            print(f"\n¡ÉXITO! El comando '{nombre}' abrió el cajón.")
            continuar = input("\n¿Quieres probar más comandos? (s/n): ").lower().strip()
            if continuar != 's' and continuar != 'si' and continuar != 'y' and continuar != 'yes':
                break
        
        time.sleep(0.5)  # Pequeña pausa entre comandos
    
    # Cerrar conexión
    try:
        printer.close()
    except:
        pass
    
    # Resumen
    print("\n" + "="*60)
    print("RESUMEN")
    print("="*60)
    
    if comandos_exitosos:
        print(f"\n✓ Comandos que abrieron el cajón ({len(comandos_exitosos)}):")
        for cmd in comandos_exitosos:
            print(f"  - {cmd}")
        print("\nUsa el PRIMER comando exitoso en tu aplicación.")
    else:
        print("\n✗ Ningún comando abrió el cajón.")
        print("\nPosibles causas:")
        print("1. El cajón no está correctamente conectado a la impresora")
        print("2. El cajón requiere un comando específico del fabricante")
        print("3. Necesitas verificar la documentación de tu modelo específico")
        print("4. Puede requerir configuración adicional en la impresora")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

