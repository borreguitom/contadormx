"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { SelectInput } from "@/components/ui/SelectInput";
import { useRouter } from "next/navigation";

interface DecResult {
  total_ingresos_acumulables: number;
  deducciones_aplicables: number;
  limite_deducciones: number;
  total_deducciones_declaradas: number;
  base_gravable: number;
  isr_del_ejercicio: number;
  retenciones_sueldos: number;
  pagos_provisionales: number;
  subsidio_empleo_acreditado: number;
  total_acreditable: number;
  saldo_cargo: number;
  saldo_favor: number;
  resultado: "cargo" | "favor" | "equilibrio";
  tasa_efectiva: number;
  regimen_predominante: string;
  fundamento: string;
}

const fmt = (n: number) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(n);

const pct = (n: number) => `${n.toFixed(2)}%`;

const NIVELES = [
  { value: "preescolar", label: "Preescolar ($14,200)" },
  { value: "primaria", label: "Primaria ($12,900)" },
  { value: "secundaria", label: "Secundaria ($19,900)" },
  { value: "preparatoria", label: "Preparatoria / Bachillerato ($24,500)" },
  { value: "profesional_tecnico", label: "Profesional técnico ($17,100)" },
];

function Field({
  label, name, value, onChange, hint,
}: {
  label: string; name: string; value: string;
  onChange: (n: string, v: string) => void; hint?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
      <input
        type="number"
        min={0}
        step={0.01}
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        placeholder="0.00"
        className="w-full border border-white/10 bg-white/5 text-gray-200 rounded-lg px-3 py-2 text-sm
                   placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
      />
      {hint && <p className="text-xs text-gray-500 mt-0.5">{hint}</p>}
    </div>
  );
}

const EMPTY = {
  ingresos_sueldos: "",
  ingresos_honorarios: "",
  ingresos_arrendamiento: "",
  ingresos_actividad_empresarial: "",
  ingresos_intereses: "",
  ingresos_dividendos: "",
  ingresos_otros: "",
  retenciones_sueldos: "",
  pagos_provisionales: "",
  subsidio_empleo_acreditado: "",
  deducciones_medicas: "",
  gastos_hospitalarios: "",
  primas_gmm: "",
  intereses_hipotecarios_reales: "",
  donativos: "",
  aportaciones_afore: "",
  colegiaturas: "",
  nivel_educativo: "preparatoria",
};

