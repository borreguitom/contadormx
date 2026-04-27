"""
Constantes fiscales mexicanas 2025
===================================
Una sola fuente de verdad para tarifas, UMAs, salarios mínimos, tasas.
Actualizar este archivo anualmente con valores oficiales DOF.

Referencias:
  - DOF UMA 2025: https://www.dof.gob.mx
  - SAT Tarifas: https://www.sat.gob.mx
  - CONASAMI Salario Mínimo: https://www.gob.mx/conasami
"""
from __future__ import annotations
from typing import NamedTuple


# ══════════════════════════════════════════════════════════════════════════
# UMA — Unidad de Medida y Actualización (vigente 1 feb 2025)
# ══════════════════════════════════════════════════════════════════════════

UMA_DIARIA = 113.14
UMA_MENSUAL = round(UMA_DIARIA * 30.4, 2)      # 3,439.46
UMA_ANUAL = round(UMA_DIARIA * 365.25, 2)      # 41,325.84


# ══════════════════════════════════════════════════════════════════════════
# Salario Mínimo (vigente 1 ene 2025)
# ══════════════════════════════════════════════════════════════════════════

SALARIO_MINIMO_GENERAL = 278.80
SALARIO_MINIMO_ZONA_NORTE = 419.88
SALARIO_MINIMO_PROFESIONAL = SALARIO_MINIMO_GENERAL  # base, varía por profesión

# Topes según LFT/LSS
TOPE_INDEMNIZACION_DIARIA = SALARIO_MINIMO_GENERAL * 25     # Art. 50 LFT
TOPE_PRIMA_ANTIGUEDAD = SALARIO_MINIMO_GENERAL * 2          # Art. 162 LFT
TOPE_SBC_25_UMA = UMA_DIARIA * 25                          # Art. 28 LSS


# ══════════════════════════════════════════════════════════════════════════
# Tarifa ISR Mensual 2025 (Art. 96 LISR)
# (límite_inferior, límite_superior, cuota_fija, tasa_marginal)
# ══════════════════════════════════════════════════════════════════════════

class RangoTarifa(NamedTuple):
    limite_inferior: float
    limite_superior: float
    cuota_fija: float
    tasa_marginal: float


TARIFA_ISR_MENSUAL_2025 = [
    RangoTarifa(0.01,        746.04,         0.00,        0.0192),
    RangoTarifa(746.05,      6_332.05,       14.32,       0.0640),
    RangoTarifa(6_332.06,    11_128.01,      371.83,      0.1088),
    RangoTarifa(11_128.02,   12_935.82,      893.63,      0.1600),
    RangoTarifa(12_935.83,   15_487.71,      1_182.88,    0.1792),
    RangoTarifa(15_487.72,   31_236.49,      1_640.18,    0.2136),
    RangoTarifa(31_236.50,   49_233.00,      5_004.12,    0.2352),
    RangoTarifa(49_233.01,   93_993.90,      9_236.89,    0.3000),
    RangoTarifa(93_993.91,   125_325.20,     22_665.17,   0.3200),
    RangoTarifa(125_325.21,  375_975.61,     32_691.18,   0.3400),
    RangoTarifa(375_975.62,  float("inf"),   117_912.32,  0.3500),
]


# ══════════════════════════════════════════════════════════════════════════
# Tarifa ISR Anual 2025 (Art. 152 LISR)
# ══════════════════════════════════════════════════════════════════════════

