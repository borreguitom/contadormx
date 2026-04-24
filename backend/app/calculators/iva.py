"""
IVA — Ley del Impuesto al Valor Agregado.
Art. 1 LIVA (actos gravados), Art. 5 LIVA (acreditamiento),
Art. 2-A LIVA (tasa 0%), Art. 15-18 LIVA (exenciones).
"""
from dataclasses import dataclass, field


@dataclass
class ResultadoIVA:
    periodo: str
    iva_trasladado_16: float
    iva_trasladado_0: float
    iva_acreditable_16: float
    iva_acreditable_0: float
    iva_a_cargo: float
    iva_a_favor: float
    saldo_favor_anterior: float
    diferencia_final: float
    desglose: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "periodo": self.periodo,
            "fundamento": "Art. 1, 4, 5 LIVA",
            "iva_trasladado": {
                "tasa_16_pct": self.iva_trasladado_16,
                "tasa_0_pct": self.iva_trasladado_0,
                "total": round(self.iva_trasladado_16 + self.iva_trasladado_0, 2),
            },
            "iva_acreditable": {
                "tasa_16_pct": self.iva_acreditable_16,
                "tasa_0_pct": self.iva_acreditable_0,
                "total": round(self.iva_acreditable_16 + self.iva_acreditable_0, 2),
            },
            "saldo_favor_anterior": self.saldo_favor_anterior,
            "iva_a_cargo": self.iva_a_cargo,
            "iva_a_favor": self.iva_a_favor,
            "resultado_final": (
                f"IVA a CARGO: ${self.iva_a_cargo:,.2f}"
                if self.iva_a_cargo > 0
                else f"IVA a FAVOR: ${self.iva_a_favor:,.2f}"
            ),
            "desglose": self.desglose,
        }


def calcular_iva(
    ventas_16: float = 0.0,
    ventas_0: float = 0.0,
    ventas_exentas: float = 0.0,
    compras_16_acreditables: float = 0.0,
    compras_0_acreditables: float = 0.0,
    compras_exentas: float = 0.0,
    saldo_favor_anterior: float = 0.0,
    periodo: str = "mensual",
) -> dict:
    """
    Determina IVA a cargo o a favor en una declaración mensual/anual.
    El IVA de compras exentas NO es acreditable (Art. 5 LIVA).
    La proporcionalidad aplica cuando hay actos mixtos (Art. 5-C LIVA).
    """
    iva_trasladado_16 = round(ventas_16 * 0.16, 2)
    iva_trasladado_0 = 0.0
    iva_acreditable_16 = round(compras_16_acreditables * 0.16, 2)
    iva_acreditable_0 = 0.0

    total_trasladado = iva_trasladado_16
    total_acreditable = iva_acreditable_16

    # Proporcionalidad si hay ventas mixtas (Art. 5-C LIVA)
    total_ventas_gravadas = ventas_16 + ventas_0
    total_ventas_todas = total_ventas_gravadas + ventas_exentas
    proporcion = (
        total_ventas_gravadas / total_ventas_todas if total_ventas_todas > 0 else 1.0
    )

    if ventas_exentas > 0 and compras_exentas > 0:
        iva_acreditable_16 = round(iva_acreditable_16 * proporcion, 2)
        total_acreditable = iva_acreditable_16

    diferencia = round(total_trasladado - total_acreditable - saldo_favor_anterior, 2)
    iva_cargo = max(diferencia, 0.0)
    iva_favor = abs(min(diferencia, 0.0))

    return ResultadoIVA(
        periodo=periodo,
        iva_trasladado_16=iva_trasladado_16,
        iva_trasladado_0=iva_trasladado_0,
        iva_acreditable_16=iva_acreditable_16,
        iva_acreditable_0=iva_acreditable_0,
        iva_a_cargo=round(iva_cargo, 2),
        iva_a_favor=round(iva_favor, 2),
        saldo_favor_anterior=round(saldo_favor_anterior, 2),
        diferencia_final=round(diferencia, 2),
        desglose={
            "ventas_gravadas_16pct": round(ventas_16, 2),
            "ventas_tasa_0pct": round(ventas_0, 2),
            "ventas_exentas": round(ventas_exentas, 2),
            "compras_acreditables": round(compras_16_acreditables, 2),
            "compras_tasa_0": round(compras_0_acreditables, 2),
            "compras_exentas_no_acreditables": round(compras_exentas, 2),
            "proporcion_acreditamiento": round(proporcion, 4) if ventas_exentas > 0 else 1.0,
            "nota_proporcionalidad": (
                "Se aplicó proporcionalidad Art. 5-C LIVA por existir actos exentos."
                if ventas_exentas > 0
                else "No aplica proporcionalidad — todos los actos son gravados."
            ),
        },
    ).to_dict()
