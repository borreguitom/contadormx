"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import ResultPanel from "@/components/calculadoras/ResultPanel";

type Tab = "isr_pf" | "isr_pm" | "iva" | "ieps" | "imss" | "nomina" | "finiquito";

const TABS: { id: Tab; icon: string; label: string }[] = [
  { id: "isr_pf",    icon: "👤", label: "ISR PF" },
  { id: "isr_pm",    icon: "🏢", label: "ISR PM" },
  { id: "iva",       icon: "🧾", label: "IVA" },
  { id: "ieps",      icon: "🏭", label: "IEPS" },
  { id: "imss",      icon: "🏥", label: "IMSS / INFONAVIT" },
  { id: "nomina",    icon: "💵", label: "Nómina" },
  { id: "finiquito", icon: "📄", label: "Finiquito" },
];

// ── Helpers ──────────────────────────────────────────────────────────────────

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-gray-400 mb-1 uppercase tracking-wide">{label}</label>
      {children}
    </div>
  );
}

function NumInput({ value, onChange, placeholder = "0", step = "any" }: {
  value: string; onChange: (v: string) => void; placeholder?: string; step?: string;
}) {
  return (
    <input type="number" value={value} step={step} onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-green-50 focus:outline-none focus:border-green-500/40 placeholder:text-gray-600" />
  );
}

