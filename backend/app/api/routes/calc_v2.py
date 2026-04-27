"""
Endpoints FastAPI para calculadoras fiscales — v2
===================================================
Reemplaza/complementa /api/routes/calc.py con validación Pydantic v2,
respuestas estandarizadas y manejo de errores consistente.
"""
from __future__ import annotations
import logging
from datetime import date
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.calculators.isr_pf import calcular_isr_pf
from app.calculators.isr_pm import calcular_isr_pm
from app.calculators.iva import calcular_iva
from app.calculators.ieps import calcular_ieps, listar_categorias_ieps
from app.calculators.imss import calcular_cuotas_imss, calcular_sdi_completo
from app.calculators.nomina import calcular_nomina
from app.calculators.finiquito import calcular_finiquito
from app.schemas.comunes import (
    DatosTrabajador, DatosEmpleador, DatosContribuyente,
    RespuestaCalculo, ErrorValidacion,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/calc", tags=["Calculadoras Fiscales v2"])


# ══════════════════════════════════════════════════════════════════════════
# ISR PERSONAS FÍSICAS
# ══════════════════════════════════════════════════════════════════════════

class ISRPFRequest(BaseModel):
    contribuyente: Optional[DatosContribuyente] = None
    ingresos_mensuales: float = Field(..., ge=0, description="Ingresos brutos del período")
    regimen: Literal[
        "sueldos", "honorarios", "actividades_empresariales",
        "arrendamiento", "resico_pf"
    ] = "sueldos"
    deducciones_mensuales: float = Field(0, ge=0, description="Deducciones autorizadas (honorarios/AE)")
    deducciones_personales_anuales: float = Field(0, ge=0, description="Para cálculo anual")
    periodo: Literal["mensual", "anual"] = "mensual"
    incluye_subsidio_empleo: bool = True
    usar_deduccion_ciega_arrendamiento: bool = True
    ingresos_acumulados_anio: float = Field(0, ge=0, description="Para verificar límite RESICO")


@router.post("/isr-pf", response_model=RespuestaCalculo, summary="Calcular ISR Persona Física")
async def isr_pf_endpoint(req: ISRPFRequest):
    try:
        logger.info(f"ISR PF — régimen={req.regimen}, ingresos={req.ingresos_mensuales}")
        datos = calcular_isr_pf(
            ingresos_mensuales=req.ingresos_mensuales,
            regimen=req.regimen,
            deducciones_mensuales=req.deducciones_mensuales,
            periodo=req.periodo,
            deducciones_personales_anuales=req.deducciones_personales_anuales,
            ingresos_acumulados_anio=req.ingresos_acumulados_anio,
            usar_deduccion_ciega_arrendamiento=req.usar_deduccion_ciega_arrendamiento,
            incluye_subsidio_empleo=req.incluye_subsidio_empleo,
        )
        return RespuestaCalculo.exitosa(
            datos=datos,
            fundamento=datos.get("fundamento", []),
        )
    except Exception as e:
        logger.exception(f"Error ISR PF: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# ISR PERSONAS MORALES
# ══════════════════════════════════════════════════════════════════════════

class ISRPMRequest(BaseModel):
    contribuyente: Optional[DatosContribuyente] = None
    ingresos_acumulados: float = Field(..., ge=0)
    coeficiente_utilidad: float = Field(0.20, ge=0, le=1)
    mes: int = Field(1, ge=1, le=12)
    regimen: Literal["general", "resico_pm"] = "general"
    pagos_provisionales_previos: float = Field(0, ge=0)
    retenciones_acreditables: float = Field(0, ge=0)
    perdidas_fiscales_pendientes: float = Field(0, ge=0)
    actividad: str = "default"
    es_calculo_anual: bool = False
    deducciones_autorizadas_anual: float = Field(0, ge=0)
    depreciaciones_anual: float = Field(0, ge=0)
    ptu_pagada: float = Field(0, ge=0)


@router.post("/isr-pm", response_model=RespuestaCalculo, summary="Calcular ISR Persona Moral")
async def isr_pm_endpoint(req: ISRPMRequest):
    try:
        logger.info(f"ISR PM — régimen={req.regimen}, mes={req.mes}")
        datos = calcular_isr_pm(
            ingresos_acumulados=req.ingresos_acumulados,
            coeficiente_utilidad=req.coeficiente_utilidad,
            mes=req.mes,
            regimen=req.regimen,
            pagos_provisionales_previos=req.pagos_provisionales_previos,
            retenciones_acreditables=req.retenciones_acreditables,
            perdidas_fiscales_pendientes=req.perdidas_fiscales_pendientes,
            actividad=req.actividad,
            es_calculo_anual=req.es_calculo_anual,
            deducciones_autorizadas_anual=req.deducciones_autorizadas_anual,
            depreciaciones_anual=req.depreciaciones_anual,
            ptu_pagada=req.ptu_pagada,
        )
        return RespuestaCalculo.exitosa(datos=datos, fundamento=datos.get("fundamento", []))
    except Exception as e:
        logger.exception(f"Error ISR PM: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# IVA
# ══════════════════════════════════════════════════════════════════════════

class IVARequest(BaseModel):
    contribuyente: Optional[DatosContribuyente] = None
    # Ventas
    ventas_16: float = Field(0, ge=0)
    ventas_8_frontera: float = Field(0, ge=0)
    ventas_0: float = Field(0, ge=0)
    ventas_exentas: float = Field(0, ge=0)
    # Compras
    compras_16_acreditables: float = Field(0, ge=0)
    compras_8_acreditables: float = Field(0, ge=0)
    compras_0: float = Field(0, ge=0)
    compras_exentas: float = Field(0, ge=0)
    iva_pagado_importaciones: float = Field(0, ge=0)
    # Retenciones
    iva_retenido_a_terceros: float = Field(0, ge=0)
    iva_retenido_por_terceros: float = Field(0, ge=0)
    # Saldo previo
    saldo_favor_anterior: float = Field(0, ge=0)
    periodo: Literal["mensual", "anual"] = "mensual"
    aplicar_frontera: bool = False


@router.post("/iva", response_model=RespuestaCalculo, summary="Calcular IVA")
async def iva_endpoint(req: IVARequest):
    try:
        logger.info(f"IVA — período={req.periodo}, frontera={req.aplicar_frontera}")
        datos = calcular_iva(**req.model_dump(exclude={"contribuyente"}))
        return RespuestaCalculo.exitosa(datos=datos, fundamento=datos.get("fundamento", []))
    except Exception as e:
        logger.exception(f"Error IVA: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# IEPS
# ══════════════════════════════════════════════════════════════════════════

class IEPSRequest(BaseModel):
    categoria: str = Field(..., description="Clave de categoría (ver /ieps/categorias)")
    precio_enajenacion: float = Field(..., ge=0)
    cantidad_litros: float = Field(0, ge=0, description="Para combustibles y bebidas")
    cantidad_cigarros: int = Field(0, ge=0, description="Para tabacos labrados")
    incluir_iva: bool = True
    es_acreditable: bool = False


@router.get("/ieps/categorias", summary="Listar categorías IEPS disponibles")
async def ieps_categorias():
    return {"success": True, "categorias": listar_categorias_ieps()}


@router.post("/ieps", response_model=RespuestaCalculo, summary="Calcular IEPS")
async def ieps_endpoint(req: IEPSRequest):
    try:
        logger.info(f"IEPS — categoría={req.categoria}")
        datos = calcular_ieps(**req.model_dump())
        if datos.get("error"):
            return RespuestaCalculo.con_errores([
                ErrorValidacion(campo="categoria", motivo=datos["mensaje"])
            ])
        return RespuestaCalculo.exitosa(datos=datos, fundamento=[datos.get("fundamento", "")])
    except Exception as e:
        logger.exception(f"Error IEPS: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# IMSS / INFONAVIT
# ══════════════════════════════════════════════════════════════════════════

class IMSSRequest(BaseModel):
    salario_diario_integrado: float = Field(..., gt=0)
    salario_diario_base: Optional[float] = None
    prima_riesgo_trabajo: float = Field(0.0054355, ge=0, le=0.15)
    clase_riesgo: Optional[Literal["I", "II", "III", "IV", "V"]] = None
    zona_norte: bool = False


@router.post("/imss", response_model=RespuestaCalculo, summary="Calcular cuotas IMSS/INFONAVIT")
async def imss_endpoint(req: IMSSRequest):
    try:
        logger.info(f"IMSS — SDI={req.salario_diario_integrado}")
        datos = calcular_cuotas_imss(**req.model_dump())
        return RespuestaCalculo.exitosa(datos=datos, fundamento=datos.get("fundamento", []))
    except Exception as e:
        logger.exception(f"Error IMSS: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


class SDIRequest(BaseModel):
    salario_diario_base: float = Field(..., gt=0)
    aguinaldo_dias: int = Field(15, ge=15, le=365)
    prima_vacacional_pct: float = Field(0.25, ge=0.25, le=1)
    dias_vacaciones: int = Field(12, ge=6, le=365)
    prestaciones_adicionales_anuales: float = Field(0, ge=0)


@router.post("/imss/sdi", summary="Calcular SDI desde salario base + prestaciones")
async def sdi_endpoint(req: SDIRequest):
    try:
        datos = calcular_sdi_completo(**req.model_dump())
        return {"success": True, "datos": datos}
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# NÓMINA
# ══════════════════════════════════════════════════════════════════════════

class NominaRequest(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Identificación (opcional para cálculo, requerido para CFDI)
    trabajador: Optional[DatosTrabajador] = None
    empleador: Optional[DatosEmpleador] = None

    # Salario y período
    salario_mensual_bruto: float = Field(..., gt=0)
    periodo: Literal["diario", "semanal", "catorcenal", "quincenal", "decenal", "mensual"] = "mensual"
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    fecha_pago: Optional[date] = None

    # Antigüedad (impacta vacaciones)
    anios_antiguedad: int = Field(1, ge=0, le=70)

    # Percepciones extras
    otras_percepciones_gravadas: float = Field(0, ge=0)
    otras_percepciones_exentas: float = Field(0, ge=0)
    vales_despensa: float = Field(0, ge=0)
    horas_extras_dobles: float = Field(0, ge=0)
    horas_extras_triples: float = Field(0, ge=0)
    fondo_ahorro_patron: float = Field(0, ge=0)
    ptu: float = Field(0, ge=0)
    bono_productividad: float = Field(0, ge=0)

    # Deducciones extras
    pension_alimenticia_pct: float = Field(0, ge=0, le=1)
    fonacot_descuento: float = Field(0, ge=0)
    prestamo_patron: float = Field(0, ge=0)
    infonavit_descuento_credito: float = Field(0, ge=0)
    otras_deducciones: float = Field(0, ge=0)

    # Riesgo
    prima_riesgo_trabajo: float = Field(0.0054355, ge=0, le=0.15)
    clase_riesgo: Optional[Literal["I", "II", "III", "IV", "V"]] = None


@router.post("/nomina", response_model=RespuestaCalculo, summary="Calcular nómina completa")
async def nomina_endpoint(req: NominaRequest):
    try:
        logger.info(f"Nómina — período={req.periodo}, salario={req.salario_mensual_bruto}")

        kwargs = req.model_dump(exclude_none=True, exclude={"trabajador", "empleador"})
        kwargs["datos_trabajador"] = req.trabajador.model_dump() if req.trabajador else None
        kwargs["datos_empleador"] = req.empleador.model_dump() if req.empleador else None

        # Convertir dates a strings para compatibilidad
        for key in ("fecha_inicio", "fecha_fin", "fecha_pago"):
            if key in kwargs and kwargs[key]:
                kwargs[key] = kwargs[key].isoformat()

        datos = calcular_nomina(**kwargs)

        if datos.get("error"):
            return RespuestaCalculo.con_errores([
                ErrorValidacion(campo="general", motivo=datos["mensaje"])
            ])

        return RespuestaCalculo.exitosa(datos=datos, fundamento=datos.get("fundamento", []))
    except Exception as e:
        logger.exception(f"Error Nómina: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# FINIQUITO
# ══════════════════════════════════════════════════════════════════════════

class FiniquitoRequest(BaseModel):
    trabajador: Optional[DatosTrabajador] = None
    empleador: Optional[DatosEmpleador] = None

    salario_diario: float = Field(..., gt=0)

    # Modo 1: con fechas
    fecha_ingreso: Optional[date] = None
    fecha_separacion: Optional[date] = None

    # Modo 2: con valores directos
    anios_servicio: Optional[float] = Field(None, ge=0)
    dias_trabajados_anio: Optional[int] = Field(None, ge=0, le=366)

    tipo_separacion: Literal[
        "renuncia", "despido_justificado", "despido_injustificado",
        "mutuo_acuerdo", "muerte", "jubilacion", "incapacidad_total",
        "termino_contrato"
    ] = "renuncia"

    vacaciones_gozadas: int = Field(0, ge=0)
    dias_pendientes_pago: int = Field(0, ge=0)
    aguinaldo_ya_pagado: float = Field(0, ge=0)
    ptu_pendiente: float = Field(0, ge=0)
    bono_pendiente: float = Field(0, ge=0)
    meses_salarios_caidos: float = Field(0, ge=0, le=12)


@router.post("/finiquito", response_model=RespuestaCalculo, summary="Calcular finiquito/liquidación")
async def finiquito_endpoint(req: FiniquitoRequest):
    try:
        logger.info(f"Finiquito — tipo={req.tipo_separacion}")

        kwargs = req.model_dump(exclude_none=True, exclude={"trabajador", "empleador"})
        kwargs["datos_trabajador"] = req.trabajador.model_dump() if req.trabajador else None
        kwargs["datos_empleador"] = req.empleador.model_dump() if req.empleador else None

        for key in ("fecha_ingreso", "fecha_separacion"):
            if key in kwargs and kwargs[key]:
                kwargs[key] = kwargs[key].isoformat()

        datos = calcular_finiquito(**kwargs)

        if datos.get("error"):
            return RespuestaCalculo.con_errores([
                ErrorValidacion(campo="general", motivo=datos["mensaje"])
            ])

        return RespuestaCalculo.exitosa(datos=datos, fundamento=datos.get("fundamento", []))
    except Exception as e:
        logger.exception(f"Error Finiquito: {e}")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════
# Health check
# ══════════════════════════════════════════════════════════════════════════

@router.get("/health", summary="Health check de calculadoras")
async def health():
    return {
        "status": "ok",
        "calculadoras_disponibles": [
            "isr-pf", "isr-pm", "iva", "ieps", "imss", "imss/sdi",
            "nomina", "finiquito",
        ],
        "ejercicio_fiscal": 2025,
        "version": "2.0",
    }
