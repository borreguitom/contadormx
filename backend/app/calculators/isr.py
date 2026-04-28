"""
ISR Cálculos — Art. 96 LISR (retención sueldos), Art. 14 LISR (pagos provisionales PM),
Art. 111 LISR (RESICO PF), Art. 196 LISR (RESICO PM).
Tablas vigentes 2026 (Anexo 8 RMF 2026, DOF 28/12/2025).
"""
from dataclasses import dataclass, field
from typing import Optional


# ── Tablas ISR 2025 ──────────────────────────────────────────────────────────

# Tarifa mensual Art. 96 LISR — Anexo 8 RMF 2026 (DOF 28/12/2025)
# (límite_inferior, límite_superior, cuota_fija, tasa_marginal)
TARIFA_ISR_MENSUAL_2026 = [
    (0.01,         844.59,         0.00,         0.0192),
    (844.60,       7_168.51,       16.22,        0.0640),
    (7_168.52,     12_598.02,      420.95,       0.1088),
    (12_598.03,    14_644.64,      1_011.68,     0.1600),
    (14_644.65,    17_533.64,      1_339.14,     0.1792),
    (17_533.65,    35_362.83,      1_856.84,     0.2136),
    (35_362.84,    55_736.68,      5_665.16,     0.2352),
    (55_736.69,    106_410.50,     10_457.09,    0.3000),
    (106_410.51,   141_880.66,     25_659.23,    0.3200),
    (141_880.67,   425_641.99,     37_009.69,    0.3400),
    (425_642.00,   float("inf"),   133_488.54,   0.3500),
]
TARIFA_ISR_MENSUAL_2025 = TARIFA_ISR_MENSUAL_2026  # alias backward-compat

# Tarifa anual Art. 152 LISR — Anexo 8 RMF 2026 (DOF 28/12/2025)
TARIFA_ISR_ANUAL_2026 = [
    (0.01,           10_135.11,       0.00,          0.0192),
    (10_135.12,      86_022.11,       194.59,        0.0640),
    (86_022.12,      151_176.19,      5_051.37,      0.1088),
    (151_176.20,     175_735.66,      12_140.13,     0.1600),
    (175_735.67,     210_403.69,      16_069.64,     0.1792),
    (210_403.70,     424_353.97,      22_282.14,     0.2136),
    (424_353.98,     668_840.14,      67_981.92,     0.2352),
    (668_840.15,     1_276_925.98,    125_485.07,    0.3000),
    (1_276_925.99,   1_702_567.97,    307_910.81,    0.3200),
    (1_702_567.98,   5_107_703.92,    444_116.23,    0.3400),
    (5_107_703.93,   float("inf"),    1_601_862.46,  0.3500),
]
TARIFA_ISR_ANUAL_2025 = TARIFA_ISR_ANUAL_2026  # alias backward-compat

# Subsidio al empleo mensual 2026 (DOF 31/12/2025)
# Reforma 2026: monto fijo $536.21 para ingresos ≤ $11,492.66 (15.59% UMA mensual 2025)
SUBSIDIO_EMPLEO_MENSUAL = [
    (0.01,       11_492.66,    536.21),
    (11_492.67,  float("inf"), 0.00),
]

# Tasa RESICO PF (Art. 113-E LISR) — sobre ingresos cobrados mensuales
RESICO_PF_TASAS = [
    (0.01,        25_000.00, 0.01),
    (25_000.01,   50_000.00, 0.011),
    (50_000.01,   83_333.33, 0.013),
    (83_333.34,   208_333.33, 0.015),
    (208_333.34,  3_500_000.00 / 12, 0.02),
]

# Coeficiente de utilidad por actividad (Art. 14 LISR) — si no tiene declaración anterior
COEFICIENTES_UTILIDAD_DEFAULT = {
    "comercio": 0.20,
    "industria": 0.20,
    "servicios": 0.45,
    "agricultura": 0.20,
    "transporte": 0.15,
    "construccion": 0.20,
    "mineria": 0.25,
    "default": 0.20,
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _aplicar_tarifa(base: float, tarifa: list) -> dict:
    for li, ls, cuota, tasa in tarifa:
        if li <= base <= ls:
            excedente = base - li + 0.01
            impuesto = cuota + excedente * tasa
            return {
                "limite_inferior": li,
                "cuota_fija": round(cuota, 2),
                "excedente": round(excedente, 2),
                "tasa_marginal": tasa,
                "impuesto": round(max(impuesto, 0), 2),
            }
    return {"impuesto": 0.0, "limite_inferior": 0, "cuota_fija": 0, "excedente": 0, "tasa_marginal": 0}


def _subsidio_empleo(ingreso: float) -> float:
    for li, ls, subsidio in SUBSIDIO_EMPLEO_MENSUAL:
        if li <= ingreso <= ls:
            return subsidio
    return 0.0


# ── Cálculo ISR PF ────────────────────────────────────────────────────────────

@dataclass
class ResultadoISR_PF:
    regimen: str
    periodo: str
    fundamento: str
    ingresos_gravables: float
    base_gravable: float
    isr_determinado: float
    subsidio_al_empleo: float
    isr_a_retener: float
    tasa_efectiva: float
    desglose: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "regimen": self.regimen,
            "periodo": self.periodo,
            "fundamento": self.fundamento,
            "ingresos_gravables": self.ingresos_gravables,
            "base_gravable": self.base_gravable,
            "isr_determinado": self.isr_determinado,
            "subsidio_al_empleo": self.subsidio_al_empleo,
            "isr_a_retener": self.isr_a_retener,
            "tasa_efectiva_pct": round(self.tasa_efectiva * 100, 2),
            "desglose": self.desglose,
        }


