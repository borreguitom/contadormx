"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, DocumentoItem, DiotProveedor, ResumenFiscal, UploadResult } from "@/lib/api";

const TIPO_MAP: Record<string, string> = {
  I: "Ingreso",
  E: "Egreso",
  T: "Traslado",
  N: "Nómina",
  P: "Pago",
};

const ESTADO_COLOR: Record<string, string> = {
  extraido: "bg-green-100 text-green-800",
  pendiente: "bg-yellow-100 text-yellow-800",
  procesando: "bg-blue-100 text-blue-800",
  error: "bg-red-100 text-red-800",
};

function fmt(n: number | null | undefined) {
  if (n == null) return "—";
  return new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" }).format(n);
}

export default function DocumentosPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const clienteId = Number(id);

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
      const [d, r] = await Promise.all([
        api.documentos.list(clienteId),
        api.documentos.resumen(clienteId),
      ]);
      setDocs(d);
      setResumen(r);
    } catch {
      router.push("/dashboard");
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
        <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <button
            onClick={() => router.back()}
            className="text-sm text-gray-500 hover:text-gray-800 mb-1 flex items-center gap-1"
          >
            ← Volver
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Documentos fiscales</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {docs.length} documento{docs.length !== 1 ? "s" : ""} — XML, PDF e imágenes de facturas
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportExcel}
            disabled={exportingExcel || docs.length === 0}
            className="border border-green-600 text-green-700 hover:bg-green-50 px-3 py-2 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
          >
            {exportingExcel ? "Exportando..." : "Excel"}
          </button>
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50"
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
          dragOver ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
        }`}
      >
        <div className="text-4xl mb-2">📂</div>
        <p className="text-gray-600 font-medium">
          Arrastra aquí una carpeta o archivos
        </p>
        <p className="text-sm text-gray-400 mt-1">
          XML (CFDI), PDF, JPG, PNG — hasta 10 MB por archivo
        </p>
      </div>

      {/* Upload result banner */}
      {uploadResult && (
        <div className="bg-white border rounded-xl p-4 space-y-2">
          <p className="font-medium text-gray-800">
            Procesados: {uploadResult.procesados} archivo{uploadResult.procesados !== 1 ? "s" : ""}
          </p>
          <div className="space-y-1">
            {uploadResult.resultados.map((r, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ESTADO_COLOR[r.estado] ?? "bg-gray-100 text-gray-700"}`}>
                  {r.estado}
                </span>
                <span className="text-gray-700 truncate max-w-xs">{r.archivo}</span>
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
      <div className="border-b flex gap-4">
        {([
          ["documentos", "Listado"],
          ["resumen", "Resumen fiscal"],
          ["diot", "DIOT"],
        ] as const).map(([t, label]) => (
          <button
            key={t}
            onClick={() => { setTab(t); if (t === "diot") loadDiot(); }}
            className={`pb-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-800"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab: Listado */}
      {tab === "documentos" && (
        <div className="bg-white rounded-xl border overflow-hidden">
          {docs.length === 0 ? (
            <div className="p-12 text-center text-gray-400">
              <div className="text-5xl mb-3">🗂️</div>
              <p>Sin documentos aún — sube XMLs, PDFs o imágenes de facturas</p>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b text-left text-gray-500 text-xs uppercase">
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
                  <tr key={d.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900 max-w-[180px] truncate" title={d.nombre_archivo}>
                        {d.nombre_archivo}
                      </div>
                      {d.uuid_cfdi && (
                        <div className="text-xs text-gray-400 font-mono">{d.uuid_cfdi.slice(0, 18)}…</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                        {d.tipo_comprobante ? TIPO_MAP[d.tipo_comprobante] ?? d.tipo_comprobante : d.tipo_archivo}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-gray-900">{d.emisor_rfc ?? "—"}</div>
                      {d.emisor_nombre && (
                        <div className="text-xs text-gray-400 max-w-[140px] truncate">{d.emisor_nombre}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {d.fecha_emision ? new Date(d.fecha_emision).toLocaleDateString("es-MX") : "—"}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">{fmt(d.total)}</td>
                    <td className="px-4 py-3 text-right text-gray-600">{fmt(d.iva_trasladado)}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ESTADO_COLOR[d.estado] ?? "bg-gray-100 text-gray-700"}`}>
                        {d.estado}
                      </span>
                      {d.error_msg && (
                        <div className="text-xs text-red-500 mt-0.5 max-w-[120px] truncate" title={d.error_msg}>
                          {d.error_msg}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => sendToAgent(d)}
                          title="Enviar al agente fiscal"
                          className="text-blue-600 hover:text-blue-800 text-xs px-2 py-1 border border-blue-200 rounded"
                        >
                          Consultar
                        </button>
                        <button
                          onClick={() => handleDelete(d.id)}
                          title="Eliminar"
                          className="text-red-400 hover:text-red-600 text-xs"
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
            <div className="bg-white border rounded-xl p-5">
              <p className="text-xs text-gray-500 uppercase font-medium mb-1">Utilidad bruta</p>
              <p className={`text-2xl font-bold ${resumen.utilidad_bruta >= 0 ? "text-green-600" : "text-red-600"}`}>
                {fmt(resumen.utilidad_bruta)}
              </p>
              <p className="text-xs text-gray-400 mt-1">Ingresos − Egresos</p>
            </div>
            <div className="bg-white border rounded-xl p-5">
              <p className="text-xs text-gray-500 uppercase font-medium mb-1">IVA neto a pagar</p>
              <p className={`text-2xl font-bold ${resumen.iva_neto_a_pagar >= 0 ? "text-orange-600" : "text-green-600"}`}>
                {fmt(resumen.iva_neto_a_pagar)}
              </p>
              <p className="text-xs text-gray-400 mt-1">IVA cobrado − IVA pagado</p>
            </div>
            <div className="bg-white border rounded-xl p-5">
              <p className="text-xs text-gray-500 uppercase font-medium mb-1">ISR retenido total</p>
              <p className="text-2xl font-bold text-gray-800">{fmt(resumen.isr_retenido_total)}</p>
              <p className="text-xs text-gray-400 mt-1">{resumen.total_documentos} documentos procesados</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Ingresos */}
            <div className="bg-white border rounded-xl p-5">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span className="text-green-500">↑</span> Ingresos ({resumen.ingresos.cantidad} facturas)
              </h3>
              <table className="w-full text-sm">
                <tbody className="divide-y">
                  {[
                    ["Subtotal", resumen.ingresos.subtotal],
                    ["Descuento", -resumen.ingresos.descuento],
                    ["IVA trasladado", resumen.ingresos.iva_trasladado],
                    ["IVA retenido", -resumen.ingresos.iva_retenido],
                    ["ISR retenido", -resumen.ingresos.isr_retenido],
                  ].map(([label, val]) => (
                    <tr key={String(label)}>
                      <td className="py-2 text-gray-500">{label}</td>
                      <td className="py-2 text-right font-medium text-gray-800">{fmt(val as number)}</td>
                    </tr>
                  ))}
                  <tr className="font-bold">
                    <td className="py-2 text-gray-900">Total ingresos</td>
                    <td className="py-2 text-right text-green-600">{fmt(resumen.ingresos.total)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Egresos */}
            <div className="bg-white border rounded-xl p-5">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <span className="text-red-400">↓</span> Egresos ({resumen.egresos.cantidad} facturas)
              </h3>
              <table className="w-full text-sm">
                <tbody className="divide-y">
                  {[
                    ["Subtotal", resumen.egresos.subtotal],
                    ["Descuento", -resumen.egresos.descuento],
                    ["IVA trasladado", resumen.egresos.iva_trasladado],
                    ["IVA retenido", -resumen.egresos.iva_retenido],
                    ["ISR retenido", -resumen.egresos.isr_retenido],
                  ].map(([label, val]) => (
                    <tr key={String(label)}>
                      <td className="py-2 text-gray-500">{label}</td>
                      <td className="py-2 text-right font-medium text-gray-800">{fmt(val as number)}</td>
                    </tr>
                  ))}
                  <tr className="font-bold">
                    <td className="py-2 text-gray-900">Total egresos</td>
                    <td className="py-2 text-right text-red-500">{fmt(resumen.egresos.total)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
            <strong>Tip:</strong> Abre cualquier documento y pulsa <strong>Consultar</strong> para que el agente fiscal analice ese CFDI en detalle — deducciones, alertas SAT, y más.
          </div>
        </div>
      )}

      {/* Tab: DIOT */}
      {tab === "diot" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">DIOT — Declaración Informativa de Operaciones con Terceros</h2>
              <p className="text-sm text-gray-500 mt-0.5">Art. 32-B LIVA — Proveedores de egresos agrupados por RFC</p>
            </div>
            <button
              onClick={handleExportDiotTxt}
              disabled={exportingDiot || !diot || diot.length === 0}
              className="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
            >
              {exportingDiot ? "Generando..." : "Descargar TXT (SAT)"}
            </button>
          </div>

          {diot === null ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin w-6 h-6 border-4 border-blue-600 border-t-transparent rounded-full" />
            </div>
          ) : diot.length === 0 ? (
            <div className="bg-white border rounded-xl p-12 text-center text-gray-400">
              <div className="text-5xl mb-3">📋</div>
              <p>Sin proveedores de egresos — sube facturas de gastos para generar la DIOT</p>
            </div>
          ) : (
            <div className="bg-white border rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b text-left text-gray-500 text-xs uppercase">
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
                    <tr key={p.rfc} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-sm text-gray-900">{p.rfc}</td>
                      <td className="px-4 py-3 text-gray-700 max-w-[200px] truncate" title={p.nombre}>{p.nombre || "—"}</td>
                      <td className="px-4 py-3 text-center text-gray-600">{p.cantidad_facturas}</td>
                      <td className="px-4 py-3 text-right font-medium text-gray-900">{fmt(p.monto_operaciones)}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{fmt(p.iva_16_pagado)}</td>
                      <td className="px-4 py-3 text-right text-gray-600">{fmt(p.iva_retenido)}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-0.5 bg-gray-100 rounded-full text-xs">
                          {p.tipo_tercero === "04" ? "Nacional" : "Extranjero"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-50 font-semibold text-sm">
                    <td className="px-4 py-3 text-gray-700" colSpan={3}>Total ({diot.length} proveedores)</td>
                    <td className="px-4 py-3 text-right text-gray-900">{fmt(diot.reduce((s, p) => s + p.monto_operaciones, 0))}</td>
                    <td className="px-4 py-3 text-right text-gray-900">{fmt(diot.reduce((s, p) => s + p.iva_16_pagado, 0))}</td>
                    <td className="px-4 py-3 text-right text-gray-900">{fmt(diot.reduce((s, p) => s + p.iva_retenido, 0))}</td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          )}

          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
            <strong>Nota:</strong> El TXT generado sigue el formato de 19 columnas separadas por pipes requerido por el portal del SAT (DIOT). Verifica siempre los montos antes de presentar.
          </div>
        </div>
      )}
    </div>
  );
}
