"""Add documentos table

Revision ID: 003
Revises: 002
Create Date: 2026-04-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import inspect

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()

    if "documentos" not in tables:
        op.create_table(
            "documentos",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("cliente_id", sa.Integer, sa.ForeignKey("clientes.id"), nullable=False),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
            sa.Column("nombre_archivo", sa.String(255), nullable=False),
            sa.Column("tipo_archivo", sa.String(20), nullable=False),
            sa.Column("file_path", sa.Text, nullable=True),
            sa.Column("uuid_cfdi", sa.String(50), nullable=True),
            sa.Column("tipo_comprobante", sa.String(10), nullable=True),
            sa.Column("serie", sa.String(25), nullable=True),
            sa.Column("folio", sa.String(40), nullable=True),
            sa.Column("fecha_emision", sa.DateTime(timezone=True), nullable=True),
            sa.Column("emisor_rfc", sa.String(15), nullable=True),
            sa.Column("emisor_nombre", sa.String(255), nullable=True),
            sa.Column("receptor_rfc", sa.String(15), nullable=True),
            sa.Column("receptor_nombre", sa.String(255), nullable=True),
            sa.Column("subtotal", sa.Float, nullable=True),
            sa.Column("descuento", sa.Float, nullable=True, server_default="0"),
            sa.Column("iva_trasladado", sa.Float, nullable=True, server_default="0"),
            sa.Column("iva_retenido", sa.Float, nullable=True, server_default="0"),
            sa.Column("isr_retenido", sa.Float, nullable=True, server_default="0"),
            sa.Column("total", sa.Float, nullable=True),
            sa.Column("moneda", sa.String(10), nullable=True, server_default="MXN"),
            sa.Column("tipo_cambio", sa.Float, nullable=True, server_default="1"),
            sa.Column("conceptos", JSON, nullable=True),
            sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
            sa.Column("error_msg", sa.Text, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_documentos_uuid_cfdi", "documentos", ["uuid_cfdi"])
        op.create_index("ix_documentos_cliente_id", "documentos", ["cliente_id"])


def downgrade():
    op.drop_table("documentos")
