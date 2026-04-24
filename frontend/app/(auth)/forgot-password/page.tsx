"use client";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.auth.forgotPassword(email);
    } finally {
      // Siempre muestra éxito — no revelamos si el email existe
      setSent(true);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "#0a0f0a" }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-800 to-green-500 flex items-center justify-center text-2xl mx-auto mb-3 shadow-lg shadow-green-900/40">
            🏛️
          </div>
          <h1 className="text-xl font-bold text-green-100">ContadorMX</h1>
          <p className="text-sm text-gray-500 mt-1">Recuperar contraseña</p>
        </div>

        {sent ? (
          <div className="text-center space-y-4">
            <div className="text-4xl">📬</div>
            <p className="text-green-200 text-sm leading-relaxed">
              Si tu correo está registrado, recibirás un enlace para restablecer tu contraseña en los próximos minutos.
            </p>
            <p className="text-gray-500 text-xs">Revisa también tu carpeta de spam.</p>
            <Link href="/login" className="block mt-4 text-green-500 hover:text-green-400 text-sm">
              ← Volver al login
            </Link>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-4">
            <p className="text-sm text-gray-400 text-center mb-2">
              Ingresa tu correo y te enviamos un enlace para restablecer tu contraseña.
            </p>
            <div>
              <label className="block text-xs text-gray-400 mb-1.5 tracking-wide uppercase">Correo</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-green-50 focus:outline-none focus:border-green-500/50 transition-colors placeholder:text-gray-600"
                placeholder="contador@despacho.mx"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/40 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-50"
            >
              {loading ? "Enviando..." : "Enviar enlace"}
            </button>
            <p className="text-center text-xs text-gray-600 mt-2">
              <Link href="/login" className="text-green-500 hover:text-green-400">← Volver al login</Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}
