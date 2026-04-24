"""
Tarea Celery: recordatorios de calendario fiscal.
Corre diariamente a las 8am (hora México).
Envía email a todos los usuarios activos cuando hay obligaciones en 3 o 7 días.
"""
from __future__ import annotations
import asyncio
import logging

from celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Ejecuta una corutina desde contexto síncrono de Celery."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(name="app.tasks.fiscal_reminders.enviar_recordatorios", bind=True, max_retries=2)
def enviar_recordatorios(self):
    """
    Verifica si hoy es 3 o 7 días antes de alguna obligación fiscal.
    Si es así, envía email a todos los usuarios activos.
    """
    try:
        _run_async(_enviar_recordatorios_async())
    except Exception as exc:
        logger.error(f"[REMINDER] Error en tarea: {exc}")
        raise self.retry(exc=exc, countdown=300)


async def _enviar_recordatorios_async():
    from app.services.fiscal_calendar import obligaciones_en_exactamente
    from app.services.email import enviar_recordatorio_obligaciones
    from app.core.database import AsyncSessionLocal, User
    from sqlalchemy import select

    resultados = {}

    for dias in [3, 7]:
        obligaciones = obligaciones_en_exactamente(dias)
        if not obligaciones:
            logger.info(f"[REMINDER] Sin obligaciones en {dias} días")
            continue

        async with AsyncSessionLocal() as db:
            rows = await db.execute(
                select(User.email, User.nombre).where(User.is_active == True)
            )
            usuarios = rows.fetchall()

        if not usuarios:
            logger.info("[REMINDER] Sin usuarios activos")
            continue

        enviados = 0
        for email, _ in usuarios:
            if not email:
                continue
            ok = await enviar_recordatorio_obligaciones([email], obligaciones, dias)
            if ok:
                enviados += 1

        logger.info(
            f"[REMINDER] {dias} días: {len(obligaciones)} obligación(es), "
            f"{enviados}/{len(usuarios)} emails enviados"
        )
        resultados[f"{dias}_dias"] = {"enviados": enviados, "obligaciones": len(obligaciones)}

    return resultados
