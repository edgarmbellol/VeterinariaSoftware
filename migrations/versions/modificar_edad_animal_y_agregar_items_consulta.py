"""Modificar edad animal y agregar items consulta

Revision ID: modificar_edad_items
Revises: agregar_animal_consulta
Create Date: 2025-01-20 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'modificar_edad_items'
down_revision = 'agregar_animal_consulta'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    columns = {}
    
    if 'animales' in tables:
        animales_columns = {col['name']: col for col in inspector.get_columns('animales')}
        columns['animales'] = animales_columns
        
        # Modificar tabla animales
        with op.batch_alter_table('animales', schema=None) as batch_op:
            # Si existe la columna edad (texto), eliminarla después de migrar datos
            if 'edad' in animales_columns and 'edad_anos' not in animales_columns:
                # Agregar nuevas columnas
                batch_op.add_column(sa.Column('edad_anos', sa.Integer(), nullable=True, server_default='0'))
                batch_op.add_column(sa.Column('edad_meses', sa.Integer(), nullable=True, server_default='0'))
                # Eliminar columna antigua
                batch_op.drop_column('edad')
            elif 'edad_anos' not in animales_columns:
                batch_op.add_column(sa.Column('edad_anos', sa.Integer(), nullable=True, server_default='0'))
                batch_op.add_column(sa.Column('edad_meses', sa.Integer(), nullable=True, server_default='0'))
    
    # Crear tabla items_consulta
    if 'items_consulta' not in tables:
        op.create_table('items_consulta',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('consulta_id', sa.Integer(), nullable=False),
            sa.Column('producto_id', sa.Integer(), nullable=False),
            sa.Column('cantidad', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('notas', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['consulta_id'], ['consultas.id'], ),
            sa.ForeignKeyConstraint(['producto_id'], ['productos.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    # Eliminar tabla items_consulta
    op.drop_table('items_consulta')
    
    # Revertir cambios en animales
    with op.batch_alter_table('animales', schema=None) as batch_op:
        batch_op.add_column(sa.Column('edad', sa.String(length=50), nullable=True))
        batch_op.drop_column('edad_meses')
        batch_op.drop_column('edad_anos')

