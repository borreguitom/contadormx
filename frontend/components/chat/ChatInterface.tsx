"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api } from "@/lib/api";

const CONV_KEY = "cmx_last_conv";

const QUICK_TOPICS = [
  { icon: "📋", label: "CFDI 4.0",   query: "¿Cuáles son los requisitos del CFDI 4.0 y sus complementos principales?" },
  { icon: "💰", label: "RESICO",     query: "Explícame el RESICO PF y PM: tasas, límites y obligaciones clave" },
  { icon: "🏢", label: "ISR PM",     query: "Calcula ISR pago provisional para persona moral con ingresos de $500,000 en enero, coeficiente 0.20" },
  { icon: "👤", label: "ISR PF",     query: "¿Cuánto ISR retiene mensualmente un empleado con sueldo de $30,000?" },
  { icon: "🧾", label: "IVA",        query: "Tengo ventas de $200,000 y compras acreditables de $80,000. ¿Cuánto IVA entero?" },
  { icon: "👷", label: "Nómina",     query: "Calcula la nómina completa para un empleado con salario mensual de $25,000" },
  { icon: "📅", label: "Calendario", query: "¿Cuáles son las obligaciones fiscales de una persona moral en julio 2025?" },
  { icon: "⚖️", label: "Finiquito",  query: "Calcula el finiquito por despido injustificado de un empleado con $600 diarios y 3 años de antigüedad" },
  { icon: "📑", label: "Dec. Anual", query: "Calcula la declaración anual de un asalariado con ingresos de $480,000 al año, retenciones de $58,000 y gastos médicos de $25,000" },
];

const TOOL_LABELS: Record<string, string> = {
  calcular_isr_personas_fisicas: "ISR PF",
  calcular_isr_personas_morales: "ISR PM",
  calcular_iva: "IVA",
  calcular_cuotas_imss: "IMSS",
  calcular_nomina: "Nómina",
  calcular_finiquito: "Finiquito",
  calcular_declaracion_anual_pf: "Dec. Anual PF",
  buscar_legislacion: "RAG Legal",
  obtener_calendario_fiscal: "Calendario",
  web_search: "Búsqueda web",
};

interface Message {
  role: "user" | "assistant";
  content: string;
  tools_used?: string[];
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3 rounded-2xl bg-white/5 border border-white/8 w-fit">
      {[0, 1, 2].map(i => (
        <span key={i} className="w-2 h-2 rounded-full bg-green-400"
          style={{ animation: `bounce 1.2s infinite ${i * 0.18}s` }} />
      ))}
    </div>
  );
}

function ToolBadges({ tools }: { tools: string[] }) {
  if (!tools?.length) return null;
  return (
    <div className="flex flex-wrap gap-1 mt-2">
      {tools.map(t => (
        <span key={t} className="text-xs px-2 py-0.5 rounded-full border border-green-500/25 text-green-400 bg-green-500/8">
          ⚙ {TOOL_LABELS[t] ?? t}
        </span>
      ))}
    </div>
  );
}

