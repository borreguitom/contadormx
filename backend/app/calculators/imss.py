"""
Cuotas IMSS — Ley del Seguro Social.
Valores vigentes 2025:
  UMA diaria: $113.14
  Salario mínimo diario: $278.80 (general) / $419.88 (zona libre norte)
"""

UMA_DIARIA_2025 = 113.14
UMA_MENSUAL_2025 = round(UMA_DIARIA_2025 * 30.4, 2)
SALARIO_MINIMO_DIARIO_2025 = 278.80
TOPE_SBC_25_UMA = UMA_DIARIA_2025 * 25

# Cuotas porcentuales sobre SBC
CUOTAS = {
    "enfermedad_maternidad": {
        "prestaciones_especie_fija_patron": {
            "tasa_patron": 0.204,
            "base": "3_uma_minimas",
            "descripcion": "Cuota fija patronal E&M (Art. 25 LSS)",
        },
        "prestaciones_especie_excedente_patron": {
            "tasa_patron": 0.011,
            "tasa_trabajador": 0.004,
            "descripcion": "Excedente sobre 3 SMG (Art. 25 LSS)",
        },
        "prestaciones_dinero_patron": {
            "tasa_patron": 0.007,
            "tasa_trabajador": 0.0025,
            "descripcion": "Incapacidades temporales (Art. 27 LSS)",
        },
        "gastos_medicos_pensionados": {
            "tasa_patron": 0.0105,
            "tasa_trabajador": 0.00375,
            "descripcion": "GMPM (Art. 25 LSS)",
        },
    },
    "invalidez_vida": {
        "tasa_patron": 0.0175,
        "tasa_trabajador": 0.00625,
        "descripcion": "Art. 147 LSS",
    },
    "ceav": {
        "retiro": {
            "tasa_patron": 0.02,
            "tasa_trabajador": 0.0,
            "descripcion": "Retiro (Art. 168 LSS)",
        },
        "cesantia_vejez": {
            "tasa_patron": 0.0315,
            "tasa_trabajador": 0.01125,
            "descripcion": "Cesantía y vejez (Art. 168 LSS)",
        },
    },
    "guarderias": {
        "tasa_patron": 0.01,
        "tasa_trabajador": 0.0,
        "descripcion": "Art. 211 LSS",
    },
    "infonavit": {
        "tasa_patron": 0.05,
        "tasa_trabajador": 0.0,
        "descripcion": "Art. 29 Ley INFONAVIT",
    },
    "riesgo_trabajo": {
        "tasa_patron": 0.0054355,
        "tasa_trabajador": 0.0,
        "descripcion": "Prima promedio nacional (Art. 73 LSS). Varía por SIPA.",
    },
}


def calcular_cuotas_imss(
    salario_diario_integrado: float,
    prima_riesgo_trabajo: float = 0.0054355,
    zona_norte: bool = False,
) -> dict:
    """
    Calcula cuotas obrero-patronales IMSS + INFONAVIT + SAR.
    salario_diario_integrado (SDI): incluye salario base + partes proporcionales
    de aguinaldo, vacaciones, prima vacacional y otras percepciones integrables.
    """
    sdi = min(salario_diario_integrado, TOPE_SBC_25_UMA)
    sdi_mensual = round(sdi * 30.4, 2)
    uma_3 = UMA_DIARIA_2025 * 3 * 30.4

    # Partes calculadas
    cuota_fija_patron = round(uma_3 * 0.204, 2)

    excedente = max(sdi_mensual - uma_3, 0)
    excedente_especie_patron = round(excedente * 0.011, 2)
    excedente_especie_trabajador = round(excedente * 0.004, 2)

    dinero_patron = round(sdi_mensual * 0.007, 2)
    dinero_trabajador = round(sdi_mensual * 0.0025, 2)

    gmpm_patron = round(sdi_mensual * 0.0105, 2)
    gmpm_trabajador = round(sdi_mensual * 0.00375, 2)

    iv_patron = round(sdi_mensual * 0.0175, 2)
    iv_trabajador = round(sdi_mensual * 0.00625, 2)

    retiro_patron = round(sdi_mensual * 0.02, 2)

    cesantia_patron = round(sdi_mensual * 0.0315, 2)
    cesantia_trabajador = round(sdi_mensual * 0.01125, 2)

    guarderias_patron = round(sdi_mensual * 0.01, 2)
    infonavit_patron = round(sdi_mensual * 0.05, 2)
    riesgo_patron = round(sdi_mensual * prima_riesgo_trabajo, 2)

    total_patron = round(
        cuota_fija_patron + excedente_especie_patron + dinero_patron + gmpm_patron
        + iv_patron + retiro_patron + cesantia_patron + guarderias_patron
        + infonavit_patron + riesgo_patron,
        2,
    )
    total_trabajador = round(
        excedente_especie_trabajador + dinero_trabajador + gmpm_trabajador
        + iv_trabajador + cesantia_trabajador,
        2,
    )
    total_cuotas = round(total_patron + total_trabajador, 2)

    return {
        "fundamento": "Ley del Seguro Social, Art. 25-168; Ley INFONAVIT Art. 29",
        "salario_diario_integrado": round(salario_diario_integrado, 2),
        "sdi_topado_25uma": round(sdi, 2),
        "sdi_mensual_base": sdi_mensual,
        "uma_diaria_2025": UMA_DIARIA_2025,
        "tope_sbc_25_umas_dia": round(TOPE_SBC_25_UMA, 2),
        "cuotas_patronales": {
            "enfermedad_maternidad_cuota_fija": cuota_fija_patron,
            "enfermedad_maternidad_excedente": excedente_especie_patron,
            "enfermedad_maternidad_dinero": dinero_patron,
            "gastos_medicos_pensionados": gmpm_patron,
            "invalidez_y_vida": iv_patron,
            "retiro": retiro_patron,
            "cesantia_vejez": cesantia_patron,
            "guarderias": guarderias_patron,
            "infonavit": infonavit_patron,
            "riesgo_trabajo": riesgo_patron,
            "total_patronal": total_patron,
        },
        "cuotas_trabajador": {
            "enfermedad_maternidad_excedente": excedente_especie_trabajador,
            "enfermedad_maternidad_dinero": dinero_trabajador,
            "gastos_medicos_pensionados": gmpm_trabajador,
            "invalidez_y_vida": iv_trabajador,
            "cesantia_vejez": cesantia_trabajador,
            "total_trabajador": total_trabajador,
        },
        "costo_total_empresa_mensual": total_cuotas,
        "nota": (
            f"Prima riesgo trabajo usada: {prima_riesgo_trabajo:.5f} "
            f"(promedio nacional). Ajusta según tu SIPA determinado por IMSS."
        ),
    }