def calcular_isr_pf(
    ingresos_mensuales: float,
    regimen: str = "sueldos",
    deducciones_mensuales: float = 0.0,
    periodo: str = "mensual",
) -> dict:
    """
    Calcula ISR para personas físicas según régimen.
    regimen: sueldos | honorarios | arrendamiento | actividades_empresariales | resico_pf
    periodo: mensual | anual
    """
    regimen = regimen.lower().replace(" ", "_").replace("-", "_")

    if regimen in ("sueldos", "salarios", "sueldos_y_salarios"):
        return _isr_sueldos(ingresos_mensuales, periodo)
    elif regimen in ("honorarios", "actividades_empresariales", "actividad_empresarial"):
        return _isr_actividades_empresariales(ingresos_mensuales, deducciones_mensuales, periodo)
    elif regimen == "arrendamiento":
        return _isr_arrendamiento(ingresos_mensuales, periodo)
    elif regimen in ("resico_pf", "resico", "simplificado_confianza"):
        return _isr_resico_pf(ingresos_mensuales, periodo)
    else:
        return _isr_sueldos(ingresos_mensuales, periodo)


def _isr_sueldos(ingresos: float, periodo: str) -> dict:
    """Art. 96 LISR — retención mensual sueldos y salarios."""
    if periodo == "anual":
        tarifa = TARIFA_ISR_ANUAL_2026
        base = ingresos
        subsidio = 0.0
        fundamento = "Art. 152 LISR"
    else:
        tarifa = TARIFA_ISR_MENSUAL_2026
        base = ingresos
        subsidio = _subsidio_empleo(ingresos)
        fundamento = "Art. 96 LISR"

    resultado_tarifa = _aplicar_tarifa(base, tarifa)
    isr_det = resultado_tarifa["impuesto"]
    isr_retener = max(isr_det - subsidio, 0.0)

    return ResultadoISR_PF(
        regimen="Sueldos y Salarios",
        periodo=periodo,
        fundamento=fundamento,
        ingresos_gravables=round(ingresos, 2),
        base_gravable=round(base, 2),
        isr_determinado=round(isr_det, 2),
        subsidio_al_empleo=round(subsidio, 2),
        isr_a_retener=round(isr_retener, 2),
        tasa_efectiva=round(isr_retener / ingresos, 4) if ingresos > 0 else 0,
        desglose=resultado_tarifa,
    ).to_dict()


def _isr_actividades_empresariales(ingresos: float, deducciones: float, periodo: str) -> dict:
    """Art. 106 LISR — pago provisional actividades empresariales y honorarios."""
    utilidad = max(ingresos - deducciones, 0.0)
    if periodo == "anual":
        tarifa = TARIFA_ISR_ANUAL_2026
        fundamento = "Art. 152 LISR"
    else:
        tarifa = TARIFA_ISR_MENSUAL_2026
        fundamento = "Art. 106 LISR"

    resultado_tarifa = _aplicar_tarifa(utilidad, tarifa)
    isr_det = resultado_tarifa["impuesto"]

    return ResultadoISR_PF(
        regimen="Actividades Empresariales / Honorarios",
        periodo=periodo,
        fundamento=fundamento,
        ingresos_gravables=round(ingresos, 2),
        base_gravable=round(utilidad, 2),
        isr_determinado=round(isr_det, 2),
        subsidio_al_empleo=0.0,
        isr_a_retener=round(isr_det, 2),
        tasa_efectiva=round(isr_det / ingresos, 4) if ingresos > 0 else 0,
        desglose={**resultado_tarifa, "deducciones_autorizadas": round(deducciones, 2)},
    ).to_dict()


