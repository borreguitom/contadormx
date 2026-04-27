"use client";
/**
 * FiniquitoCalculator — Cálculo de finiquito y liquidación
 * ==========================================================
 * Soporta todos los tipos de separación según LFT.
 */
import { useState, useMemo } from "react";
import {
  calcApi, MXN, type FiniquitoRequest, type DatosTrabajador,
  type DatosEmpleador, type TipoSeparacion, type RespuestaCalculo,
} from "@/lib/api-calc";

const TIPOS_SEPARACION: { value: TipoSeparacion; label: string; icon: string }[] = [
  { value: "renuncia", label: "Renuncia voluntaria", icon: "📝" },
  { value: "despido_justificado", label: "Despido con justa causa", icon: "⚖️" },
  { value: "despido_injustificado", label: "Despido injustificado", icon: "🚫" },
  { value: "mutuo_acuerdo", label: "Mutuo acuerdo", icon: "🤝" },
  { value: "muerte", label: "Muerte del trabajador", icon: "💔" },
  { value: "jubilacion", label: "Jubilación", icon: "🎓" },
  { value: "incapacidad_total", label: "Incapacidad total", icon: "🏥" },
  { value: "termino_contrato", label: "Término de contrato", icon: "📋" },
];

const RFC_PF_REGEX = /^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$/;
const RFC_PM_REGEX = /^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$/;

