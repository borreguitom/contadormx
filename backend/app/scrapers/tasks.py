"""
Celery tasks para scraping automático de reformas fiscales.
Worker: celery -A celery_app worker --loglevel=info
Beat:   celery -A celery_app beat --loglevel=info
"""
import asyncio
import logging
from datetime import datetime, timezone

from celery_app import celery_app
from app.scrapers.dof import fetch_dof_updates
from app.scrapers.sat import fetch_sat_updates
from app.scrapers.inegi import fetch_inpc_actual
from app.services.notifier import notificar_reforma

logger = logging.getLogger(__name__)


def run_async(coro):
    """Ejecuta coroutine dentro de Celery (que es sincrónico por default)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_dof(self):
    """Revisa el DOF por reformas fiscales nuevas."""
    try:
        updates = run_async(fetch_dof_updates(days_back=2))
        nuevas = [u for u in updates if "error" not in u]

        if not nuevas:
            logger.info("DOF: sin publicaciones fiscales relevantes hoy.")
            return {"status": "ok", "nuevas": 0}

        logger.info(f"DOF: {len(nuevas)} publicaciones fiscales detectadas.")

        # Persistir en DB + notificar
        for update in nuevas:
            run_async(_procesar_reforma(update, fuente="DOF"))

        return {"status": "ok", "nuevas": len(nuevas)}

    except Exception as exc:
        logger.error(f"scrape_dof error: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_sat(self):
    """Revisa páginas del SAT por documentos nuevos."""
    try:
        updates = run_async(fetch_sat_updates())
        logger.info(f"SAT: {len(updates)} documentos encontrados.")

        for update in updates[:10]:  # procesar máximo 10 por ejecución
            run_async(_procesar_reforma(update, fuente="SAT"))

        return {"status": "ok", "documentos": len(updates)}

    except Exception as exc:
        logger.error(f"scrape_sat error: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def actualizar_inpc():
    """Actualiza el INPC mensual desde INEGI."""
    try:
        inpc = run_async(fetch_inpc_actual())
        logger.info(f"INPC actualizado: {inpc}")
        # Guardar en Redis como caché rápida
        from app.core.config import settings
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.set("inpc:actual", str(inpc.get("inpc", 0)), ex=86400 * 35)
        return {"status": "ok", "inpc": inpc}
    except Exception as e:
        logger.error(f"actualizar_inpc error: {e}")
        return {"status": "error", "error": str(e)}


async def _procesar_reforma(update: dict, fuente: str):
    """
    Pipeline de procesamiento de una reforma detectada:
    1. Guardar en DB como LawUpdate
    2. Si tiene texto, chunkear y upsertar en Qdrant como "reforma_reciente"
    3. Notificar por email a usuarios
    """
    from app.core.database import AsyncSessionLocal
    from app.services.notifier import notificar_reforma

    titulo = update.get("titulo", "")
    url = update.get("url", "")
    fecha = update.get("fecha_publicacion", datetime.now(timezone.utc).isoformat())

    # Persistir en DB
    try:
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            await db.execute(
                text("""
                    INSERT INTO law_updates (ley, tipo, titulo, url, fecha_publicacion, indexado, created_at)
                    VALUES (:ley, :tipo, :titulo, :url, :fecha, false, now())
                    ON CONFLICT DO NOTHING
                """),
                {
                    "ley": _detectar_ley_desde_titulo(titulo),
                    "tipo": update.get("tipo", fuente.lower()),
                    "titulo": titulo[:500],
                    "url": url[:1000],
                    "fecha": fecha,
                },
            )
            await db.commit()
    except Exception as e:
        logger.warning(f"No se pudo guardar en DB: {e}")

    # Notificar si es reforma importante
    if _es_reforma_importante(titulo):
        await notificar_reforma(
            titulo=titulo,
            url=url,
            fecha=fecha,
            fuente=fuente,
        )


def _detectar_ley_desde_titulo(titulo: str) -> str:
    titulo_upper = titulo.upper()
    for ley in ["CFF", "LISR", "LIVA", "LIEPS", "LFT", "LSS", "LINFONAVIT", "RMF"]:
        if ley in titulo_upper:
            return ley
    if "FISCAL" in titulo_upper or "IMPUESTO" in titulo_upper:
        return "FISCAL"
    return "GENERAL"


def _es_reforma_importante(titulo: str) -> bool:
    titulo_l = titulo.lower()
    return any(kw in titulo_l for kw in [
        "reforma", "decreto", "resolución miscelánea", "miscelánea fiscal",
        "acuerdo", "publicación", "lisr", "liva", "cff", "rmf",
    ])
