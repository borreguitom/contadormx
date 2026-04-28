"""
Constantes fiscales mexicanas 2026
===================================
Una sola fuente de verdad para tarifas, UMAs, salarios mínimos, tasas.
Actualizar este archivo anualmente con valores oficiales DOF.

Referencias:
  - DOF UMA 2026 (vigente 1 feb 2026): INEGI comunicado 1/26
  - SAT Tarifas ISR: Anexo 8 RMF 2026 (DOF 28/12/2025)
  - CONASAMI Salario Mínimo 2026: DOF 09/12/2025
  - Subsidio al Empleo 2026: DOF 31/12/2025
  - IEPS combustibles 2026: Art. 2-I-D LIEPS actualizado
  - IMSS CyV 2026: Reforma LSS DOF 16/12/2020, tabla progresiva 2026
"""
from __future__ import annotations
from typing import NamedTuple


# ══════════════════════════════════════════════════════════════════════════
# UMA — Unidad de Medida y Actualización (vigente 1 feb 2026)
# ══════════════════════════════════════════════════════════════════════════

UMA_DIARIA = 117.31
UMA_MENSUAL = round(UMA_DIARIA * 30.4, 2)      # 3,566.22
UMA_ANUAL = round(UMA_DIARIA * 365.25, 2)      # 42,846.08


# ══════════════════════════════════════════════════════════════════════════
# Salario Mínimo (vigente 1 ene 2026)
# ══════════════════════════════════════════════════════════════════════════

SALARIO_MINIMO_GENERAL = 315.04
SALARIO_MINIMO_ZONA_NORTE = 440.87
SALARIO_MINIMO_PROFESIONAL = SALARIO_MINIMO_GENERAL  # base, varía por profesión

# Topes según LFT/LSS
TOPE_INDEMNIZACION_DIARIA = SALARIO_MINIMO_GENERAL * 25     # Art. 50 LFT
TOPE_PRIMA_ANTIGUEDAD = SALARIO_MINIMO_GENERAL * 2          # Art. 162 LFT
TOPE_SBC_25_UMA = UMA_DIARIA * 25                          # Art. 28 LSS


# ══════════════════════════════════════════════════════════════════════════
# Tarifa ISR Mensual 2026 (Art. 96 LISR)
# Anexo 8 RMF 2026, DOF 28/12/2025
# (límite_inferior, límite_superior, cuota_fija, tasa_marginal)
# ══════════════════════════════════════════════════════════════════════════

class RangoTarifa(NamedTuple):
    limite_inferior: float
    limite_superior: float
    cuota_fija: float
    tasa_marginal: float


TARIFA_ISR_MENSUAL_2026 = [
    RangoTarifa(0.01,         844.59,         0.00,         0.0192),
    RangoTarifa(844.60,       7_168.51,       16.22,        0.0640),
    RangoTarifa(7_168.52,     12_598.02,      420.95,       0.1088),
    RangoTarifa(12_598.03,    14_644.64,      1_011.68,     0.1600),
    RangoTarifa(14_644.65,    17_533.64,      1_339.14,     0.1792),
    RangoTarifa(17_533.65,    35_362.83,      1_856.84,     0.2136),
    RangoTarifa(35_362.84,    55_736.68,      5_665.16,     0.2352),
    RangoTarifa(55_736.69,    106_410.50,     10_457.09,    0.3000),
    RangoTarifa(106_410.51,   141_880.66,     25_659.23,    0.3200),
    RangoTarifa(141_880.67,   425_641.99,     37_009.69,    0.3400),
    RangoTarifa(425_642.00,   float("inf"),   133_488.54,   0.3500),
]

# Alias backward-compat (eliminar en ejercicio 2027)
TARIFA_ISR_MENSUAL_2025 = TARIFA_ISR_MENSUAL_2026


# ══════════════════════════════════════════════════════════════════════════
# Tarifa ISR Anual 2026 (Art. 152 LISR)
# Anexo 8 RMF 2026, DOF 28/12/2025
# ══════════════════════════════════════════════════════════════════════════

