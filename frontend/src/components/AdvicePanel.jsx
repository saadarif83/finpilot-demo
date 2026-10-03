import { useState, useEffect, useRef } from "react";
import { streamAdvice } from "../api";
import ProposalCard from "./ProposalCard";
import { TracePanel } from "./TracePanel";
import { toolNamesFrom } from "../trace";

export default function AdvicePanel({ onClose, onActionExecuted }) {
  const [run, setRun] = useState({ events: [], status: "running" });
  const [showTrace, setShowTrace] = useState(true);
  const [reply, setReply] = useState(null);
  const [proposal, setProposal] = useState(null);
  const started = useRef(false);
  const replyRef = useRef(null);

  useEffect(() => {
    if (started.current) return; // guard against React StrictMode double-invoke
    started.current = true;

    const events = [];
    streamAdvice((event) => {
      if (event.type === "trace") {
        events.push(event);
        setRun({ events: [...events], status: "running" });
      } else if (event.type === "final") {
        setRun({ events: [...events], status: "done", totals: event.totals });
        setReply(event.reply);
        setProposal(event.proposal);
      } else if (event.type === "error") {
        setRun({ events: [...events], status: "error", error: event.message });
      }
    }).catch((err) => {
      setRun({ events: [...events], status: "error", error: err.message });
    });
  }, []);

  useEffect(() => {
    if (reply) replyRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [reply]);

  const tools = toolNamesFrom(run.events);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet advice-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>✨ Today's advice</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {showTrace ? (
          <TracePanel run={run} onClose={() => setShowTrace(false)} />
        ) : (
          <button className="trace-reopen" onClick={() => setShowTrace(true)}>
            <span className="trace-reopen-title">
              {run.status === "running" ? "⏳ FinPilot is working… tap to watch" : "🔍 Show how FinPilot built this"}
            </span>
            {tools.length > 0 && (
              <span className="trace-reopen-tools">
                MCP tools: {tools.map((t) => <code key={t}>{t}</code>)}
              </span>
            )}
          </button>
        )}

        <div ref={replyRef} />
        {reply && <div className="advice-reply">{reply}</div>}
        {proposal && <ProposalCard proposal={proposal} onExecuted={onActionExecuted} />}
      </div>
    </div>
  );
}
