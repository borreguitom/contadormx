"""
Scraper DOF (Diario Oficial de la Federación).
Monitorea el RSS del DOF y detecta publicaciones fiscales relevantes.
Solo SHCP, SAT, IMSS, STPS, SE — solo palabras clave fiscales.
"""
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx
import defusedxml.ElementTree as ET

DOF_RSS_URL = "https://www.dof.gob.mx/rss_noticias.php"

# Dependencias fiscales relevantes
DEPENDENCIAS_RELEVANTES = {
    "SHCP", "SAT", "IMSS", "INFONAVIT", "STPS",
    "Secretaría de Hacienda", "Servicio de Administración Tributaria",
    "Instituto Mexicano del Seguro Social",
}

# Palabras clave que indican reforma fiscal
KEYWORDS_FISCALES = [
    "reforma", "impuesto", "fiscal", "tributari", "iva", "isr", "ieps",
    "cff", "lisr", "liva", "rif", "resico", "cfdi", "sat", "retencion",
    "declaracion", "contribuyente", "deduccion", "miscelánea", "resolución",
    "arancel", "imss", "infonavit", "cuota", "nomina", "salario minimo",
    "uma", "inpc", "actualizacion", "recargos",
]


def _is_fiscal_relevant(title: str, description: str = "") -> bool:
    text = (title + " " + description).lower()
    # Palabras clave fiscales
    has_keyword = any(kw in text for kw in KEYWORDS_FISCALES)
    # Excluir temas claramente no fiscales
    not_excluded = not any(exc in text for exc in [
        "licitacion", "convocatoria", "obra publica", "acuerdo de cooperacion",
        "tratado internacional", "nombramientos", "curriculum",
    ])
    return has_keyword and not_excluded


async def fetch_dof_updates(days_back: int = 7) -> list[dict]:
    """
    Obtiene publicaciones del DOF de los últimos N días.
    Retorna solo las fiscalmente relevantes.
    """
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.get(
                DOF_RSS_URL,
                headers={"User-Agent": "ContadorMX/1.0 (+fiscal-monitoring)"},
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            return [{"error": f"DOF RSS no disponible: {e}"}]

    items = _parse_rss(resp.text)
    fiscales = [i for i in items if _is_fiscal_relevant(i["titulo"], i.get("descripcion", ""))]
    return fiscales


def _parse_rss(xml_text: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []

        for item in channel.findall("item"):
            titulo = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date_str = item.findtext("pubDate", "")
            descripcion = item.findtext("description", "").strip()

            pub_date = None
            if pub_date_str:
                try:
                    pub_date = parsedate_to_datetime(pub_date_str).isoformat()
                except Exception:
                    pub_date = pub_date_str

            items.append({
                "titulo": titulo,
                "url": link,
                "fecha_publicacion": pub_date,
                "descripcion": descripcion[:300] if descripcion else "",
                "fuente": "DOF",
            })
    except ET.ParseError:
        pass
    return items


async def fetch_dof_document(url: str) -> Optional[str]:
    """Descarga el texto de una publicación del DOF."""
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "ContadorMX/1.0"})
            if resp.status_code == 200:
                # HTML simple — extraer texto
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                # El DOF usa divs de clase específica para el contenido
                for tag in soup(["script", "style", "nav", "header", "footer"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)
        except Exception:
            pass
    return None
