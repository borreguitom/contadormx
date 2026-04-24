"""
Servicio centralizado de email vía Resend.
Cubre: recordatorios fiscales, bienvenida, alertas de reforma.
"""
from __future__ import annotations
import logging
from datetime import date

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_API = "https://api.resend.com/emails"
FROM_EMAIL = "ContadorMX <recordatorios@contadormx.app>"
APP_URL = settings.FRONTEND_URL or "https://contadormx.app"


async def _send(to: list[str], subject: str, html: str) -> bool:
    if not settings.RESEND_API_KEY:
        logger.info(f"[EMAIL] Sin RESEND_API_KEY — email omitido: {subject}")
        return False
    if not to:
        return False
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(
                RESEND_API,
                headers={
                    "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"from": FROM_EMAIL, "to": to, "subject": subject, "html": html},
            )
            ok = resp.status_code in (200, 201)
            if ok:
                logger.info(f"[EMAIL] Enviado a {len(to)} destinatarios: {subject}")
            else:
                logger.warning(f"[EMAIL] Resend {resp.status_code}: {resp.text[:200]}")
            return ok
        except httpx.HTTPError as e:
            logger.error(f"[EMAIL] Error: {e}")
            return False


# ── Recordatorio de obligaciones fiscales ─────────────────────────────────────

async def enviar_recordatorio_obligaciones(
    destinatarios: list[str],
    obligaciones: list[dict],
    dias_restantes: int,
) -> bool:
    if not obligaciones:
        return False

    hoy = date.today().strftime("%d de %B de %Y")
    items_html = "".join(
        f"""
        <tr>
          <td style="padding:10px 12px; border-bottom:1px solid #d1fae5;">
            <strong style="color:#052e16;">{o['nombre']}</strong><br>
            <span style="color:#6b7280; font-size:12px;">
              {o['dia']} de {o['mes'].lower()} — {o['tipo'].capitalize()}
            </span>
          </td>
          <td style="padding:10px 12px; border-bottom:1px solid #d1fae5; text-align:right; white-space:nowrap;">
            <span style="background:#fef3c7; color:#92400e; padding:3px 10px;
                         border-radius:20px; font-size:12px; font-weight:600;">
              {dias_restantes} {'día' if dias_restantes == 1 else 'días'}
            </span>
          </td>
        </tr>
        """
        for o in obligaciones
    )

    plural = "obligación" if len(obligaciones) == 1 else "obligaciones"
    subject = (
        f"⏰ {dias_restantes} días para tu{' ' if len(obligaciones) == 1 else 's '}"
        f"{plural} fiscal{'es' if len(obligaciones) > 1 else ''}"
    )

    html = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:20px;background:#f0fdf4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;
              border:1px solid #bbf7d0;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.06);">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#052e16,#14532d);padding:24px 28px;">
      <div style="font-size:22px;font-weight:800;color:white;letter-spacing:-0.5px;">
        🏛️ ContadorMX
      </div>
      <div style="font-size:12px;color:#4ade80;margin-top:4px;letter-spacing:0.5px;text-transform:uppercase;">
        Recordatorio Fiscal
      </div>
    </div>

    <!-- Body -->
    <div style="padding:28px;">
      <p style="margin:0 0 6px;color:#374151;font-size:16px;font-weight:600;">
        Tienes {len(obligaciones)} {plural} {'próxima' if len(obligaciones) == 1 else 'próximas'}
      </p>
      <p style="margin:0 0 20px;color:#6b7280;font-size:14px;">{hoy}</p>

      <table style="width:100%;border-collapse:collapse;background:#f9fafb;
                    border-radius:10px;overflow:hidden;border:1px solid #d1fae5;">
        <thead>
          <tr style="background:#dcfce7;">
            <th style="padding:10px 12px;text-align:left;font-size:11px;
                       color:#15803d;text-transform:uppercase;letter-spacing:0.5px;">Obligación</th>
            <th style="padding:10px 12px;text-align:right;font-size:11px;
                       color:#15803d;text-transform:uppercase;letter-spacing:0.5px;">Faltan</th>
          </tr>
        </thead>
        <tbody>
          {items_html}
        </tbody>
      </table>

      <div style="margin:24px 0 8px;text-align:center;">
        <a href="{APP_URL}/dashboard"
           style="display:inline-block;background:linear-gradient(135deg,#16a34a,#15803d);
                  color:white;padding:13px 28px;border-radius:10px;text-decoration:none;
                  font-size:14px;font-weight:600;letter-spacing:0.2px;">
          Ver en ContadorMX →
        </a>
      </div>

      <hr style="border:none;border-top:1px solid #d1fae5;margin:24px 0;">
      <p style="color:#9ca3af;font-size:11px;text-align:center;margin:0;line-height:1.6;">
        Recibes esto porque tienes activas las notificaciones de calendario fiscal.<br>
        <a href="{APP_URL}/configuracion" style="color:#16a34a;">Ajustar preferencias</a>
      </p>
    </div>
  </div>
</body>
</html>
"""
    return await _send(destinatarios, subject, html)


# ── Bienvenida al registrarse ─────────────────────────────────────────────────

async def enviar_bienvenida(email: str, nombre: str) -> bool:
    subject = "¡Bienvenido a ContadorMX! 🏛️"
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:20px;background:#f0fdf4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;
              border:1px solid #bbf7d0;overflow:hidden;">

    <div style="background:linear-gradient(135deg,#052e16,#14532d);padding:28px;">
      <div style="font-size:24px;font-weight:800;color:white;">🏛️ ContadorMX</div>
      <div style="font-size:12px;color:#4ade80;margin-top:6px;text-transform:uppercase;letter-spacing:0.5px;">
        Tu agente fiscal IA para México
      </div>
    </div>

    <div style="padding:32px;">
      <h2 style="margin:0 0 8px;color:#052e16;font-size:20px;">
        Bienvenido, {nombre} 👋
      </h2>
      <p style="color:#374151;font-size:15px;line-height:1.7;margin:0 0 24px;">
        Tu cuenta está lista. Esto es lo que puedes hacer desde hoy:
      </p>

      <div style="display:grid;gap:12px;">
        {''.join(f"""
        <div style="display:flex;align-items:flex-start;gap:12px;padding:14px;
                    background:#f9fafb;border-radius:10px;border:1px solid #e5e7eb;">
          <span style="font-size:20px;">{icon}</span>
          <div>
            <div style="font-weight:600;color:#111827;font-size:14px;">{title}</div>
            <div style="color:#6b7280;font-size:13px;margin-top:2px;">{desc}</div>
          </div>
        </div>
        """ for icon, title, desc in [
          ("💬", "Chat fiscal IA", "Consulta ISR, IVA, IMSS, leyes y reformas en segundos"),
          ("👥", "Gestión de clientes", "Organiza tu cartera con contexto fiscal por cliente"),
          ("🗂️", "Documentos automáticos", "Sube XMLs, PDFs e imágenes — extracción automática de CFDI"),
          ("📅", "Calendario fiscal", "Recibe recordatorios 3 días antes de cada obligación"),
        ])}
      </div>

      <div style="margin:28px 0 8px;text-align:center;">
        <a href="{APP_URL}/dashboard"
           style="display:inline-block;background:linear-gradient(135deg,#16a34a,#15803d);
                  color:white;padding:14px 32px;border-radius:10px;text-decoration:none;
                  font-size:15px;font-weight:700;">
          Abrir ContadorMX →
        </a>
      </div>
    </div>
  </div>
</body>
</html>
"""
    return await _send([email], subject, html)


# ── Recuperación de contraseña ────────────────────────────────────────────────

async def enviar_reset_password(email: str, nombre: str, reset_url: str) -> bool:
    subject = "Restablecer contraseña — ContadorMX"
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:20px;background:#f0fdf4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:520px;margin:0 auto;background:white;border-radius:16px;
              border:1px solid #bbf7d0;overflow:hidden;">
    <div style="background:linear-gradient(135deg,#052e16,#14532d);padding:24px 28px;">
      <div style="font-size:20px;font-weight:800;color:white;">🏛️ ContadorMX</div>
    </div>
    <div style="padding:32px;">
      <h2 style="margin:0 0 8px;color:#052e16;font-size:18px;">Hola, {nombre}</h2>
      <p style="color:#374151;font-size:14px;line-height:1.7;margin:0 0 24px;">
        Recibimos una solicitud para restablecer la contraseña de tu cuenta.<br>
        Este enlace es válido por <strong>15 minutos</strong>.
      </p>
      <div style="text-align:center;margin-bottom:24px;">
        <a href="{reset_url}"
           style="display:inline-block;background:linear-gradient(135deg,#16a34a,#15803d);
                  color:white;padding:14px 32px;border-radius:10px;text-decoration:none;
                  font-size:15px;font-weight:700;">
          Restablecer contraseña →
        </a>
      </div>
      <p style="color:#9ca3af;font-size:12px;text-align:center;margin:0;line-height:1.6;">
        Si no solicitaste esto, ignora este email — tu contraseña no cambiará.<br>
        Por seguridad, no compartas este enlace.
      </p>
    </div>
  </div>
</body>
</html>
"""
    return await _send([email], subject, html)


# ── Alerta de reforma fiscal ──────────────────────────────────────────────────

async def enviar_alerta_reforma(
    destinatarios: list[str],
    titulo: str,
    url: str,
    fecha: str,
    fuente: str = "DOF",
) -> bool:
    fecha_fmt = fecha[:10] if fecha else "hoy"
    subject = f"🚨 Reforma fiscal detectada: {titulo[:80]}"
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:20px;background:#f0fdf4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:white;border-radius:16px;
              border:1px solid #bbf7d0;overflow:hidden;">
    <div style="background:linear-gradient(135deg,#052e16,#14532d);padding:24px 28px;">
      <div style="font-size:20px;font-weight:800;color:white;">🏛️ ContadorMX</div>
      <div style="font-size:12px;color:#f87171;margin-top:4px;font-weight:600;">Alerta de Reforma Fiscal</div>
    </div>
    <div style="padding:28px;">
      <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:10px;
                  padding:14px 16px;margin-bottom:20px;">
        <p style="margin:0;color:#dc2626;font-weight:600;font-size:14px;">
          🚨 Nueva publicación relevante en {fuente} — {fecha_fmt}
        </p>
      </div>
      <h2 style="margin:0 0 20px;color:#052e16;font-size:17px;line-height:1.4;">{titulo}</h2>
      <a href="{url}"
         style="display:inline-block;background:#16a34a;color:white;padding:12px 24px;
                border-radius:10px;text-decoration:none;font-size:14px;font-weight:600;">
        Ver publicación oficial →
      </a>
      <hr style="border:none;border-top:1px solid #d1fae5;margin:24px 0;">
      <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.6;">
        Analiza el impacto en tus clientes en
        <a href="{APP_URL}" style="color:#16a34a;">ContadorMX</a>.
        Verifica siempre con el texto oficial del DOF.
      </p>
    </div>
  </div>
</body>
</html>
"""
    return await _send(destinatarios, subject, html)
