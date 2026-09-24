import { useState } from "react";
import { executeAction } from "../api";

// Renders a proposal the LLM computed (via a READ-ONLY tool) and lets the
// user explicitly confirm before anything actually happens. Execution goes
// through a separate, deterministic backend endpoint that the LLM itself
// has no access to — this component is the only path from "the AI suggested
// it" to "money actually moved," and it requires an explicit click.
export default function ProposalCard({ proposal, onExecuted }) {
  const [status, setStatus] = useState("pending"); // pending | executing | done | error
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  async function handleConfirm() {
    setStatus("executing");
    setError(null);
    try {
      const res = await executeAction(proposal.type, proposal.amount);
      setResult(res);
      setStatus("done");
      onExecuted?.(res);
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  if (!proposal || proposal.recommended === false) return null;

  return (
    <div className="proposal-card">
      <div className="proposal-header">💡 Proposed action</div>
      <p className="proposal-rationale">{proposal.rationale}</p>

      <div className="proposal-numbers">
        <div className="proposal-row">
          <span>Credit card balance</span>
          <span>
            ${proposal.before.creditcard_balance.toLocaleString()} → <b>${proposal.after.creditcard_balance.toLocaleString()}</b>
          </span>
        </div>
        <div className="proposal-row">
          <span>Brokerage cash</span>
          <span>
            ${proposal.before.brokerage_cash.toLocaleString()} → <b>${proposal.after.brokerage_cash.toLocaleString()}</b>
          </span>
        </div>
        <div className="proposal-row highlight">
          <span>Estimated annual savings</span>
          <span>${proposal.estimated_annual_savings.toLocaleString()}/yr</span>
        </div>
      </div>

      {status === "pending" && (
        <button className="btn-execute" onClick={handleConfirm}>
          Confirm &amp; Execute — Pay ${proposal.amount.toLocaleString()}
        </button>
      )}
      {status === "executing" && <button className="btn-execute" disabled>Executing…</button>}
      {status === "done" && (
        <div className="proposal-success">
          ✅ Done — ${proposal.amount.toLocaleString()} moved from brokerage cash to your credit card.
        </div>
      )}
      {status === "error" && (
        <div className="proposal-error">⚠️ {error}</div>
      )}
    </div>
  );
}
