"""
Definiciones de tools para Claude + ejecutores que llaman a las calculadoras.
El agente decide qué tool usar; aquí están los schemas y la lógica de dispatch.
"""
from typing import Any

from app.calculators.isr import calcular_isr_pf, calcular_isr_pm
from app.calculators.iva import calcular_iva
from app.calculators.imss import calcular_cuotas_imss
from app.calculators.nomina import calcular_nomina
from app.calculators.finiquito import calcular_finiquito
from app.calculators.declaracion_anual import calcular_declaracion_anual_pf


TOOL_DEFINITIONS = [
    {
        "name": "calcular_isr_personas_fisicas",
        "description": (
            "Calcula ISR (Impuesto Sobre la Renta) para personas físicas en México. "
            "Aplica según el régimen: sueldos y salarios (Art. 96 LISR), actividades empresariales "
            "y honorarios (Art. 106 LISR), arrendamiento (Art. 116 LISR), RESICO PF (Art. 113-E LISR). "
            "Devuelve ISR determinado, subsidio al empleo y monto a retener/enterar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ingresos_mensuales": {
                    "type": "number",
                    "description": "Ingresos brutos del periodo en pesos MXN.",
                },
                "regimen": {
                    "type": "string",
                    "enum": ["sueldos", "honorarios", "actividades_empresariales", "arrendamiento", "resico_pf"],
                    "description": "Régimen fiscal del contribuyente.",
                },
                "deducciones_mensuales": {
                    "type": "number",
                    "description": "Deducciones autorizadas del periodo (aplica en honorarios/act. empresariales).",
                    "default": 0,
                },
                "periodo": {
                    "type": "string",
                    "enum": ["mensual", "anual"],
                    "default": "mensual",
                },
            },
            "required": ["ingresos_mensuales"],
        },
    },
    {
        "name": "calcular_isr_personas_morales",
        "description": (
            "Calcula pago provisional ISR para personas morales. "
            "Régimen general (Art. 14 LISR) — coeficiente de utilidad sobre ingresos acumulados. "
            "RESICO PM (Art. 196 LISR) — 1% sobre ingresos cobrados."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ingresos_acumulados": {
                    "type": "number",
                    "description": "Ingresos acumulados desde enero hasta el mes en cálculo.",
                },
                "coeficiente_utilidad": {
                    "type": "number",
                    "description": "Coeficiente de utilidad del ejercicio anterior. Si es empresa nueva, usar valores de Art. 14 LISR según giro.",
                    "default": 0.20,
                },
                "pagos_provisionales_previos": {
                    "type": "number",
                    "description": "Suma de pagos provisionales ya enterados en el año.",
                    "default": 0,
                },
                "retenciones": {
                    "type": "number",
                    "description": "Retenciones de ISR acreditables del periodo.",
                    "default": 0,
                },
                "mes": {
                    "type": "integer",
                    "description": "Número del mes del pago provisional (1=enero … 12=diciembre).",
                    "minimum": 1,
                    "maximum": 12,
                },
                "regimen": {
                    "type": "string",
                    "enum": ["general", "resico_pm"],
                    "default": "general",
                },
            },
            "required": ["ingresos_acumulados"],
        },
    },
    {
        "name": "calcular_iva",
        "description": (
            "Determina IVA a cargo o a favor en una declaración mensual. "
            "Aplica acreditamiento (Art. 5 LIVA), proporcionalidad si hay actos exentos (Art. 5-C LIVA). "
            "Tasas: 16% general, 0% exportaciones/alimentos/medicinas, exento."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ventas_16": {"type": "number", "description": "Ventas gravadas al 16% (valor sin IVA).", "default": 0},
                "ventas_0": {"type": "number", "description": "Ventas tasa 0% (exportaciones, alimentos, medicinas).", "default": 0},
                "ventas_exentas": {"type": "number", "description": "Ventas exentas (Art. 15-18 LIVA).", "default": 0},
                "compras_16_acreditables": {"type": "number", "description": "Compras/gastos gravados al 16% acreditables.", "default": 0},
                "compras_0_acreditables": {"type": "number", "description": "Compras tasa 0% acreditables.", "default": 0},
                "compras_exentas": {"type": "number", "description": "Compras exentas (IVA no acreditable).", "default": 0},
                "saldo_favor_anterior": {"type": "number", "description": "Saldo a favor de periodos anteriores.", "default": 0},
                "periodo": {"type": "string", "default": "mensual"},
            },
        },
    },
    {
        "name": "calcular_cuotas_imss",
        "description": (
            "Calcula cuotas obrero-patronales IMSS + INFONAVIT + SAR para un trabajador. "
            "Basado en el Salario Diario Integrado (SDI). Incluye riesgo de trabajo, invalidez/vida, "
            "enfermedad/maternidad, guarderías. Valores UMA 2025."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "salario_diario_integrado": {
                    "type": "number",
                    "description": "SDI = (salario base + partes proporcionales de aguinaldo/vacaciones/prima) / 30. Tope 25 UMAs.",
                },
                "prima_riesgo_trabajo": {
                    "type": "number",
                    "description": "Prima SIPA determinada por IMSS. Default 0.54355% (promedio nacional).",
                    "default": 0.0054355,
                },
            },
            "required": ["salario_diario_integrado"],
        },
    },
    {
        "name": "calcular_nomina",
        "description": (
            "Genera comprobante de nómina completo: percepciones, deducciones, neto a pagar y costo empresa. "
            "Integra ISR Art. 96 LISR, subsidio al empleo, cuotas IMSS obrero. "
            "Periodos: semanal, catorcenal, quincenal, mensual."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "salario_mensual_bruto": {"type": "number", "description": "Salario base mensual en pesos."},
                "periodo": {"type": "string", "enum": ["semanal", "catorcenal", "quincenal", "mensual"], "default": "mensual"},
                "otras_percepciones": {"type": "number", "description": "Bonos, comisiones, horas extra, etc. gravables.", "default": 0},
                "vales_despensa": {"type": "number", "description": "Vales de despensa (exentos hasta 40% UMA mensual).", "default": 0},
            },
            "required": ["salario_mensual_bruto"],
        },
    },
    {
        "name": "calcular_finiquito",
        "description": (
            "Calcula finiquito o liquidación según el tipo de separación laboral (Art. 76, 80, 87, 50, 162 LFT). "
            "Para despido injustificado incluye: 3 meses, 20 días por año, prima de antigüedad. "
            "Para renuncia: partes proporcionales + prima antigüedad si aplica."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "salario_diario": {"type": "number", "description": "Salario diario del trabajador."},
                "dias_trabajados_anio": {"type": "integer", "description": "Días trabajados en el año en curso."},
                "anios_servicio": {"type": "number", "description": "Total de años de antigüedad.", "default": 0},
                "tipo_separacion": {
                    "type": "string",
                    "enum": ["renuncia", "despido_injustificado", "despido_justificado", "mutuo_acuerdo"],
                    "default": "renuncia",
                },
                "vacaciones_gozadas": {"type": "integer", "description": "Días de vacaciones ya disfrutados en el año.", "default": 0},
            },
            "required": ["salario_diario", "dias_trabajados_anio"],
        },
    },
    {
        "name": "calcular_declaracion_anual_pf",
        "description": (
            "Calcula la Declaración Anual ISR para Personas Físicas (Art. 150-152 LISR). "
            "Acumula ingresos de todos los regímenes, aplica deducciones personales Art. 151 LISR "
            "(gastos médicos, GMM, intereses hipotecarios, donativos, AFORE, colegiaturas) con límites 2025, "
            "aplica tarifa anual Art. 152 y determina saldo a cargo o saldo a favor. "
            "Vencimiento: 30 de abril del año siguiente al ejercicio."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ingresos_sueldos":               {"type": "number", "default": 0, "description": "Ingresos anuales por sueldos y salarios."},
                "ingresos_honorarios":            {"type": "number", "default": 0, "description": "Ingresos anuales por honorarios (servicios profesionales)."},
                "ingresos_arrendamiento":         {"type": "number", "default": 0, "description": "Ingresos anuales por arrendamiento de inmuebles."},
                "ingresos_actividad_empresarial": {"type": "number", "default": 0, "description": "Ingresos anuales por actividad empresarial."},
                "ingresos_intereses":             {"type": "number", "default": 0, "description": "Intereses reales acumulables del ejercicio."},
                "ingresos_dividendos":            {"type": "number", "default": 0, "description": "Dividendos acumulables del ejercicio."},
                "ingresos_otros":                 {"type": "number", "default": 0, "description": "Otros ingresos acumulables."},
                "retenciones_sueldos":            {"type": "number", "default": 0, "description": "ISR retenido por el empleador durante el año."},
                "pagos_provisionales":            {"type": "number", "default": 0, "description": "Pagos provisionales enterados durante el año."},
                "subsidio_empleo_acreditado":     {"type": "number", "default": 0, "description": "Subsidio al empleo aplicado en el año."},
                "deducciones_medicas":            {"type": "number", "default": 0, "description": "Honorarios médicos, dentistas, psicólogos, nutriólogos con CFDI."},
                "gastos_hospitalarios":           {"type": "number", "default": 0, "description": "Gastos hospitalarios y medicamentos con CFDI."},
                "primas_gmm":                     {"type": "number", "default": 0, "description": "Primas de seguro de gastos médicos mayores."},
                "intereses_hipotecarios_reales":  {"type": "number", "default": 0, "description": "Intereses reales de crédito hipotecario para casa habitación."},
                "donativos":                      {"type": "number", "default": 0, "description": "Donativos a instituciones autorizadas (máx 7% del ingreso)."},
                "aportaciones_afore":             {"type": "number", "default": 0, "description": "Aportaciones voluntarias al AFORE/SAR (máx 10% ingreso o 5 UMA anuales)."},
                "colegiaturas":                   {"type": "number", "default": 0, "description": "Colegiaturas de preescolar a preparatoria."},
                "nivel_educativo":                {
                    "type": "string",
                    "enum": ["preescolar", "primaria", "secundaria", "preparatoria", "profesional_tecnico"],
                    "default": "preparatoria",
                    "description": "Nivel educativo para aplicar el límite correcto de colegiaturas.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "buscar_legislacion",
        "description": (
            "Busca artículos de leyes fiscales mexicanas vigentes: CFF, LISR, LIVA, LIEPS, LSS, LFT, RMF 2025, NIF. "
            "Usa RAG sobre base vectorial de legislación indexada. Retorna artículos relevantes con citas textuales."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta en lenguaje natural sobre la legislación."},
                "fuente": {
                    "type": "string",
                    "enum": ["CFF", "LISR", "LIVA", "LIEPS", "LSS", "LFT", "RMF", "NIF", "LINFONAVIT", "todas"],
                    "default": "todas",
                    "description": "Filtrar por ley específica o buscar en todas.",
                },
                "top_k": {"type": "integer", "default": 3, "minimum": 1, "maximum": 20, "description": "Número de artículos a retornar (máx 20)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "obtener_calendario_fiscal",
        "description": (
            "Retorna las obligaciones fiscales del mes para un régimen dado: "
            "pagos provisionales ISR, declaración IVA, DIOT, IMSS/INFONAVIT, declaración anual. "
            "Con fechas límite Art. 12 CFF."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mes": {"type": "integer", "minimum": 1, "maximum": 12, "description": "Mes del calendario (1-12)."},
                "anio": {"type": "integer", "default": 2025},
                "regimen": {
                    "type": "string",
                    "enum": ["sueldos", "honorarios", "arrendamiento", "actividades_empresariales", "resico_pf", "personas_morales", "resico_pm"],
                    "default": "personas_morales",
                },
            },
            "required": ["mes"],
        },
    },
]


# ── Ejecutores de tools ──────────────────────────────────────────────────────

async def execute_tool(tool_name: str, tool_input: dict) -> Any:
    if tool_name == "calcular_isr_personas_fisicas":
        return calcular_isr_pf(
            ingresos_mensuales=tool_input["ingresos_mensuales"],
            regimen=tool_input.get("regimen", "sueldos"),
            deducciones_mensuales=tool_input.get("deducciones_mensuales", 0.0),
            periodo=tool_input.get("periodo", "mensual"),
        )

    elif tool_name == "calcular_isr_personas_morales":
        return calcular_isr_pm(
            ingresos_acumulados=tool_input["ingresos_acumulados"],
            coeficiente_utilidad=tool_input.get("coeficiente_utilidad", 0.20),
            pagos_provisionales_previos=tool_input.get("pagos_provisionales_previos", 0.0),
            retenciones=tool_input.get("retenciones", 0.0),
            mes=tool_input.get("mes", 1),
            regimen=tool_input.get("regimen", "general"),
        )

    elif tool_name == "calcular_iva":
        return calcular_iva(
            ventas_16=tool_input.get("ventas_16", 0.0),
            ventas_0=tool_input.get("ventas_0", 0.0),
            ventas_exentas=tool_input.get("ventas_exentas", 0.0),
            compras_16_acreditables=tool_input.get("compras_16_acreditables", 0.0),
            compras_0_acreditables=tool_input.get("compras_0_acreditables", 0.0),
            compras_exentas=tool_input.get("compras_exentas", 0.0),
            saldo_favor_anterior=tool_input.get("saldo_favor_anterior", 0.0),
            periodo=tool_input.get("periodo", "mensual"),
        )

    elif tool_name == "calcular_cuotas_imss":
        return calcular_cuotas_imss(
            salario_diario_integrado=tool_input["salario_diario_integrado"],
            prima_riesgo_trabajo=tool_input.get("prima_riesgo_trabajo", 0.0054355),
        )

    elif tool_name == "calcular_nomina":
        return calcular_nomina(
            salario_mensual_bruto=tool_input["salario_mensual_bruto"],
            periodo=tool_input.get("periodo", "mensual"),
            otras_percepciones=tool_input.get("otras_percepciones", 0.0),
            vales_despensa=tool_input.get("vales_despensa", 0.0),
        )

    elif tool_name == "calcular_finiquito":
        return calcular_finiquito(
            salario_diario=tool_input["salario_diario"],
            dias_trabajados_anio=tool_input["dias_trabajados_anio"],
            anios_servicio=tool_input.get("anios_servicio", 0.0),
            tipo_separacion=tool_input.get("tipo_separacion", "renuncia"),
            vacaciones_gozadas=tool_input.get("vacaciones_gozadas", 0),
        )

    elif tool_name == "calcular_declaracion_anual_pf":
        result = calcular_declaracion_anual_pf(
            ingresos_sueldos=tool_input.get("ingresos_sueldos", 0.0),
            ingresos_honorarios=tool_input.get("ingresos_honorarios", 0.0),
            ingresos_arrendamiento=tool_input.get("ingresos_arrendamiento", 0.0),
            ingresos_actividad_empresarial=tool_input.get("ingresos_actividad_empresarial", 0.0),
            ingresos_intereses=tool_input.get("ingresos_intereses", 0.0),
            ingresos_dividendos=tool_input.get("ingresos_dividendos", 0.0),
            ingresos_otros=tool_input.get("ingresos_otros", 0.0),
            retenciones_sueldos=tool_input.get("retenciones_sueldos", 0.0),
            pagos_provisionales=tool_input.get("pagos_provisionales", 0.0),
            subsidio_empleo_acreditado=tool_input.get("subsidio_empleo_acreditado", 0.0),
            deducciones_medicas=tool_input.get("deducciones_medicas", 0.0),
            gastos_hospitalarios=tool_input.get("gastos_hospitalarios", 0.0),
            primas_gmm=tool_input.get("primas_gmm", 0.0),
            intereses_hipotecarios_reales=tool_input.get("intereses_hipotecarios_reales", 0.0),
            donativos=tool_input.get("donativos", 0.0),
            aportaciones_afore=tool_input.get("aportaciones_afore", 0.0),
            colegiaturas=tool_input.get("colegiaturas", 0.0),
            nivel_educativo=tool_input.get("nivel_educativo", "preparatoria"),
        )
        from dataclasses import asdict
        return asdict(result)

    elif tool_name == "buscar_legislacion":
        return await _buscar_legislacion(
            query=tool_input["query"],
            fuente=tool_input.get("fuente", "todas"),
            top_k=tool_input.get("top_k", 3),
        )

    elif tool_name == "obtener_calendario_fiscal":
        return _calendario_fiscal(
            mes=tool_input["mes"],
            anio=tool_input.get("anio", 2025),
            regimen=tool_input.get("regimen", "personas_morales"),
        )

    return {"error": f"Tool '{tool_name}' no encontrada."}


async def _buscar_legislacion(query: str, fuente: str = "todas", top_k: int = 3) -> dict:
    top_k = max(1, min(top_k, 20))
    """Búsqueda semántica en Qdrant sobre legislación fiscal mexicana."""
    try:
        from app.services.rag import search, collection_stats
        articulos = await search(query=query, fuente=fuente, top_k=top_k)
        if not articulos:
            return {
                "status": "sin_resultados",
                "mensaje": (
                    f"No se encontraron artículos relevantes para '{query}' en {fuente}. "
                    "Si la base de conocimiento no está inicializada, ejecuta: "
                    "python scripts/bootstrap_laws.py"
                ),
                "articulos": [],
            }
        return {
            "status": "ok",
            "query": query,
            "fuente_filtro": fuente,
            "articulos": articulos,
            "total": len(articulos),
        }
    except Exception as e:
        # Si Qdrant no está disponible, responde con aviso claro
        return {
            "status": "rag_no_disponible",
            "error": str(e),
            "mensaje": (
                "Base de conocimiento legal no disponible. "
                "Verifica que Qdrant esté corriendo (docker compose up -d qdrant) "
                "y que la colección esté inicializada (python scripts/bootstrap_laws.py)."
            ),
            "articulos": [],
        }


def _calendario_fiscal(mes: int, anio: int, regimen: str) -> dict:
    """Fechas límite de obligaciones fiscales del mes."""
    NOMBRES_MESES = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
    ]

    obligaciones = []
    dia_17 = f"{anio}-{mes:02d}-17"
    dia_31 = f"{anio}-{mes:02d}-31" if mes in [1, 3, 5, 7, 8, 10, 12] else f"{anio}-{mes:02d}-30"

    if regimen in ("personas_morales", "resico_pm", "actividades_empresariales", "honorarios", "arrendamiento", "resico_pf"):
        obligaciones.append({"obligacion": "Pago provisional ISR", "fecha_limite": dia_17, "forma": "Declaración mensual via SAT"})
        obligaciones.append({"obligacion": "Declaración IVA mensual", "fecha_limite": dia_17, "forma": "Declaración mensual via SAT"})

    if regimen in ("personas_morales",):
        obligaciones.append({"obligacion": "DIOT (Declaración Informativa Operaciones con Terceros)", "fecha_limite": dia_17, "fundamento": "Art. 32-B LIVA"})

    obligaciones.append({"obligacion": "Cuotas IMSS bimestral / mensual", "fecha_limite": f"{anio}-{mes:02d}-17", "fundamento": "Art. 39 LSS"})
    obligaciones.append({"obligacion": "INFONAVIT", "fecha_limite": f"{anio}-{mes:02d}-17", "fundamento": "Art. 35 Ley INFONAVIT"})

    if mes == 3:
        obligaciones.append({"obligacion": "Declaración anual ISR Personas Morales", "fecha_limite": f"{anio}-03-31", "fundamento": "Art. 76 LISR"})
    if mes == 4:
        obligaciones.append({"obligacion": "Declaración anual ISR Personas Físicas", "fecha_limite": f"{anio}-04-30", "fundamento": "Art. 150 LISR"})

    return {
        "mes": NOMBRES_MESES[mes],
        "anio": anio,
        "regimen": regimen,
        "obligaciones": obligaciones,
        "nota": "Verificar días hábiles. Si el día 17 cae en fin de semana o festivo, el vencimiento se prorroga al siguiente día hábil (Art. 12 CFF).",
    }
