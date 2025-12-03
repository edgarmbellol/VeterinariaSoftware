from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Animal, Consulta, Venta, Producto, ItemVenta, ItemConsulta
from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, or_
import random
import string

bp = Blueprint('consultas', __name__, url_prefix='/consultas')


def generar_numero_venta():
    fecha = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f'VTA-{fecha}-{random_str}'


@bp.route('/')
@login_required
def listar():
    """Listar todos los animales"""
    busqueda = request.args.get('busqueda', '').strip()
    especie = request.args.get('especie', '').strip()
    
    query = Animal.query.filter_by(activo=True)
    
    if busqueda:
        query = query.filter(
            or_(
                Animal.nombre.ilike(f'%{busqueda}%'),
                Animal.nombre_dueno.ilike(f'%{busqueda}%')
            )
        )
    
    if especie:
        query = query.filter(Animal.especie.ilike(f'%{especie}%'))
    
    animales = query.order_by(Animal.nombre).all()
    
    # Obtener especies únicas para el filtro
    especies = db.session.query(Animal.especie).filter_by(activo=True).distinct().all()
    especies_lista = [e[0] for e in especies if e[0]]
    
    return render_template('consultas/listar.html', 
                   animales=animales, 
                   busqueda=busqueda,
                   especie_seleccionada=especie,
                   especies=especies_lista)


