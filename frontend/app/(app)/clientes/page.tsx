"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Cliente, type ClienteCreate } from "@/lib/api";
import { SelectInput } from "@/components/ui/SelectInput";

const REGIMENES = [
  "Sueldos y Salarios",
  "Actividades Empresariales",
  "Honorarios",
  "Arrendamiento",
  "RESICO PF",
  "Personas Morales Régimen General",
  "RESICO PM",
];

function rfcValido(rfc: string) {
  return /^[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}$/.test(rfc.toUpperCase());
}

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState<ClienteCreate>({
    rfc: "", razon_social: "", regimen_fiscal: "", actividad: "", correo: "", telefono: "",
  });

  useEffect(() => { loadClientes(); }, []);

  const loadClientes = async () => {
    try {
      setClientes(await api.clients.list());
    } catch {
      setError("Error cargando clientes");
    } finally {
      setLoading(false);
    }
  };

  const set = (k: keyof ClienteCreate) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }));

  const guardar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rfcValido(form.rfc)) { setError("RFC inválido"); return; }
    setSaving(true); setError("");
    try {
      const nuevo = await api.clients.create({ ...form, rfc: form.rfc.toUpperCase() });
      setClientes(prev => [...prev, nuevo]);
      setShowForm(false);
      setForm({ rfc: "", razon_social: "", regimen_fiscal: "", actividad: "", correo: "", telefono: "" });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-green-100">Clientes</h1>
            <p className="text-sm text-gray-500 mt-0.5">{clientes.length} registros</p>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400 transition-all"
          >
            + Nuevo cliente
          </button>
        </div>

        {/* Modal nuevo cliente */}
        {showForm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
            <div className="w-full max-w-md bg-[#0f1a0f] border border-green-900/40 rounded-2xl p-6 shadow-2xl">
              <h2 className="text-lg font-bold text-green-100 mb-4">Nuevo cliente</h2>
              <form onSubmit={guardar} className="space-y-3">
                {[
                  { k: "rfc", label: "RFC *", placeholder: "XAXX010101000" },
                  { k: "razon_social", label: "Razón Social / Nombre *", placeholder: "" },
                  { k: "actividad", label: "Actividad", placeholder: "Comercio, servicios, manufactura…" },
                  { k: "correo", label: "Correo", placeholder: "cliente@empresa.mx" },
                  { k: "telefono", label: "Teléfono", placeholder: "55 1234 5678" },
                ].map(({ k, label, placeholder }) => (
                  <div key={k}>
                    <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">{label}</label>
                    <input
                      value={form[k as keyof ClienteCreate] ?? ""}
                      onChange={set(k as keyof ClienteCreate)}
                      placeholder={placeholder}
                      required={k === "rfc" || k === "razon_social"}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-green-50 focus:outline-none focus:border-green-500/50 placeholder:text-gray-600"
                    />
                  </div>
                ))}
                <div>
                  <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">Régimen Fiscal</label>
                  <SelectInput
                    value={form.regimen_fiscal ?? ""}
                    onChange={v => setForm(f => ({ ...f, regimen_fiscal: v }))}
                    options={[{ value: "", label: "Seleccionar…" }, ...REGIMENES.map(r => ({ value: r, label: r }))]}
                  />
                </div>

                {error && <p className="text-xs text-red-400">{error}</p>}

                <div className="flex gap-2 pt-1">
                  <button type="button" onClick={() => { setShowForm(false); setError(""); }}
                    className="flex-1 py-2 rounded-xl border border-white/10 text-sm text-gray-400 hover:bg-white/5 transition-all">
                    Cancelar
                  </button>
                  <button type="submit" disabled={saving}
                    className="flex-1 py-2 rounded-xl bg-green-700 text-white text-sm hover:bg-green-600 transition-all disabled:opacity-50">
                    {saving ? "Guardando…" : "Guardar"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Lista */}
        {loading ? (
          <div className="text-center py-16 text-gray-600 text-sm">Cargando…</div>
        ) : clientes.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-4xl mb-3">👥</div>
            <p className="text-gray-500 text-sm">Sin clientes registrados</p>
            <button onClick={() => setShowForm(true)} className="mt-4 text-green-500 text-sm hover:underline">
              Agregar primer cliente
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {clientes.map(c => (
              <Link key={c.id} href={`/clientes/${c.id}`}
                className="flex items-center justify-between p-4 rounded-xl border border-white/8 bg-white/3 hover:bg-white/6 hover:border-green-500/25 transition-all group">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-green-900/40 flex items-center justify-center text-sm font-bold text-green-400 border border-green-800/30">
                    {c.razon_social[0].toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-green-100">{c.razon_social}</p>
                    <p className="text-xs text-gray-500 font-mono mt-0.5">{c.rfc}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {c.regimen_fiscal && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-900/30 text-green-400 border border-green-800/30">
                      {c.regimen_fiscal}
                    </span>
                  )}
                  <span className="text-gray-600 group-hover:text-green-500 transition-colors">→</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
