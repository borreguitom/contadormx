"""
ISR Cálculos — Art. 96 LISR (retención sueldos), Art. 14 LISR (pagos provisionales PM),
Art. 111 LISR (RESICO PF), Art. 196 LISR (RESICO PM).
Tablas vigentes 2025 (actualizadas con INPC publicado en RMF 2025).
"""
from dataclasses import dataclass, field
from typing import Optional


# ── Tablas ISR 2025 ──────────────────────────────────────────────────────────

# Tarifa mensual Art. 96 LISR — sueldos y salarios
# (límite_inferior, límite_superior, cuota_fija, tasa_marginal)
TARIFA_ISR_MENSUAL_2025 = [
    (0.01,       746.04,       0.00,       0.0192),
    (746.05,     6_332.05,     14.32,      0.0640),
    (6_332.06,   11_128.01,    371.83,     0.1088),
    (11_128.02,  12_935.82,    893.63,     0.1600),
    (12_935.83,  15_487.71,    1_182.88,   0.1792),
    (15_487.72,  31_236.49,    1_640.18,   0.2136),
    (31_236.50,  49_233.00,    5_004.12,   0.2352),
    (49_233.01,  93_993.90,    9_236.89,   0.3000),
    (93_993.91,  125_325.20,   22_665.17,  0.3200),
    (125_325.21, 375_975.61,   32_691.18,  0.3400),
    (375_975.62, float("inf"), 117_912.32, 0.3500),
]

# Tarifa anual Art. 152 LISR — declaración anual PF
TARIFA_ISR_ANUAL_2025 = [
    (0.01,         8_952.49,       0.00,        0.0192),
    (8_952.50,     75_984.55,      171.88,      0.0640),
    (75_984.56,    133_536.07,     4_461.94,    0.1088),
    (133_536.08,   155_229.80,     10_723.55,   0.1600),
    (155_229.81,   185_852.57,     14_194.54,   0.1792),
    (185_852.58,   374_837.88,     19_682.13,   0.2136),
    (374_837.89,   590_795.99,     60_049.40,   0.2352),
    (590_796.00,   1_127_926.84,   110_842.74,  0.3000),
    (1_127_926.85, 1_503_902.46,   271_981.99,  0.3200),
    (1_503_902.47, 4_511_707.37,   392_294.17,  0.3400),
    (4_511_707.38, float("inf"),   1_414_947.85, 0.3500),
]

# Tabla de subsidio al empleo mensual 2025 (Art. 1.15 Decreto)
SUBSIDIO_EMPLEO_MENSUAL = [
    (0.01,     1_768.96, 407.02),
    (1_768.97, 2_653.38, 406.83),
    (2_653.39, 3_472.84, 406.62),
    (3_472.85, 3_537.87, 392.77),
    (3_537.88, 4_446.15, 382.46),
    (4_446.16, 4_717.18, 354.23),
    (4_717.19, 5_335.42, 324.87),
    (5_335.43, 6_224.67, 294.63),
    (6_224.68, 7_113.90, 253.54),
    (7_113.91, 7_382.33, 217.61),
    (7_382.34, float("inf"), 0.00),
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
        tarifa = TARIFA_ISR_ANUAL_2025
        base = ingresos
        subsidio = 0.0
        fundamento = "Art. 152 LISR"
    else:
        tarifa = TARIFA_ISR_MENSUAL_2025
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
        tarifa = TARIFA_ISR_ANUAL_2025
        fundamento = "Art. 152 LISR"
    else:
        tarifa = TARIFA_ISR_MENSUAL_2025
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
        tarifa = TARIFA_ISR_ANUAL_2025
        fundamento = "Art. 152 LISR"
    else:
        tarifa = TARIFA_ISR_MENSUAL_2025
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
    resultado_tarifa = _aplicar_tarifa(utilidad_fiscal_estimada / mes, TARIFA_ISR_MENSUAL_2025)
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
