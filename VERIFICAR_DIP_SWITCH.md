# ⚠️ INFORMACIÓN CRÍTICA - DIP Switch SW-6

## Según el Manual de Xprinter XP-58IIT

El manual muestra que hay un **DIP Switch SW-6** que controla la apertura automática del cajón monedero:

### **SW-6: Cutter with cash drawer**
- **ON:** YES (Sí, permite apertura automática del cajón)
- **OFF:** NO (No, desactiva la apertura automática del cajón)

## ⚠️ ESTO ES MUY IMPORTANTE

**Si el DIP switch SW-6 está en posición OFF, el cajón NO se abrirá automáticamente,**
**incluso si envías el comando correcto.**

## Cómo Verificar y Cambiar el DIP Switch

1. **Localiza los DIP switches en la impresora:**
   - Generalmente están en la parte inferior o trasera de la impresora
   - Son pequeños interruptores numerados SW-1, SW-2, SW-3, etc.

2. **Verifica la posición de SW-6:**
   - Debe estar en posición **ON** para que el cajón se abra automáticamente
   - Si está en **OFF**, cámbialo a **ON**

3. **Después de cambiar el switch:**
   - Reinicia la impresora (apágala y vuelve a encenderla)
   - Prueba nuevamente la impresión del ticket

## Especificaciones del Cajón Monedero

Según la etiqueta de la impresora:
- **Cash Drawer Output:** 12V --- 1A
- El cajón 3BUMEN 405XD debe ser compatible con esta salida

## Comando Estándar

Según la documentación, el comando estándar ESC/POS es:
```
ESC p 0 25 250
En hexadecimal: 1B 70 00 19 FA
```

## Pasos a Seguir

1. ✅ **PRIMERO:** Verifica que el DIP switch SW-6 esté en posición **ON**
2. ✅ Verifica que la cerradura del cajón esté en posición de "Apertura automática"
3. ✅ Verifica que el cable RJ11 esté bien conectado
4. ✅ Reinicia la impresora después de cambiar el DIP switch
5. ✅ Prueba imprimir un ticket

Si después de verificar el DIP switch SW-6 el cajón aún no se abre, entonces podemos probar otros comandos o configuraciones.

