import { useState } from "react";
import { openConnectPopup, connectCreditCard } from "../api";

const PORTALS = [
  { id: "banking", name: "SecureBank", icon: "🏦", auth: "OAuth 2.0 Authorization Code", color: "#2f7ef7" },
  { id: "mortgage", name: "HomeLend", icon: "🏠", auth: "OpenID Connect", color: "#4caf50" },
  { id: "creditcard", name: "Everyday Rewards Visa", icon: "💳", auth: "Client Credentials", color: "#f7a52f" },
  { id: "brokerage", name: "StreetTrade", icon: "📈", auth: "Authorization Code + PKCE", color: "#a855f7" },
];

export default function ConnectModal({ connected, onStatusRefresh, onClose }) {
  const [connecting, setConnecting] = useState(null);

  async function handleConnect(portal) {
    if (portal === "creditcard") {
      setConnecting(portal);
      try {
        await connectCreditCard();
      } finally {
        setConnecting(null);
        onStatusRefresh();
      }
      return;
    }
    setConnecting(portal);
    const popup = openConnectPopup(portal);
    const timer = setInterval(() => {
      if (popup.closed) {
        clearInterval(timer);
        setConnecting(null);
        onStatusRefresh();
      }
    }, 500);
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Connected accounts</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <p className="subtitle">Each portal uses a different industry-standard auth flow.</p>
        <div className="portal-list">
          {PORTALS.map((p) => {
            const isConnected = connected.includes(p.id);
            return (
              <div className="portal-card" key={p.id} style={{ borderColor: isConnected ? p.color : "#2a2a3a" }}>
                <div className="portal-icon">{p.icon}</div>
                <div className="portal-info">
                  <div className="portal-name">{p.name}</div>
                  <div className="portal-auth-badge" style={{ background: p.color + "33", color: p.color }}>
                    {p.auth}
                  </div>
                </div>
                <button
                  className={isConnected ? "btn-connected" : "btn-connect"}
                  onClick={() => handleConnect(p.id)}
                  disabled={connecting === p.id}
                >
                  {isConnected ? "✓ Connected" : connecting === p.id ? "Connecting…" : "Connect"}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
