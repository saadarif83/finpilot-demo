import { useState, useEffect, useRef } from "react";

// Live sequence diagram of one FinPilot run. Every row is a real hop the
// backend reported (see backend/app/orchestrator/agent.py): the app's request,
// the MCP handshake and tools/list, each Claude Messages API call, each MCP
// tools/call with its real tool name, and the final answer. Tap a row to see
// the actual payload.

const LANES = [
  { id: "app", label: "App", icon: "📱", color: "#c3c2b7" },
  { id: "orchestrator", label: "Orchestrator", icon: "⚙️", color: "#3987e5" },
  { id: "claude", label: "Claude API", icon: "🧠", color: "#d95926" },
  { id: "mcp", label: "MCP Server", icon: "🔌", color: "#199e70" },
];
const LANE_INDEX = Object.fromEntries(LANES.map((l, i) => [l.id, i]));
const laneCenter = (id) => (LANE_INDEX[id] + 0.5) * (100 / LANES.length);

// Which portal (and which auth flow's token) sits behind each MCP tool.
function portalFor(tool = "") {
  if (tool.startsWith("get_banking")) return "SecureBank API using its OAuth Authorization Code token";
  if (tool.startsWith("get_mortgage")) return "HomeLend API using its OpenID Connect token";
  if (tool.startsWith("get_creditcard")) return "card issuer API using its Client Credentials token";
  if (tool.startsWith("get_brokerage")) return "StreetTrade API using its PKCE token";
  if (tool === "get_market_news") return "the market news feed";
  if (tool.startsWith("propose_")) return "credit card + brokerage APIs, then computed a plan (read-only, moves no money)";
  return "the portal API";
}

function explain(ev) {
  const d = ev.detail || {};
  switch (ev.kind) {
    case "request":
      return "Your question goes to the FinPilot backend.";
    case "mcp_init":
      return "Orchestrator opens an MCP session with the FinPilot MCP server.";
    case "mcp_tools_list":
      return "MCP server advertises its tools; the orchestrator converts them into Claude tool schemas.";
    case "llm_request":
      return ev.turn === 1
        ? `Question + ${d.tools_offered} tool definitions sent to Claude.`
        : `${d.tool_results_included} tool result${d.tool_results_included === 1 ? "" : "s"} sent back to Claude.`;
    case "llm_response":
      return d.stop_reason === "tool_use"
        ? "Claude picks the tools it needs. It can't run them itself; it asks the orchestrator."
        : "Claude writes the final answer from the real numbers.";
    case "tool_call":
      return "Orchestrator runs the tool on Claude's behalf over MCP.";
    case "tool_result":
      return d.is_error ? "The tool reported a problem." : `MCP server called the ${portalFor(d.tool)}.`;
    case "final":
      return "Answer streamed back to the app.";
    default:
      return null;
  }
}

// Which party is busy right now, based on the last hop.
function working(last) {
  if (!last) return { lane: "orchestrator", text: "Starting…" };
  if (last.kind === "request") return { lane: "mcp", text: "Opening MCP session…" };
  if (last.kind === "mcp_init") return { lane: "mcp", text: "Listing tools…" };
  if (last.kind === "llm_request") return { lane: "claude", text: "Claude is thinking…" };
  if (last.kind === "tool_call") return { lane: "mcp", text: `Running ${last.detail?.tool}…` };
  return { lane: "orchestrator", text: "Orchestrator working…" };
}