export default function FiniquitoCalculator() {
  const [trabajador, setTrabajador] = useState<DatosTrabajador>({
    nombre_completo: "",
    rfc: "",
    nss: "",
    fecha_ingreso: "",
  });

  const [empleador, setEmpleador] = useState<DatosEmpleador>({
    razon_social: "",
    rfc: "",
  });

  const [salarioDiario, setSalarioDiario] = useState<number>(500);
  const [fechaIngreso, setFechaIngreso] = useState<string>("");
  const [fechaSeparacion, setFechaSeparacion] = useState<string>("");
  const [tipoSeparacion, setTipoSeparacion] = useState<TipoSeparacion>("renuncia");

  const [vacacionesGozadas, setVacacionesGozadas] = useState<number>(0);
  const [diasPendientes, setDiasPendientes] = useState<number>(0);
  const [aguinaldoYaPagado, setAguinaldoYaPagado] = useState<number>(0);
  const [ptuPendiente, setPtuPendiente] = useState<number>(0);
  const [bonoPendiente, setBonoPendiente] = useState<number>(0);
  const [mesesSalariosCaidos, setMesesSalariosCaidos] = useState<number>(0);

  const [calculando, setCalculando] = useState(false);
  const [resultado, setResultado] = useState<RespuestaCalculo | null>(null);
  const [errorGlobal, setErrorGlobal] = useState<string | null>(null);

  const validRfcTrab = !trabajador.rfc || RFC_PF_REGEX.test(trabajador.rfc);
  const validRfcEmp = !empleador.rfc || RFC_PM_REGEX.test(empleador.rfc) || RFC_PF_REGEX.test(empleador.rfc);

  const aniosCalculados = useMemo(() => {
    if (!fechaIngreso || !fechaSeparacion) return 0;
    const ms = new Date(fechaSeparacion).getTime() - new Date(fechaIngreso).getTime();
    return Math.max(0, ms / (1000 * 60 * 60 * 24 * 365.25));
  }, [fechaIngreso, fechaSeparacion]);

  const handleCalcular = async () => {
    setCalculando(true);
    setErrorGlobal(null);
    setResultado(null);

    try {
      const req: FiniquitoRequest = {
        salario_diario: salarioDiario,
        fecha_ingreso: fechaIngreso || undefined,
        fecha_separacion: fechaSeparacion || undefined,
        tipo_separacion: tipoSeparacion,
        vacaciones_gozadas: vacacionesGozadas,
        dias_pendientes_pago: diasPendientes,
        aguinaldo_ya_pagado: aguinaldoYaPagado,
        ptu_pendiente: ptuPendiente,
        bono_pendiente: bonoPendiente,
        meses_salarios_caidos: mesesSalariosCaidos,
        ...(trabajador.nombre_completo && trabajador.rfc ? { trabajador } : {}),
        ...(empleador.razon_social && empleador.rfc ? { empleador } : {}),
      };
      const res = await calcApi.finiquito(req);
      setResultado(res);
    } catch (err) {
      setErrorGlobal(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setCalculando(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_460px] gap-6 p-6 max-w-7xl mx-auto">
      <div className="space-y-6">
        <header>
          <h1 className="text-3xl font-bold">Calculadora de Finiquito y Liquidación</h1>
          <p className="text-gray-600 mt-1">
            Cálculo completo según LFT (Art. 50, 76, 80, 87, 162) y LISR (Art. 93-XIII).
          </p>
        </header>

        {/* TRABAJADOR */}
        <Section title="👤 Datos del Trabajador">
          <Field label="Nombre completo" value={trabajador.nombre_completo}
                 onChange={(v) => setTrabajador({ ...trabajador, nombre_completo: v })} />
          <Field label="RFC" value={trabajador.rfc} maxLength={13}
                 onChange={(v) => setTrabajador({ ...trabajador, rfc: v.toUpperCase() })}
                 error={!validRfcTrab ? "RFC inválido" : undefined} />
          <Field label="NSS" value={trabajador.nss} maxLength={11}
                 onChange={(v) => setTrabajador({ ...trabajador, nss: v.replace(/\D/g, "") })} />
          <Field label="Número empleado" value={trabajador.numero_empleado || ""}
                 onChange={(v) => setTrabajador({ ...trabajador, numero_empleado: v })} />
        </Section>

        {/* EMPLEADOR */}
        <Section title="🏢 Datos del Empleador">
          <Field label="Razón social" value={empleador.razon_social}
                 onChange={(v) => setEmpleador({ ...empleador, razon_social: v })} />
          <Field label="RFC" value={empleador.rfc} maxLength={13}
                 onChange={(v) => setEmpleador({ ...empleador, rfc: v.toUpperCase() })}
                 error={!validRfcEmp ? "RFC inválido" : undefined} />
        </Section>

        {/* PERIODO LABORAL */}
        <Section title="📅 Período laboral">
          <Field type="date" label="Fecha de ingreso" value={fechaIngreso} onChange={setFechaIngreso} />
          <Field type="date" label="Fecha de separación" value={fechaSeparacion} onChange={setFechaSeparacion} />
          <NumberField label="Salario diario (MXN)" value={salarioDiario}
                       onChange={setSalarioDiario} step={10} min={0} />
          <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
            <b>Antigüedad calculada:</b> {aniosCalculados.toFixed(2)} años
          </div>
        </Section>

        {/* TIPO DE SEPARACIÓN */}
        <Section title="🚪 Tipo de separación">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 col-span-full">
            {TIPOS_SEPARACION.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setTipoSeparacion(t.value)}
                className={`text-left p-3 rounded-lg border-2 text-sm transition ${
                  tipoSeparacion === t.value
                    ? "border-blue-500 bg-blue-50 font-medium"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <div className="text-xl">{t.icon}</div>
                <div>{t.label}</div>
              </button>
            ))}
          </div>
        </Section>

        {/* CONCEPTOS PENDIENTES */}
        <Section title="💸 Conceptos pendientes">
          <NumberField label="Días pendientes de pago" value={diasPendientes}
                       onChange={setDiasPendientes} min={0} max={31} />
          <NumberField label="Vacaciones ya gozadas (días)" value={vacacionesGozadas}
                       onChange={setVacacionesGozadas} min={0} />
          <NumberField label="Aguinaldo ya pagado" value={aguinaldoYaPagado}
                       onChange={setAguinaldoYaPagado} step={100} min={0} />
          <NumberField label="PTU pendiente" value={ptuPendiente}
                       onChange={setPtuPendiente} step={100} min={0} />
          <NumberField label="Bono pendiente" value={bonoPendiente}
                       onChange={setBonoPendiente} step={100} min={0} />
          {tipoSeparacion === "despido_injustificado" && (
            <NumberField label="Meses de salarios caídos (máx 12)"
                         value={mesesSalariosCaidos}
                         onChange={setMesesSalariosCaidos} step={1} min={0} max={12} />
          )}
        </Section>

        {errorGlobal && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
            ⚠️ {errorGlobal}
          </div>
        )}

        <button
          disabled={salarioDiario <= 0 || calculando}
          onClick={handleCalcular}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-semibold py-3 rounded-xl transition"
        >
          {calculando ? "Calculando..." : "Calcular finiquito"}
        </button>
      </div>

      <aside className="lg:sticky lg:top-6 self-start">
        <ResultadoFiniquito resultado={resultado} />
      </aside>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// PANEL DE RESULTADO
// ════════════════════════════════════════════════════════════════════════

function ResultadoFiniquito({ resultado }: { resultado: RespuestaCalculo | null }) {
  if (!resultado) {
    return (
      <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-6 text-center text-gray-500">
        Llena los datos y presiona <b>Calcular</b>.
      </div>
    );
  }

  if (!resultado.success) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-5 space-y-2">
        <h3 className="font-semibold text-red-800">Errores</h3>
        {resultado.errores.map((e, i) => (
          <p key={i} className="text-sm text-red-700"><b>{e.campo}:</b> {e.motivo}</p>
        ))}
      </div>
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = resultado.datos as any;

  return (
    <div className="bg-white border rounded-xl p-5 shadow-sm space-y-4">
      <header className="border-b pb-3">
        <h3 className="text-xl font-bold">Resultado del finiquito</h3>
        <p className="text-xs text-gray-500">
          {d.tipo_separacion.descripcion} · Antigüedad: {d.periodo_laboral.anios_servicio.toFixed(2)} años
        </p>
      </header>

      {/* PARTES PROPORCIONALES */}
      <ResultSection title="📊 Partes proporcionales" total={d.subtotal_partes_proporcionales}>
        {d.partes_proporcionales.salario_pendiente.monto > 0 && (
          <Row label="Salario pendiente" value={d.partes_proporcionales.salario_pendiente.monto} />
        )}
        <Row label={`Vacaciones (${d.partes_proporcionales.vacaciones.dias_pendientes} días)`}
             value={d.partes_proporcionales.vacaciones.monto} />
        <Row label="Prima vacacional 25%" value={d.partes_proporcionales.prima_vacacional.monto}
             hint={`Exenta: ${MXN(d.partes_proporcionales.prima_vacacional.exento)}`} />
        <Row label="Aguinaldo proporcional" value={d.partes_proporcionales.aguinaldo.pendiente}
             hint={`Exento: ${MXN(d.partes_proporcionales.aguinaldo.exento)}`} />
        {d.partes_proporcionales.ptu_pendiente > 0 && (
          <Row label="PTU pendiente" value={d.partes_proporcionales.ptu_pendiente} />
        )}
        {d.partes_proporcionales.bono_pendiente > 0 && (
          <Row label="Bono pendiente" value={d.partes_proporcionales.bono_pendiente} />
        )}
      </ResultSection>

      {/* INDEMNIZACIÓN */}
      {d.indemnizacion.aplica && (
        <ResultSection title="⚖️ Indemnización" total={d.subtotal_indemnizacion}>
          <Row label="3 meses (Art. 50-I LFT)" value={d.indemnizacion.tres_meses_salario.monto} />
          <Row label={`20 días/año × ${d.periodo_laboral.anios_servicio.toFixed(1)} años`}
               value={d.indemnizacion.veinte_dias_por_anio.monto}
               hint="Tope 25 SM (Art. 50-II)" />
          {d.indemnizacion.salarios_caidos.monto > 0 && (
            <Row label={`Salarios caídos (${d.indemnizacion.salarios_caidos.meses} meses)`}
                 value={d.indemnizacion.salarios_caidos.monto} />
          )}
          <p className="text-xs text-gray-500 mt-2">
            Exento ISR: <b>{MXN(d.indemnizacion.exencion_isr.monto_exento)}</b> ·
            Gravado: <b>{MXN(d.indemnizacion.exencion_isr.monto_gravado)}</b>
          </p>
        </ResultSection>
      )}

      {/* PRIMA DE ANTIGÜEDAD */}
      {d.prima_antiguedad.aplica && (
        <ResultSection title="🏆 Prima de antigüedad" total={d.subtotal_prima_antiguedad}>
          <Row label="12 días/año (tope 2 SM)" value={d.prima_antiguedad.monto}
               hint="Art. 162 LFT" />
        </ResultSection>
      )}

      {/* TOTALES */}
      <div className="bg-gradient-to-br from-emerald-50 to-green-50 border-2 border-emerald-300 rounded-xl p-4 space-y-2">
        <div className="flex justify-between text-sm">
          <span>Total bruto</span>
          <span className="font-mono">{MXN(d.total_bruto)}</span>
        </div>
        <div className="flex justify-between text-sm text-green-700">
          <span>Total exento de ISR</span>
          <span className="font-mono">{MXN(d.total_exento)}</span>
        </div>
        <div className="flex justify-between text-sm text-red-700">
          <span>ISR retenido</span>
          <span className="font-mono">−{MXN(d.isr_retenido)}</span>
        </div>
        <hr className="border-emerald-300" />
        <div className="flex justify-between items-center pt-1">
          <span className="text-sm font-medium uppercase tracking-wide text-emerald-800">Neto a pagar</span>
          <span className="text-3xl font-bold text-emerald-900">{MXN(d.neto_a_pagar)}</span>
        </div>
      </div>

      {/* NOTAS */}
      {(d.notas?.length ?? 0) > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded p-3 text-xs">
          <p className="font-semibold text-blue-800 mb-1">📝 Notas</p>
          <ul className="space-y-1 text-blue-700">
            {d.notas.map((n: string, i: number) => <li key={i}>{n}</li>)}
          </ul>
        </div>
      )}

      {(resultado.advertencias?.length ?? 0) > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-xs">
          <p className="font-semibold text-yellow-800 mb-1">⚠️ Advertencias</p>
          <ul className="space-y-1 text-yellow-700">
            {resultado.advertencias.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}

      <details className="text-xs text-gray-500">
        <summary className="cursor-pointer">Fundamentos legales</summary>
        <ul className="mt-2 list-disc list-inside space-y-0.5">
          {resultado.fundamento_legal.filter(Boolean).map((f, i) => <li key={i}>{f}</li>)}
        </ul>
      </details>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// COMPONENTES AUXILIARES
// ════════════════════════════════════════════════════════════════════════

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="bg-white border rounded-xl p-5 shadow-sm">
      <h2 className="text-lg font-semibold mb-4">{title}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">{children}</div>
    </section>
  );
}

function ResultSection({ title, total, children }: {
  title: string; total: number; children: React.ReactNode;
}) {
  return (
    <div>
      <h4 className="font-semibold text-sm text-gray-700 mb-2">{title}</h4>
      <div className="space-y-1 text-sm">{children}</div>
      <div className="flex justify-between mt-2 pt-2 border-t font-semibold text-gray-800">
        <span>Subtotal</span>
        <span className="font-mono">{MXN(total)}</span>
      </div>
    </div>
  );
}

function Field({
  label, value, onChange, type = "text", error, maxLength,
}: {
  label: string; value: string; onChange: (v: string) => void;
  type?: string; error?: string; maxLength?: number;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type} value={value}
        onChange={(e) => onChange(e.target.value)}
        maxLength={maxLength}
        className={`w-full border rounded-lg px-3 py-2 text-sm ${error ? "border-red-400" : "border-gray-300"}`}
      />
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  );
}

function NumberField({
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
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
      />
    </div>
  );
}

function Row({ label, value, hint }: { label: string; value: number; hint?: string }) {
  return (
    <div className="flex justify-between items-baseline">
      <span className="text-gray-700">
        {label}
        {hint && <span className="block text-xs text-gray-500">{hint}</span>}
      </span>
      <span className="font-mono">{MXN(value)}</span>
    </div>
  );
}
