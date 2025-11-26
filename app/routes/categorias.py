from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from app import db
from app.models import Categoria, Producto

bp = Blueprint('categorias', __name__, url_prefix='/categorias')


@bp.route('/')
@login_required
def listar():
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('categorias/listar.html', categorias=categorias)


@bp.route('/crear', methods=['GET', 'POST'])
@login_required
def crear():
    if request.method == 'POST':
        try:
            # Verificar si ya existe una categoría con ese nombre
            categoria_existente = Categoria.query.filter_by(nombre=request.form.get('nombre').strip()).first()
            if categoria_existente:
                flash('Ya existe una categoría con ese nombre', 'error')
                return render_template('categorias/crear.html')
            
            categoria = Categoria(
                nombre=request.form.get('nombre').strip(),
                descripcion=request.form.get('descripcion', ''),
                activa=True
            )
            db.session.add(categoria)
            db.session.commit()
            flash('Categoría creada exitosamente', 'success')
            return redirect(url_for('categorias.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear categoría: {str(e)}', 'error')
    
    return render_template('categorias/crear.html')


@bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    categoria = Categoria.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Verificar si ya existe otra categoría con ese nombre
            nombre_nuevo = request.form.get('nombre').strip()
            categoria_existente = Categoria.query.filter(
                Categoria.nombre == nombre_nuevo,
                Categoria.id != id
            ).first()
            
            if categoria_existente:
                flash('Ya existe otra categoría con ese nombre', 'error')
                return render_template('categorias/editar.html', categoria=categoria)
            
            categoria.nombre = nombre_nuevo
            categoria.descripcion = request.form.get('descripcion', '')
            categoria.activa = request.form.get('activa') == 'on'
            
            db.session.commit()
            flash('Categoría actualizada exitosamente', 'success')
            return redirect(url_for('categorias.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar categoría: {str(e)}', 'error')
    
    return render_template('categorias/editar.html', categoria=categoria)


@bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    categoria = Categoria.query.get_or_404(id)
    
    # Verificar si hay productos usando esta categoría
    productos_con_categoria = Producto.query.filter_by(categoria_id=id, activo=True).count()
    
    if productos_con_categoria > 0:
        flash(f'No se puede eliminar la categoría porque tiene {productos_con_categoria} producto(s) asociado(s)', 'error')
        return redirect(url_for('categorias.listar'))
    
    try:
        categoria.activa = False
        db.session.commit()
        flash('Categoría eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar categoría: {str(e)}', 'error')
    
    return redirect(url_for('categorias.listar'))


@bp.route('/api/listar', methods=['GET'])
@login_required
def listar_api():
    activas = request.args.get('activas', 'false').lower() == 'true'
    query = Categoria.query
    
    if activas:
        query = query.filter_by(activa=True)
    
    categorias = query.order_by(Categoria.nombre).all()
    return jsonify([c.to_dict() for c in categorias])


@bp.route('/api/crear', methods=['POST'])
@login_required
def crear_api():
    try:
        data = request.get_json()
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '')
        
        if not nombre:
            return jsonify({'error': 'El nombre de la categoría es requerido'}), 400
        
        # Verificar si ya existe una categoría con ese nombre
        categoria_existente = Categoria.query.filter_by(nombre=nombre).first()
        if categoria_existente:
            return jsonify({'error': 'Ya existe una categoría con ese nombre'}), 400
        
        categoria = Categoria(
            nombre=nombre,
            descripcion=descripcion,
            activa=True
        )
        db.session.add(categoria)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'categoria': categoria.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear categoría: {str(e)}'}), 500


