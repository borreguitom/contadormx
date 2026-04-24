"""
Extractor de documentos fiscales.
Maneja: XML (CFDI 3.3 / 4.0), PDF (texto + escaneado vía Claude Vision), imágenes (Claude Vision).
"""
from __future__ import annotations

import base64
import io
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import defusedxml.ElementTree as ET
import pdfplumber
import anthropic

from app.core.config import settings

# ─── namespaces CFDI ──────────────────────────────────────────────────────────
NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "cfdi3": "http://www.sat.gob.mx/cfd/3",
    "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
}


def _ns(tag: str, ns: str = "cfdi") -> str:
    return f"{{{NS[ns]}}}{tag}"


# ─── resultado normalizado ─────────────────────────────────────────────────────

def _empty() -> dict[str, Any]:
    return {
        "uuid_cfdi": None,
        "tipo_comprobante": None,
        "serie": None,
        "folio": None,
        "fecha_emision": None,
        "emisor_rfc": None,
        "emisor_nombre": None,
        "receptor_rfc": None,
        "receptor_nombre": None,
        "subtotal": None,
        "descuento": 0.0,
        "iva_trasladado": 0.0,
        "iva_retenido": 0.0,
        "isr_retenido": 0.0,
        "total": None,
        "moneda": "MXN",
        "tipo_cambio": 1.0,
        "conceptos": [],
        "estado": "extraido",
        "error_msg": None,
    }


# ─── XML CFDI ─────────────────────────────────────────────────────────────────

def extract_xml(content: bytes) -> dict[str, Any]:
    try:
        root = ET.fromstring(content)
    except Exception as e:
        return {**_empty(), "estado": "error", "error_msg": f"XML inválido: {e}"}

    # detecta versión
    tag = root.tag
    if "cfd/4" in tag:
        cfdi_ns = "cfdi"
    elif "cfd/3" in tag:
        cfdi_ns = "cfdi3"
    else:
        cfdi_ns = "cfdi"

    def att(node, name: str) -> str | None:
        return node.attrib.get(name)

    data = _empty()
    data["tipo_comprobante"] = att(root, "TipoDeComprobante")
    data["serie"] = att(root, "Serie")
    data["folio"] = att(root, "Folio")
    data["moneda"] = att(root, "Moneda") or "MXN"

    try:
        tc = float(att(root, "TipoCambio") or 1)
        data["tipo_cambio"] = tc
    except (ValueError, TypeError):
        pass

    try:
        data["fecha_emision"] = datetime.fromisoformat(
            (att(root, "Fecha") or "").replace("Z", "+00:00")
        )
    except (ValueError, AttributeError):
        pass

    try:
        data["subtotal"] = float(att(root, "SubTotal") or 0)
    except (ValueError, TypeError):
        pass

    try:
        data["descuento"] = float(att(root, "Descuento") or 0)
    except (ValueError, TypeError):
        pass

    try:
        data["total"] = float(att(root, "Total") or 0)
    except (ValueError, TypeError):
        pass

    # Emisor / Receptor
    emisor = root.find(_ns("Emisor", cfdi_ns))
    if emisor is not None:
        data["emisor_rfc"] = att(emisor, "Rfc")
        data["emisor_nombre"] = att(emisor, "Nombre")

    receptor = root.find(_ns("Receptor", cfdi_ns))
    if receptor is not None:
        data["receptor_rfc"] = att(receptor, "Rfc")
        data["receptor_nombre"] = att(receptor, "Nombre")

    # Impuestos
    impuestos = root.find(_ns("Impuestos", cfdi_ns))
    if impuestos is not None:
        try:
            data["iva_trasladado"] = float(att(impuestos, "TotalImpuestosTrasladados") or 0)
        except (ValueError, TypeError):
            pass
        try:
            data["iva_retenido"] = float(att(impuestos, "TotalImpuestosRetenidos") or 0)
        except (ValueError, TypeError):
            pass

        # ISR retenido dentro de Retenciones
        retenciones = impuestos.find(_ns("Retenciones", cfdi_ns))
        if retenciones is not None:
            for ret in retenciones.findall(_ns("Retencion", cfdi_ns)):
                if att(ret, "Impuesto") == "001":  # ISR
                    try:
                        data["isr_retenido"] += float(att(ret, "Importe") or 0)
                    except (ValueError, TypeError):
                        pass

    # Conceptos
    conceptos_node = root.find(_ns("Conceptos", cfdi_ns))
    conceptos = []
    if conceptos_node is not None:
        for c in conceptos_node.findall(_ns("Concepto", cfdi_ns)):
            conceptos.append({
                "descripcion": att(c, "Descripcion"),
                "cantidad": att(c, "Cantidad"),
                "unidad": att(c, "Unidad") or att(c, "ClaveUnidad"),
                "valor_unitario": att(c, "ValorUnitario"),
                "importe": att(c, "Importe"),
            })
    data["conceptos"] = conceptos

    # UUID del timbre
    tfd = root.find(".//{http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital")
    if tfd is not None:
        data["uuid_cfdi"] = tfd.attrib.get("UUID")

    return data


# ─── PDF (texto) ──────────────────────────────────────────────────────────────

