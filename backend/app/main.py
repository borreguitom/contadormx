from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import json

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.api.routes import health, chat, calc, cfdi, clients, auth, laws, docs, dashboard, billing, documentos


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(
    title="ContadorMX API",
    description="Agente fiscal y contable para México",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else json.loads(settings.CORS_ORIGINS)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(clients.router, prefix="/api/clients", tags=["clients"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(calc.router, prefix="/api/calc", tags=["calculadoras"])
app.include_router(cfdi.router, prefix="/api/cfdi", tags=["cfdi"])
app.include_router(laws.router, prefix="/api/laws", tags=["laws"])
app.include_router(docs.router, prefix="/api/docs", tags=["documentos"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])
app.include_router(documentos.router, prefix="/api/documentos", tags=["documentos-clientes"])