export default function DeclaracionAnualPage() {
  const router = useRouter();
  const [form, setForm] = useState<typeof EMPTY>(EMPTY);
  const [result, setResult] = useState<DecResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (name: string, value: string) =>
    setForm((prev) => ({ ...prev, [name]: value }));

  const num = (v: string) => parseFloat(v) || 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await api.calc.declaracionAnualPF({
        ingresos_sueldos: num(form.ingresos_sueldos),
        ingresos_honorarios: num(form.ingresos_honorarios),
        ingresos_arrendamiento: num(form.ingresos_arrendamiento),
        ingresos_actividad_empresarial: num(form.ingresos_actividad_empresarial),
        ingresos_intereses: num(form.ingresos_intereses),
        ingresos_dividendos: num(form.ingresos_dividendos),
        ingresos_otros: num(form.ingresos_otros),
        retenciones_sueldos: num(form.retenciones_sueldos),
        pagos_provisionales: num(form.pagos_provisionales),
        subsidio_empleo_acreditado: num(form.subsidio_empleo_acreditado),
        deducciones_medicas: num(form.deducciones_medicas),
        gastos_hospitalarios: num(form.gastos_hospitalarios),
        primas_gmm: num(form.primas_gmm),
        intereses_hipotecarios_reales: num(form.intereses_hipotecarios_reales),
        donativos: num(form.donativos),
        aportaciones_afore: num(form.aportaciones_afore),
        colegiaturas: num(form.colegiaturas),
        nivel_educativo: form.nivel_educativo,
      });
      setResult(data as DecResult);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al calcular");
    } finally {
      setLoading(false);
    }
  };

  const sendToAgent = () => {
    if (!result) return;
    const ctx = `Declaración Anual PF — Ejercicio fiscal
Ingresos acumulables: ${fmt(result.total_ingresos_acumulables)}
Deducciones personales aplicadas: ${fmt(result.deducciones_aplicables)}
Base gravable: ${fmt(result.base_gravable)}
ISR del ejercicio: ${fmt(result.isr_del_ejercicio)}
Total acreditable (retenciones + pagos prov.): ${fmt(result.total_acreditable)}
Resultado: ${result.resultado === "cargo" ? "SALDO A CARGO" : result.resultado === "favor" ? "SALDO A FAVOR" : "EQUILIBRADO"}
${result.saldo_cargo > 0 ? `Monto a pagar: ${fmt(result.saldo_cargo)}` : `Devolución: ${fmt(result.saldo_favor)}`}
Tasa efectiva: ${pct(result.tasa_efectiva)}
Fundamento: ${result.fundamento}`;
    localStorage.setItem("cmx_doc_ctx", ctx);
    router.push("/chat?doc=decl-anual");
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-green-100">Declaración Anual — Personas Físicas</h1>
        <p className="text-sm text-gray-500 mt-1">
          Art. 150-152 LISR · Vencimiento: <strong>30 de abril</strong> · Tarifa anual 2026
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* Ingresos */}
          <div className="rounded-xl border border-white/8 bg-white/3 p-5 space-y-4">
            <h2 className="font-semibold text-green-200 flex items-center gap-2">
              <span className="text-green-400">↑</span> Ingresos acumulables (anuales)
            </h2>
            <Field label="Sueldos y salarios" name="ingresos_sueldos" value={form.ingresos_sueldos} onChange={set} hint="Total bruto recibido del empleador" />
            <Field label="Honorarios (servicios profesionales)" name="ingresos_honorarios" value={form.ingresos_honorarios} onChange={set} />
            <Field label="Arrendamiento de inmuebles" name="ingresos_arrendamiento" value={form.ingresos_arrendamiento} onChange={set} />
            <Field label="Actividad empresarial" name="ingresos_actividad_empresarial" value={form.ingresos_actividad_empresarial} onChange={set} />
            <Field label="Intereses reales acumulables" name="ingresos_intereses" value={form.ingresos_intereses} onChange={set} />
            <Field label="Dividendos" name="ingresos_dividendos" value={form.ingresos_dividendos} onChange={set} />
            <Field label="Otros ingresos" name="ingresos_otros" value={form.ingresos_otros} onChange={set} />
          </div>

          {/* Retenciones y pagos provisionales */}
          <div className="space-y-6">
            <div className="rounded-xl border border-white/8 bg-white/3 p-5 space-y-4">
              <h2 className="font-semibold text-green-200 flex items-center gap-2">
                <span className="text-blue-400">−</span> Retenciones y pagos provisionales
              </h2>
              <Field label="ISR retenido por empleador" name="retenciones_sueldos" value={form.retenciones_sueldos} onChange={set} hint="Del recibo de nómina anual" />
              <Field label="Pagos provisionales enterados" name="pagos_provisionales" value={form.pagos_provisionales} onChange={set} hint="Honorarios, arrendamiento, etc." />
              <Field label="Subsidio al empleo acreditado" name="subsidio_empleo_acreditado" value={form.subsidio_empleo_acreditado} onChange={set} />
            </div>

            {/* Deducciones personales */}
            <div className="rounded-xl border border-white/8 bg-white/3 p-5 space-y-4">
              <h2 className="font-semibold text-green-200 flex items-center gap-2">
                <span className="text-purple-400">−</span> Deducciones personales (Art. 151 LISR)
                <span className="text-xs text-gray-500 font-normal">Límite: 15% ingreso o 5 UMA anuales</span>
              </h2>
              <Field label="Honorarios médicos / dentista / psicólogo" name="deducciones_medicas" value={form.deducciones_medicas} onChange={set} hint="Requiere CFDI" />
              <Field label="Gastos hospitalarios y medicamentos" name="gastos_hospitalarios" value={form.gastos_hospitalarios} onChange={set} hint="Requiere CFDI" />
              <Field label="Prima de seguro de gastos médicos (GMM)" name="primas_gmm" value={form.primas_gmm} onChange={set} />
              <Field label="Intereses reales de crédito hipotecario" name="intereses_hipotecarios_reales" value={form.intereses_hipotecarios_reales} onChange={set} hint="Constancia del banco" />
              <Field label="Donativos a instituciones autorizadas" name="donativos" value={form.donativos} onChange={set} hint="Máx. 7% del ingreso total" />
              <Field label="Aportaciones voluntarias AFORE/SAR" name="aportaciones_afore" value={form.aportaciones_afore} onChange={set} hint="Máx. 10% del ingreso o 5 UMA anuales" />
              <Field label="Colegiaturas" name="colegiaturas" value={form.colegiaturas} onChange={set} />
              <div>
                <label className="block text-xs font-medium text-gray-400 mb-1">Nivel educativo</label>
                <SelectInput
                  value={form.nivel_educativo}
                  onChange={v => set("nivel_educativo", v)}
                  options={NIVELES}
                  className="!rounded-lg"
                />
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-800/40 text-red-300 rounded-lg px-4 py-3 text-sm">{error}</div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-green-700 hover:bg-green-600 disabled:opacity-50 text-white
                     py-3 rounded-xl font-semibold text-sm transition-colors"
        >
          {loading ? "Calculando..." : "Calcular Declaración Anual"}
        </button>
      </form>

      {/* Resultado */}
      {result && (
        <div className="space-y-4">
          {/* Resultado principal */}
          <div className={`rounded-xl border-2 p-6 text-center ${
            result.resultado === "cargo"
              ? "border-red-800/50 bg-red-900/20"
              : result.resultado === "favor"
              ? "border-green-800/50 bg-green-900/20"
              : "border-white/10 bg-white/5"
          }`}>
            <p className="text-sm font-medium text-gray-400 uppercase tracking-wide mb-1">
              {result.resultado === "cargo" ? "Saldo a cargo — debes pagar" :
               result.resultado === "favor" ? "Saldo a favor — devolución o compensación" :
               "Declaración en ceros"}
            </p>
            <p className={`text-4xl font-black ${
              result.resultado === "cargo" ? "text-red-400" :
              result.resultado === "favor" ? "text-green-400" : "text-gray-300"
            }`}>
              {result.resultado === "cargo" ? fmt(result.saldo_cargo) :
               result.resultado === "favor" ? fmt(result.saldo_favor) : "$0.00"}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Tasa efectiva de ISR: {pct(result.tasa_efectiva)} · Régimen predominante: {result.regimen_predominante}
            </p>
          </div>

          {/* Desglose */}
          <div className="rounded-xl border border-white/8 bg-white/3 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/8">
                  <th className="px-5 py-3 text-left text-xs text-gray-500 uppercase font-medium">Concepto</th>
                  <th className="px-5 py-3 text-right text-xs text-gray-500 uppercase font-medium">Importe</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {[
                  ["Total ingresos acumulables", result.total_ingresos_acumulables, ""],
                  ["(−) Deducciones personales aplicadas", result.deducciones_aplicables, result.total_deducciones_declaradas > result.limite_deducciones ? `Límite ${fmt(result.limite_deducciones)}` : ""],
                  ["= Base gravable", result.base_gravable, "bold"],
                  ["ISR del ejercicio (tarifa Art. 152)", result.isr_del_ejercicio, ""],
                  ["(−) Retenciones por sueldos", result.retenciones_sueldos, ""],
                  ["(−) Pagos provisionales", result.pagos_provisionales, ""],
                  ["(−) Subsidio al empleo", result.subsidio_empleo_acreditado, ""],
                  ["= " + (result.resultado === "cargo" ? "Impuesto a pagar" : "Saldo a favor"),
                   result.resultado === "cargo" ? result.saldo_cargo : result.saldo_favor, "bold"],
                ].map(([label, value, extra], i) => (
                  <tr key={i} className={String(extra) === "bold" ? "bg-white/3" : ""}>
                    <td className={`px-5 py-3 text-gray-400 ${String(extra) === "bold" ? "font-semibold text-gray-200" : ""}`}>
                      {String(label)}
                      {extra && extra !== "bold" && (
                        <span className="ml-2 text-xs text-orange-400">{String(extra)}</span>
                      )}
                    </td>
                    <td className={`px-5 py-3 text-right font-mono ${String(extra) === "bold" ? "font-bold text-green-200" : "text-gray-300"}`}>
                      {fmt(Number(value))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-xs text-gray-500 px-1">{result.fundamento}</p>

          <button
            onClick={sendToAgent}
            className="w-full border border-green-800/40 text-green-400 hover:bg-green-500/8
                       py-3 rounded-xl font-medium text-sm transition-colors"
          >
            💬 Analizar con el agente fiscal
          </button>
        </div>
      )}
    </div>
  );
}
