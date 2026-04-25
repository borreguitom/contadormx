"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";

const NAV = [
  { href: "/dashboard",          icon: "🏠", label: "Dashboard" },
  { href: "/chat",               icon: "💬", label: "Consulta" },
  { href: "/clientes",           icon: "👥", label: "Clientes" },
  { href: "/calculadoras",       icon: "🧮", label: "Calculadoras" },
  { href: "/declaracion-anual",  icon: "📑", label: "Declaración Anual" },
  { href: "/cfdi",               icon: "🧾", label: "Validador CFDI" },
  { href: "/calendario",         icon: "📅", label: "Calendario Fiscal" },
  { href: "/documentos",         icon: "📄", label: "Documentos" },
  { href: "/nomina",             icon: "💰", label: "Nómina" },
  { href: "/sat",                icon: "🏛️", label: "Descarga SAT" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();
  const [plan, setPlan] = useState<string>("free");

  useEffect(() => {
    api.billing.status().then(s => setPlan(s.plan)).catch(() => {});
  }, []);

  return (
    <aside className="w-56 shrink-0 flex flex-col border-r border-white/8 bg-gradient-to-b from-green-950/60 to-black/40">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-white/8">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-800 to-green-500 flex items-center justify-center text-sm shadow shadow-green-900/50">
          🏛️
        </div>
        <div>
          <div className="text-sm font-bold text-green-100 tracking-wide">ContadorMX</div>
          <div className="text-[10px] text-green-500 tracking-widest uppercase">Agente Fiscal</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5">
        {NAV.map(({ href, icon, label }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all ${
                active
                  ? "bg-green-500/15 text-green-300 border border-green-500/25"
                  : "text-gray-400 hover:bg-white/5 hover:text-green-200"
              }`}
            >
              <span className="text-base">{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 py-3 border-t border-white/8 space-y-1">
        {plan === "free" && (
          <Link href="/billing"
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-green-400 bg-green-500/8 border border-green-500/20 hover:bg-green-500/15 transition-all">
            <span>⚡</span> Actualizar plan
          </Link>
        )}
        <Link href="/billing"
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-all capitalize">
          <span>💳</span> {plan}
        </Link>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-500 hover:text-red-400 hover:bg-red-500/8 transition-all"
        >
          <span>↩</span> Salir
        </button>
      </div>
    </aside>
  );
}
