"""
IVA — Impuesto al Valor Agregado — Versión mejorada
====================================================
Soporta:
  - Tasa general 16% (Art. 1 LIVA)
  - Tasa frontera 8% (Art. 2 LIVA — estímulo fiscal frontera)
  - Tasa 0% (Art. 2-A LIVA)
  - Actos exentos (Art. 9, 15 LIVA)
  - Acreditamiento proporcional (Art. 5-C LIVA)
  - IVA retenido a terceros (Art. 1-A LIVA)
  - IVA retenido por terceros
  - Saldos a favor compensables o devolución
  - IVA pagado en importaciones (Art. 24 LIVA)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

from app.utils.constantes_fiscales import (
    IVA_TASA_GENERAL,
    IVA_TASA_FRONTERA,
    IVA_TASA_CERO,
    EJERCICIO_FISCAL_VIGENTE,
)


# ══════════════════════════════════════════════════════════════════════════
# Resultado estructurado
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoIVA:
    periodo: str
    ejercicio: int
    fundamento: list[str]

    # IVA Trasladado (cobrado a clientes)
    iva_trasladado_16: float
    iva_trasladado_8: float
    iva_trasladado_0: float
    iva_trasladado_total: float

    # IVA Acreditable (pagado a proveedores)
    iva_acreditable_16: float
    iva_acreditable_8: float
    iva_acreditable_importaciones: float
    iva_acreditable_total: float

    # Retenciones
    iva_retenido_a_terceros: float
    iva_retenido_por_terceros: float

    # Proporcionalidad (Art. 5-C)
    proporcion_acreditamiento: float
    aplica_proporcionalidad: bool

    # Saldos
    saldo_favor_anterior: float
    iva_a_cargo: float
    iva_a_favor: float

    # Detalles
    desglose_ventas: dict
    desglose_compras: dict
    desglose_calculo: dict

    advertencias: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════
# Cálculo principal
# ══════════════════════════════════════════════════════════════════════════

def calcular_iva(
    # Ventas (actos gravados, 0%, exentos)
    ventas_16: float = 0.0,
    ventas_8_frontera: float = 0.0,
    ventas_0: float = 0.0,
    ventas_exentas: float = 0.0,

    # Compras y gastos
    compras_16_acreditables: float = 0.0,
    compras_8_acreditables: float = 0.0,
    compras_0: float = 0.0,
    compras_exentas: float = 0.0,
    iva_pagado_importaciones: float = 0.0,

    # Retenciones
    iva_retenido_a_terceros: float = 0.0,
    iva_retenido_por_terceros: float = 0.0,

    # Saldo previo
    saldo_favor_anterior: float = 0.0,

    # Período
    periodo: str = "mensual",
    aplicar_frontera: bool = False,
) -> dict:
    """
    Calcula IVA mensual o anual.

    El IVA es un impuesto:
    - Trasladado: cobrado a clientes (al vender)
    - Acreditable: pagado a proveedores (al comprar)
    - Por pagar: IVA trasladado − IVA acreditable
    - A favor: si acreditable > trasladado

    Proporcionalidad (Art. 5-C):
    Si tienes ventas exentas, solo puedes acreditar la proporción de IVA
    que corresponde a tus ventas gravadas.
    """
    advertencias = []
    notas = []

    # ═════════════════════════════════════════════════════════════
    # 1. IVA TRASLADADO (cobrado a clientes)
    # ═════════════════════════════════════════════════════════════

    iva_trasladado_16 = round(ventas_16 * IVA_TASA_GENERAL, 2)
    iva_trasladado_8 = round(ventas_8_frontera * IVA_TASA_FRONTERA, 2)
    iva_trasladado_0 = 0.0  # Tasa 0% no genera IVA

    iva_trasladado_total = round(iva_trasladado_16 + iva_trasladado_8, 2)

    # ═════════════════════════════════════════════════════════════
    # 2. IVA ACREDITABLE (pagado a proveedores)
    # ═════════════════════════════════════════════════════════════

    iva_acreditable_16 = round(compras_16_acreditables * IVA_TASA_GENERAL, 2)
    iva_acreditable_8 = round(compras_8_acreditables * IVA_TASA_FRONTERA, 2)
    iva_acreditable_importaciones = round(iva_pagado_importaciones, 2)

    # ═════════════════════════════════════════════════════════════
    # 3. PROPORCIONALIDAD (Art. 5-C LIVA)
    # ═════════════════════════════════════════════════════════════
    # Si tienes ventas exentas, debes prorratear el IVA acreditable.

    total_ventas_gravadas = ventas_16 + ventas_8_frontera + ventas_0
    total_ventas_todas = total_ventas_gravadas + ventas_exentas

    aplica_proporcionalidad = ventas_exentas > 0 and total_ventas_todas > 0

    if aplica_proporcionalidad:
        proporcion = total_ventas_gravadas / total_ventas_todas

        iva_acreditable_16 = round(iva_acreditable_16 * proporcion, 2)
        iva_acreditable_8 = round(iva_acreditable_8 * proporcion, 2)
        iva_acreditable_importaciones = round(iva_acreditable_importaciones * proporcion, 2)

        notas.append(
            f"Proporcionalidad aplicada (Art. 5-C LIVA): {proporcion*100:.2f}% "
            f"({total_ventas_gravadas:,.2f} gravadas / {total_ventas_todas:,.2f} totales)"
        )
    else:
        proporcion = 1.0

    iva_acreditable_total = round(
        iva_acreditable_16 + iva_acreditable_8 + iva_acreditable_importaciones,
        2
    )

    # ═════════════════════════════════════════════════════════════
    # 4. CÁLCULO FINAL
    # ═════════════════════════════════════════════════════════════
    # IVA neto = trasladado − acreditable − retenido por terceros − saldo favor
    # (las retenciones que TÚ hiciste a terceros, las pagas separadamente)

    iva_a_pagar_bruto = iva_trasladado_total - iva_acreditable_total
    iva_neto = iva_a_pagar_bruto - iva_retenido_por_terceros - saldo_favor_anterior

    if iva_neto > 0:
        iva_a_cargo = round(iva_neto, 2)
        iva_a_favor = 0.0
    else:
        iva_a_cargo = 0.0
        iva_a_favor = round(abs(iva_neto), 2)

    # ═════════════════════════════════════════════════════════════
    # 5. ADVERTENCIAS Y NOTAS
    # ═════════════════════════════════════════════════════════════

    if iva_a_favor > 0:
        notas.append(
            f"Tienes saldo a favor de ${iva_a_favor:,.2f}. "
            "Puedes: (1) compensar contra futuros pagos, "
            "(2) solicitar devolución (Art. 22 CFF), "
            "(3) acreditar contra ISR a cargo."
        )

    if iva_retenido_a_terceros > 0:
        notas.append(
            f"⚠️ IVA retenido a terceros (${iva_retenido_a_terceros:,.2f}) "
            "se entera en declaración SEPARADA, no afecta este cálculo."
        )

    if compras_exentas > 0:
        notas.append(
            f"Compras exentas (${compras_exentas:,.2f}) no generan IVA acreditable (Art. 5 LIVA)."
        )

    if aplicar_frontera and ventas_8_frontera == 0 and ventas_16 > 0:
        advertencias.append(
            "Indicaste 'aplicar_frontera=True' pero no registraste ventas al 8%. "
            "Verifica si tu cliente está en zona fronteriza con estímulo."
        )

    # ═════════════════════════════════════════════════════════════
    # 6. CONSTRUIR RESULTADO
    # ═════════════════════════════════════════════════════════════

    return ResultadoIVA(
        periodo=periodo,
        ejercicio=EJERCICIO_FISCAL_VIGENTE,
        fundamento=[
            "Art. 1 LIVA (tasa general 16%)",
            "Art. 2 LIVA (tasa frontera 8%)" if ventas_8_frontera > 0 else "",
            "Art. 2-A LIVA (tasa 0%)" if ventas_0 > 0 else "",
            "Art. 5 LIVA (acreditamiento)",
            "Art. 5-C LIVA (proporcionalidad)" if aplica_proporcionalidad else "",
            "Art. 1-A LIVA (retenciones)" if iva_retenido_a_terceros > 0 or iva_retenido_por_terceros > 0 else "",
        ],

        iva_trasladado_16=iva_trasladado_16,
        iva_trasladado_8=iva_trasladado_8,
        iva_trasladado_0=iva_trasladado_0,
        iva_trasladado_total=iva_trasladado_total,

        iva_acreditable_16=iva_acreditable_16,
        iva_acreditable_8=iva_acreditable_8,
        iva_acreditable_importaciones=iva_acreditable_importaciones,
        iva_acreditable_total=iva_acreditable_total,

        iva_retenido_a_terceros=round(iva_retenido_a_terceros, 2),
        iva_retenido_por_terceros=round(iva_retenido_por_terceros, 2),

        proporcion_acreditamiento=round(proporcion, 4),
        aplica_proporcionalidad=aplica_proporcionalidad,

        saldo_favor_anterior=round(saldo_favor_anterior, 2),
        iva_a_cargo=iva_a_cargo,
        iva_a_favor=iva_a_favor,

        desglose_ventas={
            "tasa_16_pct": {
                "monto_actos": round(ventas_16, 2),
                "iva_trasladado": iva_trasladado_16,
            },
            "tasa_8_pct_frontera": {
                "monto_actos": round(ventas_8_frontera, 2),
                "iva_trasladado": iva_trasladado_8,
            },
            "tasa_0_pct": {
                "monto_actos": round(ventas_0, 2),
                "iva_trasladado": 0.0,
            },
            "exentos": {
                "monto_actos": round(ventas_exentas, 2),
                "iva_trasladado": 0.0,
            },
            "total_ventas": round(ventas_16 + ventas_8_frontera + ventas_0 + ventas_exentas, 2),
        },

        desglose_compras={
            "tasa_16_pct": {
                "monto_actos": round(compras_16_acreditables, 2),
                "iva_acreditable_bruto": round(compras_16_acreditables * IVA_TASA_GENERAL, 2),
                "iva_acreditable_neto": iva_acreditable_16,
            },
            "tasa_8_pct_frontera": {
                "monto_actos": round(compras_8_acreditables, 2),
                "iva_acreditable_bruto": round(compras_8_acreditables * IVA_TASA_FRONTERA, 2),
                "iva_acreditable_neto": iva_acreditable_8,
            },
            "tasa_0_pct": {
                "monto_actos": round(compras_0, 2),
                "iva_acreditable": 0.0,
            },
            "exentos_no_acreditables": {
                "monto_actos": round(compras_exentas, 2),
                "iva_acreditable": 0.0,
            },
            "importaciones": {
                "iva_pagado": round(iva_pagado_importaciones, 2),
                "iva_acreditable_neto": iva_acreditable_importaciones,
            },
            "total_compras": round(
                compras_16_acreditables + compras_8_acreditables +
                compras_0 + compras_exentas, 2
            ),
        },

        desglose_calculo={
            "paso_1_iva_trasladado_total": iva_trasladado_total,
            "paso_2_menos_iva_acreditable": -iva_acreditable_total,
            "paso_3_subtotal": round(iva_a_pagar_bruto, 2),
            "paso_4_menos_retenciones_recibidas": -round(iva_retenido_por_terceros, 2),
            "paso_5_menos_saldo_favor_anterior": -round(saldo_favor_anterior, 2),
            "paso_6_resultado_final": round(iva_neto, 2),
        },

        advertencias=advertencias,
        notas=notas,
    ).to_dict()
