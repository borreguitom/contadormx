"""Add SAT integration tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sat_credentials',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rfc', sa.String(13), nullable=False),
        sa.Column('alias', sa.String(100), nullable=True),
        sa.Column('cer_enc', sa.Text(), nullable=False),
        sa.Column('key_enc', sa.Text(), nullable=False),
        sa.Column('pwd_enc', sa.Text(), nullable=False),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sat_credentials_id', 'sat_credentials', ['id'])

    op.create_table('sat_download_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('credential_id', sa.Integer(), nullable=False),
        sa.Column('rfc', sa.String(13), nullable=False),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('sat_request_id', sa.String(50), nullable=True),
        sa.Column('date_from', sa.Date(), nullable=False),
        sa.Column('date_to', sa.Date(), nullable=False),
        sa.Column('tipo_comprobante', sa.String(1), nullable=True),
        sa.Column('tipo_solicitud', sa.String(10), nullable=True),
        sa.Column('total_cfdi', sa.Integer(), nullable=True),
        sa.Column('packages_total', sa.Integer(), nullable=True),
        sa.Column('packages_downloaded', sa.Integer(), nullable=True),
        sa.Column('error_msg', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['credential_id'], ['sat_credentials.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sat_download_jobs_id', 'sat_download_jobs', ['id'])

    op.create_table('cfdi_downloaded',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('uuid', sa.String(36), nullable=False),
        sa.Column('rfc_emisor', sa.String(13), nullable=True),
        sa.Column('nombre_emisor', sa.String(300), nullable=True),
        sa.Column('rfc_receptor', sa.String(13), nullable=True),
        sa.Column('nombre_receptor', sa.String(300), nullable=True),
        sa.Column('total', sa.Numeric(15, 2), nullable=True),
        sa.Column('subtotal', sa.Numeric(15, 2), nullable=True),
        sa.Column('impuestos_trasladados', sa.Numeric(15, 2), nullable=True),
        sa.Column('fecha_emision', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_timbrado', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tipo_comprobante', sa.String(1), nullable=True),
        sa.Column('metodo_pago', sa.String(3), nullable=True),
        sa.Column('forma_pago', sa.String(2), nullable=True),
        sa.Column('moneda', sa.String(3), nullable=True),
        sa.Column('serie', sa.String(25), nullable=True),
        sa.Column('folio', sa.String(40), nullable=True),
        sa.Column('xml_data', sa.Text(), nullable=True),
        sa.Column('estatus', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['job_id'], ['sat_download_jobs.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cfdi_downloaded_id', 'cfdi_downloaded', ['id'])
    op.create_index('ix_cfdi_downloaded_uuid', 'cfdi_downloaded', ['uuid'], unique=True)
    op.create_index('ix_cfdi_downloaded_rfc_emisor', 'cfdi_downloaded', ['rfc_emisor'])
    op.create_index('ix_cfdi_downloaded_rfc_receptor', 'cfdi_downloaded', ['rfc_receptor'])


def downgrade():
    op.drop_table('cfdi_downloaded')
    op.drop_table('sat_download_jobs')
    op.drop_table('sat_credentials')
