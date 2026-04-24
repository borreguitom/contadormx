"""
Cálculo de nómina completo: ISR retención, IMSS cuotas obrero, subsidio empleo.
Integra isr.py + imss.py para dar el comprobante de nómina completo.
"""
from .isr import calcular_isr_pf, _subsidio_empleo
from .imss import calcular_cuotas_imss, UMA_DIARIA_2025

DIAS_PERIODO = {
    "semanal": 7,
    "catorcenal": 14,
    "quincenal": 15,
    "mensual": 30,
}


def calcular_nomina(
    salario_mensual_bruto: float,
    periodo: str = "mensual",
    otras_percepciones: float = 0.0,
    vales_despensa: float = 0.0,
    fondo_ahorro_patron: float = 0.0,
    prima_riesgo_trabajo: float = 0.0054355,
) -> dict:
    """
    Genera comprobante de nómina completo.
    salario_mensual_bruto: salario base mensual.
    periodo: semanal | catorcenal | quincenal | mensual.
    vales_despensa: exentos hasta 40% de UMA mensual.
    """
    dias = DIAS_PERIODO.get(periodo, 30)
    factor = dias / 30

    # Percepciones del periodo
    salario_periodo = round(salario_mensual_bruto * factor, 2)
    partes_prop_aguinaldo = round(salario_mensual_bruto * 15 / 365 * factor, 2)
    partes_prop_vacaciones = round(salario_mensual_bruto * 15 / 365 * factor * 0.25, 2)
    partes_prop_total = round(partes_prop_aguinaldo + partes_prop_vacaciones, 2)

    # Integración SDI (Art. 27 LSS)
    sdi = round((salario_mensual_bruto + salario_mensual_bruto * 15 / 365 + salario_mensual_bruto * 15 / 365 * 0.25) / 30, 4)

    # Vales de despensa — exención Art. 93 fracción XIV LISR (40% UMA mensual)
    uma_mensual = UMA_DIARIA_2025 * 30.4
    vales_exentos = min(vales_despensa, uma_mensual * 0.40)
    vales_gravados = max(vales_despensa - vales_exentos, 0.0)

    # Base gravable ISR mensual
    base_isr_mensual = salario_mensual_bruto + vales_gravados + otras_percepciones

    isr_mensual_result = calcular_isr_pf(base_isr_mensual, regimen="sueldos")
    isr_periodo = round(isr_mensual_result["isr_a_retener"] * factor, 2)
    subsidio_periodo = round(isr_mensual_result["subsidio_al_empleo"] * factor, 2)

    # Cuotas IMSS trabajador
    imss_result = calcular_cuotas_imss(sdi, prima_riesgo_trabajo)
    cuota_trabajador_mensual = imss_result["cuotas_trabajador"]["total_trabajador"]
    cuota_trabajador_periodo = round(cuota_trabajador_mensual * factor, 2)

    # Totales
    total_percepciones = round(salario_periodo + partes_prop_total + vales_exentos + otras_percepciones * factor, 2)
    total_deducciones = round(isr_periodo + cuota_trabajador_periodo, 2)
    neto_pagar = round(total_percepciones - total_deducciones, 2)

    return {
        "periodo": periodo,
        "dias_periodo": dias,
        "fundamentos": "Art. 27 LSS (integración), Art. 93, 96 LISR (ISR), Art. 25 LSS (IMSS)",
        "percepciones": {
            "salario_base": salario_periodo,
            "partes_proporcionales": partes_prop_total,
            "vales_despensa_exentos": round(vales_exentos * factor, 2),
            "otras_percepciones": round(otras_percepciones * factor, 2),
            "total_percepciones": total_percepciones,
        },
        "deducciones": {
            "isr_retenido": isr_periodo,
            "subsidio_al_empleo": subsidio_periodo,
            "imss_cuota_obrero": cuota_trabajador_periodo,
            "total_deducciones": total_deducciones,
        },
        "neto_a_pagar": neto_pagar,
        "costo_empresa": {
            "salario_base_mensual": salario_mensual_bruto,
            "imss_cuota_patronal": round(imss_result["cuotas_patronales"]["total_patronal"] * factor, 2),
            "infonavit_patron": round(imss_result["cuotas_patronales"]["infonavit"] * factor, 2),
            "costo_total_empresa": round(
                salario_periodo + imss_result["cuotas_patronales"]["total_patronal"] * factor, 2
            ),
        },
        "integracion_sdi": {
            "sdi_diario": round(sdi, 4),
            "formula": "SDI = (salario_base + partes_proporcionales) / 30",
        },
    }
