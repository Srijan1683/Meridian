import { useEffect, useMemo, useRef, useState } from "react";
import {
  BookOpen,
  ChevronDown,
  CheckCircle2,
  Copy,
  History,
  Loader2,
  PauseCircle,
  Search,
  Send,
  Sparkles,
  Square,
  Trash2,
  XCircle,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const WS_BASE = API_BASE.replace(/^http/, "ws");

function classNames(...values) {
  return values.filter(Boolean).join(" ");
}

function normalizeSource(source) {
  return {
    id: source.source_id || source.id || source.url,
    title: source.title || "Untitled source",
    url: String(source.url || ""),
    snippet: source.snippet || "",
  };
}

function sourceDedupeKey(source) {
  try {
    const url = new URL(source.url);
    url.hash = "";
    for (const key of Array.from(url.searchParams.keys())) {
      if (key.toLowerCase().startsWith("utm_")) {
        url.searchParams.delete(key);
      }
    }
    url.pathname = url.pathname.replace(/\/$/, "") || "/";
    return `url:${url.origin.toLowerCase()}${url.pathname}${url.search}`;
  } catch {
    return `title:${source.title.toLowerCase().replace(/\s+/g, " ").trim()}`;
  }
}

function sourceTitleKey(source) {
  return source.title
    .toLowerCase()
    .replace(/\.\.\./g, "")
    .replace(/[^\p{L}\p{N}\s]/gu, "")
    .replace(/\s+/g, " ")
    .trim();
}

function HistoryList({ items, onSelect, onDelete }) {
  if (!items.length) {
    return (
      <div className="rounded-lg border border-white/10 bg-white/[0.035] px-3 py-3 text-xs leading-5 text-slate-500">
        Your searched queries will appear here.
      </div>
    );
  }

  return (
    <div className="max-w-full space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="group grid max-w-full grid-cols-[minmax(0,1fr)_auto] gap-2 rounded-lg border border-white/10 bg-white/[0.04] p-2 transition hover:border-signal-cyan/40 hover:bg-white/[0.065]"
        >
          <button
            type="button"
            onClick={() => onSelect(item)}
            className="min-w-0 text-left"
          >
            <div className="flex min-w-0 items-center gap-2">
              <span className="line-clamp-2 text-xs leading-5 text-slate-300">{item.query}</span>
            </div>
            <span className="mt-1 inline-flex rounded-full border border-white/10 px-2 py-0.5 text-[10px] capitalize text-slate-500">
              {item.mode}
            </span>
          </button>
          <button
            type="button"
            onClick={() => onDelete(item.id)}
            className="grid h-8 w-8 shrink-0 place-items-center rounded-md text-slate-600 transition hover:bg-signal-rose/10 hover:text-signal-rose"
            title="Delete from history"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

function SourcesPanel({ sources }) {
  return (
    <div className="thin-scrollbar max-h-[420px] space-y-3 overflow-auto pr-1">
      {sources.length ? (
        sources.map((source, index) => (
          <a
            key={source.id}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="block max-w-full rounded-lg border border-white/10 bg-white/[0.04] p-3 transition hover:border-signal-cyan/40 hover:bg-white/[0.065]"
          >
            <div className="flex min-w-0 items-center gap-2">
              <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-signal-cyan/15 font-mono text-xs text-signal-cyan">
                {index + 1}
              </span>
              <h3 className="min-w-0 break-words text-sm font-medium leading-5 text-white">{source.title}</h3>
            </div>
            <p className="mt-2 line-clamp-3 text-xs leading-5 text-slate-400">{source.snippet}</p>
            <p className="mt-2 truncate font-mono text-[11px] text-signal-cyan/80">{source.url}</p>
          </a>
        ))
      ) : (
        <div className="flex min-h-[180px] items-center justify-center rounded-lg border border-white/10 bg-white/[0.035] p-5 text-center text-sm leading-6 text-slate-500">
          Sources appear here as Meridian finds them.
        </div>
      )}
    </div>
  );
}

function HeaderDropdown({ label, count, children, align = "right" }) {
  return (
    <details className="group relative">
      <summary className="inline-flex h-10 cursor-pointer list-none items-center gap-2 rounded-lg border border-white/10 bg-white/[0.055] px-3 text-sm font-medium text-slate-200 transition hover:border-signal-cyan/40 hover:text-white">
        <span>{label}</span>
        {count !== undefined ? (
          <span className="rounded-full border border-signal-cyan/30 bg-signal-cyan/10 px-2 py-0.5 font-mono text-[11px] text-signal-cyan">
            {count}
          </span>
        ) : null}
        <ChevronDown className="h-4 w-4 text-slate-500 transition group-open:rotate-180" />
      </summary>
      <div
        className={classNames(
          "absolute top-12 z-30 w-[min(calc(100vw-2rem),420px)] rounded-lg border border-white/10 bg-ink-950/95 p-4 shadow-panel backdrop-blur",
          align === "left" ? "left-0" : "right-0"
        )}
      >
        {children}
      </div>
    </details>
  );
}

function parseInlineText(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }

    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={index} className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[0.9em] text-signal-amber">
          {part.slice(1, -1)}
        </code>
      );
    }

    return part;
  });
}

