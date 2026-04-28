"""
Declaración Anual ISR — Personas Físicas
Art. 150-152 LISR y Anexo 8 RMF 2025.

Cubre los regímenes más comunes:
  - Sueldos y salarios
  - Honorarios (actividades profesionales)
  - Actividades empresariales
  - Arrendamiento
  - Combinación de regímenes

Deducciones personales Art. 151 LISR con límites 2025.
"""
from __future__ import annotations
from dataclasses import dataclass

from app.calculators.isr import TARIFA_ISR_ANUAL_2026, _aplicar_tarifa as _tarifa_isr
from app.utils.constantes_fiscales import UMA_ANUAL


# ── Constantes 2025 ───────────────────────────────────────────────────────────

LIMITE_DEDUCCIONES_FACTOR = 0.15          # 15% del ingreso total acumulable — Art. 151 LISR
LIMITE_DEDUCCIONES_UMA = 5 * UMA_ANUAL   # 5 UMAs anuales — $206,629.20 (vigente feb 2025)

# Colegiaturas — Art. 1.8 Decreto (límite por nivel educativo)
LIMITE_COLEGIATURAS = {
    "preescolar":    14_200,
    "primaria":      12_900,
    "secundaria":    19_900,
    "preparatoria":  24_500,
    "profesional_tecnico": 17_100,
}

# Intereses reales hipotecarios — crédito máximo deducible
LIMITE_CREDITO_HIPOTECARIO_UDIS = 750_000  # UDIS — ~$5.5M MXN aprox


# ── Resultado ─────────────────────────────────────────────────────────────────

@dataclass
class ResultadoDeclaracionAnualPF:
    # Ingresos
    ingresos_sueldos: float
    ingresos_honorarios: float
    ingresos_arrendamiento: float
    ingresos_actividad_empresarial: float
    ingresos_intereses: float
    ingresos_dividendos: float
    ingresos_otros: float
    total_ingresos_acumulables: float

    # Deducciones personales
    deducciones_medicas: float
    gastos_hospitalarios: float
    primas_gmm: float
    intereses_hipotecarios_reales: float
    donativos: float
    aportaciones_afore: float
    colegiaturas: float
    total_deducciones_declaradas: float
    limite_deducciones: float
    deducciones_aplicables: float  # mínimo entre declaradas y límite

    # Base y cálculo
    base_gravable: float
    isr_del_ejercicio: float
    retenciones_sueldos: float
    pagos_provisionales: float
    subsidio_empleo_acreditado: float
    total_acreditable: float

    # Resultado final
    saldo_cargo: float    # > 0 = a pagar
    saldo_favor: float    # > 0 = devolución
    resultado: str        # "cargo" | "favor" | "equilibrio"

    # Metadata
    fundamento: str
    tasa_efectiva: float
    regimen_predominante: str


