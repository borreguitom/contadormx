"""
Finiquito y Liquidación — Versión definitiva
==============================================
Calcula ALL conceptos legales según LFT 2023+:

PARTES PROPORCIONALES (siempre):
  - Salario pendiente de pago
  - Aguinaldo proporcional (Art. 87 LFT — 15 días/año)
  - Vacaciones proporcionales (Art. 76 LFT — tabla nueva 2023)
  - Prima vacacional proporcional (Art. 80 LFT — 25%)
  - PTU pendiente (si aplica)

INDEMNIZACIÓN (sólo en despido injustificado):
  - 3 meses de salario (Art. 50 fracción I LFT)
  - 20 días por año de antigüedad (Art. 50 fracción II LFT)
  - Salarios caídos (Art. 48 LFT — máximo 12 meses)

PRIMA DE ANTIGÜEDAD (Art. 162 LFT):
  - 12 días por año (tope 2 SM)
  - Aplica en: despido injust., renuncia con 15+ años, muerte, jubilación

ISR DEL FINIQUITO:
  - Indemnización exenta hasta 90 SM × años (Art. 93-XIII LISR)
  - Excedente gravable a tasa efectiva (Art. 95 LISR)
  - Aguinaldo, prima vacacional con exención específica
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Optional, Literal

from app.utils.constantes_fiscales import (
    UMA_DIARIA,
    SALARIO_MINIMO_GENERAL,
    TOPE_INDEMNIZACION_DIARIA,
    TOPE_PRIMA_ANTIGUEDAD,
    AGUINALDO_DIAS_MIN,
    PRIMA_VACACIONAL_PCT_MIN,
    PRIMA_VACACIONAL_EXENTA_UMA,
    AGUINALDO_EXENTO_UMA,
    INDEMNIZACION_EXENTA_UMA_POR_ANIO,
    EJERCICIO_FISCAL_VIGENTE,
    dias_vacaciones,
)


TipoSeparacion = Literal[
    "renuncia",
    "despido_justificado",
    "despido_injustificado",
    "mutuo_acuerdo",
    "muerte",
    "jubilacion",
    "incapacidad_total",
    "termino_contrato",
]


# ══════════════════════════════════════════════════════════════════════════
# Resultado estructurado
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoFiniquito:
    # Identificación
    datos_trabajador: dict
    datos_empleador: dict
    periodo_laboral: dict
    tipo_separacion: dict
    ejercicio: int
    fundamento: list[str]

    # Cálculos
    partes_proporcionales: dict
    subtotal_partes_proporcionales: float

    indemnizacion: dict
    subtotal_indemnizacion: float

    prima_antiguedad: dict
    subtotal_prima_antiguedad: float

    # ISR
    isr_finiquito: dict

    # Totales
    total_bruto: float
    total_exento: float
    total_gravado: float
    isr_retenido: float
    neto_a_pagar: float

    # Resumen
    resumen: dict

    advertencias: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════

def _calcular_anios_y_dias(fecha_ingreso: date, fecha_separacion: date) -> tuple:
    """Devuelve (años_completos, días_año_actual)."""
    delta = fecha_separacion - fecha_ingreso
    dias_totales = delta.days
    anios = dias_totales / 365.25

    # Días del año en curso al momento de la separación
    inicio_anio = date(fecha_separacion.year, 1, 1)
    dias_anio_actual = (fecha_separacion - inicio_anio).days + 1

    return anios, dias_anio_actual


def _calcular_isr_finiquito(
    monto_gravable: float,
    salario_diario_promedio: float,
) -> dict:
    """
    Calcula ISR del finiquito usando tasa efectiva mensual (Art. 95 LISR).
    Procedimiento simplificado: aplicar % efectivo del último mes ordinario.
    """
    from .isr_pf import calcular_isr_sueldos

    if monto_gravable <= 0:
        return {
            "monto_gravable": 0.0,
            "tasa_efectiva_aplicada_pct": 0.0,
            "isr_retenido": 0.0,
            "metodo": "No aplica (monto gravable cero)",
        }

    # Calcular ISR del salario mensual ordinario
    salario_mensual = salario_diario_promedio * 30
    isr_ordinario = calcular_isr_sueldos(salario_mensual, "mensual")
    tasa_efectiva = (
        isr_ordinario["isr_a_cargo"] / salario_mensual
        if salario_mensual > 0
        else 0
    )

    isr_retenido = round(monto_gravable * tasa_efectiva, 2)

    return {
        "monto_gravable": round(monto_gravable, 2),
        "tasa_efectiva_aplicada_pct": round(tasa_efectiva * 100, 4),
        "isr_retenido": isr_retenido,
        "metodo": "Tasa efectiva del salario mensual ordinario (Art. 95 LISR)",
    }


# ══════════════════════════════════════════════════════════════════════════
# Cálculo principal
# ══════════════════════════════════════════════════════════════════════════

def calcular_finiquito(
    salario_diario: float,
    *,
    # Fechas (preferidas si se proveen)
    fecha_ingreso: Optional[str] = None,
    fecha_separacion: Optional[str] = None,

    # Alternativa: provee directamente
    anios_servicio: Optional[float] = None,
    dias_trabajados_anio: Optional[int] = None,

    # Tipo de separación
    tipo_separacion: TipoSeparacion = "renuncia",

    # Vacaciones
    vacaciones_gozadas: int = 0,

    # Salario y conceptos pendientes
    dias_pendientes_pago: int = 0,
    aguinaldo_ya_pagado: float = 0.0,
    ptu_pendiente: float = 0.0,
    bono_pendiente: float = 0.0,

    # Salarios caídos (despido injustificado, máximo 12 meses, Art. 48 LFT)
    meses_salarios_caidos: float = 0.0,

    # Datos identificatorios
    datos_trabajador: Optional[dict] = None,
    datos_empleador: Optional[dict] = None,
) -> dict:
    """
    Calcula finiquito completo según LFT.

    Tipos de separación:
        - renuncia: Sólo partes proporcionales + prima antigüedad si 15+ años
        - despido_justificado: Sólo partes proporcionales (no indemnización)
        - despido_injustificado: TODAS las prestaciones + indemnización + salarios caídos
        - mutuo_acuerdo: Negociado (típicamente igual a renuncia)
        - muerte: Partes proporcionales + prima antigüedad (a beneficiarios)
        - jubilacion: Partes proporcionales + prima antigüedad
        - incapacidad_total: Partes proporcionales + prima antigüedad
        - termino_contrato: Partes proporcionales (si tipo determinado)
    """
    advertencias = []
    notas = []

    if salario_diario <= 0:
        return {"error": True, "mensaje": "El salario diario debe ser mayor a 0"}

    # ═════════════════════════════════════════════════════════════
    # Determinar antigüedad y días del año
    # ═════════════════════════════════════════════════════════════

    if fecha_ingreso and fecha_separacion:
        d_ingreso = datetime.strptime(fecha_ingreso, "%Y-%m-%d").date()
        d_separacion = datetime.strptime(fecha_separacion, "%Y-%m-%d").date()

        if d_separacion < d_ingreso:
            return {"error": True, "mensaje": "Fecha separación anterior a ingreso"}

        anios_calc, dias_anio_calc = _calcular_anios_y_dias(d_ingreso, d_separacion)
        anios_servicio = anios_servicio or anios_calc
        dias_trabajados_anio = dias_trabajados_anio or dias_anio_calc
    else:
        if anios_servicio is None or dias_trabajados_anio is None:
            return {
                "error": True,
                "mensaje": "Provee fecha_ingreso/fecha_separacion O anios_servicio/dias_trabajados_anio"
            }

    tipo = tipo_separacion.lower().replace(" ", "_")
    proporcion_anio = dias_trabajados_anio / 365

    # ═════════════════════════════════════════════════════════════
    # 1. SALARIO PENDIENTE
    # ═════════════════════════════════════════════════════════════

    salario_pendiente = round(dias_pendientes_pago * salario_diario, 2)

    # ═════════════════════════════════════════════════════════════
    # 2. VACACIONES (Art. 76 LFT — tabla 2023+)
    # ═════════════════════════════════════════════════════════════

    dias_vacaciones_anuales = dias_vacaciones(int(anios_servicio))
    vacaciones_proporcionales_dias = round(dias_vacaciones_anuales * proporcion_anio, 2)
    vacaciones_pendientes_dias = max(vacaciones_proporcionales_dias - vacaciones_gozadas, 0)
    importe_vacaciones = round(vacaciones_pendientes_dias * salario_diario, 2)

    # Prima vacacional 25% (Art. 80 LFT)
    prima_vacacional = round(importe_vacaciones * PRIMA_VACACIONAL_PCT_MIN, 2)

    # Exenciones ISR (Art. 93-XIV LISR)
    prima_vac_exenta = min(prima_vacacional, PRIMA_VACACIONAL_EXENTA_UMA)
    prima_vac_gravada = round(prima_vacacional - prima_vac_exenta, 2)

    # ═════════════════════════════════════════════════════════════
    # 3. AGUINALDO PROPORCIONAL (Art. 87 LFT)
    # ═════════════════════════════════════════════════════════════

    aguinaldo_proporcional = round(AGUINALDO_DIAS_MIN * proporcion_anio * salario_diario, 2)
    # Restar lo ya pagado
    aguinaldo_pendiente = max(aguinaldo_proporcional - aguinaldo_ya_pagado, 0)

    # Exención (Art. 93-XIV LISR)
    aguinaldo_exento = min(aguinaldo_pendiente, AGUINALDO_EXENTO_UMA)
    aguinaldo_gravado = round(aguinaldo_pendiente - aguinaldo_exento, 2)

    # ═════════════════════════════════════════════════════════════
    # 4. SUBTOTAL PARTES PROPORCIONALES
    # ═════════════════════════════════════════════════════════════

    subtotal_pp = round(
        salario_pendiente +
        importe_vacaciones +
        prima_vacacional +
        aguinaldo_pendiente +
        ptu_pendiente +
        bono_pendiente,
        2
    )

    # Total exento de partes proporcionales
    pp_exentas = round(prima_vac_exenta + aguinaldo_exento, 2)
    pp_gravadas = round(subtotal_pp - pp_exentas, 2)

    # ═════════════════════════════════════════════════════════════
    # 5. INDEMNIZACIÓN (sólo despido injustificado)
    # ═════════════════════════════════════════════════════════════

    indemnizacion_data = {
        "aplica": False,
        "concepto_separacion": tipo,
    }
    subtotal_indemnizacion = 0.0
    indemnizacion_exenta = 0.0
    indemnizacion_gravada = 0.0

    if tipo == "despido_injustificado":
        # 3 meses de salario (Art. 50-I LFT) — sin tope
        tres_meses = round(90 * salario_diario, 2)

        # 20 días por año de antigüedad (Art. 50-II LFT) — tope 25 SM diarios
        salario_topado_indem = min(salario_diario, TOPE_INDEMNIZACION_DIARIA)
        veinte_dias_anio = round(20 * salario_topado_indem * anios_servicio, 2)

        # Salarios caídos (Art. 48 LFT — máx 12 meses)
        meses_caidos_aplicables = min(meses_salarios_caidos, 12)
        salarios_caidos = round(meses_caidos_aplicables * 30 * salario_diario, 2)

        if meses_salarios_caidos > 12:
            advertencias.append(
                f"Salarios caídos topados a 12 meses (Art. 48 LFT). "
                f"Solicitados: {meses_salarios_caidos} meses."
            )

        subtotal_indemnizacion = round(tres_meses + veinte_dias_anio + salarios_caidos, 2)

        # Exención ISR: 90 SM × años de servicio (Art. 93-XIII LISR)
        indemnizacion_exenta = min(
            subtotal_indemnizacion,
            INDEMNIZACION_EXENTA_UMA_POR_ANIO * anios_servicio
        )
        indemnizacion_gravada = round(subtotal_indemnizacion - indemnizacion_exenta, 2)

        indemnizacion_data = {
            "aplica": True,
            "concepto_separacion": "Despido injustificado",
            "tres_meses_salario": {
                "fundamento": "Art. 50-I LFT",
                "calculo": "90 días × salario diario",
                "monto": tres_meses,
            },
            "veinte_dias_por_anio": {
                "fundamento": "Art. 50-II LFT",
                "calculo": f"20 × {salario_topado_indem:.2f} × {anios_servicio:.2f} años",
                "salario_topado_25_sm": round(salario_topado_indem, 2),
                "tope_diario": round(TOPE_INDEMNIZACION_DIARIA, 2),
                "monto": veinte_dias_anio,
            },
            "salarios_caidos": {
                "fundamento": "Art. 48 LFT (máximo 12 meses)",
                "meses": meses_caidos_aplicables,
                "monto": salarios_caidos,
            },
            "total_indemnizacion": subtotal_indemnizacion,
            "exencion_isr": {
                "fundamento": "Art. 93-XIII LISR",
                "calculo": f"90 SM × {anios_servicio:.2f} años",
                "monto_exento": round(indemnizacion_exenta, 2),
                "monto_gravado": indemnizacion_gravada,
            },
        }

    # ═════════════════════════════════════════════════════════════
    # 6. PRIMA DE ANTIGÜEDAD (Art. 162 LFT)
    # ═════════════════════════════════════════════════════════════

    prima_antiguedad_data = {"aplica": False, "monto": 0.0}
    subtotal_prima = 0.0

    aplica_prima = (
        tipo == "despido_injustificado" or
        tipo == "despido_justificado" or
        (tipo in ("renuncia", "mutuo_acuerdo") and anios_servicio >= 15) or
        tipo in ("muerte", "jubilacion", "incapacidad_total")
    )

    if aplica_prima:
        # 12 días por año, tope 2 SM
        salario_topado_prima = min(salario_diario, TOPE_PRIMA_ANTIGUEDAD)
        prima_calculada = round(12 * salario_topado_prima * anios_servicio, 2)
        subtotal_prima = prima_calculada

        # Exención: 90 SM × años (Art. 93-XIII LISR — junto con indemnización)
        # El monto exento se comparte con la indemnización
        prima_antiguedad_data = {
            "aplica": True,
            "fundamento": "Art. 162 LFT",
            "calculo": f"12 × {salario_topado_prima:.2f} × {anios_servicio:.2f} años",
            "salario_topado_2_sm": round(salario_topado_prima, 2),
            "tope_diario": round(TOPE_PRIMA_ANTIGUEDAD, 2),
            "monto": prima_calculada,
        }

        # Si es renuncia, la prima de antigüedad se suma a la exención
        if tipo not in ("despido_injustificado",):
            prima_exenta = min(
                prima_calculada,
                INDEMNIZACION_EXENTA_UMA_POR_ANIO * anios_servicio
            )
            prima_gravada = round(prima_calculada - prima_exenta, 2)
            indemnizacion_exenta += prima_exenta
            indemnizacion_gravada += prima_gravada
            prima_antiguedad_data["exencion_isr"] = {
                "monto_exento": round(prima_exenta, 2),
                "monto_gravado": prima_gravada,
            }
    elif tipo in ("renuncia", "mutuo_acuerdo"):
        prima_antiguedad_data = {
            "aplica": False,
            "razon": "Renuncia con menos de 15 años de servicio (Art. 162 LFT)",
            "monto": 0.0,
        }

    # ═════════════════════════════════════════════════════════════
    # 7. ISR DEL FINIQUITO
    # ═════════════════════════════════════════════════════════════

    total_gravado = round(pp_gravadas + indemnizacion_gravada, 2)
    isr_calculo = _calcular_isr_finiquito(total_gravado, salario_diario)
    isr_retenido = isr_calculo["isr_retenido"]

    # ═════════════════════════════════════════════════════════════
    # 8. TOTALES
    # ═════════════════════════════════════════════════════════════

    total_bruto = round(subtotal_pp + subtotal_indemnizacion + subtotal_prima, 2)
    total_exento = round(pp_exentas + indemnizacion_exenta, 2)
    neto_a_pagar = round(total_bruto - isr_retenido, 2)

    # ═════════════════════════════════════════════════════════════
    # 9. NOTAS
    # ═════════════════════════════════════════════════════════════

    if tipo == "renuncia":
        if anios_servicio < 15:
            notas.append(
                f"Renuncia con {anios_servicio:.2f} años. "
                "No hay prima de antigüedad (requiere 15+ años) ni indemnización."
            )
        else:
            notas.append(
                f"Renuncia con 15+ años: aplica prima de antigüedad (Art. 162 LFT)."
            )

    if tipo == "despido_injustificado":
        notas.append(
            "💡 El trabajador puede elegir entre indemnización constitucional (3 meses + 20 días) "
            "o reinstalación. Esta calculadora asume indemnización."
        )

    if dias_vacaciones_anuales == 12 and anios_servicio >= 1:
        notas.append(
            "📅 Tabla vacaciones reformada en 2023: ahora 12 días desde el primer año "
            "(antes eran 6). Verifica antigüedad correcta."
        )

    notas.append(
        f"Salario diario integrado para finiquito: ${salario_diario:,.2f} (sin SDI integrado)."
    )

    # ═════════════════════════════════════════════════════════════
    # 10. CONSTRUIR RESULTADO
    # ═════════════════════════════════════════════════════════════

    return ResultadoFiniquito(
        datos_trabajador=datos_trabajador or {},
        datos_empleador=datos_empleador or {},
        periodo_laboral={
            "fecha_ingreso": fecha_ingreso,
            "fecha_separacion": fecha_separacion,
            "anios_servicio": round(anios_servicio, 4),
            "dias_trabajados_anio_actual": dias_trabajados_anio,
            "proporcion_anio": round(proporcion_anio, 4),
            "dias_vacaciones_segun_antiguedad": dias_vacaciones_anuales,
        },
        tipo_separacion={
            "tipo": tipo,
            "descripcion": _descripcion_separacion(tipo),
        },
        ejercicio=EJERCICIO_FISCAL_VIGENTE,
        fundamento=[
            "Art. 76 LFT (vacaciones)",
            "Art. 80 LFT (prima vacacional)",
            "Art. 87 LFT (aguinaldo)",
            "Art. 50 LFT (indemnización)" if tipo == "despido_injustificado" else "",
            "Art. 48 LFT (salarios caídos)" if meses_salarios_caidos > 0 else "",
            "Art. 162 LFT (prima antigüedad)" if aplica_prima else "",
            "Art. 93-XIII y XIV LISR (exenciones)",
            "Art. 95 LISR (ISR finiquito)",
        ],

        partes_proporcionales={
            "salario_pendiente": {
                "dias": dias_pendientes_pago,
                "salario_diario": round(salario_diario, 2),
                "monto": salario_pendiente,
            },
            "vacaciones": {
                "fundamento": "Art. 76 LFT",
                "dias_por_antiguedad_anuales": dias_vacaciones_anuales,
                "dias_proporcionales": round(vacaciones_proporcionales_dias, 2),
                "dias_gozados": vacaciones_gozadas,
                "dias_pendientes": round(vacaciones_pendientes_dias, 2),
                "salario_diario": round(salario_diario, 2),
                "monto": importe_vacaciones,
            },
            "prima_vacacional": {
                "fundamento": "Art. 80 LFT",
                "porcentaje": "25%",
                "base": importe_vacaciones,
                "monto": prima_vacacional,
                "exento": round(prima_vac_exenta, 2),
                "gravado": prima_vac_gravada,
            },
            "aguinaldo": {
                "fundamento": "Art. 87 LFT",
                "dias_anuales": AGUINALDO_DIAS_MIN,
                "proporcional": aguinaldo_proporcional,
                "ya_pagado": round(aguinaldo_ya_pagado, 2),
                "pendiente": round(aguinaldo_pendiente, 2),
                "exento": round(aguinaldo_exento, 2),
                "gravado": aguinaldo_gravado,
            },
            "ptu_pendiente": round(ptu_pendiente, 2),
            "bono_pendiente": round(bono_pendiente, 2),
        },
        subtotal_partes_proporcionales=subtotal_pp,

        indemnizacion=indemnizacion_data,
        subtotal_indemnizacion=subtotal_indemnizacion,

        prima_antiguedad=prima_antiguedad_data,
        subtotal_prima_antiguedad=subtotal_prima,

        isr_finiquito={
            "total_gravable": total_gravado,
            "total_exento": round(total_exento, 2),
            **isr_calculo,
        },

        total_bruto=total_bruto,
        total_exento=round(total_exento, 2),
        total_gravado=total_gravado,
        isr_retenido=isr_retenido,
        neto_a_pagar=neto_a_pagar,

        resumen={
            "salario_diario": round(salario_diario, 2),
            "antiguedad_anios": round(anios_servicio, 2),
            "tipo_separacion": tipo,
            "subtotal_partes_proporcionales": subtotal_pp,
            "subtotal_indemnizacion": subtotal_indemnizacion,
            "subtotal_prima_antiguedad": subtotal_prima,
            "total_bruto": total_bruto,
            "total_exento": round(total_exento, 2),
            "isr_retenido": isr_retenido,
            "neto_a_pagar": neto_a_pagar,
        },

        advertencias=advertencias,
        notas=notas,
    ).to_dict()


def _descripcion_separacion(tipo: str) -> str:
    descripciones = {
        "renuncia": "Renuncia voluntaria del trabajador",
        "despido_justificado": "Despido con justa causa (Art. 47 LFT)",
        "despido_injustificado": "Despido sin justa causa — derecho a indemnización (Art. 50 LFT)",
        "mutuo_acuerdo": "Separación por mutuo acuerdo entre las partes",
        "muerte": "Fallecimiento del trabajador — beneficiarios reciben prestaciones",
        "jubilacion": "Jubilación del trabajador",
        "incapacidad_total": "Incapacidad permanente total",
        "termino_contrato": "Término natural de contrato por tiempo determinado",
    }
    return descripciones.get(tipo, "Separación laboral")
