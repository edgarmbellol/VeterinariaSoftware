from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Configuración
    if config_name == 'development':
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///veterinaria.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Usuario
        return Usuario.query.get(int(user_id))
    
    # Registrar blueprints
    from app.routes import productos, ventas, admin, categorias, auth, consultas, compras, proveedores, asistente_ia
    app.register_blueprint(auth.bp)
    app.register_blueprint(productos.bp)
    app.register_blueprint(ventas.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(categorias.bp)
    app.register_blueprint(consultas.bp)
    app.register_blueprint(compras.bp)
    app.register_blueprint(proveedores.bp)
    app.register_blueprint(asistente_ia.bp)
    
    # Contexto global para templates
    @app.context_processor
    def inject_configuracion():
        from app.models import ConfiguracionNegocio
        try:
            config = ConfiguracionNegocio.obtener_configuracion()
            return {'configuracion_negocio': config}
        except:
            return {'configuracion_negocio': None}
    
    # Ruta principal
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect('/ventas')
        else:
            return redirect('/auth/login')
    
    return app

