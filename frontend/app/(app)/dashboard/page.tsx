"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

interface DashboardStats {
  user_nombre: string;
  plan: string;
  queries_used: number;
  queries_limit: number;
  total_clientes: number;
  clientes_limit: number;
  conversaciones_recientes: { id: number; titulo: string; fecha: string }[];
  proximas_obligaciones: { fecha: string; dia: number; mes: string; nombre: string; tipo: string }[];
}

const TIPO_COLORS: Record<string, string> = {
  pago:        "text-red-400 bg-red-500/10 border-red-500/20",
  declaracion: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  laboral:     "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  informativa: "text-purple-400 bg-purple-500/10 border-purple-500/20",
};

const TIPO_ICON: Record<string, string> = {
  pago: "💰", declaracion: "📋", laboral: "👷", informativa: "📊",
};

const PLAN_BADGE: Record<string, string> = {
  free:    "bg-gray-500/15 text-gray-400 border-gray-500/25",
  pro:     "bg-blue-500/15 text-blue-400 border-blue-500/25",
  agencia: "bg-purple-500/15 text-purple-400 border-purple-500/25",
};

function UsageBar({ used, limit, label }: { used: number; limit: number; label: string }) {
  const pct = limit === -1 ? 0 : Math.min((used / limit) * 100, 100);
  const warn = pct > 80;
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className={warn ? "text-yellow-400" : "text-gray-500"}>
          {used} / {limit === -1 ? "∞" : limit}
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-white/8 overflow-hidden">
        {limit !== -1 && (
          <div
            className={`h-full rounded-full transition-all ${warn ? "bg-yellow-400" : "bg-green-400"}`}
            style={{ width: `${pct}%` }}
          />
        )}
        {limit === -1 && <div className="h-full w-full rounded-full bg-green-400/40" />}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard.stats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex gap-1.5">
        {[0,1,2].map(i => (
          <span key={i} className="w-2 h-2 rounded-full bg-green-500"
            style={{ animation: `bounce 1.2s infinite ${i * 0.18}s` }} />
        ))}
      </div>
    </div>
  );

  if (!stats) return (
    <div className="flex-1 flex items-center justify-center text-gray-600 text-sm">
      No se pudo cargar el dashboard
    </div>
  );

  const planLabel = stats.plan.charAt(0).toUpperCase() + stats.plan.slice(1);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">

        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-green-100">
              Hola, {stats.user_nombre} 👋
            </h1>
            <p className="text-sm text-gray-500 mt-0.5">Panel principal — ContadorMX</p>
          </div>
          <span className={`text-xs px-3 py-1 rounded-full border font-medium ${PLAN_BADGE[stats.plan]}`}>
            Plan {planLabel}
          </span>
        </div>

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <div className="rounded-2xl border border-white/8 bg-white/3 p-4">
            <p className="text-2xl mb-1">💬</p>
            <p className="text-2xl font-bold text-green-300">{stats.queries_used}</p>
            <p className="text-xs text-gray-500 mt-0.5">Consultas este mes</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/3 p-4">
            <p className="text-2xl mb-1">👥</p>
            <p className="text-2xl font-bold text-green-300">{stats.total_clientes}</p>
            <p className="text-xs text-gray-500 mt-0.5">Clientes activos</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/3 p-4">
            <p className="text-2xl mb-1">📅</p>
            <p className="text-2xl font-bold text-green-300">
              {stats.proximas_obligaciones[0]?.dia ?? "—"}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              Próx. límite ({stats.proximas_obligaciones[0]?.mes ?? ""})
            </p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/3 p-4">
            <p className="text-2xl mb-1">🏛️</p>
            <p className="text-2xl font-bold text-green-300">2025</p>
            <p className="text-xs text-gray-500 mt-0.5">Ejercicio fiscal</p>
          </div>
        </div>

        {/* Uso del plan */}
        <div className="rounded-2xl border border-white/8 bg-white/3 p-5 mb-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-green-200">Uso del plan</h2>
            {stats.plan === "free" && (
              <Link href="/billing"
                className="text-xs px-3 py-1 rounded-lg bg-green-500/12 border border-green-500/25 text-green-400 hover:bg-green-500/20 transition-all">
                Actualizar →
              </Link>
            )}
          </div>
          <div className="space-y-4">
            <UsageBar
              used={stats.queries_used}
              limit={stats.queries_limit}
              label="Consultas al agente"
            />
            <UsageBar
              used={stats.total_clientes}
              limit={stats.clientes_limit}
              label="Clientes"
            />
          </div>
          {stats.plan === "free" && stats.queries_used >= stats.queries_limit * 0.8 && (
            <p className="text-xs text-yellow-400 mt-3 bg-yellow-500/8 border border-yellow-500/20 rounded-lg px-3 py-2">
              ⚠ Llevas el {Math.round((stats.queries_used / stats.queries_limit) * 100)}% de tus consultas. Actualiza a Pro para 1,000 consultas/mes.
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Próximas obligaciones */}
          <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-green-200">Próximas obligaciones</h2>
              <Link href="/calendario" className="text-xs text-gray-500 hover:text-green-400 transition-colors">
                Ver todas →
              </Link>
            </div>
            <div className="space-y-2">
              {stats.proximas_obligaciones.map((ob, i) => (
                <div key={i} className={`flex items-center gap-3 px-3 py-2 rounded-xl border text-xs ${TIPO_COLORS[ob.tipo] ?? "text-gray-400 bg-white/3 border-white/8"}`}>
                  <span className="text-base">{TIPO_ICON[ob.tipo] ?? "📌"}</span>
                  <div className="flex-1">
                    <p className="font-medium">{ob.nombre}</p>
                    <p className="opacity-60 mt-0.5">{ob.dia} de {ob.mes}</p>
                  </div>
                </div>
              ))}
              {stats.proximas_obligaciones.length === 0 && (
                <p className="text-xs text-gray-600 text-center py-4">Sin obligaciones próximas</p>
              )}
            </div>
          </div>

          {/* Acciones rápidas + recientes */}
          <div className="space-y-5">
            {/* Quick actions */}
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
              <h2 className="text-sm font-semibold text-green-200 mb-3">Acciones rápidas</h2>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { href: "/chat",        icon: "💬", label: "Nueva consulta" },
                  { href: "/clientes",    icon: "👥", label: "Mis clientes" },
                  { href: "/calculadoras",icon: "🧮", label: "Calcular ISR" },
                  { href: "/documentos",  icon: "📄", label: "Generar PDF" },
                ].map(a => (
                  <Link key={a.href} href={a.href}
                    className="flex items-center gap-2 px-3 py-2.5 rounded-xl border border-white/8 bg-white/3 text-xs text-gray-300 hover:bg-green-500/8 hover:border-green-500/20 hover:text-green-300 transition-all">
                    <span className="text-base">{a.icon}</span>
                    {a.label}
                  </Link>
                ))}
              </div>
            </div>

            {/* Conversaciones recientes */}
            <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-green-200">Consultas recientes</h2>
                <Link href="/chat" className="text-xs text-gray-500 hover:text-green-400 transition-colors">
                  Nueva →
                </Link>
              </div>
              {stats.conversaciones_recientes.length === 0 ? (
                <p className="text-xs text-gray-600 text-center py-4">Aún no hay consultas</p>
              ) : (
                <div className="space-y-1.5">
                  {stats.conversaciones_recientes.map(c => (
                    <Link key={c.id} href="/chat"
                      className="flex items-center justify-between px-3 py-2 rounded-xl hover:bg-white/5 transition-all group">
                      <span className="text-xs text-gray-400 group-hover:text-green-300 truncate flex-1">{c.titulo}</span>
                      <span className="text-[10px] text-gray-600 ml-2 shrink-0">{c.fecha}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
