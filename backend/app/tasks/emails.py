"""
Tareas Celery para envío de emails transaccionales.
Reemplaza asyncio.create_task() en los route handlers — Celery gestiona reintentos
y el ciclo de vida independientemente del request/response de FastAPI.
"""
from __future__ import annotations
import logging

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.emails.bienvenida", bind=True, max_retries=3, default_retry_delay=60)
def enviar_bienvenida_task(self, email: str, nombre: str) -> bool:
    import asyncio
    from app.services.email import enviar_bienvenida
    try:
        return asyncio.run(enviar_bienvenida(email, nombre))
    except Exception as exc:
        logger.error(f"[EMAIL] bienvenida falló para {email}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(name="app.tasks.emails.reset_password", bind=True, max_retries=3, default_retry_delay=30)
def enviar_reset_password_task(self, email: str, nombre: str, reset_url: str) -> bool:
    import asyncio
    from app.services.email import enviar_reset_password
    try:
        return asyncio.run(enviar_reset_password(email, nombre, reset_url))
    except Exception as exc:
        logger.error(f"[EMAIL] reset_password falló para {email}: {exc}")
        raise self.retry(exc=exc)
