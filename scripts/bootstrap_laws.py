#!/usr/bin/env python3
"""
Bootstrap: indexa todas las leyes en /data/laws/ en Qdrant.

Uso:
    python scripts/bootstrap_laws.py                   # todas las leyes
    python scripts/bootstrap_laws.py --ley LISR        # solo LISR
    python scripts/bootstrap_laws.py --dry-run         # sin insertar, ver stats
    python scripts/bootstrap_laws.py --reset           # borra colección y re-indexa

Coloca los PDFs en data/laws/ con el nombre de la ley en el filename:
    data/laws/CFF_2025-01.pdf
    data/laws/LISR_2025-01.pdf
    data/laws/LIVA_2025-01.pdf
    etc.
"""
import asyncio
import argparse
import sys
import os
import time
from pathlib import Path

# Agregar backend al path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import settings
from app.services.rag import ensure_collection, upsert_chunks, collection_stats
from app.services.embeddings import get_embedding_dim
from scripts.law_chunker import extract_text_from_pdf, clean_legal_text, chunk_by_article, detect_ley


DATA_DIR = ROOT / "data" / "laws"


async def index_pdf(pdf_path: Path, dry_run: bool = False) -> dict:
    ley = detect_ley(pdf_path.name)
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Procesando: {pdf_path.name} ({ley})")

    t0 = time.time()

    try:
        raw_text = extract_text_from_pdf(str(pdf_path))
    except Exception as e:
        print(f"  ERROR extrayendo texto: {e}")
        return {"pdf": pdf_path.name, "status": "error", "error": str(e)}

    text = clean_legal_text(raw_text)
    print(f"  Texto extraído: {len(text):,} chars")

    chunks = list(
        chunk_by_article(
            text=text,
            ley=ley,
            fuente_url=f"file://{pdf_path}",
            fecha_actualizacion=pdf_path.stem.split("_")[-1] if "_" in pdf_path.stem else "2025",
        )
    )
    print(f"  Artículos detectados: {len(chunks)}")

    if dry_run:
        for c in chunks[:3]:
            print(f"  → Art. {c['articulo']}: {c['texto'][:80]}...")
        return {"pdf": pdf_path.name, "ley": ley, "chunks": len(chunks), "status": "dry_run"}

    if not chunks:
        print(f"  Sin artículos detectados — omitiendo.")
        return {"pdf": pdf_path.name, "ley": ley, "chunks": 0, "status": "skipped"}

    inserted = await upsert_chunks(chunks)
    elapsed = round(time.time() - t0, 1)
    print(f"  ✓ {inserted} chunks insertados en {elapsed}s")

    return {"pdf": pdf_path.name, "ley": ley, "chunks": inserted, "status": "ok", "elapsed_s": elapsed}


async def main():
    parser = argparse.ArgumentParser(description="Bootstrap leyes fiscales en Qdrant")
    parser.add_argument("--ley", help="Procesar solo esta ley (ej: LISR)")
    parser.add_argument("--dry-run", action="store_true", help="Solo mostrar stats, sin insertar")
    parser.add_argument("--reset", action="store_true", help="Borrar colección y re-indexar")
    args = parser.parse_args()

    print("=" * 60)
    print("ContadorMX — Bootstrap de base de conocimiento legal")
    print("=" * 60)
    print(f"Directorio de leyes: {DATA_DIR}")
    print(f"Qdrant URL: {settings.QDRANT_URL}")
    print(f"Colección: {settings.QDRANT_COLLECTION}")
    print(f"Embeddings: {settings.EMBEDDING_PROVIDER} ({get_embedding_dim()} dims)")

    if not DATA_DIR.exists():
        print(f"\nERROR: {DATA_DIR} no existe.")
        print("Crea el directorio y coloca los PDFs de las leyes ahí.")
        sys.exit(1)

    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if args.ley:
        pdfs = [p for p in pdfs if args.ley.upper() in p.name.upper()]

    if not pdfs:
        print(f"\nNo se encontraron PDFs en {DATA_DIR}")
        print("Descarga las leyes con: python scripts/download_laws.py")
        sys.exit(1)

    print(f"\nPDFs encontrados: {len(pdfs)}")
    for p in pdfs:
        print(f"  - {p.name}")

    if args.reset:
        from qdrant_client import AsyncQdrantClient
        client = AsyncQdrantClient(url=settings.QDRANT_URL)
        collections = await client.get_collections()
        names = {c.name for c in collections.collections}
        if settings.QDRANT_COLLECTION in names:
            await client.delete_collection(settings.QDRANT_COLLECTION)
            print(f"\nColección '{settings.QDRANT_COLLECTION}' eliminada.")

    if not args.dry_run:
        await ensure_collection()

    print("\nIniciando ingesta...\n")
    t_total = time.time()
    results = []
    for pdf in pdfs:
        r = await index_pdf(pdf, dry_run=args.dry_run)
        results.append(r)

    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    total_chunks = sum(r.get("chunks", 0) for r in results)
    ok = sum(1 for r in results if r["status"] in ("ok", "dry_run"))
    errors = [r for r in results if r["status"] == "error"]

    for r in results:
        icon = "✓" if r["status"] == "ok" else "~" if r["status"] == "dry_run" else "✗"
        print(f"  {icon} {r.get('ley', '?'):15} {r.get('chunks', 0):5} artículos   {r.get('elapsed_s', 0)}s")

    print(f"\nTotal: {total_chunks:,} artículos en {round(time.time() - t_total, 1)}s")

    if errors:
        print(f"\n⚠ Errores ({len(errors)}):")
        for e in errors:
            print(f"  - {e['pdf']}: {e.get('error')}")

    if not args.dry_run and ok > 0:
        stats = await collection_stats()
        print(f"\nEstado Qdrant: {stats['total_vectores']:,} vectores totales")
        print("\n✅ Base de conocimiento legal lista.")
        print("El agente ya puede citar artículos con texto textual.")


if __name__ == "__main__":
    asyncio.run(main())
