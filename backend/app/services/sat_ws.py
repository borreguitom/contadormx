"""SAT Descarga Masiva de CFDI — SOAP web service client.

Uses cfdiclient library. Flow:
  1. Build Fiel from e.firma (.cer + .key + password)
  2. Authenticate → get token (valid ~5 min)
  3. Request download → get SAT request ID
  4. Poll verification until status=3 (ready)
  5. Download each package (base64 ZIP) → extract XMLs
  6. Parse XML → return metadata + raw XML
"""
from __future__ import annotations

import base64
import io
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Literal

import defusedxml.ElementTree as ET

DocType = Literal["I", "E", "T", "N", "P"]
SolicitudType = Literal["CFDI", "Metadata"]

CFDI_NS = "http://www.sat.gob.mx/cfd/4"
CFDI_NS3 = "http://www.sat.gob.mx/cfd/3"
TFD_NS = "http://www.sat.gob.mx/TimbreFiscalDigital"


class SatAuthError(Exception):
    pass


class SatRequestError(Exception):
    pass


@dataclass
class CfdiParsed:
    uuid: str
    rfc_emisor: str
    nombre_emisor: str
    rfc_receptor: str
    nombre_receptor: str
    total: float | None
    subtotal: float | None
    impuestos_trasladados: float | None
    fecha_emision: datetime | None
    fecha_timbrado: datetime | None
    tipo_comprobante: str
    metodo_pago: str | None
    forma_pago: str | None
    moneda: str
    serie: str | None
    folio: str | None
    xml_data: str


def _parse_cfdi_xml(xml_bytes: bytes) -> CfdiParsed | None:
    try:
        root = ET.fromstring(xml_bytes)
        ns = CFDI_NS if root.tag.startswith(f"{{{CFDI_NS}}}") else CFDI_NS3

        def attr(element, key: str, default: str = "") -> str:
            return element.get(key, default)

        def float_attr(element, key: str) -> float | None:
            v = element.get(key)
            try:
                return float(v) if v else None
            except (ValueError, TypeError):
                return None

        def parse_dt(s: str | None) -> datetime | None:
            if not s:
                return None
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
                try:
                    return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            return None

        emisor = root.find(f"{{{ns}}}Emisor")
        receptor = root.find(f"{{{ns}}}Receptor")
        complemento = root.find(f"{{{ns}}}Complemento")
        tfd = complemento.find(f"{{{TFD_NS}}}TimbreFiscalDigital") if complemento is not None else None

        impuestos_el = root.find(f"{{{ns}}}Impuestos")
        imp_valor = float_attr(impuestos_el, "TotalImpuestosTrasladados") if impuestos_el is not None else None

        uuid = attr(tfd, "UUID") if tfd is not None else ""
        if not uuid:
            return None

        return CfdiParsed(
            uuid=uuid.upper(),
            rfc_emisor=attr(emisor, "Rfc") if emisor is not None else "",
            nombre_emisor=attr(emisor, "Nombre") if emisor is not None else "",
            rfc_receptor=attr(receptor, "Rfc") if receptor is not None else "",
            nombre_receptor=attr(receptor, "Nombre") if receptor is not None else "",
            total=float_attr(root, "Total"),
            subtotal=float_attr(root, "SubTotal"),
            impuestos_trasladados=imp_valor,
            fecha_emision=parse_dt(attr(root, "Fecha") or None),
            fecha_timbrado=parse_dt(attr(tfd, "FechaTimbrado") if tfd is not None else None),
            tipo_comprobante=attr(root, "TipoDeComprobante", "I"),
            metodo_pago=attr(root, "MetodoPago") or None,
            forma_pago=attr(root, "FormaPago") or None,
            moneda=attr(root, "Moneda", "MXN"),
            serie=attr(root, "Serie") or None,
            folio=attr(root, "Folio") or None,
            xml_data=xml_bytes.decode("utf-8", errors="replace"),
        )
    except Exception:
        return None


def authenticate(cer_bytes: bytes, key_bytes: bytes, key_password: str) -> tuple[object, str]:
    """Authenticate with SAT. Returns (fiel, token)."""
    try:
        from cfdiclient import Autenticacion, Fiel
        fiel = Fiel(cer_bytes, key_bytes, key_password.encode())
        auth = Autenticacion(fiel)
        token = auth.obtener_token()
        if not token:
            raise SatAuthError("SAT no devolvió token")
        return fiel, token
    except ImportError:
        raise SatAuthError("cfdiclient no instalado. Ejecuta: pip install cfdiclient")
    except Exception as e:
        raise SatAuthError(f"Error de autenticación SAT: {e}") from e


def request_download(
    fiel: object,
    token: str,
    rfc: str,
    date_from: date,
    date_to: date,
    tipo_comprobante: str | None = None,
    tipo_solicitud: str = "CFDI",
) -> str:
    """Request bulk download. Returns SAT request ID."""
    from cfdiclient import SolicitaDescarga
    solicitud = SolicitaDescarga(fiel)
    result = solicitud.solicitar_descarga(
        token,
        rfc,
        date_from,
        date_to,
        rfc_receptor=rfc,
        tipo_solicitud=tipo_solicitud,
        tipo_comprobante=tipo_comprobante,
    )
    cod = result.get("CodEstatus", "")
    if cod != "5000":
        msg = result.get("Mensaje", f"Código: {cod}")
        raise SatRequestError(f"SAT rechazó solicitud: {msg}")
    return result["IdSolicitud"]


def verify_download(fiel: object, token: str, rfc: str, request_id: str) -> dict:
    """Check download status. EstadoSolicitud: 1=Aceptada 2=En proceso 3=Terminada 4+=Error."""
    from cfdiclient import VerificaSolicitudDescarga
    verifica = VerificaSolicitudDescarga(fiel)
    return verifica.verificar_descarga(token, rfc, request_id)


def download_package(fiel: object, token: str, rfc: str, package_id: str) -> list[CfdiParsed]:
    """Download one ZIP package and return parsed CFDIs."""
    from cfdiclient import DescargaMasiva
    descarga = DescargaMasiva(fiel)
    result = descarga.descargar_paquete(token, rfc, package_id)
    paquete_b64 = result.get("Paquete") or result.get("paquete_b64", "")
    if not paquete_b64:
        return []

    zip_bytes = base64.b64decode(paquete_b64)
    parsed = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for name in z.namelist():
            if name.endswith(".xml"):
                xml_bytes = z.read(name)
                cfdi = _parse_cfdi_xml(xml_bytes)
                if cfdi:
                    parsed.append(cfdi)
    return parsed
