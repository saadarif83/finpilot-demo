import AgentTrace from "./AgentTrace";

const STATUS_TEXT = { running: "Live", done: "Complete", error: "Failed" };

// Header + live sequence diagram. `run` = { events, status, error, totals }.
export function TracePanel({ run, onClose }) {
  return (
    <div className="trace-panel">
      <div className="trace-panel-head">
        <div className="trace-panel-title">🔍 Under the hood</div>
        <span className={`trace-status ${run.status}`}>
          {run.status === "running" && <span className="trace-status-dot" />}
          {STATUS_TEXT[run.status]}
        </span>
        {onClose && (
          <button className="modal-close" onClick={onClose} aria-label="Close trace">✕</button>
        )}
      </div>
      <AgentTrace events={run.events} status={run.status} error={run.error} totals={run.totals} />
    </div>
  );
}

// Full-screen sheet version, used over the chat screen.
export function TraceSheet({ run, onClose }) {
  return (
    <div className="modal-overlay" onClick={run.status === "running" ? undefined : onClose}>
      <div className="modal-sheet trace-sheet" onClick={(e) => e.stopPropagation()}>
        <TracePanel run={run} onClose={onClose} />
        {run.status !== "running" && (
          <button className="btn-trace-done" onClick={onClose}>
            {run.status === "done" ? "View answer" : "Close"}
          </button>
        )}
      </div>
    </div>
  );
}