function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex msg-appear ${isUser ? "justify-end" : "justify-start"} mb-5`}>
      {!isUser && (
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-green-800 to-green-600 flex items-center justify-center text-base mr-2.5 mt-0.5 shrink-0 shadow shadow-green-900/40">
          🏛️
        </div>
      )}
      <div className={`max-w-[78%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
        isUser
          ? "bg-gradient-to-br from-green-700 to-green-600 rounded-br-sm text-green-50 shadow shadow-green-900/30"
          : "bg-white/5 border border-white/8 rounded-bl-sm text-green-50"
      }`}>
        {isUser
          ? <p className="whitespace-pre-wrap">{msg.content}</p>
          : (
            <div className="prose-chat">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              <ToolBadges tools={msg.tools_used ?? []} />
            </div>
          )
        }
      </div>
    </div>
  );
}

const DOC_CTX_KEY = "cmx_doc_ctx";

export default function ChatInterface() {
  const searchParams = useSearchParams();
  const clienteId = searchParams.get("cliente");
  const clienteNombre = searchParams.get("nombre");
  const docParam = searchParams.get("doc");

  // Si viene de la página de documentos, leemos el contexto guardado
  const docContext = typeof window !== "undefined" && docParam
    ? localStorage.getItem(DOC_CTX_KEY)
    : null;

  const welcomeMsg: Message = {
    role: "assistant",
    content: docContext
      ? `Documento cargado:\n\n\`\`\`\n${docContext}\n\`\`\`\n\n¿Qué necesitas analizar de esta factura?`
      : clienteNombre
      ? `Consulta cargada para el cliente **${decodeURIComponent(clienteNombre)}**. ¿Qué necesitas calcular o consultar?`
      : "Bienvenido a **ContadorMX**. Soy tu agente especializado en contabilidad fiscal y pública para México.\n\n¿En qué te ayudo?",
  };

  const [messages, setMessages] = useState<Message[]>([welcomeMsg]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [hydrating, setHydrating] = useState(true);

  const historyRef = useRef<{ role: string; content: string }[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load last conversation on mount (skip if client/doc context from URL)
  useEffect(() => {
    // limpia el contexto de documento una vez cargado
    if (docParam) {
      localStorage.removeItem(DOC_CTX_KEY);
      setHydrating(false);
      return;
    }
    if (clienteNombre) { setHydrating(false); return; }

    const savedId = localStorage.getItem(CONV_KEY);
    if (!savedId) { setHydrating(false); return; }

    api.chatHistory.get(parseInt(savedId))
      .then(conv => {
        if (!conv.messages.length) { setHydrating(false); return; }
        const loaded: Message[] = conv.messages.map(m => ({
          role: m.role as "user" | "assistant",
          content: m.content,
          tools_used: m.tools_used,
        }));
        setMessages(loaded);
        historyRef.current = conv.messages.map(m => ({ role: m.role, content: m.content }));
        setConversationId(conv.id);
      })
      .catch(() => {
        localStorage.removeItem(CONV_KEY);
      })
      .finally(() => setHydrating(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = useCallback(async (text?: string) => {
    const msg = text ?? input.trim();
    if (!msg || loading) return;
    setInput("");

    const userMsg: Message = { role: "user", content: msg };
    setMessages(prev => [...prev, userMsg]);
    historyRef.current = [...historyRef.current, { role: "user", content: msg }];
    setLoading(true);

    try {
      const data = await api.chat.message(
        historyRef.current,
        {
          use_web_search: searchMode,
          client_context: docContext
            ? `Contexto de factura:\n${docContext}`
            : clienteNombre
            ? `Cliente: ${decodeURIComponent(clienteNombre)} (ID: ${clienteId})`
            : undefined,
        },
        conversationId,
      );

      const assistantMsg: Message = {
        role: "assistant",
        content: data.content,
        tools_used: data.tools_used,
      };
      historyRef.current = [...historyRef.current, { role: "assistant", content: data.content }];
      setMessages(prev => [...prev, assistantMsg]);

      // Persist conversation ID
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
        localStorage.setItem(CONV_KEY, String(data.conversation_id));
      }
    } catch (e: unknown) {
      const detail = e instanceof Error ? e.message : "Error de conexión";
      const isLimit = detail.includes("Límite");
      setMessages(prev => [...prev, {
        role: "assistant",
        content: isLimit
          ? `⚠️ ${detail}`
          : "Error de conexión. Verifica que el backend esté corriendo en `localhost:8000`.",
      }]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  }, [input, loading, searchMode, clienteId, clienteNombre, conversationId]);

  const clearChat = () => {
    setMessages([{ role: "assistant", content: "Conversación reiniciada. ¿En qué te ayudo?" }]);
    historyRef.current = [];
    setConversationId(undefined);
    localStorage.removeItem(CONV_KEY);
  };

  if (hydrating) return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex gap-1.5">
        {[0,1,2].map(i => (
          <span key={i} className="w-2 h-2 rounded-full bg-green-500"
            style={{ animation: `bounce 1.2s infinite ${i * 0.18}s` }} />
        ))}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Sub-header */}
      <div className="flex items-center justify-between px-5 py-2.5 border-b border-white/7 bg-green-950/20">
        <div className="flex items-center gap-2">
          {docParam && (
            <span className="text-xs px-2.5 py-1 rounded-full bg-blue-500/12 border border-blue-500/25 text-blue-400">
              🗂️ Factura #{docParam}
            </span>
          )}
          {clienteNombre && !docParam && (
            <span className="text-xs px-2.5 py-1 rounded-full bg-green-500/12 border border-green-500/25 text-green-400">
              👤 {decodeURIComponent(clienteNombre)}
            </span>
          )}
          {conversationId && !clienteNombre && !docParam && (
            <span className="text-xs text-gray-600">Conv. #{conversationId}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setSearchMode(s => !s)}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
              searchMode
                ? "bg-green-500/12 border-green-500/35 text-green-400"
                : "bg-white/4 border-white/10 text-gray-500"
            }`}>
            {searchMode ? "🔍 Búsqueda activa" : "📚 Sin búsqueda"}
          </button>
          <button onClick={clearChat}
            className="text-xs px-3 py-1.5 rounded-lg border border-white/10 bg-white/4 text-gray-500 hover:text-gray-300 transition-all">
            🗑 Nueva
          </button>
        </div>
      </div>

      {/* Quick topics */}
      <div className="px-4 pt-3 pb-0 flex flex-wrap gap-1.5">
        {QUICK_TOPICS.map((t, i) => (
          <button key={i} disabled={loading} onClick={() => send(t.query)}
            className="text-xs px-3 py-1.5 rounded-full border border-white/10 bg-white/3 text-green-200 hover:bg-green-500/10 hover:border-green-500/35 transition-all disabled:opacity-40">
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 max-w-3xl w-full mx-auto">
        {messages.map((msg, i) => <ChatMessage key={i} msg={msg} />)}
        {loading && (
          <div className="flex items-center gap-2.5 mb-5">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-green-800 to-green-600 flex items-center justify-center text-base shrink-0">🏛️</div>
            <TypingDots />
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/7 bg-green-950/15 px-4 py-3">
        <div className="max-w-3xl mx-auto flex gap-2 items-end">
          <div className="flex-1 border border-green-500/18 rounded-xl bg-white/5 px-3.5 py-2.5 focus-within:border-green-500/35 transition-colors">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
              placeholder="Consulta fiscal o contable…"
              rows={2}
              className="w-full bg-transparent border-none text-green-50 text-sm leading-relaxed resize-none focus:outline-none placeholder:text-gray-600"
            />
          </div>
          <button onClick={() => send()} disabled={loading || !input.trim()}
            className="w-11 h-11 rounded-xl bg-gradient-to-br from-green-700 to-green-500 text-white text-xl flex items-center justify-center shadow shadow-green-900/40 hover:from-green-600 hover:to-green-400 transition-all disabled:opacity-40 disabled:cursor-not-allowed">
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
