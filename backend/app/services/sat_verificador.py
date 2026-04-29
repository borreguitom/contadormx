"""
Verificador de autenticidad CFDI contra el SAT.
Consulta el servicio SOAP oficial:
  https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc

Parámetros: UUID + RFC emisor + RFC receptor + Total
Respuesta:  Estado (Vigente / Cancelado / No Encontrado) + EsCancelable + EstatusCancelacion
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

log = logging.getLogger(__name__)

_SAT_URL = "https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc"
_SAT_ACTION = "http://tempuri.org/IConsultaCFDIService/Consultar"

_SOAP_TMPL = """\
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope
    xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:tem="http://tempuri.org/">
  <soapenv:Header/>
  <soapenv:Body>
    <tem:Consultar>
      <tem:expresionImpresa>?re={re}&amp;rr={rr}&amp;tt={tt}&amp;id={id}</tem:expresionImpresa>
    </tem:Consultar>
  </soapenv:Body>
</soapenv:Envelope>"""


def _extract_tag(xml_text: str, tag: str) -> Optional[str]:
    start = xml_text.find(f"<{tag}>")
    end   = xml_text.find(f"</{tag}>")
    if start == -1 or end == -1:
        return None
    return xml_text[start + len(tag) + 2 : end].strip() or None


async def verificar_cfdi_sat(
    uuid: str,
    rfc_emisor: str,
    rfc_receptor: str,
    total: float,
    timeout: float = 10.0,
) -> dict:
    """
    Retorna:
      {
        "sat_estado":       "Vigente" | "Cancelado" | "No Encontrado" | "error",
        "sat_cancelable":   "No cancelable" | "Cancelable con aceptación" | ... | None,
        "sat_codigo":       "S - Comprobante obtenido satisfactoriamente." | ...,
        "sat_efos":         "200" | None,
        "error":            None | "mensaje de error técnico",
      }
    """
    body = _SOAP_TMPL.format(
        re=rfc_emisor.upper(),
        rr=rfc_receptor.upper(),
        tt=f"{total:.6f}",
        id=uuid.upper(),
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                _SAT_URL,
                content=body.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction":   _SAT_ACTION,
                },
            )
    except httpx.TimeoutException:
        log.warning("SAT verificador: timeout para UUID %s", uuid)
        return {"sat_estado": "error", "sat_cancelable": None, "sat_codigo": None, "sat_efos": None, "error": "timeout"}
    except Exception as exc:
        log.warning("SAT verificador: %s", exc)
        return {"sat_estado": "error", "sat_cancelable": None, "sat_codigo": None, "sat_efos": None, "error": str(exc)}

    text = resp.text
    estado      = _extract_tag(text, "Estado")
    cancelable  = _extract_tag(text, "EsCancelable")
    codigo      = _extract_tag(text, "CodigoEstatus")
    efos        = _extract_tag(text, "ValidacionEFOS")

    if estado is None:
        # respuesta inesperada del SAT
        log.warning("SAT verificador: respuesta sin <Estado> para UUID %s — HTTP %s", uuid, resp.status_code)
        return {
            "sat_estado": "error",
            "sat_cancelable": None,
            "sat_codigo": codigo,
            "sat_efos": efos,
            "error": f"HTTP {resp.status_code}: sin <Estado>",
        }

    return {
        "sat_estado":     estado,       # "Vigente" | "Cancelado" | "No Encontrado"
        "sat_cancelable": cancelable,
        "sat_codigo":     codigo,
        "sat_efos":       efos,
        "error":          None,
    }
