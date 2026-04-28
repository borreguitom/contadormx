"use client";
import { useState } from "react";

const MESES = [
  "Enero","Febrero","Marzo","Abril","Mayo","Junio",
  "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre",
];

type Regimen = "todos" | "general_pm" | "pf_actividad" | "sueldos" | "resico" | "con_empleados";

const REGIMENES: { id: Regimen; label: string }[] = [
  { id: "todos",         label: "Todos" },
  { id: "general_pm",   label: "PM Régimen General" },
  { id: "resico",       label: "RESICO PF/PM" },
  { id: "pf_actividad", label: "PF Honorarios/Act. Emp." },
  { id: "sueldos",      label: "PF Sueldos" },
  { id: "con_empleados",label: "Con empleados" },
];

interface Obligacion {
  dia: number;
  nombre: string;
  ley: string;
  regimenes: Regimen[];
  tipo: "pago" | "declaracion" | "laboral" | "informativa";
  urgente?: boolean;
}

// Obligaciones mensuales (se repiten todos los meses salvo excepciones)
const MENSUALES: Obligacion[] = [
  {
    dia: 17,
    nombre: "ISR Pago Provisional PM",
    ley: "Art. 14 LISR",
    regimenes: ["general_pm"],
    tipo: "pago",
  },
  {
    dia: 17,
    nombre: "ISR Pago Provisional PF (Hon./Act. Emp.)",
    ley: "Art. 106 LISR",
    regimenes: ["pf_actividad"],
    tipo: "pago",
  },
  {
    dia: 17,
    nombre: "RESICO — Pago Mensual",
    ley: "Arts. 113-E / 196 LISR",
    regimenes: ["resico"],
    tipo: "pago",
  },
  {
    dia: 17,
    nombre: "IVA Declaración Mensual",
    ley: "Art. 5-D LIVA",
    regimenes: ["general_pm", "pf_actividad", "resico"],
    tipo: "declaracion",
  },
  {
    dia: 17,
    nombre: "DIOT",
    ley: "Art. 32 fracc. VIII LIVA",
    regimenes: ["general_pm", "pf_actividad"],
    tipo: "informativa",
  },
  {
    dia: 17,
    nombre: "Retenciones ISR nómina — entero",
    ley: "Art. 96 LISR",
    regimenes: ["con_empleados"],
    tipo: "pago",
  },
  {
    dia: 17,
    nombre: "Cuotas IMSS patronales",
    ley: "Art. 39 LSS",
    regimenes: ["con_empleados"],
    tipo: "pago",
  },
  {
    dia: 17,
    nombre: "Aportaciones INFONAVIT",
    ley: "Art. 29 Ley INFONAVIT",
    regimenes: ["con_empleados"],
    tipo: "pago",
  },
];

