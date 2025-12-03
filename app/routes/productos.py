from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Producto, Categoria
from decimal import Decimal
from sqlalchemy import func

bp = Blueprint('productos', __name__, url_prefix='/productos')


@bp.route('/')
@login_required
def listar():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    return render_template('productos/listar.html', productos=productos)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            codigo_barras = request.form.get('codigo_barras')
            
            # Verificar si ya existe un producto con ese código de barras
            producto_existente = Producto.query.filter_by(codigo_barras=codigo_barras).first()
            
            if producto_existente:
                if not producto_existente.activo:
                    # Si el producto existe pero está inactivo, redirigir a editar
                    flash(f'Ya existe un producto inactivo con el código "{codigo_barras}". Puedes modificarlo y reactivarlo.', 'info')
                    return redirect(url_for('productos.editar', id=producto_existente.id))
                else:
                    # Si el producto existe y está activo, mostrar error
                    flash(f'Ya existe un producto activo con el código de barras "{codigo_barras}".', 'error')
                    categorias_list = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()
                    categorias = [c.to_dict() for c in categorias_list]
                    return render_template('productos/crear.html', categorias=categorias)
            
            # Si no existe, crear el producto nuevo
            categoria_id = request.form.get('categoria_id')
            producto = Producto(
                codigo_barras=codigo_barras,
                nombre=request.form.get('nombre'),
                descripcion=request.form.get('descripcion', ''),
                precio_venta=Decimal(request.form.get('precio_venta')),
                precio_compra=Decimal(request.form.get('precio_compra')),
                stock=int(request.form.get('stock', 0)),
                stock_minimo=int(request.form.get('stock_minimo', 0)),
                categoria_id=int(categoria_id) if categoria_id and categoria_id != '' else None
            )
            db.session.add(producto)
            db.session.commit()
            flash('Producto creado exitosamente', 'success')
            return redirect(url_for('productos.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear producto: {str(e)}', 'error')
    
    # Cargar categorías para el formulario
    categorias_list = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()
    categorias = [c.to_dict() for c in categorias_list]
    
    return render_template('productos/crear.html', categorias=categorias)


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    producto = Producto.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Guardar el estado anterior para el mensaje
            estaba_inactivo = not producto.activo
            
            categoria_id = request.form.get('categoria_id')
            producto.codigo_barras = request.form.get('codigo_barras')
            producto.nombre = request.form.get('nombre')
            producto.descripcion = request.form.get('descripcion', '')
            producto.precio_venta = Decimal(request.form.get('precio_venta'))
            producto.precio_compra = Decimal(request.form.get('precio_compra'))
            producto.stock = int(request.form.get('stock', 0))
            producto.stock_minimo = int(request.form.get('stock_minimo', 0))
            producto.categoria_id = int(categoria_id) if categoria_id and categoria_id != '' else None
            
            # Si el producto estaba inactivo, reactivarlo automáticamente
            if estaba_inactivo:
                producto.activo = True
            
            db.session.commit()
            
            if estaba_inactivo:
                flash('Producto reactivado y actualizado exitosamente', 'success')
            else:
                flash('Producto actualizado exitosamente', 'success')
            
            return redirect(url_for('productos.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'error')
    
    # Cargar categorías para el formulario
    categorias_list = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()
    categorias = [c.to_dict() for c in categorias_list]
    
    return render_template('productos/editar.html', producto=producto, categorias=categorias)


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    producto = Producto.query.get_or_404(id)
    try:
        producto.activo = False
        db.session.commit()
        flash('Producto eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'error')
    
    return redirect(url_for('productos.listar'))


@bp.route('/api/buscar', methods=['GET'])
@login_required
def buscar_api():
    codigo = request.args.get('codigo', '')
    if not codigo:
        return jsonify({'error': 'Código requerido'}), 400
    
    producto = Producto.query.filter_by(codigo_barras=codigo, activo=True).first()
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    
    return jsonify(producto.to_dict())


@bp.route('/api/listar', methods=['GET'])
@login_required
def listar_api():
    productos = Producto.query.filter_by(activo=True).all()
    return jsonify([p.to_dict() for p in productos])


@bp.route('/api/buscar-nombre', methods=['GET'])
@login_required
def buscar_nombre():
    """Buscar productos por nombre, incluyendo los que no tienen stock (para recibir pedidos)"""
    nombre = request.args.get('nombre', '').strip()
    if not nombre or len(nombre) < 2:
        return jsonify([])
    
    # Búsqueda por nombre (case insensitive, parcial) - incluye productos sin stock
    productos = Producto.query.filter(
        func.lower(Producto.nombre).like(f'%{nombre.lower()}%'),
        Producto.activo == True
    ).limit(20).all()
    
    return jsonify([p.to_dict() for p in productos])


@bp.route('/api/recibir-pedido', methods=['POST'])
@login_required
def recibir_pedido():
    """Endpoint legacy - redirige a la nueva funcionalidad de compras"""
    return jsonify({
        'error': 'Esta funcionalidad ha sido movida a la sección de Compras. Por favor usa el botón "Recibir Pedido" en la página de ventas.'
    }), 400

