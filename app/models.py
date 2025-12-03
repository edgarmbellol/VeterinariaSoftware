from app import db
from datetime import datetime
from sqlalchemy import Numeric
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os


class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(200))
    es_admin = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Genera el hash de la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nombre_completo': self.nombre_completo,
            'es_admin': self.es_admin,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    productos = db.relationship('Producto', backref='categoria_rel', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'activa': self.activa,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }


class Producto(db.Model):
    __tablename__ = 'productos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(50), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    precio_venta = db.Column(Numeric(10, 2), nullable=False)
    precio_compra = db.Column(Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0, nullable=False)
    stock_minimo = db.Column(db.Integer, default=0)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items_venta = db.relationship('ItemVenta', backref='producto', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_barras': self.codigo_barras,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'precio_venta': float(self.precio_venta),
            'precio_compra': float(self.precio_compra),
            'stock': self.stock,
            'stock_minimo': self.stock_minimo,
            'categoria_id': self.categoria_id,
            'categoria': self.categoria_rel.nombre if self.categoria_rel else None,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
    
    def calcular_ganancia(self, cantidad=1):
        return (float(self.precio_venta) - float(self.precio_compra)) * cantidad


class Venta(db.Model):
    __tablename__ = 'ventas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_venta = db.Column(db.String(20), unique=True, nullable=False)
    total = db.Column(Numeric(10, 2), nullable=False)
    metodo_pago = db.Column(db.String(20), nullable=False)  # efectivo, nequi, daviplata
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notas = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    items = db.relationship('ItemVenta', backref='venta', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', backref='ventas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_venta': self.numero_venta,
            'total': float(self.total),
            'metodo_pago': self.metodo_pago,
            'fecha_venta': self.fecha_venta.isoformat() if self.fecha_venta else None,
            'notas': self.notas,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.username if self.usuario else None,
            'items': [item.to_dict() for item in self.items]
        }
    
    def calcular_ganancia_total(self):
        return sum(item.calcular_ganancia() for item in self.items)


class ItemVenta(db.Model):
    __tablename__ = 'items_venta'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(Numeric(10, 2), nullable=False)
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal)
        }
    
    def calcular_ganancia(self):
        if self.producto:
            precio_compra = float(self.producto.precio_compra)
            return (float(self.precio_unitario) - precio_compra) * self.cantidad
        return 0


class Devolucion(db.Model):
    __tablename__ = 'devoluciones'
    
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    numero_devolucion = db.Column(db.String(20), unique=True, nullable=False)
    total_devolucion = db.Column(Numeric(10, 2), nullable=False)
    motivo = db.Column(db.Text)
    fecha_devolucion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    venta = db.relationship('Venta', backref='devoluciones')
    items = db.relationship('ItemDevolucion', backref='devolucion', lazy=True, cascade='all, delete-orphan')
    
    def calcular_ganancia_perdida_total(self):
        """Calcula la ganancia total perdida por esta devolución"""
        return sum(item.calcular_ganancia_perdida() for item in self.items)
    
    def to_dict(self):
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'numero_devolucion': self.numero_devolucion,
            'total_devolucion': float(self.total_devolucion),
            'motivo': self.motivo,
            'fecha_devolucion': self.fecha_devolucion.isoformat() if self.fecha_devolucion else None,
            'items': [item.to_dict() for item in self.items]
        }


class ItemDevolucion(db.Model):
    __tablename__ = 'items_devolucion'
    
    id = db.Column(db.Integer, primary_key=True)
    devolucion_id = db.Column(db.Integer, db.ForeignKey('devoluciones.id'), nullable=False)
    item_venta_id = db.Column(db.Integer, db.ForeignKey('items_venta.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(Numeric(10, 2), nullable=False)
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    
    item_venta = db.relationship('ItemVenta', backref='devoluciones')
    producto = db.relationship('Producto', backref='items_devolucion')
    
    def calcular_ganancia_perdida(self):
        """Calcula la ganancia perdida por este item devuelto"""
        if self.producto:
            precio_compra = float(self.producto.precio_compra)
            return (float(self.precio_unitario) - precio_compra) * self.cantidad
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'devolucion_id': self.devolucion_id,
            'item_venta_id': self.item_venta_id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal)
        }


class Animal(db.Model):
    __tablename__ = 'animales'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    especie = db.Column(db.String(100), nullable=False)  # perro, gato, etc.
    raza = db.Column(db.String(200))
    edad_anos = db.Column(db.Integer, default=0)  # Edad en años
    edad_meses = db.Column(db.Integer, default=0)  # Edad en meses
    nombre_dueno = db.Column(db.String(200), nullable=False)
    telefono_dueno = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.Text)
    
    consultas = db.relationship('Consulta', backref='animal', lazy=True, cascade='all, delete-orphan', order_by='Consulta.fecha_consulta.desc()')
    
    def get_edad_display(self):
        """Retorna la edad formateada como string"""
        partes = []
        if self.edad_anos and self.edad_anos > 0:
            partes.append(f"{self.edad_anos} año{'s' if self.edad_anos != 1 else ''}")
        if self.edad_meses and self.edad_meses > 0:
            partes.append(f"{self.edad_meses} mes{'es' if self.edad_meses != 1 else ''}")
        return ", ".join(partes) if partes else "No especificada"
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'especie': self.especie,
            'raza': self.raza,
            'edad_anos': self.edad_anos,
            'edad_meses': self.edad_meses,
            'edad_display': self.get_edad_display(),
            'nombre_dueno': self.nombre_dueno,
            'telefono_dueno': self.telefono_dueno,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'notas': self.notas,
            'total_consultas': len(self.consultas)
        }


