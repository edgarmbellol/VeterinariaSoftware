# Verificación de Configuración - Cajón Monedero 3BUMEN 405XD

## Puntos Importantes a Verificar:

### 1. **Posición de la Cerradura del Cajón**

El cajón monedero 3BUMEN 405XD tiene una cerradura con diferentes posiciones:

- **Cerrado permanentemente:** El cajón NO se abrirá ni manualmente ni mediante señal electrónica
- **Apertura manual:** El cajón solo se abre con la llave
- **Apertura automática:** El cajón se abre mediante señal electrónica de la impresora ⚠️ **DEBE ESTAR EN ESTA POSICIÓN**

**Verifica que la cerradura esté en la posición de "Apertura automática"**

### 2. **Manual de la Impresora Xprinter XP-58IIT**

Revisa el manual de la impresora para:
- Configuración de pines para el cajón monedero
- Comandos específicos soportados
- Configuración del puerto RJ11
- Posibles ajustes en el menú de la impresora

### 3. **Capturar el Comando de Eleventa**

Si Eleventa funciona, puedes intentar:
- Revisar los logs del software Eleventa
- Ver la configuración de impresora en Eleventa
- Usar herramientas de captura de tráfico USB (como Wireshark con filtro USB)
- Revisar archivos de configuración de Eleventa

### 4. **Comandos Más Probables Según Documentación**

Basado en la búsqueda, estos son los comandos más comunes:

```python
# Comando estándar más común
b'\x1B\x70\x00\x19\xFA'  # ESC p 0 25 250

# Variaciones comunes
b'\x1B\x70\x00\x32\xC8'  # ESC p 0 50 200
b'\x1B\x70\x00\x10\x10'  # ESC p 0 16 16 (el que ya probaste)
```

### 5. **Verificar Conexión Física**

- Cable RJ11 bien conectado en ambos extremos
- El cable debe estar en buen estado
- Verificar que el puerto RJ11 de la impresora esté funcionando

### 6. **Prueba con el Script Automático**

El script `probar_comandos_automatico.py` probará más de 200 comandos diferentes.
Ejecútalo y observa cuál funciona.