function CodeBlock({ language, code }) {
  async function copyCode() {
    await navigator.clipboard.writeText(code);
  }

  return (
    <div className="my-5 max-w-full overflow-hidden rounded-lg border border-white/10 bg-[#070911]">
      <div className="flex items-center justify-between border-b border-white/10 bg-white/[0.045] px-4 py-2">
        <span className="font-mono text-xs uppercase tracking-[0.16em] text-signal-cyan">
          {language || "snippet"}
        </span>
        <button
          type="button"
          onClick={copyCode}
          className="inline-flex h-8 items-center gap-2 rounded-md border border-white/10 bg-white/[0.04] px-2 text-xs text-slate-300 transition hover:border-signal-cyan/40 hover:text-white"
        >
          <Copy className="h-3.5 w-3.5" />
          Copy
        </button>
      </div>
      <pre className="thin-scrollbar max-w-full overflow-x-auto p-4 text-sm leading-6">
        <code className="font-mono text-slate-100">{code}</code>
      </pre>
    </div>
  );
}

function MarkdownResponse({ text }) {
  const blocks = [];
  const lines = text.split("\n");
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const fence = line.match(/^```([\w-]*)\s*$/);

    if (fence) {
      const language = fence[1] || "snippet";
      const codeLines = [];
      index += 1;

      while (index < lines.length && !lines[index].startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }

      blocks.push({
        type: "code",
        language,
        code: codeLines.join("\n"),
      });

      index += 1;
      continue;
    }

    blocks.push({ type: "line", text: line });
    index += 1;
  }

  return (
    <article className="response-markdown w-full max-w-full overflow-hidden text-[15px] leading-7 text-slate-200 lg:max-w-4xl">
      {blocks.map((block, blockIndex) => {
        if (block.type === "code") {
          return <CodeBlock key={blockIndex} language={block.language} code={block.code} />;
        }

        const trimmed = block.text.trim();

        if (!trimmed) {
          return <div key={blockIndex} className="h-3" />;
        }

        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={blockIndex} className="mb-2 mt-5 text-lg font-bold text-white">
              {parseInlineText(trimmed.slice(4))}
            </h3>
          );
        }

        if (trimmed.startsWith("## ")) {
          return (
            <h2 key={blockIndex} className="mb-3 mt-6 text-xl font-bold text-white">
              {parseInlineText(trimmed.slice(3))}
            </h2>
          );
        }

        if (trimmed.startsWith("# ")) {
          return (
            <h1 key={blockIndex} className="mb-3 mt-6 text-2xl font-extrabold text-white">
              {parseInlineText(trimmed.slice(2))}
            </h1>
          );
        }

        if (/^[-*]\s+/.test(trimmed)) {
          return (
            <div key={blockIndex} className="my-1 flex min-w-0 max-w-full gap-3 pl-1">
              <span className="mt-3 h-1.5 w-1.5 shrink-0 rounded-full bg-signal-cyan" />
              <p className="min-w-0 max-w-full">{parseInlineText(trimmed.replace(/^[-*]\s+/, ""))}</p>
            </div>
          );
        }

        if (/^\d+\.\s+/.test(trimmed)) {
          const [number] = trimmed.split(".");
          return (
            <div key={blockIndex} className="my-1 flex min-w-0 max-w-full gap-3">
              <span className="w-8 shrink-0 whitespace-nowrap text-right font-mono text-sm text-signal-cyan">{number}.</span>
              <p className="min-w-0 max-w-full">{parseInlineText(trimmed.replace(/^\d+\.\s+/, ""))}</p>
            </div>
          );
        }

        return (
          <p key={blockIndex} className="my-2 min-w-0 max-w-full">
            {parseInlineText(trimmed)}
          </p>
        );
      })}
    </article>
  );
}

export default function App() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("normal");
  const [sessionId, setSessionId] = useState("");
  const [status, setStatus] = useState("idle");
  const [progress, setProgress] = useState("Ask a question to begin.");
  const [response, setResponse] = useState("");
  const [sources, setSources] = useState([]);
  const [error, setError] = useState("");
  const [memory, setMemory] = useState({ short: 0, long: 0, context: "" });
  const [tokenUsage, setTokenUsage] = useState(null);
  const [queryHistory, setQueryHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("meridian.queryHistory") || "[]");
    } catch {
      return [];
    }
  });
  const socketRef = useRef(null);
  const normalRequestRef = useRef(null);
  const queryInputRef = useRef(null);

  const sourceList = useMemo(() => {
    const map = new Map();
    const titleKeys = new Set();
    for (const source of sources) {
      const normalized = normalizeSource(source);
      const key = sourceDedupeKey(normalized);
      const titleKey = sourceTitleKey(normalized);
      if (!map.has(key) && (!titleKey || !titleKeys.has(titleKey))) {
        map.set(key, normalized);
        if (titleKey) {
          titleKeys.add(titleKey);
        }
      }
    }
    return Array.from(map.values());
  }, [sources]);

  const canSubmit = query.trim() && status !== "running";

  useEffect(() => {
    const input = queryInputRef.current;
    if (!input) return;

    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 320)}px`;
  }, [query]);

  function resetWorkspace() {
    setResponse("");
    setSources([]);
    setError("");
    setMemory({ short: 0, long: 0, context: "" });
    setTokenUsage(null);
    setProgress("Ask a question to begin.");
  }

  function addQueryToHistory(nextQuery, nextMode) {
    const trimmed = nextQuery.trim();
    if (!trimmed) return;

    setQueryHistory((current) => {
      const withoutDuplicate = current.filter(
        (item) => item.query.toLowerCase() !== trimmed.toLowerCase()
      );
      const updated = [
        {
          id: crypto.randomUUID(),
          query: trimmed,
          mode: nextMode,
          createdAt: new Date().toISOString(),
        },
        ...withoutDuplicate,
      ].slice(0, 8);

      localStorage.setItem("meridian.queryHistory", JSON.stringify(updated));
      return updated;
    });
  }

  function deleteQueryFromHistory(historyId) {
    setQueryHistory((current) => {
      const updated = current.filter((item) => item.id !== historyId);
      localStorage.setItem("meridian.queryHistory", JSON.stringify(updated));
      return updated;
    });
  }

  function selectHistoryItem(item) {
    setQuery(item.query);
    setMode(item.mode);
  }

  async function runNormalResearch() {
    setStatus("running");
    resetWorkspace();
    setProgress("Searching and preparing a cited answer...");

    try {
      const controller = new AbortController();
      normalRequestRef.current = controller;

      const result = await fetch(`${API_BASE}/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          query: query.trim(),
          mode: "normal",
          session_id: sessionId || null,
        }),
      });

      if (!result.ok) {
        throw new Error(`Research failed with ${result.status}`);
      }

      const data = await result.json();
      setSessionId(data.session_id);
      setResponse(data.response || "");
      setSources(data.sources || []);
      setTokenUsage(data.token_usage || null);
      setMemory({
        short: data.memory_context?.short_term_retrieved ?? 0,
        long: data.memory_context?.long_term_retrieved ?? 0,
        context: "",
      });
      setProgress("Answer ready.");
      setStatus("complete");
    } catch (caught) {
      if (caught.name === "AbortError") {
        return;
      }

      setError(caught.message);
      setProgress("Something went wrong.");
      setStatus("error");
    } finally {
      normalRequestRef.current = null;
    }
  }

  function runDeepResearch() {
    setStatus("running");
    resetWorkspace();
    setProgress("Opening research stream...");

    const socket = new WebSocket(`${WS_BASE}/ws/research`);
    socketRef.current = socket;

    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          type: "query",
          data: {
            query: query.trim(),
            mode: "deep",
            session_id: sessionId || null,
          },
        })
      );
    };

    socket.onmessage = (message) => {
      const event = JSON.parse(message.data);
      const data = event.data || {};

      if (data.session_id) {
        setSessionId(data.session_id);
      }

      if (event.type === "memory") {
        setMemory({
          short: data.short_term_retrieved ?? 0,
          long: data.long_term_retrieved ?? 0,
          context: data.context || "",
        });
        setProgress("Relevant memory checked.");
      }

      if (event.type === "searching") {
        setProgress(`Searching ${data.search_index || ""} of ${data.total_searches || ""}...`);
      }

      if (event.type === "source" && data.source) {
        setSources((current) => [...current, data.source]);
        setProgress("Reviewing sources...");
      }

      if (event.type === "content") {
        setResponse((current) => current + (data.chunk || ""));
        setProgress("Writing the answer...");
      }

      if (event.type === "done") {
        setResponse((current) => current || data.response || "");
        setTokenUsage(data.token_usage || null);
        setProgress(
          data.cancelled
            ? "Response saved for later. Partial results/citations will be stored if available."
            : "Answer ready."
        );
        setStatus(data.cancelled ? "cancelled" : "complete");
        socket.close();
      }

      if (event.type === "error") {
        setError(data.error || "Unknown websocket error");
        setProgress("Something went wrong.");
        setStatus("error");
        socket.close();
      }
    };

    socket.onerror = () => {
      setError("Could not connect to the research stream.");
      setProgress("Connection failed.");
      setStatus("error");
    };
  }

  function submitResearch() {
    if (!canSubmit) return;

    addQueryToHistory(query, mode);

    if (mode === "deep") {
      runDeepResearch();
      return;
    }

    runNormalResearch();
  }

  function cancelResearch() {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "cancel" }));
    }
    setProgress("Research cancelled.");
    setStatus("cancelled");
  }

  async function saveForLater() {
    if (status === "running") {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({ type: "cancel" }));
      }

      if (normalRequestRef.current) {
        normalRequestRef.current.abort();
      }

      setProgress("Response saved for later. Partial results/citations will be stored if available.");
      setStatus("cancelled");
      return;
    }

    if (!sessionId) return;

    try {
      setProgress("Saving this session for future recall...");

      const result = await fetch(`${API_BASE}/sessions/${sessionId}/summarize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!result.ok) {
        throw new Error(`Memory save failed with ${result.status}`);
      }

      const data = await result.json();

      if (data.memory_job) {
        setProgress("Long-term memory job queued. Run the worker to finish the summary.");
      } else {
        setProgress("Session ended. There was not enough content to summarize yet.");
      }
    } catch (caught) {
      setError(caught.message);
      setStatus("error");
    }
  }

  async function copyResponse() {
    if (!response) return;
    await navigator.clipboard.writeText(response);
    setProgress("Answer copied.");
  }

  return (
    <main className={classNames("app-shell min-h-screen w-full max-w-full overflow-x-hidden px-3 py-4 text-slate-100 sm:px-5 lg:h-screen lg:overflow-hidden", mode === "deep" ? "theme-deep" : "theme-normal")}>
      <div className="mx-auto flex min-h-screen w-full max-w-[1720px] flex-col gap-4 overflow-x-hidden lg:h-full lg:min-h-0">
        <header className="flex shrink-0 flex-col gap-4 border-b border-white/10 pb-4 md:flex-row md:items-center md:justify-between">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-signal-cyan/30 bg-signal-cyan/10 shadow-glow">
              <Sparkles className="h-5 w-5 text-signal-cyan" />
            </div>
            <div className="min-w-0">
              <h1 className="font-display text-3xl font-extrabold tracking-tight text-white">Meridian</h1>
              <p className="truncate text-sm text-slate-400">Focused research with memory and cited answers</p>
            </div>
          </div>

          <div className="flex w-full flex-wrap items-center justify-end gap-2 md:w-auto">
            <HeaderDropdown label="Tokens" count={tokenUsage?.total_tokens ?? 0} align="right">
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
                  <div className="text-xs text-slate-500">This session</div>
                  <div className="mt-1 font-mono text-xl font-semibold text-white">{memory.short}</div>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
                  <div className="text-xs text-slate-500">Past sessions</div>
                  <div className="mt-1 font-mono text-xl font-semibold text-white">{memory.long}</div>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
                  <div className="text-xs text-slate-500">Prompt</div>
                  <div className="mt-1 font-mono text-xl font-semibold text-white">{tokenUsage?.prompt_tokens ?? 0}</div>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/[0.035] p-3">
                  <div className="text-xs text-slate-500">Answer</div>
                  <div className="mt-1 font-mono text-xl font-semibold text-white">{tokenUsage?.completion_tokens ?? 0}</div>
                </div>
              </div>
            </HeaderDropdown>

            <HeaderDropdown label="Sources" count={sourceList.length} align="right">
              <SourcesPanel sources={sourceList} />
            </HeaderDropdown>
          </div>
        </header>

        <section className="grid w-full max-w-full flex-1 gap-4 overflow-x-hidden lg:min-h-0 lg:grid-cols-[290px_minmax(0,1fr)] xl:grid-cols-[330px_minmax(0,1fr)]">
          <aside className="flex w-full max-w-full flex-col rounded-lg border border-white/10 bg-ink-900/78 p-4 shadow-panel backdrop-blur lg:min-h-0">
            <div className="shrink-0">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-400">Ask</h2>
                <Search className="h-4 w-4 text-signal-cyan" />
              </div>

              <div className="mt-4 grid grid-cols-2 rounded-lg border border-white/10 bg-black/20 p-1">
                {["normal", "deep"].map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setMode(item)}
                    className={classNames(
                      "h-10 rounded-md text-sm font-medium capitalize transition",
                      mode === item ? "bg-signal-cyan text-ink-950 shadow-glow" : "text-slate-400 hover:text-white"
                    )}
                  >
                    {item}
                  </button>
                ))}
              </div>

              <p className="mt-3 rounded-lg border border-white/10 bg-white/[0.035] px-3 py-2 text-xs leading-5 text-slate-400">
                {mode === "deep"
                  ? "Deep mode takes longer because it searches from more angles before writing."
                  : "Normal mode is faster and best for concise answers."}
              </p>
            </div>

            <div className="thin-scrollbar mt-4 flex-1 overflow-visible pr-1 lg:min-h-0 lg:overflow-auto">
              <label className="block text-sm font-medium text-slate-300" htmlFor="query">
                Research question
              </label>
              <textarea
                ref={queryInputRef}
                id="query"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                rows={3}
                className="mt-2 max-h-[320px] min-h-[150px] w-full max-w-full resize-none overflow-y-hidden rounded-lg border border-white/10 bg-black/30 p-3 text-sm leading-6 text-white outline-none transition placeholder:text-slate-600 focus:border-signal-cyan/60 focus:ring-2 focus:ring-signal-cyan/10 lg:h-[240px] lg:max-h-none lg:min-h-0 lg:overflow-y-auto"
                placeholder="Ask a question..."
              />

              <details className="mt-4 rounded-lg border border-white/10 bg-white/[0.035] p-3 lg:hidden">
                <summary className="flex cursor-pointer list-none items-center justify-between text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  <span className="flex items-center gap-2">
                    <History className="h-3.5 w-3.5 text-signal-cyan" />
                    History
                  </span>
                  <ChevronDown className="h-4 w-4 text-slate-500" />
                </summary>
                <div className="thin-scrollbar mt-3 max-h-[260px] overflow-auto pr-1">
                  <HistoryList
                    items={queryHistory}
                    onSelect={selectHistoryItem}
                    onDelete={deleteQueryFromHistory}
                  />
                </div>
              </details>

              <div className="mt-4 hidden lg:block">
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                    <History className="h-3.5 w-3.5 text-signal-cyan" />
                    History
                  </div>
                  {queryHistory.length ? (
                    <span className="font-mono text-[11px] text-slate-600">{queryHistory.length}/8</span>
                  ) : null}
                </div>

                <HistoryList
                  items={queryHistory}
                  onSelect={selectHistoryItem}
                  onDelete={deleteQueryFromHistory}
                />
              </div>

              <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.035] p-3">
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  {status === "running" ? (
                    <Loader2 className="h-4 w-4 animate-spin text-signal-cyan" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4 text-signal-green" />
                  )}
                  <span>{progress}</span>
                </div>
              </div>
            </div>

            <div className="mt-4 shrink-0 space-y-3">
              <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-3">
                <button
                  type="button"
                  disabled={!canSubmit}
                  onClick={submitResearch}
                  className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-signal-cyan px-4 text-sm font-semibold text-ink-950 shadow-glow transition hover:bg-white disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400 disabled:shadow-none"
                >
                  {status === "running" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  Research
                </button>
                <button
                  type="button"
                  onClick={cancelResearch}
                  disabled={status !== "running"}
                  className="grid h-12 w-12 place-items-center rounded-lg border border-white/10 bg-white/[0.05] text-slate-300 transition hover:border-signal-rose/40 hover:text-signal-rose disabled:cursor-not-allowed disabled:text-slate-700"
                  title="Cancel"
                >
                  <Square className="h-4 w-4" />
                </button>
              </div>

              <button
                type="button"
                onClick={saveForLater}
                disabled={status !== "running" && !sessionId}
                className="inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.045] text-sm font-medium text-slate-300 transition hover:border-signal-amber/40 hover:text-white disabled:cursor-not-allowed disabled:text-slate-700"
              >
                <PauseCircle className="h-4 w-4" />
                {status === "running" ? "Save response" : "Save for later"}
              </button>
            </div>
          </aside>

          <section className="flex min-h-[68vh] w-full max-w-full min-w-0 flex-col rounded-lg border border-white/10 bg-ink-900/74 shadow-panel backdrop-blur lg:min-h-0">
            <div className="flex shrink-0 flex-col gap-3 border-b border-white/10 p-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <h2 className="text-xl font-semibold text-white">Answer</h2>
                <p className="truncate text-sm text-slate-400">The response stays in this panel and scrolls independently.</p>
              </div>
              <button
                type="button"
                onClick={copyResponse}
                disabled={!response}
                className="inline-flex h-10 shrink-0 items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.055] px-3 text-sm font-medium text-slate-200 transition hover:border-signal-cyan/40 hover:text-white disabled:cursor-not-allowed disabled:text-slate-700"
              >
                <Copy className="h-4 w-4" />
                Copy answer
              </button>
            </div>

            {error ? (
              <div className="mx-4 mt-4 shrink-0 rounded-lg border border-signal-rose/30 bg-signal-rose/10 p-4 text-sm text-signal-rose">
                <div className="flex items-center gap-2 font-medium">
                  <XCircle className="h-4 w-4" />
                  {error}
                </div>
              </div>
            ) : null}

            <div className="min-h-0 min-w-0 max-w-full flex-1 overflow-hidden p-3 sm:p-4">
              <div className="thin-scrollbar min-h-[56vh] w-full max-w-full min-w-0 overflow-y-auto overflow-x-hidden rounded-lg border border-white/10 bg-black/24 p-4 sm:p-5 lg:h-full lg:min-h-0">
                {response ? (
                  <MarkdownResponse text={response} />
                ) : (
                  <div className="flex h-full min-h-[360px] flex-col items-center justify-center text-center">
                    <div className="grid h-16 w-16 place-items-center rounded-lg border border-signal-cyan/25 bg-signal-cyan/10">
                      {status === "running" ? (
                        <Loader2 className="h-6 w-6 animate-spin text-signal-cyan" />
                      ) : (
                        <BookOpen className="h-6 w-6 text-signal-cyan" />
                      )}
                    </div>
                    <p className="mt-4 max-w-md text-sm leading-6 text-slate-400">
                      The response will appear here as Meridian works.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </section>

        </section>
      </div>
    </main>
  );
}