def extract_pdf_text(content: bytes) -> dict[str, Any]:
    """Intenta extraer datos fiscales de un PDF con texto embebido."""
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception as e:
        return {**_empty(), "estado": "error", "error_msg": f"PDF ilegible: {e}"}

    if not full_text.strip():
        return {**_empty(), "estado": "pendiente", "error_msg": "PDF sin texto — requiere OCR"}

    # Intenta encontrar datos con regex simples
    data = _empty()
    data["error_msg"] = "Extraído con heurística desde PDF"

    uuid_m = re.search(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", full_text)
    if uuid_m:
        data["uuid_cfdi"] = uuid_m.group(0)

    rfc_m = re.findall(r"\b[A-Z&Ñ]{3,4}\d{6}[A-Z0-9]{3}\b", full_text)
    if len(rfc_m) >= 1:
        data["emisor_rfc"] = rfc_m[0]
    if len(rfc_m) >= 2:
        data["receptor_rfc"] = rfc_m[1]

    total_m = re.search(r"Total\s*\$?\s*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
    if total_m:
        data["total"] = float(total_m.group(1).replace(",", ""))

    subtotal_m = re.search(r"SubTotal\s*\$?\s*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
    if subtotal_m:
        data["subtotal"] = float(subtotal_m.group(1).replace(",", ""))

    iva_m = re.search(r"IVA\s*(?:16%)?\s*\$?\s*([\d,]+\.\d{2})", full_text, re.IGNORECASE)
    if iva_m:
        data["iva_trasladado"] = float(iva_m.group(1).replace(",", ""))

    data["estado"] = "extraido"
    return data


# ─── Claude Vision (imágenes y PDFs escaneados) ────────────────────────────────

_VISION_PROMPT = """Eres un extractor de datos fiscales mexicanos. Analiza esta imagen de una factura/CFDI y extrae los siguientes datos en formato JSON exacto:

{
  "uuid_cfdi": "string o null",
  "tipo_comprobante": "I/E/T/N/P o null",
  "serie": "string o null",
  "folio": "string o null",
  "fecha_emision": "ISO 8601 o null",
  "emisor_rfc": "string o null",
  "emisor_nombre": "string o null",
  "receptor_rfc": "string o null",
  "receptor_nombre": "string o null",
  "subtotal": number o null,
  "descuento": number,
  "iva_trasladado": number,
  "iva_retenido": number,
  "isr_retenido": number,
  "total": number o null,
  "moneda": "MXN",
  "tipo_cambio": 1,
  "conceptos": [{"descripcion": "", "cantidad": "", "unidad": "", "valor_unitario": "", "importe": ""}]
}

Responde ÚNICAMENTE con el JSON, sin texto adicional."""


def extract_via_vision(content: bytes, media_type: str = "image/jpeg") -> dict[str, Any]:
    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        b64 = base64.standard_b64encode(content).decode("utf-8")

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": _VISION_PROMPT},
                    ],
                }
            ],
        )

        import json
        raw = msg.content[0].text.strip()
        # elimina posibles bloques markdown ```json
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)

        data = _empty()
        data.update({k: v for k, v in parsed.items() if k in data})

        # normaliza fecha
        if data["fecha_emision"] and isinstance(data["fecha_emision"], str):
            try:
                data["fecha_emision"] = datetime.fromisoformat(
                    data["fecha_emision"].replace("Z", "+00:00")
                )
            except ValueError:
                data["fecha_emision"] = None

        data["estado"] = "extraido"
        return data

    except Exception as e:
        return {**_empty(), "estado": "error", "error_msg": f"Vision error: {e}"}


# ─── PDF escaneado (convierte a imagen y usa Vision) ──────────────────────────

def extract_pdf_scanned(content: bytes) -> dict[str, Any]:
    """Convierte primera página del PDF a PNG y usa Claude Vision."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        doc.close()
        return extract_via_vision(img_bytes, "image/png")
    except ImportError:
        # PyMuPDF no instalado — intenta extracción de texto igual
        return extract_pdf_text(content)
    except Exception as e:
        return {**_empty(), "estado": "error", "error_msg": f"PDF→imagen error: {e}"}


# ─── dispatcher principal ─────────────────────────────────────────────────────

def extract_document(filename: str, content: bytes) -> dict[str, Any]:
    ext = Path(filename).suffix.lower()

    if ext == ".xml":
        return extract_xml(content)

    if ext == ".pdf":
        result = extract_pdf_text(content)
        # si no extrajo datos esenciales, intenta Vision
        if result.get("estado") == "pendiente" or (
            result.get("total") is None and result.get("uuid_cfdi") is None
        ):
            return extract_pdf_scanned(content)
        return result

    if ext in {".jpg", ".jpeg", ".png", ".webp", ".heic", ".tiff", ".tif"}:
        mt_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".webp": "image/webp",
            ".heic": "image/jpeg", ".tiff": "image/jpeg", ".tif": "image/jpeg",
        }
        return extract_via_vision(content, mt_map.get(ext, "image/jpeg"))

    return {**_empty(), "estado": "error", "error_msg": f"Formato no soportado: {ext}"}
