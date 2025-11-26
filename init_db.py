"""
Script de inicialización de la base de datos
Ejecutar este script para crear las tablas iniciales
"""
from app import create_app, db
from app.models import Categoria, Producto, Venta, ItemVenta, Devolucion, ItemDevolucion

app = create_app()

with app.app_context():
    print("Creando tablas de la base de datos...")
    db.create_all()
    print("✓ Tablas creadas exitosamente!")
    print("\nBase de datos inicializada. Puedes ejecutar 'python run.py' para iniciar la aplicación.")

