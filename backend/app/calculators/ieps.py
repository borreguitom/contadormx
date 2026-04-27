"""
IEPS — Ley del Impuesto Especial sobre Producción y Servicios 2025.
Tasas vigentes: Art. 2 LIEPS y sus fracciones.
"""
from dataclasses import dataclass, field
from typing import Literal

# ─── Tasas vigentes 2025 ──────────────────────────────────────────────────────

CATEGORIAS = {
    "bebidas_alcoholicas_hasta_14gl": {
        "descripcion": "Bebidas alcohólicas hasta 14° GL (cerveza, sidra, vino)",
        "tasa": 0.265,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso A) LIEPS",
    },
    "bebidas_alcoholicas_mas_20gl": {
        "descripcion": "Bebidas alcohólicas más de 20° GL (destilados, licores)",
        "tasa": 0.53,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso C) LIEPS",
    },
    "alcohol_desnaturalizado": {
        "descripcion": "Alcohol etílico y alcohol desnaturalizado",
        "tasa": 0.50,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso B) LIEPS",
    },
    "tabacos_cigarros": {
        "descripcion": "Cigarros y tabacos labrados (excepto puros)",
        "tasa": 1.60,
        "cuota_adicional": 0.35,  # pesos por cigarro
        "tipo": "ad_valorem_mas_cuota",
        "fundamento": "Art. 2 Fracc. I inciso D) LIEPS",
    },
    "tabacos_puros": {
        "descripcion": "Puros y otros tabacos labrados hechos enteramente a mano",
        "tasa": 0.306,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso D) numeral 3 LIEPS",
    },
    "bebidas_energizantes": {
        "descripcion": "Bebidas energizantes con cafeína, taurina, glucuronolactona",
        "tasa": 0.25,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso G) LIEPS",
    },
    "bebidas_azucaradas": {
        "descripcion": "Bebidas azucaradas (refrescos, aguas saborizadas con azúcar añadida)",
        "tasa": None,
        "cuota_litro": 1.46,
        "tipo": "cuota_litro",
        "fundamento": "Art. 2 Fracc. I inciso F) LIEPS",
    },
    "alimentos_hcnc": {
        "descripcion": "Alimentos con alto contenido calórico (≥275 kcal/100g)",
        "tasa": 0.08,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso J) LIEPS",
    },
    "plaguicidas_clase_1": {
        "descripcion": "Plaguicidas toxicidad Clase I (extremadamente peligrosos)",
        "tasa": 0.09,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso I) LIEPS",
    },
    "plaguicidas_clase_2": {
        "descripcion": "Plaguicidas toxicidad Clase II (moderadamente peligrosos)",
        "tasa": 0.07,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso I) LIEPS",
    },
    "plaguicidas_clase_3_4": {
        "descripcion": "Plaguicidas toxicidad Clase III y IV (ligeramente peligrosos)",
        "tasa": 0.06,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. I inciso I) LIEPS",
    },
    "juegos_sorteos": {
        "descripcion": "Juegos con apuestas y sorteos (casinos, loterías)",
        "tasa": 0.30,
        "tipo": "ad_valorem",
        "fundamento": "Art. 2 Fracc. II LIEPS",
    },
    "combustibles_gasolina_magna": {
        "descripcion": "Gasolina Magna (cuota por litro, actualizable)",
        "tasa": None,
        "cuota_litro": 5.95,
        "tipo": "cuota_litro",
        "fundamento": "Art. 2-A LIEPS (cuota actualizada DOF 2025)",
    },
    "combustibles_gasolina_premium": {
        "descripcion": "Gasolina Premium (cuota por litro)",
        "tasa": None,
        "cuota_litro": 5.75,
        "tipo": "cuota_litro",
        "fundamento": "Art. 2-A LIEPS (cuota actualizada DOF 2025)",
    },
    "combustibles_diesel": {
        "descripcion": "Diésel (cuota por litro)",
        "tasa": None,
        "cuota_litro": 6.24,
        "tipo": "cuota_litro",
        "fundamento": "Art. 2-A LIEPS (cuota actualizada DOF 2025)",
    },
}


def calcular_ieps(
    categoria: str,
    base_gravable: float = 0.0,
    litros: float = 0.0,
    cantidad_cigarros: int = 0,
    incluye_iva: bool = False,
) -> dict:
    """
    Calcula IEPS según categoría y base gravable.
    - Ad valorem: base_gravable en pesos (precio enajenación sin IEPS)
    - Cuota por litro: litros consumidos/enajenados
    - Tabacos con cuota adicional: base_gravable + cantidad_cigarros
    """
    if categoria not in CATEGORIAS:
        return {
            "error": f"Categoría '{categoria}' no reconocida.",
            "categorias_disponibles": list(CATEGORIAS.keys()),
        }

    cat = CATEGORIAS[categoria]
    tipo = cat["tipo"]
    ieps = 0.0
    desglose = {}

    if tipo == "ad_valorem":
        ieps = round(base_gravable * cat["tasa"], 2)
        desglose = {
            "base_gravable": round(base_gravable, 2),
            "tasa": f"{cat['tasa'] * 100:.1f}%",
            "ieps_calculado": ieps,
        }

    elif tipo == "cuota_litro":
        ieps = round(litros * cat["cuota_litro"], 2)
        desglose = {
            "litros": litros,
            "cuota_por_litro": cat["cuota_litro"],
            "ieps_calculado": ieps,
        }

    elif tipo == "ad_valorem_mas_cuota":
        ieps_pct = round(base_gravable * cat["tasa"], 2)
        ieps_cuota = round(cantidad_cigarros * cat["cuota_adicional"], 2)
        ieps = round(ieps_pct + ieps_cuota, 2)
        desglose = {
            "base_gravable": round(base_gravable, 2),
            "tasa_ad_valorem": f"{cat['tasa'] * 100:.0f}%",
            "ieps_ad_valorem": ieps_pct,
            "cantidad_cigarros": cantidad_cigarros,
            "cuota_adicional_por_cigarro": cat["cuota_adicional"],
            "ieps_cuota_adicional": ieps_cuota,
            "ieps_total": ieps,
        }

    iva_sobre_ieps = 0.0
    precio_final = round(base_gravable + ieps, 2)
    if incluye_iva:
        iva_sobre_ieps = round((base_gravable + ieps) * 0.16, 2)
        precio_final = round(base_gravable + ieps + iva_sobre_ieps, 2)

    return {
        "categoria": categoria,
        "descripcion": cat["descripcion"],
        "fundamento": cat["fundamento"],
        "tipo_calculo": tipo,
        "ieps": ieps,
        "base_gravable": round(base_gravable, 2),
        "iva_sobre_base_mas_ieps": iva_sobre_ieps if incluye_iva else "No solicitado",
        "precio_final_con_ieps": precio_final,
        "desglose": desglose,
        "nota": (
            "El IEPS forma parte de la base para IVA cuando aplica (Art. 18 LIVA). "
            "En transferencias entre contribuyentes del mismo bien, el IEPS es acreditable (Art. 4 LIEPS)."
        ),
    }


def listar_categorias() -> dict:
    return {
        k: {
            "descripcion": v["descripcion"],
            "tasa": f"{v['tasa']*100:.1f}%" if v.get("tasa") else f"${v.get('cuota_litro', 0):.2f}/litro",
            "fundamento": v["fundamento"],
        }
        for k, v in CATEGORIAS.items()
    }
