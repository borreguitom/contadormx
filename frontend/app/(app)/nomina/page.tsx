"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { SelectInput } from "@/components/ui/SelectInput";
import {
  api,
  type Cliente,
  type Empleado,
  type EmpleadoCreate,
  type NominaResult,
  type NominaRunRequest,
} from "@/lib/api";

const CONTRATOS = ["indeterminado", "determinado", "honorarios", "obra"];
const PERIODOS = [
  { value: "semanal",    label: "Semanal (7 días)" },
  { value: "catorcenal", label: "Catorcenal (14 días)" },
  { value: "quincenal",  label: "Quincenal (15 días)" },
  { value: "mensual",    label: "Mensual (30 días)" },
];

const MXN = (n: number) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(n);

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

const EMPTY_EMP: EmpleadoCreate = {
  nombre_completo: "", rfc: "", curp: "", nss: "",
  fecha_nacimiento: "", fecha_alta: "", tipo_contrato: "indeterminado",
  periodicidad_pago: "quincenal", salario_diario: 0,
  departamento: "", puesto: "", banco: "", clabe: "",
};

export default function NominaPage() {
  const [tab, setTab] = useState<"empleados" | "nomina">("empleados");

  // Cliente selector
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [clienteId, setClienteId] = useState<number | "">("");

  // Employees
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [loadingEmps, setLoadingEmps] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingEmp, setEditingEmp] = useState<Empleado | null>(null);
  const [form, setForm] = useState<EmpleadoCreate>(EMPTY_EMP);
  const [saving, setSaving] = useState(false);
  const [empErr, setEmpErr] = useState("");

  // Import
  const importRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [importMsg, setImportMsg] = useState("");

  // Nómina run
  const today = new Date().toISOString().slice(0, 10);
  const firstOfMonth = today.slice(0, 8) + "01";
  const [nomReq, setNomReq] = useState<NominaRunRequest>({
    periodo: "quincenal", fecha_inicio: firstOfMonth, fecha_fin: today,
    otras_percepciones_global: 0, vales_despensa_global: 0,
  });
  const [nomResult, setNomResult] = useState<NominaResult | null>(null);
  const [runningNom, setRunningNom] = useState(false);
  const [nomErr, setNomErr] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    api.clients.list().then(setClientes).catch(() => {});
  }, []);

  const loadEmps = useCallback(async (id: number) => {
    setLoadingEmps(true);
    try { setEmpleados(await api.empleados.list(id)); }
    catch { setEmpErr("Error cargando empleados"); }
    finally { setLoadingEmps(false); }
  }, []);

  useEffect(() => {
    if (clienteId) loadEmps(Number(clienteId));
    else setEmpleados([]);
  }, [clienteId, loadEmps]);

  function openNew() {
    setEditingEmp(null);
    setForm(EMPTY_EMP);
    setEmpErr("");
    setShowForm(true);
  }

  function openEdit(emp: Empleado) {
    setEditingEmp(emp);
    setForm({
      nombre_completo: emp.nombre_completo,
      rfc: emp.rfc ?? "",
      curp: emp.curp ?? "",
      nss: emp.nss ?? "",
      fecha_nacimiento: emp.fecha_nacimiento ?? "",
      fecha_alta: emp.fecha_alta,
      tipo_contrato: emp.tipo_contrato,
      periodicidad_pago: emp.periodicidad_pago,
      salario_diario: emp.salario_diario,
      departamento: emp.departamento ?? "",
      puesto: emp.puesto ?? "",
      banco: emp.banco ?? "",
      clabe: emp.clabe ?? "",
    });
    setEmpErr("");
    setShowForm(true);
  }

  async function handleSaveEmp(e: React.FormEvent) {
    e.preventDefault();
    if (!clienteId) return;
    if (!form.nombre_completo || !form.fecha_alta || !form.salario_diario) {
      setEmpErr("Nombre, fecha de alta y salario diario son obligatorios");
      return;
    }
    setSaving(true); setEmpErr("");
    try {
      if (editingEmp) {
        await api.empleados.update(Number(clienteId), editingEmp.id, form);
      } else {
        await api.empleados.create(Number(clienteId), form);
      }
      setShowForm(false);
      await loadEmps(Number(clienteId));
    } catch (err: unknown) {
      setEmpErr(err instanceof Error ? err.message : "Error guardando");
    } finally { setSaving(false); }
  }

  async function handleDelete(empId: number) {
    if (!clienteId || !confirm("¿Dar de baja a este empleado?")) return;
    try {
      await api.empleados.delete(Number(clienteId), empId);
      await loadEmps(Number(clienteId));
    } catch {}
  }

  async function handleImport(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !clienteId) return;
    setImporting(true); setImportMsg("");
    try {
      const res = await api.empleados.importExcel(Number(clienteId), file);
      setImportMsg(`${res.importados} empleados importados${res.errores.length ? ` — ${res.errores.length} errores` : ""}`);
      await loadEmps(Number(clienteId));
    } catch (err: unknown) {
      setImportMsg(err instanceof Error ? err.message : "Error al importar");
    } finally {
      setImporting(false);
      if (importRef.current) importRef.current.value = "";
    }
  }

  async function handleDownloadTemplate() {
    try {
      const blob = await api.empleados.downloadTemplate();
      download(blob, "plantilla_empleados.xlsx");
    } catch {}
  }

  async function handleRunNomina(e: React.FormEvent) {
    e.preventDefault();
    if (!clienteId) return;
    setRunningNom(true); setNomErr(""); setNomResult(null);
    try {
      setNomResult(await api.empleados.runNomina(Number(clienteId), nomReq));
    } catch (err: unknown) {
      setNomErr(err instanceof Error ? err.message : "Error calculando nómina");
    } finally { setRunningNom(false); }
  }

  async function handleExportExcel() {
    if (!clienteId) return;
    setExporting(true);
    try {
      const blob = await api.empleados.exportNominaExcel(Number(clienteId), nomReq);
      download(blob, `nomina_${nomReq.fecha_inicio}_${nomReq.fecha_fin}.xlsx`);
    } catch {} finally { setExporting(false); }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/8 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white">Nómina</h1>
          <p className="text-xs text-gray-500 mt-0.5">Empleados, cálculo masivo y exportación a Excel</p>
        </div>
        <SelectInput
          value={String(clienteId)}
          onChange={v => setClienteId(v ? Number(v) : "")}
          options={[{ value: "", label: "Seleccionar cliente..." }, ...clientes.map(c => ({ value: String(c.id), label: c.razon_social }))]}
          className="min-w-[200px] !rounded-lg !py-1.5"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-6 pt-3 border-b border-white/8">
        {(["empleados", "nomina"] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm rounded-t-lg border-b-2 transition-all ${
              tab === t ? "text-green-300 border-green-400 bg-green-500/8" : "text-gray-500 border-transparent hover:text-gray-300"
            }`}
          >
            {t === "empleados" ? "👥 Empleados" : "💰 Correr Nómina"}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">

        {!clienteId && (
          <div className="rounded-xl border border-white/10 bg-white/3 px-4 py-12 text-center text-gray-600 text-sm">
            Selecciona un cliente arriba para ver sus empleados
          </div>
        )}

        {/* ── Empleados tab ──────────────────────────────────────────── */}
        {tab === "empleados" && clienteId && (
          <>
            {/* Toolbar */}
            <div className="flex items-center gap-3 flex-wrap">
              <button onClick={openNew}
                className="px-3 py-1.5 text-sm bg-green-600 hover:bg-green-500 text-white rounded-lg transition-colors">
                + Nuevo empleado
              </button>
              <button onClick={handleDownloadTemplate}
                className="px-3 py-1.5 text-sm bg-white/5 hover:bg-white/10 text-gray-300 rounded-lg transition-colors border border-white/10">
                Descargar plantilla
              </button>
              <label className={`px-3 py-1.5 text-sm rounded-lg transition-colors border border-white/10 cursor-pointer ${
                importing ? "bg-white/5 text-gray-500" : "bg-white/5 hover:bg-white/10 text-gray-300"
              }`}>
                {importing ? "Importando..." : "Importar Excel"}
                <input ref={importRef} type="file" accept=".xlsx,.xls" className="hidden"
                  onChange={handleImport} disabled={importing} />
              </label>
              {importMsg && (
                <span className={`text-xs ${importMsg.includes("Error") ? "text-red-400" : "text-green-400"}`}>
                  {importMsg}
                </span>
              )}
              <span className="ml-auto text-xs text-gray-600">{empleados.length} empleados</span>
            </div>

            {/* Employee form */}
            {showForm && (
              <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4 space-y-4">
                <h2 className="text-sm font-semibold text-green-200">
                  {editingEmp ? "Editar empleado" : "Nuevo empleado"}
                </h2>
                <form onSubmit={handleSaveEmp} className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <label className="space-y-1 col-span-2 sm:col-span-1">
                      <span className="text-xs text-gray-400">Nombre completo *</span>
                      <input value={form.nombre_completo}
                        onChange={e => setForm(f => ({ ...f, nombre_completo: e.target.value }))}
                        placeholder="García López Juan" required
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50" />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Puesto</span>
                      <input value={form.puesto ?? ""}
                        onChange={e => setForm(f => ({ ...f, puesto: e.target.value }))}
                        placeholder="Contador"
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50" />
                    </label>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">RFC</span>
                      <input value={form.rfc ?? ""} onChange={e => setForm(f => ({ ...f, rfc: e.target.value.toUpperCase() }))}
                        placeholder="GALJ850101ABC" maxLength={13}
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 font-mono focus:outline-none focus:border-green-500/50" />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">CURP</span>
                      <input value={form.curp ?? ""} onChange={e => setForm(f => ({ ...f, curp: e.target.value.toUpperCase() }))}
                        placeholder="GALJ850101HDFXXX01" maxLength={18}
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 font-mono focus:outline-none focus:border-green-500/50" />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">NSS IMSS</span>
                      <input value={form.nss ?? ""} onChange={e => setForm(f => ({ ...f, nss: e.target.value }))}
                        placeholder="12345678901" maxLength={11}
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 font-mono focus:outline-none focus:border-green-500/50" />
                    </label>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Salario diario * (MXN)</span>
                      <input type="number" min="0" step="0.01" value={form.salario_diario || ""}
                        onChange={e => setForm(f => ({ ...f, salario_diario: parseFloat(e.target.value) || 0 }))}
                        placeholder="500.00" required
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50" />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Periodicidad de pago</span>
                      <SelectInput
                        value={form.periodicidad_pago ?? "quincenal"}
                        onChange={v => setForm(f => ({ ...f, periodicidad_pago: v }))}
                        options={PERIODOS.map(p => ({ value: p.value, label: p.label }))}
                        className="!rounded-lg"
                      />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Tipo de contrato</span>
                      <SelectInput
                        value={form.tipo_contrato ?? "indeterminado"}
                        onChange={v => setForm(f => ({ ...f, tipo_contrato: v }))}
                        options={CONTRATOS}
                        className="!rounded-lg"
                      />
                    </label>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Fecha de alta *</span>
                      <input type="date" value={form.fecha_alta}
                        onChange={e => setForm(f => ({ ...f, fecha_alta: e.target.value }))} required
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50" />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Departamento</span>
                      <input value={form.departamento ?? ""} onChange={e => setForm(f => ({ ...f, departamento: e.target.value }))}
                        placeholder="Administración"
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50" />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">CLABE bancaria</span>
                      <input value={form.clabe ?? ""} onChange={e => setForm(f => ({ ...f, clabe: e.target.value }))}
                        placeholder="18 dígitos" maxLength={18}
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 font-mono focus:outline-none focus:border-green-500/50" />
                    </label>
                  </div>
                  {empErr && <p className="text-xs text-red-400">{empErr}</p>}
                  <div className="flex gap-2">
                    <button type="submit" disabled={saving}
                      className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded-lg transition-colors">
                      {saving ? "Guardando..." : editingEmp ? "Actualizar" : "Agregar empleado"}
                    </button>
                    <button type="button" onClick={() => setShowForm(false)}
                      className="px-4 py-2 text-sm bg-white/5 hover:bg-white/10 text-gray-400 rounded-lg transition-colors">
                      Cancelar
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Employee table */}
            {loadingEmps ? (
              <p className="text-center text-gray-600 text-sm py-8">Cargando...</p>
            ) : empleados.length === 0 ? (
              <div className="rounded-xl border border-white/10 bg-white/3 px-4 py-12 text-center text-gray-600 text-sm">
                Sin empleados. Agrega uno manualmente o importa desde Excel.
              </div>
            ) : (
              <div className="rounded-xl border border-white/10 bg-white/3 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[700px]">
                    <thead>
                      <tr className="text-xs text-gray-500 border-b border-white/8">
                        <th className="px-4 py-2 text-left">Nombre</th>
                        <th className="px-4 py-2 text-left">RFC</th>
                        <th className="px-4 py-2 text-left">NSS</th>
                        <th className="px-4 py-2 text-left">Puesto</th>
                        <th className="px-4 py-2 text-left">Depto</th>
                        <th className="px-4 py-2 text-right">Salario diario</th>
                        <th className="px-4 py-2 text-left">Periodo</th>
                        <th className="px-4 py-2 text-left">Alta</th>
                        <th className="px-4 py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {empleados.map(emp => (
                        <tr key={emp.id} className="border-b border-white/5 last:border-0 hover:bg-white/3">
                          <td className="px-4 py-2.5 text-white">{emp.nombre_completo}</td>
                          <td className="px-4 py-2.5 font-mono text-xs text-green-400">{emp.rfc || "—"}</td>
                          <td className="px-4 py-2.5 font-mono text-xs text-gray-400">{emp.nss || "—"}</td>
                          <td className="px-4 py-2.5 text-gray-400 text-xs">{emp.puesto || "—"}</td>
                          <td className="px-4 py-2.5 text-gray-400 text-xs">{emp.departamento || "—"}</td>
                          <td className="px-4 py-2.5 text-right text-white">{MXN(emp.salario_diario)}</td>
                          <td className="px-4 py-2.5 text-gray-400 text-xs capitalize">{emp.periodicidad_pago}</td>
                          <td className="px-4 py-2.5 text-gray-400 text-xs">{emp.fecha_alta}</td>
                          <td className="px-4 py-2.5">
                            <div className="flex gap-2 justify-end">
                              <button onClick={() => openEdit(emp)}
                                className="text-xs text-gray-500 hover:text-green-400 transition-colors">Editar</button>
                              <button onClick={() => handleDelete(emp.id)}
                                className="text-xs text-gray-500 hover:text-red-400 transition-colors">Baja</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {/* ── Nómina tab ─────────────────────────────────────────────── */}
        {tab === "nomina" && clienteId && (
          <>
            <div className="rounded-xl border border-white/10 bg-white/3 p-4 space-y-3">
              <h2 className="text-sm font-semibold text-green-200">Parámetros de nómina</h2>
              <form onSubmit={handleRunNomina} className="space-y-3">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Periodicidad</span>
                    <SelectInput
                      value={nomReq.periodo}
                      onChange={v => setNomReq(r => ({ ...r, periodo: v }))}
                      options={PERIODOS.map(p => ({ value: p.value, label: p.label }))}
                      className="!rounded-lg"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Fecha inicio</span>
                    <input type="date" value={nomReq.fecha_inicio}
                      onChange={e => setNomReq(r => ({ ...r, fecha_inicio: e.target.value }))}
                      className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50" />
                  </label>
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Fecha fin</span>
                    <input type="date" value={nomReq.fecha_fin}
                      onChange={e => setNomReq(r => ({ ...r, fecha_fin: e.target.value }))}
                      className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50" />
                  </label>
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Vales despensa global</span>
                    <input type="number" min="0" step="0.01" value={nomReq.vales_despensa_global || ""}
                      onChange={e => setNomReq(r => ({ ...r, vales_despensa_global: parseFloat(e.target.value) || 0 }))}
                      placeholder="0.00"
                      className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50" />
                  </label>
                </div>
                {nomErr && <p className="text-xs text-red-400">{nomErr}</p>}
                <div className="flex gap-2">
                  <button type="submit" disabled={runningNom || empleados.length === 0}
                    className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded-lg transition-colors">
                    {runningNom ? "Calculando..." : `Calcular nómina (${empleados.length} empleados)`}
                  </button>
                  {nomResult && (
                    <button type="button" onClick={handleExportExcel} disabled={exporting}
                      className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg transition-colors">
                      {exporting ? "Exportando..." : "Exportar Excel"}
                    </button>
                  )}
                </div>
              </form>
            </div>

            {nomResult && (
              <>
                {/* Totales */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: "Total percepciones",  value: nomResult.totales.total_percepciones,  color: "text-green-300" },
                    { label: "Total deducciones",   value: nomResult.totales.total_deducciones,   color: "text-red-300" },
                    { label: "Total neto a pagar",  value: nomResult.totales.total_neto,          color: "text-white" },
                    { label: "Costo total empresa", value: nomResult.totales.costo_total_empresa, color: "text-yellow-300" },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="rounded-xl border border-white/10 bg-white/3 px-4 py-3">
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className={`text-lg font-semibold ${color} mt-1`}>{MXN(value)}</p>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: "ISR retenido total",   value: nomResult.totales.total_isr },
                    { label: "IMSS cuota obrera",    value: nomResult.totales.total_imss_obrero },
                    { label: "IMSS cuota patronal",  value: nomResult.totales.total_imss_patronal },
                    { label: "INFONAVIT patronal",   value: nomResult.totales.total_infonavit },
                  ].map(({ label, value }) => (
                    <div key={label} className="rounded-xl border border-white/10 bg-white/3 px-4 py-3">
                      <p className="text-xs text-gray-500">{label}</p>
                      <p className="text-sm font-medium text-gray-300 mt-1">{MXN(value)}</p>
                    </div>
                  ))}
                </div>

                {/* Detalle por empleado */}
                <div className="rounded-xl border border-white/10 bg-white/3 overflow-hidden">
                  <div className="px-4 py-2.5 border-b border-white/8 flex items-center justify-between">
                    <h2 className="text-sm font-semibold text-green-200">
                      Detalle por empleado — {nomResult.total_empleados} empleados
                    </h2>
                    <span className="text-xs text-gray-500 capitalize">{nomResult.periodo}</span>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm min-w-[900px]">
                      <thead>
                        <tr className="text-xs text-gray-500 border-b border-white/8">
                          <th className="px-4 py-2 text-left">Nombre</th>
                          <th className="px-4 py-2 text-left">RFC</th>
                          <th className="px-4 py-2 text-right">Sal. mensual</th>
                          <th className="px-4 py-2 text-right">Percepciones</th>
                          <th className="px-4 py-2 text-right">ISR</th>
                          <th className="px-4 py-2 text-right">IMSS obrero</th>
                          <th className="px-4 py-2 text-right">Neto a pagar</th>
                          <th className="px-4 py-2 text-right">Costo empresa</th>
                        </tr>
                      </thead>
                      <tbody>
                        {nomResult.empleados.map(emp => (
                          <tr key={emp.id} className="border-b border-white/5 last:border-0 hover:bg-white/3">
                            <td className="px-4 py-2.5 text-white text-xs">{emp.nombre_completo}</td>
                            <td className="px-4 py-2.5 font-mono text-xs text-green-400">{emp.rfc || "—"}</td>
                            <td className="px-4 py-2.5 text-right text-xs text-gray-400">{MXN(emp.salario_mensual)}</td>
                            <td className="px-4 py-2.5 text-right text-xs text-green-300">{MXN(emp.percepciones.total_percepciones)}</td>
                            <td className="px-4 py-2.5 text-right text-xs text-red-400">{MXN(emp.deducciones.isr_retenido)}</td>
                            <td className="px-4 py-2.5 text-right text-xs text-red-400">{MXN(emp.deducciones.imss_cuota_obrero)}</td>
                            <td className="px-4 py-2.5 text-right text-sm font-semibold text-white">{MXN(emp.neto_a_pagar)}</td>
                            <td className="px-4 py-2.5 text-right text-xs text-yellow-300">{MXN(emp.costo_empresa.costo_total_empresa)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
