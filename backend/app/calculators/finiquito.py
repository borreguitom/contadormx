"""
Finiquito y liquidación — Art. 76, 80, 87 LFT (vacaciones, prima, aguinaldo).
Art. 50 LFT (3 meses + 20 días por año en liquidación).
"""

SALARIO_MINIMO_2025 = 278.80
TOPE_INDEMNIZACION = SALARIO_MINIMO_2025 * 25


def calcular_finiquito(
    salario_diario: float,
    dias_trabajados_anio: int,
    anios_servicio: float = 0.0,
    tipo_separacion: str = "renuncia",
    vacaciones_gozadas: int = 0,
    mes_rescision: int = 12,
) -> dict:
    """
    tipo_separacion: renuncia | despido_justificado | despido_injustificado | mutuo_acuerdo
    dias_trabajados_anio: días del año en curso (para proporcionales).
    anios_servicio: total de años de antigüedad.
    """
    tipo = tipo_separacion.lower().replace(" ", "_")
    prop = dias_trabajados_anio / 365

    # Vacaciones proporcionales (tabla Art. 76 LFT)
    dias_vacaciones = _dias_vacaciones(int(anios_servicio))
    vacaciones_prop = round(dias_vacaciones * prop, 2)
    vacaciones_pendientes = max(vacaciones_prop - vacaciones_gozadas, 0.0)
    importe_vacaciones = round(vacaciones_pendientes * salario_diario, 2)

    # Prima vacacional 25% (Art. 80 LFT)
    prima_vacacional = round(importe_vacaciones * 0.25, 2)

    # Aguinaldo proporcional — 15 días/año (Art. 87 LFT)
    aguinaldo_prop = round(15 * prop * salario_diario, 2)

    # Partes proporcionales base
    partes_prop = round(importe_vacaciones + prima_vacacional + aguinaldo_prop, 2)

    # Indemnización por despido injustificado
    indemnizacion = {}
    if tipo in ("despido_injustificado", "liquidacion"):
        tres_meses = round(90 * salario_diario, 2)
        # 20 días por año (tope 25 SM diarios) Art. 50 LFT
        sd_topado = min(salario_diario, TOPE_INDEMNIZACION)
        veinte_dias_anio = round(20 * sd_topado * anios_servicio, 2)
        # Prima de antigüedad: 12 días por año, tope 2 SM (Art. 162 LFT)
        sd_prima = min(salario_diario, SALARIO_MINIMO_2025 * 2)
        prima_antiguedad = round(12 * sd_prima * anios_servicio, 2)

        indemnizacion = {
            "tres_meses_art_50": tres_meses,
            "veinte_dias_por_anio": veinte_dias_anio,
            "prima_antiguedad_art_162": prima_antiguedad,
            "total_indemnizacion": round(tres_meses + veinte_dias_anio + prima_antiguedad, 2),
        }

    elif tipo in ("renuncia", "mutuo_acuerdo"):
        # Prima de antigüedad solo si tiene más de 15 años (Art. 162 LFT)
        sd_prima = min(salario_diario, SALARIO_MINIMO_2025 * 2)
        prima = round(12 * sd_prima * anios_servicio, 2) if anios_servicio >= 15 else 0.0
        indemnizacion = {
            "nota": "Renuncia voluntaria — sin indemnización por despido.",
            "prima_antiguedad_art_162": prima,
            "total_indemnizacion": prima,
        }

    total_finiquito = round(partes_prop + indemnizacion.get("total_indemnizacion", 0.0), 2)

    return {
        "tipo_separacion": tipo_separacion,
        "fundamento": "Art. 76, 80, 87, 50, 162 LFT",
        "salario_diario": round(salario_diario, 2),
        "dias_trabajados_anio": dias_trabajados_anio,
        "anios_servicio": anios_servicio,
        "partes_proporcionales": {
            "vacaciones_dias": round(vacaciones_pendientes, 2),
            "importe_vacaciones": importe_vacaciones,
            "prima_vacacional_25pct": prima_vacacional,
            "aguinaldo_proporcional": aguinaldo_prop,
            "subtotal": partes_prop,
        },
        "indemnizacion": indemnizacion,
        "total_a_pagar": total_finiquito,
        "nota_isr": (
            "La indemnización por despido injustificado está exenta de ISR hasta "
            "90 veces el SM x los años de servicio (Art. 93 LISR). El excedente es gravable."
        ),
    }


def _dias_vacaciones(anios: int) -> int:
    """Tabla Art. 76 LFT vigente 2023+ (reforma que duplicó días)."""
    if anios == 0:
        return 12
    tabla = {1: 12, 2: 14, 3: 16, 4: 18, 5: 20}
    if anios <= 5:
        return tabla.get(anios, 12)
    elif anios <= 10:
        return 22
    elif anios <= 15:
        return 24
    elif anios <= 20:
        return 26
    elif anios <= 25:
        return 28
    else:
        return 30
