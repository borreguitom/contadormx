from pathlib import Path
from datetime import date
import base64

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

DOC_TYPES = {
    "carta_sat": {
        "nombre": "Carta de respuesta al SAT",
        "descripcion": "Respuesta formal a oficios, requerimientos y notificaciones del SAT",
        "template": "carta_sat.html",
        "campos": ["emisor_nombre", "emisor_rfc", "emisor_domicilio", "numero_oficio",
                   "fecha_oficio", "asunto", "cuerpo", "lugar"],
    },
    "cedula_isr": {
        "nombre": "Cédula de determinación ISR Anual PF",
        "descripcion": "Hoja de trabajo para la declaración anual de personas físicas",
        "template": "cedula_isr.html",
        "campos": ["contribuyente_nombre", "contribuyente_rfc", "regimen", "ejercicio",
                   "ingresos_totales", "deducciones_autorizadas", "deducciones_personales",
                   "pagos_provisionales", "retenciones"],
    },
    "carta_encargo": {
        "nombre": "Carta encargo profesional",
        "descripcion": "Contrato de prestación de servicios contables/fiscales",
        "template": "carta_encargo.html",
        "campos": ["cliente_nombre", "cliente_rfc", "contador_nombre", "contador_rfc",
                   "contador_cedula", "servicios", "honorarios_mensuales", "vigencia_inicio",
                   "vigencia_fin", "lugar"],
    },
    "escrito_respuesta": {
        "nombre": "Escrito de respuesta a requerimiento",
        "descripcion": "Escrito formal ante el SAT con documentación soporte",
        "template": "escrito_respuesta.html",
        "campos": ["contribuyente_nombre", "contribuyente_rfc", "numero_requerimiento",
                   "fecha_requerimiento", "autoridad", "respuesta", "documentacion_adjunta",
                   "lugar"],
    },
}


def _fecha_hoy_es() -> str:
    hoy = date.today()
    return f"{hoy.day} de {MESES_ES[hoy.month]} de {hoy.year}"


def generate_pdf(doc_type: str, data: dict) -> bytes:
    if doc_type not in DOC_TYPES:
        raise ValueError(f"Tipo de documento no válido: {doc_type}")

    template = _env.get_template(DOC_TYPES[doc_type]["template"])
    html_str = template.render(**data, fecha_hoy=_fecha_hoy_es())

    import weasyprint  # lazy — falla en Windows dev si no hay GTK, ok en Docker/Linux
    pdf_bytes = weasyprint.HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()
    return pdf_bytes


def generate_pdf_b64(doc_type: str, data: dict) -> str:
    return base64.b64encode(generate_pdf(doc_type, data)).decode()
