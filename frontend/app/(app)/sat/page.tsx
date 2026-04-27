"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, SatCredential, SatJob, SatCfdi } from "@/lib/api";
import { SelectInput } from "@/components/ui/SelectInput";

const TIPO_OPTS = [
  { value: "", label: "Todos" },
  { value: "I", label: "I — Ingreso" },
  { value: "E", label: "E — Egreso" },
  { value: "N", label: "N — Nómina" },
  { value: "P", label: "P — Pago" },
  { value: "T", label: "T — Traslado" },
];

const STATUS_BADGE: Record<string, string> = {
  pending:    "bg-yellow-500/15 text-yellow-300 border-yellow-500/25",
  processing: "bg-blue-500/15 text-blue-300 border-blue-500/25",
  completed:  "bg-green-500/15 text-green-300 border-green-500/25",
  error:      "bg-red-500/15 text-red-300 border-red-500/25",
};

const TIPO_LABEL: Record<string, string> = {
  I: "Ingreso", E: "Egreso", N: "Nómina", P: "Pago", T: "Traslado",
};

export default function SatPage() {
  const [tab, setTab] = useState<"creds" | "jobs" | "cfdis">("creds");

  // Credentials
  const [creds, setCreds] = useState<SatCredential[]>([]);
  const [cerFile, setCerFile] = useState<File | null>(null);
  const [keyFile, setKeyFile] = useState<File | null>(null);
  const [keyPwd, setKeyPwd] = useState("");
  const [alias, setAlias] = useState("");
  const [uploadErr, setUploadErr] = useState("");
  const [uploading, setUploading] = useState(false);

  // Download form
  const [credId, setCredId] = useState<number | "">("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [tipoCmp, setTipoCmp] = useState("");
  const [downloadErr, setDownloadErr] = useState("");
  const [downloading, setDownloading] = useState(false);

  // Jobs
  const [jobs, setJobs] = useState<SatJob[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // CFDIs
  const [cfdis, setCfdis] = useState<SatCfdi[]>([]);
  const [cfdiTotal, setCfdiTotal] = useState(0);
  const [cfdiOffset, setCfdiOffset] = useState(0);
  const [cfdiTipo, setCfdiTipo] = useState("");

  const loadCreds = useCallback(async () => {
    try { setCreds(await api.sat.listCredentials()); } catch {}
  }, []);

  const loadJobs = useCallback(async () => {
    try { setJobs(await api.sat.listJobs()); } catch {}
  }, []);

  const loadCfdis = useCallback(async (offset = 0, tipo = "") => {
    try {
      const res = await api.sat.listCfdis({ limit: 50, offset, tipo: tipo || undefined });
      setCfdis(res.items);
      setCfdiTotal(res.total);
      setCfdiOffset(offset);
    } catch {}
  }, []);

  useEffect(() => {
    loadCreds();
    loadJobs();
    loadCfdis();
  }, [loadCreds, loadJobs, loadCfdis]);

  // Poll active jobs every 10s
  useEffect(() => {
    const hasActive = jobs.some(j => j.status === "pending" || j.status === "processing");
    if (hasActive && !pollRef.current) {
      pollRef.current = setInterval(loadJobs, 10000);
    } else if (!hasActive && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
      // Refresh CFDIs when a job finishes
      loadCfdis(cfdiOffset, cfdiTipo);
    }
    return () => {};
  }, [jobs, loadJobs, loadCfdis, cfdiOffset, cfdiTipo]);

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  async function handleUploadCred(e: React.FormEvent) {
    e.preventDefault();
    if (!cerFile || !keyFile || !keyPwd) {
      setUploadErr("Selecciona los archivos .cer y .key, e ingresa la contraseña");
      return;
    }
    setUploadErr("");
    setUploading(true);
    const form = new FormData();
    form.append("cer_file", cerFile);
    form.append("key_file", keyFile);
    form.append("key_password", keyPwd);
    form.append("alias", alias);
    try {
      await api.sat.uploadCredential(form);
      setCerFile(null); setKeyFile(null); setKeyPwd(""); setAlias("");
      await loadCreds();
    } catch (err: unknown) {
      setUploadErr(err instanceof Error ? err.message : "Error al subir credencial");
    } finally {
      setUploading(false);
    }
  }

  async function handleDeleteCred(id: number) {
    if (!confirm("¿Eliminar esta e.firma? Los jobs activos seguirán corriendo.")) return;
    try { await api.sat.deleteCredential(id); await loadCreds(); } catch {}
  }

  async function handleDownload(e: React.FormEvent) {
    e.preventDefault();
    if (!credId || !dateFrom || !dateTo) {
      setDownloadErr("Selecciona credencial y rango de fechas");
      return;
    }
    setDownloadErr("");
    setDownloading(true);
    try {
      await api.sat.requestDownload({
        credential_id: Number(credId),
        date_from: dateFrom,
        date_to: dateTo,
        tipo_comprobante: (tipoCmp as "I"|"E"|"T"|"N"|"P") || undefined,
      });
      setTab("jobs");
      await loadJobs();
    } catch (err: unknown) {
      setDownloadErr(err instanceof Error ? err.message : "Error al solicitar descarga");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/8">
        <h1 className="text-lg font-semibold text-white">Descarga Masiva SAT</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          Conecta tu e.firma y descarga todos tus CFDIs directamente del SAT
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-6 pt-3 pb-0 border-b border-white/8">
        {(["creds", "jobs", "cfdis"] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm rounded-t-lg border-b-2 transition-all ${
              tab === t
                ? "text-green-300 border-green-400 bg-green-500/8"
                : "text-gray-500 border-transparent hover:text-gray-300"
            }`}
          >
            {t === "creds" ? "🔑 e.firma" : t === "jobs" ? "📥 Descargas" : "🧾 CFDIs"}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">

        {/* ── Credentials tab ────────────────────────────────────────── */}
        {tab === "creds" && (
          <>
            <div className="rounded-xl border border-white/10 bg-white/3 p-4 space-y-3">
              <h2 className="text-sm font-semibold text-green-200">Registrar e.firma</h2>
              <p className="text-xs text-gray-500">
                Tu llave privada se cifra con AES-128 antes de guardarse. Nunca se almacena en texto plano.
              </p>
              <form onSubmit={handleUploadCred} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Certificado (.cer)</span>
                    <input
                      type="file" accept=".cer"
                      onChange={ev => setCerFile(ev.target.files?.[0] ?? null)}
                      className="block w-full text-xs text-gray-300 file:mr-2 file:py-1 file:px-3 file:rounded file:border-0 file:bg-green-700/40 file:text-green-200 hover:file:bg-green-700/60"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Llave privada (.key)</span>
                    <input
                      type="file" accept=".key"
                      onChange={ev => setKeyFile(ev.target.files?.[0] ?? null)}
                      className="block w-full text-xs text-gray-300 file:mr-2 file:py-1 file:px-3 file:rounded file:border-0 file:bg-green-700/40 file:text-green-200 hover:file:bg-green-700/60"
                    />
                  </label>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Contraseña de llave</span>
                    <input
                      type="password" value={keyPwd} onChange={e => setKeyPwd(e.target.value)}
                      placeholder="Contraseña del archivo .key"
                      className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50"
                    />
                  </label>
                  <label className="space-y-1">
                    <span className="text-xs text-gray-400">Alias (opcional)</span>
                    <input
                      type="text" value={alias} onChange={e => setAlias(e.target.value)}
                      placeholder="Ej. Empresa Principal"
                      className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-600 focus:outline-none focus:border-green-500/50"
                    />
                  </label>
                </div>
                {uploadErr && <p className="text-xs text-red-400">{uploadErr}</p>}
                <button
                  type="submit" disabled={uploading}
                  className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded-lg transition-colors"
                >
                  {uploading ? "Verificando..." : "Registrar e.firma"}
                </button>
              </form>
            </div>

            {creds.length > 0 && (
              <div className="rounded-xl border border-white/10 bg-white/3 overflow-hidden">
                <div className="px-4 py-2.5 border-b border-white/8">
                  <h2 className="text-sm font-semibold text-green-200">Credenciales registradas</h2>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-gray-500 border-b border-white/8">
                      <th className="px-4 py-2 text-left">RFC</th>
                      <th className="px-4 py-2 text-left">Alias</th>
                      <th className="px-4 py-2 text-left">Vigente hasta</th>
                      <th className="px-4 py-2 text-left"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {creds.map(c => (
                      <tr key={c.id} className="border-b border-white/5 last:border-0 hover:bg-white/3">
                        <td className="px-4 py-2.5 font-mono text-xs text-green-300">{c.rfc}</td>
                        <td className="px-4 py-2.5 text-gray-300">{c.alias || "—"}</td>
                        <td className="px-4 py-2.5 text-gray-400 text-xs">
                          {c.valid_to ? new Date(c.valid_to).toLocaleDateString("es-MX") : "—"}
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <button onClick={() => handleDeleteCred(c.id)}
                            className="text-xs text-red-400 hover:text-red-300 transition-colors">
                            Eliminar
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Download request form */}
            {creds.length > 0 && (
              <div className="rounded-xl border border-white/10 bg-white/3 p-4 space-y-3">
                <h2 className="text-sm font-semibold text-green-200">Solicitar descarga de CFDIs</h2>
                <form onSubmit={handleDownload} className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">e.firma</span>
                      <SelectInput
                        value={String(credId)}
                        onChange={v => setCredId(Number(v))}
                        options={[{ value: "", label: "Seleccionar..." }, ...creds.map(c => ({ value: String(c.id), label: c.alias || c.rfc }))]}
                        className="!rounded-lg"
                      />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Tipo de comprobante</span>
                      <SelectInput
                        value={tipoCmp}
                        onChange={setTipoCmp}
                        options={TIPO_OPTS}
                        className="!rounded-lg"
                      />
                    </label>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Fecha inicio</span>
                      <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50" />
                    </label>
                    <label className="space-y-1">
                      <span className="text-xs text-gray-400">Fecha fin (máx 1 año)</span>
                      <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-green-500/50" />
                    </label>
                  </div>
                  {downloadErr && <p className="text-xs text-red-400">{downloadErr}</p>}
                  <button type="submit" disabled={downloading}
                    className="px-4 py-2 text-sm bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white rounded-lg transition-colors">
                    {downloading ? "Enviando al SAT..." : "Iniciar descarga"}
                  </button>
                </form>
              </div>
            )}
          </>
        )}

        {/* ── Jobs tab ───────────────────────────────────────────────── */}
        {tab === "jobs" && (
          <div className="rounded-xl border border-white/10 bg-white/3 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/8">
              <h2 className="text-sm font-semibold text-green-200">Historial de descargas</h2>
              <button onClick={loadJobs} className="text-xs text-gray-500 hover:text-gray-300">Actualizar</button>
            </div>
            {jobs.length === 0 ? (
              <p className="px-4 py-8 text-center text-gray-600 text-sm">
                Sin descargas aún. Ve a e.firma para solicitar una.
              </p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-gray-500 border-b border-white/8">
                    <th className="px-4 py-2 text-left">RFC</th>
                    <th className="px-4 py-2 text-left">Período</th>
                    <th className="px-4 py-2 text-left">Tipo</th>
                    <th className="px-4 py-2 text-left">Estado</th>
                    <th className="px-4 py-2 text-right">CFDIs</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map(j => (
                    <tr key={j.id} className="border-b border-white/5 last:border-0 hover:bg-white/3">
                      <td className="px-4 py-3 font-mono text-xs text-green-300">{j.rfc}</td>
                      <td className="px-4 py-3 text-xs text-gray-400">
                        {j.date_from} → {j.date_to}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400">
                        {j.tipo_comprobante ? TIPO_LABEL[j.tipo_comprobante] ?? j.tipo_comprobante : "Todos"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-xs border ${STATUS_BADGE[j.status] ?? "bg-gray-500/15 text-gray-300 border-gray-500/25"}`}>
                          {j.status === "processing" && j.packages_total > 0
                            ? `${j.progress}% (${j.packages_downloaded}/${j.packages_total})`
                            : j.status}
                        </span>
                        {j.error_msg && (
                          <p className="text-xs text-red-400 mt-0.5 max-w-xs truncate" title={j.error_msg}>
                            {j.error_msg}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-gray-300">{j.total_cfdi ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* ── CFDIs tab ──────────────────────────────────────────────── */}
        {tab === "cfdis" && (
          <>
            <div className="flex items-center gap-3">
              <SelectInput
                value={cfdiTipo}
                onChange={v => { setCfdiTipo(v); loadCfdis(0, v); }}
                options={TIPO_OPTS}
                className="!rounded-lg !py-1.5 !text-xs min-w-[140px]"
              />
              <span className="text-xs text-gray-600">{cfdiTotal} CFDIs descargados</span>
            </div>

            {cfdis.length === 0 ? (
              <div className="rounded-xl border border-white/10 bg-white/3 px-4 py-12 text-center">
                <p className="text-gray-600 text-sm">Sin CFDIs descargados. Inicia una descarga desde la pestaña e.firma.</p>
              </div>
            ) : (
              <div className="rounded-xl border border-white/10 bg-white/3 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm min-w-[700px]">
                    <thead>
                      <tr className="text-xs text-gray-500 border-b border-white/8">
                        <th className="px-4 py-2 text-left">Fecha</th>
                        <th className="px-4 py-2 text-left">Emisor</th>
                        <th className="px-4 py-2 text-left">Receptor</th>
                        <th className="px-4 py-2 text-left">Tipo</th>
                        <th className="px-4 py-2 text-right">Total</th>
                        <th className="px-4 py-2 text-left">UUID</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cfdis.map(c => (
                        <tr key={c.id} className="border-b border-white/5 last:border-0 hover:bg-white/3">
                          <td className="px-4 py-2.5 text-xs text-gray-400">
                            {c.fecha_emision ? new Date(c.fecha_emision).toLocaleDateString("es-MX") : "—"}
                          </td>
                          <td className="px-4 py-2.5 text-xs">
                            <div className="font-mono text-green-400">{c.rfc_emisor}</div>
                            <div className="text-gray-500 truncate max-w-[140px]" title={c.nombre_emisor ?? ""}>{c.nombre_emisor}</div>
                          </td>
                          <td className="px-4 py-2.5 text-xs">
                            <div className="font-mono text-blue-400">{c.rfc_receptor}</div>
                            <div className="text-gray-500 truncate max-w-[140px]" title={c.nombre_receptor ?? ""}>{c.nombre_receptor}</div>
                          </td>
                          <td className="px-4 py-2.5 text-xs text-gray-400">
                            {c.tipo_comprobante ? TIPO_LABEL[c.tipo_comprobante] ?? c.tipo_comprobante : "—"}
                          </td>
                          <td className="px-4 py-2.5 text-right text-sm font-medium text-white">
                            {c.total != null
                              ? new Intl.NumberFormat("es-MX", { style: "currency", currency: c.moneda ?? "MXN" }).format(c.total)
                              : "—"}
                          </td>
                          <td className="px-4 py-2.5">
                            <a
                              href={`/api/sat/cfdis/${c.uuid}/xml`}
                              className="font-mono text-[10px] text-gray-600 hover:text-green-400 transition-colors truncate block max-w-[120px]"
                              title={c.uuid}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {c.uuid.slice(0, 8)}…
                            </a>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {cfdiTotal > 50 && (
                  <div className="flex justify-between items-center px-4 py-2.5 border-t border-white/8 text-xs text-gray-500">
                    <span>{cfdiOffset + 1}–{Math.min(cfdiOffset + 50, cfdiTotal)} de {cfdiTotal}</span>
                    <div className="flex gap-2">
                      <button disabled={cfdiOffset === 0}
                        onClick={() => loadCfdis(Math.max(0, cfdiOffset - 50), cfdiTipo)}
                        className="px-3 py-1 rounded bg-white/5 disabled:opacity-30 hover:bg-white/10">
                        ← Anterior
                      </button>
                      <button disabled={cfdiOffset + 50 >= cfdiTotal}
                        onClick={() => loadCfdis(cfdiOffset + 50, cfdiTipo)}
                        className="px-3 py-1 rounded bg-white/5 disabled:opacity-30 hover:bg-white/10">
                        Siguiente →
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
