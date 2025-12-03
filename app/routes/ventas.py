from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Producto, Venta, ItemVenta, Categoria, Consulta, Animal, ItemConsulta, ConfiguracionNegocio
from decimal import Decimal
from datetime import datetime
import random
import string
import time
import google.generativeai as genai
from sqlalchemy import func, or_
import json
import re
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
import os

# Imports opcionales para impresora térmica
try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False

bp = Blueprint('ventas', __name__, url_prefix='/ventas')


def generar_numero_venta():
    fecha = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'VTA-{fecha}-{random_str}'


@bp.route('/')
@login_required
def nueva_venta():
    return render_template('ventas/nueva_venta.html')


@bp.route('/procesar', methods=['POST'])
@login_required
def procesar_venta():
    try:
        data = request.get_json()
        items = data.get('items', [])
        metodo_pago = data.get('metodo_pago')
        notas = data.get('notas', '')
        
        if not items:
            return jsonify({'error': 'No hay items en la venta'}), 400
        
        if not metodo_pago:
            return jsonify({'error': 'Método de pago requerido'}), 400
        
        # Crear venta
        numero_venta = generar_numero_venta()
        total = Decimal('0.00')
        
        venta = Venta(
            numero_venta=numero_venta,
            total=Decimal('0.00'),
            metodo_pago=metodo_pago,
            notas=notas,
            usuario_id=current_user.id
        )
        db.session.add(venta)
        db.session.flush()
        
        # Crear items de venta
        for item_data in items:
            producto = Producto.query.get(item_data['producto_id'])
            if not producto:
                continue
            
            cantidad = int(item_data['cantidad'])
            precio_unitario = Decimal(str(item_data['precio_unitario']))
            subtotal = precio_unitario * cantidad
            
            # Verificar stock
            if producto.stock < cantidad:
                db.session.rollback()
                return jsonify({'error': f'Stock insuficiente para {producto.nombre}'}), 400
            
            # Actualizar stock
            producto.stock -= cantidad
            
            item_venta = ItemVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            db.session.add(item_venta)
            total += subtotal
        
        venta.total = total
        db.session.commit()
        
        return jsonify({
            'success': True,
            'venta_id': venta.id,
            'numero_venta': venta.numero_venta,
            'total': float(total)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/buscar-producto', methods=['GET'])
@login_required
def buscar_producto():
    codigo = request.args.get('codigo', '').strip()
    if not codigo:
        return jsonify({'error': 'Código requerido'}), 400
    
    producto = Producto.query.filter_by(codigo_barras=codigo, activo=True).first()
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    if producto.stock <= 0:
        return jsonify({'error': 'Producto sin stock disponible'}), 400
    
    return jsonify(producto.to_dict())


@bp.route('/api/buscar-producto-nombre', methods=['GET'])
@login_required
def buscar_producto_nombre():
    nombre = request.args.get('nombre', '').strip()
    if not nombre or len(nombre) < 2:
        return jsonify([])
    
    # Búsqueda por nombre (case insensitive, parcial) - compatible con SQLite
    productos = Producto.query.filter(
        func.lower(Producto.nombre).like(f'%{nombre.lower()}%'),
        Producto.activo == True,
        Producto.stock > 0
    ).limit(20).all()
    
    return jsonify([p.to_dict() for p in productos])


@bp.route('/api/buscar-consulta', methods=['GET'])
@login_required
def buscar_consulta():
    """Buscar consultas por animal o número de consulta"""
    busqueda = request.args.get('q', '').strip()
    if not busqueda or len(busqueda) < 2:
        return jsonify([])
    
    # Buscar por nombre del animal o ID de consulta
    filtros = [
        Animal.nombre.ilike(f'%{busqueda}%'),
        Animal.nombre_dueno.ilike(f'%{busqueda}%')
    ]
    
    # Si la búsqueda es un número, buscar por ID de consulta
    if busqueda.isdigit():
        filtros.append(Consulta.id == int(busqueda))
    
    consultas = Consulta.query.join(Animal).filter(
        or_(*filtros),
        Consulta.venta_id.is_(None)  # Solo consultas sin venta asociada
    ).order_by(Consulta.fecha_consulta.desc()).limit(20).all()
    
    resultado = []
    for consulta in consultas:
        if consulta.items:  # Solo incluir consultas con medicamentos
            resultado.append({
                'id': consulta.id,
                'fecha': consulta.fecha_consulta.strftime('%d/%m/%Y %H:%M'),
                'animal_nombre': consulta.animal.nombre,
                'animal_dueno': consulta.animal.nombre_dueno,
                'motivo': consulta.motivo[:50] + '...' if len(consulta.motivo) > 50 else consulta.motivo,
                'total_medicamentos': len(consulta.items),
                'items': [item.to_dict() for item in consulta.items]
            })
    
    return jsonify(resultado)


def clasificar_consulta_ventas(mensaje, model):
    """
    LLAMADA 1: Clasificar la consulta y extraer información relevante
    """
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
- categoria: nombre exacto de la categoría si busca productos
- palabras_clave: términos relevantes para buscar
- especie: animal mencionado o null
- necesita_productos: true si necesita buscar en inventario"""

    try:
        response = model.generate_content(prompt_clasificacion)
        respuesta_texto = response.text.strip()
        respuesta_texto = re.sub(r'```json\s*', '', respuesta_texto)
        respuesta_texto = re.sub(r'```\s*', '', respuesta_texto)
        respuesta_texto = respuesta_texto.strip()
        clasificacion = json.loads(respuesta_texto)
        return clasificacion
    except Exception as e:
        print(f"Error en clasificación: {e}")
        return {
            "tipo_consulta": "producto",
            "categoria": None,
            "palabras_clave": [],
            "especie": None,
            "necesita_productos": True
        }


def buscar_productos_filtrados_ventas(clasificacion):
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


@bp.route('/api/chat-ayuda', methods=['POST'])
@login_required
def chat_ayuda():
    try:
        data = request.get_json()
        mensaje = data.get('mensaje', '').strip()
        historial = data.get('historial', [])  # Recibir historial de conversación
        
        if not mensaje:
            return jsonify({'error': 'Mensaje requerido'}), 400
        
        # Configurar API de Gemini
        genai.configure(api_key='AIzaSyDUUf47aGZtGKVxI4Id-4FXkom8MyVB7OY')
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # LLAMADA 1: Clasificar la consulta
        clasificacion = clasificar_consulta_ventas(mensaje, model)
        print(f"Clasificación: {clasificacion}")  # Debug
        
        # LLAMADA 2: Buscar productos si es necesario
        productos_info = []
        productos_texto = ""
        
        if clasificacion.get('necesita_productos', False):
            productos = buscar_productos_filtrados_ventas(clasificacion)
            
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
        
        # LLAMADA 3: Generar respuesta final
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
            'productos_sugeridos': productos_info  # Enviar productos para referencia
        })
    
    except Exception as e:
        print(f"Error en chat: {str(e)}")
        return jsonify({'error': f'Error al procesar la consulta: {str(e)}'}), 500


@bp.route('/pdf/<int:venta_id>')
@login_required
def generar_pdf(venta_id):
    """Generar PDF de factura para una venta"""
    venta = Venta.query.get_or_404(venta_id)
    config = ConfiguracionNegocio.obtener_configuracion()
    
    # Crear buffer para el PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    # Contenedor para los elementos del PDF
    elements = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12
    )
    
    # Logo e información de la empresa
    empresa_data = []
    
    # Logo si existe
    if config and config.logo_path:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', config.logo_path)
        if os.path.exists(logo_path):
            try:
                logo_img = ReportLabImage(logo_path, width=2*inch, height=1*inch)
                logo_img.hAlign = 'CENTER'
                elements.append(logo_img)
                elements.append(Spacer(1, 0.2*inch))
            except:
                pass
    
    # Título
    elements.append(Paragraph("FACTURA DE VENTA", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Información de la empresa
    nombre_negocio = config.nombre_negocio if config and config.nombre_negocio else "VETERINARIA"
    elements.append(Paragraph(f"<b>{nombre_negocio.upper()}</b>", styles['Heading2']))
    
    # Información adicional del negocio
    info_negocio = []
    if config:
        if config.nit:
            info_negocio.append(f"NIT: {config.nit}")
        if config.direccion:
            info_negocio.append(config.direccion)
        if config.telefono:
            info_negocio.append(f"Tel: {config.telefono}")
        if config.correo:
            info_negocio.append(f"Email: {config.correo}")
    
    if info_negocio:
        for info in info_negocio:
            elements.append(Paragraph(info, styles['Normal']))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Información de la venta
    data_venta = [
        ['Número de Venta:', venta.numero_venta],
        ['Fecha:', venta.fecha_venta.strftime('%d/%m/%Y %H:%M')],
        ['Método de Pago:', venta.metodo_pago.upper()],
        ['Vendedor:', venta.usuario.username if venta.usuario else 'N/A'],
    ]
    
    # Si la venta viene de una consulta, agregar información del animal
    consulta = Consulta.query.filter_by(venta_id=venta_id).first()
    if consulta and consulta.animal:
        animal = consulta.animal
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph("<b>INFORMACIÓN DEL PACIENTE</b>", heading_style))
        data_animal = [
            ['Nombre del Animal:', animal.nombre],
            ['Especie:', animal.especie],
            ['Raza:', animal.raza or 'No especificada'],
            ['Edad:', animal.get_edad_display()],
            ['Dueño:', animal.nombre_dueno],
            ['Contacto:', animal.telefono_dueno or 'No registrado'],
        ]
        table_animal = Table(data_animal, colWidths=[2.5*inch, 3.5*inch])
        table_animal.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(table_animal)
        elements.append(Spacer(1, 0.2*inch))
    
    # Tabla de información de venta
    table_venta = Table(data_venta, colWidths=[2.5*inch, 3.5*inch])
    table_venta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    elements.append(table_venta)
    elements.append(Spacer(1, 0.3*inch))
    
    # Tabla de productos
    elements.append(Paragraph("<b>DETALLE DE PRODUCTOS</b>", heading_style))
    
    data_productos = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    for item in venta.items:
        data_productos.append([
            item.producto.nombre,
            str(item.cantidad),
            f"${item.precio_unitario:,.0f}",
            f"${item.subtotal:,.0f}"
        ])
    
    # Agregar total
    data_productos.append(['TOTAL', '', '', f"${venta.total:,.0f}"])
    
    table_productos = Table(data_productos, colWidths=[3.5*inch, 1*inch, 1.25*inch, 1.25*inch])
    table_productos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-2, -2), colors.white),
        ('TEXTCOLOR', (0, 1), (-2, -2), colors.black),
        ('FONTNAME', (0, 1), (-2, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-2, -2), 10),
        ('GRID', (0, 0), (-1, -2), 1, colors.grey),
        ('LINEBELOW', (0, -2), (-1, -2), 2, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('TOPPADDING', (0, -1), (-1, -1), 12),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ]))
    elements.append(table_productos)
    elements.append(Spacer(1, 0.3*inch))
    
    # Notas si existen
    if venta.notas:
        elements.append(Paragraph("<b>NOTAS:</b>", styles['Heading3']))
        elements.append(Paragraph(venta.notas, styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Pie de página
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Gracias por su compra", styles['Normal']))
    footer_text = nombre_negocio
    if config and config.telefono:
        footer_text += f" | Tel: {config.telefono}"
    elements.append(Paragraph(footer_text, 
                             ParagraphStyle('Footer', parent=styles['Normal'], 
                                           fontSize=8, textColor=colors.grey, 
                                           alignment=TA_CENTER)))
    
    # Construir PDF
    doc.build(elements)
    
    # Obtener el valor del buffer
    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()
    
    # Crear respuesta para descarga
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=factura_{venta.numero_venta}.pdf'
    
    return response


def detectar_impresora_usb():
    """
    Detecta la impresora térmica Xprinter XP-58IIT conectada por USB.
    Retorna el objeto de la impresora o None si no se encuentra.
    """
    if not USB_AVAILABLE:
        return None
    
    try:
        from escpos.printer import Usb
        
        # IDs comunes de impresoras Xprinter (pueden variar)
        # Xprinter XP-58IIT comúnmente usa estos IDs
        # Puedes agregar más IDs si conoces el de tu impresora específica
        impresoras_xprinter = [
            (0x0483, 0x070b),  # Xprinter XP-58IIT detectada (1155, 1803 en decimal)
            (1155, 1803),       # Xprinter XP-58IIT (IDs en decimal)
            (0x0483, 0x5743),  # Otra variante Xprinter común
            (0x04e8, 0x0202),  # Samsung (algunas Xprinter usan este)
            (0x04b8, 0x0202),  # Epson (compatible ESC/POS)
            (0x0483, 0x5840),  # Otra variante Xprinter
        ]
        
        # Intentar encontrar la impresora con IDs conocidos
        for vendor_id, product_id in impresoras_xprinter:
            # Primero intentar sin especificar endpoints (auto-detección)
            try:
                printer = Usb(vendor_id, product_id, timeout=0)
                # Verificar que la impresora responde (intento silencioso)
                return printer
            except Exception as e:
                # Si falla, intentar con diferentes combinaciones de endpoints
                endpoints_configs = [
                    (0x81, 0x03),  # Endpoints comunes
                    (0x82, 0x01),  # Alternativa 1
                    (0x83, 0x02),  # Alternativa 2
                    (0x81, 0x01),  # Alternativa 3
                    (0x82, 0x03),  # Alternativa 4
                ]
                
                for in_ep, out_ep in endpoints_configs:
                    try:
                        printer = Usb(vendor_id, product_id, timeout=0, in_ep=in_ep, out_ep=out_ep)
                        return printer
                    except Exception as e:
                        continue
        
        # Si no se encuentra con IDs conocidos, intentar buscar todas las impresoras USB
        # que sean compatibles con ESC/POS
        try:
            if not USB_AVAILABLE:
                return None
            devices = usb.core.find(find_all=True)
            for device in devices:
                # Primero intentar sin especificar endpoints (auto-detección)
                try:
                    printer = Usb(device.idVendor, device.idProduct, timeout=0)
                    return printer
                except:
                    # Si falla, intentar con endpoints comunes
                    try:
                        printer = Usb(device.idVendor, device.idProduct, timeout=0, in_ep=0x81, out_ep=0x03)
                        return printer
                    except:
                        continue
        except Exception:
            pass
        
        return None
    except ImportError as e:
        print(f"Error: python-escpos no está instalado: {str(e)}")
        return None
    except Exception as e:
        print(f"Error al detectar impresora: {str(e)}")
        return None


@bp.route('/imprimir-ticket/<int:venta_id>')
@login_required
def imprimir_ticket(venta_id):
    """Imprimir ticket de venta en impresora térmica"""
    try:
        venta = Venta.query.get_or_404(venta_id)
        
        # Detectar impresora
        try:
            printer = detectar_impresora_usb()
        except Exception as e:
            import traceback
            print(f"Error al detectar impresora: {traceback.format_exc()}")
            return jsonify({
                'success': False,
                'error': f'Error al detectar impresora: {str(e)}'
            }), 500
        
        if not printer:
            return jsonify({
                'success': False,
                'error': 'No se pudo detectar la impresora. Verifica que esté conectada por USB y que tengas los permisos necesarios.'
            }), 400
        
        # Obtener configuración del negocio
        config = ConfiguracionNegocio.obtener_configuracion()
        nombre_negocio = config.nombre_negocio.upper() if config and config.nombre_negocio else "VETERINARIA"
        
        try:
            # IMPORTANTE: Abrir cajón ANTES de imprimir (como en Eleventa punto de ventas)
            # Según el manual de programación 58XX Program Manual V6.3:
            # Comando: ESC p m t1 t2
            # - m = 0, 1, 48, o 49 (pin del cajón)
            # - t1 = 0-255 (tiempo ON en unidades de 2ms)
            # - t2 = 0-255 (tiempo OFF en unidades de 2ms)
            # - Tiempo ON = t1 × 2ms, Tiempo OFF = t2 × 2ms
            
            # IMPORTANTE: Enviar comandos del cajón ANTES de cualquier otra operación
            # Según el manual ESC/POS (serie 80XX):
            # Comando: ESC p m t1 t2
            # - m = 0 (pin 2 del conector de expulsión del cajón)
            # - t1 = tiempo ON en unidades de 2ms (t1 × 2ms = tiempo ON)
            # - t2 = tiempo OFF en unidades de 2ms (t2 × 2ms = tiempo OFF)
            # 
            # Comando recomendado según manual: ESC p 0 50 50
            # - t1 = 50 → 50 × 2ms = 100ms ON
            # - t2 = 50 → 50 × 2ms = 100ms OFF
            # Secuencia: \x1B\x70\x00\x32\x32
            
            # Inicializar impresora primero (importante para algunos modelos)
            try:
                if hasattr(printer, 'device') and printer.device:
                    printer._raw(b'\x1B\x40')  # ESC @ - Inicializar impresora
                    time.sleep(0.1)
            except:
                pass
            
            # COMANDO PRINCIPAL según el manual (100ms ON, 100ms OFF)
            comando_principal = b'\x1B\x70\x00\x32\x32'  # ESC p 0 50 50
            
            # COMANDO ALTERNATIVO (32ms ON, 32ms OFF) - para cajones más sensibles
            comando_alternativo = b'\x1B\x70\x00\x10\x10'  # ESC p 0 16 16
            
            # Enviar el comando principal primero (el más común según el manual)
            try:
                if hasattr(printer, 'device') and printer.device:
                    printer._raw(comando_principal)
                    time.sleep(0.2)  # Pausa para dar tiempo al cajón
            except Exception as e:
                print(f"Error al enviar comando principal del cajón: {e}")
            
            # Si el principal no funciona, probar el alternativo
            try:
                if hasattr(printer, 'device') and printer.device:
                    printer._raw(comando_alternativo)
                    time.sleep(0.2)
            except Exception as e:
                print(f"Error al enviar comando alternativo del cajón: {e}")
            
            # También probar con pin 1 (por si acaso)
            try:
                if hasattr(printer, 'device') and printer.device:
                    printer._raw(b'\x1B\x70\x01\x32\x32')  # ESC p 1 50 50
                    time.sleep(0.2)
            except:
                pass
            
            # Probar cashdraw() como respaldo (pin 2 es el estándar según el manual)
            try:
                if hasattr(printer, 'device') and printer.device:
                    printer.cashdraw(2)  # Pin 2 según el manual
                    time.sleep(0.2)
            except:
                pass
            
            # Verificar que la conexión siga activa antes de imprimir
            if not (hasattr(printer, 'device') and printer.device):
                # Recrear la conexión
                try:
                    printer.close()
                except:
                    pass
                printer = detectar_impresora_usb()
                if not printer:
                    raise Exception("No se pudo mantener la conexión con la impresora")
            
            # Inicializar impresora (reset básico) DESPUÉS de los comandos del cajón
            try:
                if hasattr(printer, 'device') and printer.device:
                    printer._raw(b'\x1B\x40')  # ESC @ - Inicializar impresora
                    time.sleep(0.05)
            except:
                pass
            
            # Configurar impresora (centrado, tamaño de fuente)
            printer.set(align='center', font='a', width=1, height=1)
            
            # Logo si existe (para impresoras térmicas)
            if config and config.logo_path:
                logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', config.logo_path)
                if os.path.exists(logo_path):
                    try:
                        from PIL import Image as PILImage
                        # Cargar y redimensionar imagen para impresora térmica (máximo 384px de ancho para 80mm)
                        img = PILImage.open(logo_path)
                        # Convertir a escala de grises si es necesario
                        if img.mode != '1':  # Modo 1 es bitmap (blanco y negro)
                            img = img.convert('L')  # Escala de grises
                            # Convertir a bitmap (umbral)
                            threshold = 128
                            img = img.point(lambda x: 0 if x < threshold else 255, '1')
                        
                        # Redimensionar manteniendo proporción (máximo 384px de ancho)
                        max_width = 384
                        if img.width > max_width:
                            ratio = max_width / img.width
                            new_height = int(img.height * ratio)
                            # Usar LANCZOS si está disponible, sino usar NEAREST
                            try:
                                img = img.resize((max_width, new_height), PILImage.Resampling.LANCZOS)
                            except AttributeError:
                                # Fallback para versiones antiguas de PIL
                                img = img.resize((max_width, new_height), PILImage.LANCZOS)
                        
                        # Imprimir logo centrado
                        printer.set(align='center')
                        printer.image(img)
                        printer.text("\n")
                    except ImportError:
                        print("PIL/Pillow no disponible para imprimir logo")
                    except Exception as e:
                        print(f"Error al imprimir logo: {str(e)}")
                        # Continuar sin logo si hay error
            
            # Encabezado
            printer.text("\n")
            printer.set(align='center', font='b', width=2, height=2)
            printer.text(f"{nombre_negocio}\n")
            printer.set(align='center', font='a', width=1, height=1)
            
            # Información adicional del negocio
            if config:
                if config.nit:
                    printer.text(f"NIT: {config.nit}\n")
                if config.direccion:
                    # Dividir dirección si es muy larga
                    direccion = config.direccion
                    if len(direccion) > 32:
                        palabras = direccion.split()
                        linea = ""
                        for palabra in palabras:
                            if len(linea + palabra) <= 32:
                                linea += palabra + " "
                            else:
                                if linea:
                                    printer.text(f"{linea.strip()}\n")
                                linea = palabra + " "
                        if linea:
                            printer.text(f"{linea.strip()}\n")
                    else:
                        printer.text(f"{direccion}\n")
                if config.telefono:
                    printer.text(f"Tel: {config.telefono}\n")
                if config.correo:
                    printer.text(f"{config.correo}\n")
            
            printer.text("=" * 32 + "\n")
            printer.text("\n")
            
            # Información de la venta
            printer.set(align='left')
            printer.text(f"Venta: {venta.numero_venta}\n")
            printer.text(f"Fecha: {venta.fecha_venta.strftime('%d/%m/%Y %H:%M')}\n")
            printer.text(f"Vendedor: {venta.usuario.username if venta.usuario else 'N/A'}\n")
            printer.text(f"Pago: {venta.metodo_pago.upper()}\n")
            printer.text("-" * 32 + "\n")
            printer.text("\n")
            
            # Productos
            printer.set(align='center', font='b')
            printer.text("PRODUCTOS\n")
            printer.set(align='left', font='a')
            printer.text("-" * 32 + "\n")
            
            for item in venta.items:
                # Nombre del producto (puede ser largo, ajustar si es necesario)
                nombre_producto = item.producto.nombre[:28]  # Limitar a 28 caracteres
                if len(item.producto.nombre) > 28:
                    nombre_producto += "..."
                
                printer.text(f"{nombre_producto}\n")
                printer.text(f"  {item.cantidad} x ${float(item.precio_unitario):,.0f} = ${float(item.subtotal):,.0f}\n")
                printer.text("\n")
            
            printer.text("=" * 32 + "\n")
            
            # Total
            printer.set(align='right', font='b', width=2, height=2)
            printer.text(f"TOTAL: ${float(venta.total):,.0f}\n")
            printer.set(align='left', font='a', width=1, height=1)
            printer.text("\n")
            printer.text("=" * 32 + "\n")
            printer.text("\n")
            
            # Pie de página
            printer.set(align='center')
            printer.text("Gracias por su compra\n")
            if config and config.telefono:
                printer.text(f"{nombre_negocio}\n")
                printer.text(f"Tel: {config.telefono}\n")
            printer.text("\n")
            printer.text("\n")
            
            # Cortar el ticket
            printer.cut()
            
            # Cerrar conexión
            printer.close()
            
            return jsonify({
                'success': True,
                'message': 'Ticket impreso correctamente'
            })
            
        except Exception as e:
            try:
                printer.close()
            except:
                pass
            error_msg = str(e)
            # Log del error completo para debugging
            import traceback
            print(f"Error completo al imprimir ticket: {traceback.format_exc()}")
            # Mensaje más amigable para errores comunes
            if 'not found' in error_msg.lower() or 'device not found' in error_msg.lower():
                error_msg = 'Impresora no encontrada. Verifica que esté conectada y encendida. En Linux, puede necesitar permisos USB (ver INSTRUCCIONES_IMPRESORA.md)'
            elif 'permission' in error_msg.lower() or 'access denied' in error_msg.lower():
                error_msg = 'Sin permisos para acceder a la impresora. En Linux, configura reglas udev o ejecuta con sudo (ver INSTRUCCIONES_IMPRESORA.md)'
            return jsonify({
                'success': False,
                'error': f'Error al imprimir: {error_msg}'
            }), 500
            
    except Exception as e:
        import traceback
        print(f"Error en imprimir_ticket (nivel superior): {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500

