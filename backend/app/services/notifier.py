"""
Notificador de reformas fiscales via Resend.
Se dispara cuando un scraper detecta una publicación relevante en DOF/SAT.
"""
import logging
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API = "https://api.resend.com/emails"
FROM_EMAIL = "ContadorMX <alertas@contadormx.app>"


async def notificar_reforma(
    titulo: str,
    url: str,
    fecha: str,
    fuente: str = "DOF",
    destinatarios: list[str] | None = None,
) -> bool:
    """
    Envía email de alerta cuando se detecta una reforma fiscal.
    Si no hay RESEND_API_KEY configurada, solo loguea.
    """
    if not hasattr(settings, "RESEND_API_KEY") or not settings.RESEND_API_KEY:
        logger.info(f"[NOTIFIER] Reforma detectada (sin email): {titulo}")
        return False

    # Obtener todos los emails de usuarios activos
    recipients = destinatarios or await _get_user_emails()
    if not recipients:
        logger.info(f"[NOTIFIER] Sin destinatarios configurados.")
        return False

    html = _build_email_html(titulo, url, fecha, fuente)

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                RESEND_API,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": FROM_EMAIL,
                    "to": recipients,
                    "subject": f"🚨 Reforma fiscal detectada: {titulo[:80]}",
                    "html": html,
                },
            )
            if resp.status_code in (200, 201):
                logger.info(f"[NOTIFIER] Email enviado a {len(recipients)} usuarios: {titulo[:60]}")
                return True
            else:
                logger.warning(f"[NOTIFIER] Resend error {resp.status_code}: {resp.text}")
                return False
        except httpx.HTTPError as e:
            logger.error(f"[NOTIFIER] Error HTTP: {e}")
            return False


def _build_email_html(titulo: str, url: str, fecha: str, fuente: str) -> str:
    fecha_fmt = fecha[:10] if fecha else "hoy"
    return f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family: Georgia, serif; background: #f0fdf4; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px;
              border: 1px solid #bbf7d0; overflow: hidden;">
    <div style="background: #052e16; padding: 20px 24px; color: white;">
      <div style="font-size: 20px; font-weight: bold;">🏛️ ContadorMX</div>
      <div style="font-size: 12px; color: #4ade80; margin-top: 4px;">Alerta de Reforma Fiscal</div>
    </div>
    <div style="padding: 24px;">
      <p style="color: #ef4444; font-weight: bold; font-size: 14px;">
        🚨 Nueva publicación relevante detectada en {fuente}
      </p>
      <h2 style="color: #052e16; font-size: 18px; margin: 8px 0;">{titulo}</h2>
      <p style="color: #6b7280; font-size: 13px;">Publicado: {fecha_fmt}</p>
      <a href="{url}" style="display: inline-block; background: #16a34a; color: white;
         padding: 10px 20px; border-radius: 8px; text-decoration: none; font-size: 14px; margin: 12px 0;">
        Ver publicación oficial
      </a>
      <hr style="border: none; border-top: 1px solid #d1fae5; margin: 20px 0;">
      <p style="color: #6b7280; font-size: 12px;">
        Revisa el impacto en tus clientes en
        <a href="https://contadormx.app" style="color: #16a34a;">ContadorMX</a>.
        Esta es una notificación automática — el sistema ha detectado que esta publicación
        puede contener reformas fiscales relevantes. Verifica con el texto oficial.
      </p>
    </div>
  </div>
</body>
</html>
"""


async def _get_user_emails() -> list[str]:
    """Obtiene emails de usuarios activos desde la DB."""
    try:
        from app.core.database import AsyncSessionLocal, User
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(User.email).where(User.is_active == True)
            )
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error obteniendo emails: {e}")
        return []
