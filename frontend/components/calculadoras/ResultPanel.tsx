interface Props {
  data: Record<string, unknown> | null;
  loading: boolean;
  error: string;
}

function Value({ v }: { v: unknown }): React.ReactElement {
  if (v === null || v === undefined) return <span className="text-gray-600">—</span>;
  if (typeof v === "boolean") return <span className={v ? "text-green-400" : "text-red-400"}>{v ? "Sí" : "No"}</span>;
  if (typeof v === "number") {
    const formatted = v.toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
    return <span className="font-mono text-green-300">${formatted}</span>;
  }
  if (typeof v === "string") return <span className="text-gray-300">{v}</span>;
  if (typeof v === "object" && !Array.isArray(v)) {
    return (
      <div className="pl-3 border-l border-white/8 mt-1 space-y-1">
        {Object.entries(v as Record<string, unknown>).map(([k, val]) => (
          <Row key={k} k={k} v={val} />
        ))}
      </div>
    );
  }
  if (Array.isArray(v)) {
    return (
      <div className="space-y-0.5">
        {v.map((item, i) => <Value key={i} v={item} />)}
      </div>
    );
  }
  return <span className="text-gray-400">{String(v)}</span>;
}

function Row({ k, v }: { k: string; v: unknown }) {
  const label = k
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
  const isObject = typeof v === "object" && v !== null && !Array.isArray(v);

  return (
    <div className={`flex ${isObject ? "flex-col" : "justify-between items-start gap-2"}`}>
      <span className="text-xs text-gray-500 shrink-0">{label}</span>
      <Value v={v} />
    </div>
  );
}

// Campos destacados para mostrar arriba
const HIGHLIGHT_KEYS = new Set([
  "isr_a_retener", "pago_provisional_a_enterar", "iva_a_cargo", "iva_a_favor",
  "neto_a_pagar", "total_a_pagar", "total_cuotas", "costo_total_empresa_mensual",
  "resultado_final",
]);

export default function ResultPanel({ data, loading, error }: Props) {
  if (loading) return (
    <div className="flex items-center justify-center h-40">
      <div className="flex gap-1.5">
        {[0, 1, 2].map(i => (
          <span key={i} className="w-2 h-2 rounded-full bg-green-500"
            style={{ animation: `bounce 1.2s infinite ${i * 0.18}s` }} />
        ))}
      </div>
    </div>
  );

  if (error) return (
    <div className="rounded-xl border border-red-500/20 bg-red-500/8 px-4 py-3 text-sm text-red-400">
      {error}
    </div>
  );

  if (!data) return (
    <div className="text-center py-10 text-gray-600 text-sm">
      Completa el formulario y calcula
    </div>
  );

  // Separar campos destacados del resto
  const highlights = Object.entries(data).filter(([k]) => HIGHLIGHT_KEYS.has(k));
  const rest = Object.entries(data).filter(([k]) => !HIGHLIGHT_KEYS.has(k));

  return (
    <div className="space-y-4">
      {/* Cifras clave */}
      {highlights.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {highlights.map(([k, v]) => (
            <div key={k} className="rounded-xl bg-green-500/8 border border-green-500/20 px-3 py-2.5">
              <p className="text-xs text-gray-500 mb-0.5">{k.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</p>
              <p className="text-base font-bold text-green-300">
                {typeof v === "number"
                  ? `$${v.toLocaleString("es-MX", { minimumFractionDigits: 2 })}`
                  : String(v)}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Desglose completo */}
      <div className="rounded-xl bg-white/3 border border-white/8 p-4 space-y-2 text-xs">
        <p className="text-[10px] text-gray-600 uppercase tracking-widest mb-2">Desglose</p>
        {rest.map(([k, v]) => <Row key={k} k={k} v={v} />)}
      </div>
    </div>
  );
}