TARIFA_ISR_ANUAL_2026 = [
    RangoTarifa(0.01,           10_135.11,       0.00,          0.0192),
    RangoTarifa(10_135.12,      86_022.11,       194.59,        0.0640),
    RangoTarifa(86_022.12,      151_176.19,      5_051.37,      0.1088),
    RangoTarifa(151_176.20,     175_735.66,      12_140.13,     0.1600),
    RangoTarifa(175_735.67,     210_403.69,      16_069.64,     0.1792),
    RangoTarifa(210_403.70,     424_353.97,      22_282.14,     0.2136),
    RangoTarifa(424_353.98,     668_840.14,      67_981.92,     0.2352),
    RangoTarifa(668_840.15,     1_276_925.98,    125_485.07,    0.3000),
    RangoTarifa(1_276_925.99,   1_702_567.97,    307_910.81,    0.3200),
    RangoTarifa(1_702_567.98,   5_107_703.92,    444_116.23,    0.3400),
    RangoTarifa(5_107_703.93,   float("inf"),    1_601_862.46,  0.3500),
]

# Alias backward-compat (eliminar en ejercicio 2027)
TARIFA_ISR_ANUAL_2025 = TARIFA_ISR_ANUAL_2026


# ══════════════════════════════════════════════════════════════════════════
# Subsidio para el Empleo Mensual 2026 (DOF 31/12/2025)
# Reforma: ahora es monto fijo ($536.21) para ingresos ≤ $11,492.66
# Antes había 10 tramos con montos variables (tabla 2008-2025)
# ══════════════════════════════════════════════════════════════════════════

class RangoSubsidio(NamedTuple):
    limite_inferior: float
    limite_superior: float
    subsidio: float


SUBSIDIO_EMPLEO_MENSUAL_2026 = [
    RangoSubsidio(0.01,       11_492.66,     536.21),
    RangoSubsidio(11_492.67,  float("inf"),  0.00),
]

# Alias backward-compat (eliminar en ejercicio 2027)
SUBSIDIO_EMPLEO_MENSUAL_2025 = SUBSIDIO_EMPLEO_MENSUAL_2026


# ══════════════════════════════════════════════════════════════════════════
# RESICO PF (Art. 113-E LISR) — Tasas mensuales sobre ingresos cobrados
# ══════════════════════════════════════════════════════════════════════════

RESICO_PF_TASAS_2026 = [
    RangoTarifa(0.01,            25_000.00,    0.0,  0.0100),
    RangoTarifa(25_000.01,       50_000.00,    0.0,  0.0110),
    RangoTarifa(50_000.01,       83_333.33,    0.0,  0.0150),
    RangoTarifa(83_333.34,       208_333.33,   0.0,  0.0200),
    RangoTarifa(208_333.34,      291_666.66,   0.0,  0.0250),
]

RESICO_PF_TASAS_2025 = RESICO_PF_TASAS_2026  # alias backward-compat
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
# Tasas IEPS 2026 (Art. 2 LIEPS)
# Cuotas de combustibles actualizadas con INPC (DOF ene 2026)
# ══════════════════════════════════════════════════════════════════════════

