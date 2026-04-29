"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api, type Cliente, DocumentoItem, DiotProveedor, ResumenFiscal, UploadResult } from "@/lib/api";

const TIPO_MAP: Record<string, string> = {
  I: "Ingreso",
  E: "Egreso",
  T: "Traslado",
  N: "Nómina",
  P: "Pago",
};

const ESTADO_COLOR: Record<string, string> = {
  extraido: "bg-green-900/40 text-green-300 border border-green-800/30",
  pendiente: "bg-yellow-900/40 text-yellow-300 border border-yellow-800/30",
  procesando: "bg-blue-900/40 text-blue-300 border border-blue-800/30",
  error: "bg-red-900/40 text-red-300 border border-red-800/30",
};

const SAT_COLOR: Record<string, string> = {
  Vigente: "bg-emerald-900/40 text-emerald-300 border border-emerald-800/30",
  Cancelado: "bg-red-900/50 text-red-300 border border-red-700/40",
  "No Encontrado": "bg-orange-900/40 text-orange-300 border border-orange-800/30",
  error: "bg-white/5 text-gray-500 border border-white/8",
};

function fmt(n: number | null | undefined) {
  if (n == null) return "—";
  return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(n);
}

export default function DocumentosPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const clienteId = Number(id);

  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [docs, setDocs] = useState<DocumentoItem[]>([]);
  const [resumen, setResumen] = useState<ResumenFiscal | null>(null);
  const [diot, setDiot] = useState<DiotProveedor[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [tab, setTab] = useState<"documentos" | "resumen" | "diot">("documentos");
  const [exportingExcel, setExportingExcel] = useState(false);
  const [exportingDiot, setExportingDiot] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadData = async () => {
    try {
      const [c, d, r] = await Promise.all([
        api.clients.get(clienteId),
        api.documentos.list(clienteId),
        api.documentos.resumen(clienteId),
      ]);
      setCliente(c);
      setDocs(d);
      setResumen(r);
    } catch {
      router.push("/clientes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [clienteId]);

  const loadDiot = async () => {
    if (diot !== null) return;
    const result = await api.documentos.diot(clienteId);
    setDiot(result.proveedores);
  };

  const handleExportExcel = async () => {
    setExportingExcel(true);
    try {
      const blob = await api.documentos.exportarExcel(clienteId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `documentos_cliente_${clienteId}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExportingExcel(false);
    }
  };

  const handleExportDiotTxt = async () => {
    setExportingDiot(true);
    try {
      const blob = await api.documentos.diotTxt(clienteId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DIOT_cliente_${clienteId}.txt`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExportingDiot(false);
    }
  };

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const arr = Array.from(files);
    setUploading(true);
    setUploadResult(null);
    try {
      const result = await api.documentos.upload(clienteId, arr);
      setUploadResult(result);
      await loadData();
    } catch (e: unknown) {
      setUploadResult({
        procesados: 0,
        resultados: [{ archivo: "—", estado: "error", detalle: String(e) }],
      });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm("¿Eliminar este documento?")) return;
    await api.documentos.delete(docId);
    setDocs((prev) => prev.filter((d) => d.id !== docId));
    const r = await api.documentos.resumen(clienteId);
    setResumen(r);
  };

  const sendToAgent = (doc: DocumentoItem) => {
    const ctx = `Documento: ${doc.nombre_archivo}\nUUID: ${doc.uuid_cfdi ?? "N/A"}\nEmisor: ${doc.emisor_rfc} – ${doc.emisor_nombre}\nReceptor: ${doc.receptor_rfc}\nTotal: ${fmt(doc.total)}\nIVA: ${fmt(doc.iva_trasladado)}\nFecha: ${doc.fecha_emision ?? "N/A"}`;
    localStorage.setItem("cmx_doc_ctx", ctx);
    router.push(`/chat?doc=${doc.id}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Breadcrumb + cliente */}
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <Link href="/clientes" className="hover:text-green-400 transition-colors">Clientes</Link>
        <span>/</span>
        <Link href={`/clientes/${clienteId}`} className="hover:text-green-400 transition-colors">
          {cliente?.razon_social ?? "…"}
        </Link>
        <span>/</span>
        <span className="text-gray-400">Documentos</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 rounded-xl bg-green-900/40 border border-green-800/30 flex items-center justify-center text-lg font-bold text-green-300">
              {cliente?.razon_social?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div>
              <h1 className="text-xl font-bold text-green-100">{cliente?.razon_social}</h1>
              <p className="text-xs font-mono text-gray-500">{cliente?.rfc}</p>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Documentos fiscales · {docs.length} archivo{docs.length !== 1 ? "s" : ""}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportExcel}
            disabled={exportingExcel || docs.length === 0}
            className="border border-white/10 text-gray-300 hover:bg-white/5 px-3 py-2 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
          >
            {exportingExcel ? "Exportando..." : "Excel"}
          </button>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="bg-green-700 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {uploading ? "Subiendo..." : "+ Subir documentos"}
          </button>
        </div>
        <input
          ref={fileRef}
          type="file"
          multiple
          accept=".xml,.pdf,.jpg,.jpeg,.png,.webp,.tiff"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files); }}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          dragOver ? "border-green-500/60 bg-green-500/8" : "border-white/10 hover:border-green-500/30 hover:bg-green-500/5"
        }`}
      >
        <div className="text-4xl mb-2">📂</div>
        <p className="text-gray-400 font-medium">
          Arrastra aquí una carpeta o archivos
        </p>
        <p className="text-sm text-gray-600 mt-1">
          XML (CFDI), PDF, JPG, PNG — hasta 10 MB por archivo
        </p>
      </div>

      {/* Upload result banner */}
      {uploadResult && (
        <div className="border border-white/10 bg-white/3 rounded-xl p-4 space-y-2">
          <p className="font-medium text-green-200">
            Procesados: {uploadResult.procesados} archivo{uploadResult.procesados !== 1 ? "s" : ""}
          </p>
          <div className="space-y-1">
            {uploadResult.resultados.map((r, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ESTADO_COLOR[r.estado] ?? "bg-white/10 text-gray-300"}`}>
                  {r.estado}
                </span>
                <span className="text-gray-400 truncate max-w-xs">{r.archivo}</span>
                {r.sat_estado && (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SAT_COLOR[r.sat_estado] ?? "bg-white/5 text-gray-500"}`}>
                    SAT: {r.sat_estado}
                  </span>
                )}
                {r.total != null && (
                  <span className="text-gray-500 ml-auto">{fmt(r.total)}</span>
                )}
                {r.detalle && <span className="text-red-500 ml-auto">{r.detalle}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-white/8 flex gap-1">
        {([
          ["documentos", "Listado"],
          ["resumen", "Resumen fiscal"],
          ["diot", "DIOT"],
        ] as const).map(([t, label]) => (
          <button
            key={t}
            onClick={() => { setTab(t); if (t === "diot") loadDiot(); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors rounded-t-lg ${
              tab === t
                ? "border-green-400 text-green-300 bg-green-500/8"
                : "border-transparent text-gray-500 hover:text-gray-300"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab: Listado */}
      {tab === "documentos" && (
        <div className="rounded-xl border border-white/8 bg-white/3 overflow-hidden">
          {docs.length === 0 ? (
            <div className="p-12 text-center text-gray-500">
              <div className="text-5xl mb-3">🗂️</div>
              <p>Sin documentos aún — sube XMLs, PDFs o imágenes de facturas</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/8 text-left text-gray-500 text-xs uppercase">
                  <th className="px-4 py-3">Archivo</th>
                  <th className="px-4 py-3">Tipo</th>
                  <th className="px-4 py-3">Emisor</th>
                  <th className="px-4 py-3">Fecha</th>
                  <th className="px-4 py-3 text-right">Total</th>
                  <th className="px-4 py-3 text-right">IVA</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <tr key={d.id} className="border-b border-white/5 last:border-0 hover:bg-white/3">
                    <td className="px-4 py-3">
                      <div className="font-medium text-green-100 max-w-[180px] truncate" title={d.nombre_archivo}>
                        {d.nombre_archivo}
                      </div>
                      {d.uuid_cfdi && (
                        <div className="text-xs text-gray-500 font-mono">{d.uuid_cfdi.slice(0, 18)}…</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 bg-white/8 border border-white/10 rounded text-xs text-gray-300">
                        {d.tipo_comprobante ? TIPO_MAP[d.tipo_comprobante] ?? d.tipo_comprobante : d.tipo_archivo}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-gray-300 font-mono text-xs">{d.emisor_rfc ?? "—"}</div>
                      {d.emisor_nombre && (
                        <div className="text-xs text-gray-500 max-w-[140px] truncate">{d.emisor_nombre}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {d.fecha_emision ? new Date(d.fecha_emision).toLocaleDateString("es-MX") : "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-green-200">{fmt(d.total)}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{fmt(d.iva_trasladado)}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium w-fit ${ESTADO_COLOR[d.estado] ?? "bg-white/8 text-gray-400"}`}>
                          {d.estado}
                        </span>
                        {d.sat_estado && (
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium w-fit ${SAT_COLOR[d.sat_estado] ?? "bg-white/5 text-gray-500 border border-white/8"}`}
                            title={d.sat_cancelable ?? undefined}
                          >
                            SAT: {d.sat_estado}
                          </span>
                        )}
                        {d.error_msg && (
                          <div className="text-xs text-red-400 max-w-[120px] truncate" title={d.error_msg}>
                            {d.error_msg}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => sendToAgent(d)}
                          title="Enviar al agente fiscal"
                          className="text-green-400 hover:text-green-300 text-xs px-2 py-1 border border-green-800/40 rounded transition-colors"
                        >
                          Consultar
                        </button>
                        <button
                          onClick={() => handleDelete(d.id)}
                          title="Eliminar"
                          className="text-red-400 hover:text-red-300 text-xs"
                        >
                          ✕
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Tab: Resumen fiscal */}
      {tab === "resumen" && resumen && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-white/8 bg-white/3 p-5">
              <p className="text-xs text-gray-500 uppercase font-medium mb-1">Utilidad bruta</p>
              <p className={`text-2xl font-bold ${resumen.utilidad_bruta >= 0 ? "text-green-400" : "text-red-400"}`}>
                {fmt(resumen.utilidad_bruta)}
              </p>
              <p className="text-xs text-gray-500 mt-1">Ingresos − Egresos</p>
            </div>
            <div className="rounded-xl border border-white/8 bg-white/3 p-5">
              <p className="text-xs text-gray-500 uppercase font-medium mb-1">IVA neto a pagar</p>
              <p className={`text-2xl font-bold ${resumen.iva_neto_a_pagar >= 0 ? "text-orange-400" : "text-green-400"}`}>
                {fmt(resumen.iva_neto_a_pagar)}
              </p>
              <p className="text-xs text-gray-500 mt-1">IVA cobrado − IVA pagado</p>
            </div>
            <div className="rounded-xl border border-white/8 bg-white/3 p-5">
              <p className="text-xs text-gray-500 uppercase font-medium mb-1">ISR retenido total</p>
              <p className="text-2xl font-bold text-green-200">{fmt(resumen.isr_retenido_total)}</p>
              <p className="text-xs text-gray-500 mt-1">{resumen.total_documentos} documentos procesados</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="rounded-xl border border-white/8 bg-white/3 p-5">
              <h3 className="font-semibold text-green-200 mb-4 flex items-center gap-2">
                <span className="text-green-400">↑</span> Ingresos ({resumen.ingresos.cantidad} facturas)
              </h3>
              <table className="w-full text-sm">
                <tbody className="divide-y divide-white/5">
                  {[
                    ["Subtotal", resumen.ingresos.subtotal],
                    ["Descuento", -resumen.ingresos.descuento],
                    ["IVA trasladado", resumen.ingresos.iva_trasladado],
                    ["IVA retenido", -resumen.ingresos.iva_retenido],
                    ["ISR retenido", -resumen.ingresos.isr_retenido],
                  ].map(([label, val]) => (
                    <tr key={String(label)}>
                      <td className="py-2 text-gray-500">{label}</td>
                      <td className="py-2 text-right font-medium text-gray-300">{fmt(val as number)}</td>
                    </tr>
                  ))}
                  <tr className="font-bold">
                    <td className="py-2 text-gray-200">Total ingresos</td>
                    <td className="py-2 text-right text-green-400">{fmt(resumen.ingresos.total)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="rounded-xl border border-white/8 bg-white/3 p-5">
              <h3 className="font-semibold text-green-200 mb-4 flex items-center gap-2">
                <span className="text-red-400">↓</span> Egresos ({resumen.egresos.cantidad} facturas)
              </h3>
              <table className="w-full text-sm">
                <tbody className="divide-y divide-white/5">
                  {[
                    ["Subtotal", resumen.egresos.subtotal],
                    ["Descuento", -resumen.egresos.descuento],
                    ["IVA trasladado", resumen.egresos.iva_trasladado],
                    ["IVA retenido", -resumen.egresos.iva_retenido],
                    ["ISR retenido", -resumen.egresos.isr_retenido],
                  ].map(([label, val]) => (
                    <tr key={String(label)}>
                      <td className="py-2 text-gray-500">{label}</td>
                      <td className="py-2 text-right font-medium text-gray-300">{fmt(val as number)}</td>
                    </tr>
                  ))}
                  <tr className="font-bold">
                    <td className="py-2 text-gray-200">Total egresos</td>
                    <td className="py-2 text-right text-red-400">{fmt(resumen.egresos.total)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4 text-sm text-green-300">
            Abre cualquier documento y pulsa <strong>Consultar</strong> para que el agente fiscal analice ese CFDI — deducciones, alertas SAT, y más.
          </div>
        </div>
      )}

      {/* Tab: DIOT */}
      {tab === "diot" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-green-100">DIOT — Declaración Informativa de Operaciones con Terceros</h2>
              <p className="text-sm text-gray-500 mt-0.5">Art. 32-B LIVA — Proveedores de egresos agrupados por RFC</p>
            </div>
            <button
              onClick={handleExportDiotTxt}
              disabled={exportingDiot || !diot || diot.length === 0}
              className="border border-white/10 text-gray-300 hover:bg-white/5 px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
            >
              {exportingDiot ? "Generando..." : "Descargar TXT (SAT)"}
            </button>
          </div>

          {diot === null ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin w-6 h-6 border-4 border-green-500 border-t-transparent rounded-full" />
            </div>
          ) : diot.length === 0 ? (
            <div className="rounded-xl border border-white/8 bg-white/3 p-12 text-center text-gray-500">
              <div className="text-5xl mb-3">📋</div>
              <p>Sin proveedores de egresos — sube facturas de gastos para generar la DIOT</p>
            </div>
          ) : (
            <div className="rounded-xl border border-white/8 bg-white/3 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/8 text-left text-gray-500 text-xs uppercase">
                    <th className="px-4 py-3">RFC Proveedor</th>
                    <th className="px-4 py-3">Nombre</th>
                    <th className="px-4 py-3 text-center">Facturas</th>
                    <th className="px-4 py-3 text-right">Monto operaciones</th>
                    <th className="px-4 py-3 text-right">IVA 16% pagado</th>
                    <th className="px-4 py-3 text-right">IVA retenido</th>
                    <th className="px-4 py-3 text-center">Tipo</th>
                  </tr>
                </thead>
                <tbody>
                  {diot.map((p) => (
                    <tr key={p.rfc} className="border-b border-white/5 last:border-0 hover:bg-white/3">
                      <td className="px-4 py-3 font-mono text-sm text-green-100">{p.rfc}</td>
                      <td className="px-4 py-3 text-gray-300 max-w-[200px] truncate" title={p.nombre}>{p.nombre || "—"}</td>
                      <td className="px-4 py-3 text-center text-gray-400">{p.cantidad_facturas}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-200">{fmt(p.monto_operaciones)}</td>
                      <td className="px-4 py-3 text-right text-gray-400">{fmt(p.iva_16_pagado)}</td>
                      <td className="px-4 py-3 text-right text-gray-400">{fmt(p.iva_retenido)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-0.5 bg-white/8 border border-white/10 rounded-full text-xs text-gray-300">
                          {p.tipo_tercero === "04" ? "Nacional" : "Extranjero"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-white/8 bg-white/3 font-semibold text-sm">
                    <td className="px-4 py-3 text-gray-400" colSpan={3}>Total ({diot.length} proveedores)</td>
                    <td className="px-4 py-3 text-right text-gray-200">{fmt(diot.reduce((s, p) => s + p.monto_operaciones, 0))}</td>
                    <td className="px-4 py-3 text-right text-gray-200">{fmt(diot.reduce((s, p) => s + p.iva_16_pagado, 0))}</td>
                    <td className="px-4 py-3 text-right text-gray-200">{fmt(diot.reduce((s, p) => s + p.iva_retenido, 0))}</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          )}

          <div className="rounded-xl border border-yellow-800/30 bg-yellow-900/20 p-4 text-sm text-yellow-300">
            <strong>Nota:</strong> El TXT generado sigue el formato de 19 columnas separadas por pipes requerido por el portal del SAT (DIOT). Verifica siempre los montos antes de presentar.
          </div>
        </div>
      )}
    </div>
    </div>
  );
}