function Sel({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-green-50 focus:outline-none focus:border-green-500/40">
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

function CalcBtn({ loading, onClick }: { loading: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-50 mt-1">
      {loading ? "Calculando…" : "Calcular"}
    </button>
  );
}

// ── Formularios ───────────────────────────────────────────────────────────────

function ISRPFForm({ onResult, loading, setLoading, setError }: FormProps) {
  const [ingresos, setIngresos] = useState("30000");
  const [regimen, setRegimen] = useState("sueldos");
  const [deducciones, setDeducciones] = useState("0");
  const [periodo, setPeriodo] = useState("mensual");

  const calc = async () => {
    setLoading(true); setError("");
    try {
      onResult(await api.calc.isrPF({ ingresos_mensuales: +ingresos, regimen, deducciones_mensuales: +deducciones, periodo }));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 bg-white/3 rounded-lg px-3 py-2 border border-white/6">
        Art. 96 LISR (sueldos), Art. 106 LISR (honorarios/act. empresariales), Art. 116 LISR (arrendamiento), Art. 113-E LISR (RESICO PF)
      </div>
      <Field label="Ingresos del periodo ($)">
        <NumInput value={ingresos} onChange={setIngresos} />
      </Field>
      <Field label="Régimen">
        <Sel value={regimen} onChange={setRegimen}
          options={["sueldos", "honorarios", "actividades_empresariales", "arrendamiento", "resico_pf"]} />
      </Field>
      <Field label="Deducciones autorizadas ($)">
        <NumInput value={deducciones} onChange={setDeducciones} />
      </Field>
      <Field label="Periodo">
        <Sel value={periodo} onChange={setPeriodo} options={["mensual", "anual"]} />
      </Field>
      <CalcBtn loading={loading} onClick={calc} />
    </div>
  );
}

function ISRPMForm({ onResult, loading, setLoading, setError }: FormProps) {
  const [ingresos, setIngresos] = useState("500000");
  const [cu, setCu] = useState("0.20");
  const [previos, setPrevios] = useState("0");
  const [mes, setMes] = useState("1");
  const [regimen, setRegimen] = useState("general");

  const calc = async () => {
    setLoading(true); setError("");
    try {
      onResult(await api.calc.isrPM({ ingresos_acumulados: +ingresos, coeficiente_utilidad: +cu, pagos_provisionales_previos: +previos, mes: +mes, regimen }));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 bg-white/3 rounded-lg px-3 py-2 border border-white/6">
        Art. 14 LISR (régimen general — pagos provisionales), Art. 196 LISR (RESICO PM — 1%)
      </div>
      <Field label="Ingresos acumulados enero–mes ($)"><NumInput value={ingresos} onChange={setIngresos} /></Field>
      <Field label="Coeficiente de utilidad"><NumInput value={cu} onChange={setCu} step="0.0001" /></Field>
      <Field label="Pagos provisionales previos ($)"><NumInput value={previos} onChange={setPrevios} /></Field>
      <Field label="Mes (1–12)">
        <Sel value={mes} onChange={setMes} options={["1","2","3","4","5","6","7","8","9","10","11","12"]} />
      </Field>
      <Field label="Régimen">
        <Sel value={regimen} onChange={setRegimen} options={["general", "resico_pm"]} />
      </Field>
      <CalcBtn loading={loading} onClick={calc} />
    </div>
  );
}

function IVAForm({ onResult, loading, setLoading, setError }: FormProps) {
  const [v16, setV16] = useState("100000");
  const [v0, setV0] = useState("0");
  const [vEx, setVEx] = useState("0");
  const [c16, setC16] = useState("50000");
  const [saldo, setSaldo] = useState("0");

  const calc = async () => {
    setLoading(true); setError("");
    try {
      onResult(await api.calc.iva({ ventas_16: +v16, ventas_0: +v0, ventas_exentas: +vEx, compras_16_acreditables: +c16, saldo_favor_anterior: +saldo }));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 bg-white/3 rounded-lg px-3 py-2 border border-white/6">
        Art. 1 LIVA (16%), Art. 2-A LIVA (tasa 0%), Art. 5 LIVA (acreditamiento), Art. 5-C LIVA (proporcionalidad)
      </div>
      <Field label="Ventas gravadas 16% ($)"><NumInput value={v16} onChange={setV16} /></Field>
      <Field label="Ventas tasa 0% ($)"><NumInput value={v0} onChange={setV0} /></Field>
      <Field label="Ventas exentas ($)"><NumInput value={vEx} onChange={setVEx} /></Field>
      <Field label="Compras/gastos acreditables 16% ($)"><NumInput value={c16} onChange={setC16} /></Field>
      <Field label="Saldo a favor anterior ($)"><NumInput value={saldo} onChange={setSaldo} /></Field>
      <CalcBtn loading={loading} onClick={calc} />
    </div>
  );
}

const IEPS_CATEGORIAS: { value: string; label: string; tipo: "ad_valorem" | "cuota_litro" | "ad_valorem_mas_cuota" }[] = [
  { value: "bebidas_alcoholicas_hasta_14gl",  label: "Bebidas alcohólicas ≤14° GL (cerveza, vino) — 26.5%", tipo: "ad_valorem" },
  { value: "bebidas_alcoholicas_mas_20gl",    label: "Bebidas alcohólicas >20° GL (destilados) — 53%",      tipo: "ad_valorem" },
  { value: "alcohol_desnaturalizado",         label: "Alcohol / alcohol desnaturalizado — 50%",             tipo: "ad_valorem" },
  { value: "tabacos_cigarros",                label: "Cigarros y tabacos — 160% + $0.35/cigarro",           tipo: "ad_valorem_mas_cuota" },
  { value: "tabacos_puros",                   label: "Puros hechos a mano — 30.6%",                         tipo: "ad_valorem" },
  { value: "bebidas_energizantes",            label: "Bebidas energizantes — 25%",                          tipo: "ad_valorem" },
  { value: "bebidas_azucaradas",              label: "Bebidas azucaradas — $1.46/litro",                    tipo: "cuota_litro" },
  { value: "alimentos_hcnc",                  label: "Alimentos alta densidad calórica (≥275 kcal/100g) — 8%", tipo: "ad_valorem" },
  { value: "plaguicidas_clase_1",             label: "Plaguicidas Clase I — 9%",                            tipo: "ad_valorem" },
  { value: "plaguicidas_clase_2",             label: "Plaguicidas Clase II — 7%",                           tipo: "ad_valorem" },
  { value: "plaguicidas_clase_3_4",           label: "Plaguicidas Clase III-IV — 6%",                       tipo: "ad_valorem" },
  { value: "juegos_sorteos",                  label: "Juegos con apuestas y sorteos — 30%",                 tipo: "ad_valorem" },
  { value: "combustibles_gasolina_magna",     label: "Gasolina Magna — $5.95/litro",                       tipo: "cuota_litro" },
  { value: "combustibles_gasolina_premium",   label: "Gasolina Premium — $5.75/litro",                     tipo: "cuota_litro" },
  { value: "combustibles_diesel",             label: "Diésel — $6.24/litro",                               tipo: "cuota_litro" },
];

function IEPSForm({ onResult, loading, setLoading, setError }: FormProps) {
  const [categoria, setCategoria] = useState(IEPS_CATEGORIAS[0].value);
  const [base, setBase] = useState("10000");
  const [litros, setLitros] = useState("100");
  const [cigarros, setCigarros] = useState("0");
  const [conIva, setConIva] = useState(false);

  const catActual = IEPS_CATEGORIAS.find(c => c.value === categoria)!;

  const calc = async () => {
    setLoading(true); setError("");
    try {
      onResult(await api.calc.ieps({
        categoria,
        base_gravable: +base,
        litros: +litros,
        cantidad_cigarros: +cigarros,
        incluye_iva: conIva,
      }));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 bg-white/3 rounded-lg px-3 py-2 border border-white/6">
        Art. 2 LIEPS — tasas 2025. El IEPS integra la base para IVA (Art. 18 LIVA).
      </div>
      <Field label="Categoría">
        <select value={categoria} onChange={e => setCategoria(e.target.value)}
          className="w-full border border-white/10 rounded-xl px-3 py-2 text-sm text-green-50 focus:outline-none focus:border-green-500/40"
          style={{ backgroundColor: "#0d1a0d" }}>
          {IEPS_CATEGORIAS.map(c => (
            <option key={c.value} value={c.value} style={{ backgroundColor: "#0d1a0d", color: "#fff" }}>{c.label}</option>
          ))}
        </select>
      </Field>

      {(catActual.tipo === "ad_valorem" || catActual.tipo === "ad_valorem_mas_cuota") && (
        <Field label="Precio de enajenación sin IEPS ($)">
          <NumInput value={base} onChange={setBase} />
        </Field>
      )}
      {catActual.tipo === "cuota_litro" && (
        <Field label="Litros enajenados">
          <NumInput value={litros} onChange={setLitros} />
        </Field>
      )}
      {catActual.tipo === "ad_valorem_mas_cuota" && (
        <Field label="Cantidad de cigarros">
          <NumInput value={cigarros} onChange={setCigarros} step="1" />
        </Field>
      )}

      <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer select-none">
        <input type="checkbox" checked={conIva} onChange={e => setConIva(e.target.checked)}
          className="accent-green-500 w-3.5 h-3.5" />
        Incluir IVA 16% sobre (precio + IEPS)
      </label>

      <CalcBtn loading={loading} onClick={calc} />
    </div>
  );
}

function IMSSForm({ onResult, loading, setLoading, setError }: FormProps) {
  const [sdi, setSdi] = useState("500");
  const [prima, setPrima] = useState("0.0054355");

  const calc = async () => {
    setLoading(true); setError("");
    try {
      onResult(await api.calc.imss({ salario_diario_integrado: +sdi, prima_riesgo_trabajo: +prima }));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 bg-white/3 rounded-lg px-3 py-2 border border-white/6">
        Art. 25-168 LSS — cuotas obrero-patronales. Art. 29 Ley INFONAVIT. UMA 2025: $113.14/día.
      </div>
      <Field label="Salario Diario Integrado — SDI ($)">
        <NumInput value={sdi} onChange={setSdi} />
      </Field>
      <Field label="Prima riesgo trabajo (default 0.54355%)">
        <NumInput value={prima} onChange={setPrima} step="0.0001" />
      </Field>
      <div className="text-xs text-gray-600 bg-white/3 rounded-lg px-3 py-2">
        SDI = (salario base + partes prop. aguinaldo + partes prop. vacaciones) ÷ 30
      </div>
      <CalcBtn loading={loading} onClick={calc} />
    </div>
  );
}

function NominaForm({ onResult, loading, setLoading, setError }: FormProps) {
  const [salario, setSalario] = useState("20000");
  const [periodo, setPeriodo] = useState("mensual");
  const [otras, setOtras] = useState("0");
  const [vales, setVales] = useState("0");

  const calc = async () => {
    setLoading(true); setError("");
    try {
      onResult(await api.calc.nomina({ salario_mensual_bruto: +salario, periodo, otras_percepciones: +otras, vales_despensa: +vales }));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 bg-white/3 rounded-lg px-3 py-2 border border-white/6">
        Nómina completa: ISR Art. 96 LISR + subsidio al empleo + IMSS obrero Art. 25 LSS + integración SDI Art. 27 LSS
      </div>
      <Field label="Salario mensual bruto ($)"><NumInput value={salario} onChange={setSalario} /></Field>
      <Field label="Periodo">
        <Sel value={periodo} onChange={setPeriodo} options={["semanal", "catorcenal", "quincenal", "mensual"]} />
      </Field>
      <Field label="Otras percepciones (bonos, comisiones) ($)"><NumInput value={otras} onChange={setOtras} /></Field>
      <Field label="Vales de despensa ($)"><NumInput value={vales} onChange={setVales} /></Field>
      <CalcBtn loading={loading} onClick={calc} />
    </div>
  );
}

function FiniquitoForm({ onResult, loading, setLoading, setError }: FormProps) {
  const [sd, setSd] = useState("500");
  const [dias, setDias] = useState("180");
  const [anios, setAnios] = useState("2");
  const [tipo, setTipo] = useState("renuncia");
  const [vacGozadas, setVacGozadas] = useState("0");

  const calc = async () => {
    setLoading(true); setError("");
    try {
      onResult(await api.calc.finiquito({ salario_diario: +sd, dias_trabajados_anio: +dias, anios_servicio: +anios, tipo_separacion: tipo, vacaciones_gozadas: +vacGozadas }));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 bg-white/3 rounded-lg px-3 py-2 border border-white/6">
        Art. 76, 80, 87 LFT (vacaciones, prima vacacional, aguinaldo). Art. 50 LFT (3 meses + 20 días). Art. 162 LFT (prima antigüedad).
      </div>
      <Field label="Salario diario ($)"><NumInput value={sd} onChange={setSd} /></Field>
      <Field label="Días trabajados en el año"><NumInput value={dias} onChange={setDias} step="1" /></Field>
      <Field label="Años de antigüedad"><NumInput value={anios} onChange={setAnios} step="0.5" /></Field>
      <Field label="Tipo de separación">
        <Sel value={tipo} onChange={setTipo}
          options={["renuncia", "despido_injustificado", "despido_justificado", "mutuo_acuerdo"]} />
      </Field>
      <Field label="Vacaciones ya gozadas (días)"><NumInput value={vacGozadas} onChange={setVacGozadas} step="1" /></Field>
      <CalcBtn loading={loading} onClick={calc} />
    </div>
  );
}

interface FormProps {
  onResult: (r: Record<string, unknown>) => void;
  loading: boolean;
  setLoading: (v: boolean) => void;
  setError: (v: string) => void;
}

const FORMS: Record<Tab, React.ComponentType<FormProps>> = {
  isr_pf: ISRPFForm,
  isr_pm: ISRPMForm,
  iva: IVAForm,
  ieps: IEPSForm,
  imss: IMSSForm,
  nomina: NominaForm,
  finiquito: FiniquitoForm,
};

// ── Página principal ──────────────────────────────────────────────────────────

export default function CalculadorasPage() {
  const [tab, setTab] = useState<Tab>("isr_pf");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onTabChange = (t: Tab) => { setTab(t); setResult(null); setError(""); };

  const Form = FORMS[tab];

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-5">
          <h1 className="text-xl font-bold text-green-100">Calculadoras Fiscales</h1>
          <p className="text-sm text-gray-500 mt-0.5">Tablas vigentes 2025 — ISR, IVA, IEPS, IMSS, INFONAVIT, LFT</p>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-1.5 mb-6">
          {TABS.map(t => (
            <button key={t.id} onClick={() => onTabChange(t.id)}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm transition-all ${
                tab === t.id
                  ? "bg-green-500/15 text-green-300 border border-green-500/30"
                  : "bg-white/3 text-gray-400 border border-white/8 hover:bg-white/6 hover:text-green-200"
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Formulario */}
          <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
            <h2 className="text-sm font-semibold text-green-200 mb-4">
              {TABS.find(t => t.id === tab)?.icon}{" "}
              {TABS.find(t => t.id === tab)?.label}
            </h2>
            <Form
              onResult={r => { setResult(r); setError(""); }}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
            />
          </div>

          {/* Resultado */}
          <div className="rounded-2xl border border-white/8 bg-white/3 p-5">
            <h2 className="text-sm font-semibold text-green-200 mb-4">Resultado</h2>
            <ResultPanel data={result} loading={loading} error={error} />
          </div>
        </div>
      </div>
    </div>
  );
}
