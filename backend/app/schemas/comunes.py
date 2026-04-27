"""
Esquemas Pydantic compartidos para calculadoras fiscales
=========================================================
Validación de entrada y serialización de respuestas.
"""
from __future__ import annotations
from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.utils.validators_mx import (
    validar_rfc, validar_nss, validar_curp, validar_clabe,
    detectar_tipo_rfc,
)


# ══════════════════════════════════════════════════════════════════════════
# Datos identificatorios
# ══════════════════════════════════════════════════════════════════════════

class DatosTrabajador(BaseModel):
    """Datos del trabajador para nómina/finiquito."""
    nombre_completo: str = Field(..., min_length=3, max_length=200,
                                 description="Nombre completo legal")
    rfc: str = Field(..., description="RFC con homoclave (13 caracteres)",
                     examples=["PEGJ950101AB1"])
    curp: Optional[str] = Field(None, description="CURP (18 caracteres)")
    nss: str = Field(..., description="NSS IMSS (11 dígitos)",
                     examples=["12345678901"])
    numero_empleado: Optional[str] = Field(None, max_length=50)
    puesto: Optional[str] = Field(None, max_length=100)
    departamento: Optional[str] = Field(None, max_length=100)
    fecha_ingreso: date = Field(..., description="Fecha alta IMSS (YYYY-MM-DD)")
    clabe: Optional[str] = Field(None, description="CLABE bancaria (18 dígitos)")
    banco: Optional[str] = Field(None, max_length=100)

    @field_validator("rfc")
    @classmethod
    def _val_rfc(cls, v: str) -> str:
        v = v.upper().strip()
        if not validar_rfc(v, "pf"):
            raise ValueError(
                f"RFC inválido: '{v}'. Persona física debe tener 13 caracteres."
            )
        return v

    @field_validator("curp")
    @classmethod
    def _val_curp(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.upper().strip()
        if not validar_curp(v):
            raise ValueError(f"CURP inválido: '{v}'. Debe tener 18 caracteres.")
        return v

    @field_validator("nss")
    @classmethod
    def _val_nss(cls, v: str) -> str:
        if not validar_nss(v):
            raise ValueError(f"NSS inválido: '{v}'. Debe tener 11 dígitos.")
        return v.strip()

    @field_validator("clabe")
    @classmethod
    def _val_clabe(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        v = v.strip().replace(" ", "")
        if not validar_clabe(v):
            raise ValueError(f"CLABE inválida: '{v}'. Debe tener 18 dígitos válidos.")
        return v


class DatosEmpleador(BaseModel):
    """Datos del patrón/empleador."""
    razon_social: str = Field(..., min_length=3, max_length=300)
    rfc: str = Field(..., description="RFC empleador (12 PM o 13 PF)")
    registro_patronal: Optional[str] = Field(
        None, description="Registro patronal IMSS",
        examples=["A1234567890"]
    )
    domicilio_fiscal: Optional[str] = Field(None, max_length=500)
    actividad_economica: Optional[str] = Field(None, max_length=200)
    clase_riesgo: Optional[Literal["I", "II", "III", "IV", "V"]] = None
    prima_riesgo_trabajo: float = Field(
        0.0054355, ge=0, le=0.15,
        description="Prima riesgo trabajo (varía 0.5% a 15%). Default = promedio nacional."
    )

    @field_validator("rfc")
    @classmethod
    def _val_rfc_empresa(cls, v: str) -> str:
        v = v.upper().strip()
        tipo = detectar_tipo_rfc(v)
        if tipo is None:
            raise ValueError(
                f"RFC empleador inválido: '{v}'. Debe ser 12 (PM) o 13 (PF) caracteres."
            )
        return v


# ══════════════════════════════════════════════════════════════════════════
# Datos identificatorios para cálculos fiscales (sin necesariamente tener trabajador)
# ══════════════════════════════════════════════════════════════════════════

class DatosContribuyente(BaseModel):
    """Datos básicos de contribuyente para ISR/IVA/IEPS."""
    rfc: str
    nombre_o_razon_social: str = Field(..., min_length=3, max_length=300)
    tipo: Literal["PF", "PM"] = Field(..., description="Persona física o moral")
    actividad_economica: Optional[str] = None
    domicilio_fiscal: Optional[str] = None

    @field_validator("rfc")
    @classmethod
    def _val_rfc(cls, v: str) -> str:
        v = v.upper().strip()
        if not validar_rfc(v):
            raise ValueError(f"RFC inválido: '{v}'.")
        return v


# ══════════════════════════════════════════════════════════════════════════
# Período fiscal
# ══════════════════════════════════════════════════════════════════════════

class PeriodoFiscal(BaseModel):
    """Período de cálculo fiscal."""
    fecha_inicio: date
    fecha_fin: date
    ejercicio: int = Field(..., ge=2020, le=2030, description="Año fiscal")
    mes: Optional[int] = Field(None, ge=1, le=12)
    tipo: Literal["mensual", "bimestral", "trimestral", "anual"] = "mensual"

    @field_validator("fecha_fin")
    @classmethod
    def _val_fechas(cls, v: date, info) -> date:
        inicio = info.data.get("fecha_inicio")
        if inicio and v < inicio:
            raise ValueError("fecha_fin debe ser >= fecha_inicio")
        return v


# ══════════════════════════════════════════════════════════════════════════
# Respuestas estandarizadas
# ══════════════════════════════════════════════════════════════════════════

class ErrorValidacion(BaseModel):
    campo: str
    motivo: str
    valor_recibido: Optional[str] = None


class RespuestaCalculo(BaseModel):
    """Respuesta estandarizada para todos los endpoints de cálculo."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    mensaje: str = ""
    fundamento_legal: list[str] = Field(default_factory=list)
    ejercicio_fiscal: int = 2025
    datos: dict = Field(default_factory=dict)
    errores: list[ErrorValidacion] = Field(default_factory=list)
    advertencias: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    @classmethod
    def exitosa(cls, datos: dict, fundamento: list[str], **kwargs) -> "RespuestaCalculo":
        return cls(
            success=True,
            mensaje="Cálculo realizado correctamente",
            fundamento_legal=fundamento,
            datos=datos,
            **kwargs,
        )

    @classmethod
    def con_errores(cls, errores: list[ErrorValidacion]) -> "RespuestaCalculo":
        return cls(
            success=False,
            mensaje="Errores de validación",
            errores=errores,
        )
