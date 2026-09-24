// Shows the live sequence of steps (status updates, tool calls, tool
// results) as FinPilot works through a question. This is deliberately
// visible rather than hidden behind a spinner — for the talk, it's the
// piece that makes the MCP architecture visible: the audience watches
// FinPilot decide which accounts to check, in real time.

const TOOL_LABELS = {
  get_banking_accounts: "Checking bank balances",
  get_banking_transactions: "Reading bank transactions",
  get_banking_cashflow: "Analyzing cash flow",
  get_mortgage_details: "Checking mortgage details",
  get_mortgage_amortization: "Reading mortgage amortization",
  get_creditcard_account: "Checking credit card balance",
  get_creditcard_transactions: "Reading credit card transactions",
  get_creditcard_spending_breakdown: "Analyzing card spending",
  get_brokerage_positions: "Checking brokerage positions",
  get_brokerage_cash: "Checking brokerage cash",
  get_brokerage_performance: "Reading portfolio performance",
  get_market_news: "Checking market news",
  propose_creditcard_payoff_from_brokerage: "Computing a debt payoff plan",
};

function labelFor(event) {
  if (event.type === "status") return event.message;
  if (event.type === "tool_call") return TOOL_LABELS[event.tool] || `Calling ${event.tool}`;
  if (event.type === "tool_result") return `Got result from ${TOOL_LABELS[event.tool] || event.tool}`;
  if (event.type === "error") return `Error: ${event.message}`;
  return null;
}

function iconFor(event) {
  if (event.type === "tool_call") return "🔧";
  if (event.type === "tool_result") return "✅";
  if (event.type === "error") return "⚠️";
  return "•";
}

export default function ActivityFeed({ steps, active }) {
  if (steps.length === 0 && !active) return null;

  return (
    <div className="activity-feed">
      <div className="activity-feed-header">
        {active ? "FinPilot is working…" : "What FinPilot did"}
      </div>
      <div className="activity-feed-steps">
        {steps.map((event, i) => {
          const label = labelFor(event);
          if (!label) return null;
          return (
            <div key={i} className={`activity-step ${event.type}`}>
              <span className="activity-icon">{iconFor(event)}</span>
              <span className="activity-label">{label}</span>
            </div>
          );
        })}
        {active && <div className="activity-step pulse"><span className="activity-icon">⏳</span><span className="activity-label">…</span></div>}
      </div>
    </div>
  );
}