TARIFA_ISR_ANUAL_2025 = [
    RangoTarifa(0.01,           8_952.49,        0.00,         0.0192),
    RangoTarifa(8_952.50,       75_984.55,       171.88,       0.0640),
    RangoTarifa(75_984.56,      133_536.07,      4_461.94,     0.1088),
    RangoTarifa(133_536.08,     155_229.80,      10_723.55,    0.1600),
    RangoTarifa(155_229.81,     185_852.57,      14_194.54,    0.1792),
    RangoTarifa(185_852.58,     374_837.88,      19_682.13,    0.2136),
    RangoTarifa(374_837.89,     590_795.99,      60_049.40,    0.2352),
    RangoTarifa(590_796.00,     1_127_926.84,    110_842.74,   0.3000),
    RangoTarifa(1_127_926.85,   1_503_902.46,    271_981.99,   0.3200),
    RangoTarifa(1_503_902.47,   4_511_707.37,    392_294.17,   0.3400),
    RangoTarifa(4_511_707.38,   float("inf"),    1_414_947.85, 0.3500),
]


# ══════════════════════════════════════════════════════════════════════════
# Subsidio para el Empleo Mensual 2025 (Decreto Art. 1.15)
# ══════════════════════════════════════════════════════════════════════════

class RangoSubsidio(NamedTuple):
    limite_inferior: float
    limite_superior: float
    subsidio: float


SUBSIDIO_EMPLEO_MENSUAL_2025 = [
    RangoSubsidio(0.01,       1_768.96,      407.02),
    RangoSubsidio(1_768.97,   2_653.38,      406.83),
    RangoSubsidio(2_653.39,   3_472.84,      406.62),
    RangoSubsidio(3_472.85,   3_537.87,      392.77),
    RangoSubsidio(3_537.88,   4_446.15,      382.46),
    RangoSubsidio(4_446.16,   4_717.18,      354.23),
    RangoSubsidio(4_717.19,   5_335.42,      324.87),
    RangoSubsidio(5_335.43,   6_224.67,      294.63),
    RangoSubsidio(6_224.68,   7_113.90,      253.54),
    RangoSubsidio(7_113.91,   7_382.33,      217.61),
    RangoSubsidio(7_382.34,   float("inf"),  0.00),
]


# ══════════════════════════════════════════════════════════════════════════
# RESICO PF (Art. 113-E LISR) — Tasas mensuales sobre ingresos cobrados
# ══════════════════════════════════════════════════════════════════════════

RESICO_PF_TASAS_2025 = [
    RangoTarifa(0.01,            25_000.00,    0.0,  0.0100),
    RangoTarifa(25_000.01,       50_000.00,    0.0,  0.0110),
    RangoTarifa(50_000.01,       83_333.33,    0.0,  0.0150),
    RangoTarifa(83_333.34,       208_333.33,   0.0,  0.0200),
    RangoTarifa(208_333.34,      291_666.66,   0.0,  0.0250),
]

RESICO_PF_LIMITE_ANUAL = 3_500_000.00
RESICO_PM_TASA = 0.01            # Art. 196 LISR
RESICO_PM_LIMITE_ANUAL = 35_000_000.00


# ══════════════════════════════════════════════════════════════════════════
# Tasas IVA (LIVA)
# ══════════════════════════════════════════════════════════════════════════

IVA_TASA_GENERAL = 0.16          # Art. 1 LIVA
IVA_TASA_FRONTERA = 0.08         # Art. 2 LIVA (frontera norte/sur con estímulo)
IVA_TASA_CERO = 0.00             # Art. 2-A LIVA


# ══════════════════════════════════════════════════════════════════════════
# Tasas IEPS 2025 (Art. 2 LIEPS)
# ══════════════════════════════════════════════════════════════════════════

