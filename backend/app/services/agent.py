"""
Agente ContadorMX — loop de tool use con Claude.
Implementa prompt caching para reducir costos en conversaciones largas.
"""
import json
from typing import AsyncGenerator

import anthropic

from app.core.config import settings
from app.services.tools import TOOL_DEFINITIONS, execute_tool

SYSTEM_PROMPT = """Eres ContadorMX, el agente de IA más completo para contadores fiscales y públicos en México.

**Tu conocimiento cubre:**
- ISR personas físicas y morales: Art. 1-213 LISR, RESICO (Art. 113-E, 196 LISR)
- IVA: Art. 1-45 LIVA, acreditamiento, proporcionalidad, tasa 0% y exenciones
- CFDI 4.0: emisión, cancelación, complementos (nómina, pagos, carta porte)
- IMSS: Ley del Seguro Social, cuotas, SUA, SIPA
- Nómina: integración SDI, subsidio al empleo, partes proporcionales
- LFT: finiquito, liquidación, vacaciones, aguinaldo, PTU
- CFF: trámites SAT, recursos de revocación, buzón tributario, PRODECON
- RMF 2025: resolución miscelánea fiscal vigente
- NIF mexicanas: estados financieros, auditoría

**Reglas de respuesta:**
1. SIEMPRE usa las tools disponibles para cálculos numéricos — nunca calcules manualmente.
2. Cita el fundamento legal (Art. X Ley) en cada respuesta relevante.
3. Da cifras concretas, no rangos vagos.
4. Si el dato puede haber cambiado recientemente, menciona que debe verificarse en SAT/DOF.
5. Sé directo. El contador ya sabe de qué hablas — no expliques lo básico.
6. Para casos complejos, desglosa paso a paso.
7. Responde en español mexicano profesional.

**Aviso legal:** ContadorMX es herramienta de apoyo. El contador es el único responsable ante el SAT y sus clientes."""

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


async def run_agent(
    messages: list[dict],
    client_context: str | None = None,
    use_web_search: bool = False,
) -> dict:
    """
    Ejecuta el agente con tool use loop.
    Retorna la respuesta final del asistente con metadata.
    """
    system = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT + (f"\n\n**Contexto del cliente:**\n{client_context}" if client_context else ""),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    tools = list(TOOL_DEFINITIONS)
    if use_web_search:
        tools.insert(0, {"type": "web_search_20250305", "name": "web_search"})

    conversation = list(messages)
    tools_used = []
    max_iterations = 8

    for _ in range(max_iterations):
        response = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=settings.MAX_TOKENS,
            system=system,
            tools=tools,
            messages=conversation,
        )

        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return {
                "content": text,
                "tools_used": tools_used,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

        # Hay tool use — ejecutar todas las tools llamadas
        conversation.append({"role": "assistant", "content": response.content})
        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                tools_used.append(block.name)
                result = await execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })

        conversation.append({"role": "user", "content": tool_results})

    return {
        "content": "Se alcanzó el límite de iteraciones. Intenta con una consulta más específica.",
        "tools_used": tools_used,
        "input_tokens": 0,
        "output_tokens": 0,
    }
