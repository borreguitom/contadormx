"""
Lógica de calendario fiscal mexicano — compartida entre dashboard, Celery y el agente.
"""
from __future__ import annotations
from datetime import date, timedelta

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# Fechas especiales fijas (mes, día, nombre, tipo)
_ESPECIALES: list[tuple[int, int, str, str]] = [
    (1, 17,  "Pagos provisionales ISR/IVA + DIOT (diciembre)",     "pago"),
    (2, 17,  "Pagos provisionales ISR/IVA + DIOT (enero)",         "pago"),
    (2, 28,  "Constancias de retenciones a trabajadores",           "informativa"),
    (3, 17,  "Pagos provisionales ISR/IVA + DIOT (febrero)",        "pago"),
    (3, 31,  "Declaración anual ISR — Personas Morales",            "declaracion"),
    (4, 17,  "Pagos provisionales ISR/IVA + DIOT (marzo)",          "pago"),
    (4, 30,  "Declaración anual ISR — Personas Físicas",            "declaracion"),
    (5, 15,  "PTU — plazo máximo pago Personas Morales",            "laboral"),
    (5, 17,  "Pagos provisionales ISR/IVA + DIOT (abril)",          "pago"),
    (6, 17,  "Pagos provisionales ISR/IVA + DIOT (mayo)",           "pago"),
    (6, 29,  "PTU — plazo máximo pago Personas Físicas",            "laboral"),
    (7, 17,  "Pagos provisionales ISR/IVA + DIOT (junio)",          "pago"),
    (8, 17,  "Pagos provisionales ISR/IVA + DIOT (julio)",          "pago"),
    (9, 17,  "Pagos provisionales ISR/IVA + DIOT (agosto)",         "pago"),
    (10, 17, "Pagos provisionales ISR/IVA + DIOT (septiembre)",     "pago"),
    (11, 17, "Pagos provisionales ISR/IVA + DIOT (octubre)",        "pago"),
    (12, 17, "Pagos provisionales ISR/IVA + DIOT (noviembre)",      "pago"),
    (12, 20, "Aguinaldo — pago máximo a trabajadores",              "laboral"),
]


def obligaciones_para_fecha(referencia: date, ventana_dias: int = 90) -> list[dict]:
    """Devuelve obligaciones vigentes desde `referencia` hasta `referencia + ventana_dias`."""
    hasta = referencia + timedelta(days=ventana_dias)
    resultado: list[dict] = []

    for mes_num, dia, nombre, tipo in _ESPECIALES:
        for anio in [referencia.year, referencia.year + 1]:
            try:
                d = date(anio, mes_num, dia)
            except ValueError:
                continue
            if referencia <= d <= hasta:
                resultado.append({
                    "fecha": d.isoformat(),
                    "dia": dia,
                    "mes": MESES_ES[mes_num].capitalize(),
                    "anio": anio,
                    "nombre": nombre,
                    "tipo": tipo,
                    "dias_restantes": (d - referencia).days,
                })

    resultado.sort(key=lambda x: x["fecha"])
    return resultado


def proximas_obligaciones(n: int = 5) -> list[dict]:
    """Shortcut: próximas n obligaciones desde hoy."""
    return obligaciones_para_fecha(date.today())[:n]


def obligaciones_en_exactamente(dias: int) -> list[dict]:
    """Obligaciones que vencen exactamente en `dias` días desde hoy. Para recordatorios."""
    hoy = date.today()
    target = hoy + timedelta(days=dias)
    return [
        o for o in obligaciones_para_fecha(hoy, ventana_dias=dias + 1)
        if o["fecha"] == target.isoformat()
    ]
