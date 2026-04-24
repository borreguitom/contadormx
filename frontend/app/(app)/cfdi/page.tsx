"use client";
import { useState, useCallback } from "react";
import { api, type CFDIResult } from "@/lib/api";

export default function CFDIPage() {
  const [xml, setXml] = useState("");
  const [result, setResult] = useState<CFDIResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  const validate = async (content: string) => {
    if (!content.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      setResult(await api.cfdi.validate(content));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al validar");
    } finally {
      setLoading(false);
    }
  };

  const readFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = e => {
      const content = e.target?.result as string;
      setXml(content);
      validate(content);
    };
    reader.readAsText(file, "UTF-8");
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith(".xml") || file.type === "text/xml")) readFile(file);
    else setError("Solo se aceptan archivos XML");
  }, []);

  const onFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) readFile(file);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-green-100">Validador CFDI 4.0</h1>
          <p className="text-sm text-gray-500 mt-0.5">Estructura, campos obligatorios, namespace, Timbre Fiscal Digital</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Input */}
          <div className="space-y-4">
            {/* Drop zone */}
            <div
              onDrop={onDrop}
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onClick={() => document.getElementById("xml-input")?.click()}
              className={`relative rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition-all ${
                dragging
                  ? "border-green-500/60 bg-green-500/8"
                  : "border-white/12 bg-white/3 hover:border-green-500/30 hover:bg-green-500/5"
              }`}
            >
              <input id="xml-input" type="file" accept=".xml,text/xml" className="hidden" onChange={onFileInput} />
              <div className="text-3xl mb-2">📂</div>
              <p className="text-sm text-gray-400">Arrastra un XML aquí</p>
              <p className="text-xs text-gray-600 mt-1">o haz clic para seleccionar</p>
            </div>

            {/* Textarea */}
            <div>
              <p className="text-xs text-gray-500 mb-1.5 uppercase tracking-wide">O pega el XML directamente</p>
              <textarea
                value={xml}
                onChange={e => setXml(e.target.value)}
                rows={8}
                placeholder={'<?xml version="1.0" encoding="UTF-8"?>\n<cfdi:Comprobante ...>'}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3.5 py-3 text-xs text-green-200 font-mono focus:outline-none focus:border-green-500/40 resize-none placeholder:text-gray-700"
              />
            </div>

            <button
              onClick={() => validate(xml)}
              disabled={loading || !xml.trim()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-green-700 to-green-500 text-white text-sm font-medium shadow shadow-green-900/30 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-50"
            >
              {loading ? "Validando…" : "Validar CFDI"}
            </button>

            {error && (
              <p className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>
            )}
          </div>

          {/* Resultado */}
          <div>
            {!result && !loading && (
              <div className="rounded-2xl border border-white/8 bg-white/3 p-8 text-center h-full flex flex-col items-center justify-center">
                <div className="text-4xl mb-3">🧾</div>
                <p className="text-sm text-gray-500">Carga un XML para validar</p>
              </div>
            )}

            {loading && (
              <div className="rounded-2xl border border-white/8 bg-white/3 p-8 flex items-center justify-center h-full">
                <div className="flex gap-1.5">
                  {[0,1,2].map(i => (
                    <span key={i} className="w-2 h-2 rounded-full bg-green-500"
                      style={{ animation: `bounce 1.2s infinite ${i * 0.18}s` }} />
                  ))}
                </div>
              </div>
            )}

            {result && !loading && (
              <div className="rounded-2xl border border-white/8 bg-white/3 p-5 space-y-4">
                {/* Estado general */}
                <div className={`flex items-center gap-2.5 p-3 rounded-xl border ${
                  result.valido
                    ? "bg-green-500/10 border-green-500/25 text-green-300"
                    : "bg-red-500/10 border-red-500/25 text-red-300"
                }`}>
                  <span className="text-xl">{result.valido ? "✅" : "❌"}</span>
                  <div>
                    <p className="text-sm font-semibold">{result.valido ? "CFDI Válido" : "CFDI con errores"}</p>
                    <p className="text-xs opacity-70">
                      {result.valido
                        ? `UUID: ${result.uuid ?? "Sin timbre"}`
                        : `${result.errores.length} error${result.errores.length !== 1 ? "es" : ""} detectado${result.errores.length !== 1 ? "s" : ""}`}
                    </p>
                  </div>
                </div>

                {/* Datos del comprobante */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { label: "UUID", value: result.uuid ?? "Sin timbre", mono: true },
                    { label: "Versión", value: result.version ?? "—" },
                    { label: "Emisor RFC", value: result.emisor_rfc ?? "—", mono: true },
                    { label: "Receptor RFC", value: result.receptor_rfc ?? "—", mono: true },
                    { label: "Total", value: result.total != null ? `$${result.total.toLocaleString("es-MX", { minimumFractionDigits: 2 })}` : "—" },
                    { label: "Tipo", value: result.tipo_comprobante ?? "—" },
                    { label: "Fecha", value: result.fecha ?? "—" },
                  ].map(c => (
                    <div key={c.label} className="rounded-xl bg-white/3 border border-white/6 px-2.5 py-2">
                      <p className="text-gray-600 mb-0.5 uppercase tracking-wide" style={{ fontSize: 10 }}>{c.label}</p>
                      <p className={`text-green-200 break-all ${c.mono ? "font-mono" : ""}`}>{c.value}</p>
                    </div>
                  ))}
                </div>

                {/* Errores */}
                {result.errores.length > 0 && (
                  <div className="rounded-xl border border-red-500/20 bg-red-500/8 p-3 space-y-1.5">
                    <p className="text-xs text-red-400 font-semibold uppercase tracking-wide">Errores</p>
                    {result.errores.map((e, i) => (
                      <p key={i} className="text-xs text-red-300">• {e}</p>
                    ))}
                  </div>
                )}

                {/* Advertencias */}
                {result.advertencias.length > 0 && (
                  <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/8 p-3 space-y-1.5">
                    <p className="text-xs text-yellow-400 font-semibold uppercase tracking-wide">Advertencias</p>
                    {result.advertencias.map((w, i) => (
                      <p key={i} className="text-xs text-yellow-300">• {w}</p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
