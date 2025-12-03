#!/usr/bin/env python3
"""
Script automático para probar múltiples comandos y encontrar cuál abre el cajón monedero.
Ejecuta todos los comandos automáticamente con pausas entre ellos.
"""

from escpos.printer import Usb
import time

def main():
    print("="*70)
    print("SCRIPT AUTOMÁTICO - PRUEBA DE COMANDOS CAJÓN MONEDERO")
    print("="*70)
    print("\nEste script probará automáticamente muchos comandos diferentes.")
    print("Observa el cajón y cuando se abra, anota el número del comando.")
    print("\nAsegúrate de que la impresora esté conectada y encendida.")
    print("\nPresiona Ctrl+C para detener en cualquier momento.\n")
    
    input("Presiona Enter para comenzar...")
    
    try:
        # Detectar impresora
        print("\nDetectando impresora...")
        printer = Usb(0x0483, 0x070b, timeout=0)
        print("✓ Impresora detectada\n")
        print("="*70)
        print("INICIANDO PRUEBAS AUTOMÁTICAS")
        print("="*70)
        print("\nObserva el cajón monedero...\n")
        
        # Lista completa de comandos a probar
        comandos = []
        contador = 1
        
        # 1. Comandos con cashdraw()
        print("GRUPO 1: Método cashdraw()")
        print("-" * 70)
        for pin in [0, 1, 2, 3, 4, 5]:
            comandos.append((contador, f"cashdraw(pin={pin})", lambda p, pin=pin: p.cashdraw(pin)))
            contador += 1
        
        # 2. Comandos ESC p con diferentes tiempos (pin 0) - más selectivo
        print("\nGRUPO 2: ESC p 0 con diferentes tiempos")
        print("-" * 70)
        tiempos_t1 = [5, 10, 12, 14, 16, 18, 20, 25, 30, 40, 50]
        tiempos_t2 = [10, 16, 20, 25, 32, 40, 50, 64, 80, 100, 128, 200, 250, 255]
        for t1 in tiempos_t1:
            for t2 in tiempos_t2:
                if t1 <= t2:
                    cmd_bytes = bytes([0x1B, 0x70, 0x00, t1, t2])
                    comandos.append((contador, f"ESC p 0 {t1} {t2}", lambda p, cmd=cmd_bytes: p._raw(cmd)))
                    contador += 1
        
        # 3. Comandos ESC p con diferentes tiempos (pin 1)
        print("\nGRUPO 3: ESC p 1 con diferentes tiempos")
        print("-" * 70)
        tiempos_pin1 = [10, 16, 20, 25, 50, 100, 250]
        for t1 in tiempos_pin1:
            for t2 in tiempos_pin1:
                if t1 <= t2:
                    cmd_bytes = bytes([0x1B, 0x70, 0x01, t1, t2])
                    comandos.append((contador, f"ESC p 1 {t1} {t2}", lambda p, cmd=cmd_bytes: p._raw(cmd)))
                    contador += 1
        
        # 4. Comandos específicos comunes
        print("\nGRUPO 4: Comandos específicos comunes")
        print("-" * 70)
        comandos_especificos = [
            (b'\x1B\x70\x00\x10\x10', "ESC p 0 16 16 (ya probado)"),
            (b'\x1B\x70\x00\x10\x20', "ESC p 0 16 32"),
            (b'\x1B\x70\x00\x10\x40', "ESC p 0 16 64"),
            (b'\x1B\x70\x00\x10\x80', "ESC p 0 16 128"),
            (b'\x1B\x70\x00\x10\xFF', "ESC p 0 16 255"),
            (b'\x1B\x70\x01\x10\x10', "ESC p 1 16 16"),
            (b'\x1B\x70\x01\x10\x20', "ESC p 1 16 32"),
            (b'\x1B\x70\x00\x19\xFA', "ESC p 0 25 250 (común)"),
            (b'\x1B\x70\x01\x19\xFA', "ESC p 1 25 250"),
            (b'\x1B\x70\x00\x32\x32', "ESC p 0 50 50"),
            (b'\x1B\x70\x00\x40\x40', "ESC p 0 64 64"),
            (b'\x1B\x70\x00\x3C\xFF', "ESC p 0 60 255"),
            (b'\x1B\x70\x00\x32\xC8', "ESC p 0 50 200"),
            (b'\x1B\x70', "ESC p básico"),
            (b'\x10\x14\x01\x01\x0A', "DLE DC4"),
            (b'\x10\x14\x02\x02\x0A', "DLE DC4 variante"),
        ]
        
        for cmd_bytes, nombre in comandos_especificos:
            comandos.append((contador, nombre, lambda p, cmd=cmd_bytes: p._raw(cmd)))
            contador += 1
        
        # 5. Comandos con tiempos asimétricos específicos
        print("\nGRUPO 5: Comandos asimétricos específicos")
        print("-" * 70)
        asimetricos = [
            (10, 20), (10, 50), (10, 100), (10, 250),
            (16, 20), (16, 50), (16, 100), (16, 250),
            (20, 50), (20, 100), (20, 250),
            (25, 50), (25, 100), (25, 250),
            (50, 100), (50, 200), (50, 250),
            (100, 200), (100, 250),
        ]
        
        for t1, t2 in asimetricos:
            # Pin 0
            cmd_bytes = bytes([0x1B, 0x70, 0x00, t1, t2])
            comandos.append((contador, f"ESC p 0 {t1} {t2} (asimétrico)", lambda p, cmd=cmd_bytes: p._raw(cmd)))
            contador += 1
            # Pin 1
            cmd_bytes = bytes([0x1B, 0x70, 0x01, t1, t2])
            comandos.append((contador, f"ESC p 1 {t1} {t2} (asimétrico)", lambda p, cmd=cmd_bytes: p._raw(cmd)))
            contador += 1
        
        print(f"\nTotal de comandos a probar: {len(comandos)}")
        print("\n" + "="*70)
        print("INICIANDO PRUEBAS...")
        print("="*70)
        print("\nObserva el cajón monedero. Cuando se abra, anota el número.\n")
        input("Presiona Enter para comenzar las pruebas automáticas...")
        
        # Ejecutar todos los comandos
        comandos_exitosos = []
        
        for num, nombre, comando_func in comandos:
            try:
                print(f"[{num:3d}] Probando: {nombre}")
                comando_func(printer)
                time.sleep(0.3)  # Pausa de 300ms entre comandos para observar
            except Exception as e:
                print(f"      ✗ Error: {str(e)[:50]}")
                time.sleep(0.1)
        
        # Cerrar conexión
        printer.close()
        
        # Resumen
        print("\n" + "="*70)
        print("PRUEBAS COMPLETADAS")
        print("="*70)
        print(f"\nSe probaron {len(comandos)} comandos diferentes.")
        print("\n¿Se abrió el cajón con alguno de los comandos?")
        print("Si sí, indica el número del comando que funcionó.")
        
    except KeyboardInterrupt:
        print("\n\nPruebas interrumpidas por el usuario.")
        try:
            printer.close()
        except:
            pass
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        try:
            printer.close()
        except:
            pass

if __name__ == "__main__":
    main()