function fmtMs(ms) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)} s` : `${ms} ms`;
}

function Detail({ ev }) {
  const d = ev.detail || {};
  if (ev.kind === "mcp_tools_list") {
    return (
      <div className="trace-chips">
        {d.tools.map((t) => <code key={t} className="trace-chip">{t}</code>)}
      </div>
    );
  }
  if (ev.kind === "tool_result") {
    return <pre className="trace-pre">{d.result_preview}</pre>;
  }
  if (ev.kind === "tool_call") {
    return (
      <pre className="trace-pre">{`tool: ${d.tool}\narguments: ${JSON.stringify(d.arguments)}\ntool_use_id: ${d.tool_use_id}`}</pre>
    );
  }
  if (ev.kind === "llm_response") {
    return (
      <>
        {d.claude_text && d.stop_reason === "tool_use" && (
          <div className="trace-quote">“{d.claude_text}”</div>
        )}
        <pre className="trace-pre">{
          `stop_reason: ${d.stop_reason}\n` +
          (d.tools_requested?.length ? `tools_requested: ${d.tools_requested.map((t) => t.name).join(", ")}\n` : "") +
          `input_tokens: ${d.input_tokens}\noutput_tokens: ${d.output_tokens}`
        }</pre>
      </>
    );
  }
  return <pre className="trace-pre">{JSON.stringify(d, null, 2)}</pre>;
}

function Row({ ev }) {
  const [open, setOpen] = useState(false);
  const from = laneCenter(ev.from);
  const to = laneCenter(ev.to);
  const left = Math.min(from, to);
  const width = Math.abs(from - to);
  const color = LANES[LANE_INDEX[ev.from]].color;
  const isError = ev.detail?.is_error;
  const hasDetail = ev.detail && Object.keys(ev.detail).length > 0;

  return (
    <div className="trace-row">
      <button
        type="button"
        className="trace-row-hit"
        onClick={() => hasDetail && setOpen((o) => !o)}
        aria-expanded={open}
      >
        <div className="trace-arrow-track">
          <div
            className={`trace-arrow ${to > from ? "right" : "left"}`}
            style={{ left: `${left}%`, width: `${width}%`, "--c": isError ? "#e66767" : color }}
          />
        </div>
        <div className="trace-label-wrap" style={{ paddingLeft: `${left}%` }}>
          <div className="trace-label">
            <span className="trace-seq">{ev.seq}</span>
            <span className={`trace-label-text ${isError ? "err" : ""}`}>{ev.label}</span>
          </div>
          <div className="trace-explain">
            {ev.duration_ms != null && <span className="trace-dur">{fmtMs(ev.duration_ms)} · </span>}
            {explain(ev)}
          </div>
        </div>
        {hasDetail && <span className="trace-caret" aria-hidden="true">{open ? "▾" : "▸"}</span>}
      </button>
      {open && <div className="trace-detail"><Detail ev={ev} /></div>}
    </div>
  );
}

export default function AgentTrace({ events, status, error, totals }) {
  const endRef = useRef(null);

  useEffect(() => {
    if (status === "running") endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [events.length, status]);

  const busy = status === "running" ? working(events[events.length - 1]) : null;

  return (
    <div className="trace">
      <div className="trace-lanes">
        {LANES.map((l) => (
          <div key={l.id} className="trace-lane-head" style={{ "--c": l.color }}>
            <span className="trace-lane-icon">{l.icon}</span>
            <span className="trace-lane-name">{l.label}</span>
          </div>
        ))}
      </div>

      <div className="trace-body">
        <div className="trace-lifelines" aria-hidden="true">
          {LANES.map((l) => (
            <div key={l.id} className="trace-lifeline" style={{ left: `${laneCenter(l.id)}%`, "--c": l.color }} />
          ))}
        </div>

        {events.map((ev, i) => {
          const prevTurn = i > 0 ? events[i - 1].turn : undefined;
          const showTurn = ev.turn && ev.turn !== prevTurn;
          return (
            <div key={ev.seq}>
              {showTurn && <div className="trace-turn"><span>Agent loop · turn {ev.turn}</span></div>}
              <Row ev={ev} />
            </div>
          );
        })}

        {busy && (
          <div className="trace-busy">
            <div className="trace-busy-dot" style={{ left: `${laneCenter(busy.lane)}%`, "--c": LANES[LANE_INDEX[busy.lane]].color }} />
            <div className="trace-busy-text">{busy.text}</div>
          </div>
        )}

        {status === "error" && (
          <div className="trace-error">⚠️ {error || "Something went wrong."}</div>
        )}
        <div ref={endRef} />
      </div>

      {status === "done" && totals && (
        <div className="trace-summary">
          <div><b>{totals.claude_calls}</b> Claude call{totals.claude_calls === 1 ? "" : "s"}</div>
          <div><b>{totals.tool_calls}</b> MCP tool call{totals.tool_calls === 1 ? "" : "s"}</div>
          <div><b>{(totals.input_tokens + totals.output_tokens).toLocaleString()}</b> tokens</div>
          <div><b>{fmtMs(totals.total_ms)}</b> total</div>
        </div>
      )}
    </div>
  );
}
