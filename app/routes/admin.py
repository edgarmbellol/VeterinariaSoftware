from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import Venta, Producto, ItemVenta, Devolucion, ItemDevolucion, Usuario
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from decimal import Decimal
import random
import string

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorador para verificar que el usuario sea administrador"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.es_admin:
            flash('Acceso denegado. Se requieren permisos de administrador.', 'error')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
def dashboard():
    return render_template('admin/dashboard.html')


@bp.route('/api/estadisticas', methods=['GET'])
@login_required
def estadisticas():
    # Filtros de fecha y usuario
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    usuario_id = request.args.get('usuario_id')
    
    query = Venta.query
    
    if fecha_inicio:
        query = query.filter(Venta.fecha_venta >= datetime.fromisoformat(fecha_inicio))
    if fecha_fin:
        query = query.filter(Venta.fecha_venta <= datetime.fromisoformat(fecha_fin))
    if usuario_id and usuario_id != '':
        query = query.filter(Venta.usuario_id == int(usuario_id))
    
    ventas = query.all()
    
    # Calcular estadísticas
    total_ventas = len(ventas)
    total_ingresos = sum(float(v.total) for v in ventas)
    total_ganancias = sum(v.calcular_ganancia_total() for v in ventas)
    
    # Ventas por método de pago
    pagos = {}
    for venta in ventas:
        metodo = venta.metodo_pago
        pagos[metodo] = pagos.get(metodo, 0) + float(venta.total)
    
    # Productos más vendidos
    items_query = db.session.query(
        ItemVenta.producto_id,
        func.sum(ItemVenta.cantidad).label('total_vendido')
    ).join(Venta)
    
    if fecha_inicio:
        items_query = items_query.filter(Venta.fecha_venta >= datetime.fromisoformat(fecha_inicio))
    if fecha_fin:
        items_query = items_query.filter(Venta.fecha_venta <= datetime.fromisoformat(fecha_fin))
    
    productos_vendidos = items_query.group_by(ItemVenta.producto_id).order_by(
        func.sum(ItemVenta.cantidad).desc()
    ).limit(10).all()
    
    productos_top = []
    for producto_id, cantidad in productos_vendidos:
        producto = Producto.query.get(producto_id)
        if producto:
            productos_top.append({
                'nombre': producto.nombre,
                'cantidad': int(cantidad)
            })
    
    # Ventas por día (últimos 7 días)
    ultimos_7_dias = []
    for i in range(6, -1, -1):
        fecha = datetime.now() - timedelta(days=i)
        fecha_inicio_dia = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_dia = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        ventas_dia = Venta.query.filter(
            Venta.fecha_venta >= fecha_inicio_dia,
            Venta.fecha_venta <= fecha_fin_dia
        ).all()
        
        total_dia = sum(float(v.total) for v in ventas_dia)
        ultimos_7_dias.append({
            'fecha': fecha.strftime('%Y-%m-%d'),
            'total': total_dia
        })
    
    # Productos con stock bajo
    productos_stock_bajo = Producto.query.filter(
        Producto.stock <= Producto.stock_minimo,
        Producto.activo == True
    ).all()
    
    # Estadísticas por empleado
    estadisticas_empleados = []
    usuarios_con_ventas = db.session.query(
        Usuario.id,
        Usuario.username,
        func.count(Venta.id).label('total_ventas'),
        func.sum(Venta.total).label('total_ingresos')
    ).join(Venta, Usuario.id == Venta.usuario_id, isouter=True)
    
    if fecha_inicio:
        usuarios_con_ventas = usuarios_con_ventas.filter(Venta.fecha_venta >= datetime.fromisoformat(fecha_inicio))
    if fecha_fin:
        usuarios_con_ventas = usuarios_con_ventas.filter(Venta.fecha_venta <= datetime.fromisoformat(fecha_fin))
    
    usuarios_con_ventas = usuarios_con_ventas.group_by(Usuario.id, Usuario.username).all()
    
    for usuario_id, username, num_ventas, total_ing in usuarios_con_ventas:
        if num_ventas > 0:
            # Calcular ganancias para este usuario
            ventas_usuario = Venta.query.filter_by(usuario_id=usuario_id)
            if fecha_inicio:
                ventas_usuario = ventas_usuario.filter(Venta.fecha_venta >= datetime.fromisoformat(fecha_inicio))
            if fecha_fin:
                ventas_usuario = ventas_usuario.filter(Venta.fecha_venta <= datetime.fromisoformat(fecha_fin))
            
            total_ganancias_usuario = sum(v.calcular_ganancia_total() for v in ventas_usuario.all())
            
            estadisticas_empleados.append({
                'usuario_id': usuario_id,
                'username': username,
                'total_ventas': int(num_ventas),
                'total_ingresos': round(float(total_ing or 0), 2),
                'total_ganancias': round(total_ganancias_usuario, 2)
            })
    
    # Ordenar por total de ingresos descendente
    estadisticas_empleados.sort(key=lambda x: x['total_ingresos'], reverse=True)
    
    # Lista de usuarios para el filtro
    usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.username).all()
    usuarios_lista = [{'id': u.id, 'username': u.username} for u in usuarios]
    
    return jsonify({
        'total_ventas': total_ventas,
        'total_ingresos': round(total_ingresos, 2),
        'total_ganancias': round(total_ganancias, 2),
        'pagos_por_metodo': pagos,
        'productos_mas_vendidos': productos_top,
        'ventas_ultimos_7_dias': ultimos_7_dias,
        'productos_stock_bajo': [p.to_dict() for p in productos_stock_bajo],
        'estadisticas_empleados': estadisticas_empleados,
        'usuarios': usuarios_lista
    })


