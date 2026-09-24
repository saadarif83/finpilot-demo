import { useState } from "react";
import DetailView from "./DetailView";

const CARD_META = {
  banking: { icon: "🏦", label: "Checking & Savings", color: "#2f7ef7" },
  creditcard: { icon: "💳", label: "Credit Card", color: "#f7a52f" },
  mortgage: { icon: "🏠", label: "Mortgage", color: "#4caf50" },
  brokerage: { icon: "📈", label: "Brokerage", color: "#a855f7" },
};

function fmt(n) {
  return n.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 0 });
}

export default function Dashboard({ summary, onConnectClick }) {
  const [detailAccount, setDetailAccount] = useState(null);

  if (!summary) return <div className="dashboard-loading">Loading your accounts…</div>;

  const accounts = summary.accounts || {};
  const connected = summary.connected || [];

  const netWorth = Object.entries(accounts).reduce((sum, [key, a]) => {
    if (key === "banking") return sum + a.total;
    if (key === "brokerage") return sum + a.total;
    if (key === "creditcard") return sum - a.current_balance;
    if (key === "mortgage") return sum - a.current_principal;
    return sum;
  }, 0);

  return (
    <div className="dashboard">
      {connected.length > 0 && (
        <div className="net-worth-tile">
          <div className="net-worth-label">Net position across connected accounts</div>
          <div className="net-worth-value">{fmt(netWorth)}</div>
        </div>
      )}

      <div className="account-grid">
        {["banking", "creditcard", "mortgage", "brokerage"].map((key) => {
          const meta = CARD_META[key];
          const isConnected = connected.includes(key);
          const a = accounts[key];

          return (
            <button
              key={key}
              className="account-card"
              style={{ borderColor: isConnected ? meta.color : "#2a2a3a" }}
              onClick={() => (isConnected ? setDetailAccount(key) : onConnectClick())}
            >
              <div className="account-card-icon" style={{ background: meta.color + "22" }}>{meta.icon}</div>
              <div className="account-card-body">
                <div className="account-card-label">{meta.label}</div>
                {!isConnected && <div className="account-card-cta">Tap to connect</div>}
                {isConnected && key === "banking" && (
                  <>
                    <div className="account-card-value">{fmt(a.total)}</div>
                    <div className="account-card-sub">Checking {fmt(a.checking_balance)} · Savings {fmt(a.savings_balance)}</div>
                  </>
                )}
                {isConnected && key === "creditcard" && (
                  <>
                    <div className="account-card-value">{fmt(a.current_balance)}</div>
                    <div className="account-card-sub">{a.utilization_pct}% of {fmt(a.credit_limit)} limit · {a.apr}% APR</div>
                  </>
                )}
                {isConnected && key === "mortgage" && (
                  <>
                    <div className="account-card-value">{fmt(a.current_principal)}</div>
                    <div className="account-card-sub">{a.interest_rate_apr}% APR · {fmt(a.monthly_payment)}/mo</div>
                  </>
                )}
                {isConnected && key === "brokerage" && (
                  <>
                    <div className="account-card-value">{fmt(a.total)}</div>
                    <div className="account-card-sub">Positions {fmt(a.positions_value)} · Cash {fmt(a.cash)}</div>
                  </>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {connected.length === 0 && (
        <div className="empty-state">
          <p>Connect your accounts to see your financial picture in one place.</p>
          <button className="btn-connect" onClick={onConnectClick}>Connect accounts</button>
        </div>
      )}

      {detailAccount && (
        <DetailView accountType={detailAccount} onClose={() => setDetailAccount(null)} />
      )}
    </div>
  );
}