def calcular_declaracion_anual_pf(
    # Ingresos por tipo (anuales, pesos MXN)
    ingresos_sueldos: float = 0.0,
    ingresos_honorarios: float = 0.0,
    ingresos_arrendamiento: float = 0.0,
    ingresos_actividad_empresarial: float = 0.0,
    ingresos_intereses: float = 0.0,
    ingresos_dividendos: float = 0.0,
    ingresos_otros: float = 0.0,
    # Retenciones y pagos provisionales (anuales)
    retenciones_sueldos: float = 0.0,
    pagos_provisionales: float = 0.0,
    subsidio_empleo_acreditado: float = 0.0,
    # Deducciones personales Art. 151 LISR
    deducciones_medicas: float = 0.0,         # Honorarios médicos, dentista, psicólogo
    gastos_hospitalarios: float = 0.0,
    primas_gmm: float = 0.0,                   # Prima seguro gastos médicos mayores
    intereses_hipotecarios_reales: float = 0.0,
    donativos: float = 0.0,
    aportaciones_afore: float = 0.0,
    colegiaturas: float = 0.0,
    # Nivel educativo para validar límite de colegiaturas
    nivel_educativo: str = "preparatoria",
) -> ResultadoDeclaracionAnualPF:

    # ── 1. Total ingresos acumulables ─────────────────────────────────────────
    total_ingresos = (
        ingresos_sueldos
        + ingresos_honorarios
        + ingresos_arrendamiento
        + ingresos_actividad_empresarial
        + ingresos_intereses
        + ingresos_dividendos
        + ingresos_otros
    )

    # ── 2. Límite de deducciones personales ──────────────────────────────────
    # Art. 151 LISR: el menor de 15% del ingreso total o 5 UMA anuales
    limite_por_porcentaje = total_ingresos * LIMITE_DEDUCCIONES_FACTOR
    limite_deducciones = min(limite_por_porcentaje, LIMITE_DEDUCCIONES_UMA)

    # Validar colegiaturas contra límite del nivel educativo
    limite_colegiatura_nivel = LIMITE_COLEGIATURAS.get(nivel_educativo.lower(), 24_500)
    colegiaturas_aplicables = min(colegiaturas, limite_colegiatura_nivel)

    # Donativos: máx 7% del ingreso total acumulable
    donativos_aplicables = min(donativos, total_ingresos * 0.07)

    # AFORE: máx 10% del ingreso acumulable, máx 5 UMA anuales
    afore_aplicables = min(aportaciones_afore, total_ingresos * 0.10, 5 * UMA_ANUAL)

    total_deducciones_declaradas = (
        deducciones_medicas
        + gastos_hospitalarios
        + primas_gmm
        + intereses_hipotecarios_reales
        + donativos_aplicables
        + afore_aplicables
        + colegiaturas_aplicables
    )

    # Aplicar límite global
    deducciones_aplicables = min(total_deducciones_declaradas, limite_deducciones)

    # ── 3. Base gravable ─────────────────────────────────────────────────────
    base_gravable = max(0.0, total_ingresos - deducciones_aplicables)

    # ── 4. ISR del ejercicio — tarifa Art. 152 LISR ──────────────────────────
    isr_ejercicio = _tarifa_isr(base_gravable, TARIFA_ISR_ANUAL_2026)["impuesto"]

    # ── 5. Acreditamientos ───────────────────────────────────────────────────
    total_acreditable = retenciones_sueldos + pagos_provisionales + subsidio_empleo_acreditado
    diferencia = isr_ejercicio - total_acreditable

    saldo_cargo = max(0.0, diferencia)
    saldo_favor = max(0.0, -diferencia)

    if saldo_cargo > 0:
        resultado = "cargo"
    elif saldo_favor > 0:
        resultado = "favor"
    else:
        resultado = "equilibrio"

    # Tasa efectiva
    tasa_efectiva = (isr_ejercicio / total_ingresos * 100) if total_ingresos > 0 else 0.0

    # Régimen predominante
    ingresos_map = {
        "Sueldos y Salarios": ingresos_sueldos,
        "Honorarios": ingresos_honorarios,
        "Arrendamiento": ingresos_arrendamiento,
        "Actividad Empresarial": ingresos_actividad_empresarial,
        "Intereses": ingresos_intereses,
        "Dividendos": ingresos_dividendos,
        "Otros": ingresos_otros,
    }
    regimen_predominante = max(ingresos_map, key=lambda k: ingresos_map[k])

    return ResultadoDeclaracionAnualPF(
        ingresos_sueldos=ingresos_sueldos,
        ingresos_honorarios=ingresos_honorarios,
        ingresos_arrendamiento=ingresos_arrendamiento,
        ingresos_actividad_empresarial=ingresos_actividad_empresarial,
        ingresos_intereses=ingresos_intereses,
        ingresos_dividendos=ingresos_dividendos,
        ingresos_otros=ingresos_otros,
        total_ingresos_acumulables=round(total_ingresos, 2),
        deducciones_medicas=deducciones_medicas,
        gastos_hospitalarios=gastos_hospitalarios,
        primas_gmm=primas_gmm,
        intereses_hipotecarios_reales=intereses_hipotecarios_reales,
        donativos=donativos_aplicables,
        aportaciones_afore=afore_aplicables,
        colegiaturas=colegiaturas_aplicables,
        total_deducciones_declaradas=round(total_deducciones_declaradas, 2),
        limite_deducciones=round(limite_deducciones, 2),
        deducciones_aplicables=round(deducciones_aplicables, 2),
        base_gravable=round(base_gravable, 2),
        isr_del_ejercicio=round(isr_ejercicio, 2),
        retenciones_sueldos=retenciones_sueldos,
        pagos_provisionales=pagos_provisionales,
        subsidio_empleo_acreditado=subsidio_empleo_acreditado,
        total_acreditable=round(total_acreditable, 2),
        saldo_cargo=round(saldo_cargo, 2),
        saldo_favor=round(saldo_favor, 2),
        resultado=resultado,
        tasa_efectiva=round(tasa_efectiva, 2),
        regimen_predominante=regimen_predominante,
        fundamento="Art. 150-152 LISR · Art. 151 LISR (ded. personales) · Anexo 8 RMF 2025",
    )
