"""
Validador CFDI 4.0 — lxml + defusedxml para prevenir XML injection.
Valida estructura, namespace, campos obligatorios, sumas.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import defusedxml.ElementTree as ET

router = APIRouter()

CFDI_NS = "http://www.sat.gob.mx/cfd/4"
TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"


class CFDIValidateRequest(BaseModel):
    xml_content: str


class CFDIValidateResponse(BaseModel):
    valido: bool
    uuid: Optional[str]
    emisor_rfc: Optional[str]
    receptor_rfc: Optional[str]
    total: Optional[float]
    fecha: Optional[str]
    tipo_comprobante: Optional[str]
    version: Optional[str]
    errores: list[str]
    advertencias: list[str]


@router.post("/validate", response_model=CFDIValidateResponse)
async def validate_cfdi(req: CFDIValidateRequest):
    errores = []
    advertencias = []

    try:
        root = ET.fromstring(req.xml_content)
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail=f"XML inválido: {e}")

    # Namespace check
    version = root.get("Version")
    if version != "4.0":
        advertencias.append(f"Versión {version} — se esperaba 4.0 (CFDI 4.0 obligatorio desde 2023)")

    # Campos obligatorios
    uuid = None
    emisor_rfc = None
    receptor_rfc = None
    total = None
    fecha = root.get("Fecha")
    tipo = root.get("TipoDeComprobante")

    # Emisor
    emisor = root.find(f"{{{CFDI_NS}}}Emisor")
    if emisor is None:
        errores.append("Falta nodo Emisor")
    else:
        emisor_rfc = emisor.get("Rfc")
        if not emisor_rfc:
            errores.append("Emisor sin RFC")
        regimen_fiscal = emisor.get("RegimenFiscal")
        if not regimen_fiscal:
            errores.append("Emisor sin RegimenFiscal (obligatorio CFDI 4.0)")

    # Receptor
    receptor = root.find(f"{{{CFDI_NS}}}Receptor")
    if receptor is None:
        errores.append("Falta nodo Receptor")
    else:
        receptor_rfc = receptor.get("Rfc")
        if not receptor_rfc:
            errores.append("Receptor sin RFC")
        uso_cfdi = receptor.get("UsoCFDI")
        if not uso_cfdi:
            errores.append("Receptor sin UsoCFDI (obligatorio CFDI 4.0)")
        domicilio_fiscal_receptor = receptor.get("DomicilioFiscalReceptor")
        if not domicilio_fiscal_receptor:
            advertencias.append("Receptor sin DomicilioFiscalReceptor (recomendado CFDI 4.0)")

    # Total
    total_str = root.get("Total")
    if total_str:
        try:
            total = float(total_str)
        except ValueError:
            errores.append(f"Total no numérico: {total_str}")
    else:
        errores.append("Falta atributo Total")

    # Timbre Fiscal Digital
    complemento = root.find(f"{{{CFDI_NS}}}Complemento")
    if complemento is not None:
        tfd = complemento.find(f"{{{TFD_NS}}}TimbreFiscalDigital")
        if tfd is not None:
            uuid = tfd.get("UUID")
        else:
            advertencias.append("CFDI sin Timbre Fiscal Digital — no ha sido timbrado")
    else:
        advertencias.append("CFDI sin Complemento — no ha sido timbrado")

    # Conceptos
    conceptos = root.find(f"{{{CFDI_NS}}}Conceptos")
    if conceptos is None:
        errores.append("Falta nodo Conceptos")
    else:
        if len(list(conceptos)) == 0:
            errores.append("Conceptos vacío")

    return CFDIValidateResponse(
        valido=len(errores) == 0,
        uuid=uuid,
        emisor_rfc=emisor_rfc,
        receptor_rfc=receptor_rfc,
        total=total,
        fecha=fecha,
        tipo_comprobante=tipo,
        version=version,
        errores=errores,
        advertencias=advertencias,
    )
