"""Add billing and usage fields to users

Revision ID: 002
Revises: 001
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {c["name"] for c in inspector.get_columns("users")}

    if "plan" not in existing_cols:
        op.add_column("users", sa.Column("plan", sa.String(20), server_default="free", nullable=False))

    if "queries_this_month" not in existing_cols:
        op.add_column("users", sa.Column("queries_this_month", sa.Integer(), server_default="0", nullable=False))

    if "queries_reset_date" not in existing_cols:
        op.add_column("users", sa.Column("queries_reset_date", sa.DateTime(timezone=True), nullable=True))

    if "stripe_customer_id" not in existing_cols:
        op.add_column("users", sa.Column("stripe_customer_id", sa.String(255), nullable=True))

    if "stripe_subscription_id" not in existing_cols:
        op.add_column("users", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
    op.drop_column("users", "queries_reset_date")
    op.drop_column("users", "queries_this_month")
    op.drop_column("users", "plan")
