"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, type Cliente } from "@/lib/api";

export default function ClienteDetalle() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.clients.get(Number(id))
      .then(setCliente)
      .catch(() => router.replace("/clientes"))
      .finally(() => setLoading(false));
  }, [id, router]);

  if (loading) return (
    <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">Cargando…</div>
  );
  if (!cliente) return null;

  const campos = [
    { label: "RFC", value: cliente.rfc, mono: true },
    { label: "Régimen Fiscal", value: cliente.regimen_fiscal },
    { label: "Actividad", value: cliente.actividad },
    { label: "Correo", value: cliente.correo },
  ].filter(c => c.value);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-6">
          <Link href="/clientes" className="hover:text-green-400 transition-colors">Clientes</Link>
          <span>/</span>
          <span className="text-gray-400">{cliente.razon_social}</span>
        </div>

        {/* Card principal */}
        <div className="rounded-2xl border border-white/8 bg-white/3 p-6 mb-5">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-14 h-14 rounded-2xl bg-green-900/40 flex items-center justify-center text-2xl font-bold text-green-300 border border-green-800/30">
              {cliente.razon_social[0].toUpperCase()}
            </div>
            <div>
              <h1 className="text-xl font-bold text-green-100">{cliente.razon_social}</h1>
              <p className="text-sm font-mono text-gray-400 mt-0.5">{cliente.rfc}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {campos.map(c => (
              <div key={c.label} className="rounded-xl bg-white/3 border border-white/6 p-3">
                <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{c.label}</p>
                <p className={`text-sm text-green-200 ${c.mono ? "font-mono" : ""}`}>{c.value}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Acciones */}
        <div className="grid grid-cols-2 gap-3">
          <Link
            href={`/chat?cliente=${cliente.id}&nombre=${encodeURIComponent(cliente.razon_social)}`}
            className="flex items-center gap-2.5 p-4 rounded-xl border border-green-500/25 bg-green-500/8 hover:bg-green-500/15 transition-all"
          >
            <span className="text-xl">💬</span>
            <div>
              <p className="text-sm font-medium text-green-300">Nueva consulta</p>
              <p className="text-xs text-gray-500">Con contexto del cliente</p>
            </div>
          </Link>
          <Link
            href={`/clientes/${cliente.id}/documentos`}
            className="flex items-center gap-2.5 p-4 rounded-xl border border-blue-500/25 bg-blue-500/8 hover:bg-blue-500/15 transition-all"
          >
            <span className="text-xl">🗂️</span>
            <div>
              <p className="text-sm font-medium text-blue-300">Documentos</p>
              <p className="text-xs text-gray-500">XML, PDF, facturas</p>
            </div>
          </Link>
          <Link
            href="/calculadoras"
            className="flex items-center gap-2.5 p-4 rounded-xl border border-white/8 bg-white/3 hover:bg-white/6 transition-all"
          >
            <span className="text-xl">🧮</span>
            <div>
              <p className="text-sm font-medium text-green-200">Calculadoras</p>
              <p className="text-xs text-gray-500">ISR, IVA, IMSS, nómina</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
