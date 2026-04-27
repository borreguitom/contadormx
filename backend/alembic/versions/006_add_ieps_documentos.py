"""Add ieps fields to documentos

Revision ID: 006
Revises: 005
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('documentos', sa.Column('ieps_trasladado', sa.Float(), nullable=True, server_default='0'))
    op.add_column('documentos', sa.Column('ieps_retenido', sa.Float(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('documentos', 'ieps_retenido')
    op.drop_column('documentos', 'ieps_trasladado')
