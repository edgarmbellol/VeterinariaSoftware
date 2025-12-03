from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Producto, Proveedor, Compra, ItemCompra
from decimal import Decimal
from datetime import datetime
from sqlalchemy import func
import random
import string

bp = Blueprint('compras', __name__, url_prefix='/compras')


def generar_numero_compra():
    fecha = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'COM-{fecha}-{random_str}'


@bp.route('/')
@login_required
def listar():
    compras = Compra.query.order_by(Compra.fecha_recepcion.desc()).limit(50).all()
    return render_template('compras/listar.html', compras=compras)


@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    proveedores = Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    return render_template('compras/nueva.html', proveedores=proveedores)


@bp.route('/api/buscar-producto', methods=['GET'])
@login_required
def buscar_producto():
    codigo = request.args.get('codigo', '').strip()
    nombre = request.args.get('nombre', '').strip()
    
    if codigo:
        producto = Producto.query.filter_by(codigo_barras=codigo, activo=True).first()
        if producto:
            return jsonify(producto.to_dict())
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    if nombre and len(nombre) >= 2:
        productos = Producto.query.filter(
            func.lower(Producto.nombre).like(f'%{nombre.lower()}%'),
            Producto.activo == True
        ).limit(20).all()
        return jsonify([p.to_dict() for p in productos])
    
    return jsonify({'error': 'Código o nombre requerido'}), 400


@bp.route('/api/procesar', methods=['POST'])
@login_required
def procesar_compra():
    try:
        data = request.get_json()
        items = data.get('items', [])
        proveedor_id = data.get('proveedor_id')
        total = Decimal(str(data.get('total', 0)))
        notas = data.get('notas', '')
        
        if not items:
            return jsonify({'error': 'No hay items en la compra'}), 400
        
        if total <= 0:
            return jsonify({'error': 'El total debe ser mayor a cero'}), 400
        
        # Crear compra
        numero_compra = generar_numero_compra()
        compra = Compra(
            numero_compra=numero_compra,
            proveedor_id=int(proveedor_id) if proveedor_id else None,
            total=Decimal('0.00'),
            notas=notas,
            usuario_id=current_user.id
        )
        db.session.add(compra)
        db.session.flush()
        
        # Crear items de compra y actualizar stock
        total_calculado = Decimal('0.00')
        for item_data in items:
            producto_id = item_data.get('producto_id')
            cantidad = int(item_data.get('cantidad', 0))
            precio_unitario = Decimal(str(item_data.get('precio_unitario', 0)))
            subtotal = precio_unitario * cantidad
            
            producto = Producto.query.get(producto_id)
            if not producto:
                continue
            
            # Actualizar stock
            producto.stock += cantidad
            
            # Crear item de compra
            item_compra = ItemCompra(
                compra_id=compra.id,
                producto_id=producto_id,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            db.session.add(item_compra)
            total_calculado += subtotal
        
        compra.total = total_calculado
        db.session.commit()
        
        return jsonify({
            'success': True,
            'compra_id': compra.id,
            'numero_compra': compra.numero_compra,
            'total': float(total_calculado)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/estadisticas', methods=['GET'])
@login_required
def estadisticas():
    """Estadísticas de recepción de pedidos por día y hora"""
    from sqlalchemy import extract
    
    # Compras por día de la semana
    compras_por_dia = db.session.query(
        extract('dow', Compra.fecha_recepcion).label('dia_semana'),
        func.count(Compra.id).label('total')
    ).group_by('dia_semana').all()
    
    dias_semana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    compras_dia = {dias_semana[int(dia)]: int(total) for dia, total in compras_por_dia}
    
    # Compras por hora del día
    compras_por_hora = db.session.query(
        extract('hour', Compra.fecha_recepcion).label('hora'),
        func.count(Compra.id).label('total')
    ).group_by('hora').all()
    
    compras_hora = {f"{int(hora):02d}:00": int(total) for hora, total in compras_por_hora}
    
    # Total de compras y monto total
    total_compras = Compra.query.count()
    total_monto = db.session.query(func.sum(Compra.total)).scalar() or 0
    
    return jsonify({
        'compras_por_dia': compras_dia,
        'compras_por_hora': compras_hora,
        'total_compras': total_compras,
        'total_monto': float(total_monto)
    })

