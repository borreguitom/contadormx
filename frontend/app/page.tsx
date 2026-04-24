"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const FEATURES = [
  {
    icon: "💬",
    title: "Agente fiscal IA",
    desc: "Pregunta cualquier duda. El agente usa herramientas reales: calcula ISR, busca en la ley, obtiene el calendario.",
  },
  {
    icon: "🧮",
    title: "Calculadoras 2025",
    desc: "ISR PF/PM, IVA con proporcionalidad, IMSS, nómina completa y finiquito. Tablas vigentes actualizadas.",
  },
  {
    icon: "🧾",
    title: "Validador CFDI 4.0",
    desc: "Pega o arrastra tu XML. Detecta errores de estructura, namespace, campos obligatorios y Timbre Fiscal.",
  },
  {
    icon: "📚",
    title: "RAG legislativo",
    desc: "Busca en LISR, LIVA, CFF, LSS y LFT. El agente cita el artículo exacto con fundamento legal.",
  },
  {
    icon: "📅",
    title: "Calendario fiscal",
    desc: "Todas las obligaciones del ejercicio 2025 por régimen. Pagos provisionales, DIOT, PTU, aguinaldo.",
  },
  {
    icon: "📄",
    title: "Documentos PDF",
    desc: "Genera cartas al SAT, cédulas ISR, carta encargo y escritos de respuesta en segundos.",
  },
];

const PRICING = [
  {
    id: "free",
    nombre: "Free",
    precio: "$0",
    periodo: "",
    desc: "Para empezar",
    highlight: false,
    features: ["5 clientes", "50 consultas / mes", "Calculadoras", "Validador CFDI", "Calendario"],
  },
  {
    id: "pro",
    nombre: "Pro",
    precio: "$499",
    periodo: "/ mes MXN",
    desc: "Para contadores activos",
    highlight: true,
    features: ["50 clientes", "1,000 consultas / mes", "Todo Free +", "RAG legislación completa", "Documentos PDF", "Búsqueda web"],
  },
  {
    id: "agencia",
    nombre: "Agencia",
    precio: "$999",
    periodo: "/ mes MXN",
    desc: "Para despachos",
    highlight: false,
    features: ["Clientes ilimitados", "Consultas ilimitadas", "Todo Pro +", "Soporte prioritario", "Onboarding personalizado"],
  },
];

