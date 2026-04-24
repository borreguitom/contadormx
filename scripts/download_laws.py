#!/usr/bin/env python3
"""
Descarga las leyes fiscales mexicanas vigentes desde fuentes oficiales.

Uso:
    python scripts/download_laws.py              # descarga todas
    python scripts/download_laws.py --ley CFF    # solo CFF

Fuentes: diputados.gob.mx (leyes), dof.gob.mx (RMF)
"""
import asyncio
import argparse
import sys
from pathlib import Path
from datetime import date

import httpx

DATA_DIR = Path(__file__).parent.parent / "data" / "laws"

# Fuentes oficiales vigentes 2025
LEYES = {
    "CFF": {
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/CFF.pdf",
        "nombre": "Código Fiscal de la Federación",
    },
    "LISR": {
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf",
        "nombre": "Ley del Impuesto Sobre la Renta",
    },
    "LIVA": {
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LIVA.pdf",
        "nombre": "Ley del Impuesto al Valor Agregado",
    },
    "LIEPS": {
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LIEPS.pdf",
        "nombre": "Ley del Impuesto Especial sobre Producción y Servicios",
    },
    "LFT": {
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LFT.pdf",
        "nombre": "Ley Federal del Trabajo",
    },
    "LSS": {
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LSS.pdf",
        "nombre": "Ley del Seguro Social",
    },
    "LINFONAVIT": {
        "url": "https://www.diputados.gob.mx/LeyesBiblio/pdf/LINFONAVIT.pdf",
        "nombre": "Ley del INFONAVIT",
    },
    # RMF 2025 — publicada en DOF, múltiples anexos; usar compilación
    "RMF": {
        "url": "https://www.sat.gob.mx/cs/Satellite?blobcol=urldata&blobkey=id&blobtable=MungoBlobs&blobwhere=1461174805&ssbinary=true",
        "nombre": "Resolución Miscelánea Fiscal 2025",
        "fallback_url": "https://www.dof.gob.mx/2025/SAT/RMF_2025_19_12.pdf",
    },
}


async def download_law(key: str, info: dict, force: bool = False) -> dict:
    hoy = date.today().strftime("%Y-%m")
    dest = DATA_DIR / f"{key}_{hoy}.pdf"

    if dest.exists() and not force:
        size = dest.stat().st_size
        print(f"  ✓ {key:15} ya descargado ({size/1024:.0f} KB) — {dest.name}")
        return {"ley": key, "status": "cached", "path": str(dest)}

    print(f"  ↓ {key:15} Descargando desde {info['url'][:60]}...")

    urls = [info["url"]]
    if "fallback_url" in info:
        urls.append(info["fallback_url"])

    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 ContadorMX/1.0"},
                )
                if resp.status_code == 200 and len(resp.content) > 10_000:
                    dest.write_bytes(resp.content)
                    size_kb = len(resp.content) / 1024
                    print(f"  ✓ {key:15} {size_kb:.0f} KB → {dest.name}")
                    return {"ley": key, "status": "downloaded", "path": str(dest), "size_kb": size_kb}
                else:
                    print(f"  ⚠ {key} URL retornó {resp.status_code} o archivo muy pequeño, probando fallback...")
            except Exception as e:
                print(f"  ⚠ {key} Error con {url[:50]}: {e}")

    print(f"  ✗ {key} No se pudo descargar de ninguna URL.")
    return {"ley": key, "status": "failed"}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ley", help="Descargar solo esta ley (CFF, LISR, etc.)")
    parser.add_argument("--force", action="store_true", help="Re-descargar aunque ya exista")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    leyes = {args.ley.upper(): LEYES[args.ley.upper()]} if args.ley else LEYES

    if args.ley and args.ley.upper() not in LEYES:
        print(f"Ley '{args.ley}' no reconocida. Opciones: {', '.join(LEYES.keys())}")
        sys.exit(1)

    print(f"ContadorMX — Descarga de leyes fiscales 2025")
    print(f"Destino: {DATA_DIR}\n")

    tasks = [download_law(k, v, force=args.force) for k, v in leyes.items()]
    results = await asyncio.gather(*tasks)

    ok = sum(1 for r in results if r["status"] in ("downloaded", "cached"))
    failed = [r for r in results if r["status"] == "failed"]

    print(f"\n{ok}/{len(results)} leyes disponibles.")

    if failed:
        print(f"\n⚠ Fallaron: {', '.join(r['ley'] for r in failed)}")
        print("Descarga manualmente desde https://www.diputados.gob.mx/LeyesBiblio/")
        print(f"y coloca los PDFs en {DATA_DIR}/")

    print("\nSiguiente paso:")
    print("  python scripts/bootstrap_laws.py")


if __name__ == "__main__":
    asyncio.run(main())
