from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.models import Producto, Categoria
from sqlalchemy import or_
import google.generativeai as genai
import json
import re

bp = Blueprint('asistente_ia', __name__, url_prefix='/asistente-ia')

@bp.route('/')
@login_required
def index():
    """Página principal del asistente IA"""
    return render_template('asistente_ia/index.html')


def clasificar_consulta(mensaje, model):
    """
    LLAMADA 1: Clasificar la consulta y extraer información relevante
    Retorna JSON con categoría, palabras clave, especie, tipo de consulta
    """
    # Obtener todas las categorías disponibles
    categorias = Categoria.query.filter_by(activa=True).all()
    categorias_texto = ", ".join([c.nombre for c in categorias]) if categorias else "Medicamentos, Alimentos, Accesorios"
    
    prompt_clasificacion = f"""Analiza esta consulta veterinaria y extrae información estructurada.

CATEGORÍAS DISPONIBLES: {categorias_texto}

CONSULTA DEL USUARIO: "{mensaje}"

Responde SOLO con un JSON en este formato exacto (sin texto adicional):
{{
  "tipo_consulta": "producto" o "veterinaria" o "mixta",
  "categoria": "nombre de categoría si busca productos, o null",
  "palabras_clave": ["palabra1", "palabra2"],
  "especie": "perro/gato/ave/etc o null",
  "necesita_productos": true o false
}}

REGLAS:
- tipo_consulta: "producto" si busca productos, "veterinaria" si es consulta médica, "mixta" si ambas
- categoria: nombre exacto de la categoría si busca productos (ej: "Medicamentos")
- palabras_clave: términos relevantes para buscar (ej: ["desparasitante", "antiparasitario"])
- especie: animal mencionado o null
- necesita_productos: true si necesita buscar en inventario

Ejemplos:
"¿Tienen desparasitante para gatos?" → {{"tipo_consulta": "producto", "categoria": "Medicamentos", "palabras_clave": ["desparasitante", "antiparasitario", "parásitos"], "especie": "gato", "necesita_productos": true}}
"¿Qué dosis de Drontal para un gato de 5kg?" → {{"tipo_consulta": "mixta", "categoria": "Medicamentos", "palabras_clave": ["drontal", "desparasitante"], "especie": "gato", "necesita_productos": true}}
"Mi perro vomita mucho" → {{"tipo_consulta": "veterinaria", "categoria": null, "palabras_clave": ["vomito", "gastritis", "digestivo"], "especie": "perro", "necesita_productos": false}}
"¿Qué vacunas necesita un cachorro?" → {{"tipo_consulta": "veterinaria", "categoria": null, "palabras_clave": ["vacuna", "cachorro", "preventivo"], "especie": "perro", "necesita_productos": false}}"""

    try:
        response = model.generate_content(prompt_clasificacion)
        respuesta_texto = response.text.strip()
        
        # Limpiar la respuesta (quitar markdown si existe)
        respuesta_texto = re.sub(r'```json\s*', '', respuesta_texto)
        respuesta_texto = re.sub(r'```\s*', '', respuesta_texto)
        respuesta_texto = respuesta_texto.strip()
        
        # Parsear JSON
        clasificacion = json.loads(respuesta_texto)
        return clasificacion
    except Exception as e:
        print(f"Error en clasificación: {e}")
        # Fallback: asumir que busca productos
        return {
            "tipo_consulta": "producto",
            "categoria": None,
            "palabras_clave": [],
            "especie": None,
            "necesita_productos": True
        }


def buscar_productos_filtrados(clasificacion):
    """
    Buscar productos en BD según la clasificación
    Búsqueda inteligente: primero por palabras clave, luego por categoría si no encuentra nada
    """
    productos = []
    
    # PASO 1: Buscar por palabras clave (más específico)
    palabras_clave = clasificacion.get('palabras_clave', [])
    if palabras_clave:
        query = Producto.query.filter(Producto.activo == True, Producto.stock > 0)
        
        # Crear filtros OR para buscar en nombre o descripción
        filtros = []
        for palabra in palabras_clave:
            filtros.append(Producto.nombre.ilike(f'%{palabra}%'))
            filtros.append(Producto.descripcion.ilike(f'%{palabra}%'))
        
        if filtros:
            query = query.filter(or_(*filtros))
            productos = query.limit(20).all()
    
    # PASO 2: Si no encontró nada por palabras clave, buscar por categoría
    if not productos and clasificacion.get('categoria'):
        categoria = Categoria.query.filter_by(nombre=clasificacion['categoria'], activa=True).first()
        if categoria:
            query = Producto.query.filter(
                Producto.activo == True, 
                Producto.stock > 0,
                Producto.categoria_id == categoria.id
            )
            productos = query.limit(20).all()
    
    # PASO 3: Si aún no encontró nada y hay palabras clave, buscar SIN filtro de categoría
    # (por si el producto no tiene categoría asignada)
    if not productos and palabras_clave:
        query = Producto.query.filter(Producto.activo == True, Producto.stock > 0)
        # Búsqueda más amplia con palabras relacionadas
        filtros_amplios = []
        for palabra in palabras_clave:
            # Buscar variaciones comunes
            filtros_amplios.append(Producto.nombre.ilike(f'%{palabra}%'))
            filtros_amplios.append(Producto.descripcion.ilike(f'%{palabra}%'))
            # Agregar sinónimos comunes
            if 'antiparasit' in palabra.lower() or 'desparasit' in palabra.lower():
                filtros_amplios.append(Producto.nombre.ilike('%parasit%'))
                filtros_amplios.append(Producto.descripcion.ilike('%parasit%'))
                filtros_amplios.append(Producto.nombre.ilike('%drontal%'))
                filtros_amplios.append(Producto.nombre.ilike('%vermifugo%'))
        
        if filtros_amplios:
            query = query.filter(or_(*filtros_amplios))
            productos = query.limit(20).all()
    
    return productos


@bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """API para el chat con el asistente IA - Sistema de 2 llamadas inteligentes"""
    try:
        data = request.get_json()
        mensaje = data.get('mensaje', '').strip()
        historial = data.get('historial', [])  # Recibir historial de conversación
        
        if not mensaje:
            return jsonify({'error': 'Mensaje requerido'}), 400
        
        # Configurar API de Gemini
        genai.configure(api_key='AIzaSyDUUf47aGZtGKVxI4Id-4FXkom8MyVB7OY')
        # Usar Gemini 2.5 Flash-Lite
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # ============================================
        # LLAMADA 1: Clasificar la consulta
        # ============================================
        clasificacion = clasificar_consulta(mensaje, model)
        print(f"Clasificación: {clasificacion}")  # Debug
        
        # ============================================
        # LLAMADA 2: Buscar productos si es necesario
        # ============================================
        productos_info = []
        productos_texto = ""
        
        if clasificacion.get('necesita_productos', False):
            # Buscar productos filtrados según la clasificación
            productos = buscar_productos_filtrados(clasificacion)
            
            # Preparar información de productos
            for p in productos:
                categoria_nombre = p.categoria_rel.nombre if p.categoria_rel else 'Sin categoría'
                productos_info.append({
                    'nombre': p.nombre,
                    'descripcion': p.descripcion or '',
                    'precio': float(p.precio_venta),
                    'stock': p.stock,
                    'categoria': categoria_nombre,
                    'codigo_barras': p.codigo_barras
                })
            
            if productos_info:
                productos_texto = chr(10).join([
                    f"- {p['nombre']} ({p['categoria']}): {p['descripcion']} - Precio: ${p['precio']:,.0f} - Stock: {p['stock']} unidades - Código: {p['codigo_barras']}" 
                    for p in productos_info
                ])
            else:
                productos_texto = "No se encontraron productos que coincidan con la búsqueda."
        
        # ============================================
        # LLAMADA 3: Generar respuesta final
        # ============================================
        
        # Información del contexto de clasificación
        info_clasificacion = f"""
INFORMACIÓN DE LA CONSULTA:
- Tipo: {clasificacion.get('tipo_consulta', 'general')}
- Especie: {clasificacion.get('especie', 'no especificada')}
- Categoría de productos: {clasificacion.get('categoria', 'ninguna')}
"""

        system_prompt = f"""Eres un VETERINARIO PROFESIONAL amable y experto. Eres un asistente veterinario COMPLETO que ayuda con TODO tipo de consultas veterinarias.

{info_clasificacion}

PRODUCTOS RELEVANTES ENCONTRADOS:
{productos_texto if productos_texto else "No se buscaron productos para esta consulta."}

TUS CAPACIDADES COMO ASISTENTE VETERINARIO:

1. DIAGNÓSTICO Y SÍNTOMAS:
   - Analiza síntomas que describan
   - Identifica posibles enfermedades o condiciones
   - Explica qué podría estar pasando
   - Orienta sobre gravedad y urgencia
   - Ejemplo: "Esos síntomas podrían indicar [condición]. Te recomiendo [acción]."

2. TRATAMIENTOS Y PROTOCOLOS:
   - Explica tratamientos veterinarios
   - Describe procedimientos médicos
   - Orienta sobre cuidados post-operatorios
   - Da instrucciones de administración de medicamentos
   - Explica cómo hacer curaciones, vendajes, etc.

3. DOSIS Y MEDICAMENTOS:
   - Proporciona dosis específicas según especie y peso
   - Explica para qué sirve cada medicamento
   - Indica frecuencia, vía de administración y duración
   - Menciona efectos secundarios importantes
   - Ejemplo: "Claro! Para un gato de 5kg: 1 tableta cada 12 horas por 7 días, vía oral."

4. NUTRICIÓN Y ALIMENTACIÓN:
   - Recomienda dietas según edad, especie y condición
   - Explica porciones y frecuencia de alimentación
   - Orienta sobre alimentos prohibidos
   - Da consejos nutricionales específicos

5. CUIDADOS PREVENTIVOS:
   - Explica calendarios de vacunación
   - Orienta sobre desparasitación preventiva
   - Da consejos de higiene y cuidado dental
   - Recomienda chequeos y exámenes rutinarios

6. COMPORTAMIENTO ANIMAL:
   - Explica comportamientos normales y anormales
   - Da consejos de entrenamiento básico
   - Orienta sobre problemas de conducta
   - Ayuda con adaptación de nuevas mascotas

7. PRIMEROS AUXILIOS:
   - Explica qué hacer en emergencias
   - Da instrucciones de primeros auxilios
   - Orienta sobre heridas, fracturas, intoxicaciones
   - Indica cuándo es urgente ir al veterinario

8. REPRODUCCIÓN Y GESTACIÓN:
   - Explica cuidados durante embarazo
   - Orienta sobre parto y lactancia
   - Da consejos sobre esterilización
   - Responde dudas sobre cría responsable

9. ENFERMEDADES COMUNES:
   - Explica enfermedades frecuentes por especie
   - Describe síntomas característicos
   - Orienta sobre prevención y tratamiento
   - Aclara dudas sobre contagios

10. PRODUCTOS DEL INVENTARIO (cuando pregunten):
    - Recomienda productos disponibles según necesidad
    - Menciona precio y stock
    - Sugiere alternativas si no hay disponibilidad

CÓMO RESPONDER:
✓ SÉ AMABLE Y CERCANO (usa "Claro!", "Por supuesto", "Con gusto", "¡Perfecto!")
✓ RESPONDE DE FORMA CONVERSACIONAL pero profesional
✓ Usa emojis ocasionalmente (😊, 👍, ✨, 🐱, 🐶, 🩺, 💊)
✓ SÉ CLARO Y ÚTIL (máximo 7-8 líneas para respuestas complejas)
✓ Muestra EMPATÍA, especialmente si la mascota está enferma
✓ Da información PRÁCTICA y ACCIONABLE
✓ Si es EMERGENCIA grave: "⚠️ Es urgente que acudas al veterinario inmediatamente"
✓ Para consultas de inventario: menciona productos disponibles con precio y stock
✓ NO inventes productos que no están en el inventario

EJEMPLOS DE RESPUESTAS:

Síntomas: "Por los síntomas que describes, podría ser [condición]. Te recomiendo [acción]. Si empeora, acude al veterinario. 🩺"

Cuidados: "Para cuidar la herida: limpia con suero fisiológico 2 veces al día, aplica [medicamento], y mantén el área seca. Debería sanar en 5-7 días. 👍"

Alimentación: "Para un cachorro de esa edad, te recomiendo 3 comidas al día con alimento para cachorros. Porción: 1 taza por comida. 🐶"

Comportamiento: "Ese comportamiento es normal en gatos cuando [explicación]. Puedes ayudarlo con [consejo]. 🐱"

Responde como un veterinario experto, amable y accesible que realmente se preocupa por el bienestar de los animales."""

        # Construir el contexto de la conversación
        contexto_conversacion = ""
        if historial and len(historial) > 0:
            # Incluir las últimas 6 interacciones (3 pares de pregunta-respuesta)
            historial_reciente = historial[-6:] if len(historial) > 6 else historial
            contexto_conversacion = "\n\nCONTEXTO DE LA CONVERSACIÓN PREVIA:\n"
            for item in historial_reciente:
                if item.get('tipo') == 'usuario':
                    contexto_conversacion += f"Usuario: {item.get('texto', '')}\n"
                elif item.get('tipo') == 'asistente':
                    contexto_conversacion += f"Asistente: {item.get('texto', '')}\n"
            contexto_conversacion += "\n"

        # Generar respuesta con contexto
        prompt_completo = f"{system_prompt}{contexto_conversacion}PREGUNTA ACTUAL: {mensaje}\n\nRespuesta breve y directa (considera el contexto previo si es relevante):"
        
        response = model.generate_content(prompt_completo)
        
        respuesta = response.text if response.text else "Lo siento, no pude generar una respuesta. Por favor intenta de nuevo."
        
        return jsonify({
            'respuesta': respuesta,
            'productos_sugeridos': productos_info
        })
    
    except Exception as e:
        print(f"Error en chat: {str(e)}")
        return jsonify({'error': f'Error al procesar la consulta: {str(e)}'}), 500

