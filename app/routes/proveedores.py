from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Proveedor, Compra, ItemCompra, Producto
from sqlalchemy import func
from decimal import Decimal

bp = Blueprint('proveedores', __name__, url_prefix='/proveedores')


@bp.route('/')
@login_required
def listar():
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    # Agregar total_compras a cada proveedor para el template
    for proveedor in proveedores:
        proveedor.total_compras = len(proveedor.compras)
    return render_template('proveedores/listar.html', proveedores=proveedores)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            if not nombre:
                flash('El nombre del proveedor es requerido', 'error')
                return render_template('proveedores/crear.html')
            
            proveedor = Proveedor(
                nombre=nombre,
                telefono=request.form.get('telefono', '').strip() or None,
                correo_electronico=request.form.get('correo_electronico', '').strip() or None,
                notas=request.form.get('notas', '').strip() or None,
                activo=True
            )
            db.session.add(proveedor)
            db.session.commit()
            flash('Proveedor creado exitosamente', 'success')
            return redirect(url_for('proveedores.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear proveedor: {str(e)}', 'error')
    
    return render_template('proveedores/crear.html')


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    proveedor = Proveedor.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            if not nombre:
                flash('El nombre del proveedor es requerido', 'error')
                return render_template('proveedores/editar.html', proveedor=proveedor)
            
            proveedor.nombre = nombre
            proveedor.telefono = request.form.get('telefono', '').strip() or None
            proveedor.correo_electronico = request.form.get('correo_electronico', '').strip() or None
            proveedor.notas = request.form.get('notas', '').strip() or None
            
            db.session.commit()
            flash('Proveedor actualizado exitosamente', 'success')
            return redirect(url_for('proveedores.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar proveedor: {str(e)}', 'error')
    
    return render_template('proveedores/editar.html', proveedor=proveedor)


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    proveedor = Proveedor.query.get_or_404(id)
    try:
        proveedor.activo = False
        db.session.commit()
        flash('Proveedor desactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar proveedor: {str(e)}', 'error')
    
    return redirect(url_for('proveedores.listar'))


@bp.route('/api/listar', methods=['GET'])
@login_required
def listar_api():
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    return jsonify([p.to_dict() for p in proveedores])


@bp.route('/api/crear', methods=['POST'])
@login_required
def crear_api():
    """API para crear proveedor desde modal"""
    try:
        data = request.get_json()
        nombre = data.get('nombre', '').strip() if data.get('nombre') else ''
        
        if not nombre:
            return jsonify({'error': 'El nombre del proveedor es requerido'}), 400
        
        # Verificar si ya existe un proveedor con ese nombre
        proveedor_existente = Proveedor.query.filter_by(nombre=nombre, activo=True).first()
        if proveedor_existente:
            return jsonify({'error': 'Ya existe un proveedor con ese nombre'}), 400
        
        # Manejar campos opcionales de forma segura
        telefono = data.get('telefono')
        telefono = telefono.strip() if telefono else None
        
        correo_electronico = data.get('correo_electronico')
        correo_electronico = correo_electronico.strip() if correo_electronico else None
        
        notas = data.get('notas')
        notas = notas.strip() if notas else None
        
        proveedor = Proveedor(
            nombre=nombre,
            telefono=telefono,
            correo_electronico=correo_electronico,
            notas=notas,
            activo=True
        )
        db.session.add(proveedor)
        db.session.commit()
        
        return jsonify(proveedor.to_dict())
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/<int:id>/productos')
@login_required
def productos(id):
    """Muestra los productos comprados a un proveedor"""
    proveedor = Proveedor.query.get_or_404(id)
    
    # Obtener todas las compras del proveedor
    compras = Compra.query.filter_by(proveedor_id=id).all()
    
    # Agrupar productos por producto_id
    productos_dict = {}
    
    for compra in compras:
        for item in compra.items:
            producto_id = item.producto_id
            
            if producto_id not in productos_dict:
                producto = Producto.query.get(producto_id)
                if producto:
                    productos_dict[producto_id] = {
                        'producto': {
                            'id': producto.id,
                            'nombre': producto.nombre,
                            'codigo_barras': producto.codigo_barras
                        },
                        'cantidad_total': 0,
                        'total_gastado': Decimal('0.00'),
                        'precio_minimo': item.precio_unitario,
                        'precio_maximo': item.precio_unitario,
                        'ultima_compra': compra.fecha_recepcion,
                        'numero_compras': 0,
                        'items_compra': []
                    }
            
            productos_dict[producto_id]['cantidad_total'] += item.cantidad
            productos_dict[producto_id]['total_gastado'] += item.subtotal
            productos_dict[producto_id]['precio_minimo'] = min(
                productos_dict[producto_id]['precio_minimo'], 
                item.precio_unitario
            )
            productos_dict[producto_id]['precio_maximo'] = max(
                productos_dict[producto_id]['precio_maximo'], 
                item.precio_unitario
            )
            
            if compra.fecha_recepcion > productos_dict[producto_id]['ultima_compra']:
                productos_dict[producto_id]['ultima_compra'] = compra.fecha_recepcion
            
            productos_dict[producto_id]['items_compra'].append({
                'fecha': compra.fecha_recepcion,
                'cantidad': item.cantidad,
                'precio_unitario': item.precio_unitario,
                'subtotal': item.subtotal,
                'numero_compra': compra.numero_compra
            })
    
    # Calcular precio promedio y número de compras
    productos_lista = []
    for producto_id, datos in productos_dict.items():
        datos['precio_promedio'] = datos['total_gastado'] / datos['cantidad_total']
        datos['numero_compras'] = len(set(item['numero_compra'] for item in datos['items_compra']))
        productos_lista.append(datos)
    
    # Ordenar por nombre del producto
    productos_lista.sort(key=lambda x: x['producto']['nombre'])
    
    # Calcular totales
    total_gastado = sum(datos['total_gastado'] for datos in productos_lista)
    cantidad_total = sum(datos['cantidad_total'] for datos in productos_lista)
    
    return render_template('proveedores/productos.html', 
                         proveedor=proveedor, 
                         productos=productos_lista,
                         total_gastado=total_gastado,
                         cantidad_total=cantidad_total)

