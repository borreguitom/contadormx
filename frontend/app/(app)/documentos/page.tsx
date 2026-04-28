"use client";
import { useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TEMPLATES = [
  {
    id: "carta_sat",
    icon: "📨",
    nombre: "Carta de respuesta al SAT",
    descripcion: "Responde oficios, requerimientos y notificaciones del SAT",
    campos: [
      { key: "emisor_nombre",    label: "Nombre / Razón Social", type: "text", placeholder: "Juan García López" },
      { key: "emisor_rfc",       label: "RFC del contribuyente", type: "text", placeholder: "GALJ850101ABC", mono: true },
      { key: "emisor_domicilio", label: "Domicilio fiscal",      type: "text", placeholder: "Av. Reforma 123, CDMX" },
      { key: "numero_oficio",    label: "Número de oficio SAT",  type: "text", placeholder: "500-05-2026-XXXXX" },
      { key: "fecha_oficio",     label: "Fecha del oficio",      type: "text", placeholder: "15 de abril de 2026" },
      { key: "asunto",           label: "Asunto",                type: "text", placeholder: "Respuesta a requerimiento de información" },
      { key: "lugar",            label: "Lugar",                 type: "text", placeholder: "Ciudad de México" },
      { key: "cuerpo",           label: "Cuerpo de la carta",    type: "textarea", placeholder: "En respuesta al oficio de referencia, manifiesto lo siguiente…" },
    ],
  },
  {
    id: "cedula_isr",
    icon: "📊",
    nombre: "Cédula ISR Anual PF",
    descripcion: "Hoja de trabajo para declaración anual de personas físicas",
    campos: [
      { key: "contribuyente_nombre",   label: "Nombre completo",          type: "text", placeholder: "María Sánchez Ruiz" },
      { key: "contribuyente_rfc",      label: "RFC",                      type: "text", placeholder: "SARM750312JK5", mono: true },
      { key: "regimen",                label: "Régimen fiscal",           type: "text", placeholder: "Sueldos y salarios" },
      { key: "ejercicio",              label: "Ejercicio fiscal",         type: "text", placeholder: "2026" },
      { key: "ingresos_totales",       label: "Ingresos acumulables ($)", type: "number", placeholder: "0.00" },
      { key: "deducciones_autorizadas",label: "Deducciones autorizadas ($)",type: "number", placeholder: "0.00" },
      { key: "deducciones_personales", label: "Deducciones personales ($)",type: "number", placeholder: "0.00" },
      { key: "pagos_provisionales",    label: "Pagos provisionales ($)",  type: "number", placeholder: "0.00" },
      { key: "retenciones",            label: "Retenciones ISR ($)",      type: "number", placeholder: "0.00" },
    ],
  },
  {
    id: "carta_encargo",
    icon: "🤝",
    nombre: "Carta encargo profesional",
    descripcion: "Contrato de servicios contables entre contador y cliente",
    campos: [
      { key: "cliente_nombre",       label: "Nombre del cliente",         type: "text", placeholder: "Empresa XYZ SA de CV" },
      { key: "cliente_rfc",          label: "RFC del cliente",            type: "text", placeholder: "EXY010101ABC", mono: true },
      { key: "contador_nombre",      label: "Nombre del contador",        type: "text", placeholder: "C.P. Roberto Pérez" },
      { key: "contador_rfc",         label: "RFC del contador",           type: "text", placeholder: "PERR800101XYZ", mono: true },
      { key: "contador_cedula",      label: "Cédula profesional",         type: "text", placeholder: "1234567" },
      { key: "servicios",            label: "Servicios a prestar",        type: "textarea", placeholder: "1. Contabilidad mensual\n2. Declaraciones provisionales ISR/IVA\n3. Nómina…" },
      { key: "honorarios_mensuales", label: "Honorarios mensuales (sin IVA)", type: "number", placeholder: "5000" },
      { key: "vigencia_inicio",      label: "Vigencia inicio",            type: "text", placeholder: "1 de enero de 2026" },
      { key: "vigencia_fin",         label: "Vigencia fin",               type: "text", placeholder: "31 de diciembre de 2026" },
      { key: "lugar",                label: "Lugar",                      type: "text", placeholder: "Ciudad de México" },
    ],
  },
  {
    id: "escrito_respuesta",
    icon: "⚖️",
    nombre: "Escrito respuesta a requerimiento",
    descripcion: "Escrito formal con argumentos y documentación soporte",
    campos: [
      { key: "contribuyente_nombre",   label: "Nombre / Razón Social",   type: "text", placeholder: "Juan García López" },
      { key: "contribuyente_rfc",      label: "RFC",                     type: "text", placeholder: "GALJ850101ABC", mono: true },
      { key: "numero_requerimiento",   label: "Número de requerimiento", type: "text", placeholder: "300-SAT-2026-XXXXX" },
      { key: "fecha_requerimiento",    label: "Fecha del requerimiento", type: "text", placeholder: "10 de abril de 2026" },
      { key: "autoridad",              label: "Autoridad emisora",       type: "text", placeholder: "ADR Oriente del DF" },
      { key: "respuesta",              label: "Respuesta y argumentos",  type: "textarea", placeholder: "En respuesta al requerimiento en cita, manifiesto bajo protesta de decir verdad…" },
      { key: "documentacion_adjunta",  label: "Documentación que se acompaña", type: "textarea", placeholder: "1. Copia de CFDI…\n2. Estado de cuenta…" },
      { key: "lugar",                  label: "Lugar",                   type: "text", placeholder: "Ciudad de México" },
    ],
  },
];

interface Campo {
  key: string;
  label: string;
  type: string;
  placeholder?: string;
  mono?: boolean;
}

function FormField({ campo, value, onChange }: { campo: Campo; value: string; onChange: (v: string) => void }) {
  const base = "w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-green-50 focus:outline-none focus:border-green-500/40 placeholder:text-gray-600";
  if (campo.type === "textarea") {
    return (
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={campo.placeholder}
        rows={4}
        className={`${base} resize-none ${campo.mono ? "font-mono" : ""}`}
      />
    );
  }
  return (
    <input
      type={campo.type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={campo.placeholder}
      className={`${base} ${campo.mono ? "font-mono" : ""}`}
    />
  );
}

export default function DocumentosPage() {
  const [selected, setSelected] = useState<string | null>(null);
  const [formData, setFormData] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const template = TEMPLATES.find(t => t.id === selected);

  const selectTemplate = (id: string) => {
    setSelected(id);
    setFormData({});
    setError("");
  };

  const generate = async () => {
    if (!selected) return;
    setLoading(true);
    setError("");

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
      const res = await fetch(`${API_BASE}/api/docs/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ tipo: selected, datos: formData }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? "Error al generar");
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selected}_${new Date().toISOString().slice(0, 10)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al generar el PDF");
    } finally {
      setLoading(false);
    }
  };

  const allFilled = template
    ? template.campos.filter(c => c.type !== "textarea").every(c => (formData[c.key] ?? "").trim())
    : false;

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-green-100">Generador de Documentos</h1>
          <p className="text-sm text-gray-500 mt-0.5">Cartas SAT, cédulas ISR, contratos y escritos — PDF en segundos</p>
        </div>

        {/* Template selector */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          {TEMPLATES.map(t => (
            <button key={t.id} onClick={() => selectTemplate(t.id)}
              className={`text-left p-4 rounded-2xl border transition-all ${
                selected === t.id
                  ? "bg-green-500/12 border-green-500/35 text-green-200"
                  : "bg-white/3 border-white/8 text-gray-400 hover:bg-white/5 hover:text-green-200 hover:border-white/15"
              }`}>
              <div className="text-2xl mb-2">{t.icon}</div>
              <p className="text-xs font-semibold leading-snug">{t.nombre}</p>
              <p className="text-[10px] text-gray-600 mt-1 leading-snug">{t.descripcion}</p>
            </button>
          ))}
        </div>

        {/* Form */}
        {template && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xl">{template.icon}</span>
                <h2 className="text-sm font-semibold text-green-200">{template.nombre}</h2>
              </div>

              <div className="space-y-3">
                {template.campos.map(campo => (
                  <div key={campo.key}>
                    <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">
                      {campo.label}
                    </label>
                    <FormField
                      campo={campo}
                      value={formData[campo.key] ?? ""}
                      onChange={v => setFormData(prev => ({ ...prev, [campo.key]: v }))}
                    />
                  </div>
                ))}

                {error && (
                  <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                    {error}
                  </p>
                )}

                <button
                  onClick={generate}
                  disabled={loading || !allFilled}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-50 mt-1"
                >
                  {loading ? "Generando PDF…" : "⬇ Generar y descargar PDF"}
                </button>
              </div>
            </div>

            {/* Preview info */}
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5 flex flex-col items-center justify-center text-center">
              <div className="text-5xl mb-4">{template.icon}</div>
              <h3 className="text-sm font-semibold text-green-200 mb-2">{template.nombre}</h3>
              <p className="text-xs text-gray-500 max-w-xs mb-6">{template.descripcion}</p>
              <div className="space-y-2 w-full text-left">
                <p className="text-[10px] text-gray-600 uppercase tracking-widest">El PDF incluye</p>
                {selected === "carta_sat" && (
                  <>
                    <p className="text-xs text-gray-400">• Encabezado formal con datos del contribuyente</p>
                    <p className="text-xs text-gray-400">• Referencia al oficio SAT y número de expediente</p>
                    <p className="text-xs text-gray-400">• Cuerpo de respuesta redactado por ti</p>
                    <p className="text-xs text-gray-400">• Espacio para firma y sello</p>
                  </>
                )}
                {selected === "cedula_isr" && (
                  <>
                    <p className="text-xs text-gray-400">• Tabla de determinación con base gravable</p>
                    <p className="text-xs text-gray-400">• Crédito por pagos provisionales y retenciones</p>
                    <p className="text-xs text-gray-400">• Referencia legal Arts. 150–152 LISR</p>
                    <p className="text-xs text-gray-400">• Espacios para firma de contribuyente y contador</p>
                  </>
                )}
                {selected === "carta_encargo" && (
                  <>
                    <p className="text-xs text-gray-400">• Identificación de ambas partes con RFC</p>
                    <p className="text-xs text-gray-400">• Alcance detallado de servicios</p>
                    <p className="text-xs text-gray-400">• Tabla de honorarios + IVA</p>
                    <p className="text-xs text-gray-400">• Cláusulas de confidencialidad y terminación</p>
                  </>
                )}
                {selected === "escrito_respuesta" && (
                  <>
                    <p className="text-xs text-gray-400">• Encabezado con datos de identificación</p>
                    <p className="text-xs text-gray-400">• Antecedentes del requerimiento</p>
                    <p className="text-xs text-gray-400">• Fundamento legal (Art. 33-A CFF)</p>
                    <p className="text-xs text-gray-400">• Lista de documentación adjunta</p>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {!selected && (
          <div className="rounded-2xl border border-white/8 bg-white/3 p-12 text-center">
            <div className="text-4xl mb-3">📄</div>
            <p className="text-sm text-gray-500">Selecciona un tipo de documento para comenzar</p>
          </div>
        )}
      </div>
    </div>
  );
}