class Consulta(db.Model):
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animales.id'), nullable=False)
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    motivo = db.Column(db.Text, nullable=False)
    diagnostico = db.Column(db.Text)
    tratamiento = db.Column(db.Text)
    observaciones = db.Column(db.Text)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    venta = db.relationship('Venta', backref='consultas')
    usuario = db.relationship('Usuario', backref='consultas')
    items = db.relationship('ItemConsulta', backref='consulta', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'animal_id': self.animal_id,
            'animal_nombre': self.animal.nombre if self.animal else None,
            'fecha_consulta': self.fecha_consulta.isoformat() if self.fecha_consulta else None,
            'motivo': self.motivo,
            'diagnostico': self.diagnostico,
            'tratamiento': self.tratamiento,
            'observaciones': self.observaciones,
            'venta_id': self.venta_id,
            'venta_numero': self.venta.numero_venta if self.venta else None,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.username if self.usuario else None,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'items': [item.to_dict() for item in self.items]
        }


class ItemConsulta(db.Model):
    __tablename__ = 'items_consulta'
    
    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    notas = db.Column(db.Text)  # Instrucciones de uso, dosis, etc.
    
    producto = db.relationship('Producto', backref='items_consulta')
    
    def to_dict(self):
        return {
            'id': self.id,
            'consulta_id': self.consulta_id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'producto_codigo': self.producto.codigo_barras if self.producto else None,
            'producto_precio': float(self.producto.precio_venta) if self.producto else 0,
            'cantidad': self.cantidad,
            'subtotal': float(self.producto.precio_venta) * self.cantidad if self.producto else 0,
            'notas': self.notas
        }


class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    correo_electronico = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    notas = db.Column(db.Text)
    
    compras = db.relationship('Compra', backref='proveedor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'telefono': self.telefono,
            'correo_electronico': self.correo_electronico,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'notas': self.notas,
            'total_compras': len(self.compras)
        }


class Compra(db.Model):
    __tablename__ = 'compras'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_compra = db.Column(db.String(20), unique=True, nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=True)
    total = db.Column(Numeric(10, 2), nullable=False)
    fecha_recepcion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notas = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    items = db.relationship('ItemCompra', backref='compra', lazy=True, cascade='all, delete-orphan')
    usuario = db.relationship('Usuario', backref='compras')
    
    def to_dict(self):
        return {
            'id': self.id,
            'numero_compra': self.numero_compra,
            'proveedor_id': self.proveedor_id,
            'proveedor_nombre': self.proveedor.nombre if self.proveedor else 'Sin proveedor',
            'total': float(self.total),
            'fecha_recepcion': self.fecha_recepcion.isoformat() if self.fecha_recepcion else None,
            'notas': self.notas,
            'usuario_id': self.usuario_id,
            'usuario_nombre': self.usuario.username if self.usuario else None,
            'items': [item.to_dict() for item in self.items]
        }


class ItemCompra(db.Model):
    __tablename__ = 'items_compra'
    
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(Numeric(10, 2), nullable=False)
    subtotal = db.Column(Numeric(10, 2), nullable=False)
    
    producto = db.relationship('Producto', backref='items_compra')
    
    def to_dict(self):
        return {
            'id': self.id,
            'compra_id': self.compra_id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'producto_codigo': self.producto.codigo_barras if self.producto else None,
            'cantidad': self.cantidad,
            'precio_unitario': float(self.precio_unitario),
            'subtotal': float(self.subtotal)
        }


class ConfiguracionNegocio(db.Model):
    __tablename__ = 'configuracion_negocio'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_negocio = db.Column(db.String(200), default='Veterinaria')
    nit = db.Column(db.String(50))
    direccion = db.Column(db.Text)
    telefono = db.Column(db.String(50))
    correo = db.Column(db.String(200))
    logo_path = db.Column(db.String(500))  # Ruta del archivo de logo
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre_negocio': self.nombre_negocio,
            'nit': self.nit,
            'direccion': self.direccion,
            'telefono': self.telefono,
            'correo': self.correo,
            'logo_path': self.logo_path,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
        }
    
    @staticmethod
    def obtener_configuracion():
        """Obtiene la configuración del negocio, creándola si no existe"""
        config = ConfiguracionNegocio.query.first()
        if not config:
            config = ConfiguracionNegocio(
                nombre_negocio='Veterinaria',
                nit='',
                direccion='',
                telefono='',
                correo=''
            )
            db.session.add(config)
            db.session.commit()
        return config

