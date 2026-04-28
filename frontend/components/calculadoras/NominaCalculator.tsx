"use client";
/**
 * NominaCalculator — Componente completo de cálculo de nómina
 * ============================================================
 * - Validación en vivo de RFC, NSS, CLABE
 * - Datos completos del trabajador y empleador
 * - Desglose visual de percepciones, deducciones y costo empresa
 * - Sticky panel de resultados
 */
import { useState, useMemo } from "react";
import { calcApi, MXN, PCT, type NominaRequest, type DatosTrabajador, type DatosEmpleador, type PeriodoPago, type RespuestaCalculo } from "@/lib/api-calc";

const PERIODOS: { value: PeriodoPago; label: string }[] = [
  { value: "semanal", label: "Semanal (7 días)" },
  { value: "catorcenal", label: "Catorcenal (14 días)" },
  { value: "quincenal", label: "Quincenal (15 días)" },
  { value: "decenal", label: "Decenal (10 días)" },
  { value: "mensual", label: "Mensual (30 días)" },
];

const CLASES_RIESGO = [
  { value: "I", label: "Clase I — Riesgo bajo (oficinas, comercio)" },
  { value: "II", label: "Clase II — Riesgo medio bajo" },
  { value: "III", label: "Clase III — Riesgo medio" },
  { value: "IV", label: "Clase IV — Riesgo medio alto" },
  { value: "V", label: "Clase V — Riesgo alto (construcción, minería)" },
];

// Validadores en vivo (regex client-side)
const RFC_PF_REGEX = /^[A-ZÑ&]{4}\d{6}[A-Z0-9]{3}$/;
const RFC_PM_REGEX = /^[A-ZÑ&]{3}\d{6}[A-Z0-9]{3}$/;
const NSS_REGEX = /^\d{11}$/;
const CLABE_REGEX = /^\d{18}$/;
const CURP_REGEX = /^[A-Z][AEIOUX][A-Z]{2}\d{6}[HM][A-Z]{2}[BCDFGHJKLMNPQRSTVWXYZ]{3}[A-Z0-9]\d$/;

