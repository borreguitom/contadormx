"use client";
import { useState, useEffect } from "react";

const STEPS = [
  {
    icon: "💬",
    titulo: "Chat fiscal con IA",
    desc: "Pregunta cualquier duda contable o fiscal. El agente usa tablas ISR 2026, LIVA, LSS y consulta legislación en tiempo real.",
  },
  {
    icon: "🧮",
    titulo: "Calculadoras en un clic",
    desc: "ISR PF/PM, IVA, IMSS, nómina y finiquito — con fundamento legal incluido en cada resultado.",
  },
  {
    icon: "📅",
    titulo: "Calendario fiscal completo",
    desc: "Todas las obligaciones de 2026 por régimen. Nunca más pierdas un pago provisional.",
  },
  {
    icon: "📄",
    titulo: "Genera documentos PDF",
    desc: "Cartas al SAT, cédulas ISR, carta encargo y escritos de respuesta en segundos.",
  },
];

const STORAGE_KEY = "contadormx_onboarding_done";

export default function WelcomeBanner() {
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const done = localStorage.getItem(STORAGE_KEY);
    if (!done) setVisible(true);
  }, []);

  const close = () => {
    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
  };

  if (!visible) return null;

  const isLast = step === STEPS.length - 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md mx-4 rounded-3xl border border-green-500/20 bg-gradient-to-br from-green-950/90 to-black/90 p-8 shadow-2xl shadow-green-900/30">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-800 to-green-500 flex items-center justify-center text-xl shadow shadow-green-900/50">
            🏛️
          </div>
          <div>
            <div className="text-base font-bold text-green-100">ContadorMX</div>
            <div className="text-[10px] text-green-500 tracking-widest uppercase">Agente Fiscal IA</div>
          </div>
        </div>

        {/* Step content */}
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">{STEPS[step].icon}</div>
          <h2 className="text-lg font-bold text-green-100 mb-2">{STEPS[step].titulo}</h2>
          <p className="text-sm text-gray-400 leading-relaxed">{STEPS[step].desc}</p>
        </div>

        {/* Step dots */}
        <div className="flex justify-center gap-1.5 mb-6">
          {STEPS.map((_, i) => (
            <button key={i} onClick={() => setStep(i)}
              className={`rounded-full transition-all ${
                i === step ? "w-6 h-2 bg-green-400" : "w-2 h-2 bg-white/20"
              }`} />
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button onClick={close}
            className="flex-1 py-2.5 rounded-xl border border-white/10 bg-white/4 text-sm text-gray-400 hover:text-gray-200 transition-all">
            Saltar
          </button>
          <button
            onClick={() => isLast ? close() : setStep(s => s + 1)}
            className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400 transition-all">
            {isLast ? "Empezar →" : "Siguiente →"}
          </button>
        </div>
      </div>
    </div>
  );
}
