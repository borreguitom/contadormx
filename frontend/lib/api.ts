const BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg?.replace(/^Value error, /, "") ?? "Error").join(". ")
      : (typeof detail === "string" ? detail : `Error ${res.status}`);
    throw new Error(message);
  }
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export const api = {
  auth: {
    login: (email: string, password: string) =>
      request<{ access_token: string }>("/api/auth/login", {
        method: "POST",
        // OAuth2PasswordRequestForm espera form-urlencoded
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: email, password }),
      }),
    register: (email: string, password: string, nombre: string) =>
      request<{ access_token: string }>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, nombre }),
      }),
    forgotPassword: (email: string) =>
      request<{ ok: boolean }>("/api/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      }),
    resetPassword: (token: string, password: string) =>
      request<{ access_token: string }>("/api/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      }),
    logout: () =>
      request<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
  },

  // ── Chat ─────────────────────────────────────────────────────────────────
  chat: {
    message: (
      messages: { role: string; content: string }[],
      opts?: { use_web_search?: boolean; client_context?: string },
      conversationId?: number,
    ) =>
      request<{ content: string; tools_used: string[]; input_tokens: number; output_tokens: number; conversation_id: number }>(
        "/api/chat/message",
        { method: "POST", body: JSON.stringify({ messages, ...opts, conversation_id: conversationId }) }
      ),
  },

  // ── Clientes ──────────────────────────────────────────────────────────────
  clients: {
    list: () => request<Cliente[]>("/api/clients"),
    get: (id: number) => request<Cliente>(`/api/clients/${id}`),
    create: (data: ClienteCreate) =>
      request<Cliente>("/api/clients", { method: "POST", body: JSON.stringify(data) }),
  },

  // ── Calculadoras ──────────────────────────────────────────────────────────
  calc: {
    isrPF: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/isr/personas-fisicas", { method: "POST", body: JSON.stringify(body) }),
    isrPM: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/isr/personas-morales", { method: "POST", body: JSON.stringify(body) }),
    iva: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/iva", { method: "POST", body: JSON.stringify(body) }),
    imss: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/imss", { method: "POST", body: JSON.stringify(body) }),
    nomina: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/nomina", { method: "POST", body: JSON.stringify(body) }),
    finiquito: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/finiquito", { method: "POST", body: JSON.stringify(body) }),
    declaracionAnualPF: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/declaracion-anual/pf", { method: "POST", body: JSON.stringify(body) }),
    iepsCategorias: () =>
      request<Record<string, unknown>>("/api/calc/ieps/categorias"),
    ieps: (body: Record<string, unknown>) =>
      request<Record<string, unknown>>("/api/calc/ieps", { method: "POST", body: JSON.stringify(body) }),
  },

  // ── CFDI ─────────────────────────────────────────────────────────────────
  cfdi: {
    validate: (xml_content: string) =>
      request<CFDIResult>("/api/cfdi/validate", { method: "POST", body: JSON.stringify({ xml_content }) }),
  },

  // ── Laws ──────────────────────────────────────────────────────────────────
  laws: {
    stats: () => request<Record<string, unknown>>("/api/laws/stats"),
    recentUpdates: () => request<LawUpdate[]>("/api/laws/recent-updates"),
    search: (query: string, fuente = "todas", top_k = 5) =>
      request<{ articulos: Articulo[] }>("/api/laws/search", {
        method: "POST",
        body: JSON.stringify({ query, fuente, top_k }),
      }),
    inpc: () => request<Record<string, unknown>>("/api/laws/inpc"),
  },

  // ── Chat conversations ────────────────────────────────────────────────────
  chatHistory: {
    list: () => request<ConversationSummary[]>("/api/chat/conversations"),
    get: (id: number) => request<ConversationDetail>(`/api/chat/conversations/${id}`),
  },

  // ── Dashboard ─────────────────────────────────────────────────────────────
  dashboard: {
    stats: () => request<DashboardStats>("/api/dashboard/stats"),
  },

  // ── Documentos ────────────────────────────────────────────────────────────
  documentos: {
    upload: (clienteId: number, files: File[]) => {
      const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      return fetch(`${BASE}/api/documentos/${clienteId}/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      }).then(async (r) => {
        if (!r.ok) {
          const b = await r.json().catch(() => ({}));
          throw new Error(b.detail ?? `HTTP ${r.status}`);
        }
        return r.json() as Promise<UploadResult>;
      });
    },
    list: (clienteId: number) =>
      request<DocumentoItem[]>(`/api/documentos/${clienteId}`),
    resumen: (clienteId: number) =>
      request<ResumenFiscal>(`/api/documentos/${clienteId}/resumen`),
    delete: (docId: number) =>
      request<{ ok: boolean }>(`/api/documentos/${docId}/documento`, { method: "DELETE" }),
    exportarExcel: (clienteId: number): Promise<Blob> => {
      const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;
      return fetch(`${BASE}/api/documentos/${clienteId}/exportar-excel`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.blob();
      });
    },
    diot: (clienteId: number) =>
      request<DiotResult>(`/api/documentos/${clienteId}/diot`),
    diotTxt: (clienteId: number): Promise<Blob> => {
      const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;
      return fetch(`${BASE}/api/documentos/${clienteId}/diot?formato=txt`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.blob();
      });
    },
  },

  // ── SAT ───────────────────────────────────────────────────────────────────
  sat: {
    listCredentials: () => request<SatCredential[]>("/api/sat/credentials"),
    deleteCredential: (id: number) =>
      request<void>(`/api/sat/credentials/${id}`, { method: "DELETE" }),
    requestDownload: (body: SatDownloadRequest) =>
      request<{ job_id: number; status: string }>("/api/sat/download", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    listJobs: () => request<SatJob[]>("/api/sat/jobs"),
    getJob: (id: number) => request<SatJob>(`/api/sat/jobs/${id}`),
    listCfdis: (params?: { tipo?: string; rfc_contraparte?: string; credential_id?: number; limit?: number; offset?: number }) => {
      const q = new URLSearchParams();
      if (params?.tipo) q.set("tipo", params.tipo);
      if (params?.rfc_contraparte) q.set("rfc_contraparte", params.rfc_contraparte);
      if (params?.credential_id) q.set("credential_id", String(params.credential_id));
      if (params?.limit) q.set("limit", String(params.limit));
      if (params?.offset) q.set("offset", String(params.offset));
      return request<{ total: number; items: SatCfdi[] }>(`/api/sat/cfdis?${q}`);
    },
    uploadCredential: (form: FormData): Promise<SatCredential> => {
      const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;
      return fetch(`${BASE}/api/sat/credentials`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      }).then(async (r) => {
        if (!r.ok) {
          const b = await r.json().catch(() => ({}));
          throw new Error(b.detail ?? `HTTP ${r.status}`);
        }
        return r.json();
      });
    },
  },

  // ── Empleados / Nómina ────────────────────────────────────────────────────
  empleados: {
    list: (clienteId: number) =>
      request<Empleado[]>(`/api/empleados/${clienteId}`),
    create: (clienteId: number, data: EmpleadoCreate) =>
      request<Empleado>(`/api/empleados/${clienteId}`, { method: "POST", body: JSON.stringify(data) }),
    update: (clienteId: number, empId: number, data: Partial<EmpleadoCreate>) =>
      request<Empleado>(`/api/empleados/${clienteId}/${empId}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (clienteId: number, empId: number) =>
      request<{ ok: boolean }>(`/api/empleados/${clienteId}/${empId}`, { method: "DELETE" }),
    runNomina: (clienteId: number, body: NominaRunRequest) =>
      request<NominaResult>(`/api/empleados/${clienteId}/nomina`, { method: "POST", body: JSON.stringify(body) }),
    downloadTemplate: (): Promise<Blob> => {
      const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;
      return fetch(`${BASE}/api/empleados/template`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.blob();
      });
    },
    importExcel: (clienteId: number, file: File): Promise<{ importados: number; errores: string[] }> => {
      const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;
      const form = new FormData();
      form.append("file", file);
      return fetch(`${BASE}/api/empleados/${clienteId}/import`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      }).then(async (r) => {
        if (!r.ok) { const b = await r.json().catch(() => ({})); throw new Error(b.detail ?? `HTTP ${r.status}`); }
        return r.json();
      });
    },
    exportNominaExcel: (clienteId: number, params: NominaRunRequest): Promise<Blob> => {
      const token = typeof window !== "undefined" ? localStorage.getItem("cmx_token") : null;
      const q = new URLSearchParams({
        periodo: params.periodo,
        fecha_inicio: params.fecha_inicio,
        fecha_fin: params.fecha_fin,
      });
      return fetch(`${BASE}/api/empleados/${clienteId}/nomina/excel?${q}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }).then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.blob();
      });
    },
  },

  // ── Billing ───────────────────────────────────────────────────────────────
  billing: {
    status: () => request<BillingStatus>("/api/billing/status"),
    plans: () => request<{ plans: BillingPlan[] }>("/api/billing/plans"),
    checkout: (plan: string) =>
      request<{ checkout_url: string }>("/api/billing/checkout", {
        method: "POST",
        body: JSON.stringify({ plan }),
      }),
    portal: () =>
      request<{ portal_url: string }>("/api/billing/portal", { method: "POST" }),
  },
};

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Cliente {
  id: number;
  rfc: string;
  razon_social: string;
  regimen_fiscal: string | null;
  actividad: string | null;
  correo: string | null;
}

export interface ClienteCreate {
  rfc: string;
  razon_social: string;
  regimen_fiscal?: string;
  actividad?: string;
  correo?: string;
  telefono?: string;
}

export interface CFDIResult {
  valido: boolean;
  uuid: string | null;
  emisor_rfc: string | null;
  receptor_rfc: string | null;
  total: number | null;
  fecha: string | null;
  tipo_comprobante: string | null;
  version: string | null;
  errores: string[];
  advertencias: string[];
}

export interface LawUpdate {
  id: number;
  ley: string;
  tipo: string;
  titulo: string;
  url: string;
  fecha_publicacion: string | null;
  indexado: boolean;
  created_at: string;
}

export interface Articulo {
  ley: string;
  articulo: string;
  titulo: string;
  texto: string;
  fuente_url: string;
  cita: string;
  score: number;
}

export interface DashboardStats {
  user_nombre: string;
  plan: string;
  queries_used: number;
  queries_limit: number;
  total_clientes: number;
  clientes_limit: number;
  conversaciones_recientes: { id: number; titulo: string; fecha: string }[];
  proximas_obligaciones: { fecha: string; dia: number; mes: string; nombre: string; tipo: string }[];
}

export interface BillingStatus {
  plan: string;
  queries_used: number;
  queries_limit: number;
  clientes_limit: number;
  stripe_customer_id: string | null;
}

export interface BillingPlan {
  id: string;
  nombre: string;
  precio_mxn: number;
  queries: number;
  clientes: number;
}

export interface ConversationSummary {
  id: number;
  title: string;
  created_at: string;
}

export interface ConversationDetail {
  id: number;
  title: string;
  messages: { role: string; content: string; tools_used: string[] }[];
}

export interface DocumentoItem {
  id: number;
  nombre_archivo: string;
  tipo_archivo: string;
  uuid_cfdi: string | null;
  tipo_comprobante: string | null;
  fecha_emision: string | null;
  emisor_rfc: string | null;
  emisor_nombre: string | null;
  receptor_rfc: string | null;
  total: number | null;
  iva_trasladado: number | null;
  moneda: string | null;
  estado: string;
  error_msg: string | null;
  created_at: string;
}

export interface UploadResult {
  procesados: number;
  resultados: { archivo: string; estado: string; doc_id?: number; uuid_cfdi?: string | null; total?: number | null; detalle?: string }[];
}

export interface DiotProveedor {
  rfc: string;
  nombre: string;
  tipo_tercero: string;
  tipo_operacion: string;
  monto_operaciones: number;
  iva_16_pagado: number;
  iva_retenido: number;
  cantidad_facturas: number;
}

export interface DiotResult {
  periodo: string;
  total_proveedores: number;
  total_operaciones: number;
  proveedores: DiotProveedor[];
}

export interface Empleado {
  id: number;
  cliente_id: number;
  nombre_completo: string;
  rfc: string | null;
  curp: string | null;
  nss: string | null;
  fecha_nacimiento: string | null;
  fecha_alta: string;
  fecha_baja: string | null;
  tipo_contrato: string;
  periodicidad_pago: string;
  salario_diario: number;
  departamento: string | null;
  puesto: string | null;
  banco: string | null;
  clabe: string | null;
  is_active: boolean;
}

export interface EmpleadoCreate {
  nombre_completo: string;
  rfc?: string;
  curp?: string;
  nss?: string;
  fecha_nacimiento?: string;
  fecha_alta: string;
  tipo_contrato?: string;
  periodicidad_pago?: string;
  salario_diario: number;
  departamento?: string;
  puesto?: string;
  banco?: string;
  clabe?: string;
}

export interface NominaRunRequest {
  periodo: string;
  fecha_inicio: string;
  fecha_fin: string;
  otras_percepciones_global?: number;
  vales_despensa_global?: number;
}

export interface NominaEmpleadoResult {
  id: number;
  nombre_completo: string;
  rfc: string | null;
  nss: string | null;
  puesto: string | null;
  departamento: string | null;
  salario_diario: number;
  salario_mensual: number;
  percepciones: Record<string, number>;
  deducciones: Record<string, number>;
  neto_a_pagar: number;
  costo_empresa: Record<string, number>;
}

export interface NominaResult {
  periodo: string;
  fecha_inicio: string;
  fecha_fin: string;
  total_empleados: number;
  totales: {
    total_percepciones: number;
    total_deducciones: number;
    total_neto: number;
    costo_total_empresa: number;
    total_isr: number;
    total_imss_obrero: number;
    total_imss_patronal: number;
    total_infonavit: number;
  };
  empleados: NominaEmpleadoResult[];
}

export interface SatCredential {
  id: number;
  rfc: string;
  alias: string | null;
  valid_to: string | null;
  created_at: string;
}

export interface SatJob {
  id: number;
  rfc: string;
  status: string;
  date_from: string;
  date_to: string;
  tipo_comprobante: string | null;
  tipo_solicitud: string;
  total_cfdi: number;
  packages_total: number;
  packages_downloaded: number;
  progress: number;
  error_msg: string | null;
  created_at: string;
}

export interface SatCfdi {
  id: number;
  uuid: string;
  rfc_emisor: string | null;
  nombre_emisor: string | null;
  rfc_receptor: string | null;
  nombre_receptor: string | null;
  total: number | null;
  fecha_emision: string | null;
  tipo_comprobante: string | null;
  metodo_pago: string | null;
  moneda: string | null;
  estatus: string | null;
}

export interface SatDownloadRequest {
  credential_id: number;
  date_from: string;
  date_to: string;
  tipo_comprobante?: "I" | "E" | "T" | "N" | "P";
  tipo_solicitud?: "CFDI" | "Metadata";
}

export interface ResumenFiscal {
  total_documentos: number;
  ingresos: { subtotal: number; descuento: number; iva_trasladado: number; iva_retenido: number; isr_retenido: number; total: number; cantidad: number };
  egresos: { subtotal: number; descuento: number; iva_trasladado: number; iva_retenido: number; isr_retenido: number; total: number; cantidad: number };
  iva_neto_a_pagar: number;
  isr_retenido_total: number;
  utilidad_bruta: number;
}
