# Instrucciones para Configurar la Impresora Térmica

## Requisitos Previos

1. **Instalar las dependencias:**
   ```bash
   source venv/bin/activate  # Activar el entorno virtual
   pip install -r requirements.txt
   ```

2. **Permisos USB en Linux (Ubuntu/Lubuntu):**

   Para acceder a dispositivos USB sin usar `sudo`, necesitas crear una regla udev:
   
   ```bash
   # Crear el archivo de reglas
   sudo nano /etc/udev/rules.d/99-impresora-termica.rules
   ```
   
   Agrega esta línea (reemplaza VENDOR_ID y PRODUCT_ID con los de tu impresora):
   ```
   SUBSYSTEM=="usb", ATTRS{idVendor}=="VENDOR_ID", ATTRS{idProduct}=="PRODUCT_ID", MODE="0666", GROUP="plugdev"
   ```
   
   Ejemplo:
   ```
   SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5743", MODE="0666", GROUP="plugdev"
   ```
   
   Luego recarga las reglas:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```
   
   **Nota:** Asegúrate de que tu usuario esté en el grupo `plugdev`:
   ```bash
   sudo usermod -a -G plugdev $USER
   ```
   (Necesitarás cerrar sesión y volver a iniciar sesión para que tome efecto)

## Detectar los IDs de tu Impresora

1. **Conecta la impresora por USB y enciéndela**

2. **Ejecuta el script de detección:**
   ```bash
   python3 detectar_impresora.py
   ```
   
   Si no tienes permisos, ejecuta con sudo:
   ```bash
   sudo python3 detectar_impresora.py
   ```

3. **Busca tu impresora Xprinter en la lista** y anota:
   - Vendor ID (en hexadecimal, ej: 0x0483)
   - Product ID (en hexadecimal, ej: 0x5743)

4. **Si tu impresora no aparece en la lista automática**, puedes agregar manualmente los IDs en `app/routes/ventas.py` en la función `detectar_impresora_usb()`, en la lista `impresoras_xprinter`.

## Uso

Una vez configurado, puedes imprimir tickets desde:

1. **Después de realizar una venta:** Aparecerá un botón "Imprimir Ticket" en el modal de éxito
2. **Desde el historial de ventas (Admin):** Haz clic en el ícono de ticket (📄) junto a cada venta

## Solución de Problemas

### Error: "No se pudo detectar la impresora"

1. Verifica que la impresora esté conectada y encendida
2. Verifica los permisos USB (ver sección de permisos arriba)
3. Ejecuta el script de detección para verificar que la impresora aparezca
4. Si los IDs no coinciden, agrégalos manualmente en el código

### Error: "Permission denied" o "Access denied"

- Necesitas configurar los permisos USB (ver sección de permisos)
- O ejecuta la aplicación con `sudo` (no recomendado para producción)

### La impresora imprime pero el formato está mal

- Ajusta el ancho del ticket en `app/routes/ventas.py` en la función `imprimir_ticket()`
- La Xprinter XP-58IIT es de 80mm, pero el código está configurado para 32 caracteres de ancho
- Puedes ajustar el número de caracteres según necesites

### Personalizar el nombre del negocio

Edita la variable `nombre_negocio` en la función `imprimir_ticket()` en `app/routes/ventas.py`:
```python
nombre_negocio = "TU NOMBRE DE NEGOCIO"
```

## Notas Importantes

- La caja monedero 3bumem funciona independientemente de la impresora
- La impresora solo imprime el ticket, no controla la caja
- En producción, asegúrate de tener los permisos USB configurados correctamente
- Si cambias de puerto USB, puede que necesites reconfigurar los permisos

