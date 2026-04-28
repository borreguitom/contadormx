"""
IEPS — Impuesto Especial sobre Producción y Servicios — Versión mejorada
=========================================================================
Soporta TODAS las categorías 2025:
  - Bebidas alcohólicas (3 niveles según graduación)
  - Tabacos labrados (cigarros, puros, otros)
  - Combustibles automotrices (cuota fija por litro)
  - Bebidas saborizadas con azúcares añadidos (cuota fija por litro)
  - Bebidas energetizantes
  - Alimentos no básicos alta densidad calórica (8%)
  - Plaguicidas (3 categorías toxicidad)
  - Juegos con apuestas y sorteos
  - Redes públicas de telecomunicaciones

Soporta cálculo de:
  - IEPS trasladado (al vender)
  - IEPS acreditable (al comprar)
  - Base para IVA (precio + IEPS, Art. 18 LIVA)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional

from app.utils.constantes_fiscales import (
    IEPS_CATEGORIAS_2026,
    IVA_TASA_GENERAL,
    EJERCICIO_FISCAL_VIGENTE,
)


# ══════════════════════════════════════════════════════════════════════════
# Resultado estructurado
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ResultadoIEPS:
    categoria: str
    nombre_categoria: str
    fundamento: str
    ejercicio: int

    precio_enajenacion_sin_ieps: float
    cantidad_unidades: float
    unidad: str

    tipo_calculo: str  # 'tasa' o 'cuota_fija'
    tasa_aplicada: Optional[float]
    cuota_unitaria: Optional[float]

    base_ieps: float
    ieps_calculado: float

    iva_aplicado: bool
    base_iva: float
    iva_calculado: float

    precio_total_consumidor: float

    desglose: dict = field(default_factory=dict)
    advertencias: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ══════════════════════════════════════════════════════════════════════════
# Listar categorías disponibles
# ══════════════════════════════════════════════════════════════════════════

def listar_categorias_ieps() -> list[dict]:
    """Devuelve lista de todas las categorías IEPS para usar en frontend."""
    categorias = []
    for clave, info in IEPS_CATEGORIAS_2026.items():
        cat = {
            "clave": clave,
            "nombre": info["nombre"],
            "fundamento": info["fundamento"],
        }
        if "tasa" in info:
            cat["tipo"] = "tasa"
            cat["tasa_pct"] = info["tasa"] * 100
        if "cuota_litro" in info:
            cat["tipo"] = "cuota_litro"
            cat["cuota_litro"] = info["cuota_litro"]
        if "cuota_adicional_cigarro" in info:
            cat["cuota_adicional_cigarro"] = info["cuota_adicional_cigarro"]
        categorias.append(cat)
    return categorias


# ══════════════════════════════════════════════════════════════════════════
# Cálculo principal
# ══════════════════════════════════════════════════════════════════════════

def calcular_ieps(
    categoria: str,
    precio_enajenacion: float,
    *,
    cantidad_litros: float = 0.0,
    cantidad_cigarros: int = 0,
    incluir_iva: bool = True,
    es_acreditable: bool = False,
) -> dict:
    """
    Calcula IEPS según categoría.

    Tipos de cálculo:
    - Por TASA: IEPS = precio × tasa
    - Por CUOTA FIJA: IEPS = cantidad × cuota_unitaria
    - MIXTO (cigarros): IEPS = (precio × tasa) + (cigarros × cuota_adicional)

    El IEPS forma parte de la base para calcular IVA (Art. 18 LIVA).
    """
    advertencias = []
    notas = []

    # Validar categoría
    cat_norm = categoria.lower().replace(" ", "_").replace("-", "_")
    if cat_norm not in IEPS_CATEGORIAS_2026:
        return {
            "error": True,
            "mensaje": f"Categoría '{categoria}' no encontrada.",
            "categorias_disponibles": list(IEPS_CATEGORIAS_2026.keys()),
        }

    info = IEPS_CATEGORIAS_2026[cat_norm]
    nombre = info["nombre"]
    fundamento = info["fundamento"]

    # ═════════════════════════════════════════════════════════════
    # Determinar tipo de cálculo
    # ═════════════════════════════════════════════════════════════

    ieps_calculado = 0.0
    tipo_calculo = ""
    tasa_aplicada = None
    cuota_unitaria = None
    cantidad_unidades = 0.0
    unidad = ""
    desglose = {}

    if "cuota_litro" in info and "tasa" not in info:
        # Solo cuota fija por litro (combustibles, bebidas saborizadas)
        if cantidad_litros <= 0:
            advertencias.append(
                f"Categoría '{nombre}' requiere especificar cantidad_litros."
            )

        cuota_unitaria = info["cuota_litro"]
        cantidad_unidades = cantidad_litros
        unidad = "litros"
        ieps_calculado = round(cantidad_litros * cuota_unitaria, 2)
        tipo_calculo = "cuota_fija_por_litro"

        desglose = {
            "cuota_por_litro": cuota_unitaria,
            "litros": cantidad_litros,
            "ieps": ieps_calculado,
        }

    elif "tasa" in info and "cuota_adicional_cigarro" in info:
        # Cigarros: tasa sobre precio + cuota por unidad
        ieps_por_tasa = round(precio_enajenacion * info["tasa"], 2)
        ieps_por_cuota = round(cantidad_cigarros * info["cuota_adicional_cigarro"], 2)
        ieps_calculado = round(ieps_por_tasa + ieps_por_cuota, 2)

        tipo_calculo = "mixto_tasa_y_cuota_unitaria"
        tasa_aplicada = info["tasa"]
        cuota_unitaria = info["cuota_adicional_cigarro"]
        cantidad_unidades = cantidad_cigarros
        unidad = "cigarros"

        desglose = {
            "ieps_por_tasa": {
                "tasa": info["tasa"],
                "tasa_pct": f"{info['tasa']*100:.2f}%",
                "base": precio_enajenacion,
                "monto": ieps_por_tasa,
            },
            "ieps_por_cuota_adicional": {
                "cuota_por_cigarro": info["cuota_adicional_cigarro"],
                "cantidad_cigarros": cantidad_cigarros,
                "monto": ieps_por_cuota,
            },
            "total": ieps_calculado,
        }

    elif "tasa" in info:
        # Solo tasa (alcoholes, tabaco general, plaguicidas, etc.)
        tasa_aplicada = info["tasa"]
        ieps_calculado = round(precio_enajenacion * tasa_aplicada, 2)
        tipo_calculo = "tasa_porcentual"

        desglose = {
            "tasa": tasa_aplicada,
            "tasa_pct": f"{tasa_aplicada*100:.2f}%",
            "base": precio_enajenacion,
            "ieps": ieps_calculado,
        }

        # Si la categoría tiene cuota_litro adicional (bebidas saborizadas en algunos casos)
        if "cuota_litro" in info and cantidad_litros > 0:
            cuota_unitaria = info["cuota_litro"]
            ieps_cuota = round(cantidad_litros * cuota_unitaria, 2)
            ieps_calculado += ieps_cuota
            desglose["ieps_cuota_litro"] = ieps_cuota
            desglose["total"] = ieps_calculado

    # ═════════════════════════════════════════════════════════════
    # Base para IVA (Art. 18 LIVA)
    # ═════════════════════════════════════════════════════════════

    base_iva = precio_enajenacion + ieps_calculado
    iva_calculado = 0.0

    if incluir_iva:
        iva_calculado = round(base_iva * IVA_TASA_GENERAL, 2)
        notas.append(
            "El IEPS forma parte de la base gravable del IVA (Art. 18 LIVA)."
        )

    precio_total = round(base_iva + iva_calculado, 2)

    # ═════════════════════════════════════════════════════════════
    # Notas según categoría
    # ═════════════════════════════════════════════════════════════

    if "combustible" in cat_norm or "gasolina" in cat_norm or "diesel" in cat_norm:
        notas.append(
            "⛽ El IEPS de combustibles tiene cuotas fijas por litro (no porcentajes)."
        )
        notas.append(
            "Las cuotas se actualizan trimestralmente por SHCP."
        )

    if "alcoholic" in cat_norm or "cerveza" in cat_norm or "destilado" in cat_norm:
        notas.append(
            "🍺 El IEPS de bebidas alcohólicas se traslada y entera mensualmente."
        )

    if es_acreditable:
        notas.append(
            "✅ IEPS acreditable: solo si fuiste contribuyente del impuesto y "
            "el bien se utilizó en producción (Art. 4 LIEPS)."
        )

    return ResultadoIEPS(
        categoria=cat_norm,
        nombre_categoria=nombre,
        fundamento=fundamento,
        ejercicio=EJERCICIO_FISCAL_VIGENTE,

        precio_enajenacion_sin_ieps=round(precio_enajenacion, 2),
        cantidad_unidades=cantidad_unidades,
        unidad=unidad,

        tipo_calculo=tipo_calculo,
        tasa_aplicada=tasa_aplicada,
        cuota_unitaria=cuota_unitaria,

        base_ieps=round(precio_enajenacion, 2),
        ieps_calculado=ieps_calculado,

        iva_aplicado=incluir_iva,
        base_iva=round(base_iva, 2),
        iva_calculado=iva_calculado,

        precio_total_consumidor=precio_total,

        desglose=desglose,
        advertencias=advertencias,
        notas=notas,
    ).to_dict()