IEPS_CATEGORIAS_2026 = {
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
        "cuota_adicional_cigarro": 0.6166,
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
        "cuota_litro": 1.6451,
        "fundamento": "Art. 2-I-G LIEPS",
    },
    "alimentos_alta_densidad_calorica": {
        "nombre": "Alimentos no básicos con alta densidad calórica (≥275 kcal/100g)",
        "tasa": 0.08,
        "fundamento": "Art. 2-I-J LIEPS",
    },
    # Combustibles automotrices — cuotas actualizadas 2026 (Art. 2-I-D LIEPS)
    "combustibles_automotrices_gasolina_menor_92": {
        "nombre": "Gasolina menor a 92 octanos (Magna)",
        "cuota_litro": 6.7001,
        "fundamento": "Art. 2-I-D LIEPS",
    },
    "combustibles_automotrices_gasolina_mayor_92": {
        "nombre": "Gasolina mayor o igual a 92 octanos (Premium)",
        "cuota_litro": 5.6579,
        "fundamento": "Art. 2-I-D LIEPS",
    },
    "combustibles_diesel": {
        "nombre": "Diésel",
        "cuota_litro": 7.3634,
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

# Alias backward-compat
IEPS_CATEGORIAS_2025 = IEPS_CATEGORIAS_2026


# ══════════════════════════════════════════════════════════════════════════
# Cuotas IMSS 2026 (Ley del Seguro Social)
# Cesantía y Vejez: tabla PROGRESIVA por SBC a partir de 2026
# (Reforma LSS DOF 16/12/2020 — implementación gradual hasta 2030)
# ══════════════════════════════════════════════════════════════════════════

CUOTAS_IMSS_2026 = {
    "enfermedad_maternidad": {
        "fija_patron_3uma": 0.204,
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
    # Cesantía y Vejez: ver función tasa_cesantia_vejez_patron_2026()
    # La cuota obrera permanece fija en 1.125% para todos los rangos
    "cesantia_vejez": {
        "patron": None,       # PROGRESIVA — usar tasa_cesantia_vejez_patron_2026(sbc_diario)
        "trabajador": 0.01125,
    },
    "guarderias": {
        "patron": 0.01,
        "trabajador": 0.0,
    },
    "infonavit": {
        "patron": 0.05,
        "trabajador": 0.0,
    },
    "riesgo_trabajo_promedio": 0.0054355,
}

# Alias backward-compat
CUOTAS_IMSS_2025 = CUOTAS_IMSS_2026


# ══════════════════════════════════════════════════════════════════════════
# Cesantía y Vejez 2026 — Tabla progresiva por SBC (Art. 168 BIS LSS)
# Reforma DOF 16/12/2020, vigente progresivamente hasta 2030
# Rangos expresados en múltiplos del Salario Mínimo diario ($315.04)
# ══════════════════════════════════════════════════════════════════════════

# (limite_superior_sm, tasa_patron)  — trabajador siempre 1.125%
CESANTIA_VEJEZ_TABLA_2026 = [
    (1.00,        0.03150),   # ≤ 1 SM  ($315.04/día)
    (1.50,        0.03676),   # 1.01–1.50 SM  ($315–$473/día)
    (2.00,        0.04851),   # 1.51–2.00 SM  ($473–$630/día)
    (2.50,        0.05556),   # 2.01–2.50 SM  ($630–$788/día)
    (3.00,        0.06026),   # 2.51–3.00 SM  ($788–$945/día)
    (3.50,        0.06361),   # 3.01–3.50 SM  ($945–$1,103/día)
    (4.00,        0.06613),   # 3.51–4.00 SM  ($1,103–$1,260/día)
    (float("inf"), 0.07513),  # 4.01+ SM  (>$1,260/día)
]
CESANTIA_VEJEZ_TRABAJADOR_2026 = 0.01125


def tasa_cesantia_vejez_patron_2026(sbc_diario: float) -> float:
    """Devuelve la tasa patronal de cesantía y vejez según SBC diario (Art. 168 BIS LSS 2026)."""
    multiplo_sm = sbc_diario / SALARIO_MINIMO_GENERAL
    for limite, tasa in CESANTIA_VEJEZ_TABLA_2026:
        if multiplo_sm <= limite:
            return tasa
    return 0.07513


# ══════════════════════════════════════════════════════════════════════════
# Coeficientes de utilidad por actividad (Art. 14 LISR)
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
# Deducciones personales 2026 (Art. 151 LISR)
# ══════════════════════════════════════════════════════════════════════════

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

EJERCICIO_FISCAL_VIGENTE = 2026
DIAS_NATURALES_ANIO = 365
DIAS_NATURALES_ANIO_BISIESTO = 366
