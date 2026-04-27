"""
Modelo SQLAlchemy: CalculoFiscal
=================================
Representa un cálculo fiscal auditado.

Uso:
    from app.models.calculo_fiscal import CalculoFiscal
    nuevo = CalculoFiscal(
        usuario_id=user.id,
        tipo_calculo="nomina",
        ejercicio_fiscal=2025,
        parametros_entrada={...},
        resultado={...},
    )
    db.add(nuevo)
    db.commit()
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional, Any
from sqlalchemy import (
    BigInteger, String, SmallInteger, DateTime, Text, Boolean,
    Numeric, ForeignKey, CheckConstraint, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB, INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base  # ← Ajustar al import real de tu Base


class CalculoFiscal(Base):
    """
    Auditoría de cálculos fiscales realizados en la plataforma.

    Cada registro guarda:
    - Quién (usuario_id, IP, user-agent)
    - Para quién (cliente_id, RFC contribuyente)
    - Qué tipo (ISR, IVA, IEPS, nómina, finiquito)
    - Parámetros completos de entrada
    - Resultado completo
    - Cuándo (timestamp)
    """

    __tablename__ = "calculos_fiscales"

    __table_args__ = (
        CheckConstraint(
            "tipo_calculo IN ('isr_pf','isr_pm','iva','ieps','imss','nomina','finiquito')",
            name="ck_calculos_tipo_valido",
        ),
        CheckConstraint(
            "estado IN ('completado','error','archivado')",
            name="ck_calculos_estado_valido",
        ),
        CheckConstraint(
            "ejercicio_fiscal BETWEEN 2020 AND 2050",
            name="ck_calculos_ejercicio_rango",
        ),
        Index(
            "ix_calculos_cliente_fecha",
            "cliente_id", "creado_en",
            postgresql_where="cliente_id IS NOT NULL",
        ),
        Index("ix_calculos_usuario_fecha", "usuario_id", "creado_en"),
        Index(
            "ix_calculos_rfc_contribuyente",
            "rfc_contribuyente",
            postgresql_where="rfc_contribuyente IS NOT NULL",
        ),
        Index(
            "ix_calculos_tipo_ejercicio",
            "tipo_calculo", "ejercicio_fiscal", "creado_en",
        ),
        Index(
            "ix_calculos_resultado_gin",
            "resultado",
            postgresql_using="gin",
        ),
    )

    # ─── Identificadores ──────────────────────────────────────────────
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
        doc="ID interno autoincremental",
    )
    uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        server_default=func.gen_random_uuid(),
        doc="UUID público para referencia externa",
    )

    # ─── Relaciones ───────────────────────────────────────────────────
    cliente_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        # ForeignKey("clientes.id", ondelete="SET NULL"),  # ← descomenta si tienes la tabla
        nullable=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        BigInteger,
        # ForeignKey("users.id", ondelete="RESTRICT"),  # ← descomenta si tienes la tabla
        nullable=False,
    )

    # ─── Clasificación ────────────────────────────────────────────────
    tipo_calculo: Mapped[str] = mapped_column(String(50), nullable=False)
    subtipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ejercicio_fiscal: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    periodo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mes: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    # ─── Identificatorios fiscales ────────────────────────────────────
    rfc_contribuyente: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    rfc_empleador: Mapped[Optional[str]] = mapped_column(String(13), nullable=True)
    nombre_contribuyente: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # ─── Datos del cálculo ────────────────────────────────────────────
    parametros_entrada: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    resultado: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    fundamento_legal: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    # ─── Indicadores ──────────────────────────────────────────────────
    monto_principal: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    tiene_advertencias: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=func.false(),
    )

    # ─── Auditoría ────────────────────────────────────────────────────
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ip_origen: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # ─── Estado ───────────────────────────────────────────────────────
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="completado",
    )
    notas: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Relaciones ORM (descomentar cuando tengas modelos User/Cliente) ──
    # cliente = relationship("Cliente", back_populates="calculos")
    # usuario = relationship("User", back_populates="calculos")

    def __repr__(self) -> str:
        return (
            f"<CalculoFiscal id={self.id} tipo={self.tipo_calculo} "
            f"rfc={self.rfc_contribuyente} fecha={self.creado_en}>"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "uuid": str(self.uuid),
            "tipo_calculo": self.tipo_calculo,
            "subtipo": self.subtipo,
            "ejercicio_fiscal": self.ejercicio_fiscal,
            "periodo": self.periodo,
            "rfc_contribuyente": self.rfc_contribuyente,
            "nombre_contribuyente": self.nombre_contribuyente,
            "monto_principal": float(self.monto_principal) if self.monto_principal else None,
            "tiene_advertencias": self.tiene_advertencias,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
            "estado": self.estado,
            "resultado": self.resultado,
        }