// Obligaciones especiales por mes (mes = 1-indexed)
const ESPECIALES: (Obligacion & { mes: number; soloMes?: true })[] = [
  {
    mes: 1, dia: 31,
    nombre: "CFDI Nómina — cierre enero",
    ley: "Art. 99 LISR",
    regimenes: ["con_empleados"],
    tipo: "informativa",
  },
  {
    mes: 2, dia: 28,
    nombre: "Constancias de retenciones (trabajadores)",
    ley: "Art. 99 fracc. III LISR",
    regimenes: ["con_empleados"],
    tipo: "informativa",
    urgente: true,
  },
  {
    mes: 3, dia: 31,
    nombre: "ISR Anual Personas Morales 2024",
    ley: "Art. 9 LISR",
    regimenes: ["general_pm"],
    tipo: "declaracion",
    urgente: true,
  },
  {
    mes: 4, dia: 30,
    nombre: "ISR Anual Personas Físicas 2024",
    ley: "Art. 150 LISR",
    regimenes: ["pf_actividad", "sueldos"],
    tipo: "declaracion",
    urgente: true,
  },
  {
    mes: 5, dia: 15,
    nombre: "PTU — plazo máximo pago (PM)",
    ley: "Art. 122 LFT",
    regimenes: ["general_pm", "con_empleados"],
    tipo: "laboral",
    urgente: true,
  },
  {
    mes: 6, dia: 29,
    nombre: "PTU — plazo máximo pago (PF)",
    ley: "Art. 122 LFT",
    regimenes: ["pf_actividad", "con_empleados"],
    tipo: "laboral",
    urgente: true,
  },
  {
    mes: 7, dia: 15,
    nombre: "Prima vacacional — primera quincena julio",
    ley: "Art. 80 LFT",
    regimenes: ["con_empleados"],
    tipo: "laboral",
  },
  {
    mes: 9, dia: 30,
    nombre: "Actualización de datos SAT (si hubo cambios)",
    ley: "Art. 27 CFF",
    regimenes: ["todos"],
    tipo: "informativa",
  },
  {
    mes: 11, dia: 30,
    nombre: "Aviso contadores públicos registrados (SIPRED)",
    ley: "Art. 52 CFF",
    regimenes: ["general_pm"],
    tipo: "informativa",
  },
  {
    mes: 12, dia: 20,
    nombre: "Aguinaldo — pago máximo 20 de diciembre",
    ley: "Art. 87 LFT",
    regimenes: ["con_empleados"],
    tipo: "laboral",
    urgente: true,
  },
  {
    mes: 12, dia: 31,
    nombre: "Inventario físico y cierre contable",
    ley: "Art. 28 CFF",
    regimenes: ["general_pm", "pf_actividad"],
    tipo: "informativa",
  },
];

const TIPO_COLORS: Record<string, string> = {
  pago:        "bg-red-500/15 border-red-500/30 text-red-300",
  declaracion: "bg-blue-500/15 border-blue-500/30 text-blue-300",
  laboral:     "bg-yellow-500/15 border-yellow-500/30 text-yellow-300",
  informativa: "bg-purple-500/15 border-purple-500/30 text-purple-300",
};

const TIPO_ICON: Record<string, string> = {
  pago: "💰", declaracion: "📋", laboral: "👷", informativa: "📊",
};

function ObligacionCard({ ob }: { ob: Obligacion }) {
  return (
    <div className={`flex items-start gap-2 px-3 py-2 rounded-xl border text-xs ${TIPO_COLORS[ob.tipo]} ${ob.urgente ? "ring-1 ring-red-500/40" : ""}`}>
      <span className="text-base leading-none mt-0.5">{TIPO_ICON[ob.tipo]}</span>
      <div className="flex-1">
        <p className="font-medium">{ob.nombre}</p>
        <p className="opacity-60 mt-0.5">{ob.ley}</p>
      </div>
      <span className="font-bold text-sm shrink-0">día {ob.dia}</span>
    </div>
  );
}

