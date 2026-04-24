"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

function ResetForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!token) {
    return (
      <div className="text-center space-y-3">
        <p className="text-red-400 text-sm">Enlace inválido o expirado.</p>
        <Link href="/forgot-password" className="text-green-500 hover:text-green-400 text-sm">
          Solicitar nuevo enlace
        </Link>
      </div>
    );
  }

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (password !== confirm) { setError("Las contraseñas no coinciden"); return; }
    if (password.length < 8) { setError("Mínimo 8 caracteres"); return; }
    setLoading(true);
    try {
      await api.auth.resetPassword(token, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Enlace inválido o expirado");
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <div>
        <label className="block text-xs text-gray-400 mb-1.5 tracking-wide uppercase">Nueva contraseña</label>
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-green-50 focus:outline-none focus:border-green-500/50 transition-colors"
          placeholder="Mínimo 8 caracteres"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-400 mb-1.5 tracking-wide uppercase">Confirmar contraseña</label>
        <input
          type="password"
          value={confirm}
          onChange={e => setConfirm(e.target.value)}
          required
          className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-green-50 focus:outline-none focus:border-green-500/50 transition-colors"
        />
      </div>
      {error && (
        <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>
      )}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/40 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-50"
      >
        {loading ? "Guardando..." : "Guardar nueva contraseña"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "#0a0f0a" }}>
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-800 to-green-500 flex items-center justify-center text-2xl mx-auto mb-3 shadow-lg shadow-green-900/40">
            🏛️
          </div>
          <h1 className="text-xl font-bold text-green-100">ContadorMX</h1>
          <p className="text-sm text-gray-500 mt-1">Nueva contraseña</p>
        </div>
        <Suspense fallback={<div className="text-gray-500 text-sm text-center">Cargando...</div>}>
          <ResetForm />
        </Suspense>
      </div>
    </div>
  );
}
