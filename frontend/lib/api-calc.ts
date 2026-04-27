/**
 * Cliente API tipado para calculadoras fiscales v2
 * ==================================================
 * Uso:
 *   import { calcApi } from '@/lib/api-calc';
 *   const result = await calcApi.nomina({ salario_mensual_bruto: 20000, ... });
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V2 = `${API_BASE}/api/v2/calc`;

// ────────────────────────────────────────────────────────────────────────
// Tipos compartidos
// ────────────────────────────────────────────────────────────────────────

export interface DatosTrabajador {
  nombre_completo: string;
  rfc: string;
  curp?: string;
  nss: string;
  numero_empleado?: string;
  puesto?: string;
  departamento?: string;
  fecha_ingreso: string; // YYYY-MM-DD
  clabe?: string;
  banco?: string;
}

export interface DatosEmpleador {
  razon_social: string;
  rfc: string;
  registro_patronal?: string;
  domicilio_fiscal?: string;
  actividad_economica?: string;
  clase_riesgo?: "I" | "II" | "III" | "IV" | "V";
  prima_riesgo_trabajo?: number;
}

export interface DatosContribuyente {
  rfc: string;
  nombre_o_razon_social: string;
  tipo: "PF" | "PM";
  actividad_economica?: string;
  domicilio_fiscal?: string;
}

export interface ErrorValidacion {
  campo: string;
  motivo: string;
  valor_recibido?: string;
}

export interface RespuestaCalculo<T = Record<string, unknown>> {
  success: boolean;
  mensaje: string;
  fundamento_legal: string[];
  ejercicio_fiscal: number;
  datos: T;
  errores: ErrorValidacion[];
  advertencias: string[];
  metadata: Record<string, unknown>;
}

// ────────────────────────────────────────────────────────────────────────
// ISR PF
// ────────────────────────────────────────────────────────────────────────

export type RegimenISRPF =
  | "sueldos"
  | "honorarios"
  | "actividades_empresariales"
  | "arrendamiento"
  | "resico_pf";

export interface ISRPFRequest {
  contribuyente?: DatosContribuyente;
  ingresos_mensuales: number;
  regimen?: RegimenISRPF;
  deducciones_mensuales?: number;
  deducciones_personales_anuales?: number;
  periodo?: "mensual" | "anual";
  incluye_subsidio_empleo?: boolean;
  usar_deduccion_ciega_arrendamiento?: boolean;
  ingresos_acumulados_anio?: number;
}

// ────────────────────────────────────────────────────────────────────────
// ISR PM
// ────────────────────────────────────────────────────────────────────────

export interface ISRPMRequest {
  contribuyente?: DatosContribuyente;
  ingresos_acumulados: number;
  coeficiente_utilidad?: number;
  mes?: number;
  regimen?: "general" | "resico_pm";
  pagos_provisionales_previos?: number;
  retenciones_acreditables?: number;
  perdidas_fiscales_pendientes?: number;
  actividad?: string;
  es_calculo_anual?: boolean;
  deducciones_autorizadas_anual?: number;
  depreciaciones_anual?: number;
  ptu_pagada?: number;
}

// ────────────────────────────────────────────────────────────────────────
// IVA
// ────────────────────────────────────────────────────────────────────────

export interface IVARequest {
  contribuyente?: DatosContribuyente;
  ventas_16?: number;
  ventas_8_frontera?: number;
  ventas_0?: number;
  ventas_exentas?: number;
  compras_16_acreditables?: number;
  compras_8_acreditables?: number;
  compras_0?: number;
  compras_exentas?: number;
  iva_pagado_importaciones?: number;
  iva_retenido_a_terceros?: number;
  iva_retenido_por_terceros?: number;
  saldo_favor_anterior?: number;
  periodo?: "mensual" | "anual";
  aplicar_frontera?: boolean;
}

// ────────────────────────────────────────────────────────────────────────
// IEPS
// ────────────────────────────────────────────────────────────────────────

export interface IEPSCategoria {
  clave: string;
  nombre: string;
  fundamento: string;
  tipo: "tasa" | "cuota_litro";
  tasa_pct?: number;
  cuota_litro?: number;
  cuota_adicional_cigarro?: number;
}

export interface IEPSRequest {
  categoria: string;
  precio_enajenacion: number;
  cantidad_litros?: number;
  cantidad_cigarros?: number;
  incluir_iva?: boolean;
  es_acreditable?: boolean;
}

// ────────────────────────────────────────────────────────────────────────
// IMSS
// ────────────────────────────────────────────────────────────────────────

export interface IMSSRequest {
  salario_diario_integrado: number;
  salario_diario_base?: number;
  prima_riesgo_trabajo?: number;
  clase_riesgo?: "I" | "II" | "III" | "IV" | "V";
  zona_norte?: boolean;
}

export interface SDIRequest {
  salario_diario_base: number;
  aguinaldo_dias?: number;
  prima_vacacional_pct?: number;
  dias_vacaciones?: number;
  prestaciones_adicionales_anuales?: number;
}

// ────────────────────────────────────────────────────────────────────────
// Nómina
// ────────────────────────────────────────────────────────────────────────

export type PeriodoPago =
  | "diario" | "semanal" | "catorcenal"
  | "quincenal" | "decenal" | "mensual";

export interface NominaRequest {
  trabajador?: DatosTrabajador;
  empleador?: DatosEmpleador;
  salario_mensual_bruto: number;
  periodo?: PeriodoPago;
  fecha_inicio?: string;
  fecha_fin?: string;
  fecha_pago?: string;
  anios_antiguedad?: number;
  otras_percepciones_gravadas?: number;
  otras_percepciones_exentas?: number;
  vales_despensa?: number;
  horas_extras_dobles?: number;
  horas_extras_triples?: number;
  fondo_ahorro_patron?: number;
  ptu?: number;
  bono_productividad?: number;
  pension_alimenticia_pct?: number;
  fonacot_descuento?: number;
  prestamo_patron?: number;
  infonavit_descuento_credito?: number;
  otras_deducciones?: number;
  prima_riesgo_trabajo?: number;
  clase_riesgo?: "I" | "II" | "III" | "IV" | "V";
}

// ────────────────────────────────────────────────────────────────────────
// Finiquito
// ────────────────────────────────────────────────────────────────────────

export type TipoSeparacion =
  | "renuncia" | "despido_justificado" | "despido_injustificado"
  | "mutuo_acuerdo" | "muerte" | "jubilacion"
  | "incapacidad_total" | "termino_contrato";

export interface FiniquitoRequest {
  trabajador?: DatosTrabajador;
  empleador?: DatosEmpleador;
  salario_diario: number;
  fecha_ingreso?: string;
  fecha_separacion?: string;
  anios_servicio?: number;
  dias_trabajados_anio?: number;
  tipo_separacion?: TipoSeparacion;
  vacaciones_gozadas?: number;
  dias_pendientes_pago?: number;
  aguinaldo_ya_pagado?: number;
  ptu_pendiente?: number;
  bono_pendiente?: number;
  meses_salarios_caidos?: number;
}

// ────────────────────────────────────────────────────────────────────────
// Helper de fetch tipado
// ────────────────────────────────────────────────────────────────────────

async function postJson<T = Record<string, unknown>>(
  endpoint: string,
  body: Record<string, unknown>
): Promise<RespuestaCalculo<T>> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const res = await fetch(`${API_V2}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

async function getJson<T>(endpoint: string): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const res = await fetch(`${API_V2}${endpoint}`, {
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ────────────────────────────────────────────────────────────────────────
// API tipada
// ────────────────────────────────────────────────────────────────────────

export const calcApi = {
  isrPf: (req: ISRPFRequest) => postJson("/isr-pf", req),
  isrPm: (req: ISRPMRequest) => postJson("/isr-pm", req),
  iva: (req: IVARequest) => postJson("/iva", req),
  ieps: (req: IEPSRequest) => postJson("/ieps", req),
  iepsCategorias: () => getJson<{ success: boolean; categorias: IEPSCategoria[] }>("/ieps/categorias"),
  imss: (req: IMSSRequest) => postJson("/imss", req),
  sdi: (req: SDIRequest) => postJson("/imss/sdi", req),
  nomina: (req: NominaRequest) => postJson("/nomina", req),
  finiquito: (req: FiniquitoRequest) => postJson("/finiquito", req),
  health: () => getJson<{ status: string; ejercicio_fiscal: number; version: string }>("/health"),
};

// Helper para formato de moneda mexicana
export const MXN = (n: number) =>
  new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
  }).format(n);

// Helper para porcentajes
export const PCT = (n: number, decimals = 2) =>
  `${(n * 100).toFixed(decimals)}%`;