export default function LandingPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("cmx_token");
    if (token) router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen" style={{ background: "#0a0f0a" }}>

      {/* Nav */}
      <nav className="sticky top-0 z-40 border-b border-white/7 bg-black/40 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-green-800 to-green-500 flex items-center justify-center text-sm shadow shadow-green-900/50">
              🏛️
            </div>
            <span className="text-sm font-bold text-green-100 tracking-wide">ContadorMX</span>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/login"
              className="text-sm text-gray-400 hover:text-green-300 px-3 py-1.5 transition-colors">
              Ingresar
            </Link>
            <Link href="/register"
              className="text-sm px-4 py-1.5 rounded-lg bg-gradient-to-r from-green-700 to-green-500 text-white font-medium shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400 transition-all">
              Empieza gratis
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden pt-20 pb-24 px-6">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full bg-green-900/20 blur-3xl" />
        </div>
        <div className="relative max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 text-xs px-3 py-1 rounded-full border border-green-500/25 bg-green-500/8 text-green-400 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            Tablas fiscales 2025 actualizadas · ISR · IVA · IMSS · LFT
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-green-50 leading-tight mb-5">
            El agente fiscal IA<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-300">
              para contadores mexicanos
            </span>
          </h1>
          <p className="text-lg text-gray-400 leading-relaxed mb-8 max-w-xl mx-auto">
            Calcula ISR, valida CFDIs, busca en la ley y genera documentos profesionales — todo en segundos, con fundamento legal incluido.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link href="/register"
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white font-semibold shadow-lg shadow-green-900/40 hover:from-green-600 hover:to-green-400 transition-all text-sm">
              Empieza gratis →
            </Link>
            <Link href="/login"
              className="px-6 py-3 rounded-xl border border-white/12 bg-white/4 text-gray-300 hover:text-green-300 hover:border-green-500/25 transition-all text-sm">
              Ya tengo cuenta
            </Link>
          </div>
          <p className="text-xs text-gray-600 mt-4">Sin tarjeta de crédito · Gratis para empezar</p>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 border-t border-white/7">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-green-100 mb-2">Todo lo que necesita un contador</h2>
            <p className="text-gray-500 text-sm">Seis herramientas integradas en un solo agente inteligente</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map((f) => (
              <div key={f.title}
                className="rounded-2xl border border-white/8 bg-white/3 p-5 hover:bg-white/5 hover:border-green-500/20 transition-all group">
                <div className="text-3xl mb-3">{f.icon}</div>
                <h3 className="text-sm font-semibold text-green-200 mb-1.5 group-hover:text-green-300 transition-colors">
                  {f.title}
                </h3>
                <p className="text-xs text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-6 border-t border-white/7">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-green-100 mb-2">Tres pasos para empezar</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[
              { num: "01", title: "Crea tu cuenta gratis", desc: "Registro en 30 segundos. Sin tarjeta, sin contratos." },
              { num: "02", title: "Agrega tus clientes", desc: "RFC, régimen y datos fiscales. El agente los usa como contexto en cada consulta." },
              { num: "03", title: "Consulta y calcula", desc: "Pregunta en lenguaje natural. El agente usa las herramientas correctas automáticamente." },
            ].map((s) => (
              <div key={s.num} className="text-center">
                <div className="w-12 h-12 rounded-full bg-green-500/12 border border-green-500/25 flex items-center justify-center text-green-400 font-bold text-sm mx-auto mb-4">
                  {s.num}
                </div>
                <h3 className="text-sm font-semibold text-green-200 mb-2">{s.title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="py-20 px-6 border-t border-white/7">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold text-green-100 mb-2">Precios simples</h2>
            <p className="text-gray-500 text-sm">Cancela cuando quieras</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {PRICING.map((p) => (
              <div key={p.id}
                className={`rounded-2xl p-6 flex flex-col ${
                  p.highlight
                    ? "border-2 border-green-500/40 bg-green-500/5"
                    : "border border-white/8 bg-white/3"
                }`}>
                {p.highlight && (
                  <span className="self-start text-[10px] px-2 py-0.5 rounded-full bg-green-500/15 border border-green-500/25 text-green-400 uppercase tracking-wide mb-3">
                    Más popular
                  </span>
                )}
                <h3 className="text-lg font-bold text-green-100">{p.nombre}</h3>
                <p className="text-xs text-gray-500 mb-3">{p.desc}</p>
                <div className="flex items-baseline gap-1 mb-5">
                  <span className="text-2xl font-bold text-green-200">{p.precio}</span>
                  <span className="text-xs text-gray-500">{p.periodo}</span>
                </div>
                <ul className="flex-1 space-y-2 mb-6">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-center gap-2 text-xs text-gray-300">
                      <span className="text-green-400">✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link href="/register"
                  className={`w-full py-2.5 rounded-xl text-center text-sm font-medium transition-all ${
                    p.highlight
                      ? "bg-gradient-to-r from-green-700 to-green-500 text-white shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400"
                      : "border border-white/12 bg-white/4 text-gray-300 hover:text-green-300 hover:border-green-500/20"
                  }`}>
                  {p.id === "free" ? "Empieza gratis →" : `Probar ${p.nombre} →`}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA final */}
      <section className="py-20 px-6 border-t border-white/7">
        <div className="max-w-2xl mx-auto text-center">
          <div className="text-4xl mb-4">🏛️</div>
          <h2 className="text-2xl font-bold text-green-100 mb-3">
            Empieza hoy, gratis
          </h2>
          <p className="text-gray-500 text-sm mb-8">
            Más de 6 herramientas fiscales integradas. Tablas 2025 actualizadas. Sin instalación.
          </p>
          <Link href="/register"
            className="inline-flex px-8 py-3 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white font-semibold shadow-lg shadow-green-900/40 hover:from-green-600 hover:to-green-400 transition-all text-sm">
            Crear cuenta gratis →
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/7 py-8 px-6">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <span>🏛️</span>
            <span>ContadorMX — Hecho en México · 2025</span>
          </div>
          <div className="flex gap-4">
            <Link href="/login" className="hover:text-gray-400 transition-colors">Ingresar</Link>
            <Link href="/register" className="hover:text-gray-400 transition-colors">Registro</Link>
          </div>
        </div>
      </footer>

    </div>
  );
}
