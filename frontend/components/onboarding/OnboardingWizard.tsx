"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const STORAGE_KEY = "cmx_onboarding_v2";

const REGIMENES = [
  "Sueldos y Salarios",
  "Actividades Empresariales y Profesionales",
  "Honorarios",
  "Arrendamiento",
  "RESICO — Persona Física",
  "RESICO — Persona Moral",
  "Personas Morales Régimen General",
];

type Role = "contador" | "empresa" | "freelancer" | null;

export default function OnboardingWizard() {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);
  const [role, setRole] = useState<Role>(null);

  // Client form
  const [rfc, setRfc] = useState("");
  const [razon, setRazon] = useState("");
  const [regimen, setRegimen] = useState(REGIMENES[0]);
  const [saving, setSaving] = useState(false);
  const [saveErr, setSaveErr] = useState("");
  const [clientCreated, setClientCreated] = useState(false);

  useEffect(() => {
    const done = localStorage.getItem(STORAGE_KEY);
    if (!done) setVisible(true);
  }, []);

  function close() {
    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
  }

  async function handleCreateClient() {
    if (!rfc.trim() || !razon.trim()) { setSaveErr("RFC y razón social son obligatorios"); return; }
    setSaving(true); setSaveErr("");
    try {
      await api.clients.create({ rfc: rfc.toUpperCase().trim(), razon_social: razon.trim(), regimen_fiscal: regimen });
      setClientCreated(true);
      setStep(3);
    } catch (err: unknown) {
      setSaveErr(err instanceof Error ? err.message : "Error al guardar");
    } finally { setSaving(false); }
  }

  function goNext() { setStep(s => s + 1); }

  function finish(destination?: string) {
    close();
    if (destination) router.push(destination);
  }

  if (!visible) return null;

  const TOTAL_STEPS = 4;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-3xl border border-green-500/20 bg-gradient-to-br from-[#0d1a0d] to-[#0a0f0a] shadow-2xl shadow-green-900/30 overflow-hidden">

        {/* Progress bar */}
        <div className="h-0.5 bg-white/5">
          <div
            className="h-full bg-gradient-to-r from-green-700 to-green-400 transition-all duration-500"
            style={{ width: `${((step + 1) / TOTAL_STEPS) * 100}%` }}
          />
        </div>

        <div className="p-8">
          {/* Logo */}
          <div className="flex items-center gap-2.5 mb-7">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-green-800 to-green-500 flex items-center justify-center text-lg shadow shadow-green-900/50">
              🏛️
            </div>
            <div>
              <div className="text-sm font-bold text-green-100">ContadorMX</div>
              <div className="text-[10px] text-green-500 tracking-widest uppercase">Agente Fiscal IA</div>
            </div>
            <button onClick={close}
              className="ml-auto text-gray-600 hover:text-gray-400 text-xl transition-colors">×</button>
          </div>

          {/* ── STEP 0: Bienvenida ─────────────────────────────────── */}
          {step === 0 && (
            <div className="text-center">
              <div className="text-5xl mb-4">👋</div>
              <h2 className="text-xl font-bold text-green-100 mb-3">Bienvenido a ContadorMX</h2>
              <p className="text-sm text-gray-400 leading-relaxed mb-8">
                Tu agente fiscal con IA. En 2 minutos configuras tu espacio y empiezas a ahorrar horas de trabajo.
              </p>
              <div className="grid grid-cols-3 gap-3 mb-8">
                {[
                  { icon: "🧮", text: "Calcula ISR, IVA e IMSS" },
                  { icon: "📥", text: "Descarga CFDIs del SAT" },
                  { icon: "💬", text: "Consulta al agente fiscal" },
                ].map(f => (
                  <div key={f.text} className="rounded-xl border border-white/8 bg-white/3 p-3">
                    <div className="text-2xl mb-1.5">{f.icon}</div>
                    <p className="text-xs text-gray-400">{f.text}</p>
                  </div>
                ))}
              </div>
              <button onClick={goNext}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-semibold shadow shadow-green-900/40 hover:from-green-600 hover:to-green-400 transition-all">
                Empezar configuración →
              </button>
            </div>
          )}

          {/* ── STEP 1: Rol ────────────────────────────────────────── */}
          {step === 1 && (
            <div>
              <h2 className="text-lg font-bold text-green-100 mb-2">¿Cómo usarás ContadorMX?</h2>
              <p className="text-sm text-gray-500 mb-6">Esto personaliza tu flujo de trabajo.</p>
              <div className="space-y-3 mb-8">
                {[
                  {
                    id: "contador" as Role,
                    icon: "📊",
                    title: "Soy contador",
                    desc: "Gestiono la contabilidad de varios clientes. Necesito calcular declaraciones, organizar facturas y generar reportes.",
                  },
                  {
                    id: "empresa" as Role,
                    icon: "🏢",
                    title: "Tengo una empresa",
                    desc: "Administro mi negocio. Quiero controlar mis facturas, nómina, y saber cuánto le debo al SAT.",
                  },
                  {
                    id: "freelancer" as Role,
                    icon: "💻",
                    title: "Soy freelancer o autónomo",
                    desc: "Facturo por honorarios o actividades empresariales. Quiero saber cuánto pago de ISR e IVA cada mes.",
                  },
                ].map(opt => (
                  <button key={opt.id} onClick={() => setRole(opt.id)}
                    className={`w-full flex items-start gap-3 p-4 rounded-xl border text-left transition-all ${
                      role === opt.id
                        ? "border-green-500/50 bg-green-500/10 text-white"
                        : "border-white/8 bg-white/3 text-gray-400 hover:border-white/15 hover:text-gray-300"
                    }`}>
                    <span className="text-2xl">{opt.icon}</span>
                    <div>
                      <p className="text-sm font-semibold mb-0.5">{opt.title}</p>
                      <p className="text-xs opacity-70 leading-relaxed">{opt.desc}</p>
                    </div>
                    {role === opt.id && (
                      <span className="ml-auto text-green-400 text-lg">✓</span>
                    )}
                  </button>
                ))}
              </div>
              <button onClick={goNext} disabled={!role}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-green-700 to-green-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-all hover:from-green-600 hover:to-green-400">
                Continuar →
              </button>
            </div>
          )}

          {/* ── STEP 2: Crear primer cliente / perfil ──────────────── */}
          {step === 2 && (
            <div>
              <h2 className="text-lg font-bold text-green-100 mb-2">
                {role === "contador" ? "Agrega tu primer cliente" : "¿Cuál es tu RFC?"}
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                {role === "contador"
                  ? "Puedes agregar más clientes después desde el menú Clientes."
                  : "Lo usamos para calcular tus declaraciones correctamente."}
              </p>
              <div className="space-y-3 mb-6">
                <div>
                  <label className="block text-xs text-gray-400 mb-1">
                    {role === "contador" ? "RFC del cliente" : "Tu RFC"}
                  </label>
                  <input
                    value={rfc} onChange={e => setRfc(e.target.value.toUpperCase())}
                    placeholder="XAXX010101000" maxLength={13}
                    className="w-full px-3 py-2.5 text-sm bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 font-mono focus:outline-none focus:border-green-500/50 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">
                    {role === "contador" ? "Razón social del cliente" : "Tu nombre o razón social"}
                  </label>
                  <input
                    value={razon} onChange={e => setRazon(e.target.value)}
                    placeholder={role === "contador" ? "Empresa Ejemplo SA de CV" : "Tu nombre completo"}
                    className="w-full px-3 py-2.5 text-sm bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50 transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">Régimen fiscal</label>
                  <select value={regimen} onChange={e => setRegimen(e.target.value)}
                    className="w-full px-3 py-2.5 text-sm bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-green-500/50 transition-colors">
                    {REGIMENES.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
              </div>
              {saveErr && <p className="text-xs text-red-400 mb-3">{saveErr}</p>}
              <div className="flex gap-2">
                <button onClick={() => { setStep(3); }}
                  className="flex-1 py-2.5 rounded-xl border border-white/10 text-sm text-gray-400 hover:text-gray-200 transition-all">
                  Saltar por ahora
                </button>
                <button onClick={handleCreateClient} disabled={saving}
                  className="flex-2 flex-grow py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 disabled:opacity-50 text-white text-sm font-semibold transition-all hover:from-green-600 hover:to-green-400">
                  {saving ? "Guardando..." : "Guardar y continuar →"}
                </button>
              </div>
            </div>
          )}

          {/* ── STEP 3: Próximo paso ───────────────────────────────── */}
          {step === 3 && (
            <div>
              {clientCreated && (
                <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-2.5 mb-5">
                  <span className="text-green-400">✓</span>
                  <p className="text-sm text-green-300">
                    {role === "contador" ? "Cliente creado." : "Perfil guardado."} Ahora elige tu primer paso:
                  </p>
                </div>
              )}
              {!clientCreated && (
                <p className="text-sm text-gray-400 mb-5">Sin problema. ¿Por dónde quieres empezar?</p>
              )}

              <h2 className="text-lg font-bold text-green-100 mb-5">
                ¿Qué quieres hacer primero?
              </h2>

              <div className="space-y-3 mb-6">
                {[
                  role === "contador" || role === "empresa"
                    ? {
                        icon: "📥",
                        title: "Descargar mis CFDIs del SAT",
                        desc: "Conecta tu e.firma y descarga todas tus facturas automáticamente.",
                        href: "/sat",
                        cta: "Ir a Descarga SAT →",
                        highlight: true,
                      }
                    : null,
                  {
                    icon: "📄",
                    title: "Subir facturas manualmente",
                    desc: "Arrastra tus XMLs o PDFs y el sistema extrae los datos automáticamente.",
                    href: "/documentos",
                    cta: "Ir a Documentos →",
                    highlight: false,
                  },
                  {
                    icon: "🧮",
                    title: "Calcular cuánto debo este mes",
                    desc: role === "freelancer"
                      ? "Ingresa tus ingresos del mes y calcula tu ISR e IVA en segundos."
                      : "ISR provisional, IVA, IMSS — con fundamento legal incluido.",
                    href: role === "freelancer" ? "/calculadoras" : "/calculadoras",
                    cta: "Abrir calculadora →",
                    highlight: false,
                  },
                  {
                    icon: "💬",
                    title: "Preguntarle al agente fiscal",
                    desc: "Haz cualquier pregunta sobre tus obligaciones, deducciones o trámites del SAT.",
                    href: "/chat",
                    cta: "Ir al chat →",
                    highlight: false,
                  },
                ].filter(Boolean).map((opt) => {
                  if (!opt) return null;
                  return (
                    <button key={opt.href} onClick={() => finish(opt.href)}
                      className={`w-full flex items-start gap-3 p-4 rounded-xl border text-left transition-all hover:scale-[1.01] ${
                        opt.highlight
                          ? "border-green-500/40 bg-green-500/8 hover:bg-green-500/15"
                          : "border-white/8 bg-white/3 hover:border-white/15"
                      }`}>
                      <span className="text-2xl">{opt.icon}</span>
                      <div className="flex-1">
                        <p className="text-sm font-semibold text-white mb-0.5">{opt.title}</p>
                        <p className="text-xs text-gray-500 leading-relaxed">{opt.desc}</p>
                      </div>
                      <span className="text-xs text-green-400 shrink-0 mt-1">{opt.cta}</span>
                    </button>
                  );
                })}
              </div>

              <button onClick={() => finish("/dashboard")}
                className="w-full py-2.5 rounded-xl border border-white/10 text-sm text-gray-500 hover:text-gray-300 transition-all">
                Ir al dashboard →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
