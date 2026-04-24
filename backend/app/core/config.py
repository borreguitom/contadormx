from pydantic_settings import BaseSettings
from typing import List
import logging
import sys

logger = logging.getLogger(__name__)

_INSECURE_JWT_DEFAULT = "dev-secret-change-in-production"


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    DATABASE_URL: str = "postgresql://contadormx:contadormx_dev@localhost:5432/contadormx"
    REDIS_URL: str = "redis://localhost:6379/0"

    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "contadormx-laws"
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX: str = "contadormx-laws"

    VOYAGE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    EMBEDDING_PROVIDER: str = "voyage"

    RESEND_API_KEY: str = ""

    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_AGENCIA: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    JWT_SECRET: str = _INSECURE_JWT_DEFAULT
    JWT_EXPIRE_MINUTES: int = 10080

    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    APP_ENV: str = "development"

    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    MAX_TOKENS: int = 4096

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Validación de seguridad: JWT_SECRET no debe ser el default ni menor a 32 chars
_jwt_insecure = (
    settings.JWT_SECRET == _INSECURE_JWT_DEFAULT
    or len(settings.JWT_SECRET) < 32
)
if _jwt_insecure:
    if settings.APP_ENV != "development":
        sys.exit(
            "FATAL: JWT_SECRET es inseguro. "
            "Configura un secreto aleatorio de ≥32 caracteres en tu .env antes de arrancar en producción."
        )
    else:
        logger.warning(
            "⚠️  JWT_SECRET inseguro detectado. "
            "Aceptable solo en development. Configura uno fuerte antes de pasar a producción."
        )

_DB_DEFAULT = "postgresql://contadormx:contadormx_dev@localhost:5432/contadormx"
if settings.DATABASE_URL == _DB_DEFAULT and settings.APP_ENV != "development":
    sys.exit(
        "FATAL: DATABASE_URL usa credenciales por defecto. "
        "Configura usuario, password y host reales en tu .env antes de arrancar en producción."
    )
elif settings.DATABASE_URL == _DB_DEFAULT:
    logger.warning(
        "⚠️  DATABASE_URL usa credenciales de desarrollo. "
        "Cambia usuario y password antes de desplegar a producción."
    )
