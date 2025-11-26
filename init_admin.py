"""
Script para crear el usuario administrador inicial
Ejecutar: python init_admin.py
"""
from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    # Verificar si ya existe el usuario admin
    admin = Usuario.query.filter_by(username='admin').first()
    
    if admin:
        print("El usuario 'admin' ya existe.")
        respuesta = input("¿Deseas actualizar la contraseña? (s/n): ")
        if respuesta.lower() == 's':
            admin.set_password('admin123')
            db.session.commit()
            print("✓ Contraseña del usuario 'admin' actualizada correctamente.")
        else:
            print("Operación cancelada.")
    else:
        # Crear usuario admin
        admin = Usuario(
            username='admin',
            nombre_completo='Administrador',
            es_admin=True,
            activo=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Usuario administrador creado exitosamente:")
        print("  Usuario: admin")
        print("  Contraseña: admin123")