def _isr_arrendamiento(ingresos: float, periodo: str) -> dict:
    """Art. 115 LISR — arrendamiento. Deducción opcional 35% ciega."""
    deduccion_ciega = ingresos * 0.35
    base = ingresos - deduccion_ciega
    if periodo == "anual":
        tarifa = TARIFA_ISR_ANUAL_2026
        fundamento = "Art. 152 LISR"
    else:
        tarifa = TARIFA_ISR_MENSUAL_2026
        fundamento = "Art. 116 LISR"

    resultado_tarifa = _aplicar_tarifa(base, tarifa)
    isr_det = resultado_tarifa["impuesto"]

    return ResultadoISR_PF(
        regimen="Arrendamiento",
        periodo=periodo,
        fundamento=fundamento,
        ingresos_gravables=round(ingresos, 2),
        base_gravable=round(base, 2),
        isr_determinado=round(isr_det, 2),
        subsidio_al_empleo=0.0,
        isr_a_retener=round(isr_det, 2),
        tasa_efectiva=round(isr_det / ingresos, 4) if ingresos > 0 else 0,
        desglose={
            **resultado_tarifa,
            "deduccion_ciega_35pct": round(deduccion_ciega, 2),
            "nota": "Deducción opcional Art. 115 LISR. Si tiene gastos reales mayores al 35%, conviene deducir los reales.",
        },
    ).to_dict()


def _isr_resico_pf(ingresos: float, periodo: str) -> dict:
    """Art. 113-E LISR — RESICO PF. Tasa sobre ingresos cobrados."""
    tasa = 0.025
    for li, ls, t in RESICO_PF_TASAS:
        if li <= ingresos <= ls:
            tasa = t
            break
    isr = round(ingresos * tasa, 2)

    return ResultadoISR_PF(
        regimen="RESICO PF",
        periodo=periodo,
        fundamento="Art. 113-E LISR",
        ingresos_gravables=round(ingresos, 2),
        base_gravable=round(ingresos, 2),
        isr_determinado=isr,
        subsidio_al_empleo=0.0,
        isr_a_retener=isr,
        tasa_efectiva=tasa,
        desglose={
            "tasa_aplicada_pct": round(tasa * 100, 2),
            "nota": "RESICO PF — tasa sobre ingresos cobrados sin deducciones. Límite $3,500,000/año.",
        },
    ).to_dict()


# ── Cálculo ISR PM ────────────────────────────────────────────────────────────

def calcular_isr_pm(
    ingresos_acumulados: float,
    coeficiente_utilidad: float,
    pagos_provisionales_previos: float = 0.0,
    retenciones: float = 0.0,
    mes: int = 1,
    regimen: str = "general",
) -> dict:
    """
    Art. 14 LISR — pago provisional ISR personas morales régimen general.
    Art. 196 LISR — RESICO PM (1% sobre ingresos).
    """
    if regimen in ("resico_pm", "resico"):
        return _isr_resico_pm(ingresos_acumulados, pagos_provisionales_previos, mes)

    utilidad_fiscal_estimada = ingresos_acumulados * coeficiente_utilidad

    # Tarifa mensual proporcional al número de meses transcurridos
    resultado_tarifa = _aplicar_tarifa(utilidad_fiscal_estimada / mes, TARIFA_ISR_MENSUAL_2026)
    isr_mensual = resultado_tarifa["impuesto"]
    isr_acumulado = isr_mensual * mes

    isr_cargo = max(isr_acumulado - pagos_provisionales_previos - retenciones, 0.0)

    return {
        "regimen": "Personas Morales Régimen General",
        "mes": mes,
        "fundamento": "Art. 14 LISR",
        "ingresos_acumulados": round(ingresos_acumulados, 2),
        "coeficiente_utilidad": coeficiente_utilidad,
        "utilidad_fiscal_estimada": round(utilidad_fiscal_estimada, 2),
        "isr_acumulado_determinado": round(isr_acumulado, 2),
        "pagos_provisionales_previos": round(pagos_provisionales_previos, 2),
        "retenciones_acreditables": round(retenciones, 2),
        "pago_provisional_a_enterar": round(isr_cargo, 2),
        "tasa_isr_pm": 0.30,
        "nota": "Tasa del 30% aplica sobre utilidad fiscal. Art. 9 LISR.",
    }


def _isr_resico_pm(ingresos: float, pagos_previos: float, mes: int) -> dict:
    """Art. 196 LISR — RESICO PM. 1% sobre ingresos cobrados."""
    isr_acumulado = round(ingresos * 0.01, 2)
    isr_cargo = max(isr_acumulado - pagos_previos, 0.0)

    return {
        "regimen": "RESICO PM",
        "mes": mes,
        "fundamento": "Art. 196 LISR",
        "ingresos_acumulados": round(ingresos, 2),
        "tasa_resico": 0.01,
        "isr_acumulado_determinado": isr_acumulado,
        "pagos_provisionales_previos": round(pagos_previos, 2),
        "pago_provisional_a_enterar": round(isr_cargo, 2),
        "nota": "RESICO PM — 1% sobre ingresos cobrados. Límite $35,000,000/año. Art. 196 LISR.",
    }
