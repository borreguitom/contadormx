"""
Cuotas IMSS / INFONAVIT — Versión mejorada
============================================
Desglose completo de cada concepto:
  - Enfermedad y maternidad (cuota fija + excedente + gastos médicos pensionados)
  - Invalidez y vida
  - Riesgo de trabajo
  - Retiro, Cesantía y Vejez (CEAV/RCV)
  - Guarderías
  - INFONAVIT (Art. 29 Ley INFONAVIT)

Mejoras vs versión anterior:
  ✓ Topes correctos (25 UMAs IMSS, 25 UMAs INFONAVIT)
  ✓ SDI calculado con fórmula completa Art. 27 LSS
  ✓ Separación clara: cuota trabajador vs patrón
  ✓ Validación de prima de riesgo según clase
  ✓ Soporta zona fronteriza norte
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.utils.constantes_fiscales import (
    UMA_DIARIA,
    SALARIO_MINIMO_GENERAL,
    SALARIO_MINIMO_ZONA_NORTE,
    TOPE_SBC_25_UMA,
    CUOTAS_IMSS_2026,
    CESANTIA_VEJEZ_TRABAJADOR_2026,
    tasa_cesantia_vejez_patron_2026,
    EJERCICIO_FISCAL_VIGENTE,
)


# ══════════════════════════════════════════════════════════════════════════
# Primas de riesgo por clase (Art. 73 LSS)
# ══════════════════════════════════════════════════════════════════════════

PRIMAS_RIESGO_CLASE = {
    "I":   0.005435,    # Riesgo bajo (oficinas, comercio)
    "II":  0.013065,    # Riesgo medio bajo
    "III": 0.024988,    # Riesgo medio
    "IV":  0.039950,    # Riesgo medio alto
    "V":   0.071875,    # Riesgo alto (construcción, minería)
}


# ══════════════════════════════════════════════════════════════════════════
# Resultado estructurado
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoIMSS:
    ejercicio: int
    fundamento: list[str]

    # SDI
    salario_diario: float
    salario_diario_integrado: float
    sdi_topado_25_uma: float
    sdi_mensual_base: float
    factor_integracion: float

    # Cuotas patronales (desglose por concepto)
    cuotas_patronales: dict
    total_cuota_patronal: float

    # Cuotas trabajador (desglose por concepto)
    cuotas_trabajador: dict
    total_cuota_trabajador: float

    # INFONAVIT
    infonavit: dict

    # Costo total
    costo_total_empresa_mensual: float

    # Información adicional
    prima_riesgo_aplicada: float
    clase_riesgo: str
    zona_norte: bool

    advertencias: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════
# Cálculo SDI desde salario base + prestaciones
# ══════════════════════════════════════════════════════════════════════════

def calcular_sdi_completo(
    salario_diario_base: float,
    *,
    aguinaldo_dias: int = 15,
    prima_vacacional_pct: float = 0.25,
    dias_vacaciones: int = 12,
    prestaciones_adicionales_anuales: float = 0.0,
) -> dict:
    """
    Calcula Salario Diario Integrado según Art. 27 LSS.

    Fórmula:
        Factor de integración = 1 + (días_aguinaldo + (días_vacaciones × prima_vacacional)) / 365
        SDI = salario_base_diario × factor_integración + (prestaciones_adicionales / 365)
    """
    factor_aguinaldo = aguinaldo_dias / 365
    factor_prima_vacacional = (dias_vacaciones * prima_vacacional_pct) / 365

    factor_integracion = 1 + factor_aguinaldo + factor_prima_vacacional

    sdi_por_factor = salario_diario_base * factor_integracion
    sdi_por_prestaciones = prestaciones_adicionales_anuales / 365

    sdi = round(sdi_por_factor + sdi_por_prestaciones, 4)

    return {
        "salario_diario_base": round(salario_diario_base, 2),
        "factor_integracion": round(factor_integracion, 6),
        "factor_aguinaldo": round(factor_aguinaldo, 6),
        "factor_prima_vacacional": round(factor_prima_vacacional, 6),
        "prestaciones_adicionales_diarias": round(sdi_por_prestaciones, 4),
        "sdi_calculado": sdi,
        "fundamento": "Art. 27 LSS",
        "formula": "SDI = SD_base × (1 + aguinaldo/365 + (vacaciones × prima)/365)"
    }


# ══════════════════════════════════════════════════════════════════════════
# Cálculo principal de cuotas
# ══════════════════════════════════════════════════════════════════════════

def calcular_cuotas_imss(
    salario_diario_integrado: float,
    *,
    prima_riesgo_trabajo: float = 0.0054355,
    clase_riesgo: Optional[str] = None,
    zona_norte: bool = False,
    salario_diario_base: Optional[float] = None,
) -> dict:
    """
    Calcula todas las cuotas IMSS + INFONAVIT.

    Conceptos (todos sobre SDI mensual = SDI × 30.4):

    PATRÓN:
      - E&M Cuota fija: 20.4% sobre 3 UMAs mensuales
      - E&M Excedente: 1.1% sobre (SDI − 3 UMAs)
      - E&M Dinero: 0.7% sobre SDI
      - GMP: 1.05% sobre SDI
      - I&V: 1.75% sobre SDI
      - Retiro: 2% sobre SDI
      - C&V: 3.15% sobre SDI
      - Guarderías: 1% sobre SDI
      - INFONAVIT: 5% sobre SDI
      - Riesgo trabajo: % SIPA sobre SDI

    TRABAJADOR:
      - E&M Excedente: 0.4% sobre (SDI − 3 UMAs)
      - E&M Dinero: 0.25% sobre SDI
      - GMP: 0.375% sobre SDI
      - I&V: 0.625% sobre SDI
      - C&V: 1.125% sobre SDI

    Total trabajador típicamente: ~3.275% del SDI mensual
    """
    advertencias = []
    notas = []

    # ═════════════════════════════════════════════════════════════
    # Aplicar tope SBC 25 UMAs (Art. 28 LSS)
    # ═════════════════════════════════════════════════════════════

    sdi_topado = min(salario_diario_integrado, TOPE_SBC_25_UMA)

    if salario_diario_integrado > TOPE_SBC_25_UMA:
        advertencias.append(
            f"SDI topado a 25 UMAs: ${TOPE_SBC_25_UMA:,.2f}/día (Art. 28 LSS). "
            f"SDI real: ${salario_diario_integrado:,.2f}"
        )

    # Validar salario mínimo
    sm = SALARIO_MINIMO_ZONA_NORTE if zona_norte else SALARIO_MINIMO_GENERAL
    if sdi_topado < sm:
        advertencias.append(
            f"⚠️ SDI (${sdi_topado:,.2f}) menor al salario mínimo "
            f"({'zona norte' if zona_norte else 'general'}: ${sm}/día). "
            "El IMSS exige al menos un salario mínimo."
        )

    sdi_mensual = round(sdi_topado * 30.4, 2)
    uma_3_mensual = UMA_DIARIA * 3 * 30.4

    # ═════════════════════════════════════════════════════════════
    # Determinar prima de riesgo
    # ═════════════════════════════════════════════════════════════

    if clase_riesgo and clase_riesgo.upper() in PRIMAS_RIESGO_CLASE:
        prima_aplicada = PRIMAS_RIESGO_CLASE[clase_riesgo.upper()]
        notas.append(
            f"Prima riesgo Clase {clase_riesgo}: {prima_aplicada*100:.4f}% "
            "(promedio de la clase, ajustar según SIPA real)"
        )
    else:
        prima_aplicada = prima_riesgo_trabajo
        clase_riesgo = "personalizada"

    if prima_aplicada > 0.15:
        advertencias.append(
            f"Prima de riesgo demasiado alta: {prima_aplicada*100:.4f}%. "
            "Máximo legal: 15% (Art. 73 LSS)."
        )

    # ═════════════════════════════════════════════════════════════
    # CUOTAS PATRONALES
    # ═════════════════════════════════════════════════════════════

    em = CUOTAS_IMSS_2026["enfermedad_maternidad"]

    # Enfermedad y Maternidad
    em_fija_patron = round(uma_3_mensual * em["fija_patron_3uma"], 2)
    excedente_base = max(sdi_mensual - uma_3_mensual, 0)
    em_excedente_patron = round(excedente_base * em["excedente_patron"], 2)
    em_dinero_patron = round(sdi_mensual * em["dinero_patron"], 2)
    em_gmpm_patron = round(sdi_mensual * em["gmpm_patron"], 2)

    # Invalidez y Vida
    iv_patron = round(sdi_mensual * CUOTAS_IMSS_2026["invalidez_vida"]["patron"], 2)

    # Retiro
    retiro_patron = round(sdi_mensual * CUOTAS_IMSS_2026["retiro"]["patron"], 2)

    # Cesantía y Vejez — tasa progresiva por SBC (Art. 168 BIS LSS, reforma 2026)
    sbc_diario = salario_diario_base if salario_diario_base else salario_diario_integrado
    tasa_cv_patron = tasa_cesantia_vejez_patron_2026(sbc_diario)
    cv_patron = round(sdi_mensual * tasa_cv_patron, 2)

    # Guarderías
    guarderias_patron = round(sdi_mensual * CUOTAS_IMSS_2026["guarderias"]["patron"], 2)

    # Riesgo de trabajo
    riesgo_patron = round(sdi_mensual * prima_aplicada, 2)

    # INFONAVIT
    infonavit_patron = round(sdi_mensual * CUOTAS_IMSS_2026["infonavit"]["patron"], 2)

    total_patron = round(
        em_fija_patron + em_excedente_patron + em_dinero_patron + em_gmpm_patron +
        iv_patron + retiro_patron + cv_patron + guarderias_patron +
        riesgo_patron + infonavit_patron,
        2
    )

    # ═════════════════════════════════════════════════════════════
    # CUOTAS TRABAJADOR
    # ═════════════════════════════════════════════════════════════

    em_excedente_trab = round(excedente_base * em["excedente_trabajador"], 2)
    em_dinero_trab = round(sdi_mensual * em["dinero_trabajador"], 2)
    em_gmpm_trab = round(sdi_mensual * em["gmpm_trabajador"], 2)
    iv_trab = round(sdi_mensual * CUOTAS_IMSS_2026["invalidez_vida"]["trabajador"], 2)
    cv_trab = round(sdi_mensual * CESANTIA_VEJEZ_TRABAJADOR_2026, 2)

    total_trabajador = round(
        em_excedente_trab + em_dinero_trab + em_gmpm_trab + iv_trab + cv_trab,
        2
    )

    # ═════════════════════════════════════════════════════════════
    # CONSTRUIR RESULTADO
    # ═════════════════════════════════════════════════════════════

    cuotas_patronales = {
        "enfermedad_maternidad": {
            "cuota_fija_3uma": {
                "tasa": "20.4% sobre 3 UMAs",
                "base": round(uma_3_mensual, 2),
                "monto": em_fija_patron,
            },
            "excedente": {
                "tasa": "1.1% sobre excedente 3 UMAs",
                "base": round(excedente_base, 2),
                "monto": em_excedente_patron,
            },
            "prestaciones_dinero": {
                "tasa": "0.7% sobre SDI",
                "monto": em_dinero_patron,
            },
            "gastos_medicos_pensionados": {
                "tasa": "1.05% sobre SDI",
                "monto": em_gmpm_patron,
            },
            "subtotal": round(em_fija_patron + em_excedente_patron + em_dinero_patron + em_gmpm_patron, 2),
        },
        "invalidez_y_vida": {
            "tasa": "1.75% sobre SDI",
            "monto": iv_patron,
        },
        "retiro": {
            "tasa": "2% sobre SDI",
            "monto": retiro_patron,
        },
        "cesantia_y_vejez": {
            "tasa": f"{tasa_cv_patron*100:.3f}% sobre SDI (progresiva por SBC, Art. 168 BIS LSS)",
            "monto": cv_patron,
        },
        "guarderias": {
            "tasa": "1% sobre SDI",
            "monto": guarderias_patron,
        },
        "riesgo_trabajo": {
            "tasa": f"{prima_aplicada*100:.4f}% sobre SDI",
            "clase_riesgo": clase_riesgo,
            "monto": riesgo_patron,
        },
        "total_imss_patronal": round(
            em_fija_patron + em_excedente_patron + em_dinero_patron + em_gmpm_patron +
            iv_patron + retiro_patron + cv_patron + guarderias_patron + riesgo_patron,
            2
        ),
    }

    cuotas_trabajador = {
        "enfermedad_maternidad": {
            "excedente": {
                "tasa": "0.4% sobre excedente 3 UMAs",
                "base": round(excedente_base, 2),
                "monto": em_excedente_trab,
            },
            "prestaciones_dinero": {
                "tasa": "0.25% sobre SDI",
                "monto": em_dinero_trab,
            },
            "gastos_medicos_pensionados": {
                "tasa": "0.375% sobre SDI",
                "monto": em_gmpm_trab,
            },
            "subtotal": round(em_excedente_trab + em_dinero_trab + em_gmpm_trab, 2),
        },
        "invalidez_y_vida": {
            "tasa": "0.625% sobre SDI",
            "monto": iv_trab,
        },
        "cesantia_y_vejez": {
            "tasa": "1.125% sobre SDI",
            "monto": cv_trab,
        },
        "total_trabajador": total_trabajador,
        "tasa_efectiva_total": f"{(total_trabajador/sdi_mensual*100):.3f}%" if sdi_mensual > 0 else "0%",
    }

    infonavit = {
        "tasa": "5% sobre SDI",
        "base": sdi_mensual,
        "monto_patronal": infonavit_patron,
        "fundamento": "Art. 29 Ley INFONAVIT",
        "nota": "Es aportación 100% patronal. Si trabajador tiene crédito, también se descuenta.",
    }

    return ResultadoIMSS(
        ejercicio=EJERCICIO_FISCAL_VIGENTE,
        fundamento=[
            "Art. 25-168 Ley del Seguro Social",
            "Art. 27 LSS (integración SDI)",
            "Art. 28 LSS (tope 25 UMAs)",
            "Art. 73 LSS (prima riesgo)",
            "Art. 29 Ley INFONAVIT",
        ],

        salario_diario=round(salario_diario_base or salario_diario_integrado, 2),
        salario_diario_integrado=round(salario_diario_integrado, 4),
        sdi_topado_25_uma=round(sdi_topado, 4),
        sdi_mensual_base=sdi_mensual,
        factor_integracion=round(salario_diario_integrado / (salario_diario_base or salario_diario_integrado), 6) if salario_diario_base else 0,

        cuotas_patronales=cuotas_patronales,
        total_cuota_patronal=cuotas_patronales["total_imss_patronal"],

        cuotas_trabajador=cuotas_trabajador,
        total_cuota_trabajador=total_trabajador,

        infonavit=infonavit,

        costo_total_empresa_mensual=round(total_patron, 2),

        prima_riesgo_aplicada=prima_aplicada,
        clase_riesgo=clase_riesgo,
        zona_norte=zona_norte,

        advertencias=advertencias,
        notas=notas,
    ).to_dict()
