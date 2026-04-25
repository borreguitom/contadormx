"""Add empleados table

Revision ID: 005
Revises: 004
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'empleados',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('nombre_completo', sa.String(255), nullable=False),
        sa.Column('rfc', sa.String(13), nullable=True),
        sa.Column('curp', sa.String(18), nullable=True),
        sa.Column('nss', sa.String(11), nullable=True),
        sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
        sa.Column('fecha_alta', sa.Date(), nullable=False),
        sa.Column('fecha_baja', sa.Date(), nullable=True),
        sa.Column('tipo_contrato', sa.String(30), nullable=True),
        sa.Column('periodicidad_pago', sa.String(20), nullable=True),
        sa.Column('salario_diario', sa.Numeric(12, 4), nullable=False),
        sa.Column('departamento', sa.String(100), nullable=True),
        sa.Column('puesto', sa.String(100), nullable=True),
        sa.Column('banco', sa.String(50), nullable=True),
        sa.Column('clabe', sa.String(18), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_empleados_id', 'empleados', ['id'])
    op.create_index('ix_empleados_cliente_id', 'empleados', ['cliente_id'])


def downgrade():
    op.drop_index('ix_empleados_cliente_id', table_name='empleados')
    op.drop_index('ix_empleados_id', table_name='empleados')
    op.drop_table('empleados')
