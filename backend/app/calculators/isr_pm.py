"""
ISR Personas Morales — Versión mejorada
========================================
Soporta:
  - Pagos provisionales (Art. 14 LISR)
  - Cálculo anual (Art. 9 LISR)
  - RESICO PM (Art. 196 LISR)
  - Deducciones autorizadas detalladas
  - Depreciación de activos
  - Pérdidas fiscales pendientes
  - Acreditamiento de retenciones

Fundamentos:
  - Tasa ISR PM: 30% (Art. 9 LISR)
  - Coeficiente utilidad: declaración previa o estimado (Art. 14)
  - PTU (10%) no es deducible (Art. 28 LISR)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.utils.constantes_fiscales import (
    COEFICIENTES_UTILIDAD_DEFAULT,
    RESICO_PM_TASA,
    RESICO_PM_LIMITE_ANUAL,
    EJERCICIO_FISCAL_VIGENTE,
)


TASA_ISR_PM = 0.30  # Art. 9 LISR


# ══════════════════════════════════════════════════════════════════════════
# Resultados estructurados
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoISRPM:
    regimen: str
    ejercicio: int
    mes: int
    fundamento: list[str]

    ingresos_acumulados: float
    coeficiente_utilidad: float
    utilidad_fiscal_estimada: float

    deducciones_autorizadas: float
    depreciaciones: float
    perdidas_fiscales_amortizadas: float
    base_gravable: float

    isr_acumulado_determinado: float
    pagos_provisionales_previos: float
    retenciones_acreditables: float
    pago_provisional_a_enterar: float

    tasa_aplicada_pct: float

    advertencias: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════
# Cálculo ISR PM Régimen General — Pagos provisionales
# ══════════════════════════════════════════════════════════════════════════

def calcular_isr_pm_provisional(
    ingresos_acumulados: float,
    coeficiente_utilidad: float,
    mes: int,
    *,
    pagos_provisionales_previos: float = 0.0,
    retenciones_acreditables: float = 0.0,
    perdidas_fiscales_pendientes: float = 0.0,
    actividad: str = "default",
) -> dict:
    """
    Art. 14 LISR — Pagos provisionales mensuales ISR personas morales.

    Fórmula:
        Utilidad fiscal estimada = ingresos_acumulados × coeficiente_utilidad
        Base gravable = utilidad - pérdidas fiscales pendientes
        ISR provisional = base × 30% (acumulado)
        A pagar = ISR acumulado − pagos provisionales previos − retenciones
    """
    advertencias = []
    notas = []

    # Validaciones
    if mes < 1 or mes > 12:
        advertencias.append(f"Mes inválido: {mes}. Debe estar entre 1 y 12.")
        mes = max(1, min(mes, 12))

    if coeficiente_utilidad <= 0:
        # Usar coeficiente por actividad
        coef_default = COEFICIENTES_UTILIDAD_DEFAULT.get(
            actividad.lower().replace(" ", "_"),
            COEFICIENTES_UTILIDAD_DEFAULT["default"]
        )
        advertencias.append(
            f"Coeficiente de utilidad no proporcionado. Usando default {coef_default*100:.0f}% "
            f"para actividad '{actividad}'."
        )
        coeficiente_utilidad = coef_default

    if coeficiente_utilidad > 1:
        advertencias.append(
            f"Coeficiente de utilidad sospechosamente alto: {coeficiente_utilidad}. "
            "Verifica que esté en formato decimal (ej: 0.20 para 20%)."
        )

    # Cálculo
    utilidad_fiscal_estimada = ingresos_acumulados * coeficiente_utilidad

    # Amortizar pérdidas fiscales pendientes (hasta el límite de utilidad)
    perdidas_amortizadas = min(perdidas_fiscales_pendientes, utilidad_fiscal_estimada)

    if perdidas_fiscales_pendientes > utilidad_fiscal_estimada:
        notas.append(
            f"Pérdidas fiscales no amortizadas en este pago: "
            f"${perdidas_fiscales_pendientes - perdidas_amortizadas:,.2f} "
            f"(se podrán amortizar en pagos futuros, máximo 10 años Art. 57 LISR)."
        )

    base_gravable = max(utilidad_fiscal_estimada - perdidas_amortizadas, 0)
    isr_acumulado = round(base_gravable * TASA_ISR_PM, 2)

    # ISR a enterar = acumulado − pagos previos − retenciones
    isr_a_enterar = max(
        isr_acumulado - pagos_provisionales_previos - retenciones_acreditables,
        0.0
    )

    # Si retenciones + pagos > ISR acumulado → saldo a favor
    if pagos_provisionales_previos + retenciones_acreditables > isr_acumulado:
        saldo_favor = (pagos_provisionales_previos + retenciones_acreditables) - isr_acumulado
        notas.append(
            f"Saldo a favor: ${saldo_favor:,.2f} "
            f"(podrá compensarse en pagos futuros o solicitar devolución Art. 22 CFF)."
        )

    notas.append(f"Tasa ISR PM régimen general: {TASA_ISR_PM*100:.0f}% (Art. 9 LISR)")
    notas.append(f"Coeficiente de utilidad usado: {coeficiente_utilidad*100:.2f}%")

    return ResultadoISRPM(
        regimen="Personas Morales — Régimen General",
        ejercicio=EJERCICIO_FISCAL_VIGENTE,
        mes=mes,
        fundamento=[
            "Art. 14 LISR (pagos provisionales)",
            "Art. 9 LISR (tasa ISR PM)",
            "Art. 57 LISR (amortización pérdidas)" if perdidas_amortizadas > 0 else "",
        ],
        ingresos_acumulados=round(ingresos_acumulados, 2),
        coeficiente_utilidad=coeficiente_utilidad,
        utilidad_fiscal_estimada=round(utilidad_fiscal_estimada, 2),
        deducciones_autorizadas=0.0,  # Se aplica en cálculo anual
        depreciaciones=0.0,
        perdidas_fiscales_amortizadas=round(perdidas_amortizadas, 2),
        base_gravable=round(base_gravable, 2),
        isr_acumulado_determinado=isr_acumulado,
        pagos_provisionales_previos=round(pagos_provisionales_previos, 2),
        retenciones_acreditables=round(retenciones_acreditables, 2),
        pago_provisional_a_enterar=round(isr_a_enterar, 2),
        tasa_aplicada_pct=round(TASA_ISR_PM * 100, 2),
        advertencias=advertencias,
        notas=notas,
    ).to_dict()


# ══════════════════════════════════════════════════════════════════════════
# Cálculo ISR PM Anual — Declaración anual
# ══════════════════════════════════════════════════════════════════════════

def calcular_isr_pm_anual(
    ingresos_acumulables_anuales: float,
    deducciones_autorizadas: float,
    *,
    depreciaciones: float = 0.0,
    perdidas_fiscales_pendientes: float = 0.0,
    pagos_provisionales_realizados: float = 0.0,
    retenciones_anuales: float = 0.0,
    ptu_pagada: float = 0.0,
) -> dict:
    """
    Art. 9 LISR — Cálculo anual ISR personas morales régimen general.

    Resultado fiscal = Ingresos acumulables − Deducciones autorizadas − Depreciaciones
    Utilidad fiscal = Resultado fiscal − PTU pagada
    Base gravable = Utilidad fiscal − Pérdidas fiscales pendientes (Art. 57 LISR)
    ISR del ejercicio = Base × 30%
    ISR a cargo = ISR del ejercicio − Pagos provisionales − Retenciones
    """
    advertencias = []
    notas = []

    # Resultado fiscal
    resultado_fiscal = ingresos_acumulables_anuales - deducciones_autorizadas - depreciaciones

    # Utilidad fiscal (PTU pagada del ejercicio anterior es deducible Art. 9 LISR)
    utilidad_fiscal = max(resultado_fiscal - ptu_pagada, 0)

    if ptu_pagada > 0:
        notas.append(
            f"PTU pagada del ejercicio anterior deducible: ${ptu_pagada:,.2f} (Art. 9 LISR)"
        )

    # Amortizar pérdidas fiscales (máximo 10 años, actualizadas por INPC)
    perdidas_amortizadas = min(perdidas_fiscales_pendientes, utilidad_fiscal)

    if perdidas_fiscales_pendientes > 0:
        notas.append(
            f"Pérdidas fiscales aplicadas: ${perdidas_amortizadas:,.2f} "
            f"(Art. 57 LISR, vigencia 10 años)"
        )

    base_gravable = max(utilidad_fiscal - perdidas_amortizadas, 0)
    isr_ejercicio = round(base_gravable * TASA_ISR_PM, 2)

    # ISR a cargo o a favor
    diferencia = isr_ejercicio - pagos_provisionales_realizados - retenciones_anuales

    if diferencia > 0:
        isr_cargo = round(diferencia, 2)
        isr_favor = 0.0
        notas.append(f"Diferencia a pagar en declaración anual: ${isr_cargo:,.2f}")
    else:
        isr_cargo = 0.0
        isr_favor = round(abs(diferencia), 2)
        notas.append(f"Saldo a favor: ${isr_favor:,.2f} (compensable o devolución)")

    return {
        "regimen": "Personas Morales — Régimen General (Anual)",
        "ejercicio": EJERCICIO_FISCAL_VIGENTE,
        "fundamento": [
            "Art. 9 LISR (tasa y base)",
            "Art. 25 LISR (deducciones)",
            "Art. 31-37 LISR (depreciaciones)",
            "Art. 57 LISR (pérdidas)",
        ],
        "calculo": {
            "ingresos_acumulables_anuales": round(ingresos_acumulables_anuales, 2),
            "menos_deducciones_autorizadas": round(deducciones_autorizadas, 2),
            "menos_depreciaciones": round(depreciaciones, 2),
            "igual_resultado_fiscal": round(resultado_fiscal, 2),
            "menos_ptu_pagada": round(ptu_pagada, 2),
            "igual_utilidad_fiscal": round(utilidad_fiscal, 2),
            "menos_perdidas_fiscales": round(perdidas_amortizadas, 2),
            "igual_base_gravable": round(base_gravable, 2),
            "tasa_pct": round(TASA_ISR_PM * 100, 2),
            "isr_del_ejercicio": isr_ejercicio,
        },
        "acreditamiento": {
            "pagos_provisionales": round(pagos_provisionales_realizados, 2),
            "retenciones": round(retenciones_anuales, 2),
            "total_acreditable": round(pagos_provisionales_realizados + retenciones_anuales, 2),
        },
        "resultado": {
            "isr_a_cargo": isr_cargo,
            "isr_a_favor": isr_favor,
        },
        "advertencias": advertencias,
        "notas": notas,
    }


# ══════════════════════════════════════════════════════════════════════════
# Cálculo RESICO PM
# ══════════════════════════════════════════════════════════════════════════

def calcular_isr_resico_pm(
    ingresos_acumulados: float,
    *,
    pagos_provisionales_previos: float = 0.0,
    mes: int = 1,
) -> dict:
    """
    Art. 196 LISR — RESICO Personas Morales.
    Tasa única 1% sobre ingresos cobrados.
    Límite anual: $35,000,000.
    """
    advertencias = []

    if ingresos_acumulados > RESICO_PM_LIMITE_ANUAL:
        advertencias.append(
            f"⚠️ Límite RESICO PM superado: ${RESICO_PM_LIMITE_ANUAL:,.2f}. "
            f"Acumulado: ${ingresos_acumulados:,.2f}. "
            "Debe migrar al régimen general."
        )

    isr_acumulado = round(ingresos_acumulados * RESICO_PM_TASA, 2)
    isr_enterar = max(isr_acumulado - pagos_provisionales_previos, 0)

    return {
        "regimen": "RESICO Personas Morales",
        "ejercicio": EJERCICIO_FISCAL_VIGENTE,
        "mes": mes,
        "fundamento": ["Art. 196 LISR", "Art. 198 LISR (requisitos)"],
        "ingresos_acumulados": round(ingresos_acumulados, 2),
        "tasa_resico_pct": round(RESICO_PM_TASA * 100, 2),
        "isr_acumulado": isr_acumulado,
        "pagos_previos": round(pagos_provisionales_previos, 2),
        "pago_provisional_a_enterar": round(isr_enterar, 2),
        "advertencias": advertencias,
        "notas": [
            f"RESICO PM: {RESICO_PM_TASA*100:.0f}% sobre ingresos cobrados.",
            f"Límite anual: ${RESICO_PM_LIMITE_ANUAL:,.2f}",
            "No requiere coeficiente de utilidad ni deducciones.",
            "Al rebasar el límite debe migrar a régimen general.",
        ],
    }


# ══════════════════════════════════════════════════════════════════════════
# Dispatcher principal
# ══════════════════════════════════════════════════════════════════════════

def calcular_isr_pm(
    ingresos_acumulados: float,
    *,
    coeficiente_utilidad: float = 0.20,
    mes: int = 1,
    regimen: str = "general",
    pagos_provisionales_previos: float = 0.0,
    retenciones_acreditables: float = 0.0,
    perdidas_fiscales_pendientes: float = 0.0,
    actividad: str = "default",
    # Para cálculo anual:
    es_calculo_anual: bool = False,
    deducciones_autorizadas_anual: float = 0.0,
    depreciaciones_anual: float = 0.0,
    ptu_pagada: float = 0.0,
) -> dict:
    """
    Dispatcher principal ISR Personas Morales.
    """
    regimen_norm = regimen.lower().replace(" ", "_").replace("-", "_")

    if regimen_norm in ("resico_pm", "resico"):
        return calcular_isr_resico_pm(
            ingresos_acumulados,
            pagos_provisionales_previos=pagos_provisionales_previos,
            mes=mes,
        )

    if es_calculo_anual:
        return calcular_isr_pm_anual(
            ingresos_acumulados,
            deducciones_autorizadas_anual,
            depreciaciones=depreciaciones_anual,
            perdidas_fiscales_pendientes=perdidas_fiscales_pendientes,
            pagos_provisionales_realizados=pagos_provisionales_previos,
            retenciones_anuales=retenciones_acreditables,
            ptu_pagada=ptu_pagada,
        )

    return calcular_isr_pm_provisional(
        ingresos_acumulados,
        coeficiente_utilidad,
        mes,
        pagos_provisionales_previos=pagos_provisionales_previos,
        retenciones_acreditables=retenciones_acreditables,
        perdidas_fiscales_pendientes=perdidas_fiscales_pendientes,
        actividad=actividad,
    )