export default function CalendarioPage() {
  const [regimen, setRegimen] = useState<Regimen>("todos");
  const [mesActivo, setMesActivo] = useState<number | null>(null);
  const hoy = new Date();
  const mesActual = hoy.getMonth(); // 0-indexed

  function getObligacionesMes(mesIndex: number): Obligacion[] {
    const mes = mesIndex + 1;
    const matches = (ob: Obligacion) =>
      regimen === "todos" ||
      ob.regimenes.includes("todos") ||
      ob.regimenes.includes(regimen);

    const mensuales = MENSUALES.filter(matches);
    const especiales = ESPECIALES.filter(e => e.mes === mes && matches(e));
    return [...mensuales, ...especiales].sort((a, b) => a.dia - b.dia);
  }

  const mesVista = mesActivo ?? mesActual;
  const obligacionesVista = getObligacionesMes(mesVista);

  // Count urgentes in current month
  const totalMes = getObligacionesMes(mesActual).length;
  const urgentes = getObligacionesMes(mesActual).filter(o => o.urgente).length;

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-5">
          <div>
            <h1 className="text-xl font-bold text-green-100">Calendario Fiscal 2026</h1>
            <p className="text-sm text-gray-500 mt-0.5">Obligaciones por régimen — México</p>
          </div>
          <div className="flex gap-2 flex-wrap justify-end">
            {REGIMENES.map(r => (
              <button key={r.id} onClick={() => setRegimen(r.id)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                  regimen === r.id
                    ? "bg-green-500/15 border-green-500/30 text-green-300"
                    : "bg-white/3 border-white/10 text-gray-400 hover:text-green-200"
                }`}>
                {r.label}
              </button>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[
            { label: "Obligaciones este mes", value: totalMes, icon: "📅" },
            { label: "Fechas críticas", value: urgentes, icon: "🔴" },
            { label: "Día límite principal", value: "17", icon: "📌" },
            { label: "Ejercicio fiscal", value: "2026", icon: "🏛️" },
          ].map(s => (
            <div key={s.label} className="rounded-2xl border border-white/8 bg-white/3 p-4">
              <p className="text-2xl mb-1">{s.icon}</p>
              <p className="text-xl font-bold text-green-300">{s.value}</p>
              <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* Grid meses */}
          <div className="lg:col-span-1">
            <p className="text-xs text-gray-500 uppercase tracking-widest mb-3">Meses</p>
            <div className="grid grid-cols-3 gap-1.5">
              {MESES.map((mes, i) => {
                const count = getObligacionesMes(i).length;
                const isActual = i === mesActual;
                const isSelected = i === mesVista;
                return (
                  <button key={i} onClick={() => setMesActivo(i)}
                    className={`rounded-xl border px-2 py-2.5 text-center transition-all ${
                      isSelected
                        ? "bg-green-500/15 border-green-500/30 text-green-300"
                        : isActual
                          ? "bg-white/6 border-white/15 text-green-200"
                          : "bg-white/3 border-white/8 text-gray-400 hover:bg-white/5 hover:text-green-200"
                    }`}>
                    <p className="text-xs font-medium">{mes.slice(0, 3)}</p>
                    <p className="text-[10px] text-gray-500 mt-0.5">{count} obligs.</p>
                    {isActual && <div className="w-1.5 h-1.5 rounded-full bg-green-400 mx-auto mt-1" />}
                  </button>
                );
              })}
            </div>

            {/* Leyenda */}
            <div className="mt-4 space-y-1.5">
              <p className="text-xs text-gray-500 uppercase tracking-widest mb-2">Leyenda</p>
              {Object.entries(TIPO_ICON).map(([tipo, icon]) => (
                <div key={tipo} className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs ${TIPO_COLORS[tipo]}`}>
                  <span>{icon}</span>
                  <span className="capitalize">{tipo === "pago" ? "Pago de impuesto" : tipo === "declaracion" ? "Declaración" : tipo === "laboral" ? "Obligación laboral" : "Informativa"}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Lista obligaciones */}
          <div className="lg:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-gray-500 uppercase tracking-widest">
                {MESES[mesVista]} 2026
                {mesVista === mesActual && <span className="ml-2 text-green-400">← hoy</span>}
              </p>
              <span className="text-xs text-gray-600">{obligacionesVista.length} obligaciones</span>
            </div>

            {obligacionesVista.length === 0 ? (
              <div className="rounded-2xl border border-white/8 bg-white/3 p-10 text-center">
                <p className="text-gray-600 text-sm">Sin obligaciones para este régimen en {MESES[mesVista]}</p>
              </div>
            ) : (
              <div className="space-y-2">
                {obligacionesVista.map((ob, i) => (
                  <ObligacionCard key={i} ob={ob} />
                ))}
              </div>
            )}

            {mesVista === mesActual && (
              <div className="mt-4 rounded-xl border border-green-500/20 bg-green-500/5 p-3">
                <p className="text-xs text-green-400">
                  💡 Hoy es {hoy.getDate()} de {MESES[mesActual].toLowerCase()}. El próximo límite del 17 está en <strong>{17 - hoy.getDate() > 0 ? `${17 - hoy.getDate()} días` : "este mes (ya pasó)"}</strong>.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