@bp.route('/ventas')
@login_required
def listar_ventas():
    return render_template('admin/ventas.html')


@bp.route('/api/ventas', methods=['GET'])
@login_required
def api_ventas():
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    usuario_id = request.args.get('usuario_id')
    pagina = int(request.args.get('pagina', 1))
    por_pagina = int(request.args.get('por_pagina', 20))
    
    query = Venta.query.order_by(Venta.fecha_venta.desc())
    
    if fecha_inicio:
        query = query.filter(Venta.fecha_venta >= datetime.fromisoformat(fecha_inicio))
    if fecha_fin:
        query = query.filter(Venta.fecha_venta <= datetime.fromisoformat(fecha_fin))
    if usuario_id and usuario_id != '':
        query = query.filter(Venta.usuario_id == int(usuario_id))
    
    paginacion = query.paginate(page=pagina, per_page=por_pagina, error_out=False)
    
    # Agregar información de devoluciones a cada venta
    ventas_con_devoluciones = []
    for venta in paginacion.items:
        venta_dict = venta.to_dict()
        devoluciones = Devolucion.query.filter_by(venta_id=venta.id).all()
        total_devuelto = sum(float(d.total_devolucion) for d in devoluciones)
        venta_dict['tiene_devoluciones'] = len(devoluciones) > 0
        venta_dict['total_devuelto'] = total_devuelto
        venta_dict['cantidad_devoluciones'] = len(devoluciones)
        ventas_con_devoluciones.append(venta_dict)
    
    return jsonify({
        'ventas': ventas_con_devoluciones,
        'total': paginacion.total,
        'paginas': paginacion.pages,
        'pagina_actual': pagina
    })


def generar_numero_devolucion():
    fecha = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'DEV-{fecha}-{random_str}'


@bp.route('/api/venta/<int:venta_id>', methods=['GET'])
@login_required
def obtener_venta(venta_id):
    venta = Venta.query.get_or_404(venta_id)
    
    # Verificar si ya tiene devoluciones
    devoluciones = Devolucion.query.filter_by(venta_id=venta_id).all()
    total_devuelto = sum(float(d.total_devolucion) for d in devoluciones)
    
    # Calcular cantidades ya devueltas por item
    items_devueltos = {}
    for devolucion in devoluciones:
        for item_dev in devolucion.items:
            item_venta_id = item_dev.item_venta_id
            if item_venta_id not in items_devueltos:
                items_devueltos[item_venta_id] = 0
            items_devueltos[item_venta_id] += item_dev.cantidad
    
    # Agregar información de devoluciones a los items
    venta_dict = venta.to_dict()
    for item in venta_dict['items']:
        item['cantidad_devuelta'] = items_devueltos.get(item['id'], 0)
        item['cantidad_disponible'] = item['cantidad'] - item['cantidad_devuelta']
    
    venta_dict['total_devuelto'] = total_devuelto
    venta_dict['total_disponible'] = float(venta.total) - total_devuelto
    
    return jsonify(venta_dict)


