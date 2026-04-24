"""Initial schema — all base tables

Revision ID: 001
Revises:
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = set(inspector.get_table_names())

    if "users" not in existing:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("hashed_password", sa.String(255), nullable=False),
            sa.Column("nombre", sa.String(255), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "clientes" not in existing:
        op.create_table(
            "clientes",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("rfc", sa.String(13), nullable=False),
            sa.Column("razon_social", sa.String(255), nullable=False),
            sa.Column("regimen_fiscal", sa.String(100), nullable=True),
            sa.Column("actividad", sa.String(255), nullable=True),
            sa.Column("correo", sa.String(255), nullable=True),
            sa.Column("telefono", sa.String(20), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_clientes_rfc", "clientes", ["rfc"])

    if "conversations" not in existing:
        op.create_table(
            "conversations",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("cliente_id", sa.Integer(), nullable=True),
            sa.Column("title", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "messages" not in existing:
        op.create_table(
            "messages",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("conversation_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("tools_used", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if "law_updates" not in existing:
        op.create_table(
            "law_updates",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("ley", sa.String(50), nullable=True),
            sa.Column("tipo", sa.String(50), nullable=True),
            sa.Column("titulo", sa.Text(), nullable=False),
            sa.Column("url", sa.Text(), nullable=True),
            sa.Column("fecha_publicacion", sa.DateTime(timezone=True), nullable=True),
            sa.Column("resumen", sa.Text(), nullable=True),
            sa.Column("indexado", sa.Boolean(), nullable=True, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_law_updates_ley", "law_updates", ["ley"])


def downgrade() -> None:
    op.drop_table("law_updates")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("clientes")
    op.drop_table("users")
