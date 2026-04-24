from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
import uuid

import redis.asyncio as aioredis

from app.core.database import get_db, User
from app.core.config import settings
from app.core.limiter import limiter
from app.core.deps import oauth2_scheme as _oauth2_scheme

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

RESET_TTL = 900  # 15 minutos


def _redis() -> aioredis.Redis:
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nombre: str = ""

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "jti": str(uuid.uuid4())},
        settings.JWT_SECRET,
        algorithm="HS256",
    )


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user = User(
        email=data.email,
        hashed_password=pwd_context.hash(data.password),
        nombre=data.nombre,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Email de bienvenida — Celery gestiona reintentos sin bloquear el response
    try:
        from celery_app import celery_app as _celery
        _celery.send_task(
            "app.tasks.emails.bienvenida",
            args=[user.email, user.nombre or user.email.split("@")[0]],
        )
    except Exception:
        pass

    return TokenResponse(access_token=create_token(user.id))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.username))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return TokenResponse(access_token=create_token(user.id))


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    # Siempre responde igual — no revelar si el email existe
    if not user or not user.is_active:
        return {"ok": True}

    token = str(uuid.uuid4())
    async with _redis() as r:
        await r.setex(f"reset:{token}", RESET_TTL, str(user.id))

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    try:
        from celery_app import celery_app as _celery
        _celery.send_task(
            "app.tasks.emails.reset_password",
            args=[user.email, user.nombre or user.email.split("@")[0], reset_url],
        )
    except Exception:
        pass

    return {"ok": True}


@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres")

    # GETDEL consume el token atómicamente — elimina la race condition TOCTOU
    async with _redis() as r:
        user_id_str = await r.getdel(f"reset:{data.token}")

    if not user_id_str:
        raise HTTPException(status_code=400, detail="Enlace inválido o expirado")

    result = await db.execute(select(User).where(User.id == int(user_id_str)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.hashed_password = pwd_context.hash(data.password)
    await db.commit()

    return TokenResponse(access_token=create_token(user.id))


@router.post("/logout")
async def logout(token: str = Depends(_oauth2_scheme)):
    """Invalida el JWT actual añadiéndolo al blocklist de Redis hasta que expire."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        jti = payload.get("jti")
        exp = payload.get("exp")
    except Exception:
        return {"ok": True}  # Token ya inválido — nada que hacer

    if jti and exp:
        ttl = exp - int(datetime.now(timezone.utc).timestamp())
        if ttl > 0:
            async with _redis() as r:
                await r.setex(f"logout:{jti}", ttl, "1")

    return {"ok": True}