@bp.route('/api/devolucion', methods=['POST'])
@login_required
def procesar_devolucion():
    try:
        data = request.get_json()
        venta_id = data.get('venta_id')
        items = data.get('items', [])
        motivo = data.get('motivo', '')
        
        if not venta_id:
            return jsonify({'error': 'ID de venta requerido'}), 400
        
        if not items:
            return jsonify({'error': 'No hay items para devolver'}), 400
        
        venta = Venta.query.get_or_404(venta_id)
        
        # Verificar que no se devuelva más de lo disponible
        devoluciones_existentes = Devolucion.query.filter_by(venta_id=venta_id).all()
        items_devueltos = {}
        for devolucion in devoluciones_existentes:
            for item_dev in devolucion.items:
                item_venta_id = item_dev.item_venta_id
                if item_venta_id not in items_devueltos:
                    items_devueltos[item_venta_id] = 0
                items_devueltos[item_venta_id] += item_dev.cantidad
        
        total_devolucion = Decimal('0.00')
        numero_devolucion = generar_numero_devolucion()
        
        # Crear devolución
        devolucion = Devolucion(
            venta_id=venta_id,
            numero_devolucion=numero_devolucion,
            total_devolucion=Decimal('0.00'),
            motivo=motivo
        )
        db.session.add(devolucion)
        db.session.flush()
        
        # Crear items de devolución
        for item_data in items:
            item_venta_id = item_data['item_venta_id']
            cantidad_devolver = int(item_data['cantidad'])
            
            item_venta = ItemVenta.query.get(item_venta_id)
            if not item_venta:
                continue
            
            # Verificar cantidad disponible
            cantidad_ya_devuelta = items_devueltos.get(item_venta_id, 0)
            cantidad_disponible = item_venta.cantidad - cantidad_ya_devuelta
            
            if cantidad_devolver > cantidad_disponible:
                db.session.rollback()
                return jsonify({'error': f'Cantidad a devolver mayor a la disponible para {item_venta.producto.nombre}'}), 400
            
            # Restaurar stock
            producto = Producto.query.get(item_venta.producto_id)
            if producto:
                producto.stock += cantidad_devolver
            
            # Calcular subtotal
            subtotal = item_venta.precio_unitario * cantidad_devolver
            total_devolucion += subtotal
            
            item_devolucion = ItemDevolucion(
                devolucion_id=devolucion.id,
                item_venta_id=item_venta_id,
                producto_id=item_venta.producto_id,
                cantidad=cantidad_devolver,
                precio_unitario=item_venta.precio_unitario,
                subtotal=subtotal
            )
            db.session.add(item_devolucion)
        
        devolucion.total_devolucion = total_devolucion
        db.session.commit()
        
        return jsonify({
            'success': True,
            'devolucion_id': devolucion.id,
            'numero_devolucion': devolucion.numero_devolucion,
            'total_devolucion': float(total_devolucion)
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ========== RUTAS DE GESTIÓN DE USUARIOS ==========

@bp.route('/usuarios')
@admin_required
def listar_usuarios():
    """Listar todos los usuarios"""
    usuarios = Usuario.query.order_by(Usuario.fecha_creacion.desc()).all()
    return render_template('admin/usuarios.html', usuarios=usuarios)


@bp.route('/usuarios/crear', methods=['GET', 'POST'])
@admin_required
def crear_usuario():
    """Crear un nuevo usuario"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validaciones
        if not username:
            flash('El nombre de usuario es requerido', 'error')
            return render_template('admin/crear_usuario.html')
        
        if not password:
            flash('La contraseña es requerida', 'error')
            return render_template('admin/crear_usuario.html')
        
        if len(password) < 4:
            flash('La contraseña debe tener al menos 4 caracteres', 'error')
            return render_template('admin/crear_usuario.html')
        
        # Verificar si el usuario ya existe
        usuario_existente = Usuario.query.filter_by(username=username).first()
        if usuario_existente:
            flash('El nombre de usuario ya existe. Por favor elige otro.', 'error')
            return render_template('admin/crear_usuario.html')
        
        try:
            # Crear nuevo usuario
            nuevo_usuario = Usuario(
                username=username,
                es_admin=False,  # Por defecto no es admin
                activo=True
            )
            nuevo_usuario.set_password(password)
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash(f'Usuario "{username}" creado exitosamente', 'success')
            return redirect(url_for('admin.listar_usuarios'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el usuario: {str(e)}', 'error')
            return render_template('admin/crear_usuario.html')
    
    return render_template('admin/crear_usuario.html')


@bp.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@admin_required
def eliminar_usuario(id):
    """Eliminar un usuario (desactivarlo)"""
    usuario = Usuario.query.get_or_404(id)
    
    # No permitir eliminar al propio usuario
    if usuario.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'error')
        return redirect(url_for('admin.listar_usuarios'))
    
    # No permitir eliminar si es el único admin
    if usuario.es_admin:
        otros_admins = Usuario.query.filter(
            Usuario.es_admin == True,
            Usuario.id != usuario.id,
            Usuario.activo == True
        ).count()
        if otros_admins == 0:
            flash('No se puede eliminar el último administrador', 'error')
            return redirect(url_for('admin.listar_usuarios'))
    
    try:
        usuario.activo = False
        db.session.commit()
        flash(f'Usuario "{usuario.username}" desactivado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar el usuario: {str(e)}', 'error')
    
    return redirect(url_for('admin.listar_usuarios'))

