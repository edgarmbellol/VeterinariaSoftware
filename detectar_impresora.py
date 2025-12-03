#!/usr/bin/env python3
"""
Script para detectar la impresora térmica USB conectada.
Ejecuta este script para identificar los IDs (vendor_id, product_id) de tu impresora.
"""

import sys
import usb.core
import usb.util

def detectar_dispositivos_usb():
    """Detecta todos los dispositivos USB conectados"""
    print("=" * 60)
    print("DETECCIÓN DE DISPOSITIVOS USB")
    print("=" * 60)
    print()
    
    try:
        # Buscar todos los dispositivos USB
        devices = usb.core.find(find_all=True)
        
        if devices is None:
            print("No se encontraron dispositivos USB.")
            return
        
        dispositivos = list(devices)
        
        if len(dispositivos) == 0:
            print("No se encontraron dispositivos USB conectados.")
            return
        
        print(f"Se encontraron {len(dispositivos)} dispositivo(s) USB:\n")
        
        for i, device in enumerate(dispositivos, 1):
            try:
                vendor_id = device.idVendor
                product_id = device.idProduct
                
                # Intentar obtener información del dispositivo
                try:
                    manufacturer = usb.util.get_string(device, device.iManufacturer)
                except:
                    manufacturer = "Desconocido"
                
                try:
                    product = usb.util.get_string(device, device.iProduct)
                except:
                    product = "Desconocido"
                
                print(f"Dispositivo {i}:")
                print(f"  Vendor ID:  0x{vendor_id:04x} ({vendor_id})")
                print(f"  Product ID: 0x{product_id:04x} ({product_id})")
                print(f"  Fabricante: {manufacturer}")
                print(f"  Producto:    {product}")
                print()
                
            except Exception as e:
                print(f"Error al leer dispositivo {i}: {str(e)}\n")
        
        print("=" * 60)
        print("INSTRUCCIONES:")
        print("=" * 60)
        print("1. Busca tu impresora Xprinter en la lista anterior")
        print("2. Anota los valores de Vendor ID y Product ID (en hexadecimal)")
        print("3. Si tu impresora no aparece, verifica que esté conectada y encendida")
        print("4. Si necesitas permisos, ejecuta este script con sudo:")
        print("   sudo python3 detectar_impresora.py")
        print()
        
    except Exception as e:
        print(f"Error al detectar dispositivos: {str(e)}")
        print("\nPosibles soluciones:")
        print("1. Ejecuta el script con permisos de administrador: sudo python3 detectar_impresora.py")
        print("2. Verifica que pyusb esté instalado: pip install pyusb")
        print("3. En Linux, puede ser necesario crear reglas udev (ver documentación)")

if __name__ == "__main__":
    detectar_dispositivos_usb()