IEPS_CATEGORIAS_2025 = {
    "bebidas_alcoholicas_hasta_14gl": {
        "nombre": "Bebidas alcohólicas ≤14° GL (cerveza, vino)",
        "tasa": 0.265,
        "fundamento": "Art. 2-I-A-1 LIEPS",
    },
    "bebidas_alcoholicas_14_a_20gl": {
        "nombre": "Bebidas alcohólicas >14° y ≤20° GL",
        "tasa": 0.30,
        "fundamento": "Art. 2-I-A-2 LIEPS",
    },
    "bebidas_alcoholicas_mas_20gl": {
        "nombre": "Bebidas alcohólicas >20° GL (destilados)",
        "tasa": 0.53,
        "fundamento": "Art. 2-I-A-3 LIEPS",
    },
    "cerveza": {
        "nombre": "Cerveza",
        "tasa": 0.265,
        "fundamento": "Art. 2-I-A-1 LIEPS",
    },
    "tabacos_labrados": {
        "nombre": "Tabacos labrados (cigarros)",
        "tasa": 1.60,
        "cuota_adicional_cigarro": 0.6166,  # por cigarro
        "fundamento": "Art. 2-I-C LIEPS",
    },
    "puros_artesanales": {
        "nombre": "Puros y otros tabacos labrados hechos a mano",
        "tasa": 0.3091,
        "fundamento": "Art. 2-I-C LIEPS",
    },
    "bebidas_energetizantes": {
        "nombre": "Bebidas energetizantes",
        "tasa": 0.25,
        "fundamento": "Art. 2-I-F LIEPS",
    },
    "bebidas_saborizadas": {
        "nombre": "Bebidas saborizadas con azúcares añadidos",
        "tasa": 0.0,
        "cuota_litro": 1.6451,  # 2025 — actualizado por inflación
        "fundamento": "Art. 2-I-G LIEPS",
    },
    "alimentos_alta_densidad_calorica": {
        "nombre": "Alimentos no básicos con alta densidad calórica (≥275 kcal/100g)",
        "tasa": 0.08,
        "fundamento": "Art. 2-I-J LIEPS",
    },
    "combustibles_automotrices_gasolina_menor_92": {
        "nombre": "Gasolina menor a 92 octanos (Magna)",
        "cuota_litro": 6.4555,
        "fundamento": "Art. 2-I-D LIEPS",
    },
    "combustibles_automotrices_gasolina_mayor_92": {
        "nombre": "Gasolina mayor o igual a 92 octanos (Premium)",
        "cuota_litro": 5.4555,
        "fundamento": "Art. 2-I-D LIEPS",
    },
    "combustibles_diesel": {
        "nombre": "Diésel",
        "cuota_litro": 7.0978,
        "fundamento": "Art. 2-I-D LIEPS",
    },
    "plaguicidas_categoria_1_2": {
        "nombre": "Plaguicidas categoría 1 y 2 toxicidad",
        "tasa": 0.09,
        "fundamento": "Art. 2-I-I LIEPS",
    },
    "plaguicidas_categoria_3": {
        "nombre": "Plaguicidas categoría 3 toxicidad",
        "tasa": 0.07,
        "fundamento": "Art. 2-I-I LIEPS",
    },
    "plaguicidas_categoria_4": {
        "nombre": "Plaguicidas categoría 4 toxicidad",
        "tasa": 0.06,
        "fundamento": "Art. 2-I-I LIEPS",
    },
    "juegos_apuestas": {
        "nombre": "Juegos con apuestas y sorteos",
        "tasa": 0.30,
        "fundamento": "Art. 2-II-B LIEPS",
    },
    "redes_telecomunicaciones": {
        "nombre": "Redes públicas de telecomunicaciones",
        "tasa": 0.03,
        "fundamento": "Art. 2-C LIEPS",
    },
}


# ══════════════════════════════════════════════════════════════════════════
# Cuotas IMSS 2025 (Ley del Seguro Social)
# ══════════════════════════════════════════════════════════════════════════

