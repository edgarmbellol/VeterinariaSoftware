from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Producto, Categoria
from decimal import Decimal

bp = Blueprint('productos', __name__, url_prefix='/productos')


@bp.route('/')
@login_required
def listar():
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    return render_template('productos/listar.html', productos=productos)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()
    categorias_dict = [c.to_dict() for c in categorias]
    
    if request.method == 'POST':
        try:
            categoria_id = request.form.get('categoria_id')
            producto = Producto(
                codigo_barras=request.form.get('codigo_barras'),
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
    
    return render_template('productos/crear.html', categorias=categorias_dict)


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    producto = Producto.query.get_or_404(id)
    categorias = Categoria.query.filter_by(activa=True).order_by(Categoria.nombre).all()
    categorias_dict = [c.to_dict() for c in categorias]
    
    if request.method == 'POST':
        try:
            categoria_id = request.form.get('categoria_id')
            producto.codigo_barras = request.form.get('codigo_barras')
            producto.nombre = request.form.get('nombre')
            producto.descripcion = request.form.get('descripcion', '')
            producto.precio_venta = Decimal(request.form.get('precio_venta'))
            producto.precio_compra = Decimal(request.form.get('precio_compra'))
            producto.stock = int(request.form.get('stock', 0))
            producto.stock_minimo = int(request.form.get('stock_minimo', 0))
            producto.categoria_id = int(categoria_id) if categoria_id and categoria_id != '' else None
            
            db.session.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('productos.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'error')
    
    return render_template('productos/editar.html', producto=producto, categorias=categorias_dict)


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

