"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

interface BillingStatus {
  plan: string;
  queries_used: number;
  queries_limit: number;
  clientes_limit: number;
  stripe_customer_id: string | null;
}

const PLANS = [
  {
    id: "free",
    nombre: "Free",
    precio: "$0",
    periodo: "",
    color: "border-white/12",
    badge: "",
    features: [
      "5 clientes",
      "50 consultas al mes",
      "Calculadoras fiscales",
      "Validador CFDI",
      "Calendario fiscal",
    ],
    disabled: ["RAG legislación avanzado", "Generación de documentos PDF", "Soporte prioritario"],
  },
  {
    id: "pro",
    nombre: "Pro",
    precio: "$499",
    periodo: "/ mes MXN",
    color: "border-green-500/35",
    badge: "Más popular",
    features: [
      "50 clientes",
      "1,000 consultas al mes",
      "Todo lo del plan Free",
      "RAG legislación completo",
      "Generación de documentos PDF",
      "Búsqueda web en consultas",
    ],
    disabled: ["Soporte prioritario"],
  },
  {
    id: "agencia",
    nombre: "Agencia",
    precio: "$999",
    periodo: "/ mes MXN",
    color: "border-purple-500/25",
    badge: "Para despachos",
    features: [
      "Clientes ilimitados",
      "Consultas ilimitadas",
      "Todo lo del plan Pro",
      "Soporte prioritario",
      "Onboarding personalizado",
      "API access (próximamente)",
    ],
    disabled: [],
  },
];

export default function BillingPage() {
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);

  const success = searchParams.get("success");
  const canceled = searchParams.get("canceled");

  useEffect(() => {
    api.billing.status()
      .then(setStatus)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const upgrade = async (planId: string) => {
    setCheckoutLoading(planId);
    try {
      const data = await api.billing.checkout(planId);
      window.location.href = data.checkout_url;
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Error al procesar pago");
    } finally {
      setCheckoutLoading(null);
    }
  };

  const openPortal = async () => {
    setPortalLoading(true);
    try {
      const data = await api.billing.portal();
      window.location.href = data.portal_url;
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Error al abrir portal");
    } finally {
      setPortalLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-green-100">Facturación</h1>
          <p className="text-sm text-gray-500 mt-0.5">Planes y suscripciones — ContadorMX</p>
        </div>

        {/* Banners de estado */}
        {success === "1" && (
          <div className="mb-5 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-300">
            ✅ Suscripción activada. Bienvenido al plan Pro.
          </div>
        )}
        {canceled === "1" && (
          <div className="mb-5 rounded-xl border border-yellow-500/25 bg-yellow-500/8 px-4 py-3 text-sm text-yellow-300">
            Pago cancelado. Tu plan no cambió.
          </div>
        )}

        {/* Plan actual */}
        {!loading && status && (
          <div className="rounded-2xl border border-white/8 bg-white/3 p-5 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">Plan actual</p>
                <p className="text-lg font-bold text-green-100 capitalize">{status.plan}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {status.queries_used} / {status.queries_limit === -1 ? "∞" : status.queries_limit} consultas este mes
                </p>
              </div>
              {status.stripe_customer_id && (
                <button onClick={openPortal} disabled={portalLoading}
                  className="text-xs px-4 py-2 rounded-xl border border-white/12 bg-white/4 text-gray-300 hover:text-green-300 hover:border-green-500/25 transition-all disabled:opacity-50">
                  {portalLoading ? "Cargando…" : "Gestionar suscripción →"}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Pricing cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {PLANS.map(plan => {
            const isCurrent = status?.plan === plan.id;
            const isLoading = checkoutLoading === plan.id;

            return (
              <div key={plan.id}
                className={`rounded-2xl border p-6 flex flex-col ${plan.color} ${isCurrent ? "bg-green-500/5" : "bg-white/3"}`}>
                {/* Badge */}
                {plan.badge && (
                  <span className="self-start text-[10px] px-2 py-0.5 rounded-full bg-green-500/15 border border-green-500/25 text-green-400 uppercase tracking-wide mb-3">
                    {plan.badge}
                  </span>
                )}

                <h3 className="text-lg font-bold text-green-100">{plan.nombre}</h3>
                <div className="flex items-baseline gap-1 mt-1 mb-4">
                  <span className="text-2xl font-bold text-green-200">{plan.precio}</span>
                  <span className="text-xs text-gray-500">{plan.periodo}</span>
                </div>

                {/* Features */}
                <div className="flex-1 space-y-2 mb-6">
                  {plan.features.map(f => (
                    <div key={f} className="flex items-center gap-2 text-xs text-gray-300">
                      <span className="text-green-400">✓</span> {f}
                    </div>
                  ))}
                  {plan.disabled.map(f => (
                    <div key={f} className="flex items-center gap-2 text-xs text-gray-600">
                      <span>✗</span> {f}
                    </div>
                  ))}
                </div>

                {/* CTA */}
                {isCurrent ? (
                  <div className="w-full py-2.5 rounded-xl border border-green-500/25 text-center text-sm text-green-400 bg-green-500/8">
                    Plan actual
                  </div>
                ) : plan.id === "free" ? (
                  <div className="w-full py-2.5 rounded-xl border border-white/8 text-center text-sm text-gray-500">
                    Plan gratuito
                  </div>
                ) : (
                  <button onClick={() => upgrade(plan.id)} disabled={!!checkoutLoading}
                    className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-50">
                    {isLoading ? "Redirigiendo…" : `Actualizar a ${plan.nombre} →`}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <p className="text-xs text-gray-600 text-center mt-6">
          Precios en MXN. Facturación mensual. Cancela cuando quieras desde el portal de Stripe.
        </p>
      </div>
    </div>
  );
}