export default function NominaCalculator() {
  // Datos del trabajador
  const [trabajador, setTrabajador] = useState<DatosTrabajador>({
    nombre_completo: "",
    rfc: "",
    curp: "",
    nss: "",
    numero_empleado: "",
    puesto: "",
    departamento: "",
    fecha_ingreso: "",
    clabe: "",
    banco: "",
  });

  // Datos del empleador
  const [empleador, setEmpleador] = useState<DatosEmpleador>({
    razon_social: "",
    rfc: "",
    registro_patronal: "",
    domicilio_fiscal: "",
    actividad_economica: "",
    clase_riesgo: "I",
    prima_riesgo_trabajo: 0.005435,
  });

  // Datos del cálculo
  const [salarioMensual, setSalarioMensual] = useState<number>(20000);
  const [periodo, setPeriodo] = useState<PeriodoPago>("quincenal");
  const [fechaInicio, setFechaInicio] = useState<string>("");
  const [fechaFin, setFechaFin] = useState<string>("");
  const [aniosAntiguedad, setAniosAntiguedad] = useState<number>(1);

  // Percepciones extras
  const [valesDespensa, setValesDespensa] = useState<number>(0);
  const [horasExtrasDobles, setHorasExtrasDobles] = useState<number>(0);
  const [horasExtrasTriples, setHorasExtrasTriples] = useState<number>(0);
  const [otrasGravadas, setOtrasGravadas] = useState<number>(0);
  const [otrasExentas, setOtrasExentas] = useState<number>(0);
  const [bonoProductividad, setBonoProductividad] = useState<number>(0);

  // Deducciones extras
  const [pensionPct, setPensionPct] = useState<number>(0);
  const [fonacot, setFonacot] = useState<number>(0);
  const [infonavitCredito, setInfonavitCredito] = useState<number>(0);

  // Estado UI
  const [calculando, setCalculando] = useState(false);
  const [resultado, setResultado] = useState<RespuestaCalculo | null>(null);
  const [errorGlobal, setErrorGlobal] = useState<string | null>(null);

  // Validaciones en vivo
  const validaciones = useMemo(() => ({
    rfcTrabajador: !trabajador.rfc || RFC_PF_REGEX.test(trabajador.rfc),
    rfcEmpleador: !empleador.rfc || (RFC_PM_REGEX.test(empleador.rfc) || RFC_PF_REGEX.test(empleador.rfc)),
    nss: !trabajador.nss || NSS_REGEX.test(trabajador.nss),
    clabe: !trabajador.clabe || CLABE_REGEX.test(trabajador.clabe),
    curp: !trabajador.curp || CURP_REGEX.test(trabajador.curp),
  }), [trabajador, empleador]);

  const formularioValido = useMemo(() =>
    salarioMensual > 0 &&
    Object.values(validaciones).every(Boolean),
    [salarioMensual, validaciones]
  );

  const handleCalcular = async () => {
    setCalculando(true);
    setErrorGlobal(null);
    setResultado(null);

    try {
      const req: NominaRequest = {
        salario_mensual_bruto: salarioMensual,
        periodo,
        fecha_inicio: fechaInicio || undefined,
        fecha_fin: fechaFin || undefined,
        anios_antiguedad: aniosAntiguedad,
        vales_despensa: valesDespensa,
        horas_extras_dobles: horasExtrasDobles,
        horas_extras_triples: horasExtrasTriples,
        otras_percepciones_gravadas: otrasGravadas,
        otras_percepciones_exentas: otrasExentas,
        bono_productividad: bonoProductividad,
        pension_alimenticia_pct: pensionPct,
        fonacot_descuento: fonacot,
        infonavit_descuento_credito: infonavitCredito,
        prima_riesgo_trabajo: empleador.prima_riesgo_trabajo,
        clase_riesgo: empleador.clase_riesgo,
        // Solo enviar trabajador/empleador si todos los campos requeridos están llenos
        ...(trabajador.nombre_completo && trabajador.rfc && trabajador.nss && trabajador.fecha_ingreso
          ? { trabajador }
          : {}),
        ...(empleador.razon_social && empleador.rfc ? { empleador } : {}),
      };

      const res = await calcApi.nomina(req);
      setResultado(res);
    } catch (err) {
      setErrorGlobal(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setCalculando(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_460px] gap-6 p-6 max-w-7xl mx-auto">
      {/* ──────────────────────────────────────────── FORMULARIO */}
      <div className="space-y-6">
        <header>
          <h1 className="text-3xl font-bold">Calculadora de Nómina 2026</h1>
          <p className="text-gray-600 mt-1">
            Cálculo completo según Art. 96 LISR, Art. 25 LSS y Art. 29 Ley INFONAVIT.
          </p>
        </header>

        {/* SECCIÓN 1: TRABAJADOR */}
        <section className="bg-white border rounded-xl p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            👤 Datos del Trabajador
            <span className="text-xs font-normal text-gray-500">(opcional para cálculo, requerido para CFDI)</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Nombre completo" value={trabajador.nombre_completo}
                   onChange={(v) => setTrabajador({ ...trabajador, nombre_completo: v })} />
            <Field label="Número de empleado" value={trabajador.numero_empleado || ""}
                   onChange={(v) => setTrabajador({ ...trabajador, numero_empleado: v })} />
            <Field
              label="RFC (13 caracteres)"
              value={trabajador.rfc}
              onChange={(v) => setTrabajador({ ...trabajador, rfc: v.toUpperCase() })}
              error={!validaciones.rfcTrabajador ? "RFC inválido (formato: AAAA000000XXX)" : undefined}
              maxLength={13}
              placeholder="PEGJ950101AB1"
            />
            <Field
              label="CURP (18 caracteres)"
              value={trabajador.curp || ""}
              onChange={(v) => setTrabajador({ ...trabajador, curp: v.toUpperCase() })}
              error={!validaciones.curp ? "CURP inválido" : undefined}
              maxLength={18}
            />
            <Field
              label="NSS (11 dígitos)"
              value={trabajador.nss}
              onChange={(v) => setTrabajador({ ...trabajador, nss: v.replace(/\D/g, "") })}
              error={!validaciones.nss ? "NSS debe tener 11 dígitos" : undefined}
              maxLength={11}
              placeholder="12345678901"
            />
            <Field
              type="date"
              label="Fecha de ingreso"
              value={trabajador.fecha_ingreso}
              onChange={(v) => setTrabajador({ ...trabajador, fecha_ingreso: v })}
            />
            <Field label="Puesto" value={trabajador.puesto || ""}
                   onChange={(v) => setTrabajador({ ...trabajador, puesto: v })} />
            <Field label="Departamento" value={trabajador.departamento || ""}
                   onChange={(v) => setTrabajador({ ...trabajador, departamento: v })} />
            <Field
              label="CLABE (18 dígitos)"
              value={trabajador.clabe || ""}
              onChange={(v) => setTrabajador({ ...trabajador, clabe: v.replace(/\D/g, "") })}
              error={!validaciones.clabe ? "CLABE inválida" : undefined}
              maxLength={18}
            />
            <Field label="Banco" value={trabajador.banco || ""}
                   onChange={(v) => setTrabajador({ ...trabajador, banco: v })} />
          </div>
        </section>

        {/* SECCIÓN 2: EMPLEADOR */}
        <section className="bg-white border rounded-xl p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">🏢 Datos del Empleador</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Razón social" value={empleador.razon_social}
                   onChange={(v) => setEmpleador({ ...empleador, razon_social: v })} />
            <Field
              label="RFC empresa (12 o 13)"
              value={empleador.rfc}
              onChange={(v) => setEmpleador({ ...empleador, rfc: v.toUpperCase() })}
              error={!validaciones.rfcEmpleador ? "RFC inválido" : undefined}
              maxLength={13}
            />
            <Field label="Registro patronal IMSS" value={empleador.registro_patronal || ""}
                   onChange={(v) => setEmpleador({ ...empleador, registro_patronal: v })} />
            <Field label="Domicilio fiscal" value={empleador.domicilio_fiscal || ""}
                   onChange={(v) => setEmpleador({ ...empleador, domicilio_fiscal: v })} />
            <Field label="Actividad económica" value={empleador.actividad_economica || ""}
                   onChange={(v) => setEmpleador({ ...empleador, actividad_economica: v })} />
            <SelectField
              label="Clase de riesgo IMSS"
              value={empleador.clase_riesgo || "I"}
              onChange={(v) => setEmpleador({ ...empleador, clase_riesgo: v as DatosEmpleador["clase_riesgo"] })}
              options={CLASES_RIESGO}
            />
          </div>
        </section>

        {/* SECCIÓN 3: SALARIO Y PERÍODO */}
        <section className="bg-white border rounded-xl p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">📅 Período y salario</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <NumberField label="Salario mensual bruto (MXN)" value={salarioMensual}
                         onChange={setSalarioMensual} step={100} min={0} />
            <NumberField label="Años de antigüedad" value={aniosAntiguedad}
                         onChange={setAniosAntiguedad} step={1} min={0} max={50} />
            <SelectField label="Periodicidad de pago" value={periodo}
                         onChange={(v) => setPeriodo(v as PeriodoPago)}
                         options={PERIODOS.map((p) => ({ value: p.value, label: p.label }))} />
            <Field type="date" label="Fecha inicio período" value={fechaInicio}
                   onChange={setFechaInicio} />
            <Field type="date" label="Fecha fin período" value={fechaFin}
                   onChange={setFechaFin} />
          </div>
        </section>

        {/* SECCIÓN 4: PERCEPCIONES EXTRAS */}
        <section className="bg-white border rounded-xl p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">💰 Percepciones adicionales</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <NumberField label="Vales de despensa" value={valesDespensa}
                         onChange={setValesDespensa} step={50} min={0} />
            <NumberField label="Horas extras dobles" value={horasExtrasDobles}
                         onChange={setHorasExtrasDobles} step={1} min={0} max={9} />
            <NumberField label="Horas extras triples" value={horasExtrasTriples}
                         onChange={setHorasExtrasTriples} step={1} min={0} />
            <NumberField label="Bono productividad" value={bonoProductividad}
                         onChange={setBonoProductividad} step={100} min={0} />
            <NumberField label="Otras percepciones gravadas" value={otrasGravadas}
                         onChange={setOtrasGravadas} step={100} min={0} />
            <NumberField label="Otras percepciones exentas" value={otrasExentas}
                         onChange={setOtrasExentas} step={100} min={0} />
          </div>
        </section>

        {/* SECCIÓN 5: DEDUCCIONES EXTRAS */}
        <section className="bg-white border rounded-xl p-5 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">📉 Deducciones adicionales</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <NumberField label="Pensión alimenticia (% salario)" value={pensionPct * 100}
                         onChange={(v) => setPensionPct(v / 100)} step={1} min={0} max={50} />
            <NumberField label="Descuento FONACOT" value={fonacot}
                         onChange={setFonacot} step={50} min={0} />
            <NumberField label="Descuento INFONAVIT (crédito)" value={infonavitCredito}
                         onChange={setInfonavitCredito} step={50} min={0} />
          </div>
        </section>

        {errorGlobal && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl p-4">
            ⚠️ {errorGlobal}
          </div>
        )}

        <button
          disabled={!formularioValido || calculando}
          onClick={handleCalcular}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-semibold py-3 rounded-xl transition"
        >
          {calculando ? "Calculando..." : "Calcular nómina"}
        </button>
      </div>

      {/* ──────────────────────────────────────────── PANEL RESULTADO */}
      <aside className="lg:sticky lg:top-6 self-start">
        <ResultadoNomina resultado={resultado} />
      </aside>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// PANEL DE RESULTADOS
// ════════════════════════════════════════════════════════════════════════

function ResultadoNomina({ resultado }: { resultado: RespuestaCalculo | null }) {
  if (!resultado) {
    return (
      <div className="bg-gray-50 border border-dashed border-gray-300 rounded-xl p-6 text-center text-gray-500">
        Llena los datos y presiona <b>Calcular</b> para ver el resultado.
      </div>
    );
  }

  if (!resultado.success) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-5 space-y-2">
        <h3 className="font-semibold text-red-800">Errores de validación</h3>
        {resultado.errores.map((e, i) => (
          <div key={i} className="text-sm text-red-700">
            <b>{e.campo}:</b> {e.motivo}
          </div>
        ))}
      </div>
    );
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = resultado.datos as any;
  const totalP: number = d.total_percepciones;
  const totalD: number = d.total_deducciones;
  const neto: number = d.neto_a_pagar;
  const costo: number = d.costo_empresa.costo_total_para_empresa;

  return (
    <div className="bg-white border rounded-xl p-5 shadow-sm space-y-4">
      <header className="border-b pb-3">
        <h3 className="text-xl font-bold">Resultado del cálculo</h3>
        <p className="text-xs text-gray-500">
          Período: {d.periodo_pago.tipo} · {d.periodo_pago.dias} días · Ejercicio {d.ejercicio}
        </p>
      </header>

      {/* PERCEPCIONES */}
      <Section title="💰 Percepciones" total={totalP} colorClass="text-green-700">
        <Row label="Salario base" value={d.percepciones.salario_base.monto_periodo} />
        {d.percepciones.horas_extras.total > 0 && (
          <Row label="Horas extras" value={d.percepciones.horas_extras.total} />
        )}
        {d.percepciones.vales_despensa.monto_total > 0 && (
          <Row label="Vales despensa" value={d.percepciones.vales_despensa.monto_total} hint={`Exento: ${MXN(d.percepciones.vales_despensa.exento)}`} />
        )}
        {d.percepciones.bono_productividad > 0 && (
          <Row label="Bono productividad" value={d.percepciones.bono_productividad} />
        )}
        {d.percepciones.ptu > 0 && <Row label="PTU" value={d.percepciones.ptu} />}
      </Section>

      {/* DEDUCCIONES */}
      <Section title="📉 Deducciones" total={totalD} colorClass="text-red-700">
        <Row label="ISR retenido" value={d.deducciones.isr.isr_a_retener}
             hint={`Tasa efectiva ${d.deducciones.isr.tasa_efectiva_pct}%`} />
        <Row label="IMSS trabajador" value={d.deducciones.imss_trabajador.cuota_periodo} />
        {d.deducciones.infonavit_credito.monto > 0 && (
          <Row label="INFONAVIT (crédito)" value={d.deducciones.infonavit_credito.monto} />
        )}
        {d.deducciones.pension_alimenticia.monto > 0 && (
          <Row label="Pensión alimenticia" value={d.deducciones.pension_alimenticia.monto} />
        )}
        {d.deducciones.fonacot > 0 && <Row label="FONACOT" value={d.deducciones.fonacot} />}
      </Section>

      {/* NETO */}
      <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-4 text-center">
        <p className="text-sm font-medium text-green-700 uppercase tracking-wide">Neto a pagar</p>
        <p className="text-4xl font-bold text-green-800 mt-1">{MXN(neto)}</p>
        {d.resumen.subsidio_aplicado > 0 && (
          <p className="text-xs text-green-700 mt-1">
            Incluye subsidio empleo: {MXN(d.resumen.subsidio_aplicado)}
          </p>
        )}
      </div>

      {/* COSTO EMPRESA */}
      <Section title="🏢 Costo total para la empresa" total={costo} colorClass="text-purple-700">
        <Row label="Salario base" value={d.costo_empresa.salario_base} />
        <Row label="IMSS patronal" value={d.costo_empresa.imss_patronal_periodo} />
        <Row label="INFONAVIT patronal" value={d.costo_empresa.infonavit_patronal_periodo} />
      </Section>

      {/* SDI */}
      <details className="text-sm">
        <summary className="cursor-pointer font-medium text-gray-700">Ver SDI calculado</summary>
        <div className="mt-2 bg-gray-50 rounded p-3 text-xs space-y-1">
          <div>SDI: <b>{MXN(d.sdi.sdi_calculado)}</b></div>
          <div>Factor integración: {d.sdi.factor_integracion}</div>
          <div className="text-gray-500">{d.sdi.formula}</div>
        </div>
      </details>

      {/* Advertencias */}
      {(resultado.advertencias?.length ?? 0) > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-xs">
          <p className="font-semibold text-yellow-800 mb-1">⚠️ Advertencias</p>
          <ul className="list-disc list-inside text-yellow-700 space-y-1">
            {resultado.advertencias.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </div>
      )}

      {/* Fundamentos */}
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

function Field({
  label, value, onChange, type = "text", error, placeholder, maxLength,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  error?: string;
  placeholder?: string;
  maxLength?: number;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        className={`w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 ${
          error ? "border-red-400" : "border-gray-300"
        }`}
      />
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  );
}

function NumberField({
  label, value, onChange, step = 1, min, max,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  max?: number;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(Number(e.target.value) || 0)}
        step={step}
        min={min}
        max={max}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
}

function SelectField<T extends string>({
  label, value, onChange, options,
}: {
  label: string;
  value: T;
  onChange: (v: T) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

function Section({
  title, total, colorClass = "text-gray-700", children,
}: {
  title: string;
  total: number;
  colorClass?: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h4 className="font-semibold text-sm text-gray-700 mb-2">{title}</h4>
      <div className="space-y-1 text-sm">{children}</div>
      <div className={`flex justify-between mt-2 pt-2 border-t font-semibold ${colorClass}`}>
        <span>Total</span>
        <span>{MXN(total)}</span>
      </div>
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
