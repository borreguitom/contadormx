"""
Nómina Completa — Versión definitiva
======================================
Genera comprobante de nómina con TODOS los conceptos legales:

PERCEPCIONES:
  - Salario base proporcional al período
  - Partes proporcionales (aguinaldo, vacaciones, prima vacacional)
  - Vales de despensa (con exención 40% UMA)
  - Horas extras (Art. 67 LFT — 1.5x primeras 9hr, 2x adicionales)
  - Otras percepciones (bonos, comisiones, premios)
  - PTU (Art. 117 LFT — 10% utilidad fiscal)
  - Fondo de ahorro patronal

DEDUCCIONES:
  - ISR (Art. 96 LISR con subsidio empleo)
  - Cuotas IMSS trabajador (Art. 25 LSS)
  - INFONAVIT trabajador (descuento por crédito)
  - Pensión alimenticia (orden judicial)
  - FONACOT
  - Préstamo del patrón
  - Otras deducciones

CONCEPTOS PATRONALES (no afectan al neto trabajador):
  - IMSS patronal
  - INFONAVIT patronal
  - Riesgo de trabajo
  - Costo total para la empresa
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from datetime import date

from app.utils.constantes_fiscales import (
    UMA_DIARIA,
    UMA_MENSUAL,
    VALES_DESPENSA_EXENTOS,
    AGUINALDO_DIAS_MIN,
    PRIMA_VACACIONAL_PCT_MIN,
    EJERCICIO_FISCAL_VIGENTE,
    dias_vacaciones,
)
from .isr_pf import calcular_isr_pf
from .imss import calcular_cuotas_imss, calcular_sdi_completo


# ══════════════════════════════════════════════════════════════════════════
# Configuración de períodos
# ══════════════════════════════════════════════════════════════════════════

DIAS_PERIODO = {
    "diario": 1,
    "semanal": 7,
    "catorcenal": 14,
    "quincenal": 15,
    "decenal": 10,
    "mensual": 30,
}


# ══════════════════════════════════════════════════════════════════════════
# Resultado estructurado
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoNomina:
    # Identificación
    datos_trabajador: dict
    datos_empleador: dict
    periodo_pago: dict
    ejercicio: int
    fundamento: list[str]

    # Percepciones
    percepciones: dict
    total_percepciones: float
    total_percepciones_gravadas: float
    total_percepciones_exentas: float

    # SDI
    sdi: dict

    # Deducciones
    deducciones: dict
    total_deducciones: float

    # Resultado
    neto_a_pagar: float

    # Costo empresa
    costo_empresa: dict

    # Resumen
    resumen: dict

    advertencias: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════
# Cálculo principal
# ══════════════════════════════════════════════════════════════════════════

def calcular_nomina(
    salario_mensual_bruto: float,
    *,
    # Período
    periodo: Literal["diario", "semanal", "catorcenal", "quincenal", "decenal", "mensual"] = "mensual",
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    fecha_pago: Optional[str] = None,

    # Datos identificatorios (opcionales para cálculo, requeridos para CFDI)
    datos_trabajador: Optional[dict] = None,
    datos_empleador: Optional[dict] = None,

    # Antigüedad (afecta vacaciones)
    anios_antiguedad: int = 1,

    # Percepciones adicionales
    otras_percepciones_gravadas: float = 0.0,
    otras_percepciones_exentas: float = 0.0,
    vales_despensa: float = 0.0,
    horas_extras_dobles: float = 0.0,        # primeras 9 hrs / semana
    horas_extras_triples: float = 0.0,       # adicionales (excedente 9 hrs)
    fondo_ahorro_patron: float = 0.0,
    ptu: float = 0.0,
    bono_productividad: float = 0.0,

    # Deducciones adicionales
    pension_alimenticia_pct: float = 0.0,    # 0.0 a 1.0 (porcentaje del salario)
    fonacot_descuento: float = 0.0,
    prestamo_patron: float = 0.0,
    infonavit_descuento_credito: float = 0.0,
    otras_deducciones: float = 0.0,

    # IMSS
    prima_riesgo_trabajo: float = 0.0054355,
    clase_riesgo: Optional[str] = None,
) -> dict:
    """
    Calcula nómina completa con TODOS los conceptos legales.

    Args:
        salario_mensual_bruto: Salario base mensual (sueldo nominal)
        periodo: Tipo de período de pago
        anios_antiguedad: Para calcular días de vacaciones correctos
        otras_percepciones_gravadas: Bonos, comisiones gravadas
        otras_percepciones_exentas: Premios puntualidad/asistencia (parcialmente exentos)
        vales_despensa: Monto de vales (40% UMA exento)
        horas_extras_dobles: Cantidad de horas extras al doble (1.5x normal)
        horas_extras_triples: Cantidad de horas extras al triple (2x normal)
        ptu: Participación de utilidades
        pension_alimenticia_pct: % del salario para pensión alimenticia (0.0 - 1.0)
    """
    advertencias = []
    notas = []

    # Validaciones
    if salario_mensual_bruto <= 0:
        return {"error": True, "mensaje": "El salario mensual debe ser mayor a 0"}

    if periodo not in DIAS_PERIODO:
        return {
            "error": True,
            "mensaje": f"Período inválido. Use: {list(DIAS_PERIODO.keys())}"
        }

    dias = DIAS_PERIODO[periodo]
    factor = dias / 30  # factor para escalar de mensual al período
    salario_diario = salario_mensual_bruto / 30

    # ═════════════════════════════════════════════════════════════
    # 1. SALARIO PROPORCIONAL AL PERÍODO
    # ═════════════════════════════════════════════════════════════

    salario_periodo = round(salario_diario * dias, 2)

    # ═════════════════════════════════════════════════════════════
    # 2. INTEGRACIÓN SDI (Art. 27 LSS) — usa antigüedad correcta
    # ═════════════════════════════════════════════════════════════

    dias_vac_anuales = dias_vacaciones(anios_antiguedad)
    sdi_info = calcular_sdi_completo(
        salario_diario,
        aguinaldo_dias=AGUINALDO_DIAS_MIN,
        prima_vacacional_pct=PRIMA_VACACIONAL_PCT_MIN,
        dias_vacaciones=dias_vac_anuales,
    )
    sdi = sdi_info["sdi_calculado"]

    # ═════════════════════════════════════════════════════════════
    # 3. VALES DE DESPENSA (Art. 93-XIV LISR — exento 40% UMA)
    # ═════════════════════════════════════════════════════════════

    vales_exencion_periodo = round(VALES_DESPENSA_EXENTOS * factor, 2)
    vales_exentos = min(vales_despensa, vales_exencion_periodo)
    vales_gravados = max(vales_despensa - vales_exentos, 0)

    if vales_despensa > vales_exencion_periodo:
        notas.append(
            f"Vales gravados: ${vales_gravados:,.2f} "
            f"(excedente sobre 40% UMA = ${vales_exencion_periodo:,.2f})"
        )

    # ═════════════════════════════════════════════════════════════
    # 4. HORAS EXTRAS (Art. 67 LFT)
    # ═════════════════════════════════════════════════════════════
    # - Primeras 9 hrs/semana al doble (1.5x normal = 100% extra)
    # - Adicionales al triple (2x normal = 200% extra)
    # Exención ISR: 50% hasta 5 UMAs (Art. 93-I LISR)

    salario_horario = salario_diario / 8  # 8 horas/día
    importe_he_dobles = round(horas_extras_dobles * salario_horario * 2, 2)
    importe_he_triples = round(horas_extras_triples * salario_horario * 3, 2)
    importe_he_total = round(importe_he_dobles + importe_he_triples, 2)

    # Exención de horas extras dobles
    he_dobles_exencion_max = UMA_DIARIA * 5
    he_dobles_exentas = min(importe_he_dobles * 0.5, he_dobles_exencion_max)
    he_dobles_gravadas = importe_he_dobles - he_dobles_exentas
    # Las triples son 100% gravadas (Art. 93-I LISR último párrafo)
    he_triples_gravadas = importe_he_triples

    if importe_he_total > 0:
        notas.append(
            f"Horas extras: {horas_extras_dobles}h dobles + {horas_extras_triples}h triples = "
            f"${importe_he_total:,.2f}. Exentas: ${he_dobles_exentas:,.2f}"
        )

    # ═════════════════════════════════════════════════════════════
    # 5. PARTES PROPORCIONALES (sólo informativas, ya en SDI)
    # ═════════════════════════════════════════════════════════════

    # Provisión proporcional al período
    aguinaldo_prop = round(salario_diario * AGUINALDO_DIAS_MIN / 365 * dias, 2)
    vacaciones_prop = round(salario_diario * dias_vac_anuales / 365 * dias, 2)
    prima_vac_prop = round(vacaciones_prop * PRIMA_VACACIONAL_PCT_MIN, 2)

    # ═════════════════════════════════════════════════════════════
    # 6. TOTAL PERCEPCIONES
    # ═════════════════════════════════════════════════════════════

    total_gravadas = round(
        salario_periodo +
        otras_percepciones_gravadas * factor +
        vales_gravados +
        he_dobles_gravadas +
        he_triples_gravadas +
        ptu +
        bono_productividad,
        2
    )

    total_exentas = round(
        otras_percepciones_exentas * factor +
        vales_exentos +
        he_dobles_exentas,
        2
    )

    total_percepciones = round(total_gravadas + total_exentas, 2)

    # ═════════════════════════════════════════════════════════════
    # 7. ISR (Art. 96 LISR)
    # ═════════════════════════════════════════════════════════════
    # Base ISR mensual = percepciones gravadas escaladas a mensual
    base_isr_mensual = total_gravadas / factor if factor > 0 else 0

    isr_resultado = calcular_isr_pf(
        ingresos_mensuales=base_isr_mensual,
        regimen="sueldos",
        periodo="mensual",
        incluye_subsidio_empleo=True,
    )

    isr_periodo = round(isr_resultado["isr_a_cargo"] * factor, 2)
    subsidio_periodo = round(isr_resultado["subsidio_empleo"]["subsidio"] * factor, 2)

    # ═════════════════════════════════════════════════════════════
    # 8. CUOTAS IMSS TRABAJADOR
    # ═════════════════════════════════════════════════════════════

    imss_resultado = calcular_cuotas_imss(
        salario_diario_integrado=sdi,
        prima_riesgo_trabajo=prima_riesgo_trabajo,
        clase_riesgo=clase_riesgo,
        salario_diario_base=salario_diario,
    )

    cuota_imss_trabajador_mensual = imss_resultado["total_cuota_trabajador"]
    cuota_imss_trabajador_periodo = round(cuota_imss_trabajador_mensual * factor, 2)

    # ═════════════════════════════════════════════════════════════
    # 9. PENSIÓN ALIMENTICIA Y OTROS DESCUENTOS
    # ═════════════════════════════════════════════════════════════

    pension_alimenticia = round(salario_periodo * pension_alimenticia_pct, 2)
    fonacot_periodo = round(fonacot_descuento * factor, 2)
    prestamo_periodo = round(prestamo_patron * factor, 2)
    infonavit_credito_periodo = round(infonavit_descuento_credito * factor, 2)
    otras_ded_periodo = round(otras_deducciones * factor, 2)

    # ═════════════════════════════════════════════════════════════
    # 10. TOTAL DEDUCCIONES Y NETO
    # ═════════════════════════════════════════════════════════════

    total_deducciones = round(
        isr_periodo +
        cuota_imss_trabajador_periodo +
        pension_alimenticia +
        fonacot_periodo +
        prestamo_periodo +
        infonavit_credito_periodo +
        otras_ded_periodo,
        2
    )

    neto_a_pagar = round(total_percepciones - total_deducciones + subsidio_periodo, 2)

    # ═════════════════════════════════════════════════════════════
    # 11. COSTO EMPRESA
    # ═════════════════════════════════════════════════════════════

    cuota_imss_patronal_periodo = round(imss_resultado["total_cuota_patronal"] * factor, 2)
    infonavit_patronal_periodo = round(imss_resultado["infonavit"]["monto_patronal"] * factor, 2)

    costo_total_empresa = round(
        total_percepciones +
        cuota_imss_patronal_periodo +
        infonavit_patronal_periodo,
        2
    )

    # ═════════════════════════════════════════════════════════════
    # 12. ARMAR RESULTADO COMPLETO
    # ═════════════════════════════════════════════════════════════

    return ResultadoNomina(
        datos_trabajador=datos_trabajador or {},
        datos_empleador=datos_empleador or {},
        periodo_pago={
            "tipo": periodo,
            "dias": dias,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_pago": fecha_pago,
        },
        ejercicio=EJERCICIO_FISCAL_VIGENTE,
        fundamento=[
            "Art. 96 LISR (retención ISR)",
            "Decreto Subsidio para el Empleo",
            "Art. 25-168 LSS (cuotas IMSS)",
            "Art. 27 LSS (integración SDI)",
            "Art. 29 Ley INFONAVIT",
            "Art. 93 LISR (exenciones)",
            "Art. 67, 87, 76, 80 LFT (prestaciones)",
        ],

        percepciones={
            "salario_base": {
                "salario_mensual": round(salario_mensual_bruto, 2),
                "salario_diario": round(salario_diario, 2),
                "dias_periodo": dias,
                "monto_periodo": salario_periodo,
            },
            "horas_extras": {
                "dobles": {
                    "horas": horas_extras_dobles,
                    "importe": importe_he_dobles,
                    "exento": round(he_dobles_exentas, 2),
                    "gravado": round(he_dobles_gravadas, 2),
                },
                "triples": {
                    "horas": horas_extras_triples,
                    "importe": importe_he_triples,
                    "exento": 0.0,
                    "gravado": importe_he_triples,
                },
                "total": importe_he_total,
            },
            "vales_despensa": {
                "monto_total": round(vales_despensa, 2),
                "exento": round(vales_exentos, 2),
                "gravado": round(vales_gravados, 2),
            },
            "ptu": round(ptu, 2),
            "bono_productividad": round(bono_productividad, 2),
            "fondo_ahorro_patron": round(fondo_ahorro_patron, 2),
            "otras_percepciones_gravadas": round(otras_percepciones_gravadas * factor, 2),
            "otras_percepciones_exentas": round(otras_percepciones_exentas * factor, 2),
            "partes_proporcionales_informativas": {
                "aguinaldo_proporcional": aguinaldo_prop,
                "vacaciones_proporcionales": vacaciones_prop,
                "prima_vacacional_proporcional": prima_vac_prop,
                "nota": "Estas partes ya están integradas en el SDI para IMSS, son informativas.",
            },
        },
        total_percepciones=total_percepciones,
        total_percepciones_gravadas=total_gravadas,
        total_percepciones_exentas=total_exentas,

        sdi=sdi_info,

        deducciones={
            "isr": {
                "base_gravable_periodo": round(total_gravadas, 2),
                "base_gravable_mensual_proyectado": round(base_isr_mensual, 2),
                "isr_determinado_periodo": round(isr_resultado["isr_determinado"] * factor, 2),
                "subsidio_empleo": subsidio_periodo,
                "isr_a_retener": isr_periodo,
                "tasa_efectiva_pct": isr_resultado["tasa_efectiva_pct"],
                "fundamento": "Art. 96 LISR",
            },
            "imss_trabajador": {
                "cuota_mensual": round(cuota_imss_trabajador_mensual, 2),
                "cuota_periodo": cuota_imss_trabajador_periodo,
                "desglose_mensual": imss_resultado["cuotas_trabajador"],
                "fundamento": "Art. 25-168 LSS",
            },
            "infonavit_credito": {
                "monto": infonavit_credito_periodo,
                "nota": "Solo aplica si trabajador tiene crédito INFONAVIT activo",
            },
            "pension_alimenticia": {
                "porcentaje_aplicado": f"{pension_alimenticia_pct*100:.2f}%",
                "monto": pension_alimenticia,
                "fundamento": "Orden judicial",
            },
            "fonacot": fonacot_periodo,
            "prestamo_patron": prestamo_periodo,
            "otras_deducciones": otras_ded_periodo,
        },
        total_deducciones=total_deducciones,

        neto_a_pagar=neto_a_pagar,

        costo_empresa={
            "salario_base": salario_periodo,
            "imss_patronal_periodo": cuota_imss_patronal_periodo,
            "infonavit_patronal_periodo": infonavit_patronal_periodo,
            "riesgo_trabajo_incluido_en_imss": True,
            "costo_total_para_empresa": costo_total_empresa,
            "factor_de_costo_sobre_salario_base": round(costo_total_empresa / salario_periodo, 4) if salario_periodo > 0 else 0,
        },

        resumen={
            "total_percepciones": total_percepciones,
            "total_deducciones": total_deducciones,
            "subsidio_aplicado": subsidio_periodo,
            "neto_a_pagar": neto_a_pagar,
            "costo_total_empresa": costo_total_empresa,
            "porcentaje_deducciones_sobre_percepciones": round(total_deducciones / total_percepciones * 100, 2) if total_percepciones > 0 else 0,
            "diferencia_costo_vs_neto": round(costo_total_empresa - neto_a_pagar, 2),
        },

        advertencias=advertencias,
        notas=notas,
    ).to_dict()
