#!/usr/bin/env python3
"""
Script simple para probar comandos del cajón monedero 3BUMEN 405XD
Ejecuta comandos uno por uno y espera confirmación del usuario
"""

import sys
import time

try:
    from escpos.printer import Usb
    import usb.core
except ImportError:
    print("Error: Necesitas instalar python-escpos y pyusb")
    print("Ejecuta: pip install python-escpos pyusb")
    sys.exit(1)

def detectar_impresora():
    """Detecta la impresora Xprinter XP-58IIT"""
    impresoras_xprinter = [
        (0x0483, 0x070b),  # Xprinter XP-58IIT
        (0x0483, 0x5743),  # Xprinter común
    ]
    
    for vendor_id, product_id in impresoras_xprinter:
        try:
            printer = Usb(vendor_id, product_id, timeout=0)
            print(f"✓ Impresora detectada: VID={hex(vendor_id)}, PID={hex(product_id)}")
            return printer
        except:
            continue
    
    print("✗ No se encontró la impresora")
    return None

def probar_comando(printer, nombre, comando):
    """Prueba un comando y espera confirmación del usuario"""
    try:
        if hasattr(printer, 'device') and printer.device:
            print(f"\nProbando: {nombre}")
            print(f"Comando hex: {' '.join(f'{b:02X}' for b in comando)}")
            printer._raw(comando)
            time.sleep(0.5)
            
            respuesta = input("¿Se abrió el cajón? (s/n): ").lower().strip()
            if respuesta == 's':
                print("✓ ¡ÉXITO! Este comando funciona.")
                return True
        else:
            print("✗ Error: La conexión con la impresora se perdió")
            return False
    except Exception as e:
        print(f"✗ Error al enviar comando: {e}")
        return False
    
    return False

def main():
    print("=" * 60)
    print("PRUEBA DE COMANDOS PARA CAJÓN MONEDERO 3BUMEN 405XD")
    print("=" * 60)
    
    printer = detectar_impresora()
    if not printer:
        return
    
    # Inicializar impresora
    try:
        printer._raw(b'\x1B\x40')  # ESC @
        time.sleep(0.2)
        print("✓ Impresora inicializada")
    except:
        pass
    
    # Lista de comandos a probar
    comandos = [
        ("ESC p 0 50 200 (100ms ON, 400ms OFF)", b'\x1B\x70\x00\x32\xC8'),
        ("ESC p 0 60 255 (120ms ON, 510ms OFF)", b'\x1B\x70\x00\x3C\xFF'),
        ("ESC p 0 25 250 (50ms ON, 500ms OFF)", b'\x1B\x70\x00\x19\xFA'),
        ("ESC p 0 50 50 (100ms ON, 100ms OFF)", b'\x1B\x70\x00\x32\x32'),
        ("ESC p 0 16 16 (32ms ON, 32ms OFF)", b'\x1B\x70\x00\x10\x10'),
        ("ESC p 1 50 200 (Pin 1, 100ms ON, 400ms OFF)", b'\x1B\x70\x01\x32\xC8'),
        ("ESC p 1 25 250 (Pin 1, 50ms ON, 500ms OFF)", b'\x1B\x70\x01\x19\xFA'),
        ("ESC p 48 50 200 (m=48, 100ms ON, 400ms OFF)", b'\x1B\x70\x30\x32\xC8'),
        ("ESC p 49 50 200 (m=49, 100ms ON, 400ms OFF)", b'\x1B\x70\x31\x32\xC8'),
    ]
    
    print(f"\nSe probarán {len(comandos)} comandos.")
    print("Después de cada comando, indica si el cajón se abrió.\n")
    input("Presiona ENTER para comenzar...")
    
    for nombre, comando in comandos:
        if probar_comando(printer, nombre, comando):
            print(f"\n{'='*60}")
            print(f"COMANDO EXITOSO: {nombre}")
            print(f"Hex: {' '.join(f'{b:02X}' for b in comando)}")
            print(f"{'='*60}")
            break
        
        continuar = input("\n¿Continuar con el siguiente comando? (s/n): ").lower().strip()
        if continuar != 's':
            break
    
    # También probar cashdraw()
    print("\n" + "="*60)
    print("Probando método cashdraw()")
    print("="*60)
    
    for pin in [2, 5, 0, 1]:
        try:
            if hasattr(printer, 'device') and printer.device:
                print(f"\nProbando: cashdraw(pin={pin})")
                printer.cashdraw(pin)
                time.sleep(0.5)
                
                respuesta = input("¿Se abrió el cajón? (s/n): ").lower().strip()
                if respuesta == 's':
                    print(f"✓ ¡ÉXITO! cashdraw(pin={pin}) funciona.")
                    break
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    try:
        printer.close()
    except:
        pass
    
    print("\n" + "="*60)
    print("Prueba completada")
    print("="*60)

if __name__ == "__main__":
    main()

