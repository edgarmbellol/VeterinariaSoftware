from app import create_app, db
from app.models import Categoria, Producto, Venta, ItemVenta, Devolucion, ItemDevolucion, Usuario

app = create_app()

with app.app_context():
    db.create_all()
    # Crear usuario admin si no existe
    admin = Usuario.query.filter_by(username='admin').first()
    if not admin:
        admin = Usuario(
            username='admin',
            nombre_completo='Administrador',
            es_admin=True,
            activo=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Usuario administrador creado: admin / admin123")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

