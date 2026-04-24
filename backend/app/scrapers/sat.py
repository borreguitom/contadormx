"""
Scraper SAT — novedades, criterios normativos y no vinculativos.
Monitorea cambios en las páginas oficiales del SAT.
"""
import hashlib
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

SAT_BASE = "https://www.sat.gob.mx"

SAT_PAGES = [
    {
        "url": "https://www.sat.gob.mx/consultas/98850/conoce-la-ley",
        "tipo": "legislacion",
        "nombre": "Legislación SAT",
    },
    {
        "url": "https://www.sat.gob.mx/consultas/87064/criterios-normativos",
        "tipo": "criterio_normativo",
        "nombre": "Criterios Normativos SAT",
    },
    {
        "url": "https://www.sat.gob.mx/consultas/89332/criterios-no-vinculativos",
        "tipo": "criterio_no_vinculativo",
        "nombre": "Criterios No Vinculativos SAT",
    },
    {
        "url": "https://www.sat.gob.mx/consultas/43358/resoluciones-miscelaneas-fiscales",
        "tipo": "rmf",
        "nombre": "RMF SAT",
    },
]


async def fetch_sat_updates() -> list[dict]:
    """Scrape páginas del SAT buscando documentos recientes."""
    results = []
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for page in SAT_PAGES:
            try:
                resp = await client.get(
                    page["url"],
                    headers={"User-Agent": "Mozilla/5.0 ContadorMX/1.0"},
                )
                if resp.status_code != 200:
                    continue

                items = _extract_sat_links(resp.text, page["tipo"], page["nombre"])
                results.extend(items)
            except httpx.HTTPError:
                continue

    return results


def _extract_sat_links(html: str, tipo: str, fuente_nombre: str) -> list[dict]:
    """Extrae links de PDFs y documentos de una página del SAT."""
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = a.get_text(strip=True)

        if not text or len(text) < 5:
            continue

        # PDFs o links con texto relevante
        is_pdf = href.lower().endswith(".pdf")
        is_fiscal = any(kw in text.lower() for kw in [
            "resolución", "miscelánea", "criterio", "ley", "reglamento",
            "reforma", "cfdi", "isr", "iva", "rmf", "2024", "2025",
        ])

        if is_pdf or is_fiscal:
            full_url = href if href.startswith("http") else SAT_BASE + href
            items.append({
                "titulo": text[:200],
                "url": full_url,
                "tipo": tipo,
                "fuente": fuente_nombre,
                "fecha_detectado": datetime.now(timezone.utc).isoformat(),
            })

    return items[:20]  # top 20 por página


async def fetch_sat_criteria_text(url: str) -> str | None:
    """Descarga el texto de un criterio del SAT."""
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers={"User-Agent": "ContadorMX/1.0"})
            if resp.status_code != 200:
                return None

            if url.lower().endswith(".pdf"):
                # Guardar y procesar como PDF
                import tempfile, os
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                    f.write(resp.content)
                    tmp_path = f.name
                try:
                    import pdfplumber
                    with pdfplumber.open(tmp_path) as pdf:
                        return "\n".join(p.extract_text() or "" for p in pdf.pages)
                finally:
                    os.unlink(tmp_path)
            else:
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "nav"]):
                    tag.decompose()
                return soup.get_text(separator="\n", strip=True)
        except Exception:
            return None
