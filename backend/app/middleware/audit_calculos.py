"""
Middleware: AuditoriaCalculosMiddleware
=========================================
Captura automáticamente cada llamada a /api/v2/calc/* y la persiste
en la tabla calculos_fiscales.

Uso en main.py:
    from app.middleware.audit_calculos import AuditoriaCalculosMiddleware
    app.add_middleware(AuditoriaCalculosMiddleware)
"""
from __future__ import annotations
import json
import logging
import uuid
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from app.database import SessionLocal  # ← Ajustar al import real
from app.repositories.calculo_fiscal_repository import CalculoFiscalRepository

logger = logging.getLogger(__name__)


# Mapeo endpoint → tipo_calculo
ENDPOINT_TO_TIPO = {
    "/api/v2/calc/isr-pf": "isr_pf",
    "/api/v2/calc/isr-pm": "isr_pm",
    "/api/v2/calc/iva": "iva",
    "/api/v2/calc/ieps": "ieps",
    "/api/v2/calc/imss": "imss",
    "/api/v2/calc/nomina": "nomina",
    "/api/v2/calc/finiquito": "finiquito",
}


class AuditoriaCalculosMiddleware(BaseHTTPMiddleware):
    """
    Intercepta peticiones a /api/v2/calc/* y guarda el cálculo en BD.

    No bloquea la respuesta al usuario: si la auditoría falla, se logea
    pero la respuesta del cálculo se entrega normalmente.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Solo auditar endpoints de cálculo POST
        if request.method != "POST" or request.url.path not in ENDPOINT_TO_TIPO:
            return await call_next(request)

        tipo_calculo = ENDPOINT_TO_TIPO[request.url.path]
        request_id = str(uuid.uuid4())

        # Capturar body del request
        body_bytes = await request.body()
        try:
            parametros_entrada = json.loads(body_bytes) if body_bytes else {}
        except json.JSONDecodeError:
            parametros_entrada = {"raw": body_bytes.decode("utf-8", errors="ignore")}

        # Re-inyectar el body porque ya lo consumimos
        async def receive():
            return {"type": "http.request", "body": body_bytes}
        request._receive = receive

        # Procesar request
        response = await call_next(request)

        # Capturar body de respuesta
        if isinstance(response, StreamingResponse):
            body_chunks = []
            async for chunk in response.body_iterator:
                body_chunks.append(chunk)
            response_body = b"".join(body_chunks)

            # Reconstruir respuesta
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        else:
            response_body = getattr(response, "body", b"")

        # Solo auditar si fue exitoso
        if 200 <= response.status_code < 300:
            try:
                resultado = json.loads(response_body) if response_body else {}
                self._guardar_auditoria(
                    request=request,
                    tipo_calculo=tipo_calculo,
                    parametros_entrada=parametros_entrada,
                    resultado=resultado,
                    request_id=request_id,
                )
            except Exception as e:
                # Auditoría no bloqueante: solo log
                logger.warning(
                    f"No se pudo registrar auditoría de {tipo_calculo}: {e}"
                )

        return response

    def _guardar_auditoria(
        self,
        *,
        request: Request,
        tipo_calculo: str,
        parametros_entrada: dict,
        resultado: dict,
        request_id: str,
    ):
        """Persiste el cálculo en la tabla de auditoría."""
        # Extraer usuario del request (depende de tu auth)
        usuario_id = self._extraer_usuario_id(request)
        if not usuario_id:
            return  # Sin usuario, no auditamos

        # Extraer datos identificatorios
        datos_id = self._extraer_datos_identificatorios(parametros_entrada, tipo_calculo)

        # IP del cliente
        ip_origen = self._obtener_ip(request)

        # User-Agent
        user_agent = request.headers.get("user-agent", "")[:500]

        with SessionLocal() as db:
            try:
                repo = CalculoFiscalRepository(db)
                repo.crear(
                    usuario_id=usuario_id,
                    tipo_calculo=tipo_calculo,
                    ejercicio_fiscal=resultado.get("ejercicio_fiscal", 2025),
                    parametros_entrada=parametros_entrada,
                    resultado=resultado,
                    cliente_id=datos_id.get("cliente_id"),
                    subtipo=datos_id.get("subtipo"),
                    periodo=datos_id.get("periodo"),
                    mes=datos_id.get("mes"),
                    rfc_contribuyente=datos_id.get("rfc_contribuyente"),
                    rfc_empleador=datos_id.get("rfc_empleador"),
                    nombre_contribuyente=datos_id.get("nombre_contribuyente"),
                    ip_origen=ip_origen,
                    user_agent=user_agent,
                    request_id=request_id,
                )
                db.commit()
                logger.info(
                    f"Auditoría {tipo_calculo} guardada — request_id={request_id}"
                )
            except Exception as e:
                db.rollback()
                logger.error(f"Error al persistir auditoría: {e}", exc_info=True)

    @staticmethod
    def _extraer_usuario_id(request: Request) -> Optional[int]:
        """Extrae usuario_id del request. Ajustar según tu sistema auth."""
        # Opción 1: middleware de auth ya colocó user en request.state
        user = getattr(request.state, "user", None)
        if user:
            return getattr(user, "id", None)

        # Opción 2: middleware ya colocó user_id directamente
        return getattr(request.state, "user_id", None)

    @staticmethod
    def _extraer_datos_identificatorios(params: dict, tipo: str) -> dict:
        """Extrae RFCs, nombres, período del payload."""
        datos = {
            "cliente_id": params.get("cliente_id"),
            "rfc_contribuyente": None,
            "rfc_empleador": None,
            "nombre_contribuyente": None,
            "subtipo": None,
            "periodo": params.get("periodo"),
            "mes": params.get("mes"),
        }

        # Trabajador (nómina/finiquito)
        if "trabajador" in params and isinstance(params["trabajador"], dict):
            t = params["trabajador"]
            datos["rfc_contribuyente"] = t.get("rfc")
            datos["nombre_contribuyente"] = t.get("nombre_completo")

        # Empleador
        if "empleador" in params and isinstance(params["empleador"], dict):
            e = params["empleador"]
            datos["rfc_empleador"] = e.get("rfc")

        # Contribuyente (ISR/IVA/IEPS)
        if "contribuyente" in params and isinstance(params["contribuyente"], dict):
            c = params["contribuyente"]
            datos["rfc_contribuyente"] = c.get("rfc")
            datos["nombre_contribuyente"] = c.get("nombre_o_razon_social")

        # Subtipo según tipo de cálculo
        if tipo == "isr_pf":
            datos["subtipo"] = params.get("regimen", "sueldos")
        elif tipo == "isr_pm":
            datos["subtipo"] = params.get("regimen", "general")
        elif tipo == "finiquito":
            datos["subtipo"] = params.get("tipo_separacion", "renuncia")
        elif tipo == "ieps":
            datos["subtipo"] = params.get("categoria")

        return datos

    @staticmethod
    def _obtener_ip(request: Request) -> Optional[str]:
        """Obtiene IP real considerando proxies (X-Forwarded-For)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return None
