"use client";
import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const [form, setForm] = useState({ nombre: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form.email, form.password, form.nombre);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al registrar");
    } finally {
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
          <h1 className="text-xl font-bold text-green-100">Crear cuenta</h1>
          <p className="text-sm text-gray-500 mt-1">ContadorMX</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          {[
            { k: "nombre", label: "Nombre", type: "text", placeholder: "Lic. Juan García" },
            { k: "email", label: "Correo", type: "email", placeholder: "contador@despacho.mx" },
            { k: "password", label: "Contraseña", type: "password", placeholder: "••••••••" },
          ].map(({ k, label, type, placeholder }) => (
            <div key={k}>
              <label className="block text-xs text-gray-400 mb-1.5 tracking-wide uppercase">{label}</label>
              <input
                type={type}
                value={form[k as keyof typeof form]}
                onChange={set(k)}
                required
                placeholder={placeholder}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-green-50 focus:outline-none focus:border-green-500/50 transition-colors placeholder:text-gray-600"
              />
            </div>
          ))}

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
            {loading ? "Creando cuenta..." : "Crear cuenta"}
          </button>
        </form>

        <p className="text-center text-xs text-gray-600 mt-5">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="text-green-500 hover:text-green-400">
            Entrar
          </Link>
        </p>
      </div>
    </div>
  );
}
