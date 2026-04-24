from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt, JWTError
from datetime import datetime, timezone
import redis.asyncio as aioredis

from app.core.database import get_db, User
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

PLAN_LIMITS = {
    "free":    {"queries": 50,   "clientes": 5},
    "pro":     {"queries": 1000, "clientes": 50},
    "agencia": {"queries": -1,   "clientes": -1},
}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload["sub"])
        jti = payload.get("jti")
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # Verificar blocklist de logout
    if jti:
        async with aioredis.from_url(settings.REDIS_URL, decode_responses=True) as r:
            if await r.exists(f"logout:{jti}"):
                raise HTTPException(status_code=401, detail="Sesión cerrada. Vuelve a iniciar sesión.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    return user


def check_query_limit(user: User) -> tuple[bool, str, bool]:
    """Returns (allowed, error_message, month_reset_happened).
    Caller debe hacer db.flush() si month_reset_happened es True para garantizar
    que el reset persista incluso si el handler falla antes del commit final.
    """
    now = datetime.now(timezone.utc)
    reset_happened = False
    if user.queries_reset_date is None or user.queries_reset_date.month != now.month:
        user.queries_this_month = 0
        user.queries_reset_date = now
        reset_happened = True

    limit = PLAN_LIMITS.get(user.plan or "free", PLAN_LIMITS["free"])["queries"]
    if limit == -1:
        return True, "", reset_happened
    if user.queries_this_month >= limit:
        return False, f"Límite de {limit} consultas/mes alcanzado. Actualiza tu plan en Facturación.", reset_happened
    return True, "", reset_happened


def check_cliente_limit(user: User, current_count: int) -> tuple[bool, str]:
    limit = PLAN_LIMITS.get(user.plan or "free", PLAN_LIMITS["free"])["clientes"]
    if limit == -1:
        return True, ""
    if current_count >= limit:
        return False, f"Límite de {limit} clientes en plan {user.plan or 'free'}. Actualiza tu plan."
    return True, ""
