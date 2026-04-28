"""
Endpoints directos a las calculadoras — sin pasar por el agente.
Útiles para el frontend de calculadoras dedicado.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from app.calculators.isr import calcular_isr_pf, calcular_isr_pm
from app.calculators.iva import calcular_iva
from app.calculators.imss import calcular_cuotas_imss
from app.calculators.nomina import calcular_nomina
from app.calculators.finiquito import calcular_finiquito
from app.calculators.declaracion_anual import calcular_declaracion_anual_pf
from app.calculators.ieps import calcular_ieps, listar_categorias_ieps as listar_categorias
from app.core.deps import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])


class ISRPFRequest(BaseModel):
    ingresos_mensuales: float
    regimen: str = "sueldos"
    deducciones_mensuales: float = 0.0
    periodo: str = "mensual"


class ISRPMRequest(BaseModel):
    ingresos_acumulados: float
    coeficiente_utilidad: float = 0.20
    pagos_provisionales_previos: float = 0.0
    retenciones: float = 0.0
    mes: int = 1
    regimen: str = "general"


class IVARequest(BaseModel):
    ventas_16: float = 0.0
    ventas_0: float = 0.0
    ventas_exentas: float = 0.0
    compras_16_acreditables: float = 0.0
    compras_0_acreditables: float = 0.0
    compras_exentas: float = 0.0
    saldo_favor_anterior: float = 0.0
    periodo: str = "mensual"


class IMSSRequest(BaseModel):
    salario_diario_integrado: float
    prima_riesgo_trabajo: float = 0.0054355


class NominaRequest(BaseModel):
    salario_mensual_bruto: float
    periodo: str = "mensual"
    otras_percepciones: float = 0.0
    vales_despensa: float = 0.0


class FiniquitoRequest(BaseModel):
    salario_diario: float
    dias_trabajados_anio: int
    anios_servicio: float = 0.0
    tipo_separacion: str = "renuncia"
    vacaciones_gozadas: int = 0


@router.post("/isr/personas-fisicas")
async def calc_isr_pf(req: ISRPFRequest):
    return calcular_isr_pf(
        ingresos_mensuales=req.ingresos_mensuales,
        regimen=req.regimen,
        deducciones_mensuales=req.deducciones_mensuales,
        periodo=req.periodo,
    )


@router.post("/isr/personas-morales")
async def calc_isr_pm(req: ISRPMRequest):
    return calcular_isr_pm(
        ingresos_acumulados=req.ingresos_acumulados,
        coeficiente_utilidad=req.coeficiente_utilidad,
        pagos_provisionales_previos=req.pagos_provisionales_previos,
        retenciones=req.retenciones,
        mes=req.mes,
        regimen=req.regimen,
    )


@router.post("/iva")
async def calc_iva(req: IVARequest):
    return calcular_iva(
        ventas_16=req.ventas_16,
        ventas_0=req.ventas_0,
        ventas_exentas=req.ventas_exentas,
        compras_16_acreditables=req.compras_16_acreditables,
        compras_0_acreditables=req.compras_0_acreditables,
        compras_exentas=req.compras_exentas,
        saldo_favor_anterior=req.saldo_favor_anterior,
        periodo=req.periodo,
    )


@router.post("/imss")
async def calc_imss(req: IMSSRequest):
    return calcular_cuotas_imss(
        salario_diario_integrado=req.salario_diario_integrado,
        prima_riesgo_trabajo=req.prima_riesgo_trabajo,
    )


@router.post("/nomina")
async def calc_nomina(req: NominaRequest):
    return calcular_nomina(
        salario_mensual_bruto=req.salario_mensual_bruto,
        periodo=req.periodo,
        otras_percepciones=req.otras_percepciones,
        vales_despensa=req.vales_despensa,
    )


@router.post("/finiquito")
async def calc_finiquito(req: FiniquitoRequest):
    return calcular_finiquito(
        salario_diario=req.salario_diario,
        dias_trabajados_anio=req.dias_trabajados_anio,
        anios_servicio=req.anios_servicio,
        tipo_separacion=req.tipo_separacion,
        vacaciones_gozadas=req.vacaciones_gozadas,
    )


class DeclaracionAnualPFRequest(BaseModel):
    # Ingresos por tipo (anuales)
    ingresos_sueldos: float = 0.0
    ingresos_honorarios: float = 0.0
    ingresos_arrendamiento: float = 0.0
    ingresos_actividad_empresarial: float = 0.0
    ingresos_intereses: float = 0.0
    ingresos_dividendos: float = 0.0
    ingresos_otros: float = 0.0
    # Retenciones y pagos provisionales
    retenciones_sueldos: float = 0.0
    pagos_provisionales: float = 0.0
    subsidio_empleo_acreditado: float = 0.0
    # Deducciones personales Art. 151 LISR
    deducciones_medicas: float = 0.0
    gastos_hospitalarios: float = 0.0
    primas_gmm: float = 0.0
    intereses_hipotecarios_reales: float = 0.0
    donativos: float = 0.0
    aportaciones_afore: float = 0.0
    colegiaturas: float = 0.0
    nivel_educativo: str = "preparatoria"


class IEPSRequest(BaseModel):
    categoria: str
    base_gravable: float = 0.0
    litros: float = 0.0
    cantidad_cigarros: int = 0
    incluye_iva: bool = False


@router.get("/ieps/categorias")
async def get_ieps_categorias():
    return listar_categorias()


@router.post("/ieps")
async def calc_ieps_endpoint(req: IEPSRequest):
    return calcular_ieps(
        categoria=req.categoria,
        base_gravable=req.base_gravable,
        litros=req.litros,
        cantidad_cigarros=req.cantidad_cigarros,
        incluye_iva=req.incluye_iva,
    )


@router.post("/declaracion-anual/pf")
async def calc_declaracion_anual_pf(req: DeclaracionAnualPFRequest):
    return calcular_declaracion_anual_pf(
        ingresos_sueldos=req.ingresos_sueldos,
        ingresos_honorarios=req.ingresos_honorarios,
        ingresos_arrendamiento=req.ingresos_arrendamiento,
        ingresos_actividad_empresarial=req.ingresos_actividad_empresarial,
        ingresos_intereses=req.ingresos_intereses,
        ingresos_dividendos=req.ingresos_dividendos,
        ingresos_otros=req.ingresos_otros,
        retenciones_sueldos=req.retenciones_sueldos,
        pagos_provisionales=req.pagos_provisionales,
        subsidio_empleo_acreditado=req.subsidio_empleo_acreditado,
        deducciones_medicas=req.deducciones_medicas,
        gastos_hospitalarios=req.gastos_hospitalarios,
        primas_gmm=req.primas_gmm,
        intereses_hipotecarios_reales=req.intereses_hipotecarios_reales,
        donativos=req.donativos,
        aportaciones_afore=req.aportaciones_afore,
        colegiaturas=req.colegiaturas,
        nivel_educativo=req.nivel_educativo,
    )
