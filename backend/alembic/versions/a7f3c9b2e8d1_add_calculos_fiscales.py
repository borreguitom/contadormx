"""add_calculos_fiscales_audit_table

Crea tabla de auditoría para todos los cálculos fiscales realizados.
Permite trazabilidad completa: quién hizo qué cálculo, cuándo y con qué parámetros.

Revision ID: a7f3c9b2e8d1
Revises: <PREVIA>  # ← AJUSTAR: poner el ID de la última migración existente
Create Date: 2026-04-27 18:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "a7f3c9b2e8d1"
down_revision = None  # ← AJUSTAR: ID de la última migración. Ejemplo: "f1e2d3c4b5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Crea tabla calculos_fiscales con índices y constraint de tipo."""

    # ════════════════════════════════════════════════════════════════════
    # Tabla principal de auditoría
    # ════════════════════════════════════════════════════════════════════
    op.create_table(
        "calculos_fiscales",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
            comment="ID interno autoincremental",
        ),
        sa.Column(
            "uuid",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
            comment="UUID público para referencia externa (logs, frontend)",
        ),

        # ─── Relaciones ───────────────────────────────────────────────
        sa.Column(
            "cliente_id",
            sa.BigInteger(),
            nullable=True,
            comment="Cliente del despacho contable (FK opcional)",
        ),
        sa.Column(
            "usuario_id",
            sa.BigInteger(),
            nullable=False,
            comment="Usuario que ejecutó el cálculo (FK obligatorio)",
        ),

        # ─── Clasificación del cálculo ────────────────────────────────
        sa.Column(
            "tipo_calculo",
            sa.String(50),
            nullable=False,
            comment="Tipo: isr_pf, isr_pm, iva, ieps, imss, nomina, finiquito",
        ),
        sa.Column(
            "subtipo",
            sa.String(50),
            nullable=True,
            comment="Subtipo: regimen ISR, tipo separación finiquito, etc.",
        ),
        sa.Column(
            "ejercicio_fiscal",
            sa.SmallInteger(),
            nullable=False,
            comment="Año fiscal del cálculo (ej: 2025)",
        ),
        sa.Column(
            "periodo",
            sa.String(20),
            nullable=True,
            comment="mensual, quincenal, anual, etc.",
        ),
        sa.Column(
            "mes",
            sa.SmallInteger(),
            nullable=True,
            comment="Mes 1-12 (si aplica)",
        ),

        # ─── Datos identificatorios (denormalizados para búsqueda) ───
        sa.Column(
            "rfc_contribuyente",
            sa.String(13),
            nullable=True,
            comment="RFC del contribuyente/trabajador",
        ),
        sa.Column(
            "rfc_empleador",
            sa.String(13),
            nullable=True,
            comment="RFC del empleador (sólo nómina/finiquito)",
        ),
        sa.Column(
            "nombre_contribuyente",
            sa.String(300),
            nullable=True,
            comment="Nombre completo o razón social",
        ),

        # ─── Datos del cálculo (JSONB para flexibilidad) ─────────────
        sa.Column(
            "parametros_entrada",
            postgresql.JSONB(),
            nullable=False,
            comment="Parámetros enviados al endpoint de cálculo",
        ),
        sa.Column(
            "resultado",
            postgresql.JSONB(),
            nullable=False,
            comment="Resultado completo del cálculo",
        ),
        sa.Column(
            "fundamento_legal",
            postgresql.JSONB(),
            nullable=True,
            comment="Array de artículos legales aplicados",
        ),

        # ─── Indicadores numéricos (para reportes y agregaciones) ────
        sa.Column(
            "monto_principal",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Monto principal: ISR, IVA, neto nómina, total finiquito",
        ),
        sa.Column(
            "tiene_advertencias",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True si el cálculo arrojó advertencias",
        ),

        # ─── Auditoría ────────────────────────────────────────────────
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            comment="Timestamp de creación (UTC)",
        ),
        sa.Column(
            "ip_origen",
            postgresql.INET(),
            nullable=True,
            comment="IP del cliente que originó la petición",
        ),
        sa.Column(
            "user_agent",
            sa.String(500),
            nullable=True,
            comment="User-Agent del navegador/cliente",
        ),
        sa.Column(
            "request_id",
            sa.String(64),
            nullable=True,
            comment="ID único del request HTTP (para correlacionar logs)",
        ),

        # ─── Estado ───────────────────────────────────────────────────
        sa.Column(
            "estado",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'completado'"),
            comment="completado, error, archivado",
        ),
        sa.Column(
            "notas",
            sa.Text(),
            nullable=True,
            comment="Notas opcionales del usuario",
        ),
    )

    # ════════════════════════════════════════════════════════════════════
    # Constraint de tipos válidos
    # ════════════════════════════════════════════════════════════════════
    op.create_check_constraint(
        "ck_calculos_tipo_valido",
        "calculos_fiscales",
        "tipo_calculo IN ('isr_pf','isr_pm','iva','ieps','imss','nomina','finiquito')",
    )
    op.create_check_constraint(
        "ck_calculos_estado_valido",
        "calculos_fiscales",
        "estado IN ('completado','error','archivado')",
    )
    op.create_check_constraint(
        "ck_calculos_ejercicio_rango",
        "calculos_fiscales",
        "ejercicio_fiscal BETWEEN 2020 AND 2050",
    )

    # ════════════════════════════════════════════════════════════════════
    # Foreign keys (descomentar y ajustar nombres si tus tablas existen)
    # ════════════════════════════════════════════════════════════════════
    # op.create_foreign_key(
    #     "fk_calculos_cliente",
    #     "calculos_fiscales", "clientes",
    #     ["cliente_id"], ["id"],
    #     ondelete="SET NULL",
    # )
    # op.create_foreign_key(
    #     "fk_calculos_usuario",
    #     "calculos_fiscales", "users",
    #     ["usuario_id"], ["id"],
    #     ondelete="RESTRICT",
    # )

    # ════════════════════════════════════════════════════════════════════
    # Índices para queries frecuentes
    # ════════════════════════════════════════════════════════════════════

    # Búsqueda por cliente y fecha (dashboard)
    op.create_index(
        "ix_calculos_cliente_fecha",
        "calculos_fiscales",
        ["cliente_id", sa.text("creado_en DESC")],
        postgresql_where=sa.text("cliente_id IS NOT NULL"),
    )

    # Búsqueda por usuario
    op.create_index(
        "ix_calculos_usuario_fecha",
        "calculos_fiscales",
        ["usuario_id", sa.text("creado_en DESC")],
    )

    # Búsqueda por RFC
    op.create_index(
        "ix_calculos_rfc_contribuyente",
        "calculos_fiscales",
        ["rfc_contribuyente"],
        postgresql_where=sa.text("rfc_contribuyente IS NOT NULL"),
    )

    # Búsqueda por tipo y ejercicio (reportes)
    op.create_index(
        "ix_calculos_tipo_ejercicio",
        "calculos_fiscales",
        ["tipo_calculo", "ejercicio_fiscal", sa.text("creado_en DESC")],
    )

    # Índice GIN sobre JSONB para búsquedas dentro del resultado
    op.create_index(
        "ix_calculos_resultado_gin",
        "calculos_fiscales",
        ["resultado"],
        postgresql_using="gin",
    )

    # UUID para lookups externos
    op.create_index(
        "ix_calculos_uuid",
        "calculos_fiscales",
        ["uuid"],
        unique=True,
    )

    # ════════════════════════════════════════════════════════════════════
    # Trigger para actualizar timestamp si se modifica el registro
    # ════════════════════════════════════════════════════════════════════
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_calculos_fiscales_audit()
        RETURNS TRIGGER AS $$
        BEGIN
            -- No permitir modificar parametros_entrada ni resultado después de creado
            IF (OLD.parametros_entrada IS DISTINCT FROM NEW.parametros_entrada
                OR OLD.resultado IS DISTINCT FROM NEW.resultado)
               AND NEW.estado = 'completado' THEN
                RAISE EXCEPTION 'No se pueden modificar los datos de un cálculo completado. Cambie estado a archivado primero.';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER tr_calculos_fiscales_audit
        BEFORE UPDATE ON calculos_fiscales
        FOR EACH ROW
        EXECUTE FUNCTION fn_calculos_fiscales_audit();
        """
    )

    # ════════════════════════════════════════════════════════════════════
    # Comentario en la tabla
    # ════════════════════════════════════════════════════════════════════
    op.execute(
        """
        COMMENT ON TABLE calculos_fiscales IS
        'Auditoría de cálculos fiscales realizados. Cada registro representa un cálculo de ISR, IVA, IEPS, IMSS, nómina o finiquito ejecutado por algún usuario.';
        """
    )


def downgrade() -> None:
    """Reversa la migración."""
    op.execute("DROP TRIGGER IF EXISTS tr_calculos_fiscales_audit ON calculos_fiscales;")
    op.execute("DROP FUNCTION IF EXISTS fn_calculos_fiscales_audit();")
    op.drop_table("calculos_fiscales")
