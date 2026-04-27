"use client";
/**
 * CalculadorasFiscales — Hub para ISR, IVA, IEPS, IMSS
 * =====================================================
 * Componente único con tabs para todas las calculadoras fiscales
 * (excepto nómina y finiquito que tienen su propio componente).
 */
import { useState, useEffect } from "react";
import {
  calcApi, MXN, type RegimenISRPF, type IEPSCategoria, type RespuestaCalculo,
} from "@/lib/api-calc";

type Tab = "isr-pf" | "isr-pm" | "iva" | "ieps" | "imss";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "isr-pf", label: "ISR Persona Física", icon: "👤" },
  { id: "isr-pm", label: "ISR Persona Moral", icon: "🏢" },
  { id: "iva", label: "IVA", icon: "💵" },
  { id: "ieps", label: "IEPS", icon: "🍷" },
  { id: "imss", label: "IMSS / INFONAVIT", icon: "🏥" },
];

export default function CalculadorasFiscales() {
  const [tab, setTab] = useState<Tab>("isr-pf");

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="text-3xl font-bold">Calculadoras fiscales 2025</h1>
        <p className="text-gray-600 mt-1">Cálculos basados en la legislación mexicana vigente.</p>
      </header>

      <nav className="flex flex-wrap gap-2 border-b">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 border-b-2 transition ${
              tab === t.id ? "border-blue-600 text-blue-700 font-semibold" : "border-transparent hover:border-gray-300"
            }`}
          >
            <span className="mr-2">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>

      <div>
        {tab === "isr-pf" && <ISRPFTab />}
        {tab === "isr-pm" && <ISRPMTab />}
        {tab === "iva" && <IVATab />}
        {tab === "ieps" && <IEPSTab />}
        {tab === "imss" && <IMSSTab />}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// TAB ISR PERSONA FÍSICA
// ════════════════════════════════════════════════════════════════════════

function ISRPFTab() {
  const [ingresos, setIngresos] = useState(20000);
  const [regimen, setRegimen] = useState<RegimenISRPF>("sueldos");
  const [deducciones, setDeducciones] = useState(0);
  const [periodo, setPeriodo] = useState<"mensual" | "anual">("mensual");
  const [resultado, setResultado] = useState<RespuestaCalculo | null>(null);
  const [loading, setLoading] = useState(false);

  const calcular = async () => {
    setLoading(true);
    try {
      const res = await calcApi.isrPf({
        ingresos_mensuales: ingresos,
        regimen,
        deducciones_mensuales: deducciones,
        periodo,
      });
      setResultado(res);
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card title="Datos de entrada">
        <NumberInput label="Ingresos mensuales" value={ingresos} onChange={setIngresos} step={500} />
        <Select label="Régimen" value={regimen} onChange={(v) => setRegimen(v as RegimenISRPF)}
                options={[
                  { value: "sueldos", label: "Sueldos y Salarios" },
                  { value: "honorarios", label: "Honorarios / Actividad Empresarial" },
                  { value: "arrendamiento", label: "Arrendamiento" },
                  { value: "resico_pf", label: "RESICO PF" },
                ]} />
        {(regimen === "honorarios" || regimen === "arrendamiento") && (
          <NumberInput label="Deducciones autorizadas" value={deducciones}
                       onChange={setDeducciones} step={100} />
        )}
        <Select label="Período" value={periodo}
                onChange={(v) => setPeriodo(v as "mensual" | "anual")}
                options={[
                  { value: "mensual", label: "Mensual (provisional)" },
                  { value: "anual", label: "Anual (declaración)" },
                ]} />
        <button onClick={calcular} disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-2 rounded-lg font-medium">
          {loading ? "Calculando..." : "Calcular ISR"}
        </button>
      </Card>

      <Card title="Resultado">
        {!resultado && <Empty />}
        {resultado?.success && (() => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const d = resultado.datos as any;
          return (
            <div className="space-y-3">
              <BigNumber label="ISR a pagar" value={d.isr_a_cargo} />
              <Row label="Base gravable" value={MXN(d.base_gravable)} />
              <Row label="ISR determinado" value={MXN(d.isr_determinado)} />
              {d.subsidio_empleo?.subsidio > 0 && (
                <Row label="Subsidio empleo" value={`-${MXN(d.subsidio_empleo.subsidio)}`} />
              )}
              <Row label="Tasa efectiva" value={`${d.tasa_efectiva_pct}%`} />
              <FundamentoBox legal={resultado.fundamento_legal} />
            </div>
          );
        })()}
      </Card>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// TAB ISR PERSONA MORAL
// ════════════════════════════════════════════════════════════════════════

function ISRPMTab() {
  const [ingresos, setIngresos] = useState(500000);
  const [coef, setCoef] = useState(0.20);
  const [mes, setMes] = useState(1);
  const [regimen, setRegimen] = useState<"general" | "resico_pm">("general");
  const [pagosPrev, setPagosPrev] = useState(0);
  const [resultado, setResultado] = useState<RespuestaCalculo | null>(null);
  const [loading, setLoading] = useState(false);

  const calcular = async () => {
    setLoading(true);
    try {
      const res = await calcApi.isrPm({
        ingresos_acumulados: ingresos,
        coeficiente_utilidad: coef,
        mes,
        regimen,
        pagos_provisionales_previos: pagosPrev,
      });
      setResultado(res);
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card title="Datos de entrada">
        <Select label="Régimen" value={regimen}
                onChange={(v) => setRegimen(v as "general" | "resico_pm")}
                options={[
                  { value: "general", label: "Régimen General (30%)" },
                  { value: "resico_pm", label: "RESICO PM (1%)" },
                ]} />
        <NumberInput label="Ingresos acumulados" value={ingresos} onChange={setIngresos} step={1000} />
        {regimen === "general" && (
          <NumberInput label="Coeficiente utilidad (decimal)" value={coef}
                       onChange={setCoef} step={0.01} min={0} max={1} />
        )}
        <NumberInput label="Mes" value={mes} onChange={setMes} step={1} min={1} max={12} />
        <NumberInput label="Pagos provisionales previos" value={pagosPrev}
                     onChange={setPagosPrev} step={100} />
        <button onClick={calcular} disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-2 rounded-lg font-medium">
          {loading ? "Calculando..." : "Calcular ISR PM"}
        </button>
      </Card>

      <Card title="Resultado">
        {!resultado && <Empty />}
        {resultado?.success && (() => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const d = resultado.datos as any;
          return (
            <div className="space-y-3">
              <BigNumber label="Pago provisional a enterar" value={d.pago_provisional_a_enterar} />
              <Row label="Utilidad fiscal estimada" value={MXN(d.utilidad_fiscal_estimada || 0)} />
              <Row label="ISR acumulado determinado" value={MXN(d.isr_acumulado_determinado || d.isr_acumulado || 0)} />
              <Row label="Tasa aplicada" value={`${d.tasa_aplicada_pct || d.tasa_resico_pct}%`} />
              <FundamentoBox legal={resultado.fundamento_legal} />
            </div>
          );
        })()}
      </Card>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// TAB IVA
// ════════════════════════════════════════════════════════════════════════

function IVATab() {
  const [v16, setV16] = useState(50000);
  const [v8, setV8] = useState(0);
  const [v0, setV0] = useState(0);
  const [vEx, setVEx] = useState(0);
  const [c16, setC16] = useState(20000);
  const [c8, setC8] = useState(0);
  const [retenido, setRetenido] = useState(0);
  const [saldoFavor, setSaldoFavor] = useState(0);
  const [resultado, setResultado] = useState<RespuestaCalculo | null>(null);
  const [loading, setLoading] = useState(false);

  const calcular = async () => {
    setLoading(true);
    try {
      const res = await calcApi.iva({
        ventas_16: v16,
        ventas_8_frontera: v8,
        ventas_0: v0,
        ventas_exentas: vEx,
        compras_16_acreditables: c16,
        compras_8_acreditables: c8,
        iva_retenido_por_terceros: retenido,
        saldo_favor_anterior: saldoFavor,
      });
      setResultado(res);
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card title="Ventas y compras del período">
        <h4 className="text-sm font-semibold text-gray-700 mt-2">Ventas (cobradas)</h4>
        <NumberInput label="Ventas tasa 16%" value={v16} onChange={setV16} step={500} />
        <NumberInput label="Ventas frontera 8%" value={v8} onChange={setV8} step={500} />
        <NumberInput label="Ventas tasa 0%" value={v0} onChange={setV0} step={500} />
        <NumberInput label="Ventas exentas" value={vEx} onChange={setVEx} step={500} />

        <h4 className="text-sm font-semibold text-gray-700 mt-4">Compras (pagadas)</h4>
        <NumberInput label="Compras tasa 16%" value={c16} onChange={setC16} step={500} />
        <NumberInput label="Compras frontera 8%" value={c8} onChange={setC8} step={500} />

        <h4 className="text-sm font-semibold text-gray-700 mt-4">Otros</h4>
        <NumberInput label="IVA retenido por terceros" value={retenido} onChange={setRetenido} step={100} />
        <NumberInput label="Saldo a favor anterior" value={saldoFavor} onChange={setSaldoFavor} step={100} />

        <button onClick={calcular} disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-2 rounded-lg font-medium mt-3">
          {loading ? "Calculando..." : "Calcular IVA"}
        </button>
      </Card>

      <Card title="Resultado">
        {!resultado && <Empty />}
        {resultado?.success && (() => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const d = resultado.datos as any;
          return (
            <div className="space-y-3">
              {d.iva_a_cargo > 0 ? (
                <BigNumber label="IVA a cargo" value={d.iva_a_cargo} color="red" />
              ) : (
                <BigNumber label="IVA a favor" value={d.iva_a_favor} color="green" />
              )}
              <Row label="IVA trasladado total" value={MXN(d.iva_trasladado_total)} />
              <Row label="IVA acreditable total" value={MXN(d.iva_acreditable_total)} />
              {d.aplica_proporcionalidad && (
                <Row label="Proporción acreditamiento"
                     value={`${(d.proporcion_acreditamiento * 100).toFixed(2)}%`} />
              )}
              <FundamentoBox legal={resultado.fundamento_legal} />
            </div>
          );
        })()}
      </Card>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// TAB IEPS
// ════════════════════════════════════════════════════════════════════════

function IEPSTab() {
  const [categorias, setCategorias] = useState<IEPSCategoria[]>([]);
  const [categoria, setCategoria] = useState("");
  const [precio, setPrecio] = useState(100);
  const [litros, setLitros] = useState(0);
  const [cigarros, setCigarros] = useState(0);
  const [resultado, setResultado] = useState<RespuestaCalculo | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    calcApi.iepsCategorias().then((r) => {
      setCategorias(r.categorias);
      if (r.categorias.length > 0) setCategoria(r.categorias[0].clave);
    }).catch(() => {});
  }, []);

  const catSeleccionada = categorias.find((c) => c.clave === categoria);
  const requiereLitros = catSeleccionada?.tipo === "cuota_litro" ||
                         catSeleccionada?.cuota_litro !== undefined;
  const requiereCigarros = catSeleccionada?.cuota_adicional_cigarro !== undefined;

  const calcular = async () => {
    setLoading(true);
    try {
      const res = await calcApi.ieps({
        categoria,
        precio_enajenacion: precio,
        cantidad_litros: litros,
        cantidad_cigarros: cigarros,
      });
      setResultado(res);
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card title="Datos del producto">
        <Select label="Categoría IEPS" value={categoria}
                onChange={setCategoria}
                options={categorias.map((c) => ({ value: c.clave, label: c.nombre }))} />
        {catSeleccionada && (
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-xs text-blue-900">
            <p><b>Fundamento:</b> {catSeleccionada.fundamento}</p>
            {catSeleccionada.tasa_pct !== undefined && (
              <p><b>Tasa:</b> {catSeleccionada.tasa_pct.toFixed(2)}%</p>
            )}
            {catSeleccionada.cuota_litro && (
              <p><b>Cuota:</b> ${catSeleccionada.cuota_litro}/litro</p>
            )}
          </div>
        )}
        <NumberInput label="Precio de enajenación (sin IEPS)" value={precio}
                     onChange={setPrecio} step={10} />
        {requiereLitros && (
          <NumberInput label="Cantidad de litros" value={litros} onChange={setLitros} step={1} />
        )}
        {requiereCigarros && (
          <NumberInput label="Cantidad de cigarros" value={cigarros}
                       onChange={setCigarros} step={1} />
        )}
        <button onClick={calcular} disabled={loading || !categoria}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-2 rounded-lg font-medium">
          {loading ? "Calculando..." : "Calcular IEPS"}
        </button>
      </Card>

      <Card title="Resultado">
        {!resultado && <Empty />}
        {resultado?.success && (() => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const d = resultado.datos as any;
          return (
            <div className="space-y-3">
              <BigNumber label="IEPS calculado" value={d.ieps_calculado} />
              <Row label="Precio sin IEPS" value={MXN(d.precio_enajenacion_sin_ieps)} />
              <Row label="IEPS" value={MXN(d.ieps_calculado)} />
              {d.iva_aplicado && (
                <>
                  <Row label="Base IVA (precio + IEPS)" value={MXN(d.base_iva)} />
                  <Row label="IVA 16%" value={MXN(d.iva_calculado)} />
                </>
              )}
              <div className="bg-emerald-50 border-2 border-emerald-300 rounded-lg p-3 text-center">
                <p className="text-xs uppercase text-emerald-700">Precio total al consumidor</p>
                <p className="text-2xl font-bold text-emerald-800">{MXN(d.precio_total_consumidor)}</p>
              </div>
              <FundamentoBox legal={[d.fundamento]} />
            </div>
          );
        })()}
      </Card>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// TAB IMSS / INFONAVIT
// ════════════════════════════════════════════════════════════════════════

function IMSSTab() {
  const [sdi, setSdi] = useState(500);
  const [sdBase, setSdBase] = useState(450);
  const [claseRiesgo, setClaseRiesgo] = useState<"I" | "II" | "III" | "IV" | "V">("I");
  const [resultado, setResultado] = useState<RespuestaCalculo | null>(null);
  const [loading, setLoading] = useState(false);

  const calcular = async () => {
    setLoading(true);
    try {
      const res = await calcApi.imss({
        salario_diario_integrado: sdi,
        salario_diario_base: sdBase,
        clase_riesgo: claseRiesgo,
      });
      setResultado(res);
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <Card title="Datos del trabajador">
        <NumberInput label="Salario diario base" value={sdBase} onChange={setSdBase} step={10} />
        <NumberInput label="Salario diario integrado (SDI)" value={sdi}
                     onChange={setSdi} step={10} />
        <Select label="Clase de riesgo IMSS" value={claseRiesgo}
                onChange={(v) => setClaseRiesgo(v as "I" | "II" | "III" | "IV" | "V")}
                options={[
                  { value: "I", label: "I — Riesgo bajo (oficinas)" },
                  { value: "II", label: "II — Medio bajo" },
                  { value: "III", label: "III — Medio" },
                  { value: "IV", label: "IV — Medio alto" },
                  { value: "V", label: "V — Alto (construcción)" },
                ]} />
        <button onClick={calcular} disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white py-2 rounded-lg font-medium">
          {loading ? "Calculando..." : "Calcular IMSS"}
        </button>
      </Card>

      <Card title="Resultado mensual">
        {!resultado && <Empty />}
        {resultado?.success && (() => {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const d = resultado.datos as any;
          return (
            <div className="space-y-3">
              <div className="bg-red-50 border border-red-200 rounded p-3">
                <p className="text-xs text-red-700 uppercase">Cuota trabajador</p>
                <p className="text-xl font-bold text-red-800">{MXN(d.total_cuota_trabajador)}</p>
                <p className="text-xs text-red-600">{d.cuotas_trabajador?.tasa_efectiva_total}</p>
              </div>
              <div className="bg-purple-50 border border-purple-200 rounded p-3">
                <p className="text-xs text-purple-700 uppercase">Cuota patronal IMSS</p>
                <p className="text-xl font-bold text-purple-800">{MXN(d.total_cuota_patronal)}</p>
              </div>
              <div className="bg-orange-50 border border-orange-200 rounded p-3">
                <p className="text-xs text-orange-700 uppercase">INFONAVIT patronal</p>
                <p className="text-xl font-bold text-orange-800">{MXN(d.infonavit.monto_patronal)}</p>
              </div>
              <Row label="SDI topado (25 UMAs)" value={MXN(d.sdi_topado_25_uma)} />
              <Row label="Costo total empresa" value={MXN(d.costo_total_empresa_mensual + d.infonavit.monto_patronal)} />
              <FundamentoBox legal={resultado.fundamento_legal} />
            </div>
          );
        })()}
      </Card>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// COMPONENTES AUXILIARES
// ════════════════════════════════════════════════════════════════════════

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border rounded-xl p-5 shadow-sm space-y-3">
      <h3 className="font-semibold text-gray-800">{title}</h3>
      {children}
    </div>
  );
}

function NumberInput({
  label, value, onChange, step = 1, min, max,
}: {
  label: string; value: number; onChange: (v: number) => void;
  step?: number; min?: number; max?: number;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type="number" value={value}
        onChange={(e) => onChange(Number(e.target.value) || 0)}
        step={step} min={min} max={max}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
}

function Select({
  label, value, onChange, options,
}: {
  label: string; value: string; onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm border-b last:border-0 py-1">
      <span className="text-gray-700">{label}</span>
      <span className="font-mono text-gray-900">{value}</span>
    </div>
  );
}

function BigNumber({ label, value, color = "blue" }: {
  label: string; value: number; color?: "blue" | "green" | "red";
}) {
  const colors = {
    blue: "from-blue-50 to-cyan-50 border-blue-300 text-blue-800",
    green: "from-green-50 to-emerald-50 border-green-300 text-green-800",
    red: "from-red-50 to-pink-50 border-red-300 text-red-800",
  };
  return (
    <div className={`bg-gradient-to-br ${colors[color]} border-2 rounded-lg p-4 text-center`}>
      <p className="text-xs uppercase tracking-wide font-medium">{label}</p>
      <p className="text-3xl font-bold mt-1">{MXN(value)}</p>
    </div>
  );
}

function Empty() {
  return (
    <div className="text-center text-gray-400 py-8 text-sm">
      Llena los datos y presiona <b>Calcular</b>
    </div>
  );
}

function FundamentoBox({ legal }: { legal: string[] }) {
  const filtered = legal.filter(Boolean);
  if (filtered.length === 0) return null;
  return (
    <details className="text-xs text-gray-500 mt-3">
      <summary className="cursor-pointer">Fundamentos legales</summary>
      <ul className="mt-1 list-disc list-inside">
        {filtered.map((f, i) => <li key={i}>{f}</li>)}
      </ul>
    </details>
  );
}
