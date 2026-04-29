"""add_sat_verificacion

Revision ID: 007
Revises: ed13d28c7c6e
Create Date: 2026-04-29
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "ed13d28c7c6e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documentos", sa.Column("sat_estado", sa.String(30), nullable=True))
    op.add_column("documentos", sa.Column("sat_cancelable", sa.String(50), nullable=True))
    op.add_column("documentos", sa.Column("sat_verificado_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("documentos", "sat_verificado_at")
    op.drop_column("documentos", "sat_cancelable")
    op.drop_column("documentos", "sat_estado")