@bp.route('/crear-animal', methods=['GET', 'POST'])
@login_required
def crear_animal():
    """Crear un nuevo animal"""
    if request.method == 'POST':
        try:
            animal = Animal(
                nombre=request.form.get('nombre', '').strip(),
                especie=request.form.get('especie', '').strip(),
                raza=request.form.get('raza', '').strip(),
                edad_anos=int(request.form.get('edad_anos', 0) or 0),
                edad_meses=int(request.form.get('edad_meses', 0) or 0),
                nombre_dueno=request.form.get('nombre_dueno', '').strip(),
                telefono_dueno=request.form.get('telefono_dueno', '').strip(),
                notas=request.form.get('notas', '').strip()
            )
            
            if not animal.nombre or not animal.especie or not animal.nombre_dueno:
                flash('Nombre del animal, especie y nombre del dueño son requeridos', 'error')
                return render_template('consultas/crear_animal.html')
            
            db.session.add(animal)
            db.session.commit()
            flash('Animal registrado exitosamente', 'success')
            return redirect(url_for('consultas.historia_clinica', id=animal.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear animal: {str(e)}', 'error')
    
    return render_template('consultas/crear_animal.html')


@bp.route('/animal/<int:id>')
@login_required
def historia_clinica(id):
    """Ver historia clínica completa de un animal"""
    animal = Animal.query.get_or_404(id)
    consultas = Consulta.query.filter_by(animal_id=id).order_by(Consulta.fecha_consulta.desc()).all()
    return render_template('consultas/historia_clinica.html', animal=animal, consultas=consultas)


@bp.route('/animal/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_animal(id):
    """Editar datos de un animal"""
    animal = Animal.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            animal.nombre = request.form.get('nombre', '').strip()
            animal.especie = request.form.get('especie', '').strip()
            animal.raza = request.form.get('raza', '').strip()
            animal.edad_anos = int(request.form.get('edad_anos', 0) or 0)
            animal.edad_meses = int(request.form.get('edad_meses', 0) or 0)
            animal.nombre_dueno = request.form.get('nombre_dueno', '').strip()
            animal.telefono_dueno = request.form.get('telefono_dueno', '').strip()
            animal.notas = request.form.get('notas', '').strip()
            
            if not animal.nombre or not animal.especie or not animal.nombre_dueno:
                flash('Nombre del animal, especie y nombre del dueño son requeridos', 'error')
                return render_template('consultas/crear_animal.html', animal=animal)
            
            db.session.commit()
            flash('Animal actualizado exitosamente', 'success')
            return redirect(url_for('consultas.historia_clinica', id=animal.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar animal: {str(e)}', 'error')
    
    return render_template('consultas/crear_animal.html', animal=animal)


@bp.route('/animal/<int:id>/nueva-consulta', methods=['GET', 'POST'])
@login_required
def nueva_consulta(id):
    """Crear una nueva consulta para un animal"""
    animal = Animal.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            fecha_consulta_str = request.form.get('fecha_consulta', '').strip()
            if fecha_consulta_str:
                try:
                    fecha_consulta = datetime.fromisoformat(fecha_consulta_str.replace('Z', '+00:00'))
                except ValueError:
                    fecha_consulta = datetime.utcnow()
            else:
                fecha_consulta = datetime.utcnow()
            
            consulta = Consulta(
                animal_id=animal.id,
                fecha_consulta=fecha_consulta,
                motivo=request.form.get('motivo', '').strip(),
                diagnostico=request.form.get('diagnostico', '').strip(),
                tratamiento=request.form.get('tratamiento', '').strip(),
                observaciones=request.form.get('observaciones', '').strip(),
                usuario_id=current_user.id
            )
            
            if not consulta.motivo:
                flash('El motivo de la consulta es requerido', 'error')
                return render_template('consultas/nueva_consulta.html', animal=animal)
            
            db.session.add(consulta)
            db.session.flush()
            
            # Procesar medicamentos
            # El formulario envía los datos como medicamentos[0][producto_id], medicamentos[1][producto_id], etc.
            medicamentos_data = []
            i = 0
            while True:
                producto_id = request.form.get(f'medicamentos[{i}][producto_id]')
                if not producto_id:
                    break
                cantidad = int(request.form.get(f'medicamentos[{i}][cantidad]', 1))
                notas = request.form.get(f'medicamentos[{i}][notas]', '').strip()
                
                item = ItemConsulta(
                    consulta_id=consulta.id,
                    producto_id=int(producto_id),
                    cantidad=cantidad,
                    notas=notas
                )
                db.session.add(item)
                medicamentos_data.append(producto_id)
                i += 1
            
            db.session.commit()
            flash('Consulta registrada exitosamente', 'success')
            
            # Si hay medicamentos, redirigir a crear venta
            if medicamentos_data:
                return redirect(url_for('consultas.crear_venta_desde_consulta', consulta_id=consulta.id))
            
            return redirect(url_for('consultas.historia_clinica', id=animal.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear consulta: {str(e)}', 'error')
    
    return render_template('consultas/nueva_consulta.html', animal=animal)


@bp.route('/api/buscar-animal', methods=['GET'])
@login_required
def buscar_animal():
    """API para búsqueda de animales"""
    busqueda = request.args.get('q', '').strip()
    if not busqueda or len(busqueda) < 2:
        return jsonify([])
    
    animales = Animal.query.filter(
        or_(
            Animal.nombre.ilike(f'%{busqueda}%'),
            Animal.nombre_dueno.ilike(f'%{busqueda}%')
        ),
        Animal.activo == True
    ).limit(20).all()
    
    return jsonify([a.to_dict() for a in animales])


@bp.route('/api/crear-consulta-con-venta', methods=['POST'])
@login_required
def crear_consulta_con_venta():
    """Crear una consulta y una venta asociada"""
    try:
        data = request.get_json()
        animal_id = data.get('animal_id')
        items = data.get('items', [])
        metodo_pago = data.get('metodo_pago')
        motivo = data.get('motivo', '').strip()
        diagnostico = data.get('diagnostico', '').strip()
        tratamiento = data.get('tratamiento', '').strip()
        observaciones = data.get('observaciones', '').strip()
        fecha_consulta = data.get('fecha_consulta')
        
        if not animal_id:
            return jsonify({'error': 'ID de animal requerido'}), 400
        
        if not motivo:
            return jsonify({'error': 'Motivo de consulta requerido'}), 400
        
        animal = Animal.query.get_or_404(animal_id)
        
        # Crear consulta
        consulta = Consulta(
            animal_id=animal.id,
            fecha_consulta=datetime.fromisoformat(fecha_consulta) if fecha_consulta else datetime.utcnow(),
            motivo=motivo,
            diagnostico=diagnostico,
            tratamiento=tratamiento,
            observaciones=observaciones,
            usuario_id=current_user.id
        )
        db.session.add(consulta)
        db.session.flush()
        
        venta_id = None
        
        # Si hay items, crear venta
        if items and metodo_pago:
            numero_venta = generar_numero_venta()
            total = Decimal('0.00')
            
            venta = Venta(
                numero_venta=numero_venta,
                total=Decimal('0.00'),
                metodo_pago=metodo_pago,
                notas=f'Venta asociada a consulta del animal: {animal.nombre}',
                usuario_id=current_user.id
            )
            db.session.add(venta)
            db.session.flush()
            venta_id = venta.id
            
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
            consulta.venta_id = venta_id
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'consulta_id': consulta.id,
            'venta_id': venta_id,
            'numero_venta': venta.numero_venta if venta_id else None,
            'total': float(venta.total) if venta_id else 0
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/consulta/<int:id>')
@login_required
def consulta_detalle(id):
    """Ver detalle de una consulta individual"""
    consulta = Consulta.query.get_or_404(id)
    return render_template('consultas/consulta_detalle.html', consulta=consulta)


@bp.route('/consulta/<int:consulta_id>/crear-carrito', methods=['POST'])
@login_required
def crear_carrito_desde_consulta(consulta_id):
    """Crear un carrito en ventas desde los medicamentos de una consulta"""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    # Obtener el nombre del animal
    nombre_animal = consulta.animal.nombre
    
    # Preparar los items del carrito
    items_carrito = []
    for item_consulta in consulta.items:
        producto = Producto.query.get(item_consulta.producto_id)
        if producto and producto.stock >= item_consulta.cantidad:
            precio_unitario = float(producto.precio_venta)
            cantidad = item_consulta.cantidad
            items_carrito.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'codigo_barras': producto.codigo_barras,
                'precio_unitario': precio_unitario,
                'precio_venta': precio_unitario,  # Alias para compatibilidad
                'cantidad': cantidad,
                'subtotal': precio_unitario * cantidad,
                'stock': producto.stock
            })
    
    if not items_carrito:
        flash('No hay medicamentos disponibles para agregar al carrito', 'error')
        return redirect(url_for('consultas.consulta_detalle', id=consulta_id))
    
    # Retornar JSON con los datos del carrito para que el frontend lo cree
    return jsonify({
        'success': True,
        'nombre_animal': nombre_animal,
        'items': items_carrito,
        'redirect': url_for('ventas.nueva_venta')
    })


@bp.route('/consulta/<int:consulta_id>/crear-venta', methods=['GET', 'POST'])
@login_required
def crear_venta_desde_consulta(consulta_id):
    """Crear una venta desde los medicamentos de una consulta"""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    if request.method == 'POST':
        try:
            metodo_pago = request.form.get('metodo_pago')
            if not metodo_pago:
                flash('Método de pago requerido', 'error')
                return render_template('consultas/crear_venta_consulta.html', consulta=consulta)
            
            # Crear venta
            numero_venta = generar_numero_venta()
            total = Decimal('0.00')
            
            venta = Venta(
                numero_venta=numero_venta,
                total=Decimal('0.00'),
                metodo_pago=metodo_pago,
                notas=f'Venta de medicamentos de consulta - Animal: {consulta.animal.nombre}',
                usuario_id=current_user.id
            )
            db.session.add(venta)
            db.session.flush()
            
            # Crear items de venta desde los medicamentos de la consulta
            for item_consulta in consulta.items:
                producto = Producto.query.get(item_consulta.producto_id)
                if not producto or producto.stock < item_consulta.cantidad:
                    db.session.rollback()
                    flash(f'Stock insuficiente para {producto.nombre if producto else "producto desconocido"}', 'error')
                    return render_template('consultas/crear_venta_consulta.html', consulta=consulta)
                
                precio_unitario = Decimal(str(producto.precio_venta))
                subtotal = precio_unitario * item_consulta.cantidad
                
                # Actualizar stock
                producto.stock -= item_consulta.cantidad
                
                item_venta = ItemVenta(
                    venta_id=venta.id,
                    producto_id=producto.id,
                    cantidad=item_consulta.cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal
                )
                db.session.add(item_venta)
                total += subtotal
            
            venta.total = total
            consulta.venta_id = venta.id
            db.session.commit()
            
            flash('Venta creada exitosamente', 'success')
            return redirect(url_for('ventas.generar_pdf', venta_id=venta.id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear venta: {str(e)}', 'error')
    
    return render_template('consultas/crear_venta_consulta.html', consulta=consulta)

