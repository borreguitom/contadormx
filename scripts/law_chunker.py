"""
Módulo de chunking de leyes fiscales mexicanas.
Divide textos legales por artículo usando patrones de regex.
Cada artículo = 1 chunk con metadatos estructurados.
"""
import re
from pathlib import Path
from typing import Iterator


# Patrones de artículos en leyes mexicanas
ARTICLE_PATTERN = re.compile(
    r"(?:^|\n)"
    r"(Art[íi]culo\s+(\d+[oO°]?(?:-[A-Z])?(?:\s+[A-Z])?)"
    r"(?:\.|°|\s))",
    re.MULTILINE | re.IGNORECASE,
)

# Patrones alternativos: ARTÍCULO en mayúsculas, numerales romanos
ALT_PATTERNS = [
    re.compile(r"(?:^|\n)(ARTÍCULO\s+(\d+[oO°]?)[\.\s])", re.MULTILINE),
    re.compile(r"(?:^|\n)(Art\.\s+(\d+[oO°]?(?:-[A-Z])?)[\.\s])", re.MULTILINE),
]

# Detectar nombre de ley desde el nombre del archivo
LEY_FROM_FILENAME = {
    "cff": "CFF",
    "lisr": "LISR",
    "liva": "LIVA",
    "lieps": "LIEPS",
    "lft": "LFT",
    "lss": "LSS",
    "linfonavit": "LINFONAVIT",
    "rmf": "RMF",
    "nif": "NIF",
    "cpeum": "CPEUM",
}

# Texto de encabezado de cada ley para contexto
LEY_CONTEXTO = {
    "CFF": "Código Fiscal de la Federación",
    "LISR": "Ley del Impuesto Sobre la Renta",
    "LIVA": "Ley del Impuesto al Valor Agregado",
    "LIEPS": "Ley del Impuesto Especial sobre Producción y Servicios",
    "LFT": "Ley Federal del Trabajo",
    "LSS": "Ley del Seguro Social",
    "LINFONAVIT": "Ley del INFONAVIT",
    "RMF": "Resolución Miscelánea Fiscal",
    "NIF": "Normas de Información Financiera",
}


def detect_ley(filename: str) -> str:
    """Detecta la ley desde el nombre del archivo."""
    stem = Path(filename).stem.lower()
    for key, ley in LEY_FROM_FILENAME.items():
        if key in stem:
            return ley
    return Path(filename).stem.upper().split("_")[0]


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae texto de un PDF usando pdfplumber (mejor para leyes)."""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts)


def clean_legal_text(text: str) -> str:
    """Limpia el texto: elimina headers de página, números de página, artefactos de PDF."""
    # Números de página solos
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)
    # Headers/footers comunes de DOF
    text = re.sub(r"Jueves \d+ de .+ de 20\d{2}", "", text)
    text = re.sub(r"DIARIO OFICIAL\s+(?:DE LA FEDERACIÓN)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[­\xad]", "", text)  # soft hyphens
    # Espacios múltiples → uno
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Más de 2 saltos de línea → 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_article_title(article_text: str) -> str:
    """Intenta extraer el título descriptivo del artículo (primera línea después del número)."""
    lines = article_text.strip().split("\n")
    if len(lines) > 1:
        # Si la siguiente línea parece un título (no es un párrafo largo)
        second = lines[1].strip()
        if second and len(second) < 120 and not second[0].islower():
            return second
    return ""


def chunk_by_article(
    text: str,
    ley: str,
    fuente_url: str = "",
    fecha_actualizacion: str = "",
    min_chars: int = 50,
) -> Iterator[dict]:
    """
    Divide el texto legal en chunks por artículo.
    Yields dicts compatibles con rag.upsert_chunks().
    """
    # Intentar con el patrón principal
    matches = list(ARTICLE_PATTERN.finditer(text))

    # Si hay pocos artículos, intentar patrones alternativos
    if len(matches) < 5:
        for pattern in ALT_PATTERNS:
            alt_matches = list(pattern.finditer(text))
            if len(alt_matches) > len(matches):
                matches = alt_matches
                break

    if not matches:
        # Sin artículos detectados — chunk único del documento
        if len(text) >= min_chars:
            yield {
                "ley": ley,
                "articulo": "0",
                "titulo": LEY_CONTEXTO.get(ley, ley),
                "texto": text[:4000],
                "fuente_url": fuente_url,
                "fecha_actualizacion": fecha_actualizacion,
                "vigente": True,
            }
        return

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        article_text = text[start:end].strip()
        if len(article_text) < min_chars:
            continue

        # Número de artículo normalizado
        article_num = match.group(2).strip().rstrip(".")

        # Título del artículo
        titulo = extract_article_title(article_text)

        # Limitar texto a 3000 chars para no exceder límites de embedding
        texto_chunk = article_text[:3000]

        # Agregar contexto de la ley al inicio para mejorar retrieval
        contexto = LEY_CONTEXTO.get(ley, ley)
        texto_con_contexto = f"[{ley} — {contexto}] Art. {article_num}\n{texto_chunk}"

        yield {
            "ley": ley,
            "articulo": article_num,
            "titulo": titulo,
            "texto": texto_con_contexto,
            "fuente_url": fuente_url,
            "fecha_actualizacion": fecha_actualizacion,
            "vigente": True,
        }
