"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Credenciales incorrectas");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "#0a0f0a" }}>
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-800 to-green-500 flex items-center justify-center text-2xl mx-auto mb-3 shadow-lg shadow-green-900/40">
            🏛️
          </div>
          <h1 className="text-xl font-bold text-green-100">ContadorMX</h1>
          <p className="text-sm text-gray-500 mt-1">Agente Fiscal & Contable</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
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
          <div>
            <label className="block text-xs text-gray-400 mb-1.5 tracking-wide uppercase">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-green-50 focus:outline-none focus:border-green-500/50 transition-colors"
            />
          </div>

          {error && (
            <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/40 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-50"
          >
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>

        <div className="flex items-center justify-between mt-5">
          <p className="text-xs text-gray-600">
            ¿Sin cuenta?{" "}
            <Link href="/register" className="text-green-500 hover:text-green-400">
              Registrarse
            </Link>
          </p>
          <Link href="/forgot-password" className="text-xs text-gray-500 hover:text-green-400 transition-colors">
            ¿Olvidaste tu contraseña?
          </Link>
        </div>
      </div>
    </div>
  );
}