CUOTAS_IMSS_2025 = {
    "enfermedad_maternidad": {
        "fija_patron_3uma": 0.204,         # 20.4% sobre 3 UMAs
        "excedente_patron": 0.011,
        "excedente_trabajador": 0.004,
        "dinero_patron": 0.007,
        "dinero_trabajador": 0.0025,
        "gmpm_patron": 0.0105,
        "gmpm_trabajador": 0.00375,
    },
    "invalidez_vida": {
        "patron": 0.0175,
        "trabajador": 0.00625,
    },
    "retiro": {
        "patron": 0.02,
        "trabajador": 0.0,
    },
    "cesantia_vejez": {
        "patron": 0.0315,                  # 2025 (sube a 11.875% en 2030)
        "trabajador": 0.01125,
    },
    "guarderias": {
        "patron": 0.01,
        "trabajador": 0.0,
    },
    "infonavit": {
        "patron": 0.05,                    # Art. 29 Ley INFONAVIT
        "trabajador": 0.0,
    },
    "riesgo_trabajo_promedio": 0.0054355,  # Promedio nacional, varía por SIPA
}


# ══════════════════════════════════════════════════════════════════════════
# Coeficientes de utilidad por actividad (Art. 14 LISR)
# Para empresas sin declaración anterior (estimados)
# ══════════════════════════════════════════════════════════════════════════

COEFICIENTES_UTILIDAD_DEFAULT = {
    "comercio": 0.20,
    "industria": 0.20,
    "servicios": 0.45,
    "agricultura_ganaderia_pesca": 0.20,
    "transporte": 0.15,
    "construccion": 0.20,
    "mineria": 0.25,
    "default": 0.20,
}


# ══════════════════════════════════════════════════════════════════════════
# Deducciones personales 2025 (Art. 151 LISR)
# ══════════════════════════════════════════════════════════════════════════

# Tope global: 5 UMAs anuales o 15% de ingresos (lo que resulte menor)
TOPE_DEDUCCIONES_PERSONALES_UMA = UMA_ANUAL * 5
TOPE_DEDUCCIONES_PERSONALES_PCT = 0.15


# ══════════════════════════════════════════════════════════════════════════
# Aguinaldo y exenciones (LFT y LISR)
# ══════════════════════════════════════════════════════════════════════════

AGUINALDO_DIAS_MIN = 15                          # Art. 87 LFT
AGUINALDO_EXENTO_UMA = UMA_DIARIA * 30           # Art. 93-XIV LISR

PRIMA_VACACIONAL_PCT_MIN = 0.25                  # Art. 80 LFT
PRIMA_VACACIONAL_EXENTA_UMA = UMA_DIARIA * 15    # Art. 93-XIV LISR

VALES_DESPENSA_EXENTOS_PCT_UMA = 0.40            # 40% UMA mensual
VALES_DESPENSA_EXENTOS = round(UMA_MENSUAL * VALES_DESPENSA_EXENTOS_PCT_UMA, 2)

PTU_EXENTA_UMA = UMA_DIARIA * 15                 # Art. 93-XIV LISR

INDEMNIZACION_EXENTA_UMA_POR_ANIO = UMA_DIARIA * 90  # Art. 93-XIII LISR


# ══════════════════════════════════════════════════════════════════════════
# Tabla vacaciones LFT (reforma 2023+)
# ══════════════════════════════════════════════════════════════════════════

DIAS_VACACIONES_POR_ANIO = {
    1: 12, 2: 14, 3: 16, 4: 18, 5: 20,
    6: 22, 7: 22, 8: 22, 9: 22, 10: 22,
    11: 24, 12: 24, 13: 24, 14: 24, 15: 24,
    16: 26, 17: 26, 18: 26, 19: 26, 20: 26,
    21: 28, 22: 28, 23: 28, 24: 28, 25: 28,
}


def dias_vacaciones(anios: int) -> int:
    """Devuelve días de vacaciones según antigüedad (Art. 76 LFT)."""
    if anios < 1:
        return 12
    if anios > 25:
        return 30
    return DIAS_VACACIONES_POR_ANIO.get(anios, 30)


# ══════════════════════════════════════════════════════════════════════════
# Año fiscal vigente
# ══════════════════════════════════════════════════════════════════════════

EJERCICIO_FISCAL_VIGENTE = 2025
DIAS_NATURALES_ANIO = 365
DIAS_NATURALES_ANIO_BISIESTO = 366
