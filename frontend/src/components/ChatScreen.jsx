import { useState, useRef, useEffect } from "react";
import { streamChat } from "../api";
import ProposalCard from "./ProposalCard";
import { TraceSheet } from "./TracePanel";
import { toolNamesFrom } from "../trace";

const SUGGESTED = [
  "Should I take this vacation?",
  "Should I make an extra mortgage payment to reduce my total interest?",
  "Where should my idle cash go?",
  "Should I pay down my credit card with brokerage cash?",
];

export default function ChatScreen({ onActionExecuted }) {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi, I'm FinPilot. Connect your accounts, then ask me anything about your finances." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [liveRun, setLiveRun] = useState(null); // { events, status, error, totals }
  const [traceView, setTraceView] = useState(null); // null | "live" | message index
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text) {
    const messageText = text ?? input;
    if (!messageText.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: messageText }]);
    setInput("");
    setLoading(true);

    // Collected locally too, so the finished message keeps its own copy of
    // the trace and can reopen it later.
    const events = [];
    setLiveRun({ events: [], status: "running" });
    setTraceView("live");

    const finish = (run, message) => {
      setLiveRun(run);
      setMessages((m) => [...m, { ...message, trace: run }]);
      setLoading(false);
    };

    try {
      await streamChat(messageText, (event) => {
        if (event.type === "trace") {
          events.push(event);
          setLiveRun({ events: [...events], status: "running" });
        } else if (event.type === "final") {
          finish(
            { events: [...events], status: "done", totals: event.totals },
            { role: "assistant", text: event.reply, proposal: event.proposal },
          );
        } else if (event.type === "error") {
          finish(
            { events: [...events], status: "error", error: event.message },
            { role: "assistant", text: `⚠️ ${event.message}`, isError: true },
          );
        }
      });
    } catch (err) {
      finish(
        { events: [...events], status: "error", error: err.message },
        { role: "assistant", text: `⚠️ ${err.message}`, isError: true },
      );
    }
  }

  const sheetRun = traceView === "live" ? liveRun : traceView != null ? messages[traceView]?.trace : null;

  return (
    <div className="chat-screen">
      <div className="messages">
        {messages.map((m, i) => {
          const tools = toolNamesFrom(m.trace?.events);
          return (
            <div key={i} className={`bubble ${m.role} ${m.isError ? "error" : ""}`}>
              {m.text}
              {m.proposal && <ProposalCard proposal={m.proposal} onExecuted={onActionExecuted} />}
              {m.trace && (
                <button className="trace-reopen" onClick={() => setTraceView(i)}>
                  <span className="trace-reopen-title">🔍 How FinPilot got this</span>
                  {tools.length > 0 && (
                    <span className="trace-reopen-tools">
                      MCP tools: {tools.map((t) => <code key={t}>{t}</code>)}
                    </span>
                  )}
                  {m.trace.totals && (
                    <span className="trace-reopen-meta">
                      {m.trace.totals.claude_calls} Claude calls · {m.trace.totals.tool_calls} tool calls · {(m.trace.totals.total_ms / 1000).toFixed(1)} s
                    </span>
                  )}
                </button>
              )}
            </div>
          );
        })}
        {loading && traceView !== "live" && (
          <button className="trace-reopen live" onClick={() => setTraceView("live")}>
            <span className="trace-reopen-title">⏳ FinPilot is working… tap to watch</span>
          </button>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 1 && (
        <div className="suggestions">
          {SUGGESTED.map((s) => (
            <button key={s} className="suggestion-chip" onClick={() => handleSend(s)}>
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask FinPilot…"
        />
        <button onClick={() => handleSend()} disabled={loading}>Send</button>
      </div>

      {sheetRun && <TraceSheet run={sheetRun} onClose={() => setTraceView(null)} />}
    </div>
  );
}
