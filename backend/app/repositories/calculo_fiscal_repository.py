"""
Repository: CalculoFiscalRepository
====================================
Capa de acceso a datos para auditoría de cálculos fiscales.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Any
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.calculo_fiscal import CalculoFiscal


class CalculoFiscalRepository:
    """Repository para operaciones sobre la tabla calculos_fiscales."""

    def __init__(self, db: Session):
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # CREATE
    # ──────────────────────────────────────────────────────────────────

    def crear(
        self,
        usuario_id: int,
        tipo_calculo: str,
        ejercicio_fiscal: int,
        parametros_entrada: dict[str, Any],
        resultado: dict[str, Any],
        *,
        cliente_id: Optional[int] = None,
        subtipo: Optional[str] = None,
        periodo: Optional[str] = None,
        mes: Optional[int] = None,
        rfc_contribuyente: Optional[str] = None,
        rfc_empleador: Optional[str] = None,
        nombre_contribuyente: Optional[str] = None,
        ip_origen: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        notas: Optional[str] = None,
    ) -> CalculoFiscal:
        """Registra un nuevo cálculo en la auditoría."""

        # Extraer monto principal del resultado según tipo
        monto_principal = self._extraer_monto_principal(tipo_calculo, resultado)

        # Detectar advertencias
        advertencias = resultado.get("advertencias", []) if isinstance(resultado, dict) else []
        tiene_advertencias = bool(advertencias)

        # Fundamento legal
        fundamento = resultado.get("fundamento_legal") or resultado.get("fundamento", [])
        if isinstance(fundamento, str):
            fundamento = [fundamento]

        nuevo = CalculoFiscal(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            tipo_calculo=tipo_calculo,
            subtipo=subtipo,
            ejercicio_fiscal=ejercicio_fiscal,
            periodo=periodo,
            mes=mes,
            rfc_contribuyente=rfc_contribuyente,
            rfc_empleador=rfc_empleador,
            nombre_contribuyente=nombre_contribuyente,
            parametros_entrada=parametros_entrada,
            resultado=resultado,
            fundamento_legal=fundamento,
            monto_principal=monto_principal,
            tiene_advertencias=tiene_advertencias,
            ip_origen=ip_origen,
            user_agent=user_agent,
            request_id=request_id,
            notas=notas,
        )
        self.db.add(nuevo)
        self.db.flush()
        return nuevo

    @staticmethod
    def _extraer_monto_principal(tipo: str, resultado: dict) -> Optional[float]:
        """Extrae el monto más representativo según el tipo de cálculo."""
        if not isinstance(resultado, dict):
            return None

        # Estructura RespuestaCalculo: { datos: {...} }
        datos = resultado.get("datos", resultado)
        if not isinstance(datos, dict):
            return None

        mapeo = {
            "isr_pf": "isr_a_cargo",
            "isr_pm": "pago_provisional_a_enterar",
            "iva": "iva_a_cargo",
            "ieps": "ieps_calculado",
            "imss": "costo_total_empresa_mensual",
            "nomina": "neto_a_pagar",
            "finiquito": "neto_a_pagar",
        }
        clave = mapeo.get(tipo)
        if clave and clave in datos:
            try:
                return float(datos[clave])
            except (TypeError, ValueError):
                return None
        return None

    # ──────────────────────────────────────────────────────────────────
    # READ
    # ──────────────────────────────────────────────────────────────────

    def obtener_por_id(self, calculo_id: int) -> Optional[CalculoFiscal]:
        return self.db.get(CalculoFiscal, calculo_id)

    def obtener_por_uuid(self, uuid_str: str) -> Optional[CalculoFiscal]:
        stmt = select(CalculoFiscal).where(CalculoFiscal.uuid == uuid_str)
        return self.db.execute(stmt).scalar_one_or_none()

    def listar_por_cliente(
        self,
        cliente_id: int,
        *,
        tipo_calculo: Optional[str] = None,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CalculoFiscal]:
        """Cálculos de un cliente con filtros opcionales."""
        stmt = select(CalculoFiscal).where(CalculoFiscal.cliente_id == cliente_id)

        if tipo_calculo:
            stmt = stmt.where(CalculoFiscal.tipo_calculo == tipo_calculo)
        if desde:
            stmt = stmt.where(CalculoFiscal.creado_en >= desde)
        if hasta:
            stmt = stmt.where(CalculoFiscal.creado_en <= hasta)

        stmt = stmt.order_by(desc(CalculoFiscal.creado_en)).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())

    def listar_por_usuario(
        self,
        usuario_id: int,
        *,
        ultimos_dias: int = 30,
        limit: int = 50,
    ) -> list[CalculoFiscal]:
        desde = datetime.utcnow() - timedelta(days=ultimos_dias)
        stmt = (
            select(CalculoFiscal)
            .where(CalculoFiscal.usuario_id == usuario_id)
            .where(CalculoFiscal.creado_en >= desde)
            .order_by(desc(CalculoFiscal.creado_en))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def buscar_por_rfc(
        self,
        rfc: str,
        *,
        ejercicio: Optional[int] = None,
        limit: int = 50,
    ) -> list[CalculoFiscal]:
        stmt = select(CalculoFiscal).where(CalculoFiscal.rfc_contribuyente == rfc.upper())
        if ejercicio:
            stmt = stmt.where(CalculoFiscal.ejercicio_fiscal == ejercicio)
        stmt = stmt.order_by(desc(CalculoFiscal.creado_en)).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # AGREGACIONES (para dashboards)
    # ──────────────────────────────────────────────────────────────────

    def estadisticas_por_tipo(
        self,
        *,
        cliente_id: Optional[int] = None,
        ejercicio: Optional[int] = None,
    ) -> list[dict]:
        """Cuenta de cálculos por tipo. Útil para dashboard."""
        stmt = select(
            CalculoFiscal.tipo_calculo,
            func.count(CalculoFiscal.id).label("total"),
            func.sum(CalculoFiscal.monto_principal).label("monto_total"),
        )

        if cliente_id:
            stmt = stmt.where(CalculoFiscal.cliente_id == cliente_id)
        if ejercicio:
            stmt = stmt.where(CalculoFiscal.ejercicio_fiscal == ejercicio)

        stmt = stmt.group_by(CalculoFiscal.tipo_calculo)

        return [
            {
                "tipo": row.tipo_calculo,
                "total": row.total,
                "monto_total": float(row.monto_total) if row.monto_total else 0,
            }
            for row in self.db.execute(stmt).all()
        ]

    def calculos_recientes_global(self, limit: int = 10) -> list[CalculoFiscal]:
        """Últimos cálculos del sistema (para admin)."""
        stmt = (
            select(CalculoFiscal)
            .order_by(desc(CalculoFiscal.creado_en))
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # ARCHIVAR (no borrar — preserva auditoría)
    # ──────────────────────────────────────────────────────────────────

    def archivar(self, calculo_id: int) -> bool:
        calc = self.obtener_por_id(calculo_id)
        if not calc:
            return False
        calc.estado = "archivado"
        self.db.flush()
        return True
