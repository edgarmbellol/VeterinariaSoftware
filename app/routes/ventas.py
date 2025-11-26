from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Producto, Venta, ItemVenta, Categoria, Consulta, Animal, ItemConsulta
from decimal import Decimal
from datetime import datetime
import random
import string
import google.generativeai as genai
from sqlalchemy import func, or_
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO

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


@bp.route('/api/chat-ayuda', methods=['POST'])
@login_required
def chat_ayuda():
    try:
        data = request.get_json()
        mensaje = data.get('mensaje', '').strip()
        
        if not mensaje:
            return jsonify({'error': 'Mensaje requerido'}), 400
        
        # Configurar API de Gemini
        genai.configure(api_key='AIzaSyDUUf47aGZtGKVxI4Id-4FXkom8MyVB7OY')
        # Usar Gemini 2.5 Flash-Lite como solicitado
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        # Obtener productos disponibles en stock
        productos = Producto.query.filter(
            Producto.activo == True,
            Producto.stock > 0
        ).all()
        
        # Obtener categorías
        categorias = Categoria.query.filter_by(activa=True).all()
        
        # Preparar información de productos para el contexto
        productos_info = []
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
        
        categorias_info = [{'nombre': c.nombre, 'descripcion': c.descripcion or ''} for c in categorias]
        
        # Crear el prompt del sistema
        productos_texto = chr(10).join([f"- {p['nombre']} ({p['categoria']}): {p['descripcion']} - Precio: ${p['precio']:,.0f} - Stock: {p['stock']} unidades - Código: {p['codigo_barras']}" for p in productos_info])
        categorias_texto = chr(10).join([f"- {c['nombre']}: {c['descripcion']}" for c in categorias_info]) if categorias_info else "No hay categorías definidas"
        
        system_prompt = f"""Eres un vendedor experto y asesor en veterinaria. Tu trabajo es ayudar al vendedor a encontrar los mejores productos para los clientes que llegan a la tienda.

INFORMACIÓN DEL INVENTARIO DISPONIBLE:

CATEGORÍAS:
{categorias_texto}

PRODUCTOS EN STOCK:
{productos_texto if productos_texto else "No hay productos en stock actualmente"}

REGLAS CRÍTICAS Y OBLIGATORIAS:
1. Trabajas como vendedor y experto en veterinaria. Tu objetivo es ayudar a encontrar el mejor producto para cada necesidad del cliente.

2. ANÁLISIS ESTRICTO DE PRODUCTOS:
   - SOLO recomienda un producto si REALMENTE coincide con la necesidad del cliente según su nombre, descripción y categoría
   - NUNCA inventes información sobre un producto. Si un producto no tiene descripción o no está claro qué es, NO lo recomiendes
   - Si un producto se llama "Prueba" o tiene un nombre genérico sin descripción, NO lo recomiendes como si fuera un producto específico
   - NO asumas que un producto es algo que no es solo porque está en el inventario

3. BÚSQUEDA INTELIGENTE:
   - Analiza la consulta del cliente y busca productos que REALMENTE coincidan
   - Busca por nombre, descripción y categoría
   - Si un producto no tiene descripción clara o es genérico, NO lo recomiendes

4. SI HAY PRODUCTOS ADECUADOS:
   - Sugiere SOLO los productos que realmente coincidan con la necesidad
   - Menciona nombre exacto, código de barras, precio y stock
   - Explica por qué ese producto es adecuado basándote en la información REAL del inventario

5. SI NO HAY PRODUCTOS ADECUADOS EN EL INVENTARIO:
   - Di CLARAMENTE: "No tenemos productos específicos para [necesidad] en nuestro inventario actual"
   - NO inventes productos ni recomiendes productos que no son adecuados
   - Recomienda específicamente qué producto deberían pedir al proveedor (marca, tipo, características)

6. SI HAY PRODUCTOS PARCIALMENTE RELACIONADOS:
   - Menciona que no hay productos exactos pero hay alternativas relacionadas
   - Explica las limitaciones de las alternativas
   - Sugiere qué producto específico deberían pedir

7. NUNCA:
   - Inventes información sobre productos
   - Recomiendes productos genéricos o de prueba como si fueran productos específicos
   - Asumas que un producto es algo que no es

8. SIEMPRE:
   - Sé honesto si no hay productos adecuados
   - Incluye códigos de barras cuando menciones productos del inventario
   - Proporciona información útil basada SOLO en datos reales

Responde de forma clara, honesta y útil. Si no hay productos adecuados, dilo claramente y recomienda qué pedir al proveedor."""

        # Generar respuesta
        response = model.generate_content(
            f"{system_prompt}\n\nConsulta del cliente: {mensaje}\n\nResponde como vendedor experto en veterinaria:"
        )
        
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
    
    # Título
    elements.append(Paragraph("FACTURA DE VENTA", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Información de la empresa
    elements.append(Paragraph("<b>VETERINARIA</b>", styles['Heading2']))
    elements.append(Paragraph("Sistema de Gestión de Ventas", styles['Normal']))
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
    elements.append(Paragraph("Sistema de Gestión Veterinaria", 
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

