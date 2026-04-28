"""
INEGI scraper — INPC mensual y UMA vigente.
INPC: series del BIE (Banco de Información Económica).
UMA: publicada en DOF cada febrero.
"""
from datetime import datetime, timezone
from typing import Optional

import httpx

# API del BIE — no requiere API key para series públicas
INPC_API = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/628194/es/0700/false/BIE/2.0/token_no_requerido"

# Valores estáticos de respaldo 2026 (actualizar anualmente)
VALORES_2026 = {
    "uma_diaria": 117.31,                          # INEGI comunicado 1/26, vigente 1 feb 2026
    "uma_mensual": round(117.31 * 30.4, 2),        # 3,566.22
    "uma_anual": round(117.31 * 365.25, 2),        # 42,846.08
    "salario_minimo_diario_general": 315.04,        # CONASAMI, vigente 1 ene 2026
    "salario_minimo_diario_zona_libre_norte": 440.87,
    "inpc_base": 131.50,                           # valor aproximado ene 2026 (base 2Q 2018=100)
    "fecha_actualizacion": "2026-01-01",
}

# Alias para retrocompatibilidad
VALORES_2025 = VALORES_2026


async def fetch_inpc_actual() -> dict:
    """
    Obtiene el INPC más reciente del BIE-INEGI.
    Si la API falla, retorna los valores estáticos.
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/628194/es/0700/false/BIE/2.0/token_no_requerido",
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                series = data.get("Series", [])
                if series:
                    obs = series[0].get("OBSERVATIONS", [])
                    if obs:
                        last = obs[-1]
                        return {
                            "inpc": float(last.get("OBS_VALUE", 0)),
                            "periodo": last.get("TIME_PERIOD", ""),
                            "fuente": "INEGI BIE",
                            "fecha_consulta": datetime.now(timezone.utc).isoformat(),
                        }
    except Exception:
        pass

    return {
        "inpc": VALORES_2026["inpc_base"],
        "periodo": "2026-01",
        "fuente": "valores_estaticos_2026",
        "fecha_consulta": datetime.now(timezone.utc).isoformat(),
        "nota": "API INEGI no disponible. Usando valores base 2026.",
    }


def get_uma_2025() -> dict:
    return {
        "uma_diaria": VALORES_2026["uma_diaria"],
        "uma_mensual": VALORES_2026["uma_mensual"],
        "uma_anual": VALORES_2026["uma_anual"],
        "salario_minimo_diario": VALORES_2026["salario_minimo_diario_general"],
        "salario_minimo_zona_norte": VALORES_2026["salario_minimo_diario_zona_libre_norte"],
        "fundamento": "DOF 09-dic-2025 (SM) · INEGI comunicado 1/26 (UMA)",
        "vigencia": "1 enero 2026 — 31 diciembre 2026",
    }


def calcular_actualizacion_inpc(monto: float, inpc_actual: float, inpc_cuando: float) -> dict:
    """
    Actualización de cantidades usando INPC — Art. 17-A CFF.
    factor = INPC_actual / INPC_cuando_se_adquirió
    """
    if inpc_cuando <= 0:
        return {"error": "INPC_cuando no puede ser 0"}

    factor = inpc_actual / inpc_cuando
    monto_actualizado = round(monto * factor, 2)

    return {
        "monto_original": round(monto, 2),
        "inpc_actual": inpc_actual,
        "inpc_historico": inpc_cuando,
        "factor_actualizacion": round(factor, 6),
        "monto_actualizado": monto_actualizado,
        "incremento": round(monto_actualizado - monto, 2),
        "fundamento": "Art. 17-A CFF",
    }
